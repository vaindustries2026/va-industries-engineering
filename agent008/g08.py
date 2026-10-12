"""G08: governed visual treatments on approved shot frames (zero spend, no provider).

Only the three treatments the approved EP005 manifest assigns are supported (evidence/agent008/g08/G08_CONTRACT_v1.md):

  TREATMENT-EP005-MIRROR-REFLECTION-v01  static, whole shot. "Composite or preserve" Mikko's reflection inside the mirror
                                          glass while the glass itself stays clean. PRESERVE: the approved frame already
                                          shows the reflection; the reflected marks are the G03 REFLECTION placements and are
                                          verified to lie inside the glass, and no mark may sit on the glass. COMPOSITE: a
                                          declared face region of the frame (after G03 FACE overlays) is left-right reversed,
                                          scaled (no upscale), lightly tinted and clipped to the glass ellipse. Output: a
                                          REVIEW frame (COMPOSITE) or a certificate bound to the unchanged frame (PRESERVE).
  TREATMENT-EP005-MIRROR-GLINT-v01       timed, 6-10 frames, procedural soft specular sprite on the glass, drawn above the
                                          reflected content with the soft attack/decay opacity envelope.
  TREATMENT-EP005-COMPLETION-POP-ACCENT-v01 timed, 6-8 frames, brightness/bloom pulse (gain <= 0.12) restricted to the glass,
                                          on a clean frame only (zero berry overlays).

Geometry comes from a human-approved treatment record bound by its canonical SHA-256 to the shot and to the exact frame
the treatments start from. Operation order is fixed: base frame -> G03 overlays -> G08 reflection (static) -> [G07 cut,
later] -> G08 glint -> G08 pop. Anything else fails closed. Nothing here registers, uploads or calls a provider.
"""
import json
import math
from pathlib import Path

import numpy as np

from . import AGENT_NAME, compositor as C, media
from .derive import decode_png_rgb, write_png_rgb
from .errors import FailClosed
from .hashing import canonical_sha256, sha256_bytes, sha256_file, verify_file
from .overlay import precomposited_overlay_set
from .treatments import TREATMENTS, envelope, validate_window

AGENT_VERSION_G08 = 'agent008-v0.3-treatments'
CONTRACT_ID = 'AGENT008_G08_TREATMENTS_v1'
REFL = 'TREATMENT-EP005-MIRROR-REFLECTION-v01'
GLINT = 'TREATMENT-EP005-MIRROR-GLINT-v01'
POP = 'TREATMENT-EP005-COMPLETION-POP-ACCENT-v01'
SUPPORTED = (REFL, GLINT, POP)
STATIC, TIMED = (REFL,), (GLINT, POP)
FRAME_CLASSIFICATIONS = ('SHOT_FRAME/BASE_FRAME', 'SHOT_FRAME/DERIVED_FRAME')
APPROVED_STATES = ('APPROVED', 'LOCKED')
REFLECTION_MODES = ('PRESERVE', 'COMPOSITE')
MAX_TINT = 0.10                     # "light glass tint" (Phase-0 reference 0.07); contract guard
MAX_FEATHER_PX = 4
# Manifest-governed per-shot constraints (G08 requirement audit, approved manifest 0325d35c).
GOVERNED = {
    'sync': {('S004', GLINT): 'SFX-LUMI-CLUE-CHIME',          # "synchronized with the initial mirror tilt and clue chime"
             ('S025', POP): 'SFX-COMPLETION-POP-v01'},       # "synchronised with the completion-pop audio"
    'glint_target': {'S004': 'OVERLAY-EP005-BERRY-SMUDGE-CHEEK-v01',   # "near the selected cheek"
                     'S012': 'OVERLAY-EP005-BERRY-SMUDGE-MOUTH-v01'},  # "to the reflected mouth-area clue"
}
RECORD_KEYS = {'contract', 'record_id', 'shot_id', 'input_frame', 'frame_size', 'frame_range', 'mirror_glass',
               'reflection', 'glint', 'pop'}
GLASS_KEYS = {'shape', 'cx', 'cy', 'rx', 'ry', 'feather_px'}
REFL_KEYS = {'PRESERVE': {'mode', 'reflected_overlays'},
             'COMPOSITE': {'mode', 'reflected_overlays', 'source_rect', 'flip', 'target_center', 'target_width_px',
                           'tint_rgb', 'tint_amount'}}
