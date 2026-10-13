# Agent-008 batch driver v0.1 + G04 overlay/treatment certificate chain (2026-10-13)

Mikko & Lumi only. Anime Clip Farming not touched.

Engineering only: 0 provider calls, 0 production writes, 0 production renders, 0 generations.

- **Contract:** `evidence/agent008/batch_driver/AGENT008_BATCH_DRIVER_CONTRACT_v0.1.md`.
- **Code:** `agent008/batch.py`, `agent008/g04chain.py`.
- **Tests:** `agent008/tests/test_batch_driver.py` (24).

## Results
- **Tests:** **205/205 OK** (181 existing, unchanged, plus 24 new). Output: `AGENT008_TEST_OUTPUT_BATCH_DRIVER_v1.txt`.
- **Regression (`REGRESSION_COMPARISON_v1.json`):** compared with the pre-G03 baseline, the G02 still output and deterministic core are identical, and the v0.2 motion MP4, WAV and provenance keys are identical. The driver and chain are additive; no existing module changed.
- **Determinism:** the PLAN_ONLY dry run, run twice, gave an identical plan and `plan_sha256` `d3e6fe5efbc92961f19f67ba49ae8a9f5b1e56aed9910fbebaf81a5b9a458574`. Test 23 shows the same for a synthetic 9-shot batch, manifest SHA included.
- **Synthetic local modes (tests):**
  - LOCAL_RENDER_ONLY: G03 → G02 ×2, byte-identical, QC PASS.
  - LOCAL_PREPARE_ONLY: G04 crop derivation.
  - PROVIDER_PREFLIGHT_ONLY: package frozen, `submitted: false`, socket disabled, no overwrite, prompt approval enforced.
  - G04 chain: G03 and G08 inheritance; stale / missing / chain-broken / index / pin / set mismatches rejected; no re-application.

## First-batch dry run (PLAN_ONLY, live authoritative specs, read-only registry)
Allowlist: S001, S004, S005, S012, S013, S017, S019, S025, S026.

