# EP005 Batch 0D: final pre-production closeout (2026-10-10)

Mikko & Lumi only. Zero provider calls, zero generations, zero production renders, zero production-state writes. Batch 1 not started.

**Accepted bases:**
- Batch 0C: `802d2d8ef71eaff9bcee9452779768311f3d6de5`
- Lumi voice: `2f89854eba42766dcff2472d9201723844fe67b9`

**Production voices (human-approved):**
- Mikko: Teddy Twinkle – Cute Cartoon Boy, `XjGYkUkzth8BPs29fmcV`
- Lumi: Lola – Soft, Innocent and Calming, `f9imtLc2jfOLXtqe3Ihb`
- No production Lumi dialogue clip exists.

## Part 1: G09 implemented (`agent008/dialogue_timing.py`)
Exact gap-matrix requirement: "Add non-overlap and window checks to resolve_dialogue (fail closed)."

`govern_dialogue_timing(spec_shot, dialogue, inputs, timing, spec)` runs right after `resolve_dialogue` in both `compose_motion_shot` and `compose_still_shot`. Its report is recorded as `provenance.dialogue_timing`.

| # | Requirement | Implementation |
|---|---|---|
| 1 | Authoritative slot representation | Manifest `dialogue_slots` (speaker, exact text), unchanged. `resolve_dialogue` binds each slot one-to-one to an approved, SHA-verified clip. |
| 2 | Deterministic start/end | start = round(start_s × SR). end = start + decoded sample count at the output rate. Both are reported in samples and seconds. |
| 3 | Inside the allowed window | Window = [pre_hold, shot_end − post_hold]. Codes: `DIALOGUE_OUTSIDE_WINDOW`; `DIALOGUE_OVERRUNS_SHOT` past the shot end (same code as the mix backstop). |
| 4 | Required dialogue cannot disappear | `DIALOGUE_SLOT_UNFILLED` in `resolve_dialogue`, in G09, and now also in `mix_motion_audio`, so the mix can no longer be called with fewer clips than slots. Also `DIALOGUE_CLIP_EMPTY`. |
| 5 | Overlap only if declared and authorised | `timing['dialogue_overlaps'] = [{slots: [i, j], max_overlap_seconds, authorised_by}]`. Codes: `DIALOGUE_OVERLAP_DECLARATION_INVALID`, `…_EXCEEDS_AUTHORISED`, `…_DECLARED_NOT_PRESENT`. |
| 6 | Accidental overlap fails closed | `DIALOGUE_OVERLAP_UNAUTHORISED`; script order is enforced (`DIALOGUE_ORDER_MISMATCH`). |
| 7 | Pre/post visual holds representable | `timing['dialogue_window'] = {pre_hold_seconds, post_hold_seconds}`. Actual holds are reported in `visual_holds`. Protected participation holds reject dialogue (`DIALOGUE_IN_PROTECTED_HOLD`). |
| 8 | Ending exactly on a boundary is valid | Sample-exact comparison `end ≤ window_end`. |
| 9 | Beyond a boundary fails closed | One sample over → `DIALOGUE_OUTSIDE_WINDOW` / `DIALOGUE_OVERRUNS_SHOT`. |
| 10 | No-dialogue shots backward-compatible | Empty report, no new requirements. |
| 11 | S027 unchanged | See below. |

**S027 unchanged:**
- The S027 mix was rebuilt from the approved inputs (audio only, no video) with G09 active.
- Mix WAV `c67da3f3d7cf0a2aeca0e9d8736db64c09aa2b819b9a3a607338bf1893e2a863` is **identical** to the approved mix.
- G09 report: Mikko 0.500–2.125396 s inside 0–5 s (`S027_G09_UNCHANGED_CHECK_v1.json`).
- Approved MP4 `7b01c392…8fde` is unaffected.
- A future re-render's provenance JSON would gain a `dialogue_timing` block.

Out of scope, as instructed: lip-sync, speech generation, voice choice.

**Tests: 138/138 OK.** The 128 existing tests pass unchanged, plus 10 new in `agent008/tests/test_g09.py`:
- G01 valid window
- G02 overrun
- G03 unauthorised overlap / order
- G04 authorised overlap
- G05 missing required dialogue
- G06 deterministic pre-hold, via the G02 still path, two runs identical
- G07 post-hold and protected hold
- G08 exact boundary
- G09 no-dialogue compatibility
- G10 S027 unchanged

Full output: `AGENT008_TEST_OUTPUT_BATCH0D_v1.txt`.

