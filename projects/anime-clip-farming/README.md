# V&A Anime Clip Farming — Engine 2

**Lane:** Engineer-2 (Claude), human owner Viva. Governed by the V&A Company Brain.
**Scope of this folder:** Anime Clip Farming / Anime Shorts Lab / Engine 2 only. Nothing here touches the YouTube Kids (Mikko & Lumi) system, and no Kids file may be added here.

## Purpose
Build a human-governed system that turns anime research into **original V&A commentary, analysis and entertainment** shorts — an editorial idea first, with anime footage only as supporting evidence. It is not a raw-reposting channel. The first commercial goal is a 30-video validation batch, not maximum automation.

## Current sprint and state

| | |
|---|---|
| Last completed | **Pre-Sprint 1 Supabase provisioning + migration preflight** (2026-10-07, branch `engine2/clip-farming-sprint-01-preflight`). Sprint 0 (foundation) before it, on `engine2/clip-farming-sprint-00-foundation` |
| Status | **Stopped.** Sprint 1 migration is READY TO APPLY, not applied. The n8n credential waits on a human |
| Database | Dedicated Supabase project `V&A Anime Clip Farming — Engine 2` (ref `mkeldytatorxxszjdngt`, eu-north-1, Free plan), schema `cf` ([ADR-001](architecture/decisions/ADR-001_DEDICATED_SUPABASE_PROJECT.md)). It holds no CF table yet |
| Implemented live | The empty dedicated project and the runtime role `cf_n8n_runtime` (no password, no grants) |
| Design only | Data model, full schema (DESIGN ONLY — NOT APPLIED), identities, state model, gates, CF-001…CF-009 contracts, dependency map, test strategy |
| Other live Engine 2 objects | One experimental, unpublished, never-executed n8n workflow `WStqWRlqax7iocOx` (ANIME-LAB — VIDEO-SMOKE-001). No CF workflow, no CF credential |
| Next | Approve and apply `migrations/0001_cf_sprint01.sql`; a human sets the role password and creates the n8n credential; then Sprint 1 — CF-001 Market & Trend Radar. **Sprint 1 is not authorised.** No sprint is ever automatically authorised by a previous one or by any document in this folder |

## Engine 2 architecture

```text
CF-001 Market & Trend Radar
  → CF-002 Scene Intelligence & Provenance
  → CF-003 Editorial Opportunity Planner   → G1 Human content idea approval
  → CF-004 Script & Commentary Architect   → G2 Human script approval
  → CF-005 Publication Source & Rights Resolver → G3 Human source / rights approval
  → CF-006 Edit & Production Planner
  → CF-007 Production Assembly              → G4 Human final video QC / publish approval
  → CF-008 Publisher & Distribution         (first point where anything can be published)
  → CF-009 Analytics & Learning Engine      ┄┄ soft feedback to CF-001 / CF-003
LATER ONLY: CF-000 Deterministic Orchestrator (Sprint 11, explicit go-ahead)
```

## Governance model
- The Company Brain plans and authorises each bounded sprint; Claude executes only that sprint; Viva returns evidence; the Company Brain reconciles.
- Models may research, rank, interpret, ideate and script. Code owns IDs, status, approvals, dedupe, timestamps, retries, budgets, sequencing and platform IDs.
- **Human gates G1–G4** are persisted, attributable, append-only decisions bound to an exact object ID and content hash. An AI recommendation is never an approval. Downstream agents fail closed on a missing, rejected, revoked or stale approval.
- Kill switches (`PUBLISH_ENABLED`, `PAID_CALLS_ENABLED`, `SCHEDULES_ENABLED`) default OFF. Paid calls also need a per-run authorisation reference.

## Research source ≠ publication source
```text
Research access ≠ Publication permission ≠ Platform monetisation eligibility ≠ Legal determination
```
Scenes carry only research provenance. Publication material exists only in G3-reviewed source packages. No field anywhere means "fair use", "copyright safe" or "legal safe". A scene can be editorially strong with no approved publication source; that is a valid state. The system never downloads episodes, defeats DRM, scrapes or logs into streaming services, or extracts clips.

## Folder map

```text
projects/anime-clip-farming/
  README.md                                   this file
  architecture/
    ENGINE2_INFRASTRUCTURE_BLUEPRINT.md       blueprint, byte-for-byte from project files
    decisions/
      ADR-001_DEDICATED_SUPABASE_PROJECT.md   dedicated project + runtime role (post-Sprint 0)
    data-contracts/
      DATA_MODEL_v0.1.md                      tables, keys, writers, readers, dedupe
      IDENTITY_CONTRACTS_v0.1.md              every UUID identity and its rules
      migrations-draft/
        0001_cf_backbone.DESIGN_ONLY.sql      DESIGN ONLY — NOT APPLIED (full 23-table design)
        0001_cf_backbone.STATIC_TESTS.sql     local-only static tests (33)
      migrations/
        0001_cf_sprint01.sql                  Sprint 1 subset — READY TO APPLY, NOT APPLIED
        0001_cf_sprint01.ROLLBACK.sql         removes exactly what 0001 creates
        0001_cf_sprint01.VERIFY.sql           read-only post-apply check
        0001_cf_sprint01.TESTS.sql            local-only tests (33)
    workflow-contracts/
      AGENT_CONTRACTS_CF001_CF009_v0.1.md     per-agent contracts
      DEPENDENCY_MAP_v0.1.md                  chain, gates, paid and publish entry points
    approval-contracts/
      HUMAN_GOVERNANCE_GATES_v0.1.md          G1–G4
    state-machine/
      STATE_MODEL_v0.1.md                     vocabulary + per-object transitions
  sprints/
    SPRINT_00_FOUNDATION/                     discovery, gap analysis, test strategy, final report
    SPRINT_01_CF001/ … SPRINT_11_CF000/       placeholders — NOT AUTHORISED
  evidence/
    SPRINT_00_BASELINE_EVIDENCE.md            read-only baseline
    SPRINT_00_STATIC_TEST_OUTPUT.txt          local static test run
    PRE_SPRINT_01_SUPABASE_PROVISIONING_EVIDENCE.md   project, region, isolation, role, credential stop
    PRE_SPRINT_01_MIGRATION_PREFLIGHT.md      comparison, target guard, tests, rollback, READY TO APPLY
    PRE_SPRINT_01_TEST_OUTPUT.txt             local test run (PostgreSQL 16.15 and 17.10)
    pre-sprint-01-tools/                      scripts that built and checked the migration
  changelog/
    ENGINE2_CHANGELOG.md
```

## Naming
Agents and n8n workflows use `CF-000 … CF-009` (e.g. `CF-001 — Market & Trend Radar`). Never `AGENT-00x`, which belongs to the YouTube Kids system. Database objects live in schema `cf` inside the dedicated Supabase project `mkeldytatorxxszjdngt`; the n8n login role is `cf_n8n_runtime`. Git branches: `engine2/clip-farming-sprint-NN-<topic>`.
