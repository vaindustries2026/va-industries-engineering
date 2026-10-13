# EP005 base-frame batch preflight (2026-10-13)

READ-ONLY. Mikko & Lumi only. Anime Clip Farming not touched.

**Calls:** 0 image generation, 0 provider calls, 0 production writes.

**Local check:** one engineering check ran on a synthetic file in the scratchpad. It confirmed that G04 normalises a 2688×1520 PNG to 1920×1080 byte-identically on two runs.

## Sources
- APPROVED manifest `0325d35c`: camera, framing, animation and continuity per shot.
- APPROVED readiness `69bff641`: live Agent-008 specs.
- Live registry (GET): approved frames and the C1/world/prop references.
- G03/G08 contracts and audits, and the G08 factory matrix.

**Scripts:**
- `evidence/ep005/base_frame_preflight/base_frame_preflight.py` → `EP005_BASE_FRAME_PREFLIGHT_v1.json`
- `build_image_briefs.py` → `EP005_BASE_FRAME_IMAGE_BRIEFS_v1.json`

## 1–2. Frame families: live verification
The old estimate of 9 families, 8 needing generation, came from the scaleout plan table. **The live specs disagree:**

| Old grouping | Live spec | Effect |
|---|---|---|
| F-OVERSHOULDER-MIRROR (S003, S004, S005) | S003 is **over Mikko's shoulder**, S004 is **over Lumi's shoulder**, S005 is **front-facing** face-and-mirror | 3 different viewpoints |
| F-MEDIUM-TWOSHOT (S002, S017, S023, S026) | S002 needs the cloth **resting within reach** (pick-up start). S017 is front-facing with the mirror between the characters. S023 is three-quarter with Mikko facing the mirror and Lumi partial. S026 is S027's own opening state | 4 distinct frames (one of them reusable) |
| F-FACE-MIRROR (S010–S013, S016) | S010 and S016 are motion starts with the cloth or hand **raised** at different places. S012 is an over-Lumi's-shoulder view (matches S004). S013 is mirror-centric (matches S001) | regrouped |
| F-MACRO-REFLECTION (S018/S019) | the manifest says `image_generation_required=false`: "tighter macro reframe of the approved reflection artwork" | a crop of the S017 frame, not a new image |
| S026 needs a new frame | the approved `FRAME-EP005-S027-BASE-v01` is S026's exact successor state | **reusable, no generation** |

**Result:**

| Measure | Value |
|---|---|
| TOTAL_FRAME_FAMILIES | **16** (S001–S026 all covered, each shot in exactly one family) |
| FAMILIES_REQUIRING_NEW_IMAGE_GENERATION | **10**: F01–F10 |
| FAMILIES_DERIVABLE_FROM_APPROVED_ASSETS | **6**: F11–F16 |
| Derivable now from an existing approved asset | F11 only (`FRAME-EP005-S027-BASE-v01`) |
| Derivable only after future approvals | F15 (needs the F09 frame); F12, F13, F14, F16 (need future approved S007, S010, S014 or S020/S021 motion) |

| FRAME_FAMILY_ID | MEMBER_SHOTS | PRIMARY | CAN_BE_DERIVED | NEW_IMAGE_GENERATION_REQUIRED | code-ready members | blocked members |
|---|---|---|---|---|---|---|
| F01-MIRROR-OPEN | S001, S005, S013, S024, S025 | S001 | NO | YES | S001, S005, S013, S025 | S024 |
| F02-OVERSHOULDER-MIKKO | S003 | S003 | NO | YES | S003 | — |
| F03-OVERSHOULDER-LUMI | S004, S012 | S004 | NO | YES | S004, S012 | — |
| F04-FACE-MIRROR-3Q | S006, S007 | S006 | NO | YES | S006, S007 | — |
| F05-MIRROR-CLOTH-RAISED-CHEEK | S010 | S010 | NO | YES | S010 | — |
| F06-MIRROR-HAND-RAISED-MOUTH | S016 | S016 | NO | YES | S016 | — |
| F07-FACE-CLOTH-LOW | S014, S020 | S014 | NO | YES | S014, S020 | — |
| F08-MEDIUM-TWOSHOT-REACH | S002 | S002 | NO | YES | S002 | — |
| F09-MEDIUM-TWOSHOT-MIRROR-FRONT | S017 | S017 | NO | YES | S017 | — |
| F10-MEDIUM-MIKKO-FACING-MIRROR | S023 | S023 | NO | YES | S023 | — |
| F11-S027-START-REUSE | S026 | S026 | YES | NO | S026 | — |
| F12-S007-END | S008, S009 | S008 | YES | NO | S008 | S009 |
| F13-S010-END | S011 | S011 | YES | NO | S011 | — |
| F14-S014-END | S015 | S015 | YES | NO | — | S015 |
| F15-MACRO-REFLECTION | S018, S019 | S019 | YES | NO | S019 | S018 |
| F16-S020-S021-END | S021, S022 | S022 | YES | NO | S022 | S021 |

