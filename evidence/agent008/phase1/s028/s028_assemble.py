"""S028 final-shot assembly (Agent-008 compose_motion_shot) from approved inputs only. No provider calls, no generation.

Usage (repo root): python3 evidence/agent008/phase1/s028/s028_assemble.py <work_dir> <render_label>
Reads the five approved inputs from V&A production storage (GET), verifies each SHA-256 against its APPROVED registry row,
builds the S028 spec from the approved v05 lineage (readiness 69bff641), and composes once into <work_dir>/<render_label>.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from agent008.config import load_output_spec  # noqa: E402
from agent008.episode import PINS, resolve_episode  # noqa: E402
from agent008.hashing import sha256_file  # noqa: E402
from agent008.inputs import load_hash_pins  # noqa: E402
from agent008.motion.compose import compose_motion_shot  # noqa: E402
from agent008.motion.contracts import MotionRequest, MotionResult  # noqa: E402
from agent008.motion.http import UrllibHttpClient  # noqa: E402
from agent008.tools.snapshot_inputs import build_snapshot  # noqa: E402

SB = 'https://ziluiwrwwbayhcskeere.supabase.co'
D = ROOT / 'evidence/agent008/phase1/s028'
READINESS = '69bff641-e056-4701-a23f-d91dbc2039b2'
INPUTS = {
    'MOTION-EP005-S028-SEEDANCE20-CAND-v01': '341683c40de8d71ebed564b7739f9b338add2f954d00e347e0561c7fbe7a9b58',
    'DLG-EP005-S028-LUMI-v01': '970f55a95f73f0949be74c5d5424318811d5fa2add0438abd42e3f37f639a8bc',
    'DLG-EP005-S028-MIKKO-v01': 'ab81173ee7ddb15eeb8b3bbb0bdd7eed6840d76f9100d5edb1e6ca5d04b230b0',
    'AMB-BATHROOM-QUIET-v01': 'ea28fad468e353b99d48070d12853620f08e8b05c8d912706122d31176544d2f',
    'FOLEY-CLOTH-SOFT-v01': '11fe4284b8540f84dc693f1b5ec9282123a930dfcb9f9209a6bc5c86cb00682f',
}
FOLEY_FRAME = 62                                   # first frame with the cloth released from Mikko's paw into Lumi's hold
TIMING = {
    'beds': {'AMB-BATHROOM-QUIET-v01': {'gain_db': 0.0}},
    'named': {'FOLEY-CLOTH-SOFT-v01': {'start_seconds': FOLEY_FRAME / 24, 'gain_db': float(sys.argv[3]) if len(sys.argv) > 3 else -12.0}},
    'dialogue': [
        {'shot_id': 'S028', 'speaker': 'Lumi', 'text': 'You look comfy. Story time.', 'audio_asset_id': 'DLG-EP005-S028-LUMI-v01',
         'expected_sha256': INPUTS['DLG-EP005-S028-LUMI-v01'], 'registry_status': None, 'start_seconds': 0.25, 'gain_db': 15.0},
        {'shot_id': 'S028', 'speaker': 'Mikko', 'text': 'I’m ready to rest.', 'audio_asset_id': 'DLG-EP005-S028-MIKKO-v01',
         'expected_sha256': INPUTS['DLG-EP005-S028-MIKKO-v01'], 'registry_status': None, 'start_seconds': 2.804187, 'gain_db': -4.0}],
    'dialogue_window': {'pre_hold_seconds': 0.25},
}

work, label = Path(sys.argv[1]), sys.argv[2]
http = UrllibHttpClient()
src = work / 'inputs'
src.mkdir(parents=True, exist_ok=True)
paths, registry = {}, {}
for aid, want in INPUTS.items():
    r = http.send('GET', f'{SB}/rest/v1/asset_registry?asset_id=eq.{aid}&select=*', {'Accept': 'application/json'})
    rows = json.loads(r.body)
    if r.status != 200 or len(rows) != 1 or rows[0]['status'] not in ('APPROVED', 'LOCKED'):
        sys.exit(f'STOP: {aid} not exactly one APPROVED/LOCKED registry row')
    row = rows[0]
    if (row.get('metadata_json') or {}).get('sha256') != want:
        sys.exit(f'STOP: {aid} governed sha differs')
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
    registry[aid] = {'registry_id': row['id'], 'status': row['status'], 'asset_type': row['asset_type'], 'asset_subtype': row['asset_subtype'],
                     'storage_path': row['storage_path'], 'sha256': want,
                     'human_decision': (row.get('metadata_json') or {}).get('human_decision')}
for t in TIMING['dialogue']:
    t['registry_status'] = registry[t['audio_asset_id']]['status']

mr = json.loads((D / 'S028_MOTION_RESULT_v1.json').read_text())
req = MotionRequest(**{k: v for k, v in mr['reservation']['request'].items() if k not in ('prompt_sha256', 'negative_constraints_sha256')})
res = MotionResult(**{**mr['result'], 'raw_output_path': str(paths['MOTION-EP005-S028-SEEDANCE20-CAND-v01'])})
spec = load_output_spec()
snap = build_snapshot(READINESS)
spec_shot = {r['shot_id']: r for r in resolve_episode(snap, load_hash_pins(PINS), spec)}['S028']['spec']
asset_paths = {k: paths[k] for k in INPUTS if k != 'MOTION-EP005-S028-SEEDANCE20-CAND-v01'}
out = work / label
prov = compose_motion_shot(res, req, spec_shot, spec, asset_paths, TIMING, out)
summary = {'label': label, 'inputs': registry, 'timing': TIMING, 'foley_frame': FOLEY_FRAME, 'outputs': prov['outputs'], 'qc': prov['qc'],
           'audio_cues': prov['audio_cues'], 'dialogue_tracks': prov['dialogue_tracks'], 'dialogue_timing': prov['dialogue_timing'],
           'mix_peak_dbfs': prov['mix_peak_dbfs'], 'deterministic_core_sha256': prov['deterministic_core_sha256'],
           'sources_after_sha256': {k: sha256_file(p) for k, p in paths.items()}}
(out / 'ASSEMBLY_SUMMARY.json').write_text(json.dumps(summary, indent=1, default=str, ensure_ascii=False))
print(json.dumps({k: summary[k] for k in ('label', 'outputs', 'mix_peak_dbfs', 'deterministic_core_sha256')}, indent=1))
print('QC', summary['qc']['automatic_result'], summary['qc']['issues'], summary['qc']['output_frames'], summary['qc']['output_resolution'],
      summary['qc']['output_duration_s'])
print('cues', [(c['asset_id'], c['kind'], round(c['start_s'], 6), round(c['end_s'], 6), c['gain_db']) for c in summary['audio_cues']])
