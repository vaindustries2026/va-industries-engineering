"""S029 base frame: Agent-008 G04 deterministic extraction of approved S028 raw frame 119, run twice (as executed 2026-10-12).

Usage (repo root): python3 evidence/agent008/phase1/s029/s029_derive_base_frame.py <work_dir>
<work_dir>/src/raw.mp4 must be MOTION-EP005-S028-SEEDANCE20-CAND-v01 read from production storage (GET) and verified
341683c4...9b58 before use. Writes <work_dir>/runA, <work_dir>/runB and <work_dir>/derive_result.json. No provider calls.
"""
import hashlib
import json
import os
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from agent008.derive import derive_frame, extract_frame_rgb  # noqa: E402
from agent008.hashing import sha256_bytes, sha256_file  # noqa: E402

d = Path(sys.argv[1]); src = d / 'src' / 'raw.mp4'
st0 = (sha256_file(src), os.stat(src).st_size, os.stat(src).st_mtime_ns)
source = {'asset_id': 'MOTION-EP005-S028-SEEDANCE20-CAND-v01', 'registry_id': '2e13b73d-a328-4cb9-b366-8d3cba5f350e',
          'classification': 'SHOT_MOTION/RAW_MOTION_SOURCE', 'registry_status': 'APPROVED', 'path': str(src),
          'expected_sha256': '341683c40de8d71ebed564b7739f9b338add2f954d00e347e0561c7fbe7a9b58', 'expected_frames': 121,
          'expected_width': 1920, 'expected_height': 1080}
runs = [derive_frame(source, 119, 'S029', d / f'run{i}') for i in 'AB']
st1 = (sha256_file(src), os.stat(src).st_size, os.stat(src).st_mtime_ns)
a, b = (d / f'run{i}' / 'S029_DERIVED_FRAME_CANDIDATE.png' for i in 'AB')
pil = hashlib.sha256(Image.open(a).convert('RGB').tobytes()).hexdigest()
src119 = sha256_bytes(extract_frame_rgb(src, 119, 1920, 1080).tobytes())
res = {'png_sha256': [runs[0]['output']['sha256'], runs[1]['output']['sha256']], 'bytes': runs[0]['output']['bytes'],
       'dims': [runs[0]['output']['width'], runs[0]['output']['height']], 'byte_identical': a.read_bytes() == b.read_bytes(),
       'canonical_rgb_sha256_PIL': pil, 'source_frame119_rgb_sha256': src119,
       'selected_frame_rgb_sha256': runs[0]['selected_frame_rgb_sha256'],
       'pixels_equal_source_frame119': pil == src119 == runs[0]['selected_frame_rgb_sha256'] == runs[0]['output']['rgb24_sha256'],
       'crop': runs[0]['recipe']['crop'], 'scale': runs[0]['recipe']['scale'], 'source_unchanged': st0 == st1, 'source_sha': st1[0],
       'core_sha_equal': runs[0]['deterministic_core_sha256'] == runs[1]['deterministic_core_sha256'],
       'frame_timestamp_s': runs[0]['frame_timestamp_s']}
json.dump(res, open(d / 'derive_result.json', 'w'), indent=1); print(json.dumps(res, indent=1))
