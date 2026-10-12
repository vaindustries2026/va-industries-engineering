# Agent-008 G03: deterministic overlay placement (2026-10-12)

Mikko & Lumi only. Anime Clip Farming not touched.

Engineering only: 0 provider calls, 0 production writes, 0 renders of production shots. S027, S028 and S029 are untouched.

## 1. Requirement audit (read-only, live authoritative lineage)
- **Script:** `evidence/agent008/g03/g03_requirement_audit.py`.
- **Output:** `G03_REQUIREMENT_AUDIT_v1.json`.
- **Sources:**
  - Full `manifest_json` of APPROVED manifest `0325d35c` (GET).
  - The Agent-008 specs of APPROVED readiness `69bff641`.
  - The governed overlay rows.

**G03_DEPENDENT_SHOTS = 18** (verified; equal to the checkpoint): S001, S002, S003, S004, S005, S006, S007, S008, S010, S011, S012, S013, S014, S016, S017, S018, S019, S020.

S009, S015 and S021 also carry overlays, but each removes one inside the shot. That needs a cloth-occlusion design (G11), not placement; the spec already fails closed on them.

| Shot | Path | Overlays (role) | Frame range | Reflection in usage | Placement / scale / anchor | Opacity / z-order | Removal |
|---|---|---|---|---|---|---|---|
| S001 | motion base-frame pre-composite | CHEEK (COMPOSITING), MOUTH (COMPOSITING), NOSE (COMPOSITING) | 0-143 | yes | G03_SPEC_GAP | not declared | none |
| S002 | motion base-frame pre-composite | CHEEK (STATE_MARK), MOUTH (STATE_MARK), NOSE (STATE_MARK) | 0-83 | yes | G03_SPEC_GAP | not declared | none |
| S003 | still | CHEEK (COMPOSITING), MOUTH (COMPOSITING), NOSE (COMPOSITING) | 0-83 | yes | G03_SPEC_GAP | not declared | none |
| S004 | still | CHEEK (CLUE_HIGHLIGHT), MOUTH (CLUE_HIGHLIGHT), NOSE (CLUE_HIGHLIGHT) | 0-119 | yes | G03_SPEC_GAP | not declared | none |
| S005 | still | CHEEK (OTHER), MOUTH (OTHER), NOSE (OTHER) | 0-95 | no | G03_SPEC_GAP | not declared | none |
| S006 | still | CHEEK (COMPOSITING), MOUTH (COMPOSITING), NOSE (COMPOSITING) | 0-59 | yes | G03_SPEC_GAP | not declared | none |
| S007 | motion base-frame pre-composite | CHEEK (STATE_MARK), MOUTH (STATE_MARK), NOSE (STATE_MARK) | 0-119 | no | G03_SPEC_GAP | not declared | none |
| S008 | still | CHEEK (OTHER), MOUTH (OTHER), NOSE (OTHER) | 0-71 | no | G03_SPEC_GAP | not declared | none |
| S009 | blocked (G11) | CHEEK (COMPOSITING), MOUTH (COMPOSITING), NOSE (COMPOSITING) | transition | no | G03_SPEC_GAP | not declared | in-shot removal → G11 |
| S010 | motion base-frame pre-composite | MOUTH (CLUE_HIGHLIGHT), NOSE (CLUE_HIGHLIGHT) | 0-119 | yes | G03_SPEC_GAP | not declared | none |
| S011 | motion base-frame pre-composite | MOUTH (STATE_MARK), NOSE (STATE_MARK) | 0-119 | no | G03_SPEC_GAP | not declared | none |
| S012 | still | MOUTH (CLUE_HIGHLIGHT), NOSE (CLUE_HIGHLIGHT) | 0-119 | yes | G03_SPEC_GAP | not declared | none |
| S013 | still | MOUTH (OTHER), NOSE (OTHER) | 0-95 | yes | G03_SPEC_GAP | not declared | none |
| S014 | motion base-frame pre-composite | MOUTH (CLUE_HIGHLIGHT), NOSE (CLUE_HIGHLIGHT) | 0-95 | no | G03_SPEC_GAP | not declared | none |
| S015 | blocked (G11) | MOUTH (COMPOSITING), NOSE (COMPOSITING) | transition | no | G03_SPEC_GAP | not declared | in-shot removal → G11 |
| S016 | motion base-frame pre-composite | NOSE (OTHER) | 0-95 | yes | G03_SPEC_GAP | not declared | none |
| S017 | still | NOSE (COMPOSITING) | 0-95 | yes | G03_SPEC_GAP | not declared | none |
| S018 | still | NOSE (CLUE_HIGHLIGHT) | 0-143 | yes | G03_SPEC_GAP | not declared | none |
| S019 | still | NOSE (OTHER) | 0-119 | yes | G03_SPEC_GAP | not declared | none |
| S020 | motion base-frame pre-composite | NOSE (CLUE_HIGHLIGHT) | 0-95 | yes | G03_SPEC_GAP | not declared | none |
| S021 | blocked (G11) | NOSE (COMPOSITING) | transition | no | G03_SPEC_GAP | not declared | in-shot removal → G11 |

