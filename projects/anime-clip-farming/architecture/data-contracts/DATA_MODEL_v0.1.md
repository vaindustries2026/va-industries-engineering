# Engine 2 — Data Model v0.1

**Status:** PROPOSED — DESIGN ONLY — NOT APPLIED. Placement revised after Sprint 0 by ADR-001 (dedicated Supabase project); the tables, columns, keys and rules below are unchanged.
**Draft DDL:** `migrations-draft/0001_cf_backbone.DESIGN_ONLY.sql` (validated only in throwaway local PostgreSQL 16.15 and 17.10; 33/33 static tests in `migrations-draft/0001_cf_backbone.STATIC_TESTS.sql` pass).
**Sprint 1 subset:** `migrations/0001_cf_sprint01.sql` (applied 2026-10-07; see `../../evidence/PRE_SPRINT_01_MIGRATION_PREFLIGHT.md` and `../../evidence/PRE_CF001_DATABASE_ACTIVATION_EVIDENCE.md`), plus `migrations/0002_cf_runtime_human_admin_guard.sql` (applied; [ADR-002](../decisions/ADR-002_RUNTIME_ROLE_CANNOT_MAKE_HUMAN_ADMIN_TRANSITIONS.md)). The guard function in the draft design file still shows the 0001 body; 0002 is the live version.
**Identities:** `IDENTITY_CONTRACTS_v0.1.md`. **States:** `../state-machine/STATE_MODEL_v0.1.md`. **Gates:** `../approval-contracts/HUMAN_GOVERNANCE_GATES_v0.1.md`.

---

## 1. Placement and isolation

| Decision | Proposal | Why | Needs human decision? |
|---|---|---|---|
| ~~D-DB-1 Where~~ (Sprint 0 proposal, **superseded**) | ~~Same Supabase project as today (`VA-Company-Brain*`, ref `ziluiwrwwbayhcskeere`), in a new dedicated Postgres schema `cf`.~~ | ~~The project is the only one visible; a second project may add cost. A separate schema gives hard name isolation from the YouTube Kids tables in `public` without touching them.~~ | Decided after Sprint 0: see D-DB-1R. |
| **D-DB-1R Where** (Company Brain, 2026-10-07, [ADR-001](../decisions/ADR-001_DEDICATED_SUPABASE_PROJECT.md)) | **Dedicated Supabase project** `V&A Anime Clip Farming — Engine 2` (ref `mkeldytatorxxszjdngt`, eu-north-1), with all objects still in schema `cf`. | Separate blast radius from the YouTube Kids project. Keeping `cf` leaves the data model unchanged and keeps CF tables out of the Data API's default `public` schema. Cost $0 (second Free-plan slot). | Decided. |
| D-DB-2 Access path | n8n reaches `cf` through a **Postgres-node credential for the dedicated login role `cf_n8n_runtime`** (LOGIN NOINHERIT NOBYPASSRLS NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION), not through the Supabase REST API. Revised by ADR-001: grants go to `cf_n8n_runtime` directly; the Sprint 0 group role `cf_agent` is dropped because a NOINHERIT role would not receive its grants. | `cf` is never exposed over PostgREST. A dedicated role lets grants (not prompts) stop agents writing approvals. | Role created 2026-10-07 without a password. **A human sets the password and creates the n8n credential.** |
| D-DB-3 Credentials | Never reuse `V&A - Supabase Service Role - AGENT007`, `Supabase account`, or any service-role key for CF workflows. | Service role bypasses all grants and RLS, which would defeat the gate design; those credentials belong to the Kids lane. | No (rule). |
| D-DB-4 Naming | Tables inside `cf` use the brief's names without a prefix (`cf.anime_titles`…). | Schema already namespaces them. If D-DB-1 is rejected in favour of `public`, prefix every table `cf_`. | Follows D-DB-1. |

Nothing in `cf` references, reads, or alters any `public` object, and the dedicated project holds no YouTube Kids object at all.

## 2. Table list: brief vs proposal

