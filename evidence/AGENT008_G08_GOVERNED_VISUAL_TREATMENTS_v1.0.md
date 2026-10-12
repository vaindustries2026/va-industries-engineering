# Agent-008 G08: governed visual treatments (2026-10-12)

Mikko & Lumi only. Anime Clip Farming not touched.

Engineering only: 0 provider calls, 0 production writes, 0 production renders. S027, S028 and S029 are untouched.

## 1. Requirement audit (read-only, live authoritative lineage)
- **Script:** `evidence/agent008/g08/g08_requirement_audit.py`.
- **Output:** `G08_REQUIREMENT_AUDIT_v1.json`. Per shot it records treatment type, purpose, frame range, visual source, timing, placement, mirror behaviour, compositing, current code support, spec gaps and the manifest QC evidence.

**G08_DEPENDENT_SHOTS = 9 (verified):** S004, S006, S007, S010, S011, S012, S014, S018, S025.

| Shot | Path | Treatments | Authoritative timing / purpose | Spec gaps (G08_SPEC_GAP) |
|---|---|---|---|---|
| S004 | still (held pose approved) | MIRROR_GLINT | synced with the clue chime (`SFX-LUMI-CLUE-CHIME`), near the selected cheek, complete before S005 | glass region, glint centre/size/start |
| S006 | motion (Batch 0C plan) | MIRROR_REFLECTION | cheek mark clearly connected to its reflection; glass clean | glass, reflection mode/mapping |
| S007 | motion | MIRROR_REFLECTION | face marks reflected; glass clean | glass, mode/mapping |
| S010 | motion | MIRROR_REFLECTION | clean cheek + two marks in the reflection; glass clean | glass, mode/mapping |
| S011 | motion | MIRROR_REFLECTION | readable reflection, clear cheek + two marks | glass, mode/mapping |
| S012 | still (held) | MIRROR_GLINT | at the reflected mouth-area clue after the mirror angle; finishes in the shot | glass, glint centre/size/start |
| S014 | motion | MIRROR_REFLECTION | glass clean while showing the reflection | glass, mode/mapping |
| S018 | still (held) + G07 cut | MIRROR_GLINT | once, in the macro part, ending before S019 | glass, glint, cut frame (G07) |
| S025 | still (held), CLEAN REVEAL | MIRROR_REFLECTION + COMPLETION_POP | clean bright reflection; pop synced to `SFX-COMPLETION-POP-v01`; zero overlays | glass, mode/mapping, pop start |

**Current code support before G08:**
- G02 rejected any treatment (`STILL_TREATMENTS_NEED_G08`).
- Motion rejected any treatment (`MOTION_TREATMENTS_NEED_TRACKING_V02`).
- The primitives existed only in the Phase-0 stand-in render.

**G08_TREATMENT_TYPES_REQUIRED = MIRROR_GLINT, MIRROR_REFLECTION, COMPLETION_POP_ACCENT (bloom).**
- CLEAN_REVEAL is a state rule (zero overlays), not a separate treatment.
- No other treatment exists in the approved manifest.

## 2. Contract (locked): `evidence/agent008/g08/G08_CONTRACT_v1.md`
The contract file defines:
- input frame and SHA
- treatment identity
- the human-approved treatment record (canonical SHA, bound to shot and frame)
- parameters, frame windows and glass mask rules
- mirror transformation rules
- deterministic timing and pixels
- provenance, output asset type and REVIEW status

It also carries the **G08_MIRROR_REFLECTION_PIPELINE**, the glint contract, the completion / clean-reveal contract, the **S018_REQUIRED_OPERATION_ORDER** and every fail-closed code.

**Operation order:** base frame → G03 overlays → G08 reflection (static) → [G07 segments, later] → G08 glint → G08 pop.

**S018_REQUIRED_OPERATION_ORDER:**
1. Segment A: frame A + G03.
2. Segment B: frame B + G03.
3. G08 glint, one window entirely inside segment B (`plan_timed(segment=…)`).
4. G07 frame-exact concatenation at the cut, then audio.

