-- =============================================================================
-- DESIGN ONLY — NOT APPLIED
-- =============================================================================
-- V&A Anime Clip Farming / Engine 2 — proposed Supabase backbone v0.1
-- Sprint 0 (Foundation) draft for human / Company Brain review.
--
-- This file has NOT been applied to any Supabase project and must not be
-- applied by any agent. Sprint 0 validated it only by loading it into a
-- throwaway local PostgreSQL 16 instance inside the engineering container
-- (see sprints/SPRINT_00_FOUNDATION/SPRINT_00_TEST_STRATEGY.md §6).
--
-- Revised 2026-10-07, after Sprint 0 (architecture/decisions/ADR-001):
--   * Target is the dedicated Supabase project "V&A Anime Clip Farming —
--     Engine 2" (ref mkeldytatorxxszjdngt), not the shared VA-Company-Brain
--     project. Schema `cf` is kept inside it.
--   * Section 14 only: the n8n runtime role is cf_n8n_runtime, provisioned
--     before any migration, with direct grants (the group role cf_agent is
--     dropped because the runtime role is NOINHERIT).
--   No table, column, constraint, type, function, trigger or view changed.
--   Re-validated on local PostgreSQL 16.15 and 17.10
--   (evidence/PRE_SPRINT_01_MIGRATION_PREFLIGHT.md).
--
-- Applying any part of it requires a separate, explicit migration
-- authorisation naming the exact objects. Sprint 1 applies only the subset in
-- migrations/0001_cf_sprint01.sql (SPRINT_00_ARCHITECTURE_REPORT.md §15).
--
-- Isolation: every object lives in the dedicated schema `cf`. Nothing here
-- reads, references, alters or depends on any object in `public` (the
-- YouTube Kids / Mikko & Lumi tables).
--
-- Rights rule: there is deliberately NO column anywhere named or meaning
-- fair_use, copyright_safe, legal_safe or similar. Test T-RIGHTS-01 asserts
-- this against the catalog.
-- =============================================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS cf;
COMMENT ON SCHEMA cf IS 'V&A Anime Clip Farming / Engine 2 only. Never store YouTube Kids state here.';

-- -----------------------------------------------------------------------------
-- 1. Vocabularies
-- -----------------------------------------------------------------------------

-- Shared lifecycle vocabulary. Each table restricts it further with a CHECK,
-- and cf.allowed_transitions defines the exact edges per object type.
CREATE TYPE cf.lifecycle_status AS ENUM (
  'IDEA', 'DRAFT', 'REVIEW', 'APPROVED', 'REJECTED',
  'BLOCKED', 'READY', 'PUBLISHED', 'RETIRED'
);

-- Execution state for runs and jobs only. Kept separate from the content
-- lifecycle on purpose (see STATE_MODEL_v0.1.md §3).
CREATE TYPE cf.run_state AS ENUM ('QUEUED', 'RUNNING', 'SUCCEEDED', 'FAILED', 'CANCELLED');

CREATE TYPE cf.gate_code AS ENUM ('G1', 'G2', 'G3', 'G4');

CREATE TYPE cf.gate_decision_value AS ENUM ('APPROVE', 'REJECT', 'REVOKE');

CREATE TYPE cf.format_class AS ENUM (
  'DISCOVERY_SHORT', 'CORE_ANALYSIS', 'MINI_ANALYSIS', 'MINI_ESSAY', 'LONG_FORM_EXPANSION'
);

CREATE TYPE cf.research_access_basis AS ENUM (
  'HUMAN_VIEWED_LICENSED_PLATFORM',   -- a person watched it on a legal service (e.g. Crunchyroll)
  'PUBLIC_OFFICIAL_UPLOAD',           -- rightsholder's own public upload (official channel)
  'PUBLIC_UPLOAD_OWNER_UNVERIFIED',   -- public upload whose owner is not verified
  'PRESS_OR_PROMO_KIT',
  'SECONDARY_REFERENCE'               -- wiki, database, article; no footage viewed
);

CREATE TYPE cf.source_category AS ENUM (
  'OFFICIAL_PROMO', 'OFFICIAL_TRAILER', 'PLATFORM_PERMITTED_SOURCE', 'LICENSED_SOURCE',
  'HUMAN_REVIEWED_SOURCE', 'ORIGINAL_GRAPHICS', 'ORIGINAL_MOTION_GRAPHICS',
  'ORIGINAL_DIAGRAM', 'ORIGINAL_STILL'
);

CREATE TYPE cf.platform AS ENUM ('YOUTUBE_SHORTS', 'YOUTUBE_LONG', 'TIKTOK', 'INSTAGRAM_REELS');

-- -----------------------------------------------------------------------------
-- 2. Governance and operational tables
-- -----------------------------------------------------------------------------

CREATE TABLE cf.reviewers (
  reviewer_id     uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  display_name    text NOT NULL,
  allowed_gates   cf.gate_code[] NOT NULL DEFAULT '{}',
  active          boolean NOT NULL DEFAULT true,
  created_at      timestamptz NOT NULL DEFAULT now(),
  retired_at      timestamptz
);
COMMENT ON TABLE cf.reviewers IS 'Named humans allowed to decide gates. Agents and service accounts are never reviewers.';

CREATE TABLE cf.agent_runs (
  agent_run_id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_code                text NOT NULL CHECK (agent_code ~ '^CF-00[0-9]$'),
  agent_version             text NOT NULL,
  prompt_version            text,
  model_requested           text,
  n8n_workflow_id           text,
  n8n_workflow_version_id   text,
  n8n_execution_id          text,
  idempotency_key           text NOT NULL UNIQUE,
  input_ids                 jsonb NOT NULL DEFAULT '{}'::jsonb,
  input_state_hash          text NOT NULL,
  run_state                 cf.run_state NOT NULL DEFAULT 'QUEUED',
  attempt_count             integer NOT NULL DEFAULT 0 CHECK (attempt_count >= 0),
  provider_call_count       integer NOT NULL DEFAULT 0 CHECK (provider_call_count >= 0),
  paid_call_count           integer NOT NULL DEFAULT 0 CHECK (paid_call_count >= 0),
  estimated_cost_usd        numeric(12,4) NOT NULL DEFAULT 0 CHECK (estimated_cost_usd >= 0),
  paid_authorisation_ref    text,
  output_summary            jsonb,
  error_code                text,
  error_detail              text,
  started_at                timestamptz,
  finished_at               timestamptz,
  created_at                timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT paid_calls_need_authorisation
    CHECK (paid_call_count = 0 OR paid_authorisation_ref IS NOT NULL),
  CONSTRAINT paid_is_subset_of_provider
    CHECK (paid_call_count <= provider_call_count)
);
COMMENT ON TABLE cf.agent_runs IS 'One invocation of one CF agent version. Replay with the same idempotency_key returns existing outputs.';

-- Global kill switches. Default OFF. Only a reviewer changes them.
CREATE TABLE cf.system_flags (
  flag_key                  text PRIMARY KEY CHECK (flag_key IN ('PUBLISH_ENABLED', 'PAID_CALLS_ENABLED', 'SCHEDULES_ENABLED')),
  enabled                   boolean NOT NULL DEFAULT false,
  changed_by_reviewer_id    uuid REFERENCES cf.reviewers(reviewer_id),
  changed_at                timestamptz NOT NULL DEFAULT now(),
  notes                     text
);

-- -----------------------------------------------------------------------------
-- 3. Reference identities
-- -----------------------------------------------------------------------------

