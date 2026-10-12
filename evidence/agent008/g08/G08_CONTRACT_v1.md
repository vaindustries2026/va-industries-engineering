# Agent-008 G08 governed visual treatments: contract v1 (`AGENT008_G08_TREATMENTS_v1`)

- **Module:** `agent008/g08.py`, version `agent008-v0.3-treatments`.
- **Tests:** `agent008/tests/test_g08.py` (21).
- **Scope:** authoritative v05 lineage only. Script `6498ea8d`, manifest `0325d35c` (`compositing_treatments` + shot plans), readiness `69bff641`.
- **Audit:** `G08_REQUIREMENT_AUDIT_v1.json`.

## 1. Required treatment types (G08_TREATMENT_TYPES_REQUIRED)
| Candidate | Authoritative? | Treatment id | Shots |
|---|---|---|---|
| A. MIRROR_GLINT | **yes** | `TREATMENT-EP005-MIRROR-GLINT-v01` | S004, S012, S018 |
| B. MIRROR_REFLECTION | **yes** | `TREATMENT-EP005-MIRROR-REFLECTION-v01` | S006, S007, S010, S011, S014, S025 |
| C. COMPLETION_POP_ACCENT | **yes** | `TREATMENT-EP005-COMPLETION-POP-ACCENT-v01` (bloom pulse) | S025 |
| D. CLEAN_REVEAL | **not a separate treatment** | — | S025 is a *state rule*: zero active berry overlays (`spec.validate_clean_reveal`). G08 enforces it on the reflection and the pop, and the bloom never stands in for removal. |
| E. other | **none** | — | The manifest has exactly three `compositing_treatments`. The mirror tilt / angle (S004, S012, S018) is animation, which Batch 0C held-pose approval covers. The S018 macro reframe is G07. |

All three are `COMPOSITING_TREATMENT_NOT_AN_ASSET`, with `paid_generation_required=false`. **There is no treatment asset file.** The governed treatment inputs are the approved treatment record and the authenticated G03 provenance, and both are SHA-bound.

## 2. Inputs, identity, output
- **Source frame:** an approved `SHOT_FRAME/BASE_FRAME` or `DERIVED_FRAME` for the shot, verified by SHA-256.
  - For overlay shots it is the approved G03 frame plus its G03 provenance. That provenance is authenticated by its recomputed deterministic core, its output SHA and its overlay set.
- **Treatment identity:**
  - Every treatment must be in the shot spec (`spec.treatments`, from the manifest).
  - Only the three ids above are accepted.
  - Duplicates fail closed.
- **Treatment record** (human-approved, bound by canonical SHA-256 to the shot and to the exact frame the treatments start from):
```json
{"record": {"contract": "AGENT008_G08_TREATMENTS_v1", "record_id": "…", "shot_id": "S025",
            "input_frame": {"asset_id": "…", "sha256": "<frame entering G08>"}, "frame_size": [1920, 1080],
            "frame_range": [0, 95],
            "mirror_glass": {"shape": "ELLIPSE", "cx": 0, "cy": 0, "rx": 0, "ry": 0, "feather_px": 0},
            "reflection": {"mode": "PRESERVE", "reflected_overlays": []},
            "pop": {"treatment_id": "TREATMENT-EP005-COMPLETION-POP-ACCENT-v01", "start_frame": 0, "frames": 7,
                    "gain": 0.12, "sync_audio_asset_id": "SFX-COMPLETION-POP-v01"}},
 "approval_status": "APPROVED", "expected_sha256": "<canonical SHA-256 of record>"}
```

  - A section exists **iff** the shot is assigned that treatment.
  - A missing section fails closed (`TREATMENT_RECORD_INCOMPLETE`); an extra one also fails (`TREATMENT_UNDECLARED`).
  - Geometry is in integer frame pixels. Values are left as zeros above because **no approved base frame exists yet**, so none can be measured. This is the G08_SPEC_GAP, closed only by this record after the frame is approved.
- **Output:**
  - MIRROR_REFLECTION COMPOSITE: a new lossless PNG, `<shot>_G08_REFLECTION_FRAME_CANDIDATE.png` (REVIEW; proposed SHOT_FRAME/DERIVED_FRAME), plus provenance carrying `treatments_composited`.
  - MIRROR_REFLECTION PRESERVE: a certificate (provenance) bound to the unchanged frame SHA.
  - Glint and pop are frame-exact in the G02 still path's REVIEW MP4. The provenance records the record SHA, glass, windows, envelopes and sync.
  - Everything is REVIEW status, never auto-approved, and nothing is registered.

## 3. G08_MIRROR_REFLECTION_PIPELINE
**What the specs say:**
- Mirror reflection is "Composite **or preserve** the mirror reflection so the face marks are reflected while the mirror glass itself remains clean" (S007).
- QC checks: "only Mikko's reflection contains the marks", "no dirt or smudge is placed on the mirror surface", and "the selected smudge … is clearly connected to its mirror reflection" (S006).
- S025 asks for "the clean, bright Mikko reflection inside the clean mirror glass".
- It is shot-level compositing, "NOT A SEPARATE ASSET".

