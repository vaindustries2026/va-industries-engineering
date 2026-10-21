# EP005 Batch 1 — First Four Shots v02 (Presentation Pass) Ready for Human Review

## Company Brain decision (2026-10-21)
- **Accepted:** the visual composition and G03 content of S005, S013, S017 and S019.
- **Rejected as final video presentation:** the v01 MP4s.
  - They are effectively static images held for 4–5 s; the decoded differences are H.264 noise, not animation.
  - The ambience was effectively inaudible: mean about −44.5 dB, peak about −30.5 dB.

**New product-level QC principle:** a REVIEW shot is not presentation-ready merely because the container, duration and hashes are valid.

**History kept:** the v01 objects and rows are untouched (status REVIEW, timestamps unchanged). The rejection is recorded in `B1_REVIEW_CANDIDATE_LEDGER_v1.jsonl`.

## Presentation pass (deterministic; same approved pixels)
Script: `evidence/ep005/batch1_render/b1_presentation_v02.py`. It is a small evidence script, not a framework, and no agent008 code changed.

1. **Source:** the approved G03 frame, re-applied from the APPROVED G03 record. It must equal the record's reproduced output SHA, so base frame and G03 are unchanged.
2. **Camera:** the whole frame moves as one 2D image, so the marks move with Mikko. Per output frame:
   - `t = i/(n−1)`, `e(t) = 0.75·(1−cos πt)/2 + 0.25·t` (smooth, never stationary);
   - `s = 1 + (S_END−1)·e`, `dx = DRIFT_X·e`;
   - window = `F + (frame − F)/s + (dx, 0)`, then one Lanczos resample to 1920×1080 (PIL).
   - There is no interpolation between frames, no optical flow, no character animation and no new objects.
3. **Audio:** only the approved `AMB-BATHROOM-QUIET-v01`, through the governed `mix_motion_audio` bed gain (**+11.5 dB**).
   - At 0 dB the bed measured −42.2 LUFS with a −30.4 dBTP true peak.
   - +12 dB would reach about −30 LUFS but sit about at the −18 dBFS ceiling, so +11.5 dB keeps margin.
   - No dialogue, no SFX.
4. **Encode:** the governed `media.encode_review` (H.264 yuv420p + AAC 48 kHz stereo, bitexact, single thread).

**Viewing-level QC adjustment (documented).** The first trial zoomed about the glass or nose centre and cropped 12–18 px of the mirror's top petal, which already touches the top edge in F01/F15. S005, S013 and S019 therefore use a top-anchored focal y of 150 px. The horizontal focus stays on the mirror or clue, and the extra petal crop is at most 4–5 px.

## Results (two independent runs byte-identical for every shot)

| Shot | v02 MP4 SHA-256 | Scale | Focal point / translation | Max safe crop (end) | Consecutive-frame motion median / first↔last (mean-abs) | Audio (MP4) |
|---|---|---|---|---|---|---|
| S005 | `b5c052ad7b8a4b9969ae45cc29546ae91c27249876f29e4b0f417db57e7ae37d` | 1.000 → 1.030 | F=(895, 150), dx_end=0 px, dy=0 | end window [26.1, 4.4, 1890.1, 1052.9] | 0.6086 / 17.003 | -30.8 LUFS / -19.3 dBTP / mean -33.0 dB |
| S013 | `1b6ef6b63905007471b9d576f7737c313fe86de17bd08e6f6acf48b4e8eeb882` | 1.000 → 1.025 | F=(954, 150), dx_end=0 px, dy=0 | end window [23.3, 3.7, 1896.4, 1057.3] | 0.5132 / 15.103 | -30.8 LUFS / -19.3 dBTP / mean -33.0 dB |
| S017 | `a4b6a8cdb17d04bdda1c7175acf2ee8c69026617801afee30f0522c561e4301a` | 1.000 → 1.025 | F=(830, 413), dx_end=12 px, dy=0 | end window [32.2, 10.1, 1905.4, 1063.7] | 0.7769 / 17.681 | -30.8 LUFS / -19.3 dBTP / mean -33.0 dB |
| S019 | `854e88c3218c870b871c1373ae024e55c4830f7bbb10eb431ae8590fc7d04001` | 1.000 → 1.035 | F=(959, 150), dx_end=0 px, dy=0 | end window [32.4, 5.1, 1887.5, 1048.6] | 0.4856 / 16.55 | -30.6 LUFS / -19.3 dBTP / mean -32.8 dB |

