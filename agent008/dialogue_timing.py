"""G09: dialogue timing, overlap and visual-hold guard (offline, deterministic, no provider).

Runs after `motion.compose.resolve_dialogue` has bound every authoritative dialogue slot to exactly one
approved, hash-verified clip. It fixes each clip's start and end on the output sample grid and fails closed
when dialogue cannot fit safely inside the authoritative shot.

Timing contract (all optional; absent keys keep the pre-G09 behaviour for shots that already fit):
  timing['dialogue'][i]['start_seconds']            explicit start of slot i (already required)
  timing['dialogue_window'] = {'pre_hold_seconds': a, 'post_hold_seconds': b}
      a visual hold with no dialogue before the first line and after the last line;
      dialogue must lie inside [a, shot_duration - b]. Ending exactly on a boundary is valid.
  timing['dialogue_overlaps'] = [{'slots': [i, j], 'max_overlap_seconds': x, 'authorised_by': '<who>'}]
      the only way two lines may overlap; each declared overlap must actually occur and stay within x.

Never covered here: lip-sync, speech generation, voice choice.
"""
from . import media
from .errors import FailClosed

G09_VERSION = 'agent008-g09-v1'


def _sample(seconds, sr):
    return int(round(float(seconds) * sr))


def govern_dialogue_timing(spec_shot, dialogue, inputs, timing, spec):
    """Return the deterministic G09 report for `dialogue` (output of resolve_dialogue). Fail closed otherwise."""
    sid = spec_shot['shot_id']
    slots = spec_shot.get('dialogue_slots') or []
    sr, ch = spec.audio_sample_rate, spec.audio_channels
    shot_end = _sample(spec_shot['frames'] / spec.fps, sr)
    if len(dialogue) != len(slots):                                        # required dialogue cannot vanish
        raise FailClosed('DIALOGUE_SLOT_UNFILLED', f'{sid}: {len(slots)} slot(s), {len(dialogue)} resolved')
    win = timing.get('dialogue_window') or {}
    unknown = set(win) - {'pre_hold_seconds', 'post_hold_seconds'}
    if unknown:
        raise FailClosed('DIALOGUE_WINDOW_INVALID', f'{sid}: unknown keys {sorted(unknown)}')
    pre, post = float(win.get('pre_hold_seconds', 0.0)), float(win.get('post_hold_seconds', 0.0))
    w0, w1 = _sample(pre, sr), shot_end - _sample(post, sr)
    if pre < 0 or post < 0 or w0 >= w1:
        raise FailClosed('DIALOGUE_WINDOW_INVALID', f'{sid}: pre {pre} s, post {post} s in {shot_end / sr} s')
    if dialogue and spec_shot.get('protected_participation_hold'):
        raise FailClosed('DIALOGUE_IN_PROTECTED_HOLD', sid)

    lines = []
    for i, d in enumerate(dialogue):
        n = len(media.load_audio(inputs[d['audio_asset_id']], sr, ch))
        if n == 0:
            raise FailClosed('DIALOGUE_CLIP_EMPTY', d['audio_asset_id'])
        s = _sample(d['start_seconds'], sr)
        e = s + n
        if e > shot_end:                                                   # same code as the mix backstop
            raise FailClosed('DIALOGUE_OVERRUNS_SHOT', f'{sid} slot {i} {d["audio_asset_id"]} ends at {e / sr:.6f} s '
                                                       f'(shot {shot_end / sr:.6f} s)')
        if s < w0 or e > w1:
            raise FailClosed('DIALOGUE_OUTSIDE_WINDOW', f'{sid} slot {i} {d["audio_asset_id"]}: '
                                                        f'{s / sr:.6f}-{e / sr:.6f} s outside {w0 / sr:.6f}-{w1 / sr:.6f} s')
        lines.append({'slot': i, 'speaker': d['speaker'], 'audio_asset_id': d['audio_asset_id'],
                      'start_sample': s, 'end_sample': e, 'start_s': round(s / sr, 6), 'end_s': round(e / sr, 6),
                      'duration_s': round(n / sr, 6)})
    for a, b in zip(lines, lines[1:]):
        if b['start_sample'] < a['start_sample']:
            raise FailClosed('DIALOGUE_ORDER_MISMATCH', f"{sid}: slot {b['slot']} starts before slot {a['slot']}")

    declared = {}
    for o in timing.get('dialogue_overlaps') or []:
        pair = tuple(sorted(int(x) for x in o.get('slots', ())))
        if len(pair) != 2 or pair[0] == pair[1] or pair[1] >= len(lines) or not o.get('authorised_by') \
                or float(o.get('max_overlap_seconds', -1)) <= 0 or pair in declared:
            raise FailClosed('DIALOGUE_OVERLAP_DECLARATION_INVALID', f'{sid}: {o}')
        declared[pair] = o
    overlaps = []
    for i in range(len(lines)):
        for j in range(i + 1, len(lines)):
            ov = min(lines[i]['end_sample'], lines[j]['end_sample']) - max(lines[i]['start_sample'], lines[j]['start_sample'])
            if ov <= 0:
                continue
            o = declared.get((i, j))
            if o is None:
                raise FailClosed('DIALOGUE_OVERLAP_UNAUTHORISED', f'{sid}: slots {i}/{j} overlap {ov / sr:.6f} s')
            if ov > _sample(o['max_overlap_seconds'], sr):
                raise FailClosed('DIALOGUE_OVERLAP_EXCEEDS_AUTHORISED',
                                 f"{sid}: slots {i}/{j} overlap {ov / sr:.6f} s > {o['max_overlap_seconds']} s")
            overlaps.append({'slots': [i, j], 'overlap_s': round(ov / sr, 6), 'authorised_by': o['authorised_by'],
                             'max_overlap_seconds': float(o['max_overlap_seconds'])})
    unused = sorted(set(declared) - {tuple(o['slots']) for o in overlaps})
    if unused:
        raise FailClosed('DIALOGUE_OVERLAP_DECLARED_NOT_PRESENT', f'{sid}: {unused}')

    report = {'version': G09_VERSION, 'shot_id': sid, 'sample_rate': sr, 'shot_end_s': round(shot_end / sr, 6),
              'window': {'start_s': round(w0 / sr, 6), 'end_s': round(w1 / sr, 6),
                         'pre_hold_seconds': pre, 'post_hold_seconds': post},
              'lines': lines, 'overlaps': overlaps}
    if lines:
        report['visual_holds'] = {'before_first_line_s': round(lines[0]['start_sample'] / sr, 6),
                                  'after_last_line_s': round((shot_end - max(l['end_sample'] for l in lines)) / sr, 6)}
    return report
