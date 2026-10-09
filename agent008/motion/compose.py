"""Stages 8D/8F for generated motion: consume the exact hashed provider output, apply only contracted
treatments, place contracted audio, encode a REVIEW shot, run automatic QC, write provenance."""
import json
from pathlib import Path

import numpy as np

from .. import AGENT_NAME, media
from ..errors import FailClosed
from ..hashing import canonical_sha256, sha256_bytes, sha256_file, verify_file
from ..render import db_to_gain
from ..verify import audio_report

AGENT_VERSION_V02 = 'agent008-v0.2-motion'
BLACK_FRAME_MEAN = 12.0        # mean RGB code value below which a frame counts as black
REQUIRED_PROVENANCE = ('agent_version', 'status', 'shot_id', 'motion_request', 'motion_result', 'raw_output_verified_sha256',
                       'output_spec', 'audio_cues', 'qc', 'outputs', 'human_approval', 'safety')


def decode_normalised(raw_path, spec, frames_needed):
    """Decode the provider clip to the output spec: fps resample, aspect-preserving fit, centred pad. Deterministic."""
    vf = (f"fps={spec.fps},scale={spec.width}:{spec.height}:force_original_aspect_ratio=decrease:flags={media.SCALE_FLAGS},"
          f"pad={spec.width}:{spec.height}:(ow-iw)/2:(oh-ih)/2:color=black,format=rgb24")
    raw = media._run([media.FFMPEG, '-v', 'error', '-i', str(raw_path), '-map', '0:v:0', '-vf', vf,
                      '-frames:v', str(frames_needed), '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'])
    fr = np.frombuffer(raw, dtype=np.uint8).reshape(-1, spec.height, spec.width, 3)
    if fr.shape[0] < frames_needed:
        raise FailClosed('RAW_TOO_SHORT', f'{fr.shape[0]} frames, shot needs {frames_needed}')
    return fr


def auto_qc_frames(frames, max_freeze_frames, intended_freeze=False):
    means = frames.reshape(frames.shape[0], -1).mean(axis=1)
    black = [int(i) for i in np.nonzero(means < BLACK_FRAME_MEAN)[0]]
    hashes = [sha256_bytes(f.tobytes()) for f in frames]
    run, longest = 1, 1
    for a, b in zip(hashes, hashes[1:]):
        run = run + 1 if a == b else 1
        longest = max(longest, run)
    issues = []
    if black:
        issues.append(f'black frames {black[:10]}')
    if longest > max_freeze_frames and not intended_freeze:
        issues.append(f'freeze of {longest} identical frames')
    return {'frames': len(hashes), 'black_frames': black, 'longest_identical_run': longest,
            'max_freeze_frames': max_freeze_frames, 'distinct_frames': len(set(hashes)),
            'frame_hash_list_sha256': sha256_bytes('\n'.join(hashes).encode()), 'issues': issues}, hashes


DIALOGUE_APPROVED_STATES = ('APPROVED', 'LOCKED')


def resolve_dialogue(spec_shot, inputs, timing):
    """Bind every manifest dialogue slot to exactly one approved, hash-verified clip. Fail closed otherwise.

    timing['dialogue'] holds one entry per slot, in slot order: shot_id, speaker, text, audio_asset_id,
    expected_sha256, registry_status, start_seconds, gain_db. The clip file is inputs[audio_asset_id].
    """
    slots = spec_shot.get('dialogue_slots') or []
    tracks = list(timing.get('dialogue') or [])
    if len(tracks) < len(slots):
        raise FailClosed('DIALOGUE_SLOT_UNFILLED', f"{spec_shot['shot_id']}: {len(slots)} slot(s), {len(tracks)} clip(s)")
    if len(tracks) > len(slots):
        raise FailClosed('DIALOGUE_UNEXPECTED', f"{spec_shot['shot_id']}: {len(tracks)} clip(s) for {len(slots)} slot(s)")
    resolved = []
    for slot, t in zip(slots, tracks):
        aid = t.get('audio_asset_id')
        if t.get('shot_id') != slot['shot_id']:
            raise FailClosed('DIALOGUE_SHOT_MISMATCH', f"{t.get('shot_id')} != {slot['shot_id']}")
        if t.get('speaker') != slot['speaker']:
            raise FailClosed('DIALOGUE_SPEAKER_MISMATCH', f"{t.get('speaker')} != {slot['speaker']}")
        if t.get('text') != slot['text']:
            raise FailClosed('DIALOGUE_TEXT_MISMATCH', str(aid))
        if t.get('registry_status') not in DIALOGUE_APPROVED_STATES:
            raise FailClosed('DIALOGUE_NOT_APPROVED', f"{aid}: {t.get('registry_status')}")
        if not aid or aid not in inputs:
            raise FailClosed('DIALOGUE_REQUIRES_APPROVED_AUDIO', str(aid))
        sha = verify_file(inputs[aid], t.get('expected_sha256'), f'dialogue {aid}')
        if not 0 <= float(t['start_seconds']) < spec_shot['duration_seconds']:
            raise FailClosed('DIALOGUE_TIMING_INVALID', f"{aid}: {t['start_seconds']}")
        resolved.append({'shot_id': slot['shot_id'], 'speaker': slot['speaker'], 'text': slot['text'],
                         'text_sha256': sha256_bytes(slot['text'].encode('utf-8')), 'audio_asset_id': aid,
                         'sha256': sha, 'registry_status': t['registry_status'],
                         'start_seconds': float(t['start_seconds']), 'gain_db': float(t.get('gain_db', 0.0))})
    return resolved


