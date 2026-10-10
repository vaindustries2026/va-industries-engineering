#!/usr/bin/env python3
"""AGENT-008 v0.1: read-only input snapshot.

Fetches, with HTTP GET only, the exact readiness manifest, its production
manifest and the governed asset registry, then writes a reduced, hashed
snapshot that the deterministic compositor consumes offline.

Credentials are never read or written by this script: requests go to the
Supabase REST host through the environment's authenticating proxy.

Usage:
  python3 agent008/tools/snapshot_inputs.py \
      --readiness-manifest-id edc4ad58-3e5d-4ac2-9c74-c9af03af363f \
      --shots S004,S005 --validator-shots S025 \
      --out agent008/inputs/ep005_phase0_input_snapshot.json
  Omit --shots to snapshot every shot of the approved manifest (used by agent008.episode).
"""
import argparse
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from agent008.hashing import canonical_sha256  # noqa: E402

REST = 'https://ziluiwrwwbayhcskeere.supabase.co/rest/v1'

MANIFEST_KEYS = ('compositing_treatments', 'audio_asset_mappings', 'audio_workload',
                 'generation_workload', 'manifest_version', 'readiness_flags', 'episode')


def get(table, **params):
    url = f'{REST}/{table}?' + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, method='GET', headers={'Accept': 'application/json'})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def build_snapshot(readiness_manifest_id, shots=None, validator_shots=(), fetch=get):
    """Read-only snapshot of the exact approved state. shots=None means every shot in the manifest.

    The snapshot is derived from the live rows each time; it is never edited by hand.
    """
    rows = fetch('production_readiness_manifests', id=f'eq.{readiness_manifest_id}')
    if len(rows) != 1:
        raise SystemExit(f'FAIL_CLOSED: readiness manifest {readiness_manifest_id} returned {len(rows)} rows')
    readiness = rows[0]
    pm_rows = fetch('episode_production_manifests', id=f"eq.{readiness['production_manifest_id']}")
    if len(pm_rows) != 1:
        raise SystemExit('FAIL_CLOSED: production manifest not found exactly once')
    pm = pm_rows[0]
    registry = fetch('asset_registry', order='asset_id')

    m = pm['manifest_json']
    all_ids = [s['shot_id'] for s in m['shot_plans']]
    if shots is None:
        shots = all_ids
        if len(all_ids) != pm.get('shot_count'):
            raise SystemExit(f"FAIL_CLOSED: manifest shot_plans {len(all_ids)} != shot_count {pm.get('shot_count')}")
    vshots = list(validator_shots)
    wanted = set(shots) | set(vshots)
    reduced = {k: m.get(k) for k in MANIFEST_KEYS}
    reduced['shot_plans'] = [s for s in m['shot_plans'] if s['shot_id'] in wanted]
    missing = wanted - {s['shot_id'] for s in reduced['shot_plans']}
    if missing:
        raise SystemExit(f'FAIL_CLOSED: shots not in manifest: {sorted(missing)}')

    return {
        'snapshot_version': 'agent008-input-snapshot-v1',
        'method': 'HTTP GET only (read-only); reduced copy of the live rows',
        'render_shots': list(shots),
        'validator_only_shots': vshots,
        'readiness_manifest': readiness,
        'readiness_manifest_json_canonical_sha256': canonical_sha256(readiness['readiness_manifest_json']),
        'production_manifest': {
            'id': pm['id'], 'status': pm['status'],
            'production_plan_run_id': pm['production_plan_run_id'],
            'episode_code': pm['episode_code'],
            'shot_count': pm.get('shot_count'),
            'manifest_json_canonical_sha256': canonical_sha256(m),
            'manifest_json_reduced': reduced,
        },
        'asset_registry': registry,
        'asset_registry_canonical_sha256': canonical_sha256(registry),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--readiness-manifest-id', required=True)
    ap.add_argument('--shots', help='comma-separated subset; omit (or ALL) for every shot in the manifest')
    ap.add_argument('--validator-shots', default='')
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    shots = None if not a.shots or a.shots == 'ALL' else [s for s in a.shots.split(',') if s]
    vshots = [s for s in a.validator_shots.split(',') if s]
    snap = build_snapshot(a.readiness_manifest_id, shots, vshots)
    Path(a.out).write_text(json.dumps(snap, indent=1, ensure_ascii=False, sort_keys=True) + '\n')
    print('wrote', a.out)
    print('production manifest canonical sha256', snap['production_manifest']['manifest_json_canonical_sha256'])
    print('readiness json canonical sha256', snap['readiness_manifest_json_canonical_sha256'])


if __name__ == '__main__':
    main()
