-- =============================================================================
-- LOCAL ONLY — tests for 0003_cf_freeze_generated_columns_and_search_path.sql
-- =============================================================================
-- Run ONLY against a throwaway local PostgreSQL that mirrors the Supabase
-- set-up (see 0002 TESTS header): non-superuser `postgres` owner, roles anon /
-- authenticated / service_role, cf_n8n_runtime created as provisioning created
-- it, local trust authentication (the file reconnects as cf_n8n_runtime).
-- Never run against Supabase. All data is fictional fixture data.
--   (as postgres)  psql -v ON_ERROR_STOP=1 --single-transaction -f 0001_cf_sprint01.sql
--   (as postgres)  psql -v ON_ERROR_STOP=1 --single-transaction -f 0002_cf_runtime_human_admin_guard.sql
--   (as postgres)  psql -v ON_ERROR_STOP=1 --single-transaction -f 0003_cf_freeze_generated_columns_and_search_path.sql
--   (as superuser) psql -v ON_ERROR_STOP=1 -At -f 0003_cf_freeze_generated_columns_and_search_path.TESTS.sql
-- Expected output: one "PASS <id>" notice per test and no "FAIL".
-- IDs: H3-0x function security (F-7); H3-1x dated titles (F-6) for the runtime
-- role and the admin; H3-2x immutable content still frozen; H3-3x..H3-4x generic
-- generated-column fixtures; H3-4xa real runtime login; H3-5x nothing else changed;
-- H3-6x search_path really pins resolution.
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
-- H3-0x / H3-5x: catalog checks on the fresh 0001 + 0002 + 0003 state
-- ---------------------------------------------------------------------------
SELECT cf_test.expect_true('H3-01 cf.guard_status_transition(): search_path = pg_catalog, cf, SECURITY INVOKER, postgres-owned',
  (SELECT proconfig = ARRAY['search_path=pg_catalog, cf'] AND NOT prosecdef AND proowner = 'postgres'::regrole
   FROM pg_proc WHERE oid = to_regprocedure('cf.guard_status_transition()')));
SELECT cf_test.expect_true('H3-02 cf.freeze_after_first_status(): search_path = pg_catalog, cf, SECURITY INVOKER, postgres-owned',
  (SELECT proconfig = ARRAY['search_path=pg_catalog, cf'] AND NOT prosecdef AND proowner = 'postgres'::regrole
   FROM pg_proc WHERE oid = to_regprocedure('cf.freeze_after_first_status()')));
SELECT cf_test.expect_true('H3-03 cf.forbid_delete(): search_path = pg_catalog, cf, SECURITY INVOKER, postgres-owned',
  (SELECT proconfig = ARRAY['search_path=pg_catalog, cf'] AND NOT prosecdef AND proowner = 'postgres'::regrole
   FROM pg_proc WHERE oid = to_regprocedure('cf.forbid_delete()')));
SELECT cf_test.expect_true('H3-04 cf.touch_updated_at(): search_path = pg_catalog, cf, SECURITY INVOKER, postgres-owned',
  (SELECT proconfig = ARRAY['search_path=pg_catalog, cf'] AND NOT prosecdef AND proowner = 'postgres'::regrole
   FROM pg_proc WHERE oid = to_regprocedure('cf.touch_updated_at()')));
SELECT cf_test.expect_true('H3-05 no cf function has SECURITY DEFINER, and no search_path names public, "$user" or pg_temp',
  NOT EXISTS (SELECT 1 FROM pg_proc WHERE pronamespace = 'cf'::regnamespace
              AND (prosecdef OR proconfig::text ~ '(public|\$user|pg_temp)')));
SELECT cf_test.expect_true('H3-06 no EXECUTE grant on any cf function to anyone but the owner (PUBLIC, runtime, anon, authenticated, service_role)',
  NOT EXISTS (SELECT 1 FROM pg_proc p, aclexplode(coalesce(p.proacl, acldefault('f', p.proowner))) a
               WHERE p.pronamespace = 'cf'::regnamespace AND a.grantee <> p.proowner)
  AND NOT EXISTS (SELECT 1 FROM pg_proc p WHERE p.pronamespace = 'cf'::regnamespace
               AND (has_function_privilege('cf_n8n_runtime', p.oid, 'EXECUTE')
                 OR has_function_privilege('anon', p.oid, 'EXECUTE')
                 OR has_function_privilege('authenticated', p.oid, 'EXECUTE')
                 OR has_function_privilege('service_role', p.oid, 'EXECUTE'))));
