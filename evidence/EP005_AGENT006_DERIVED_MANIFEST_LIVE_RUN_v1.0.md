# EP005 Agent-006 Live Resolution Run on the Derived Manifest 3bcde9ee

**Date:** 2026-10-05 (UTC)
**Actor:** Claude Code (bounded engineering operator)
**Authorised by:** Company Brain. The authorisation was exactly ONE Agent-006 run against `3bcde9ee-6676-480f-90da-5695b64532a7`. It did not cover Agent-007, generation, provider or paid calls, readiness approval, publication or any workflow, registry, storage or manifest change.
**Scope:** Mikko & Lumi only.
**Result:** `PASS`

## 1. Pre-run verification (live, 2026-10-05T06:16:59Z; all passed)

| Check | Result |
|---|---|
| Manifest `3bcde9ee` | APPROVED; row md5 `931d64dfaca0b235ea70ea698cef7eea`; md5 excluding status `caafdbd5…` (= evidence) |
| Source `670b201b` | APPROVED; row md5 `249adbfe4a9ddbc6c75446994979fe0d` (unchanged) |
| asset_registry | 20 rows (11 APPROVED, 9 REVIEW), identical to the post-pack snapshot; md5 `b7b46112661dc0a0d9218e647f747306` |
| Governed (APPROVED/LOCKED) rows | 11: the 3 C1 rows, 5 EP005 assets and 3 SFX. **No governed token is claimed by more than one row** (asset_id, name and aliases, Agent-006 normalisation). |
| Agent-006 `ZTBdnKFO8STSjJU4` | version `9bf6bbef-d49a-4f50-bce5-f8f146d43ca8`, active false, activeVersionId null, 20 nodes. Node types are Code, Supabase, IF, Set, Limit, SplitInBatches and StopAndError only, so it has no provider, HTTP or generation nodes. |
| Instance executions before the run | latest #575 (2026-09-29); no retained Agent-006 or Agent-007 executions |

**Pre-run fingerprints (server md5 over all rows):**

| Table | Rows | md5 |
|---|---|---|
| episode_production_manifests | 9 | `0e9032d6…` |
| storage.objects | 16 | `4c7ef85e…` |
| asset_resolution_items | 40 | `feb133cc…` |
| production_readiness_manifests | 5 | `9338a06f…` |
| asset_creation_jobs | 11 | `12307bb2…` |
| asset_creation_batches | 3 | `a53e0e9a…` |
| shot_production_plans | 319 | `b2e24ac7…` |
| episode_scripts | | `9e3da61a…` |
| migrations | 1 | |

## 2. Execution: the existing mechanism (as ENG-20260926-019)

- **Why a caller is needed:** the n8n MCP execute tool cannot feed Agent-006's "When Executed by Another Workflow" trigger. The established single-use caller was therefore used.
- **Caller:** `AQ4JEKWd0cQOUmJV` "CALLER — Agent-006 EP005 derived manifest 3bcde9ee controlled run (single use)". It has 2 nodes (Manual Trigger, Execute Workflow v1.4 in mode once with wait true), passes only `production_manifest_id = 3bcde9ee-6676-480f-90da-5695b64532a7`, and has no credentials.
- **After the run:** the caller was **archived**.
- **Agent-006:** not edited; its TEST node was not touched.

| Item | Value |
|---|---|
| Caller execution | **576** (manual, success, 06:18:15.958Z → 06:18:39.209Z) |
| Agent-006 execution | **577** (integrated, parent 576, success, 06:18:16.155Z → 06:18:39.072Z, last node `14 - Build Agent-006 Director Brief`, no error). One run, no retry. |
| production_manifest_id | `3bcde9ee-6676-480f-90da-5695b64532a7` |
| asset_resolution_run_id | **`A006-1791181098027`** |
| Readiness manifest | **`e32ef7eb-448d-4da8-8271-fabf51bdc81e`**: status **REVIEW**, readiness_state **NEEDS_HUMAN_REVIEW**, requirement_count 18, resolved_reuse 11, create_new 0, human_review 7, blocked 0 |

## 3. Live resolution (all 18 `asset_resolution_items`, status REVIEW)

