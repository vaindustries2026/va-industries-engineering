"""QC of the v02 presentation MP4s: format, visual-motion (real camera transform vs codec noise), audio level, content.

Usage (repo root): python3 evidence/ep005/batch1_render/b1_presentation_qc_v02.py <work dir>
Motion: decoded frame i is compared with (a) the expected transformed frame i rendered from the approved G03 frame with the
recorded transform and (b) the untransformed approved frame. Real transform motion = (a) stays at codec level while (b) grows
far beyond the v01 codec-noise ceiling (decoded mean-abs vs frame 0 <= 0.037 on the held v01 MP4s). Audio: EBU R128
integrated loudness + true peak and volumedetect on the encoded MP4; ambience bed only.
"""
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from b1_presentation_v02 import AMB, BED_GAIN_DB, CAMERA, frames, window  # noqa: E402

W, H = 1920, 1080
V01_CODEC_NOISE_MAX = 0.037       # max decoded mean-abs vs frame 0 across the four held v01 MP4s (B1_INDEPENDENT_QC_v1.json)


def sh(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def decode(p):
    b = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(p), '-map', '0:v:0', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                       capture_output=True, check=True).stdout
    return np.frombuffer(b, np.uint8).reshape(-1, H, W, 3)


def loud(p):
    e = subprocess.run(['ffmpeg', '-nostats', '-hide_banner', '-i', str(p), '-vn', '-af', 'ebur128=peak=true+sample', '-f', 'null', '-'],
                       capture_output=True, text=True).stderr
    s = e[e.rindex('Summary'):]
    i = float(re.search(r'I:\s+(-?[\d.]+) LUFS', s).group(1))
    peaks = [float(x) for x in re.findall(r'Peak:\s+(-?[\d.inf]+) dBFS', s)]
    v = subprocess.run(['ffmpeg', '-nostats', '-hide_banner', '-i', str(p), '-vn', '-af', 'volumedetect', '-f', 'null', '-'],
                       capture_output=True, text=True).stderr
    return {'integrated_lufs': i, 'sample_peak_dbfs': peaks[0], 'true_peak_dbtp': peaks[1],
            'mean_volume_db': float(re.search(r'mean_volume: (-?[\d.]+) dB', v).group(1)),
            'max_volume_db': float(re.search(r'max_volume: (-?[\d.]+) dB', v).group(1))}