Until G07 exists, S018 is refused by the still path (`STILL_IN_SHOT_CUT_NEEDS_G07`).

## 3. Implementation
- **`agent008/g08.py`** (new):
  - `apply_reflection`: static stage, PRESERVE certificate or COMPOSITE frame.
  - `plan_timed` / `render_frame`: glint and pop.
  - `resolve_frame_chain` / `motion_gate`: downstream gates.
  - It reuses the existing `compositor.glint_sprite`, `brightness_pulse`-style lift, `flip_h`, `tint`, `over`, `treatments.envelope` and `validate_window`.
- **`agent008/still.py`:** `compose_still_shot(..., treatment_record=)`.
  - Treated shots need the record, and a certified reflection when one is assigned.
  - Timed frames are rendered only in their windows. QC hashes all frames.
  - The G07 guard is added.
- **`agent008/motion/compose.py`:** `treatments_composited=`. Only the certified static reflection may accompany generated motion. Glint and pop remain rejected.
- **`agent008/spec.py`:** `IN_SHOT_CUT_SHOTS = {'S018'}`.
- No new agent, provider or dependency. No production asset touched.

## 4. Tests: `agent008/tests/test_g08.py` (21 new)
| # | Required test | Test | Covers |
|---|---|---|---|
| 1 | valid mirror glint | T01 | S004 class, synced to the chime |
| 2 | glint placement and timing | T02 | box exact; only window frames change, and only inside the box; peak; sync/target failures |
| 3 | valid reflection | T03 | COMPOSITE |
| 4 | mirror orientation | T04 | left-right reversal pixels; vertical flip and unknown modes rejected |
| 5 | mirror clipping | T05 | copy larger than the glass is clipped to it |
| 6 | mirrored overlays | T06 | COMPOSITE carries the reversed marks; PRESERVE REFLECTION marks inside the glass; double source, outside glass, mark on glass and straddling mark all rejected |
| 7 | valid completion pop | T07 | glass-only lift, frame-exact sync |
| 8 | clean reveal | T08 | overlays in the spec, the frame or the reflection, or a pop with overlays, all rejected |
| 9 | frame range | T09 | 6–10 OK; 5, 11, crossing, negative, float rejected; G07 segment bound; record range |
| 10 | unsupported treatment | T10 | unsupported id, undeclared/incomplete record, no record, mask shape, field, wrong id |
| 11 | unapproved source | T11 | frame / record / still frame unapproved |
| 12 | source SHA mismatch | T12 | frame SHA, record bound to another frame, certificate mismatch |
| 13 | treatment-input hash mismatch | T13 | edited record, static vs timed record, missing/forged G03 provenance (treatments have no asset files) |
| 14 | invalid geometry | T14 | glass, scale/upscale, source on glass, target, tint, glint outside, size, gain |
| 15 | duplicate treatment | T15 | spec duplicate, re-applied reflection, doubled certificate |
| 16 | source immutability | T16 | SHA and mtime, no overwrite |
| 17 | two-run determinism | T17 | reflection, glint and pop |
| 18 | G03 + G08 ordering | T18 | G08 before G03 refused, chain accepted, reflection skipped refused, chain broken refused |
| 19 | treatment-free regression | T19 | still path unchanged, record without treatments refused, S018 G07 guard, layout identity |
| — | no network or provider | T19b | — |
| — | motion gate | T20 | only the certified reflection is accepted; glint/pop rejected; G03 → G08 → upload chain |

**Full suite: 181/181 OK** (160 existing + 21 G08). Output: `AGENT008_TEST_OUTPUT_G08_v1.txt`.

**Regression (`G08_REGRESSION_COMPARISON_v1.json`):** compared with the pre-G03 baseline, the treatment-free G02 output and deterministic core are identical, and the v0.2 motion MP4, WAV and provenance keys are identical.

