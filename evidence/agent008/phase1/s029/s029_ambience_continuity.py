"""Read-only S028 -> S029 ambience continuity check (no render, no writes outside <work_dir>).

Usage (repo root): python3 evidence/agent008/phase1/s029/s029_ambience_continuity.py <work_dir> <s028_final_mp4>
Decodes the approved S028 final soundtrack, computes the proposed S029 mix in memory with the governed Agent-008 mixer
(mix_motion_audio: AMBIENCE-only bed, tile-loop, 20 ms edge ramps), and measures the butt-join for click, discontinuity,
repeated transient and level jump.
"""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from agent008 import media  # noqa: E402
from agent008.hashing import sha256_file  # noqa: E402
from agent008.motion.compose import mix_motion_audio  # noqa: E402
from s029_assemble import TIMING, fetch_inputs, s029_spec  # noqa: E402

S028_FINAL_SHA = '1d5dfabde957aeabaec89659858eb7a28910de2266513a16b77734ea11a47cc0'


def dbfs(x):
    v = float(np.sqrt(np.mean(np.square(x)))) if len(x) else 0.0
    return round(20 * np.log10(v), 2) if v > 0 else -999.0


def peak(x):
    v = float(np.max(np.abs(x))) if len(x) else 0.0
    return round(20 * np.log10(v), 2) if v > 0 else -999.0


work, s028 = Path(sys.argv[1]), Path(sys.argv[2])
if sha256_file(s028) != S028_FINAL_SHA:
    sys.exit('STOP: S028 final sha differs')
paths, _ = fetch_inputs(work)
spec, spec_shot = s029_spec()
sr = spec.audio_sample_rate
a28 = media.load_audio(s028, sr, spec.audio_channels)
amb = media.load_audio(paths['AMB-BATHROOM-QUIET-v01'], sr, spec.audio_channels)
a29, cues, mix_peak = mix_motion_audio(spec_shot, {'AMB-BATHROOM-QUIET-v01': paths['AMB-BATHROOM-QUIET-v01']}, TIMING, spec)
joined = np.concatenate([a28, a29])
j = len(a28)
w20, w100, w500 = int(0.02 * sr), int(0.1 * sr), int(0.5 * sr)
d = np.abs(np.diff(joined, axis=0)).max(axis=1)
seam = d[j - 4:j + 4]
amb_steady = np.abs(np.diff(amb[w20:-w20], axis=0)).max()
# short-window envelope through the seam (10 ms hops)
hop = int(0.01 * sr)
env = [(round((k - j) / sr, 3), dbfs(joined[k:k + hop])) for k in range(j - 10 * hop, j + 10 * hop, hop)]
# repeated transient: S028 and S029 both start the ambience loop at sample 0; compare their first 0.5 s and look for onsets
amb_head = amb[:w500]
onset_ratio = float(np.max(np.abs(amb_head)) / (np.sqrt(np.mean(np.square(amb))) + 1e-12))
loop_points = [round(k * len(amb) / sr, 6) for k in range(1, int(np.ceil(len(a29) / len(amb))))]
loop_seams = [float(np.abs(a29[int(round(t * sr))] - a29[int(round(t * sr)) - 1]).max()) for t in loop_points]
r = {
    's028_final_sha256': S028_FINAL_SHA, 's028_audio_seconds': round(len(a28) / sr, 6),
    'ambience_sha256': sha256_file(paths['AMB-BATHROOM-QUIET-v01']), 'ambience_seconds': round(len(amb) / sr, 6),
    'ambience_rms_dbfs': dbfs(amb), 'ambience_peak_dbfs': peak(amb),
    's029_mix_seconds': round(len(a29) / sr, 6), 's029_mix_peak_dbfs': mix_peak, 's029_cues': cues,
    's029_loop_points_s': loop_points, 's029_loop_seam_max_sample_step': loop_seams,
    's028_tail_last_500ms_rms_dbfs': dbfs(a28[-w500:]), 's028_tail_last_100ms_rms_dbfs': dbfs(a28[-w100:]),
    's028_last_20ms_rms_dbfs': dbfs(a28[-w20:]), 's028_last_sample_abs': float(np.abs(a28[-1]).max()),
    's029_first_20ms_rms_dbfs': dbfs(a29[:w20]), 's029_first_sample_abs': float(np.abs(a29[0]).max()),
    's029_first_100ms_rms_dbfs': dbfs(a29[:w100]), 's029_first_500ms_rms_dbfs': dbfs(a29[:w500]),
    's029_steady_rms_dbfs': dbfs(a29[w500:-w500]),
    'seam_max_sample_step': float(seam.max()), 'ambience_steady_max_sample_step': float(amb_steady),
    'seam_envelope_10ms_dbfs': env, 'ambience_head_peak_to_rms_ratio': round(onset_ratio, 3),
}
r['level_jump_db_500ms_windows'] = round(r['s029_first_500ms_rms_dbfs'] - r['s028_tail_last_500ms_rms_dbfs'], 2)
r['checks'] = {
    'click_or_discontinuity': 'NONE' if r['seam_max_sample_step'] <= r['ambience_steady_max_sample_step'] else 'PRESENT',
    'level_jump_lt_1p5db': bool(abs(r['level_jump_db_500ms_windows']) < 1.5),
    'repeated_transient': 'NONE' if onset_ratio < 6.0 else 'POSSIBLE',
    'clip_free': bool(mix_peak <= -1.0),
}
r['result'] = 'CLEAN' if (r['checks']['click_or_discontinuity'] == 'NONE' and r['checks']['level_jump_lt_1p5db']
                          and r['checks']['repeated_transient'] == 'NONE' and r['checks']['clip_free']) else 'MATERIAL_DISCONTINUITY'
(work / 'S029_AMBIENCE_CONTINUITY.json').write_text(json.dumps(r, indent=1, default=str))
print(json.dumps({k: v for k, v in r.items() if k not in ('s029_cues',)}, indent=1, default=str))
