-- =============================================================================
-- V&A Anime Clip Farming / Engine 2 — rollback for 0002_cf_runtime_human_admin_guard
-- =============================================================================
-- Target:  the dedicated project mkeldytatorxxszjdngt only.
-- Effect:  puts cf.guard_status_transition() back to the approved 0001 body
--          (md5 eb7450cc84bc9e3d8c4ae4cd7d9187e3) and removes the cf_runtime_human_admin_guard
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
  IF md5(v_src) = 'eb7450cc84bc9e3d8c4ae4cd7d9187e3' THEN
    RAISE EXCEPTION 'CF_PRECONDITION: cf.guard_status_transition() is already the 0001 version; nothing to roll back';
  END IF;
  IF md5(v_src) <> '0dac745af135d4772111d92fd2b168c9' THEN
    RAISE EXCEPTION 'CF_PRECONDITION: cf.guard_status_transition() is neither the 0001 nor the 0002 version; stopping';
  END IF;
END $$;

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

DO $$
BEGIN
  IF to_regclass('supabase_migrations.schema_migrations') IS NOT NULL THEN
    DELETE FROM supabase_migrations.schema_migrations WHERE name = 'cf_runtime_human_admin_guard';
  END IF;
END $$;

-- =============================================================================
-- END — rollback for 0002_cf_runtime_human_admin_guard
-- =============================================================================
