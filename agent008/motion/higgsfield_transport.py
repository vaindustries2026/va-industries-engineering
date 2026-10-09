"""Official Higgsfield API transport (sanctioned route for HiggsfieldProvider).

Contract (verified 2026-10-09; see evidence/AGENT008_V02_HIGGSFIELD_TRANSPORT_WIRED_v1.0.md):
  POST {base}/files/generate-upload-url         {content_type} -> {upload_url, upload_headers, public_url}
  PUT  upload_url  (exact bytes; ONLY upload_headers; never the API credential)
  POST {base}/<model endpoint>                  {prompt, image_url, ...} -> {request_id, status_url, cancel_url, status}
  GET  {base}/requests/{request_id}/status      -> {status, video: {url}}
  statuses: queued | in_progress | completed | failed | nsfw | canceled

Rules: each request is sent once (no retry, unlike the SDK's POST backoff); the provider
credential is supplied by the AuthBoundary only to the API host and is never read, logged
or placed in an exception; malformed responses fail closed.
"""
import json
import logging
import re
from pathlib import Path
from urllib.parse import quote, urlsplit

from ..errors import FailClosed
from ..hashing import sha256_bytes
from .http import EnvironmentProxyAuth, UrllibHttpClient, redact

log = logging.getLogger('agent008.motion.higgsfield')

API_MODELS = Path(__file__).resolve().parent / 'higgsfield_api_models.json'
CONTENT_TYPES = {'image/png': b'\x89PNG\r\n\x1a\n', 'image/jpeg': b'\xff\xd8\xff', 'image/webp': b'RIFF'}
STATE_MAP = {'queued': 'QUEUED', 'in_progress': 'RUNNING', 'completed': 'COMPLETED',
             'failed': 'FAILED', 'nsfw': 'FAILED', 'canceled': 'FAILED', 'cancelled': 'FAILED'}
HTTP_CODES = {400: 'PROVIDER_BAD_INPUT', 401: 'PROVIDER_AUTH_REJECTED', 403: 'PROVIDER_INSUFFICIENT_CREDITS_OR_FORBIDDEN',
              404: 'PROVIDER_NOT_FOUND', 422: 'PROVIDER_VALIDATION_ERROR', 429: 'PROVIDER_RATE_LIMITED'}
_ID = re.compile(r'^[A-Za-z0-9._-]{1,128}$')


def load_api_models(path=API_MODELS):
    return json.loads(Path(path).read_text())


def resolve_model(cfg, model):
    """Official model id or alias -> (official_id, record). None when unknown."""
    models = cfg['models']
    if model in models:
        return model, models[model]
    for mid, rec in models.items():
        if model in rec.get('aliases', []):
            return mid, rec
    return None, None


def _https(url, what):
    if not isinstance(url, str) or urlsplit(url).scheme != 'https' or not urlsplit(url).hostname:
        raise FailClosed('PROVIDER_RESPONSE_MALFORMED', f'{what} is not an https URL')
    return url


def serialize_request(request, model_record, image_url):
    """Provider-neutral MotionRequest -> official JSON body for the model. Pure; no I/O."""
    if not image_url:
        raise FailClosed('SOURCE_URL_MISSING', 'image_url (hosted approved source frame) is required')
    _https(image_url, 'image_url')
    d = request.duration_seconds
    lo, hi = model_record['duration_range']
    if not (lo <= d <= hi):
        raise FailClosed('DURATION_NOT_SUPPORTED', f'{d} outside {model_record["duration_range"]}')
    if model_record.get('duration_integer'):
        if float(d) != int(d):
            raise FailClosed('DURATION_NOT_SUPPORTED', f'{d} must be a whole number of seconds')
        d = int(d)
    ser = model_record['serializer']
    if ser == 'seedance_2_0_i2v':
        body = {'prompt': request.motion_prompt, 'image_url': image_url, 'duration': d,
                'resolution': request.resolution}
        if model_record.get('resolutions') and request.resolution not in model_record['resolutions']:
            raise FailClosed('RESOLUTION_NOT_SUPPORTED', request.resolution)
    elif ser == 'kling_3_0_i2v':
        body = {'prompt': request.motion_prompt, 'image_url': image_url, 'duration': d}
    else:
        raise FailClosed('MODEL_SERIALIZER_UNKNOWN', ser)
    body.update(model_record.get('fixed_fields', {}))
    extra = set(body) - set(model_record['allowed_fields'])
    if extra:
        raise FailClosed('REQUEST_FIELD_NOT_IN_OFFICIAL_SCHEMA', ','.join(sorted(extra)))
    missing = [f for f in model_record['required_fields'] if not body.get(f)]
    if missing:
        raise FailClosed('REQUEST_FIELD_MISSING', ','.join(missing))
    return body