## 5. Determinism: `G08_DETERMINISM_PROOF_v1.json` (PASS)
| Treatment | INPUT_SHA | OUTPUT_A_SHA | OUTPUT_B_SHA | DETERMINISM_PASS |
|---|---|---|---|---|
| MIRROR_REFLECTION_COMPOSITE (frame png) | `e91ab7c3…` | `405d0643…4050` | `405d0643…4050` | PASS |
| MIRROR_REFLECTION_COMPOSITE (provenance core) | `6a1a4330…` | `f6e72ea1…e030` | `f6e72ea1…e030` | PASS |
| MIRROR_REFLECTION_PRESERVE (certificate core; frame unchanged) | `e91ab7c3…` | `768c0c90…5dac` | `768c0c90…5dac` | PASS |
| MIRROR_GLINT (still mp4) | `4e60ec62…` | `b3bb6b08…29bd` | `b3bb6b08…29bd` | PASS |
| MIRROR_GLINT (still wav) | `4e60ec62…` | `132d96b8…5698` | `132d96b8…5698` | PASS |
| MIRROR_GLINT (raw frame hash list) | `4e60ec62…` | `1ca2336d…c73e` | `1ca2336d…c73e` | PASS |
| COMPLETION_POP (still mp4) | `405d0643…` | `ed8d2eae…6768` | `ed8d2eae…6768` | PASS |
| COMPLETION_POP (still wav) | `405d0643…` | `0281de4e…a940` | `0281de4e…a940` | PASS |
| COMPLETION_POP (raw frame hash list) | `405d0643…` | `c7b9db7e…3087` | `c7b9db7e…3087` | PASS |
| G03_THEN_G08_CHAIN (frame png) | `e91ab7c3…` | `3b40bd95…46ab` | `3b40bd95…46ab` | PASS |

Inputs were unchanged after all runs.

## 6. Live EP005 read-only validation and updated matrix
- **Script:** `g08_live_spec_validation.py`.
- **Output:** `G08_LIVE_SPEC_VALIDATION_AND_MATRIX_v1.json`.
- **Method:**
  - Each remaining shot's production gate was run in memory with stand-ins for its future approved inputs.
  - Manifest-governed constraints were checked on the live specs: the S004 chime and the S025 pop SFX are present as shot events, and the S004 cheek and S012 mouth glint targets are active overlays.
  - Nothing was rendered or written.

