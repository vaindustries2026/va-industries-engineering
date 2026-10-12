"""Pre/post-change regression proof: G02 still and v0.2 motion compose on synthetic fixtures (no overlays).

Usage (repo root): python3 evidence/agent008/g03/g03_regression_baseline.py <out_json>
Runs the existing G02 still path (TEST-S023 with a dialogue clip) and the v0.2 motion compositor (fake provider, S027
fixture) on the committed synthetic test fixtures, and records output SHAs and deterministic core SHAs. Run once on the
code before G03 integration and once after: equal values prove that shots without overlays are byte-unchanged.
No network, no provider, no production asset.
"""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from agent008.tests import test_batch0c as B  # noqa: E402
from agent008.tests import test_motion as M  # noqa: E402

out = {}


class Still(B.G02StillShot):
    def runTest(self):
        spec, track = self.with_dialogue()
        p = self.run_still('a', spec=spec, timing={'dialogue': [track]})
        out['g02_still'] = {'outputs': p['outputs'], 'core': p['deterministic_core_sha256'],
                            'qc_keys': sorted(p['qc']), 'source_frame_keys': sorted(p['source_frame']), 'keys': sorted(p)}


class Motion(M.ComposeFixture):
    def runTest(self):
        p = M.compose_motion_shot(self.result, self.req, self.spec_shot, M.SMALL, self.assets, self.timing, self.tmp / 'o')
        out['v02_motion'] = {'outputs': p['outputs'], 'core': p['deterministic_core_sha256'],
                             'qc_keys': sorted(p['qc']), 'keys': sorted(p)}


r = unittest.TextTestRunner(verbosity=0).run(unittest.TestSuite([Still(), Motion()]))
if not r.wasSuccessful():
    sys.exit('STOP: baseline run failed')
Path(sys.argv[1]).write_text(json.dumps(out, indent=1, sort_keys=True))
print(json.dumps({k: {'mp4': v['outputs']['review_mp4']['sha256'], 'core': v['core']} for k, v in out.items()}, indent=1))