| Family | Scene / camera / poses / props / mirror (base frame) | Scale | Smudge state per shot (added by G03; base frames are CLEAN) | Treatments | Variance / human decision |
|---|---|---|---|---|---|
| F01-MIRROR-OPEN | CLOSE, front-facing into Lumi's hand mirror; reflection of Mikko's face large and centred; enough of Mikko's face and Lumi's holding hand; Mikko's hands at rest, cloth not in hand (resting out of frame / below frame); clean face, clean glass, clean reflection (G03 adds smudges, G08 measures the glass) | CLOSE | S001: CHEEK, NOSE, MOUTH; S005: CHEEK, NOSE, MOUTH; S013: NOSE, MOUTH; S024: none; S025: none | S025: MIRROR-REFLECTION, COMPLETION-POP-ACCENT | S025 calls for Lumi's soft smile and Mikko's settled gaze (held pose approved for S025): accept the neutral-attentive F01 expression for S025, else S025 needs its own generation. S024 is G06-blocked (shares the frame). |
| F02-OVERSHOULDER-MIKKO | CLOSE over MIKKO's shoulder toward the mirror; Mikko's face side-on plus his readable reflection; Lumi holds the mirror; cloth lowered within reach | CLOSE | S003: CHEEK, NOSE, MOUTH | — | — |
| F03-OVERSHOULDER-LUMI | CLOSE over LUMI's shoulder toward the mirror; Lumi's tiny hands holding the mirror angled; Mikko's reflection readable; Mikko attentive, cloth lowered, not pointing | CLOSE | S004: CHEEK, NOSE, MOUTH; S012: NOSE, MOUTH | S004: MIRROR-GLINT; S012: MIRROR-GLINT | S004 (3 marks) and S012 (2 marks) differ only in G03 overlays; the mirror tilt/angle animation is represented by the held pose + glint (Batch 0C approval). |
| F04-FACE-MIRROR-3Q | CLOSE front three-quarter: Mikko's physical anatomical-left cheek and its reflection both readable; Lumi holds the mirror; Mikko's free hand at rest, cloth held low in the other hand | CLOSE | S006: CHEEK, NOSE, MOUTH; S007: CHEEK, NOSE, MOUTH | S006: MIRROR-REFLECTION; S007: MIRROR-REFLECTION | motion start frame for both S006 (pointing) and S007 (cloth lift); S007 is "cheek-focused" but explicitly "consistent with the preceding face-and-mirror view". |
| F05-MIRROR-CLOTH-RAISED-CHEEK | CLOSE mirror-centric: tiny hand mirror and Mikko's reflected face; Mikko's cloth hand raised near the (clear) cheek, about to lower | CLOSE | S010: NOSE, MOUTH | S010: MIRROR-REFLECTION | continuity source S009 end is G11-blocked; an independent start frame unblocks S010. |
| F06-MIRROR-HAND-RAISED-MOUTH | CLOSE mirror-centric with face context; Mikko's hand (cloth) raised near the (clear) mouth area, about to lower | CLOSE | S016: NOSE | — | continuity source S015 end is G11-blocked; an independent start frame unblocks S016. |
| F07-FACE-CLOTH-LOW | CLOSE front-facing face-and-mirror; Mikko's face (closed mouth, nose) and the clean reflection readable; cloth held low in Mikko's hand, ready to approach; Lumi visibly holding/angling the mirror | CLOSE | S014: NOSE, MOUTH; S020: NOSE | S014: MIRROR-REFLECTION | motion start frame for S014 (toward mouth) and S020 (toward nose). |
| F08-MEDIUM-TWOSHOT-REACH | MEDIUM two-shot, straight-on/slight 3/4; Lumi holds the mirror; the cloth rests within Mikko's reach (NOT in hand) | MEDIUM | S002: CHEEK, NOSE, MOUTH | — | the old plan derived S002 from the shared two-shot frame; live specs give a different cloth state (pick-up start), so it is not derivable. |
| F09-MEDIUM-TWOSHOT-MIRROR-FRONT | MEDIUM two-shot front-facing, mirror visible between the characters, Mikko's reflection readable; Mikko's relaxed cloth hand | MEDIUM | S017: NOSE | — | source of the S018/S019 macro crop (F15). |
| F10-MEDIUM-MIKKO-FACING-MIRROR | MEDIUM three-quarter toward Mikko facing the hand mirror; Lumi's supporting hand / partial presence; lowered cloth; clean face and reflection | MEDIUM | S023: none | — | Batch 0C recorded S023 = S022 end state, but S022 is CLOSE and S023 MEDIUM: an S023 frame of its own removes the S021/G11 upstream dependency (human decision). |
| F11-S027-START-REUSE | S026 base = knees-up two-shot, clean face, cloth folded at chest height, Lumi holding the mirror upright | MEDIUM | S026: none | — | MEDIUM (spec) vs knees-up two-shot: same class as S027; human acceptance. |
| F12-S007-END | S007 end: cloth resting still on the marked cheek, three smudges as composited into the S007 base frame | CLOSE | S008: CHEEK, NOSE, MOUTH; S009: none | — | needs S007 motion first; the smudges are baked into the motion, so the G03 overlay set must be inherited through G04 (engineering gap G04_OVERLAY_CHAIN). S009 is G11-blocked. |
| F13-S010-END | S010 end: cloth lowered, clear cheek, mouth + nose smudges, readable reflection | CLOSE | S011: NOSE, MOUTH | S011: MIRROR-REFLECTION | live S011 framing is a "relaxed two-shot" while S010 is mirror-centric: human must accept the S010 end framing for S011, else S011 needs its own generation. Also needs G04_OVERLAY_CHAIN (overlays + reflection certificate). |
| F14-S014-END | S014 end | CLOSE | S015: none | — | S015 is G11-blocked: do not prioritise. |
| F15-MACRO-REFLECTION | tighter macro of the clean-glass reflection | MACRO | S018: NOSE; S019: NOSE | S018: MIRROR-GLINT | quality risk: a macro crop of a MEDIUM frame upscales the reflection (human check). S018 is G07-blocked; S019 (static macro hold) can use F15 without G07. |
| F16-S020-S021-END | cloth at the nose, then lowered from the clear nose | CLOSE | S021: none; S022: none | — | S021 is G11-blocked, so S022 waits on G11 unless a human accepts F07 (cloth low, clean face) as S022's start. |

