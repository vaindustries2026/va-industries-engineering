"""S027 final-shot assembly (Agent-008 8D/8F) with the approved dialogue. No provider calls, no generation.

Usage (repo root): python3 evidence/agent008/phase1/s027_v2/stage4_assemble_s027.py <work_dir> <render_label>
Reads the four approved inputs from V&A production storage (GET), verifies every SHA-256 against the registry
(or committed hash pin), and runs compose_motion_shot once with the Company-Brain-accepted timing.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from agent008.config import load_output_spec  # noqa: E402
from agent008.hashing import sha256_file  # noqa: E402
from agent008.inputs import load_hash_pins, load_snapshot, validate_readiness  # noqa: E402
from agent008.motion.compose import compose_motion_shot  # noqa: E402
from agent008.motion.contracts import MotionRequest, MotionResult  # noqa: E402
from agent008.motion.http import UrllibHttpClient  # noqa: E402
from agent008.resolve import Resolver  # noqa: E402
from agent008.spec import build_shot_spec  # noqa: E402

SB = 'https://ziluiwrwwbayhcskeere.supabase.co'
D = ROOT / 'evidence/agent008/phase1/s027_v2'
INPUTS = {   # asset_id -> expected sha256 (Company Brain task) ; verified again against the live registry / pin below
    'MOTION-EP005-S027-SEEDANCE20-CAND-v01': '86dddea5a37cbe5b35a5c7540e0914ebebb1abcf1365cbc778b47ffc0b450e25',
    'DLG-EP005-S027-L1-MIKKO-v01': '81a0b038e0e81114f88079dd3f42aeafbbe47ba39cb8e8a706933e6ba531da50',
    'AMB-BATHROOM-QUIET-v01': 'ea28fad468e353b99d48070d12853620f08e8b05c8d912706122d31176544d2f',
    'SFX-WIN-SPARKLE-CHORD': '84e0d57cf17a170af66dfb31ade4d647f6077cbbe13eb2fd87be6ae6f0c5bd9b',
}
TIMING = {
    'beds': {'AMB-BATHROOM-QUIET-v01': {'gain_db': 0.0}},
    'named': {'SFX-WIN-SPARKLE-CHORD': {'start_seconds': 46 / 24, 'gain_db': -10.0, 'fade_out_seconds': 1.0,
                                        'fade_complete_by_seconds': 5.0}},
    'dialogue': [{'shot_id': 'S027', 'speaker': 'Mikko', 'text': 'We did it! I feel fresh.',
                  'audio_asset_id': 'DLG-EP005-S027-L1-MIKKO-v01',
                  'expected_sha256': INPUTS['DLG-EP005-S027-L1-MIKKO-v01'], 'registry_status': None,
                  'start_seconds': 0.5, 'gain_db': 0.0}],
}

work, label = Path(sys.argv[1]), sys.argv[2]
http = UrllibHttpClient()
src = work / 'inputs'
src.mkdir(parents=True, exist_ok=True)
pins = load_hash_pins(ROOT / 'agent008/inputs/hash_pins.json')
paths, registry = {}, {}
for aid, want in INPUTS.items():
    r = http.send('GET', f'{SB}/rest/v1/asset_registry?asset_id=eq.{aid}&select=*', {'Accept': 'application/json'})
    rows = json.loads(r.body)
    if r.status != 200 or len(rows) != 1 or rows[0]['status'] not in ('APPROVED', 'LOCKED'):
        sys.exit(f'STOP: {aid} not exactly one APPROVED/LOCKED registry row')
    row = rows[0]
    gov = (row.get('metadata_json') or {}).get('sha256') or pins.get(aid, {}).get('sha256')
    if gov != want:
        sys.exit(f'STOP: {aid} governed sha {gov} != {want}')
    key = row['storage_path'].split('production-assets/', 1)[1]
    p = src / Path(key).name
    if not p.exists():
        g = http.send('GET', f'{SB}/storage/v1/object/authenticated/production-assets/{key}', {})
        if g.status != 200:
            sys.exit(f'STOP: storage read {aid} HTTP {g.status}')
        p.write_bytes(g.body)
    if sha256_file(p) != want:
        sys.exit(f'STOP: {aid} stored bytes sha differs')
    paths[aid] = p
    registry[aid] = {'registry_id': row['id'], 'status': row['status'], 'asset_type': row['asset_type'],
                     'asset_subtype': row['asset_subtype'], 'storage_path': row['storage_path'], 'sha256': want,
                     'sha256_source': 'asset_registry.metadata_json.sha256' if (row.get('metadata_json') or {}).get('sha256')
                     else 'agent008/inputs/hash_pins.json'}
TIMING['dialogue'][0]['registry_status'] = registry['DLG-EP005-S027-L1-MIKKO-v01']['status']

mr = json.loads((D / 'S027_MOTION_RESULT_v1.json').read_text())
req = MotionRequest(**{k: v for k, v in mr['reservation']['request'].items()
                       if k not in ('prompt_sha256', 'negative_constraints_sha256')})
res = MotionResult(**{**mr['result'], 'raw_output_path': str(paths['MOTION-EP005-S027-SEEDANCE20-CAND-v01'])})
spec = load_output_spec()
snap = load_snapshot(ROOT / 'agent008/inputs/ep005_motion_s027_input_snapshot.json')
rd = validate_readiness(snap, 'edc4ad58-3e5d-4ac2-9c74-c9af03af363f', '45cc7493-80b4-4e8d-b71d-fbd7fd3656ed',
                        'A006-1791346204213')
spec_shot = build_shot_spec(snap, Resolver(rd, snap['asset_registry'], pins), 'S027', spec, motion_phase=True)
asset_paths = {k: paths[k] for k in ('AMB-BATHROOM-QUIET-v01', 'SFX-WIN-SPARKLE-CHORD', 'DLG-EP005-S027-L1-MIKKO-v01')}
out = work / label
prov = compose_motion_shot(res, req, spec_shot, spec, asset_paths, TIMING, out)
summary = {'label': label, 'inputs': registry, 'timing': TIMING, 'outputs': prov['outputs'], 'qc': prov['qc'],
           'audio_cues': prov['audio_cues'], 'dialogue_tracks': prov['dialogue_tracks'],
           'deterministic_core_sha256': prov['deterministic_core_sha256'],
           'raw_after_sha256': sha256_file(paths['MOTION-EP005-S027-SEEDANCE20-CAND-v01'])}
(out / 'ASSEMBLY_SUMMARY.json').write_text(json.dumps(summary, indent=1, default=str))
print(json.dumps({k: summary[k] for k in ('label', 'outputs', 'deterministic_core_sha256', 'raw_after_sha256')}, indent=1))
print('QC', summary['qc']['automatic_result'], summary['qc']['issues'], summary['qc']['output_frames'],
      summary['qc']['output_resolution'], summary['qc']['output_duration_s'])
