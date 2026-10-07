#!/usr/bin/env python3
"""Builds 0002_cf_runtime_human_admin_guard.sql, its ROLLBACK and VERIFY from the
approved 0001_cf_sprint01.sql, so the guard function body cannot drift by hand-editing.

0002 replaces exactly one object, cf.guard_status_transition(). The new body is the
approved 0001 body plus one inserted block. The script prints the md5 values that the
migration, rollback and verification files embed.
"""
import hashlib
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2] / "architecture" / "data-contracts" / "migrations"
S1 = (ROOT / "0001_cf_sprint01.sql").read_text(encoding="utf-8")

START = "CREATE FUNCTION cf.guard_status_transition() RETURNS trigger LANGUAGE plpgsql AS $$"
i = S1.index(START) + len(START)
j = S1.index("$$;", i)
body0 = S1[i:j]  # exactly what pg_proc.prosrc holds after 0001
assert body0.endswith("END "), repr(body0[-20:])

ANCHOR = """  IF NOT FOUND THEN
    RAISE EXCEPTION 'CF_INVALID_TRANSITION: % % -> % is not allowed', v_object_type, v_from, v_to
      USING ERRCODE = 'check_violation';
  END IF;
"""
INSERT = """
  -- HUMAN_ADMIN edges are for a human or admin session. The n8n runtime role
  -- fails closed here, whatever table privileges it holds. HUMAN_GATE edges are
  -- not affected: they depend on a persisted gate decision, checked below.
  IF v_rule.mode = 'HUMAN_ADMIN'
     AND (session_user = 'cf_n8n_runtime' OR current_user = 'cf_n8n_runtime') THEN
    RAISE EXCEPTION 'CF_GOVERNANCE_DENIED: % % -> % is a HUMAN_ADMIN transition; the n8n runtime role may not perform it',
      v_object_type, v_from, v_to
      USING ERRCODE = 'insufficient_privilege',
            HINT = 'A human or admin session performs this transition outside the n8n runtime.';
  END IF;
"""
assert body0.count(ANCHOR) == 1
body1 = body0.replace(ANCHOR, ANCHOR + INSERT)

md5_0 = hashlib.md5(body0.encode("utf-8")).hexdigest()
md5_1 = hashlib.md5(body1.encode("utf-8")).hexdigest()

COMMON_GUARD = """  SELECT * INTO r FROM pg_roles WHERE rolname = 'cf_n8n_runtime';
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

MIGRATION = f"""-- =============================================================================
-- V&A Anime Clip Farming / Engine 2 — migration 0002_cf_runtime_human_admin_guard
-- =============================================================================
-- Target:  Supabase project "V&A Anime Clip Farming — Engine 2",
--          ref mkeldytatorxxszjdngt, region eu-north-1. No other project.
--          Section 0 aborts on any database that is not that project, or on
--          one where 0001_cf_sprint01 is missing or has been changed.
-- Apply:   only after an explicit human / Company Brain approval that names
--          this file and its sha256, after 0001_cf_sprint01 is applied and
--          verified. Status and evidence live outside this file.
-- Decision: Company Brain, 2026-10-07, finding F-2 (ADR-002). The runtime role
--          cf_n8n_runtime must not be able to perform a transition whose
--          cf.allowed_transitions.mode is HUMAN_ADMIN, even though it holds
--          UPDATE on the lifecycle tables.
-- Change:  replaces exactly one object, cf.guard_status_transition(). The new
--          body is the approved 0001 body (md5 {md5_0}) plus one
--          block that raises CF_GOVERNANCE_DENIED (SQLSTATE 42501) when the
--          edge is HUMAN_ADMIN and session_user or current_user is
--          cf_n8n_runtime. Everything else in the function is unchanged.
-- Unchanged: 0001_cf_sprint01.sql and its sha256; tables, types, triggers,
--          allowed_transitions rows, privileges of every role; DETERMINISTIC
--          edges and research-candidate lifecycle; HUMAN_GATE handling. No
--          privilege is added or removed. CREATE OR REPLACE keeps the owner,
--          the (empty) execute list and the trigger bindings.
-- Carry-forward: any later migration that replaces cf.guard_status_transition()
--          must keep the HUMAN_ADMIN block, or the F-2 protection is lost.
--          0002_cf_runtime_human_admin_guard.VERIFY.sql checks for it.
-- Admin path: a human or admin session (postgres, supabase_admin, a dashboard
--          SQL session) is not cf_n8n_runtime, so HUMAN_ADMIN edges still work
--          for it. The check is by identity, not by role membership: postgres
--          holds an ADMIN-only grant on cf_n8n_runtime, which must not block it.
-- No BEGIN/COMMIT of its own: apply it as one migration. Undo with
--          0002_cf_runtime_human_admin_guard.ROLLBACK.sql.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 0. Target and precondition guard
-- -----------------------------------------------------------------------------
DO $$
DECLARE
  r     pg_roles%ROWTYPE;
  v_src text;