**Columns this table leaves out:**
- **Overlay asset:**
  - CHEEK = `OVERLAY-EP005-BERRY-SMUDGE-CHEEK-v01` (`e2fc6426`, b2c735f2…78ac)
  - MOUTH = `…-MOUTH-v01` (`b960c11c`, df7c2adb…7b0e)
  - NOSE = `…-NOSE-v01` (`dfaa3b89`, c1169127…0bc1)
  - All three are APPROVED OVERLAY_VFX/BERRY_SMUDGE_OVERLAY. Stored bytes were re-verified by GET.
- **Other governed behaviour:** the per-overlay `usage` text is in the JSON. It includes:
  - "independently removable"
  - "preserve correct mirror reversal"
  - "readable and unobscured" (S014)
  - "no removal, animation, glow, sparkle" (S013)

**G03_SPEC_GAP.** No authoritative record defines x/y, scale or a numeric anchor for any shot; the manifest names anatomy only. No approved base frame exists for S001–S026, so nothing can be measured yet. The gap is closed by a per-base-frame, human-approved **placement record** (the recorded G03 design). Opacity and z-order are not declared, so G03 governs full opacity only and forbids overlap.

## 2. Contract (locked)
`evidence/agent008/g03/G03_CONTRACT_v1.md` (`AGENT008_G03_OVERLAY_PLACEMENT_v1`).

| Feature | Decision |
|---|---|
| overlay image input | supported (governed, approved, SHA-bound) |
| multiple overlays | supported |
| one per surface FACE / REFLECTION | supported |
| mirror reversal | enforced on REFLECTION |
| x/y | integer base-frame pixels |
| anchor | CENTER only |
| deterministic width scale | aspect kept, no upscale |
| rotation | supported (recorded design) |
| frame range | whole shot only, declared and checked |
| opacity | 1.0 only |
| z-order | none (overlap rejected) |
| clipping | none |
| removal at a frame | rejected (G11) |
| inputs | immutable |
| output | a new REVIEW PNG (proposed SHOT_FRAME/DERIVED_FRAME) |

## 3. Implementation
- **`agent008/overlay.py`** (new). Contains `place_overlays`, `validate_record`, `validate_placement`, `check_overlay_assets`, `overlay_layer` and `precomposited_overlay_set`. It reuses the existing `compositor`, `media` and `derive` PNG primitives.
- **`agent008/still.py`:** the G02 still path accepts a shot with overlays only from an approved G03 DERIVED_FRAME whose composited set matches. Otherwise it fails closed with the same `STILL_OVERLAYS_NEED_G03_ANCHORS` as before.
- **`agent008/motion/compose.py`:** optional `overlays_composited=`. Persistent overlays pre-composited into the motion base frame are accepted, bound to the request's source-frame SHA. Treatments still fail closed.
- No new agent, provider, dependency or schema.

