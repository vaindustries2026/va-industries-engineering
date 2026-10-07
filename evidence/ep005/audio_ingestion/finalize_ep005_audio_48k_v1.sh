#!/usr/bin/env bash
# EP005 final production masters: approved 44.1 kHz mastered review files -> 48 kHz / 24-bit WAV. Offline, deterministic, ffmpeg only.
# The ONLY processing is sample-rate conversion (libsoxr, precision 28). Channel layout (stereo) and levels are preserved.
# Ambience: loop-aware (3x concatenation, resample, keep the middle copy) so the seamless-loop join is not disturbed by resampler edge effects.
# Usage: finalize_ep005_audio_48k_v1.sh <dir with the 3 approved *_MASTER_REVIEW.wav> <output dir>
set -euo pipefail
SRC="${1:?approved masters dir required}"; OUT="${2:?output dir required}"; mkdir -p "$OUT"
sha256sum -c - <<SUMS
4ce88a1a396c3a9dc4f34ee4f9d1ae8464b2ab5bd81ddf0fd375eff5ab5566c7  $SRC/AMB-BATHROOM-QUIET-v01_MASTER_REVIEW.wav
e861dd2b7b26a78b7be31ab9db1bef3d5ccc7905f700e5c04bc9eae849805f03  $SRC/FOLEY-CLOTH-SOFT-v01_MASTER_REVIEW.wav
0c5d136d407b60f9dc6ec65ab98fbd764dcb0e6f7f24b2fd04dd3f5d57f6398f  $SRC/SFX-COMPLETION-POP-v01_MASTER_REVIEW.wav
SUMS
FF=(ffmpeg -nostdin -hide_banner -loglevel error -y -fflags +bitexact)
OUTFMT=(-flags:a +bitexact -map_metadata -1 -c:a pcm_s24le -ar 48000)
RS="aresample=resampler=soxr:precision=28:out_sample_rate=48000"
nsamp() { ffprobe -v error -select_streams a:0 -show_entries stream=duration_ts -of csv=p=0 "$1"; }

# AMBIENCE: N samples @44.1k -> N' = round(N*48000/44100) samples @48k; middle copy of the 3x concatenation.
N=$(nsamp "$SRC/AMB-BATHROOM-QUIET-v01_MASTER_REVIEW.wav")
NP=$(python3 -c "print(round($N*48000/44100))")
"${FF[@]}" -stream_loop 2 -i "$SRC/AMB-BATHROOM-QUIET-v01_MASTER_REVIEW.wav" \
  -af "$RS,atrim=start_sample=$NP:end_sample=$((2*NP)),asetpts=N/SR/TB" "${OUTFMT[@]}" "$OUT/AMB-BATHROOM-QUIET-v01.wav"
# CLOTH and POP: one-shots, direct resample.
"${FF[@]}" -i "$SRC/FOLEY-CLOTH-SOFT-v01_MASTER_REVIEW.wav" -af "$RS" "${OUTFMT[@]}" "$OUT/FOLEY-CLOTH-SOFT-v01.wav"
"${FF[@]}" -i "$SRC/SFX-COMPLETION-POP-v01_MASTER_REVIEW.wav" -af "$RS" "${OUTFMT[@]}" "$OUT/SFX-COMPLETION-POP-v01.wav"
echo "OK: final 48 kHz masters in $OUT (ambience N=$N -> N'=$NP samples)"