GLINT_KEYS = {'treatment_id', 'start_frame', 'frames', 'cx', 'cy', 'size_px', 'target_overlay', 'sync_audio_asset_id'}
POP_KEYS = {'treatment_id', 'start_frame', 'frames', 'gain', 'sync_audio_asset_id'}
SECTION = {REFL: 'reflection', GLINT: 'glint', POP: 'pop'}


def _int(v, code, what):
    if not isinstance(v, int) or isinstance(v, bool):
        raise FailClosed(code, f'{what}: {v!r} is not an integer')
    return v


def _num(v, code, what):
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
        raise FailClosed(code, f'{what}: {v!r}')
    return float(v)


def _keys(d, allowed, required, where):
    if not isinstance(d, dict):
        raise FailClosed('TREATMENT_FIELD_INVALID', where)
    extra = set(d) - allowed
    if extra:
        raise FailClosed('TREATMENT_FIELD_UNSUPPORTED', f'{where}: {sorted(extra)}')
    missing = required - set(d)
    if missing:
        raise FailClosed('TREATMENT_FIELD_MISSING', f'{where}: {sorted(missing)}')


# --- mirror glass geometry (axis-aligned ellipse, pixel-edge coordinates) ---
def in_glass(g, x, y):
    return ((x + 0.5 - g['cx']) / g['rx']) ** 2 + ((y + 0.5 - g['cy']) / g['ry']) ** 2 <= 1.0


def box_in_glass(g, box):
    x0, y0, x1, y1 = box
    return all(in_glass(g, x, y) for x, y in ((x0, y0), (x1 - 1, y0), (x0, y1 - 1), (x1 - 1, y1 - 1)))


def glass_mask(H, W, g, feather=None):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float64)
    d = np.sqrt(((xx + 0.5 - g['cx']) / g['rx']) ** 2 + ((yy + 0.5 - g['cy']) / g['ry']) ** 2)
    f = g.get('feather_px', 0) if feather is None else feather
    if not f:
        return (d <= 1.0).astype(np.float64)
    return np.clip((1.0 - d) * min(g['rx'], g['ry']) / f + 0.5, 0.0, 1.0)


def box_touches_glass(g, box, H, W):
    x0, y0, x1, y1 = (max(0, box[0]), max(0, box[1]), min(W, box[2]), min(H, box[3]))
    if x0 >= x1 or y0 >= y1:
        return False
    return bool(glass_mask(H, W, g, feather=0)[y0:y1, x0:x1].any())


def validate_glass(g, W, H):
    _keys(g, GLASS_KEYS, GLASS_KEYS - {'feather_px'}, 'mirror_glass')
    if g['shape'] != 'ELLIPSE':
        raise FailClosed('TREATMENT_MASK_UNSUPPORTED', f"mirror_glass shape {g['shape']!r} (ELLIPSE only)")
    cx, cy = _int(g['cx'], 'TREATMENT_COORDINATE_INVALID', 'glass cx'), _int(g['cy'], 'TREATMENT_COORDINATE_INVALID', 'glass cy')
    rx, ry = _int(g['rx'], 'TREATMENT_MASK_UNSUPPORTED', 'glass rx'), _int(g['ry'], 'TREATMENT_MASK_UNSUPPORTED', 'glass ry')
    if rx < 2 or ry < 2:
        raise FailClosed('TREATMENT_MASK_UNSUPPORTED', f'glass radii {rx}x{ry}')
    if cx - rx < 0 or cy - ry < 0 or cx + rx > W or cy + ry > H:
        raise FailClosed('TREATMENT_COORDINATE_INVALID', f'glass ellipse ({cx},{cy}) r=({rx},{ry}) outside {W}x{H}')
    f = _int(g.get('feather_px', 0), 'TREATMENT_MASK_UNSUPPORTED', 'feather_px')
    if not 0 <= f <= MAX_FEATHER_PX:
        raise FailClosed('TREATMENT_MASK_UNSUPPORTED', f'feather_px {f} (0..{MAX_FEATHER_PX})')
    return {'shape': 'ELLIPSE', 'cx': cx, 'cy': cy, 'rx': rx, 'ry': ry, 'feather_px': f}