SELECT cf_test.expect_true('H3-07 the cf schema holds exactly the same four functions, owned by postgres',
  (SELECT array_agg(proname::text ORDER BY proname) FROM pg_proc WHERE pronamespace = 'cf'::regnamespace)
    = ARRAY['forbid_delete','freeze_after_first_status','guard_status_transition','touch_updated_at']
  AND (SELECT bool_and(proowner = 'postgres'::regrole) FROM pg_proc WHERE pronamespace = 'cf'::regnamespace));
SELECT cf_test.expect_true('H3-08 bodies: guard is the 0002 body (HUMAN_ADMIN block retained, byte for byte), touch and forbid are the 0001 bodies, freeze is the 0003 body',
  (SELECT md5(prosrc) FROM pg_proc WHERE oid = to_regprocedure('cf.guard_status_transition()')) = '0dac745af135d4772111d92fd2b168c9'
  AND (SELECT prosrc FROM pg_proc WHERE oid = to_regprocedure('cf.guard_status_transition()')) LIKE '%session_user = ''cf_n8n_runtime'' OR current_user = ''cf_n8n_runtime''%'
  AND (SELECT md5(prosrc) FROM pg_proc WHERE oid = to_regprocedure('cf.touch_updated_at()')) = 'c28bbd99ced3dfcd7ff6c2a1298a90e1'
  AND (SELECT md5(prosrc) FROM pg_proc WHERE oid = to_regprocedure('cf.forbid_delete()')) = '4097ad56aa56e6835ce9d375769fc6ba'
  AND (SELECT md5(prosrc) FROM pg_proc WHERE oid = to_regprocedure('cf.freeze_after_first_status()')) = 'f957a25df6e08a74a21b6a64e5181a47');
SELECT cf_test.expect_true('H3-09 the 12 triggers are still bound and enabled (3 guard, 3 freeze, 3 no-delete, 3 touch)',
  (SELECT count(*) FROM pg_trigger t JOIN pg_class c ON c.oid = t.tgrelid
    WHERE c.relnamespace = 'cf'::regnamespace AND NOT t.tgisinternal AND t.tgenabled = 'O') = 12);

SELECT cf_test.expect_true('H3-50 allowed_transitions is exactly the accepted 14 rows, 4 of them HUMAN_ADMIN',
  (SELECT count(*) = 14
          AND md5(string_agg(concat_ws('|', object_type, from_status, to_status,
                coalesce(required_gate::text, ''), coalesce(required_decision::text, ''), mode), ';'
                ORDER BY object_type, from_status, to_status)) = '6ea6f7a4fafee461dc64345d400b648c'
          AND count(*) FILTER (WHERE mode = 'HUMAN_ADMIN') = 4
   FROM cf.allowed_transitions));
