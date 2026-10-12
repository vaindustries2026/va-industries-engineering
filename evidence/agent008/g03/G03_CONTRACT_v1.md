# Agent-008 G03 deterministic overlay placement: contract v1 (`AGENT008_G03_OVERLAY_PLACEMENT_v1`)

- **Module:** `agent008/overlay.py`, version `agent008-v0.3-overlay-placement`.
- **Tests:** `agent008/tests/test_g03.py`.
- **Design basis:** the recorded G03 design in `evidence/agent008/scaleout/EP005_AGENT008_CAPABILITY_GAP_MATRIX_v1.md`: "a human-approved anchor JSON per frame (x, y, scale, rotation, mirror), applied deterministically on stills, and pre-composited into base frames before provider upload, so no motion tracking is needed for persistent smudges".
- **Scope:** the authoritative v05 lineage only. Script `6498ea8d`, manifest `0325d35c`, readiness `69bff641`.

## 1. What the authoritative specs require (audit: `G03_REQUIREMENT_AUDIT_v1.json`)
| Behaviour | Required by EP005? | Evidence | G03 v1 |
|---|---|---|---|
| Overlay image input | yes | 3 approved `OVERLAY_VFX/BERRY_SMUDGE_OVERLAY` rows; WEBP with alpha, ~1447×1087 canvas | **supported**: governed identity, status APPROVED/LOCKED, SHA-256 verified |
| Multiple overlays per frame | yes | up to 3 per shot (S001–S008) | **supported** |
| Same overlay on face **and** in the mirror | yes | e.g. S003 "…and its corresponding reflection"; S020 "in the face and mirror reflection" | **supported**: one placement per surface (`FACE`, `REFLECTION`) per asset |
| Mirror reversal | yes | S001 "preserve correct mirror reversal" | **enforced**: `REFLECTION` ⇒ `mirror=true`, `FACE` ⇒ `mirror=false` |
| Frame range | whole shot only | every dependent shot has `visible_at_start = visible_at_end = true` | **enforced**: the record must declare `frame_range = [0, frames-1]`; any other range fails closed |
| Removal at a declared frame | **no** for G03 | removals exist only in S009/S015/S021 and need a cloth-occlusion design (G11) | **rejected** (`OVERLAY_REMOVAL_UNSUPPORTED_G11`); the spec already fails closed on transitions |
| x/y placement | yes, but **not defined** | the manifest names anatomy only ("anatomical left cheek", "beside, not inside, the mouth", "nose") | **G03_SPEC_GAP**: supplied by the human-approved placement record (§2) |
| Scale | yes, but **not defined** | no size in the manifest | **G03_SPEC_GAP**: record `width_px` |
| Anchor | yes, but **not defined** | no numeric anchor; no approved base frame exists for S001–S026 | **G03_SPEC_GAP**: record; only the `CENTER` anchor is supported |
| Placement relative to the source frame | yes | anchors refer to the shot's base frame | **enforced**: integer base-frame pixels; `frame_size` must equal the base frame |
| Rotation | in the recorded design | smudge orientation on the face (Phase-0 stand-in precedent) | **supported**: `rotation_deg`, finite, \|deg\| ≤ 180 |
| Opacity | not declared | only presence or absence is governed; S013 forbids "glow, sparkle" | **full opacity only**: `opacity` absent or exactly 1.0; anything else fails closed |
| Z-order | not declared | marks must stay "readable and unobscured" (S014) | **no z-order**: overlapping overlays fail closed, so draw order cannot affect pixels; any z/layer field fails closed |
| Clipping | not required | — | **not supported**: any visible pixel outside the frame fails closed |
| Treatments (glint, reflection, pop) | separate | `COMPOSITING_TREATMENT_NOT_AN_ASSET` | out of scope (G08) |

## 2. Placement record (the human-approved input that closes the spec gap)
```json
{"record": {"contract": "AGENT008_G03_OVERLAY_PLACEMENT_v1", "record_id": "...", "shot_id": "S017",
            "base_frame": {"asset_id": "<approved SHOT_FRAME>", "sha256": "<its sha256>"},
            "frame_size": [1920, 1080], "frame_range": [0, 95],
            "placements": [{"asset_id": "OVERLAY-EP005-BERRY-SMUDGE-NOSE-v01", "overlay_sha256": "c1169127…",
                            "surface": "REFLECTION", "anchor": "CENTER", "x": 0, "y": 0, "width_px": 0,
                            "rotation_deg": 0, "mirror": true}]},
 "approval_status": "APPROVED", "expected_sha256": "<canonical SHA-256 of record, bound by the human approval>"}
```

- **Approval:** the record is approved by its exact canonical SHA-256, the same canonical form as the manifest evidence.
- **Binding:** it is bound to one shot and one approved base-frame SHA. It can only be written after that base frame exists and is approved.
- **Unknown fields:** a field outside the contract fails closed (`PLACEMENT_FIELD_UNSUPPORTED`).

