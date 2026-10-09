"""Offline Agent-008 preflight for the S027 v2 motion package. No network calls, no provider writes.

Usage (from repo root): python3 evidence/agent008/phase1/s027_v2/run_preflight_v2.py <verified_frame.png> <registry_row.json>
The frame bytes must be the ones read back from production storage; the registry row is the live GET of
asset_registry id d2a07b22-cf25-42ff-b86a-c4080ff24bc2.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from agent008.hashing import sha256_file  # noqa: E402
from agent008.inputs import load_hash_pins, load_snapshot  # noqa: E402
from agent008.motion.authorisation import AttemptLedger  # noqa: E402
from agent008.motion.contracts import MotionRequest  # noqa: E402
from agent008.motion.higgsfield import HiggsfieldProvider  # noqa: E402
from agent008.motion.higgsfield_transport import HiggsfieldApiTransport, resolve_model, serialize_request  # noqa: E402
from agent008.motion.preflight import preflight  # noqa: E402
from agent008.errors import FailClosed  # noqa: E402

frame, row_path = sys.argv[1], sys.argv[2]
job = json.loads((ROOT / 'agent008/motion/jobs/ep005_s027_motion_smoke_v2.json').read_text())
row = json.loads(Path(row_path).read_text())[0]
got = sha256_file(frame)
if got != job['approved_source_sha256'] or row['metadata_json']['sha256'] != got or row['status'] != 'APPROVED' \
        or row['asset_id'] != job['frame_id']:
    sys.exit(f'STOP: source frame verification failed ({got})')
approval = {'sha256': got, 'status': row['status'], 'asset_registry_id': row['id']}
transport = HiggsfieldApiTransport()
provider = HiggsfieldProvider(transport=transport)
rep = preflight(job, load_snapshot(ROOT / 'agent008/inputs/ep005_motion_s027_input_snapshot.json'),
                load_hash_pins(ROOT / 'agent008/inputs/hash_pins.json'), frame, approval, provider,
                AttemptLedger('/dev/null'), 'S027-MOTION-SEEDANCE20-1')
# Offline serialisation proof: the future body with a placeholder https URL (never sent).
mid, rec = resolve_model(transport.cfg, job['provider_model'])
req = MotionRequest(job['shot_id'], frame, got, job['motion_prompt'], job['negative_constraints'], job['duration_seconds'],
                    job['aspect_ratio'], job['resolution'], job['fps_target'], job['provider'], job['provider_model'],
                    'S027-MOTION-SEEDANCE20-1')
try:
    serialize_request(req, rec, None)
    no_url = 'UNEXPECTED_PASS'
except FailClosed as e:
    no_url = e.code
body = serialize_request(req, rec, 'https://placeholder.invalid/NOT_YET_ASSIGNED.png')
rep['offline_serialisation'] = {
    'official_model_id': mid, 'endpoint': rec['endpoint'], 'contract_status': rec['contract_status'],
    'without_source_url': no_url,
    'body_keys_with_placeholder_url': sorted(body),
    'body_without_prompt_and_url': {k: v for k, v in body.items() if k not in ('prompt', 'image_url')},
    'prompt_transmitted_equals_package_prompt': body['prompt'] == job['motion_prompt'],
    'prompt_sha256': req.prompt_sha256,
}
rep['source_frame_verified'] = {'sha256': got, 'registry_status': row['status'], 'registry_id': row['id']}
rep['network_calls'] = 0
print(json.dumps(rep, indent=1, default=str))
