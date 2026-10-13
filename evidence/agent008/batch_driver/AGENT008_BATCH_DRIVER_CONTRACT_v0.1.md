# AGENT008_BATCH_DRIVER_v0.1 + G04 certificate chain: contract

- **Modules:** `agent008/batch.py` (driver) and `agent008/g04chain.py` (G04 certificate chain). Both are part of Agent-008; no new agent was created.
- **Tests:** `agent008/tests/test_batch_driver.py` (24).

## 1. Input
- **`batch`:** `{batch_id, mode, shot_ids}`.
  - `shot_ids` is an explicit, non-empty, duplicate-free list. Wildcard, `ALL`, empty, a string, or `None` fail closed (`BATCH_ALLOWLIST_INVALID`).
  - Execution is refused for any shot not in the list (`BATCH_SHOT_NOT_ALLOWED`). Inventory entries for other shots are never read or touched.
- **`specs`:** the authoritative Agent-008 specs (`resolve_episode` of the APPROVED readiness).
- **`families`:** per shot `{family_id, kind, source, provider_motion[, crop, scale]}`. The kinds are `GENERATE`, `REUSE_APPROVED_ASSET`, `DERIVE_CROP` and `DERIVE_MOTION_END` (from the accepted base-frame preflight).
- **`inventory`:** approved and pending artifacts read from authoritative records. Per shot:
  - `final`, `frame`, `g03_record`, `g08_record`, `timing`, `dialogue[]`
  - `motion{prompt, prompt_record, preflight_sha256, authorisation{human_approved, spend_ceiling_usd}, submitted, result, certificate}`
  - plus the shared tables `__families__` (family frames) and `__assets__` (approved reusable assets).
  - The driver never writes it.

## 2. Resolved per shot
- SHOT_ID
- AUTHORITATIVE_SPEC (status, canonical SHA, frames, duration)
- PRODUCTION_MODE (G02_STILL / PROVIDER_MOTION / BLOCKED)
- BASE_FRAME_REQUIREMENT
- G03_REQUIREMENT (overlays, record_required, satisfied_by_inherited_certificate)
- G08_REQUIREMENT (same fields)
- G06 / G07 / G11_REQUIREMENT
- DIALOGUE_REQUIREMENTS
- AUDIO_REQUIREMENTS (beds, events, event_timing_required)
- PROVIDER_MOTION_REQUIRED
- UPSTREAM_CONTINUITY_DEPENDENCIES
- CURRENT_BLOCKERS
- OUTSTANDING (every unmet input)
- STATE, CATEGORY, NEXT_REQUIRED_HUMAN_GATE, NEXT_REQUIRED_AUTOMATED_STAGE

## 3. State machine
The ladder is deterministic, and the earliest unmet requirement wins. It is computed only from the inputs and stores nothing. Tests 23 and the live dry run show two runs give an identical plan and SHA.

1. `FAILED`: spec missing, SHA mismatch (a supplied local file disagrees with the recorded SHA), unexpected production state, human rejection, provider failure, missing upstream certificate, upstream cycle, undeclared family.
2. `COMPLETE_APPROVED`: the final shot is APPROVED. It is **never reopened**: no stage runs in any mode.
3. `BLOCKED_ENGINEERING`: G11 (spec BLOCKED), G07 (`spec.IN_SHOT_CUT_SHOTS`), G06 (S024), or an upstream continuity source that is engineering-blocked.
4. `WAITING_FOR_FINAL_SHOT_APPROVAL`: an assembled REVIEW shot exists.
5. **Base frame:**
   - `WAITING_FOR_BASE_FRAME`: the family frame is not generated (GENERATE).
   - `WAITING_FOR_UPSTREAM`: the reuse, crop or motion source is not approved.
   - `READY_FOR_FRAME_DERIVATION`: the source is approved; G04 crop or G04 certificate chain runs locally.
   - `WAITING_FOR_FRAME_APPROVAL`: the frame, family frame or reuse binding is in REVIEW.
6. `WAITING_FOR_G03_RECORD`: overlays are active and not inherited, and the record is not approved.
7. `WAITING_FOR_G08_RECORD`: treatments are assigned and the record is not approved.
8. `WAITING_FOR_AUDIO_TIMING`: an event SFX or foley timing is not approved.
9. `WAITING_FOR_DIALOGUE` / `WAITING_FOR_DIALOGUE_APPROVAL`.
10. **Still path:** `READY_FOR_LOCAL_RENDER`.
11. **Motion path:**
    - `READY_FOR_PROVIDER_PREFLIGHT`
    - `WAITING_FOR_PROVIDER_AUTHORISATION`: blocker `PROVIDER_AUTHORISATION_MISSING`, `SPEND_CEILING_MISSING`, or `PAID_MODE_NOT_AVAILABLE_IN_DRIVER_v0.1`
    - `WAITING_FOR_PROVIDER_OUTPUT`
    - `WAITING_FOR_RAW_MOTION_APPROVAL`
    - `READY_FOR_ASSEMBLY`

