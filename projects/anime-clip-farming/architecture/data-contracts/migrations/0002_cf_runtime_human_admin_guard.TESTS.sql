-- =============================================================================
-- LOCAL ONLY — tests for 0002_cf_runtime_human_admin_guard.sql
-- =============================================================================
-- Run ONLY against a throwaway local PostgreSQL that mirrors the Supabase
-- set-up: a non-superuser `postgres` owner, roles anon / authenticated /
-- service_role, cf_n8n_runtime created exactly as provisioning created it, and
-- local trust authentication (the file reconnects as cf_n8n_runtime).
-- Never run against Supabase. All data is fictional fixture data.
-- Title fixtures have no start_year on purpose: see finding F-6 in
-- evidence/PRE_CF001_DATABASE_ACTIVATION_EVIDENCE.md. A dated title is stopped by
-- cf.freeze_after_first_status before the status guard runs, for every role.
--   (as postgres)  psql -v ON_ERROR_STOP=1 --single-transaction -f 0001_cf_sprint01.sql
--   (as postgres)  psql -v ON_ERROR_STOP=1 --single-transaction -f 0002_cf_runtime_human_admin_guard.sql
--   (as superuser) psql -v ON_ERROR_STOP=1 -At -f 0002_cf_runtime_human_admin_guard.TESTS.sql
-- Expected output: one "PASS <id>" notice per test and no "FAIL".
-- IDs: H2-0x runtime denied; H2-1x deterministic path still works; H2-2x invalid
-- edges still rejected; H2-3x real runtime login; H2-4x human/admin path;
-- H2-5x nothing else changed; H2-6x future HUMAN_GATE compatibility.
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

-- A governance denial is identified by its message prefix and SQLSTATE 42501.
CREATE OR REPLACE FUNCTION cf_test.expect_denied(p_test text, p_sql text) RETURNS void
LANGUAGE plpgsql AS $$
DECLARE
  v_state text;
  v_msg   text;
BEGIN
  BEGIN
    EXECUTE p_sql;
  EXCEPTION WHEN others THEN
    GET STACKED DIAGNOSTICS v_state = RETURNED_SQLSTATE;
    v_msg := SQLERRM;
    IF v_state = '42501' AND v_msg LIKE 'CF_GOVERNANCE_DENIED:%' THEN
      RAISE NOTICE 'PASS %', p_test;
      RETURN;
    END IF;
    RAISE EXCEPTION 'FAIL % (wrong error % : %)', p_test, v_state, v_msg;
  END;
  RAISE EXCEPTION 'FAIL % (statement succeeded but must be denied)', p_test;
END $$;

CREATE OR REPLACE FUNCTION cf_test.expect_ok(p_test text, p_sql text) RETURNS void
LANGUAGE plpgsql AS $$
BEGIN
  BEGIN
    EXECUTE p_sql;
  EXCEPTION WHEN others THEN
    RAISE EXCEPTION 'FAIL % (unexpected error: %)', p_test, SQLERRM;
  END;
  RAISE NOTICE 'PASS %', p_test;
END $$;

CREATE OR REPLACE FUNCTION cf_test.expect_true(p_test text, p_cond boolean) RETURNS void
LANGUAGE plpgsql AS $$
BEGIN
  IF p_cond IS TRUE THEN RAISE NOTICE 'PASS %', p_test;
  ELSE RAISE EXCEPTION 'FAIL %', p_test; END IF;
END $$;

GRANT USAGE ON SCHEMA cf_test TO cf_n8n_runtime, postgres;

SET client_min_messages = notice;

-- ---------------------------------------------------------------------------
-- Nothing else changed (catalog, as the harness superuser, on the fresh state)
-- ---------------------------------------------------------------------------
SELECT cf_test.expect_true('H2-50 allowed_transitions is exactly the accepted 14 rows, 4 of them HUMAN_ADMIN',
  (SELECT count(*) = 14
          AND md5(string_agg(concat_ws('|', object_type, from_status, to_status,
                coalesce(required_gate::text, ''), coalesce(required_decision::text, ''), mode), ';'
                ORDER BY object_type, from_status, to_status)) = '6ea6f7a4fafee461dc64345d400b648c'
          AND count(*) FILTER (WHERE mode = 'HUMAN_ADMIN') = 4
   FROM cf.allowed_transitions));

