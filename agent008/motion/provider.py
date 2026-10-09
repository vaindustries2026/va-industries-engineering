"""MotionGenerationProvider: the only interface Agent-008 uses for generated motion.

Implementations: HiggsfieldProvider (first), test providers. A new provider is
added by implementing this class; the compositor (8D) never changes because it
only consumes the hashed raw output recorded in MotionResult.
"""
from abc import ABC, abstractmethod

TERMINAL_OK = 'COMPLETED'
TERMINAL_FAILED = 'FAILED'


class MotionGenerationProvider(ABC):
    name = 'abstract'

    @abstractmethod
    def credentials_present(self):
        """True only when a sanctioned generation route is configured. Never reads browser cookies."""

    @abstractmethod
    def capabilities(self, model):
        """Static capability record: durations, resolutions, aspect ratios, media roles, controls."""

    @abstractmethod
    def submit(self, request):
        """Submit exactly one image-to-video job (no variations). Returns provider_job_id. PAID."""

    @abstractmethod
    def poll(self, provider_job_id):
        """Read-only status: {'status': 'QUEUED'|'RUNNING'|'COMPLETED'|'FAILED', 'usage': ..., 'detail': ...}."""

    @abstractmethod
    def fetch(self, provider_job_id, dest_dir):
        """Download the raw result unchanged into dest_dir. Returns (path, original_filename)."""

    def validate_request(self, request):
        caps = self.capabilities(request.provider_model)
        from ..errors import FailClosed
        if not caps:
            raise FailClosed('MODEL_NOT_SUPPORTED', request.provider_model)
        d = request.duration_seconds
        if 'durations' in caps and d not in caps['durations']:
            raise FailClosed('DURATION_NOT_SUPPORTED', f'{d} not in {caps["durations"]}')
        if 'duration_range' in caps and not (caps['duration_range'][0] <= d <= caps['duration_range'][1]):
            raise FailClosed('DURATION_NOT_SUPPORTED', f'{d} outside {caps["duration_range"]}')
        if caps.get('aspect_ratios') and request.aspect_ratio not in caps['aspect_ratios']:
            raise FailClosed('ASPECT_NOT_SUPPORTED', request.aspect_ratio)
        if caps.get('resolutions') and request.resolution not in caps['resolutions']:
            raise FailClosed('RESOLUTION_NOT_SUPPORTED', request.resolution)
        if 'start_image' not in caps.get('media_roles', []):
            raise FailClosed('IMAGE_TO_VIDEO_NOT_SUPPORTED', request.provider_model)
        return True