| Item | Rule |
|---|---|
| Reflected subject | Mikko's face as it appears in the hand mirror |
| Source-frame relationship | PRESERVE: the approved frame already shows the reflection. COMPOSITE: a declared `source_rect` of the same frame (the physical face, after G03 FACE overlays) is the reflected content. |
| Mirror region | `mirror_glass`: axis-aligned **ELLIPSE** (cx, cy, rx, ry) inside the frame. Other mask shapes fail closed. Measured on the approved base frame. |
| Flip / orientation | **Left-right reversal only** (`flip: HORIZONTAL`), matching the manifest's "preserve correct mirror reversal". Vertical flip, rotation and perspective fail closed (`MIRROR_SEMANTICS_UNSUPPORTED`); a tilted mirror needs a new human decision. |
| Scale | COMPOSITE `target_width_px` ≤ the source width (no upscale); height rounded to keep aspect; lanczos bitexact |
| Clipping | Whatever the reflection writes is clipped to the glass ellipse (optional 0–4 px feather). Pixels outside the glass are proven unchanged. |
| Occlusion | FACE marks may not touch the glass (`OVERLAY_ON_MIRROR_GLASS`), so the glass stays clean. A reflected mark partly outside the glass, or straddling the source region, fails closed (`REFLECTED_MARK_CLIPPED` / `REFLECTED_MARK_OUTSIDE_GLASS`). |
| Mirrored smudges | **Yes.** PRESERVE: the reflected marks are exactly the G03 REFLECTION placements (`mirror=true`), inside the glass. COMPOSITE: they arrive through the reversed copy; G03 REFLECTION placements are refused (`REFLECTION_DOUBLE_SOURCE`). Either way the record's `reflected_overlays` must equal what the frame actually shows (`REFLECTED_OVERLAYS_MISMATCH`). S025: must be empty. |
| G03 vs G08 order | **G03 first, then G08.** Running G08 on a frame that lacks the shot's overlays fails `STILL_OVERLAYS_NEED_G03_ANCHORS`. |
| Light glass tint | COMPOSITE `tint_rgb` and `tint_amount` 0–0.10 (contract guard; Phase-0 reference 0.07) |
| Operation order | base frame → G03 FACE overlays (+ REFLECTION overlays in PRESERVE) → G08 reflection → [G07 segments, later] → G08 glint → G08 pop |
| Motion shots (S006 planned, S007, S010, S011, S014) | The reflection is applied **to the motion base frame before upload**, the same principle as G03. `compose_motion_shot(..., treatments_composited=)` accepts only that static certificate, bound to `source_frame_sha256`. Glint or pop on generated motion still fails closed. Production risk: the provider animates the reflection, so human raw-motion QC must check it. |

**Future record required per reflection shot:**
- `mirror_glass` ellipse
- mode
- `reflected_overlays`
- for COMPOSITE: `source_rect`, `target_center`, `target_width_px`, tint

No coordinates are guessed.

## 4. Glint contract (S004, S012, S018)
- **Visual source:** the existing deterministic primitive `compositor.glint_sprite(size)` (procedural soft specular core plus a faint 4-point star). It is reused unchanged.
- **Timing:**
  - One window of 6–10 frames, ending inside the shot (`treatments.validate_window`, reused).
  - Opacity envelope `soft_attack_decay` (reused).
  - The start frame comes from the record. A G07 segment bound can be passed (`segment=`), and a window outside it fails closed (`TREATMENT_OUTSIDE_GOVERNED_RANGE`).
- **S004 sync:** "synchronized with … clue chime". The record must name `SFX-LUMI-CLUE-CHIME`, and its timing start × fps must equal `start_frame` exactly. Otherwise `TREATMENT_AUDIO_SYNC_MISSING` / `_MISMATCH`.
- **Placement:**
  - Integer centre plus `size_px` (≥ 4). The whole sprite must lie inside the mirror glass (`GLINT_OUTSIDE_GLASS`), so placement depends on the mirror geometry.
  - **Target mark:** S004 = cheek, S012 = mouth (manifest "near the selected cheek" / "to the reflected mouth-area clue"). The target must be a reflected mark in the frame (`GLINT_TARGET_INVALID`). S018 has no target ("on or around the mirror reflection").
  - "Near" is not quantified in the manifest (G08_SPEC_GAP). It is fixed by the human-approved record.
- **Layering:** above the reflected content and overlays (a specular on the glass surface), using premultiplied `over` at the envelope opacity.

## 5. Completion / clean-reveal contract (S025)
- **S025 treatments (live spec):** MIRROR_REFLECTION + COMPLETION_POP_ACCENT. Event audio: `SFX-COMPLETION-POP-v01`. Active overlays: **0**. `clean_reveal: true`.
- **Pop:**
  - Window of 6–8 frames, `bloom` envelope.
  - `gain` in (0, 0.12] (treatment `max_gain`).
  - Lift toward white restricted to the glass mask ("pulse on the mirror glass").
  - Must sync to `SFX-COMPLETION-POP-v01`: frame-exact against its timing start.
