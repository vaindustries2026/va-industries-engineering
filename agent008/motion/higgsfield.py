"""Higgsfield implementation of MotionGenerationProvider.

The sanctioned route is the official Higgsfield API (`HiggsfieldApiTransport`), with the
credential supplied by the execution environment's AuthBoundary (Claude cloud: egress
proxy network secret; elsewhere e.g. an n8n credential). The read-only MCP connector is
not a generation route.

Paid-call guards owned here (defence in depth beyond the runner):
- submit requires a bound, human-approved, single-attempt SpendAuthorisation that matches
  the exact request (bound by the runner after the ledger reservation) and is consumed by
  that one submit;
- submit requires the hosted source URL produced by the integrity-checked upload stage;
- models whose official contract is not VERIFIED cannot be submitted.
Without a transport the adapter fails closed before any spend.
"""
import json
from pathlib import Path

from ..errors import FailClosed
from .higgsfield_transport import API_MODELS, load_api_models, resolve_model
from .provider import MotionGenerationProvider

CATALOG = Path(__file__).resolve().parent / 'higgsfield_video_models_2026-10-09.json'


def require_paid_authorisation(auth, req=None):
    """Higgsfield spend policy: explicit, human-approved, exactly one attempt, provider HIGGSFIELD."""
    if auth is None:
        raise FailClosed('SPEND_AUTHORISATION_MISSING')
    if str(auth.provider).upper() != 'HIGGSFIELD':
        raise FailClosed('AUTHORISATION_SCOPE_MISMATCH', 'provider')
    if getattr(auth, 'human_approved', False) is not True:
        raise FailClosed('AUTHORISATION_NOT_HUMAN_APPROVED')
    if auth.max_generations != 1:
        raise FailClosed('AUTHORISATION_ATTEMPTS_NOT_ONE', str(auth.max_generations))
    if req is not None:
        auth.matches(req)
    return True


class HiggsfieldProvider(MotionGenerationProvider):
    name = 'higgsfield'
    requires_hosted_source = True
    requires_human_approved_authorisation = True

    def __init__(self, transport=None, catalog_path=CATALOG, api_models_path=API_MODELS):
        self.transport = transport
        self.catalog = json.loads(Path(catalog_path).read_text())['models']
        self.api = load_api_models(api_models_path)
        self._bound = None

    def credentials_present(self):
        return bool(self.transport is not None and getattr(self.transport, 'sanctioned', False)
                    and self.transport.credentials_present())

    def _require(self):
        if not self.credentials_present():
            raise FailClosed('PROVIDER_CREDENTIAL_MISSING', 'no sanctioned Higgsfield API transport configured')

    def official_model(self, model):
        return resolve_model(self.api, model)

    def capabilities(self, model):
        mid, rec = resolve_model(self.api, model)
        if rec:
            caps = dict(rec)
            caps['official_model_id'] = mid
            return caps
        return self.catalog.get(model)

    def bind_authorisation(self, auth, reservation):
        """Called by the runner after the ledger reservation; one-shot."""
        require_paid_authorisation(auth)
        self._bound = (auth, reservation)

    def submit(self, request):
        self._require()
        bound, self._bound = self._bound, None          # consumed by this one submit, success or failure
        if bound is None:
            raise FailClosed('SPEND_AUTHORISATION_MISSING', 'no bound authorisation for this submit')
        auth, reservation = bound
        require_paid_authorisation(auth, request)
        self.validate_request(request)
        if not request.source_frame_url:
            raise FailClosed('SOURCE_URL_MISSING', 'hosted approved source frame required (image_url)')
        key = f'{auth.approval_scope_id}:{reservation.get("attempt_number")}'
        return self.transport.submit(request, request.source_frame_url, key)

    def poll(self, provider_job_id):
        self._require()
        return self.transport.poll(provider_job_id)

    def fetch(self, provider_job_id, dest_dir):
        self._require()
        return self.transport.retrieve(provider_job_id, dest_dir)

    retrieve = fetch

    def prepare_source_upload(self, data, content_type, expected_sha256):
        self._require()
        return self.transport.prepare_source_upload(data, content_type, expected_sha256)