## 4. Tests: `agent008/tests/test_g03.py` (22 new)
| # | Test | Covers |
|---|---|---|
| 1 | G01 | valid placement |
| 2 | G02 | exact pixel position, with every other pixel unchanged |
| 3 | G03 | exact deterministic scale, checked against an independent scale and the no-upscale rule |
| 4 | G04 | opacity: full only |
| 5 | G05 | frame range, undeclared timing, per-overlay windows/removal |
| 6 | G06 | order independence, z-order rejected, overlap rejected |
| 6b | G06b | mirror reversal pixels, mirror rule, rotation determinism and bounds |
| 7 | G07 | SHA mismatches: overlay, record overlay SHA, base frame, edited record, record for another frame |
| 8 | G08 | unapproved overlay / wrong type / base frame / record |
| 9 | G09, G09b | missing overlay, missing file, unplaced overlay, empty record |
| 10 | G10 | invalid coordinates, out of bounds, frame size |
| 11 | G11 | invalid scale |
| 12 | G12 | invalid opacity |
| 13 | G13 | unsupported anchor / surface / fields / contract / shot |
| 14 | G14 | source immutability (SHA and mtime), no overwrite, no double composite |
| 15 | G15 | two-run determinism (PNG, core, provenance) |
| 16 | G16 | no unexpected overlays: extra or undeclared overlays, duplicates, untouched pixels, clean-reveal refusal |
| — | G17 | no network or provider |
| — | G18, G19 | the G03 frame feeds the G02 still path (two runs identical); mismatched frames rejected |
| — | G20 | motion base-frame pre-composite gate |

**Full suite: 160/160 OK** (138 existing, unchanged, plus 22 new). Output: `AGENT008_TEST_OUTPUT_G03_v1.txt`.

## 5. Determinism proof: `G03_DETERMINISM_PROOF_v1.json` (PASS)
- **Setup:** synthetic fixture with 4 placements, including a mirrored REFLECTION. Run straight and rotated, two runs each.
- **Result:** the PNG SHA, RGB SHA, deterministic core and downstream G02 still MP4/WAV/core are all identical. Base frame and overlays are unchanged.
  - Straight PNG `c7bc35ff…0e20`.
  - Rotated PNG `64fa5ced…0f4c`.
- **Regression (`G03_REGRESSION_COMPARISON_v1.json`):** the pre/post-change G02 still output and deterministic core are identical. The v0.2 motion MP4, WAV and provenance keys are identical.

## 6. Live-spec read-only validation and updated matrix
- **Script:** `g03_live_spec_validation.py`.
- **Output:** `G03_LIVE_SPEC_VALIDATION_AND_MATRIX_v1.json`.
- **Method:**
  - Overlay governance was applied to the live identities, and the stored bytes were GET-verified. All three PASS, with alpha present. Trimmed sizes are CHEEK 1356×637, MOUTH 1380×568, NOSE 885×947.
  - The downstream gate was run in memory with the overlay set a G03 frame would carry.
  - Nothing was composited or written to production.

