# EP005 Batch 0C: factory paths (G02, G04), whoosh repair, decisions record (2026-10-10)

Mikko & Lumi only. Zero provider calls, zero generations, zero production renders. One approved production-state write: the whoosh registry metadata repair.

## 1. Whoosh governance repair: APPLIED
**Row:** `asset_registry` 0e10bf46-4099-43cd-ab91-5c10fcb59d9d (`SFX-MIKKO-TRY-WHOOSH`, APPROVED).

**Write:**
- One PATCH of `metadata_json` only, filtered on `id` and `status=APPROVED`; 1 row affected.
- The 4 existing keys are kept unchanged.
- 8 keys were added exactly as proposed: `sha256`, `bytes`, `duration_s`, `codec`, `sample_rate`, `channels`, `storage_object_id`, `hash_evidence`.

**Read-back:** `metadata_json.sha256` = `53d06150dc0acc73cc972890510ba406486b178e4222eca253f848129bbed0c3`, which matches the governed SHA. The stored bytes were re-hashed immediately before the write and gave the same SHA (341,541 B).

**Not changed:**
- The file and its storage object: id 7e415397, ETag `ac26a571…-1`, updated_at 2026-09-15T06:32:40.782Z.
- `storage_path`, `status`, `updated_at`.
- Manifest 45cc7493 (bytes identical).
- Counts: 27 registry rows, 23 storage objects, 11 manifests.

**Agent-006 read-only proof** (local node script, not the workflow):
- Before and after: 14 requirements and 18 governed rows.
- All 14 resolution lines are identical.
- See `AGENT006_READONLY_PROOF_PRE/POST_WHOOSH_REPAIR.txt` → **AGENT006_RESOLUTION_UNCHANGED**.

**Agent-008 effect (live):**
- S007 changes from `BLOCKED:NO_EXPECTED_HASH` to `SPEC`; the whoosh SHA now comes from `asset_registry.metadata_json.sha256`.
- Episode resolution is 26 SPEC / 3 BLOCKED (S009, S015, S021).
- New read-only capture `ep005_approved_state_capture_v2.json`. It differs from v1 only in this row; v1 is kept as the pre-repair capture.

**Rollback:** PATCH `metadata_json` back to the 4-key object recorded in `WHOOSH_GOVERNANCE_REPAIR_APPLIED_v1.json`. This needs a human instruction.

## 2. G04: derived frame from approved motion (`agent008/derive.py`)
Implemented exactly as the gap matrix defines it: "exact-index ffmpeg extract; record source SHA, index and output SHA; human approval; SHOT_FRAME/DERIVED_FRAME".

**`derive_frame(source, frame_index, target_shot_id, out_dir, crop=None, scale=None, expected_frame_rgb_sha256=None)`**

Steps:
1. Source must be APPROVED or LOCKED and have an expected SHA. The SHA is verified.
2. The exact decoded frame count and geometry are checked against the expected values.
3. `select=eq(n,K)` takes decoded frame K as rgb24.
4. Optional exact-pixel crop, then an optional deterministic scale (aspect must match).
5. Lossless PNG output, verified by a byte-identical rgb24 round-trip.
6. Source SHA re-verified; an existing output is never overwritten.

Output and provenance:
- Provenance records the source identity and SHA, frame index and timestamp, selected-frame rgb SHA, recipe and output SHA.
- `status: REVIEW`, `registered: false`, approval by exact PNG SHA.
- **Nothing is uploaded or registered.**

Fail-closed codes:
- `HASH_MISMATCH`, `NO_EXPECTED_HASH`, `DERIVE_SOURCE_NOT_APPROVED`, `DERIVE_SOURCE_GEOMETRY_MISMATCH`
- `FRAME_INDEX_INVALID`, `FRAME_INDEX_OUT_OF_RANGE`, `DERIVED_FRAME_MISMATCH`
- `CROP_OUT_OF_BOUNDS`, `SCALE_ASPECT_MISMATCH`
- `OUTPUT_EXISTS`, `OUTPUT_WOULD_OVERWRITE_SOURCE`, `DERIVED_FRAME_NOT_LOSSLESS`, `SOURCE_MUTATED`

## 3. G02: production still-shot path (`agent008/still.py`)
Implemented exactly as the gap matrix defines it: "hold a hash-verified approved/derived frame for N frames, reusing … `mix_motion_audio` (with dialogue) and `encode_review`".

**`compose_still_shot(spec_shot, frame, spec, asset_paths, timing, out_dir, crop=None)`**

Source frame checks:
- Must be `SHOT_FRAME/BASE_FRAME` or `SHOT_FRAME/DERIVED_FRAME`.
- Must be APPROVED or LOCKED and belong to the same shot.
- SHA is verified.

Layout:
- Deterministic optional exact-pixel crop, then an aspect-preserving fit and centred black pad.
- Opaque only (`STILL_SOURCE_HAS_TRANSPARENCY`).

