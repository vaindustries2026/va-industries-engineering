-- =============================================================================
-- V&A Anime Clip Farming / Engine 2 — Sprint 1 migration 0001_cf_sprint01
-- =============================================================================
-- Target:  Supabase project "V&A Anime Clip Farming — Engine 2",
--          ref mkeldytatorxxszjdngt, region eu-north-1. No other project.
--          Section 0 aborts on any database that is not that project.
-- Apply:   only after an explicit human / Company Brain approval that names
--          this file and its sha256. Status and evidence live outside this
--          file: evidence/PRE_SPRINT_01_MIGRATION_PREFLIGHT.md and the changelog.
-- Source:  object-for-object subset of the accepted Sprint 0 design
--          migrations-draft/0001_cf_backbone.DESIGN_ONLY.sql (commit 5190db5),
--          limited to SPRINT_00_ARCHITECTURE_REPORT.md §15. Every type, table,
--          seed row, function and trigger body below is copied unchanged.
--          Differences from §15 / the design, all deliberate:
--            1. cf.reviewers is included: cf.system_flags.changed_by_reviewer_id
--               references it, so system_flags cannot exist without it.
--            2. Section 0 target guard (new).
--            3. Section 7 grants go directly to cf_n8n_runtime (ADR-001); the
--               Sprint 0 group role cf_agent is not created, because the
--               runtime role is NOINHERIT and would not receive its grants.
--               The privilege set is cf_agent's, limited to these tables.
--            4. VALUES lists trimmed to the Sprint 1 object types.
-- Order:   provisioning already created cf_n8n_runtime (LOGIN NOINHERIT
--          NOBYPASSRLS NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION, no
--          password, no grants). This migration creates the objects as the
--          applying role (postgres) and then grants the runtime role only what
--          CF-001 needs. A human sets the role password and creates the n8n
--          credential separately; neither appears in this file.
-- Not here: episodes, scenes, editorial, scripts, gate decisions and
--          cf.record_gate_decision, source governance, production, publishing,
--          learning tables, views, cf_governance. Those need later migrations.
-- No BEGIN/COMMIT of its own: apply it as one migration. If an apply ever
-- stops part-way, 0001_cf_sprint01.ROLLBACK.sql removes whatever was created.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 0. Target guard (new): abort unless this is the dedicated Engine 2 project
-- -----------------------------------------------------------------------------
DO $$
DECLARE
  r pg_roles%ROWTYPE;
BEGIN
  SELECT * INTO r FROM pg_roles WHERE rolname = 'cf_n8n_runtime';
  IF NOT FOUND THEN
    RAISE EXCEPTION 'CF_WRONG_TARGET: role cf_n8n_runtime does not exist; it is provisioned only in the dedicated Engine 2 project';
  END IF;
  IF NOT r.rolcanlogin OR r.rolinherit OR r.rolbypassrls OR r.rolsuper
     OR r.rolcreatedb OR r.rolcreaterole OR r.rolreplication THEN
    RAISE EXCEPTION 'CF_WRONG_TARGET: cf_n8n_runtime must be LOGIN NOINHERIT NOBYPASSRLS NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION';
  END IF;
  IF EXISTS (SELECT 1 FROM pg_auth_members WHERE member = r.oid) THEN
    RAISE EXCEPTION 'CF_WRONG_TARGET: cf_n8n_runtime must not be a member of any role';
  END IF;
  IF to_regclass('public.episode_scripts') IS NOT NULL
     OR to_regclass('public.asset_registry') IS NOT NULL
     OR to_regclass('public.production_plans') IS NOT NULL
     OR to_regclass('public.videos') IS NOT NULL THEN
    RAISE EXCEPTION 'CF_WRONG_TARGET: YouTube Kids tables found; this is not the dedicated Engine 2 project';
  END IF;
  IF to_regnamespace('cf') IS NOT NULL THEN
    RAISE EXCEPTION 'CF_ALREADY_APPLIED: schema cf already exists';
  END IF;
