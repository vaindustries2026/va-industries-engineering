-- =============================================================================
-- LOCAL ONLY — tests for 0001_cf_sprint01.sql
-- =============================================================================
-- Run ONLY against a throwaway local PostgreSQL that mirrors the Supabase
-- set-up: a non-superuser `postgres` owner, roles anon / authenticated /
-- service_role, and cf_n8n_runtime created exactly as provisioning created it.
-- Never run against Supabase. All data is fictional fixture data.
--   (as postgres)  psql -v ON_ERROR_STOP=1 --single-transaction -f 0001_cf_sprint01.sql
--   (as superuser) psql -v ON_ERROR_STOP=1 -f 0001_cf_sprint01.TESTS.sql
-- Expected output: one "PASS <id>" notice per test and no "FAIL".
-- IDs starting T- repeat a Sprint 0 static test that still applies to the
-- Sprint 1 objects; IDs starting S1- are new for this migration.
-- =============================================================================

SET client_min_messages = warning;

CREATE SCHEMA cf_test;

CREATE OR REPLACE FUNCTION cf_test.expect_error(p_test text, p_sql text, p_expect text) RETURNS void
LANGUAGE plpgsql AS $$
BEGIN
  BEGIN
    EXECUTE p_sql;
  EXCEPTION WHEN others THEN
    IF position(p_expect IN SQLERRM) > 0 THEN
      RAISE NOTICE 'PASS %', p_test;
      RETURN;
    END IF;
    RAISE EXCEPTION 'FAIL % (wrong error: %)', p_test, SQLERRM;
  END;
  RAISE EXCEPTION 'FAIL % (statement succeeded but must fail)', p_test;
END $$;

CREATE OR REPLACE FUNCTION cf_test.expect_true(p_test text, p_cond boolean) RETURNS void
LANGUAGE plpgsql AS $$
BEGIN
  IF p_cond IS TRUE THEN RAISE NOTICE 'PASS %', p_test;
  ELSE RAISE EXCEPTION 'FAIL %', p_test; END IF;
END $$;

GRANT USAGE ON SCHEMA cf_test TO cf_n8n_runtime;

SET client_min_messages = notice;

-- ---------------------------------------------------------------------------
-- Catalog checks: inventory, isolation, privileges (run as the harness user)
-- ---------------------------------------------------------------------------
SELECT cf_test.expect_true('S1-ISO-01 cf holds exactly the Sprint 1 objects',
      (SELECT array_agg(relname::text ORDER BY relname) FROM pg_class
        WHERE relnamespace = 'cf'::regnamespace AND relkind IN ('r','p','v','m','f','S'))
    = ARRAY['agent_runs','allowed_transitions','anime_franchises','anime_titles','research_candidates','reviewers','system_flags']
  AND (SELECT array_agg(typname::text ORDER BY typname) FROM pg_type
        WHERE typnamespace = 'cf'::regnamespace AND typtype = 'e')
    = ARRAY['gate_code','gate_decision_value','lifecycle_status','run_state']
  AND (SELECT array_agg(proname::text ORDER BY proname) FROM pg_proc WHERE pronamespace = 'cf'::regnamespace)
    = ARRAY['forbid_delete','freeze_after_first_status','guard_status_transition','touch_updated_at']
  AND (SELECT count(*) FROM pg_trigger t JOIN pg_class c ON c.oid = t.tgrelid
        WHERE c.relnamespace = 'cf'::regnamespace AND NOT t.tgisinternal) = 12
  AND (SELECT count(*) FROM cf.allowed_transitions) = 14);

SELECT cf_test.expect_true('S1-ISO-02 every foreign key in cf points at a cf table',
  NOT EXISTS (SELECT 1 FROM pg_constraint k JOIN pg_class r ON r.oid = k.confrelid
              WHERE k.connamespace = 'cf'::regnamespace AND k.contype = 'f'
                AND r.relnamespace <> 'cf'::regnamespace));

