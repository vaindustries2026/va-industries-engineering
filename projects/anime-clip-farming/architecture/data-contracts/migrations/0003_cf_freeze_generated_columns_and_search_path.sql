-- =============================================================================
-- V&A Anime Clip Farming / Engine 2 — migration 0003_cf_freeze_generated_columns_and_search_path
-- =============================================================================
-- Target:  Supabase project "V&A Anime Clip Farming — Engine 2",
--          ref mkeldytatorxxszjdngt, region eu-north-1. No other project.
--          Section 0 aborts on any database that is not that project, or on
--          one where 0001 / 0002 are missing or have been changed.
-- Apply:   only after an explicit human / Company Brain approval, after
--          0001_cf_sprint01 and 0002_cf_runtime_human_admin_guard are applied
--          and verified. Status and evidence live outside this file.
-- Decision: Company Brain, 2026-10-07, findings F-6 and F-7 (ADR-003).
-- Change 1 (F-6): cf.freeze_after_first_status() no longer compares
--          PostgreSQL generated columns. They are read from the catalog
--          (pg_attribute.attgenerated) for the triggering relation, not
--          hard-coded, and removed from the OLD/NEW comparison. A generated
--          column such as anime_titles.era_decade is not computed in NEW during
--          a BEFORE trigger, so the old comparison raised CF_IMMUTABLE_ROW on
--          every status change of a dated title after DRAFT. Unchanged: status
--          and updated_at stay excluded, the TG_ARGV mutable-column arguments
--          stay, and every ordinary content column stays frozen.
-- Change 2 (F-7): search_path = pg_catalog, cf is pinned on all four cf
--          functions (guard_status_transition, freeze_after_first_status,
--          forbid_delete, touch_updated_at). No public, no "$user". All four stay
--          SECURITY INVOKER, owned by postgres, with no EXECUTE grants.
-- Not rewritten: cf.guard_status_transition(), cf.forbid_delete() and
--          cf.touch_updated_at() only get ALTER FUNCTION ... SET search_path, so
--          their bodies keep their approved md5 values. The 0002 HUMAN_ADMIN block
--          (CF_GOVERNANCE_DENIED, SQLSTATE 42501, session_user / current_user =
--          cf_n8n_runtime) is therefore retained byte for byte.
-- Unchanged: 0001 and 0002 files and hashes; tables, types, triggers, the
--          allowed_transitions rows, every role, attribute and privilege.
-- No BEGIN/COMMIT of its own: apply it as one migration. Undo with
--          0003_cf_freeze_generated_columns_and_search_path.ROLLBACK.sql.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 0. Target and precondition guard
-- -----------------------------------------------------------------------------
DO $$
DECLARE
  r     pg_roles%ROWTYPE;
  f     record;
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
  IF to_regclass('cf.allowed_transitions') IS NULL THEN
    RAISE EXCEPTION 'CF_PRECONDITION: migration 0001_cf_sprint01 is not applied (cf.allowed_transitions is missing)';
  END IF;
  FOR f IN SELECT * FROM (VALUES
      ('cf.guard_status_transition()',    '0dac745af135d4772111d92fd2b168c9'),
      ('cf.freeze_after_first_status()',  'e4b4d9c63cc9870d5f59ab09e5dfe2c1'),
      ('cf.forbid_delete()',              '4097ad56aa56e6835ce9d375769fc6ba'),
      ('cf.touch_updated_at()',           'c28bbd99ced3dfcd7ff6c2a1298a90e1')) AS t(fn, expected_md5)
  LOOP
    IF to_regprocedure(f.fn) IS NULL THEN
      RAISE EXCEPTION 'CF_PRECONDITION: % is missing', f.fn;
    END IF;
    IF position('attgenerated' IN (SELECT prosrc FROM pg_proc WHERE oid = to_regprocedure(f.fn))) > 0
       OR (SELECT proconfig FROM pg_proc WHERE oid = to_regprocedure(f.fn)) IS NOT NULL THEN
      RAISE EXCEPTION 'CF_ALREADY_APPLIED: % already has the 0003 changes', f.fn;
    END IF;
    IF md5((SELECT prosrc FROM pg_proc WHERE oid = to_regprocedure(f.fn))) <> f.expected_md5 THEN
      RAISE EXCEPTION 'CF_PRECONDITION: % differs from the approved 0001/0002 version; stopping before changing it', f.fn;
    END IF;
    IF (SELECT prosecdef OR proowner <> 'postgres'::regrole FROM pg_proc WHERE oid = to_regprocedure(f.fn)) THEN
      RAISE EXCEPTION 'CF_PRECONDITION: % must be SECURITY INVOKER and owned by postgres', f.fn;
    END IF;
  END LOOP;
