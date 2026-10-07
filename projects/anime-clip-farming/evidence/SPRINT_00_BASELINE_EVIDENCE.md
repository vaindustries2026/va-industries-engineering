# Sprint 0 — Baseline Evidence (read-only)

**Sprint:** BATCH A / SPRINT 0 — Engine 2 Foundation
**Operator:** Claude Engineer-2 (human owner: Viva)
**Captured:** 2026-10-07 (UTC), before any Git change
**Mode:** read-only. Every call listed here was a list / search / get call or a catalog `SELECT`.

This file is raw evidence. Interpretation lives in `sprints/SPRINT_00_FOUNDATION/SPRINT_00_DISCOVERY_REPORT.md`.

---

## 1. GitHub

| Item | Value |
|---|---|
| Repository | `vaindustries2026/va-industries-engineering` (the only repository this account can reach) |
| Default branch | `main` |
| Starting HEAD | `14f66e10664d6f295ef74402998e22949714098b` ("Record EP005 Suno candidate task stop: commercial rights not verified") |
| Remote branches | `main` @14f66e1, `claude/busy-turing-b2egbj` @14f66e1, `claude/funny-cray-e21af5` @e7ebdf8, `claude/test-supabase-storage-connectivity-jvvmsn` @57ab83c |
| Branch policy found | None written. `CLAUDE.md` has no branch rule. Existing non-main branches are harness-generated `claude/*` names, all on YouTube Kids C1/EP005 work. |
| Sprint 0 branch | `engine2/clip-farming-sprint-00-foundation` (new; did not exist on the remote) |

Top-level tree at HEAD: `CLAUDE.md`, `README.md`, `SOURCE_PACK_MANIFEST.json`, `canon/c1/` (Mikko & Lumi canon PNGs), `company-brain/` (3 files), `evidence/` (YouTube Kids evidence), `workflows/` (2 Agent-006/007 drafts).

Search for Clip Farming content (`grep -ril anime|clip farm|engine 2|engine2`):

- No `projects/` directory, no Clip Farming / Anime / Engine 2 path, no CF-* file anywhere.
- Mentions only: `company-brain/VA_01_*` lines 12, 441 and `company-brain/VA_02_*` lines 88, 216, 760 (anime named as a future reuse target); four EP005 evidence files say "Anime Clip Farming: untouched".
- The two other `claude/*` branches contain only older YouTube Kids C1 commits (diff vs main is deletions of later EP005 files). No anime content.

## 2. n8n

| Item | Value |
|---|---|
| Project | `VA Industries <vaindustries26@gmail.com>` — id `eMjDEqobimuAbLo7`, type personal (only project visible) |
| Workflows visible | 22 |
| Folders | 0 |
| n8n data tables | 0 |

### Engine 2 / Anime workflows (complete list)

| Workflow ID | Name | Active / published | activeVersionId | Current versionId | Executions on record |
|---|---|---|---|---|---|
| `WStqWRlqax7iocOx` | ANIME-LAB — VIDEO-SMOKE-001 — Scene Intelligence | `active: false` (unpublished draft) | `null` | `9ce21a4f-992c-41c8-bbcd-ff29f5d43884` | **0** |

Details of `WStqWRlqax7iocOx` (read via `get_workflow_details`, `get_workflow_history`, `search_workflow_executions`):

