"""EP005 Batch 1 presentation pass v02 for S005 / S013 / S017 / S019 (deterministic; no provider, no generation).

Usage (repo root): python3 evidence/ep005/batch1_render/b1_presentation_v02.py <work dir> <label>
Company Brain rejected the v01 MP4s as presentation (held still + inaudible ambience); the visual content was accepted.
Same pixels, same governed content: the approved G03 frame (re-applied from the APPROVED G03 record and verified against
the record's reproduced output SHA) moves as ONE 2D image under a restrained camera push:
  e(t) = 0.75 * (1 - cos(pi t)) / 2 + 0.25 * t,  t = i / (n - 1)      (smooth, never stationary)
  s(t) = 1 + (S_END - 1) * e(t);  dx(t) = DRIFT_X * e(t)
  window = F + (frame - F) / s + (dx, 0)   (zoom about the focal point F; always inside the frame for s >= 1)
  (viewing QC: S005/S013/S019 use a top-anchored F (y 150) so the mirror's top petal, already touching the frame edge, is
  not cropped further by more than ~5 px; the first trial with F at the glass/nose centre cropped 12-18 px of the petal)
  frame_i = PIL resize(window -> 1920x1080, LANCZOS)   (single resample of the approved frame; no interpolation between frames)
Audio: the governed mixer (motion.compose.mix_motion_audio) with the approved AMB-BATHROOM-QUIET-v01 bed at BED_GAIN_DB;
encode: the governed media.encode_review (H.264 yuv420p + AAC, bitexact, single thread). Nothing else is added.
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
from agent008 import media  # noqa: E402
from agent008.config import load_output_spec  # noqa: E402
from agent008.episode import PINS, resolve_episode  # noqa: E402
from agent008.hashing import sha256_bytes, sha256_file  # noqa: E402
from agent008.inputs import load_hash_pins  # noqa: E402
from agent008.motion.compose import mix_motion_audio  # noqa: E402
from agent008.motion.http import UrllibHttpClient  # noqa: E402
from agent008.overlay import place_overlays  # noqa: E402
from agent008.tools.snapshot_inputs import build_snapshot  # noqa: E402

SB = 'https://ziluiwrwwbayhcskeere.supabase.co'
AMB = 'AMB-BATHROOM-QUIET-v01'
BED_GAIN_DB = 11.5            # -42.2 LUFS / -30.4 dBTP at 0 dB -> about -30.7 LUFS / -18.9 dBTP (ceiling -18 dBFS)
CAMERA = {  # shot: end scale, focal point F (approved-frame pixels, from the approved G03/G08 geometry), lateral drift
    'S005': {'S_END': 1.030, 'F': (895, 150), 'DRIFT_X': 0, 'focus': 'mirror glass centre x (F01 glass ellipse); top-anchored '
             '(y 150) so the mirror top petal, already at the frame edge, loses <= 4.4 px'},
    'S013': {'S_END': 1.025, 'F': (954, 150), 'DRIFT_X': 0, 'focus': 'remaining smudges x (midpoint of the nose and mouth marks); '
             'top-anchored (y 150) to protect the top petal (<= 3.7 px)'},
    'S017': {'S_END': 1.025, 'F': (830, 413), 'DRIFT_X': 12,
             'focus': "between Mikko's real-face nose mark (668,376) and the reflected nose mark (991,450); drift toward the reflection"},
    'S019': {'S_END': 1.035, 'F': (959, 150), 'DRIFT_X': 0, 'focus': 'reflected nose clue x (F15 approved nose mark); top-anchored '
             '(y 150) to protect the top petal (<= 5.1 px)'},
}
FRAMES = {'S005': 'FRAME-EP005-F01-BASE-CAND-v02', 'S013': 'FRAME-EP005-F01-BASE-CAND-v02',
          'S017': 'FRAME-EP005-F09-BASE-CAND-v01', 'S019': 'FRAME-EP005-F15-BASE-CAND-v02'}
http = UrllibHttpClient()


def ease(t):
    return 0.75 * (1 - math.cos(math.pi * t)) / 2 + 0.25 * t


def window(cam, t, W=1920, H=1080):
    s = 1 + (cam['S_END'] - 1) * ease(t)
    fx, fy = cam['F']
    dx = cam['DRIFT_X'] * ease(t)
    box = (fx - fx / s + dx, fy - fy / s, fx + (W - fx) / s + dx, fy + (H - fy) / s)
    if box[0] < -1e-9 or box[1] < -1e-9 or box[2] > W + 1e-9 or box[3] > H + 1e-9:
        raise SystemExit(f'STOP: window {box} leaves the frame (edge exposure)')
    return s, dx, box


def frames(src, cam, n):
    for i in range(n):
        _, _, box = window(cam, i / (n - 1))
        yield np.asarray(src.resize((1920, 1080), Image.LANCZOS, box=box))


def get(path):
    r = http.send('GET', f'{SB}{path}', {'Accept': 'application/json'}, None, 120.0)
    if r.status != 200:
        raise SystemExit(f'STOP: GET {path} HTTP {r.status}')
    return r


def main(work, label):
    work = Path(work)
    spec = load_output_spec()
    specs = {x['shot_id']: x.get('spec') for x in resolve_episode(build_snapshot('69bff641-e056-4701-a23f-d91dbc2039b2'),
                                                                  load_hash_pins(PINS), spec)}
    reg = {r['asset_id']: r for r in json.loads(get('/rest/v1/asset_registry?or=(asset_id.like.FRAME-EP005-F*,asset_id.like.'
                                                    'OVERLAY-EP005-BERRY-SMUDGE-*,asset_id.like.G03-REC-EP005-*,asset_id.eq.'
                                                    f'{AMB})&select=*').body)}
    inputs = {}
    for aid, r in reg.items():
        if r['storage_path'] is None:
            continue
        p = work / 'inputs' / Path(r['storage_path']).name
        p.parent.mkdir(parents=True, exist_ok=True)
        if not p.exists():
            p.write_bytes(get(f"/storage/v1/object/authenticated/{r['storage_path']}").body)
        if r['status'] != 'APPROVED' or sha256_file(p) != r['metadata_json']['sha256']:
            raise SystemExit(f'STOP: {aid} not APPROVED at its registry SHA')
        inputs[aid] = p
    out = {}
    for sid, cam in CAMERA.items():
        sp, fr, rec = specs[sid], reg[FRAMES[sid]], reg[f'G03-REC-EP005-{sid}-v01']
        md = rec['metadata_json']
        if rec['status'] != 'APPROVED':
            raise SystemExit(f'STOP {sid}: G03 record not APPROVED')
        frame = {'asset_id': fr['asset_id'], 'registry_id': fr['id'], 'classification': 'SHOT_FRAME/BASE_FRAME',
                 'registry_status': 'APPROVED', 'shot_id': sid, 'path': str(inputs[fr['asset_id']]),
                 'expected_sha256': fr['metadata_json']['sha256']}
        d = work / label / sid
        g3 = place_overlays(sp, frame, {o['asset_id']: str(inputs[o['asset_id']]) for o in sp['active_overlays']},
                            {'record': md['record'], 'approval_status': 'APPROVED', 'expected_sha256': md['record_sha256']}, d / 'g03')
        if g3['output']['sha256'] != md['reproduced_g03_output_sha256']:
            raise SystemExit(f'STOP {sid}: G03 frame differs from the approved reproduced output')
        g3png = d / 'g03' / g3['output']['file']
        src = Image.open(g3png).convert('RGB')
        n = sp['frames']
        if n != round(sp['duration_seconds'] * spec.fps):
            raise SystemExit(f'STOP {sid}: frames/duration mismatch')
        win = [window(cam, i / (n - 1)) for i in range(n)]
        audio, cues, peak = mix_motion_audio(sp, {AMB: inputs[AMB]}, {'beds': {AMB: {'gain_db': BED_GAIN_DB}}}, spec, [])
        wav, mp4 = d / f'{sid}_PRESENTATION_MIX.wav', d / f'{sid}_PRESENTATION_v02.mp4'
        media.write_wav24(audio, spec.audio_sample_rate, wav)
        fh = []

        def tap(it):
            for f in it:
                fh.append(sha256_bytes(f.tobytes()))
                yield f
        cmd = media.encode_review(tap(frames(src, cam, n)), n, spec, wav, mp4)
        out[sid] = {'mp4_sha256': sha256_file(mp4), 'wav_sha256': sha256_file(wav), 'frames': n,
                    'duration_s': sp['duration_seconds'], 'g03_frame_sha256': g3['output']['sha256'],
                    'g03_record_sha256': md['record_sha256'], 'base_frame_sha256': fr['metadata_json']['sha256'],
                    'camera': {'START_SCALE': 1.0, 'END_SCALE': cam['S_END'], 'FOCAL_POINT': list(cam['F']),
                               'TRANSLATION_X_END': cam['DRIFT_X'], 'TRANSLATION_Y_END': 0, 'focus': cam['focus'],
                               'MOTION_CURVE': '0.75 * cosine ease-in-out + 0.25 * linear (never stationary)',
                               'MAX_SAFE_CROP': {'end_window': [round(v, 3) for v in win[-1][2]],
                                                 'min_margin_px': round(min(min(b[0], b[1], 1920 - b[2], 1080 - b[3])
                                                                            for _, _, b in win), 4)},
                               'resample': 'PIL Image.resize(box, LANCZOS) of the approved frame, once per output frame'},
                    'pre_encode_frame_hash_list_sha256': sha256_bytes('\n'.join(fh).encode()),
                    'pre_encode_distinct_frames': len(set(fh)), 'frame0_equals_approved_frame': fh[0] == sha256_bytes(np.asarray(src).tobytes()),
                    'audio': {'bed': AMB, 'gain_db': BED_GAIN_DB, 'mix_peak_dbfs': peak, 'cues': cues},
                    'encode_command': [c if not str(c).startswith('/') else '<OUT>/' + Path(c).name for c in cmd],
                    'sources_after': {k: sha256_file(inputs[k]) for k in (FRAMES[sid], AMB)}}
        print(sid, out[sid]['mp4_sha256'], 'distinct', out[sid]['pre_encode_distinct_frames'], '/', n,
              'margin', out[sid]['camera']['MAX_SAFE_CROP']['min_margin_px'])
    (work / label / 'PRESENTATION_RESULT.json').write_text(json.dumps(out, indent=1, default=str))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
