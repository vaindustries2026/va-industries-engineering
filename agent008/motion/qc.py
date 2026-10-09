"""Stage 8G: human QC decisions on generated motion. Append-only; Agent-008 never decides."""
import json
import time
from pathlib import Path

from ..errors import FailClosed

DECISIONS = ('APPROVE', 'REJECT', 'REGENERATE')


class QCDecisionLog:
    def __init__(self, path):
        self.path = Path(path)

    def decisions(self, candidate_sha256):
        if not self.path.exists():
            return []
        rows = [json.loads(l) for l in self.path.read_text().splitlines() if l.strip()]
        return [r for r in rows if r['candidate_sha256'] == candidate_sha256]

    def record(self, candidate_sha256, decision, reviewer, notes=''):
        if decision not in DECISIONS:
            raise FailClosed('QC_DECISION_INVALID', decision)
        if not reviewer or reviewer.lower().startswith('agent'):
            raise FailClosed('QC_REQUIRES_HUMAN', 'decisions must be recorded by a named human reviewer')
        prior = [d['decision'] for d in self.decisions(candidate_sha256)]
        if 'REJECT' in prior:
            raise FailClosed('QC_REJECTED_IS_TERMINAL', candidate_sha256)
        if 'APPROVE' in prior:
            raise FailClosed('QC_ALREADY_APPROVED', candidate_sha256)
        row = {'candidate_sha256': candidate_sha256, 'decision': decision, 'reviewer': reviewer, 'notes': notes,
               'at_unix': time.time(),
               'follow_up': 'NEW_SPEND_AUTHORISATION_REQUIRED' if decision == 'REGENERATE' else None}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, 'a') as f:
            f.write(json.dumps(row, sort_keys=True) + '\n')
        return row

    def status(self, candidate_sha256):
        d = [r['decision'] for r in self.decisions(candidate_sha256)]
        if not d:
            return 'REVIEW'
        return {'APPROVE': 'APPROVED', 'REJECT': 'REJECTED', 'REGENERATE': 'REGENERATE_REQUESTED'}[d[-1]]

    def production_approved(self, candidate_sha256):
        d = [r['decision'] for r in self.decisions(candidate_sha256)]
        return 'REJECT' not in d and 'APPROVE' in d
