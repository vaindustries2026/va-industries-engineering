#!/usr/bin/env bash
# EP005 selected ElevenLabs audio -> local PRODUCTION-READY REVIEW DERIVATIVES (Mikko & Lumi). Offline, deterministic, ffmpeg only.
# Inputs: the three exact original downloads (verified against recorded SHA-256 before anything runs):
#   AMB-C.mp3   = AMB-BATHROOM-QUIET-v01-EL-CAND-C   (generation Oe9nvpw0JuR3zKjs6Vib)
#   CLOTH-C.mp3 = FOLEY-CLOTH-SOFT-v01-EL-CAND-C     (generation eiW0bnQ9IsbkD6qwPVuQ)
#   POP-A.mp3   = SFX-COMPLETION-POP-v01-EL-CAND-A   (generation 75tahAZ0wFnzcjSADUkx)
# Output: 24-bit PCM WAV at the source sample rate (44.1 kHz) and channel layout (stereo). No resampling, no downmix.
# Usage: master_ep005_selected_audio_v1.sh <dir with the 3 original .mp3> <output dir>
set -euo pipefail
SRC="${1:?source dir required}"; OUT="${2:?output dir required}"
W="$OUT/work"; AID="$OUT/review_aids"; mkdir -p "$W" "$AID"

# --- 0. verify the exact original bytes -------------------------------------------------------------------------------
sha256sum -c - <<SUMS
baee962c86f8725ffa595331f452a698bde7d5e69871165696bf43e933317d6b  $SRC/AMB-C.mp3
b0c80ce840bc39f0f306b8f84dcf5fb8b654a011249bcd03a63933911f6b9080  $SRC/CLOTH-C.mp3
26cbfe89678e68b4826a8179c29ffa427492bd521a8df300c51d9c8f4b9d4a6d  $SRC/POP-A.mp3
SUMS

FF=(ffmpeg -nostdin -hide_banner -loglevel error -y -fflags +bitexact)
OUTFMT=(-flags:a +bitexact -map_metadata -1 -c:a pcm_s24le)
dec()   { "${FF[@]}" -i "$1" -map_metadata -1 -c:a pcm_f32le "$2"; }          # lossless float decode (sample-exact)
nsamp() { ffprobe -v error -select_streams a:0 -show_entries stream=duration_ts -of csv=p=0 "$1"; }

# --- 1. AMBIENCE: loop-aware 80 Hz high-pass (objective defect: ~99% of power is a 25-40 Hz rumble) + gain +34.5 dB -------
# Loop-aware: filter a 3x concatenation and keep the middle copy, so the filter state is continuous across the loop join.
# 4th-order Butterworth = two biquads with Q 0.5412 and 1.3066. Audible band (>=100 Hz) is untouched.
dec "$SRC/AMB-C.mp3" "$W/amb_dec.wav"; N=$(nsamp "$W/amb_dec.wav")
"${FF[@]}" -stream_loop 2 -i "$W/amb_dec.wav" \
  -af "highpass=f=80:t=q:w=0.5412,highpass=f=80:t=q:w=1.3066,atrim=start_sample=$N:end_sample=$((2*N)),asetpts=N/SR/TB,volume=34.5dB" \
  "${OUTFMT[@]}" "$OUT/AMB-BATHROOM-QUIET-v01_MASTER_REVIEW.wav"
# review aid 1: the master played twice in a row (listen at its midpoint for the loop seam)
"${FF[@]}" -stream_loop 1 -i "$OUT/AMB-BATHROOM-QUIET-v01_MASTER_REVIEW.wav" "${OUTFMT[@]}" "$AID/LOOPCHECK_AMB-BATHROOM-QUIET-v01_MASTER_x2.wav"
# review aid 2: comparison only - the SAME gain with NO filter (the strict "gain only" version), to show what the high-pass removed
"${FF[@]}" -i "$W/amb_dec.wav" -af "volume=34.5dB" "${OUTFMT[@]}" "$AID/COMPARISON_AMB-BATHROOM-QUIET-v01_gain-only_no-highpass.wav"

# --- 2. CLOTH: trim the near-silent tail at 940 ms (41454 samples) + gain +18.8 dB (sample peak -> about -6 dBFS) ---------
dec "$SRC/CLOTH-C.mp3" "$W/cloth_dec.wav"
"${FF[@]}" -i "$W/cloth_dec.wav" -af "atrim=end_sample=41454,asetpts=N/SR/TB,volume=18.8dB" \
  "${OUTFMT[@]}" "$OUT/FOLEY-CLOTH-SOFT-v01_MASTER_REVIEW.wav"

# --- 3. POP: 30 Hz high-pass (objective defect: sub-40 Hz unipolar pulse / baseline shift), trim to 200 ms (8820 samples),
#            0.25 ms anti-click fade-in (11 samples; ends before the peak at ~0.45 ms), 20 ms fade-out, gain +26.9 dB ------
dec "$SRC/POP-A.mp3" "$W/pop_dec.wav"
"${FF[@]}" -i "$W/pop_dec.wav" \
  -af "highpass=f=30:poles=2,atrim=end_sample=8820,asetpts=N/SR/TB,afade=t=in:ss=0:d=0.00025,afade=t=out:st=0.180:d=0.020,volume=26.9dB" \
  "${OUTFMT[@]}" "$OUT/SFX-COMPLETION-POP-v01_MASTER_REVIEW.wav"
echo "OK: masters written to $OUT"
