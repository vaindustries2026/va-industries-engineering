-- =============================================================================
-- V&A Anime Clip Farming / Engine 2 — migration 0004_cf002_scene_intelligence
-- =============================================================================
-- Target:  Supabase project "V&A Anime Clip Farming — Engine 2",
--          ref mkeldytatorxxszjdngt, region eu-north-1. No other project.
--          Section 0 aborts on any database that is not that project, on
--          drift in 0001-0003, or when 0004 is already applied.
-- Apply:   only after the local migration tests pass (evidence/cf-002-tools).
--          Status and evidence live outside this file.
-- Source:  object-for-object subset of the accepted Sprint 0 design
--          migrations-draft/0001_cf_backbone.DESIGN_ONLY.sql, limited to what
--          CF-002 (Scene Intelligence & Provenance) needs:
--            cf.research_access_basis, cf.anime_source_episodes,
--            cf.anime_scene_intelligence, their 11 allowed_transitions rows,
--            the same guard / freeze / no-delete / touch triggers as CF-001.
-- Deliberate differences from the design (documented in ADR-004):
--   1. cf.anime_scene_intelligence.research_observed_at (NOT NULL) and
--      research_observer (nullable) are added: the brief requires an
--      observation timestamp and the design has no column for it.
--   2. Consistency is enforced by foreign keys, not by convention:
--      scenes (source_episode_id, anime_title_id) -> episodes, and
--      scenes (research_candidate_id, anime_title_id) -> research_candidates
--      through a new UNIQUE INDEX on research_candidates (a pure index on the
--      CF-001 table; no column, trigger or privilege change).
--   3. Copyright-minimal storage limits as CHECK constraints (summary and
--      reason <= 800 chars, <= 8 angles, <= 30 characters) and a CHECK that
--      research_source_reference carries no credential-like material.
--   4. cf.v_scene_publication_status is created now as a constant-UNKNOWN view.
--      The accepted design derives it from G3-approved packages, which do not
--      exist yet; CF-005's migration will CREATE OR REPLACE it. There is NO
--      publication or rights column on the scene (accepted contract).
--   5. Runtime UPDATE is column-level (status and the contract's mutable
--      columns only).
-- Runtime grants: SELECT on the two tables and the view; INSERT; column-level
--          UPDATE. No DELETE, TRUNCATE, REFERENCES, TRIGGER, CREATE, EXECUTE.
--          anon, authenticated, service_role and PUBLIC get nothing.
-- Unchanged: 0001-0003 files and hashes, every existing table, function,
--          trigger, role attribute and privilege, the 14 CF-001 transition rows,
--          the kill switches.
-- No BEGIN/COMMIT of its own: apply it as one migration. Undo with
--          0004_cf002_scene_intelligence.ROLLBACK.sql.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 0. Target and precondition guard
-- -----------------------------------------------------------------------------
DO $$
DECLARE
  r pg_roles%ROWTYPE;
  f record;
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
  IF to_regclass('cf.agent_runs') IS NULL OR to_regclass('cf.anime_franchises') IS NULL
     OR to_regclass('cf.anime_titles') IS NULL OR to_regclass('cf.research_candidates') IS NULL
     OR to_regclass('cf.allowed_transitions') IS NULL OR to_regclass('cf.system_flags') IS NULL THEN
    RAISE EXCEPTION 'CF_PRECONDITION: the accepted CF-001 tables (0001) are not all present';
  END IF;
  -- already applied?
  IF to_regclass('cf.anime_source_episodes') IS NOT NULL OR to_regclass('cf.anime_scene_intelligence') IS NOT NULL
     OR to_regtype('cf.research_access_basis') IS NOT NULL OR to_regclass('cf.v_scene_publication_status') IS NOT NULL THEN
    RAISE EXCEPTION 'CF_ALREADY_APPLIED: 0004 objects already exist';
  END IF;
  -- F-2 / F-6 / F-7: the four approved function bodies and pinned search paths must be intact
  FOR f IN SELECT * FROM (VALUES
      ('cf.guard_status_transition()',    '0dac745af135d4772111d92fd2b168c9'),
      ('cf.freeze_after_first_status()',  'f957a25df6e08a74a21b6a64e5181a47'),
      ('cf.forbid_delete()',              '4097ad56aa56e6835ce9d375769fc6ba'),
      ('cf.touch_updated_at()',           'c28bbd99ced3dfcd7ff6c2a1298a90e1')) AS t(fn, expected_md5)
  LOOP
    IF to_regprocedure(f.fn) IS NULL THEN
      RAISE EXCEPTION 'CF_PRECONDITION: % is missing', f.fn;
    END IF;
    IF md5((SELECT prosrc FROM pg_proc WHERE oid = to_regprocedure(f.fn))) <> f.expected_md5 THEN
      RAISE EXCEPTION 'CF_DRIFT: % differs from the approved 0002/0003 version; stopping before changing anything', f.fn;
    END IF;
    IF (SELECT proconfig FROM pg_proc WHERE oid = to_regprocedure(f.fn)) IS DISTINCT FROM ARRAY['search_path=pg_catalog, cf'] THEN
      RAISE EXCEPTION 'CF_DRIFT: % does not have search_path pinned to pg_catalog, cf (F-7)', f.fn;
    END IF;
    IF (SELECT prosecdef OR proowner <> 'postgres'::regrole FROM pg_proc WHERE oid = to_regprocedure(f.fn)) THEN
      RAISE EXCEPTION 'CF_DRIFT: % must be SECURITY INVOKER and owned by postgres', f.fn;
    END IF;
  END LOOP;
  IF position('CF_GOVERNANCE_DENIED' IN (SELECT prosrc FROM pg_proc WHERE oid = to_regprocedure('cf.guard_status_transition()'))) = 0 THEN
    RAISE EXCEPTION 'CF_DRIFT: the HUMAN_ADMIN runtime guard (F-2) is missing';
  END IF;
  IF (SELECT count(*) FROM cf.allowed_transitions) <> 14 THEN
    RAISE EXCEPTION 'CF_DRIFT: cf.allowed_transitions must hold exactly the 14 CF-001 rows';
  END IF;
  IF EXISTS (SELECT 1 FROM cf.system_flags WHERE enabled IS TRUE) THEN
    RAISE EXCEPTION 'CF_PRECONDITION: a kill switch is on; 0004 does not apply while any is enabled';
  END IF;
  IF (SELECT count(*) FROM pg_trigger t JOIN pg_class c ON c.oid = t.tgrelid
       WHERE c.relnamespace = 'cf'::regnamespace AND NOT t.tgisinternal AND t.tgenabled = 'O') <> 12 THEN
    RAISE EXCEPTION 'CF_DRIFT: expected exactly 12 enabled cf triggers';
  END IF;
