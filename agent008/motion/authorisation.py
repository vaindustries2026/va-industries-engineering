"""Exact-scope spend authorisation and an append-only attempt ledger.

A paid generation is allowed only when a human authorisation names the exact
provider, model, shot, source-frame SHA-256 and prompt SHA-256, and the ledger
shows fewer attempts than the authorised maximum. The attempt is reserved in the
ledger BEFORE submission, so a crash or failure still counts. There is no retry.
"""
import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from ..errors import FailClosed


@dataclass(frozen=True)
class SpendAuthorisation:
    approval_scope_id: str
    authorised_by: str
    provider: str
    provider_model: str
    shot_id: str
    source_frame_sha256: str
    prompt_sha256: str
    max_generations: int
    no_auto_retry: bool = True

    def matches(self, req):
        pairs = {'provider': (self.provider, req.provider), 'provider_model': (self.provider_model, req.provider_model),
                 'shot_id': (self.shot_id, req.shot_id), 'source_frame_sha256': (self.source_frame_sha256, req.source_frame_sha256),
                 'prompt_sha256': (self.prompt_sha256, req.prompt_sha256),
                 'approval_scope_id': (self.approval_scope_id, req.approval_scope_id)}
        bad = [k for k, (a, b) in pairs.items() if a != b]
        if bad:
            raise FailClosed('AUTHORISATION_SCOPE_MISMATCH', ','.join(bad))
        if not self.no_auto_retry:
            raise FailClosed('AUTHORISATION_ALLOWS_RETRY')
        return True


class AttemptLedger:
    """JSON-lines file; entries are only ever appended."""

    def __init__(self, path):
        self.path = Path(path)

    def entries(self, scope_id=None):
        if not self.path.exists():
            return []
        rows = [json.loads(l) for l in self.path.read_text().splitlines() if l.strip()]
        return [r for r in rows if scope_id is None or r['approval_scope_id'] == scope_id]

    def attempts(self, scope_id):
        return sum(1 for r in self.entries(scope_id) if r['event'] == 'RESERVED')

    def append(self, event, scope_id, **data):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        row = {'event': event, 'approval_scope_id': scope_id, 'at_unix': time.time(), **data}
        with open(self.path, 'a') as f:
            f.write(json.dumps(row, sort_keys=True) + '\n')
        return row

    def reserve(self, auth, req):
        auth.matches(req)
        n = self.attempts(auth.approval_scope_id)
        if n >= auth.max_generations:
            raise FailClosed('GENERATION_COUNT_EXCEEDED', f'{n} of {auth.max_generations} already used')
        return self.append('RESERVED', auth.approval_scope_id, attempt_number=n + 1, request=req.to_dict())


def load_authorisation(d):
    return SpendAuthorisation(**d)