SELECT cf_test.expect_true('H3-51 runtime privilege matrix unchanged: USAGE on cf, SELECT everywhere, INSERT/UPDATE on the four CF-001 tables, nothing else',
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
SELECT cf_test.expect_true('H3-52 runtime role attributes unchanged, no memberships, owns nothing, still has no password',
  (SELECT rolcanlogin AND NOT rolinherit AND NOT rolbypassrls AND NOT rolsuper AND NOT rolcreatedb
          AND NOT rolcreaterole AND NOT rolreplication FROM pg_roles WHERE rolname = 'cf_n8n_runtime')
  AND NOT EXISTS (SELECT 1 FROM pg_auth_members WHERE member = 'cf_n8n_runtime'::regrole)
  AND NOT EXISTS (SELECT 1 FROM pg_class WHERE relowner = 'cf_n8n_runtime'::regrole)
  AND (SELECT rolpassword IS NULL FROM pg_authid WHERE rolname = 'cf_n8n_runtime'));
SELECT cf_test.expect_true('H3-53 no cf table holds data before the fixtures (apart from the 14 transition rows and 3 kill switches)',
  (SELECT count(*) FROM cf.agent_runs) + (SELECT count(*) FROM cf.anime_franchises)
  + (SELECT count(*) FROM cf.anime_titles) + (SELECT count(*) FROM cf.research_candidates)
  + (SELECT count(*) FROM cf.reviewers) = 0);

-- ---------------------------------------------------------------------------
-- Fixtures that only a non-runtime session may build (superuser)
-- ---------------------------------------------------------------------------
INSERT INTO cf.anime_franchises (franchise_id, normalised_key, display_name) VALUES
  ('00000000-0000-4000-8000-0000000000e1', 'dated one', 'Dated One'),
  ('00000000-0000-4000-8000-0000000000e2', 'dated two', 'Dated Two');

-- ---------------------------------------------------------------------------
-- H3-1x: dated titles (non-null start_year), as the n8n runtime role (SET ROLE)
-- ---------------------------------------------------------------------------
SET ROLE cf_n8n_runtime;

SELECT cf_test.expect_ok('H3-10 runtime: dated anime_title NEW -> DRAFT (insert)',
  $$INSERT INTO cf.anime_titles (anime_title_id, franchise_id, normalised_title_key, display_title, start_year) VALUES
    ('00000000-0000-4000-8000-000000000011', '00000000-0000-4000-8000-0000000000e1', 'dated ready',   'Dated Ready',   2001),
    ('00000000-0000-4000-8000-000000000012', '00000000-0000-4000-8000-0000000000e1', 'dated blocked', 'Dated Blocked', 2002)$$);
SELECT cf_test.expect_true('H3-11 the generated column era_decade is computed for the dated titles',
  (SELECT era_decade FROM cf.anime_titles WHERE anime_title_id = '00000000-0000-4000-8000-000000000011') = 2000);
SELECT cf_test.expect_ok('H3-12 runtime: dated anime_title DRAFT -> READY (NEW -> DRAFT -> READY)',
  $$UPDATE cf.anime_titles SET status = 'READY' WHERE anime_title_id = '00000000-0000-4000-8000-000000000011'$$);
SELECT cf_test.expect_ok('H3-13 runtime: dated anime_title DRAFT -> BLOCKED (NEW -> DRAFT -> BLOCKED)',
  $$UPDATE cf.anime_titles SET status = 'BLOCKED' WHERE anime_title_id = '00000000-0000-4000-8000-000000000012'$$);
SELECT cf_test.expect_ok('H3-14 runtime: a mutable column (display_title) still changes on a dated READY title',
  $$UPDATE cf.anime_titles SET display_title = 'Dated Ready (renamed)' WHERE anime_title_id = '00000000-0000-4000-8000-000000000011'$$);

SELECT cf_test.expect_denied('H3-15 runtime denied (CF_GOVERNANCE_DENIED, not CF_IMMUTABLE_ROW): dated anime_title BLOCKED -> READY',
  $$UPDATE cf.anime_titles SET status = 'READY' WHERE anime_title_id = '00000000-0000-4000-8000-000000000012'$$);
SELECT cf_test.expect_denied('H3-16 runtime denied (CF_GOVERNANCE_DENIED, not CF_IMMUTABLE_ROW): dated anime_title READY -> RETIRED',
  $$UPDATE cf.anime_titles SET status = 'RETIRED' WHERE anime_title_id = '00000000-0000-4000-8000-000000000011'$$);
SELECT cf_test.expect_denied('H3-17 runtime denied: dated anime_title READY -> RETIRED through INSERT ... ON CONFLICT DO UPDATE',
  $$INSERT INTO cf.anime_titles (anime_title_id, franchise_id, normalised_title_key, display_title, start_year)
    VALUES ('00000000-0000-4000-8000-000000000011', '00000000-0000-4000-8000-0000000000e1', 'dated ready', 'Dated Ready (renamed)', 2001)
    ON CONFLICT (anime_title_id) DO UPDATE SET status = 'RETIRED'$$);
SELECT cf_test.expect_true('H3-18 every refused attempt left its row unchanged',
  (SELECT status::text FROM cf.anime_titles WHERE anime_title_id = '00000000-0000-4000-8000-000000000011') = 'READY'
  AND (SELECT status::text FROM cf.anime_titles WHERE anime_title_id = '00000000-0000-4000-8000-000000000012') = 'BLOCKED');

-- H3-2x: ordinary content columns stay frozen on READY and BLOCKED titles (runtime)
SELECT cf_test.expect_error('H3-20 runtime: READY title, normalised_title_key change -> CF_IMMUTABLE_ROW',
  $$UPDATE cf.anime_titles SET normalised_title_key = 'other key' WHERE anime_title_id = '00000000-0000-4000-8000-000000000011'$$, 'CF_IMMUTABLE_ROW');
SELECT cf_test.expect_error('H3-21 runtime: READY title, franchise_id change -> CF_IMMUTABLE_ROW',
  $$UPDATE cf.anime_titles SET franchise_id = '00000000-0000-4000-8000-0000000000e2' WHERE anime_title_id = '00000000-0000-4000-8000-000000000011'$$, 'CF_IMMUTABLE_ROW');
SELECT cf_test.expect_error('H3-22 runtime: READY title, start_year change (era_decade follows) -> CF_IMMUTABLE_ROW',
  $$UPDATE cf.anime_titles SET start_year = 2011 WHERE anime_title_id = '00000000-0000-4000-8000-000000000011'$$, 'CF_IMMUTABLE_ROW');
SELECT cf_test.expect_error('H3-23 runtime: READY title, media_type change -> CF_IMMUTABLE_ROW',
  $$UPDATE cf.anime_titles SET media_type = 'MOVIE' WHERE anime_title_id = '00000000-0000-4000-8000-000000000011'$$, 'CF_IMMUTABLE_ROW');
SELECT cf_test.expect_error('H3-24 runtime: BLOCKED title, normalised_title_key change -> CF_IMMUTABLE_ROW',
  $$UPDATE cf.anime_titles SET normalised_title_key = 'other key' WHERE anime_title_id = '00000000-0000-4000-8000-000000000012'$$, 'CF_IMMUTABLE_ROW');
SELECT cf_test.expect_error('H3-25 runtime: BLOCKED title, franchise_id change -> CF_IMMUTABLE_ROW',
  $$UPDATE cf.anime_titles SET franchise_id = '00000000-0000-4000-8000-0000000000e2' WHERE anime_title_id = '00000000-0000-4000-8000-000000000012'$$, 'CF_IMMUTABLE_ROW');
SELECT cf_test.expect_error('H3-26 runtime: BLOCKED title, start_year change -> CF_IMMUTABLE_ROW',
  $$UPDATE cf.anime_titles SET start_year = 2012 WHERE anime_title_id = '00000000-0000-4000-8000-000000000012'$$, 'CF_IMMUTABLE_ROW');
SELECT cf_test.expect_error('H3-27 runtime: BLOCKED title, media_type change -> CF_IMMUTABLE_ROW',
  $$UPDATE cf.anime_titles SET media_type = 'OVA' WHERE anime_title_id = '00000000-0000-4000-8000-000000000012'$$, 'CF_IMMUTABLE_ROW');
SELECT cf_test.expect_error('H3-28 runtime: a status change that also alters a frozen column is still CF_IMMUTABLE_ROW (READY title, start_year + status)',
  $$UPDATE cf.anime_titles SET status = 'RETIRED', start_year = 2013 WHERE anime_title_id = '00000000-0000-4000-8000-000000000011'$$, 'CF_IMMUTABLE_ROW');

RESET ROLE;

-- ---------------------------------------------------------------------------
-- Human / admin path on the same dated titles
-- ---------------------------------------------------------------------------
SET ROLE postgres;

SELECT cf_test.expect_ok('H3-30 admin (postgres): dated anime_title BLOCKED -> READY',
  $$UPDATE cf.anime_titles SET status = 'READY' WHERE anime_title_id = '00000000-0000-4000-8000-000000000012'$$);
SELECT cf_test.expect_ok('H3-31 admin (postgres): dated anime_title READY -> RETIRED',
  $$UPDATE cf.anime_titles SET status = 'RETIRED' WHERE anime_title_id = '00000000-0000-4000-8000-000000000011'$$);
SELECT cf_test.expect_true('H3-32 the admin transitions are persisted (READY and RETIRED) and era_decade is intact',
  (SELECT status::text FROM cf.anime_titles WHERE anime_title_id = '00000000-0000-4000-8000-000000000012') = 'READY'
  AND (SELECT status::text FROM cf.anime_titles WHERE anime_title_id = '00000000-0000-4000-8000-000000000011') = 'RETIRED'
  AND (SELECT era_decade FROM cf.anime_titles WHERE anime_title_id = '00000000-0000-4000-8000-000000000012') = 2000);
SELECT cf_test.expect_error('H3-33 admin: content of a RETIRED dated title is still frozen (start_year)',
  $$UPDATE cf.anime_titles SET start_year = 2014 WHERE anime_title_id = '00000000-0000-4000-8000-000000000011'$$, 'CF_IMMUTABLE_ROW');
SELECT cf_test.expect_error('H3-34 admin: a RETIRED title cannot be deleted',
  $$DELETE FROM cf.anime_titles WHERE anime_title_id = '00000000-0000-4000-8000-000000000011'$$, 'CF_NO_DELETE');

RESET ROLE;

-- ---------------------------------------------------------------------------
-- H3-3x: generic fixture. Tables that are NOT cf.anime_titles, bound to the
-- freeze function, with generated stored columns other than era_decade.
-- ---------------------------------------------------------------------------
CREATE TABLE cf_test.gen_fixture (
  gid         integer PRIMARY KEY,
  status      cf.lifecycle_status NOT NULL DEFAULT 'READY',
  src_a       integer NOT NULL,
  src_b       text NOT NULL,
  mut         text,
  doubled     integer GENERATED ALWAYS AS (src_a * 2) STORED,
  shout       text    GENERATED ALWAYS AS (upper(src_b)) STORED,
  updated_at  timestamptz NOT NULL DEFAULT now()
);
CREATE TRIGGER gen_freeze BEFORE UPDATE ON cf_test.gen_fixture
  FOR EACH ROW EXECUTE FUNCTION cf.freeze_after_first_status('mut');
INSERT INTO cf_test.gen_fixture (gid, src_a, src_b, mut) VALUES (1, 5, 'abc', 'm'), (2, 6, 'def', 'm');

CREATE TABLE cf_test.gen_dropped (
  gid         integer PRIMARY KEY,
  status      cf.lifecycle_status NOT NULL DEFAULT 'READY',
  scrap       text,
  src_a       integer NOT NULL,
  tripled     integer GENERATED ALWAYS AS (src_a * 3) STORED,
  updated_at  timestamptz NOT NULL DEFAULT now()
);
ALTER TABLE cf_test.gen_dropped DROP COLUMN scrap;
CREATE TRIGGER gen_freeze BEFORE UPDATE ON cf_test.gen_dropped
  FOR EACH ROW EXECUTE FUNCTION cf.freeze_after_first_status();
INSERT INTO cf_test.gen_dropped (gid, src_a) VALUES (1, 7);

CREATE TABLE cf_test.plain_fixture (
  gid         integer PRIMARY KEY,
  status      cf.lifecycle_status NOT NULL DEFAULT 'READY',
  src_a       integer NOT NULL,
  updated_at  timestamptz NOT NULL DEFAULT now()
);
CREATE TRIGGER gen_freeze BEFORE UPDATE ON cf_test.plain_fixture
  FOR EACH ROW EXECUTE FUNCTION cf.freeze_after_first_status();
INSERT INTO cf_test.plain_fixture (gid, src_a) VALUES (1, 1);

SELECT cf_test.expect_true('H3-35 fixture check: gen_fixture has two generated stored columns, neither is era_decade',
  (SELECT array_agg(attname::text ORDER BY attname) FROM pg_attribute
    WHERE attrelid = 'cf_test.gen_fixture'::regclass AND attnum > 0 AND NOT attisdropped AND attgenerated = 's')
  = ARRAY['doubled','shout']);
SELECT cf_test.expect_ok('H3-36 generic: status-only change succeeds when the only OLD/NEW difference is a generated column',
  $$UPDATE cf_test.gen_fixture SET status = 'BLOCKED' WHERE gid = 1$$);
SELECT cf_test.expect_ok('H3-37 generic: a second status-only change on the same row succeeds',
  $$UPDATE cf_test.gen_fixture SET status = 'READY' WHERE gid = 1$$);
SELECT cf_test.expect_ok('H3-38 generic: a mutable column (TG_ARGV) still changes, generated columns untouched',
  $$UPDATE cf_test.gen_fixture SET mut = 'm2' WHERE gid = 1$$);
SELECT cf_test.expect_error('H3-39 generic: a real immutable source column change (src_a, which drives "doubled") still fails',
  $$UPDATE cf_test.gen_fixture SET src_a = 50 WHERE gid = 1$$, 'CF_IMMUTABLE_ROW');
SELECT cf_test.expect_error('H3-40 generic: a real immutable source column change (src_b, which drives "shout") still fails',
  $$UPDATE cf_test.gen_fixture SET src_b = 'zzz' WHERE gid = 2$$, 'CF_IMMUTABLE_ROW');
SELECT cf_test.expect_error('H3-41 generic: status plus a source column change in one statement still fails',
  $$UPDATE cf_test.gen_fixture SET status = 'RETIRED', src_a = 60 WHERE gid = 2$$, 'CF_IMMUTABLE_ROW');
SELECT cf_test.expect_true('H3-42 generic: the failed attempts changed nothing; generated values follow the sources',
  (SELECT src_a = 5 AND doubled = 10 AND shout = 'ABC' AND mut = 'm2' AND status::text = 'READY' FROM cf_test.gen_fixture WHERE gid = 1)
  AND (SELECT src_b = 'def' AND shout = 'DEF' AND status::text = 'READY' FROM cf_test.gen_fixture WHERE gid = 2));
SELECT cf_test.expect_ok('H3-43 generic: a table with a dropped column and a generated column accepts a status-only change',
  $$UPDATE cf_test.gen_dropped SET status = 'RETIRED' WHERE gid = 1$$);
SELECT cf_test.expect_error('H3-44 generic: the same table still rejects a source change',
  $$UPDATE cf_test.gen_dropped SET src_a = 8 WHERE gid = 1$$, 'CF_IMMUTABLE_ROW');
SELECT cf_test.expect_ok('H3-45 generic: a table with no generated column (empty set) accepts a status-only change',
  $$UPDATE cf_test.plain_fixture SET status = 'RETIRED' WHERE gid = 1$$);
SELECT cf_test.expect_error('H3-46 generic: a table with no generated column still rejects a content change',
  $$UPDATE cf_test.plain_fixture SET src_a = 2 WHERE gid = 1$$, 'CF_IMMUTABLE_ROW');
SELECT cf_test.expect_ok('H3-47 generic: IDEA/DRAFT rows are still unfrozen (freeze returns before comparing)',
  $$UPDATE cf_test.plain_fixture SET status = 'DRAFT' WHERE gid = 1; UPDATE cf_test.plain_fixture SET src_a = 3 WHERE gid = 1$$);

-- ---------------------------------------------------------------------------
-- H3-4x: real runtime login on dated titles
-- ---------------------------------------------------------------------------
INSERT INTO cf.anime_titles (anime_title_id, franchise_id, normalised_title_key, display_title, start_year) VALUES
  ('00000000-0000-4000-8000-000000000013', '00000000-0000-4000-8000-0000000000e1', 'dated login ready',   'Dated Login Ready',   2003),
  ('00000000-0000-4000-8000-000000000014', '00000000-0000-4000-8000-0000000000e1', 'dated login blocked', 'Dated Login Blocked', 2004),
  ('00000000-0000-4000-8000-000000000015', '00000000-0000-4000-8000-0000000000e1', 'dated login new',     'Dated Login New',     2005);
UPDATE cf.anime_titles SET status = 'READY'   WHERE anime_title_id = '00000000-0000-4000-8000-000000000013';
UPDATE cf.anime_titles SET status = 'BLOCKED' WHERE anime_title_id = '00000000-0000-4000-8000-000000000014';

\connect - cf_n8n_runtime

SELECT cf_test.expect_true('H3-40a this session is a real cf_n8n_runtime login',
  session_user = 'cf_n8n_runtime' AND current_user = 'cf_n8n_runtime');
SELECT cf_test.expect_denied('H3-41a real login denied: dated anime_title BLOCKED -> READY',
  $$UPDATE cf.anime_titles SET status = 'READY' WHERE anime_title_id = '00000000-0000-4000-8000-000000000014'$$);
SELECT cf_test.expect_denied('H3-42a real login denied: dated anime_title READY -> RETIRED',
  $$UPDATE cf.anime_titles SET status = 'RETIRED' WHERE anime_title_id = '00000000-0000-4000-8000-000000000013'$$);
SELECT cf_test.expect_ok('H3-43a real login: dated anime_title DRAFT -> READY works',
  $$UPDATE cf.anime_titles SET status = 'READY' WHERE anime_title_id = '00000000-0000-4000-8000-000000000015'$$);
SELECT cf_test.expect_error('H3-44a real login: a frozen column on a READY dated title still fails',
  $$UPDATE cf.anime_titles SET media_type = 'ONA' WHERE anime_title_id = '00000000-0000-4000-8000-000000000013'$$, 'CF_IMMUTABLE_ROW');
SELECT cf_test.expect_error('H3-45a real login: a dated title cannot be deleted',
  $$DELETE FROM cf.anime_titles WHERE anime_title_id = '00000000-0000-4000-8000-000000000013'$$, 'permission denied');

\connect - pgtest

-- ---------------------------------------------------------------------------
-- H3-6x: the pinned search_path really decides resolution. A hostile schema is
-- placed in front of pg_catalog in the SESSION path; the functions must ignore it.
-- ---------------------------------------------------------------------------
CREATE SCHEMA cf_evil;
CREATE FUNCTION cf_evil.now() RETURNS timestamptz LANGUAGE sql AS $$ SELECT '1999-01-01'::timestamptz $$;
CREATE FUNCTION cf_evil.to_jsonb(anyelement) RETURNS jsonb LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'EVIL to_jsonb was resolved'; END $$;
CREATE FUNCTION cf_evil.upper(text) RETURNS text LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'EVIL upper was resolved'; END $$;
CREATE FUNCTION cf_evil.md5(text) RETURNS text LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'EVIL md5 was resolved'; END $$;

SET search_path = cf_evil, pg_catalog;
SELECT cf_test.expect_ok('H3-60 hostile session search_path: a franchise status change on a READY row (guard + freeze + touch) still succeeds',
  $$UPDATE cf.anime_franchises SET status = 'BLOCKED' WHERE franchise_id = '00000000-0000-4000-8000-0000000000e2' AND status = 'DRAFT'$$);
SELECT cf_test.expect_ok('H3-61 hostile session search_path: freeze on a READY dated title (display_title change) does not resolve cf_evil.to_jsonb',
  $$UPDATE cf.anime_titles SET display_title = 'Renamed under hostile path' WHERE anime_title_id = '00000000-0000-4000-8000-000000000012'$$);
RESET search_path;
SELECT cf_test.expect_true('H3-62 updated_at was set by pg_catalog.now(), not by cf_evil.now() (no 1999 timestamp)',
  (SELECT updated_at > '2020-01-01'::timestamptz FROM cf.anime_titles WHERE anime_title_id = '00000000-0000-4000-8000-000000000012'));
SELECT cf_test.expect_true('H3-63 the functions hold search_path = pg_catalog, cf, which excludes the hostile and every non-cf schema',
  NOT EXISTS (SELECT 1 FROM pg_proc WHERE pronamespace = 'cf'::regnamespace
              AND proconfig IS DISTINCT FROM ARRAY['search_path=pg_catalog, cf']));

DROP SCHEMA cf_evil CASCADE;

-- ---------------------------------------------------------------------------
-- Final: this run left only its own fixture rows, all inside the local database
-- ---------------------------------------------------------------------------
SELECT cf_test.expect_true('H3-70 every fixture row is mine (fictional): 2 franchises, 5 dated titles, nothing in agent_runs, reviewers or research_candidates',
  (SELECT count(*) FROM cf.anime_franchises) = 2 AND (SELECT count(*) FROM cf.anime_titles) = 5
  AND (SELECT count(*) FROM cf.agent_runs) + (SELECT count(*) FROM cf.reviewers) + (SELECT count(*) FROM cf.research_candidates) = 0);