| Brief candidate | Proposal | Reason |
|---|---|---|
| anime_titles | **keep** | |
| anime_source_episodes | **keep** | |
| anime_scene_intelligence | **keep**, minus publication-status column | Publication status is derived (`cf.v_scene_publication_status`), never stored on the scene. Structural separation of research vs publication. |
| editorial_opportunities | **keep** (PK `content_candidate_id`) | |
| content_scripts | **keep** | |
| publication_source_packages | **keep** | |
| publication_source_decisions | **replace with `gate_decisions`** | One append-only decision log for G1–G4 means one downstream validation method and one guard trigger. A G3-only table would make G3 a special case. |
| production_manifests | **keep** | |
| production_jobs | **keep** | |
| content_assets | **keep** | |
| published_content | **keep** (one row per content object) | |
| performance_snapshots | **keep** (append-only) | |
| content_learning_log | **keep** (append-only) | |
| — | **add `research_candidates`** | `research_candidate_id` is in the identity list and is CF-001's output, but no table held it. |
| — | **add `anime_franchises`** | Analytics and wrong-franchise contamination tests need a franchise identity; the strategy docs treat franchise as a primary dimension. |
| — | **add `editorial_opportunity_scenes`** | An idea can use more than one scene. |
| — | **add `publication_source_items`** | A package is several pieces of material; each needs its own provenance and category. |
| — | **add `renders`** | `render_id` is the G4 subject and the CF-008 input, but had no table. |
| — | **add `platform_posts`** | Blueprint rule: platform posts are distributions of one content object. Per-platform columns (`youtube_post_id`, `tiktok_post_id`…) would not hold status, failure, retry or schedule per platform. |
| — | **add `gate_decisions`** | Persisted, attributable human approvals (replaces publication_source_decisions). |
| — | **add `reviewers`** | Approvals must be attributable to a named human allowed to decide that gate. Carried over from A1-FOUNDATION. |
| — | **add `agent_runs`** | Run identity, replay key, provider/paid call counters, n8n execution provenance. Carried over from A1-FOUNDATION. |
| — | **add `system_flags`** | Global kill switches (`PUBLISH_ENABLED`, `PAID_CALLS_ENABLED`, `SCHEDULES_ENABLED`), all default OFF. |
| — | **add `allowed_transitions`** | The state machine stored as data so a trigger enforces it. |

Result: 23 tables, 3 views, 1 governance function, 5 guard functions. Deferred from A1-FOUNDATION: `angle_taxonomy`, `rightsholders`, `franchise_rights_map` (see gap analysis).

## 3. Cross-cutting column contract

Every lifecycle table has: UUID PK (`gen_random_uuid()`), `status cf.lifecycle_status` restricted by a per-table CHECK, `agent_run_id` (FK, provenance), `agent_version` (and `prompt_version` where a model is used), `created_at`, `updated_at` (trigger-maintained). Gated objects also have `content_sha256` (the exact bytes a human approves) and `revision_number` / `revision_of_*`.

Enforced by triggers on every lifecycle table:
- `*_guard_status` — only edges in `cf.allowed_transitions`; gated edges need an effective `gate_decisions` row for this exact ID and `content_sha256`.
- `*_freeze` — once status leaves `IDEA`/`DRAFT`, content columns cannot change (new revision instead).
- `*_no_delete` — rows are retired, never deleted.

Append-only tables (UPDATE and DELETE raise): `gate_decisions`, `performance_snapshots`, `content_learning_log`, `publication_source_items`, `editorial_opportunity_scenes`.

## 4. Tables

Legend: **W** = expected writer, **R** = expected readers, **Gate** = human-approval dependency, **Imm** = immutable fields.

### 4.1 `cf.reviewers`
- **Purpose:** named humans allowed to decide G1–G4.
- **PK:** `reviewer_id`. **Required:** `display_name`, `allowed_gates`, `active`. **Optional:** `retired_at`.
- **Status:** `active` boolean (not lifecycle). **W:** humans via governed setup. **R:** `record_gate_decision`, governance surface.
- **Dedupe:** none needed (few rows). **Imm:** `reviewer_id`.