SELECT cf_test.expect_true('S1-ISO-03 no cf function names another schema, none is SECURITY DEFINER',
  NOT EXISTS (SELECT 1 FROM pg_proc WHERE pronamespace = 'cf'::regnamespace
              AND (prosecdef OR prosrc ~* '\m(public|auth|storage|vault|extensions|net|cron|graphql|graphql_public|realtime|pgbouncer|supabase_[a-z_]+)\.')));

SELECT cf_test.expect_true('S1-ISO-04 cf columns use only built-in or cf types, and no cf object depends on an extension',
  NOT EXISTS (SELECT 1 FROM pg_attribute a JOIN pg_class c ON c.oid = a.attrelid JOIN pg_type t ON t.oid = a.atttypid
              WHERE c.relnamespace = 'cf'::regnamespace AND a.attnum > 0 AND NOT a.attisdropped
                AND t.typnamespace NOT IN ('pg_catalog'::regnamespace, 'cf'::regnamespace))
  AND NOT EXISTS (SELECT 1 FROM pg_depend d
                  WHERE d.refclassid = 'pg_extension'::regclass
                    AND ((d.classid = 'pg_class'::regclass AND d.objid IN (SELECT oid FROM pg_class WHERE relnamespace = 'cf'::regnamespace))
                      OR (d.classid = 'pg_proc'::regclass  AND d.objid IN (SELECT oid FROM pg_proc  WHERE pronamespace = 'cf'::regnamespace))
                      OR (d.classid = 'pg_type'::regclass  AND d.objid IN (SELECT oid FROM pg_type  WHERE typnamespace = 'cf'::regnamespace)))));

SELECT cf_test.expect_true('S1-ISO-05 cf_n8n_runtime is LOGIN NOINHERIT NOBYPASSRLS NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION and a member of nothing',
  (SELECT rolcanlogin AND NOT rolinherit AND NOT rolbypassrls AND NOT rolsuper AND NOT rolcreatedb
          AND NOT rolcreaterole AND NOT rolreplication FROM pg_roles WHERE rolname = 'cf_n8n_runtime')
  AND NOT EXISTS (SELECT 1 FROM pg_auth_members WHERE member = 'cf_n8n_runtime'::regrole)
  AND NOT EXISTS (SELECT 1 FROM pg_class WHERE relowner = 'cf_n8n_runtime'::regrole)
  AND NOT EXISTS (SELECT 1 FROM pg_namespace WHERE nspowner = 'cf_n8n_runtime'::regrole)
  AND NOT EXISTS (SELECT 1 FROM pg_proc WHERE proowner = 'cf_n8n_runtime'::regrole));

SELECT cf_test.expect_true('S1-PRIV-01 cf_n8n_runtime has exactly the designed privileges on cf',
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
                  AND has_function_privilege('cf_n8n_runtime', oid, 'EXECUTE')));

SELECT cf_test.expect_true('S1-PRIV-02 anon, authenticated and service_role get nothing in cf',
  NOT EXISTS (
    SELECT 1 FROM pg_roles r
    WHERE r.rolname IN ('anon','authenticated','service_role')
      AND (has_schema_privilege(r.oid, 'cf', 'USAGE')
           OR EXISTS (SELECT 1 FROM pg_class c
                      CROSS JOIN unnest(ARRAY['SELECT','INSERT','UPDATE','DELETE','TRUNCATE']) AS p(priv)
                      WHERE c.relnamespace = 'cf'::regnamespace AND c.relkind = 'r'
                        AND has_table_privilege(r.oid, c.oid, p.priv))))
  AND (SELECT count(*) FROM pg_roles WHERE rolname IN ('anon','authenticated','service_role')) = 3);

