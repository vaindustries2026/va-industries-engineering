"""Prove S027 is unchanged by G09: rebuild ONLY the S027 audio mix (no video, no render) from the approved,
already-downloaded inputs and compare with the approved mix WAV SHA. Offline; no network; no provider.

Usage (repo root): python3 evidence/agent008/batch0d/verify_s027_g09_unchanged.py <dir with the 4 approved S027 input files> <out_dir>
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from agent008 import media  # noqa: E402
from agent008.config import load_output_spec  # noqa: E402
from agent008.dialogue_timing import govern_dialogue_timing  # noqa: E402
from agent008.hashing import sha256_file, verify_file  # noqa: E402
from agent008.inputs import load_hash_pins, load_snapshot, validate_readiness  # noqa: E402
from agent008.motion.compose import mix_motion_audio, resolve_dialogue  # noqa: E402
from agent008.resolve import Resolver  # noqa: E402
from agent008.spec import build_shot_spec  # noqa: E402

APPROVED_MIX_WAV = 'c67da3f3d7cf0a2aeca0e9d8736db64c09aa2b819b9a3a607338bf1893e2a863'
FILES = {'DLG-EP005-S027-L1-MIKKO-v01': ('DLG-EP005-S027-L1-MIKKO-v01.mp3', '81a0b038e0e81114f88079dd3f42aeafbbe47ba39cb8e8a706933e6ba531da50'),
         'AMB-BATHROOM-QUIET-v01': ('AMB-BATHROOM-QUIET-v01.wav', 'ea28fad468e353b99d48070d12853620f08e8b05c8d912706122d31176544d2f'),
         'SFX-WIN-SPARKLE-CHORD': ('SFX-WIN-SPARKLE-CHORD-v01.mp3.mp3', '84e0d57cf17a170af66dfb31ade4d647f6077cbbe13eb2fd87be6ae6f0c5bd9b')}
TIMING = {   # identical to evidence/agent008/phase1/s027_v2/stage4_assemble_s027.py
    'beds': {'AMB-BATHROOM-QUIET-v01': {'gain_db': 0.0}},
    'named': {'SFX-WIN-SPARKLE-CHORD': {'start_seconds': 46 / 24, 'gain_db': -10.0, 'fade_out_seconds': 1.0,
                                        'fade_complete_by_seconds': 5.0}},
    'dialogue': [{'shot_id': 'S027', 'speaker': 'Mikko', 'text': 'We did it! I feel fresh.',
                  'audio_asset_id': 'DLG-EP005-S027-L1-MIKKO-v01', 'expected_sha256': FILES['DLG-EP005-S027-L1-MIKKO-v01'][1],
                  'registry_status': 'APPROVED', 'start_seconds': 0.5, 'gain_db': 0.0}]}

src, out = Path(sys.argv[1]), Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=True)
paths = {aid: Path(verify_file(src / f, sha, aid) and src / f) for aid, (f, sha) in FILES.items()}
spec = load_output_spec()
snap = load_snapshot(ROOT / 'agent008/inputs/ep005_motion_s027_input_snapshot.json')
rd = validate_readiness(snap, 'edc4ad58-3e5d-4ac2-9c74-c9af03af363f', '45cc7493-80b4-4e8d-b71d-fbd7fd3656ed', 'A006-1791346204213')
shot = build_shot_spec(snap, Resolver(rd, snap['asset_registry'], load_hash_pins(ROOT / 'agent008/inputs/hash_pins.json')),
                       'S027', spec, motion_phase=True)
dlg = resolve_dialogue(shot, paths, TIMING)
report = govern_dialogue_timing(shot, dlg, paths, TIMING, spec)
audio, cues, peak = mix_motion_audio(shot, paths, TIMING, spec, dlg)
wav = out / 'S027_MOTION_MIX_G09_CHECK.wav'
media.write_wav24(audio, spec.audio_sample_rate, wav)
res = {'mix_wav_sha256': sha256_file(wav), 'approved_mix_wav_sha256': APPROVED_MIX_WAV,
       'identical': sha256_file(wav) == APPROVED_MIX_WAV, 'peak_dbfs': peak, 'g09_report': report,
       'video_rendered': False, 'provider_calls': 0}
print(json.dumps(res, indent=1))
sys.exit(0 if res['identical'] else 1)