BEGIN
{COMMON_GUARD}  IF to_regclass('cf.allowed_transitions') IS NULL THEN
    RAISE EXCEPTION 'CF_PRECONDITION: migration 0001_cf_sprint01 is not applied (cf.allowed_transitions is missing)';
  END IF;
  SELECT prosrc INTO v_src FROM pg_proc WHERE oid = to_regprocedure('cf.guard_status_transition()');
  IF v_src IS NULL THEN
    RAISE EXCEPTION 'CF_PRECONDITION: cf.guard_status_transition() is missing';
  END IF;
  IF position('CF_GOVERNANCE_DENIED' IN v_src) > 0 THEN
    RAISE EXCEPTION 'CF_ALREADY_APPLIED: cf.guard_status_transition() already has the HUMAN_ADMIN block';
  END IF;
  IF md5(v_src) <> '{md5_0}' THEN
    RAISE EXCEPTION 'CF_PRECONDITION: cf.guard_status_transition() differs from the approved 0001 version; stopping before replacing it';
  END IF;
END $$;

-- -----------------------------------------------------------------------------
-- 1. The guard function: approved 0001 body plus the HUMAN_ADMIN block
-- -----------------------------------------------------------------------------
-- Rejects any status change that is not an allowed edge, any HUMAN_ADMIN edge
-- made by the n8n runtime role, and any edge that needs a human gate without an
-- effective matching gate decision for this exact object ID and content hash.
-- TG_ARGV[0] = object_type, TG_ARGV[1] = primary-key column name.
CREATE OR REPLACE FUNCTION cf.guard_status_transition() RETURNS trigger LANGUAGE plpgsql AS $${body1}$$;

-- =============================================================================
-- END — 0002_cf_runtime_human_admin_guard
-- =============================================================================
"""

ROLLBACK = f"""-- =============================================================================
-- V&A Anime Clip Farming / Engine 2 — rollback for 0002_cf_runtime_human_admin_guard
-- =============================================================================
-- Target:  the dedicated project mkeldytatorxxszjdngt only.
-- Effect:  puts cf.guard_status_transition() back to the approved 0001 body
--          (md5 {md5_0}) and removes the cf_runtime_human_admin_guard
--          migration-history row. After it, the runtime role can again make
--          HUMAN_ADMIN transitions (finding F-2), so run it only to undo a
--          faulty 0002, and with explicit human approval.
-- Fails closed: stops if the function is neither the 0002 version nor missing
--          the marker, so it never overwrites an unknown function.
-- =============================================================================

DO $$
DECLARE
  v_src text;
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
  SELECT prosrc INTO v_src FROM pg_proc WHERE oid = to_regprocedure('cf.guard_status_transition()');
  IF v_src IS NULL THEN
    RAISE EXCEPTION 'CF_PRECONDITION: cf.guard_status_transition() is missing';
  END IF;
  IF md5(v_src) = '{md5_0}' THEN
    RAISE EXCEPTION 'CF_PRECONDITION: cf.guard_status_transition() is already the 0001 version; nothing to roll back';
  END IF;
  IF md5(v_src) <> '{md5_1}' THEN
    RAISE EXCEPTION 'CF_PRECONDITION: cf.guard_status_transition() is neither the 0001 nor the 0002 version; stopping';
  END IF;
END $$;

CREATE OR REPLACE FUNCTION cf.guard_status_transition() RETURNS trigger LANGUAGE plpgsql AS $${body0}$$;

DO $$
BEGIN
  IF to_regclass('supabase_migrations.schema_migrations') IS NOT NULL THEN
    DELETE FROM supabase_migrations.schema_migrations WHERE name = 'cf_runtime_human_admin_guard';
  END IF;
END $$;

-- =============================================================================
-- END — rollback for 0002_cf_runtime_human_admin_guard
-- =============================================================================
"""

(ROOT / "0002_cf_runtime_human_admin_guard.sql").write_text(MIGRATION, encoding="utf-8")
(ROOT / "0002_cf_runtime_human_admin_guard.ROLLBACK.sql").write_text(ROLLBACK, encoding="utf-8")
print("md5 0001 body:", md5_0)
print("md5 0002 body:", md5_1)
for n in ("0002_cf_runtime_human_admin_guard.sql", "0002_cf_runtime_human_admin_guard.ROLLBACK.sql"):
    print(hashlib.sha256((ROOT / n).read_bytes()).hexdigest(), n)
sys.exit(0)
