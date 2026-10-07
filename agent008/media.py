"""ffmpeg / ffprobe wrappers. Every call is local, offline and deterministic for a fixed ffmpeg build."""
import json
import subprocess

import numpy as np

from .errors import FailClosed

FFMPEG = 'ffmpeg'
FFPROBE = 'ffprobe'
SCALE_FLAGS = 'lanczos+accurate_rnd+full_chroma_int+bitexact'


def _run(cmd, input_bytes=None):
    p = subprocess.run(cmd, input=input_bytes, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode != 0:
        raise FailClosed('FFMPEG_FAILED', ' '.join(cmd[:8]) + ' ... ' + p.stderr.decode(errors='replace')[-600:])
    return p.stdout


def toolchain():
    v = _run([FFMPEG, '-hide_banner', '-version']).decode().splitlines()[0]
    return {'ffmpeg': v, 'numpy': np.__version__}


def probe(path):
    return json.loads(_run([FFPROBE, '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(path)]))


def image_size(path):
    s = [st for st in probe(path)['streams'] if st['codec_type'] == 'video'][0]
    return int(s['width']), int(s['height'])


def load_rgba(path):
    """Decode an image file to uint8 RGBA (H, W, 4)."""
    w, h = image_size(path)
    raw = _run([FFMPEG, '-v', 'error', '-i', str(path), '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-'])
    if len(raw) != w * h * 4:
        raise FailClosed('IMAGE_DECODE_SIZE', str(path))
    return np.frombuffer(raw, dtype=np.uint8).reshape(h, w, 4).copy()


def scale_rgba(img, w, h):
    """Lanczos resize of an RGBA array through ffmpeg (premultiplied-safe enough for keyed layers)."""
    ih, iw = img.shape[:2]
    if (iw, ih) == (w, h):
        return img.copy()
    raw = _run([FFMPEG, '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', f'{iw}x{ih}', '-i', '-',
                '-vf', f'scale={w}:{h}:flags={SCALE_FLAGS}', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-'],
               img.tobytes())
    return np.frombuffer(raw, dtype=np.uint8).reshape(h, w, 4).copy()


def gblur_rgba(img, sigma):
    ih, iw = img.shape[:2]
    raw = _run([FFMPEG, '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', f'{iw}x{ih}', '-i', '-',
                '-vf', f'gblur=sigma={sigma}:steps=3', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-'], img.tobytes())
    return np.frombuffer(raw, dtype=np.uint8).reshape(ih, iw, 4).copy()


def text_layer(text, font_file, font_size, box_w, box_h, fg='white', bg_rgba=(0, 0, 0, 150)):
    """Render a text banner to RGBA with libfreetype (deterministic for a fixed font file)."""
    r, g, b, a = bg_rgba
    esc = text.replace('\\', '\\\\').replace(':', '\\:').replace("'", "\\'")
    vf = (f"drawtext=fontfile={font_file}:text='{esc}':fontsize={font_size}:fontcolor={fg}:"
          f"x=(w-text_w)/2:y=(h-text_h)/2")
    raw = _run([FFMPEG, '-v', 'error', '-f', 'lavfi', '-i',
                f'color=c=0x{r:02x}{g:02x}{b:02x}@{a / 255:.4f}:s={box_w}x{box_h},format=rgba',
                '-vf', vf, '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-'])
    return np.frombuffer(raw, dtype=np.uint8).reshape(box_h, box_w, 4).copy()


def load_audio(path, sample_rate, channels):
    """Decode the first audio stream to float64 (N, C) at the working rate."""
    raw = _run([FFMPEG, '-v', 'error', '-i', str(path), '-map', '0:a:0', '-f', 'f64le', '-acodec', 'pcm_f64le',
                '-ac', str(channels), '-ar', str(sample_rate), '-af', 'aresample=resampler=soxr:precision=28', '-'])
    return np.frombuffer(raw, dtype='<f8').reshape(-1, channels).copy()


def write_wav24(samples, sample_rate, path):
    n, c = samples.shape
    _run([FFMPEG, '-v', 'error', '-y', '-f', 'f64le', '-ar', str(sample_rate), '-ac', str(c), '-i', '-',
          '-c:a', 'pcm_s24le', '-fflags', '+bitexact', '-flags:a', '+bitexact', '-map_metadata', '-1', str(path)],
         samples.astype('<f8').tobytes())


def encode_review(frames_iter, n_frames, spec, wav_path, out_path):
    """Encode RGB24 frames + WAV to the review MP4 (H.264 yuv420p + AAC), bitexact flags, single thread."""
    cmd = [FFMPEG, '-v', 'error', '-y',
           '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{spec.width}x{spec.height}', '-r', str(spec.fps), '-i', '-',
           '-i', str(wav_path),
           '-map', '0:v:0', '-map', '1:a:0',
           '-vf', f'scale=out_color_matrix=bt709:out_range=tv:flags={SCALE_FLAGS},format={spec.pixel_format}',
           '-c:v', spec.video_codec, '-preset', spec.x264_preset, '-crf', str(spec.x264_crf), '-threads', '1',
           '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709',
           '-c:a', spec.review_audio_codec, '-b:a', spec.review_audio_bitrate, '-ar', str(spec.audio_sample_rate),
           '-frames:v', str(n_frames),
           '-fflags', '+bitexact', '-flags:v', '+bitexact', '-flags:a', '+bitexact', '-map_metadata', '-1',
           '-movflags', '+faststart', str(out_path)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        for fr in frames_iter:
            p.stdin.write(fr.tobytes())
        p.stdin.close()
    except BrokenPipeError:
        pass
    err = p.stderr.read().decode(errors='replace')
    p.stderr.close()
    if p.wait() != 0:
        raise FailClosed('ENCODE_FAILED', err[-600:])
    return cmd


def decode_frames_rgb(path, w, h):
    raw = _run([FFMPEG, '-v', 'error', '-i', str(path), '-map', '0:v:0', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'])
    return np.frombuffer(raw, dtype=np.uint8).reshape(-1, h, w, 3)
