"""Unattended acquisition pipeline for tier-A source classes.

job -> class gate -> discover (authority API) -> per-candidate filters + rights gate
-> dedupe against the append-only ledger -> download (host-pinned, size-capped)
-> authority integrity check -> SHA-256 -> read-only raw file + provenance (REVIEW).

Nothing here can set APPROVED. A human approves an exact sha256 later.
"""
import datetime as _dt
import hashlib
import json
import os
from pathlib import Path

from . import rights
from .adapters.base import Transport
from .adapters.wikimedia_commons import WikimediaCommonsAdapter
from .classes import require_automatable
from .errors import FailClosed

TOOL_VERSION = 'sourcing-v0.1'
ADAPTERS = {'wikimedia_commons': WikimediaCommonsAdapter}
_JOB_KEYS = {'job_id', 'channel', 'source_class', 'adapter', 'query', 'search_limit',
             'accept_mediatypes', 'accept_mimes', 'max_items', 'max_bytes'}
_EXT = {'video/webm': '.webm', 'video/ogg': '.ogv', 'video/mp4': '.mp4',
        'image/png': '.png', 'image/jpeg': '.jpg', 'audio/ogg': '.oga'}


def canonical_sha256(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(',', ':'),
                                     ensure_ascii=False).encode()).hexdigest()


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def load_job(path):
    job = json.loads(Path(path).read_text())
    missing = _JOB_KEYS - job.keys()
    extra = job.keys() - _JOB_KEYS
    if missing or extra:
        raise FailClosed('JOB_SCHEMA_INVALID', f'missing={sorted(missing)} extra={sorted(extra)}')
    if job['channel'] != 'ANIME_CLIP_FARMING':
        raise FailClosed('JOB_CHANNEL_INVALID', job['channel'])
    if not (isinstance(job['max_items'], int) and 1 <= job['max_items'] <= 5):
        raise FailClosed('JOB_MAX_ITEMS_INVALID', str(job['max_items']))
    if not (isinstance(job['max_bytes'], int) and 0 < job['max_bytes'] <= 500_000_000):
        raise FailClosed('JOB_MAX_BYTES_INVALID', str(job['max_bytes']))
    return job


class Ledger:
    """Append-only JSONL ledger keyed by sha256 (insert-only; a duplicate is ignored, never rewritten)."""

    def __init__(self, path):
        self.path = Path(path)

    def rows(self):
        if not self.path.is_file():
            return []
        return [json.loads(line) for line in self.path.read_text().splitlines() if line.strip()]

    def find(self, *, sha256=None, authority_sha1=None):
        for r in self.rows():
            if sha256 and r.get('sha256') == sha256:
                return r
            if authority_sha1 and r.get('authority_sha1') == authority_sha1:
                return r
        return None

    def insert(self, row):
        if self.find(sha256=row['sha256']):
            return False
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, 'a') as f:
            f.write(json.dumps(row, sort_keys=True) + '\n')
        return True


def _screen(job, adapter, item):
    """Return (rights_record, None) or (None, reason_code). Deterministic, no network."""
    if item.get('mediatype') not in job['accept_mediatypes']:
        return None, f'MEDIATYPE_NOT_ACCEPTED:{item.get("mediatype")}'
    if item.get('mime') not in job['accept_mimes']:
        return None, f'MIME_NOT_ACCEPTED:{item.get("mime")}'
    if not isinstance(item.get('size'), int) or item['size'] > job['max_bytes']:
        return None, f'SIZE_NOT_ACCEPTED:{item.get("size")}'
    if not adapter.allowed_file_host(item.get('file_url')):
        return None, 'FILE_HOST_NOT_AUTHORITY'
    if not item.get('sha1'):
        return None, 'AUTHORITY_DIGEST_MISSING'
    try:
        return rights.evaluate(job['source_class'], item['rights']), None
    except FailClosed as e:
        return None, e.code