**Shared across every family:**
- Scene: the approved bathroom (`WORLD-EP005-BATHROOM-MASTER-v01`).
- Base frames are **clean**: clean face and clean glass. G03 adds the smudges and G08 adds the treatments.
- Continuity source: the previous shot's end state, as listed under derivations.

## 3. Derivation and reuse map (nothing executed)
| Family | SOURCE_ASSET_ID | SOURCE_SHA | SOURCE_FRAME_INDEX | DERIVATION_METHOD | EXPECTED_OUTPUT | WHY_CONTINUITY_IS_VALID |
|---|---|---|---|---|---|---|
| F11-S027-START-REUSE | FRAME-EP005-S027-BASE-v01 | 81b841a6ab53219b26755c4e83a9777953a2d03f37213875e38691c112f0061b | — | REUSE the exact approved bytes as the S026 motion base frame (no pixel change; provider input as-is, like S027) | S026 base = knees-up two-shot, clean face, cloth folded at chest height, Lumi holding the mirror upright | S026 precedes S027 and the frame is S027's approved opening state: identical characters, props, clean face, setting and framing. S026's lift motion moves away from it, so the S026->S027 cut returns to this pose (human acceptance). S026 has no overlays or treatments. |
| F12-S007-END | future approved S007 raw motion | future approval | last frame used by the approved S007 shot | G04 derive_frame (exact index; crop/scale only if needed) | S007 end: cloth resting still on the marked cheek, three smudges as composited into the S007 base frame | manifest: S008 "Same face-to-mirror angle as S007"; protected hold of S007 end (visible_at_start(N)=visible_at_end(N-1)) |
| F13-S010-END | future approved S010 raw motion | future approval | last frame used by the approved S010 shot | G04 derive_frame | S010 end: cloth lowered, clear cheek, mouth + nose smudges, readable reflection | plan: "base = last frame of approved S010 raw motion" |
| F14-S014-END | future approved S014 raw motion | future approval | — | G04 derive_frame | S014 end | S015 continues S014 |
| F15-MACRO-REFLECTION | future approved F09 frame (S017) | future approval | — | deterministic crop (+ lanczos scale) of the mirror reflection region (G04 crop/scale on the still) | tighter macro of the clean-glass reflection | manifest S018: image_generation_required=false, "cut to a tighter macro reframe of the approved reflection artwork", production notes "Prepare the approved S017 artwork"; S019 holds the S018 macro view |
| F16-S020-S021-END | future approved S020 raw motion (S021) / S021 raw motion (S022) | future approval | — | G04 derive_frame | cloth at the nose, then lowered from the clear nose | S021 continues S020; S022 continues S021 |

