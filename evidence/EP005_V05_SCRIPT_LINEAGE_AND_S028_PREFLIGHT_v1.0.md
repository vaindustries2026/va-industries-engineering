# EP005: script v05 governance + S028 base-frame preflight (2026-10-11)

Mikko & Lumi only. Anime Clip Farming not touched.

Accepted bases:
- Batch 0C: `802d2d8`
- Lumi voice: `2f89854`
- Batch 0D: `a7b602b`

Paid provider calls: 0.

## Human decisions taken during the task (Gilang, 2026-10-11, in answer to blocking conflicts)

1. **Status gating.** Agent-006 node 03 refuses any manifest that is not APPROVED, and by precedent derived manifests are created as REVIEW. Decision: create both rows REVIEW; after readback and the local proof pass, change status only to APPROVED; then run Agent-006 once.
2. **Version collision.** EP-CANDIDATE-005 already has script rows v03 (`6b14e140`, REVIEW, 15 shots) and v04 (`b5567e13`, REVIEW, 14 shots). These are older, unrelated Agent-004 drafts. `UNIQUE(episode_code, script_version_number)` forbids a new v03. Decision: the amendment planned as "v03" is created as **v05** (number 5).
3. **Lineage location.** `episode_scripts` has no parent column and migrations are forbidden. Decision: explicit parent lineage goes in `production_script_json.lineage`.

## Part 1: older dialogue copies
`ep005/v05_lineage/EP005_OLDER_DIALOGUE_COPIES_CLASSIFICATION_v1.json`

I searched every column for fragments, not exact strings, and found **8** occurrences. Batch 0D had listed 7.

| # | Field | Class | v05 |
|---|---|---|---|
| 1 | `architecture_json.cue.lumi_notice` | DERIVED_ACTIVE_FIELD | quote → “A glint on his cheek!” |
| 2 | `architecture_json.cue.child_prompt` | DERIVED_ACTIVE_FIELD | → Lumi: “Find the next smudge!” |
| 3 | `architecture_json.three[1].lumi_line` | DERIVED_ACTIVE_FIELD | before-pause → “By your mouth!” (S016 line unchanged) |
| 4 | `architecture_json.three[1].child_prompt` | DERIVED_ACTIVE_FIELD | → ritual |
| 5 | `architecture_json.three[2].lumi_line` | DERIVED_ACTIVE_FIELD | before-pause → “One spot left!” (S022 line unchanged) |
| 6 | `architecture_json.three[2].child_prompt` | DERIVED_ACTIVE_FIELD | → ritual |
| 7 | `architecture_json.character_voice_check.lumi` (**newly found**) | DERIVED_ACTIVE_FIELD | example quote → “By your mouth!”; characterisation unchanged |
| 8 | `approved_episode_snapshot.participation_question` | HISTORICAL_PROVENANCE_SNAPSHOT | unchanged; byte-identical copy of the APPROVED backlog row 07d622e9 (verified live) |

No field was classified ACTIVE_AUTHORITATIVE or STALE_DUPLICATE_BUG among the copies. The 6 authoritative fields are the approved changes themselves.

## Part 2: script v05
- **Record:** `6498ea8d-5902-4a3f-af03-0005ec0c81be`, v05 / number 5, **APPROVED** (status-only change after verification).
- **Parent:** v02 `14471926-f6fb-4bba-b355-109f3ae9e21c`, immutable and byte-identical before and after.

Readback verification:
- Every field equals the deterministic derivation (`derive_v05_lineage.py`, fail-closed).
- Lines are exact:

  | Shot | Line 1 | Line 2 |
  |---|---|---|
  | S004 | "A glint on his cheek!" | "Find the next smudge!" |
  | S012 | "By your mouth!" | "Find the next smudge!" |
  | S018 | "One spot left!" | "Find the next smudge!" |

- The other 26 shots are identical to v02.
- S027 script entry is identical: `301d2406…e1b8`.
- `approved_episode_snapshot` is identical.
- The only row-column changes are version, number, run id, title, status and agent_version.

