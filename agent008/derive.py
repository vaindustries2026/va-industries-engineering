"""G04: deterministic derived frame from an approved motion source (zero spend, no provider).

Takes exactly one decoded frame, by index, from a hash-verified source video and writes it as a lossless
PNG, with an optional exact-pixel crop and a deterministic scale. The source is never written. The output
is a REVIEW candidate only: it becomes a shot asset (proposed SHOT_FRAME / DERIVED_FRAME) only after human
approval of its exact SHA-256 and a separately authorised registration. Nothing here registers or uploads.
"""
import json
from pathlib import Path

import numpy as np

from . import AGENT_NAME, media
from .errors import FailClosed
from .hashing import canonical_sha256, sha256_bytes, sha256_file, verify_file

AGENT_VERSION_G04 = 'agent008-v0.3-derived-frame'
SOURCE_APPROVED_STATES = ('APPROVED', 'LOCKED')
REQUIRED_PROVENANCE = ('agent_version', 'status', 'target_shot_id', 'source', 'frame_index', 'recipe', 'output',
                       'proposed_registry', 'human_approval', 'safety')


def count_frames(path):
    """Exact decoded video frame count (decodes the stream; does not trust container metadata)."""
    pr = json.loads(media._run([media.FFPROBE, '-v', 'error', '-count_frames', '-select_streams', 'v:0',
                                '-show_entries', 'stream=nb_read_frames,width,height,r_frame_rate',
                                '-of', 'json', str(path)]))
    s = pr['streams'][0]
    return int(s['nb_read_frames']), int(s['width']), int(s['height']), s['r_frame_rate']


def extract_frame_rgb(path, frame_index, width, height):
    """Decoded frame number `frame_index` (0-based, decode order of the first video stream) as uint8 RGB."""
    raw = media._run([media.FFMPEG, '-v', 'error', '-i', str(path), '-map', '0:v:0',
                      '-vf', f'select=eq(n\\,{frame_index}),format=rgb24', '-fps_mode', 'passthrough',
                      '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'])
    if len(raw) != width * height * 3:
        raise FailClosed('FRAME_EXTRACT_FAILED', f'frame {frame_index}: {len(raw)} bytes')
    return np.frombuffer(raw, dtype=np.uint8).reshape(height, width, 3).copy()


