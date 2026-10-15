"""CLI: python3 -m sourcing classes | acquire --job JOB.json --out DIR"""
import argparse
import json
import sys

from .acquire import run
from .classes import ranked
from .errors import FailClosed


def main(argv=None):
    p = argparse.ArgumentParser(prog='sourcing')
    sub = p.add_subparsers(dest='cmd', required=True)
    sub.add_parser('classes', help='print the ranked source-class registry')
    a = sub.add_parser('acquire', help='run one tier-A acquisition job')
    a.add_argument('--job', required=True)
    a.add_argument('--out', required=True)
    args = p.parse_args(argv)
    if args.cmd == 'classes':
        for rank, cid, rec in ranked():
            print(f'{rank}. [{rec["tier"]}] {cid} (anime relevance {rec["anime_relevance"]}/5): {rec["name"]}')
        return 0
    try:
        print(json.dumps(run(args.job, args.out), indent=2))
        return 0
    except FailClosed as e:
        print(json.dumps({'status': 'FAIL_CLOSED', 'code': e.code, 'detail': e.detail}, indent=2))
        return 2


if __name__ == '__main__':
    sys.exit(main())