def run(job_path, out_dir, transport=None, now=None):
    job = load_job(job_path)
    job_sha = canonical_sha256(job)
    require_automatable(job['source_class'])
    adapter_cls = ADAPTERS.get(job['adapter'])
    if adapter_cls is None:
        raise FailClosed('ADAPTER_UNKNOWN', job['adapter'])
    if job['source_class'] not in adapter_cls.source_classes:
        raise FailClosed('ADAPTER_CLASS_MISMATCH', f'{job["adapter"]} cannot serve {job["source_class"]}')
    adapter = adapter_cls(transport or Transport())
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    ledger = Ledger(out / 'acquisition_ledger.jsonl')
    stamp = (now or _dt.datetime.now(_dt.timezone.utc)).strftime('%Y-%m-%dT%H:%M:%SZ')

    found = adapter.discover(job['query'], job['search_limit'])
    screened, eligible = [], []
    for item in found['items']:
        record, reason = _screen(job, adapter, item)
        screened.append({'item_id': item['item_id'], 'license_code': item['rights'].get('license_code'),
                         'mime': item.get('mime'), 'size': item.get('size'),
                         'decision': 'ELIGIBLE' if record else 'REJECTED', 'reason': reason})
        if record:
            eligible.append((item, record))
    discovery = {'job_id': job['job_id'], 'job_sha256': job_sha, 'at': stamp,
                 'request_url': found['request_url'], 'response_sha256': found['response_sha256'],
                 'candidates': len(found['items']), 'eligible': len(eligible), 'screened': screened}
    (out / 'discovery_report.json').write_text(json.dumps(discovery, indent=2, sort_keys=True))
    if not eligible:
        raise FailClosed('NO_ELIGIBLE_SOURCE', f'{len(found["items"])} candidates, 0 eligible')

    results = []
    for item, record in eligible[:job['max_items']]:
        prior = ledger.find(authority_sha1=item['sha1'].lower())
        if prior:
            results.append({'status': 'ALREADY_ACQUIRED', 'source_item_id': prior['source_item_id'],
                            'sha256': prior['sha256']})
            continue
        ext = _EXT.get(item['mime'], '.bin')
        tmp = out / f'.partial-{item["sha1"].lower()}{ext}'
        try:
            adapter.transport.download(item['file_url'], tmp, job['max_bytes'])
            integrity = adapter.verify_integrity(item, tmp)
            digest = sha256_file(tmp)
        except FailClosed:
            if tmp.exists():
                tmp.unlink()
            raise
        source_item_id = f'SRCITEM-{digest[:16].upper()}'
        item_dir = out / source_item_id
        item_dir.mkdir(exist_ok=True)
        raw = item_dir / f'raw{ext}'
        os.replace(tmp, raw)
        os.chmod(raw, 0o444)
        provenance = {
            'source_item_id': source_item_id,
            'status': 'REVIEW',
            'channel': job['channel'],
            'source_class': job['source_class'],
            'authority': item['authority'],
            'authority_item_id': item['item_id'],
            'authority_page_id': item['page_id'],
            'authority_description_url': item['description_url'],
            'authority_file_url': item['file_url'],
            'authority_revision_timestamp': item['revision_timestamp'],
            'authority_sha1': integrity['authority_sha1'],
            'sha256': digest,
            'size_bytes': integrity['size_bytes'],
            'mime': item['mime'],
            'raw_filename': raw.name,
            'rights': record,
            'authority_rights_raw': item['raw_extmetadata'],
            'acquired_at': stamp,
            'job_id': job['job_id'],
            'job_sha256': job_sha,
            'discovery_response_sha256': found['response_sha256'],
            'tool_version': TOOL_VERSION,
            'paid_calls': 0,
        }
        (item_dir / 'provenance.json').write_text(json.dumps(provenance, indent=2, sort_keys=True))
        ledger.insert({'source_item_id': source_item_id, 'sha256': digest,
                       'authority_sha1': integrity['authority_sha1'], 'authority_item_id': item['item_id'],
                       'source_class': job['source_class'], 'status': 'REVIEW', 'acquired_at': stamp,
                       'job_sha256': job_sha})
        results.append({'status': 'ACQUIRED_REVIEW', 'source_item_id': source_item_id, 'sha256': digest,
                        'authority_item_id': item['item_id'], 'license_code': record['license_code']})
    return {'job_id': job['job_id'], 'results': results, 'discovery': 'discovery_report.json'}
