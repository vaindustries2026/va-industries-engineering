# EP005 Batch 1: motion review reconciliation (v04)

Record: `ENG-20261021-EP005-BATCH1-MOTION-REVIEW-RECONCILED`. This covers Mikko & Lumi only.

**Outcome:**
- S005 and S017 are now **COMPLETE_APPROVED**.
- Both replacement generations, S013 v04 and S019 v04, **FAILED** visual QC on the exact hard negatives they were meant to avoid.
- No v04 MP4 was assembled. There were no retries.

## 1. Authorisation and basis

| | |
|---|---|
| Decision | Company Brain decision plus Gilang's paid authorisation, 2026-10-21 |
| Evidence basis | commit `5b4aeea8f9684b2541896a832abdd063a15b67b0` |
| Spend ceiling | USD 1.00 additional |
| Calls | max 1 per shot (S013, S019), total 2 |
| Constraints | 0 retries, 0 alternates, no fallback |
| Provider / model | Higgsfield `kling-video/v3.0-turbo/image-to-video`, 720p |

## 2. Human decisions bound (script `ep005/batch1_motion_v04/b1_decisions_v04.py`)

Each row was PATCHed in place, and the stored bytes were re-hashed before and after. Readback: `ep005/batch1_motion_v04/B1_V04_DECISION_ROWS_READBACK_v1.json`.

| Asset | SHA-256 | Result |
|---|---|---|
| SHOT-EP005-S005-ASSEMBLED-CAND-v03 | 629e2e44fb10e285fe6782dac7724573a823f251e614edbd101de0ef0ca70cc8 | REVIEW → **APPROVED**; approved true; human_decision APPROVED; final_state COMPLETE_APPROVED; stored SHA match |
| SHOT-EP005-S017-ASSEMBLED-CAND-v03 | 78fdfe927296235dea176f970aeb26554b9864a93789de009acc3f7b6eeaf97f | REVIEW → **APPROVED**; COMPLETE_APPROVED; stored SHA match |
| SHOT-EP005-S013-ASSEMBLED-CAND-v03 | 38c43abbb1e9c57ec7d54a6b92b34a2422f2e42763a4a8eb6704b7f062a33216 | REVIEW → **REJECTED** (REJECTED_BY_HUMAN: red facial mark appears late on foreground Mikko); kept as evidence |
| MOTION-EP005-S019-KLING30T-CAND-v01 (raw) | f107ef3e453bfad26d12426c2c39bd6155f29509ba01b68d7334b1b79969023b | REVIEW → **REJECTED** (REJECTED_BY_HUMAN / CANON_FAIL: second hand, yellow glove, brown furry sleeve); kept as evidence |

S005 and S017 were promoted with the exact bytes, unchanged. There was no re-encode and no copy, and nothing has changed since promotion.

Finished EP005 shots (APPROVED SHOT_RENDER rows, read live):
- S027
- S028
- S029
- S005
- S017

**FINISHED_SHOT_COUNT = 5.**

## 3. Locked packages (lock commit `98df19106bcfaf05c7cfd73761038e79f59f5ff7`, before submission)

Package file: `ep005/batch1_motion_v04/B1_MOTION_V04_PACKAGES_v1.json`.