def mix_motion_audio(spec_shot, inputs, timing, spec, dialogue=()):
    sr, ch = spec.audio_sample_rate, spec.audio_channels
    total = int(round(spec_shot['frames'] / spec.fps * sr))
    out = np.zeros((total, ch))
    cues = []
    for d in dialogue:
        a = media.load_audio(inputs[d['audio_asset_id']], sr, ch) * db_to_gain(d['gain_db'])
        start = int(round(d['start_seconds'] * sr))
        if start + len(a) > total:
            raise FailClosed('DIALOGUE_OVERRUNS_SHOT', f"{d['audio_asset_id']} ends at {(start + len(a)) / sr:.3f} s")
        out[start:start + len(a)] += a              # placed once; never looped, stretched or trimmed
        cues.append({'asset_id': d['audio_asset_id'], 'kind': 'DIALOGUE', 'start_s': start / sr,
                     'end_s': (start + len(a)) / sr, 'gain_db': d['gain_db'], 'sha256': d['sha256']})
    bed_ids = [a['asset_id'] for a in spec_shot['mapped_audio']]
    for aid in bed_ids:
        a = media.load_audio(inputs[aid], sr, ch)
        g = timing.get('beds', {}).get(aid, {}).get('gain_db', 0.0)
        reps = int(np.ceil(total / len(a)))
        bed = np.tile(a, (reps, 1))[:total] * db_to_gain(g)
        f = int(0.02 * sr)
        ramp = np.linspace(0, 1, f, endpoint=False)[:, None]
        bed[:f] *= ramp
        bed[-f:] *= ramp[::-1]
        out += bed
        cues.append({'asset_id': aid, 'kind': 'BED', 'start_s': 0.0, 'end_s': total / sr, 'gain_db': g})
    for s in spec_shot['named_sfx']:
        aid = s['asset_id']
        t = timing.get('named', {}).get(aid)
        if not t:
            raise FailClosed('NAMED_AUDIO_WITHOUT_TIMING', aid)
        a = media.load_audio(inputs[aid], sr, ch) * db_to_gain(t.get('gain_db', 0.0))
        start = int(round(t['start_seconds'] * sr))
        end_by = int(round(t['fade_complete_by_seconds'] * sr)) if 'fade_complete_by_seconds' in t else total
        keep = max(0, min(len(a), end_by - start))
        a = a[:keep].copy()
        fo = min(keep, int(round(t.get('fade_out_seconds', 0.0) * sr)))
        if fo:
            a[-fo:] *= np.linspace(1, 0, fo)[:, None]
        out[start:start + keep] += a
        cues.append({'asset_id': aid, 'kind': 'NAMED', 'start_s': start / sr, 'end_s': (start + keep) / sr,
                     'gain_db': t.get('gain_db', 0.0), 'fade_out_s': t.get('fade_out_seconds', 0.0)})
    peak = float(np.abs(out).max()) if out.size else 0.0
    peak_db = 20 * np.log10(peak) if peak > 0 else -np.inf
    if peak_db > spec.peak_ceiling_dbfs:
        raise FailClosed('AUDIO_PEAK_EXCEEDS_CEILING', f'{peak_db:.2f}')
    return out, cues, round(peak_db, 3)


