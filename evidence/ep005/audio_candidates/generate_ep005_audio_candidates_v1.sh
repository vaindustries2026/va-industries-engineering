#!/usr/bin/env bash
# EP005 local audio candidates v1 - deterministic, offline, owned audio (Mikko & Lumi).
# Uses ONLY ffmpeg built-in lavfi signal sources (anoisesrc with fixed seeds, aevalsrc math expressions).
# No input files, no network, no provider, no external licence dependency.
# Output: 3 ambience candidates (AMB-BATHROOM-QUIET-v01 A/B/C) and 3 completion-pop candidates
# (SFX-COMPLETION-POP-v01 A/B/C) as WAV PCM 24-bit 48 kHz. CANDIDATES ONLY - not approved, not registered.
# Usage: generate_ep005_audio_candidates_v1.sh <output_dir>
set -euo pipefail
OUT="${1:?output dir required}"; mkdir -p "$OUT"
BITEXACT=(-fflags +bitexact -flags:a +bitexact -map_metadata -1 -c:a pcm_s24le -ar 48000)

# ---------------------------------------------------------------------------------------------
# Ambience: stereo room tone from two decorrelated pink-noise sources (fixed seeds), band-limited,
# made seamless with an equal-power 3 s crossfade of the tail into the head (loop length L=40 s),
# then a very slow +/-0.7 dB level drift whose period equals the loop length (so the loop stays seamless).
# Loop construction: out = A[3:40] ++ mix(A[40:43] fade-out, A[0:3] fade-in); out ends where it begins.
# ---------------------------------------------------------------------------------------------
ambience() { # id seedL seedR amplitude eq_chain
  local id="$1" sl="$2" sr="$3" amp="$4" eq="$5"
  ffmpeg -nostdin -hide_banner -loglevel error -y \
    -f lavfi -i "anoisesrc=color=pink:seed=${sl}:amplitude=${amp}:sample_rate=48000:duration=43" \
    -f lavfi -i "anoisesrc=color=pink:seed=${sr}:amplitude=${amp}:sample_rate=48000:duration=43" \
    -filter_complex "\
[0:a][1:a]join=inputs=2:channel_layout=stereo,${eq},asplit=3[s1][s2][s3];\
[s1]atrim=3:40,asetpts=PTS-STARTPTS[body];\
[s2]atrim=40:43,asetpts=PTS-STARTPTS,afade=t=out:st=0:d=3:curve=qsin[tail];\
[s3]atrim=0:3,asetpts=PTS-STARTPTS,afade=t=in:st=0:d=3:curve=qsin[head];\
[tail][head]amix=inputs=2:normalize=0[seam];\
[body][seam]concat=n=2:v=0:a=1,volume=eval=frame:volume='1+0.08*sin(2*PI*t/40)'[out]" \
    -map "[out]" "${BITEXACT[@]}" "$OUT/${id}.wav"
}
# A: cleanest / most neutral
ambience AMB-BATHROOM-QUIET-v01-CAND-A 1101 1102 0.0180 "highpass=f=90:poles=2,lowpass=f=6000:poles=2"
# B: slightly warmer / softer (lower top end, gentle low-mid lift)
ambience AMB-BATHROOM-QUIET-v01-CAND-B 1201 1202 0.0200 "highpass=f=70:poles=2,lowpass=f=3800:poles=2,equalizer=f=250:t=q:w=0.8:g=1.5"
# C: slightly airier / more open (higher top end, small air shelf)
ambience AMB-BATHROOM-QUIET-v01-CAND-C 1301 1302 0.0160 "highpass=f=120:poles=2,lowpass=f=10000:poles=2,highshelf=f=6000:g=2"

# ---------------------------------------------------------------------------------------------
# Completion pop: mono, a short damped sine whose frequency glides quickly downward
# f(t) = F1 + (F0-F1)*exp(-t/TAU)  ->  phase = F1*t + (F0-F1)*TAU*(1-exp(-t/TAU))
# amplitude envelope = AMP * min(1, t/ATT) * exp(-t/DEC); final 20 ms linear fade to true zero; gentle low-pass.
# Short decay (45-70 ms) so it reads as a soft "pop", not a pitched note.
# ---------------------------------------------------------------------------------------------
pop() { # id F0 F1 TAU ATT DEC DUR AMP lowpass extra_click(0/1)
  local id="$1" f0="$2" f1="$3" tau="$4" att="$5" dec="$6" dur="$7" amp="$8" lp="$9" click="${10}"
  local expr="${amp}*min(1\,t/${att})*exp(-t/${dec})*sin(2*PI*(${f1}*t+(${f0}-${f1})*${tau}*(1-exp(-t/${tau}))))"
  if [ "$click" = "1" ]; then  # very soft 2.9 kHz transient decaying in ~4 ms (no noise source)
    expr="${expr}+0.06*exp(-t/0.0015)*sin(2*PI*2900*t)"
  fi
  local fo; fo=$(awk -v d="$dur" 'BEGIN{printf "%.3f", d-0.020}')
  ffmpeg -nostdin -hide_banner -loglevel error -y \
    -f lavfi -i "aevalsrc=exprs='${expr}':s=48000:d=${dur}:c=mono" \
    -af "lowpass=f=${lp}:poles=2,afade=t=out:st=${fo}:d=0.020" \
    "${BITEXACT[@]}" "$OUT/${id}.wav"
}
# A: balanced soft pop
pop SFX-COMPLETION-POP-v01-CAND-A 900 380 0.025 0.002 0.060 0.25 0.50 4500 0
# B: softer, slightly lower, rounder
pop SFX-COMPLETION-POP-v01-CAND-B 700 300 0.030 0.003 0.070 0.30 0.50 2600 0
# C: slightly brighter and shorter, with a barely-there transient
pop SFX-COMPLETION-POP-v01-CAND-C 1100 450 0.020 0.0015 0.045 0.18 0.45 6000 1
