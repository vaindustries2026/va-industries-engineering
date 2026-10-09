"""Input and output contracts for motion generation. Provider-neutral."""
import hashlib
from dataclasses import asdict, dataclass, field

from ..errors import FailClosed


def text_sha256(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


@dataclass(frozen=True)
class MotionRequest:
    shot_id: str
    source_frame_path: str
    source_frame_sha256: str
    motion_prompt: str
    negative_constraints: str
    duration_seconds: float
    aspect_ratio: str
    resolution: str
    fps_target: int
    provider: str
    provider_model: str
    approval_scope_id: str
    provider_params: dict = field(default_factory=dict)

    @property
    def prompt_sha256(self):
        return text_sha256(self.motion_prompt)

    @property
    def negative_sha256(self):
        return text_sha256(self.negative_constraints)

    def validate(self):
        for k in ('shot_id', 'source_frame_path', 'motion_prompt', 'provider', 'provider_model', 'approval_scope_id'):
            if not getattr(self, k):
                raise FailClosed('MOTION_REQUEST_INCOMPLETE', k)
        if len(self.source_frame_sha256 or '') != 64:
            raise FailClosed('MOTION_REQUEST_INCOMPLETE', 'source_frame_sha256')
        if not (0 < self.duration_seconds <= 30):
            raise FailClosed('MOTION_REQUEST_INVALID', f'duration {self.duration_seconds}')
        return True

    def to_dict(self):
        d = asdict(self)
        d['prompt_sha256'] = self.prompt_sha256
        d['negative_constraints_sha256'] = self.negative_sha256
        return d


@dataclass
class MotionResult:
    provider: str
    provider_model: str
    provider_job_id: str
    source_frame_sha256: str
    prompt_hash: str
    provider_status: str
    raw_output_path: str = None
    raw_output_sha256: str = None
    raw_original_filename: str = None
    raw_bytes: int = None
    raw_duration: float = None
    raw_resolution: str = None
    raw_fps: str = None
    raw_codec: str = None
    created_at: str = None
    cost_or_usage_if_available: object = None
    status: str = 'REVIEW'

    def to_dict(self):
        return asdict(self)
