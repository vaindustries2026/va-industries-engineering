"""Higgsfield implementation of MotionGenerationProvider.

Access audit (2026-10-09): the connected Higgsfield MCP connector is READ-ONLY
(workspaces, balance, model catalogue, generation history, Claude-Motion import);
its own instructions state it cannot generate media, upload files or purchase.
No Higgsfield API credential exists in this environment, in n8n, or in the repo.

Therefore this adapter has no built-in transport. A sanctioned generation route
must be injected as a `transport` object exposing submit/poll/fetch and bound to
Higgsfield's official, documented API with a human-provided credential. Endpoints
are deliberately NOT guessed here (no reverse-engineered or cookie-based access).
Without a transport the adapter fails closed before any spend.
"""
import json
from pathlib import Path

from ..errors import FailClosed
from .provider import MotionGenerationProvider

CATALOG = Path(__file__).resolve().parent / 'higgsfield_video_models_2026-10-09.json'


class HiggsfieldProvider(MotionGenerationProvider):
    name = 'higgsfield'

    def __init__(self, transport=None, catalog_path=CATALOG):
        self.transport = transport
        self.catalog = json.loads(Path(catalog_path).read_text())['models']

    def credentials_present(self):
        return bool(self.transport is not None and getattr(self.transport, 'sanctioned', False)
                    and self.transport.credentials_present())

    def _require(self):
        if not self.credentials_present():
            raise FailClosed('PROVIDER_CREDENTIAL_MISSING',
                             'no sanctioned Higgsfield generation route (MCP connector is read-only; no API credential)')

    def capabilities(self, model):
        return self.catalog.get(model)

    def submit(self, request):
        self._require()
        self.validate_request(request)
        return self.transport.submit(request)

    def poll(self, provider_job_id):
        self._require()
        return self.transport.poll(provider_job_id)

    def fetch(self, provider_job_id, dest_dir):
        self._require()
        return self.transport.fetch(provider_job_id, dest_dir)