- **Motion curve:** `0.75·cosine ease-in-out + 0.25·linear`.
- **Format:** 1920×1080, 24 fps, exact authoritative frames (96 / 96 / 96 / 120).
- **Pre-encode frames:** all distinct (96/96, 120/120), so there is no duplicated still.

## QC (`B1_V02_PRESENTATION_QC_v1.json`): PASS × 4

**Visual motion**
- **MEASURED_MOTION_PASS:**
  - The consecutive-frame median is 0.49–0.78, against the v01 codec-noise ceiling of 0.037.
  - First↔last differs by 15–18.
  - The minimum consecutive-frame difference also exceeds the codec ceiling.
- **Motion is the approved transform:**
  - Each decoded frame matches its expected transformed frame within codec error (≤ 1.97 mean-abs).
  - The difference from the untransformed frame grows to 15–18 by the end.
- **Frame 0 = approved content.**
- **Safe bounds:** the window always stays inside the frame and no border is black.

**Audio**
- AUDIO_TRACK_PRESENT: true.
- AMBIENCE_ASSET_APPROVED: true (only the approved bed; source SHA unchanged).
- AUDIBLE_LEVEL_PASS: true (−30.6 to −30.8 LUFS, true and sample peak −19.3 dBFS, at most −18; mean −33 dB versus −44.5 in v01).
- NO_DIALOGUE: true.
- NO_UNAPPROVED_SFX: true.

**Viewing-level:** first, middle and last frames inspected. The push toward the mirror reads clearly; there are no edge exposures and no petal or face cropping beyond 5 px.
- **Limitation:** I cannot listen to playback in this environment. Audibility is shown by measurement only; the actual playback judgement rests with Company Brain.

## Candidates (status REVIEW, human_decision PENDING, approved false)

| Shot | Asset | Storage object | Registry id |
|---|---|---|---|
| S005 | SHOT-EP005-S005-ASSEMBLED-CAND-v02 | 58d75536-ec87-45a5-99b8-98365f2be09a | 0c2214d9-34f0-4705-9636-aaba402a8bef |
| S013 | SHOT-EP005-S013-ASSEMBLED-CAND-v02 | 2f32b1bf-8836-49b3-9542-cd139414b469 | 3fe6db9d-c7af-4abc-beb2-f426fae75df3 |
| S017 | SHOT-EP005-S017-ASSEMBLED-CAND-v02 | 1ae2cf6c-8f3b-46d4-82e8-264982c30002 | 87f02ff2-f403-4d4a-aa16-47f3708714e8 |
| S019 | SHOT-EP005-S019-ASSEMBLED-CAND-v02 | e41c3e9d-2246-499e-9c06-19a5b795acdf | 257b104e-a66a-4c9f-a153-68fd65ab5a11 |

## Side-effect audit
**Zero:** provider calls, generative video, image generations, ElevenLabs calls, Agent-006/Agent-007 runs.

**Unchanged:**
- base frames, the G03 geometry and records (all 10 records still APPROVED and not updated);
- G08;
- script, manifest and readiness (both APPROVED);
- S027, S028, S029 (re-hash equal).

**Production writes:** 4 v02 storage objects plus 4 REVIEW rows. The v01 history is preserved.

**Tests:** 205/205 OK.

Anime Clip Farming: untouched.