**Not usable as base frames:**
- **C1 masters** (Mikko, Lumi, duo scale sheet, bathroom board): character and world sheets, used as generation references only.
- **Approved S028/S029 frames:** the cloth is on Mikko's shoulder and the mirror is lowered, which belongs to the end state only.
- **S027 raw-motion frames:** the same state as F11. Any frame of them is an alternative S026 source.

**New engineering gap found: G04_OVERLAY_CHAIN.**
- F12 (S008) and F13 (S011) start from the end frame of a motion whose base frame already had G03 smudges and, for S011, a G08 reflection baked in.
- G03 cannot place the smudges again, because they would be doubled.
- The G02 still path currently requires a G03 certificate bound to the held frame, so a G04 frame of such a motion fails closed (`STILL_OVERLAYS_NEED_G03_ANCHORS`).
- **Smallest fix (not built):** G04 provenance inherits the motion base frame's `overlays_composited` / `treatments_composited` through the approved motion's `source_frame_sha256`. Human raw-motion QC confirms the smudges are intact.
- **Until then:** S008 and S011 are code-ready only in principle; any other shots this affects stay blocked.

**Dependency improvements from the live specs (human decisions):**
- S005 and S013 no longer need S004's or S012's end frame (different camera), so they use F01.
- S019 can use the F15 crop of the F09 frame without waiting for S018/G07.
- S023 can use its own F10 frame instead of S022's end (removes the S021/G11 dependency).
- S022 could start from F07 instead of S021's end.

## 4. Paid image requirements (10 families; briefs frozen as text, NOT submitted)
Full EXACT_VISUAL_BRIEF text and every field is in `EP005_BASE_FRAME_IMAGE_BRIEFS_v1.json`. The character, prop and setting wording is copied verbatim from the **approved S027 Flare package**.

**Every brief specifies:**
- Characters: Mikko (ref 1) and Lumi (ref 2), on-model.
- Props: hand mirror (ref 4) and cloth (ref 5).
- Background: bathroom (ref 3), unchanged.
- **Clean face, zero smudges.**
- Mirror glass clean, with its full outline visible.
- A clean, readable, mirror-reversed reflection of Mikko where G03/G08 need it.
- Negatives: no smudges or marks, no glints or effects on the mirror, no text, no extra characters or props, no tilt or distortion.

| FRAME_FAMILY_ID | REQUIRED_SHOTS | CAMERA | MIRROR_STATE | brief SHA-256 |
|---|---|---|---|---|
| F01-MIRROR-OPEN | S001, S005, S013, S024, S025 | CLOSE, slightly front-facing view into the hand mirror, locked | clean glass, full outline visible, clean readable mirror-reversed reflection of Mikko (G03 REFLECTION marks + G08 PRESERVE) | `c4569262cb3ff27e…` (2433 chars) |
| F02-OVERSHOULDER-MIKKO | S003 | CLOSE, over Mikko's shoulder toward the mirror, locked | clean glass, full outline visible, clean readable mirror-reversed reflection of Mikko (G03 REFLECTION marks + G08 PRESERVE) | `0ef61b9f5b79f41b…` (2317 chars) |
| F03-OVERSHOULDER-LUMI | S004, S012 | CLOSE, over Lumi's shoulder toward the mirror and Mikko, locked | clean glass, full outline visible, clean readable mirror-reversed reflection of Mikko (G03 REFLECTION marks + G08 PRESERVE) | `ef2a65b0a0d17faf…` (2328 chars) |
| F04-FACE-MIRROR-3Q | S006, S007 | CLOSE, front three-quarter, locked | clean glass, full outline visible, clean readable mirror-reversed reflection of Mikko (G03 REFLECTION marks + G08 PRESERVE) | `cd5a04f82480597f…` (2290 chars) |
| F05-MIRROR-CLOTH-RAISED-CHEEK | S010 | CLOSE, slightly front-facing toward the mirror, locked | clean glass, full outline visible, clean readable mirror-reversed reflection of Mikko (G03 REFLECTION marks + G08 PRESERVE) | `7ed4a527917f736a…` (2292 chars) |
| F06-MIRROR-HAND-RAISED-MOUTH | S016 | CLOSE, aligned with the mirror reflection, locked | clean glass, full outline visible, clean readable mirror-reversed reflection of Mikko (G03 REFLECTION marks + G08 PRESERVE) | `72dbc185c15cee96…` (2267 chars) |
| F07-FACE-CLOTH-LOW | S014, S020 | CLOSE, front-facing, aligned with the mirror reflection, locked | clean glass, full outline visible, clean readable mirror-reversed reflection of Mikko (G03 REFLECTION marks + G08 PRESERVE) | `25061e5ca4383418…` (2273 chars) |
| F08-MEDIUM-TWOSHOT-REACH | S002 | MEDIUM, straight-on or slight three-quarter, locked | clean glass, full outline visible, plain sheen | `aea40c2d3a170115…` (2216 chars) |
| F09-MEDIUM-TWOSHOT-MIRROR-FRONT | S017, S018 (macro source), S019 (macro source) | MEDIUM, front-facing, locked | clean glass, full outline visible, clean readable mirror-reversed reflection of Mikko (G03 REFLECTION marks + G08 PRESERVE) | `5cd6922bba82e8c7…` (2282 chars) |
| F10-MEDIUM-MIKKO-FACING-MIRROR | S023 | MEDIUM, three-quarter toward Mikko and the mirror, locked | clean glass, full outline visible, clean readable mirror-reversed reflection of Mikko (G03 REFLECTION marks + G08 PRESERVE) | `fcae5de644c12bf9…` (2243 chars) |