### 4.2 `cf.agent_runs`
- **Purpose:** one invocation of one CF agent version; replay key; spend counters.
- **PK:** `agent_run_id`. **Required:** `agent_code` (`^CF-00[0-9]$`), `agent_version`, `idempotency_key`, `input_ids`, `input_state_hash`, `run_state`. **Optional:** prompt/model, n8n workflow/version/execution IDs, `output_summary`, error fields, timestamps.
- **State:** `run_state` (QUEUED/RUNNING/SUCCEEDED/FAILED/CANCELLED). **Provenance:** n8n IDs, prompt version, model requested.
- **Dedupe:** `idempotency_key` UNIQUE. **Guards:** `paid_call_count > 0` requires `paid_authorisation_ref`; paid ≤ provider calls.
- **W:** first deterministic node of each CF workflow. **R:** all agents, CF-000 later, audits.
- **Indexes to consider (beyond the DDL):** `(agent_code, created_at)`.

### 4.3 `cf.system_flags`
- **Purpose:** kill switches. **PK:** `flag_key` ∈ {PUBLISH_ENABLED, PAID_CALLS_ENABLED, SCHEDULES_ENABLED}. Seeded OFF.
- **W:** reviewers only (agent role has no write grant). **R:** CF-007, CF-008, CF-000.

### 4.4 `cf.anime_franchises`
- **Purpose:** franchise identity for joins and contamination checks.
- **PK:** `franchise_id`. **Required:** `normalised_key` (UNIQUE, lowercase), `display_name`. **Optional:** `anilist_franchise_ref` (UNIQUE).
- **Status:** DRAFT → READY / BLOCKED → RETIRED. **W:** CF-001 resolver. **R:** all. **Gate:** none (BLOCKED → READY is a human admin action).
- **Imm:** `normalised_key` once READY.

### 4.5 `cf.anime_titles`
- **Purpose:** one anime work.
- **PK:** `anime_title_id`. **FK:** `franchise_id`. **Required:** `normalised_title_key`, `display_title`, `media_type`. **Optional:** `alt_titles`, `anilist_id` (UNIQUE), `mal_id` (UNIQUE), `start_year`; generated `era_decade`.
- **Status:** DRAFT → READY / BLOCKED → RETIRED. **Dedupe:** external IDs; fallback `(franchise_id, normalised_title_key, start_year)` UNIQUE NULLS NOT DISTINCT.
- **W:** CF-001 resolver (CF-002 via the same resolver). **R:** all downstream, CF-009.

### 4.6 `cf.anime_source_episodes`
- **Purpose:** one episode/OVA/film segment of a title (the work, not a file).
- **PK:** `source_episode_id`. **FK:** `anime_title_id`. **Required:** `season_number`, `episode_number`, `episode_variant`. **Optional:** display title, duration.
- **Dedupe:** `(anime_title_id, season_number, episode_number, episode_variant)` UNIQUE. **W:** CF-002 resolver. **R:** scenes, source items.

### 4.7 `cf.research_candidates` (CF-001 output)
- **Purpose:** "worth investigating" record.
- **PK:** `research_candidate_id`. **FK:** `anime_title_id`, `franchise_id`, `agent_run_id`.
- **Required:** `topic_key`, `topic_display`, `content_lane`, `trend_state`, `signal_evidence` (non-empty array of `{source, url, retrieved_at, metric}`), `observation_window` (ISO week), `dedupe_key`. **Optional:** four 0–1 signals, `rejection_reason`.
- **Status:** IDEA → READY / REJECTED; READY → RETIRED. **Provenance:** `signal_evidence`, `agent_run_id`, `agent_version`, `prompt_version`.
- **Dedupe:** `dedupe_key = sha256(anime_title_id|topic_key|content_lane|observation_window)` UNIQUE.
- **Imm:** everything except status/`rejection_reason` once READY. **W:** CF-001. **R:** CF-002, CF-003, CF-009. **Gate:** none.
- **Indexes to consider (beyond the DDL):** `(status, observation_window)`, `(anime_title_id)`.

