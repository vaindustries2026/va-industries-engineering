"""CLI: python3 -m agent008 --asset-dir DIR --out-dir DIR [--readiness-manifest-id ID ...]"""
import argparse
import json
import sys
from pathlib import Path

from .config import load_output_spec
from .errors import FailClosed
from .inputs import load_hash_pins, load_snapshot
from .render import run
from .standin import LAYOUT_DIR, load_layout

HERE = Path(__file__).resolve().parent


def main(argv=None):
    ap = argparse.ArgumentParser(prog='agent008')
    ap.add_argument('--readiness-manifest-id', required=True, help='exact id; no latest-approved lookup exists')
    ap.add_argument('--production-manifest-id', required=True)
    ap.add_argument('--agent006-run-id', required=True)
    ap.add_argument('--snapshot', default=str(HERE / 'inputs' / 'ep005_phase0_input_snapshot.json'))
    ap.add_argument('--hash-pins', default=str(HERE / 'inputs' / 'hash_pins.json'))
    ap.add_argument('--layout', default=str(LAYOUT_DIR / 'ep005_s004_s005_standin_v1.json'))
    ap.add_argument('--output-spec', default=None)
    ap.add_argument('--asset-dir', required=True, help='local copies of the approved storage objects')
    ap.add_argument('--out-dir', required=True)
    a = ap.parse_args(argv)
    ids = {'readiness_manifest_id': a.readiness_manifest_id, 'production_manifest_id': a.production_manifest_id,
           'agent006_run_id': a.agent006_run_id}
    try:
        prov = run(load_snapshot(a.snapshot), a.snapshot, load_hash_pins(a.hash_pins), load_layout(a.layout),
                   a.layout, load_output_spec(a.output_spec), ids, a.asset_dir, a.out_dir)
    except FailClosed as e:
        print(json.dumps({'status': 'FAIL_CLOSED', 'code': e.code, 'detail': e.detail}))
        return 2
    o = prov['outputs']
    print(json.dumps({'status': prov['status'], 'review_mp4_sha256': o['review_mp4']['sha256'],
                      'mix_wav_sha256': o['mix_wav']['sha256'], 'frames': prov['raw_frames']['count'],
                      'deterministic_core_sha256': prov['deterministic_core_sha256']}, indent=1))
    return 0


if __name__ == '__main__':
    sys.exit(main())