# --- record ---
def spec_treatments(spec_shot):
    ids = [t['treatment_id'] for t in spec_shot['treatments']]
    if len(ids) != len(set(ids)):
        raise FailClosed('TREATMENT_DUPLICATE_INVOCATION', f"{spec_shot['shot_id']}: {ids}")
    for t in ids:
        if t not in SUPPORTED:
            raise FailClosed('TREATMENT_UNSUPPORTED', t)
    return ids


def validate_record(treatment, spec_shot, input_frame_sha, frame_size):
    """treatment: {record, approval_status, expected_sha256}. Returns (record, record_sha, glass)."""
    sid = spec_shot['shot_id']
    if not isinstance(treatment, dict) or 'record' not in treatment:
        raise FailClosed('TREATMENT_RECORD_MISSING', sid)
    if treatment.get('approval_status') not in APPROVED_STATES:
        raise FailClosed('TREATMENT_RECORD_NOT_APPROVED', str(treatment.get('approval_status')))
    rec = treatment['record']
    if not treatment.get('expected_sha256'):
        raise FailClosed('NO_EXPECTED_HASH', 'treatment record')
    rec_sha = canonical_sha256(rec)
    if rec_sha != treatment['expected_sha256']:
        raise FailClosed('TREATMENT_RECORD_HASH_MISMATCH', f"expected {treatment['expected_sha256']}, got {rec_sha}")
    _keys(rec, RECORD_KEYS, {'contract', 'shot_id', 'input_frame', 'frame_size', 'frame_range', 'mirror_glass'}, 'record')
    if rec['contract'] != CONTRACT_ID:
        raise FailClosed('TREATMENT_CONTRACT_UNKNOWN', str(rec['contract']))
    if rec['shot_id'] != sid:
        raise FailClosed('SHOT_IDENTITY_MISMATCH', f"record for {rec['shot_id']}, shot {sid}")
    if (rec['input_frame'] or {}).get('sha256') != input_frame_sha:
        raise FailClosed('TREATMENT_RECORD_FRAME_MISMATCH', f"record {rec['input_frame']}, frame {input_frame_sha}")
    if list(rec['frame_size']) != list(frame_size):
        raise FailClosed('TREATMENT_FRAME_SIZE_MISMATCH', f"record {rec['frame_size']}, frame {list(frame_size)}")
    if rec['frame_range'] != [0, spec_shot['frames'] - 1]:
        raise FailClosed('TREATMENT_FRAME_RANGE_INVALID', f"{rec['frame_range']} (shot is 0..{spec_shot['frames'] - 1})")
    assigned = spec_treatments(spec_shot)
    for tid, sec in SECTION.items():
        if sec in rec and tid not in assigned:
            raise FailClosed('TREATMENT_UNDECLARED', f'{sid}: record carries {sec} but the shot contract does not assign {tid}')
        if tid in assigned and sec not in rec:
            raise FailClosed('TREATMENT_RECORD_INCOMPLETE', f'{sid}: {tid} assigned but no {sec} entry')
    return rec, rec_sha, validate_glass(rec['mirror_glass'], *frame_size)


def _frame_checks(spec_shot, frame, label):
    if frame.get('classification') not in FRAME_CLASSIFICATIONS:
        raise FailClosed('TREATMENT_SOURCE_NOT_A_SHOT_FRAME', f"{frame.get('asset_id')}: {frame.get('classification')}")
    if frame.get('registry_status') not in APPROVED_STATES:
        raise FailClosed('TREATMENT_SOURCE_NOT_APPROVED', f"{frame.get('asset_id')}: {frame.get('registry_status')}")
    if frame.get('shot_id') != spec_shot['shot_id']:
        raise FailClosed('SHOT_IDENTITY_MISMATCH', f"frame for {frame.get('shot_id')}, shot {spec_shot['shot_id']}")
    if not frame.get('expected_sha256'):
        raise FailClosed('NO_EXPECTED_HASH', str(frame.get('asset_id')))
    return verify_file(frame.get('path') or '', frame['expected_sha256'], f"{label} {frame.get('asset_id')}")