- **Clean reveal fails closed** (`CLEAN_REVEAL_HAS_ACTIVE_OVERLAYS`) if any of these hold:
  - the spec has active overlays
  - the frame carries a G03 overlay set
  - the reflection declares reflected marks
  - a pop is requested on a frame with any overlay
- **Order:** G03 has nothing to place on S025 (`OVERLAY_NONE_REQUIRED`) → G08 reflection (clean) → pop. The pop never changes overlay state.

## 6. S018_REQUIRED_OPERATION_ORDER (G07 not implemented here)
1. **Segment A** (opening, Lumi adjusting the mirror): approved frame A → G03 nose overlay with its own placement record → [G08 reflection: not assigned to S018].
2. **Segment B** (macro reframe of the reflection): approved frame B → G03 nose overlay with its own placement record.
3. **G08 glint:** exactly one window, entirely inside segment B ("ends before S019"). It is applied per segment through `plan_timed(..., segment=(first, last))` and may not straddle the cut.
4. **G07:** frame-exact concatenation of the two rendered segments at the declared cut frame, then audio/dialogue over the whole shot.

Until G07 exists, the G02 still path refuses S018 outright (`STILL_IN_SHOT_CUT_NEEDS_G07`; `spec.IN_SHOT_CUT_SHOTS`), so a single-segment S018 cannot be produced by accident.

## 7. Fail-closed codes
| Requirement | Code |
|---|---|
| Unsupported treatment / field | `TREATMENT_UNSUPPORTED` / `TREATMENT_FIELD_UNSUPPORTED` |
| Missing source / unapproved / not a shot frame / wrong shot | `ASSET_FILE_MISSING` / `TREATMENT_SOURCE_NOT_APPROVED` / `TREATMENT_SOURCE_NOT_A_SHOT_FRAME` / `SHOT_IDENTITY_MISMATCH` |
| Source SHA mismatch / record bound to another frame / certificate frame mismatch | `HASH_MISMATCH` / `TREATMENT_RECORD_FRAME_MISMATCH` / `TREATMENT_CERTIFICATE_FRAME_MISMATCH` |
| Undeclared treatment (record or frame) / missing section / still shot without a record | `TREATMENT_UNDECLARED` / `TREATMENT_RECORD_INCOMPLETE` / `STILL_TREATMENTS_NEED_G08` |
| Invalid frame range / outside governed segment | `TREATMENT_FRAME_RANGE_INVALID` / `TREATMENT_OUTSIDE_GOVERNED_RANGE` |
| Treatment input hash mismatch (record edited, static vs timed record differ, forged G03 provenance) | `TREATMENT_RECORD_HASH_MISMATCH` / `G03_PROVENANCE_MISMATCH` |
| Record not approved / missing | `TREATMENT_RECORD_NOT_APPROVED` / `TREATMENT_RECORD_MISSING` |
| Coordinates / scale / mask / tint, gain | `TREATMENT_COORDINATE_INVALID` / `TREATMENT_SCALE_INVALID` / `TREATMENT_MASK_UNSUPPORTED` / `TREATMENT_FIELD_INVALID` |
| Mirror semantics | `MIRROR_SEMANTICS_UNSUPPORTED`, `REFLECTION_DOUBLE_SOURCE`, `REFLECTION_SOURCE_ON_GLASS`, `REFLECTED_*`, `OVERLAY_ON_MIRROR_GLASS` |
| Glint geometry / target; audio sync | `GLINT_OUTSIDE_GLASS` / `GLINT_TARGET_INVALID`; `TREATMENT_AUDIO_SYNC_MISSING` / `_INVALID` / `_MISMATCH` |
| Duplicate invocation (spec duplicate, re-applied reflection, doubled certificate) | `TREATMENT_DUPLICATE_INVOCATION` / `TREATMENT_CERTIFICATE_INVALID` |
| Reflection skipped before the timed stage | `TREATMENT_NOT_COMPOSITED` |
| In-place modification / existing output / input changed / pixels outside the glass changed | `OUTPUT_WOULD_OVERWRITE_SOURCE` / `OUTPUT_EXISTS` / `SOURCE_MUTATED` / `TREATMENT_UNEXPECTED_PIXEL_CHANGE` |
| Crop/scale/pad of a treated frame in G02 | `TREATMENT_LAYOUT_NOT_IDENTITY` |
| Timed treatment or uncertified reflection on generated motion | `MOTION_TREATMENTS_NEED_TRACKING_V02` (unchanged rule; only the certified static reflection is newly accepted) |

## 8. Integration and non-regression
- **G02 `compose_still_shot(..., treatment_record=)`:**
  - The reflection must already be certified on the frame (`frame['treatments_composited']`).
  - Glint and pop frames are rendered only inside their windows. Every other frame is the identical held image.
  - QC hashes every output frame.
- **Shots without treatments or overlays** are byte-identical, MP4 and deterministic core included (`G08_REGRESSION_COMPARISON_v1.json`, against the pre-G03 baseline). So S027/S028/S029 would re-render unchanged.
