-- =============================================================================
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
--          body is the approved 0001 body (md5 eb7450cc84bc9e3d8c4ae4cd7d9187e3) plus one
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
  SELECT prosrc INTO v_src FROM pg_proc WHERE oid = to_regprocedure('cf.guard_status_transition()');
  IF v_src IS NULL THEN
    RAISE EXCEPTION 'CF_PRECONDITION: cf.guard_status_transition() is missing';
  END IF;
  IF position('CF_GOVERNANCE_DENIED' IN v_src) > 0 THEN
    RAISE EXCEPTION 'CF_ALREADY_APPLIED: cf.guard_status_transition() already has the HUMAN_ADMIN block';
  END IF;
  IF md5(v_src) <> 'eb7450cc84bc9e3d8c4ae4cd7d9187e3' THEN
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
CREATE OR REPLACE FUNCTION cf.guard_status_transition() RETURNS trigger LANGUAGE plpgsql AS $$
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

-- =============================================================================
-- END — 0002_cf_runtime_human_admin_guard
-- =============================================================================