END $$;

-- -----------------------------------------------------------------------------
-- 1. Vocabulary (design §1)
-- -----------------------------------------------------------------------------
CREATE TYPE cf.research_access_basis AS ENUM (
  'HUMAN_VIEWED_LICENSED_PLATFORM',   -- a person watched it on a legal service (e.g. Crunchyroll)
  'PUBLIC_OFFICIAL_UPLOAD',           -- rightsholder's own public upload (official channel)
  'PUBLIC_UPLOAD_OWNER_UNVERIFIED',   -- public upload whose owner is not verified
  'PRESS_OR_PROMO_KIT',
  'SECONDARY_REFERENCE'               -- wiki, database, article; no footage viewed
);
COMMENT ON TYPE cf.research_access_basis IS
  'How a person or system was able to OBSERVE a scene for research. It is never publication permission.';

-- -----------------------------------------------------------------------------
-- 2. Tables
-- -----------------------------------------------------------------------------
-- Pure index on the CF-001 table so scenes can bind (candidate, title) in a foreign key.
CREATE UNIQUE INDEX research_candidates_id_title_uq ON cf.research_candidates (research_candidate_id, anime_title_id);

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
  CONSTRAINT source_episode_natural_key UNIQUE (anime_title_id, season_number, episode_number, episode_variant),
  CONSTRAINT source_episode_id_title_uq UNIQUE (source_episode_id, anime_title_id)
);
COMMENT ON TABLE cf.anime_source_episodes IS
  'One episode/OVA/film segment of a title (the work, not a file). Identity is the UUID; the natural key is the dedupe rule.';