END $$;

CREATE SCHEMA IF NOT EXISTS cf;
COMMENT ON SCHEMA cf IS 'V&A Anime Clip Farming / Engine 2 only. Never store YouTube Kids state here.';

-- -----------------------------------------------------------------------------
-- 1. Vocabularies (design §1: the four types §15 names)
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

-- -----------------------------------------------------------------------------
-- 2. Governance and operational tables (design §2)
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
-- 3. Reference identities (design §3, without anime_source_episodes)
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

-- -----------------------------------------------------------------------------
-- 4. Intelligence (design §4: CF-001 only)
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

-- -----------------------------------------------------------------------------
-- 5. State machine as data (design §10: rows for the three Sprint 1 object types)
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
  -- CF-001
  ('research_candidate', 'NEW', 'IDEA', NULL, NULL, 'DETERMINISTIC'),
  ('research_candidate', 'IDEA', 'READY', NULL, NULL, 'DETERMINISTIC'),
  ('research_candidate', 'IDEA', 'REJECTED', NULL, NULL, 'DETERMINISTIC'),
  ('research_candidate', 'READY', 'RETIRED', NULL, NULL, 'DETERMINISTIC');

-- -----------------------------------------------------------------------------
-- 6. Guard functions and triggers (design §11, without the append-only parts)
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

CREATE FUNCTION cf.forbid_delete() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'CF_NO_DELETE: %.% rows are retired, never deleted', TG_TABLE_SCHEMA, TG_TABLE_NAME
    USING ERRCODE = 'check_violation';
END $$;

-- Status guards, freeze rules, no-delete and updated_at on lifecycle tables
DO $$
DECLARE
  r record;
BEGIN
  FOR r IN SELECT * FROM (VALUES
    ('anime_franchises',            'anime_franchise',            'franchise_id',            ARRAY['display_name','anilist_franchise_ref']),
    ('anime_titles',                'anime_title',                'anime_title_id',          ARRAY['display_title','alt_titles','anilist_id','mal_id']),
    ('research_candidates',         'research_candidate',         'research_candidate_id',   ARRAY['rejection_reason'])
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
-- 7. Privileges (ADR-001: direct grants to the NOINHERIT runtime role)
-- -----------------------------------------------------------------------------
-- cf_n8n_runtime already exists (section 0 checked it). It gets exactly what the
-- Sprint 0 design gave cf_agent on these tables: read everything in cf, insert
-- and update the CF-001 tables. Deliberately absent: any write to reviewers,
-- system_flags or allowed_transitions; DELETE, TRUNCATE, REFERENCES or TRIGGER
-- anywhere; CREATE on the schema; EXECUTE on any cf function. No default
-- privileges are set, so later objects get nothing until a migration grants it.
-- Supabase's anon, authenticated and service_role get nothing on cf.

REVOKE ALL ON SCHEMA cf FROM PUBLIC;
REVOKE ALL ON ALL TABLES IN SCHEMA cf FROM PUBLIC;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA cf FROM PUBLIC;
GRANT USAGE ON SCHEMA cf TO cf_n8n_runtime;

GRANT SELECT ON ALL TABLES IN SCHEMA cf TO cf_n8n_runtime;
GRANT INSERT, UPDATE ON
  cf.agent_runs, cf.anime_franchises, cf.anime_titles, cf.research_candidates
  TO cf_n8n_runtime;

-- Seed kill switches OFF.
INSERT INTO cf.system_flags (flag_key, enabled, notes) VALUES
  ('PUBLISH_ENABLED', false, 'Sprint 0 default. Only a reviewer may change this, per sprint and per item.'),
  ('PAID_CALLS_ENABLED', false, 'Sprint 0 default. Paid calls also need a per-run paid_authorisation_ref.'),
  ('SCHEDULES_ENABLED', false, 'No CF schedule may run until CF-000 owns scheduling and a human enables it.');

-- =============================================================================
-- END — 0001_cf_sprint01
-- =============================================================================
