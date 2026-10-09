"""S027 motion, Steps 1-2: reconcile approved inputs, then EXACTLY ONE authorised Higgsfield source upload.

Usage (repo root): python3 evidence/agent008/phase1/s027_v2/stage1_reconcile_and_upload.py <work_dir>
Reads the frame from V&A production storage and the registry row (GET), verifies both SHA-256s, then
stages the frame through the official upload flow. The public_url is ledgered BEFORE readback.
"""
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from agent008.errors import FailClosed  # noqa: E402
from agent008.hashing import sha256_bytes, sha256_file  # noqa: E402
from agent008.motion.authorisation import AttemptLedger  # noqa: E402
from agent008.motion.contracts import text_sha256  # noqa: E402
from agent008.motion.higgsfield import HiggsfieldProvider  # noqa: E402
from agent008.motion.higgsfield_transport import HiggsfieldApiTransport  # noqa: E402
from agent008.motion.http import UrllibHttpClient  # noqa: E402
from agent008.motion.source_upload import SourceFrame, UploadAuthorisation, check_source_frame  # noqa: E402

FRAME_SHA = '81b841a6ab53219b26755c4e83a9777953a2d03f37213875e38691c112f0061b'
PROMPT_SHA = 'ab7f92afa5d7a8bde2efc621eb86ebe249614762b66e15576ec0b5d9c3f4cab3'
SB = 'https://ziluiwrwwbayhcskeere.supabase.co'
D = ROOT / 'evidence/agent008/phase1/s027_v2'
LEDGER = AttemptLedger(D / 'S027_MOTION_LEDGER_v1.jsonl')
SCOPE_UP = 'S027-MOTION-SOURCE-UPLOAD-1'

work = Path(sys.argv[1]); work.mkdir(parents=True, exist_ok=True)
http = UrllibHttpClient()
out = {}

# ---- Step 1: reconcile (GET only) ----
r = http.send('GET', f'{SB}/rest/v1/asset_registry?asset_id=eq.FRAME-EP005-S027-BASE-v01&select=*', {'Accept': 'application/json'})
rows = json.loads(r.body)
if r.status != 200 or len(rows) != 1:
    sys.exit(f'STOP: registry lookup HTTP {r.status}, rows {len(rows) if isinstance(rows, list) else "?"}')
row = rows[0]
if row['status'] != 'APPROVED' or row['id'] != 'd2a07b22-cf25-42ff-b86a-c4080ff24bc2' or row['metadata_json']['sha256'] != FRAME_SHA:
    sys.exit('STOP: registry row not APPROVED or sha mismatch')
key = row['metadata_json']['storage_object_key']
r = http.send('GET', f'{SB}/storage/v1/object/authenticated/production-assets/{key}', {})
if r.status != 200:
    sys.exit(f'STOP: storage read HTTP {r.status}')
frame_path = work / 'FRAME-EP005-S027-BASE-v01.png'
frame_path.write_bytes(r.body)
if sha256_file(frame_path) != FRAME_SHA:
    sys.exit('STOP: stored frame SHA differs')
job = json.loads((ROOT / 'agent008/motion/jobs/ep005_s027_motion_smoke_v2.json').read_text())
prompt_file = (D / 'S027_MOTION_PROMPT_v2.txt').read_bytes().decode('utf-8')
if text_sha256(prompt_file) != PROMPT_SHA or text_sha256(job['motion_prompt']) != PROMPT_SHA or job['motion_prompt'] != prompt_file:
    sys.exit('STOP: prompt SHA differs')
out['step1'] = {'registry_id': row['id'], 'registry_status': row['status'], 'storage_key': key,
                'stored_bytes': frame_path.stat().st_size, 'stored_sha256': FRAME_SHA, 'prompt_sha256': PROMPT_SHA}

# ---- Step 2: exactly one source upload ----
transport = HiggsfieldApiTransport()
provider = HiggsfieldProvider(transport=transport)
frame = SourceFrame('FRAME-EP005-S027-BASE-v01', str(frame_path), FRAME_SHA, row['status'], 'image/png')
auth = UploadAuthorisation(SCOPE_UP, 'Gilang / Company Brain', 'higgsfield', frame.frame_id, FRAME_SHA, 'image/png',
                           max_uploads=1, human_approved=True)
data = check_source_frame(frame)                       # status, sha (immediately before upload), signature
auth.matches(frame, provider.name)
if not provider.credentials_present():
    sys.exit('STOP: PROVIDER_CREDENTIAL_MISSING')
if LEDGER.upload_attempts(SCOPE_UP) >= 1:
    sys.exit('STOP: UPLOAD_COUNT_EXCEEDED (an upload was already attempted under this scope)')
LEDGER.append('UPLOAD_RESERVED', SCOPE_UP, frame_id=frame.frame_id, source_frame_sha256=FRAME_SHA, content_type='image/png',
              bytes=len(data))
try:
    rec = transport.prepare_source_upload(data, 'image/png', FRAME_SHA, verify_readback=False)
except FailClosed as e:
    LEDGER.append('UPLOAD_FAILED', SCOPE_UP, code=e.code, detail=str(e.detail)[:300])
    print(json.dumps(out, indent=1)); sys.exit(f'STOP: upload failed {e.code}')
LEDGER.append('UPLOADED', SCOPE_UP, frame_id=frame.frame_id, **rec)
out['step2_upload'] = rec

# readback (unauthenticated GET of the public URL), after the URL is ledgered
rb = http.send('GET', rec['public_url'], {})
got = sha256_bytes(rb.body) if rb.status == 200 else None
ct = {k.lower(): v for k, v in rb.headers.items()}.get('content-type')
ev = {'public_url': rec['public_url'], 'http_status': rb.status, 'bytes': len(rb.body), 'content_type': ct, 'sha256': got}
if got == FRAME_SHA:
    LEDGER.append('READBACK_SHA256_MATCH', SCOPE_UP, **ev)
else:
    LEDGER.append('READBACK_FAILED', SCOPE_UP, **ev)
    out['step2_readback'] = ev; print(json.dumps(out, indent=1)); sys.exit('STOP: readback verification failed')
out['step2_readback'] = ev
(D / 'S027_SOURCE_UPLOAD_v1.json').write_text(json.dumps(out, indent=1))
print(json.dumps(out, indent=1))