def _scale_rgb(img, w, h):
    ih, iw = img.shape[:2]
    raw = media._run([media.FFMPEG, '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{iw}x{ih}', '-i', '-',
                      '-vf', f'scale={w}:{h}:flags={media.SCALE_FLAGS}', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                     img.tobytes())
    return np.frombuffer(raw, dtype=np.uint8).reshape(h, w, 3).copy()


def write_png_rgb(img, path):
    h, w = img.shape[:2]
    media._run([media.FFMPEG, '-v', 'error', '-n', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{w}x{h}', '-i', '-',
                '-frames:v', '1', '-c:v', 'png', '-pix_fmt', 'rgb24', '-fflags', '+bitexact', '-flags:v', '+bitexact',
                '-map_metadata', '-1', str(path)], img.tobytes())


def decode_png_rgb(path):
    w, h = media.image_size(path)
    raw = media._run([media.FFMPEG, '-v', 'error', '-i', str(path), '-frames:v', '1', '-f', 'rawvideo',
                      '-pix_fmt', 'rgb24', '-'])
    return np.frombuffer(raw, dtype=np.uint8).reshape(h, w, 3)


def derive_frame(source, frame_index, target_shot_id, out_dir, crop=None, scale=None, expected_frame_rgb_sha256=None):
    """Derive one REVIEW frame. Fail closed on any identity, index or geometry problem.

    source: {asset_id, registry_id, classification, registry_status, path, expected_sha256,
             expected_frames?, expected_width?, expected_height?}
    crop:   {x, y, w, h} in source pixels (exact array slice), applied before scale.
    scale:  {w, h} deterministic resample (SCALE_FLAGS); aspect must match the (cropped) frame exactly.
    expected_frame_rgb_sha256: optional re-derivation pin; the selected frame's raw RGB must match it.
    """
    out_dir = Path(out_dir)
    src = Path(source['path'])
    if source.get('registry_status') not in SOURCE_APPROVED_STATES:
        raise FailClosed('DERIVE_SOURCE_NOT_APPROVED', f"{source.get('asset_id')}: {source.get('registry_status')}")
    if not source.get('expected_sha256'):
        raise FailClosed('NO_EXPECTED_HASH', str(source.get('asset_id')))
    src_sha = verify_file(src, source['expected_sha256'], f"derive source {source.get('asset_id')}")
    if not isinstance(frame_index, int) or isinstance(frame_index, bool) or frame_index < 0:
        raise FailClosed('FRAME_INDEX_INVALID', repr(frame_index))
    n, w, h, rate = count_frames(src)
    for key, actual in (('expected_frames', n), ('expected_width', w), ('expected_height', h)):
        if source.get(key) is not None and source[key] != actual:
            raise FailClosed('DERIVE_SOURCE_GEOMETRY_MISMATCH', f'{key}: expected {source[key]}, got {actual}')
    if frame_index >= n:
        raise FailClosed('FRAME_INDEX_OUT_OF_RANGE', f'index {frame_index}, source has {n} frames (0..{n - 1})')

    frame = extract_frame_rgb(src, frame_index, w, h)
    frame_sha = sha256_bytes(frame.tobytes())
    if expected_frame_rgb_sha256 is not None and frame_sha != expected_frame_rgb_sha256:
        raise FailClosed('DERIVED_FRAME_MISMATCH', f'frame {frame_index}: expected {expected_frame_rgb_sha256}, got {frame_sha}')
    img = frame
    if crop:
        x, y, cw, ch = (int(crop[k]) for k in ('x', 'y', 'w', 'h'))
        if x < 0 or y < 0 or cw <= 0 or ch <= 0 or x + cw > w or y + ch > h:
            raise FailClosed('CROP_OUT_OF_BOUNDS', f'{crop} on {w}x{h}')
        img = img[y:y + ch, x:x + cw].copy()
    if scale:
        sw, sh = int(scale['w']), int(scale['h'])
        ih, iw = img.shape[:2]
        if sw * ih != sh * iw:
            raise FailClosed('SCALE_ASPECT_MISMATCH', f'{iw}x{ih} -> {sw}x{sh}')
        img = _scale_rgb(img, sw, sh)

    out_dir.mkdir(parents=True, exist_ok=True)
    png = out_dir / f'{target_shot_id}_DERIVED_FRAME_CANDIDATE.png'
    if png.exists():
        raise FailClosed('OUTPUT_EXISTS', str(png))
    if png.resolve() == src.resolve():
        raise FailClosed('OUTPUT_WOULD_OVERWRITE_SOURCE', str(png))
    write_png_rgb(img, png)
    out_rgb_sha = sha256_bytes(img.tobytes())
    if sha256_bytes(decode_png_rgb(png).tobytes()) != out_rgb_sha:
        raise FailClosed('DERIVED_FRAME_NOT_LOSSLESS', png.name)
    if sha256_file(src) != src_sha:
        raise FailClosed('SOURCE_MUTATED', str(src))

    prov = {
        'agent': AGENT_NAME, 'agent_version': AGENT_VERSION_G04, 'stage': 'G04 derived frame', 'status': 'REVIEW',
        'target_shot_id': target_shot_id,
        'source': {k: source.get(k) for k in ('asset_id', 'registry_id', 'classification', 'registry_status')}
                  | {'verified_sha256': src_sha, 'decoded_frames': n, 'width': w, 'height': h, 'r_frame_rate': rate,
                     'sha256_after_derive': src_sha},
        'frame_index': frame_index, 'frame_timestamp_s': _frame_time(frame_index, rate),
        'selected_frame_rgb_sha256': frame_sha,
        'recipe': {'select': f'select=eq(n\\,{frame_index}) on decoded frames of stream 0:v:0, rgb24',
                   'crop': crop, 'scale': scale, 'scale_flags': media.SCALE_FLAGS if scale else None,
                   'png': 'ffmpeg png encoder, rgb24, bitexact, no metadata'},
        'output': {'file': png.name, 'sha256': sha256_file(png), 'bytes': png.stat().st_size,
                   'width': int(img.shape[1]), 'height': int(img.shape[0]), 'rgb24_sha256': out_rgb_sha,
                   'lossless_roundtrip': True},
        'proposed_registry': {'asset_type': 'SHOT_FRAME', 'asset_subtype': 'DERIVED_FRAME', 'shot_id': target_shot_id,
                              'registered': False, 'requires': 'human approval of output.sha256, then a separately '
                                                              'authorised storage write + registration'},
        'human_approval': {'required': True, 'approved': False, 'decisions': ['APPROVE', 'REJECT'],
                           'approve_by': 'exact output png sha256'},
        'safety': {'provider_calls': 0, 'source_mutated': False, 'auto_approved': False, 'registered': False},
        'toolchain': media.toolchain(),
    }
    missing = [k for k in REQUIRED_PROVENANCE if k not in prov]
    if missing:
        raise FailClosed('PROVENANCE_INCOMPLETE', ','.join(missing))
    prov['deterministic_core_sha256'] = canonical_sha256({k: v for k, v in prov.items() if k != 'toolchain'})
    (out_dir / f'{target_shot_id}_DERIVED_FRAME_PROVENANCE.json').write_text(
        json.dumps(prov, indent=1, sort_keys=True) + '\n')
    return prov


def _frame_time(i, rate):
    num, den = (int(x) for x in rate.split('/'))
    return round(i * den / num, 6)
