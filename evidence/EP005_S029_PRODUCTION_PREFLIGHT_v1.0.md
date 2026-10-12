# EP005 S029: read-only production preflight (2026-10-12)

Mikko & Lumi only. Read-only throughout:
- No production writes, provider calls, TTS, generation or renders.
- No code changes, no Agent-006/007.

Authority (all APPROVED, read live):
- Script v05 `6498ea8d`
- Manifest `0325d35c` (`shot_plans[S029]`)
- Readiness `69bff641`
- Agent-008 `agent008.episode` spec built from those rows

S028 is closed: `SHOT-EP005-S028-ASSEMBLED-v01` `1d5dfabd…7cc0`.

## 1. Authoritative S029 spec
| Field | Value |
|---|---|
| SHOT_ID | S029 (section COMFORT, index 29; last shot) |
| SHOT_DURATION | 6.0 s (episode 114.0 → 120.0 s) |
| FRAME_COUNT | 144 |
| FPS | 24 |
| SHOT_PURPOSE | "Final six-second safe-state ending hold, not an additional response pause." |
| ACTION | Script: "Both relax their shoulders and remain comfortably settled, with only subtle breathing." Manifest: "Create a still ending composition with only minimal composited breathing and natural settling in the shoulders." Method COMPOSITE; `video_generation_required: false`. |
| CAMERA | Locked-off, eye-level, front-facing; "Calm close two-shot"; framing_scale CLOSE; no push-in, pan, tilt or rack focus |
| CHARACTERS_PRESENT | Mikko (settled beside Lumi, relaxed, content, clean face visible); Lumi (settled, warm, holds mirror, cloth resting; no further pat or action) |
| PROPS_PRESENT | Tiny hand mirror and soft cloth: "rest quietly in Lumi's lap"; mirror glass clean |
| DIALOGUE | **None** (`voice_lines: []`, `voice_required: false`) |
| AUDIO_REQUIREMENTS | "Quiet background ambience only". Mapped ambience: **AMB-BATHROOM-QUIET-v01**. No music; no closing sting. |
| SFX_REQUIREMENTS | **None.** "No cloth sound, wipe sound, comfort-pat sound, answer-revealing sound, or additional effect."; `named_audio_assets: []` |
| VISUAL_TREATMENTS | **None.** `overlay_vfx_requirements: []`; QC: "No glint, sparkle, overlay, or other attention-grabbing VFX" |
| START_STATE | `visible_at_start(S029) = visible_at_end(S028)`. No smudges; mirror held by Lumi; clean glass; Mikko's reflection; cloth within Mikko's reach; no glint. |
| END_STATE | Identical to start: unchanged hold through 120.0 s |
| CONTINUITY | "S028 end-state continuity: Mikko and Lumi are already settled together"; carry forward the removed-smudge state; "Preserve the approved calm resting action exactly" |

The Agent-008 spec agrees: SPEC; 144 frames; COMPOSITE; no overlays, treatments, dialogue slots, named SFX or events; the only bed is AMB-BATHROOM-QUIET-v01 (`ea28fad4…4d2f`).

## 2. S028 → S029 continuity
**S029_STARTS_DIRECTLY_FROM_S028 = YES.** Manifest `continuity_start_authority`: `source_shot_id: S028`, all 8 tracked elements inherited.

**RECOMMENDED_S029_CONTINUITY_SOURCE:** the last frame used by the approved S028, taken from the approved S028 raw motion.

| Item | Value |
|---|---|
| SOURCE_ASSET_ID | `MOTION-EP005-S028-SEEDANCE20-CAND-v01` (row 2e13b73d, APPROVED) |
| SOURCE_SHA | `341683c40de8d71ebed564b7739f9b338add2f954d00e347e0561c7fbe7a9b58` |
| SOURCE_FRAME_INDEX | **119** (of 121) |

**Why this source:**
- The approved assembled S028 uses raw frames 0–119 at identity fps and scale. Raw frame 119 is therefore exactly the last picture the viewer sees before S029.
- Raw frame 120 is not in the approved shot.
- Decoding the raw gives the cleanest first-generation pixels. The assembled MP4 is a second H.264 encode of the same frame: mean absolute difference 1.26, max 28.
- This is the same G04 pattern already approved for S027 → S028.
- The S028 base frame (`9ac6ccc3…`) is S027's end state, not S028's end, so it is wrong for S029.

