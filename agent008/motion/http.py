"""Minimal HTTP layer and authentication boundaries for provider transports.

Agent-008 never reads, stores, prints or logs a provider credential. How a request to
the provider API is authenticated is decided by an AuthBoundary chosen by the
execution environment:

- EnvironmentProxyAuth: Claude cloud. An egress proxy injects the credential for the
  provider API host; application code adds no auth header.
- SuppliedHeaderAuth: another runtime (e.g. a future n8n wrapper) supplies a header
  value at send time through its own credential mechanism; the value is never kept.

Every request is sent exactly once (no retry at this layer).
"""
import os
import ssl
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from urllib.parse import urlsplit

from ..errors import FailClosed


@dataclass
class HttpResponse:
    status: int
    headers: dict = field(default_factory=dict)
    body: bytes = b''


class HttpClient:
    """Interface: send one request, return HttpResponse. Must not retry."""

    def send(self, method, url, headers, body=None, timeout=60.0):
        raise NotImplementedError


class UrllibHttpClient(HttpClient):
    """Standard-library client. Honours the environment's HTTPS proxy and CA bundle."""

    def __init__(self):
        cafile = next((os.environ[k] for k in ('SSL_CERT_FILE', 'REQUESTS_CA_BUNDLE', 'CURL_CA_BUNDLE')
                       if os.environ.get(k)), None)
        self._ctx = ssl.create_default_context(cafile=cafile)

    def send(self, method, url, headers, body=None, timeout=60.0):
        req = urllib.request.Request(url, data=body, method=method, headers=dict(headers))
        try:
            with urllib.request.urlopen(req, timeout=timeout, context=self._ctx) as r:
                return HttpResponse(r.status, dict(r.headers), r.read())
        except urllib.error.HTTPError as e:
            return HttpResponse(e.code, dict(e.headers or {}), e.read() or b'')
        except (urllib.error.URLError, OSError) as e:
            # Never include request headers in the error.
            raise FailClosed('HTTP_TRANSPORT_ERROR', f'{method} {_host(url)}: {type(e).__name__}') from None


def _host(url):
    return (urlsplit(url).hostname or '').lower()


class AuthBoundary:
    """Decides which headers (if any) authenticate a request to the provider API hosts."""
    name = 'abstract'
    api_hosts = ()

    def configured(self):
        return False

    def is_api_host(self, url):
        return _host(url) in self.api_hosts

    def headers_for(self, url):
        """Auth headers for url. Empty for any host that is not a provider API host."""
        return {}

    def injects_for(self, url):
        """True when a credential would reach url without application code adding it (proxy injection)."""
        return False

    def secrets_for_redaction(self):
        return ()


class EnvironmentProxyAuth(AuthBoundary):
    """Credential injected by the environment's egress proxy for api_hosts (Claude cloud network secret).

    `declared` records that the environment operator configured the injection; it was
    verified on 2026-10-09 by an authenticated read-only GET returning HTTP 200.
    """
    name = 'environment_proxy'

    def __init__(self, api_hosts=('api.higgsfield.ai',), declared=True):
        self.api_hosts = tuple(h.lower() for h in api_hosts)
        self.declared = declared

    def configured(self):
        return bool(self.declared)

    def injects_for(self, url):
        return self.is_api_host(url)

    def __repr__(self):
        return f'EnvironmentProxyAuth(api_hosts={self.api_hosts!r})'


class SuppliedHeaderAuth(AuthBoundary):
    """Header value supplied per request by the host runtime (e.g. an n8n credential). Never stored."""
    name = 'supplied_header'

    def __init__(self, supplier, header='Authorization', api_hosts=('api.higgsfield.ai',)):
        self._supplier = supplier
        self.header = header
        self.api_hosts = tuple(h.lower() for h in api_hosts)
        self._last = ()

    def configured(self):
        return callable(self._supplier)

    def headers_for(self, url):
        if not self.is_api_host(url):
            return {}
        v = self._supplier()
        self._last = (v,)
        return {self.header: v}

    def secrets_for_redaction(self):
        return self._last

    def __repr__(self):
        return f'SuppliedHeaderAuth(header={self.header!r}, api_hosts={self.api_hosts!r})'


def redact(text, secrets):
    for s in secrets:
        if s:
            text = text.replace(s, '[REDACTED]')
            for part in s.split():          # e.g. "Key id:secret" -> also redact "id:secret"
                if len(part) >= 8:
                    text = text.replace(part, '[REDACTED]')
    return text
