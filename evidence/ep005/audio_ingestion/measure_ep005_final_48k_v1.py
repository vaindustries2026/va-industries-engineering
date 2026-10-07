#!/usr/bin/env python3
"""Measure approved 44.1 kHz masters vs final 48 kHz production masters. Usage: measure_ep005_final_48k_v1.py <masters dir> <final dir> <json out>"""
import subprocess, sys, math, re, json, hashlib
import numpy as np
MAS, FIN, JSON = sys.argv[1:4]
db = lambda x: 20 * math.log10(max(x, 1e-12))
def probe(f):
    return json.loads(subprocess.run(['ffprobe','-v','error','-select_streams','a:0','-show_entries','stream=codec_name,sample_rate,channels,bits_per_raw_sample,duration_ts','-of','json',f],capture_output=True).stdout)['streams'][0]
def load(f, sr):
    raw = subprocess.run(['ffmpeg','-v','error','-i',f,'-f','f32le','-acodec','pcm_f32le','-ac','2','-'],capture_output=True,check=True).stdout
    return np.frombuffer(raw, dtype='<f4').reshape(-1,2).astype(np.float64)
def ebur(f):
    s = subprocess.run(['ffmpeg','-nostdin','-hide_banner','-i',f,'-af','ebur128=peak=true','-f','null','-'],capture_output=True,text=True).stderr.split('Summary:')[-1]
    return float(re.search(r'I:\s*(-?[\d.]+)',s).group(1)), float(re.search(r'Peak:\s*(-?[\d.]+)',s).group(1))
def metrics(f):
    p = probe(f); sr = int(p['sample_rate']); x = load(f, sr); m = x.mean(axis=1); n = len(x)
    S = np.fft.rfft(m); fr = np.fft.rfftfreq(n, 1/sr)
    band = lambda lo, hi: db(np.sqrt((np.fft.irfft(np.where((fr>=lo)&(fr<hi),S,0),n)**2).mean()))
    I, TP = ebur(f)
    return {'codec':p['codec_name'],'sample_rate':sr,'channels':p['channels'],'bits':int(p['bits_per_raw_sample']),'samples_per_channel':n,'duration_s':round(n/sr,5),
            'sample_peak_dBFS':round(db(np.abs(x).max()),2),'true_peak_dBTP':TP,'rms_dBFS':round(db(np.sqrt((x**2).mean())),1),'integrated_LUFS':I,
            'rms_below_60Hz_dBFS':round(band(0,60),1),'rms_100Hz_to_16kHz_dBFS':round(band(100,16000),1),'rms_above_16kHz_dBFS':round(band(16000,sr/2),1),
            'first_sample_abs':float(f'{np.abs(x[0]).max():.2e}'),'last_sample_abs':float(f'{np.abs(x[-1]).max():.2e}')}
def seam(f):
    p = probe(f); sr = int(p['sample_rate']); m = load(f, sr).mean(axis=1); n = len(m)
    S = np.fft.rfft(m); fr = np.fft.rfftfreq(n, 1/sr); S[fr<100] = 0; hi = np.fft.irfft(S, n)
    d = np.abs(np.diff(hi)); wrap = abs(hi[0]-hi[-1]); w = int(0.2*sr)
    lvl = lambda s: db(np.sqrt((s**2).mean()))
    spread = [lvl(hi[i:i+w]) for i in range(0, n-w, w)]
    return {'wrap_step_percentile_of_adjacent_steps': round(100*(d<wrap).mean(),2), 'last_200ms_dBFS': round(lvl(hi[-w:]),1), 'first_200ms_dBFS': round(lvl(hi[:w]),1),
            'file_200ms_range_dBFS': [round(min(spread),1), round(max(spread),1)]}
items = [('AMB-BATHROOM-QUIET-v01','AMB-BATHROOM-QUIET-v01_MASTER_REVIEW.wav','AMB-BATHROOM-QUIET-v01.wav'),
         ('FOLEY-CLOTH-SOFT-v01','FOLEY-CLOTH-SOFT-v01_MASTER_REVIEW.wav','FOLEY-CLOTH-SOFT-v01.wav'),
         ('SFX-COMPLETION-POP-v01','SFX-COMPLETION-POP-v01_MASTER_REVIEW.wav','SFX-COMPLETION-POP-v01.wav')]
res = []
for pid, a, b in items:
    ap, bp = f'{MAS}/{a}', f'{FIN}/{b}'; d = open(bp,'rb').read()
    r = {'production_id':pid,'approved_master_file':a,'approved_master_sha256':hashlib.sha256(open(ap,'rb').read()).hexdigest(),
         'final_file':b,'final_bytes':len(d),'final_sha256':hashlib.sha256(d).hexdigest(),'before_44k1_master':metrics(ap),'after_48k_final':metrics(bp)}
    if pid.startswith('AMB'): r['loop_seam_before']=seam(ap); r['loop_seam_after']=seam(bp)
    res.append(r)
json.dump(res, open(JSON,'w'), indent=1)
for r in res:
    print('==', r['production_id'], '| final bytes', r['final_bytes'], '| sha256', r['final_sha256'])
    for k in r['before_44k1_master']: print(f"   {k:26s} before {str(r['before_44k1_master'][k]):>12s}   after {str(r['after_48k_final'][k]):>12s}")
    if 'loop_seam_after' in r: print('   seam before:', r['loop_seam_before'], '\n   seam after :', r['loop_seam_after'])