### 4.8 `cf.anime_scene_intelligence` (CF-002 output)
- **Purpose:** the compounding scene library.
- **PK:** `scene_id`. **FK:** `source_episode_id`, `anime_title_id`, optional `research_candidate_id`, `possible_duplicate_of_scene_id`, `supersedes_scene_id`, `agent_run_id`.
- **Required:** `start_ms` < `end_ms`, `scene_summary`, `why_scene_matters`, `spoiler_level`, `editorial_strength`, **research provenance** (`research_source_platform`, `research_source_reference`, `research_access_basis`), `dedupe_key`. **Optional:** characters, function, angles, context, visual/nostalgia signals, `model_confidence`, `research_access_notes`, `timestamps_human_verified`.
- **Not present by design:** any publication-status, rights, fair-use or permission column.
- **Status:** DRAFT → READY / BLOCKED / REJECTED; READY → RETIRED.
- **Dedupe:** `sha256(source_episode_id|floor(start_s)|ceil(end_s))` UNIQUE; ≥80 % overlap flagged, never merged.
- **Imm:** all content once READY (`timestamps_human_verified` may flip). **W:** CF-002. **R:** CF-003, CF-004, CF-005, CF-009. **Gate:** none.
- **Indexes to consider (beyond the DDL):** `(anime_title_id, status)`, `(source_episode_id, start_ms)`.

### 4.9 `cf.editorial_opportunities` (CF-003 output; G1 subject)
- **PK:** `content_candidate_id`. **FK:** `primary_scene_id` (nullable for scene-less formats), `anime_title_id`, `research_candidate_id`, `revision_of_content_candidate_id`, `agent_run_id`.
- **Required:** `editorial_angle_key`, `working_hook`, `content_lane`, `format_class`, `estimated_duration_seconds`, `why_viewer_cares`, `hypothesis`, `primary_metric`, `content_sha256`, `dedupe_key`, `output_ordinal`. **Optional:** territory, audience, why_now, difficulty, `model_rank`, `recommend_for_review`.
- **Status:** IDEA → REVIEW → APPROVED/REJECTED (G1); IDEA → REJECTED/BLOCKED; APPROVED → RETIRED (G1 REVOKE).
- **Dedupe:** live `dedupe_key` partial UNIQUE (excludes REJECTED/RETIRED); `(agent_run_id, output_ordinal)` UNIQUE.
- **Imm:** all content once REVIEW. **W:** CF-003 (status to APPROVED only via `record_gate_decision`). **R:** G1 surface, CF-004, CF-009. **Gate:** **G1**.
- `recommend_for_review` and `model_rank` are advice. They never move status.

### 4.10 `cf.editorial_opportunity_scenes`
- Join table `(content_candidate_id, scene_id, scene_role)`. Append-only. **W:** CF-003.

### 4.11 `cf.content_scripts` (CF-004 output; G2 subject)
- **PK:** `script_id`. **FK:** `content_candidate_id` (must be G1-APPROVED when written; checked by CF-004 and re-checked by G2 surface), `revision_of_script_id`, `agent_run_id`.
- **Required:** `format_class`, `target_duration_seconds`, `hook`, `thesis`, `narration_text`, `content_sha256`. **Optional:** context, evidence points, interpretation, payoff, CTA, caption plan, claims to verify, spoiler handling, visual-evidence requirements, `narration_independence_selfcheck` (advisory).
- **Status:** DRAFT → REVIEW → APPROVED/REJECTED (G2); DRAFT → BLOCKED/RETIRED; APPROVED → RETIRED (G2 REVOKE).
- **Dedupe:** `(content_candidate_id, revision_number)` UNIQUE; one APPROVED per candidate (partial UNIQUE).
- **W:** CF-004. **R:** G2 surface, CF-005, CF-006, CF-009. **Gate:** **G2**.