| Shot | G03 status | Other code blockers | Missing base frame | Missing dialogue | Provider motion | Code-ready once inputs exist | Upstream continuity blocker |
|---|---|---|---|---|---|---|---|
| S001 | SUPPORTED | — | yes: F-MIRROR-OPEN, NEEDS_NEW_SHOT_FRAME | 2 lines | yes | YES | — |
| S002 | SUPPORTED | — | yes: F-MEDIUM-TWOSHOT, CAN_DERIVE_DETERMINISTICALLY | 1 line | yes | YES | — |
| S003 | SUPPORTED | — | yes: F-OVERSHOULDER-MIRROR, NEEDS_NEW_SHOT_FRAME | 1 line | no | YES | — |
| S004 | SUPPORTED | G08 | yes: F-OVERSHOULDER-MIRROR, CAN_DERIVE_DETERMINISTICALLY | 2 lines | no | no | — |
| S005 | SUPPORTED | — | yes: F-OVERSHOULDER-MIRROR, CAN_DERIVE_DETERMINISTICALLY | 0 lines | no | YES | S004 |
| S006 | SUPPORTED | G08 | yes: F-FACE-MIRROR-POINT, NEEDS_NEW_SHOT_FRAME | 1 line | yes | no | — |
| S007 | SUPPORTED | G08(motion) | yes: F-CHEEK-CLOTH, NEEDS_NEW_SHOT_FRAME | 2 lines | yes | no | — |
| S008 | SUPPORTED | — | yes: F-CHEEK-CLOTH, CAN_DERIVE_DETERMINISTICALLY | 0 lines | no | YES | S007 |
| S009 | N/A (G11 shot) | G11 | yes: F-CHEEK-CLOTH, BLOCKED | 0 lines | no | no | — |
| S010 | SUPPORTED | G08(motion) | yes: F-FACE-MIRROR, NEEDS_NEW_SHOT_FRAME | 1 line | yes | no | — |
| S011 | SUPPORTED | G08(motion) | yes: F-FACE-MIRROR, CAN_DERIVE_DETERMINISTICALLY | 0 lines | yes | no | S010 |
| S012 | SUPPORTED | G08 | yes: F-FACE-MIRROR, CAN_DERIVE_DETERMINISTICALLY | 2 lines | no | no | — |
| S013 | SUPPORTED | — | yes: F-FACE-MIRROR, CAN_DERIVE_DETERMINISTICALLY | 0 lines | no | YES | S012 |
| S014 | SUPPORTED | G08(motion) | yes: F-MOUTH-CLOTH, NEEDS_NEW_SHOT_FRAME | 1 line | yes | no | — |
| S015 | N/A (G11 shot) | G11 | yes: F-MOUTH-CLOTH, BLOCKED | 0 lines | no | no | — |
| S016 | SUPPORTED | — | yes: F-FACE-MIRROR, CAN_DERIVE_DETERMINISTICALLY | 1 line | yes | YES | — |
| S017 | SUPPORTED | — | yes: F-MEDIUM-TWOSHOT, CAN_DERIVE_DETERMINISTICALLY | 0 lines | no | YES | — |
| S018 | SUPPORTED | G07, G08 | yes: F-MACRO-REFLECTION, NEEDS_NEW_SHOT_FRAME | 2 lines | no | no | — |
| S019 | SUPPORTED | — | yes: F-MACRO-REFLECTION, CAN_DERIVE_DETERMINISTICALLY | 0 lines | no | YES | S018 |
| S020 | SUPPORTED | — | yes: F-NOSE-CLOTH, NEEDS_NEW_SHOT_FRAME | 1 line | yes | YES | — |
| S021 | N/A (G11 shot) | G11 | yes: F-NOSE-CLOTH, BLOCKED | 0 lines | no | no | — |
| S022 | NOT_REQUIRED | — | yes: F-NOSE-CLOTH, CAN_DERIVE_DETERMINISTICALLY | 1 line | yes | YES | S021 |
| S023 | NOT_REQUIRED | — | yes: F-MEDIUM-TWOSHOT, CAN_DERIVE_DETERMINISTICALLY | 0 lines | no | YES | S021 |
| S024 | NOT_REQUIRED | G06 | yes: F-MIRROR-OPEN, CAN_DERIVE_DETERMINISTICALLY | 0 lines | no | no | — |
| S025 | NOT_REQUIRED | G08 | yes: F-MIRROR-OPEN, CAN_DERIVE_DETERMINISTICALLY | 1 line | no | no | — |
| S026 | NOT_REQUIRED | — | yes: F-MEDIUM-TWOSHOT, NEEDS_NEW_SHOT_FRAME | 1 line | yes | YES | — |

**Notes:**
- **Newly found:** S007, S010, S011 and S014 carry `TREATMENT-EP005-MIRROR-REFLECTION-v01` on provider motion. The motion gate rejects it (`MOTION_TREATMENTS_NEED_TRACKING_V02`), so they are G08-blocked too. Earlier matrices listed only G03 for them.
- **S006:** the spec has `video_generation_required=false`, but the Batch 0C plan says motion. Either way it carries the reflection treatment, so G08 applies.
- **Base frames:** every remaining shot still lacks an approved base frame. Each G03 shot also needs an approved placement record, which can only be written once that frame exists.

## 7. Factory impact
| Measure | Value |
|---|---|
| G03_DEPENDENT_SHOTS_BEFORE | 18 |
| G03_DEPENDENT_SHOTS_NOW_SUPPORTED | 18 |
| SHOTS_STILL_BLOCKED_BY_G03 | 0 |
| TOTAL_REMAINING_SHOTS | 26 |
| SHOTS_WITH_ALL_CODE_PATHS_SUPPORTED_AFTER_G03 | **13** (was 3: S022, S023, S026): S001, S002, S003, S005, S008, S013, S016, S017, S019, S020, S022, S023, S026 |
| SHOTS_STILL_BLOCKED_BY_G06 | 1: S024 |
| SHOTS_STILL_BLOCKED_BY_G07 | 1: S018 |
| SHOTS_STILL_BLOCKED_BY_G08 | 9: S004, S006, S007, S010, S011, S012, S014, S018, S025 |
| SHOTS_STILL_BLOCKED_BY_G11 | 3: S009, S015, S021 |
| SHOTS_BLOCKED_ONLY_BY_MISSING_ASSETS_OR_DIALOGUE | 13 (the same 13) |

