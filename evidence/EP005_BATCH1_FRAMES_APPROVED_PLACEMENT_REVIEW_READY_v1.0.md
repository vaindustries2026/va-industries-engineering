# EP005 Batch 1 — Frames Approved, G03/G08 Placement Review Ready

**Decision source:** Company Brain human decision, 2026-10-20.
- Accepted generation commit: `c241be36de8019439849da50e11ca541e2381aba`.
- Governance mode: PRODUCT-FIRST production tolerance.
- F01, F03 and F15 frame families are **CLOSED_APPROVED**. v03 needs an explicit reopening.

## Pixel bridge: PASS × 3
Method: `SHA256(Image.open(f).convert('RGB').tobytes())`, computed on both normalisation runs of each local candidate.
- F01 v02: `c963f4d2…e0fd`
- F03 v02: `df5e11f9…c253`
- F15 dedicated: `671b79d2…5deba`

All three equal the Company Brain reviewed hashes.

## Approvals, preserved and registered (S027 / F09 pattern)
Each frame was:
- stored with `x-upsert: false`, then read back with a matching SHA;
- registered with a single insert (no upsert), then the row was read back.

| Frame | Approved SHA | Storage object | Registry id | Family binding |
|---|---|---|---|---|
| FRAME-EP005-F01-BASE-CAND-v02 | 5710032060494eea80bb6ac95bb31a3a1345caadfb8f711fa118de4ebcb1a845 | 289843fa-f029-4df5-9561-42029fd537a0 | 584d5e7a-c9eb-46f8-818f-d97a3c970104 | F01-MIRROR-OPEN, primary S001; members S001, S005, S013, S024 (G06-blocked), S025 |
| FRAME-EP005-F03-BASE-CAND-v02 | ac93ecfb986dbed9ea32525dc8be7851cb790f6b59c656d7cd41815588ed5410 | d3d66c00-261b-48d3-a149-8dc1dbe9a810 | 12ba1870-4fae-4e6f-a53a-4d2444a15f59 | F03-OVERSHOULDER-LUMI, primary S004; members S004, S012 |
| FRAME-EP005-F15-BASE-CAND-v02 | e7a3936d8ab6f3fff5d2d39a5b349f6159f4eeb22953dbf715f45df8dfbdc690 | 048071bb-10d8-4676-9c32-a4fbda281751 | ca534cfb-ba09-4758-b01a-7893c05563aa | F15-MACRO-REFLECTION (now GENERATE), primary S019; S018 G07-blocked |
| FRAME-EP005-S026-BASE-REUSE-v01 | 81b841a6ab53219b26755c4e83a9777953a2d03f37213875e38691c112f0061b | none (points at the existing S027 object) | ce83a8ae-67e9-4520-bdbe-e0f8b4e8d545 | F11-S027-START-REUSE: REUSE_EXISTING for S026; no crop, scale or edit; S027 row untouched |

Every row records:
- `SHOT_FRAME / BASE_FRAME`, status APPROVED, `human_decision` / `human_approval` APPROVED, `approved: true`;
- full Flare + normalisation provenance;
- the pixel-bridge proof;
- the **accepted human variances**:
  - F01: Mikko's rear head and shoulder at frame-left, accepted as an over-the-shoulder element.
  - F03: mirror glass at about 34% of frame height, and a beside-Lumi camera.
  - F15: the top petal close to the upper edge.

F09 is unchanged. The historical F15 crop evidence is kept.

## Batch Driver PLAN_ONLY v3 (deterministic, plan `cf146f24…`)
- Families: F01, F03, F09 and F15 are APPROVED; F11 is APPROVED_REUSE.
- **All frame gates are cleared.**

| Shots | State |
|---|---|
| S001, S004, S005, S012, S013, S017, S019 | WAITING_FOR_G03_RECORD |
| S025 | WAITING_FOR_G08_RECORD |
| S026 | WAITING_FOR_DIALOGUE |

## G03 / G08 candidates (scratch only; nothing approved or registered)
- **Records:** `evidence/ep005/batch1_placement/`
  - `B1_PLACEMENT_CANDIDATES_v1.json` (geometry, landmarks, glass)
  - `B1_PLACEMENT_REVIEW_PACKET_v1.json`
- **Previews:** rendered by the **unchanged** G03/G08 modules. The candidate record is passed in memory with a preview-only approval flag.