| SHOT_ID | FRAME_FAMILY | CURRENT_BATCH_STATE | blocker | NEXT_REQUIRED_HUMAN_GATE | NEXT_REQUIRED_AUTOMATED_STAGE | DIALOGUE_COUNT | G03_RECORD_COUNT | G08_RECORD_COUNT | event timing | PROVIDER_VIDEO_CALL_REQUIRED | EXPECTED_FINAL_PRODUCTION_PATH |
|---|---|---|---|---|---|---|---|---|---|---|---|
| S001 | F01-MIRROR-OPEN (GENERATE) | WAITING_FOR_BASE_FRAME | FAMILY_FRAME_NOT_GENERATED:F01-MIRROR-OPEN | authorise the base-frame generation (paid) for the family | normalise + hash the generated frame (G04) | 2 | 1 (3 overlays) | 0 | — | YES | frame -> G03 static -> provider preflight -> [spend auth] -> Seedance -> [raw approval] -> motion assembly x2 -> REVIEW |
| S004 | F03-OVERSHOULDER-LUMI (GENERATE) | WAITING_FOR_BASE_FRAME | FAMILY_FRAME_NOT_GENERATED:F03-OVERSHOULDER-LUMI | authorise the base-frame generation (paid) for the family | normalise + hash the generated frame (G04) | 2 | 1 (3 overlays) | 1 (MIRROR-GLINT) | SFX-LUMI-CLUE-CHIME | no | frame -> G03 -> G02 still x2 (glint/pop frame-exact, dialogue G09) -> QC -> REVIEW |
| S005 | F01-MIRROR-OPEN (GENERATE) | WAITING_FOR_BASE_FRAME | FAMILY_FRAME_NOT_GENERATED:F01-MIRROR-OPEN | authorise the base-frame generation (paid) for the family | normalise + hash the generated frame (G04) | 0 | 1 (3 overlays) | 0 | — | no | frame -> G03 -> G02 still x2 (dialogue G09) -> QC -> REVIEW |
| S012 | F03-OVERSHOULDER-LUMI (GENERATE) | WAITING_FOR_BASE_FRAME | FAMILY_FRAME_NOT_GENERATED:F03-OVERSHOULDER-LUMI | authorise the base-frame generation (paid) for the family | normalise + hash the generated frame (G04) | 2 | 1 (2 overlays) | 1 (MIRROR-GLINT) | — | no | frame -> G03 -> G02 still x2 (glint/pop frame-exact, dialogue G09) -> QC -> REVIEW |
| S013 | F01-MIRROR-OPEN (GENERATE) | WAITING_FOR_BASE_FRAME | FAMILY_FRAME_NOT_GENERATED:F01-MIRROR-OPEN | authorise the base-frame generation (paid) for the family | normalise + hash the generated frame (G04) | 0 | 1 (2 overlays) | 0 | — | no | frame -> G03 -> G02 still x2 (dialogue G09) -> QC -> REVIEW |
| S017 | F09-MEDIUM-TWOSHOT-MIRROR-FRONT (GENERATE) | WAITING_FOR_BASE_FRAME | FAMILY_FRAME_NOT_GENERATED:F09-MEDIUM-TWOSHOT-MIRROR-FRONT | authorise the base-frame generation (paid) for the family | normalise + hash the generated frame (G04) | 0 | 1 (1 overlays) | 0 | — | no | frame -> G03 -> G02 still x2 (dialogue G09) -> QC -> REVIEW |
| S019 | F15-MACRO-REFLECTION (DERIVE_CROP) | WAITING_FOR_UPSTREAM | CROP_SOURCE_FAMILY_NOT_APPROVED:F09-MEDIUM-TWOSHOT-MIRROR-FRONT | complete the upstream shot / source approval | derive the base frame once the source is approved | 0 | 1 (1 overlays) | 0 | — | no | frame -> G03 -> G02 still x2 (dialogue G09) -> QC -> REVIEW |
| S025 | F01-MIRROR-OPEN (GENERATE) | WAITING_FOR_BASE_FRAME | FAMILY_FRAME_NOT_GENERATED:F01-MIRROR-OPEN | authorise the base-frame generation (paid) for the family | normalise + hash the generated frame (G04) | 1 | 0 (0 overlays) | 1 (MIRROR-REFLECTION, COMPLETION-POP-ACCENT) | SFX-COMPLETION-POP-v01 | no | frame -> G03 -> G08 reflection -> G02 still x2 (glint/pop frame-exact, dialogue G09) -> QC -> REVIEW |
| S026 | F11-S027-START-REUSE (REUSE_APPROVED_ASSET) | WAITING_FOR_FRAME_APPROVAL | REUSE_BINDING_NOT_APPROVED:FRAME-EP005-S027-BASE-v01 | APPROVE/REJECT the base frame (or the reuse binding) by exact SHA | None | 1 | 0 (0 overlays) | 0 | — | YES | frame -> G03 static -> provider preflight -> [spend auth] -> Seedance -> [raw approval] -> motion assembly x2 -> REVIEW |

**The driver resolves the families as specified:**
- F01 → S001, S005, S013, S025
- F03 → S004, S012
- F09 → S017
- F15 → S019, waiting on F09 approval, then a local crop derivation
- F11 → S026, reusing the approved `FRAME-EP005-S027-BASE-v01`; it waits only on the human reuse-binding approval

## Batch review manifest (dry run): `BATCH_REVIEW_MANIFEST_EXAMPLE_FIRST_BATCH_v1.json`
| Field | Value |
|---|---|
| BATCH_ID | EP005-FIRST-FRAME-BATCH-DRY-RUN-v1 |
| SHOT_COUNT | 9 |
| COMPLETE_COUNT | 0 |
| BLOCKED_COUNT | 0 |
| WAITING_HUMAN_COUNT | 9 |
| WAITING_PROVIDER_COUNT | 0 |
| READY_AUTOMATED_COUNT | 0 |
| FAILED_COUNT | 0 |
| manifest_sha256 | `d44000507b0b1ac95a4583c9500545a2b53056a83a6c45a031e856039e26d23a` |

