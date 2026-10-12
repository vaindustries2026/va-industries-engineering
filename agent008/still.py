"""G02: production still-shot path (zero spend, no provider).

Holds one hash-verified, human-approved shot frame (SHOT_FRAME / BASE_FRAME or DERIVED_FRAME) for exactly
the shot's frame count, with deterministic crop / fit-scale / pad only, places the shot's governed audio
(AMBIENCE bed, FOLEY/SFX one-shot events, approved dialogue; fail closed otherwise) through the same mix used
for motion shots, encodes a REVIEW mp4 and verifies it. Shots with active overlays are accepted only when the
frame is an approved G03 DERIVED_FRAME whose composited overlay set equals the shot contract
(frame['overlays_composited'], from the G03 provenance). Not supported here, and failing closed rather than
being approximated: treatments on stills (G08), camera moves (G06), in-shot cuts (G07).
Nothing here calls a provider, uploads, registers or approves.
"""
import json
from pathlib import Path

import numpy as np

from . import AGENT_NAME, media
from .dialogue_timing import govern_dialogue_timing
from .errors import FailClosed
from .hashing import canonical_sha256, sha256_bytes, sha256_file, verify_file
from .motion.compose import auto_qc_frames, mix_motion_audio, resolve_dialogue
from . import g08
from .spec import IN_SHOT_CUT_SHOTS
from .verify import audio_report

AGENT_VERSION_G02 = 'agent008-v0.3-still'
FRAME_CLASSIFICATIONS = ('SHOT_FRAME/BASE_FRAME', 'SHOT_FRAME/DERIVED_FRAME')
FRAME_APPROVED_STATES = ('APPROVED', 'LOCKED')
REQUIRED_PROVENANCE = ('agent_version', 'status', 'shot_id', 'source_frame', 'layout', 'output_spec', 'audio_cues',
                       'qc', 'outputs', 'human_approval', 'safety')


def check_still_contract(spec_shot, spec, overlays_composited=None, frame_sha256=None, treatments_composited=None,
                         treatment_record=None):
    sid = spec_shot['shot_id']
    if spec_shot.get('video_generation_required'):
        raise FailClosed('STILL_PATH_NOT_FOR_MOTION_SHOT', sid)
    if sid in IN_SHOT_CUT_SHOTS:
        raise FailClosed('STILL_IN_SHOT_CUT_NEEDS_G07', sid)
    if spec_shot['treatments'] and not treatment_record:
        raise FailClosed('STILL_TREATMENTS_NEED_G08', f"{sid}: {[t.get('treatment_id') for t in spec_shot['treatments']]}")
    if treatment_record and not spec_shot['treatments']:
        raise FailClosed('TREATMENT_UNDECLARED', f'{sid}: treatment record for a shot without treatments')
    if spec_shot['active_overlays'] or overlays_composited or treatments_composited:   # G03 / G08 frame chain
        g08.resolve_frame_chain(spec_shot, frame_sha256, overlays_composited, treatments_composited)
    if spec_shot['frames'] != int(round(spec_shot['duration_seconds'] * spec.fps)):
        raise FailClosed('STILL_DURATION_FRAME_MISMATCH', f"{sid}: {spec_shot['frames']} vs {spec_shot['duration_seconds']} s")


def verify_source_frame(frame, spec_shot):
    """frame: {asset_id, registry_id, classification, registry_status, shot_id, path, expected_sha256}."""
    if frame.get('classification') not in FRAME_CLASSIFICATIONS:
        raise FailClosed('STILL_SOURCE_NOT_A_SHOT_FRAME', f"{frame.get('asset_id')}: {frame.get('classification')}")
    if frame.get('registry_status') not in FRAME_APPROVED_STATES:
        raise FailClosed('STILL_SOURCE_NOT_APPROVED', f"{frame.get('asset_id')}: {frame.get('registry_status')}")
    if frame.get('shot_id') != spec_shot['shot_id']:
        raise FailClosed('SHOT_IDENTITY_MISMATCH', f"frame for {frame.get('shot_id')}, shot {spec_shot['shot_id']}")
    if not frame.get('expected_sha256'):
        raise FailClosed('NO_EXPECTED_HASH', str(frame.get('asset_id')))
    return verify_file(frame['path'], frame['expected_sha256'], f"still frame {frame.get('asset_id')}")