**Normalisation:** Flare returned 2688×1520 for S027 (≈16:9, not exact). G03/G08 geometry is measured in frame pixels, and G08 refuses non-identity layout. Each approved generation therefore gets a deterministic G04 normalisation (crop 2688×1512 at y=4 → lanczos 1920×1080). This was verified byte-identical on a synthetic file. Human approval is of the normalised frame's SHA.

## 5. Provider and cost preflight (no call made)
| Item | Value |
|---|---|
| PROVIDER | Higgsfield API (official), the only approved EP005 image route on record |
| MODEL | Marketing Studio Image 2.5 Flare, `POST /marketing-studio/image/flare`, DIRECT mode |
| Body (S027 precedent) | `prompt`, `image_urls` (5 approved references), `aspect_ratio` 16:9, `resolution` 2k, `quality` high, `enhance_prompt` false, count 1 |
| CALLS_REQUIRED | all code-ready shots: **10** (one per F01–F10); recommended first batch: **3** |
| ESTIMATED_COST_PER_CALL | **UNKNOWN**: the provider never exposed Flare cost (S027 record) |
| ESTIMATED_TOTAL_COST | **UNKNOWN** |
| CREDIT_REQUIREMENT | **UNKNOWN**: the API-key balance is not readable through documented routes. Last recorded: $5.00 before S027 Flare; after that, S027 Seedance ≈$3.43 and S028 Seedance ≈$3.43 (Gilang confirmed balance each time). Gilang must confirm the balance before any submit. Per the S027 record, an insufficient balance is expected to return 403 without charge. |
| Reference URLs | the S027 upload URLs (10-09) must be HEAD-checked or re-staged (upload, readback SHA) before use |
| Output retention | the provider CDN deletes outputs after 7 days, so retrieval and preservation must follow approval promptly |

No pricing is guessed and no stale price is used.

## 6. BASE_FRAME_BATCH_GOVERNANCE_PLAN
1. **Authorisation:** an explicit Company Brain scope naming the families, max 1 POST each, a budget ceiling, and the balance confirmed by Gilang.
2. **Freeze:**
   - The final prompt per family, as `EXACT_VISUAL_BRIEF` (or an approved revision).
   - The exact request body JSON: canonical serialisation hashed with SHA-256 and recorded before submit.
   - The reference set: 5 approved assets, SHA re-verified, URL readback SHA = registry SHA.
3. **Pre-submit gate (same as S027, 12 checks):**
   - body SHA and prompt SHA
   - references
   - 16:9 / 2k / high / `enhance_prompt` false / count 1
   - exact key set
   - not previously submitted (ledger)
4. **One attempt per family:**
   - The ledger reserves the attempt **before** the POST.
   - **No retry, no alternate, no variation.**
   - A failure stops that family and is recorded.
5. **Retrieve and preserve exactly:**
   - One GET of the output URL.
   - Bytes hashed and kept unmodified as the raw output.
   - Then the G04 normalisation to 1920×1080 (two-run identical); the raw and normalised SHAs are both recorded.
6. **REVIEW:**
   - Each normalised frame is shown to Gilang as the exact file.
   - Status stays REVIEW; it is not registered or used downstream until **APPROVE by exact SHA**.
   - A rejection is terminal for that attempt; any regeneration needs a new authorisation.
7. **After approval** (separate authorised write): storage with no-overwrite and readback, then a registry row as SHOT_FRAME (BASE or DERIVED) bound to its shot(s). Family members each get their shot binding.

## 7. G03 records required after frame approval (none created)
39 shot×overlay entries. MIRROR_COPY_REQUIRED marks a REFLECTION placement needed because the frame shows Mikko's reflection (PRESERVE mode). "via G08 mode" means the shot also has the reflection treatment, so the REFLECTION copy comes from G03 under PRESERVE, or from the G08 copy under COMPOSITE.

