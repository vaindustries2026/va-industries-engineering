# EP005 Batch 1 — Real Motion Pass v03 (Kling 3.0 Turbo): 3 PASS, 1 FAIL

## Authorisation
Gilang / Company Brain, 2026-10-21:
- **Spend:** at most USD 1.50 in total.
- **Model:** `kling-video/v3.0-turbo/image-to-video` at 720p.
- **Calls:** one per shot for S005, S013, S017, S019; 4 maximum, 0 retries, no fallback, no alternates.
- **Why:** v01 and v02 were rejected as finished video; they looked like static illustrations.

## Locked packages (commit `93e027fc`, before any paid call)

| Shot | Prompt SHA-256 | Request body SHA-256 | Start image (approved composed frame) | Duration |
|---|---|---|---|---|
| S005 | 27256c701f4423417c12df63d3a50d2d577fe03a56001f287d23d6760e4bb62a | b2522a4e99f169d4244f904e6c1e115c0e25e01d333823a1031f32b4cb183073 | 407efd17… (G03 S005 output) | 4 s |
| S013 | 86b68d36a642b2ae14cb4864126e7a1585edbea4e8c20ec2deea60d897e79e68 | 88bd214774e87c04d0c2ea100d82424799a27fbed17ec032abb2da53253b7f94 | 5ff38815… | 4 s |
| S017 | e874ccaa72afb46dd4e9a4c5fa347c9821566322528412d3bc2c86a421c47e57 | 90df4264951995d5d12e23635ca820313b0f3f02f80484774c5727416937963b | f8513ca6… | 4 s |
| S019 | 4a827017ae609f981c7819f54b910408f14dfa23d3d7122422e214ab3f9f0459 | 2b3fe64c61e90c34eace88872e0b2c0ec2954b3929786a706aad8d9c4d6d33d3 | f429b9bd… | 5 s |

**Request body:** `{prompt, image_url, duration, resolution: "720p"}`.
- The parameters are corroborated by the Higgsfield catalog entry `kling3_0_turbo`: 720p or 1080p, 3–15 s, a single start image, no sound parameter.
- The aspect ratio follows the 16:9 source image.