def qc(work, sid, res):
    d = Path(work) / 'RUN_A' / sid
    mp4 = d / f'{sid}_PRESENTATION_v02.mp4'
    g3 = Image.open(next((d / 'g03').glob('*_G03_OVERLAY_FRAME_CANDIDATE.png'))).convert('RGB')
    src = np.asarray(g3).astype(int)
    cam, n = CAMERA[sid], res['frames']
    fr = decode(mp4)
    exp = list(frames(g3, cam, n))
    mae = lambda a, b: float(np.abs(a.astype(int) - b.astype(int)).mean())  # noqa: E731
    vs_exp = [mae(fr[i], exp[i]) for i in range(n)]
    vs_src = [mae(fr[i], src) for i in range(n)]
    consec = [mae(fr[i + 1], fr[i]) for i in range(n - 1)]
    pr = json.loads(subprocess.run(['ffprobe', '-v', 'error', '-count_frames', '-show_streams', '-of', 'json', str(mp4)],
                                   capture_output=True, check=True).stdout)
    v = [s for s in pr['streams'] if s['codec_type'] == 'video'][0]
    a = [s for s in pr['streams'] if s['codec_type'] == 'audio']
    au = loud(mp4)
    border = float(min(fr[:, :, :8].mean(), fr[:, :, -8:].mean(), fr[:, :8].mean(), fr[:, -8:].mean()))
    r = {'shot_id': sid, 'mp4_sha256': sh(mp4), 'run_b_sha256': sh(Path(work) / 'RUN_B' / sid / f'{sid}_PRESENTATION_v02.mp4'),
         'video': {'codec': v['codec_name'], 'pix_fmt': v['pix_fmt'], 'res': f"{v['width']}x{v['height']}", 'fps': v['r_frame_rate'],
                   'frames': int(v['nb_read_frames']), 'duration_s': float(v['duration'])},
         'audio_streams': len(a), 'camera': res['camera'],
         'motion': {'decoded_vs_expected_transform_mae_max': round(max(vs_exp), 3),
                    'decoded_vs_untransformed_mae_first': round(vs_src[0], 3), 'decoded_vs_untransformed_mae_last': round(vs_src[-1], 3),
                    'consecutive_mae_min': round(min(consec), 4), 'consecutive_mae_median': round(float(np.median(consec)), 4),
                    'consecutive_mae_max': round(max(consec), 4), 'v01_codec_noise_ceiling': V01_CODEC_NOISE_MAX,
                    'last_vs_first_mae': round(mae(fr[-1], fr[0]), 3), 'pre_encode_distinct_frames': res['pre_encode_distinct_frames'],
                    'min_border_mean_8px': round(border, 2)},
         'audio': {**au, 'gain_db': BED_GAIN_DB, 'cues': [c['asset_id'] + ':' + c['kind'] for c in res['audio']['cues']]}}
    m, A = r['motion'], r['audio']
    r['checks'] = {
        'res_1920x1080': r['video']['res'] == '1920x1080', 'fps_24': r['video']['fps'] == '24/1',
        'exact_frames': r['video']['frames'] == n, 'exact_duration': abs(r['video']['duration_s'] - res['duration_s']) < 1e-6,
        'h264_yuv420p': r['video']['codec'] == 'h264' and r['video']['pix_fmt'] == 'yuv420p',
        'deterministic_two_runs_byte_identical': r['mp4_sha256'] == r['run_b_sha256'] == res['mp4_sha256'],
        'MEASURED_MOTION_PASS': (m['last_vs_first_mae'] > 50 * V01_CODEC_NOISE_MAX and m['consecutive_mae_min'] > V01_CODEC_NOISE_MAX
                                 and m['pre_encode_distinct_frames'] == n),
        'motion_is_the_approved_transform': m['decoded_vs_expected_transform_mae_max'] < 3.0
                                            and m['decoded_vs_untransformed_mae_last'] > 3 * m['decoded_vs_expected_transform_mae_max'],
        'frame0_is_approved_content': res['frame0_equals_approved_frame'] and m['decoded_vs_untransformed_mae_first'] < 3.0,
        'safe_bounds_no_edge_exposure': res['camera']['MAX_SAFE_CROP']['min_margin_px'] >= 0 and m['min_border_mean_8px'] > 20,
        'approved_g03_frame': res['g03_frame_sha256'] is not None,
        'AUDIO_TRACK_PRESENT': r['audio_streams'] == 1,
        'AMBIENCE_ASSET_APPROVED': A['cues'] == [f'{AMB}:BED'] and res['sources_after'][AMB] == 'ea28fad468e353b99d48070d12853620f08e8b05c8d912706122d31176544d2f',
        'AUDIBLE_LEVEL_PASS': -33.0 <= A['integrated_lufs'] <= -27.0 and A['true_peak_dbtp'] <= -18.0 and A['sample_peak_dbfs'] <= -18.0,
        'NO_DIALOGUE': not any('DIALOGUE' in c for c in A['cues']),
        'NO_UNAPPROVED_SFX': all(c.endswith(':BED') for c in A['cues'])}
    r['result'] = 'PASS' if all(r['checks'].values()) else 'FAIL'
    for i, tag in ((0, 'first'), (n // 2, 'mid'), (n - 1, 'last')):
        Image.fromarray(fr[i]).resize((640, 360), Image.LANCZOS).save(d / f'view_{tag}.png')
    return r


if __name__ == '__main__':
    work = Path(sys.argv[1])
    res = json.loads((work / 'RUN_A' / 'PRESENTATION_RESULT.json').read_text())
    out = {sid: qc(work, sid, res[sid]) for sid in CAMERA}
    (work / 'PRESENTATION_QC_v02.json').write_text(json.dumps(out, indent=1))
    for sid, r in out.items():
        print(sid, r['result'], json.dumps(r['motion']), json.dumps({k: r['audio'][k] for k in ('integrated_lufs', 'true_peak_dbtp', 'sample_peak_dbfs', 'mean_volume_db', 'max_volume_db')}),
              [k for k, v in r['checks'].items() if not v])
