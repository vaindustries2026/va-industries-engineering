# EP005 Batch 1 — First Four Shots Ready for Human Review (S005, S013, S017, S019)

**Decision source:** Company Brain G03/G08 review decision, 2026-10-20, on commit `5be76f01`.

| Decision | Ruling |
|---|---|
| 1. Real-face smudges | Approved for S004, S012, S017 |
| 2. Mouth side | Mikko's RIGHT, opposite the cheek (S001, S004, S005, S012, S013); supersedes the Phase-0 placeholder side |
| 3. G08 timings | S004 0.5 s, S012 1.0 s, S025 0.5 s |

## Approved production records (exact reviewed candidates)
Each record is one `asset_registry` row:
- type `PRODUCTION_RECORD / G03_PLACEMENT_RECORD | G08_TREATMENT_RECORD`, status APPROVED;
- carries the exact record, its canonical SHA-256, the frame binding, the decisions and the source review evidence;
- written as a single insert, then read back with the canonical SHA recomputed.

Before any write, each G03 record was re-applied by the unchanged G03 module and **reproduced the reviewed output SHA byte-for-byte**. That is what the S004/S012 G08 records are bound to.

| Record | Registry id | Record SHA-256 (prefix) |
|---|---|---|
| G03-REC-EP005-S001-v01 (3 placements) | b51ec1d1-9b36-4efd-9868-0417d2050c80 | b97d24d754cb |
| G03-REC-EP005-S005-v01 (3) | 431fab4d-0b62-4ebe-9324-4f6230efccb9 | 4b121fc87373 |
| G03-REC-EP005-S013-v01 (2) | 5669559f-8b17-4e05-857e-e3db19d9a702 | ec6af454b302 |
| G03-REC-EP005-S004-v01 (6) | 3f08a472-453f-4fea-b612-70f09d186c6b | 45c3deb9ff1d |
| G03-REC-EP005-S012-v01 (4) | 0368f003-f5d0-487b-b082-fdcf8211dfed | 32f82bcf823d |
| G03-REC-EP005-S017-v01 (2) | 87500cdc-4f33-42b2-a892-d851ea4f6aa7 | 3dec85135c40 |
| G03-REC-EP005-S019-v01 (1) | 6ce2cf9d-0263-4dca-a2a6-a5981d35e65f | 9ee67f836457 |
| G08-REC-EP005-S004-v01 (glint, chime 0.5 s) | bcae764d-e6fc-44dc-bb23-30f1dccef83d | 7fe4c60dc342 |
| G08-REC-EP005-S012-v01 (glint 1.0 s) | 3794e0ba-8cfc-41c9-b1cd-557aabaf1bf2 | b5592060b08b |
| G08-REC-EP005-S025-v01 (reflection PRESERVE + pop 0.5 s) | 35b9de65-02d4-4c7a-9d7d-680c69103a19 | 9838577d4db1 |

**Totals:** G03_APPROVED_RECORDS = 7 (21 placements); G08_APPROVED_RECORDS = 3.

## Batch Driver refresh (PLAN_ONLY, deterministic, plan `657e4b99…`)

| Shots | State |
|---|---|
| S005, S013, S017, S019 | READY_FOR_LOCAL_RENDER |
| S001, S012, S026 | WAITING_FOR_DIALOGUE |
| S004, S025 | WAITING_FOR_AUDIO_TIMING |

## Render
**Method:** the existing Agent-008 `LOCAL_RENDER_ONLY` runner:
1. approved base frame (from storage, SHA-verified);
2. approved G03 record → `place_overlays`;
3. G02 `compose_still_shot`, rendering A and B;
4. ambience bed `AMB-BATHROOM-QUIET-v01` at 0 dB, the same as S029.

The batch was run **twice in independent work dirs**: 4 renders per shot, all byte-identical. No code was changed and no capability was added.

