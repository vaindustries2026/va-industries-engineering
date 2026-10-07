# EP005 Selected ElevenLabs Audio: Mastered Review Derivatives (v1)

**Date:** 2026-10-07 (UTC)
**Actor:** Claude Code (bounded engineering operator)
**Selected by:** Gilang / Company Brain, after human review: AMBIENCE C, CLOTH C, COMPLETION POP A. These are the only selected candidates.
**Scope:** Mikko & Lumi only.
**Status of every output:** REVIEW DERIVATIVE. Nothing is approved, registered or uploaded.

## 1. Source verification

All three originals were verified against the SHA-256 recorded in `EP005_ELEVENLABS_AUDIO_CANDIDATES_v1.0.md` and its manifest before anything ran. The recipe script verifies them again on every run.

| Production id | Selected candidate | Source generation id | Source SHA-256 | Match |
|---|---|---|---|---|
| AMB-BATHROOM-QUIET-v01 | AMB-BATHROOM-QUIET-v01-EL-CAND-C | `Oe9nvpw0JuR3zKjs6Vib` | `baee962c86f8725ffa595331f452a698bde7d5e69871165696bf43e933317d6b` | ✓ |
| FOLEY-CLOTH-SOFT-v01 | FOLEY-CLOTH-SOFT-v01-EL-CAND-C | `eiW0bnQ9IsbkD6qwPVuQ` | `b0c80ce840bc39f0f306b8f84dcf5fb8b654a011249bcd03a63933911f6b9080` | ✓ |
| SFX-COMPLETION-POP-v01 | SFX-COMPLETION-POP-v01-EL-CAND-A | `75tahAZ0wFnzcjSADUkx` | `26cbfe89678e68b4826a8179c29ffa427492bd521a8df300c51d9c8f4b9d4a6d` | ✓ |

## 2. Masters

All outputs are WAV PCM 24-bit, 44,100 Hz, stereo, written from a lossless float32 decode of the MP3 with no resampling and no downmix. They are reproducible: two independent runs of the committed script produced byte-identical files.

| Master review file | Bytes | SHA-256 |
|---|---|---|
| `AMB-BATHROOM-QUIET-v01_MASTER_REVIEW.wav` | 6,615,168 | `4ce88a1a396c3a9dc4f34ee4f9d1ae8464b2ab5bd81ddf0fd375eff5ab5566c7` |
| `FOLEY-CLOTH-SOFT-v01_MASTER_REVIEW.wav` | 248,826 | `e861dd2b7b26a78b7be31ab9db1bef3d5ccc7905f700e5c04bc9eae849805f03` |
| `SFX-COMPLETION-POP-v01_MASTER_REVIEW.wav` | 53,022 | `0c5d136d407b60f9dc6ec65ab98fbd764dcb0e6f7f24b2fd04dd3f5d57f6398f` |

### Before and after

| | AMB-BATHROOM-QUIET-v01 | FOLEY-CLOTH-SOFT-v01 | SFX-COMPLETION-POP-v01 |
|---|---|---|---|
| Duration | 25.0002 s → 25.0002 s (1,102,511 samples, unchanged) | 1.000 s → **0.940 s** | 0.480 s → **0.200 s** |
| Sample peak | −50.39 → **−29.86 dBFS** | −24.88 → **−6.08 dBFS** | −32.22 → **−6.02 dBFS** |
| True peak | −50.4 → −29.9 dBTP | −24.7 → −5.9 dBTP | −32.2 → −6.0 dBTP |
| RMS | −63.7 → −44.2 dBFS | −40.5 → −21.4 dBFS | −52.0 → −24.8 dBFS |
| Integrated loudness | −69.0 → **−42.0 LUFS** (see note) | −33.5 → −14.6 LUFS | not measurable (shorter than the 400 ms meter block) |
| Sub-60 Hz RMS | −64.9 → −60.7 dBFS | −76.8 → −57.7 dBFS | −54.4 → −42.5 dBFS |
| ≥100 Hz RMS | −82.3 → −47.8 dBFS | −42.7 → −23.6 dBFS | −55.7 → −25.0 dBFS |
| Mean (DC) | −3.2e-5 → −5.8e-8 | −5.6e-5 → −5.1e-4 (gain only) | +1.4e-3 → −1.6e-4 |
| First / last sample | 8.4e-5 / 1.1e-5 → 8.0e-3 / 1.1e-2 (ordinary noise values) | 3.2e-4 / 2.1e-4 → 2.8e-3 / 1.6e-3 | 2.8e-3 / 2.0e-4 → 0 / 1.7e-6 |
| Format | MP3 128 kbps → WAV s24 | same | same |
| Gain applied | **+34.5 dB** | **+18.8 dB** | **+26.9 dB** |

