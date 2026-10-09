"""S027 motion, Steps 5-7: EXACTLY ONE Seedance 2.0 submit via Agent-008 run_once, read-only polling, raw retrieval.

Usage (repo root): python3 evidence/agent008/phase1/s027_v2/stage3_submit_once.py <work_dir>
Refuses to run if the ledger already holds any generation reservation for the scope, or if the body
re-serialised now differs from the frozen FINAL_REQUEST_BODY_SHA256.
"""
import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from agent008.errors import FailClosed  # noqa: E402
from agent008.motion.authorisation import AttemptLedger, SpendAuthorisation  # noqa: E402
from agent008.motion.contracts import MotionRequest  # noqa: E402
from agent008.motion.higgsfield import HiggsfieldProvider  # noqa: E402
from agent008.motion.higgsfield_transport import HiggsfieldApiTransport, resolve_model, serialize_request  # noqa: E402
from agent008.inputs import load_snapshot  # noqa: E402
from agent008.motion.runner import run_once  # noqa: E402

D = ROOT / 'evidence/agent008/phase1/s027_v2'
work = Path(sys.argv[1])
gate = json.loads((D / 'S027_FINAL_GATE_v1.json').read_text())
up = json.loads((D / 'S027_SOURCE_UPLOAD_v1.json').read_text())
sa = {k: v for k, v in gate['spend_authorisation'].items() if k != 'maximum_authorised_cost_usd'}
auth = SpendAuthorisation(**sa)
ledger = AttemptLedger(D / 'S027_MOTION_LEDGER_v1.jsonl')
if gate['gate'] != 'PASS' or ledger.attempts(auth.approval_scope_id) != 0:
    sys.exit('STOP: gate not PASS or a generation attempt already exists for this scope')
source_upload = {**up['step2_upload'], 'readback': 'SHA256_MATCH'}
job = json.loads((ROOT / 'agent008/motion/jobs/ep005_s027_motion_smoke_v2.json').read_text())
req = MotionRequest('S027', str(work / 'FRAME-EP005-S027-BASE-v01.png'), auth.source_frame_sha256, job['motion_prompt'], '',
                    5, '16:9', '1080p', 24, 'higgsfield', auth.provider_model, auth.approval_scope_id,
                    source_frame_url=source_upload['public_url'])
transport = HiggsfieldApiTransport()
_, rec = resolve_model(transport.cfg, auth.provider_model)
wire = json.dumps(serialize_request(req, rec, req.source_frame_url), separators=(',', ':')).encode()
if hashlib.sha256(wire).hexdigest() != gate['FINAL_REQUEST_BODY_SHA256']:
    sys.exit('STOP: body differs from frozen FINAL_REQUEST_BODY_SHA256')


class LoggedProvider(HiggsfieldProvider):
    """Records submit metadata and every read-only poll in the ledger. Behaviour otherwise unchanged."""

    def submit(self, request):
        rid = super().submit(request)
        r = self.transport.requests[rid]
        sent = json.dumps(r['payload'], separators=(',', ':')).encode()
        ledger.append('SUBMIT_ACCEPTED', auth.approval_scope_id, provider_request_id=rid, status_url=r['status_url'],
                      cancel_url=r['cancel_url'], initial_status=r['initial_status'],
                      sent_body_sha256=hashlib.sha256(sent).hexdigest())
        return rid

    def poll(self, rid):
        try:
            s = super().poll(rid)
        except FailClosed as e:
            ledger.append('POLL_STOP', auth.approval_scope_id, provider_request_id=rid, code=e.code, detail=str(e.detail)[:300])
            raise
        ledger.append('POLL', auth.approval_scope_id, provider_request_id=rid, status=s.get('provider_status'),
                      output_url=s.get('output_url'), usage=s.get('usage'), detail=s.get('detail'))
        return s

    def fetch(self, rid, dest):
        try:
            return super().fetch(rid, dest)
        except FailClosed as e:
            ledger.append('RETRIEVAL_STOP', auth.approval_scope_id, provider_request_id=rid, code=e.code,
                          detail=str(e.detail)[:300], output_url=self.transport.outputs.get(rid))
            raise


provider = LoggedProvider(transport=transport)
snap = load_snapshot(ROOT / 'agent008/inputs/ep005_motion_s027_input_snapshot.json')
approval = {'sha256': auth.source_frame_sha256, 'status': 'APPROVED'}
try:
    result = run_once(req, provider, auth, ledger, work / 'raw', snap, approval, poll_interval=10.0, max_polls=180,
                      source_upload=source_upload)
except FailClosed as e:
    print(json.dumps({'stopped': e.code, 'detail': str(e.detail)[:400], 'requests': {k: {kk: vv for kk, vv in v.items() if kk != 'payload'}
          for k, v in transport.requests.items()}, 'outputs': transport.outputs}, indent=1))
    sys.exit(2)
print(json.dumps({'result': result.to_dict(), 'output_url': transport.outputs}, indent=1, default=str))