| Shot | Review MP4 | SHA-256 | Frames / duration | Storage object | Registry (REVIEW) |
|---|---|---|---|---|---|
| S005 | SHOT-EP005-S005-ASSEMBLED-CAND-v01.mp4 | 3d90e8bbc1945ec91c86897d289aa068fbbb40d53fedc83268cb288511a6e271 | 96 / 4.0 s | 566f0f4c-dac4-426a-ae6e-bb328a4d174e | 7d515dc3-e1bc-4f99-bbe3-f1abd5b59179 |
| S013 | SHOT-EP005-S013-ASSEMBLED-CAND-v01.mp4 | 917b038c6f420e1f68d5d5a7454200951d08766ea7d975b7b37b3bc309ef1240 | 96 / 4.0 s | b7230c42-ecea-4596-a197-1fa88a9ce62f | 3bad029d-40f6-42cb-a383-d472f14d7530 |
| S017 | SHOT-EP005-S017-ASSEMBLED-CAND-v01.mp4 | 83cf8f642c15d6ad0313611876bc302cfebf9b7b09890031e4e29b642ae1a6f9 | 96 / 4.0 s | a1d124f5-bb7a-4661-a9c9-6636a3cdadb0 | 989d21df-b047-4100-84e4-f9fc4efe0ba4 |
| S019 | SHOT-EP005-S019-ASSEMBLED-CAND-v01.mp4 | 618a047819ac4c7b81f1803c5891cd5d56afaeb8f91fcbbf4c3f001cd0ade201 | 120 / 5.0 s | b3b5e08a-35ea-4f3a-aa9c-0a009ea8f090 | 6d9274b5-a092-4a2d-9368-c9d1c4dcad66 |

**Common format:** H.264 High, yuv420p, 1920×1080, 24 fps; AAC LC 48 kHz stereo; ambience bed only; no dialogue.

**Review lifecycle:** S029 pattern: x-upsert false, SHA readback, REVIEW, human_decision PENDING, `approved: false`. Nothing is APPROVED.

## QC
- **Agent-008 QC:** PASS for all four (exact frames, resolution, fps and duration; 1 distinct held frame; overlays pre-composited; 0 re-applied; 0 treatments).
- **Independent QC:** PASS, 20/20 checks per shot (`b1_independent_qc.py`, `B1_INDEPENDENT_QC_v1.json`):

| Check group | What it verifies |
|---|---|
| Format | exact frames and duration, 1920×1080, 24 fps, H.264, one AAC 48k stereo track |
| Overlays | expected overlay count; approved placement certificate (record SHA used = approved); no stale certificate (G03 frame = reproduced approved output); no duplicate G03 application; overlays visible; no clipping |
| Treatment | no unintended treatment |
| Inputs | approved base-frame SHA; ambience-only audio mapping (source unchanged) |
| Audio | no dialogue; no audio clipping (peak about −30.6 dBFS) |
| Determinism | deterministic render |

**QC method note.** The first independent pass flagged three items that turned out to be method issues, not render faults:
1. **Decoded variation:** decoded H.264 frames vary at codec level. Max mean-abs vs frame 0 is 0.029–0.037; the S029 precedent recorded the same kind of variation (0.011). The check is now: 1 distinct pre-encode frame, plus decoded variation < 0.05.
2. **Smudge boxes:** decoded vs G03-frame error inside the overlay boxes is 4.6–5.8, from chroma subsampling on saturated red. The bare base frame differs by 36–46 there. The check is now "< 25% of that".
3. **S017 count:** the provenance counts distinct assets (1) while the record has 2 placements (nose on the mirror and on the face). The check now compares like for like.

Both passes are recorded in the evidence.

## Remaining Batch 1 gates (`batch1_render/B1_REMAINING_GATES_v1.json`)

| Shot | State | Next gates |
|---|---|---|
| S001 | WAITING_FOR_DIALOGUE | Mikko + Lumi TTS (timing risk: ~6.1 s of speech in 6.0 s) → G03 into the motion base frame → provider preflight → Seedance spend authorisation → raw motion approval → final |
| S004 | WAITING_FOR_AUDIO_TIMING | write the Decision-3 chime timing record (0.5 s) → Lumi × 2 TTS (≈ 5.0 s in 5.0 s) → local render (still + glint) → final |
| S012 | WAITING_FOR_DIALOGUE | Lumi × 2 TTS → local render (still + glint) → final |
| S025 | WAITING_FOR_AUDIO_TIMING | write the Decision-3 pop timing record (0.5 s) → Lumi TTS → local render (still + reflection + pop) → final |
| S026 | WAITING_FOR_DIALOGUE | Mikko TTS → provider preflight → Seedance spend authorisation → raw motion approval → final |

## Side-effect audit
- **Counts:**
  - G03_APPROVED_RECORDS = 7; G08_APPROVED_RECORDS = 3.
  - S005, S013, S017, S019 rendered: yes.
- **Zero:** provider calls, image or video generations, ElevenLabs calls, Agent-006/Agent-007 runs.
- **Unchanged:**
  - script, manifest and readiness (both APPROVED);
  - S027, S028, S029 (all assets re-hash equal, rows untouched).
- **Production writes:** 10 approved record rows, plus the 4 REVIEW MP4 objects and their 4 REVIEW rows.
- **Tests:** 205/205 OK (no agent008 code changed).

Anime Clip Farming: untouched.