| SHOT_ID | STATE | QC_STATUS | HUMAN_GATE | PROVIDER_COST | BLOCKER |
|---|---|---|---|---|---|
| S001 | WAITING_FOR_BASE_FRAME | NOT_RUN | authorise the base-frame generation (paid) for the family | None | FAMILY_FRAME_NOT_GENERATED:F01-MIRROR-OPEN |
| S004 | WAITING_FOR_BASE_FRAME | NOT_RUN | authorise the base-frame generation (paid) for the family | None | FAMILY_FRAME_NOT_GENERATED:F03-OVERSHOULDER-LUMI |
| S005 | WAITING_FOR_BASE_FRAME | NOT_RUN | authorise the base-frame generation (paid) for the family | None | FAMILY_FRAME_NOT_GENERATED:F01-MIRROR-OPEN |
| S012 | WAITING_FOR_BASE_FRAME | NOT_RUN | authorise the base-frame generation (paid) for the family | None | FAMILY_FRAME_NOT_GENERATED:F03-OVERSHOULDER-LUMI |
| S013 | WAITING_FOR_BASE_FRAME | NOT_RUN | authorise the base-frame generation (paid) for the family | None | FAMILY_FRAME_NOT_GENERATED:F01-MIRROR-OPEN |
| S017 | WAITING_FOR_BASE_FRAME | NOT_RUN | authorise the base-frame generation (paid) for the family | None | FAMILY_FRAME_NOT_GENERATED:F09-MEDIUM-TWOSHOT-MIRROR-FRONT |
| S019 | WAITING_FOR_UPSTREAM | NOT_RUN | complete the upstream shot / source approval | None | CROP_SOURCE_FAMILY_NOT_APPROVED:F09-MEDIUM-TWOSHOT-MIRROR-FRONT |
| S025 | WAITING_FOR_BASE_FRAME | NOT_RUN | authorise the base-frame generation (paid) for the family | None | FAMILY_FRAME_NOT_GENERATED:F01-MIRROR-OPEN |
| S026 | WAITING_FOR_FRAME_APPROVAL | NOT_RUN | APPROVE/REJECT the base frame (or the reuse binding) by exact SHA | None | REUSE_BINDING_NOT_APPROVED:FRAME-EP005-S027-BASE-v01 |

## Future automatic flow: driver simulation (status-only inventories, PLAN_ONLY, no files)
**Deterministic still (S025):**

| # | after | STATE | human gate | automated stage |
|---|---|---|---|---|
| 1 | start (no frame) | WAITING_FOR_BASE_FRAME | authorise the base-frame generation (paid) for the family | normalise + hash the generated frame (G04) |
| 2 | F01 frame generated -> REVIEW | WAITING_FOR_FRAME_APPROVAL | APPROVE/REJECT the base frame (or the reuse binding) by exact SHA | — |
| 3 | frame APPROVED | WAITING_FOR_G08_RECORD | approve the G08 treatment record measured on the approved frame | apply G08 once approved |
| 4 | G08 record approved | WAITING_FOR_AUDIO_TIMING | approve the event-audio timing (SFX/foley start frames) | — |
| 5 | pop SFX timing approved | WAITING_FOR_DIALOGUE | authorise TTS for the missing lines | bind clips with G09 once approved |
| 6 | Lumi clip generated -> REVIEW | WAITING_FOR_DIALOGUE_APPROVAL | APPROVE/REJECT each clip by exact SHA | bind clips with G09 |
| 7 | Lumi clip APPROVED | READY_FOR_LOCAL_RENDER | — | G03/G08 static stages -> G02 still render x2 -> QC -> REVIEW |
| 8 | LOCAL_RENDER_ONLY produced REVIEW shot | WAITING_FOR_FINAL_SHOT_APPROVAL | APPROVE/REJECT the assembled shot by exact SHA | — |
| 9 | final shot APPROVED | COMPLETE_APPROVED | — | — |

**Provider motion (S001):**

| # | after | STATE | human gate | automated stage |
|---|---|---|---|---|
| 1 | start (no frame) | WAITING_FOR_BASE_FRAME | authorise the base-frame generation (paid) for the family | normalise + hash the generated frame (G04) |
| 2 | F01 frame APPROVED | WAITING_FOR_G03_RECORD | approve the G03 placement record measured on the approved frame | apply G03 once approved |
| 3 | G03 record approved | WAITING_FOR_DIALOGUE | authorise TTS for the missing lines | bind clips with G09 once approved |
| 4 | both clips APPROVED | READY_FOR_PROVIDER_PREFLIGHT | — | G03/G08 static stages -> freeze provider package (no submit) |
| 5 | PROVIDER_PREFLIGHT_ONLY froze the package | WAITING_FOR_PROVIDER_AUTHORISATION | authorise the provider spend (scope, ceiling, balance) | — |
| 6 | spend authorised with ceiling | WAITING_FOR_PROVIDER_AUTHORISATION | authorise the provider spend (scope, ceiling, balance) | — |
| 7 | (future paid mode) submitted | WAITING_FOR_PROVIDER_OUTPUT | — | retrieve + preserve the raw output exactly |
| 8 | raw output retrieved | WAITING_FOR_RAW_MOTION_APPROVAL | APPROVE/REJECT the raw motion by exact SHA | — |
| 9 | raw motion APPROVED | READY_FOR_ASSEMBLY | — | deterministic motion assembly x2 -> QC -> REVIEW |
| 10 | assembly produced REVIEW shot | WAITING_FOR_FINAL_SHOT_APPROVAL | APPROVE/REJECT the assembled shot by exact SHA | — |
| 11 | final shot APPROVED | COMPLETE_APPROVED | — | — |

