#!/usr/bin/env python3
"""Builds 0003_cf_freeze_generated_columns_and_search_path.sql and its ROLLBACK and VERIFY.

0003 replaces cf.freeze_after_first_status() (F-6: ignore generated columns, from the catalog) and pins
search_path on the four cf functions (F-7). The guard, touch and forbid bodies are NOT rewritten: their
search_path is set with ALTER FUNCTION, so their bodies keep their approved md5 values (the 0002 HUMAN_ADMIN
block is therefore retained byte for byte). The 0001 freeze body is extracted from the approved 0001 file so
that the rollback restores it exactly. Prints the md5 values the three files embed.
"""
import hashlib
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2] / "architecture" / "data-contracts" / "migrations"
S1 = (ROOT / "0001_cf_sprint01.sql").read_text(encoding="utf-8")


def body_of(name):
    start = f"CREATE FUNCTION cf.{name}() RETURNS trigger LANGUAGE plpgsql AS $$"
    i = S1.index(start) + len(start)
    return S1[i:S1.index("$$;", i)]


def md5(s):
    return hashlib.md5(s.encode("utf-8")).hexdigest()


freeze0 = body_of("freeze_after_first_status")
OLD_DECL = "  i int;\nBEGIN\n  IF OLD.status::text IN ('IDEA', 'DRAFT') THEN\n    RETURN NEW;\n  END IF;\n"
assert freeze0.count(OLD_DECL) == 1, "freeze anchor"
freeze1 = freeze0.replace(
    "  v_new jsonb := to_jsonb(NEW) - 'status' - 'updated_at';\n  i int;\n",
    "  v_new jsonb := to_jsonb(NEW) - 'status' - 'updated_at';\n  v_gen text[];\n  i int;\n")
freeze1 = freeze1.replace(
    "  IF TG_NARGS > 0 THEN\n",
    """  -- Generated columns are computed from other columns and are not yet computed in NEW during a BEFORE
  -- trigger, so they are not compared; the source columns they derive from still are. Read from the catalog
  -- for the triggering relation, so any table bound to this function is covered.
  SELECT coalesce(array_agg(a.attname::text), ARRAY[]::text[]) INTO v_gen
    FROM pg_catalog.pg_attribute a
   WHERE a.attrelid = TG_RELID AND a.attnum > 0 AND NOT a.attisdropped AND a.attgenerated <> '';
  v_old := v_old - v_gen;
  v_new := v_new - v_gen;
  IF TG_NARGS > 0 THEN
""", 1)
assert freeze1 != freeze0

M = {
    "guard": "0dac745af135d4772111d92fd2b168c9",   # 0002 body, unchanged by 0003
    "touch": md5(body_of("touch_updated_at")),
    "forbid": md5(body_of("forbid_delete")),
    "freeze0": md5(freeze0),
    "freeze1": md5(freeze1),
}
assert M["freeze0"] == "e4b4d9c63cc9870d5f59ab09e5dfe2c1", M
assert M["touch"] == "c28bbd99ced3dfcd7ff6c2a1298a90e1", M
assert M["forbid"] == "4097ad56aa56e6835ce9d375769fc6ba", M

GUARD = """  SELECT * INTO r FROM pg_roles WHERE rolname = 'cf_n8n_runtime';
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
"""

FUNCS = [("guard_status_transition", "guard"), ("freeze_after_first_status", None),
         ("forbid_delete", "forbid"), ("touch_updated_at", "touch")]

# ---------------------------------------------------------------- migration
mig = f"""-- =============================================================================
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
{GUARD}  IF to_regclass('cf.allowed_transitions') IS NULL THEN
    RAISE EXCEPTION 'CF_PRECONDITION: migration 0001_cf_sprint01 is not applied (cf.allowed_transitions is missing)';
  END IF;
  FOR f IN SELECT * FROM (VALUES
      ('cf.guard_status_transition()',    '{M["guard"]}'),
      ('cf.freeze_after_first_status()',  '{M["freeze0"]}'),
      ('cf.forbid_delete()',              '{M["forbid"]}'),
      ('cf.touch_updated_at()',           '{M["touch"]}')) AS t(fn, expected_md5)
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
SET search_path = pg_catalog, cf AS $$"""
mig += freeze1 + """$$;

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
  IF md5((SELECT prosrc FROM pg_proc WHERE oid = to_regprocedure('cf.freeze_after_first_status()'))) <> '""" + M["freeze1"] + """' THEN
    RAISE EXCEPTION 'CF_POSTCHECK: freeze function body is not the approved 0003 body';
  END IF;
END $$;

-- =============================================================================
-- END — 0003_cf_freeze_generated_columns_and_search_path
-- =============================================================================
"""

