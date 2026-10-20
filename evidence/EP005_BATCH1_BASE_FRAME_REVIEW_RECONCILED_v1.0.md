# EP005 Batch 1 — Base Frame Human Review Reconciled (F01 rejected, F03 rejected, F09 approved, F15 in review)

**Decision source:** Company Brain human review of the frames in commit `6506ed7cbb3b42ebbfa8c670aa24c2543d058df3`.

**Evidence files:**
- `evidence/ep005/batch1_base_frames/`:
  - `B1_REVIEW_RECONCILIATION_v1.json`
  - `B1_REVIEW_LEDGER_v1.jsonl`
  - `F09_REGISTRY_ROW_INSERTED_v1.json`
  - `FRAME-EP005-F15-BASE-CAND-v01_REVIEW_CANDIDATE.json`
  - `B1_V02_CORRECTION_PACKAGES_v1.json`
  - Scripts: `b1_review_decisions.py`, `build_b1_v02_packages.py`
- `evidence/agent008/batch_driver/`:
  - `FIRST_BATCH_PLAN_v2.json`
  - Script: `first_batch_plan_v2.py`

## 1. Pixel-equivalence bridge
The pixel hash is `SHA256(Image.open(f).convert('RGB').tobytes())`, computed on each local G04 normalised file. Both runs of each family give the same values.

| Family | File SHA (authoritative) | RGB pixel SHA (local) | Company Brain reviewed RGB | Bridge |
|---|---|---|---|---|
| F01 | c191a513…1e10 | a61459c5cfdb1b178f1a641f079914ca8c3151f9475c3dbacc02585c88e7831b | same | PASS |
| F03 | e8571476…c5968 | ff22ecffe85e866cd6727fc2bc97a71b5f3f8c5f456c30f8c4c48b18615480df | same | PASS |
| F09 | d442b0f7…f13e | bf6ee47c083ba484ce8174b6bde078d6f5bc196abbe15d4c52cbedd03027e117 | same | PASS |

## 2–4. Decisions (bound to the exact normalised file SHA)

**F01: REJECTED** (`c191a513a4987cc0be6ea713f8a8dc88566c952db0250b122270786e0aa11e10`)
- Reasons: Lumi's arm and hand drift from canon (elongated and limb-like), and Mikko is seen mostly from behind.
- Not approved. Not to be used for G03, G08 or as a production base frame.

**F03: REJECTED** (`e8571476c5be0b1c263c4b9c3be2c155ed1af265c87aa0c18786b69b409c5968`)
- Reasons: Lumi has extra lower lobes, and the mirror glass is too small for G03/G08.
- Same restrictions as F01.

**F09: APPROVED** (`d442b0f7ac9524319fb2d171b7891e35ea94b4877f131de77f2bced74050f13e`)
- Company Brain accepted the identities, scale, bathroom, composition, mirror placement, props and clean-face state for S017.

Neither rejected candidate was ever registered. No replacement generation is authorised.

## F09 preservation (S027 pattern, pixels unaltered)

**Storage**
- Pre-check: the storage key, `asset_id` and `asset_name` were all absent.
- Upload: `POST production-assets/visual/production/ep005/frames/FRAME-EP005-F09-BASE-CAND-v01.png`, `x-upsert: false`. Result: HTTP 200, object `6271cefa-0109-4ca0-b7f1-d8d5c639770b`.
- Readback: SHA-256 matches, 3,936,085 bytes.

**Registry**
- Insert: a single `POST /rest/v1/asset_registry` (an insert, not an upsert). Result: HTTP 201, id `c28c7904-51ae-42e4-b7e1-4a44d93d9ba3`.
- Row: `SHOT_FRAME / BASE_FRAME`, status APPROVED, `human_decision` / `human_approval` APPROVED, `approved: true`, `approved_sha256` = d442b0f7…f13e, `shot_id` S017, `frame_family` F09.
- Provenance recorded in the row:
  - Flare request `5136a0dd-2d90-4429-90a9-d42e37f3f097`
  - raw provider SHA `dd940326…1efe`
  - prompt and body SHAs
  - the six reference SHAs
  - normalisation method and two-run proof
  - pixel-equivalence proof
  - Company Brain approval
- Row readback: verified.

## 5. F15 — REVIEW candidate (not approved)

**Governed spec:** `DERIVE_CROP` of the approved F09, crop `MEASURED_AFTER_F09_APPROVAL`, scale to 1920×1080.

**Crop measurement**
- The mirror's pink flower-head bounding box was measured on the approved pixels as x 836–1186, y 234–583 (pinned).
- Rule: the smallest exact 16:9 crop that holds the full head height plus a 16 px margin, centred on the head.

**Results**

