"""EP005 Batch 1: prove the G04 normalisation recipe on a synthetic raw frame (no provider, no production data).

Usage (repo root): python3 evidence/ep005/batch1_base_frames/b1_normalisation_proof.py <scratch dir>
normalisation_crop(w, h) = the largest exact 16:9 centred crop (w = 16k, h = 9k); G04 derive_frame then scales it to
1920x1080 (lanczos, bitexact). Proven: two runs byte-identical; the unchanged G04 refuses a REVIEW source.
"""
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from agent008.derive import derive_frame, write_png_rgb  # noqa: E402
from agent008.errors import FailClosed  # noqa: E402
from agent008.hashing import sha256_file  # noqa: E402

MAX_TRIM = 0.02  # more than 2% trimmed on either axis = unexpected aspect: STOP for a human decision


def normalisation_crop(w, h):
    k = min(w // 16, h // 9)
    cw, ch = 16 * k, 9 * k
    if (w - cw) > MAX_TRIM * w or (h - ch) > MAX_TRIM * h:
        raise FailClosed('RAW_ASPECT_UNEXPECTED', f'{w}x{h} needs {w - cw}x{h - ch} px trimmed')
    return {'x': (w - cw) // 2, 'y': (h - ch) // 2, 'w': cw, 'h': ch}


def main(scratch):
    scratch = Path(scratch)
    raw = scratch / 'SYNTHETIC_RAW_2688x1520.png'
    rng = np.random.default_rng(20261020)
    write_png_rgb(rng.integers(0, 256, (1520, 2688, 3), dtype=np.uint8), raw)
    crop, scale = normalisation_crop(2688, 1520), {'w': 1920, 'h': 1080}
    src = {'asset_id': 'SYNTHETIC-RAW', 'registry_id': None, 'classification': 'synthetic', 'path': str(raw),
           'expected_sha256': sha256_file(raw), 'expected_frames': 1, 'expected_width': 2688, 'expected_height': 1520}
    result = {'raw_sha256': src['expected_sha256'], 'crop': crop, 'scale': scale}
    try:
        derive_frame({**src, 'registry_status': 'REVIEW'}, 0, 'SYN', scratch / 'review_state', crop, scale)
        result['review_source'] = 'ACCEPTED'
    except FailClosed as e:
        result['review_source'] = f'REFUSED {e.code}'
    runs = [derive_frame({**src, 'registry_status': 'LOCKED'}, 0, 'SYN', scratch / f'run{i}', crop, scale)['output']
            for i in (1, 2)]
    result |= {'run1': runs[0], 'run2': runs[1], 'byte_identical': runs[0]['sha256'] == runs[1]['sha256'],
               'source_unchanged': sha256_file(raw) == src['expected_sha256']}
    for w, h in ((2688, 1520), (2560, 1440), (1920, 1080), (2752, 1536)):
        result.setdefault('crop_table', {})[f'{w}x{h}'] = normalisation_crop(w, h)
    try:
        normalisation_crop(2048, 2048)
    except FailClosed as e:
        result['crop_table']['2048x2048'] = f'STOP {e.code}'
    print(json.dumps(result, indent=1))


if __name__ == '__main__':
    main(sys.argv[1])