# ---------------------------------------------------------------- rollback
rb = f"""-- =============================================================================
-- V&A Anime Clip Farming / Engine 2 — rollback for 0003_cf_freeze_generated_columns_and_search_path
-- =============================================================================
-- Target:  the dedicated project mkeldytatorxxszjdngt only.
-- Effect:  restores the approved 0001 body of cf.freeze_after_first_status()
--          (md5 {M["freeze0"]}) and removes the search_path setting from all four cf
--          functions (proconfig back to NULL). The guard body (the 0002 version,
--          md5 {M["guard"]}) is never rewritten. After it, finding F-6 (dated
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
     OR md5((SELECT prosrc FROM pg_proc WHERE oid = to_regprocedure('cf.freeze_after_first_status()'))) <> '{M["freeze1"]}' THEN
    RAISE EXCEPTION 'CF_PRECONDITION: cf.freeze_after_first_status() is not the 0003 version; nothing to roll back or unknown function';
  END IF;
  IF to_regprocedure('cf.guard_status_transition()') IS NULL
     OR md5((SELECT prosrc FROM pg_proc WHERE oid = to_regprocedure('cf.guard_status_transition()'))) <> '{M["guard"]}' THEN
    RAISE EXCEPTION 'CF_PRECONDITION: cf.guard_status_transition() is not the 0002 version; stopping';
  END IF;
  IF to_regprocedure('cf.forbid_delete()') IS NULL
     OR md5((SELECT prosrc FROM pg_proc WHERE oid = to_regprocedure('cf.forbid_delete()'))) <> '{M["forbid"]}'
     OR to_regprocedure('cf.touch_updated_at()') IS NULL
     OR md5((SELECT prosrc FROM pg_proc WHERE oid = to_regprocedure('cf.touch_updated_at()'))) <> '{M["touch"]}' THEN
    RAISE EXCEPTION 'CF_PRECONDITION: cf.forbid_delete() or cf.touch_updated_at() is not the approved version; stopping';
  END IF;
END $$;

CREATE OR REPLACE FUNCTION cf.freeze_after_first_status() RETURNS trigger LANGUAGE plpgsql AS $$"""
rb += freeze0 + """$$;
ALTER FUNCTION cf.freeze_after_first_status() RESET search_path;
ALTER FUNCTION cf.guard_status_transition()   RESET search_path;
ALTER FUNCTION cf.forbid_delete()             RESET search_path;
ALTER FUNCTION cf.touch_updated_at()          RESET search_path;

DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_proc WHERE pronamespace = 'cf'::regnamespace AND proconfig IS NOT NULL)
     OR md5((SELECT prosrc FROM pg_proc WHERE oid = to_regprocedure('cf.freeze_after_first_status()'))) <> '""" + M["freeze0"] + """' THEN
    RAISE EXCEPTION 'CF_POSTCHECK: rollback did not restore the 0002 function state';
  END IF;
END $$;
"""

