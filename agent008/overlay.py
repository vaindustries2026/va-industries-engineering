"""G03: deterministic overlay placement on an approved shot frame (zero spend, no provider).

Composites the shot's governed, shot-active berry overlays onto one hash-verified, human-approved shot frame,
exactly as a human-approved placement record states, and writes a new lossless PNG. Inputs are never written.
The output is a REVIEW candidate only (proposed SHOT_FRAME / DERIVED_FRAME): it becomes a shot asset after human
approval of its exact SHA-256 and a separately authorised registration. Nothing here registers or uploads.

Only what the approved EP005 shot contracts need is supported (evidence/agent008/g03/G03_CONTRACT_v1.md):
persistent whole-shot overlays, several per frame, each asset at most once per surface (FACE, REFLECTION), CENTER
anchor at an integer pixel position in base-frame pixels, deterministic width scale (aspect kept, no upscale),
optional rotation, mirror reversal for the reflection surface, full opacity, no overlap between overlays, no
clipping. Everything else (partial opacity, z-order, other anchors, frame windows, in-shot removal = G11, clipping)
fails closed. The approved frame produced here is consumed unchanged by the G02 still path, or uploaded as the
motion base frame so persistent smudges move with the provider motion without tracking.
"""
import json
import math
from pathlib import Path

import numpy as np

from . import AGENT_NAME, compositor as C, media
from .derive import decode_png_rgb, write_png_rgb
from .errors import FailClosed
from .hashing import canonical_sha256, sha256_bytes, sha256_file, verify_file

AGENT_VERSION_G03 = 'agent008-v0.3-overlay-placement'
CONTRACT_ID = 'AGENT008_G03_OVERLAY_PLACEMENT_v1'
FRAME_CLASSIFICATIONS = ('SHOT_FRAME/BASE_FRAME', 'SHOT_FRAME/DERIVED_FRAME')
APPROVED_STATES = ('APPROVED', 'LOCKED')
OVERLAY_ASSET_TYPE = 'OVERLAY_VFX'
SURFACES = ('FACE', 'REFLECTION')
ANCHORS = ('CENTER',)
ALPHA_TRIM_THRESHOLD = 8                    # same trim as the Phase-0 compositor (compositor.trim_alpha)
MAX_ROTATION_DEG = 180.0
RECORD_KEYS = {'contract', 'record_id', 'shot_id', 'base_frame', 'frame_size', 'frame_range', 'placements'}
PLACEMENT_KEYS = {'asset_id', 'overlay_sha256', 'surface', 'anchor', 'x', 'y', 'width_px', 'rotation_deg', 'mirror',
                  'opacity'}
Z_ORDER_KEYS = {'z', 'z_order', 'z_index', 'layer', 'order'}
REMOVAL_KEYS = {'remove_at_frame', 'removal_frame', 'end_frame', 'start_frame', 'visible_frames', 'frame_range'}
REQUIRED_PROVENANCE = ('agent_version', 'status', 'shot_id', 'source_frame', 'placement_record', 'placements',
                       'overlays_composited', 'output', 'proposed_registry', 'human_approval', 'safety')


def _int(v, code, what):
    if not isinstance(v, int) or isinstance(v, bool):
        raise FailClosed(code, f'{what}: {v!r} is not an integer')
    return v