CREATE TABLE cf.anime_scene_intelligence (
  scene_id                        uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  source_episode_id               uuid NOT NULL,
  anime_title_id                  uuid NOT NULL,
  research_candidate_id           uuid,
  start_ms                        integer NOT NULL CHECK (start_ms >= 0),
  end_ms                          integer NOT NULL CHECK (end_ms <= 86400000),
  characters_present              text[] NOT NULL DEFAULT '{}' CHECK (cardinality(characters_present) <= 30),
  scene_summary                   text NOT NULL CHECK (length(btrim(scene_summary)) > 0 AND length(scene_summary) <= 800),
  scene_function                  text CHECK (length(scene_function) <= 300),
  why_scene_matters               text NOT NULL CHECK (length(btrim(why_scene_matters)) > 0 AND length(why_scene_matters) <= 800),
  possible_editorial_angles       text[] NOT NULL DEFAULT '{}' CHECK (cardinality(possible_editorial_angles) <= 8),
  context_requirement             text CHECK (length(context_requirement) <= 400),
  spoiler_level                   text NOT NULL CHECK (spoiler_level IN ('NONE', 'LOW', 'MEDIUM', 'HIGH')),
  visual_strength                 numeric(5,4) CHECK (visual_strength BETWEEN 0 AND 1),
  nostalgia_signal                numeric(5,4) CHECK (nostalgia_signal BETWEEN 0 AND 1),
  editorial_strength              text NOT NULL DEFAULT 'UNASSESSED'
                                  CHECK (editorial_strength IN ('EDITORIALLY_STRONG', 'EDITORIALLY_MODERATE', 'EDITORIALLY_WEAK', 'UNASSESSED')),
  -- RESEARCH source only. Nothing here grants or implies publication permission.
  research_source_platform        text NOT NULL CHECK (research_source_platform ~ '^[A-Z0-9_]{2,40}$'),
  research_source_reference       text NOT NULL
                                  CHECK (length(btrim(research_source_reference)) > 0 AND length(research_source_reference) <= 500
                                         AND research_source_reference !~* '(token=|session[_-]?id|cookie|auth=|authorization|passw|secret|api[_-]?key|signature=|sig=|x-amz-|expires=)'),
  research_access_basis           cf.research_access_basis NOT NULL,
  research_access_notes           text CHECK (length(research_access_notes) <= 500),
  research_observed_at            timestamptz NOT NULL,
  research_observer               text CHECK (length(research_observer) <= 80),
  timestamps_human_verified       boolean NOT NULL DEFAULT false,
  model_confidence                numeric(5,4) CHECK (model_confidence BETWEEN 0 AND 1),
  possible_duplicate_of_scene_id  uuid REFERENCES cf.anime_scene_intelligence(scene_id),
  supersedes_scene_id             uuid REFERENCES cf.anime_scene_intelligence(scene_id),
  dedupe_key                      text NOT NULL UNIQUE CHECK (dedupe_key ~ '^[0-9a-f]{64}$'),
  status                          cf.lifecycle_status NOT NULL DEFAULT 'DRAFT'
                                  CHECK (status IN ('DRAFT', 'READY', 'BLOCKED', 'REJECTED', 'RETIRED')),
  agent_run_id                    uuid NOT NULL REFERENCES cf.agent_runs(agent_run_id),
  agent_version                   text NOT NULL,
  prompt_version                  text,
  created_at                      timestamptz NOT NULL DEFAULT now(),
  updated_at                      timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT scene_positive_span CHECK (end_ms > start_ms),
  CONSTRAINT scene_episode_title_fk FOREIGN KEY (source_episode_id, anime_title_id)
    REFERENCES cf.anime_source_episodes (source_episode_id, anime_title_id),
  CONSTRAINT scene_candidate_title_fk FOREIGN KEY (research_candidate_id, anime_title_id)
    REFERENCES cf.research_candidates (research_candidate_id, anime_title_id)
);
COMMENT ON TABLE cf.anime_scene_intelligence IS
  'Research intelligence only. Publication status is NOT stored here; cf.v_scene_publication_status derives it. research_access_notes holds neutral research notes, never a rights determination.';
CREATE INDEX anime_scene_intelligence_title_status_ix ON cf.anime_scene_intelligence (anime_title_id, status);
CREATE INDEX anime_scene_intelligence_episode_start_ix ON cf.anime_scene_intelligence (source_episode_id, start_ms);

-- Publication status is DERIVED, never stored on the scene. Until CF-005 creates the G3 package
-- tables there is nothing that can make a scene anything but UNKNOWN.
CREATE VIEW cf.v_scene_publication_status AS
SELECT s.scene_id, 'UNKNOWN'::text AS publication_source_status
FROM cf.anime_scene_intelligence s;
COMMENT ON VIEW cf.v_scene_publication_status IS
  'v0.1 placeholder: every scene is UNKNOWN. CF-005 replaces it with the G3-package derivation. No agent can write this value.';

-- -----------------------------------------------------------------------------
-- 3. State machine as data (design §10: the episode and scene rows)
-- -----------------------------------------------------------------------------
INSERT INTO cf.allowed_transitions (object_type, from_status, to_status, required_gate, required_decision, mode) VALUES
  ('anime_source_episode', 'NEW', 'DRAFT', NULL, NULL, 'DETERMINISTIC'),
  ('anime_source_episode', 'DRAFT', 'READY', NULL, NULL, 'DETERMINISTIC'),
  ('anime_source_episode', 'DRAFT', 'BLOCKED', NULL, NULL, 'DETERMINISTIC'),
  ('anime_source_episode', 'BLOCKED', 'READY', NULL, NULL, 'HUMAN_ADMIN'),
  ('anime_source_episode', 'READY', 'RETIRED', NULL, NULL, 'HUMAN_ADMIN'),
  ('scene', 'NEW', 'DRAFT', NULL, NULL, 'DETERMINISTIC'),
  ('scene', 'DRAFT', 'READY', NULL, NULL, 'DETERMINISTIC'),
  ('scene', 'DRAFT', 'BLOCKED', NULL, NULL, 'DETERMINISTIC'),
  ('scene', 'DRAFT', 'REJECTED', NULL, NULL, 'HUMAN_ADMIN'),
  ('scene', 'BLOCKED', 'DRAFT', NULL, NULL, 'HUMAN_ADMIN'),
  ('scene', 'READY', 'RETIRED', NULL, NULL, 'HUMAN_ADMIN');