Note on ambience loudness: the filtered source sits at the −70 LUFS absolute gate of the loudness meter, which biases a direct reading. I measured it after a coarse +30 dB boost and corrected, so the −42.0 figure is a real measurement of the final file. The true source loudness was about −76.5 LUFS.

## 3. Exact processing

The recipe is `evidence/ep005/audio_mastering/master_ep005_selected_audio_v1.sh`. The measurements come from `measure_ep005_masters_v1.py`. Per-file figures and filter chains are in `EP005_MASTERING_MANIFEST_v1.json`.

**Ambience C**
1. Lossless float decode.
2. Loop-aware filtering. The signal is concatenated three times, filtered, and the middle copy kept, so the filter state is continuous across the loop join. The filter is a 4th-order Butterworth high-pass at 80 Hz (`highpass=f=80:t=q:w=0.5412,highpass=f=80:t=q:w=1.3066`).
3. Gain +34.5 dB, targeting −42 LUFS.
4. Export WAV s24.
- **Not done:** no loop crossfade, no other EQ, no compression, no reverb, no added sound, no resampling.

**Cloth C**
1. Lossless float decode.
2. `atrim=end_sample=41454` drops the near-silent last 60 ms.
3. Gain +18.8 dB, bringing the peak to about −6 dBFS.
4. Export WAV s24.
- **Not done:** no leading trim (the file has no digital silence: it opens at −70 dBFS, 45 dB under the peak, and ramps into the event), no filter, no fades, no layering.

**Pop A**
1. Lossless float decode.
2. 2nd-order Butterworth high-pass at 30 Hz (`highpass=f=30:poles=2`).
3. Trim to 8,820 samples (0.200 s).
4. 0.25 ms linear fade-in (11 samples) and 20 ms fade-out.
5. Gain +26.9 dB, bringing the peak to about −6 dBFS.
6. Export WAV s24.
- **Not done:** no sparkle, bell, chime, reverb or layering, and no other EQ or compression.

## 4. Two filters beyond "gain only" (deviation, with reasons)

Your instruction was gain-only for the ambience, and trim, gain and fade for the pop, with EQ allowed only to solve an objective technical defect. I judged these two measured defects to qualify, and both high-passes sit below the audible character of the sounds.

1. **Ambience, 80 Hz high-pass.** About 99% of the source's power is a 25–40 Hz rumble (strongest line 30.4 Hz), 17.4 dB above the audible band (RMS −64.9 dBFS below 60 Hz against −82.3 dBFS from 100 Hz upward). Applying the gain alone would have made a loud sub-bass drone.
   - After the filter the rumble sits 13 dB below the hush (−60.7 against −47.8 dBFS at the final level).
   - Content from 100 Hz upward is unchanged (−82.3 dBFS before and after the filter, before gain).
   - **Comparison file included:** `COMPARISON_AMB-BATHROOM-QUIET-v01_gain-only_no-highpass.wav` is the same gain with no filter, so you can hear what was removed. It is a comparison aid and not a candidate.
2. **Pop, 30 Hz high-pass.** A slow, one-sided sub-40 Hz pulse (mean +1.4e-3, about 14 dB under the audible peak) lay under the transient. After the required +26.9 dB it would have been a baseline shift and an edge click. After filtering, its peak fell from −47.7 to −66.2 dBFS (pre-gain figures) and the file's mean is about zero.

**Decision for Company Brain:** accept these two filters, or tell me to re-make them as strictly gain-only.

