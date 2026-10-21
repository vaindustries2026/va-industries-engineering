"""QC of the v03 assembled motion MP4s (format, motion magnitude vs codec noise, audio level / mapping).
Usage (repo root): python3 evidence/ep005/batch1_motion/b1_motion_qc_v03.py <work dir> S005 S013 S017"""
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

W, H, CODEC_NOISE = 1920, 1080, 0.037


def sh(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def loud(p):
    e = subprocess.run(['ffmpeg', '-nostats', '-hide_banner', '-i', str(p), '-vn', '-af', 'ebur128=peak=true+sample', '-f', 'null', '-'],
                       capture_output=True, text=True).stderr
    s = e[e.rindex('Summary'):]
    pk = [float(x) for x in re.findall(r'Peak:\s+(-?[\d.]+) dBFS', s)]
    v = subprocess.run(['ffmpeg', '-nostats', '-hide_banner', '-i', str(p), '-vn', '-af', 'volumedetect', '-f', 'null', '-'],
                       capture_output=True, text=True).stderr
    return {'integrated_lufs': float(re.search(r'I:\s+(-?[\d.]+) LUFS', s).group(1)), 'sample_peak_dbfs': pk[0], 'true_peak_dbtp': pk[1],
            'mean_volume_db': float(re.search(r'mean_volume: (-?[\d.]+) dB', v).group(1)),
            'max_volume_db': float(re.search(r'max_volume: (-?[\d.]+) dB', v).group(1))}


def qc(work, sid):
    a, b = Path(work) / 'assembly' / 'A' / sid, Path(work) / 'assembly' / 'B' / sid
    mp4 = a / 'MOTION_SMOKE_REVIEW.mp4'
    prov = json.loads((a / 'ASSEMBLY_PROVENANCE.json').read_text())
    pr = json.loads(subprocess.run(['ffprobe', '-v', 'error', '-count_frames', '-show_streams', '-of', 'json', str(mp4)],
                                   capture_output=True, check=True).stdout)
    v = [s for s in pr['streams'] if s['codec_type'] == 'video'][0]
    au = [s for s in pr['streams'] if s['codec_type'] == 'audio']
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(mp4), '-map', '0:v:0', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                         capture_output=True, check=True).stdout
    fr = np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)
    consec = [float(np.abs(fr[i + 1].astype(int) - fr[i].astype(int)).mean()) for i in range(len(fr) - 1)]
    L = loud(mp4)
    n = prov['shot_spec']['frames']
    cues = [f"{c['asset_id']}:{c['kind']}" for c in prov['audio_cues']]
    r = {'shot_id': sid, 'mp4_sha256': sh(mp4), 'run_b_sha256': sh(b / 'MOTION_SMOKE_REVIEW.mp4'),
         'video': {'codec': v['codec_name'], 'pix_fmt': v['pix_fmt'], 'res': f"{v['width']}x{v['height']}", 'fps': v['r_frame_rate'],
                   'frames': int(v['nb_read_frames']), 'duration_s': float(v['duration'])},
         'audio_streams': len(au), 'audio': L, 'audio_cues': cues, 'agent008_qc': prov['qc']['automatic_result'],
         'agent008_qc_issues': prov['qc']['issues'], 'overlays_precomposited_in_base_frame': prov['qc'].get('overlays_precomposited_in_base_frame'),
         'overlays_applied': prov['qc']['overlays_applied'],
         'motion': {'consecutive_mae_median': round(float(np.median(consec)), 4), 'consecutive_mae_min': round(min(consec), 4),
                    'first_last_mae': round(float(np.abs(fr[-1].astype(int) - fr[0].astype(int)).mean()), 3),
                    'codec_noise_ceiling_v01': CODEC_NOISE}}
    r['checks'] = {'res_1920x1080': r['video']['res'] == '1920x1080', 'fps_24': r['video']['fps'] == '24/1',
                   'exact_frames': r['video']['frames'] == n, 'exact_duration': abs(r['video']['duration_s'] - n / 24) < 1e-6,
                   'h264_yuv420p': r['video']['codec'] == 'h264' and r['video']['pix_fmt'] == 'yuv420p',
                   'deterministic_two_runs': r['mp4_sha256'] == r['run_b_sha256'], 'agent008_qc_pass': r['agent008_qc'] == 'PASS',
                   'g03_travelled_not_reapplied': r['overlays_applied'] == 0 and (r['overlays_precomposited_in_base_frame'] or 0) > 0,
                   'pixel_motion_far_above_codec_noise': r['motion']['consecutive_mae_median'] > 10 * CODEC_NOISE,
                   'AUDIO_TRACK_PRESENT': r['audio_streams'] == 1,
                   'AMBIENCE_ONLY_PROVIDER_AUDIO_STRIPPED': cues == ['AMB-BATHROOM-QUIET-v01:BED'],
                   'AUDIBLE_LEVEL_PASS': -33 <= L['integrated_lufs'] <= -27 and L['true_peak_dbtp'] <= -18 and L['sample_peak_dbfs'] <= -18,
                   'NO_DIALOGUE': not any('DIALOGUE' in c for c in cues)}
    r['result'] = 'PASS' if all(r['checks'].values()) else 'FAIL'
    return r


if __name__ == '__main__':
    out = {sid: qc(sys.argv[1], sid) for sid in sys.argv[2:]}
    (Path(sys.argv[1]) / 'ASSEMBLY_QC_v03.json').write_text(json.dumps(out, indent=1))
    for sid, r in out.items():
        print(sid, r['result'], r['video'], r['motion'], r['audio'], [k for k, v in r['checks'].items() if not v])