SELECT cf_test.expect_true('H2-51 only the guard function changed: its body is the 0002 body, the other three are the 0001 bodies',
  (SELECT md5(prosrc) FROM pg_proc WHERE oid = to_regprocedure('cf.guard_status_transition()')) = '0dac745af135d4772111d92fd2b168c9'
  AND (SELECT md5(prosrc) FROM pg_proc WHERE oid = to_regprocedure('cf.touch_updated_at()')) = 'c28bbd99ced3dfcd7ff6c2a1298a90e1'
  AND (SELECT md5(prosrc) FROM pg_proc WHERE oid = to_regprocedure('cf.freeze_after_first_status()')) = 'e4b4d9c63cc9870d5f59ab09e5dfe2c1'
  AND (SELECT md5(prosrc) FROM pg_proc WHERE oid = to_regprocedure('cf.forbid_delete()')) = '4097ad56aa56e6835ce9d375769fc6ba');

SELECT cf_test.expect_true('H2-52 guard function keeps invoker rights, postgres ownership and an empty execute list',
  (SELECT NOT prosecdef AND proowner = 'postgres'::regrole AND proconfig IS NULL
     AND NOT EXISTS (SELECT 1 FROM aclexplode(coalesce(proacl, acldefault('f', proowner))) a WHERE a.grantee <> proowner)
   FROM pg_proc WHERE oid = to_regprocedure('cf.guard_status_transition()')));

