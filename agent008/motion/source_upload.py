"""Stage 8B2: host the exact human-approved source frame for providers that need a public URL.

Agent-008 never uploads an arbitrary local file. Before any upload:
  1. the source frame status is APPROVED (or LOCKED / APPROVED_FOR_MOTION_INPUT)
  2. an exact expected SHA-256 is supplied
  3. the local bytes match that SHA (the bytes hashed are the bytes sent)
  4. the content type is explicit, allowed and matches the file signature
  5. a human-approved UploadAuthorisation names this exact frame id, SHA, content type and provider
     and the ledger shows no earlier upload attempt (one upload; reserved before the call)
  6. the returned public_url is recorded (ledger + provenance)
  7. the generation request must then reference that exact public_url (checked by the runner)
Any failure fails closed. This stage is paid-gated: it is not executed in v0.2 tests except with mocks.
"""
from dataclasses import dataclass, replace
from pathlib import Path

from ..errors import FailClosed
from ..hashing import sha256_bytes
from .higgsfield_transport import CONTENT_TYPES

APPROVED_FRAME_STATES = ('APPROVED', 'LOCKED', 'APPROVED_FOR_MOTION_INPUT')


@dataclass(frozen=True)
class SourceFrame:
    frame_id: str
    path: str
    expected_sha256: str
    status: str
    content_type: str


@dataclass(frozen=True)
class UploadAuthorisation:
    approval_scope_id: str
    authorised_by: str
    provider: str
    frame_id: str
    source_frame_sha256: str
    content_type: str
    max_uploads: int = 1
    human_approved: bool = False

    def matches(self, frame, provider_name):
        bad = [k for k, (a, b) in {
            'provider': (str(self.provider).lower(), str(provider_name).lower()),
            'frame_id': (self.frame_id, frame.frame_id),
            'source_frame_sha256': (self.source_frame_sha256, frame.expected_sha256),
            'content_type': (self.content_type, frame.content_type)}.items() if a != b]
        if bad:
            raise FailClosed('UPLOAD_AUTHORISATION_SCOPE_MISMATCH', ','.join(bad))
        if self.human_approved is not True:
            raise FailClosed('UPLOAD_AUTHORISATION_NOT_HUMAN_APPROVED')
        if self.max_uploads != 1:
            raise FailClosed('UPLOAD_AUTHORISATION_ATTEMPTS_NOT_ONE', str(self.max_uploads))
        return True


def check_source_frame(frame):
    """Checks 1-4. Returns the exact bytes that were hashed (these and only these may be uploaded)."""
    if frame is None:
        raise FailClosed('SOURCE_FRAME_MISSING')
    if frame.status not in APPROVED_FRAME_STATES:
        raise FailClosed('SOURCE_FRAME_NOT_APPROVED', str(frame.status))
    if not isinstance(frame.expected_sha256, str) or len(frame.expected_sha256) != 64:
        raise FailClosed('SOURCE_SHA_MISSING')
    p = Path(frame.path) if frame.path else None
    if not p or not p.is_file():
        raise FailClosed('SOURCE_FRAME_MISSING', str(frame.path))
    data = p.read_bytes()
    if sha256_bytes(data) != frame.expected_sha256:
        raise FailClosed('SOURCE_SHA_MISMATCH', f'{frame.frame_id}: local bytes differ from the approved sha256')
    sig = CONTENT_TYPES.get(frame.content_type)
    if not frame.content_type or sig is None:
        raise FailClosed('SOURCE_CONTENT_TYPE_INVALID', str(frame.content_type))
    if not data.startswith(sig):
        raise FailClosed('SOURCE_CONTENT_TYPE_MISMATCH', f'{frame.content_type} signature not found')
    return data


def stage_source_frame(frame, provider, upload_auth, ledger):
    """Run checks 1-6 and the provider upload exactly once. Returns the source-upload provenance record."""
    data = check_source_frame(frame)
    if upload_auth is None:
        raise FailClosed('UPLOAD_AUTHORISATION_MISSING')
    upload_auth.matches(frame, provider.name)
    if not provider.credentials_present():
        raise FailClosed('PROVIDER_CREDENTIAL_MISSING', provider.name)
    used = ledger.upload_attempts(upload_auth.approval_scope_id)
    if used >= upload_auth.max_uploads:
        raise FailClosed('UPLOAD_COUNT_EXCEEDED', f'{used} of {upload_auth.max_uploads}')
    ledger.append('UPLOAD_RESERVED', upload_auth.approval_scope_id, frame_id=frame.frame_id,
                  source_frame_sha256=frame.expected_sha256, content_type=frame.content_type)
    try:
        rec = provider.prepare_source_upload(data, frame.content_type, frame.expected_sha256)
    except FailClosed as e:
        ledger.append('UPLOAD_FAILED', upload_auth.approval_scope_id, code=e.code)
        raise
    record = {'frame_id': frame.frame_id, 'provider': provider.name, **rec,
              'upload_scope_id': upload_auth.approval_scope_id}
    ledger.append('UPLOADED', upload_auth.approval_scope_id, **record)
    return record


def bind_request_to_upload(req, record):
    """Return the request with source_frame_url set to the exact recorded public_url (check 7)."""
    if record.get('sha256') != req.source_frame_sha256:
        raise FailClosed('SOURCE_UPLOAD_MISMATCH', 'upload sha256 differs from request source_frame_sha256')
    return replace(req, source_frame_url=record['public_url'])
