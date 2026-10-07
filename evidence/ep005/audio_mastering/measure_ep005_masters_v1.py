#!/usr/bin/env python3
"""Measure source originals vs mastered review derivatives (before/after). Usage: measure_ep005_masters_v1.py <src dir> <out dir> <json out>"""
import subprocess, sys, math, re, json, hashlib, os
import numpy as np
SRC, OUT, JSON = sys.argv[1:4]
db = lambda x: 20 * math.log10(max(x, 1e-12))
def load(f):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', f, '-f', 'f32le', '-acodec', 'pcm_f32le', '-ac', '2', '-'], capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype='<f4').reshape(-1, 2).astype(np.float64)
def probe(f):
    p = json.loads(subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'a:0', '-show_entries', 'stream=codec_name,sample_rate,channels,duration_ts,bits_per_sample', '-of', 'json', f], capture_output=True).stdout)['streams'][0]
    return p
def ebur(f):
    s = subprocess.run(['ffmpeg', '-nostdin', '-hide_banner', '-i', f, '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr.split('Summary:')[-1]
    g = lambda p: float(re.search(p + r'\s*(-?[\d.]+)', s).group(1))
    return g(r'I:'), g(r'Peak:')
def metrics(f, sr):
    x = load(f); m = x.mean(axis=1); n = len(x); p = probe(f)
    S = np.fft.rfft(m); fr = np.fft.rfftfreq(n, 1 / sr)
    band = lambda lo, hi: db(np.sqrt((np.fft.irfft(np.where((fr >= lo) & (fr < hi), S, 0), n) ** 2).mean()))
    I, TP = ebur(f)
    return {'codec': p['codec_name'], 'sample_rate': int(p['sample_rate']), 'channels': p['channels'], 'samples_per_channel': n, 'duration_s': round(n / sr, 4),
            'sample_peak_dBFS': round(db(np.abs(x).max()), 2), 'true_peak_dBTP': TP, 'rms_dBFS': round(db(np.sqrt((x ** 2).mean())), 1),
            'integrated_LUFS': I, 'rms_below_60Hz_dBFS': round(band(0, 60), 1), 'rms_above_100Hz_dBFS': round(band(100, 22050), 1),
            'mean_dc': float(f'{m.mean():.2e}'), 'first_sample_abs': float(f'{np.abs(x[0]).max():.2e}'), 'last_sample_abs': float(f'{np.abs(x[-1]).max():.2e}')}
items = [('AMB-BATHROOM-QUIET-v01', 'AMB-C.mp3', 'AMB-BATHROOM-QUIET-v01_MASTER_REVIEW.wav', 'Oe9nvpw0JuR3zKjs6Vib'),
         ('FOLEY-CLOTH-SOFT-v01', 'CLOTH-C.mp3', 'FOLEY-CLOTH-SOFT-v01_MASTER_REVIEW.wav', 'eiW0bnQ9IsbkD6qwPVuQ'),
         ('SFX-COMPLETION-POP-v01', 'POP-A.mp3', 'SFX-COMPLETION-POP-v01_MASTER_REVIEW.wav', '75tahAZ0wFnzcjSADUkx')]
res = []
for pid, s, o, gen in items:
    sp, op = f'{SRC}/{s}', f'{OUT}/{o}'
    d = open(op, 'rb').read()
    res.append({'production_id': pid, 'source_generation_id': gen, 'source_file': s, 'source_sha256': hashlib.sha256(open(sp, 'rb').read()).hexdigest(),
                'master_review_file': o, 'master_bytes': len(d), 'master_sha256': hashlib.sha256(d).hexdigest(),
                'before': metrics(sp, 44100), 'after': metrics(op, 44100)})
json.dump(res, open(JSON, 'w'), indent=1)
for r in res:
    print('==', r['production_id'], '| master bytes', r['master_bytes'], '| sha256', r['master_sha256'])
    for k in r['before']:
        print(f"   {k:24s} before {str(r['before'][k]):>14s}   after {str(r['after'][k]):>14s}")
