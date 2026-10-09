"""S027 motion, Steps 3-4: freeze the exact request body and run the final spend gate. No provider writes.

Usage (repo root): python3 evidence/agent008/phase1/s027_v2/stage2_freeze_and_gate.py <work_dir>
"""
import hashlib
import json
import math
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from agent008.inputs import load_hash_pins, load_snapshot  # noqa: E402
from agent008.motion.authorisation import AttemptLedger, SpendAuthorisation  # noqa: E402
from agent008.motion.contracts import MotionRequest  # noqa: E402
from agent008.motion.higgsfield import HiggsfieldProvider  # noqa: E402
from agent008.motion.higgsfield_transport import HiggsfieldApiTransport, resolve_model, serialize_request  # noqa: E402
from agent008.motion.preflight import preflight  # noqa: E402
from agent008.motion.runner import validate_pre_generation  # noqa: E402

FRAME_SHA = '81b841a6ab53219b26755c4e83a9777953a2d03f37213875e38691c112f0061b'
PROMPT_SHA = 'ab7f92afa5d7a8bde2efc621eb86ebe249614762b66e15576ec0b5d9c3f4cab3'
MODEL = 'bytedance/seedance-2.0/image-to-video'
SCOPE_GEN = 'S027-MOTION-SEEDANCE20-1'
MAX_COST = 3.50
D = ROOT / 'evidence/agent008/phase1/s027_v2'
work = Path(sys.argv[1])
job = json.loads((ROOT / 'agent008/motion/jobs/ep005_s027_motion_smoke_v2.json').read_text())
up = json.loads((D / 'S027_SOURCE_UPLOAD_v1.json').read_text())
ledger = AttemptLedger(D / 'S027_MOTION_LEDGER_v1.jsonl')
source_upload = {**up['step2_upload'], 'readback': 'SHA256_MATCH'}
assert up['step2_readback']['sha256'] == FRAME_SHA and source_upload['sha256'] == FRAME_SHA

frame = str(work / 'FRAME-EP005-S027-BASE-v01.png')
req = MotionRequest('S027', frame, FRAME_SHA, job['motion_prompt'], '', 5, '16:9', '1080p', 24, 'higgsfield', MODEL,
                    SCOPE_GEN, source_frame_url=source_upload['public_url'])
transport = HiggsfieldApiTransport()
provider = HiggsfieldProvider(transport=transport)
mid, rec = resolve_model(transport.cfg, MODEL)
body = serialize_request(req, rec, source_upload['public_url'])
wire = json.dumps(body, separators=(',', ':')).encode()      # exactly what HiggsfieldApiTransport._api sends
expected = {'prompt': job['motion_prompt'], 'image_url': source_upload['public_url'], 'duration': 5, 'resolution': '1080p',
            'generate_audio': False}
problems = []
if body != expected: problems.append('BODY_NOT_EXACTLY_APPROVED_FIELDS')
if hashlib.sha256(body['prompt'].encode()).hexdigest() != PROMPT_SHA: problems.append('PROMPT_SHA')
if req.prompt_sha256 != PROMPT_SHA: problems.append('REQ_PROMPT_SHA')
if 'negative_prompt' in body: problems.append('NEGATIVE_PROMPT_FIELD')
auth = SpendAuthorisation(SCOPE_GEN, 'Gilang / Company Brain', 'HIGGSFIELD', MODEL, 'S027', FRAME_SHA, PROMPT_SHA,
                          max_generations=1, no_auto_retry=True, human_approved=True)
cost = {w_h: round(math.ceil(5 * w_h[0] * w_h[1] * 24 / 1024) / 1000 * 0.014, 4) for w_h in [(1920, 1080), (1920, 1088)]}
if max(cost.values()) > MAX_COST: problems.append('EXPECTED_COST_ABOVE_CEILING')
snap = load_snapshot(ROOT / 'agent008/inputs/ep005_motion_s027_input_snapshot.json')
approval = {'sha256': FRAME_SHA, 'status': 'APPROVED', 'asset_registry_id': 'd2a07b22-cf25-42ff-b86a-c4080ff24bc2'}
pf = preflight(job, snap, load_hash_pins(ROOT / 'agent008/inputs/hash_pins.json'), frame, approval, provider, ledger,
               SCOPE_GEN, source_upload=source_upload, authorisation=auth)
if pf['blockers']: problems.append('PREFLIGHT_BLOCKERS:' + ','.join(pf['blockers']))
checks = validate_pre_generation(req, provider, auth, ledger, snap, approval, source_upload)
auth.matches(req)
gate = {
    'final_request_body': body,
    'final_request_body_wire_bytes': len(wire),
    'FINAL_REQUEST_BODY_SHA256': hashlib.sha256(wire).hexdigest(),
    'body_serialisation': "json.dumps(body, separators=(',', ':')) - identical to HiggsfieldApiTransport._api",
    'endpoint': transport.base + rec['endpoint'],
    'spend_authorisation': {**asdict(auth), 'maximum_authorised_cost_usd': MAX_COST},
    'expected_cost_usd_by_output_size': {f'{w}x{h}': c for (w, h), c in cost.items()},
    'preflight': pf,
    'runner_validate_pre_generation': checks,
    'generation_attempts_so_far': ledger.attempts(SCOPE_GEN),
    'problems': problems,
    'gate': 'PASS' if not problems else 'STOP',
}
(D / 'S027_FINAL_GATE_v1.json').write_text(json.dumps(gate, indent=1, default=str))
print(json.dumps({k: v for k, v in gate.items() if k not in ('final_request_body', 'preflight')}, indent=1, default=str))
print('preflight blockers:', pf['blockers'])