- Created 2026-09-29T05:04:55Z, updated 2026-09-29T11:49:51Z, `triggerCount: 0`, not archived.
- Description: "E2-VIDEO-SMOKE-001A · Engineer-2 Anime Lab isolated smoke workflow. UNPUBLISHED. Node 04 is a live paid Gemini call: do not execute until the Company Brain authorises the live test. No Supabase, no Slack."
- Version history shows one saved version: `9ce21a4f…` named "E2-VIDEO-SMOKE-001B-RESET: restore 01 placeholder source".
- 10 nodes: `Manual Trigger` → `01 - Set Test Input` (source_url = `https://www.youtube.com/watch?v=PLACEHOLDER`, source_authorisation = `AUTHORIZED_TEST`) → `02 - Validate Test Input` (fail-closed; rejects placeholder URL) → `03 - Build Video Analysis Request` (model `gemini-3.8-flash`, prompt `anime-lab-scene-intel-v0.1`, ≤5 candidate moments, explicit "do not assess copyright / fair use") → `04 - Gemini Video Analysis` (HTTP POST to Gemini Interactions API, credential `Google API - x-goog-api-key` id `MpX1PC9vapbWYQji`; **paid**) → `05 - Parse Analysis Result` → `06 - Validate Structured Result` → `07 - Build Director Brief`. Isolated test branch: `TEST - Manual Trigger` → `TEST - Mock Gemini Result` → `05`.
- No Supabase node, no Slack node, no persistence, no stable IDs.

### Other workflows (not Engine 2; listed only to prove scope; not opened)

`00 - V&A Slack Command Router` (kXUxCTqkuUSM7Gsy), AGENT-001 … AGENT-007 and their TEST/HARNESS/ARCHIVE copies (21 workflows). All belong to the YouTube Kids system and are out of scope. Only their names and IDs from the list call were read.

No workflow named `CF-*` exists.

### Credentials visible (metadata only; no secret read)

| Credential ID | Name | Type | Engine 2 relevance |
|---|---|---|---|
| `MpX1PC9vapbWYQji` | Google API - x-goog-api-key | httpHeaderAuth | Used by the ANIME-LAB smoke workflow node 04. Ownership/billing scope not recorded. |
| `bJgwIJkzHaL3SjbT` | YouTube account | youTubeOAuth2Api | Which channel it is bound to is unknown. Not Engine 2-specific. |
| `6RmhHTYLsvhKsqqd` | OpenAI account | openAiApi | Shared; used by YouTube Kids agents. |
| `kmO9E7oT9FykYcL2` | n8n free OpenAI API credits | openAiApi (managed) | Shared. |
| `bj5SMSknZ2GG7ICw` | Supabase account | supabaseApi | Used by YouTube Kids agents. |
| `Ax7S0H6CThziGyl6` | V&A - Supabase Service Role - AGENT007 | supabaseApi | YouTube Kids Agent-007. Off-limits. |
| `kGDMigT1YHnSmCPI` | Runway API - AGENT-007 | httpHeaderAuth | YouTube Kids Agent-007. Off-limits. |
| `1hcUSW3XMdIolZpE`, `3ll3yh4MrL1WCl4D`, `icXvbgwOIjohxT2w` | Slack account / 2 / 3 | Slack | Router / Kids. Off-limits. |

No credential is dedicated to Clip Farming.

## 3. Supabase

| Item | Value |
|---|---|
| Projects visible | 1 — `VA-Company-Brain*`, ref `ziluiwrwwbayhcskeere`, region ap-southeast-2, Postgres 17.6, ACTIVE_HEALTHY |
| Non-system schemas | `public` only (plus Supabase-managed `auth`, `storage`, `realtime`, `vault`, `extensions`, `graphql`, `graphql_public`, `supabase_migrations`) |
| `public` tables (14) | videos, video_snapshots, content_genomes, content_syntheses, episode_backlog, episode_scripts, production_plans, shot_production_plans, episode_production_manifests, asset_registry, asset_resolution_items, production_readiness_manifests, asset_creation_batches, asset_creation_jobs |
| `public` views (4) | agent002_candidates, market_scout_rankings, video_momentum, video_momentum_daily |
| `public` functions (3) | a007_checkpoint_submission, a007_claim_submission, a007_reserve_generation |
| `public` triggers | none |
| `public` enum types | none |
| Migrations recorded | 1 — `20260925043429 s3a_episode_scripts_backlog_identity` (YouTube Kids) |
| Edge functions | 0 |
| Storage buckets | 1 (16 objects) — not opened |