| SHOT_ID | FRAME_FAMILY_ID | OVERLAY_ASSET | PLACEMENT_RECORD_REQUIRED | MIRROR_COPY_REQUIRED | HUMAN_MEASUREMENT_REQUIRED | shot code-ready |
|---|---|---|---|---|---|---|
| S001 | F01-MIRROR-OPEN | CHEEK | YES | YES | YES | yes |
| S001 | F01-MIRROR-OPEN | NOSE | YES | YES | YES | yes |
| S001 | F01-MIRROR-OPEN | MOUTH | YES | YES | YES | yes |
| S002 | F08-MEDIUM-TWOSHOT-REACH | CHEEK | YES | NO | YES | yes |
| S002 | F08-MEDIUM-TWOSHOT-REACH | NOSE | YES | NO | YES | yes |
| S002 | F08-MEDIUM-TWOSHOT-REACH | MOUTH | YES | NO | YES | yes |
| S003 | F02-OVERSHOULDER-MIKKO | CHEEK | YES | YES | YES | yes |
| S003 | F02-OVERSHOULDER-MIKKO | NOSE | YES | YES | YES | yes |
| S003 | F02-OVERSHOULDER-MIKKO | MOUTH | YES | YES | YES | yes |
| S004 | F03-OVERSHOULDER-LUMI | CHEEK | YES | YES | YES | yes |
| S004 | F03-OVERSHOULDER-LUMI | NOSE | YES | YES | YES | yes |
| S004 | F03-OVERSHOULDER-LUMI | MOUTH | YES | YES | YES | yes |
| S005 | F01-MIRROR-OPEN | CHEEK | YES | YES | YES | yes |
| S005 | F01-MIRROR-OPEN | NOSE | YES | YES | YES | yes |
| S005 | F01-MIRROR-OPEN | MOUTH | YES | YES | YES | yes |
| S006 | F04-FACE-MIRROR-3Q | CHEEK | YES | via G08 mode | YES | yes |
| S006 | F04-FACE-MIRROR-3Q | NOSE | YES | via G08 mode | YES | yes |
| S006 | F04-FACE-MIRROR-3Q | MOUTH | YES | via G08 mode | YES | yes |
| S007 | F04-FACE-MIRROR-3Q | CHEEK | YES | via G08 mode | YES | yes |
| S007 | F04-FACE-MIRROR-3Q | NOSE | YES | via G08 mode | YES | yes |
| S007 | F04-FACE-MIRROR-3Q | MOUTH | YES | via G08 mode | YES | yes |
| S008 | F12-S007-END | CHEEK | NO (inherited) | YES | NO | yes |
| S008 | F12-S007-END | NOSE | NO (inherited) | YES | NO | yes |
| S008 | F12-S007-END | MOUTH | NO (inherited) | YES | NO | yes |
| S010 | F05-MIRROR-CLOTH-RAISED-CHEEK | NOSE | YES | via G08 mode | YES | yes |
| S010 | F05-MIRROR-CLOTH-RAISED-CHEEK | MOUTH | YES | via G08 mode | YES | yes |
| S011 | F13-S010-END | NOSE | NO (inherited) | NO | NO | yes |
| S011 | F13-S010-END | MOUTH | NO (inherited) | NO | NO | yes |
| S012 | F03-OVERSHOULDER-LUMI | NOSE | YES | YES | YES | yes |
| S012 | F03-OVERSHOULDER-LUMI | MOUTH | YES | YES | YES | yes |
| S013 | F01-MIRROR-OPEN | NOSE | YES | YES | YES | yes |
| S013 | F01-MIRROR-OPEN | MOUTH | YES | YES | YES | yes |
| S014 | F07-FACE-CLOTH-LOW | NOSE | YES | via G08 mode | YES | yes |
| S014 | F07-FACE-CLOTH-LOW | MOUTH | YES | via G08 mode | YES | yes |
| S016 | F06-MIRROR-HAND-RAISED-MOUTH | NOSE | YES | YES | YES | yes |
| S017 | F09-MEDIUM-TWOSHOT-MIRROR-FRONT | NOSE | YES | YES | YES | yes |
| S018 | F15-MACRO-REFLECTION | NOSE | YES | YES | YES | blocked |
| S019 | F15-MACRO-REFLECTION | NOSE | YES | YES | YES | yes |
| S020 | F07-FACE-CLOTH-LOW | NOSE | YES | YES | YES | yes |

