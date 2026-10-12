"""G08 two-run determinism proof per implemented treatment type (synthetic fixtures; no network, provider or production asset).

Usage (repo root): python3 evidence/agent008/g08/g08_determinism_proof.py <work_dir> <out_json>
Builds the test_g08 fixtures and runs each treatment twice from identical inputs into separate directories:
MIRROR_REFLECTION (COMPOSITE: new frame PNG; PRESERVE: certificate core), MIRROR_GLINT and COMPLETION_POP (G02 still MP4,
WAV and raw-frame hash list), and the G03 -> G08 chain. Records INPUT_SHA, OUTPUT_A_SHA, OUTPUT_B_SHA, DETERMINISM_PASS.
"""
import json
import sys
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from agent008 import g08  # noqa: E402
from agent008.g08 import apply_reflection  # noqa: E402
from agent008.hashing import sha256_file  # noqa: E402
from agent008.tests import test_g08 as T  # noqa: E402

work, out_json = Path(sys.argv[1]), Path(sys.argv[2])
work.mkdir(parents=True, exist_ok=False)
T._G08.setUpClass()
fx = T._G08('setUp')
with mock.patch.object(g08, 'GOVERNED', T.GOV):
    fx.setUp = T._Tmp.setUp.__get__(fx)
    T._Tmp.setUp(fx)
    fx.tmp = work
    (work / 'in').mkdir()
    T._base_png(work / 'in' / 'base.png')
    fx.base = work / 'in' / 'base.png'
    fx.ov = {}
    for i, aid in enumerate(T.OV):
        p = work / 'in' / f'{aid}.png'
        T._rgba_png(p, 120, 90, (30 + i, 20, 40, 30), (T.GREEN, T.GREEN))
        fx.ov[aid] = p
    for name, sec, f in (('chime', 0.4, 880), ('pop', 0.2, 660), ('amb', 2.0, 0)):
        T._wav(work / 'in' / f'{name}.wav', sec, f, 0.003 if f == 0 else 0.2)
    fx.audio = {'SFX-LUMI-CLUE-CHIME': work / 'in' / 'chime.wav', 'SFX-COMPLETION-POP-v01': work / 'in' / 'pop.wav',
                'AMB-BATHROOM-QUIET-v01': work / 'in' / 'amb.wav'}
    res = {}

    def row(name, inp, a, b):
        res[name] = {'INPUT_SHA': inp, 'OUTPUT_A_SHA': a, 'OUTPUT_B_SHA': b, 'DETERMINISM_PASS': a == b}

    # MIRROR_REFLECTION, COMPOSITE (new pixels)
    a = fx.s025(sub='refl_a')[3]
    b = fx.s025(sub='refl_b')[3]
    row('MIRROR_REFLECTION_COMPOSITE (frame png)', a['source_frame']['verified_sha256'], a['output']['sha256'], b['output']['sha256'])
    row('MIRROR_REFLECTION_COMPOSITE (provenance core)', a['treatment_record']['sha256'], a['deterministic_core_sha256'],
        b['deterministic_core_sha256'])
    # MIRROR_REFLECTION, PRESERVE (certificate on the unchanged frame)
    pa = fx.s025(sub='pres_a', mode='PRESERVE')[3]
    pb = fx.s025(sub='pres_b', mode='PRESERVE')[3]
    row('MIRROR_REFLECTION_PRESERVE (certificate core; frame unchanged)', pa['source_frame']['verified_sha256'],
        pa['deterministic_core_sha256'], pb['deterministic_core_sha256'])
    res['MIRROR_REFLECTION_PRESERVE (certificate core; frame unchanged)']['frame_unchanged'] = \
        pa['output']['sha256'] == pa['source_frame']['verified_sha256']
    # MIRROR_GLINT through the G02 still path (G03 frame input)
    spec, f, t, timing, _ = fx.s004()
    ga, gb = fx.still(spec, f, 'glint_a', timing, t), fx.still(spec, f, 'glint_b', timing, t)
    for k, label in (('review_mp4', 'mp4'), ('mix_wav', 'wav')):
        row(f'MIRROR_GLINT (still {label})', f['expected_sha256'], ga['outputs'][k]['sha256'], gb['outputs'][k]['sha256'])
    row('MIRROR_GLINT (raw frame hash list)', f['expected_sha256'], ga['qc']['frame_hash_list_sha256'], gb['qc']['frame_hash_list_sha256'])
    # COMPLETION_POP through the G02 still path (G08 reflection frame input)
    spec25, _, t25, _, held = fx.s025(sub='pop_src')
    tm = {'named': {'SFX-COMPLETION-POP-v01': {'start_seconds': 1.0, 'gain_db': -6.0}}}
    qa, qb = fx.still(spec25, held, 'pop_a', tm, t25), fx.still(spec25, held, 'pop_b', tm, t25)
    for k, label in (('review_mp4', 'mp4'), ('mix_wav', 'wav')):
        row(f'COMPLETION_POP (still {label})', held['expected_sha256'], qa['outputs'][k]['sha256'], qb['outputs'][k]['sha256'])
    row('COMPLETION_POP (raw frame hash list)', held['expected_sha256'], qa['qc']['frame_hash_list_sha256'], qb['qc']['frame_hash_list_sha256'])
    # G03 -> G08 chain (overlay frame -> composited reflection)
    spec7 = fx.spec('S007', overlays=1)
    chain = []
    for run in ('a', 'b'):
        g, gp = fx.g03(spec7, 'S007', [fx.pl('TEST-OVERLAY-CHEEK', 'FACE', 70, 90)], sub=f'chain_g03_{run}')
        r = fx.rec(spec7, g['expected_sha256'], reflection=fx.composite(['TEST-OVERLAY-CHEEK']))
        chain.append(apply_reflection(spec7, g, r, work / f'chain_g08_{run}', gp)['output']['sha256'])
    row('G03_THEN_G08_CHAIN (frame png)', sha256_file(fx.base), *chain)
    res['inputs_unchanged'] = sha256_file(fx.base) == pa['source_frame']['verified_sha256'] and \
        all(sha256_file(p) == o['expected_sha256'] for p, o in zip(fx.ov.values(), fx.spec('S004')['active_overlays']))
    res['result'] = 'PASS' if all(v['DETERMINISM_PASS'] for k, v in res.items() if isinstance(v, dict)) and res['inputs_unchanged'] \
        else 'FAIL'
out_json.write_text(json.dumps(res, indent=1))
print(json.dumps(res, indent=1))