### 4.12 `cf.publication_source_packages` (CF-005 output; G3 subject)
- **PK:** `source_package_id`. **FK:** `script_id`, `revision_of_source_package_id`, `agent_run_id`.
- **Required:** `package_summary`, `content_sha256`. **Optional:** required original assets, `rights_risk_notes` (notes, never a determination), source-minimisation notes, commentary ratio estimate, `blocked_reason` (required when BLOCKED: `NO_ACCEPTABLE_SOURCE` / `HUMAN_REVIEW_REQUIRED`).
- **Status:** DRAFT → REVIEW → APPROVED/REJECTED (G3); DRAFT → BLOCKED → RETIRED; APPROVED → RETIRED (G3 REVOKE).
- **Dedupe:** `(script_id, revision_number)` UNIQUE; one APPROVED per script.
- **W:** CF-005. **R:** G3 surface, CF-006, CF-007, G4. **Gate:** **G3**.

### 4.13 `cf.publication_source_items`
- **PK:** `source_item_id`. **FK:** `source_package_id`, optional `source_episode_id`, `scene_id`.
- **Required:** `item_ordinal`, `source_category` (OFFICIAL_PROMO, OFFICIAL_TRAILER, PLATFORM_PERMITTED_SOURCE, LICENSED_SOURCE, HUMAN_REVIEWED_SOURCE, ORIGINAL_GRAPHICS, ORIGINAL_MOTION_GRAPHICS, ORIGINAL_DIAGRAM, ORIGINAL_STILL), `origin_reference`. **Optional:** claimed owner, segment span, proposed seconds, provenance and risk notes.
- Append-only. **W:** CF-005. **R:** G3 surface, CF-006, CF-007.

### 4.14 `cf.gate_decisions`
- **Purpose:** the only record of human approval. Append-only.
- **PK:** `gate_decision_id`. **FK:** `reviewer_id`, `supersedes_gate_decision_id`.
- **Required:** `gate`, `object_type` (CHECK-mapped to gate), `object_id`, `object_content_sha256`, `decision` (APPROVE/REJECT/REVOKE), `idempotency_key` (UNIQUE), `surface`, `decided_at`. **Optional:** `notes`, `approved_platforms` (required for G4 APPROVE, forbidden elsewhere).
- **W:** `cf.record_gate_decision()` only (SECURITY DEFINER; `cf_n8n_runtime` has no grant). **R:** every downstream validator, guard trigger.
- **Indexes (in the DDL):** `(object_type, object_id)`; `supersedes_gate_decision_id` UNIQUE.

### 4.15 `cf.production_manifests` (CF-006 output)
- **PK:** `production_manifest_id`. **FK:** `script_id` (G2-APPROVED), `source_package_id` (G3-APPROVED, same script), `agent_run_id`.
- **Required:** `manifest_schema_version`, `planner_version`, `input_hash` (UNIQUE), segment/audio/caption plans, asset requirements, target runtime, aspect ratio, render spec, `content_sha256`.
- **Status:** DRAFT → READY / BLOCKED / REJECTED; READY → RETIRED. Deterministic, no human gate (blueprint). **W:** CF-006. **R:** CF-007, G4.
- **Dedupe:** `input_hash` = sha256(script_id|source_package_id|schema version|planner version).

### 4.16 `cf.production_jobs` (CF-007)
- **PK:** `production_job_id`. **FK:** `production_manifest_id`, `agent_run_id`.
- **Required:** `job_type`, `segment_ref`, `attempt_group`, `idempotency_key` (UNIQUE), `is_paid`, `run_state`, `attempt_count` ≤ `max_attempts` (default 1). **Optional:** provider, `paid_authorisation_ref` (required when `is_paid`), last error.
- **State:** `run_state` (not lifecycle). **W:** CF-007. **R:** CF-007, CF-000 later.

### 4.17 `cf.content_assets`
- **PK:** `asset_id`. **FK:** optional `production_job_id`, `source_item_id` (required for `THIRD_PARTY_SOURCE_SEGMENT`), `agent_run_id`.
- **Required:** `asset_kind`, `storage_bucket`, `storage_path` (pair UNIQUE), `sha256` (UNIQUE), `bytes`, `mime_type`. **Optional:** duration, dimensions, provider provenance.
- **Status:** DRAFT → READY / REJECTED; READY → RETIRED. **Imm:** bytes never change for an asset_id.
- **W:** CF-007 / asset intake. **R:** renders, CF-008.
- Storage: a dedicated bucket (proposed `cf-assets`) is a future decision; Sprint 0 creates none.