-- -----------------------------------------------------------------------------
-- 4. Triggers (same four per table as 0001)
-- -----------------------------------------------------------------------------
DO $$
DECLARE
  r record;
BEGIN
  FOR r IN SELECT * FROM (VALUES
    ('anime_source_episodes',    'anime_source_episode', 'source_episode_id', ARRAY['episode_title_display','duration_seconds']),
    ('anime_scene_intelligence', 'scene',                'scene_id',          ARRAY['timestamps_human_verified'])
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
-- 5. Privileges (direct grants to the NOINHERIT runtime role; nothing else)
-- -----------------------------------------------------------------------------
REVOKE ALL ON cf.anime_source_episodes, cf.anime_scene_intelligence, cf.v_scene_publication_status FROM PUBLIC;
REVOKE ALL ON cf.anime_source_episodes, cf.anime_scene_intelligence, cf.v_scene_publication_status FROM anon, authenticated, service_role;

GRANT SELECT ON cf.anime_source_episodes, cf.anime_scene_intelligence, cf.v_scene_publication_status TO cf_n8n_runtime;
GRANT INSERT ON cf.anime_source_episodes, cf.anime_scene_intelligence TO cf_n8n_runtime;
GRANT UPDATE (status, episode_title_display, duration_seconds) ON cf.anime_source_episodes TO cf_n8n_runtime;
GRANT UPDATE (status, timestamps_human_verified) ON cf.anime_scene_intelligence TO cf_n8n_runtime;

-- -----------------------------------------------------------------------------
-- 6. In-migration self-check: the transaction aborts if the result is not exact
-- -----------------------------------------------------------------------------
DO $$
BEGIN
  IF (SELECT count(*) FROM cf.allowed_transitions) <> 25 THEN
    RAISE EXCEPTION 'CF_POSTCHECK: expected 25 allowed_transitions rows (14 + 11)';
  END IF;
  IF (SELECT count(*) FROM pg_trigger t JOIN pg_class c ON c.oid = t.tgrelid
       WHERE c.relnamespace = 'cf'::regnamespace AND NOT t.tgisinternal AND t.tgenabled = 'O') <> 20 THEN
    RAISE EXCEPTION 'CF_POSTCHECK: expected 20 enabled cf triggers (12 + 8)';
  END IF;
  IF (SELECT count(*) FROM pg_proc WHERE pronamespace = 'cf'::regnamespace) <> 4 THEN
    RAISE EXCEPTION 'CF_POSTCHECK: the cf schema must still hold exactly the four functions';
  END IF;
  IF has_table_privilege('cf_n8n_runtime', 'cf.anime_scene_intelligence', 'DELETE')
     OR has_table_privilege('cf_n8n_runtime', 'cf.anime_scene_intelligence', 'TRUNCATE')
     OR has_table_privilege('cf_n8n_runtime', 'cf.anime_source_episodes', 'DELETE')
     OR has_table_privilege('cf_n8n_runtime', 'cf.anime_source_episodes', 'TRUNCATE')
     OR has_table_privilege('cf_n8n_runtime', 'cf.anime_scene_intelligence', 'REFERENCES')
     OR has_table_privilege('cf_n8n_runtime', 'cf.anime_scene_intelligence', 'TRIGGER') THEN
    RAISE EXCEPTION 'CF_POSTCHECK: runtime role has a privilege it must not have';
  END IF;
  IF has_table_privilege('anon', 'cf.anime_scene_intelligence', 'SELECT')
     OR has_table_privilege('authenticated', 'cf.anime_scene_intelligence', 'SELECT')
     OR has_table_privilege('service_role', 'cf.anime_scene_intelligence', 'SELECT')
     OR has_table_privilege('anon', 'cf.anime_source_episodes', 'SELECT')
     OR has_table_privilege('authenticated', 'cf.anime_source_episodes', 'SELECT')
     OR has_table_privilege('service_role', 'cf.anime_source_episodes', 'SELECT') THEN
    RAISE EXCEPTION 'CF_POSTCHECK: a Supabase API role can read the new tables';
  END IF;
END $$;

-- =============================================================================
-- END — 0004_cf002_scene_intelligence
-- =============================================================================