## Part 3: new manifest
| Item | Value |
|---|---|
| NEW_MANIFEST_ID | `0325d35c-d567-4488-bf78-c3887e819382` (**APPROVED**, status-only change after the proof) |
| NEW_MANIFEST_SHA (canonical `manifest_json`) | `295a816e2f492a33f1fd2daef216b90b7e94b11652f3f0c86aff1025a0fe7d7c` |
| PARENT_MANIFEST_ID | `45cc7493-80b4-4e8d-b71d-fbd7fd3656ed` (unchanged; canonical `e0c2e849…0d55`) |
| Shots / duration | 29 / 120.000 s, contiguous |
| Changed | 6 `voice_lines`; `episode` (script id, version, title); `manifest_version` (+script-v05-altb-1); `derivation`. Row: script id, version, title, run id, agent_version, status. |
| Unchanged | Every asset section (inventory, reused/new assets, source_approved_assets, audio_asset_mappings, TBD dependencies, compositing treatments, dropped requirements, generation workload, shot_queue, audio_workload) and all counts. S027 shot plan identical: `576e43ec…747e`. |

## Part 4: local Agent-006 proof
Agent-006 node code 03/05/07 was verified identical to the live workflow at `9bf6bbef`.

| Case | Result |
|---|---|
| Against the REVIEW manifest | `AGENT-006 BLOCKED (MANIFEST_NOT_APPROVED_OR_NOT_FOUND)`, as designed |
| With status APPROVED | 14 requirements, 14 REUSE_EXISTING, 18 governed rows |
| Compared with 45cc7493 | Every resolution line identical |

**PASS.** No new CREATE_NEW requirement.

## Part 5: one authorised Agent-006 run
- **Method:** single-use caller `N0R2or3Gv5Pbo439` (Manual Trigger + Execute Workflow, input `production_manifest_id` only, no credentials). Executed once, then **archived**. Agent-006 itself was not modified.
- **AGENT006_EXECUTION_ID:** **581** (caller execution 580); success, 23:24:55–23:25:14Z. No retry.
- **AGENT006_RUN_ID:** `A006-1791761096896`.
- **NEW_READINESS_ID:** `69bff641-e056-4701-a23f-d91dbc2039b2`.
  - Status REVIEW, readiness_state READY_FOR_HUMAN_APPROVAL.
  - Requirements 14: reuse 14, create_new 0, human_review 0, blocked 0.
  - Asset-creation and human-review queues empty.
- **Changed requirements:** none.
  - The 14 resolution items match the edc4ad58 run on key, resolution, canonical asset and exact candidates.
  - Only difference: `suggested_candidate_asset_ids` for the 3 audio requirements now also lists `DLG-EP005-S027-L1-MIKKO-v01`, which was registered after the edc4ad58 run. This is informational and does not affect resolution.
- **Paid or provider work:** none. Agent-007: 0.
- **The readiness record is REVIEW.** Approving it is a separate human decision and was not performed. Until it is approved, Agent-008 fails closed on it (`READINESS_NOT_APPROVED`).
  - An in-memory check (status set in a local copy only) shows: 26 SPEC / 3 BLOCKED, as before, and **only** S004/S012/S018 `dialogue_slots[*].text` change.

## Part 6: S027 non-regression
- Script entry identical: `301d2406…`.
- Manifest shot plan identical: `576e43ec…`.
- Agent-008 S027 spec unchanged (in-memory).
- All four approved S027 assets were re-downloaded and re-hashed:

| Asset | SHA-256 |
|---|---|
| Frame | `81b841a6…061b` |
| Raw motion | `86dddea5…0e25` |
| Dialogue | `81a0b038…da50` |
| **Assembled shot `SHOT-EP005-S027-ASSEMBLED-v01`** | **`7b01c392…8fde`** |

- Registry rows are unchanged (registry prior-hash equal). No re-render.

## Part 7: S028 derived frame
`ep005/s028_base_frame/`

