"""Deterministic numpy compositing primitives.

Layers are float64 premultiplied RGBA in [0, 1]. Pure arithmetic only, so a
fixed input and numpy build give identical output. Final frames are rounded
once with np.rint to uint8.
"""
import numpy as np

from .errors import FailClosed


def to_premul(rgba_u8):
    f = rgba_u8.astype(np.float64) / 255.0
    f[..., :3] *= f[..., 3:4]
    return f


def to_rgb_u8(premul_on_opaque):
    return np.rint(np.clip(premul_on_opaque[..., :3], 0.0, 1.0) * 255.0).astype(np.uint8)


def crop(img, x, y, w, h):
    H, W = img.shape[:2]
    if x < 0 or y < 0 or x + w > W or y + h > H or w <= 0 or h <= 0:
        raise FailClosed('CROP_OUT_OF_BOUNDS', f'{(x, y, w, h)} in {W}x{H}')
    return img[y:y + h, x:x + w].copy()


def key_light_background(rgba_u8, lo, hi):
    """Alpha from the darkest channel: near-white background (min channel >= hi) becomes transparent.

    Pixels with min channel <= lo stay opaque; linear ramp in between. Existing alpha is preserved.
    """
    rgb = rgba_u8[..., :3].astype(np.float64)
    m = rgb.min(axis=2)
    a = np.clip((hi - m) / float(hi - lo), 0.0, 1.0)
    out = rgba_u8.copy()
    out[..., 3] = np.rint(a * (rgba_u8[..., 3].astype(np.float64))).astype(np.uint8)
    return out


def trim_alpha(rgba_u8, threshold=8):
    """Crop to the bounding box of alpha > threshold. Fails closed on an empty layer."""
    ys, xs = np.nonzero(rgba_u8[..., 3] > threshold)
    if len(xs) == 0:
        raise FailClosed('EMPTY_ALPHA_LAYER')
    return rgba_u8[ys.min():ys.max() + 1, xs.min():xs.max() + 1].copy()


def flip_h(img):
    return img[:, ::-1].copy()


def disc_mask(h, w, cx, cy, r, feather):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float64)
    d = np.sqrt((xx + 0.5 - cx) ** 2 + (yy + 0.5 - cy) ** 2)
    return np.clip((r - d) / max(feather, 1e-9) + 0.5, 0.0, 1.0)


def apply_mask(premul, mask):
    out = premul.copy()
    out *= mask[..., None]
    return out


def over(dst, src, x, y, opacity=1.0):
    """Premultiplied 'over' of src onto dst at integer offset (x, y), clipped to dst. Returns new array."""
    out = dst.copy()
    H, W = dst.shape[:2]
    h, w = src.shape[:2]
    x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + w, W), min(y + h, H)
    if x0 >= x1 or y0 >= y1:
        return out
    s = src[y0 - y:y1 - y, x0 - x:x1 - x] * opacity
    d = out[y0:y1, x0:x1]
    out[y0:y1, x0:x1] = s + d * (1.0 - s[..., 3:4])
    return out


def tint(premul, rgb, amount):
    """Blend toward a colour inside the layer's own alpha (used for the glass sheen)."""
    out = premul.copy()
    col = np.array(rgb, dtype=np.float64) / 255.0
    out[..., :3] = out[..., :3] * (1 - amount) + col * out[..., 3:4] * amount
    return out


def rotate(premul, degrees, cx, cy):
    """Rigid rotation about (cx, cy) with bilinear sampling on premultiplied data; same canvas size."""
    if degrees == 0:
        return premul.copy()
    h, w = premul.shape[:2]
    t = np.deg2rad(degrees)
    c, s = np.cos(t), np.sin(t)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float64)
    dx, dy = xx + 0.5 - cx, yy + 0.5 - cy
    sx = c * dx + s * dy + cx - 0.5   # inverse map (rotate by -t)
    sy = -s * dx + c * dy + cy - 0.5
    x0, y0 = np.floor(sx).astype(np.int64), np.floor(sy).astype(np.int64)
    fx, fy = (sx - x0)[..., None], (sy - y0)[..., None]
    pad = np.zeros((h + 2, w + 2, 4))
    pad[1:-1, 1:-1] = premul

    def at(yi, xi):
        return pad[np.clip(yi + 1, 0, h + 1), np.clip(xi + 1, 0, w + 1)]

    return (at(y0, x0) * (1 - fx) * (1 - fy) + at(y0, x0 + 1) * fx * (1 - fy)
            + at(y0 + 1, x0) * (1 - fx) * fy + at(y0 + 1, x0 + 1) * fx * fy)


def glint_sprite(size, core_rgb=(255, 252, 240)):
    """Procedural soft specular glint: radial core plus a faint 4-point star. Deterministic."""
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float64)
    c = (size - 1) / 2.0
    dx, dy = (xx - c) / c, (yy - c) / c
    r = np.sqrt(dx ** 2 + dy ** 2)
    core = np.exp(-(r / 0.22) ** 2)
    rays = np.exp(-(np.abs(dx) / 0.05) ** 2) * np.exp(-(np.abs(dy) / 0.65) ** 2) \
        + np.exp(-(np.abs(dy) / 0.05) ** 2) * np.exp(-(np.abs(dx) / 0.65) ** 2)
    a = np.clip(core + 0.45 * rays, 0, 1) * np.clip(1.0 - r, 0, 1)
    out = np.zeros((size, size, 4))
    col = np.array(core_rgb, dtype=np.float64) / 255.0
    out[..., :3] = col * a[..., None]
    out[..., 3] = a
    return out


def brightness_pulse(premul_frame, gain):
    """Completion-accent bloom primitive: additive lift toward white by `gain` (0..1), clipped."""
    out = premul_frame.copy()
    out[..., :3] = out[..., :3] + (out[..., 3:4] - out[..., :3]) * gain
    return out
