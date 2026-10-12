import subprocess, numpy as np, json, sys
mp4=sys.argv[1]; H,W=1080,1920; fs=H*W*3//2
p=subprocess.Popen(['ffmpeg','-v','error','-i',mp4,'-f','rawvideo','-pix_fmt','yuv420p','-'],stdout=subprocess.PIPE)
f0=prev=None; rows=[]
while True:
    b=p.stdout.read(fs)
    if len(b)<fs: break
    f=np.frombuffer(b,np.uint8).astype(np.int16)
    if f0 is None: f0=f
    d0=np.abs(f-f0); dc=np.abs(f-prev) if prev is not None else d0*0
    rows.append({'max_vs_f0':int(d0.max()),'mean_vs_f0':round(float(d0.mean()),5),'px_gt2_vs_f0':int((d0>2).sum()),'max_vs_prev':int(dc.max()),'mean_vs_prev':round(float(dc.mean()),5)})
    prev=f
p.wait()
pt=json.loads(subprocess.run(['ffprobe','-v','error','-select_streams','v','-show_frames','-show_entries','frame=pict_type','-of','json',mp4],capture_output=True).stdout)
r={'frames':len(rows),'gop':''.join(f['pict_type'] for f in pt['frames']),
 'identical_to_f0':sum(x['max_vs_f0']==0 for x in rows),
 'max_abs_vs_f0':max(x['max_vs_f0'] for x in rows),'max_mean_abs_vs_f0':max(x['mean_vs_f0'] for x in rows),
 'max_px_gt2_vs_f0':max(x['px_gt2_vs_f0'] for x in rows),'max_abs_consecutive':max(x['max_vs_prev'] for x in rows),
 'max_mean_abs_consecutive':max(x['mean_vs_prev'] for x in rows)}
print(json.dumps(r,indent=1))
