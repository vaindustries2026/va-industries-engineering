"""G03 two-run determinism proof on synthetic fixtures (no network, no provider, no production asset).

Usage (repo root): python3 evidence/agent008/g03/g03_determinism_proof.py <work_dir> <out_json>
Builds the test_g03 fixture (480x270 base frame, three RGBA overlays, four placements incl. one mirrored REFLECTION and
a rotated variant), runs place_overlays twice into separate directories, then feeds each G03 frame through the G02
still path, and compares exact SHA-256s.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from agent008.hashing import sha256_file  # noqa: E402
from agent008.overlay import place_overlays  # noqa: E402
from agent008.still import compose_still_shot  # noqa: E402
from agent008.tests import test_g03 as T  # noqa: E402

work, out_json = Path(sys.argv[1]), Path(sys.argv[2])
work.mkdir(parents=True, exist_ok=False)
T._G03.setUpClass()
fx = T._G03('setUp')
fx.setUp()
fx.tmp = work                                     # place outputs under the proof work dir
res = {}
for variant, placements in (('straight', fx.placements), ('rotated', [{**p, 'rotation_deg': 17.5} for p in fx.placements])):
    runs = []
    for run in ('run1', 'run2'):
        prov = place_overlays(fx.spec, fx.frame, fx.ov_paths, fx.record(placements), work / variant / run)
        png = work / variant / run / prov['output']['file']
        T._wav(work / 'amb.wav', 2.0, 0, 0.003)
        frame = {**fx.frame, 'asset_id': 'TEST-G03-FRAME', 'classification': 'SHOT_FRAME/DERIVED_FRAME', 'path': str(png),
                 'expected_sha256': prov['output']['sha256'], 'overlays_composited': prov['overlays_composited']}
        st = compose_still_shot(fx.spec, frame, T.SMALL, {'AMB-BATHROOM-QUIET-v01': work / 'amb.wav'}, {},
                                work / variant / run / 'still')
        runs.append({'png_sha256': sha256_file(png), 'rgb24_sha256': prov['output']['rgb24_sha256'],
                     'core_sha256': prov['deterministic_core_sha256'], 'placement_record_sha256': prov['placement_record']['sha256'],
                     'still_mp4_sha256': st['outputs']['review_mp4']['sha256'], 'still_wav_sha256': st['outputs']['mix_wav']['sha256'],
                     'still_core_sha256': st['deterministic_core_sha256']})
    res[variant] = {'runs': runs, 'identical': runs[0] == runs[1]}
res['base_frame_sha256_after'] = sha256_file(fx.base)
res['base_frame_unchanged'] = res['base_frame_sha256_after'] == fx.frame['expected_sha256']
res['overlays_unchanged'] = all(sha256_file(p) == o['expected_sha256'] for p, o in zip(fx.ov_paths.values(), fx.spec['active_overlays']))
res['result'] = 'PASS' if all(res[v]['identical'] for v in ('straight', 'rotated')) and res['base_frame_unchanged'] \
    and res['overlays_unchanged'] else 'FAIL'
out_json.write_text(json.dumps(res, indent=1))
print(json.dumps(res, indent=1))