def layout_frame(path, spec, crop=None):
    """Decode the frame to RGB, exact-pixel crop (optional), aspect-preserving fit to the output, centred pad."""
    rgba = media.load_rgba(path)
    h, w = rgba.shape[:2]
    if crop:
        x, y, cw, ch = (int(crop[k]) for k in ('x', 'y', 'w', 'h'))
        if x < 0 or y < 0 or cw <= 0 or ch <= 0 or x + cw > w or y + ch > h:
            raise FailClosed('CROP_OUT_OF_BOUNDS', f'{crop} on {w}x{h}')
        rgba = rgba[y:y + ch, x:x + cw].copy()
    ih, iw = rgba.shape[:2]
    k = min(spec.width / iw, spec.height / ih)
    fw, fh = int(round(iw * k)), int(round(ih * k))
    fitted = media.scale_rgba(rgba, fw, fh)
    out = np.zeros((spec.height, spec.width, 3), np.uint8)
    ox, oy = (spec.width - fw) // 2, (spec.height - fh) // 2
    out[oy:oy + fh, ox:ox + fw] = fitted[..., :3]
    if int(fitted[..., 3].min()) != 255:
        raise FailClosed('STILL_SOURCE_HAS_TRANSPARENCY', str(path))
    return out, {'source_size': [w, h], 'crop': crop, 'fit_scale': round(k, 6), 'fitted_size': [fw, fh],
                 'pad_offset': [ox, oy], 'pad_color': 'black', 'scale_flags': media.SCALE_FLAGS}