CREATE TABLE cf.anime_franchises (
  franchise_id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  normalised_key          text NOT NULL UNIQUE CHECK (normalised_key = lower(normalised_key) AND normalised_key <> ''),
  display_name            text NOT NULL,
  anilist_franchise_ref   text UNIQUE,
  status                  cf.lifecycle_status NOT NULL DEFAULT 'DRAFT'
                          CHECK (status IN ('DRAFT', 'READY', 'BLOCKED', 'RETIRED')),
  agent_run_id            uuid REFERENCES cf.agent_runs(agent_run_id),
  created_at              timestamptz NOT NULL DEFAULT now(),
  updated_at              timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE cf.anime_titles (
  anime_title_id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  franchise_id            uuid NOT NULL REFERENCES cf.anime_franchises(franchise_id),
  normalised_title_key    text NOT NULL CHECK (normalised_title_key = lower(normalised_title_key) AND normalised_title_key <> ''),
  display_title           text NOT NULL,
  alt_titles              text[] NOT NULL DEFAULT '{}',
  anilist_id              integer UNIQUE,
  mal_id                  integer UNIQUE,
  media_type              text NOT NULL DEFAULT 'TV' CHECK (media_type IN ('TV', 'OVA', 'ONA', 'MOVIE', 'SPECIAL')),
  start_year              smallint CHECK (start_year BETWEEN 1917 AND 2100),
  era_decade              smallint GENERATED ALWAYS AS ((start_year / 10) * 10) STORED,
  status                  cf.lifecycle_status NOT NULL DEFAULT 'DRAFT'
                          CHECK (status IN ('DRAFT', 'READY', 'BLOCKED', 'RETIRED')),
  agent_run_id            uuid REFERENCES cf.agent_runs(agent_run_id),
  created_at              timestamptz NOT NULL DEFAULT now(),
  updated_at              timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT anime_titles_fallback_key UNIQUE NULLS NOT DISTINCT (franchise_id, normalised_title_key, start_year)
);

CREATE TABLE cf.anime_source_episodes (
  source_episode_id       uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  anime_title_id          uuid NOT NULL REFERENCES cf.anime_titles(anime_title_id),
  season_number           smallint NOT NULL CHECK (season_number >= 0),
  episode_number          numeric(6,1) NOT NULL CHECK (episode_number >= 0),
  episode_variant         text NOT NULL DEFAULT 'TV'
                          CHECK (episode_variant IN ('TV', 'OVA', 'MOVIE', 'SPECIAL', 'RECAP', 'DIRECTORS_CUT')),
  episode_title_display   text,
  duration_seconds        integer CHECK (duration_seconds > 0),
  status                  cf.lifecycle_status NOT NULL DEFAULT 'DRAFT'
                          CHECK (status IN ('DRAFT', 'READY', 'BLOCKED', 'RETIRED')),
  agent_run_id            uuid REFERENCES cf.agent_runs(agent_run_id),
  created_at              timestamptz NOT NULL DEFAULT now(),
  updated_at              timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT source_episode_natural_key UNIQUE (anime_title_id, season_number, episode_number, episode_variant)
);

-- -----------------------------------------------------------------------------
-- 4. Intelligence (CF-001, CF-002)
-- -----------------------------------------------------------------------------

CREATE TABLE cf.research_candidates (
  research_candidate_id   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  anime_title_id          uuid NOT NULL REFERENCES cf.anime_titles(anime_title_id),
  franchise_id            uuid NOT NULL REFERENCES cf.anime_franchises(franchise_id),
  topic_key               text NOT NULL CHECK (topic_key = lower(topic_key) AND topic_key <> ''),
  topic_display           text NOT NULL,
  content_lane            text NOT NULL,
  trend_state             text NOT NULL DEFAULT 'UNKNOWN'
                          CHECK (trend_state IN ('RISING', 'PEAKING', 'STEADY', 'DECLINING', 'EVERGREEN', 'UNKNOWN')),
  demand_signal           numeric(5,4) CHECK (demand_signal BETWEEN 0 AND 1),
  nostalgia_signal        numeric(5,4) CHECK (nostalgia_signal BETWEEN 0 AND 1),
  editorial_potential     numeric(5,4) CHECK (editorial_potential BETWEEN 0 AND 1),
  timeliness              numeric(5,4) CHECK (timeliness BETWEEN 0 AND 1),
  signal_evidence         jsonb NOT NULL CHECK (jsonb_typeof(signal_evidence) = 'array' AND jsonb_array_length(signal_evidence) > 0),
  observation_window      text NOT NULL CHECK (observation_window ~ '^[0-9]{4}-W[0-9]{2}$'),
  dedupe_key              text NOT NULL UNIQUE,
  status                  cf.lifecycle_status NOT NULL DEFAULT 'IDEA'
                          CHECK (status IN ('IDEA', 'READY', 'REJECTED', 'RETIRED')),
  rejection_reason        text,
  agent_run_id            uuid NOT NULL REFERENCES cf.agent_runs(agent_run_id),
  agent_version           text NOT NULL,
  prompt_version          text,
  created_at              timestamptz NOT NULL DEFAULT now(),
  updated_at              timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE cf.anime_scene_intelligence (
  scene_id                        uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  source_episode_id               uuid NOT NULL REFERENCES cf.anime_source_episodes(source_episode_id),
  anime_title_id                  uuid NOT NULL REFERENCES cf.anime_titles(anime_title_id),
  research_candidate_id           uuid REFERENCES cf.research_candidates(research_candidate_id),
  start_ms                        integer NOT NULL CHECK (start_ms >= 0),
  end_ms                          integer NOT NULL,
  characters_present              text[] NOT NULL DEFAULT '{}',
  scene_summary                   text NOT NULL,
  scene_function                  text,
  why_scene_matters               text NOT NULL,
  possible_editorial_angles       text[] NOT NULL DEFAULT '{}',
  context_requirement             text,
  spoiler_level                   text NOT NULL CHECK (spoiler_level IN ('NONE', 'LOW', 'MEDIUM', 'HIGH')),
  visual_strength                 numeric(5,4) CHECK (visual_strength BETWEEN 0 AND 1),
  nostalgia_signal                numeric(5,4) CHECK (nostalgia_signal BETWEEN 0 AND 1),
  editorial_strength              text NOT NULL DEFAULT 'UNASSESSED'
                                  CHECK (editorial_strength IN ('EDITORIALLY_STRONG', 'EDITORIALLY_MODERATE', 'EDITORIALLY_WEAK', 'UNASSESSED')),
  -- RESEARCH source only. Nothing here grants or implies publication permission.
  research_source_platform        text NOT NULL,
  research_source_reference       text NOT NULL,
  research_access_basis           cf.research_access_basis NOT NULL,
  research_access_notes           text,
  timestamps_human_verified       boolean NOT NULL DEFAULT false,
  model_confidence                numeric(5,4) CHECK (model_confidence BETWEEN 0 AND 1),
  possible_duplicate_of_scene_id  uuid REFERENCES cf.anime_scene_intelligence(scene_id),
  supersedes_scene_id             uuid REFERENCES cf.anime_scene_intelligence(scene_id),
  dedupe_key                      text NOT NULL UNIQUE,
  status                          cf.lifecycle_status NOT NULL DEFAULT 'DRAFT'
                                  CHECK (status IN ('DRAFT', 'READY', 'BLOCKED', 'REJECTED', 'RETIRED')),
  agent_run_id                    uuid NOT NULL REFERENCES cf.agent_runs(agent_run_id),
  agent_version                   text NOT NULL,
  prompt_version                  text,
  created_at                      timestamptz NOT NULL DEFAULT now(),
  updated_at                      timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT scene_positive_span CHECK (end_ms > start_ms)
);
COMMENT ON TABLE cf.anime_scene_intelligence IS
  'Research intelligence only. Publication status is NOT stored here; it is derived by cf.v_scene_publication_status from G3-approved packages.';

-- -----------------------------------------------------------------------------
-- 5. Editorial (CF-003 + G1, CF-004 + G2)
-- -----------------------------------------------------------------------------

CREATE TABLE cf.editorial_opportunities (
  content_candidate_id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  primary_scene_id                  uuid REFERENCES cf.anime_scene_intelligence(scene_id),
  anime_title_id                    uuid NOT NULL REFERENCES cf.anime_titles(anime_title_id),
  research_candidate_id             uuid REFERENCES cf.research_candidates(research_candidate_id),
  editorial_angle_key               text NOT NULL CHECK (editorial_angle_key = lower(editorial_angle_key) AND editorial_angle_key <> ''),
  editorial_territory               text,
  working_hook                      text NOT NULL,
  audience_type                     text,
  content_lane                      text NOT NULL,
  format_class                      cf.format_class NOT NULL,
  estimated_duration_seconds        integer NOT NULL CHECK (estimated_duration_seconds > 0),
  why_now                           text,
  why_viewer_cares                  text NOT NULL,
  hypothesis                        text NOT NULL,
  primary_metric                    text NOT NULL,
  production_difficulty             text CHECK (production_difficulty IN ('LOW', 'MEDIUM', 'HIGH')),
  model_rank                        integer CHECK (model_rank > 0),
  recommend_for_review              boolean NOT NULL DEFAULT false,
  content_sha256                    text NOT NULL,
  dedupe_key                        text NOT NULL,
  revision_of_content_candidate_id  uuid REFERENCES cf.editorial_opportunities(content_candidate_id),
  revision_number                   integer NOT NULL DEFAULT 1 CHECK (revision_number >= 1),
  output_ordinal                    integer NOT NULL CHECK (output_ordinal >= 0),
  status                            cf.lifecycle_status NOT NULL DEFAULT 'IDEA'
                                    CHECK (status IN ('IDEA', 'REVIEW', 'APPROVED', 'REJECTED', 'BLOCKED', 'RETIRED')),
  agent_run_id                      uuid NOT NULL REFERENCES cf.agent_runs(agent_run_id),
  agent_version                     text NOT NULL,
  prompt_version                    text,
  created_at                        timestamptz NOT NULL DEFAULT now(),
  updated_at                        timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT opportunity_run_ordinal UNIQUE (agent_run_id, output_ordinal)
);
CREATE UNIQUE INDEX editorial_opportunities_live_dedupe
  ON cf.editorial_opportunities (dedupe_key) WHERE status NOT IN ('REJECTED', 'RETIRED');

CREATE TABLE cf.editorial_opportunity_scenes (
  content_candidate_id  uuid NOT NULL REFERENCES cf.editorial_opportunities(content_candidate_id),
  scene_id              uuid NOT NULL REFERENCES cf.anime_scene_intelligence(scene_id),
  scene_role            text NOT NULL CHECK (scene_role IN ('PRIMARY', 'SUPPORTING')),
  created_at            timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (content_candidate_id, scene_id)
);

CREATE TABLE cf.content_scripts (
  script_id                       uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  content_candidate_id            uuid NOT NULL REFERENCES cf.editorial_opportunities(content_candidate_id),
  revision_number                 integer NOT NULL DEFAULT 1 CHECK (revision_number >= 1),
  revision_of_script_id           uuid REFERENCES cf.content_scripts(script_id),
  format_class                    cf.format_class NOT NULL,
  target_duration_seconds         integer NOT NULL CHECK (target_duration_seconds > 0),
  hook                            text NOT NULL,
  thesis                          text NOT NULL,
  required_context                text,
  narration_text                  text NOT NULL,
  evidence_points                 jsonb NOT NULL DEFAULT '[]'::jsonb,
  interpretation                  text,
  payoff                          text,
  cta                             text,
  caption_plan                    jsonb,
  factual_claims_to_verify        jsonb NOT NULL DEFAULT '[]'::jsonb,
  spoiler_handling                text,
  visual_evidence_requirements    jsonb NOT NULL DEFAULT '[]'::jsonb,
  narration_independence_selfcheck text NOT NULL DEFAULT 'NOT_RUN'
                                  CHECK (narration_independence_selfcheck IN ('PASS', 'FAIL', 'NOT_RUN')),
  content_sha256                  text NOT NULL,
  status                          cf.lifecycle_status NOT NULL DEFAULT 'DRAFT'
                                  CHECK (status IN ('DRAFT', 'REVIEW', 'APPROVED', 'REJECTED', 'BLOCKED', 'RETIRED')),
  agent_run_id                    uuid NOT NULL REFERENCES cf.agent_runs(agent_run_id),
  agent_version                   text NOT NULL,
  prompt_version                  text,
  created_at                      timestamptz NOT NULL DEFAULT now(),
  updated_at                      timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT script_revision_key UNIQUE (content_candidate_id, revision_number)
);
CREATE UNIQUE INDEX content_scripts_one_approved
  ON cf.content_scripts (content_candidate_id) WHERE status = 'APPROVED';

-- -----------------------------------------------------------------------------
-- 6. Source governance (CF-005 + G3)
-- -----------------------------------------------------------------------------

CREATE TABLE cf.publication_source_packages (
  source_package_id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  script_id                       uuid NOT NULL REFERENCES cf.content_scripts(script_id),
  revision_number                 integer NOT NULL DEFAULT 1 CHECK (revision_number >= 1),
  revision_of_source_package_id   uuid REFERENCES cf.publication_source_packages(source_package_id),
  package_summary                 text NOT NULL,
  required_original_assets        jsonb NOT NULL DEFAULT '[]'::jsonb,
  rights_risk_notes               text,       -- human-readable notes; never a determination
  source_minimisation_notes       text,
  commentary_ratio_estimate       numeric(5,4) CHECK (commentary_ratio_estimate BETWEEN 0 AND 1),
  blocked_reason                  text CHECK (blocked_reason IN ('NO_ACCEPTABLE_SOURCE', 'HUMAN_REVIEW_REQUIRED')),
  content_sha256                  text NOT NULL,
  status                          cf.lifecycle_status NOT NULL DEFAULT 'DRAFT'
                                  CHECK (status IN ('DRAFT', 'REVIEW', 'APPROVED', 'REJECTED', 'BLOCKED', 'RETIRED')),
  agent_run_id                    uuid NOT NULL REFERENCES cf.agent_runs(agent_run_id),
  agent_version                   text NOT NULL,
  created_at                      timestamptz NOT NULL DEFAULT now(),
  updated_at                      timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT source_package_revision_key UNIQUE (script_id, revision_number),
  CONSTRAINT blocked_needs_reason CHECK (status <> 'BLOCKED' OR blocked_reason IS NOT NULL)
);
CREATE UNIQUE INDEX publication_source_packages_one_approved
  ON cf.publication_source_packages (script_id) WHERE status = 'APPROVED';

CREATE TABLE cf.publication_source_items (
  source_item_id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  source_package_id       uuid NOT NULL REFERENCES cf.publication_source_packages(source_package_id),
  item_ordinal            integer NOT NULL CHECK (item_ordinal >= 0),
  source_category         cf.source_category NOT NULL,
  source_episode_id       uuid REFERENCES cf.anime_source_episodes(source_episode_id),
  scene_id                uuid REFERENCES cf.anime_scene_intelligence(scene_id),
  origin_reference        text NOT NULL,     -- URL of the official upload, licence reference, or internal asset ref
  origin_owner_claimed    text,              -- who the material is believed to belong to
  segment_start_ms        integer CHECK (segment_start_ms >= 0),
  segment_end_ms          integer,
  proposed_use_seconds    numeric(7,2) CHECK (proposed_use_seconds >= 0),
  provenance_notes        text,
  item_risk_notes         text,
  created_at              timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT source_item_ordinal UNIQUE (source_package_id, item_ordinal),
  CONSTRAINT source_item_span CHECK (segment_end_ms IS NULL OR segment_end_ms > coalesce(segment_start_ms, 0))
);

-- -----------------------------------------------------------------------------
-- 7. Production (CF-006, CF-007 + G4)
-- -----------------------------------------------------------------------------

CREATE TABLE cf.production_manifests (
  production_manifest_id    uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  script_id                 uuid NOT NULL REFERENCES cf.content_scripts(script_id),
  source_package_id         uuid NOT NULL REFERENCES cf.publication_source_packages(source_package_id),
  revision_number           integer NOT NULL DEFAULT 1 CHECK (revision_number >= 1),
  manifest_schema_version   text NOT NULL,
  planner_version           text NOT NULL,
  input_hash                text NOT NULL UNIQUE,
  segment_plan              jsonb NOT NULL,
  audio_plan                jsonb NOT NULL,
  caption_plan              jsonb NOT NULL,
  asset_requirements        jsonb NOT NULL,
  target_runtime_seconds    integer NOT NULL CHECK (target_runtime_seconds > 0),
  target_aspect_ratio       text NOT NULL DEFAULT '9:16' CHECK (target_aspect_ratio IN ('9:16', '16:9', '1:1', '4:5')),
  render_specification      jsonb NOT NULL,
  content_sha256            text NOT NULL,
  status                    cf.lifecycle_status NOT NULL DEFAULT 'DRAFT'
                            CHECK (status IN ('DRAFT', 'READY', 'BLOCKED', 'REJECTED', 'RETIRED')),
  agent_run_id              uuid NOT NULL REFERENCES cf.agent_runs(agent_run_id),
  agent_version             text NOT NULL,
  created_at                timestamptz NOT NULL DEFAULT now(),
  updated_at                timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT manifest_revision_key UNIQUE (script_id, source_package_id, revision_number)
);

CREATE TABLE cf.production_jobs (
  production_job_id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  production_manifest_id    uuid NOT NULL REFERENCES cf.production_manifests(production_manifest_id),
  job_type                  text NOT NULL CHECK (job_type IN ('NARRATION', 'CAPTIONS', 'GRAPHIC', 'MUSIC_SELECTION', 'SFX_SELECTION', 'ASSEMBLY', 'RENDER')),
  segment_ref               text NOT NULL DEFAULT 'ALL',
  attempt_group             integer NOT NULL DEFAULT 1 CHECK (attempt_group >= 1),
  idempotency_key           text NOT NULL UNIQUE,
  provider                  text,
  is_paid                   boolean NOT NULL DEFAULT false,
  paid_authorisation_ref    text,
  run_state                 cf.run_state NOT NULL DEFAULT 'QUEUED',
  attempt_count             integer NOT NULL DEFAULT 0 CHECK (attempt_count >= 0),
  max_attempts              integer NOT NULL DEFAULT 1 CHECK (max_attempts >= 1),
  last_error_code           text,
  agent_run_id              uuid NOT NULL REFERENCES cf.agent_runs(agent_run_id),
  created_at                timestamptz NOT NULL DEFAULT now(),
  updated_at                timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT paid_job_needs_authorisation CHECK (NOT is_paid OR paid_authorisation_ref IS NOT NULL),
  CONSTRAINT attempts_capped CHECK (attempt_count <= max_attempts)
);

CREATE TABLE cf.content_assets (
  asset_id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  asset_kind                text NOT NULL CHECK (asset_kind IN (
                              'NARRATION_AUDIO', 'CAPTION_FILE', 'ORIGINAL_GRAPHIC', 'ORIGINAL_STILL',
                              'ORIGINAL_MOTION', 'THIRD_PARTY_SOURCE_SEGMENT', 'MUSIC', 'SFX',
                              'MASTER_VIDEO', 'PLATFORM_VARIANT', 'THUMBNAIL')),
  storage_bucket            text NOT NULL,
  storage_path              text NOT NULL,
  sha256                    text NOT NULL UNIQUE CHECK (sha256 ~ '^[0-9a-f]{64}$'),
  bytes                     bigint NOT NULL CHECK (bytes > 0),
  mime_type                 text NOT NULL,
  duration_ms               integer CHECK (duration_ms > 0),
  width                     integer CHECK (width > 0),
  height                    integer CHECK (height > 0),
  production_job_id         uuid REFERENCES cf.production_jobs(production_job_id),
  source_item_id            uuid REFERENCES cf.publication_source_items(source_item_id),
  provider_provenance       jsonb,
  status                    cf.lifecycle_status NOT NULL DEFAULT 'DRAFT'
                            CHECK (status IN ('DRAFT', 'READY', 'REJECTED', 'RETIRED')),
  agent_run_id              uuid REFERENCES cf.agent_runs(agent_run_id),
  created_at                timestamptz NOT NULL DEFAULT now(),
  updated_at                timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT third_party_needs_source_item
    CHECK (asset_kind <> 'THIRD_PARTY_SOURCE_SEGMENT' OR source_item_id IS NOT NULL),
  CONSTRAINT storage_location_unique UNIQUE (storage_bucket, storage_path)
);

CREATE TABLE cf.renders (
  render_id                 uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  production_manifest_id    uuid NOT NULL REFERENCES cf.production_manifests(production_manifest_id),
  render_revision           integer NOT NULL DEFAULT 1 CHECK (render_revision >= 1),
  master_asset_id           uuid NOT NULL UNIQUE REFERENCES cf.content_assets(asset_id),
  master_format             text NOT NULL DEFAULT 'MASTER_VERTICAL_9x16',
  duration_ms               integer NOT NULL CHECK (duration_ms > 0),
  width                     integer NOT NULL CHECK (width > 0),
  height                    integer NOT NULL CHECK (height > 0),
  content_sha256            text NOT NULL CHECK (content_sha256 ~ '^[0-9a-f]{64}$'),  -- = master asset sha256
  provider_provenance       jsonb,
  status                    cf.lifecycle_status NOT NULL DEFAULT 'DRAFT'
                            CHECK (status IN ('DRAFT', 'REVIEW', 'APPROVED', 'REJECTED', 'RETIRED')),
  agent_run_id              uuid NOT NULL REFERENCES cf.agent_runs(agent_run_id),
  agent_version             text NOT NULL,
  created_at                timestamptz NOT NULL DEFAULT now(),
  updated_at                timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT render_revision_key UNIQUE (production_manifest_id, render_revision)
);

-- -----------------------------------------------------------------------------
-- 8. Distribution and learning (CF-008, CF-009)
-- -----------------------------------------------------------------------------

CREATE TABLE cf.published_content (
  published_content_id      uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  render_id                 uuid NOT NULL UNIQUE REFERENCES cf.renders(render_id),
  content_candidate_id      uuid NOT NULL REFERENCES cf.editorial_opportunities(content_candidate_id),
  script_id                 uuid NOT NULL REFERENCES cf.content_scripts(script_id),
  display_title             text NOT NULL,
  status                    cf.lifecycle_status NOT NULL DEFAULT 'READY'
                            CHECK (status IN ('READY', 'PUBLISHED', 'RETIRED')),
  agent_run_id              uuid NOT NULL REFERENCES cf.agent_runs(agent_run_id),
  created_at                timestamptz NOT NULL DEFAULT now(),
  updated_at                timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE cf.platform_posts (
  platform_post_id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  published_content_id      uuid NOT NULL REFERENCES cf.published_content(published_content_id),
  platform                  cf.platform NOT NULL,
  upload_asset_id           uuid NOT NULL REFERENCES cf.content_assets(asset_id),
  title                     text NOT NULL,
  description               text,
  hashtags                  text[] NOT NULL DEFAULT '{}',
  scheduled_for             timestamptz,
  publish_idempotency_key   text NOT NULL UNIQUE,
  external_post_id          text,
  external_url              text,
  published_at              timestamptz,
  status                    cf.lifecycle_status NOT NULL DEFAULT 'READY'
                            CHECK (status IN ('READY', 'PUBLISHED', 'BLOCKED', 'RETIRED')),
  failure_code              text,
  attempt_count             integer NOT NULL DEFAULT 0 CHECK (attempt_count >= 0),
  agent_run_id              uuid NOT NULL REFERENCES cf.agent_runs(agent_run_id),
  created_at                timestamptz NOT NULL DEFAULT now(),
  updated_at                timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT external_post_unique UNIQUE (platform, external_post_id),
  CONSTRAINT published_needs_external_id
    CHECK (status <> 'PUBLISHED' OR (external_post_id IS NOT NULL AND published_at IS NOT NULL))
);
CREATE UNIQUE INDEX platform_posts_one_live_per_platform
  ON cf.platform_posts (published_content_id, platform) WHERE status <> 'RETIRED';

CREATE TABLE cf.performance_snapshots (
  performance_snapshot_id   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  platform_post_id          uuid NOT NULL REFERENCES cf.platform_posts(platform_post_id),
  captured_at               timestamptz NOT NULL,
  captured_bucket_utc       timestamp NOT NULL,   -- date_trunc('hour', captured_at at time zone 'UTC'); set by the writer, checked below
  metric_window             text NOT NULL CHECK (metric_window IN ('LIFETIME', 'H24', 'D7', 'D28', 'D90')),
  views                     bigint CHECK (views >= 0),
  likes                     bigint CHECK (likes >= 0),
  comments                  bigint CHECK (comments >= 0),
  shares                    bigint CHECK (shares >= 0),
  saves                     bigint CHECK (saves >= 0),
  avg_view_duration_ms      bigint CHECK (avg_view_duration_ms >= 0),
  completion_rate           numeric(5,4) CHECK (completion_rate BETWEEN 0 AND 1),
  subscribers_gained        bigint,
  metrics                   jsonb NOT NULL,     -- full raw platform payload subset
  source_api                text NOT NULL,
  agent_run_id              uuid NOT NULL REFERENCES cf.agent_runs(agent_run_id),
  created_at                timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT snapshot_bucket_matches
    CHECK (captured_bucket_utc = date_trunc('hour', captured_at AT TIME ZONE 'UTC')),
  CONSTRAINT snapshot_dedupe UNIQUE (platform_post_id, metric_window, captured_bucket_utc)
);

CREATE TABLE cf.content_learning_log (
  learning_log_id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  published_content_id        uuid REFERENCES cf.published_content(published_content_id),
  hypothesis                  text NOT NULL,
  result                      text NOT NULL,
  performance_vs_baseline     jsonb,
  what_worked                 text,
  what_failed                 text,
  confidence                  numeric(5,4) CHECK (confidence BETWEEN 0 AND 1),
  next_test                   text,
  recommended_backlog_effect  text,
  evidence_snapshot_ids       uuid[] NOT NULL DEFAULT '{}',
  supersedes_learning_log_id  uuid REFERENCES cf.content_learning_log(learning_log_id),
  output_ordinal              integer NOT NULL CHECK (output_ordinal >= 0),
  agent_run_id                uuid NOT NULL REFERENCES cf.agent_runs(agent_run_id),
  created_at                  timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT learning_run_ordinal UNIQUE (agent_run_id, output_ordinal)
);

-- -----------------------------------------------------------------------------
-- 9. Gate decisions (append-only; G1–G4)
-- -----------------------------------------------------------------------------

CREATE TABLE cf.gate_decisions (
  gate_decision_id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  gate                          cf.gate_code NOT NULL,
  object_type                   text NOT NULL,
  object_id                     uuid NOT NULL,
  object_content_sha256         text NOT NULL,
  decision                      cf.gate_decision_value NOT NULL,
  reviewer_id                   uuid NOT NULL REFERENCES cf.reviewers(reviewer_id),
  decided_at                    timestamptz NOT NULL DEFAULT now(),
  notes                         text,
  approved_platforms            cf.platform[],
  supersedes_gate_decision_id   uuid UNIQUE REFERENCES cf.gate_decisions(gate_decision_id),
  idempotency_key               text NOT NULL UNIQUE,
  surface                       text NOT NULL,     -- which human surface recorded it (e.g. 'SUPABASE_STUDIO', 'SLACK_INTERACTIVE')
  created_at                    timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT gate_object_mapping CHECK (
       (gate = 'G1' AND object_type = 'editorial_opportunity')
    OR (gate = 'G2' AND object_type = 'content_script')
    OR (gate = 'G3' AND object_type = 'publication_source_package')
    OR (gate = 'G4' AND object_type = 'render')),
  CONSTRAINT g4_approve_names_platforms CHECK (
       gate <> 'G4' OR decision <> 'APPROVE'
    OR (approved_platforms IS NOT NULL AND cardinality(approved_platforms) > 0)),
  CONSTRAINT platforms_only_on_g4 CHECK (gate = 'G4' OR approved_platforms IS NULL),
  CONSTRAINT revoke_supersedes CHECK (decision <> 'REVOKE' OR supersedes_gate_decision_id IS NOT NULL)
);
CREATE INDEX gate_decisions_object ON cf.gate_decisions (object_type, object_id);

-- A decision is effective when no later decision supersedes it.
CREATE VIEW cf.v_effective_gate_decisions AS
SELECT d.*
FROM cf.gate_decisions d
WHERE NOT EXISTS (
  SELECT 1 FROM cf.gate_decisions s WHERE s.supersedes_gate_decision_id = d.gate_decision_id
);

-- -----------------------------------------------------------------------------
-- 10. State machine as data
-- -----------------------------------------------------------------------------

CREATE TABLE cf.allowed_transitions (
  object_type     text NOT NULL,
  from_status     text NOT NULL,      -- 'NEW' = initial insert
  to_status       text NOT NULL,
  required_gate   cf.gate_code,
  required_decision cf.gate_decision_value,
  mode            text NOT NULL CHECK (mode IN ('DETERMINISTIC', 'HUMAN_GATE', 'HUMAN_ADMIN')),
  PRIMARY KEY (object_type, from_status, to_status),
  CHECK ((required_gate IS NULL) = (required_decision IS NULL)),
  CHECK ((mode = 'HUMAN_GATE') = (required_gate IS NOT NULL))
);

INSERT INTO cf.allowed_transitions (object_type, from_status, to_status, required_gate, required_decision, mode) VALUES
  -- reference data
  ('anime_franchise', 'NEW', 'DRAFT', NULL, NULL, 'DETERMINISTIC'),
  ('anime_franchise', 'DRAFT', 'READY', NULL, NULL, 'DETERMINISTIC'),
  ('anime_franchise', 'DRAFT', 'BLOCKED', NULL, NULL, 'DETERMINISTIC'),
  ('anime_franchise', 'BLOCKED', 'READY', NULL, NULL, 'HUMAN_ADMIN'),
  ('anime_franchise', 'READY', 'RETIRED', NULL, NULL, 'HUMAN_ADMIN'),
  ('anime_title', 'NEW', 'DRAFT', NULL, NULL, 'DETERMINISTIC'),
  ('anime_title', 'DRAFT', 'READY', NULL, NULL, 'DETERMINISTIC'),
  ('anime_title', 'DRAFT', 'BLOCKED', NULL, NULL, 'DETERMINISTIC'),
  ('anime_title', 'BLOCKED', 'READY', NULL, NULL, 'HUMAN_ADMIN'),
  ('anime_title', 'READY', 'RETIRED', NULL, NULL, 'HUMAN_ADMIN'),
  ('anime_source_episode', 'NEW', 'DRAFT', NULL, NULL, 'DETERMINISTIC'),
  ('anime_source_episode', 'DRAFT', 'READY', NULL, NULL, 'DETERMINISTIC'),
  ('anime_source_episode', 'DRAFT', 'BLOCKED', NULL, NULL, 'DETERMINISTIC'),
  ('anime_source_episode', 'BLOCKED', 'READY', NULL, NULL, 'HUMAN_ADMIN'),
  ('anime_source_episode', 'READY', 'RETIRED', NULL, NULL, 'HUMAN_ADMIN'),
  -- CF-001
  ('research_candidate', 'NEW', 'IDEA', NULL, NULL, 'DETERMINISTIC'),
  ('research_candidate', 'IDEA', 'READY', NULL, NULL, 'DETERMINISTIC'),
  ('research_candidate', 'IDEA', 'REJECTED', NULL, NULL, 'DETERMINISTIC'),
  ('research_candidate', 'READY', 'RETIRED', NULL, NULL, 'DETERMINISTIC'),
  -- CF-002
  ('scene', 'NEW', 'DRAFT', NULL, NULL, 'DETERMINISTIC'),
  ('scene', 'DRAFT', 'READY', NULL, NULL, 'DETERMINISTIC'),
  ('scene', 'DRAFT', 'BLOCKED', NULL, NULL, 'DETERMINISTIC'),
  ('scene', 'DRAFT', 'REJECTED', NULL, NULL, 'HUMAN_ADMIN'),
  ('scene', 'BLOCKED', 'DRAFT', NULL, NULL, 'HUMAN_ADMIN'),
  ('scene', 'READY', 'RETIRED', NULL, NULL, 'HUMAN_ADMIN'),
  -- CF-003 + G1
  ('editorial_opportunity', 'NEW', 'IDEA', NULL, NULL, 'DETERMINISTIC'),
  ('editorial_opportunity', 'IDEA', 'REVIEW', NULL, NULL, 'DETERMINISTIC'),
  ('editorial_opportunity', 'IDEA', 'REJECTED', NULL, NULL, 'DETERMINISTIC'),
  ('editorial_opportunity', 'IDEA', 'BLOCKED', NULL, NULL, 'DETERMINISTIC'),
  ('editorial_opportunity', 'REVIEW', 'APPROVED', 'G1', 'APPROVE', 'HUMAN_GATE'),
  ('editorial_opportunity', 'REVIEW', 'REJECTED', 'G1', 'REJECT', 'HUMAN_GATE'),
  ('editorial_opportunity', 'APPROVED', 'RETIRED', 'G1', 'REVOKE', 'HUMAN_GATE'),
  ('editorial_opportunity', 'REVIEW', 'RETIRED', NULL, NULL, 'DETERMINISTIC'),
  -- CF-004 + G2
  ('content_script', 'NEW', 'DRAFT', NULL, NULL, 'DETERMINISTIC'),
  ('content_script', 'DRAFT', 'REVIEW', NULL, NULL, 'DETERMINISTIC'),
  ('content_script', 'DRAFT', 'BLOCKED', NULL, NULL, 'DETERMINISTIC'),
  ('content_script', 'DRAFT', 'RETIRED', NULL, NULL, 'DETERMINISTIC'),
  ('content_script', 'REVIEW', 'APPROVED', 'G2', 'APPROVE', 'HUMAN_GATE'),
  ('content_script', 'REVIEW', 'REJECTED', 'G2', 'REJECT', 'HUMAN_GATE'),
  ('content_script', 'APPROVED', 'RETIRED', 'G2', 'REVOKE', 'HUMAN_GATE'),
  -- CF-005 + G3
  ('publication_source_package', 'NEW', 'DRAFT', NULL, NULL, 'DETERMINISTIC'),
  ('publication_source_package', 'DRAFT', 'REVIEW', NULL, NULL, 'DETERMINISTIC'),
  ('publication_source_package', 'DRAFT', 'BLOCKED', NULL, NULL, 'DETERMINISTIC'),
  ('publication_source_package', 'BLOCKED', 'RETIRED', NULL, NULL, 'DETERMINISTIC'),
  ('publication_source_package', 'REVIEW', 'APPROVED', 'G3', 'APPROVE', 'HUMAN_GATE'),
  ('publication_source_package', 'REVIEW', 'REJECTED', 'G3', 'REJECT', 'HUMAN_GATE'),
  ('publication_source_package', 'APPROVED', 'RETIRED', 'G3', 'REVOKE', 'HUMAN_GATE'),
  -- CF-006
  ('production_manifest', 'NEW', 'DRAFT', NULL, NULL, 'DETERMINISTIC'),
  ('production_manifest', 'DRAFT', 'READY', NULL, NULL, 'DETERMINISTIC'),
  ('production_manifest', 'DRAFT', 'BLOCKED', NULL, NULL, 'DETERMINISTIC'),
  ('production_manifest', 'DRAFT', 'REJECTED', NULL, NULL, 'DETERMINISTIC'),
  ('production_manifest', 'READY', 'RETIRED', NULL, NULL, 'DETERMINISTIC'),
  -- CF-007 assets
  ('content_asset', 'NEW', 'DRAFT', NULL, NULL, 'DETERMINISTIC'),
  ('content_asset', 'DRAFT', 'READY', NULL, NULL, 'DETERMINISTIC'),
  ('content_asset', 'DRAFT', 'REJECTED', NULL, NULL, 'DETERMINISTIC'),
  ('content_asset', 'READY', 'RETIRED', NULL, NULL, 'HUMAN_ADMIN'),
  -- CF-007 + G4
  ('render', 'NEW', 'DRAFT', NULL, NULL, 'DETERMINISTIC'),
  ('render', 'DRAFT', 'REVIEW', NULL, NULL, 'DETERMINISTIC'),
  ('render', 'DRAFT', 'REJECTED', NULL, NULL, 'DETERMINISTIC'),
  ('render', 'REVIEW', 'APPROVED', 'G4', 'APPROVE', 'HUMAN_GATE'),
  ('render', 'REVIEW', 'REJECTED', 'G4', 'REJECT', 'HUMAN_GATE'),
  ('render', 'APPROVED', 'RETIRED', 'G4', 'REVOKE', 'HUMAN_GATE'),
  -- CF-008
  ('published_content', 'NEW', 'READY', NULL, NULL, 'DETERMINISTIC'),
  ('published_content', 'READY', 'PUBLISHED', NULL, NULL, 'DETERMINISTIC'),
  ('published_content', 'PUBLISHED', 'RETIRED', NULL, NULL, 'HUMAN_ADMIN'),
  ('published_content', 'READY', 'RETIRED', NULL, NULL, 'HUMAN_ADMIN'),
  ('platform_post', 'NEW', 'READY', NULL, NULL, 'DETERMINISTIC'),
  ('platform_post', 'READY', 'PUBLISHED', NULL, NULL, 'DETERMINISTIC'),
  ('platform_post', 'READY', 'BLOCKED', NULL, NULL, 'DETERMINISTIC'),
  ('platform_post', 'BLOCKED', 'READY', NULL, NULL, 'HUMAN_ADMIN'),
  ('platform_post', 'BLOCKED', 'RETIRED', NULL, NULL, 'HUMAN_ADMIN'),
  ('platform_post', 'PUBLISHED', 'RETIRED', NULL, NULL, 'HUMAN_ADMIN');

-- -----------------------------------------------------------------------------
-- 11. Guard functions and triggers
-- -----------------------------------------------------------------------------

CREATE FUNCTION cf.touch_updated_at() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  NEW.updated_at := now();
  RETURN NEW;
END $$;

-- Rejects any status change that is not an allowed edge, and any edge that
-- needs a human gate without an effective matching gate decision for this
-- exact object ID and content hash.
-- TG_ARGV[0] = object_type, TG_ARGV[1] = primary-key column name.
CREATE FUNCTION cf.guard_status_transition() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
  v_object_type text := TG_ARGV[0];
  v_pk_col      text := TG_ARGV[1];
  v_from        text;
  v_to          text := NEW.status::text;
  v_obj_id      uuid := (to_jsonb(NEW) ->> v_pk_col)::uuid;
  v_sha         text := to_jsonb(NEW) ->> 'content_sha256';
  v_rule        cf.allowed_transitions%ROWTYPE;
BEGIN
  IF TG_OP = 'INSERT' THEN
    v_from := 'NEW';
  ELSE
    v_from := OLD.status::text;
    IF v_from = v_to THEN
      RETURN NEW;
    END IF;
  END IF;

  SELECT * INTO v_rule FROM cf.allowed_transitions
   WHERE object_type = v_object_type AND from_status = v_from AND to_status = v_to;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'CF_INVALID_TRANSITION: % % -> % is not allowed', v_object_type, v_from, v_to
      USING ERRCODE = 'check_violation';
  END IF;

  IF v_rule.required_gate IS NOT NULL THEN
    PERFORM 1 FROM cf.v_effective_gate_decisions d
     WHERE d.gate = v_rule.required_gate
       AND d.object_type = v_object_type
       AND d.object_id = v_obj_id
       AND d.decision = v_rule.required_decision
       AND d.object_content_sha256 = v_sha;
    IF NOT FOUND THEN
      RAISE EXCEPTION 'CF_GATE_DECISION_MISSING: % % -> % needs an effective % % decision for this object and content hash',
        v_object_type, v_from, v_to, v_rule.required_gate, v_rule.required_decision
        USING ERRCODE = 'check_violation';
    END IF;
  END IF;

  RETURN NEW;
END $$;

-- Once a row has left its first status, only the listed columns may change.
-- TG_ARGV = mutable column names (status and updated_at are always mutable).
CREATE FUNCTION cf.freeze_after_first_status() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
  v_old jsonb := to_jsonb(OLD) - 'status' - 'updated_at';
  v_new jsonb := to_jsonb(NEW) - 'status' - 'updated_at';
  i int;
BEGIN
  IF OLD.status::text IN ('IDEA', 'DRAFT') THEN
    RETURN NEW;
  END IF;
  IF TG_NARGS > 0 THEN
    FOR i IN 0 .. TG_NARGS - 1 LOOP
      v_old := v_old - TG_ARGV[i];
      v_new := v_new - TG_ARGV[i];
    END LOOP;
  END IF;
  IF v_old IS DISTINCT FROM v_new THEN
    RAISE EXCEPTION 'CF_IMMUTABLE_ROW: %.% content is frozen once status leaves IDEA/DRAFT; create a new revision instead',
      TG_TABLE_SCHEMA, TG_TABLE_NAME USING ERRCODE = 'check_violation';
  END IF;
  RETURN NEW;
END $$;

CREATE FUNCTION cf.forbid_update_delete() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'CF_APPEND_ONLY: %.% rows cannot be updated or deleted', TG_TABLE_SCHEMA, TG_TABLE_NAME
    USING ERRCODE = 'check_violation';
END $$;

CREATE FUNCTION cf.forbid_delete() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'CF_NO_DELETE: %.% rows are retired, never deleted', TG_TABLE_SCHEMA, TG_TABLE_NAME
    USING ERRCODE = 'check_violation';
END $$;

-- Append-only history
CREATE TRIGGER gate_decisions_append_only BEFORE UPDATE OR DELETE ON cf.gate_decisions
  FOR EACH ROW EXECUTE FUNCTION cf.forbid_update_delete();
CREATE TRIGGER performance_snapshots_append_only BEFORE UPDATE OR DELETE ON cf.performance_snapshots
  FOR EACH ROW EXECUTE FUNCTION cf.forbid_update_delete();
CREATE TRIGGER content_learning_log_append_only BEFORE UPDATE OR DELETE ON cf.content_learning_log
  FOR EACH ROW EXECUTE FUNCTION cf.forbid_update_delete();
CREATE TRIGGER publication_source_items_append_only BEFORE UPDATE OR DELETE ON cf.publication_source_items
  FOR EACH ROW EXECUTE FUNCTION cf.forbid_update_delete();
CREATE TRIGGER editorial_opportunity_scenes_append_only BEFORE UPDATE OR DELETE ON cf.editorial_opportunity_scenes
  FOR EACH ROW EXECUTE FUNCTION cf.forbid_update_delete();

-- Status guards, freeze rules, no-delete and updated_at on lifecycle tables
DO $$
DECLARE
  r record;
BEGIN
  FOR r IN SELECT * FROM (VALUES
    ('anime_franchises',            'anime_franchise',            'franchise_id',            ARRAY['display_name','anilist_franchise_ref']),
    ('anime_titles',                'anime_title',                'anime_title_id',          ARRAY['display_title','alt_titles','anilist_id','mal_id']),
    ('anime_source_episodes',       'anime_source_episode',       'source_episode_id',       ARRAY['episode_title_display','duration_seconds']),
    ('research_candidates',         'research_candidate',         'research_candidate_id',   ARRAY['rejection_reason']),
    ('anime_scene_intelligence',    'scene',                      'scene_id',                ARRAY['timestamps_human_verified']),
    ('editorial_opportunities',     'editorial_opportunity',      'content_candidate_id',    ARRAY[]::text[]),
    ('content_scripts',             'content_script',             'script_id',               ARRAY[]::text[]),
    ('publication_source_packages', 'publication_source_package', 'source_package_id',       ARRAY['blocked_reason']),
    ('production_manifests',        'production_manifest',        'production_manifest_id',  ARRAY[]::text[]),
    ('content_assets',              'content_asset',              'asset_id',                ARRAY[]::text[]),
    ('renders',                     'render',                     'render_id',               ARRAY[]::text[]),
    ('published_content',           'published_content',          'published_content_id',    ARRAY['display_title']),
    ('platform_posts',              'platform_post',              'platform_post_id',        ARRAY['external_post_id','external_url','published_at','failure_code','attempt_count','scheduled_for'])
  ) AS t(tbl, obj, pk, mutable_cols)
  LOOP
    EXECUTE format('CREATE TRIGGER %I BEFORE INSERT OR UPDATE OF status ON cf.%I FOR EACH ROW EXECUTE FUNCTION cf.guard_status_transition(%L, %L)',
                   r.tbl || '_guard_status', r.tbl, r.obj, r.pk);
    EXECUTE format('CREATE TRIGGER %I BEFORE UPDATE ON cf.%I FOR EACH ROW EXECUTE FUNCTION cf.freeze_after_first_status(%s)',
                   r.tbl || '_freeze', r.tbl,
                   coalesce((SELECT string_agg(quote_literal(c), ', ') FROM unnest(r.mutable_cols) c), ''));
    EXECUTE format('CREATE TRIGGER %I BEFORE DELETE ON cf.%I FOR EACH ROW EXECUTE FUNCTION cf.forbid_delete()',
                   r.tbl || '_no_delete', r.tbl);
    EXECUTE format('CREATE TRIGGER %I BEFORE UPDATE ON cf.%I FOR EACH ROW EXECUTE FUNCTION cf.touch_updated_at()',
                   r.tbl || '_touch', r.tbl);
  END LOOP;
END $$;

-- -----------------------------------------------------------------------------
-- 12. The only write path for human decisions
-- -----------------------------------------------------------------------------

CREATE FUNCTION cf.record_gate_decision(
  p_gate              cf.gate_code,
  p_object_id         uuid,
  p_decision          cf.gate_decision_value,
  p_reviewer_id       uuid,
  p_idempotency_key   text,
  p_surface           text,
  p_notes             text DEFAULT NULL,
  p_approved_platforms cf.platform[] DEFAULT NULL,
  p_expected_sha256   text DEFAULT NULL
) RETURNS uuid
LANGUAGE plpgsql SECURITY DEFINER SET search_path = cf, pg_temp AS $$
DECLARE
  v_existing   uuid;
  v_type       text;
  v_table      text;
  v_pk         text;
  v_status     text;
  v_sha        text;
  v_target     cf.lifecycle_status;
  v_supersedes uuid;
  v_id         uuid;
BEGIN
  -- Replay: same idempotency key returns the same decision, no second write.
  SELECT gate_decision_id INTO v_existing FROM cf.gate_decisions WHERE idempotency_key = p_idempotency_key;
  IF FOUND THEN
    RETURN v_existing;
  END IF;

  PERFORM 1 FROM cf.reviewers r
   WHERE r.reviewer_id = p_reviewer_id AND r.active AND p_gate = ANY (r.allowed_gates);
  IF NOT FOUND THEN
    RAISE EXCEPTION 'CF_REVIEWER_NOT_AUTHORISED for %', p_gate USING ERRCODE = 'insufficient_privilege';
  END IF;

  CASE p_gate
    WHEN 'G1' THEN v_type := 'editorial_opportunity';      v_table := 'editorial_opportunities';     v_pk := 'content_candidate_id';
    WHEN 'G2' THEN v_type := 'content_script';             v_table := 'content_scripts';             v_pk := 'script_id';
    WHEN 'G3' THEN v_type := 'publication_source_package'; v_table := 'publication_source_packages'; v_pk := 'source_package_id';
    WHEN 'G4' THEN v_type := 'render';                     v_table := 'renders';                     v_pk := 'render_id';
  END CASE;

  EXECUTE format('SELECT status::text, content_sha256 FROM cf.%I WHERE %I = $1 FOR UPDATE', v_table, v_pk)
    INTO v_status, v_sha USING p_object_id;
  IF v_status IS NULL THEN
    RAISE EXCEPTION 'CF_OBJECT_NOT_FOUND: % %', v_type, p_object_id USING ERRCODE = 'no_data_found';
  END IF;
  IF p_expected_sha256 IS NOT NULL AND p_expected_sha256 <> v_sha THEN
    RAISE EXCEPTION 'CF_STALE_REVIEW: the object changed since the reviewer saw it' USING ERRCODE = 'serialization_failure';
  END IF;

  IF p_decision IN ('APPROVE', 'REJECT') THEN
    IF v_status <> 'REVIEW' THEN
      RAISE EXCEPTION 'CF_NOT_IN_REVIEW: % % is %', v_type, p_object_id, v_status USING ERRCODE = 'check_violation';
    END IF;
    v_target := CASE p_decision WHEN 'APPROVE' THEN 'APPROVED' ELSE 'REJECTED' END;
  ELSE -- REVOKE
    IF v_status <> 'APPROVED' THEN
      RAISE EXCEPTION 'CF_NOTHING_TO_REVOKE: % % is %', v_type, p_object_id, v_status USING ERRCODE = 'check_violation';
    END IF;
    SELECT gate_decision_id INTO v_supersedes FROM cf.v_effective_gate_decisions
     WHERE gate = p_gate AND object_id = p_object_id AND decision = 'APPROVE';
    v_target := 'RETIRED';
  END IF;

  INSERT INTO cf.gate_decisions (gate, object_type, object_id, object_content_sha256, decision, reviewer_id,
                                 notes, approved_platforms, supersedes_gate_decision_id, idempotency_key, surface)
  VALUES (p_gate, v_type, p_object_id, v_sha, p_decision, p_reviewer_id,
          p_notes, p_approved_platforms, v_supersedes, p_idempotency_key, p_surface)
  RETURNING gate_decision_id INTO v_id;

  -- The status trigger re-checks that this decision exists and is effective.
  -- (A REVOKE supersedes the APPROVE; the REVOKE row itself is the effective decision.)
  EXECUTE format('UPDATE cf.%I SET status = $1 WHERE %I = $2', v_table, v_pk) USING v_target, p_object_id;

  RETURN v_id;
END $$;

-- -----------------------------------------------------------------------------
-- 13. Derived views (read-only; agents read these, never compute permission)
-- -----------------------------------------------------------------------------

-- Publication status for a scene is DERIVED, never stored on the scene.
CREATE VIEW cf.v_scene_publication_status AS
SELECT s.scene_id,
       CASE WHEN EXISTS (
              SELECT 1
              FROM cf.publication_source_items i
              JOIN cf.publication_source_packages p ON p.source_package_id = i.source_package_id
              WHERE i.scene_id = s.scene_id AND p.status = 'APPROVED')
            THEN 'IN_G3_APPROVED_PACKAGE'
            ELSE 'UNKNOWN'
       END AS publication_source_status
FROM cf.anime_scene_intelligence s;
COMMENT ON VIEW cf.v_scene_publication_status IS
  'IN_G3_APPROVED_PACKAGE means a human approved a package that includes material for this scene, for that one script only. It is not a general licence for the scene.';

-- What CF-008 is allowed to publish: G4-approved render, whose manifest is READY,
-- whose package is G3-approved and whose script is G2-approved, and the global flag is on.
CREATE VIEW cf.v_publish_eligibility AS
SELECT r.render_id,
       d.gate_decision_id AS g4_decision_id,
       d.approved_platforms,
       (SELECT enabled FROM cf.system_flags WHERE flag_key = 'PUBLISH_ENABLED') IS TRUE AS publish_enabled
FROM cf.renders r
JOIN cf.production_manifests m ON m.production_manifest_id = r.production_manifest_id
JOIN cf.publication_source_packages p ON p.source_package_id = m.source_package_id
JOIN cf.content_scripts s ON s.script_id = m.script_id
JOIN cf.v_effective_gate_decisions d
  ON d.gate = 'G4' AND d.object_id = r.render_id AND d.decision = 'APPROVE' AND d.object_content_sha256 = r.content_sha256
WHERE r.status = 'APPROVED'
  AND m.status = 'READY'
  AND p.status = 'APPROVED'
  AND s.status = 'APPROVED'
  AND p.script_id = s.script_id;

-- -----------------------------------------------------------------------------
-- 14. Roles and privileges (revised 2026-10-07, ADR-001)
-- -----------------------------------------------------------------------------
-- cf_n8n_runtime: the n8n login role for CF-001..CF-009. Created by the
--                 provisioning step BEFORE any migration as LOGIN NOINHERIT
--                 NOBYPASSRLS NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION,
--                 with no password until a human sets it. Can write agent
--                 tables; cannot write gate_decisions, reviewers, system_flags
--                 or allowed_transitions; cannot execute record_gate_decision.
-- cf_governance : the human governance surface. Can execute
--                 record_gate_decision only. Unchanged; which login uses it is
--                 decision D-GOV-2.
--
-- Changed from Sprint 0: the NOLOGIN group role cf_agent is gone. A NOINHERIT
-- login role does not receive a group role's privileges, so its grants now go
-- directly to cf_n8n_runtime. The privilege set is the one cf_agent had.
-- Sprint 0 also described a cf_owner role that this file never created; objects
-- are owned by the role that applies the migration (`postgres` on Supabase).
--
-- Supabase service_role bypasses all of this; CF workflows must NOT use the
-- service-role key (and must never reuse the YouTube Kids credentials).

DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'cf_n8n_runtime') THEN
    RAISE EXCEPTION 'CF_PRECONDITION: role cf_n8n_runtime must be provisioned before this migration';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'cf_governance') THEN CREATE ROLE cf_governance NOLOGIN; END IF;
END $$;

REVOKE ALL ON SCHEMA cf FROM PUBLIC;
REVOKE ALL ON ALL TABLES IN SCHEMA cf FROM PUBLIC;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA cf FROM PUBLIC;
GRANT USAGE ON SCHEMA cf TO cf_n8n_runtime, cf_governance;

GRANT SELECT ON ALL TABLES IN SCHEMA cf TO cf_n8n_runtime;
GRANT INSERT, UPDATE ON
  cf.agent_runs, cf.anime_franchises, cf.anime_titles, cf.anime_source_episodes,
  cf.research_candidates, cf.anime_scene_intelligence, cf.editorial_opportunities,
  cf.content_scripts, cf.publication_source_packages, cf.production_manifests,
  cf.production_jobs, cf.content_assets, cf.renders, cf.published_content, cf.platform_posts
  TO cf_n8n_runtime;
GRANT INSERT ON
  cf.editorial_opportunity_scenes, cf.publication_source_items,
  cf.performance_snapshots, cf.content_learning_log
  TO cf_n8n_runtime;
-- Deliberately absent for cf_n8n_runtime: gate_decisions, reviewers, system_flags, allowed_transitions writes.

GRANT SELECT ON cf.reviewers, cf.v_effective_gate_decisions, cf.editorial_opportunities,
  cf.content_scripts, cf.publication_source_packages, cf.publication_source_items, cf.renders
  TO cf_governance;
GRANT EXECUTE ON FUNCTION cf.record_gate_decision(cf.gate_code, uuid, cf.gate_decision_value, uuid, text, text, text, cf.platform[], text)
  TO cf_governance;

-- Seed kill switches OFF.
INSERT INTO cf.system_flags (flag_key, enabled, notes) VALUES
  ('PUBLISH_ENABLED', false, 'Sprint 0 default. Only a reviewer may change this, per sprint and per item.'),
  ('PAID_CALLS_ENABLED', false, 'Sprint 0 default. Paid calls also need a per-run paid_authorisation_ref.'),
  ('SCHEDULES_ENABLED', false, 'No CF schedule may run until CF-000 owns scheduling and a human enables it.');

COMMIT;

-- =============================================================================
-- END — DESIGN ONLY — NOT APPLIED
-- =============================================================================
