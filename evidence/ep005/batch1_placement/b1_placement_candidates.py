"""EP005 Batch 1: G03 placement + G08 treatment CANDIDATE records and scratch previews (LOCAL_PREPARE_ONLY; no
production write, no provider call, nothing approved).

Usage (repo root): python3 evidence/ep005/batch1_placement/b1_placement_candidates.py <scratch dir>
Base frames: the approved family frames, read back from production storage and verified against the registry SHA.
Geometry: whole base-frame pixels, measured on each approved frame (landmarks: nose / eye / mouth-corner / blush
positions read from gridded zooms and dark/pink blob detection; glass = flood fill of the clear glass inside the pink
flower ring, axis-aligned ellipse). Sizes follow one rule for every frame (documented below). Previews are rendered by
the UNCHANGED G03 (overlay.place_overlays) and G08 (g08.apply_reflection / plan_timed / render_frame) modules; the
modules only run approved records, so the candidate record is passed in memory with a preview-only approval flag. The
committed records carry status CANDIDATE_PENDING_HUMAN_APPROVAL; preview provenance stays in scratch.
"""
import copy
import json
import sys
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
from agent008.config import load_output_spec  # noqa: E402
from agent008.derive import write_png_rgb  # noqa: E402
from agent008.episode import PINS, resolve_episode  # noqa: E402
from agent008.g08 import GLINT, POP, REFL, apply_reflection, box_in_glass, plan_timed, render_frame  # noqa: E402
from agent008.hashing import canonical_sha256, sha256_bytes, sha256_file  # noqa: E402
from agent008.inputs import load_hash_pins  # noqa: E402
from agent008.motion.http import UrllibHttpClient  # noqa: E402
from agent008.overlay import CONTRACT_ID as G03_CONTRACT, place_overlays  # noqa: E402
from agent008.g08 import CONTRACT_ID as G08_CONTRACT  # noqa: E402
from agent008.tools.snapshot_inputs import build_snapshot  # noqa: E402