SELECT cf_test.expect_true('S1-PRIV-03 PUBLIC holds no privilege on any cf object',
  NOT EXISTS (SELECT 1 FROM pg_class c, aclexplode(coalesce(c.relacl, acldefault('r', c.relowner))) a
              WHERE c.relnamespace = 'cf'::regnamespace AND a.grantee = 0)
  AND NOT EXISTS (SELECT 1 FROM pg_proc f, aclexplode(coalesce(f.proacl, acldefault('f', f.proowner))) a
                  WHERE f.pronamespace = 'cf'::regnamespace AND a.grantee = 0)
  AND NOT EXISTS (SELECT 1 FROM pg_namespace n, aclexplode(coalesce(n.nspacl, acldefault('n', n.nspowner))) a
                  WHERE n.nspname = 'cf' AND a.grantee = 0));

SELECT cf_test.expect_true('S1-GATE-00 no gate objects yet and no Sprint 1 transition needs a gate',
  to_regclass('cf.gate_decisions') IS NULL
  AND NOT EXISTS (SELECT 1 FROM pg_proc WHERE proname = 'record_gate_decision')
  AND NOT EXISTS (SELECT 1 FROM cf.allowed_transitions WHERE required_gate IS NOT NULL OR mode = 'HUMAN_GATE'));

SELECT cf_test.expect_true('T-RIGHTS-01 no automated legal-determination column exists anywhere in cf',
  NOT EXISTS (SELECT 1 FROM information_schema.columns
              WHERE table_schema = 'cf' AND column_name ~* '(fair_?use|copyright_?safe|legal_?safe|is_legal|rights_?cleared)'));

SELECT cf_test.expect_true('T-PUB-01 all kill switches default OFF',
  (SELECT count(*) FROM cf.system_flags) = 3 AND NOT EXISTS (SELECT 1 FROM cf.system_flags WHERE enabled));

-- ---------------------------------------------------------------------------
-- As the n8n runtime role: the CF-001 write path works
-- ---------------------------------------------------------------------------
SET ROLE cf_n8n_runtime;

INSERT INTO cf.agent_runs (agent_run_id, agent_code, agent_version, idempotency_key, input_state_hash, run_state, started_at)
VALUES ('00000000-0000-4000-8000-0000000000a1', 'CF-001', 'fixture', 'run-key-1', 'h', 'RUNNING', now());

INSERT INTO cf.anime_franchises (franchise_id, normalised_key, display_name, agent_run_id) VALUES
  ('00000000-0000-4000-8000-0000000000f1', 'fixture franchise', 'Fixture Franchise', '00000000-0000-4000-8000-0000000000a1'),
  ('00000000-0000-4000-8000-0000000000f2', 'other franchise', 'Other Franchise', '00000000-0000-4000-8000-0000000000a1');

INSERT INTO cf.anime_titles (anime_title_id, franchise_id, normalised_title_key, display_title, start_year, anilist_id, agent_run_id)
VALUES ('00000000-0000-4000-8000-0000000000b1', '00000000-0000-4000-8000-0000000000f1', 'fixture title', 'Fixture Title', 2004, 999001,
        '00000000-0000-4000-8000-0000000000a1');

INSERT INTO cf.research_candidates (research_candidate_id, anime_title_id, franchise_id, topic_key, topic_display,
  content_lane, signal_evidence, observation_window, dedupe_key, agent_run_id, agent_version)
VALUES ('00000000-0000-4000-8000-0000000000c1', '00000000-0000-4000-8000-0000000000b1', '00000000-0000-4000-8000-0000000000f1',
  'fixture topic', 'Fixture topic', '2000s Nostalgia', '[{"source":"fixture","url":"https://example.invalid"}]', '2026-W41',
  'rc-dedupe-1', '00000000-0000-4000-8000-0000000000a1', 'fixture');

UPDATE cf.anime_franchises SET status = 'READY' WHERE franchise_id = '00000000-0000-4000-8000-0000000000f1';
UPDATE cf.anime_titles SET status = 'READY' WHERE anime_title_id = '00000000-0000-4000-8000-0000000000b1';
UPDATE cf.research_candidates SET status = 'READY' WHERE research_candidate_id = '00000000-0000-4000-8000-0000000000c1';
UPDATE cf.agent_runs SET run_state = 'SUCCEEDED', finished_at = now() WHERE agent_run_id = '00000000-0000-4000-8000-0000000000a1';