Audio (Batch 0 semantics):
- `resolve_dialogue` fails closed on missing, unexpected, unapproved, wrong-text or SHA-mismatched dialogue.
- `mix_motion_audio`: AMBIENCE is the only bed; FOLEY/SFX play once at explicit times; fails closed without timing or on overrun.

Encode and verification:
- Exact `frames` = round(duration × fps), at the spec resolution and fps (`STILL_DURATION_FRAME_MISMATCH`).
- Encoded with `encode_review`.
- Automatic QC checks frame count, resolution, fps, duration and the audio stream.
- Status REVIEW; approval by exact mp4 SHA.

**Support is limited to the defined scope.** Anything else fails closed rather than being approximated:

| Request | Fail-closed code | Open gap |
|---|---|---|
| Overlays | `STILL_OVERLAYS_NEED_G03_ANCHORS` | G03, no approved anchors |
| Treatments | `STILL_TREATMENTS_NEED_G08` | G08 |
| Motion shots | `STILL_PATH_NOT_FOR_MOTION_SHOT` | — |

Camera moves (G06) and in-shot cuts (G07) are not implemented.

There is no provider, network or registry dependency (tested with sockets disabled).

## 4. Tests: 128/128 OK
- The 108 existing tests are unchanged and pass.
- 20 new tests are in `agent008/tests/test_batch0c.py`. They use synthetic fixtures only (testsrc2 video, flat PNGs, tones).

| Required test | Tests |
|---|---|
| deterministic still-shot output | S01 |
| source SHA mismatch fails closed | S03 (still), D02 (derive); also S04, D07 identity |
| deterministic frame extraction | D01 (frames 0/60/119/120 equal a full decode, lossless) |
| wrong frame index fails closed | D03 (121, 500, −1, 119.0, True, pinned-frame mismatch, frame-count mismatch) |
| derived-frame provenance | D04 |
| no source mutation | D05, S08 (SHA + mtime, no overwrite) |
| no provider calls | D08, S09 (socket disabled; no provider/http imports) |
| dialogue requirement fails closed | S05 (unfilled, unapproved, SHA, text, overrun, unexpected) |
| audio event semantics preserved | S06 (bed spans the shot; FOLEY once at 1.0–1.4 s, sample-exact; no timing → fail) |
| two-run determinism | S02 (mp4/wav byte-identical, same core SHA), D06 |
| extra | S07 unsupported contracts, S10 derived→still chain, E01 S007 resolves after the repair, E02 S023/S029 fit the G02 contract |

Full output: `AGENT008_TEST_OUTPUT_BATCH0C_v1.txt`.

## 5. Decisions recorded (Company Brain, Batch 0C)

**Held pose: APPROVED** for every SAFE_HELD_POSE or SAFE_DETERMINISTIC_TREATMENT shot except S006:
- S003, S004, S005, S008, S012, S013, S017, S018, S019, S023, S024, S025, S029.
- No held-pose shot was rendered.

**S006: MOTION REQUIRED for planning** (`S006_MOTION_REQUIRED_FOR_PLANNING`):
- The held pointing pose is not forced. S006 is now planned as HIGGSFIELD_MOTION_REQUIRED: +1 video, and its motion base frame is still needed.
- Its reflection treatment remains G08 (motion compose rejects treatments); its smudges follow G03 (pre-composited into the base frame).
- This can be revisited only after a later human-reviewed deterministic test.

**Smudge removal:** direction approved but not implemented. S009, S015 and S021 stay blocked (`OVERLAY_TRANSITION_UNSUPPORTED_V01` / G11) until the overlay-anchor/wipe sprint.

**Voice-over policy:** there is no global policy. S027 is the only approved voice-over case; every other shot keeps its shot-specific sync classification (H4 stays open for those shots).

**Lumi voice: PENDING HUMAN.** L1/L2/L3 were not selected and no takes were generated. H1 stays open for 10 shots.

**S028:**
- Direction approved; the spec is ready and nothing was created (`S028_DERIVED_FRAME_SPEC_v1.json`).
- Source: approved raw S027 motion `86dddea5…0e25` (row 2ebed34b), decoded frame **119** (121 frames, 1920×1080, 24/1).
- Frame 119 is the last raw frame used by the approved assembled S027.
- Recipe: no crop, no scale.
- Interpretation recorded: "lowers the mirror to her lap" = "lowers the mirror to a relaxed resting position in front of her lower body while floating". This applies to the S028 motion brief and the S029 continuity check, not to the base frame.

## 6. S004/S012/S018 script amendment package: READY, NOT APPLIED
`SCRIPT_AMENDMENT_AUTHORISED = FALSE`. The full machine-readable package is `EP005_S004_S012_S018_SCRIPT_AMENDMENT_PACKAGE_v1.json`.
- **Alternative B:** exact wording from decision pack section 6.
- **Reason:** TIMING_FIT.