# ---------------------------------------------------------------- verify
ver = f"""-- =============================================================================
-- Read-only post-apply verification for 0003_cf_freeze_generated_columns_and_search_path
-- =============================================================================
-- Safe to run on mkeldytatorxxszjdngt right after the apply: one SELECT, no
-- writes. Every column must be true. Compares the live function bodies with the
-- bodies that passed the local tests. runtime_role_passwordless is expected to
-- turn false after the human sets the role password; every other column must
-- stay true. Needs to read pg_authid (the postgres role can on Supabase).
-- =============================================================================
SELECT
  (SELECT md5(prosrc) = '{M["freeze1"]}' AND position('attgenerated' IN prosrc) > 0
   FROM pg_proc WHERE oid = to_regprocedure('cf.freeze_after_first_status()'))
    AS freeze_function_is_0003_exact,
  (SELECT md5(prosrc) = '{M["guard"]}'
     AND position('CF_GOVERNANCE_DENIED' IN prosrc) > 0
     AND position('session_user = ''cf_n8n_runtime'' OR current_user = ''cf_n8n_runtime''' IN prosrc) > 0
   FROM pg_proc WHERE oid = to_regprocedure('cf.guard_status_transition()'))
    AS guard_body_is_0002_exact_with_human_admin_block,
  (SELECT md5(prosrc) = '{M["forbid"]}' FROM pg_proc WHERE oid = to_regprocedure('cf.forbid_delete()'))
  AND (SELECT md5(prosrc) = '{M["touch"]}' FROM pg_proc WHERE oid = to_regprocedure('cf.touch_updated_at()'))
    AS forbid_and_touch_bodies_unchanged,
  (SELECT count(*) = 4 AND bool_and(coalesce(proconfig = ARRAY['search_path=pg_catalog, cf'], false))
   FROM pg_proc WHERE pronamespace = 'cf'::regnamespace)
    AS all_four_search_paths_pinned_to_pg_catalog_cf,
  (SELECT bool_and(NOT prosecdef AND proowner = 'postgres'::regrole
                   AND NOT EXISTS (SELECT 1 FROM aclexplode(coalesce(proacl, acldefault('f', proowner))) a
                                   WHERE a.grantee <> proowner))
   FROM pg_proc WHERE pronamespace = 'cf'::regnamespace)
    AS all_four_invoker_owned_by_postgres_no_execute_grants,
  (SELECT count(*) FROM pg_trigger t JOIN pg_class c ON c.oid = t.tgrelid
    WHERE c.relnamespace = 'cf'::regnamespace AND NOT t.tgisinternal AND t.tgenabled = 'O') = 12
  AND (SELECT count(*) FROM pg_trigger t
        WHERE t.tgfoid = to_regprocedure('cf.guard_status_transition()') AND NOT t.tgisinternal) = 3
  AND (SELECT count(*) FROM pg_trigger t
        WHERE t.tgfoid = to_regprocedure('cf.freeze_after_first_status()') AND NOT t.tgisinternal) = 3
    AS triggers_bound_and_enabled,
  (SELECT array_agg(proname::text ORDER BY proname) FROM pg_proc WHERE pronamespace = 'cf'::regnamespace)
    = ARRAY['forbid_delete','freeze_after_first_status','guard_status_transition','touch_updated_at']
  AND (SELECT array_agg(relname::text ORDER BY relname) FROM pg_class
        WHERE relnamespace = 'cf'::regnamespace AND relkind IN ('r','p','v','m','f','S'))
    = ARRAY['agent_runs','allowed_transitions','anime_franchises','anime_titles','research_candidates','reviewers','system_flags']
    AS inventory_unchanged,
  (SELECT count(*) = 14
          AND md5(string_agg(concat_ws('|', object_type, from_status, to_status,
                coalesce(required_gate::text, ''), coalesce(required_decision::text, ''), mode), ';'
                ORDER BY object_type, from_status, to_status)) = '6ea6f7a4fafee461dc64345d400b648c'
   FROM cf.allowed_transitions)
    AS transition_rows_unchanged,
  (SELECT array_agg(a.attname::text ORDER BY a.attname) FROM pg_attribute a
    WHERE a.attrelid = 'cf.anime_titles'::regclass AND a.attnum > 0 AND NOT a.attisdropped AND a.attgenerated <> '')
    = ARRAY['era_decade']
    AS only_generated_column_is_era_decade,
  (SELECT rolcanlogin AND NOT rolinherit AND NOT rolbypassrls AND NOT rolsuper AND NOT rolcreatedb
          AND NOT rolcreaterole AND NOT rolreplication FROM pg_roles WHERE rolname = 'cf_n8n_runtime')
  AND NOT EXISTS (SELECT 1 FROM pg_auth_members WHERE member = 'cf_n8n_runtime'::regrole)
  AND NOT EXISTS (SELECT 1 FROM pg_class WHERE relowner = 'cf_n8n_runtime'::regrole)
    AS runtime_role_attributes_exact,
  (SELECT rolpassword IS NULL FROM pg_authid WHERE rolname = 'cf_n8n_runtime')
    AS runtime_role_passwordless,
  has_schema_privilege('cf_n8n_runtime', 'cf', 'USAGE')
  AND NOT has_schema_privilege('cf_n8n_runtime', 'cf', 'CREATE')
  AND NOT EXISTS (
        SELECT 1
        FROM pg_class c
        CROSS JOIN unnest(ARRAY['SELECT','INSERT','UPDATE','DELETE','TRUNCATE','REFERENCES','TRIGGER']) AS p(priv)
        WHERE c.relnamespace = 'cf'::regnamespace AND c.relkind = 'r'
          AND has_table_privilege('cf_n8n_runtime', c.oid, p.priv)
              <> (p.priv = 'SELECT'
                  OR (p.priv IN ('INSERT','UPDATE')
                      AND c.relname IN ('agent_runs','anime_franchises','anime_titles','research_candidates'))))
  AND NOT EXISTS (SELECT 1 FROM pg_proc WHERE pronamespace = 'cf'::regnamespace
                  AND has_function_privilege('cf_n8n_runtime', oid, 'EXECUTE'))
    AS runtime_privileges_exact,
  NOT EXISTS (
    SELECT 1 FROM pg_roles r
    WHERE r.rolname IN ('anon','authenticated','service_role')
      AND (has_schema_privilege(r.oid, 'cf', 'USAGE')
           OR EXISTS (SELECT 1 FROM pg_class c
                      CROSS JOIN unnest(ARRAY['SELECT','INSERT','UPDATE','DELETE','TRUNCATE']) AS p(priv)
                      WHERE c.relnamespace = 'cf'::regnamespace AND c.relkind = 'r'
                        AND has_table_privilege(r.oid, c.oid, p.priv))))
  AND NOT EXISTS (SELECT 1 FROM pg_class c, aclexplode(coalesce(c.relacl, acldefault('r', c.relowner))) a
                  WHERE c.relnamespace = 'cf'::regnamespace AND a.grantee = 0)
  AND NOT EXISTS (SELECT 1 FROM pg_proc f, aclexplode(coalesce(f.proacl, acldefault('f', f.proowner))) a
                  WHERE f.pronamespace = 'cf'::regnamespace AND a.grantee = 0)
    AS no_access_for_supabase_api_roles_or_public,
  NOT EXISTS (SELECT 1 FROM pg_constraint k JOIN pg_class r ON r.oid = k.confrelid
              WHERE k.connamespace = 'cf'::regnamespace AND k.contype = 'f' AND r.relnamespace <> 'cf'::regnamespace)
  AND NOT EXISTS (SELECT 1 FROM pg_proc WHERE pronamespace = 'cf'::regnamespace
                  AND (prosecdef OR prosrc ~* '\\m(public|auth|storage|vault|extensions|net|cron|graphql|graphql_public|realtime|pgbouncer|supabase_[a-z_]+)\\.'))
    AS no_cross_schema_refs,
  (SELECT count(*) FROM cf.agent_runs) + (SELECT count(*) FROM cf.anime_franchises) + (SELECT count(*) FROM cf.anime_titles)
  + (SELECT count(*) FROM cf.research_candidates) + (SELECT count(*) FROM cf.reviewers) = 0
    AS no_data_rows_left_behind;
"""

for name, text in [("0003_cf_freeze_generated_columns_and_search_path.sql", mig),
                   ("0003_cf_freeze_generated_columns_and_search_path.ROLLBACK.sql", rb),
                   ("0003_cf_freeze_generated_columns_and_search_path.VERIFY.sql", ver)]:
    (ROOT / name).write_text(text, encoding="utf-8")
    print(name, hashlib.sha256(text.encode()).hexdigest())
print(M)