def validate_record(placement, spec_shot, frame_size):
    """placement: {record, approval_status, expected_sha256}. Returns (record, record_sha256). Fail closed."""
    if not isinstance(placement, dict) or 'record' not in placement:
        raise FailClosed('PLACEMENT_RECORD_MISSING', spec_shot['shot_id'])
    if placement.get('approval_status') not in APPROVED_STATES:
        raise FailClosed('PLACEMENT_RECORD_NOT_APPROVED', str(placement.get('approval_status')))
    rec = placement['record']
    rec_sha = canonical_sha256(rec)
    if not placement.get('expected_sha256'):
        raise FailClosed('NO_EXPECTED_HASH', 'placement record')
    if rec_sha != placement['expected_sha256']:
        raise FailClosed('PLACEMENT_RECORD_HASH_MISMATCH', f"expected {placement['expected_sha256']}, got {rec_sha}")
    extra = set(rec) - RECORD_KEYS
    if extra:
        raise FailClosed('PLACEMENT_FIELD_UNSUPPORTED', f'record: {sorted(extra)}')
    if rec.get('contract') != CONTRACT_ID:
        raise FailClosed('PLACEMENT_CONTRACT_UNKNOWN', str(rec.get('contract')))
    if rec.get('shot_id') != spec_shot['shot_id']:
        raise FailClosed('SHOT_IDENTITY_MISMATCH', f"record for {rec.get('shot_id')}, shot {spec_shot['shot_id']}")
    if list(rec.get('frame_size') or []) != list(frame_size):
        raise FailClosed('PLACEMENT_FRAME_SIZE_MISMATCH', f"record {rec.get('frame_size')}, frame {list(frame_size)}")
    if 'frame_range' not in rec:
        raise FailClosed('OVERLAY_TIMING_UNDECLARED', spec_shot['shot_id'])
    fr = rec['frame_range']
    if not isinstance(fr, list) or len(fr) != 2 or [_int(fr[0], 'OVERLAY_FRAME_RANGE_INVALID', 'start'),
                                                     _int(fr[1], 'OVERLAY_FRAME_RANGE_INVALID', 'end')] \
            != [0, spec_shot['frames'] - 1]:
        raise FailClosed('OVERLAY_FRAME_RANGE_INVALID',
                         f"{fr}: persistent overlays must cover the whole shot [0, {spec_shot['frames'] - 1}]")
    if not isinstance(rec.get('placements'), list) or not rec['placements']:
        raise FailClosed('PLACEMENT_RECORD_EMPTY', spec_shot['shot_id'])
    return rec, rec_sha


def validate_placement(p, W, H):
    keys = set(p)
    if keys & Z_ORDER_KEYS:
        raise FailClosed('OVERLAY_Z_ORDER_UNSUPPORTED', f'{sorted(keys & Z_ORDER_KEYS)}: overlays may not overlap, so '
                                                        'no order is governed')
    if keys & REMOVAL_KEYS:
        raise FailClosed('OVERLAY_REMOVAL_UNSUPPORTED_G11', f'{sorted(keys & REMOVAL_KEYS)}: per-overlay timing or '
                                                            'removal is not G03')
    extra = keys - PLACEMENT_KEYS
    if extra:
        raise FailClosed('PLACEMENT_FIELD_UNSUPPORTED', sorted(extra))
    missing = (PLACEMENT_KEYS - {'rotation_deg', 'opacity'}) - keys
    if missing:
        raise FailClosed('PLACEMENT_FIELD_MISSING', f"{p.get('asset_id')}: {sorted(missing)}")
    if p['surface'] not in SURFACES:
        raise FailClosed('OVERLAY_SURFACE_UNSUPPORTED', f"{p['asset_id']}: {p['surface']!r}")
    if p['anchor'] not in ANCHORS:
        raise FailClosed('OVERLAY_ANCHOR_UNSUPPORTED', f"{p['asset_id']}: {p['anchor']!r}")
    if not isinstance(p['mirror'], bool):
        raise FailClosed('OVERLAY_MIRROR_INVALID', f"{p['asset_id']}: {p['mirror']!r}")
    if p['mirror'] != (p['surface'] == 'REFLECTION'):          # manifest: "preserve correct mirror reversal"
        raise FailClosed('OVERLAY_MIRROR_RULE', f"{p['asset_id']}: surface {p['surface']} with mirror={p['mirror']}")
    x = _int(p['x'], 'OVERLAY_COORDINATE_INVALID', 'x')
    y = _int(p['y'], 'OVERLAY_COORDINATE_INVALID', 'y')
    if not (0 <= x < W and 0 <= y < H):
        raise FailClosed('OVERLAY_COORDINATE_INVALID', f"{p['asset_id']}: anchor ({x}, {y}) outside {W}x{H}")
    w = p['width_px']
    if not isinstance(w, int) or isinstance(w, bool) or w < 2:
        raise FailClosed('OVERLAY_SCALE_INVALID', f"{p['asset_id']}: width_px {w!r} (integer >= 2 required)")
    rot = p.get('rotation_deg', 0)
    if isinstance(rot, bool) or not isinstance(rot, (int, float)) or not math.isfinite(rot) \
            or abs(rot) > MAX_ROTATION_DEG:
        raise FailClosed('OVERLAY_ROTATION_INVALID', f"{p['asset_id']}: {rot!r}")
    op = p.get('opacity', 1.0)
    if isinstance(op, bool) or not isinstance(op, (int, float)) or op != 1.0:
        raise FailClosed('OVERLAY_OPACITY_INVALID', f"{p['asset_id']}: {op!r} (only full opacity 1.0 is governed)")
    return x, y, w, float(rot)