def compose_motion_shot(motion_result, motion_request, spec_shot, spec, asset_paths, timing, out_dir,
                        max_freeze_frames=24):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    if motion_result.provider_status != 'COMPLETED':
        raise FailClosed('MOTION_NOT_COMPLETED', motion_result.provider_status)
    raw = verify_file(motion_result.raw_output_path, motion_result.raw_output_sha256, 'raw provider output')
    if motion_result.source_frame_sha256 != motion_request.source_frame_sha256 \
            or motion_result.prompt_hash != motion_request.prompt_sha256:
        raise FailClosed('MOTION_RESULT_REQUEST_MISMATCH')
    if spec_shot['shot_id'] != motion_request.shot_id:
        raise FailClosed('SHOT_IDENTITY_MISMATCH')
    if spec_shot['active_overlays'] or spec_shot['treatments']:
        raise FailClosed('MOTION_TREATMENTS_NEED_TRACKING_V02',
                         'overlays/treatments on generated motion need tracked placement (not in v0.2)')
    dialogue = resolve_dialogue(spec_shot, asset_paths, timing)
    frames = decode_normalised(motion_result.raw_output_path, spec, spec_shot['frames'])[:spec_shot['frames']]
    qc, hashes = auto_qc_frames(frames, max_freeze_frames)
    audio, cues, peak_db = mix_motion_audio(spec_shot, asset_paths, timing, spec, dialogue)
    wav = out_dir / f"{spec_shot['shot_id']}_MOTION_MIX.wav"
    media.write_wav24(audio, spec.audio_sample_rate, wav)
    mp4 = out_dir / 'MOTION_SMOKE_REVIEW.mp4'
    cmd = media.encode_review(iter(frames), len(frames), spec, wav, mp4)
    ar = audio_report(wav, spec.audio_sample_rate, cues, spec_shot['frames'] / spec.fps)
    pr = media.probe(mp4)
    v = [s for s in pr['streams'] if s['codec_type'] == 'video'][0]
    qc.update({'expected_frames': spec_shot['frames'], 'output_frames': int(v.get('nb_frames', 0)),
               'output_resolution': f"{v['width']}x{v['height']}", 'expected_resolution': f'{spec.width}x{spec.height}',
               'output_duration_s': float(pr['format']['duration']), 'expected_duration_s': spec_shot['duration_seconds'],
               'audio_peak_dbfs': ar['peak_dbfs'], 'audio_silent_windows': ar['silent_windows_below_floor'],
               'overlays_applied': 0, 'treatments_applied': 0})
    if qc['output_frames'] != qc['expected_frames']:
        qc['issues'].append('frame count mismatch')
    if qc['output_resolution'] != qc['expected_resolution']:
        qc['issues'].append('resolution mismatch')
    qc['automatic_result'] = 'PASS' if not qc['issues'] else 'FAIL'
    prov = {
        'agent': AGENT_NAME, 'agent_version': AGENT_VERSION_V02, 'stage': '8C->8D->8F', 'status': 'REVIEW',
        'shot_id': spec_shot['shot_id'], 'motion_request': motion_request.to_dict(),
        'motion_result': motion_result.to_dict(), 'raw_output_verified_sha256': raw,
        'output_spec': spec.to_dict(), 'shot_spec': spec_shot, 'dialogue_tracks': dialogue,
        'audio_cues': cues, 'mix_peak_dbfs': peak_db,
        'qc': qc, 'recipes': {'encode_command': [c if not str(c).startswith('/') else '<OUT>/' + Path(c).name for c in cmd]},
        'outputs': {'review_mp4': {'file': mp4.name, 'sha256': sha256_file(mp4), 'bytes': mp4.stat().st_size},
                    'mix_wav': {'file': wav.name, 'sha256': sha256_file(wav)}},
        'human_approval': {'required': True, 'approved': False, 'decisions': ['APPROVE', 'REJECT', 'REGENERATE'],
                           'approve_by': 'exact review mp4 sha256'},
        'safety': {'auto_approved': False, 'auto_retry': False}, 'toolchain': media.toolchain(),
    }
    missing = [k for k in REQUIRED_PROVENANCE if k not in prov]
    if missing:
        raise FailClosed('PROVENANCE_INCOMPLETE', ','.join(missing))
    prov['deterministic_core_sha256'] = canonical_sha256({k: v for k, v in prov.items() if k != 'motion_result'})
    (out_dir / 'MOTION_SMOKE_PROVENANCE.json').write_text(json.dumps(prov, indent=1, sort_keys=True, default=str) + '\n')
    return prov
