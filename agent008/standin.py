"""NON_CANON_TECHNICAL_STANDIN builder for EP005 S004/S005.

Crops approved canon sheets into a stand-in composition so the compositor can
be proven without a provider call. The result is REVIEW_ONLY and never
registered as an asset.
"""
import json
from pathlib import Path

from . import compositor as C
from . import media
from .errors import FailClosed
from .hashing import sha256_file

LAYOUT_DIR = Path(__file__).resolve().parent / 'layouts'
REQUIRED_CLASSIFICATION = {'NON_CANON_TECHNICAL_STANDIN', 'REVIEW_ONLY', 'NOT_FOR_EPISODE_PUBLICATION'}


def load_layout(path=None):
    p = Path(path) if path else LAYOUT_DIR / 'ep005_s004_s005_standin_v1.json'
    lay = json.loads(p.read_text())
    if not REQUIRED_CLASSIFICATION <= set(lay.get('classification', [])):
        raise FailClosed('STANDIN_NOT_MARKED_NON_CANON', p.name)
    return lay


class Scaler:
    def __init__(self, layout, spec):
        rw, rh = layout['reference_canvas']
        if spec.width * rh != spec.height * rw:
            raise FailClosed('ASPECT_MISMATCH', f'layout {rw}x{rh} vs spec {spec.width}x{spec.height}')
        self.k = spec.width / rw

    def __call__(self, v):
        return int(round(v * self.k))


def _keyed(path, rect, key):
    img = C.crop(media.load_rgba(path), *rect)
    return C.key_light_background(img, key[0], key[1])


def _scale_to(img, w=None, h=None):
    ih, iw = img.shape[:2]
    if w is not None:
        h = max(1, int(round(ih * w / iw)))
    else:
        w = max(1, int(round(iw * h / ih)))
    return media.scale_rgba(img, w, h)


def build(asset_paths, layout, spec):
    """asset_paths: {asset_id: verified local path}. Returns the layer stack used by the renderer."""
    S = Scaler(layout, spec)
    W, H = spec.width, spec.height

    def path(aid):
        if aid not in asset_paths:
            raise FailClosed('STANDIN_ASSET_NOT_RESOLVED', aid)
        return asset_paths[aid]

    # background
    bg = layout['background']
    b = C.crop(media.load_rgba(path(bg['asset_id'])), *bg['source_rect'])
    b = media.scale_rgba(b, W, H)
    if bg.get('blur_sigma'):
        b = media.gblur_rgba(b, bg['blur_sigma'] * S.k)
    under = C.to_premul(b)

    # cloth (within Mikko's reach, unused)
    cl = layout['cloth']
    cloth = C.to_premul(_scale_to(_keyed(path(cl['asset_id']), cl['source_rect'], cl['key']), w=S(cl['width'])))
    under = C.over(under, cloth, S(cl['position'][0]), S(cl['position'][1]))

    # mirror group: reflection disc under a frame whose glass is cut out
    mi, rf = layout['mirror'], layout['reflection']
    mx, my, mw, mh = mi['source_rect']
    mirror_px_h = S(mi['height'])
    k_m = mirror_px_h / mh
    mirror_px_w = int(round(mw * k_m))
    frame = C.to_premul(media.scale_rgba(_keyed(path(mi['asset_id']), mi['source_rect'], mi['key']),
                                         mirror_px_w, mirror_px_h))
    gcx = (mi['glass_center_in_source'][0] - mx) * k_m
    gcy = (mi['glass_center_in_source'][1] - my) * k_m
    hole = C.disc_mask(mirror_px_h, mirror_px_w, gcx, gcy, mi['glass_hole_radius_in_source'] * k_m,
                       mi['glass_hole_feather'] * k_m)
    frame = C.apply_mask(frame, 1.0 - hole)

    rr = mi['reflection_radius_in_source'] * k_m
    D = int(round(2 * rr))
    face = C.crop(media.load_rgba(path(rf['character_asset_id'])), *rf['source_rect'])
    fs = rf['source_rect'][2]
    if rf['source_rect'][2] != rf['source_rect'][3]:
        raise FailClosed('REFLECTION_SOURCE_NOT_SQUARE')
    face = C.to_premul(media.scale_rgba(face, D, D))
    k_f = D / fs
    overlays_placed = []
    for aid, pl in sorted(rf['overlay_placements_unflipped'].items()):
        if aid not in asset_paths:
            continue  # only shot-active overlays are supplied; inactive ones are never drawn
        ov = C.trim_alpha(media.load_rgba(asset_paths[aid]))
        ov = C.to_premul(_scale_to(ov, w=max(2, int(round(pl['width'] * k_f)))))
        if pl.get('rotation_deg'):
            pad = max(ov.shape[:2])
            canvas = C.over(_blank(pad * 2, pad * 2), ov, pad - ov.shape[1] // 2, pad - ov.shape[0] // 2)
            ov = C.rotate(canvas, pl['rotation_deg'], pad, pad)
        cx, cy = pl['center'][0] * k_f, pl['center'][1] * k_f
        face = C.over(face, ov, int(round(cx - ov.shape[1] / 2)), int(round(cy - ov.shape[0] / 2)))
        overlays_placed.append(aid)
    if rf.get('mirror_flip'):
        face = C.flip_h(face)
    face = C.tint(face, rf['glass_tint_rgb'], rf['glass_tint_amount'])
    face = C.apply_mask(face, C.disc_mask(D, D, D / 2, D / 2, rr, 1.5 * S.k))

    group = _blank(mirror_px_h, mirror_px_w)
    gx0, gy0 = int(round(gcx - D / 2)), int(round(gcy - D / 2))
    group = C.over(group, face, gx0, gy0)
    group = C.over(group, frame, 0, 0)
    pivot = ((mi['pivot_in_source'][0] - mx) * k_m, (mi['pivot_in_source'][1] - my) * k_m)

    def reflection_to_group(pt_unflipped):
        x = pt_unflipped[0] * k_f
        if rf.get('mirror_flip'):
            x = D - x
        return gx0 + x, gy0 + pt_unflipped[1] * k_f

    # Lumi (beside the mirror, holder) and the non-canon banner
    lu = layout['lumi']
    lumi = C.to_premul(_scale_to(_keyed(path(lu['asset_id']), lu['source_rect'], lu['key']), h=S(lu['height'])))
    bn = layout['banner']
    font = Path(bn['font_file'])
    if not font.is_file():
        raise FailClosed('BANNER_FONT_MISSING', str(font))
    banner = C.to_premul(media.text_layer(bn['text'], str(font), S(bn['font_size']), W, S(bn['height'])))

    return {
        'under': under,
        'group': group, 'group_pos': (S(mi['position'][0]), S(mi['position'][1])), 'pivot': pivot,
        'reflection_to_group': reflection_to_group, 'scale': S.k,
        'over': [(lumi, S(lu['position'][0]), S(lu['position'][1])), (banner, 0, 0)],
        'overlays_drawn': overlays_placed,
        'font_sha256': sha256_file(font),
    }


def _blank(h, w):
    import numpy as np
    return np.zeros((h, w, 4))