Human gates stay explicit: the driver stops at every approval and at spend authorisation. Without an authorisation and a spend ceiling, the next state is fixed at `WAITING_FOR_PROVIDER_AUTHORISATION`. Even with both, it stays there with `PAID_MODE_NOT_AVAILABLE_IN_DRIVER_v0.1`.

## First-batch auto-batch readiness
| Item | Value |
|---|---|
| BATCH_DRIVER_STATUS | IMPLEMENTED (PLAN_ONLY, LOCAL_PREPARE_ONLY, LOCAL_RENDER_ONLY, PROVIDER_PREFLIGHT_ONLY; no paid mode) |
| G04_OVERLAY_CHAIN_STATUS | COMPLETE (G03 + G08 inheritance, fail-closed, no pixel re-application) |
| FIRST_BATCH_SHOTS | S001, S004, S005, S012, S013, S017, S019, S025, S026 |
| FIRST_BATCH_FRAME_FAMILIES | F01, F03, F09, F15, F11 |
| FIRST_BATCH_PAID_IMAGE_CALLS | 3 (F01, F03, F09; cost per call UNKNOWN) |
| FIRST_BATCH_PROVIDER_VIDEO_SHOTS | S001, S026 |
| FIRST_BATCH_DETERMINISTIC_STILL_SHOTS | S004, S005, S012, S013, S017, S019, S025 |
| FIRST_BATCH_TOTAL_DIALOGUE_LINES | 8 (Mikko 2: S001, S026; Lumi 6: S001, S004×2, S012×2, S025) |
| FIRST_BATCH_G03_RECORDS_REQUIRED | 7 (S001, S004, S005, S012, S013, S017, S019) |
| FIRST_BATCH_G08_RECORDS_REQUIRED | 3 (S004 glint, S012 glint, S025 reflection + pop) |
| Event-timing approvals | 2 (S004 clue chime, S025 completion pop) |
| FIRST_BATCH_CAN_AUTOMATICALLY_ADVANCE_AFTER_FRAME_APPROVAL | **YES**, for every deterministic stage. See below. |

**What "advance automatically" means after a frame is approved:**
- The driver recomputes each shot and runs the G04 derivation (S019).
- It applies the G03/G08 static stages, binds clips, renders the stills twice, runs QC and builds the review manifest.
- It then stops at each explicit gate listed below. No gate is skipped.

**REMAINING_HUMAN_GATES:**
1. Authorise the 3 paid images (scope, ceiling, balance).
2. Approve each normalised frame by SHA, and the S026 reuse binding.
3. Approve 7 G03 and 3 G08 records, measured on the approved frames.
4. Approve the 2 event timings.
5. Authorise the TTS batch (8 lines) and approve each clip.
6. Authorise each Seedance generation (S001, S026) and approve the raw motion.
7. Approve each assembled shot by exact SHA.
8. Authorise production storage and registry writes for the batch outputs.

## Non-regression
- **Stored assets:** the 11 approved S027/S028/S029 assets (assembled shots, base frames, raw motions, dialogue) were re-hashed from storage. Each is equal to its registry SHA and APPROVED (`NONREGRESSION_S027_S029_STORED_REHASH_v1.json`).
- **Production fingerprints are unchanged:**

  | Object | Fingerprint |
  |---|---|
  | scripts | 5:649d63f9… |
  | manifests | 12:cefb8fa2… |
  | readiness | 8:f5c646ee… |
  | resolution items | 86:ce5ac459… |
  | registry | 34:d845548f… |
  | storage | 30:16bb5c35… |

- **Calls:** zero provider, Higgsfield, ElevenLabs, Seedance, Agent-006, Agent-007, generations or production writes. Registry and readiness were read via GET only.

## Rollback
Revert the commit. All additions are new files, and no existing module was modified.