| Requirement | Shots | Matches | Resolution | Canonical asset_id |
|---|---|---|---|---|
| APPROVED_NEW::OVERLAY-EP005-BERRY-SMUDGE-CHEEK-v01 | 9 (S001–S009) | 1 | REUSE_EXISTING | OVERLAY-EP005-BERRY-SMUDGE-CHEEK-v01 |
| APPROVED_NEW::OVERLAY-EP005-BERRY-SMUDGE-MOUTH-v01 | 15 (S001–S015) | 1 | REUSE_EXISTING | OVERLAY-EP005-BERRY-SMUDGE-MOUTH-v01 |
| APPROVED_NEW::OVERLAY-EP005-BERRY-SMUDGE-NOSE-v01 | 21 (S001–S021) | 1 | REUSE_EXISTING | OVERLAY-EP005-BERRY-SMUDGE-NOSE-v01 |
| APPROVED_NEW::TMP_EP005_HAND_MIRROR | 29 | 1 | REUSE_EXISTING | PROP-EP005-HAND-MIRROR-v01 |
| APPROVED_NEW::TMP_EP005_SOFT_CLOTH | 28 | 1 | REUSE_EXISTING | PROP-EP005-CLEANING-CLOTH-v01 |
| TBD::CHARACTER::Mikko | 29 | 1 | REUSE_EXISTING | CHAR-MIKKO-MASTER-v01 |
| TBD::CHARACTER::Lumi | 29 | 1 | REUSE_EXISTING | CHAR-LUMI-MASTER-v01 |
| TBD::ENVIRONMENT::Canonical environment/background | 29 | 1 | REUSE_EXISTING | WORLD-EP005-BATHROOM-MASTER-v01 |
| APPROVED_REUSE::Lumi clue chime | 1 | 1 | REUSE_EXISTING | SFX-LUMI-CLUE-CHIME |
| APPROVED_REUSE::Mikko TRY whoosh | 1 | 1 | REUSE_EXISTING | SFX-MIKKO-TRY-WHOOSH |
| APPROVED_REUSE::WIN sparkle chord | 1 | 1 | REUSE_EXISTING | SFX-WIN-SPARKLE-CHORD |
| TBD::OVERLAY_VFX::Mirror glint treatment | 3 | 0 | NEEDS_HUMAN_REVIEW | none |
| TBD::OVERLAY_VFX::Mirror reflection/compositing treatment | 6 | 0 | NEEDS_HUMAN_REVIEW | none |
| TBD::OVERLAY_VFX::Soft completion pop visual accent | 1 | 0 | NEEDS_HUMAN_REVIEW | none |
| TBD::AUDIO::AMBIENCE | 20 | 0 | NEEDS_HUMAN_REVIEW | none |
| TBD::AUDIO::FOLEY_CLOTH | 7 | 0 | NEEDS_HUMAN_REVIEW | none |
| TBD::AUDIO::COMPLETION_SFX | 1 | 0 | NEEDS_HUMAN_REVIEW | none |
| TBD::AUDIO::FOLEY_TOUCH | 1 | 0 | NEEDS_HUMAN_REVIEW | none |

**Totals:**
- 18 requirements: 11 REUSE_EXISTING (each with exactly 1 match) and 7 NEEDS_HUMAN_REVIEW (0 matches, no canonical ID).
- Multi-match or ambiguous resolutions: 0. CREATE_NEW: 0. BLOCKED: 0.
- The 3 visual TBDs and 4 audio TBDs remain human-review items and were not converted.
- **Live vs in-memory proof:** all 18 requirements match exactly on resolution, canonical ID, exact candidates and shots (`sim_derived_3bcde9ee_post_approval_real_status.json`).

**Raw records:**
- `evidence/ep005/agent006_run/asset_resolution_items_A006-1791181098027.json`
- `evidence/ep005/agent006_run/production_readiness_manifest_e32ef7eb.json`

## 4. Post-run audit (live, 06:19:49Z)

