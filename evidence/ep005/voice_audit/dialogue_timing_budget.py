#!/usr/bin/env python3
"""EP005 dialogue timing budget (read-only, deterministic, no provider calls).

Estimates spoken duration of approved dialogue from syllable counts at fixed
preschool-appropriate rates and compares it with each shot's available window.
This is a planning estimate, not a measurement: real durations are only known
after a human-approved voice renders the line.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SNAP = ROOT / 'agent008/inputs/ep005_phase0_input_snapshot.json'

# Rates in syllables per second. Preschool delivery is slower than adult conversation.
RATES = {'preschool_comfortable': 3.0, 'preschool_brisk': 3.5, 'adult_conversational': 4.0}
INTRA_LINE_PAUSE = {'!': 0.25, '.': 0.25, '?': 0.25, ',': 0.12}   # pauses inside a line (not after the last mark)
BETWEEN_LINES = 0.45                                              # natural breath/beat between two lines
TAIL_GUARD = 0.20                                                 # silence before a protected/next shot

# Exact syllable counts for the S004 words (hand-verified); the heuristic below is only for the episode scan.
S004_SYLLABLES = {'a': 1, 'little': 2, 'glint': 1, 'look': 1, 'at': 1, 'his': 1, 'cheek': 1,
                  'can': 1, 'you': 1, 'help': 1, 'mikko': 2, 'find': 1, 'the': 1, 'next': 1, 'berry': 2, 'smudge': 1}


def syllables(word):
    w = re.sub(r'[^a-z]', '', word.lower())
    if not w:
        return 0
    if w in S004_SYLLABLES:
        return S004_SYLLABLES[w]
    groups = re.findall(r'[aeiouy]+', w)
    n = len(groups)
    if w.endswith('e') and not w.endswith(('le', 'ee')) and n > 1:
        n -= 1
    return max(1, n)


def line_stats(text):
    words = re.findall(r"[A-Za-z’']+", text)
    syl = sum(syllables(w) for w in words)
    marks = re.findall(r'[!.?,]', text.rstrip(' !.?”"'))
    pause = sum(INTRA_LINE_PAUSE[m] for m in marks)
    return {'text': text, 'words': len(words), 'syllables': syl, 'intra_pause_s': round(pause, 3)}


def speech_seconds(lines, rate):
    t = sum(l['syllables'] / rate + l['intra_pause_s'] for l in lines)
    return round(t + BETWEEN_LINES * max(0, len(lines) - 1), 3)


def main():
    snap = json.loads(SNAP.read_text())
    sys.path.insert(0, str(ROOT))
    from agent008.spec import parse_voice_line
    out = {'method': 'syllable-rate estimate; planning only', 'rates_syl_per_s': RATES,
           'between_lines_s': BETWEEN_LINES, 'tail_guard_s': TAIL_GUARD}

    # S004 detailed budget
    s = next(x for x in snap['production_manifest']['manifest_json_reduced']['shot_plans'] if x['shot_id'] == 'S004')
    lines = [line_stats(parse_voice_line(v)[1]) for v in s['shot_plan']['audio_plan']['voice_lines']]
    shot = s['end_seconds'] - s['start_seconds']
    glint_start = 12 / 24
    earliest = glint_start + 0.15          # Lumi reacts to the glint ("A little glint!") just after it appears
    latest_end = shot - TAIL_GUARD         # S005 is a protected silent hold; dialogue must be finished before it
    window = round(latest_end - earliest, 3)
    est = {k: speech_seconds(lines, r) for k, r in RATES.items()}
    out['S004'] = {
        'shot_seconds': shot, 'frames': int(shot * 24), 'glint_frames': [12, 19],
        'chime_clip_seconds': [0.5, 4.875], 'lines': lines,
        'dialogue_window': {'earliest_start_s': round(earliest, 3), 'latest_end_s': round(latest_end, 3),
                            'max_dialogue_s': window,
                            'absolute_max_s_no_reaction_no_guard': round(shot - glint_start, 3)},
        'estimated_speech_s': est,
        'overrun_s': {k: round(v - window, 3) for k, v in est.items()},
        'fits_at_any_natural_rate': any(v <= window for v in est.values()),
    }
    out['S004']['TIMING_CONFLICT'] = 'NO' if est['preschool_comfortable'] <= window else 'YES'

    # Episode scan (rendered + validator shots in the snapshot only)
    scan = []
    for x in snap['production_manifest']['manifest_json_reduced']['shot_plans']:
        vl = x['shot_plan']['audio_plan']['voice_lines']
        if not vl:
            continue
        ls = [line_stats(parse_voice_line(v)[1]) for v in vl]
        dur = x['end_seconds'] - x['start_seconds']
        scan.append({'shot_id': x['shot_id'], 'shot_s': dur, 'lines': len(ls),
                     'est_comfortable_s': speech_seconds(ls, RATES['preschool_comfortable']),
                     'est_brisk_s': speech_seconds(ls, RATES['preschool_brisk'])})
    out['snapshot_voice_shots'] = scan
    print(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == '__main__':
    main()
