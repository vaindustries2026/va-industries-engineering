# EP005 Remaining-TBD Cleanup: Second Derived Manifest Created (REVIEW)

**Date:** 2026-10-05 (UTC)
**Actor:** Claude Code (bounded engineering operator)
**Human decisions:** Gilang, recorded by Company Brain, following the EP005 remaining-TBD decision brief.
**Scope:** Mikko & Lumi only.
**Result:** `COMPLETE`. The new row stays in **REVIEW** and has not been approved.

## 1. Human decisions applied

| TBD | Decision | Handling in the derived manifest |
|---|---|---|
| Mirror glint treatment (S004, S012, S018) | DERIVE/COMPOSITE FROM EXISTING; not an asset | → `TREATMENT-EP005-MIRROR-GLINT-v01`: one compositor preset (small soft specular glint, opacity/scale envelope of about 6–10 frames, on the glass near the reflected mark, non-magical, same look each time) |
| Mirror reflection/compositing treatment (S006, S007, S010, S011, S014, S025) | NOT A SEPARATE ASSET | → `TREATMENT-EP005-MIRROR-REFLECTION-v01`: shot-level compositing with PROP-EP005-HAND-MIRROR-v01, CHAR-MIKKO-MASTER-v01 and the berry overlays active per continuity |
| Soft completion pop visual accent (S025) | NOT A SEPARATE ASSET; **KEEP** | → `TREATMENT-EP005-COMPLETION-POP-ACCENT-v01`: subtle brightness/bloom pulse on the glass, about 6–8 frames, synced with the completion-pop audio; must not imply removal |
| AMBIENCE | CREATE_NEW audio later (proposed AMB-BATHROOM-QUIET-v01) | remains an unresolved audio TBD, **not mapped** |
| FOLEY_CLOTH | CREATE_NEW audio later (proposed FOLEY-CLOTH-SOFT-v01) | remains an unresolved audio TBD, **not mapped** |
| COMPLETION_SFX | CREATE_NEW audio later (proposed SFX-COMPLETION-POP-v01) | remains an unresolved audio TBD, **not mapped** |
| FOLEY_TOUCH (S028) | **DROPPED** | removed as a requirement; recorded in `dropped_requirements`; S028 visual shoulder-pat unchanged |

None of the treatments is eligible for Agent-007, and none needs paid generation.

## 2. Transform

- **Script:** `evidence/ep005/tbd_cleanup/ep005_tbd_cleanup_v1.py`. It is deterministic and uses no LLM.
- **Source:** the APPROVED derived manifest `3bcde9ee` (run `DRV-EP005-BERRY-SPLIT-1-…`), which is never modified.

**Changes:**
- Removed the 3 visual treatment dependencies from `unique_tbd_asset_dependencies`.
- Removed FOLEY_TOUCH from `unique_tbd_asset_dependencies` and from `audio_tbd_dependencies`.
- Moved the 10 OVERLAY_VFX treatment references out of `unresolved_tbd_references` (97 → 87). Their shot attribution is kept in the treatment section.
- **New `compositing_treatments` section,** one entry per treatment, holding: id, source dependency, classification, human decision, handling, affected shots, source labels, the verbatim per-shot instructions (element, usage, overlay_role), `agent007_eligible: false`, `paid_generation_required: false`, and the full original dependency entry.
- **Per-shot overlay entries for the treatments** (10 entries): `asset_id` changed from `TBD` to the treatment id, and `asset_status` to `COMPOSITING_TREATMENT`. The originals are kept in `original_asset_id` and `original_asset_status`, plus `requirement_class`. The element, usage and role text is verbatim.
- **S028:** added `audio_plan.human_decisions`, noting that FOLEY_TOUCH was dropped. The audio phrases and the visual action are verbatim.
- **Counts:** visual TBD deps 6 → 3 (Mikko, Lumi and environment, which resolve to C1); audio TBD deps 4 → 3; unique TBD deps 10 → 6; audio TBD references 29 → 28; `tbd_asset_reference_count` 97 → 87.
- **Lineage:** `manifest_version` gains `+tbd-cleanup-1`. `derivation` records the source manifest and run, the informing run `A006-1791181098027` and readiness `e32ef7eb`, every human decision, the reclassification, the dropped item, the remaining audio, the approval requirement, and `previous_derivation` (the berry-split lineage).
- **Unchanged:** `source_approved_assets`, `asset_inventory`, `unique_new_assets`, `unique_reused_assets`, `episode`, `shot_queue`, `generation_workload`, `audio_workload`, `production_phases`, `paid_generation_summary`, `production_optimization` and `source_fidelity`, so all 11 resolved requirements are preserved.

**Invariants.** The script fails closed if any of these break. All passed:
- The source must be the APPROVED `3bcde9ee`.
- Exactly the 3 named visual dependencies are moved, and exactly one FOLEY_TOUCH is removed from each list.
- The remaining visual TBDs are exactly {Lumi, Mikko, environment}; the remaining audio TBDs are exactly [AMBIENCE, FOLEY_CLOTH, COMPLETION_SFX].
- 10 references are moved and 10 shot entries tagged, with identical (shot, treatment) attribution.
- Each treatment's per-shot instructions cover exactly its affected shots.
- All protected sections listed above are byte-identical.
- Every shot plan, once the approved tags are removed, is identical to the source.
- No dropped or reclassified item remains in any requirement list.

## 3. Write: one plain insert

`POST /rest/v1/episode_production_manifests` with no upsert returned HTTP 201.

