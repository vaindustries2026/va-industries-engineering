"""Episode-wide shot specification: approved state -> one governed spec or one governed blocker per shot.

Every shot listed in the approved production manifest is accounted for. A shot that cannot be
specified is returned as an explicit BLOCKED entry carrying the FailClosed code, never dropped.

Usage (read-only; GETs the approved rows through the environment proxy):
  python3 -m agent008.episode --readiness-manifest-id edc4ad58-3e5d-4ac2-9c74-c9af03af363f
"""
import argparse
import json
import sys
from pathlib import Path

from .config import load_output_spec
from .errors import FailClosed
from .inputs import load_hash_pins, validate_readiness
from .resolve import Resolver
from .spec import build_shot_spec

PINS = Path(__file__).resolve().parent / 'inputs' / 'hash_pins.json'


def resolve_episode(snapshot, pins, output_spec, agent006_run_id=None):
    """Return [{'shot_id', 'status': 'SPEC'|'BLOCKED', 'spec' | 'blocker'}] in manifest order, one per shot."""
    pm = snapshot['production_manifest']
    shot_ids = [s['shot_id'] for s in pm['manifest_json_reduced']['shot_plans']]
    if pm.get('shot_count') is not None and len(shot_ids) != pm['shot_count']:
        raise FailClosed('EPISODE_SNAPSHOT_INCOMPLETE', f"{len(shot_ids)} of {pm['shot_count']} shots present")
    if len(set(shot_ids)) != len(shot_ids):
        raise FailClosed('EPISODE_DUPLICATE_SHOT_IDS', str(shot_ids))
    rd = validate_readiness(snapshot, snapshot['readiness_manifest']['id'], pm['id'], agent006_run_id)
    resolver = Resolver(rd, snapshot['asset_registry'], pins)
    out = []
    for sid in shot_ids:
        try:
            out.append({'shot_id': sid, 'status': 'SPEC',
                        'spec': build_shot_spec(snapshot, resolver, sid, output_spec, motion_phase=True)})
        except FailClosed as e:
            out.append({'shot_id': sid, 'status': 'BLOCKED', 'blocker': {'code': e.code, 'detail': e.detail}})
    if [r['shot_id'] for r in out] != shot_ids:
        raise FailClosed('EPISODE_SHOT_LOST', 'resolution did not account for every manifest shot')
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--readiness-manifest-id', required=True)
    ap.add_argument('--capture-out', help='optional: also write the read-only snapshot used (evidence)')
    a = ap.parse_args()
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from agent008.tools.snapshot_inputs import build_snapshot
    snap = build_snapshot(a.readiness_manifest_id)
    if a.capture_out:
        Path(a.capture_out).write_text(json.dumps(snap, indent=1, ensure_ascii=False, sort_keys=True) + '\n')
    res = resolve_episode(snap, load_hash_pins(PINS), load_output_spec())
    for r in res:
        print(r['shot_id'], r['status'], r.get('blocker', {}).get('code', ''), r.get('blocker', {}).get('detail', ''))
    print('SPEC', sum(r['status'] == 'SPEC' for r in res), 'BLOCKED', sum(r['status'] == 'BLOCKED' for r in res),
          'of', len(res))


if __name__ == '__main__':
    main()