## Part 2: S028 human decision pack
See `S028_HUMAN_DECISION_PACK_v1.md`.
- **Classification: VISIBLE_SPEECH_DECISION_REQUIRED.** Recommendation: S027-style voice-over plus a soft-mouth-movement motion brief, judged on the raw motion.
- **Frame 119 is sufficient** (subject to PNG QC). A new still is unnecessary.
- **Dialogue fit is TIGHT.** G09 simulation: strictly sequential clips overrun (5.19 s). It fits only at the measured voice rates with a human-authorised ≤ 0.40 s overlap of Lumi's silent tail. It still overruns at the slowest estimate. Final timing must come from measured, approved clips.

## Part 3: exact Alternative B text (from the committed Batch 0C package; not applied)
`SCRIPT_AMENDMENT_AUTHORISED = FALSE`.

Each line is stored as `Lumi: “<text>”`:
- Script: line 1 in `dialogue_lyric`, line 2 in `child_prompt`.
- Manifest: `voice_lines[0]` and `voice_lines[1]`.

All three shots have exactly two Lumi lines.

**S004**

OLD LINE 1:
"A little glint! Look at his cheek."

NEW LINE 1:
"A glint on his cheek!"

OLD LINE 2:
"Can you help Mikko find the next berry smudge?"

NEW LINE 2:
"Find the next smudge!"

**S012**

OLD LINE 1:
"I see a spot near your mouth."

NEW LINE 1:
"By your mouth!"

OLD LINE 2:
"Can you help Mikko find the next berry smudge?"

NEW LINE 2:
"Find the next smudge!"

**S018**

OLD LINE 1:
"One tiny spot is still here."

NEW LINE 1:
"One spot left!"

OLD LINE 2:
"Can you help Mikko find the next berry smudge?"

NEW LINE 2:
"Find the next smudge!"

**Timing** (speech estimates; Lumi planning range 2.63–3.01 syl/s; measured L1 rate 2.96 syl/s; window = shot − 0.85 s for lead and tail):

| Shot | Authoritative duration | Speech window | Current estimate (19/18/18 syl) | Proposed estimate (9/7/7 syl) | At measured L1 rate | Current margin | Proposed margin |
|---|---|---|---|---|---|---|---|
| S004 | 5.0 s | 4.15 s | 6.31–7.22 s | 2.99–3.42 s | 3.04 s | −2.16 to −3.07 s | **+0.73 to +1.16 s** (+1.11 s at L1) |
| S012 | 5.0 s | 4.15 s | 5.98–6.84 s | 2.33–2.66 s | 2.36 s | −1.83 to −2.69 s | **+1.49 to +1.82 s** (+1.79 s at L1) |
| S018 | 6.0 s | 5.15 s | 5.98–6.84 s | 2.33–2.66 s | 2.36 s | −0.83 to −1.69 s | **+2.49 to +2.82 s** (+2.79 s at L1) |

**G09 note:** each shot has two dialogue slots, so two clips, each with its own lead and tail (≈ 0.5 s per file at L1). Final placement must pass G09 with the measured clips. S004 has the least slack.

## Part 4: script / manifest lineage plan
See `SCRIPT_V03_LINEAGE_PLAN_v1.md`. Not executed.
- v02, 45cc7493 and edc4ad58 stay immutable.
- New script v03 (6 field changes); new manifest ID (6 field changes plus lineage fields).
- New readiness record: YES. Agent-006 rerun: YES (read-only proof, then one authorised workflow run).
- No approved asset is invalidated.
- S027 is unaffected: its shot-plan and script-shot hashes are recorded as invariants.

## Part 5: EP005_AGENT008_PRODUCTION_MATRIX_v3
`EP005_AGENT008_PRODUCTION_MATRIX_v3.json`, built by `build_matrix_v3.py`. It is v2 plus the Batch 0C, Lumi-voice and G09 deltas only, and supersedes the interim 0C v3-delta and v4 voice-delta files.