SELECT cf_test.expect_true('S1-RUN-01 cf_n8n_runtime can run the CF-001 write path (run, franchise, title, candidate, READY)',
  (SELECT run_state = 'SUCCEEDED' FROM cf.agent_runs WHERE agent_run_id = '00000000-0000-4000-8000-0000000000a1')
  AND (SELECT status = 'READY' FROM cf.research_candidates WHERE research_candidate_id = '00000000-0000-4000-8000-0000000000c1')
  AND (SELECT era_decade = 2000 FROM cf.anime_titles WHERE anime_title_id = '00000000-0000-4000-8000-0000000000b1'));

-- Identity / dedupe (Sprint 0 tests that apply to Sprint 1 tables)
SELECT cf_test.expect_error('T-ID-01 malformed UUID rejected',
  $$INSERT INTO cf.anime_titles (anime_title_id, franchise_id, normalised_title_key, display_title)
    VALUES ('not-a-uuid', '00000000-0000-4000-8000-0000000000f1', 'x', 'x')$$, 'invalid input syntax for type uuid');

SELECT cf_test.expect_error('T-ID-02 duplicate research candidate (same window) rejected',
  $$INSERT INTO cf.research_candidates (anime_title_id, franchise_id, topic_key, topic_display, content_lane,
      signal_evidence, observation_window, dedupe_key, agent_run_id, agent_version)
    VALUES ('00000000-0000-4000-8000-0000000000b1', '00000000-0000-4000-8000-0000000000f1', 'fixture topic', 'x', 'x',
      '[{"s":1}]', '2026-W41', 'rc-dedupe-1', '00000000-0000-4000-8000-0000000000a1', 'fixture')$$, 'duplicate key');

SELECT cf_test.expect_error('T-ID-03 duplicate external AniList ID rejected',
  $$INSERT INTO cf.anime_titles (franchise_id, normalised_title_key, display_title, anilist_id)
    VALUES ('00000000-0000-4000-8000-0000000000f2', 'another', 'Another', 999001)$$, 'duplicate key');

SELECT cf_test.expect_error('T-ID-05 research candidate without evidence rejected',
  $$INSERT INTO cf.research_candidates (anime_title_id, franchise_id, topic_key, topic_display, content_lane,
      signal_evidence, observation_window, dedupe_key, agent_run_id, agent_version)
    VALUES ('00000000-0000-4000-8000-0000000000b1', '00000000-0000-4000-8000-0000000000f1', 'y', 'y', 'y',
      '[]', '2026-W41', 'rc-dedupe-2', '00000000-0000-4000-8000-0000000000a1', 'fixture')$$, 'signal_evidence');

SELECT cf_test.expect_error('S1-RPL-01 replaying a run with the same idempotency key writes nothing new',
  $$INSERT INTO cf.agent_runs (agent_code, agent_version, idempotency_key, input_state_hash)
    VALUES ('CF-001', 'fixture', 'run-key-1', 'h')$$, 'duplicate key');

-- State machine (CF-001 object types)
SELECT cf_test.expect_error('S1-ST-01 research candidate born READY rejected',
  $$INSERT INTO cf.research_candidates (anime_title_id, franchise_id, topic_key, topic_display, content_lane,
      signal_evidence, observation_window, dedupe_key, agent_run_id, agent_version, status)
    VALUES ('00000000-0000-4000-8000-0000000000b1', '00000000-0000-4000-8000-0000000000f1', 'z', 'z', 'z',
      '[{"s":1}]', '2026-W41', 'rc-dedupe-3', '00000000-0000-4000-8000-0000000000a1', 'fixture', 'READY')$$, 'CF_INVALID_TRANSITION');

