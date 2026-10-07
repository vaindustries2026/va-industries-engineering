"""Timeline contract, plus the dialogue-attachment and timed-text (caption) interfaces.

Dialogue tracks and captions are interfaces only in Phase 0: no voice is
generated and no caption is burned in.
"""
from .errors import FailClosed

DIALOGUE_TRACK_FIELDS = ('shot_id', 'speaker', 'audio_asset_id', 'path', 'start', 'end', 'gain_db')


def dialogue_track(shot_id, speaker, audio_asset_id, path, start, end, gain_db=0.0):
    """A future dialogue attachment. Times are clip-relative seconds. Requires an approved audio asset id."""
    if not audio_asset_id or not path:
        raise FailClosed('DIALOGUE_REQUIRES_APPROVED_AUDIO')
    if not (0 <= start < end):
        raise FailClosed('DIALOGUE_TIMING_INVALID', f'{start}-{end}')
    return dict(zip(DIALOGUE_TRACK_FIELDS, (shot_id, speaker, audio_asset_id, path, float(start), float(end),
                                            float(gain_db))))


def timed_text_from_slots(slots, assignments=None):
    """Caption cues derived from manifest dialogue slots. Without timing assignments, cues are UNTIMED."""
    cues = []
    for i, s in enumerate(slots):
        a = (assignments or {}).get(i)
        cues.append({'index': i + 1, 'shot_id': s['shot_id'], 'speaker': s['speaker'], 'text': s['text'],
                     'start': a[0] if a else None, 'end': a[1] if a else None,
                     'status': 'TIMED' if a else 'UNTIMED_NO_VOICE_ASSET'})
    return cues


def _ts(t, sep):
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f'{h:02d}:{m:02d}:{s:02d}{sep}{ms:03d}'


def _timed(cues):
    timed = [c for c in cues if c['start'] is not None]
    if len(timed) != len(cues):
        raise FailClosed('CAPTIONS_UNTIMED', f'{len(cues) - len(timed)} cue(s) without timing')
    return timed


def to_srt(cues):
    out = []
    for c in _timed(cues):
        out.append(f"{c['index']}\n{_ts(c['start'], ',')} --> {_ts(c['end'], ',')}\n{c['speaker']}: {c['text']}\n")
    return '\n'.join(out)


def to_webvtt(cues):
    out = ['WEBVTT', '']
    for c in _timed(cues):
        out.append(f"{_ts(c['start'], '.')} --> {_ts(c['end'], '.')}\n<v {c['speaker']}>{c['text']}\n")
    return '\n'.join(out)


def build_timeline(shot_specs, output_spec, timing):
    """Clip timeline: shots back-to-back at frame resolution, with cues and beds in clip time."""
    t, shots = 0, []
    for spec in shot_specs:
        shots.append({'shot_id': spec['shot_id'], 'start_frame': t, 'frames': spec['frames'],
                      'start_seconds': t / output_spec.fps, 'end_seconds': (t + spec['frames']) / output_spec.fps})
        t += spec['frames']
    return {'fps': output_spec.fps, 'total_frames': t, 'total_seconds': t / output_spec.fps,
            'shots': shots, 'timing_inputs': timing,
            'dialogue_tracks': [], 'dialogue_slots': [d for s in shot_specs for d in s['dialogue_slots']],
            'timed_text': timed_text_from_slots([d for s in shot_specs for d in s['dialogue_slots']]),
            'captions_burned_in': False}
