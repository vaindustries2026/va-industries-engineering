"""Wikimedia Commons adapter (MediaWiki Action API, no credential, no cost).

Rights come from imageinfo.extmetadata (License, LicenseShortName, LicenseUrl,
Artist/Credit, Restrictions, Copyrighted). Integrity comes from imageinfo.sha1
and imageinfo.size, which Commons publishes for every file revision.
"""
import hashlib
import html
import json
import os
import re
import urllib.parse

from ..errors import FailClosed
from .base import SourceAdapter

API = 'https://commons.wikimedia.org/w/api.php'
FILE_HOST = 'https://upload.wikimedia.org/'
_TAG = re.compile(r'<[^>]+>')


def _meta(ext, key):
    v = (ext.get(key) or {}).get('value')
    if v is None:
        return None
    return html.unescape(_TAG.sub('', str(v))).strip() or None


class WikimediaCommonsAdapter(SourceAdapter):
    name = 'wikimedia_commons'
    source_classes = ('SRC-PD-ARCHIVE', 'SRC-OPEN-LICENSE')

    def __init__(self, transport, api_url=API):
        self.transport = transport
        self.api_url = api_url

    def search_url(self, query, limit):
        params = {
            'action': 'query', 'format': 'json', 'formatversion': '2',
            'generator': 'search', 'gsrsearch': query, 'gsrnamespace': '6', 'gsrlimit': str(limit),
            'prop': 'imageinfo', 'iiprop': 'url|size|sha1|mime|mediatype|extmetadata|timestamp',
        }
        return f'{self.api_url}?{urllib.parse.urlencode(params)}'

    def discover(self, query, limit):
        url = self.search_url(query, limit)
        raw = self.transport.get_bytes(url, max_bytes=5_000_000)
        try:
            doc = json.loads(raw)
        except ValueError:
            raise FailClosed('AUTHORITY_RESPONSE_NOT_JSON', url)
        if 'error' in doc:
            raise FailClosed('AUTHORITY_API_ERROR', json.dumps(doc['error'])[:300])
        items = []
        for page in (doc.get('query') or {}).get('pages', []):
            info = (page.get('imageinfo') or [None])[0]
            if not info:
                continue
            ext = info.get('extmetadata') or {}
            items.append({
                'authority': self.name,
                'item_id': page.get('title'),
                'page_id': page.get('pageid'),
                'description_url': info.get('descriptionurl'),
                'file_url': info.get('url'),
                'size': info.get('size'),
                'sha1': info.get('sha1'),
                'mime': info.get('mime'),
                'mediatype': info.get('mediatype'),
                'revision_timestamp': info.get('timestamp'),
                'rights': {
                    'license_code': _meta(ext, 'License'),
                    'license_name': _meta(ext, 'LicenseShortName'),
                    'license_url': _meta(ext, 'LicenseUrl'),
                    'attribution': _meta(ext, 'Attribution') or _meta(ext, 'Artist') or _meta(ext, 'Credit'),
                    'restrictions': _meta(ext, 'Restrictions'),
                    'copyrighted_flag': _meta(ext, 'Copyrighted'),
                },
                'raw_extmetadata': {k: (v or {}).get('value') for k, v in sorted(ext.items())},
            })
        items.sort(key=lambda i: (i['item_id'] or ''))
        return {'request_url': url, 'response_sha256': hashlib.sha256(raw).hexdigest(), 'items': items}

    def allowed_file_host(self, url):
        return bool(url) and url.startswith(FILE_HOST)

    def verify_integrity(self, item, path):
        size = os.path.getsize(path)
        if item.get('size') is not None and size != item['size']:
            raise FailClosed('INTEGRITY_SIZE_MISMATCH', f'authority {item["size"]}, got {size}')
        h = hashlib.sha1()
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(1 << 20), b''):
                h.update(chunk)
        if not item.get('sha1'):
            raise FailClosed('INTEGRITY_AUTHORITY_DIGEST_MISSING', item.get('item_id'))
        if h.hexdigest() != item['sha1'].lower():
            raise FailClosed('INTEGRITY_SHA1_MISMATCH', f'authority {item["sha1"]}, got {h.hexdigest()}')
        return {'authority_sha1': item['sha1'].lower(), 'size_bytes': size}