| Count | Value |
|---|---|
| TOTAL_EP005_SHOTS | **29** |
| COMPLETE_APPROVED_SHOTS | **1** (S027) |
| REMAINING_SHOTS | **28** |
| TECHNICALLY_SUPPORTED_SHOTS | **5**: S022, S023, S026, S028, S029 |
| CODE_BLOCKED_SHOTS | **23**: S001–S021, S024, S025 (open gaps G03, G06, G07, G08, G11) |
| VOICE_IDENTITY_BLOCKED_SHOTS | **0** |
| MISSING_DIALOGUE_ASSET_SHOTS | **16**: S001, S002, S003, S004, S006, S007, S010, S012, S014, S016, S018, S020, S022, S025, S026, S028 (Mikko 9 lines, Lumi 13) |
| SCRIPT_AMENDMENT_BLOCKED_SHOTS | **3**: S004, S012, S018 |
| VISIBLE_SPEECH_DECISION_SHOTS | **15**: S001, S002, S003, S004, S006, S007, S010, S012, S014, S016, S020, S022, S025, S026, S028 |
| OTHER_HUMAN_DECISION_BLOCKED_SHOTS | **2**: S028, S029 (H5: derived-frame authorisation) |
| PROVIDER_READY_SHOTS | **0** |

Three of the code-blocked shots (S009, S015, S021) also cannot be specified yet (`OVERLAY_TRANSITION_UNSUPPORTED_V01`, pending G11).

**Closed since v2:** G02, G04, G09, G10. Newly technically supported: S023, S028, S029.

**S028_READY_STATE = TECHNICALLY_SUPPORTED_NOT_PRODUCTION_READY.** Spec SPEC; code gaps none. Remaining blockers:
1. H4: visible-speech decision.
2. H5: authorise creation of the frame-119 derivative, then approve its exact PNG SHA.
3. Derived base frame not stored or registered (SHOT_FRAME/DERIVED_FRAME).
4. Lumi clip missing: "You look comfy. Story time."
5. Mikko clip missing: "I’m ready to rest."
6. G09 timing plan, including any authorised silent-tail overlap, to be accepted from the measured clips.
7. Seedance package and spend authorisation (1 × 5 s, ≈ $3.40).
8. Raw motion approval and RAW_MOTION_SOURCE registration.
9. FOLEY-CLOTH-SOFT-v01 event timing.
10. Final assembled-shot QC and registration.

## Part 6: RECOMMENDED_NEXT_PRODUCTION_BATCH = **S028 + S029** (the COMFORT ending)
**Why these belong together:**
- They are the only remaining shots that are technically supported, continuity-ready from the approved S027, and free of unresolved script text.
- S028 starts from approved S027 raw frame 119, with no image generation.
- S029 is the deterministic hold of S028's end frame: G04 extract plus a G02 144-frame still with ambience. Zero provider calls.
- Together they close EP005 seamlessly from the completed S027.

**Rejected alternatives:**
- S022 / S023: their start state chains back to S021, which is blocked on smudge removal (G11).
- S026: needs a new image, and its continuity comes from S025 (G08).
- The old Batch 1 order: superseded by this state.

| Item | S028 | S029 | Batch total |
|---|---|---|---|
| New image generations | 0 (derived frame 119) | 0 (derived from approved S028 motion) | **0** |
| New video generations | 1 Seedance 2.0 i2v, 5 s 1080p (≈ $3.40 list) | 0 | **1** |
| TTS generations | 2: Lumi "You look comfy. Story time." + Mikko "I’m ready to rest." | 0 | **2** |
| Deterministic-only work | G04 frame-119 derivation; compose_motion_shot (ambience bed, FOLEY-CLOTH-SOFT-v01 event, 2 G09-governed lines), 2 identical renders | G04 last-used-frame derivation from the approved S028 raw; G02 still 144 frames with ambience, 2 identical renders | |

**Remaining human approvals before execution:**
1. S028 visible-speech decision (H4) and confirmation of the single continuous S027 framing.
2. Authorisation to create the S028 derived frame, then approval of its PNG SHA, then a storage write and registration.
3. Authorisation of 2 TTS takes, then clip approval and AUDIO/DIALOGUE registration.
4. Acceptance of the S028 G09 timing plan, including any authorised silent-tail overlap.
5. Seedance prompt package and spend cap (one generation).
6. S028 raw approval and registration.
7. S028 final QC and registration.
8. Authorisation to create the S029 derived frame and approve its SHA.
9. S029 final QC and registration.

S029's held pose was already approved in Batch 0C.

## Safety
Zero across the board:
- provider calls, ElevenLabs, Higgsfield/Seedance, image or video generation, TTS
- production compositor renders (only the S027 audio-only mix check and synthetic test renders)
- script, manifest, readiness, registry or storage writes
- C1 changes, Agent-006 workflow runs, Agent-007, billing, publishing, Anime Clip Farming

**Rollback:** revert the commit.