class HiggsfieldApiTransport:
    """HTTP transport bound to the official Higgsfield API. Holds no credential."""
    sanctioned = True

    def __init__(self, auth=None, http=None, api_models_path=API_MODELS, timeout=60.0):
        self.cfg = load_api_models(api_models_path)
        self.base = self.cfg['base_url'].rstrip('/')
        self.auth = auth if auth is not None else EnvironmentProxyAuth()
        self.http = http if http is not None else UrllibHttpClient()
        self.timeout = timeout
        self.requests = {}          # request_id -> submit record
        self.outputs = {}           # request_id -> completed video url

    def __repr__(self):
        return f'HiggsfieldApiTransport(base={self.base!r}, auth={self.auth!r})'

    def credentials_present(self):
        return self.auth.configured()

    # ---------------- low-level -----------------
    def _api(self, method, path, payload=None, extra_headers=None):
        url = self.base + path
        if not self.auth.is_api_host(url):
            raise FailClosed('API_HOST_NOT_AUTHENTICATED', urlsplit(url).hostname)
        headers = {'Accept': 'application/json'}
        body = None
        if payload is not None:
            headers['Content-Type'] = 'application/json'
            body = json.dumps(payload, separators=(',', ':')).encode()
        headers.update(extra_headers or {})
        headers.update(self.auth.headers_for(url))
        log.info('higgsfield %s %s', method, path)          # never headers or bodies
        resp = self.http.send(method, url, headers, body, self.timeout)
        return resp, self.auth.secrets_for_redaction()

    def _json(self, resp, secrets, what):
        if resp.status >= 300:
            code = HTTP_CODES.get(resp.status, 'PROVIDER_SERVER_ERROR' if resp.status >= 500 else 'PROVIDER_HTTP_ERROR')
            snippet = redact(resp.body[:300].decode('utf-8', 'replace'), secrets)
            raise FailClosed(code, f'{what}: HTTP {resp.status} {snippet}')
        try:
            data = json.loads(resp.body)
        except (ValueError, TypeError):
            raise FailClosed('PROVIDER_RESPONSE_MALFORMED', f'{what}: not JSON') from None
        if not isinstance(data, dict):
            raise FailClosed('PROVIDER_RESPONSE_MALFORMED', f'{what}: not an object')
        return data

    def status_route(self, request_id):
        if not isinstance(request_id, str) or not _ID.match(request_id):
            raise FailClosed('PROVIDER_RESPONSE_MALFORMED', 'request_id')
        return self.cfg['routes']['request_status'].format(request_id=quote(request_id, safe=''))

    # ---------------- source upload -----------------
    def prepare_source_upload(self, data, content_type, expected_sha256, verify_readback=True):
        """Signed upload of exact bytes; returns a provenance record with public_url. PAID-GATED by caller."""
        if content_type not in CONTENT_TYPES:
            raise FailClosed('SOURCE_CONTENT_TYPE_INVALID', str(content_type))
        if sha256_bytes(data) != expected_sha256:
            raise FailClosed('SOURCE_SHA_MISMATCH', 'bytes to upload differ from the approved sha256')
        resp, secrets = self._api('POST', self.cfg['routes']['generate_upload_url'], {'content_type': content_type})
        info = self._json(resp, secrets, 'generate-upload-url')
        upload_url = _https(info.get('upload_url'), 'upload_url')
        public_url = _https(info.get('public_url'), 'public_url')
        upload_headers = info.get('upload_headers', {})
        if upload_headers is None:
            upload_headers = {}
        if not isinstance(upload_headers, dict) or not all(isinstance(k, str) and isinstance(v, str)
                                                           for k, v in upload_headers.items()):
            raise FailClosed('PROVIDER_RESPONSE_MALFORMED', 'upload_headers')
        ct = {k.lower(): v for k, v in upload_headers.items()}.get('content-type')
        if ct is not None and ct != content_type:
            raise FailClosed('UPLOAD_CONTENT_TYPE_MISMATCH', f'{ct} != {content_type}')
        self._storage_put(upload_url, data, upload_headers)
        rec = {'public_url': public_url, 'upload_host': urlsplit(upload_url).hostname, 'content_type': content_type,
               'sha256': expected_sha256, 'bytes': len(data), 'readback': 'NOT_ATTEMPTED'}
        if verify_readback:
            r = self.http.send('GET', public_url, {}, None, self.timeout)
            if r.status != 200:
                raise FailClosed('SOURCE_READBACK_FAILED', f'HTTP {r.status}')
            got = sha256_bytes(r.body)
            if got != expected_sha256:
                raise FailClosed('SOURCE_READBACK_SHA_MISMATCH', f'expected {expected_sha256}, got {got}')
            rec['readback'] = 'SHA256_MATCH'
        return rec

    def _storage_put(self, upload_url, data, upload_headers):
        """PUT to the signed storage URL with ONLY the headers Higgsfield returned. No API credential."""
        if self.auth.is_api_host(upload_url) or self.auth.injects_for(upload_url):
            raise FailClosed('UPLOAD_URL_WOULD_RECEIVE_PROVIDER_AUTH', urlsplit(upload_url).hostname)
        headers = dict(upload_headers)
        log.info('higgsfield storage PUT host=%s bytes=%d', urlsplit(upload_url).hostname, len(data))
        r = self.http.send('PUT', upload_url, headers, data, self.timeout)
        if not (200 <= r.status < 300):
            raise FailClosed('SOURCE_UPLOAD_FAILED_NO_RETRY', f'HTTP {r.status}')

    # ---------------- lifecycle -----------------
    def submit(self, request, image_url, idempotency_key):
        """ONE POST to the model endpoint. PAID. Never retried."""
        mid, rec = resolve_model(self.cfg, request.provider_model)
        if not rec:
            raise FailClosed('MODEL_NOT_SUPPORTED', request.provider_model)
        if rec.get('contract_status') != 'VERIFIED' or not rec.get('submit_enabled'):
            raise FailClosed('MODEL_CONTRACT_NOT_VERIFIED', mid)
        body = serialize_request(request, rec, image_url)
        resp, secrets = self._api('POST', rec['endpoint'], body, {'Idempotency-Key': idempotency_key})
        data = self._json(resp, secrets, 'submit')
        rid = data.get('request_id')
        route = self.status_route(rid)
        if data.get('status_url') not in (None, self.base + route):
            raise FailClosed('PROVIDER_STATUS_URL_UNEXPECTED', 'status_url does not match the documented route')
        self.requests[rid] = {'request_id': rid, 'model': mid, 'status_url': self.base + route,
                              'cancel_url': data.get('cancel_url'), 'initial_status': data.get('status'),
                              'payload': body}
        return rid

    def poll(self, request_id):
        """Read-only GET /requests/{request_id}/status. Normalised to the provider-neutral states."""
        resp, secrets = self._api('GET', self.status_route(request_id))
        if resp.status >= 500:
            return {'status': 'RUNNING', 'provider_status': None, 'detail': f'HTTP {resp.status}; read-only poll continues'}
        data = self._json(resp, secrets, 'status')
        raw = data.get('status')
        if raw not in STATE_MAP:
            raise FailClosed('PROVIDER_RESPONSE_MALFORMED', f'unknown status {str(raw)[:40]!r}')
        out = {'status': STATE_MAP[raw], 'provider_status': raw, 'usage': data.get('usage') or data.get('credits')}
        if raw == 'completed':
            video = data.get('video')
            if not isinstance(video, dict):
                raise FailClosed('PROVIDER_RESPONSE_MALFORMED', 'completed without video')
            out['output_url'] = _https(video.get('url'), 'video.url')
            self.outputs[request_id] = out['output_url']
        elif STATE_MAP[raw] == 'FAILED':
            out['detail'] = f'provider status {raw}' + (f': {str(data.get("error"))[:200]}' if data.get('error') else '')
        return out

    def retrieve(self, request_id, dest_dir):
        """Download the completed output unchanged. Returns (path, original_filename)."""
        url = self.outputs.get(request_id)
        if not url:
            raise FailClosed('OUTPUT_NOT_COMPLETED', request_id)
        if self.auth.is_api_host(url):
            raise FailClosed('PROVIDER_RESPONSE_MALFORMED', 'output url on API host')
        r = self.http.send('GET', url, {}, None, self.timeout)
        if r.status != 200 or not r.body:
            raise FailClosed('OUTPUT_DOWNLOAD_FAILED_NO_RETRY', f'HTTP {r.status}')
        original = Path(urlsplit(url).path).name or f'{request_id}.mp4'
        if not re.match(r'^[A-Za-z0-9._-]{1,200}$', original):
            original = f'{request_id}.mp4'
        path = Path(dest_dir) / original
        if path.exists():
            raise FailClosed('RAW_OUTPUT_EXISTS', str(path))
        path.write_bytes(r.body)
        return path, original

    fetch = retrieve