END $$;

-- -----------------------------------------------------------------------------
-- 1. F-6: freeze function ignores generated columns (catalog-driven)
-- -----------------------------------------------------------------------------
-- Once a row has left its first status, only the listed columns may change.
-- TG_ARGV = mutable column names (status and updated_at are always mutable;
-- generated columns are never compared).
CREATE OR REPLACE FUNCTION cf.freeze_after_first_status() RETURNS trigger LANGUAGE plpgsql
SET search_path = pg_catalog, cf AS $$
DECLARE
  v_old jsonb := to_jsonb(OLD) - 'status' - 'updated_at';
  v_new jsonb := to_jsonb(NEW) - 'status' - 'updated_at';
  v_gen text[];
  i int;
BEGIN
  IF OLD.status::text IN ('IDEA', 'DRAFT') THEN
    RETURN NEW;
  END IF;
  -- Generated columns are computed from other columns and are not yet computed in NEW during a BEFORE
  -- trigger, so they are not compared; the source columns they derive from still are. Read from the catalog
  -- for the triggering relation, so any table bound to this function is covered.
  SELECT coalesce(array_agg(a.attname::text), ARRAY[]::text[]) INTO v_gen
    FROM pg_catalog.pg_attribute a
   WHERE a.attrelid = TG_RELID AND a.attnum > 0 AND NOT a.attisdropped AND a.attgenerated <> '';
  v_old := v_old - v_gen;
  v_new := v_new - v_gen;
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

-- -----------------------------------------------------------------------------
-- 2. F-7: pin search_path on the other three functions (bodies untouched)
-- -----------------------------------------------------------------------------
ALTER FUNCTION cf.guard_status_transition() SET search_path = pg_catalog, cf;
ALTER FUNCTION cf.forbid_delete()           SET search_path = pg_catalog, cf;
ALTER FUNCTION cf.touch_updated_at()        SET search_path = pg_catalog, cf;

-- -----------------------------------------------------------------------------
-- 3. In-migration self-check: the transaction aborts if the result is not exact
-- -----------------------------------------------------------------------------
DO $$
DECLARE
  f record;
BEGIN
  FOR f IN SELECT p.proname, p.prosecdef, p.proowner, p.proconfig, p.proacl
             FROM pg_proc p WHERE p.pronamespace = 'cf'::regnamespace LOOP
    IF f.prosecdef OR f.proowner <> 'postgres'::regrole
       OR f.proconfig IS DISTINCT FROM ARRAY['search_path=pg_catalog, cf']
       OR EXISTS (SELECT 1 FROM aclexplode(coalesce(f.proacl, acldefault('f', f.proowner))) a WHERE a.grantee <> f.proowner) THEN
      RAISE EXCEPTION 'CF_POSTCHECK: cf.% is not SECURITY INVOKER, postgres-owned, grant-free and search_path-pinned', f.proname;
    END IF;
  END LOOP;
  IF (SELECT count(*) FROM pg_proc WHERE pronamespace = 'cf'::regnamespace) <> 4 THEN
    RAISE EXCEPTION 'CF_POSTCHECK: the cf schema must hold exactly the four functions';
  END IF;
  IF md5((SELECT prosrc FROM pg_proc WHERE oid = to_regprocedure('cf.freeze_after_first_status()'))) <> 'f957a25df6e08a74a21b6a64e5181a47' THEN
    RAISE EXCEPTION 'CF_POSTCHECK: freeze function body is not the approved 0003 body';
  END IF;
END $$;

-- =============================================================================
-- END — 0003_cf_freeze_generated_columns_and_search_path
-- =============================================================================