## 5. Other findings

- **Ambience loop seam: clean, so I left the provider's loop as is.** The wrap-around step sits at the 56th percentile of ordinary sample steps. The last and first 200 ms are −50.4 and −49.3 dBFS, within the file's own 3.8 dB range. Spectral continuity across the join is 0.66 dB, against a median of 0.62 dB for random pairs of segments. The result is identical before and after the filter.
- **Weak tonal lines remain in the ambience.** There are faint lines at 3.6–15.8 kHz, mostly at multiples of 50 Hz. They sit about 25 dB below the hush, at about −104 dBFS before gain, and are steady in time. They are probably MP3 codec artefacts and likely below masking, and I left them untouched. Please confirm on the master.
- **The existing approved SFX library is 48 kHz** and peaks between −0.3 and −3.2 dBFS (about −15 LUFS). These masters stay at the source's native **44.1 kHz** because resampling was outside the allowed processing. A transparent conversion to 48 kHz could be done at assembly or as a separately authorised step.
- **Pop trim:** the audible transient decays into the noise floor (−40 dB below the peak) by about 160 ms. The 0.20 s length is inside your 0.15–0.35 s target.
- **Source quality:** the originals are 128 kbps MP3, so the 24-bit WAVs are lossless containers of lossy audio.
- **Gain sizes:** the sources were very quiet, so the gains are large. Gain raises the source's noise floor by the same amount.

## 6. Rights and account status (unchanged, still open)

- **Rights:** commercial-use rights for these ElevenLabs outputs remain **unreconciled**.
- **Account:** the connector's workspace (`a2a81ab0f7fd406cb3fff9eef8e173c2`) and whether it is the VA account were not resolved by the earlier reconciliation.
- **Before ingestion:** both questions must be settled and a human must approve the exact bytes.

## 7. Review files (session scratch; not committed, not uploaded)

```
/tmp/claude-0/-home-user-va-industries-engineering/26999ca9-2a8f-5871-b737-7fa96a08dad2/scratchpad/mastering/review_final/
  AMB-BATHROOM-QUIET-v01_MASTER_REVIEW.wav
  FOLEY-CLOTH-SOFT-v01_MASTER_REVIEW.wav
  SFX-COMPLETION-POP-v01_MASTER_REVIEW.wav
  review_aids/COMPARISON_AMB-BATHROOM-QUIET-v01_gain-only_no-highpass.wav   (comparison aid)
  review_aids/LOOPCHECK_AMB-BATHROOM-QUIET-v01_MASTER_x2.wav                (listening aid)
```

The audio files are not committed. The originals remain in the session scratch from the generation task, and their hashes are in the evidence.

## 8. Unchanged state and safety

| Item | State |
|---|---|
| asset_registry | 20 rows, md5 `b7b46112661dc0a0d9218e647f747306` |
| storage.objects | 16, md5 `4c7ef85e9c92af4fca27b775e233b7bc` |
| Manifest `96df250f` | APPROVED, unchanged; no derived manifest created |
| Readiness manifests | `89663d3b…` |
| Migrations | 1 |

- **ElevenLabs calls:** 0. **Credits used:** 0. **New generations:** 0.
- **Reads only:** I downloaded the three existing approved SFX from storage as a loudness reference.
- **Writes:** none to Supabase, n8n or workflows.
- **Agent-006 and Agent-007:** not run. **Readiness approvals:** 0.
- **Tooling:** no additional network installs this time.

## 9. Final status

```text
EP005_SELECTED_AUDIO_MASTERING_READY_FOR_FINAL_HUMAN_REVIEW
+ AMBIENCE_C_SELECTED + CLOTH_C_SELECTED + POP_A_SELECTED
+ THREE_MASTERED_REVIEW_FILES
+ ZERO_NEW_GENERATIONS + ZERO_ELEVENLABS_CREDITS
+ ZERO_REGISTRY_WRITES + ZERO_PRODUCTION_STORAGE_WRITES + ZERO_AGENT006_RUN
```

**Stop condition:** the three mastered review files are ready for final human listening. Nothing has been registered or uploaded.
