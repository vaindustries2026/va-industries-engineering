"""SourceAdapter: the only interface the acquisition pipeline uses.

An adapter talks to exactly one source authority through its documented public
interface. It returns the authority's own rights and integrity fields unchanged;
it never interprets a licence (that is rights.evaluate) and never selects an
item outside the job's query.
"""
import urllib.error
import urllib.request
from abc import ABC, abstractmethod

from ..errors import FailClosed

USER_AGENT = ('VA-Industries-SourceProcurement/0.1 '
              '(+https://github.com/vaindustries2026/va-industries-engineering)')


class Transport:
    """Default HTTPS transport (urllib). Tests inject a fake with the same two methods."""

    def __init__(self, timeout=60):
        self.timeout = timeout

    def _open(self, url):
        if not url.startswith('https://'):
            raise FailClosed('TRANSPORT_NOT_HTTPS', url)
        req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
        try:
            return urllib.request.urlopen(req, timeout=self.timeout)
        except urllib.error.HTTPError as e:
            raise FailClosed('TRANSPORT_HTTP_ERROR', f'{e.code} {url}')
        except (urllib.error.URLError, OSError) as e:
            raise FailClosed('TRANSPORT_UNREACHABLE', f'{url}: {e}')

    def get_bytes(self, url, max_bytes):
        with self._open(url) as r:
            data = r.read(max_bytes + 1)
        if len(data) > max_bytes:
            raise FailClosed('TRANSPORT_RESPONSE_TOO_LARGE', url)
        return data

    def download(self, url, dest_path, max_bytes):
        total = 0
        with self._open(url) as r, open(dest_path, 'wb') as f:
            for chunk in iter(lambda: r.read(1 << 20), b''):
                total += len(chunk)
                if total > max_bytes:
                    raise FailClosed('DOWNLOAD_EXCEEDS_CAP', f'>{max_bytes} bytes')
                f.write(chunk)
        return total


class SourceAdapter(ABC):
    name = 'abstract'
    source_classes = ()

    @abstractmethod
    def discover(self, query, limit):
        """Return candidate items: dicts with the authority's item id, file url, size,
        integrity digest(s), mime, and raw rights fields (see rights.evaluate)."""

    @abstractmethod
    def allowed_file_host(self, url):
        """True only for the authority's own file host."""

    @abstractmethod
    def verify_integrity(self, item, path):
        """Compare downloaded bytes with the authority's published digest/size. Raise on mismatch."""