SB = 'https://ziluiwrwwbayhcskeere.supabase.co'
FPS = 24
CHEEK, MOUTH, NOSE = (f'OVERLAY-EP005-BERRY-SMUDGE-{k}-v01' for k in ('CHEEK', 'MOUTH', 'NOSE'))
FRAMES = {  # family frame asset id, members in this batch
    'F01': ('FRAME-EP005-F01-BASE-CAND-v02', ['S001', 'S005', 'S013', 'S025']),
    'F03': ('FRAME-EP005-F03-BASE-CAND-v02', ['S004', 'S012']),
    'F09': ('FRAME-EP005-F09-BASE-CAND-v01', ['S017']),
    'F15': ('FRAME-EP005-F15-BASE-CAND-v02', ['S019']),
}
# Size rule (all frames): cheek width = round(0.50 x eye distance), mouth width = round(0.30 x eye distance),
# nose width = round(0.90 x nose width); FACE rotations cheek -12 deg, others 0; REFLECTION is the mirror image
# (mirror=true, cheek +12 deg). Mouth mark: beside the anatomical RIGHT mouth corner, offset outward by half its width
# + 6 px and down 8 px (decision flagged: the spec does not name a side). Anatomical left = image-left in a reflection,
# image-right on a front-facing real face.
MEASURED = {  # landmark measurements on the approved frames (image pixels)
    'F01_REFL': {'eye_l': (814, 467), 'eye_r': (1005, 473), 'nose_box': (872, 492, 942, 537), 'cheek_anat_left': (748, 538),
                 'mouth_corner_anat_right': (967, 550), 'glass_seed': (907, 420)},
    'F15_REFL': {'eye_l': (863, 492), 'eye_r': (1051, 493), 'nose_box': (923, 515, 995, 559), 'cheek_anat_left': (792, 566),
                 'mouth_corner_anat_right': (1020, 570), 'glass_seed': (959, 400)},
    'F03_REFL': {'eye_l': (1061, 571), 'eye_r': (1223, 544), 'nose_box': (1127, 575, 1178, 608), 'cheek_anat_left': (1055, 635),
                 'mouth_corner_anat_right': (1200, 615), 'glass_seed': (1153, 470)},
    'F03_FACE': {'eye_l': (485, 455), 'eye_r': (732, 385), 'nose_box': (605, 447, 690, 507), 'cheek_anat_left': (800, 478),
                 'mouth_corner_anat_right': (565, 535), 'cheek_w_override': 100, 'nose_w_override': 72,
                 'note': 'three-quarter view turned toward the mirror: anatomical left cheek = far cheek (image-right), '
                         'foreshortened, so the cheek width is held at 100 px; nose width reduced to clear the right eye'},
    'F09_REFL': {'eye_l': (951, 422), 'eye_r': (1044, 440), 'nose_box': (975, 442, 1007, 461), 'glass_seed': (991, 400)},
    'F09_FACE': {'eye_l': (565, 368), 'eye_r': (722, 330), 'nose_box': (637, 360, 698, 400), 'nose_w_override': 50,
                 'note': 'nose width reduced to clear the right eye'},
}
SHOTS = {  # shot: family, surfaces (FACE surfaces are flagged: the spec names the reflection only)
    'S001': ('F01', ['REFL']), 'S005': ('F01', ['REFL']), 'S013': ('F01', ['REFL']),
    'S004': ('F03', ['REFL', 'FACE']), 'S012': ('F03', ['REFL', 'FACE']),
    'S017': ('F09', ['REFL', 'FACE']), 'S019': ('F15', ['REFL']),
}
G08_SHOTS = {  # proposed timing (seconds at 24 fps) - audio timing is a separate human gate
    'S004': {'family': 'F03', 'glint': {'start_frame': 12, 'frames': 8, 'size_px': 36}, 'sync_start_seconds': 0.5},
    'S012': {'family': 'F03', 'glint': {'start_frame': 24, 'frames': 8, 'size_px': 36}},
    'S025': {'family': 'F01', 'pop': {'start_frame': 12, 'frames': 7, 'gain': 0.10}, 'sync_start_seconds': 0.5},
}
http = UrllibHttpClient()


def sb_json(path):
    r = http.send('GET', f'{SB}{path}', {'Accept': 'application/json'})
    if r.status != 200:
        sys.exit(f'STOP: GET {path} HTTP {r.status}')
    return json.loads(r.body)


def fetch(storage_path, dest):
    r = http.send('GET', f'{SB}/storage/v1/object/authenticated/{storage_path}', {}, None, 120.0)
    if r.status != 200:
        sys.exit(f'STOP: storage GET {storage_path} HTTP {r.status}')
    Path(dest).write_bytes(r.body)
    return sha256_bytes(r.body)


def glass_ellipse(path, seed, margin=3):
    """Clear glass inside the pink flower ring: flood fill of non-pink pixels from a seed inside the glass."""
    a = np.asarray(Image.open(path).convert('RGB')).astype(int)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    ring = (r > 200) & (g < 170) & (b > 110) & (b < 200) & (r - g > 60)
    H, W = ring.shape
    # the ring is the outer boundary: fill everything reachable from the seed that is not ring, stopping at the ring
    seen = np.zeros((H, W), bool)
    q = deque([seed[::-1]])
    seen[seed[1], seed[0]] = True
    while q:
        y, x = q.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            yy, xx = y + dy, x + dx
            if 0 <= yy < H and 0 <= xx < W and not seen[yy, xx] and not ring[yy, xx]:
                seen[yy, xx] = True
                q.append((yy, xx))
    ys, xs = np.nonzero(seen)
    x0, x1, y0, y1 = int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max())
    if x0 == 0 or y0 == 0 or x1 == W - 1 or y1 == H - 1:
        sys.exit(f'STOP: glass fill leaked to the frame edge ({x0},{y0},{x1},{y1})')
    cx, cy = (x0 + x1 + 1) // 2, (y0 + y1 + 1) // 2
    return {'shape': 'ELLIPSE', 'cx': cx, 'cy': cy, 'rx': (x1 - x0 + 1) // 2 - margin, 'ry': (y1 - y0 + 1) // 2 - margin,
            'feather_px': 0}, {'fill_bbox': [x0, y0, x1, y1], 'margin_px': margin}


