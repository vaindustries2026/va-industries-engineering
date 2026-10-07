"""Input loading and the readiness gate.

Agent-008 accepts only an explicitly supplied readiness manifest id. There is
no "latest approved readiness" lookup anywhere in this package.
"""
import json
from pathlib import Path

from .errors import FailClosed
from .hashing import canonical_sha256

# Legacy readiness manifests that carry APPROVED + NEEDS_ASSET_CREATION from
# pre-cleanup lineages. They must never become Agent-008 inputs.
LEGACY_DENYLIST = {
    'd124ba28-2dc5-4b86-8608-f363eeb3f8d2': 'legacy EP005 c56cabc0 lineage (APPROVED + NEEDS_ASSET_CREATION)',
    'c0012923-d22e-4b5e-b497-53d1c0ff3938': 'TEST-A007-PAID-SMOKE-001 fixture (APPROVED + NEEDS_ASSET_CREATION)',
}

# A readiness state is compatible only if it implies zero unresolved requirements.
COMPATIBLE_READINESS_STATES = {'READY_FOR_HUMAN_APPROVAL'}


def load_snapshot(path):
    snap = json.loads(Path(path).read_text())
    if snap.get('snapshot_version') != 'agent008-input-snapshot-v1':
        raise FailClosed('SNAPSHOT_VERSION_UNSUPPORTED', str(snap.get('snapshot_version')))
    return snap


def load_hash_pins(path):
    return json.loads(Path(path).read_text()).get('pins', {})


def validate_readiness(snap, readiness_manifest_id, production_manifest_id=None, asset_resolution_run_id=None):
    """Fail closed unless the snapshot is exactly the requested, approved, fully resolved readiness."""
    if not readiness_manifest_id:
        raise FailClosed('READINESS_ID_REQUIRED', 'an explicit readiness_manifest_id is required')
    if readiness_manifest_id in LEGACY_DENYLIST:
        raise FailClosed('LEGACY_READINESS_DENIED', LEGACY_DENYLIST[readiness_manifest_id])
    r = snap['readiness_manifest']
    if r.get('id') != readiness_manifest_id:
        raise FailClosed('READINESS_ID_MISMATCH', f"requested {readiness_manifest_id}, snapshot has {r.get('id')}")
    if r.get('status') != 'APPROVED':
        raise FailClosed('READINESS_NOT_APPROVED', str(r.get('status')))
    if r.get('readiness_state') not in COMPATIBLE_READINESS_STATES:
        raise FailClosed('READINESS_STATE_INCOMPATIBLE', str(r.get('readiness_state')))
    n = r.get('requirement_count')
    if not n or r.get('resolved_reuse_count') != n:
        raise FailClosed('READINESS_NOT_FULLY_RESOLVED', f"resolved {r.get('resolved_reuse_count')} of {n}")
    for k in ('create_new_count', 'human_review_count', 'blocked_count'):
        if r.get(k) != 0:
            raise FailClosed('READINESS_HAS_UNRESOLVED', f'{k}={r.get(k)}')
    rj = r.get('readiness_manifest_json') or {}
    if rj.get('human_review_queue') or rj.get('asset_creation_queue') or rj.get('blocked_requirements'):
        raise FailClosed('READINESS_QUEUES_NOT_EMPTY')
    if canonical_sha256(rj) != snap.get('readiness_manifest_json_canonical_sha256'):
        raise FailClosed('SNAPSHOT_READINESS_TAMPERED')
    pm = snap['production_manifest']
    if r.get('production_manifest_id') != pm.get('id'):
        raise FailClosed('PRODUCTION_MANIFEST_LINK_MISMATCH')
    if production_manifest_id and pm.get('id') != production_manifest_id:
        raise FailClosed('PRODUCTION_MANIFEST_ID_MISMATCH', f"requested {production_manifest_id}, linked {pm.get('id')}")
    if pm.get('status') != 'APPROVED':
        raise FailClosed('PRODUCTION_MANIFEST_NOT_APPROVED', str(pm.get('status')))
    if asset_resolution_run_id and r.get('asset_resolution_run_id') != asset_resolution_run_id:
        raise FailClosed('AGENT006_RUN_MISMATCH', str(r.get('asset_resolution_run_id')))
    for rec in rj.get('all_resolution_records', []):
        if rec.get('resolution_status') != 'REUSE_EXISTING' or len(rec.get('exact_candidate_asset_ids') or []) != 1:
            raise FailClosed('RESOLUTION_RECORD_NOT_UNIQUE_REUSE', rec.get('requirement_key', '?'))
    return r
