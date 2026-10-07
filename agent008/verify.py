"""Output verification: measures the rendered clip against the shot contract. Read-only."""
import json
from pathlib import Path

import numpy as np

from . import media
from .errors import FailClosed

SILENCE_FLOOR_DBFS = -100.0   # an RMS window below this is treated as an unintended gap (digital silence)
WINDOW_SECONDS = 0.01


def frame_hashes(out_dir):
    lines = (Path(out_dir) / 'raw_frame_sha256.txt').read_text().split('\n')
    return [ln.split()[1] for ln in lines if ln.strip()]


def check_hold(hashes, start, end):
    """All raw frames in [start, end) are byte-identical, and equal to the frame before the hold."""
    hold = hashes[start:end]
    if len(set(hold)) != 1:
        raise FailClosed('HOLD_NOT_STATIC', f'{len(set(hold))} distinct frames in {start}..{end - 1}')
    if start > 0 and hashes[start - 1] != hold[0]:
        raise FailClosed('HOLD_DISCONTINUOUS', f'frame {start - 1} differs from hold')
    return True


def changing_frames(hashes):
    return [i for i in range(1, len(hashes)) if hashes[i] != hashes[i - 1]]


def audio_report(wav_path, sample_rate, cues, total_seconds):
    a = media.load_audio(wav_path, sample_rate, 2)
    n = len(a)
    if abs(n - total_seconds * sample_rate) > 1:
        raise FailClosed('AUDIO_LENGTH', f'{n} samples for {total_seconds}s')
    w = int(WINDOW_SECONDS * sample_rate)
    rms = np.sqrt((a[: n // w * w].reshape(-1, w, 2) ** 2).mean(axis=(1, 2)))
    rms_db = 20 * np.log10(np.maximum(rms, 1e-20))
    gaps = int((rms_db < SILENCE_FLOOR_DBFS).sum())
    peak = float(np.abs(a).max())
    return {'samples': n, 'peak_dbfs': round(20 * np.log10(peak), 3),
            'min_window_rms_dbfs': round(float(rms_db.min()), 2), 'silent_windows_below_floor': gaps,
            'window_seconds': WINDOW_SECONDS, 'floor_dbfs': SILENCE_FLOOR_DBFS}


def decoded_hold_drift(mp4, w, h, start, end):
    fr = media.decode_frames_rgb(mp4, w, h)
    hold = fr[start:end].astype(np.int16)
    drift = int(np.abs(hold - hold[0]).max()) if len(hold) else 0
    return {'decoded_frames': int(fr.shape[0]), 'max_abs_pixel_diff_within_hold': drift}


def verify(out_dir, provenance_path=None):
    out_dir = Path(out_dir)
    prov = json.loads((Path(provenance_path) if provenance_path else
                       out_dir / 'A008_EP005_S004_S005_PHASE0_PROVENANCE.json').read_text())
    tl = prov['timeline']
    spec = prov['output_spec']
    hashes = frame_hashes(out_dir)
    if len(hashes) != tl['total_frames']:
        raise FailClosed('FRAME_COUNT', str(len(hashes)))
    s4 = next(s for s in tl['shots'] if s['shot_id'] == 'S004')
    s5 = next(s for s in tl['shots'] if s['shot_id'] == 'S005')
    g = tl['timing_inputs']['S004']['glint']
    tilt = tl['timing_inputs']['S004']['mirror_tilt']
    check_hold(hashes, s5['start_frame'], s5['start_frame'] + s5['frames'])
    moving = changing_frames(hashes)
    last_event = g['start_frame'] + g['frames']           # first frame after the glint
    if moving and max(moving) > last_event:
        raise FailClosed('UNINTENDED_MOTION', f'frame changes after {last_event}: {[m for m in moving if m > last_event]}')
    chime = next(c for c in prov['audio_cues'] if c['asset_id'] == 'SFX-LUMI-CLUE-CHIME')
    if chime['clip_end_seconds'] > s4['end_seconds']:
        raise FailClosed('CHIME_CROSSES_INTO_S005', str(chime['clip_end_seconds']))
    if abs(chime['clip_start_seconds'] - (s4['start_frame'] + g['start_frame']) / spec['fps']) > 1e-9:
        raise FailClosed('CHIME_NOT_ON_GLINT')
    ar = audio_report(out_dir / prov['outputs']['mix_wav']['file'], spec['audio_sample_rate'], prov['audio_cues'],
                      tl['total_seconds'])
    if ar['peak_dbfs'] > spec['peak_ceiling_dbfs']:
        raise FailClosed('AUDIO_PEAK', str(ar['peak_dbfs']))
    if ar['silent_windows_below_floor'] != 0:
        raise FailClosed('AMBIENCE_GAP', str(ar['silent_windows_below_floor']))
    mp4 = out_dir / prov['outputs']['review_mp4']['file']
    aac = audio_report_from_mp4(mp4, spec['audio_sample_rate'])
    dd = decoded_hold_drift(mp4, spec['width'], spec['height'], s5['start_frame'], s5['start_frame'] + s5['frames'])
    if dd['decoded_frames'] != tl['total_frames']:
        raise FailClosed('DECODED_FRAME_COUNT', str(dd['decoded_frames']))
    return {
        'frames': len(hashes), 'distinct_raw_frames': len(set(hashes)),
        'raw_frame_changes_at': moving,
        'tilt_frames': [tilt['start_frame'], tilt['start_frame'] + tilt['frames'] - 1],
        'glint_frames': [g['start_frame'], g['start_frame'] + g['frames'] - 1],
        's005_hold_frames': [s5['start_frame'], s5['start_frame'] + s5['frames'] - 1],
        's005_hold_raw_identical_and_equal_to_last_s004_frame': True,
        'chime_clip_seconds': [chime['clip_start_seconds'], chime['clip_end_seconds']],
        's004_end_seconds': s4['end_seconds'],
        'mix_master': ar, 'review_aac_peak_dbfs': aac,
        'decoded_review': dd,
    }


def audio_report_from_mp4(mp4, sr):
    a = media.load_audio(mp4, sr, 2)
    return round(20 * np.log10(float(np.abs(a).max())), 3)