def g03_placements(spec_shot, frame, frame_sha, g03_provenance):
    """Authenticated G03 placements for the frame (empty for a clean frame)."""
    comp = frame.get('overlays_composited')
    if spec_shot.get('clean_reveal') and (spec_shot['active_overlays'] or comp):
        raise FailClosed('CLEAN_REVEAL_HAS_ACTIVE_OVERLAYS', spec_shot['shot_id'])
    precomposited_overlay_set(spec_shot, comp, frame_sha) if (spec_shot['active_overlays'] or comp) else None
    if not comp:
        return []
    p = g03_provenance or {}
    core = {k: v for k, v in p.items() if k not in ('toolchain', 'deterministic_core_sha256')}
    if not p or p.get('deterministic_core_sha256') != canonical_sha256(core) or (p.get('output') or {}).get('sha256') != frame_sha \
            or p.get('overlays_composited') != comp:
        raise FailClosed('G03_PROVENANCE_MISMATCH', 'the G03 provenance does not authenticate this frame')
    return p['placements']


# --- static stage: mirror reflection ---
def apply_reflection(spec_shot, frame, treatment, out_dir, g03_provenance=None):
    """Run the static MIRROR_REFLECTION stage. Returns provenance with 'treatments_composited'."""
    out_dir, sid = Path(out_dir), spec_shot['shot_id']
    if REFL not in spec_treatments(spec_shot):
        raise FailClosed('TREATMENT_UNDECLARED', f'{sid}: {REFL} not assigned')
    if frame.get('treatments_composited'):
        raise FailClosed('TREATMENT_DUPLICATE_INVOCATION', f"{frame.get('asset_id')} already carries G08 treatments")
    src = Path(frame.get('path') or '')
    frame_sha = _frame_checks(spec_shot, frame, 'treatment frame')
    placements = g03_placements(spec_shot, frame, frame_sha, g03_provenance)
    base = media.load_rgba(src)
    H, W = base.shape[:2]
    if int(base[..., 3].min()) != 255:
        raise FailClosed('TREATMENT_SOURCE_HAS_TRANSPARENCY', str(src))
    rec, rec_sha, glass = validate_record(treatment, spec_shot, frame_sha, (W, H))
    r = rec['reflection']
    if not isinstance(r, dict) or r.get('mode') not in REFLECTION_MODES:
        raise FailClosed('MIRROR_SEMANTICS_UNSUPPORTED', f"reflection mode {(r or {}).get('mode')!r}")
    _keys(r, REFL_KEYS[r['mode']], REFL_KEYS[r['mode']], f"reflection {r['mode']}")
    declared = r['reflected_overlays']
    active = {o['asset_id'] for o in spec_shot['active_overlays']}
    if not isinstance(declared, list) or len(declared) != len(set(declared)) or not set(declared) <= active:
        raise FailClosed('REFLECTED_OVERLAYS_INVALID', f'{declared} vs active {sorted(active)}')
    if spec_shot.get('clean_reveal') and declared:
        raise FailClosed('CLEAN_REVEAL_HAS_ACTIVE_OVERLAYS', f'{sid}: reflection declares {declared}')
    face = [p for p in placements if p['surface'] == 'FACE']
    refl = [p for p in placements if p['surface'] == 'REFLECTION']
    for p in face:                                              # QC: "no dirt or smudge is placed on the mirror surface"
        if box_touches_glass(glass, p['visible_box'], H, W):
            raise FailClosed('OVERLAY_ON_MIRROR_GLASS', f"{p['asset_id']} FACE mark touches the mirror glass")
    out_img, recipe, reflected = base[..., :3].copy(), None, []
    if r['mode'] == 'PRESERVE':
        for p in refl:
            if not box_in_glass(glass, p['visible_box']):
                raise FailClosed('REFLECTED_MARK_OUTSIDE_GLASS', f"{p['asset_id']}: {p['visible_box']}")
        reflected = sorted(p['asset_id'] for p in refl)
    else:
        if refl:
            raise FailClosed('REFLECTION_DOUBLE_SOURCE', 'COMPOSITE copies the reflected marks; G03 REFLECTION placements '
                                                         'would duplicate them')
        if r['flip'] != 'HORIZONTAL':
            raise FailClosed('MIRROR_SEMANTICS_UNSUPPORTED', f"flip {r['flip']!r} (left-right reversal only)")
        sr = r['source_rect']
        if not isinstance(sr, list) or len(sr) != 4:
            raise FailClosed('TREATMENT_COORDINATE_INVALID', f'source_rect {sr!r}')
        sx, sy, sw, sh = (_int(v, 'TREATMENT_COORDINATE_INVALID', 'source_rect') for v in sr)
        if sx < 0 or sy < 0 or sw < 2 or sh < 2 or sx + sw > W or sy + sh > H:
            raise FailClosed('TREATMENT_COORDINATE_INVALID', f'source_rect {sr} in {W}x{H}')
        if box_touches_glass(glass, [sx, sy, sx + sw, sy + sh], H, W):
            raise FailClosed('REFLECTION_SOURCE_ON_GLASS', f'source_rect {sr} overlaps the mirror glass')
        tw = r['target_width_px']
        if not isinstance(tw, int) or isinstance(tw, bool) or tw < 2 or tw > sw:
            raise FailClosed('TREATMENT_SCALE_INVALID', f'target_width_px {tw!r} (integer 2..{sw}, no upscale)')
        tc = r['target_center']
        if not isinstance(tc, list) or len(tc) != 2:
            raise FailClosed('TREATMENT_COORDINATE_INVALID', f'target_center {tc!r}')
        tcx, tcy = (_int(v, 'TREATMENT_COORDINATE_INVALID', 'target_center') for v in tc)
        if not in_glass(glass, tcx, tcy):
            raise FailClosed('TREATMENT_COORDINATE_INVALID', f'target_center {tc} outside the mirror glass')
        tint = r['tint_rgb']
        if not isinstance(tint, list) or len(tint) != 3 or any(not isinstance(v, int) or isinstance(v, bool) or not 0 <= v <= 255
                                                                for v in tint):
            raise FailClosed('TREATMENT_FIELD_INVALID', f'tint_rgb {tint!r}')
        ta = _num(r['tint_amount'], 'TREATMENT_FIELD_INVALID', 'tint_amount')
        if not 0.0 <= ta <= MAX_TINT:
            raise FailClosed('TREATMENT_FIELD_INVALID', f'tint_amount {ta} (0..{MAX_TINT})')
        th = max(1, int(round(sh * tw / sw)))
        ox, oy = tcx - tw // 2, tcy - th // 2
        kx, ky = tw / sw, th / sh
        for p in face:                                          # which FACE marks the reversed copy carries into the glass
            x0, y0, x1, y1 = p['visible_box']
            inside = x0 >= sx and y0 >= sy and x1 <= sx + sw and y1 <= sy + sh
            if not inside and (x1 > sx and x0 < sx + sw and y1 > sy and y0 < sy + sh):
                raise FailClosed('REFLECTED_MARK_CLIPPED', f"{p['asset_id']} straddles the reflection source region")
            if not inside:
                continue
            u0, u1 = sw - (x1 - sx), sw - (x0 - sx)
            mbox = [ox + math.floor(u0 * kx), oy + math.floor((y0 - sy) * ky),
                    ox + math.ceil(u1 * kx), oy + math.ceil((y1 - sy) * ky)]
            if box_in_glass(glass, mbox):
                reflected.append(p['asset_id'])
            elif box_touches_glass(glass, mbox, H, W):
                raise FailClosed('REFLECTED_MARK_CLIPPED', f"{p['asset_id']} reflected box {mbox} crosses the glass edge")
        reflected = sorted(reflected)
        face_rgb = C.flip_h(base[sy:sy + sh, sx:sx + sw])       # left-right reversal of the physical face region
        layer = C.to_premul(media.scale_rgba(face_rgb, tw, th))
        layer = C.tint(layer, tint, ta)
        canvas = C.over(np.zeros((H, W, 4)), layer, ox, oy)
        canvas = C.apply_mask(canvas, glass_mask(H, W, glass))  # clip: nothing of the copy exists outside the glass
        out_img = C.to_rgb_u8(C.over(C.to_premul(base), canvas, 0, 0))
        outside = glass_mask(H, W, glass) == 0
        if not np.array_equal(out_img[outside], base[..., :3][outside]):
            raise FailClosed('TREATMENT_UNEXPECTED_PIXEL_CHANGE', 'pixels outside the mirror glass changed')
        recipe = {'crop': [sx, sy, sw, sh], 'flip': 'HORIZONTAL (numpy [:, ::-1])', 'scale': [tw, th],
                  'scale_flags': media.SCALE_FLAGS, 'placed_at': [ox, oy], 'tint': {'rgb': tint, 'amount': ta},
                  'clip': f"glass ellipse, feather {glass['feather_px']} px", 'composite': 'compositor.over premultiplied, one rint'}
    if reflected != sorted(declared):
        raise FailClosed('REFLECTED_OVERLAYS_MISMATCH', f'reflection shows {reflected}, record declares {sorted(declared)}')

    out_dir.mkdir(parents=True, exist_ok=True)
    if r['mode'] == 'COMPOSITE':
        png = out_dir / f'{sid}_G08_REFLECTION_FRAME_CANDIDATE.png'
        if png.exists():
            raise FailClosed('OUTPUT_EXISTS', str(png))
        if png.resolve() == src.resolve():
            raise FailClosed('OUTPUT_WOULD_OVERWRITE_SOURCE', str(png))
        write_png_rgb(out_img, png)
        if sha256_bytes(decode_png_rgb(png).tobytes()) != sha256_bytes(out_img.tobytes()):
            raise FailClosed('TREATMENT_FRAME_NOT_LOSSLESS', png.name)
        out = {'file': png.name, 'sha256': sha256_file(png), 'bytes': png.stat().st_size, 'width': W, 'height': H,
               'rgb24_sha256': sha256_bytes(out_img.tobytes()), 'new_pixels': True}
    else:
        out = {'file': None, 'sha256': frame_sha, 'width': W, 'height': H, 'rgb24_sha256': sha256_bytes(out_img.tobytes()),
               'new_pixels': False, 'note': 'PRESERVE: the approved frame already shows the reflection; certificate only'}
    if sha256_file(src) != frame_sha:
        raise FailClosed('SOURCE_MUTATED', str(src))
    tcomp = {'shot_id': sid, 'input_frame_sha256': frame_sha, 'frame_sha256': out['sha256'], 'record_sha256': rec_sha,
             'treatments': [REFL], 'mode': r['mode'], 'reflected_overlays': reflected}
    prov = {
        'agent': AGENT_NAME, 'agent_version': AGENT_VERSION_G08, 'stage': 'G08 mirror reflection (static)', 'status': 'REVIEW',
        'shot_id': sid,
        'source_frame': {k: frame.get(k) for k in ('asset_id', 'registry_id', 'classification', 'registry_status')}
                        | {'verified_sha256': frame_sha, 'sha256_after': frame_sha},
        'treatment_record': {'record_id': rec.get('record_id'), 'sha256': rec_sha, 'contract': CONTRACT_ID,
                             'approval_status': treatment['approval_status']},
        'mirror_glass': glass, 'reflection': {'mode': r['mode'], 'reflected_overlays': reflected, 'recipe': recipe},
        'treatments_composited': tcomp, 'output': out,
        'proposed_registry': ({'asset_type': 'SHOT_FRAME', 'asset_subtype': 'DERIVED_FRAME', 'shot_id': sid, 'registered': False}
                              if r['mode'] == 'COMPOSITE' else {'registered': False, 'note': 'no new asset; the certificate '
                                                                                            'travels with the approved frame'}),
        'human_approval': {'required': True, 'approved': False, 'decisions': ['APPROVE', 'REJECT'],
                           'approve_by': 'exact output sha256 + treatment record sha256'},
        'safety': {'provider_calls': 0, 'source_mutated': False, 'auto_approved': False, 'registered': False},
        'toolchain': media.toolchain(),
    }
    prov['deterministic_core_sha256'] = canonical_sha256({k: v for k, v in prov.items() if k != 'toolchain'})
    (out_dir / f'{sid}_G08_REFLECTION_PROVENANCE.json').write_text(json.dumps(prov, indent=1, sort_keys=True) + '\n')
    return prov