def check_overlay_assets(spec_shot, overlay_paths):
    """Shot-active overlays from the spec: governed, approved, hashed and present on disk. Returns {asset_id: sha}."""
    out = {}
    for o in spec_shot['active_overlays']:
        aid = o['asset_id']
        if aid in out:
            raise FailClosed('OVERLAY_DUPLICATE_IDENTITY', aid)
        if o.get('asset_type') != OVERLAY_ASSET_TYPE:
            raise FailClosed('OVERLAY_ASSET_WRONG_TYPE', f"{aid}: {o.get('asset_type')}")
        if o.get('status') not in APPROVED_STATES:
            raise FailClosed('OVERLAY_ASSET_NOT_APPROVED', f"{aid}: {o.get('status')}")
        if not o.get('expected_sha256'):
            raise FailClosed('NO_EXPECTED_HASH', aid)
        if aid not in overlay_paths:
            raise FailClosed('OVERLAY_ASSET_MISSING', aid)
        out[aid] = verify_file(overlay_paths[aid], o['expected_sha256'], f'overlay {aid}')
    for aid in overlay_paths:
        if aid not in out:
            raise FailClosed('OVERLAY_NOT_IN_SHOT_CONTRACT', f'{aid} supplied but not active in {spec_shot["shot_id"]}')
    return out


