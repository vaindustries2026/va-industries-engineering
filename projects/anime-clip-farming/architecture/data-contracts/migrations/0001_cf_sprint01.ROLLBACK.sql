-- =============================================================================
-- V&A Anime Clip Farming / Engine 2 — rollback for 0001_cf_sprint01
-- =============================================================================
-- Target:  the dedicated project mkeldytatorxxszjdngt only (same target guard as
--          the migration).
-- Effect:  removes exactly the objects 0001_cf_sprint01 creates, including any
--          rows CF-001 wrote, then its migration-history row. Safe after a
--          partial apply (every drop is IF EXISTS).
-- Fails closed: no CASCADE. If anything outside this list depends on these
--          objects or still lives in schema cf (for example a later migration),
--          the drop stops; roll back the later migration first.
-- Keeps:   role cf_n8n_runtime (a provisioning object; dropping it is a separate
--          human-approved step) and everything outside schema cf.
-- Run only with explicit human approval.
-- =============================================================================

DO $$
BEGIN
  IF to_regclass('public.episode_scripts') IS NOT NULL
     OR to_regclass('public.asset_registry') IS NOT NULL
     OR to_regclass('public.production_plans') IS NOT NULL
     OR to_regclass('public.videos') IS NOT NULL THEN
    RAISE EXCEPTION 'CF_WRONG_TARGET: YouTube Kids tables found; this is not the dedicated Engine 2 project';
  END IF;
  IF to_regrole('cf_n8n_runtime') IS NULL THEN
    RAISE EXCEPTION 'CF_WRONG_TARGET: role cf_n8n_runtime does not exist; it is provisioned only in the dedicated Engine 2 project';
  END IF;
END $$;

DROP TABLE IF EXISTS
  cf.research_candidates, cf.anime_titles, cf.anime_franchises,
  cf.system_flags, cf.agent_runs, cf.reviewers, cf.allowed_transitions;

DROP FUNCTION IF EXISTS
  cf.guard_status_transition(), cf.freeze_after_first_status(),
  cf.forbid_delete(), cf.touch_updated_at();

DROP TYPE IF EXISTS cf.lifecycle_status, cf.run_state, cf.gate_code, cf.gate_decision_value;

DROP SCHEMA IF EXISTS cf;

DO $$
BEGIN
  IF to_regclass('supabase_migrations.schema_migrations') IS NOT NULL THEN
    DELETE FROM supabase_migrations.schema_migrations WHERE name = 'cf_sprint01';
  END IF;
END $$;

-- =============================================================================
-- END — rollback for 0001_cf_sprint01
-- =============================================================================
