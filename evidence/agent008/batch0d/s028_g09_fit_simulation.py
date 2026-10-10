"""S028 dialogue fit simulation through G09 with SYNTHETIC clips sized to the estimated takes (no TTS, no provider).

Usage (repo root): python3 evidence/agent008/batch0d/s028_g09_fit_simulation.py <scratch_dir>
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from agent008.config import load_output_spec  # noqa: E402
from agent008.dialogue_timing import govern_dialogue_timing  # noqa: E402
from agent008.episode import PINS, resolve_episode  # noqa: E402
from agent008.errors import FailClosed  # noqa: E402
from agent008.hashing import sha256_file  # noqa: E402
from agent008.inputs import load_hash_pins, load_snapshot  # noqa: E402
from agent008.motion.compose import resolve_dialogue  # noqa: E402

tmp = Path(sys.argv[1]); tmp.mkdir(parents=True, exist_ok=True)
spec = load_output_spec()
shot = {r['shot_id']: r for r in resolve_episode(load_snapshot(ROOT / 'agent008/tests/fixtures/ep005_approved_state_capture_v2.json'),
                                                 load_hash_pins(PINS), spec)}['S028']['spec']


def clip(name, seconds):
    p = tmp / f'{name}.wav'
    n = int(round(seconds * 48000))
    a = np.full((n, 2), 0.05)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'f64le', '-ar', '48000', '-ac', '2', '-i', '-', '-c:a', 'pcm_s24le', str(p)],
                   input=a.astype('<f8').tobytes(), check=True)
    return p


# file length = lead + speech + tail; lead/tail from measured takes (L1 audition 0.08/0.42 s; S027 M1 0.04/0.395 s)
SCENARIOS = {
 'L1_measured_rate': {'Lumi': 0.08 + 7 / 2.96 + 0.42, 'Mikko': 0.04 + 1.64 + 0.395},
 'slowest_estimate': {'Lumi': 0.08 + 7 / 2.63 + 0.42, 'Mikko': 0.04 + 1.84 + 0.395},
}
PLANS = {
 'sequential_pre0.25_gap0': {'pre_hold': 0.25, 'overlap': None},
 'sequential_pre0.25_authorised_silent_overlap_0.40': {'pre_hold': 0.25, 'overlap': 0.40},
}
out = {'shot': 'S028', 'duration_s': shot['duration_seconds'], 'slots': shot['dialogue_slots'], 'results': []}
for sn, lens in SCENARIOS.items():
    paths = {sp: clip(f'{sn}_{sp}', s) for sp, s in lens.items()}
    for pn, plan in PLANS.items():
        lumi_start = plan['pre_hold']
        mikko_start = lumi_start + lens['Lumi'] - (plan['overlap'] or 0.0)
        timing = {'dialogue': [{'shot_id': 'S028', 'speaker': sl['speaker'], 'text': sl['text'], 'audio_asset_id': f'SIM-{sl["speaker"]}',
                                'expected_sha256': sha256_file(paths[sl['speaker']]), 'registry_status': 'APPROVED',
                                'start_seconds': round(st, 6), 'gain_db': 0.0}
                               for sl, st in zip(shot['dialogue_slots'], (lumi_start, mikko_start))],
                  'dialogue_window': {'pre_hold_seconds': plan['pre_hold']}}
        if plan['overlap']:
            timing['dialogue_overlaps'] = [{'slots': [0, 1], 'max_overlap_seconds': plan['overlap'],
                                            'authorised_by': 'SIMULATION ONLY (not a human decision)'}]
        inputs = {f'SIM-{k}': v for k, v in paths.items()}
        res = {'scenario': sn, 'plan': pn, 'clip_seconds': {k: round(v, 3) for k, v in lens.items()}}
        try:
            rep = govern_dialogue_timing(shot, resolve_dialogue(shot, inputs, timing), inputs, timing, spec)
            res.update({'g09': 'PASS', 'lines': [(l['speaker'], l['start_s'], l['end_s']) for l in rep['lines']],
                        'tail_hold_s': rep['visual_holds']['after_last_line_s']})
        except FailClosed as e:
            res.update({'g09': 'FAIL_CLOSED', 'code': e.code, 'detail': e.detail})
        out['results'].append(res)
print(json.dumps(out, indent=1, ensure_ascii=False))