| | S013 | S019 |
|---|---|---|
| PROMPT_SHA256 | 2a175930bcf65958bbff6246bb0801842a160024dd1c6b203958c9cf8e86345d | 6e79f018545a318db8edef9729d3efb6cbae099c5c6da51fb364c5d853a34f7d |
| REQUEST_BODY_SHA256 | b3b3356f4bdf5e06e7506ceff23d08b0b960ebd16fa3117cdab4e44bcd0125ea | ea443e9383a2c18e284d23c661a306ded8a70ad625d8d65fdf73846dabb99cf8 |
| START_IMAGE_SHA | the same approved v03 start image (G03 composed), re-verified by GET | the same approved F15/S019 v03 start image, re-verified |
| MODEL / RESOLUTION / DURATION | kling-video/v3.0-turbo/image-to-video / 720p / 4 s | same / 720p / 5 s |
| Hard negatives in prompt | foreground Mikko stays turned away; exactly two smudges, both in the reflection; no new red mark anywhere | exactly one hand (Lumi's); no second hand, glove, paw, sleeve or arm; nothing reaches toward the mirror |

## 4. Provider calls (ledger `ep005/batch1_motion_v04/B1_MOTION_V04_LEDGER_v1.jsonl`)

| Shot | Request ID | Attempt | Submitted (UTC) | Terminal | Cost fields |
|---|---|---|---|---|---|
| S013 | b5f182ac-7369-4389-832c-86fcbed6e363 | 1 | 2026-10-21 02:58:18 | completed | none exposed |
| S019 | 470f93c2-9160-4823-96c0-2d100aa03d00 | 1 | 2026-10-21 03:00:46 | completed | none exposed |

- **TOTAL_NEW_KLING_CALLS = 2. RETRIES = 0.**
- The provider exposed no pre-submit price and no post-run cost, so the known new spend is **USD 0.00** and the actual cost is **UNKNOWN**. The calls ran under the explicit bounded two-call authorisation.
- There was no top-up, purchase or billing change.

## 5. Raw outputs preserved (exact provider bytes; storage x-upsert false; readback SHA match)

Neither raw was assembled.

| Asset | Status | SHA-256 | Bytes | Video | Duration | Audio | Registry id / storage object |
|---|---|---|---|---|---|---|---|
| MOTION-EP005-S013-KLING30T-CAND-v02 | REVIEW (QC FAIL) | 174eb8a1ee8ba0182f9d6b6b72bef303bde987a98811de460672c67cfc0b58df | 3,020,434 | 1280x720 h264 24 fps, 97 frames | 4.041667 s | provider audio present (not used) | e5b28aee-1162-4d82-9775-f95d160d26f5 / 4a304791-158f-4366-9899-1aeeb03da489 |
| MOTION-EP005-S019-KLING30T-CAND-v02 | REVIEW (QC FAIL) | defadf575f985229d847c1b37713fed46e236cc0625986a3113ceaf8db0d72fa | 2,919,425 | 1280x720 h264 24 fps, 121 frames | 5.041667 s | provider audio present (not used) | 8be0d7c5-dce0-4067-b7d0-7209a6aebb2b / 360b0e92-2f71-4591-a1f4-5740249d591f |

Storage keys: `visual/production/ep005/motion/<asset_id>.mp4`. Rows were created by `ep005/batch1_motion_v04/b1_register_motion_v04.py`, with readback in `B1_MOTION_V04_ROWS_READBACK_v1.json`. Both rows have approved false and human_decision PENDING. Rejection is left to the human.

## 6. Visual QC (`ep005/batch1_motion_v04/B1_MOTION_V04_VISUAL_QC_v1.json`; sheets in `ep005/batch1_motion_v04/qc/`)

### S013 v04: **FAIL**
REAL_CHARACTER_MOTION=YES · **NEW_RED_MARK=YES** · SMUDGE_COUNT_STABLE=NO · SMUDGE_POSITION_STABLE=YES (reflection) · CANON_IDENTITY_STABLE=YES · EXTRA_LIMBS=NO · MIRROR_CONTINUITY_PASS=YES

- The reflection behaves correctly: a blink, eye movement between the two marks, and fixed marks.
- **Defect:** despite the explicit negative, the foreground real Mikko turns his head from about frame 48. An eye edge and his muzzle enter at the left edge with a **red berry mark on the nose tip**, which stays visible to the end (f96). Frame 0 shows no muzzle and no mark. This is the same defect class as the rejected v03.
- Evidence: `B1_V04_QC_S013_SHEET.jpg` and `B1_V04_QC_S013_FG_CROPS.jpg` (f0/48/60/72/84/96 at 1.5×).

### S019 v04: **FAIL**
REAL_CHARACTER_MOTION=YES · **EXTRA_HAND=YES** · **EXTRA_ARM=YES** · **YELLOW_GLOVE=YES** (pale-yellow mitten-like limb) · BROWN_SLEEVE=NO · NEW_CHARACTER=NO · **LUMI_HAND_CANON_PASS=NO** · NOSE_SMUDGE_STABLE=YES · MIRROR_CONTINUITY_PASS=YES

- The reflection behaves correctly: the expression settles, and the nose smudge stays fixed.
- **Defect:** from about frame 50 a **second pale-yellow limb holding a large glowing orb** enters from the lower right. It pushes the orb up the handle to just below the mirror (f60–f90), then partly withdraws. Two hands are on the handle at once, which is the same defect class as the rejected raw.
- Evidence: `B1_V04_QC_S019_SHEET.jpg` and `B1_V04_QC_S019_HAND_CROPS.jpg` (f0/50/65/75/85/100 at 2×).

Per the rule "If the defect appears: FAIL the shot. Do not retry.", both shots are FAILED and were not retried.

## 7. Assembly

Nothing was assembled. Neither raw passed, so assembly (Part 11) was not run. SHOT-EP005-S013-ASSEMBLED-CAND-v04 and SHOT-EP005-S019-ASSEMBLED-CAND-v04 were **not created**; the live registry confirms both are absent. There are no audio measurements because no new mix was made.

## 8. Side-effect audit (live readback `ep005/batch1_motion_v04/B1_V04_SIDE_EFFECT_AUDIT_READBACK_v1.json`)

| Item | Value |
|---|---|
| S005_COMPLETE_APPROVED | YES (APPROVED, stored SHA match) |
| S017_COMPLETE_APPROVED | YES (APPROVED, stored SHA match) |
| S013_NEW_KLING_CALLS | 1 |
| S019_NEW_KLING_CALLS | 1 |
| TOTAL_NEW_KLING_CALLS | 2 |
| RETRIES | 0 |
| TOTAL_KNOWN_NEW_SPEND_USD | 0.00 (actual UNKNOWN; not exposed by the provider) |
| S013_RAW_PRESERVED | YES (MOTION-EP005-S013-KLING30T-CAND-v02, REVIEW) |
| S019_RAW_PRESERVED | YES (MOTION-EP005-S019-KLING30T-CAND-v02, REVIEW) |
| S013_V04_CREATED | NO (QC FAIL) |
| S019_V04_CREATED | NO (QC FAIL) |
| S027_UNCHANGED | YES (last update 2026-10-09; all rows APPROVED) |
| S028_UNCHANGED | YES (last update 2026-10-12) |
| S029_UNCHANGED | YES (last update 2026-10-12) |

Nothing else ran or changed:
- no image generation, Flare, Seedance, ElevenLabs or dialogue;
- no Agent-006 or Agent-007;
- no script, manifest or readiness change, and no agent008 code change;
- no billing change, publishing or Anime Clip Farming.

## 9. Rollback
- **S005/S017 approval and the S013 v03/S019 raw rejections:** PATCH the rows back to REVIEW. The prior metadata is in `B1_V04_DECISION_ROWS_READBACK_v1.json`. This should only be done on human instruction.
- **The two v02 raw rows and objects:** these can be deleted on human instruction. Nothing depends on them.

## 10. Status
`EP005_BATCH1_MOTION_RECONCILED_PARTIAL`:
- S005_COMPLETE_APPROVED and S017_COMPLETE_APPROVED; FINISHED_SHOT_COUNT = 5;
- **S013_V04_FAIL (NEW_RED_MARK)** and **S019_V04_FAIL (EXTRA_HAND / CANON_FAIL)**;
- TOTAL_NEW_KLING_CALLS = 2, RETRIES = 0;
- known new spend USD 0.00 (actual UNKNOWN; provider exposes no cost);
- no v04 MP4s.

STOPPED. Next steps for S013 and S019 are a Company Brain decision.
