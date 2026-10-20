"""Independent QC of the Batch 1 still-path review MP4s (same checks as evidence/agent008/phase1/s029/s029_independent_qc.py,
plus overlay checks). Decoded H.264 frames of a held still vary at codec level (S029_DECODED_FRAME_VARIATION_v1: max mean-abs
0.011), so "no unintended treatment" = 0 treatments + 1 distinct pre-encode frame + decoded variation vs frame 0 < 0.05 mean-abs;
"overlay once" = decoded vs G03 frame inside the overlay boxes < 25% of decoded vs bare base frame there. Usage (repo root): python3 evidence/ep005/batch1_render/b1_independent_qc.py <render work dir>
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

W, H = 1920, 1080
AMB = 'ea28fad468e353b99d48070d12853620f08e8b05c8d912706122d31176544d2f'


def sh(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def rgb(p):
    b = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(p), '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True, check=True).stdout
    return np.frombuffer(b, np.uint8).reshape(-1, H, W, 3)


def qc(work, sid, rec_row, frame_row):
    d = Path(work) / 'RUN1' / sid
    mp4, wav = d / 'renderA' / f'{sid}_STILL_REVIEW.mp4', d / 'renderA' / f'{sid}_STILL_MIX.wav'
    prov = json.loads((d / 'renderA' / f'{sid}_STILL_PROVENANCE.json').read_text())
    g03p = json.loads((d / 'g03' / f'{sid}_G03_OVERLAY_PROVENANCE.json').read_text())
    g03png = d / 'g03' / f'{sid}_G03_OVERLAY_FRAME_CANDIDATE.png'
    base = Path(work) / 'inputs' / Path(frame_row['storage_path']).name
    n = prov['shot_spec']['frames'] if 'frames' in prov['shot_spec'] else prov['qc']['expected_frames']
    pr = json.loads(subprocess.run(['ffprobe', '-v', 'error', '-count_frames', '-show_streams', '-show_format', '-of', 'json', str(mp4)],
                                   capture_output=True, check=True).stdout)
    v = [s for s in pr['streams'] if s['codec_type'] == 'video']
    a = [s for s in pr['streams'] if s['codec_type'] == 'audio']
    fr = rgb(mp4)
    hashes = {hashlib.sha256(f.tobytes()).hexdigest() for f in fr}
    var = [float(np.abs(f.astype(int) - fr[0].astype(int)).mean()) for f in fr]
    g3, b0 = rgb(g03png)[0].astype(int), rgb(base)[0].astype(int)
    f0 = fr[0].astype(int)
    boxes = [q['visible_box'] for q in g03p['placements']]
    inside = np.zeros((H, W), bool)
    for x0, y0, x1, y1 in boxes:
        inside[y0:y1, x0:x1] = True
    au = np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-i', str(mp4), '-map', '0:a:0', '-f', 'f64le', '-ac', '2', '-ar', '48000', '-'],
                                      capture_output=True, check=True).stdout, '<f8').reshape(-1, 2)
    db = lambda x: round(float(20 * np.log10(max(x, 1e-12))), 2)  # noqa: E731
    win = int(0.05 * 48000)
    rms = [np.sqrt(np.mean(au[i:i + win] ** 2)) for i in range(0, len(au) - win, win)]
    rec = rec_row['metadata_json']
    r = {'shot_id': sid, 'mp4_sha256': sh(mp4), 'bytes': int(pr['format']['size']),
         'video': {'codec': v[0]['codec_name'], 'profile': v[0].get('profile'), 'pix_fmt': v[0]['pix_fmt'],
                   'res': f"{v[0]['width']}x{v[0]['height']}", 'r_frame_rate': v[0]['r_frame_rate'],
                   'nb_read_frames': int(v[0]['nb_read_frames']), 'duration_s': float(v[0]['duration'])},
         'audio': {'streams': len(a), 'codec': a[0]['codec_name'], 'sample_rate': int(a[0]['sample_rate']), 'channels': a[0]['channels'],
                   'duration_s': float(a[0]['duration'])},
         'expected_frames': n, 'decoded_frames': len(fr), 'distinct_decoded_frames': len(hashes),
         'decoded_max_mean_abs_vs_frame0': round(max(var), 5), 'source_distinct_frames_pre_encode': prov['qc']['distinct_frames'],
         'record_distinct_overlay_assets': len({q['asset_id'] for q in rec_row['metadata_json']['placements']}),
         'overlay_boxes': boxes, 'overlay_count_provenance': prov['qc']['overlays_precomposited'],
         'overlays_applied_in_render': prov['qc']['overlays_applied'], 'treatments_applied': prov['qc']['treatments_applied'],
         'record_placement_count': rec['placement_count'],
         'mae_decoded_vs_g03_frame_all': round(float(np.abs(f0 - g3).mean()), 3),
         'mae_decoded_vs_g03_frame_in_overlay_boxes': round(float(np.abs(f0 - g3)[inside].mean()), 3),
         'mae_decoded_vs_base_frame_in_overlay_boxes': round(float(np.abs(f0 - b0)[inside].mean()), 3),
         'mae_decoded_vs_base_frame_outside_boxes': round(float(np.abs(f0 - b0)[~inside].mean()), 3),
         'g03_frame_sha256': sh(g03png), 'approved_record_reproduced_sha256': rec['reproduced_g03_output_sha256'],
         'g03_record_sha_used': g03p['placement_record']['sha256'], 'approved_record_sha256': rec['record_sha256'],
         'base_frame_sha256_used': g03p['source_frame']['verified_sha256'], 'approved_frame_sha256': frame_row['metadata_json']['sha256'],
         'audio_cues': prov['audio_cues'], 'dialogue_tracks': prov['dialogue_tracks'],
         'audio_peak_dbfs': db(np.abs(au).max()), 'audio_min_50ms_rms_dbfs_excl_edges': db(min(rms[1:-1])),
         'clipped_samples': int((np.abs(au) >= 0.999).sum()), 'agent008_qc': prov['qc']['automatic_result'],
         'agent008_qc_issues': prov['qc']['issues'], 'ambience_after_sha256': sh(Path(work) / 'inputs' / 'AMB-BATHROOM-QUIET-v01.wav'),
         'base_after_sha256': sh(base)}
    c = {'res_1920x1080': r['video']['res'] == '1920x1080', 'fps_24': r['video']['r_frame_rate'] == '24/1',
         'exact_frame_count': r['video']['nb_read_frames'] == n == r['decoded_frames'],
         'exact_duration': abs(r['video']['duration_s'] - n / 24) < 1e-6,
         'h264_yuv420p': r['video']['codec'] == 'h264' and r['video']['pix_fmt'] == 'yuv420p',
         'one_audio_aac_48k_stereo': r['audio']['streams'] == 1 and r['audio']['codec'] == 'aac' and r['audio']['sample_rate'] == 48000 and r['audio']['channels'] == 2,
         'expected_overlay_count': r['overlay_count_provenance'] == r['record_distinct_overlay_assets'] and len(boxes) == r['record_placement_count'],
         'approved_placement_certificate': r['g03_record_sha_used'] == r['approved_record_sha256'] and rec_row['status'] == 'APPROVED',
         'no_stale_certificate': r['g03_frame_sha256'] == r['approved_record_reproduced_sha256'],
         'no_duplicate_g03_application': r['overlays_applied_in_render'] == 0 and r['mae_decoded_vs_g03_frame_in_overlay_boxes'] < 0.25 * r['mae_decoded_vs_base_frame_in_overlay_boxes'],
         'overlays_visible': r['mae_decoded_vs_base_frame_in_overlay_boxes'] > 10.0,
         'no_clipping_overlays': all(0 <= b[0] and 0 <= b[1] and b[2] <= W and b[3] <= H for b in boxes),
         'no_unintended_treatment': r['treatments_applied'] == 0 and r['source_distinct_frames_pre_encode'] == 1 and r['decoded_max_mean_abs_vs_frame0'] < 0.05,
         'approved_base_frame_sha': r['base_frame_sha256_used'] == r['approved_frame_sha256'] == r['base_after_sha256'],
         'audio_mapping_ambience_only': [x['asset_id'] for x in r['audio_cues']] == ['AMB-BATHROOM-QUIET-v01'] and r['ambience_after_sha256'] == AMB,
         'ambience_present': r['audio_min_50ms_rms_dbfs_excl_edges'] > -60,
         'no_unintended_dialogue': r['dialogue_tracks'] == [] or not r['dialogue_tracks'],
         'no_audio_clipping': r['clipped_samples'] == 0 and r['audio_peak_dbfs'] < -1,
         'agent008_qc_pass': r['agent008_qc'] == 'PASS' and not r['agent008_qc_issues'],
         'deterministic_render': sh(mp4) == sh(Path(work) / 'RUN2' / sid / 'renderA' / f'{sid}_STILL_REVIEW.mp4')
                                 == sh(d / 'renderB' / f'{sid}_STILL_REVIEW.mp4')}
    r['checks'] = c
    r['result'] = 'PASS' if all(c.values()) else 'FAIL'
    return r


if __name__ == '__main__':
    work = Path(sys.argv[1])
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
    from agent008.motion.http import UrllibHttpClient
    http = UrllibHttpClient()
    rows = {x['asset_id']: x for x in json.loads(http.send('GET', 'https://ziluiwrwwbayhcskeere.supabase.co/rest/v1/asset_registry?or=('
            'asset_id.like.G03-REC-EP005-*,asset_id.like.FRAME-EP005-F*)&select=*', {'Accept': 'application/json'}).body)}
    fam = {'S005': 'FRAME-EP005-F01-BASE-CAND-v02', 'S013': 'FRAME-EP005-F01-BASE-CAND-v02',
           'S017': 'FRAME-EP005-F09-BASE-CAND-v01', 'S019': 'FRAME-EP005-F15-BASE-CAND-v02'}
    out = {sid: qc(work, sid, rows[f'G03-REC-EP005-{sid}-v01'], rows[f]) for sid, f in fam.items()}
    (work / 'INDEPENDENT_QC.json').write_text(json.dumps(out, indent=1, default=str))
    for sid, r in out.items():
        print(sid, r['result'], r['video'], r['decoded_frames'], 'overlays', r['overlay_count_provenance'],
              'mae_in_boxes vs g03', r['mae_decoded_vs_g03_frame_in_overlay_boxes'], 'vs base', r['mae_decoded_vs_base_frame_in_overlay_boxes'],
              'peak', r['audio_peak_dbfs'], [k for k, v in r['checks'].items() if not v])