SELECT cf_test.expect_true('H2-53 runtime privilege matrix unchanged: USAGE on cf, SELECT everywhere, INSERT/UPDATE on the four CF-001 tables, nothing else',
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

SELECT cf_test.expect_true('H2-54 runtime role attributes unchanged, no memberships, owns nothing, still has no password',
  (SELECT rolcanlogin AND NOT rolinherit AND NOT rolbypassrls AND NOT rolsuper AND NOT rolcreatedb
          AND NOT rolcreaterole AND NOT rolreplication FROM pg_roles WHERE rolname = 'cf_n8n_runtime')
  AND NOT EXISTS (SELECT 1 FROM pg_auth_members WHERE member = 'cf_n8n_runtime'::regrole)
  AND NOT EXISTS (SELECT 1 FROM pg_class WHERE relowner = 'cf_n8n_runtime'::regrole)
  AND (SELECT rolpassword IS NULL FROM pg_authid WHERE rolname = 'cf_n8n_runtime'));

SELECT cf_test.expect_true('H2-55 no cf table holds data apart from the 14 transition rows and 3 kill switches',
  (SELECT count(*) FROM cf.agent_runs) + (SELECT count(*) FROM cf.anime_franchises)
  + (SELECT count(*) FROM cf.anime_titles) + (SELECT count(*) FROM cf.research_candidates)
  + (SELECT count(*) FROM cf.reviewers) = 0);

-- ---------------------------------------------------------------------------
-- As the n8n runtime role (SET ROLE): deterministic edges still work
-- ---------------------------------------------------------------------------
SET ROLE cf_n8n_runtime;

INSERT INTO cf.agent_runs (agent_run_id, agent_code, agent_version, idempotency_key, input_state_hash, run_state, started_at)
VALUES ('00000000-0000-4000-8000-0000000000a1', 'CF-001', 'fixture', 'h2-run-1', 'h', 'RUNNING', now());

SELECT cf_test.expect_ok('H2-10 runtime: anime_franchise NEW -> DRAFT (insert)',
  $$INSERT INTO cf.anime_franchises (franchise_id, normalised_key, display_name, agent_run_id) VALUES
    ('00000000-0000-4000-8000-0000000000f1', 'fixture one', 'Fixture One', '00000000-0000-4000-8000-0000000000a1'),
    ('00000000-0000-4000-8000-0000000000f2', 'fixture two', 'Fixture Two', '00000000-0000-4000-8000-0000000000a1')$$);

SELECT cf_test.expect_ok('H2-11 runtime: anime_franchise DRAFT -> READY',
  $$UPDATE cf.anime_franchises SET status = 'READY' WHERE franchise_id = '00000000-0000-4000-8000-0000000000f1'$$);

SELECT cf_test.expect_ok('H2-12 runtime: anime_franchise DRAFT -> BLOCKED',
  $$UPDATE cf.anime_franchises SET status = 'BLOCKED' WHERE franchise_id = '00000000-0000-4000-8000-0000000000f2'$$);

SELECT cf_test.expect_ok('H2-13 runtime: anime_title NEW -> DRAFT (insert)',
  $$INSERT INTO cf.anime_titles (anime_title_id, franchise_id, normalised_title_key, display_title, anilist_id, agent_run_id) VALUES
    ('00000000-0000-4000-8000-0000000000b1', '00000000-0000-4000-8000-0000000000f1', 'title one', 'Title One', 810001, '00000000-0000-4000-8000-0000000000a1'),
    ('00000000-0000-4000-8000-0000000000b2', '00000000-0000-4000-8000-0000000000f1', 'title two', 'Title Two', 810002, '00000000-0000-4000-8000-0000000000a1')$$);

SELECT cf_test.expect_ok('H2-14 runtime: anime_title DRAFT -> READY',
  $$UPDATE cf.anime_titles SET status = 'READY' WHERE anime_title_id = '00000000-0000-4000-8000-0000000000b1'$$);

SELECT cf_test.expect_ok('H2-15 runtime: anime_title DRAFT -> BLOCKED',
  $$UPDATE cf.anime_titles SET status = 'BLOCKED' WHERE anime_title_id = '00000000-0000-4000-8000-0000000000b2'$$);

SELECT cf_test.expect_ok('H2-16 runtime: research_candidate NEW -> IDEA (insert)',
  $$INSERT INTO cf.research_candidates (research_candidate_id, anime_title_id, franchise_id, topic_key, topic_display,
      content_lane, signal_evidence, observation_window, dedupe_key, agent_run_id, agent_version) VALUES
    ('00000000-0000-4000-8000-0000000000c1', '00000000-0000-4000-8000-0000000000b1', '00000000-0000-4000-8000-0000000000f1',
     'topic one', 'Topic one', 'lane', '[{"source":"fixture"}]', '2026-W41', 'h2-dedupe-1', '00000000-0000-4000-8000-0000000000a1', 'fixture'),
    ('00000000-0000-4000-8000-0000000000c2', '00000000-0000-4000-8000-0000000000b1', '00000000-0000-4000-8000-0000000000f1',
     'topic two', 'Topic two', 'lane', '[{"source":"fixture"}]', '2026-W41', 'h2-dedupe-2', '00000000-0000-4000-8000-0000000000a1', 'fixture')$$);

SELECT cf_test.expect_ok('H2-17 runtime: research_candidate IDEA -> READY',
  $$UPDATE cf.research_candidates SET status = 'READY' WHERE research_candidate_id = '00000000-0000-4000-8000-0000000000c1'$$);

SELECT cf_test.expect_ok('H2-18 runtime: research_candidate READY -> RETIRED (deterministic, unchanged)',
  $$UPDATE cf.research_candidates SET status = 'RETIRED' WHERE research_candidate_id = '00000000-0000-4000-8000-0000000000c1'$$);

SELECT cf_test.expect_ok('H2-19 runtime: research_candidate IDEA -> REJECTED',
  $$UPDATE cf.research_candidates SET status = 'REJECTED', rejection_reason = 'fixture' WHERE research_candidate_id = '00000000-0000-4000-8000-0000000000c2'$$);

-- ---------------------------------------------------------------------------
-- As the n8n runtime role: HUMAN_ADMIN edges are denied (the four from the brief)
-- ---------------------------------------------------------------------------
SELECT cf_test.expect_denied('H2-01 runtime denied: anime_franchise BLOCKED -> READY',
  $$UPDATE cf.anime_franchises SET status = 'READY' WHERE franchise_id = '00000000-0000-4000-8000-0000000000f2'$$);

SELECT cf_test.expect_denied('H2-02 runtime denied: anime_franchise READY -> RETIRED',
  $$UPDATE cf.anime_franchises SET status = 'RETIRED' WHERE franchise_id = '00000000-0000-4000-8000-0000000000f1'$$);

SELECT cf_test.expect_denied('H2-03 runtime denied: anime_title BLOCKED -> READY',
  $$UPDATE cf.anime_titles SET status = 'READY' WHERE anime_title_id = '00000000-0000-4000-8000-0000000000b2'$$);

SELECT cf_test.expect_denied('H2-04 runtime denied: anime_title READY -> RETIRED',
  $$UPDATE cf.anime_titles SET status = 'RETIRED' WHERE anime_title_id = '00000000-0000-4000-8000-0000000000b1'$$);

SELECT cf_test.expect_denied('H2-06 runtime denied: anime_franchise READY -> RETIRED through INSERT ... ON CONFLICT DO UPDATE',
  $$INSERT INTO cf.anime_franchises (franchise_id, normalised_key, display_name)
    VALUES ('00000000-0000-4000-8000-0000000000f1', 'fixture one', 'Fixture One')
    ON CONFLICT (franchise_id) DO UPDATE SET status = 'RETIRED'$$);

SELECT cf_test.expect_denied('H2-07 runtime denied: anime_title BLOCKED -> READY through INSERT ... ON CONFLICT DO UPDATE',
  $$INSERT INTO cf.anime_titles (anime_title_id, franchise_id, normalised_title_key, display_title)
    VALUES ('00000000-0000-4000-8000-0000000000b2', '00000000-0000-4000-8000-0000000000f1', 'title two', 'Title Two')
    ON CONFLICT (anime_title_id) DO UPDATE SET status = 'READY'$$);

SELECT cf_test.expect_true('H2-08 every refused attempt left its row unchanged',
  (SELECT status::text FROM cf.anime_franchises WHERE franchise_id = '00000000-0000-4000-8000-0000000000f2') = 'BLOCKED'
  AND (SELECT status::text FROM cf.anime_franchises WHERE franchise_id = '00000000-0000-4000-8000-0000000000f1') = 'READY'
  AND (SELECT status::text FROM cf.anime_titles WHERE anime_title_id = '00000000-0000-4000-8000-0000000000b2') = 'BLOCKED'
  AND (SELECT status::text FROM cf.anime_titles WHERE anime_title_id = '00000000-0000-4000-8000-0000000000b1') = 'READY');

-- Edges that are not allowed at all still fail as invalid transitions, not as governance denials
SELECT cf_test.expect_error('H2-20 runtime: anime_franchise READY -> DRAFT is still an invalid transition',
  $$UPDATE cf.anime_franchises SET status = 'DRAFT' WHERE franchise_id = '00000000-0000-4000-8000-0000000000f1'$$,
  'CF_INVALID_TRANSITION');

SELECT cf_test.expect_error('H2-21 runtime: anime_title BLOCKED -> RETIRED (no such edge) is still an invalid transition',
  $$UPDATE cf.anime_titles SET status = 'RETIRED' WHERE anime_title_id = '00000000-0000-4000-8000-0000000000b2'$$,
  'CF_INVALID_TRANSITION');

SELECT cf_test.expect_error('H2-22 runtime: research_candidate RETIRED -> IDEA is still an invalid transition',
  $$UPDATE cf.research_candidates SET status = 'IDEA' WHERE research_candidate_id = '00000000-0000-4000-8000-0000000000c1'$$,
  'CF_INVALID_TRANSITION');

SELECT cf_test.expect_error('H2-23 runtime: anime_franchise born READY is still an invalid transition',
  $$INSERT INTO cf.anime_franchises (normalised_key, display_name, status) VALUES ('born ready', 'Born Ready', 'READY')$$,
  'CF_INVALID_TRANSITION');

RESET ROLE;

-- ---------------------------------------------------------------------------
-- Human / admin path: the same rows can still be moved by an admin session
-- ---------------------------------------------------------------------------
SET ROLE postgres;

SELECT cf_test.expect_ok('H2-40 admin (postgres): anime_franchise BLOCKED -> READY, the row the runtime was denied',
  $$UPDATE cf.anime_franchises SET status = 'READY' WHERE franchise_id = '00000000-0000-4000-8000-0000000000f2'$$);

SELECT cf_test.expect_ok('H2-41 admin (postgres): anime_franchise READY -> RETIRED',
  $$UPDATE cf.anime_franchises SET status = 'RETIRED' WHERE franchise_id = '00000000-0000-4000-8000-0000000000f1'$$);

SELECT cf_test.expect_ok('H2-42 admin (postgres): anime_title BLOCKED -> READY',
  $$UPDATE cf.anime_titles SET status = 'READY' WHERE anime_title_id = '00000000-0000-4000-8000-0000000000b2'$$);

SELECT cf_test.expect_ok('H2-43 admin (postgres): anime_title READY -> RETIRED',
  $$UPDATE cf.anime_titles SET status = 'RETIRED' WHERE anime_title_id = '00000000-0000-4000-8000-0000000000b1'$$);

RESET ROLE;

INSERT INTO cf.anime_franchises (franchise_id, normalised_key, display_name)
VALUES ('00000000-0000-4000-8000-0000000000f7', 'fixture seven', 'Fixture Seven');
UPDATE cf.anime_franchises SET status = 'BLOCKED' WHERE franchise_id = '00000000-0000-4000-8000-0000000000f7';

SELECT cf_test.expect_ok('H2-44 admin (superuser session): anime_franchise BLOCKED -> READY',
  $$UPDATE cf.anime_franchises SET status = 'READY' WHERE franchise_id = '00000000-0000-4000-8000-0000000000f7'$$);

SELECT cf_test.expect_true('H2-45 postgres holds an ADMIN-only membership on cf_n8n_runtime, which is why the guard checks identity, not membership',
  EXISTS (SELECT 1 FROM pg_auth_members
           WHERE roleid = 'cf_n8n_runtime'::regrole AND member = 'postgres'::regrole AND admin_option));

-- ---------------------------------------------------------------------------
-- Real runtime login (session_user = current_user = cf_n8n_runtime)
-- ---------------------------------------------------------------------------
INSERT INTO cf.anime_franchises (franchise_id, normalised_key, display_name) VALUES
  ('00000000-0000-4000-8000-0000000000f3', 'fixture three', 'Fixture Three'),
  ('00000000-0000-4000-8000-0000000000f4', 'fixture four', 'Fixture Four');
UPDATE cf.anime_franchises SET status = 'READY'   WHERE franchise_id = '00000000-0000-4000-8000-0000000000f3';
UPDATE cf.anime_franchises SET status = 'BLOCKED' WHERE franchise_id = '00000000-0000-4000-8000-0000000000f4';
INSERT INTO cf.anime_titles (anime_title_id, franchise_id, normalised_title_key, display_title) VALUES
  ('00000000-0000-4000-8000-0000000000b3', '00000000-0000-4000-8000-0000000000f3', 'title three', 'Title Three'),
  ('00000000-0000-4000-8000-0000000000b4', '00000000-0000-4000-8000-0000000000f3', 'title four', 'Title Four');
UPDATE cf.anime_titles SET status = 'READY'   WHERE anime_title_id = '00000000-0000-4000-8000-0000000000b3';
UPDATE cf.anime_titles SET status = 'BLOCKED' WHERE anime_title_id = '00000000-0000-4000-8000-0000000000b4';

\connect - cf_n8n_runtime

SELECT cf_test.expect_true('H2-30 this session is a real cf_n8n_runtime login',
  session_user = 'cf_n8n_runtime' AND current_user = 'cf_n8n_runtime');

SELECT cf_test.expect_denied('H2-31 real login denied: anime_franchise BLOCKED -> READY',
  $$UPDATE cf.anime_franchises SET status = 'READY' WHERE franchise_id = '00000000-0000-4000-8000-0000000000f4'$$);

SELECT cf_test.expect_denied('H2-32 real login denied: anime_franchise READY -> RETIRED',
  $$UPDATE cf.anime_franchises SET status = 'RETIRED' WHERE franchise_id = '00000000-0000-4000-8000-0000000000f3'$$);

SELECT cf_test.expect_denied('H2-33 real login denied: anime_title BLOCKED -> READY',
  $$UPDATE cf.anime_titles SET status = 'READY' WHERE anime_title_id = '00000000-0000-4000-8000-0000000000b4'$$);

SELECT cf_test.expect_denied('H2-34 real login denied: anime_title READY -> RETIRED',
  $$UPDATE cf.anime_titles SET status = 'RETIRED' WHERE anime_title_id = '00000000-0000-4000-8000-0000000000b3'$$);

SELECT cf_test.expect_ok('H2-35 real login: anime_franchise NEW -> DRAFT still works',
  $$INSERT INTO cf.anime_franchises (franchise_id, normalised_key, display_name)
    VALUES ('00000000-0000-4000-8000-0000000000f5', 'fixture five', 'Fixture Five')$$);

SELECT cf_test.expect_ok('H2-36 real login: anime_franchise DRAFT -> READY still works',
  $$UPDATE cf.anime_franchises SET status = 'READY' WHERE franchise_id = '00000000-0000-4000-8000-0000000000f5'$$);

\connect - pgtest

-- ---------------------------------------------------------------------------
-- Future HUMAN_GATE compatibility (test-only stand-ins for objects that later
-- migrations create): a gated edge stays open to the runtime role once a
-- matching persisted decision exists, and still fails without one.
-- ---------------------------------------------------------------------------
CREATE TABLE cf_test.stub_decisions (
  gate                  cf.gate_code NOT NULL,
  object_type           text NOT NULL,
  object_id             uuid NOT NULL,
  decision              cf.gate_decision_value NOT NULL,
  object_content_sha256 text NOT NULL
);
CREATE VIEW cf.v_effective_gate_decisions AS
  SELECT gate, object_type, object_id, decision, object_content_sha256 FROM cf_test.stub_decisions;
GRANT SELECT ON cf.v_effective_gate_decisions TO cf_n8n_runtime;

CREATE TABLE cf_test.gated_obj (
  gated_id        uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  status          cf.lifecycle_status NOT NULL DEFAULT 'DRAFT',
  content_sha256  text,
  updated_at      timestamptz NOT NULL DEFAULT now()
);
CREATE TRIGGER gated_guard BEFORE INSERT OR UPDATE OF status ON cf_test.gated_obj
  FOR EACH ROW EXECUTE FUNCTION cf.guard_status_transition('gated_obj', 'gated_id');
GRANT SELECT, INSERT, UPDATE ON cf_test.gated_obj TO cf_n8n_runtime;

INSERT INTO cf.allowed_transitions (object_type, from_status, to_status, required_gate, required_decision, mode) VALUES
  ('gated_obj', 'NEW', 'DRAFT', NULL, NULL, 'DETERMINISTIC'),
  ('gated_obj', 'DRAFT', 'APPROVED', 'G1', 'APPROVE', 'HUMAN_GATE'),
  ('gated_obj', 'APPROVED', 'RETIRED', NULL, NULL, 'HUMAN_ADMIN');

INSERT INTO cf_test.gated_obj (gated_id, content_sha256) VALUES ('00000000-0000-4000-8000-0000000000d1', 'sha-fixture');

SET ROLE cf_n8n_runtime;

SELECT cf_test.expect_error('H2-60 runtime: a HUMAN_GATE edge without a persisted decision fails as a missing gate decision, not as a HUMAN_ADMIN denial',
  $$UPDATE cf_test.gated_obj SET status = 'APPROVED' WHERE gated_id = '00000000-0000-4000-8000-0000000000d1'$$,
  'CF_GATE_DECISION_MISSING');

RESET ROLE;
INSERT INTO cf_test.stub_decisions (gate, object_type, object_id, decision, object_content_sha256)
VALUES ('G1', 'gated_obj', '00000000-0000-4000-8000-0000000000d1', 'APPROVE', 'sha-fixture');
SET ROLE cf_n8n_runtime;

SELECT cf_test.expect_ok('H2-61 runtime: the same HUMAN_GATE edge succeeds once the matching decision exists',
  $$UPDATE cf_test.gated_obj SET status = 'APPROVED' WHERE gated_id = '00000000-0000-4000-8000-0000000000d1'$$);

SELECT cf_test.expect_denied('H2-62 runtime: a HUMAN_ADMIN edge on the same object stays denied, decision or not',
  $$UPDATE cf_test.gated_obj SET status = 'RETIRED' WHERE gated_id = '00000000-0000-4000-8000-0000000000d1'$$);

RESET ROLE;

SELECT 'CF 0002 TESTS COMPLETE' AS result;