**Categories:** COMPLETE, BLOCKED, HUMAN, PROVIDER, AUTOMATED, FAILED. Every state names its next human gate and its next automated stage.

## 4. Fail-closed governance
- **Independence:** each shot is evaluated and executed independently in its own try/except. Test 3 shows the result for a good shot is identical with and without a failing neighbour.
- **No retry:** exactly one attempt per stage (`attempts: 1`). A failure is terminal: no retry, no replacement candidate, no provider fallback. `PROVIDER_FAILED_NO_RETRY` and `REJECTED_BY_HUMAN_NO_AUTOMATIC_REPLACEMENT` are both terminal.
- **No provider route:** the driver imports no HTTP or provider module and has no submit code.

## 5. Modes
| Mode | Runs | Writes |
|---|---|---|
| PLAN_ONLY | resolution only | **nothing**; a `work_dir` is refused (`PLAN_ONLY_NO_WRITES`) |
| LOCAL_PREPARE_ONLY | G04 crop / G04 certificate chain for READY_FOR_FRAME_DERIVATION; G03 + G08 static stages for READY shots | scratch `work_dir` only |
| LOCAL_RENDER_ONLY | G03/G08 static → G02 `compose_still_shot` ×2 → byte-identity + automatic QC (fails `QC_NON_DETERMINISTIC` / `QC_FAILED`) | scratch `work_dir` only |
| PROVIDER_PREFLIGHT_ONLY | static stages → frozen package (`PREPARED_NOT_SUBMITTED`; request body + SHA; max 1 generation, no retry / alternate / fallback); needs an approved motion prompt | scratch `work_dir` only; **never submits** |

There is no paid mode. Any other mode fails `BATCH_MODE_NOT_AUTHORISED`. Production storage and registry writes need a future, explicitly authorised stage.

## 6. G04_OVERLAY_CHAIN (`g04chain.derive_certified_frame`)
**Input:**
- the approved motion source
- the frame index
- the target spec
- the certificate: `motion_asset_id`, `motion_sha256`, `motion_source_frame_sha256`, `source_shot_id`, `declared_frame_index`, optional `frame_rgb_sha256`, plus the G03 `overlays_composited` and optional G08 `treatments_composited` of the motion's base frame
- the requested `inherit` set

**Fails closed on:**
- missing certificate (`CERTIFICATE_MISSING`, `CERTIFICATE_INCOMPLETE`)
- a certificate for other bytes or another asset (`CERTIFICATE_STALE`)
- an undeclared or mismatched frame index (`CERTIFICATE_FRAME_INDEX_UNDECLARED` / `_MISMATCH`)
- a broken G03 → G08 → motion chain (`CERTIFICATE_CHAIN_INVALID`)
- a requested set different from the source or from the target shot's contract (`CERTIFICATE_SET_MISMATCH`)
- derived pixels not matching the pinned frame (`DERIVED_FRAME_MISMATCH`, from G04)

All of these are checked **before** any output is written.

**Output:**
- The unchanged G04 lossless PNG (REVIEW).
- `<shot>_G04_CERTIFICATE_CHAIN.json`: SOURCE_ASSET_ID, SOURCE_SHA, SOURCE_FRAME_INDEX, DERIVED_FRAME_SHA, G03_CERTIFICATES_INHERITED, G08_CERTIFICATES_INHERITED, CERTIFICATE_SOURCE_SHA, DERIVATION_METHOD, plus the re-issued `overlays_composited` / `treatments_composited` bound to the derived frame SHA with `inherited_from`.
- `pixels_reapplied: {g03: false, g08: false}`.

**Consumers:**
- **G02 still path:** accepts the inherited overlay set.
- **Motion gate:** accepts the inherited overlay set plus the reflection certificate.
- **Re-application is refused:** re-running G03 fails `OVERLAY_ALREADY_COMPOSITED`; re-running G08 fails `TREATMENT_DUPLICATE_INVOCATION`.
- **Driver:** a frame with inherited certificates needs no G03 record.

**Limitation (documented):** a *still* shot that inherits a reflection *and* adds timed treatments would need a record bound to the derived frame, and fails closed (`TREATMENT_RECORD_HASH_MISMATCH`). No EP005 shot needs this: S008 has no treatments, and S011 is motion.

## 7. Batch review manifest (`review_manifest`)
- **Batch fields:** BATCH_ID, DRIVER, MODE, PLAN_SHA256, SHOT_COUNT, COMPLETE_COUNT, BLOCKED_COUNT, WAITING_HUMAN_COUNT, WAITING_PROVIDER_COUNT, READY_AUTOMATED_COUNT, FAILED_COUNT.
- **Per shot:** SHOT_ID, STATE, CATEGORY, INPUT_SHAS, OUTPUT_SHAS, QC_STATUS, HUMAN_GATE, NEXT_AUTOMATED_STAGE, PROVIDER_COST, BLOCKER, OUTSTANDING.
- **Integrity:** a `manifest_sha256` (canonical).