def placements(region, overlays, sha):
    m = MEASURED[region]
    refl = region.endswith('REFL')
    ed = round(((m['eye_r'][0] - m['eye_l'][0]) ** 2 + (m['eye_r'][1] - m['eye_l'][1]) ** 2) ** 0.5)
    nx0, ny0, nx1, ny1 = m['nose_box']
    out = []
    for aid in overlays:
        if aid == NOSE:
            w = m.get('nose_w_override') or round(0.90 * (nx1 - nx0))
            x, y, rot = round((nx0 + nx1) / 2), round((ny0 + ny1) / 2 - 0.1 * (ny1 - ny0)), 0
            meaning = "Mikko's nose (centred on the nose, covering the bridge)"
        elif aid == CHEEK:
            w = m.get('cheek_w_override') or round(0.50 * ed)
            (x, y), rot = m['cheek_anat_left'], (12 if refl else -12)
            meaning = "Mikko's anatomical left cheek (" + ('image-left in the reflection' if refl else 'image-right on the real face') + ')'
        else:
            w = round(0.30 * ed)
            cx, cy = m['mouth_corner_anat_right']
            side = 1 if refl else -1                 # anatomical right = image-right in a reflection, image-left on the face
            x, y, rot = cx + side * (w // 2 + 6), cy + 8, 0
            meaning = "skin beside (not inside) Mikko's mouth, anatomical right corner"
        out.append({'asset_id': aid, 'overlay_sha256': sha[aid], 'surface': 'REFLECTION' if refl else 'FACE',
                    'anchor': 'CENTER', 'x': int(x), 'y': int(y), 'width_px': int(w), 'rotation_deg': rot, 'mirror': refl,
                    '_meaning': meaning, '_eye_distance_px': ed})
    return out


def label(img, lines, color=(255, 255, 255)):
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, img.width, 22 * len(lines) + 8], fill=(0, 0, 0))
    for i, t in enumerate(lines):
        d.text((8, 4 + 22 * i), t, fill=color)
    return img


