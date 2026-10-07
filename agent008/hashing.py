import hashlib
import json
from pathlib import Path

from .errors import FailClosed


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def canonical_sha256(obj):
    """Same canonical form as the manifest evidence (sorted keys, compact, UTF-8)."""
    return sha256_bytes(json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode())


def verify_file(path, expected_sha256, label):
    """Fail closed when the file is missing or its SHA-256 differs."""
    p = Path(path)
    if not p.is_file():
        raise FailClosed('ASSET_FILE_MISSING', f'{label}: {p}')
    actual = sha256_file(p)
    if actual != expected_sha256:
        raise FailClosed('HASH_MISMATCH', f'{label}: expected {expected_sha256}, got {actual}')
    return actual