def compose_still_shot(spec_shot, frame, spec, asset_paths, timing, out_dir, crop=None, treatment_record=None):
    out_dir = Path(out_dir)
    composited = frame.get('overlays_composited')
    tcomp = frame.get('treatments_composited')
    if composited and frame.get('classification') != 'SHOT_FRAME/DERIVED_FRAME':
        raise FailClosed('OVERLAY_PRECOMPOSITE_NOT_DERIVED_FRAME', str(frame.get('asset_id')))
    check_still_contract(spec_shot, spec, composited, frame.get('expected_sha256') if (composited or tcomp) else None,
                         tcomp, treatment_record)
    frame_sha = verify_source_frame(frame, spec_shot)
    dialogue = resolve_dialogue(spec_shot, asset_paths, timing)
    dialogue_timing = govern_dialogue_timing(spec_shot, dialogue, asset_paths, timing, spec)
    img, layout = layout_frame(frame['path'], spec, crop)
    n = spec_shot['frames']
    plan = None
    if treatment_record:
        if crop or layout['fit_scale'] != 1.0 or layout['pad_offset'] != [0, 0]:
            raise FailClosed('TREATMENT_LAYOUT_NOT_IDENTITY', 'treatment geometry is in frame pixels; crop/scale/pad not allowed')
        plan = g08.plan_timed(spec_shot, treatment_record, frame_sha, (img.shape[1], img.shape[0]), timing, spec.fps,
                              tcomp, composited)
        window = sorted({w['start_frame'] + j for w in plan['windows'] for j in range(w['frames'])})
        distinct = {i: g08.render_frame(img, plan, i) for i in window}
        frame_at = lambda i: distinct.get(i, img)  # noqa: E731
        qc, _ = auto_qc_frames(np.stack([img] + [distinct[i] for i in window]), max_freeze_frames=n, intended_freeze=True)
        hashes = [sha256_bytes(frame_at(i).tobytes()) for i in range(n)]
        run, longest = 1, 1
        for a_, b_ in zip(hashes, hashes[1:]):
            run = run + 1 if a_ == b_ else 1
            longest = max(longest, run)
        qc.update({'frames': n, 'longest_identical_run': longest, 'distinct_frames': len(set(hashes)),
                   'frame_hash_list_sha256': sha256_bytes('\n'.join(hashes).encode())})
    else:
        frame_at = lambda i: img  # noqa: E731
        qc, _ = auto_qc_frames(np.broadcast_to(img, (n, *img.shape)), max_freeze_frames=n, intended_freeze=True)
    audio, cues, peak_db = mix_motion_audio(spec_shot, asset_paths, timing, spec, dialogue)
    out_dir.mkdir(parents=True, exist_ok=True)
    sid = spec_shot['shot_id']
    wav = out_dir / f'{sid}_STILL_MIX.wav'
    mp4 = out_dir / f'{sid}_STILL_REVIEW.mp4'
    for p in (wav, mp4):
        if p.exists():
            raise FailClosed('OUTPUT_EXISTS', str(p))
    media.write_wav24(audio, spec.audio_sample_rate, wav)
    cmd = media.encode_review((frame_at(i) for i in range(n)), n, spec, wav, mp4)
    if sha256_file(frame['path']) != frame_sha:
        raise FailClosed('SOURCE_MUTATED', str(frame['path']))

    ar = audio_report(wav, spec.audio_sample_rate, cues, n / spec.fps)
    pr = media.probe(mp4)
    v = [s for s in pr['streams'] if s['codec_type'] == 'video'][0]
    a = [s for s in pr['streams'] if s['codec_type'] == 'audio']
    qc.update({'expected_frames': n, 'output_frames': int(v.get('nb_frames', 0)),
               'output_resolution': f"{v['width']}x{v['height']}", 'expected_resolution': f'{spec.width}x{spec.height}',
               'output_fps': v['r_frame_rate'], 'expected_fps': f'{spec.fps}/1',
               'output_duration_s': float(v['duration']), 'expected_duration_s': spec_shot['duration_seconds'],
               'audio_streams': len(a), 'audio_sample_rate': int(a[0]['sample_rate']) if a else None,
               'audio_peak_dbfs': ar['peak_dbfs'], 'audio_silent_windows': ar['silent_windows_below_floor'],
               'held_frame_rgb_sha256': sha256_bytes(img.tobytes()),
               'overlays_applied': 0, 'treatments_applied': 0})
    if composited:
        qc['overlays_precomposited'] = len({o['asset_id'] for o in composited['overlays']})
    if plan:
        qc['treatments_applied'] = len(plan['windows'])
        qc['treatments_precomposited'] = len((tcomp or {}).get('treatments') or [])
    for ok, msg in ((qc['output_frames'] == n, 'frame count mismatch'),
                    (qc['output_resolution'] == qc['expected_resolution'], 'resolution mismatch'),
                    (qc['output_fps'] == qc['expected_fps'], 'fps mismatch'),
                    (abs(qc['output_duration_s'] - spec_shot['duration_seconds']) < 0.5 / spec.fps, 'duration mismatch'),
                    (len(a) == 1 and qc['audio_sample_rate'] == spec.audio_sample_rate, 'audio stream mismatch')):
        if not ok:
            qc['issues'].append(msg)
    qc['automatic_result'] = 'PASS' if not qc['issues'] else 'FAIL'
    prov = {
        'agent': AGENT_NAME, 'agent_version': AGENT_VERSION_G02, 'stage': 'G02 still shot', 'status': 'REVIEW',
        'shot_id': sid,
        'source_frame': {k: frame.get(k) for k in ('asset_id', 'registry_id', 'classification', 'registry_status',
                                                   'shot_id')} | {'verified_sha256': frame_sha}
                        | ({'overlays_composited': composited} if composited else {})
                        | ({'treatments_composited': tcomp} if tcomp else {}),
        'layout': layout, 'output_spec': spec.to_dict(), 'shot_spec': spec_shot, 'dialogue_tracks': dialogue,
        'dialogue_timing': dialogue_timing,
        **({'treatments': {'record_sha256': plan['record_sha256'], 'glass': plan['glass'],
                           'windows': [{k: v for k, v in w.items()} for w in plan['windows']]}} if plan else {}),
        'audio_cues': cues, 'mix_peak_dbfs': peak_db, 'qc': qc,
        'recipes': {'encode_command': [c if not str(c).startswith('/') else '<OUT>/' + Path(c).name for c in cmd]},
        'outputs': {'review_mp4': {'file': mp4.name, 'sha256': sha256_file(mp4), 'bytes': mp4.stat().st_size},
                    'mix_wav': {'file': wav.name, 'sha256': sha256_file(wav)}},
        'human_approval': {'required': True, 'approved': False, 'decisions': ['APPROVE', 'REJECT'],
                           'approve_by': 'exact review mp4 sha256'},
        'safety': {'provider_calls': 0, 'auto_approved': False, 'registered': False, 'source_mutated': False},
        'toolchain': media.toolchain(),
    }
    missing = [k for k in REQUIRED_PROVENANCE if k not in prov]
    if missing:
        raise FailClosed('PROVENANCE_INCOMPLETE', ','.join(missing))
    prov['deterministic_core_sha256'] = canonical_sha256({k: v for k, v in prov.items() if k != 'toolchain'})
    (out_dir / f'{sid}_STILL_PROVENANCE.json').write_text(json.dumps(prov, indent=1, sort_keys=True, default=str) + '\n')
    return prov