# --- downstream gates (G02 still / motion base frame) ---
def resolve_frame_chain(spec_shot, frame_sha, overlays_composited, treatments_composited):
    """Overlay set and static treatment certificate for the frame a downstream path holds. Returns the frame the G08
    record must be bound to (the frame the treatments started from)."""
    tc = treatments_composited
    if tc:
        if tc.get('shot_id') != spec_shot['shot_id'] or tc.get('frame_sha256') != frame_sha:
            raise FailClosed('TREATMENT_CERTIFICATE_FRAME_MISMATCH', f"{tc.get('frame_sha256')} vs {frame_sha}")
        if tc.get('treatments') != [REFL]:
            raise FailClosed('TREATMENT_CERTIFICATE_INVALID', str(tc.get('treatments')))
        if REFL not in [t['treatment_id'] for t in spec_shot['treatments']]:
            raise FailClosed('TREATMENT_UNDECLARED', f"{spec_shot['shot_id']}: frame carries {REFL}")
        bound = tc['input_frame_sha256']
    else:
        bound = frame_sha
    if spec_shot['active_overlays'] or overlays_composited:
        precomposited_overlay_set(spec_shot, overlays_composited, bound)
    if spec_shot.get('clean_reveal') and (overlays_composited or (tc or {}).get('reflected_overlays')):
        raise FailClosed('CLEAN_REVEAL_HAS_ACTIVE_OVERLAYS', spec_shot['shot_id'])
    return bound