| Field | Value |
|---|---|
| id | **`96df250f-7182-4d5f-a556-b0448e518375`** |
| created_at | 2026-10-05T06:47:46.258594Z |
| status | **REVIEW** |
| production_plan_run_id | `DRV-EP005-TBD-CLEANUP-1-A005O-1790400144423` |
| tbd_asset_reference_count | 87 |
| manifest_json sha256 (canonical) | `833bf0aab4f28f64bd5db72c129896811cc80705e1e9becbf6b9db123eb2422e` |

**Readback:** all 21 written fields equal the transform output exactly.

## 4. In-memory Agent-006 proof

- **Harness:** `evidence/ep005/berry_split/agent006_inmemory_sim.js`.
- **Code under test:** unmodified node 03, 05, 07 and 08 code from the export, identical to live `9bf6bbef`.
- **Inputs:** the live registry (11 governed rows). Status is set to APPROVED in memory only. No n8n execution.
- **Output:** `evidence/ep005/tbd_cleanup/sim_tbd_cleanup_derived.json`.

| Requirement | Matches | Resolution | Canonical | Equal to live run A006-1791181098027 |
|---|---|---|---|---|
| Cheek / mouth / nose overlays | 1 each | REUSE_EXISTING | OVERLAY-EP005-BERRY-SMUDGE-CHEEK/MOUTH/NOSE-v01 | yes |
| Mirror / cloth | 1 each | REUSE_EXISTING | PROP-EP005-HAND-MIRROR-v01 / PROP-EP005-CLEANING-CLOTH-v01 | yes |
| Mikko / Lumi / environment | 1 each | REUSE_EXISTING | CHAR-MIKKO-MASTER-v01 / CHAR-LUMI-MASTER-v01 / WORLD-EP005-BATHROOM-MASTER-v01 | yes |
| 3 approved SFX | 1 each | REUSE_EXISTING | SFX-LUMI-CLUE-CHIME / SFX-MIKKO-TRY-WHOOSH / SFX-WIN-SPARKLE-CHORD | yes |
| TBD::AUDIO::AMBIENCE (20 shots), FOLEY_CLOTH (7), COMPLETION_SFX (1) | 0 | NEEDS_HUMAN_REVIEW | none | yes |

**Totals:**
- **14 requirements:** 11 REUSE_EXISTING, identical to the live run on resolution, canonical ID, exact candidates and shots; and 3 unresolved audio.
- No visual treatment requirement, no FOLEY_TOUCH, no CREATE_NEW. Node 08 accepts all 14.
- Removed relative to the live run: the 3 OVERLAY_VFX TBDs and FOLEY_TOUCH.
- The simulation of the **live inserted row** is identical to the pre-write simulation.

**Negative control:** the row in its real REVIEW status is blocked by node 03 (`MANIFEST_NOT_APPROVED_OR_NOT_FOUND`).

**Expected readiness after approval and a later run:** NEEDS_HUMAN_REVIEW, until the 3 audio files are approved and registered. Agent-007 stays ineligible, because no requirement is CREATE_NEW and none of the remaining items is visual.

## 5. Unchanged state (verified after the write)

| Item | Fingerprint / state |
|---|---|
| `3bcde9ee` | APPROVED, row md5 `931d64dfaca0b235ea70ea698cef7eea`; client snapshot identical before and after |
| `670b201b` | APPROVED, row md5 `249adbfe4a9ddbc6c75446994979fe0d` |
| episode_production_manifests | 9 → 10 (APPROVED 3; the new row is REVIEW) |
| asset_registry | `b7b46112661dc0a0d9218e647f747306` (20 rows) |
| storage.objects | `4c7ef85e9c92af4fca27b775e233b7bc` (16) |
| production_readiness_manifests | `89663d3b…` |
| asset_resolution_items | `409c215d…` |
| Migrations | 1 |
| Agent-006 | 9bf6bbef, unpublished |

## 6. F-1 erratum

Appended to `evidence/EP005_AGENT006_DERIVED_MANIFEST_LIVE_RUN_v1.0.md` as an addendum; the original text is unchanged. It says F-1 was repaired under ENG-20260928-020 Part A, and the earlier "open" note was stale. The SFX paths were not modified.

## 7. Rollback

```sql
delete from public.episode_production_manifests where id = '96df250f-7182-4d5f-a556-b0448e518375';
```

Nothing else needs reverting.

## 8. Safety confirmation

- Supabase writes: 1 insert (`episode_production_manifests`, REVIEW). Nothing else was written.
- Registry, storage, `3bcde9ee`, `670b201b`, readiness and resolution rows: unchanged.
- Workflow changes: 0. n8n writes: 0.
- Agent-006 executions: 0. Agent-007 executions: 0.
- Manifest approvals: 0. Readiness approvals: 0.
- Audio sourcing or creation: 0. Generation, provider and paid calls: 0. Migrations: 0.
- C1, Agent-000, S3-B and Anime Clip Farming: untouched.

## 9. Final status

```text
EP005_TBD_CLEANUP_DERIVED_MANIFEST_CREATED_REVIEW
+ THREE_VISUAL_TBDS_RECLASSIFIED_AS_COMPOSITING
+ FOLEY_TOUCH_DROPPED
+ THREE_AUDIO_TBDS_REMAIN
+ EXPECTED_REQUIREMENT_COUNT_14
+ ELEVEN_REUSE_EXISTING_PRESERVED
+ ZERO_AGENT006_RUN + ZERO_AGENT007_RUN + ZERO_GENERATION + ZERO_PAID_CALLS
+ ZERO_REGISTRY_CHANGE + ZERO_STORAGE_CHANGE
+ F1_EVIDENCE_ERRATUM_ADDED
+ SOURCE_MANIFESTS_UNCHANGED
+ EVIDENCE_COMMITTED_TO_GITHUB
```

**Stop condition:** the task is complete. `96df250f` stays in REVIEW until a separate human approval.
