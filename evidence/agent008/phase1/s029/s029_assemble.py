"""S029 final-shot assembly (Agent-008 G02 compose_still_shot) from approved inputs only. No provider calls, no generation.

Usage (repo root): python3 evidence/agent008/phase1/s029/s029_assemble.py <work_dir> <render_label>
Reads the approved S029 base frame and the AMBIENCE bed from V&A production storage (GET), verifies each SHA-256 against its
APPROVED registry row, builds the S029 spec from the approved v05 lineage (readiness 69bff641), and composes once into
<work_dir>/<render_label>. Human decisions (2026-10-12): static held pose approved, minimal breathing omitted,
cloth-location continuity exception (MIKKO_SHOULDER_IN_LUMI_HAND) for S029 only.
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
from agent008.motion.http import UrllibHttpClient  # noqa: E402
from agent008.still import compose_still_shot  # noqa: E402
from agent008.tools.snapshot_inputs import build_snapshot  # noqa: E402

SB = 'https://ziluiwrwwbayhcskeere.supabase.co'
READINESS = '69bff641-e056-4701-a23f-d91dbc2039b2'
FRAME_ID = 'FRAME-EP005-S029-BASE-CAND-v01'
INPUTS = {
    FRAME_ID: 'a8b0d0fc597d9ad009fe96745485e89c2bae5d8764734a0cdec5ca00f7b023e4',
    'AMB-BATHROOM-QUIET-v01': 'ea28fad468e353b99d48070d12853620f08e8b05c8d912706122d31176544d2f',
}
TIMING = {'beds': {'AMB-BATHROOM-QUIET-v01': {'gain_db': 0.0}}}


def fetch_inputs(work):
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
        registry[aid] = {'registry_id': row['id'], 'status': row['status'], 'asset_type': row['asset_type'],
                         'asset_subtype': row['asset_subtype'], 'storage_path': row['storage_path'], 'sha256': want,
                         'human_decision': (row.get('metadata_json') or {}).get('human_decision')}
    return paths, registry


def s029_spec():
    spec = load_output_spec()
    snap = build_snapshot(READINESS)
    return spec, {r['shot_id']: r for r in resolve_episode(snap, load_hash_pins(PINS), spec)}['S029']['spec']


if __name__ == '__main__':
    work, label = Path(sys.argv[1]), sys.argv[2]
    paths, registry = fetch_inputs(work)
    spec, spec_shot = s029_spec()
    frame = {'asset_id': FRAME_ID, 'registry_id': registry[FRAME_ID]['registry_id'],
             'classification': f"{registry[FRAME_ID]['asset_type']}/{registry[FRAME_ID]['asset_subtype']}",
             'registry_status': registry[FRAME_ID]['status'], 'shot_id': 'S029', 'path': str(paths[FRAME_ID]),
             'expected_sha256': INPUTS[FRAME_ID]}
    asset_paths = {'AMB-BATHROOM-QUIET-v01': paths['AMB-BATHROOM-QUIET-v01']}
    out = work / label
    prov = compose_still_shot(spec_shot, frame, spec, asset_paths, TIMING, out)
    summary = {'label': label, 'inputs': registry, 'timing': TIMING, 'outputs': prov['outputs'], 'qc': prov['qc'],
               'layout': prov['layout'], 'audio_cues': prov['audio_cues'], 'dialogue_tracks': prov['dialogue_tracks'],
               'dialogue_timing': prov['dialogue_timing'], 'mix_peak_dbfs': prov['mix_peak_dbfs'],
               'deterministic_core_sha256': prov['deterministic_core_sha256'],
               'sources_after_sha256': {k: sha256_file(p) for k, p in paths.items()}}
    (out / 'ASSEMBLY_SUMMARY.json').write_text(json.dumps(summary, indent=1, default=str, ensure_ascii=False))
    print(json.dumps({k: summary[k] for k in ('label', 'outputs', 'mix_peak_dbfs', 'deterministic_core_sha256')}, indent=1))
    print('QC', summary['qc']['automatic_result'], summary['qc']['issues'], summary['qc']['output_frames'],
          summary['qc']['output_resolution'], summary['qc']['output_duration_s'])
    print('cues', [(c['asset_id'], c['kind'], round(c['start_s'], 6), round(c['end_s'], 6), c['gain_db']) for c in summary['audio_cues']])