| Field | Value |
|---|---|
| F15_SOURCE_SHA | d442b0f7ac9524319fb2d171b7891e35ea94b4877f131de77f2bced74050f13e (registry c28c7904) |
| F15_CROP_GEOMETRY | {x: 667, y: 215, w: 688, h: 387} |
| Scale | lanczos+accurate_rnd+full_chroma_int+bitexact to 1920×1080 (upscale ×2.79) |
| F15_OUTPUT_SHA_A | c5c5467598718be66e6b107ce8b83be5f7376a7ef3985e817af31d3502edc5e4 |
| F15_OUTPUT_SHA_B | c5c5467598718be66e6b107ce8b83be5f7376a7ef3985e817af31d3502edc5e4 |
| F15_DETERMINISM_PASS | true |
| F15_CANONICAL_RGB_SHA | bb17401eac3f0479ebc1bbceb44927e342fc91c6d2bf07537386c6b59ca33f40 |
| F15_DIMENSIONS | 1920×1080 |

- Only the crop and the deterministic resize were applied: no enhancement, sharpening or retouch.
- It remains a local REVIEW candidate, with no registry row and no storage.

## 6–7. Locked correction packages (NOT submitted; 0 generations authorised)

| Package | PROMPT_SHA256 | REQUEST_BODY_SHA256 |
|---|---|---|
| F01 v02 | 6e3d11009d290121c19be55b3cc46fc2e91b3918805be42ce3e5159d7ca5d5c3 | f46b79b834b13b2a3384b869d1ade2f46ca34a76290dbe397665f3d1e0cb2f30 |
| F03 v02 | 4e68b6a408cc259d672ef3158a870cb0a3d35738b1f40cafd9df4d6855832782 | a5a5bef2fa28063daf425c97f1622634600dd42b5134f0fb630b4295ee955a2c |

Each package is the v1 prompt from `c6a7dd2` with two exact-once edits, both recorded verbatim in the JSON.

**F01 v02**
1. The composition asks for Mikko's whole face to be front-facing, large and readable in the centred reflection. Only a small edge of the real cheek and shoulder shows; there is no dominant rear view.
2. An added Lumi canon-silhouette sentence: a round orb with no legs, no lobes and no long or noodle-like arms; tiny hands close to the body with a small reach for the handle. It also restates Mikko's canonical proportions.

**F03 v02**
1. The composition asks for the mirror held close to camera, with the clean glass at least about 40% of the frame height, the full outline visible, and cheeks, nose and mouth readable. The over-Lumi's-shoulder camera is unchanged.
2. An added Lumi canon-silhouette sentence: a smooth orb with no legs, no lobes and no extra rounded appendages; tiny hands only.

**Unchanged:** the model, endpoint, settings, `enhance_prompt` false, the six references (same order and transport copies) and the scale sentence.

**Expiry:** the reference copies expire 2026-10-28 00:00 GMT. After that the packages must be re-locked and re-approved.

## 9. Batch Driver PLAN_ONLY v2 (deterministic, plan d15d8e5e…)

| SHOT | STATE | NEXT_HUMAN_GATE | NEXT_AUTOMATED_STAGE |
|---|---|---|---|
| S001 | WAITING_FOR_BASE_FRAME | authorise F01 base-frame generation (paid) | G04 normalise + hash |
| S004 | WAITING_FOR_BASE_FRAME | authorise F03 base-frame generation (paid) | G04 normalise + hash |
| S005 | WAITING_FOR_BASE_FRAME | authorise F01 base-frame generation (paid) | G04 normalise + hash |
| S012 | WAITING_FOR_BASE_FRAME | authorise F03 base-frame generation (paid) | G04 normalise + hash |
| S013 | WAITING_FOR_BASE_FRAME | authorise F01 base-frame generation (paid) | G04 normalise + hash |
| S017 | WAITING_FOR_G03_RECORD | approve the G03 placement record measured on the approved F09 frame | apply G03 once approved |
| S019 | WAITING_FOR_FRAME_APPROVAL (= waiting for F15 human approval) | APPROVE/REJECT F15 by exact SHA | — |
| S025 | WAITING_FOR_BASE_FRAME | authorise F01 base-frame generation (paid) | G04 normalise + hash |
| S026 | WAITING_FOR_FRAME_APPROVAL (unchanged) | approve the S027 reuse binding by exact SHA | — |

Driver v0.1 gives the blocker for a family whose candidate was rejected as `FAMILY_FRAME_NOT_GENERATED`. The state is correct; only the label is imprecise. No code was changed.

## 10. Side-effect audit
**Outcomes:** F01 REJECTED, F03 REJECTED, F09 APPROVED, F15 REVIEW only.

**Zero:** new image generations (F01_V02 = 0, F03_V02 = 0) and provider calls of any kind (Flare, Seedance, ElevenLabs, video).

**Not used:** Agent-006, Agent-007.

**Unchanged:**
- Script, manifest and readiness (both APPROVED).
- S027, S028 and S029 (stored bytes re-hash equal).

**Production writes:** only the authorised F09 storage object and its registry row.

**Not created:** G03 or G08 records.

**Tests:** 205/205 OK.

Anime Clip Farming: untouched.

## Remaining human gates
1. **F15:** APPROVE or REJECT by `c5c5467598718be66e6b107ce8b83be5f7376a7ef3985e817af31d3502edc5e4`.
2. **F01 v02 / F03 v02:** a new spend authorisation is required before any submit.
3. **S017:** the G03 placement record, measured on the approved F09, is next.