**Dependency order.** Six of the 13 begin from the end frame of a code-blocked shot:

| Shot | Waits on | Because |
|---|---|---|
| S005 | S004 | G08 |
| S008 | S007 | G08 |
| S013 | S012 | G08 |
| S019 | S018 | G07/G08 |
| S022 | S021 | G11 |
| S023 | S022, then S021 | G11 |

**Code-ready and dependency-clear now: 7**: S001, S002, S003, S016, S017, S020, S026.

The inputs these 7 still need:
- base frames
- placement records
- 7 dialogue lines
- planned provider calls: about 4 image, 5 video, 4 Mikko TTS and 3 Lumi TTS

## 8. Next-batch recommendation
| Option | Shots unlocked | Engineering | Provider cost | Dependency order | Risk |
|---|---|---|---|---|---|
| A. Batch missing dialogue (20 lines) | 0 by itself; every dialogue shot also lacks base frames or code | none | 20 TTS calls (low) | not first: lines for G08-blocked shots would sit unused | low; clips could wait months |
| **B. G08 treatments (glint, pop accent, mirror reflection; still path + pre-composite on motion base frames)** | **8 fully** (S004, S006, S007, S010, S011, S012, S014, S025). Code-ready goes 13 → **21/26**. Clears the upstream chain for S005, S008, S011, S013: dependency-clear goes 7 → **18** | medium; primitives exist and are bounds-tested since Phase 0 (`treatments.py`, `compositor.brightness_pulse`, reflection primitives), not yet wired into G02 or the motion base frame | **$0** | first in the chain for Act 1 (S004 → S005, S007 → S008, S010 → S011, S012 → S013) | low: deterministic, locally testable |
| C. G11 tracked removal | 3 (+S022/S023 via the chain = 5) | high; needs a human design decision (masked transition on cloth-occluded frames) | $0 code; motion review likely | needed, but after G08 | high |
| D. Produce S026 | 1 | none | ~$3.40 video + image + 1 TTS | fine (precedes S027) | provider risk; uses spend while the factory is still missing capabilities |
| E. Approved family base frames (9 F-* families; 9 shots need image generation) | prerequisite for all 26 | none | paid image calls | needed before any production | must follow capability work to avoid regenerating frames |

**RECOMMENDATION: B, implement G08.**
- It is the largest remaining shared code blocker: 9 shots, 8 fully unlocked.
- It costs nothing and fits `FACTORY_CAPABILITY_FIRST`.
- It is first in the dependency order for the Act-1 chain.
- It leaves only G06 (1 shot), G07 (1) and G11 (3) open.

Afterwards the natural sequence is:
1. E: family base frames plus G03 placement records.
2. A: dialogue batch.
3. G06/G07.
4. A human G11 design decision.

Not executed.

## 9. Non-regression
- **Stored assets:** the S027/S028/S029 assembled shots, base frames, raw motions and dialogue clips were re-hashed from storage. All are equal to their registry SHAs and APPROVED, with updated_at unchanged. Details: `G03_NONREGRESSION_S027_S029_STORED_REHASH_v1.json`.
- **Production fingerprints are unchanged:**

  | Object | Fingerprint |
  |---|---|
  | scripts | 5:649d63f9… |
  | manifests | 12:cefb8fa2… |
  | readiness | 8:f5c646ee… |
  | resolution items | 86:ce5ac459… |
  | registry | 34 rows; outside S028/S029 899d7f33… |
  | storage | 30:16bb5c35… |

- **Calls:** zero provider, ElevenLabs, Higgsfield, Seedance, Agent-006, Agent-007, production writes, uploads or registrations.
- **Reads:** the three overlay objects were read (GET) into the scratchpad only.

## Rollback
Revert the commit. G03 is additive. The still and motion paths fall back to the previous fail-closed behaviour, and no production state changed.