### 4.18 `cf.renders` (CF-007 output; G4 subject)
- **PK:** `render_id`. **FK:** `production_manifest_id`, `master_asset_id` (UNIQUE), `agent_run_id`.
- **Required:** `render_revision`, `master_format` (default `MASTER_VERTICAL_9x16`), duration, width, height, `content_sha256` (= master file sha256). **Optional:** provider provenance.
- **Status:** DRAFT → REVIEW → APPROVED/REJECTED (G4); DRAFT → REJECTED; APPROVED → RETIRED (G4 REVOKE).
- **W:** CF-007. **R:** G4 surface, CF-008, CF-009. **Gate:** **G4**.

### 4.19 `cf.published_content` (CF-008)
- **PK:** `published_content_id`. **FK:** `render_id` (UNIQUE), `content_candidate_id`, `script_id` (lineage, must match the render's chain), `agent_run_id`.
- **Status:** READY → PUBLISHED → RETIRED; READY → RETIRED. **W:** CF-008 only after `cf.v_publish_eligibility` returns the render. **R:** CF-009.

### 4.20 `cf.platform_posts` (CF-008)
- **PK:** `platform_post_id`. **FK:** `published_content_id`, `upload_asset_id`, `agent_run_id`.
- **Required:** `platform` (must be in the G4 decision's `approved_platforms`), title, `publish_idempotency_key` (UNIQUE). **Optional:** description, hashtags, schedule, `external_post_id` + `external_url` + `published_at` (all required at PUBLISHED), failure code, attempts.
- **Status:** READY → PUBLISHED / BLOCKED; BLOCKED → READY / RETIRED; PUBLISHED → RETIRED.
- **Dedupe:** one live post per (content, platform); `(platform, external_post_id)` UNIQUE.
- **W:** CF-008. **R:** CF-009.

### 4.21 `cf.performance_snapshots` (CF-009)
- **PK:** `performance_snapshot_id`. **FK:** `platform_post_id`, `agent_run_id`.
- **Required:** `captured_at`, `captured_bucket_utc` (CHECK = hour bucket), `metric_window`, `metrics` (raw), `source_api`. **Optional:** typed common metrics.
- Append-only. **Dedupe:** `(platform_post_id, metric_window, captured_bucket_utc)` UNIQUE. **W:** CF-009. **R:** CF-009, dashboards.

### 4.22 `cf.content_learning_log` (CF-009)
- **PK:** `learning_log_id`. **FK:** optional `published_content_id`, `supersedes_learning_log_id`, `agent_run_id`.
- **Required:** `hypothesis`, `result`, `output_ordinal`. **Optional:** baseline comparison, worked/failed, confidence, next test, recommended backlog effect, evidence snapshot IDs.
- Append-only. **Dedupe:** `(agent_run_id, output_ordinal)` UNIQUE. **W:** CF-009. **R:** CF-001, CF-003 (as soft input), humans.

### 4.23 `cf.allowed_transitions`
- State machine as rows `(object_type, from_status, to_status, required_gate, required_decision, mode)`. Changed only by migration.

## 5. Views

| View | Purpose |
|---|---|
| `cf.v_effective_gate_decisions` | decisions not superseded by a later one |
| `cf.v_scene_publication_status` | derived `UNKNOWN` / `IN_G3_APPROVED_PACKAGE` per scene — never stored on the scene, and scoped to the package's one script |
| `cf.v_publish_eligibility` | renders CF-008 may publish: G4-approved (hash-bound), manifest READY, package G3-approved, script G2-approved and matching; exposes `publish_enabled` |

## 6. Append-only vs mutable

| Append-only (history) | Mutable state (guarded) |
|---|---|
| gate_decisions, performance_snapshots, content_learning_log, publication_source_items, editorial_opportunity_scenes | status of lifecycle rows (only along allowed edges); run_state of agent_runs and production_jobs; platform_posts delivery fields; reference-data display labels |

Content of gated objects is frozen after DRAFT/IDEA; edits are new revisions with new IDs.
