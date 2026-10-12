import hashlib, json, subprocess, sys
import numpy as np
mp4, wav, raw, amb, frame = sys.argv[1:6]
def sh(p): return hashlib.sha256(open(p,'rb').read()).hexdigest()
pr = json.loads(subprocess.run(['ffprobe','-v','error','-count_frames','-show_streams','-show_format','-of','json',mp4],capture_output=True,check=True).stdout)
v=[s for s in pr['streams'] if s['codec_type']=='video']; a=[s for s in pr['streams'] if s['codec_type']=='audio']
W,H=1920,1080
buf=subprocess.run(['ffmpeg','-v','error','-i',mp4,'-map','0:v:0','-f','rawvideo','-pix_fmt','rgb24','-'],capture_output=True,check=True).stdout
fr=np.frombuffer(buf,np.uint8).reshape(-1,H,W,3)
hashes={hashlib.sha256(f.tobytes()).hexdigest() for f in fr}
means=fr.reshape(len(fr),-1).mean(axis=1)
au=np.frombuffer(subprocess.run(['ffmpeg','-v','error','-i',mp4,'-map','0:a:0','-f','f64le','-ac','2','-ar','48000','-'],capture_output=True,check=True).stdout,'<f8').reshape(-1,2)
mx=np.frombuffer(subprocess.run(['ffmpeg','-v','error','-i',wav,'-f','f64le','-'],capture_output=True,check=True).stdout,'<f8').reshape(-1,2)
db=lambda x:round(float(20*np.log10(max(x,1e-12))),2)
win=int(0.05*48000); rms=[np.sqrt(np.mean(au[i:i+win]**2)) for i in range(0,len(au)-win,win)]
# source frame vs decoded frame 0 (yuv420p round trip): mean abs error
src=np.frombuffer(subprocess.run(['ffmpeg','-v','error','-i',frame,'-f','rawvideo','-pix_fmt','rgb24','-'],capture_output=True,check=True).stdout,np.uint8).reshape(H,W,3)
mae=float(np.abs(fr[0].astype(int)-src.astype(int)).mean())
r={'mp4_sha256':sh(mp4),'bytes':int(pr['format']['size']),'format_duration_s':float(pr['format']['duration']),
 'video':{'codec':v[0]['codec_name'],'profile':v[0].get('profile'),'pix_fmt':v[0]['pix_fmt'],'res':f"{v[0]['width']}x{v[0]['height']}",'r_frame_rate':v[0]['r_frame_rate'],
   'nb_frames':int(v[0]['nb_frames']),'nb_read_frames':int(v[0]['nb_read_frames']),'duration_s':float(v[0]['duration'])},
 'audio':{'streams':len(a),'codec':a[0]['codec_name'],'sample_rate':int(a[0]['sample_rate']),'channels':a[0]['channels'],'duration_s':float(a[0]['duration'])},
 'decoded_frames':len(fr),'distinct_decoded_frame_hashes':len(hashes),'min_frame_mean_luma_rgb':round(float(means.min()),2),'black_frames':int((means<16).sum()),
 'held_frame_vs_source_png_mean_abs_error_8bit':round(mae,3),
 'audio_peak_dbfs':db(np.abs(au).max()),'audio_rms_dbfs':db(np.sqrt(np.mean(au**2))),'mix_wav_peak_dbfs':db(np.abs(mx).max()),
 'audio_min_50ms_rms_dbfs_excl_edges':db(min(rms[1:-1])),'audio_max_50ms_rms_dbfs':db(max(rms)),
 'clipped_samples':int((np.abs(au)>=0.999).sum()),
 'sources_after':{'s028_raw':sh(raw),'ambience':sh(amb),'s029_frame':sh(frame)}}
r['checks']={'res':r['video']['res']=='1920x1080','fps':r['video']['r_frame_rate']=='24/1','frames_144':r['video']['nb_read_frames']==144==r['decoded_frames'],
 'duration_6s':abs(r['video']['duration_s']-6.0)<1e-6,'h264':r['video']['codec']=='h264','one_audio_aac_48k_stereo':r['audio']['streams']==1 and r['audio']['codec']=='aac' and r['audio']['sample_rate']==48000 and r['audio']['channels']==2,
 'ambience_present':r['audio_min_50ms_rms_dbfs_excl_edges']>-60,'no_black':r['black_frames']==0,'no_unexpected_frame_diff':len(hashes)==1,
 'no_clip':r['clipped_samples']==0 and r['audio_peak_dbfs']<-1,'s028_raw_unchanged':r['sources_after']['s028_raw']=='341683c40de8d71ebed564b7739f9b338add2f954d00e347e0561c7fbe7a9b58',
 'ambience_unchanged':r['sources_after']['ambience']=='ea28fad468e353b99d48070d12853620f08e8b05c8d912706122d31176544d2f','frame_unchanged':r['sources_after']['s029_frame']=='a8b0d0fc597d9ad009fe96745485e89c2bae5d8764734a0cdec5ca00f7b023e4'}
r['result']='PASS' if all(r['checks'].values()) else 'FAIL'
print(json.dumps(r,indent=1))