| Shot | Old authoritative lines (script v02 / manifest 45cc7493) | Alternative B | Syllables | Est. speech (2.63–3.01 syl/s) | Window | Fits |
|---|---|---|---|---|---|---|
| S004 | "A little glint! Look at his cheek." + "Can you help Mikko find the next berry smudge?" | "A glint on his cheek!" + "Find the next smudge!" | 19 → 9 | 6.31–7.22 s → 2.99–3.42 s | 4.15 s | no → yes (+0.73 s) |
| S012 | "I see a spot near your mouth." + "Can you help Mikko find the next berry smudge?" | "By your mouth!" + "Find the next smudge!" | 18 → 7 | 5.98–6.84 s → 2.33–2.66 s | 4.15 s | no → yes (+1.49 s) |
| S018 | "One tiny spot is still here." + "Can you help Mikko find the next berry smudge?" | "One spot left!" + "Find the next smudge!" | 18 → 7 | 5.98–6.84 s → 2.33–2.66 s | 5.15 s | no → yes (+2.49 s) |

**Exact proposed mutations (12):** for each shot (i = 3, 11, 17), the text becomes `Lumi: “<new>”` with the curly quotes kept.
- `episode_scripts.production_script_json.shots[i].dialogue_lyric` → clue line
- `episode_scripts.production_script_json.shots[i].child_prompt` → ritual prompt
- `episode_production_manifests.manifest_json.shot_plans[i].shot_plan.audio_plan.voice_lines[0]` → clue line
- `episode_production_manifests.manifest_json.shot_plans[i].shot_plan.audio_plan.voice_lines[1]` → ritual prompt

**Not proposed for mutation:** 7 historical occurrences in `architecture_json` and `approved_episode_snapshot`, listed in the JSON. Whether v03 carries them is a human decision.

**Proposed method:**
- No in-place edit of APPROVED rows.
- After authorisation: script v03, then a derived manifest, then readiness. Then re-run the Agent-006 proof and `agent008.episode`. Only the S004/S012/S018 dialogue slot text should change.

**Story and educational intent preserved:**
- The three clues stay in the same order (cheek → mouth → nose).
- One identical ritual prompt is used in all three shots.
- The cheek and mouth target words stay, and S018 says the last-spot count.
- Lumi stays the observer; Mikko does every wipe.
- The S005, S013 and S019 protected holds are unchanged, and no answer-revealing sound is added.

**Changed:** the question becomes an imperative, and "berry" and "help Mikko" are dropped. Human tone review is recommended.

## 7. Revised preflight (planning deltas only; v1 and v2 not regenerated)
Built by `build_matrix_v3_delta.py`; output in `EP005_AGENT008_PRODUCTION_MATRIX_v3_DELTA.json`.

| Metric | v2 | v3 |
|---|---|---|
| Spec-resolved shots (incl. S027) | 25 | **26** (S007 now resolves) |
| Technically supported shots | 2 (S022, S026) | **4** (S022, S023, S026, S029) |
| **Code-blocked shots** | 26 | **24** |
| **Human-decision-blocked shots** | 23 | **17** |
| Voice-blocked (H1 Lumi) | 10 | 10 |
| Video generations (estimated) | 11 (14 if unblocked) | **12 (15)**: +1 for S006 |
| Open code gaps | 9 | **6**: G03, G06, G07, G08, G09, G11 |

**Newly technically supported:**
- By G02: **S023, S029**.
- By G04: **S029**.

**G02 closed but still code-blocked:**

| Shots | Still blocked by |
|---|---|
| S003, S005, S008, S013, S017, S019 | G03 |
| S004, S012 | G03, G08, G09 |
| S018 | G03, G07, G08, G09 |
| S024 | G06 |
| S025 | G08 |

**G04 closed but still code-blocked:**

| Shots | Still blocked by |
|---|---|
| S008, S011 | G03 |
| S028 | G09 |

**Can S023 enter production? NO.**
- It is technically supported and its held pose is approved, but it has no approved source frame.
- Its start state is the S022 end state: a derived frame from approved S022 motion.
- S022 is not produced, and it depends on S021, which is blocked on smudge removal.

**Can S029 enter production? NO.**
- It is technically supported (G04 + G02), but its source is the approved S028 motion end frame, and S028 motion does not exist yet.
- S028 itself is blocked: H1 Lumi voice, H4 visible speech, G09, H5 derived-frame authorisation, and then a separately authorised Seedance generation.

**Does S028 become base-frame-ready once the derived frame is authorised? YES.**
- G04 implements the exact spec.
- Once the frame is created, human-approved by PNG SHA and registered as SHOT_FRAME/DERIVED_FRAME, S028 is base-frame-ready.
- S028 is still not production-ready: H1, H4 and G09 remain.

None of these shots was started.