SELECT cf_test.expect_error('S1-ST-02 READY research candidate cannot go back to IDEA',
  $$UPDATE cf.research_candidates SET status = 'IDEA' WHERE research_candidate_id = '00000000-0000-4000-8000-0000000000c1'$$,
  'CF_INVALID_TRANSITION');

SELECT cf_test.expect_error('S1-IMM-01 research candidate content frozen once READY',
  $$UPDATE cf.research_candidates SET topic_display = 'changed' WHERE research_candidate_id = '00000000-0000-4000-8000-0000000000c1'$$,
  'CF_IMMUTABLE_ROW');

-- Spend guards
SELECT cf_test.expect_error('T-PAID-01 paid call count without authorisation reference rejected',
  $$INSERT INTO cf.agent_runs (agent_code, agent_version, idempotency_key, input_state_hash, provider_call_count, paid_call_count)
    VALUES ('CF-001', 'fixture', 'run-key-paid', 'h', 1, 1)$$, 'paid_calls_need_authorisation');

SELECT cf_test.expect_error('T-PAID-02 wrong agent namespace rejected (AGENT-00x is the Kids system)',
  $$INSERT INTO cf.agent_runs (agent_code, agent_version, idempotency_key, input_state_hash)
    VALUES ('AGENT-001', 'fixture', 'run-key-ns', 'h')$$, 'agent_runs_agent_code_check');

-- What the runtime role must not be able to do
SELECT cf_test.expect_error('T-ROLE-03 cf_n8n_runtime cannot turn on publishing',
  $$UPDATE cf.system_flags SET enabled = true WHERE flag_key = 'PUBLISH_ENABLED'$$, 'permission denied');

SELECT cf_test.expect_error('S1-ROLE-01 cf_n8n_runtime cannot make anyone a reviewer',
  $$INSERT INTO cf.reviewers (display_name, allowed_gates) VALUES ('Agent', '{G1,G2,G3,G4}')$$, 'permission denied');

SELECT cf_test.expect_error('S1-ROLE-02 cf_n8n_runtime cannot add a state-machine edge',
  $$INSERT INTO cf.allowed_transitions (object_type, from_status, to_status, mode)
    VALUES ('research_candidate', 'READY', 'IDEA', 'DETERMINISTIC')$$, 'permission denied');

SELECT cf_test.expect_error('S1-ROLE-03 cf_n8n_runtime cannot delete rows',
  $$DELETE FROM cf.research_candidates$$, 'permission denied');

SELECT cf_test.expect_error('S1-ROLE-04 cf_n8n_runtime cannot truncate tables',
  $$TRUNCATE cf.agent_runs CASCADE$$, 'permission denied');

SELECT cf_test.expect_error('S1-ROLE-05 cf_n8n_runtime cannot create objects in cf',
  $$CREATE TABLE cf.agent_scratch (x int)$$, 'permission denied');

SELECT cf_test.expect_error('S1-ROLE-06 cf_n8n_runtime cannot create objects in public',
  $$CREATE TABLE public.agent_scratch (x int)$$, 'permission denied');

SELECT cf_test.expect_error('S1-ROLE-07 cf_n8n_runtime cannot disable the guard triggers',
  $$ALTER TABLE cf.research_candidates DISABLE TRIGGER research_candidates_guard_status$$, 'must be owner');

SELECT cf_test.expect_error('S1-ROLE-08 cf_n8n_runtime cannot call cf functions directly',
  $$SELECT cf.touch_updated_at()$$, 'permission denied');

SELECT cf_test.expect_error('S1-ROLE-09 cf_n8n_runtime cannot switch triggers off for its session',
  $$SET session_replication_role = replica$$, 'permission denied');

RESET ROLE;

-- ---------------------------------------------------------------------------
-- Guards that hold for every role, including the owner
-- ---------------------------------------------------------------------------
SELECT cf_test.expect_error('T-APP-03 lifecycle rows are never deleted, even from a privileged session',
  $$DELETE FROM cf.research_candidates$$, 'CF_NO_DELETE');

SELECT 'SPRINT 1 TESTS COMPLETE' AS result;
