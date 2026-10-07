"""Asset identity resolution.

Priority (fixed):
  1. approved readiness canonical_reuse_map
  2. exact approved registry identity (asset_id)
  3. exact manifest shot contract
Stale human-readable labels (TMP_EP005_*, "TBD", "identity TBD") are
informational only and can never select an asset on their own.
"""
import re

from .errors import FailClosed

GOVERNED = ('APPROVED', 'LOCKED')
STALE_LABEL = re.compile(r'^(TMP_|TBD$)|\bTBD\b', re.IGNORECASE)


def is_stale_label(value):
    return value is None or bool(STALE_LABEL.search(str(value)))


def _norm(s):
    return re.sub(r'\s+', ' ', re.sub(r'[_-]+', ' ', str(s).lower())).strip()


class Resolver:
    def __init__(self, readiness_row, registry_rows, hash_pins=None):
        rj = readiness_row['readiness_manifest_json']
        self.reuse_map = rj.get('canonical_reuse_map') or []
        self.registry = registry_rows
        self.pins = hash_pins or {}
        # source label / source asset id / requirement key -> canonical id (from the readiness map only)
        self._map = {}
        for e in self.reuse_map:
            cid = e.get('canonical_asset_id')
            if not cid:
                raise FailClosed('REUSE_MAP_ENTRY_WITHOUT_CANONICAL_ID', str(e.get('requirement_key')))
            for key in (e.get('source_asset_id'), e.get('source_label'), e.get('requirement_key')):
                if key is None:
                    continue
                prev = self._map.get(key)
                if prev and prev != cid:
                    raise FailClosed('REUSE_MAP_AMBIGUOUS', f'{key} -> {prev} / {cid}')
                self._map[key] = cid

    # 1. canonical map
    def canonical_id(self, reference):
        """Map a manifest reference (TMP id, label, requirement key or exact id) to a canonical id."""
        if reference in self._map:
            return self._map[reference]
        if not is_stale_label(reference) and any(r['asset_id'] == reference for r in self.registry):
            return reference  # already an exact registry identity
        raise FailClosed('UNMAPPED_REFERENCE', f'{reference!r} is not in the readiness canonical_reuse_map')

    # 2. exact registry identity
    def registry_row(self, asset_id):
        if is_stale_label(asset_id):
            raise FailClosed('STALE_LABEL_AS_IDENTITY', asset_id)
        exact = [r for r in self.registry if r['asset_id'] == asset_id]
        governed = [r for r in exact if r['status'] in GOVERNED]
        if not exact:
            raise FailClosed('ASSET_NOT_IN_REGISTRY', asset_id)
        if len(governed) == 0:
            raise FailClosed('ASSET_NOT_APPROVED', f"{asset_id} status {[r['status'] for r in exact]}")
        if len(governed) > 1:
            raise FailClosed('AMBIGUOUS_REGISTRY_MATCH', f'{asset_id} has {len(governed)} governed rows')
        row = governed[0]
        # No other governed row may claim this id or this row's name as an alias.
        n_id, n_name = _norm(asset_id), _norm(row.get('asset_name') or '')
        for r in self.registry:
            if r is row or r['status'] not in GOVERNED:
                continue
            tokens = {_norm(r['asset_id']), _norm(r.get('asset_name') or '')} | {_norm(a) for a in (r.get('aliases') or [])}
            if n_id in tokens or (n_name and n_name in tokens):
                raise FailClosed('AMBIGUOUS_REGISTRY_MATCH', f"{asset_id} collides with {r['asset_id']}")
        return row

    def expected_sha256(self, row):
        md = row.get('metadata_json') or {}
        reg = md.get('sha256')
        pin = (self.pins.get(row['asset_id']) or {}).get('sha256')
        if reg and pin and reg != pin:
            raise FailClosed('HASH_PIN_CONFLICT', row['asset_id'])
        if reg:
            return reg, 'asset_registry.metadata_json.sha256'
        if pin:
            return pin, 'agent008/inputs/hash_pins.json (' + self.pins[row['asset_id']].get('source', '?') + ')'
        raise FailClosed('NO_EXPECTED_HASH', row['asset_id'])

    def resolve(self, reference):
        """Full resolution: reference -> canonical id -> governed row -> expected hash."""
        cid = self.canonical_id(reference)
        row = self.registry_row(cid)
        sha, sha_source = self.expected_sha256(row)
        sp = row.get('storage_path') or ''
        if not sp.startswith('production-assets/'):
            raise FailClosed('STORAGE_PATH_INVALID', f'{cid}: {sp}')
        return {
            'reference': reference, 'asset_id': cid, 'registry_row_id': row['id'], 'status': row['status'],
            'asset_type': row['asset_type'], 'storage_path': sp,
            'object_key': sp[len('production-assets/'):], 'expected_sha256': sha, 'sha256_source': sha_source,
        }