| Shot | Treatments | G08_STATUS | Other code blockers | Missing base frame | Missing dialogue | Provider motion | Upstream continuity blocker | Code-ready once inputs exist |
|---|---|---|---|---|---|---|---|---|
| S001 | — | NOT_REQUIRED | — | yes: F-MIRROR-OPEN (NEEDS_NEW_SHOT_FRAME) | 2 | yes | — | YES |
| S002 | — | NOT_REQUIRED | — | yes: F-MEDIUM-TWOSHOT (CAN_DERIVE_DETERMINISTICALLY) | 1 | yes | — | YES |
| S003 | — | NOT_REQUIRED | — | yes: F-OVERSHOULDER-MIRROR (NEEDS_NEW_SHOT_FRAME) | 1 | no | — | YES |
| S004 | MIRROR-GLINT | SUPPORTED | — | yes: F-OVERSHOULDER-MIRROR (CAN_DERIVE_DETERMINISTICALLY) | 2 | no | — | YES |
| S005 | — | NOT_REQUIRED | — | yes: F-OVERSHOULDER-MIRROR (CAN_DERIVE_DETERMINISTICALLY) | 0 | no | — | YES |
| S006 | MIRROR-REFLECTION | SUPPORTED | — | yes: F-FACE-MIRROR-POINT (NEEDS_NEW_SHOT_FRAME) | 1 | yes | — | YES |
| S007 | MIRROR-REFLECTION | SUPPORTED | — | yes: F-CHEEK-CLOTH (NEEDS_NEW_SHOT_FRAME) | 2 | yes | — | YES |
| S008 | — | NOT_REQUIRED | — | yes: F-CHEEK-CLOTH (CAN_DERIVE_DETERMINISTICALLY) | 0 | no | — | YES |
| S009 | — | N/A (G11 shot) | G11 | yes: F-CHEEK-CLOTH (BLOCKED) | 0 | no | — | no |
| S010 | MIRROR-REFLECTION | SUPPORTED | — | yes: F-FACE-MIRROR (NEEDS_NEW_SHOT_FRAME) | 1 | yes | — | YES |
| S011 | MIRROR-REFLECTION | SUPPORTED | — | yes: F-FACE-MIRROR (CAN_DERIVE_DETERMINISTICALLY) | 0 | yes | — | YES |
| S012 | MIRROR-GLINT | SUPPORTED | — | yes: F-FACE-MIRROR (CAN_DERIVE_DETERMINISTICALLY) | 2 | no | — | YES |
| S013 | — | NOT_REQUIRED | — | yes: F-FACE-MIRROR (CAN_DERIVE_DETERMINISTICALLY) | 0 | no | — | YES |
| S014 | MIRROR-REFLECTION | SUPPORTED | — | yes: F-MOUTH-CLOTH (NEEDS_NEW_SHOT_FRAME) | 1 | yes | — | YES |
| S015 | — | N/A (G11 shot) | G11 | yes: F-MOUTH-CLOTH (BLOCKED) | 0 | no | — | no |
| S016 | — | NOT_REQUIRED | — | yes: F-FACE-MIRROR (CAN_DERIVE_DETERMINISTICALLY) | 1 | yes | — | YES |
| S017 | — | NOT_REQUIRED | — | yes: F-MEDIUM-TWOSHOT (CAN_DERIVE_DETERMINISTICALLY) | 0 | no | — | YES |
| S018 | MIRROR-GLINT | SUPPORTED | G07 | yes: F-MACRO-REFLECTION (NEEDS_NEW_SHOT_FRAME) | 2 | no | — | no |
| S019 | — | NOT_REQUIRED | — | yes: F-MACRO-REFLECTION (CAN_DERIVE_DETERMINISTICALLY) | 0 | no | S018 | YES |
| S020 | — | NOT_REQUIRED | — | yes: F-NOSE-CLOTH (NEEDS_NEW_SHOT_FRAME) | 1 | yes | — | YES |
| S021 | — | N/A (G11 shot) | G11 | yes: F-NOSE-CLOTH (BLOCKED) | 0 | no | — | no |
| S022 | — | NOT_REQUIRED | — | yes: F-NOSE-CLOTH (CAN_DERIVE_DETERMINISTICALLY) | 1 | yes | S021 | YES |
| S023 | — | NOT_REQUIRED | — | yes: F-MEDIUM-TWOSHOT (CAN_DERIVE_DETERMINISTICALLY) | 0 | no | S021 | YES |
| S024 | — | NOT_REQUIRED | G06 | yes: F-MIRROR-OPEN (CAN_DERIVE_DETERMINISTICALLY) | 0 | no | — | no |
| S025 | MIRROR-REFLECTION, COMPLETION-POP-ACCENT | SUPPORTED | — | yes: F-MIRROR-OPEN (CAN_DERIVE_DETERMINISTICALLY) | 1 | no | — | YES |
| S026 | — | NOT_REQUIRED | — | yes: F-MEDIUM-TWOSHOT (NEEDS_NEW_SHOT_FRAME) | 1 | yes | — | YES |

## 7. Updated factory matrix
| Measure | Value |
|---|---|
| TOTAL_REMAINING_SHOTS | **26** |
| SHOTS_WITH_ALL_CODE_PATHS_SUPPORTED_BEFORE_G08 | 13 |
| SHOTS_WITH_ALL_CODE_PATHS_SUPPORTED_AFTER_G08 | **21**: S001–S008, S010–S014, S016, S017, S019, S020, S022, S023, S025, S026 |
| SHOTS_STILL_BLOCKED_BY_G08 | **0** |
| SHOTS_STILL_BLOCKED_BY_G06 | 1: S024 |
| SHOTS_STILL_BLOCKED_BY_G07 | 1: S018 (G03 and G08 parts supported) |
| SHOTS_STILL_BLOCKED_BY_G11 | 3: S009, S015, S021 |
| SHOTS_BLOCKED_ONLY_BY_BASE_FRAMES | 7: S005, S008, S011, S013, S017, S019, S023 |
| SHOTS_BLOCKED_ONLY_BY_DIALOGUE | 0 (no remaining shot has an approved base frame) |
| SHOTS_BLOCKED_BY_BASE_FRAMES_AND_DIALOGUE | 14: S001, S002, S003, S004, S006, S007, S010, S012, S014, S016, S020, S022, S025, S026 |
| SHOTS_REQUIRING_PROVIDER_MOTION | 11: S001, S002, S006, S007, S010, S011, S014, S016, S020, S022, S026 |
| Upstream continuity blocked | S019 (S018/G07), S022 and S023 (S021/G11) |
| SHOTS_POTENTIALLY_PRODUCIBLE_IN_FIRST_BATCH | **18**: S001–S008, S010–S014, S016, S017, S020, S025, S026 |