## 3. Deterministic recipe
For each placement, in fixed order sorted by (surface, asset_id):
1. Decode the overlay to RGBA.
2. Trim to the alpha > 8 bounding box, the same trim as the Phase-0 compositor.
3. Scale to `width_px`. Height = round(trimmed_h × width_px / trimmed_w). Uses the `media.SCALE_FLAGS` lanczos bitexact filter. Upscaling past the trimmed width is rejected.
4. Horizontal flip if `mirror`.
5. Rotate with `compositor.rotate` (bilinear, premultiplied) about the padded layer centre.
6. Place: top-left = (x − w//2, y − h//2).
7. Composite with premultiplied float64 `compositor.over` and one final `rint`.

Then the whole frame is checked:
- Visible pixels outside the frame fail closed.
- Overlaps between overlays fail closed.
- Any pixel change outside the placed overlay pixels fails closed.

**Output:**
- A new lossless PNG, `<shot>_G03_OVERLAY_FRAME_CANDIDATE.png` (rgb24, bitexact, no metadata). The round trip is verified.
- Provenance in `<shot>_G03_OVERLAY_PROVENANCE.json`: status REVIEW, proposed `SHOT_FRAME/DERIVED_FRAME`, not registered, approval by the exact PNG SHA-256.

## 4. Fail-closed codes
| Condition | Code |
|---|---|
| Missing overlay asset (not supplied / file absent) | `OVERLAY_ASSET_MISSING` / `ASSET_FILE_MISSING` |
| Unapproved overlay / wrong type | `OVERLAY_ASSET_NOT_APPROVED` / `OVERLAY_ASSET_WRONG_TYPE` |
| SHA mismatch: overlay file / record overlay SHA / base frame / record edited / record for another frame | `HASH_MISMATCH` / `OVERLAY_SHA_MISMATCH` / `HASH_MISMATCH` / `PLACEMENT_RECORD_HASH_MISMATCH` / `PLACEMENT_RECORD_BASE_FRAME_MISMATCH` |
| Unapproved record / missing record | `PLACEMENT_RECORD_NOT_APPROVED` / `PLACEMENT_RECORD_MISSING` |
| Invalid frame range / undeclared timing | `OVERLAY_FRAME_RANGE_INVALID` / `OVERLAY_TIMING_UNDECLARED` |
| Per-overlay timing or removal | `OVERLAY_REMOVAL_UNSUPPORTED_G11` |
| Anchor outside the frame, non-integer coordinate / visible pixels outside the frame / frame size mismatch | `OVERLAY_COORDINATE_INVALID` / `OVERLAY_OUT_OF_BOUNDS` / `PLACEMENT_FRAME_SIZE_MISMATCH` |
| Invalid scale (non-int, < 2, upscale) / rotation / opacity | `OVERLAY_SCALE_INVALID` / `OVERLAY_ROTATION_INVALID` / `OVERLAY_OPACITY_INVALID` |
| Unsupported anchor / surface / z-order / other field / missing field | `OVERLAY_ANCHOR_UNSUPPORTED` / `OVERLAY_SURFACE_UNSUPPORTED` / `OVERLAY_Z_ORDER_UNSUPPORTED` / `PLACEMENT_FIELD_UNSUPPORTED` / `PLACEMENT_FIELD_MISSING` |
| Mirror rule broken | `OVERLAY_MIRROR_RULE` |
| Undeclared overlay (not active in the shot) / extra overlay supplied | `OVERLAY_NOT_IN_SHOT_CONTRACT` |
| Active overlay not placed / empty record | `OVERLAY_PLACEMENT_MISSING` / `PLACEMENT_RECORD_EMPTY` |
| Duplicate identity in the contract / duplicate placement on one surface | `OVERLAY_DUPLICATE_IDENTITY` / `OVERLAY_DUPLICATE_PLACEMENT` |
| Overlapping overlays | `OVERLAY_OVERLAP_UNDECLARED` |
| Shot without overlays (e.g. S025 CLEAN REVEAL) | `OVERLAY_NONE_REQUIRED` |
| Base frame not approved / not a shot frame / wrong shot / transparent / already composited | `OVERLAY_SOURCE_NOT_APPROVED` / `OVERLAY_SOURCE_NOT_A_SHOT_FRAME` / `SHOT_IDENTITY_MISMATCH` / `OVERLAY_SOURCE_HAS_TRANSPARENCY` / `OVERLAY_ALREADY_COMPOSITED` |
| In-place modification / existing output / input mutated during the run | `OUTPUT_WOULD_OVERWRITE_SOURCE` / `OUTPUT_EXISTS` / `SOURCE_MUTATED` |
| Unexpected pixel change outside the overlays | `OVERLAY_UNEXPECTED_PIXEL_CHANGE` |

## 5. Downstream integration (existing paths, no redesign)
- **G02 still (`still.compose_still_shot`):**
  - A shot with active overlays is accepted only from a `SHOT_FRAME/DERIVED_FRAME` that carries `overlays_composited` from its approved G03 provenance.
  - That set must equal the shot's active overlay set and SHAs, and be bound to the frame SHA.
  - Otherwise the path fails closed: `STILL_OVERLAYS_NEED_G03_ANCHORS`, `OVERLAY_PRECOMPOSITE_MISMATCH`, `OVERLAY_PRECOMPOSITE_FRAME_MISMATCH` or `OVERLAY_PRECOMPOSITE_NOT_DERIVED_FRAME`.
- **v0.2 motion (`motion.compose.compose_motion_shot(..., overlays_composited=...)`):**
  - Persistent overlays pre-composited into the approved motion base frame are accepted when the set equals the contract and `frame_sha256 == motion_request.source_frame_sha256`.
  - Treatments on generated motion still fail closed (`MOTION_TREATMENTS_NEED_TRACKING_V02`, a G08 matter).
- **Shots without overlays:**
  - The new provenance and QC keys are added only when overlays are present.
  - The pre/post regression proof (`G03_REGRESSION_COMPARISON_v1.json`) shows the G02 output and deterministic core byte-identical.
  - The v0.2 motion MP4, WAV and provenance key set are identical.
  - So S027/S028/S029 re-renders would be unaffected.

## 6. Production-risk note (for the human approver, not a code gap)
On hybrid shots the provider animates the pre-composited smudge together with the face. Smudge fidelity during the motion must therefore be checked in human QC of the raw motion. This is the same review step S027/S028 used.