def motion_gate(spec_shot, source_frame_sha, overlays_composited, treatments_composited):
    """Only the static reflection, pre-composited into the motion base frame, may accompany generated motion."""
    ids = spec_treatments(spec_shot) if spec_shot['treatments'] else []
    if any(t != REFL for t in ids) or (ids and not treatments_composited):
        raise FailClosed('MOTION_TREATMENTS_NEED_TRACKING_V02', f'timed or uncertified treatments on generated motion: {ids}')
    if treatments_composited and not ids:
        raise FailClosed('TREATMENT_UNDECLARED', 'motion base frame carries a treatment the shot does not assign')
    return resolve_frame_chain(spec_shot, source_frame_sha, overlays_composited, treatments_composited)


def _sync(spec_shot, entry, tid, timing, fps, governed):
    sid = spec_shot['shot_id']
    need = governed['sync'].get((sid, tid))
    aid = entry.get('sync_audio_asset_id')
    if need and aid != need:
        raise FailClosed('TREATMENT_AUDIO_SYNC_MISSING', f'{sid}: {tid} must sync to {need}, record has {aid!r}')
    if aid is None:
        return None
    events = [x['asset_id'] for x in (spec_shot.get('named_sfx') or []) + (spec_shot.get('event_audio') or [])]
    if aid not in events:
        raise FailClosed('TREATMENT_AUDIO_SYNC_INVALID', f'{aid} is not an event in {sid}')
    t = (timing.get('named') or {}).get(aid)
    if not t:
        raise FailClosed('TREATMENT_AUDIO_SYNC_INVALID', f'{aid} has no timing')
    f = t['start_seconds'] * fps
    if abs(f - entry['start_frame']) > 1e-6:
        raise FailClosed('TREATMENT_AUDIO_SYNC_MISMATCH', f"{tid} starts at frame {entry['start_frame']}, {aid} at {f:.4f}")
    return {'audio_asset_id': aid, 'audio_start_seconds': t['start_seconds'], 'frame': entry['start_frame']}