| Item | Value |
|---|---|
| Source | `MOTION-EP005-S027-SEEDANCE20-CAND-v01` (registry 2ebed34b), SHA `86dddea5…0e25` verified before; 121 decoded frames, 1920×1080, 24/1 |
| Frame index | **119** (t = 4.958333 s) |
| Method | Agent-008 G04 `derive_frame`: ffmpeg `select=eq(n\,119)` on decoded frames → rgb24 → lossless PNG (bitexact, no metadata); lossless round-trip verified |
| Not applied | crop, scale, interpolation, colour change, generative or content modification |
| Output | **SHA-256 `9ac6ccc3239fd08a69e9a570f13a8b857d0d9d7257fb37d24f8ad676476c6ff0`**, 1920×1080, 3,091,468 B, PNG 8-bit RGB (rgb24 `f5dad881…bc12`) |
| Two runs | byte-identical; same deterministic core SHA |
| Source after | SHA, size and mtime unchanged |

## Part 8: preserved as REVIEW
- **Storage:** `production-assets/visual/production/ep005/frames/FRAME-EP005-S028-BASE-CAND-v01.png`, object `d0e61c24-6453-434d-a12e-5964cbe2e1a5`. Uploaded with `x-upsert: false` after confirming no prior object; read back byte-identical.
- **Registry:** `739b9aec-d908-4699-baea-10bf9e6b4f3e`, `FRAME-EP005-S028-BASE-CAND-v01`, SHOT_FRAME / BASE_FRAME, **status REVIEW**, human_decision **PENDING**.
  - No prior row existed.
  - Every governed field reads back equal: S028, source asset and SHA, frame 119, method, two-run proof, output SHA, dimensions, bytes, no crop/scale/generative change, not C1.
- **Agent-006 post-write proof:** unchanged. The REVIEW row is outside the governed set; still 18 governed rows and 14/14 identical.

## Part 9: shown to Gilang
The exact preserved PNG (SHA `9ac6ccc3…6ff0`) was delivered as the file itself. It is not a screenshot, thumbnail or re-encode.

## Parts 10–11: S028 TTS package and timing state
`ep005/s028_tts/EP005_S028_FUTURE_TTS_PACKAGE_v1.json`

| Line | Voice | Text | Text SHA-256 | Proposed key |
|---|---|---|---|---|
| DLG-EP005-S028-LUMI-v01 | Lola `f9imtLc2jfOLXtqe3Ihb` | You look comfy. Story time. | `cb3da4f4…0af1` | `audio/dialogue/DLG-EP005-S028-LUMI-v01.mp3` |
| DLG-EP005-S028-MIKKO-v01 | Teddy Twinkle `XjGYkUkzth8BPs29fmcV` | I’m ready to rest. | `4f365a34…2676` | `audio/dialogue/DLG-EP005-S028-MIKKO-v01.mp3` |

- Model: eleven_multilingual_v2.
- One attempt each, no retry by default; at most 2 provider calls.
- Proposed AUDIO/DIALOGUE rows and shot bindings are included.
- Not executed. No placeholder audio.
- **Timing state:**
  - `S028_DIALOGUE_TIMING_STATUS = PENDING_REAL_AUDIO`
  - `NO_SEEDANCE_BEFORE_REAL_DIALOGUE_TIMING_PASS = TRUE`
  - `S028_SEEDANCE_AUTHORISED = FALSE`

## Side-effect audit
`ep005/v05_lineage/PRODUCTION_STATE_SIDE_EFFECT_AUDIT_v1.json`. All prior rows and objects are unchanged.

Inserts:
- 1 script (v05)
- 1 manifest
- 1 readiness record and 14 resolution items (both written by Agent-006)
- 1 REVIEW registry row
- 1 storage object

Updates: 2 status-only.

Zero: ElevenLabs, Higgsfield/Seedance, image or video generation, Agent-007, migrations, C1, billing, publishing.

## Rollback (requires human instruction)
- Delete registry row 739b9aec and storage object d0e61c24.
- Delete readiness 69bff641 and the 14 resolution items under `A006-1791761096896`.
- Delete manifest 0325d35c and script 6498ea8d, or set them to RETIRED.
- v02, 45cc7493 and edc4ad58 remain the governing lineage throughout.

## Open human decisions
1. Approve or reject the S028 frame by exact SHA `9ac6ccc3…6ff0`.
2. Approve readiness `69bff641` (needed before Agent-008 can use the v05 lineage).
3. Authorise the 2 S028 TTS calls.
4. Then G09 on the real clips, then the Seedance decision.