## 8. G08 records required after frame approval (none created)
| SHOT_ID | FRAME_FAMILY_ID | TREATMENT_TYPE | MIRROR_REGION_RECORD_REQUIRED | GLINT_RECORD_REQUIRED | POP_RECORD_REQUIRED | REFLECTION (mode/mapping) | HUMAN_MEASUREMENT_REQUIRED | audio sync | shot |
|---|---|---|---|---|---|---|---|---|---|
| S004 | F03-OVERSHOULDER-LUMI | MIRROR-GLINT | YES | YES | NO | NO | YES | SFX-LUMI-CLUE-CHIME | yes |
| S006 | F04-FACE-MIRROR-3Q | MIRROR-REFLECTION | YES | NO | NO | YES | YES | — | yes |
| S007 | F04-FACE-MIRROR-3Q | MIRROR-REFLECTION | YES | NO | NO | YES | YES | — | yes |
| S010 | F05-MIRROR-CLOTH-RAISED-CHEEK | MIRROR-REFLECTION | YES | NO | NO | YES | YES | — | yes |
| S011 | F13-S010-END | MIRROR-REFLECTION | YES | NO | NO | YES | YES | — | yes |
| S012 | F03-OVERSHOULDER-LUMI | MIRROR-GLINT | YES | YES | NO | NO | YES | — | yes |
| S014 | F07-FACE-CLOTH-LOW | MIRROR-REFLECTION | YES | NO | NO | YES | YES | — | yes |
| S018 | F15-MACRO-REFLECTION | MIRROR-GLINT | YES | YES | NO | NO | YES | — | blocked (G07) |
| S025 | F01-MIRROR-OPEN | MIRROR-REFLECTION | YES | NO | NO | YES | YES | SFX-COMPLETION-POP-v01 | yes |
| S025 | F01-MIRROR-OPEN | COMPLETION-POP-ACCENT | YES | NO | YES | NO | YES | SFX-COMPLETION-POP-v01 | yes |

The mirror-glass ellipse is measured once per family frame and reused by every member's record. F01 serves S025; F03 serves S004 and S012; F04 serves S006 and S007.

## 9. Dialogue dependency (no TTS)
| FRAME_FAMILY_ID | SHOTS | MIKKO_LINES_REQUIRED | LUMI_LINES_REQUIRED | TOTAL_TTS_LINES |
|---|---|---|---|---|
| F01-MIRROR-OPEN | S001, S005, S013, S024, S025 | 1 (S001: Berries on my face! I want to feel fresh.) | 2 (S001: I see three little smudges.; S025: Cheek, mouth, nose. All clear.) | 3 |
| F02-OVERSHOULDER-MIKKO | S003 | 0 | 1 (S003: Let’s look for one little spot.) | 1 |
| F03-OVERSHOULDER-LUMI | S004, S012 | 0 | 4 (S004: A glint on his cheek!; S004: Find the next smudge!; S012: By your mouth!; S012: Find the next smudge!) | 4 |
| F04-FACE-MIRROR-3Q | S006, S007 | 3 (S006: This cheek. I’ll try a gentle wipe.; S007: Wipe your cheek with me. Soft and slow.; S007: Can you pretend to wipe your cheek?) | 0 | 3 |
| F05-MIRROR-CLOTH-RAISED-CHEEK | S010 | 0 | 1 (S010: That cheek is clear. Two smudges left.) | 1 |
| F06-MIRROR-HAND-RAISED-MOUTH | S016 | 0 | 1 (S016: That spot is gone. One is left.) | 1 |
| F07-FACE-CLOTH-LOW | S014, S020 | 2 (S014: I’ll slow my hand. One little wipe.; S020: My nose! I’ll wipe just that spot.) | 0 | 2 |
| F08-MEDIUM-TWOSHOT-REACH | S002 | 1 (S002: Where shall I try first?) | 0 | 1 |
| F09-MEDIUM-TWOSHOT-MIRROR-FRONT | S017 | 0 | 0 | 0 |
| F10-MEDIUM-MIKKO-FACING-MIRROR | S023 | 0 | 0 | 0 |
| F11-S027-START-REUSE | S026 | 1 (S026: One little spot at a time!) | 0 | 1 |
| F12-S007-END | S008, S009 | 0 | 0 | 0 |
| F13-S010-END | S011 | 0 | 0 | 0 |
| F14-S014-END | S015 | 0 | 0 | 0 |
| F15-MACRO-REFLECTION | S018, S019 | 0 | 2 (S018: One spot left!; S018: Find the next smudge!) | 2 |
| F16-S020-S021-END | S021, S022 | 0 | 1 (S022: Your nose is clear, too.) | 1 |

**Total: 8 Mikko + 12 Lumi = 20 lines** (S001–S026; includes lines for blocked shots).

Dialogue and frames are independent inputs, so the two batches can run **in parallel**. Both voices are already approved: Mikko is Teddy Twinkle and Lumi is Lola.