def overlay_layer(path, width_px, rotation_deg, mirror):
    """Alpha-trim, scale to width_px (aspect kept, rounded height, no upscale), mirror, rotate. Premultiplied f64."""
    rgba = C.trim_alpha(media.load_rgba(path), ALPHA_TRIM_THRESHOLD)
    th, tw = rgba.shape[:2]
    if width_px > tw:
        raise FailClosed('OVERLAY_SCALE_INVALID', f'{Path(path).name}: width_px {width_px} upscales trimmed width {tw}')
    h = max(1, int(round(th * width_px / tw)))
    layer = C.to_premul(media.scale_rgba(rgba, width_px, h))
    if mirror:
        layer = C.flip_h(layer)
    if rotation_deg:
        pad = int(math.ceil(math.hypot(width_px, h))) + 2
        canvas = C.over(np.zeros((pad, pad, 4)), layer, (pad - width_px) // 2, (pad - h) // 2)
        layer = C.rotate(canvas, rotation_deg, pad / 2.0, pad / 2.0)
    return layer, {'trimmed_size': [tw, th], 'scaled_size': [width_px, h], 'layer_size': [layer.shape[1], layer.shape[0]]}


def precomposited_overlay_set(spec_shot, composited, frame_sha256=None):
    """Downstream check (G02 still / motion base frame): the frame's G03 overlay set equals the shot's active set."""
    want = {o['asset_id']: o.get('expected_sha256') for o in spec_shot['active_overlays']}
    if not composited:
        if want:
            raise FailClosed('STILL_OVERLAYS_NEED_G03_ANCHORS', f"{spec_shot['shot_id']}: {sorted(want)}")
        return []
    if composited.get('shot_id') != spec_shot['shot_id']:
        raise FailClosed('SHOT_IDENTITY_MISMATCH', f"G03 frame for {composited.get('shot_id')}")
    if frame_sha256 is not None and composited.get('frame_sha256') != frame_sha256:
        raise FailClosed('OVERLAY_PRECOMPOSITE_FRAME_MISMATCH', f"{composited.get('frame_sha256')} vs {frame_sha256}")
    got = {}
    for o in composited.get('overlays') or []:
        got.setdefault(o['asset_id'], set()).add(o['sha256'])
    if sorted(got) != sorted(want) or any(got[a] != {want[a]} for a in want):
        raise FailClosed('OVERLAY_PRECOMPOSITE_MISMATCH', f'frame {sorted(got)} vs shot contract {sorted(want)}')
    return sorted(want)


def place_overlays(spec_shot, frame, overlay_paths, placement, out_dir):
    """Write one REVIEW overlay frame. frame: {asset_id, registry_id, classification, registry_status, shot_id,
    path, expected_sha256}. overlay_paths: {asset_id: path} for exactly the shot-active overlays.
    placement: {record, approval_status, expected_sha256} (human-approved record bound by canonical SHA-256)."""
    out_dir = Path(out_dir)
    sid = spec_shot['shot_id']
    if not spec_shot['active_overlays']:
        raise FailClosed('OVERLAY_NONE_REQUIRED', f'{sid} has no active overlays')
    if frame.get('classification') not in FRAME_CLASSIFICATIONS:
        raise FailClosed('OVERLAY_SOURCE_NOT_A_SHOT_FRAME', f"{frame.get('asset_id')}: {frame.get('classification')}")
    if frame.get('registry_status') not in APPROVED_STATES:
        raise FailClosed('OVERLAY_SOURCE_NOT_APPROVED', f"{frame.get('asset_id')}: {frame.get('registry_status')}")
    if frame.get('shot_id') != sid:
        raise FailClosed('SHOT_IDENTITY_MISMATCH', f"frame for {frame.get('shot_id')}, shot {sid}")
    if frame.get('overlays_composited'):
        raise FailClosed('OVERLAY_ALREADY_COMPOSITED', str(frame.get('asset_id')))
    if not frame.get('expected_sha256'):
        raise FailClosed('NO_EXPECTED_HASH', str(frame.get('asset_id')))
    src = Path(frame['path'])
    frame_sha = verify_file(src, frame['expected_sha256'], f"overlay base frame {frame.get('asset_id')}")
    ov_sha = check_overlay_assets(spec_shot, overlay_paths)

    base = media.load_rgba(src)
    H, W = base.shape[:2]
    if int(base[..., 3].min()) != 255:
        raise FailClosed('OVERLAY_SOURCE_HAS_TRANSPARENCY', str(src))
    rec, rec_sha = validate_record(placement, spec_shot, (W, H))
    bf = rec.get('base_frame') or {}
    if bf.get('asset_id') != frame.get('asset_id') or bf.get('sha256') != frame_sha:
        raise FailClosed('PLACEMENT_RECORD_BASE_FRAME_MISMATCH', f'record {bf}, frame {frame.get("asset_id")} {frame_sha}')

    seen, geo = set(), []
    for p in rec['placements']:
        x, y, w, rot = validate_placement(p, W, H)
        aid = p['asset_id']
        if aid not in ov_sha:
            raise FailClosed('OVERLAY_NOT_IN_SHOT_CONTRACT', f'{aid} is not active in {sid}')
        if p['overlay_sha256'] != ov_sha[aid]:
            raise FailClosed('OVERLAY_SHA_MISMATCH', f"{aid}: record {p['overlay_sha256']}, governed {ov_sha[aid]}")
        if (aid, p['surface']) in seen:
            raise FailClosed('OVERLAY_DUPLICATE_PLACEMENT', f"{aid} on {p['surface']}")
        seen.add((aid, p['surface']))
        geo.append((p['surface'], aid, x, y, w, rot, p['mirror']))
    unplaced = sorted(set(ov_sha) - {a for a, _ in seen})
    if unplaced:
        raise FailClosed('OVERLAY_PLACEMENT_MISSING', f'{sid}: {unplaced}')

    canvas = C.to_premul(base)
    coverage = np.zeros((H, W), np.int32)
    placed = []
    for surface, aid, x, y, w, rot, mirror in sorted(geo):          # fixed canonical order; overlap is rejected
        layer, sizes = overlay_layer(overlay_paths[aid], w, rot, mirror)
        lh, lw = layer.shape[:2]
        ox, oy = x - lw // 2, y - lh // 2
        ys, xs = np.nonzero(layer[..., 3] > 0)
        if len(xs) == 0:
            raise FailClosed('EMPTY_ALPHA_LAYER', aid)
        bx0, by0, bx1, by1 = ox + int(xs.min()), oy + int(ys.min()), ox + int(xs.max()) + 1, oy + int(ys.max()) + 1
        if bx0 < 0 or by0 < 0 or bx1 > W or by1 > H:
            raise FailClosed('OVERLAY_OUT_OF_BOUNDS', f'{aid} on {surface}: visible box {(bx0, by0, bx1, by1)} in {W}x{H}')
        mask = np.zeros((H, W), bool)
        mask[oy + ys, ox + xs] = True
        if (coverage[mask] > 0).any():
            raise FailClosed('OVERLAY_OVERLAP_UNDECLARED', f'{aid} on {surface} overlaps an earlier overlay')
        coverage[mask] += 1
        canvas = C.over(canvas, layer, ox, oy)
        placed.append({'asset_id': aid, 'sha256': ov_sha[aid], 'surface': surface, 'anchor': 'CENTER',
                       'x': x, 'y': y, 'width_px': w, 'rotation_deg': rot, 'mirror': mirror, 'opacity': 1.0,
                       'layer_offset': [ox, oy], 'visible_box': [bx0, by0, bx1, by1],
                       'visible_pixels': int(mask.sum()), **sizes})
    out = C.to_rgb_u8(canvas)
    untouched = coverage == 0
    if not np.array_equal(out[untouched], base[..., :3][untouched]):
        raise FailClosed('OVERLAY_UNEXPECTED_PIXEL_CHANGE', 'pixels outside the placed overlays changed')

    out_dir.mkdir(parents=True, exist_ok=True)
    png = out_dir / f'{sid}_G03_OVERLAY_FRAME_CANDIDATE.png'
    if png.exists():
        raise FailClosed('OUTPUT_EXISTS', str(png))
    if png.resolve() == src.resolve() or any(png.resolve() == Path(p).resolve() for p in overlay_paths.values()):
        raise FailClosed('OUTPUT_WOULD_OVERWRITE_SOURCE', str(png))
    write_png_rgb(out, png)
    out_rgb_sha = sha256_bytes(out.tobytes())
    if sha256_bytes(decode_png_rgb(png).tobytes()) != out_rgb_sha:
        raise FailClosed('OVERLAY_FRAME_NOT_LOSSLESS', png.name)
    if sha256_file(src) != frame_sha or any(sha256_file(overlay_paths[a]) != s for a, s in ov_sha.items()):
        raise FailClosed('SOURCE_MUTATED', 'base frame or overlay asset changed during placement')
    out_sha = sha256_file(png)
    composited = {'shot_id': sid, 'frame_sha256': out_sha,
                  'overlays': [{'asset_id': p['asset_id'], 'sha256': p['sha256'], 'surface': p['surface']} for p in placed]}
    prov = {
        'agent': AGENT_NAME, 'agent_version': AGENT_VERSION_G03, 'stage': 'G03 overlay placement', 'status': 'REVIEW',
        'shot_id': sid,
        'source_frame': {k: frame.get(k) for k in ('asset_id', 'registry_id', 'classification', 'registry_status')}
                        | {'verified_sha256': frame_sha, 'width': W, 'height': H, 'sha256_after': frame_sha},
        'placement_record': {'record_id': rec.get('record_id'), 'sha256': rec_sha, 'contract': CONTRACT_ID,
                             'approval_status': placement['approval_status'], 'frame_range': rec['frame_range']},
        'placements': placed, 'overlays_composited': composited,
        'recipe': {'trim': f'alpha > {ALPHA_TRIM_THRESHOLD} bounding box', 'scale_flags': media.SCALE_FLAGS,
                   'mirror': 'horizontal flip after scale (REFLECTION surface)', 'rotation': 'compositor.rotate bilinear, '
                   'premultiplied, about the padded layer centre', 'composite': 'compositor.over premultiplied float64, '
                   'one final rint', 'order': 'sorted (surface, asset_id); overlaps rejected',
                   'png': 'ffmpeg png encoder, rgb24, bitexact, no metadata'},
        'output': {'file': png.name, 'sha256': out_sha, 'bytes': png.stat().st_size, 'width': W, 'height': H,
                   'rgb24_sha256': out_rgb_sha, 'lossless_roundtrip': True,
                   'changed_pixels_outside_overlays': 0},
        'proposed_registry': {'asset_type': 'SHOT_FRAME', 'asset_subtype': 'DERIVED_FRAME', 'shot_id': sid,
                              'registered': False, 'requires': 'human approval of output.sha256, then a separately '
                                                              'authorised storage write + registration'},
        'human_approval': {'required': True, 'approved': False, 'decisions': ['APPROVE', 'REJECT'],
                           'approve_by': 'exact output png sha256'},
        'safety': {'provider_calls': 0, 'source_mutated': False, 'auto_approved': False, 'registered': False},
        'toolchain': media.toolchain(),
    }
    missing = [k for k in REQUIRED_PROVENANCE if k not in prov]
    if missing:
        raise FailClosed('PROVENANCE_INCOMPLETE', ','.join(missing))
    prov['deterministic_core_sha256'] = canonical_sha256({k: v for k, v in prov.items() if k != 'toolchain'})
    (out_dir / f'{sid}_G03_OVERLAY_PROVENANCE.json').write_text(json.dumps(prov, indent=1, sort_keys=True) + '\n')
    return prov
