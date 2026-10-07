"""Output specification. Configurable per run; NOT a channel-wide canon decision."""
import json
from dataclasses import asdict, dataclass
from fractions import Fraction
from pathlib import Path

from .errors import FailClosed

CONFIG_DIR = Path(__file__).resolve().parent / 'config'


@dataclass(frozen=True)
class OutputSpec:
    spec_id: str
    width: int
    height: int
    fps: int
    pixel_format: str
    video_codec: str
    x264_preset: str
    x264_crf: int
    audio_sample_rate: int
    audio_channels: int
    review_audio_codec: str
    review_audio_bitrate: str
    peak_ceiling_dbfs: float
    output_status: str
    canon_decision: bool

    def frames_for(self, seconds):
        """Exact frame count for a duration; fail closed if not frame-aligned."""
        n = Fraction(str(seconds)) * self.fps
        if n.denominator != 1:
            raise FailClosed('DURATION_NOT_FRAME_ALIGNED', f'{seconds}s at {self.fps} fps')
        return int(n)

    def to_dict(self):
        return asdict(self)


def load_output_spec(path=None):
    p = Path(path) if path else CONFIG_DIR / 'output_spec_phase0_review.json'
    d = json.loads(p.read_text())
    d.pop('_comment', None)
    spec = OutputSpec(**d)
    if spec.output_status != 'REVIEW':
        raise FailClosed('OUTPUT_STATUS_NOT_REVIEW', 'Phase 0 outputs are REVIEW only')
    if spec.canon_decision:
        raise FailClosed('OUTPUT_SPEC_MARKED_CANON', 'Phase 0 output spec must not be a canon decision')
    return spec