def main(work):
    work = Path(work)
    (work / 'frames').mkdir(parents=True, exist_ok=True)
    specs = {x['shot_id']: x for x in resolve_episode(build_snapshot('69bff641-e056-4701-a23f-d91dbc2039b2'),
                                                      load_hash_pins(PINS), load_output_spec())}
    rows = {r['asset_id']: r for r in sb_json('/rest/v1/asset_registry?or=(asset_id.like.FRAME-EP005-F*,asset_id.like.'
                                              'OVERLAY-EP005-BERRY-SMUDGE-*)&select=id,asset_id,status,asset_type,'
                                              'asset_subtype,storage_path,metadata_json')}
    frames = {}
    for fam, (aid, members) in FRAMES.items():
        row = rows[aid]
        dest = work / 'frames' / f'{aid}.png'
        got = fetch(row['storage_path'], dest)
        if row['status'] != 'APPROVED' or got != row['metadata_json']['sha256']:
            sys.exit(f'STOP: {aid} not APPROVED at its registry SHA')
        frames[fam] = {'asset_id': aid, 'registry_id': row['id'], 'sha256': got, 'path': str(dest)}
    ov_paths, ov_sha = {}, {}
    for aid in (CHEEK, MOUTH, NOSE):
        row = rows[aid]
        dest = work / 'frames' / f'{aid}.webp'
        got = fetch(row['storage_path'], dest)
        if row['status'] != 'APPROVED' or got != row['metadata_json']['sha256']:
            sys.exit(f'STOP: {aid} not APPROVED at its registry SHA')
        ov_paths[aid], ov_sha[aid] = str(dest), got

    glass = {}
    for fam, region in (('F01', 'F01_REFL'), ('F03', 'F03_REFL'), ('F09', 'F09_REFL'), ('F15', 'F15_REFL')):
        glass[fam] = glass_ellipse(frames[fam]['path'], MEASURED[region]['glass_seed'])

    packet, g03_out, ambiguous = [], {}, []
    for sid, (fam, surfaces) in SHOTS.items():
        sp = specs[sid]['spec']
        active = [o['asset_id'] for o in sp['active_overlays']]
        pl = []
        for s in surfaces:
            pl += placements(f'{fam}_{s}', active, ov_sha)
        rec = {'contract': G03_CONTRACT, 'record_id': f'G03-EP005-{sid}-CAND-v01', 'shot_id': sid,
               'base_frame': {'asset_id': frames[fam]['asset_id'], 'sha256': frames[fam]['sha256']},
               'frame_size': [1920, 1080], 'frame_range': [0, sp['frames'] - 1],
               'placements': [{k: v for k, v in p.items() if not k.startswith('_')} for p in pl]}
        rec_sha = canonical_sha256(rec)
        frame = {'asset_id': frames[fam]['asset_id'], 'registry_id': frames[fam]['registry_id'],
                 'classification': 'SHOT_FRAME/BASE_FRAME', 'registry_status': 'APPROVED', 'shot_id': sid,
                 'path': frames[fam]['path'], 'expected_sha256': frames[fam]['sha256']}
        preview_only = {'record': rec, 'approval_status': 'APPROVED', 'expected_sha256': rec_sha}   # in-memory preview flag
        out_dir = work / 'g03' / sid
        prov = place_overlays(sp, frame, {a: ov_paths[a] for a in active}, preview_only, out_dir)
        g03_out[sid] = {'prov': prov, 'path': out_dir / prov['output']['file']}
        flags = []
        if 'FACE' in surfaces:
            flags.append({'placement': 'all FACE-surface placements', 'question': 'the manifest names the mirror reflection '
                          "only; Mikko's real face is visible in this frame. Add the matching FACE marks (proposed, shown in "
                          'the preview) or keep the reflection only?'})
        if MOUTH in active:
            flags.append({'placement': f'{MOUTH} (both surfaces)', 'question': 'the spec says "beside, not inside, the mouth" '
                          'without a side. Proposed: anatomical RIGHT corner (opposite the cheek mark, so the three marks read '
                          'separately; the non-canon Phase-0 stand-in used the left side, which collides with the cheek mark '
                          'at production scale). Confirm the side.'})
        for f in flags:
            ambiguous.append({'shot_id': sid, **f})
        packet.append({'SHOT_ID': sid, 'FRAME_FAMILY': fam, 'FRAME_ASSET_ID': frames[fam]['asset_id'],
                       'FRAME_SHA': frames[fam]['sha256'], 'G03_RECORD_STATUS': 'CANDIDATE_PENDING_HUMAN_APPROVAL',
                       'G03_RECORD': rec, 'G03_RECORD_SHA256': rec_sha,
                       'G03_PLACEMENTS': [{**{k: v for k, v in p.items() if not k.startswith('_')},
                                           'anatomical_meaning': p['_meaning'],
                                           'visible_box': next(q['visible_box'] for q in prov['placements']
                                                               if q['asset_id'] == p['asset_id'] and q['surface'] == p['surface'])}
                                          for p in pl],
                       'G03_PREVIEW_FRAME_SHA256': prov['output']['sha256'], 'FLAGS': flags})

    # ---- G08 ----
    g08 = {}
    for sid, cfg in G08_SHOTS.items():
        sp, fam = specs[sid]['spec'], cfg['family']
        gl, glmeta = glass[fam]
        timing = {'named': {}}
        if sid in g03_out:
            p3 = g03_out[sid]['prov']
            in_frame = {'asset_id': f'{sid}-G03-PREVIEW', 'sha256': p3['output']['sha256']}
            img_path, comp = g03_out[sid]['path'], p3['overlays_composited']
        else:
            in_frame = {'asset_id': frames[fam]['asset_id'], 'sha256': frames[fam]['sha256']}
            img_path, comp = Path(frames[fam]['path']), None
        rec = {'contract': G08_CONTRACT, 'record_id': f'G08-EP005-{sid}-CAND-v01', 'shot_id': sid, 'input_frame': in_frame,
               'frame_size': [1920, 1080], 'frame_range': [0, sp['frames'] - 1], 'mirror_glass': gl}
        if 'glint' in cfg:
            tgt = {'S004': CHEEK, 'S012': MOUTH}[sid]
            t = next(q for q in g03_out[sid]['prov']['placements'] if q['asset_id'] == tgt and q['surface'] == 'REFLECTION')
            size = cfg['glint']['size_px']
            cx, cy = t['x'], t['y']                  # start on the target mark; step toward the glass centre until inside
            for _ in range(200):
                box = [cx - size // 2, cy - size // 2, cx - size // 2 + size, cy - size // 2 + size]
                if box_in_glass(gl, box):
                    break
                cx += int(np.sign(gl['cx'] - cx))
                cy += int(np.sign(gl['cy'] - cy))
            rec['glint'] = {'treatment_id': GLINT, 'start_frame': cfg['glint']['start_frame'], 'frames': cfg['glint']['frames'],
                            'cx': int(cx), 'cy': int(cy), 'size_px': size, 'target_overlay': tgt}
            if sid == 'S004':
                rec['glint']['sync_audio_asset_id'] = 'SFX-LUMI-CLUE-CHIME'
                timing['named']['SFX-LUMI-CLUE-CHIME'] = {'start_seconds': cfg['sync_start_seconds']}
        if REFL in [x['treatment_id'] for x in sp['treatments']]:
            rec['reflection'] = {'mode': 'PRESERVE', 'reflected_overlays': []}
        if 'pop' in cfg:
            rec['pop'] = {'treatment_id': POP, **cfg['pop'], 'sync_audio_asset_id': 'SFX-COMPLETION-POP-v01'}
            timing['named']['SFX-COMPLETION-POP-v01'] = {'start_seconds': cfg['sync_start_seconds']}
        rec_sha = canonical_sha256(rec)
        preview_only = {'record': rec, 'approval_status': 'APPROVED', 'expected_sha256': rec_sha}
        tcomp, refl_prov = None, None
        if 'reflection' in rec:
            fr = {'asset_id': frames[fam]['asset_id'], 'registry_id': frames[fam]['registry_id'],
                  'classification': 'SHOT_FRAME/BASE_FRAME', 'registry_status': 'APPROVED', 'shot_id': sid,
                  'path': frames[fam]['path'], 'expected_sha256': frames[fam]['sha256']}
            refl_prov = apply_reflection(sp, fr, preview_only, work / 'g08' / sid)
            tcomp = refl_prov['treatments_composited']
        plan = plan_timed(sp, preview_only, in_frame['sha256'], (1920, 1080), timing, FPS, treatments_composited=tcomp,
                          overlays_composited=comp)
        img = np.asarray(Image.open(img_path).convert('RGB'))
        w = plan['windows'][0]
        peak = w['start_frame'] + int(np.argmax(w['envelope']))
        outd = work / 'g08' / sid
        outd.mkdir(parents=True, exist_ok=True)
        f_peak = render_frame(img, plan, peak)
        f_before = render_frame(img, plan, w['start_frame'] - 1)
        write_png_rgb(f_peak, outd / f'{sid}_G08_PEAK_FRAME_{peak:03d}.png')
        g08[sid] = {'record': rec, 'record_sha256': rec_sha, 'glass_measurement': glmeta, 'plan': {
            'windows': [{k: v for k, v in x.items()} for x in plan['windows']]}, 'peak_frame': peak,
            'peak_frame_png_sha256': sha256_file(outd / f'{sid}_G08_PEAK_FRAME_{peak:03d}.png'),
            'unchanged_outside_glass': True, 'held_frame_equals_input_outside_window': bool(np.array_equal(f_before, img)),
            'reflection_certificate': ({'mode': 'PRESERVE', 'reflected_overlays': tcomp['reflected_overlays'],
                                        'frame_sha256': tcomp['frame_sha256']} if tcomp else None),
            'proposed_timing': timing['named'], 'input_frame_note': (
                'bound to the G03 preview output of the candidate placement record; if the G03 record changes, this record '
                'must be re-bound' if sid in g03_out else 'bound to the approved F01 v02 base frame (S025 has no overlays)')}
    return frames, glass, packet, g03_out, g08, ambiguous, ov_sha


def previews(work, frames, glass, packet, g03_out, g08):
    work = Path(work)
    pv = work / 'previews'
    pv.mkdir(exist_ok=True)
    tiles = []
    for p in packet:
        sid = p['SHOT_ID']
        im = Image.open(g03_out[sid]['path']).convert('RGB')
        boxes = [q['visible_box'] for q in p['G03_PLACEMENTS']]
        x0 = min(b[0] for b in boxes) - 40; y0 = min(b[1] for b in boxes) - 40
        x1 = max(b[2] for b in boxes) + 40; y1 = max(b[3] for b in boxes) + 40
        zoom = im.crop((max(0, x0), max(0, y0), min(1920, x1), min(1080, y1)))
        zoom = zoom.resize((zoom.width * 540 // zoom.height, 540), Image.LANCZOS) if zoom.height < 540 else zoom
        full = im.resize((960, 540), Image.LANCZOS)
        tile = Image.new('RGB', (960 + zoom.width, 540), (30, 30, 30))
        tile.paste(full, (0, 0)); tile.paste(zoom, (960, 0))
        label(tile, [f"{sid}  G03 CANDIDATE  frame {p['FRAME_ASSET_ID']} ({p['FRAME_SHA'][:12]})",
                     'marks: ' + ', '.join(f"{q['asset_id'].split('-')[-2]}@{q['surface'][0]}({q['x']},{q['y']},w{q['width_px']})"
                                         for q in p['G03_PLACEMENTS'])])
        f = pv / f'{sid}_G03_PREVIEW.png'
        tile.save(f)
        tiles.append(f)
    for sid, g in g08.items():
        peak = Image.open(work / 'g08' / sid / f"{sid}_G08_PEAK_FRAME_{g['peak_frame']:03d}.png").convert('RGB')
        ann = peak.copy()
        d = ImageDraw.Draw(ann)
        gl = g['record']['mirror_glass']
        d.ellipse([gl['cx'] - gl['rx'], gl['cy'] - gl['ry'], gl['cx'] + gl['rx'], gl['cy'] + gl['ry']], outline=(0, 255, 255), width=3)
        if 'glint' in g['record']:
            gg = g['record']['glint']
            s = gg['size_px']
            d.rectangle([gg['cx'] - s // 2, gg['cy'] - s // 2, gg['cx'] - s // 2 + s, gg['cy'] - s // 2 + s], outline=(255, 255, 0), width=2)
        x0, y0 = max(0, gl['cx'] - gl['rx'] - 60), max(0, gl['cy'] - gl['ry'] - 60)
        x1, y1 = min(1920, gl['cx'] + gl['rx'] + 60), min(1080, gl['cy'] + gl['ry'] + 60)
        z1, z2 = peak.crop((x0, y0, x1, y1)), ann.crop((x0, y0, x1, y1))
        h = 540
        z1 = z1.resize((z1.width * h // z1.height, h), Image.LANCZOS); z2 = z2.resize((z2.width * h // z2.height, h), Image.LANCZOS)
        tile = Image.new('RGB', (960 + z1.width + z2.width, h), (30, 30, 30))
        tile.paste(peak.resize((960, 540), Image.LANCZOS), (0, 0)); tile.paste(z1, (960, 0)); tile.paste(z2, (960 + z1.width, 0))
        w = g['plan']['windows'][0]
        what = (f"glint @({g['record']['glint']['cx']},{g['record']['glint']['cy']}) {g['record']['glint']['size_px']}px -> "
                f"{g['record']['glint']['target_overlay'].split('-')[-2]}" if 'glint' in g['record'] else
                f"reflection PRESERVE (clean) + pop gain {g['record']['pop']['gain']}")
        label(tile, [f"{sid}  G08 CANDIDATE  peak frame {g['peak_frame']} of window {w['start_frame']}..{w['start_frame'] + w['frames'] - 1}",
                     f"glass ellipse c=({gl['cx']},{gl['cy']}) r=({gl['rx']},{gl['ry']}) [cyan]  {what}"])
        f = pv / f'{sid}_G08_PREVIEW.png'
        tile.save(f)
        tiles.append(f)
    # contact sheet (fixed order)
    ims = [Image.open(t) for t in tiles]
    W = 1920
    scaled = [i.resize((W, i.height * W // i.width), Image.LANCZOS) if i.width > W else i for i in ims]
    sheet = Image.new('RGB', (W, sum(i.height for i in scaled) + 10 * len(scaled)), (15, 15, 15))
    y = 0
    for i in scaled:
        sheet.paste(i, (0, y)); y += i.height + 10
    sheet.save(pv / 'BATCH1_PLACEMENT_CONTACT_SHEET.png')
    return tiles + [pv / 'BATCH1_PLACEMENT_CONTACT_SHEET.png']


if __name__ == '__main__':
    work = Path(sys.argv[1])
    frames, glass, packet, g03_out, g08, ambiguous, ov_sha = main(work)
    files = previews(work, frames, glass, packet, g03_out, g08)
    manifest = [{'file': str(f.relative_to(work)), 'sha256': sha256_file(f)} for f in files]
    out = {'status': 'CANDIDATES_PENDING_HUMAN_APPROVAL (LOCAL_PREPARE_ONLY; nothing registered or approved)',
           'frames': frames and {k: {kk: vv for kk, vv in v.items() if kk != 'path'} for k, v in frames.items()},
           'overlay_sha256': ov_sha, 'measured_landmarks': MEASURED, 'size_rule': (
               'cheek w = round(0.50 x eye distance); mouth w = round(0.30 x eye distance); nose w = round(0.90 x nose width); '
               'overrides noted per region'),
           'glass': {k: {'ellipse': v[0], **v[1]} for k, v in glass.items()},
           'G03': packet, 'G08': g08, 'AMBIGUOUS': ambiguous, 'preview_manifest': manifest,
           'preview_note': 'previews rendered by the unchanged G03/G08 modules with the candidate records passed in memory '
                           'under a preview-only approval flag; preview provenance stays in scratch; not production assets'}
    (HERE / 'B1_PLACEMENT_CANDIDATES_v1.json').write_text(json.dumps(out, indent=1, default=str) + '\n')
    for p in packet:
        print(p['SHOT_ID'], p['FRAME_FAMILY'], p['G03_RECORD_SHA256'][:12], [(q['asset_id'].split('-')[-2], q['surface'][0], q['x'], q['y'], q['width_px']) for q in p['G03_PLACEMENTS']])
    for sid, g in g08.items():
        print(sid, g['record_sha256'][:12], g['record']['mirror_glass'], {k: g['record'][k] for k in ('glint', 'pop') if k in g['record']})
    print('ambiguous', len(ambiguous))