| Item | Before | After | Verdict |
|---|---|---|---|
| asset_resolution_items | 40 (`feb133cc…`) | 58; the prior 40 are still `feb133cc…`; +18 only under A006-1791181098027 | authorised insert only |
| production_readiness_manifests | 5 (`9338a06f…`) | 6; the prior 5 are still `9338a06f…`; +1 `e32ef7eb` (REVIEW / NEEDS_HUMAN_REVIEW) | authorised insert only |
| episode_production_manifests (incl. `3bcde9ee` `931d64df…`, `670b201b` `249adbfe…`) | 9, `0e9032d6…` | same | unchanged |
| asset_registry (incl. C1 and the 5 EP005 rows) | 20, `b7b46112…` | same | unchanged |
| storage.objects (incl. C1 and the 5 EP005 objects) | 16, `4c7ef85e…` | same | unchanged |
| asset_creation_jobs / batches | 11 `12307bb2…` / 3 `a53e0e9a…` | same | unchanged; no generation job |
| shot_production_plans / episode_scripts | 319 `b2e24ac7…` / `9e3da61a…` | same | unchanged |
| Migrations | 1 | 1 | unchanged |
| Agent-006 | 9bf6bbef, unpublished | 9bf6bbef, unpublished | unchanged |
| n8n executions since the run | | 576 (caller) and 577 (Agent-006) only; no Agent-007 execution | |

## 5. Readiness manifest handling

`e32ef7eb` was left as status **REVIEW** with readiness **NEEDS_HUMAN_REVIEW**. It was not approved.

Agent-007 only accepts APPROVED + NEEDS_ASSET_CREATION (ENG-20260926-019), so this record cannot trigger generation. Agent-007 was not run.

## 6. Rollback / containment

- **Workflows:** nothing to roll back. Agent-006 is unchanged; caller `AQ4JEKWd0cQOUmJV` is archived.
- **Run records:** the 18 ARI rows and `e32ef7eb` are REVIEW and inert. As in the previous run, they stay as evidence; deleting them is not authorised.
- **Future runs:** a later Agent-006 run creates a new run id and won't conflict.

## 7. Open human items (not actioned)

- **Remaining TBDs:** 3 visual (mirror glint, mirror reflection/compositing, completion-pop accent) and 4 audio (AMBIENCE, FOLEY_CLOTH, COMPLETION_SFX, FOLEY_TOUCH) need human asset decisions.
- **Readiness approval** of `e32ef7eb` is a separate human decision.
- **F-1 from ENG-20260926-019:** the SFX registry storage_path values don't match the stored object names. This affects a later download by storage_path, not resolution. Still open.

## 8. Safety confirmation

- Agent-006 executions: 1 (577). Agent-007 executions: 0. Publications: 0.
- Workflow modifications: 0. The single-use caller was created, run once and archived, as in the established mechanism.
- Supabase writes: only Agent-006's own inserts (18 ARI rows and 1 readiness manifest).
- Registry, storage, manifest and C1 changes: 0.
- Generation, transformation, provider (OpenAI, Gemini, Runway) and paid calls: 0.
- Readiness approvals: 0. Migrations: 0.
- Agent-004/005 reruns: 0. Agent-000, S3-B and Anime Clip Farming: untouched.

## 9. Final status

```text
EP005_AGENT006_DERIVED_MANIFEST_LIVE_RESOLUTION_PASS
+ DERIVED_MANIFEST_3BCDE9EE_USED
+ REQUIREMENT_COUNT_18
+ CHEEK_REUSE_EXISTING + MOUTH_REUSE_EXISTING + NOSE_REUSE_EXISTING
+ MIRROR_REUSE_EXISTING + CLOTH_REUSE_EXISTING
+ MIKKO_REUSE_EXISTING + LUMI_REUSE_EXISTING + BATHROOM_REUSE_EXISTING
+ APPROVED_AUDIO_REUSE_EXISTING
+ TRUE_TBDS_REMAIN_HUMAN_REVIEW
+ ZERO_AMBIGUOUS_MATCHES
+ ZERO_AGENT007_RUN + ZERO_GENERATION + ZERO_PAID_CALLS + ZERO_READINESS_APPROVAL
+ C1_CANON_UNCHANGED + EP005_ASSETS_UNCHANGED
+ SOURCE_MANIFEST_UNCHANGED + DERIVED_MANIFEST_UNCHANGED
+ EVIDENCE_COMMITTED_TO_GITHUB
```

**Stop condition:** the task is complete. Claude Code will not continue into readiness approval or any Agent-007 work without separate authorisation.
