"""EP005 Batch 1 base frames: transport-only reference uploads (zero generation, zero production writes).

Usage (repo root): python3 evidence/ep005/batch1_base_frames/b1_reference_uploads.py <dir with the verified reference bytes>
Each governed C1 reference is SHA-checked against its governed hash, uploaded once through the bounded Higgsfield
transport (signed upload; the signed upload_url is never recorded) and read back from its unsigned public_url.
The ledger holds the public_url, upload host, byte count and readback SHA only.
"""
import hashlib
import sys
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from agent008.errors import FailClosed  # noqa: E402
from agent008.motion.authorisation import AttemptLedger  # noqa: E402
from agent008.motion.higgsfield_transport import HiggsfieldApiTransport  # noqa: E402
from agent008.motion.http import UrllibHttpClient  # noqa: E402
from agent008.motion.source_upload import SourceFrame, UploadAuthorisation, check_source_frame  # noqa: E402

HERE = Path(__file__).resolve().parent
LEDGER = AttemptLedger(HERE / 'B1_REFERENCE_UPLOAD_LEDGER_v1.jsonl')
BY = 'Gilang / Company Brain (EP005 Batch 1 pre-submit: transport-only reference copies)'
REFS = [  # n, asset_id, governed sha256, content_type, file name, governance source
    (1, 'CHAR-MIKKO-MASTER-v01', '41c9480a847c962c1ecfda4fe076e0abcd86548ba67f692621cfc6e13d61f1a8', 'image/png', 'CHAR-MIKKO-MASTER-v01.png', 'asset_registry APPROVED + C1 canon'),
    (2, 'CHAR-LUMI-MASTER-v01', '8b29c1abea53cb253eea39cdd41d5001ed38036945b049078915ac5993c43a41', 'image/png', 'CHAR-LUMI-MASTER-v01.png', 'asset_registry APPROVED + C1 canon'),
    (3, 'WORLD-EP005-BATHROOM-MASTER-v01', 'ab79c560d3c79a05cb957331149ee4b8a176e109b06010480ba6c26903bd3733', 'image/png', 'WORLD-EP005-BATHROOM-MASTER-v01.png', 'asset_registry APPROVED + C1 canon'),
    (4, 'PROP-EP005-HAND-MIRROR-v01', '34fa31a132144c355714480fa82b22916fc2f825d418658bb787791a0b9c56ac', 'image/webp', 'PROP-EP005-HAND-MIRROR-v01.webp', 'asset_registry APPROVED'),
    (5, 'PROP-EP005-CLEANING-CLOTH-v01', 'afaa3a9fcfc5b562023080318425457c5b4dda8eb58065f56ae542786637c1db', 'image/webp', 'PROP-EP005-CLEANING-CLOTH-v01.webp', 'asset_registry APPROVED'),
    (6, 'DUO-MIKKO-LUMI-SCALE-v01', '735d64075af999d8a00d35afe2674174f5e0feea9b1b4acb9ec2208f1e1d121f', 'image/png', 'DUO-MIKKO-LUMI-SCALE-v01.png', 'C1 canon canon/c1/mikko_lumi_duo_scale_sheet.png (CLAUDE.md hash; no registry row)'),
]


def main(src):
    transport, http = HiggsfieldApiTransport(), UrllibHttpClient()
    if not transport.credentials_present():
        sys.exit('STOP: PROVIDER_CREDENTIAL_MISSING')
    for n, aid, sha, ct, name, gov in REFS:
        scope = f'EP005-B1-BASEFRAME-REF-{aid}'
        frame = SourceFrame(aid, str(Path(src) / name), sha, 'APPROVED', ct)
        data = check_source_frame(frame)
        UploadAuthorisation(scope, BY, 'higgsfield', aid, sha, ct, max_uploads=1, human_approved=True).matches(frame, 'higgsfield')
        if LEDGER.upload_attempts(scope) >= 1:
            sys.exit(f'STOP: UPLOAD_COUNT_EXCEEDED {scope}')
        LEDGER.append('UPLOAD_RESERVED', scope, n=n, frame_id=aid, source_frame_sha256=sha, content_type=ct, bytes=len(data),
                      governance=gov)
        try:
            rec = transport.prepare_source_upload(data, ct, sha, verify_readback=False)
        except FailClosed as e:
            LEDGER.append('UPLOAD_FAILED', scope, frame_id=aid, code=e.code)
            sys.exit(f'STOP: UPLOAD_FAILED {aid} {e.code}')
        u = urlsplit(rec['public_url'])
        if u.query or u.fragment:
            LEDGER.append('PUBLIC_URL_REJECTED', scope, frame_id=aid, reason='query/fragment present (signed URL?)')
            sys.exit(f'STOP: PUBLIC_URL_NOT_UNSIGNED {aid}')
        LEDGER.append('UPLOADED', scope, n=n, frame_id=aid, provider='higgsfield', **rec)
        rb = http.send('GET', rec['public_url'], {}, None, 60.0)
        got = hashlib.sha256(rb.body).hexdigest() if rb.status == 200 else None
        LEDGER.append('READBACK_SHA256_MATCH' if got == sha else 'READBACK_FAILED', scope, n=n, frame_id=aid,
                      expected_sha256=sha, public_url=rec['public_url'],
                      readback={'http_status': rb.status, 'sha256': got, 'bytes': len(rb.body) if rb.body else 0})
        print(n, aid, 'UPLOADED', 'READBACK', 'MATCH' if got == sha else f'FAIL {rb.status}')
        if got != sha:
            sys.exit(f'STOP: READBACK_FAILED {aid}')


if __name__ == '__main__':
    main(sys.argv[1])