**Measured end state of S028 (raw frames 96–119):**
- Mikko has turned slightly toward Lumi, eyes closed, content smile. Clean face.
- Lumi floats, smiling.
- Mirror: lowered, held in front of her lower body (matches the approved "lap" interpretation).
- **Cloth: held by Lumi's hand against or over Mikko's shoulder.** It is not resting in her lap.

**CONTINUITY CONFLICT (human decision required):**
- The S029 spec says the cloth rests "quietly in Lumi's lap" with "no additional wipe or pat".
- A hold of S028's true end frame shows the cloth resting on Mikko's shoulder under Lumi's hand.
- A held still contains no pat *motion*, so "no additional pat occurs" is met.
- The cloth *location* differs from the S029 wording. It does still satisfy the tracked element "Soft cloth within Mikko's reach".
- Moving the cloth would require either new motion or a pixel edit:
  - New motion contradicts S029's "only subtle breathing" and adds spend.
  - A pixel edit is a generative or retouch change, which is not allowed or supported.

## 3. Production mode
**S029_RECOMMENDED_PRODUCTION_MODE = B. DETERMINISTIC FRAME DERIVATION + HELD SHOT**
1. G04 extracts raw S028 frame 119.
2. G02 `compose_still_shot` holds it for 144 frames with the ambience bed.

Why:
- The manifest itself says no video generation is needed: "static/rest shot".
- Agent-008 classifies S029 as a G02-supported still.
- The S029 held pose was human-approved in Batch 0C (SAFE_HELD_POSE; "the breathing is lost").
- The true continuity frame exists already.

| Item | Value |
|---|---|
| PAID_PROVIDER_REQUIRED | **NO** |
| ESTIMATED_PROVIDER_CALLS | **0** |
| ESTIMATED_PROVIDER_COST | **$0.00** |

Alternative, not recommended: E, a new 6 s Seedance from frame 119 so Lumi moves the cloth to her lap and both breathe.
- Cost: about $4.08 list (6 s × 1920×1080 tokens; $4.12 at 121+24 frames). This is above the earlier $3.50 caps and needs new authorisation.
- It adds an action the S029 spec does not ask for, and risks identity drift on the final shot.

## 4. Dialogue
None authoritative. `voice_lines: []`.
- TTS_REQUIRED = NO.
- Maximum future ElevenLabs calls: **0**.

## 5. Audio plan
| Sound | Required? | Asset | SHA | Timing intent | Reuse |
|---|---|---|---|---|---|
| Bathroom ambience | **YES** | AMB-BATHROOM-QUIET-v01 | `ea28fad468e353b99d48070d12853620f08e8b05c8d912706122d31176544d2f` | 0.000–6.000 s bed, 0 dB (S027/S028 convention), Agent-008 20 ms edge ramps | YES |
| Cloth foley | **NO** ("No cloth sound") | — | — | — | — |
| Mirror sounds, completion pop, WIN chord, clue chime, whoosh | **NO** | — | — | — | — |
| Music | **NO** ("No closing sting") | — | — | — | — |
| Silence | Not as a separate track; "quiet ambience only" | — | — | — | — |

No required audio is missing.

## 6. Visual treatments
- VISUAL_TREATMENTS_REQUIRED: **none** (no glint, reflection, overlay, pop, clean reveal, fade or effect).
- IMPLEMENTATION_PATH: a plain G02 hold.
- CODE_SUPPORT_STATUS: supported.
- **Note:** "minimal composited breathing" in the animation plan is not implemented. G02 holds a static frame; a deterministic breathing composite does not exist. Batch 0C approved S029 as a held pose with the breathing lost. The human should reconfirm this for the final shot.

## 7. Agent-008 support
| Item | Value |
|---|---|
| S029_SPEC_STATUS | SPEC (approved v05 lineage) |
| S029_CODE_PATH_SUPPORTED | **YES**: G04 `derive_frame` + G02 `compose_still_shot` (`check_still_contract` = OK). Both are test-proven; this would be **G02's first production use**. |
| S029_CURRENT_BLOCKERS | (1) No approved S029 source frame. G02 requires an APPROVED `SHOT_FRAME/BASE_FRAME` or `DERIVED_FRAME` row with `shot_id = S029` and a verified SHA. (2) The cloth-location continuity decision (Part 2). |
| S029_MISSING_INPUTS | The derived S029 frame (G04 of raw S028 frame 119), then its storage write and registration, then human approval of its exact SHA |
| S029_CAN_RENDER_TODAY_WITH_EXISTING_ASSETS | **NO**. Only the frame derivation and approval stand in the way; zero spend. |