**Inputs for the 18-shot first batch:**
- base frames for 9 frame families:
  - 8 need image generation (`NEEDS_NEW_SHOT_FRAME`: S001, S003, S006, S007, S010, S014, S020, S026)
  - the rest are derivable (G04 / family reuse)
- 16 G03 placement records and 8 G08 treatment records
- 17 dialogue lines
- planned provider calls: 8 image, 10 video, 8 Mikko TTS, 9 Lumi TTS

## 8. Next factory step
| Option | Shots unlocked | Dependency order | Cost | Risk | Auto-batch afterwards |
|---|---|---|---|---|---|
| **A. Approved base-frame production batch** (9 families for the 18-shot first batch) | **every one of the 21 code-ready shots needs its frame; it fully unlocks the 7 frame-only shots and is required for all 16 G03 and 8 G08 records** | **first**: placement and treatment records can only be measured on approved frames; derived frames (G04) follow their family frames | ~8 image generations (cost unverified), human review per frame | medium: frame quality and continuity are reviewed per frame (S027/S028 precedent) | **yes**: frames → records → deterministic stills auto-batch; motion shots then need only per-shot Seedance approval |
| B. Missing dialogue batch (17–20 lines) | 0 by itself (no shot has a frame) | parallel to A; not first | ~20 TTS calls (low) | low | partial: clips wait for frames |
| C. G06 | 1 (S024) | independent | $0 | low | — |
| D. G07 | 1 (+S019 by continuity = 2) | independent | $0 | low–medium | — |
| E. G11 design + build | 3 (+S022, S023 = 5) | blocks the Act-2 chain | $0 code; needs a human design decision | high | — |
| F. Direct production batch | **impossible now**: zero approved base frames for S001–S026 | — | — | — | — |

**RECOMMENDATION: A, the approved base-frame production batch.**
- **Why A:** factory capability is now ahead of inputs: 21 of 26 shots are code-ready, and every one of them waits on an approved base frame. A is first in the dependency order, because the G03 and G08 records can only be measured on approved frames. It also opens auto-batching of the deterministic stills.
- **What A needs before it can run:**
  - an explicit paid-generation authorisation (about 8 images; cost unverified)
  - frame-family briefs that keep the berry smudges off the base frames (G03 adds them) and show the clean mirror glass (G08 measures it)
- **Afterwards:**
  - B (dialogue) can run in parallel or next.
  - C/D are small zero-spend follow-ups.
  - E needs a human design decision.

Not executed.

## 9. Non-regression
- **Stored assets:** all 11 approved S027/S028/S029 assets (shots, frames, motions, dialogue) were re-hashed from storage. Each is equal to its registry SHA and APPROVED (`G08_NONREGRESSION_S027_S029_STORED_REHASH_v1.json`).
- **Production fingerprints are unchanged:**

  | Object | Fingerprint |
  |---|---|
  | scripts | 5:649d63f9… |
  | manifests | 12:cefb8fa2… |
  | readiness | 8:f5c646ee… |
  | resolution items | 86:ce5ac459… |
  | registry | 34:d845548f… |
  | storage | 30:16bb5c35… |

- **Calls:** zero provider, ElevenLabs, Higgsfield, Seedance, Agent-006, Agent-007, production writes, uploads or renders.

## Rollback
Revert the commit. G08 is additive. Treated shots fall back to the previous fail-closed behaviour, and no production state changed.
