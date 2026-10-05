# EP005 Berry Requirement Repair: Derived Manifest Created (REVIEW)

**Date:** 2026-10-05 (UTC)
**Actor:** Claude Code (bounded engineering operator)
**Approved by:** Gilang / Company Brain. The approved design covers: a derived manifest, the source left unchanged, a REVIEW status, run id `DRV-EP005-BERRY-SPLIT-1-A005O-1790400144423`, an S013 nose entry, and the two free-text notes left unchanged.
**Scope:** Mikko & Lumi only.
**Result:** `COMPLETE`. The derived row stays in **REVIEW** and has not been approved.

## 1. Origin of the combined requirement (from the design phase, reconfirmed)

| Layer | Location | What happens |
|---|---|---|
| Agent-004 `zcWjXBD1PXcRWNoK` | `episode_scripts.production_script_json` of the APPROVED script `14471926`: `asset_summary.unique_new_asset_ids[0]` and `shots[S001,S009,S015,S021].asset_id` | The schema allows one `asset_id` per shot. All three marks were declared as `TMP_EP005_BERRY_SMUDGE_OVERLAYS`. |
| Agent-005 `oHXIgg7khm0FgLvB` (version 517b11ef) | node `12 - Build Episode Production Manifest` (`registerAsset`, `assetMap` keyed by asset_id) | Seeds from the Agent-004 IDs and groups them into one `asset_inventory` entry. |
| Agent-006 `ZTBdnKFO8STSjJU4` (version 9bf6bbef) | node `05 - Build Asset Resolution Work Items` | Creates one `APPROVED_NEW::<id>` per `source_approved_assets.unique_new_asset_ids` entry, so there is one berry requirement. |

## 2. Transform

- **Script:** `evidence/ep005/berry_split/ep005_berry_requirement_split_v1.py`. It is deterministic and uses no LLM.
- **Input:** a GET of source row `670b201b`.
- **Output:** the derived row, with no id or created_at.

**What it does:**
- Splits the combined ID into the three registered asset_ids in four places: `source_approved_assets.unique_new_asset_ids`, `asset_inventory`, `unique_new_assets` and `production_phases[].asset_ids`. Each new inventory entry has labels = [the mark label], the original asset_types and status, `derived_from_asset_id`, and `used_in_shots` taken from the continuity data.
- **Shot attribution:** taken only from `shot_plans[].shot_plan.continuity_state.tracked_elements`. A shot counts if the mark is visible at its start or end.
- **Per-shot overlay entries:**
  - 10 mark-specific entries are retagged to their mark (curly and straight apostrophes are treated as equal).
  - 17 generic entries are expanded into 34 mark entries, using the marks visible in each shot (`derived_from_element` is kept).
  - 1 continuity gap is filled: **S013 nose**. It copies the usage and role of the S013 berry entry and records `derived_from` as the continuity data.
- Adds `manifest_json.derivation` (lineage, split map, attribution rule, gap fills, free-text note, approval requirement) and sets `manifest_version` to `+berry-split-1`.
- **Row columns:** `production_plan_run_id` = DRV-EP005-BERRY-SPLIT-1-A005O-1790400144423, `unique_new_asset_count` = 5, `status` = REVIEW, `agent_version` = manifest-derivation-ep005-berry-split-v1. All other columns are copied unchanged.
- **Left verbatim (approved):** the two legacy free-text `production_order_notes` (S002, in both `shot_plan` and `shot_queue`).

**Invariants.** The script fails closed if any of these break. All passed:
- The source must be the APPROVED `670b201b` / `A005O-1790400144423` row.
- Each of the three tracked elements must exist in every shot.
- The per-mark shots must equal the approved shots exactly:

  | Mark | Shots | Removal shot |
  |---|---|---|
  | Cheek | S001–S009 | S009 |
  | Mouth | S001–S015 | S015 |
  | Nose | S001–S021 | S021 |

- In each removal shot, the mark must be visible at the start and not at the end.
- The three shot lists together must equal the original `used_in_shots` (S001–S021).
- The gap fills must be exactly {S013 nose}.
- No structured field may still carry the combined ID.
- No shot may have duplicate berry entries.
- Each shot's berry overlay entries must equal the marks visible there per continuity.

## 3. Write: one plain insert

`POST /rest/v1/episode_production_manifests` with no upsert returned HTTP 201.

| Field | Value |
|---|---|
| id | **`3bcde9ee-6676-480f-90da-5695b64532a7`** |
| created_at | 2026-10-05T06:03:12.791125Z |
| status | **REVIEW** |
| production_plan_run_id | DRV-EP005-BERRY-SPLIT-1-A005O-1790400144423 |
| unique_new_asset_count | 5 |
| manifest_json sha256 (canonical JSON, sorted keys) | `3b855d95b7fc5bbffabbac22bbdebc2c4e702cf113b52192591f7602bb3fd0ec` |

**Readback:** all 21 written fields equal the transform output exactly; there are 0 mismatches.

## 4. Source manifest 670b201b unchanged

| Fingerprint | Before | After |
|---|---|---|
| Server `md5(to_jsonb(row)::text)` | `249adbfe4a9ddbc6c75446994979fe0d` | `249adbfe4a9ddbc6c75446994979fe0d` |
| Server `md5(manifest_json::text)` | `da69805527dae414efb5d1823c0b7a97` | `da69805527dae414efb5d1823c0b7a97` |
| Client canonical sha256 of the full row | `1666ee3c…6cdb` | `1666ee3c…6cdb` |
| Status | APPROVED | APPROVED |