## 8. Episode-end requirements
**NO_SPECIAL_EPISODE_END_TREATMENT_SPECIFIED.**
- The spec says "Hold unchanged through 120.0s".
- No fade, end card, logo, credits, black frame, music ending or closing sting ("No closing sting"; "no … attention-grabbing end effect").
- Agent-008's standard 20 ms ambience ramp at the shot boundary is the only audio edge.

## 9. Reuse
| ASSET_ID | SHA | ROLE_IN_S029 | REUSE_METHOD | ZERO_NEW_GENERATION |
|---|---|---|---|---|
| MOTION-EP005-S028-SEEDANCE20-CAND-v01 | `341683c4…9b58` | continuity source | G04 exact extract of frame 119 (lossless PNG) | YES |
| AMB-BATHROOM-QUIET-v01 | `ea28fad4…4d2f` | only audio | G02 bed, 0 dB | YES |
| SHOT-EP005-S028-ASSEMBLED-v01 | `1d5dfabd…7cc0` | continuity reference / QC (frame 119 ≈ raw 119) | read-only comparison | YES |
| CHAR-MIKKO / CHAR-LUMI masters, WORLD-EP005-BATHROOM, PROP mirror / cloth | registry | resolved by readiness 69bff641; carried inside the derived pixels | none needed | YES |

Not reused (not allowed by the S029 spec): FOLEY-CLOTH-SOFT-v01, all SFX, dialogue clips.

## 10. Risks
| Risk | Level | Note |
|---|---|---|
| Character continuity | LOW | exact last frame of approved S028 |
| Prop continuity | **MEDIUM** | cloth sits on Mikko's shoulder, not in Lumi's lap as written; needs a human decision |
| Final-shot continuity (motion → freeze) | **MEDIUM** | S028 still has small motion at frames 117–119 (mean frame diff about 1.1), so a 6 s freeze reads as "stopped"; breathing is not implemented |
| Dialogue timing | LOW | no dialogue |
| Audio balance | LOW | ambience only, same governed bed and gain as S027/S028 |
| Motion complexity | LOW | none (held) |
| Unsupported Agent-008 behaviour | LOW–MEDIUM | G02 path supported; first production use; breathing composite unsupported |
| Unnecessary provider spend | LOW | mode B is $0 |
| Reopening S028 | LOW | read-only source use; no S028 asset touched |
| Altering approved assets | LOW | G04 verifies the source SHA before and after; outputs are new files |

## 11. S029_NEXT_ACTIONS (none executed)
1. **Human decision:**
   - (a) Accept the cloth-on-shoulder end state, held as S029's rest state, as the S029 interpretation of "props at rest".
   - (b) Reconfirm the static hold (no breathing) for the final shot.
2. G04 derives the raw S028 frame 119 twice. Byte-identical PNGs; source SHA verified before and after.
3. Preserve it with no-overwrite as `FRAME-EP005-S029-BASE-CAND-v01` (SHOT_FRAME, REVIEW, shot_id S029, derivation provenance).
4. Human approves the exact frame SHA. Then the status change and approval metadata.
5. G02 `compose_still_shot`:
   - 144 frames, 1920×1080, 24 fps, AMB-BATHROOM-QUIET-v01 bed at 0 dB.
   - Two renders, byte-identical.
   - Automatic QC: 144 frames, 6.000 s, peak ≤ −1 dBFS, no other audio.
6. Preserve and register `SHOT-EP005-S029-ASSEMBLED-v01` as REVIEW. Then human review.
7. On approval: close S029.

**Total: 0 provider calls, $0.**

## 12. Factory learning
REUSABLE_FACTORY_CAPABILITIES:
- Approved-lineage snapshot and spec, through `agent008.episode`.
- G04 deterministic frame derivation with two-run proof.
- Registry and storage governance pattern: no-overwrite, read-back, REVIEW → APPROVED with metadata.
- G02 still-shot assembly with governed audio roles.
- G09 (not needed here).
- Two-render determinism and automatic QC.
- Side-effect audit fingerprints.

S029 needs **no** new Seedance, TTS or motion process.

NEW_ENGINEERING_REQUIRED = **NO** for the recommended path.

**Optional, if the human wants S029's "minimal composited breathing":** a deterministic micro-motion treatment for G02 stills. That would be, for example, a sub-pixel vertical scale oscillation of at most 0.3%, under 0.25 Hz, applied to the whole frame or a masked character region. It is a new capability, not in G02, G06 or G08, and would need design and tests before use.
