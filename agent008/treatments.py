"""Compositing treatments: deterministic operations, never canonical assets.

Each treatment declares its frame constraints. Only treatments that a shot's
approved contract assigns are executed; the others are defined and tested
but not applied.
"""
from .errors import FailClosed

TREATMENTS = {
    'TREATMENT-EP005-MIRROR-GLINT-v01': {
        'kind': 'GLINT',
        'min_frames': 6, 'max_frames': 10,
        'must_end_before_shot_end': True,
        'non_magical': True,
        # Opacity envelope sampled over the active frames (deterministic, symmetric-ish soft flash).
        'envelope': 'soft_attack_decay',
        'implemented_v01': True,
    },
    'TREATMENT-EP005-MIRROR-REFLECTION-v01': {
        'kind': 'MIRROR_REFLECTION',
        'operation': 'hflip character face, clip to mirror glass disc, apply only the shot-active berry overlays, light glass tint',
        'implemented_v01': True,   # primitive exists (compositor.flip_h/disc_mask/tint); not executed in Phase 0
        'executed_in_phase0': False,
    },
    'TREATMENT-EP005-COMPLETION-POP-ACCENT-v01': {
        'kind': 'BLOOM_PULSE',
        'min_frames': 6, 'max_frames': 8,
        'max_gain': 0.12,
        'must_not_change_overlay_state': True,
        'implemented_v01': True,   # compositor.brightness_pulse; not executed in Phase 0
        'executed_in_phase0': False,
    },
}


def treatment(tid):
    t = TREATMENTS.get(tid)
    if not t:
        raise FailClosed('TREATMENT_NOT_IMPLEMENTED', tid)
    return t


def envelope(kind, n):
    """Per-frame opacity multipliers for a treatment window of n frames."""
    if kind == 'soft_attack_decay':
        if n < 2:
            raise FailClosed('ENVELOPE_TOO_SHORT', str(n))
        peak = max(1, round(n * 0.3))
        out = []
        for i in range(n):
            if i <= peak:
                out.append(round(0.35 + 0.65 * i / peak, 6))
            else:
                out.append(round(1.0 - 0.9 * (i - peak) / (n - 1 - peak), 6))
        return out
    if kind == 'bloom':
        half = (n - 1) / 2.0
        return [round(1.0 - abs(i - half) / (half + 1), 6) for i in range(n)]
    raise FailClosed('UNKNOWN_ENVELOPE', kind)


def validate_window(tid, start_frame, n_frames, shot_frames):
    t = treatment(tid)
    lo, hi = t.get('min_frames'), t.get('max_frames')
    if lo is not None and not (lo <= n_frames <= hi):
        raise FailClosed('TREATMENT_FRAME_COUNT', f'{tid}: {n_frames} frames, allowed {lo}-{hi}')
    if start_frame < 0:
        raise FailClosed('TREATMENT_WINDOW_INVALID', tid)
    if t.get('must_end_before_shot_end') and start_frame + n_frames > shot_frames:
        raise FailClosed('TREATMENT_CROSSES_SHOT_BOUNDARY',
                         f'{tid}: frames {start_frame}..{start_frame + n_frames - 1} of {shot_frames}')
    return True
