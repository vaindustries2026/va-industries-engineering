# EP005 Final Agent-006 Proof v1.0

Date: 2026-10-07. Mikko & Lumi only.

## Approval (Step 1)
Derived manifest `45cc7493-80b4-4e8d-b71d-fbd7fd3656ed` approved by the human via Company Brain; status-only change REVIEW to APPROVED, every other field identical (`evidence/ep005/audio_ingestion/EP005_DERIVED_MANIFEST_APPROVAL_STATUS_ONLY_DIFF_v1.json`, `evidence/EP005_DERIVED_MANIFEST_APPROVAL_v1.0.md`). Approval commit: `d1ab62cc2a09e60e7e6c191b241087d5a59abd29`. Source `96df250f` unchanged (APPROVED).

## Run (Step 2)
- Agent-006 `ZTBdnKFO8STSjJU4`, version `9bf6bbef-d49a-4f50-bce5-f8f146d43ca8`, unpublished, not modified.
- Single-use caller `ntqoBdrDyUHiGjVc` (Manual Trigger + Execute Workflow, input `production_manifest_id` only, no credentials), executed once, then archived.
- Caller execution **578** (success); Agent-006 execution **579** (success, 04:10:02.346Z to 04:10:19.828Z).
- Run id `A006-1791346204213`.
- Readiness manifest `edc4ad58-3e5d-4ac2-9c74-c9af03af363f`: status **REVIEW**, readiness_state **READY_FOR_HUMAN_APPROVAL**, requirement_count 14, resolved_reuse 14, create_new 0, human_review 0, blocked 0. Not approved.

## Resolution table
| # | Requirement key | Resolution | Canonical asset | Matches | Shots |
|---|---|---|---|---|---|
| 1 | `APPROVED_NEW::OVERLAY-EP005-BERRY-SMUDGE-CHEEK-v01` | REUSE_EXISTING | `OVERLAY-EP005-BERRY-SMUDGE-CHEEK-v01` | 1 | 9 |
| 2 | `APPROVED_NEW::OVERLAY-EP005-BERRY-SMUDGE-MOUTH-v01` | REUSE_EXISTING | `OVERLAY-EP005-BERRY-SMUDGE-MOUTH-v01` | 1 | 15 |
| 3 | `APPROVED_NEW::OVERLAY-EP005-BERRY-SMUDGE-NOSE-v01` | REUSE_EXISTING | `OVERLAY-EP005-BERRY-SMUDGE-NOSE-v01` | 1 | 21 |
| 4 | `APPROVED_NEW::TMP_EP005_SOFT_CLOTH` | REUSE_EXISTING | `PROP-EP005-CLEANING-CLOTH-v01` | 1 | 28 |
| 5 | `APPROVED_NEW::TMP_EP005_HAND_MIRROR` | REUSE_EXISTING | `PROP-EP005-HAND-MIRROR-v01` | 1 | 29 |
| 6 | `APPROVED_REUSE::Lumi clue chime` | REUSE_EXISTING | `SFX-LUMI-CLUE-CHIME` | 1 | 1 |
| 7 | `APPROVED_REUSE::Mikko TRY whoosh` | REUSE_EXISTING | `SFX-MIKKO-TRY-WHOOSH` | 1 | 1 |
| 8 | `APPROVED_REUSE::WIN sparkle chord` | REUSE_EXISTING | `SFX-WIN-SPARKLE-CHORD` | 1 | 1 |
| 9 | `APPROVED_REUSE::AMB-BATHROOM-QUIET-v01` | REUSE_EXISTING | `AMB-BATHROOM-QUIET-v01` | 1 | 20 |
| 10 | `APPROVED_REUSE::FOLEY-CLOTH-SOFT-v01` | REUSE_EXISTING | `FOLEY-CLOTH-SOFT-v01` | 1 | 7 |
| 11 | `APPROVED_REUSE::SFX-COMPLETION-POP-v01` | REUSE_EXISTING | `SFX-COMPLETION-POP-v01` | 1 | 1 |
| 12 | `TBD::CHARACTER::Lumi` | REUSE_EXISTING | `CHAR-LUMI-MASTER-v01` | 1 | 29 |
| 13 | `TBD::CHARACTER::Mikko` | REUSE_EXISTING | `CHAR-MIKKO-MASTER-v01` | 1 | 29 |
| 14 | `TBD::ENVIRONMENT::Canonical environment/background` | REUSE_EXISTING | `WORLD-EP005-BATHROOM-MASTER-v01` | 1 | 29 |

Counts: 14 REUSE_EXISTING; 0 NEEDS_HUMAN_REVIEW; 0 CREATE_NEW; 0 BLOCKED; 0 ambiguous (every requirement has exactly one exact candidate). The three audio requirements resolve to the exact new ids with no alias. Human review queue and asset creation queue are empty. Matches the offline simulation.

Note: the "3 visual TBD" labels in the manifest context are the generic Lumi / Mikko / environment entries, which resolved to the C1 character and bathroom world masters.

## Audit (before to after)
- asset_resolution_items 58 to 72: +14 under `A006-1791346204213` (all REUSE_EXISTING, status REVIEW); the prior 58 rows md5 `c7420ca1...` unchanged.
- production_readiness_manifests 6 to 7: +`edc4ad58`; the prior 6 md5 `843ada87...` unchanged.
- asset_registry 23 rows md5 `35a3624a...`, episode_production_manifests 11 rows md5 `4f74a0e4...` (5 APPROVED / 6 REVIEW), production-assets storage 19 objects md5 `3c9f134f...`: all identical before and after the run.
- Agent-007 executions: 0 (only executions 578 and 579 occurred). Provider/generation calls: 0. Paid calls: 0. ElevenLabs calls: 0. Migrations: 0.

## Rollback
Delete readiness manifest `edc4ad58...` and the 14 `asset_resolution_items` of run `A006-1791346204213` (inert REVIEW rows; no deletion performed). To undo the approval: `UPDATE episode_production_manifests SET status='REVIEW' WHERE id='45cc7493-...'`. Workflows: Agent-006 unchanged; caller archived.