| Shot | Family | Frame SHA | State | G03 placements (R = reflection, F = real face) | G08 |
|---|---|---|---|---|---|
| S001 | F01 | `571003206049…` | WAITING_FOR_G03_RECORD | CHEEK R (748,538) w96; NOSE R (907,510) w63; MOUTH R (1001,558) w57 | — |
| S004 | F03 | `ac93ecfb986d…` | WAITING_FOR_G03_RECORD | CHEEK R (1055,635) w82; NOSE R (1152,588) w46; MOUTH R (1230,623) w49; CHEEK F (800,478) w100; NOSE F (648,471) w72; MOUTH F (521,543) w77 | glint (1062,628) 36px → CHEEK, frames 12..19 |
| S005 | F01 | `571003206049…` | WAITING_FOR_G03_RECORD | CHEEK R (748,538) w96; NOSE R (907,510) w63; MOUTH R (1001,558) w57 | — |
| S012 | F03 | `ac93ecfb986d…` | WAITING_FOR_G03_RECORD | NOSE R (1152,588) w46; MOUTH R (1230,623) w49; NOSE F (648,471) w72; MOUTH F (521,543) w77 | glint (1230,623) 36px → MOUTH, frames 24..31 |
| S013 | F01 | `571003206049…` | WAITING_FOR_G03_RECORD | NOSE R (907,510) w63; MOUTH R (1001,558) w57 | — |
| S017 | F09 | `d442b0f7ac95…` | WAITING_FOR_G03_RECORD | NOSE R (991,450) w29; NOSE F (668,376) w50 | — |
| S019 | F15 | `e7a3936d8ab6…` | WAITING_FOR_G03_RECORD | NOSE R (959,533) w65 | — |
| S025 | F01 | `571003206049…` | WAITING_FOR_G08_RECORD | — | reflection PRESERVE (clean) + pop gain 0.1 frames 12..18 |
| S026 | F11 | `81b841a6ab53…` | WAITING_FOR_DIALOGUE | — | — |

**Placement method**
- **Landmarks:** measured on each approved frame using gridded zooms plus dark/pink blob detection.
- **Mirror glass:** a flood fill of the clear glass inside the pink ring, as an axis-aligned ellipse with a 3 px margin.
- **Sizes, one rule for all frames:**
  - cheek = 0.50 × eye distance;
  - mouth = 0.30 × eye distance;
  - nose = 0.90 × nose width (overrides noted per region).
- **Mirror rule:** REFLECTION marks are mirrored, with Mikko's anatomical left on image-left in the mirror.

**Checks passed:**
- G03: no overlaps, no clipping, no pixel change outside the marks.
- G08: the glint lies inside the glass and is bound to a reflected target mark.
- S025: PRESERVE reflection with zero reflected overlays (clean reveal).
- Pop gain 0.10 (at most 0.12), confined to the glass.

**Totals**
- G03_CANDIDATE_RECORDS = 7 (21 placements).
- G08_CANDIDATE_RECORDS = 3.
- AMBIGUOUS_RECORDS = 6 (S001, S004, S005, S012, S013, S017), covered by two decisions:
  1. **FACE surface (S004, S012, S017):** the manifest names the reflection only, but Mikko's real face is visible. Proposed: matching FACE marks (shown in the previews).
  2. **Mouth side (S001, S004, S005, S012, S013):** the spec says "beside, not inside, the mouth" with no side. Proposed: the anatomical RIGHT corner, opposite the cheek mark. The non-canon Phase-0 stand-in used the left side, which collides with the cheek mark at production scale.

**Proposed timing** (separate audio-timing gate):
- S004: glint at frames 12–19, with the clue chime at 0.5 s.
- S012: glint at frames 24–31.
- S025: pop at frames 12–18, with the completion pop at 0.5 s.

The S004/S012 G08 records are bound to the G03 preview output SHA. If the G03 record changes, they must be re-bound.

**Ready after record approval:**
- READY_FOR_LOCAL_RENDER: S005, S013, S017, S019.
- Then waiting on dialogue or timing: S001, S004, S012, S025.

## Dialogue packet (no ElevenLabs): `B1_DIALOGUE_REQUIREMENT_PACKET_v1.json`
- Voices: Mikko `XjGYkUkzth8BPs29fmcV` (Teddy Twinkle), Lumi `f9imtLc2jfOLXtqe3Ihb` (Lola). These are the approved voices of the registered S027/S028 dialogue.
- Estimates use the rates of the approved S028 clips.
- 8 lines: Mikko 2, Lumi 6.
- **Timing risks:**
  - S001 is about 6.1 s of speech in a 6.0 s shot.
  - S004 is about 5.0 s, including the chime offset, in a 5.0 s shot.

## Side-effect audit
**Zero:**
- new provider calls of any kind (image, video, Higgsfield, Seedance, ElevenLabs);
- Agent-006 and Agent-007 runs;
- G03/G08 production records, and final renders.

**Unchanged:**
- script, manifest and readiness (both APPROVED);
- S027, S028, S029 (stored bytes re-hash equal; rows unchanged).

**Production writes (exactly the allowed ones):**
- 3 storage objects and 3 registry rows: F01 v02, F03 v02, F15 v02.
- 1 F11 reuse row (no storage object).

**Tests:** 205/205 OK (no agent008 code changed).

Anime Clip Farming: untouched.