def plan_timed(spec_shot, treatment, frame_sha, frame_size, timing, fps, treatments_composited=None,
               overlays_composited=None, governed=None, segment=None):
    """Validate the timed treatments for a held frame and return the render plan. segment=(first, last) shot frames the
    caller renders (G07 later passes each segment); a window must lie inside one segment."""
    governed = GOVERNED if governed is None else governed
    ids = spec_treatments(spec_shot)
    bound = resolve_frame_chain(spec_shot, frame_sha, overlays_composited, treatments_composited)
    if REFL in ids and not treatments_composited:
        raise FailClosed('TREATMENT_NOT_COMPOSITED', f"{spec_shot['shot_id']}: {REFL} must be applied (static stage) first")
    rec, rec_sha, glass = validate_record(treatment, spec_shot, bound, frame_size)
    if treatments_composited and treatments_composited['record_sha256'] != rec_sha:
        raise FailClosed('TREATMENT_RECORD_HASH_MISMATCH', 'static and timed stages use different records')
    n, sid = spec_shot['frames'], spec_shot['shot_id']
    lo, hi = segment if segment is not None else (0, n - 1)
    reflected = set((treatments_composited or {}).get('reflected_overlays') or []) | \
        {o['asset_id'] for o in (overlays_composited or {}).get('overlays') or [] if o['surface'] == 'REFLECTION'}
    plan = {'record_sha256': rec_sha, 'glass': glass, 'windows': []}
    for tid in TIMED:
        if tid not in ids:
            continue
        e = rec[SECTION[tid]]
        keys = GLINT_KEYS if tid == GLINT else POP_KEYS
        _keys(e, keys, keys - {'target_overlay', 'sync_audio_asset_id'}, SECTION[tid])
        if e['treatment_id'] != tid:
            raise FailClosed('TREATMENT_UNSUPPORTED', f"{SECTION[tid]} entry names {e['treatment_id']!r}")
        s0 = _int(e['start_frame'], 'TREATMENT_FRAME_RANGE_INVALID', 'start_frame')
        k = _int(e['frames'], 'TREATMENT_FRAME_RANGE_INVALID', 'frames')
        try:
            validate_window(tid, s0, k, n)
        except FailClosed as err:
            raise FailClosed('TREATMENT_FRAME_RANGE_INVALID', str(err)) from None
        if s0 < lo or s0 + k - 1 > hi:
            raise FailClosed('TREATMENT_OUTSIDE_GOVERNED_RANGE', f'{tid}: frames {s0}..{s0 + k - 1} outside {lo}..{hi}')
        w = {'treatment_id': tid, 'start_frame': s0, 'frames': k, 'sync': _sync(spec_shot, e, tid, timing, fps, governed),
             'envelope': envelope(TREATMENTS[tid]['envelope'] if tid == GLINT else 'bloom', k)}
        if tid == GLINT:
            cx = _int(e['cx'], 'TREATMENT_COORDINATE_INVALID', 'glint cx')
            cy = _int(e['cy'], 'TREATMENT_COORDINATE_INVALID', 'glint cy')
            size = e['size_px']
            if not isinstance(size, int) or isinstance(size, bool) or size < 4:
                raise FailClosed('TREATMENT_SCALE_INVALID', f'glint size_px {size!r} (integer >= 4)')
            box = [cx - size // 2, cy - size // 2, cx - size // 2 + size, cy - size // 2 + size]
            if not box_in_glass(glass, box):
                raise FailClosed('GLINT_OUTSIDE_GLASS', f'glint box {box} is not inside the mirror glass')
            need = governed['glint_target'].get(sid)
            tgt = e.get('target_overlay')
            if need and tgt != need:
                raise FailClosed('GLINT_TARGET_INVALID', f'{sid}: glint must mark {need}, record has {tgt!r}')
            if tgt is not None and tgt not in reflected:
                raise FailClosed('GLINT_TARGET_INVALID', f'{tgt} is not a reflected mark in this frame')
            w.update({'center': [cx, cy], 'size_px': size, 'box': box, 'target_overlay': tgt})
        else:
            gain = _num(e['gain'], 'TREATMENT_FIELD_INVALID', 'pop gain')
            if not 0.0 < gain <= TREATMENTS[POP]['max_gain']:
                raise FailClosed('TREATMENT_FIELD_INVALID', f"pop gain {gain} (0..{TREATMENTS[POP]['max_gain']}]")
            if spec_shot['active_overlays'] or overlays_composited or reflected:
                raise FailClosed('CLEAN_REVEAL_HAS_ACTIVE_OVERLAYS', f'{sid}: the completion pop needs a frame with zero overlays')
            w['gain'] = gain
        plan['windows'].append(w)
    return plan


def render_frame(img, plan, i):
    """Frame i of the held shot with the timed treatments applied (glint, then pop). Pure function of its inputs."""
    active = [(w, i - w['start_frame']) for w in plan['windows'] if 0 <= i - w['start_frame'] < w['frames']]
    if not active:
        return img
    H, W = img.shape[:2]
    f = C.to_premul(np.dstack([img, np.full((H, W), 255, np.uint8)]))
    g = plan['glass']
    for w, j in active:                                         # fixed order: TIMED = (GLINT, POP)
        a = w['envelope'][j]
        if w['treatment_id'] == GLINT:
            f = C.over(f, C.glint_sprite(w['size_px']), w['box'][0], w['box'][1], opacity=a)
        else:
            m = glass_mask(H, W, g)[..., None]
            f[..., :3] = f[..., :3] + (f[..., 3:4] - f[..., :3]) * (w['gain'] * a) * m
    out = C.to_rgb_u8(f)
    outside = glass_mask(H, W, g, feather=0) == 0
    if g['feather_px']:
        outside &= glass_mask(H, W, g) == 0
    if not np.array_equal(out[outside], img[outside]):
        raise FailClosed('TREATMENT_UNEXPECTED_PIXEL_CHANGE', f'frame {i}: pixels outside the mirror glass changed')
    return out