**Clip Farming objects found: none.** No table, view, function, trigger, type or schema named or shaped for anime / clip farming / CF-*. None of the 11 A1-FOUNDATION tables (angle_taxonomy, reviewers, rightsholders, franchises, franchise_rights_map, short_backlog, scripts, source_usage_items, source_usage_reviews, gate_decisions, agent_runs) exists.

Queries run (all read-only):

1. `list_projects`
2. `list_tables(schemas=[all], verbose=false)`
3. Catalog `SELECT` over `pg_namespace`, `pg_class`, `pg_proc`, `information_schema.triggers`, `pg_type` (first attempt failed on a type-cast error and returned nothing; corrected and re-run)
4. `list_migrations`
5. `list_edge_functions`

## 4. Slack

`slack_search_channels` (public + private) for `anime` and for `clip`: **0 channels** each. No Clip Farming Slack surface exists. No message read, none sent.

## 5. Google Cloud / BigQuery

- `list_dataset_ids(projectId="va-industries")` → `Not found: Project va-industries` (guessed ID; no project ID is recorded anywhere in the repo or project files).
- `gcloud projects list` and `bq ls` from the session container → unauthenticated.
- Result: **Google Cloud project identity not verified.** Not needed for Sprint 0 design work; recorded as a blocker for any future sprint that needs GCP.

## 6. Project files used as design inputs

| File (under /mnt/project-files/knowledge/) | Header version / status |
|---|---|
| VA_ANIME_CLIP_FARMING_ENGINE2_INFRASTRUCTURE_BLUEPRINT_v1.4.md | header says **v1.0**, 5 Oct 2026, "PROPOSED BUILD BLUEPRINT — HUMAN APPROVAL REQUIRED BEFORE IMPLEMENTATION"; sha256 `f9f1013a3a54ce8da8a63cf143ad3784dd65f843196a5f26d721f3f40e930992` |
| VA_ANIME_CLIP_FARMING_FORMAT_AND_SOURCE_STRATEGY_v1.3.md | header v1.0, "Strategic Working Source of Truth — Human Approval Required" |
| VA_ANIME_CLIP_FARMING_EDGE_STRATEGY_v1.2.md | header v1.0 |
| VA_ANIME_CLIP_FARMING_STRATEGY_v1.1.md | header v1.1 |
| VA_ANIME_CLIP_FARMING_BUSINESS_PROPOSAL_v1.0.md | header v1.0 |

The blueprint was committed byte-for-byte as `architecture/ENGINE2_INFRASTRUCTURE_BLUEPRINT.md` (same sha256).

Prior Engine-2 history comes from imported project memory (not a live system): A0 design `VA_ANIME_SHORTS_LAB_SYSTEM_DESIGN_v0.1.md` (accepted), A1-PREFLIGHT (read-only), A1-FOUNDATION 11-table schema (not authorised), E2-ANIME-SMOKE-001 brief. The A0 document itself was **not found** in the repo or in the project files.

## 7. Write / spend counters for the discovery phase

| Counter | Value |
|---|---|
| n8n workflows modified / published / executed | 0 / 0 / 0 |
| Supabase INSERT / UPDATE / DELETE / DDL / RPC | 0 |
| Supabase migrations applied | 0 |
| Slack messages sent | 0 |
| Provider calls (LLM / video / audio / image) | 0 |
| Paid calls | 0 |
| External uploads / social posts / schedules | 0 |

## 8. Closing re-check (after the package was written, before commit)

Read-only, 2026-10-07:

- n8n `search_workflows(query="CF-")` → 0 workflows. `search_workflow_executions(WStqWRlqax7iocOx)` → 0 executions.
- Supabase `list_migrations` → still only `20260925043429 s3a_episode_scripts_backlog_identity`.
- Supabase catalog `SELECT`: schema `cf` exists = 0; `public` tables = 14 (unchanged); roles named `cf_*` = 0.

The draft SQL was only ever loaded into a throwaway local PostgreSQL inside the engineering container, which was then deleted.
