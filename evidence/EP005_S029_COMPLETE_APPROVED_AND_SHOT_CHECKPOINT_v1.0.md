# EP005 S029 COMPLETE_APPROVED + read-only EP005 shot-production checkpoint (2026-10-12)

Mikko & Lumi only. Anime Clip Farming not touched.

Calls: 0 provider, 0 render, 0 Agent-006, 0 Agent-007.

## 1. S029 human approval
- **Decision:** Company Brain / Gilang APPROVED `SHOT-EP005-S029-ASSEMBLED-v01`, SHA `b8a4e3b4233a31646d046000ffac5332aef0fe19d0a2a3f1ab67285fb3b137d6`.
- **Evidence basis:** `b794d235`.
- **Codec decision:** `S029_H264_STATIC_FRAME_VARIANCE = ACCEPTED_CODEC_BEHAVIOUR`.
  - The decoded-frame differences are H.264 quantisation and temporal-prediction residue.
  - They are not visual motion and not a blocker.
  - The encoder is unchanged and nothing was re-rendered.

## 2. Registry transition
Row `cf6584d5-9a4d-4788-b509-1d7320a8e28e`. PATCH guarded on `id`, `status=REVIEW` and `sha256`.

| Changed | Value |
|---|---|
| status | REVIEW→APPROVED |
| human_decision | APPROVED |
| human_approval | APPROVED |
| approved | true |
| approved_sha256 | bound to the exact SHA |
| approval_authority, approval_basis, S029_H264_STATIC_FRAME_VARIANCE | added |

Nothing else changed. The stored MP4 was re-hashed before and after: `b8a4e3b4…37d6`, 680,070 B.

**Read-back:**

| Field | Value |
|---|---|
| asset_id | SHOT-EP005-S029-ASSEMBLED-v01 |
| asset_type / asset_subtype | SHOT_RENDER / ASSEMBLED_SHOT |
| status | APPROVED |
| human_decision / human_approval / approved | APPROVED / APPROVED / true |
| SHA | b8a4e3b4…37d6 |
| storage path | `production-assets/visual/production/ep005/shots/SHOT-EP005-S029-ASSEMBLED-v01.mp4` |
| duration / resolution / fps / frames | 6.0 s / 1920x1080 / 24/1 / 144 |

## 3. S029 closure
`S029_PRODUCTION_STATUS = COMPLETE_APPROVED`. Full record: `agent008/phase1/s029/S029_CLOSURE_v1.json`.

Preserved decisions:
- S028 raw frame 119 is the continuity source.
- The cloth stays on Mikko's shoulder in Lumi's hand.
- Static 6 s hold; breathing omitted.
- Bathroom ambience only. No dialogue, foley, SFX, music, fade, end card, logo or credits.

S029 is not to be reopened without explicit Company Brain authorisation.

## 4. Non-regression (read-only)
- **Registry and storage:** all fingerprints equal the baseline.

  | Object | Fingerprint |
  |---|---|
  | scripts | 5:649d63f9… |
  | manifests | 12:cefb8fa2… |
  | readiness | 8:f5c646ee… |
  | resolution items | 86:ce5ac459… |
  | registry outside S028/S029 | 899d7f33… |
  | storage outside S029 | 28:c50f2619… |

- **Approved lineage:** script v05 `6498ea8d`, manifest `0325d35c` and readiness `69bff641` are all APPROVED and unchanged.
- **Stored bytes** were re-hashed against the registry, all equal:
  - S027 shot `7b01c392…8fde`
  - S028 shot `1d5dfabd…7cc0`
  - S029 shot `b8a4e3b4…37d6`
  - S029 base frame `a8b0d0fc…23e4`
  - ambience `ea28fad4…4d2f`
- **S027 and S028:** every row is still APPROVED, with SHAs and updated_at unchanged.

## 5. EP005 shot-production checkpoint (read-only)
- **Script:** `agent008/phase1/ep005_shot_checkpoint.py`.
- **Output:** `agent008/phase1/EP005_SHOT_PRODUCTION_CHECKPOINT_v1.json`.
- **Sources:**
  - Live Agent-008 resolution of approved readiness 69bff641.
  - Live registry.
  - Batch 0C/0D plan: method, base-frame source, open code gaps and planned provider calls.

**Q1. Final approved assembled shots: 3 of 29.**

**Q2. COMPLETE_APPROVED:**

| Shot | Asset | SHA |
|---|---|---|
| S027 | SHOT-EP005-S027-ASSEMBLED-v01 | 7b01c392…8fde |
| S028 | SHOT-EP005-S028-ASSEMBLED-v01 | 1d5dfabd…7cc0 |
| S029 | SHOT-EP005-S029-ASSEMBLED-v01 | b8a4e3b4…37d6 |

**Q3. Still lacking final approved assembled shots: 26** (S001–S026).

**Q4. Agent-008 classification of the 26:**

| Classification | Shots | Open code gaps |
|---|---|---|
| deterministic still | S024 (2 s camera settle) | G06 |
| deterministic derived-frame | S023 (S022 end state) | none; waits on approved S022 motion |
| deterministic composite | S003, S004, S005, S008, S012, S013, S017, S018, S019, S025 | G03 (all except S025); G08 on S004, S012, S018, S025; G07 on S018 |
| existing motion reuse | none: no approved motion exists for any remaining shot | n/a |
| provider motion required | S006, S022, S026 | S006: G03 + G08; S022 and S026: none |
| provider motion + deterministic composite (hybrid) | S001, S002, S007, S010, S011, S014, S016, S020 | G03 |
| blocked | S009, S015, S021 (smudge removal under a generated cloth pass) | G11 |

Two composite shots also need a new base frame from image generation: S003 and S018.

**Remaining preconditions:**
- **Dialogue:** 20 dialogue lines across the remaining shots have no clip. Only S027 and S028 dialogue exists.
- **Visible speech:** the H4 decision is open on every dialogue shot.
- **Approved base frames:** none exist for S001–S026.
- **Zero-spend shots:** no remaining shot can be produced at zero spend today. S023 is code-ready but needs the S022 end frame. S022 is downstream of S021, which is blocked by G11.

**Q5. Smallest logical next production batch: S026, one shot.**
- **Why S026:**
  - It is the shot immediately before approved S027, so it extends the finished S026–S029 tail.
  - It has no open Agent-008 code gaps and no overlays or treatments.
  - It uses the already-proven S027/S028 motion path.
- **What it needs** (each one a separate human authorisation):
  - a new F-MEDIUM-TWOSHOT base frame: 1 image generation, or an approved alternative source
  - 1 Mikko TTS line, "One little spot at a time!"
  - an H4 visible-speech decision
  - an S026 end → S027 start continuity decision
  - 1 Seedance generation, about $3.40 list for 5 s at 1080p
- **Side benefit:** the same F-MEDIUM-TWOSHOT frame is planned for S002, S017 and S023.
- **Zero-spend alternative:** an engineering batch on G03 (overlay anchor placement). It is the gap that unlocks the most shots (18) but produces no shot by itself.

Nothing was produced in this task.

## Rollback (requires human instruction)
To revert the approval, PATCH row `cf6584d5` back to status REVIEW with `human_decision` / `human_approval` PENDING and `approved` false. The pre-approval row is in `S029_ASSEMBLED_ROW_PRE_APPROVAL_v1.json`.