## 10. RECOMMENDED_FIRST_FRAME_BATCH
| Item | Value |
|---|---|
| Families | F01-MIRROR-OPEN, F03-OVERSHOULDER-LUMI, F09-MEDIUM-TWOSHOT-MIRROR-FRONT (generate) + F11 (reuse S027 frame) + F15 (crop of F09) |
| NUMBER_OF_FRAME_FAMILIES | 5 (3 generated, 2 derived) |
| IMAGE_CALLS_REQUIRED | **3** |
| SHOTS_UNLOCKED | **9**: S001, S004, S005, S012, S013, S017, S019, S025, S026 |
| Stills (no video spend) | S004, S005, S012, S013, S017, S019, S025 |
| Motion (separate Seedance authorisation later) | S001, S026 |
| TTS needed for these shots | 8 lines: Mikko 2, Lumi 6 |
| G03 records / G08 records | S001, S004, S005, S012, S013, S017, S019 / S004, S012, S025 |
| ESTIMATED_COST | **UNKNOWN** (3 Flare calls; per-call cost not exposed) |

**WHY_THIS_BATCH_FIRST:**
- **Yield:** 3 paid images yield 9 shots, three per call. F01 alone serves 4 code-ready shots (S001, S005, S013, S025).
- **No video spend:** 7 of the 9 shots are deterministic stills, so they need no video spend and can auto-batch right after approval.
- **No new engineering:** the chosen families avoid G04_OVERLAY_CHAIN entirely, so no engineering is needed before production.
- **No extra image cost for S026:** S026 is unlocked by reusing an approved frame.
- **Records:** G08 is exercised on S004/S012 (glint) and S025 (reflection + pop).
- **Second batch candidates:** F04 (S006, S007), F07 (S014, S020), F02, F08, F05, F06 and F10. These are mostly provider-motion shots, so each also needs Seedance.

## 11. Engineering-blocker interaction
| Family | Members | Prioritised? |
|---|---|---|
| F14-S014-END | only S015 (G11) | **never prioritised** |
| F01 | includes S024 (G06) | shared with 4 code-ready shots; no extra cost |
| F15 | includes S018 (G07) | shared with code-ready S019; derived, no cost |
| F12, F16 | include S009 and S021 (G11) | derived; prioritised only for their code-ready members after their source motions exist |

No paid frame serves only blocked shots.

## 12. Factory automation after frame approval
**AUTO_BATCH_READY_STEPS** (Agent-008, deterministic, zero spend, outputs REVIEW):
1. **Validate frame SHA:** G02/G03/G08 `verify_file` against the approved registry SHA, plus the normalised 1920×1080 identity check.
2. **G03:** `place_overlays` per shot, from its approved placement record (several shots share one family frame), then a two-run identical check.
3. **G08:**
   - `apply_reflection` (PRESERVE certificate / COMPOSITE frame).
   - `plan_timed` validation of glint/pop geometry, windows and audio sync.
4. **Dialogue:** `resolve_dialogue` + G09 `govern_dialogue_timing` against approved, hash-bound clips.
5. **Motion packages:** S027/S028 precedent (prompt v-file, frozen body, request SHA, attempt ledger, `overlays_composited` + `treatments_composited` bound to the uploaded frame). Packages are prepared only; nothing is submitted.
6. **Render stills:** `compose_still_shot` with the treatment record, two renders.
7. **QC:** automatic QC (frames, fps, duration, black frames, audio peak, events) plus byte-identity of the two renders.
8. **Store as REVIEW:** storage with no-overwrite and readback; registry rows as REVIEW. This needs a write authorisation scoped to the batch.
9. **Batch review manifest for Gilang:** one row per shot (exact MP4 SHA, frame/record/clip SHAs, QC, provenance), APPROVE/REJECT per exact SHA.

Engineering to add before automation: a small batch driver around these existing functions, plus G04_OVERLAY_CHAIN for S008/S011.

**HUMAN_GATES_REMAINING:**
1. Authorise the paid image batch (scope, budget, balance confirmation).
2. APPROVE or REJECT each generated frame by exact normalised SHA.
3. Approve the family-variance decisions:
   - S025 expression on F01
   - S011 framing from S010's end
   - S023 using F10
   - S022 using F07
   - S019 using the F15 crop
4. Approve each G03 placement record and G08 treatment record. These are measured from the approved frames; an automated proposal is possible, but approval is human.
5. Authorise the TTS batch and approve the clips.
6. Authorise each Seedance generation (motion shots) and approve the raw motion.
7. Approve each assembled shot by exact SHA.
8. Authorise production storage and registry writes for the batch.

## Non-regression / safety
- **Calls:** no provider, Higgsfield, ElevenLabs, Seedance, image/video generation, Agent-006 or Agent-007.
- **Production:** no writes. No script, manifest, readiness or status change. S027/S028/S029 untouched.
- **Reads:** registry and manifest via GET only.
- **Repo:** only the evidence files listed here and the changelog were committed.
