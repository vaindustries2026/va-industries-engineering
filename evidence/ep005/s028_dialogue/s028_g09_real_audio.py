"""G09 timing on the REAL S028 production dialogue clips (no estimates). Read-only; no provider calls.

Usage (repo root): python3 evidence/ep005/s028_dialogue/s028_g09_real_audio.py <lumi.mp3> <mikko.mp3> <snapshot.json|LIVE>
The S028 shot spec comes from the APPROVED v05 lineage (readiness 69bff641) via agent008.episode.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from agent008.config import load_output_spec  # noqa: E402
from agent008.dialogue_timing import govern_dialogue_timing
from agent008.episode import PINS, resolve_episode
from agent008.errors import FailClosed
from agent008.hashing import sha256_file
from agent008.inputs import load_hash_pins, load_snapshot
from agent008.motion.compose import resolve_dialogue

lumi, mikko, src = sys.argv[1:4]
spec = load_output_spec()
if src == 'LIVE':
    from agent008.tools.snapshot_inputs import build_snapshot
    snap = build_snapshot('69bff641-e056-4701-a23f-d91dbc2039b2')
else:
    snap = load_snapshot(src)
shot = {r['shot_id']: r for r in resolve_episode(snap, load_hash_pins(PINS), spec)}['S028']['spec']
files = {'DLG-EP005-S028-LUMI-v01': lumi, 'DLG-EP005-S028-MIKKO-v01': mikko}
SHA = {'DLG-EP005-S028-LUMI-v01': '970f55a95f73f0949be74c5d5424318811d5fa2add0438abd42e3f37f639a8bc',
       'DLG-EP005-S028-MIKKO-v01': 'ab81173ee7ddb15eeb8b3bbb0bdd7eed6840d76f9100d5edb1e6ca5d04b230b0'}


def run(name, lumi_start, mikko_start, window=None, overlaps=None):
    t = {'dialogue': [
        {'shot_id': 'S028', 'speaker': s['speaker'], 'text': s['text'], 'audio_asset_id': aid, 'expected_sha256': SHA[aid],
         # G09 analysis of REVIEW clips: registry_status is passed as APPROVED for the timing evaluation only;
         # production assembly stays blocked until the human approves each exact SHA.
         'registry_status': 'APPROVED', 'start_seconds': st, 'gain_db': 0.0}
        for s, aid, st in zip(shot['dialogue_slots'], files, (lumi_start, mikko_start))]}
    if window:
        t['dialogue_window'] = window
    if overlaps:
        t['dialogue_overlaps'] = overlaps
    try:
        rep = govern_dialogue_timing(shot, resolve_dialogue(shot, files, t), files, t, spec)
        return {'case': name, 'g09': 'PASS', 'lines': rep['lines'], 'window': rep['window'],
                'visual_holds': rep['visual_holds'], 'overlaps': rep['overlaps']}
    except FailClosed as e:
        return {'case': name, 'g09': 'FAIL_CLOSED', 'code': e.code, 'detail': e.detail}


slots = [(s['speaker'], s['text']) for s in shot['dialogue_slots']]
assert slots == [('Lumi', 'You look comfy. Story time.'), ('Mikko', 'I’m ready to rest.')], slots
assert all(sha256_file(p) == SHA[a] for a, p in files.items())
L = 122601 / 48000                                  # Lumi decoded length at the 48 kHz output rate
cases = [
    run('A_strict_back_to_back_from_0', 0.0, L),
    run('A2_strict_back_to_back_pre_hold_0.25', 0.25, 0.25 + L, {'pre_hold_seconds': 0.25}),
    run('B_minimal_adjustment_none_needed (same as A2; overlap 0)', 0.25, 0.25 + L, {'pre_hold_seconds': 0.25}),
    run('C_unauthorised_overlap_check (Mikko 0.10 s early, must fail)', 0.25, 0.25 + L - 0.10, {'pre_hold_seconds': 0.25}),
]
print(json.dumps({'shot': 'S028', 'shot_duration_s': shot['duration_seconds'], 'slots': slots, 'cases': cases},
                 indent=1, ensure_ascii=False))