## 5. In-memory Agent-006 proof

- **Harness:** `evidence/ep005/berry_split/agent006_inmemory_sim.js`.
- **Code under test:** the unmodified node 03, 05, 07 and 08 jsCode from the workflow export, which is identical to live `9bf6bbef`.
- **Inputs:** the live APPROVED/LOCKED registry (11 governed rows). The manifest status is set to APPROVED in memory only, to model the state after human approval.
- **n8n:** no execution.

| Requirement | Shots | Exact matches | Resolution | Node 08 |
|---|---|---|---|---|
| APPROVED_NEW::OVERLAY-EP005-BERRY-SMUDGE-CHEEK-v01 ("Berry smudge on Mikko's anatomical left cheek") | S001–S009 (9) | CHEEK row only | REUSE_EXISTING | ok |
| APPROVED_NEW::OVERLAY-EP005-BERRY-SMUDGE-MOUTH-v01 ("Berry smudge on skin beside Mikko's mouth") | S001–S015 (15) | MOUTH row only | REUSE_EXISTING | ok |
| APPROVED_NEW::OVERLAY-EP005-BERRY-SMUDGE-NOSE-v01 ("Berry smudge on Mikko's nose") | S001–S021 (21) | NOSE row only | REUSE_EXISTING | ok |
| Mirror, cloth | 29, 28 | 1 each | REUSE_EXISTING | ok |
| 3 approved audio (Lumi clue chime, Mikko TRY whoosh, WIN sparkle chord) | 1 each | 1 each | REUSE_EXISTING | ok |
| Mikko, Lumi, environment (C1) | 29 each | 1 each | REUSE_EXISTING | ok |
| 3 visual TBDs and 4 audio TBDs | unchanged | 0 | NEEDS_HUMAN_REVIEW | ok |

**Comparison with the source manifest:**
- 16 requirements become 18.
- The 15 requirements other than berry are field-for-field identical to the baseline simulation of `670b201b`.
- Removed: `APPROVED_NEW::TMP_EP005_BERRY_SMUDGE_OVERLAYS`. Added: the three overlay requirements.
- The simulation of the **live inserted row** (`3bcde9ee`) is identical to the simulation run before the write.

**S013 after derivation:** two berry overlay entries, MOUTH (retagged) and NOSE (derived from continuity).

**Negative controls:**

| Control | Result |
|---|---|
| NC1: derived row in its real REVIEW status | node 03 `AGENT-006 BLOCKED (MANIFEST_NOT_APPROVED_OR_NOT_FOUND)`. The approval gate holds. |
| NC2: the three overlay rows removed from the registry | all three berry requirements resolve CREATE_NEW |
| NC3: a duplicate APPROVED row claiming the cheek label | cheek resolves NEEDS_HUMAN_REVIEW with 2 exact matches; the ambiguity is still caught |

Simulation outputs are stored in `evidence/ep005/berry_split/`.

## 6. Side-effect check (live, after the write)

| Item | Before | After |
|---|---|---|
| episode_production_manifests | 8 (2 APPROVED) | 9 (2 APPROVED; new row REVIEW) |
| asset_registry | 20 | 20 (identical to the post-pack snapshot) |
| readiness / ARI / jobs / batches | 5 / 40 / 11 / 3 | 5 / 40 / 11 / 3 |
| storage.objects | 16 | 16 |
| Migrations | 1 | 1 |
| Agent-006 | 9bf6bbef, unpublished | 9bf6bbef, unpublished |

## 7. Rollback

```sql
delete from public.episode_production_manifests where id = '3bcde9ee-6676-480f-90da-5695b64532a7';
```

The source manifest, registry, storage and workflows need no rollback.

## 8. Next step (not done; needs separate authorisation)

1. Human (G3) manifest approval of `3bcde9ee`. This is a production-plan approval, not readiness or paid-generation approval.
2. Separately, any Agent-006 run against it.

Future root-cause item: change Agent-004's schema so independently removable marks are declared as separate new assets.

## 9. Safety confirmation

- Supabase writes: 1 row insert (`episode_production_manifests`, REVIEW). Nothing else was written.
- Registry changes: 0. Storage changes: 0. C1 canon and the five EP005 assets are untouched.
- n8n writes: 0. Workflow code changes: 0 (Agent-004, 005, 006 and 007).
- Agent-006 executions: 0. Agent-007 executions: 0. Publications: 0.
- Manifest approvals: 0. Readiness approvals: 0.
- Generation, transformation, provider and paid calls: 0. Migrations: 0.
- Agent-000 and S3-B: untouched.

## 10. Final status

```text
EP005_BERRY_DERIVED_MANIFEST_CREATED_REVIEW
+ SOURCE_MANIFEST_670B201B_UNCHANGED
+ BERRY_REQUIREMENTS_SPLIT_3_WAYS
+ S013_NOSE_ENTRY_ADDED_FROM_CONTINUITY
+ DERIVED_REQUIREMENT_COUNT_18
+ IN_MEMORY_AGENT006_MATCH_PROOF_PASS
+ ZERO_AGENT006_PRODUCTION_RUN
+ ZERO_AGENT007_RUN
+ ZERO_REGISTRY_CHANGE
+ ZERO_WORKFLOW_CODE_CHANGE
+ ZERO_MIGRATION
+ EVIDENCE_COMMITTED_TO_GITHUB
```

**Stop condition:** the task is complete. The derived manifest stays in REVIEW until a separate human approval.
