-- =============================================================================
-- V&A Anime Clip Farming / Engine 2 — rollback for 0003_cf_freeze_generated_columns_and_search_path
-- =============================================================================
-- Target:  the dedicated project mkeldytatorxxszjdngt only.
-- Effect:  restores the approved 0001 body of cf.freeze_after_first_status()
--          (md5 e4b4d9c63cc9870d5f59ab09e5dfe2c1) and removes the search_path setting from all four cf
--          functions (proconfig back to NULL). The guard body (the 0002 version,
--          md5 0dac745af135d4772111d92fd2b168c9) is never rewritten. After it, finding F-6 (dated
--          titles frozen) and F-7 (mutable search_path) are open again, so run it
--          only to undo a faulty 0003, and with explicit human approval. It does
--          not remove the migration-history row; the operator removes it
--          (supabase_migrations.schema_migrations, name
--          cf_freeze_generated_columns_and_search_path) with the rollback.
-- Fails closed: stops unless the four functions are exactly the 0003 state.
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
  IF to_regprocedure('cf.freeze_after_first_status()') IS NULL
     OR md5((SELECT prosrc FROM pg_proc WHERE oid = to_regprocedure('cf.freeze_after_first_status()'))) <> 'f957a25df6e08a74a21b6a64e5181a47' THEN
    RAISE EXCEPTION 'CF_PRECONDITION: cf.freeze_after_first_status() is not the 0003 version; nothing to roll back or unknown function';
  END IF;
  IF to_regprocedure('cf.guard_status_transition()') IS NULL
     OR md5((SELECT prosrc FROM pg_proc WHERE oid = to_regprocedure('cf.guard_status_transition()'))) <> '0dac745af135d4772111d92fd2b168c9' THEN
    RAISE EXCEPTION 'CF_PRECONDITION: cf.guard_status_transition() is not the 0002 version; stopping';
  END IF;
  IF to_regprocedure('cf.forbid_delete()') IS NULL
     OR md5((SELECT prosrc FROM pg_proc WHERE oid = to_regprocedure('cf.forbid_delete()'))) <> '4097ad56aa56e6835ce9d375769fc6ba'
     OR to_regprocedure('cf.touch_updated_at()') IS NULL
     OR md5((SELECT prosrc FROM pg_proc WHERE oid = to_regprocedure('cf.touch_updated_at()'))) <> 'c28bbd99ced3dfcd7ff6c2a1298a90e1' THEN
    RAISE EXCEPTION 'CF_PRECONDITION: cf.forbid_delete() or cf.touch_updated_at() is not the approved version; stopping';
  END IF;
END $$;

CREATE OR REPLACE FUNCTION cf.freeze_after_first_status() RETURNS trigger LANGUAGE plpgsql AS $$
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
ALTER FUNCTION cf.freeze_after_first_status() RESET search_path;
ALTER FUNCTION cf.guard_status_transition()   RESET search_path;
ALTER FUNCTION cf.forbid_delete()             RESET search_path;
ALTER FUNCTION cf.touch_updated_at()          RESET search_path;

DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_proc WHERE pronamespace = 'cf'::regnamespace AND proconfig IS NOT NULL)
     OR md5((SELECT prosrc FROM pg_proc WHERE oid = to_regprocedure('cf.freeze_after_first_status()'))) <> 'e4b4d9c63cc9870d5f59ab09e5dfe2c1' THEN
    RAISE EXCEPTION 'CF_POSTCHECK: rollback did not restore the 0002 function state';
  END IF;
END $$;