**Start images:** each is the approved composed frame (the APPROVED G03 record re-applied, with SHA equal to the record's reproduced output). Each was uploaded once and read back by SHA.

**Prompts:** direct translations of the requested motion:
- blink, breathing, small head and eye movement, Lumi floating;
- locked camera, smudges fixed, no speech, no new objects or limbs, no morphing.

## Calls (sequential, 1 each, 0 retries)

| Shot | Request id | Terminal | Raw SHA-256 | Raw format | Provider audio |
|---|---|---|---|---|---|
| S005 | 8db8e5b7-2f32-4b71-b09d-dfd9e220ee53 | completed | 7377d38324ac9eecbf26fdb06f5116800b1eb7059323067f9eb8007dcf74c54d | 1280×720, 24 fps, 97 frames, 4.04 s | present (stripped) |
| S013 | 3bcd163c-f53b-4fdd-88cb-ed1b1269855e | completed | 0fe0a14d7d0caf25dad79466920d6bcfacef77641f85fe51fcf1c55a8e8cfe0f | 1280×720, 24 fps, 97 frames, 4.04 s | present (stripped) |
| S017 | 12f7f695-1e97-46a2-a65d-595a299490ce | completed | 4a7db31e074de892e3cb2d8881a132bbe45f6038d734c70af72f13a57aa746a6 | 1280×720, 24 fps, 97 frames, 4.04 s | present (stripped) |
| S019 | d14abf6e-6be9-4c8b-b63d-1c762debcb4d | completed | f107ef3e453bfad26d12426c2c39bd6155f29509ba01b68d7334b1b79969023b | 1280×720, 24 fps, 121 frames, 5.04 s | present |

**Cost**
- The provider exposed no cost or credit field before, during or after any call. No pre-submit price exists.
- **TOTAL_KNOWN_SPEND_USD = 0.00**, but actual spend is **UNKNOWN**.
- No ceiling stop triggered, because no known spend existed. Gilang should verify the account balance against the USD 1.50 authorisation.

## Raw preservation (S027/S028 raw-motion pattern)
Exact provider bytes were stored with `x-upsert: false`, SHA readback, and registered as `SHOT_MOTION / RAW_MOTION_SOURCE` with status REVIEW and human_decision PENDING:
- `MOTION-EP005-S005-KLING30T-CAND-v01` (row b5078e2b)
- `MOTION-EP005-S013-KLING30T-CAND-v01` (row e18f7375)
- `MOTION-EP005-S017-KLING30T-CAND-v01` (row e2997b58)
- `MOTION-EP005-S019-KLING30T-CAND-v01` (row ac50f330; QC FAIL recorded)

## Visual motion QC (`B1_MOTION_V03_VISUAL_QC_v1.json`)
**Method:** frames at 0/25/50/75/100%, face and hand crops, full-size checks, and a mirror-scale check (pink area constant within about ±3%, so there is no camera zoom).

| Shot | Verdict | Key observations |
|---|---|---|
| S005 | **PASS** | Reflection changes expression and the eyes travel over the marks; the foreground head leans in; Lumi floats and changes expression; cheek, nose and mouth marks stay put; no extra limbs. |
| S013 | **PASS (flag)** | Reflection expression and eye glance; Lumi floats; nose and mouth marks fixed. **Flag:** from about 3.5 s a red mark shows at the edge of the real (foreground) Mikko's face as he turns. It is consistent with Decision 1, but whether it is the nose mark or the removed cheek mark needs a human check. |
| S017 | **PASS** | Mikko turns toward the mirror and blinks; the reflection blinks in sync; the nose mark persists on both; Lumi floats. |
| S019 | **FAIL** | The reflection reacts and the nose mark is fixed, **but** from about 2.5 s a second hand (yellow glove, cream cuff, furry brown sleeve) enters and grips the handle. That is an extra limb and a new object, outside canon. Not assembled; no retry authorised. |

## Assembly of the passing shots (governed `compose_motion_shot`; runs A and B byte-identical)
**Method:**
- 24 fps, a Lanczos fit from 1280×720 to 1920×1080, first 96 frames.
- G03 was pre-composited in the start image and is not re-applied.
- Ambience is the approved `AMB-BATHROOM-QUIET-v01` at +11.5 dB; provider audio is not mapped.

| Candidate (REVIEW, PENDING, approved false) | SHA-256 | Motion (consecutive median / first↔last) | Audio |
|---|---|---|---|
| SHOT-EP005-S005-ASSEMBLED-CAND-v03 | 629e2e44fb10e285fe6782dac7724573a823f251e614edbd101de0ef0ca70cc8 | 2.00 / 25.4 | −30.8 LUFS, −19.3 dBTP / −19.3 dBFS, mean −33.0 dB |
| SHOT-EP005-S013-ASSEMBLED-CAND-v03 | 38c43abbb1e9c57ec7d54a6b92b34a2422f2e42763a4a8eb6704b7f062a33216 | 1.34 / 19.2 | same |
| SHOT-EP005-S017-ASSEMBLED-CAND-v03 | 78fdfe927296235dea176f970aeb26554b9864a93789de009acc3f7b6eeaf97f | 0.93 / 14.3 | same |

**All three share:** 1920×1080, 24 fps, 96 frames, 4.0 s, H.264 / AAC; Agent-008 QC PASS; assembly QC PASS (`B1_MOTION_V03_ASSEMBLY_QC_v1.json`).

There is no S019 v03 candidate, because its raw clip failed visual QC.

## Side-effect audit
**Kling calls:** S005 = 1, S013 = 1, S017 = 1, S019 = 1; **TOTAL_KLING_CALLS = 4**; **RETRIES = 0**.

**Spend:** TOTAL_KNOWN_SPEND_USD = 0.00 (not exposed by the provider; actual spend UNKNOWN).

**Files:**
- RAW_MOTION_FILES_PRESERVED = 4.
- ASSEMBLED_REVIEW_FILES_CREATED = 3 (S005, S013, S017).

**Production state writes:** 4 start-image transport uploads (provider), 7 storage objects and 7 REVIEW registry rows.

**Not used:** image generation, Flare, Seedance, ElevenLabs, Agent-006, Agent-007, dialogue.

**Unchanged:**
- script, manifest and readiness (both APPROVED);
- S027, S028, S029 (re-hash equal);
- the v01 and v02 history.

Anime Clip Farming: untouched.
