-- 0004_cf002_scene_intelligence.TESTS.sql
-- LOCAL-ONLY behaviour tests. Never run against Supabase. Run as cf_n8n_runtime on a throwaway database that carries 0001-0004,
-- cf_test helpers (evidence/cf-002-tools/test/cf_test_helpers.sql) and the synthetic seed (evidence/cf-002-tools/test/seed_upstream.sql).
-- Output lines "PASS name" / "FAIL name" arrive as NOTICEs. Migration-level cases that need another role (wrong target, drift, rollback) are in run_cf002_tests.sh.
\set ON_ERROR_STOP on
SELECT cf_test.expect_true('T0 session is the restricted runtime role', session_user = 'cf_n8n_runtime' AND current_user = 'cf_n8n_runtime');
INSERT INTO cf.agent_runs (agent_code, agent_version, idempotency_key, input_ids, input_state_hash, run_state, attempt_count, provider_call_count, paid_call_count, estimated_cost_usd, started_at)
VALUES ('CF-002', 'v0.1', repeat('b', 64), '{}'::jsonb, repeat('c', 64), 'RUNNING', 1, 0, 0, 0, now());
SELECT agent_run_id::text AS rid FROM cf.agent_runs WHERE idempotency_key = repeat('b', 64) \gset

-- T9 stable episode identity
INSERT INTO cf.anime_source_episodes (anime_title_id, season_number, episode_number, episode_variant, episode_title_display, duration_seconds, status, agent_run_id)
VALUES ('22222222-2222-4222-8222-222222222222', 1, 12, 'TV', 'Synthetic', 1440, 'DRAFT', :'rid');
SELECT source_episode_id::text AS ep FROM cf.anime_source_episodes WHERE season_number = 1 AND episode_number = 12 \gset
SELECT cf_test.expect_err('T9a natural-key duplicate episode rejected (23505)', $q$INSERT INTO cf.anime_source_episodes (anime_title_id, season_number, episode_number, episode_variant, status) VALUES ('22222222-2222-4222-8222-222222222222', 1, 12.0, 'TV', 'DRAFT')$q$, '23505');
WITH i AS (INSERT INTO cf.anime_source_episodes (anime_title_id, season_number, episode_number, episode_variant, status) VALUES ('22222222-2222-4222-8222-222222222222', 1, 12, 'TV', 'DRAFT') ON CONFLICT ON CONSTRAINT source_episode_natural_key DO NOTHING RETURNING 1)
SELECT cf_test.expect_true('T9b replay ON CONFLICT inserts 0 rows, still 1 episode, same id', (SELECT count(*) FROM i) = 0 AND (SELECT count(*) FROM cf.anime_source_episodes) = 1 AND (SELECT source_episode_id::text FROM cf.anime_source_episodes) = :'ep');
INSERT INTO cf.anime_source_episodes (anime_title_id, season_number, episode_number, episode_variant, status) VALUES ('22222222-2222-4222-8222-222222222222', 1, 12, 'OVA', 'DRAFT');
SELECT cf_test.expect_true('T9c same number, different variant is a different episode; "Episode 12" text is not identity', (SELECT count(*) FROM cf.anime_source_episodes) = 2);
SELECT cf_test.expect_err('T9d episode of an unknown title rejected (23503)', $q$INSERT INTO cf.anime_source_episodes (anime_title_id, season_number, episode_number, status) VALUES ('99999999-9999-4999-8999-999999999999', 1, 1, 'DRAFT')$q$, '23503');
SELECT cf_test.expect_err('T9e episode inserted directly as READY rejected by the guard', $q$INSERT INTO cf.anime_source_episodes (anime_title_id, season_number, episode_number, status) VALUES ('22222222-2222-4222-8222-222222222222', 1, 13, 'READY')$q$, '.*');
UPDATE cf.anime_source_episodes SET status = 'READY' WHERE source_episode_id = :'ep';
SELECT cf_test.expect_true('T9f episode DRAFT -> READY (deterministic edge) works for the runtime', (SELECT status::text FROM cf.anime_source_episodes WHERE source_episode_id = :'ep') = 'READY');

-- T10 stable scene identity / T12 multiple scenes per episode
INSERT INTO cf.anime_scene_intelligence (source_episode_id, anime_title_id, research_candidate_id, start_ms, end_ms, characters_present, scene_summary, why_scene_matters, spoiler_level,
  research_source_platform, research_source_reference, research_access_basis, research_observed_at, research_observer, dedupe_key, status, agent_run_id, agent_version)
SELECT :'ep'::uuid, '22222222-2222-4222-8222-222222222222', '11111111-1111-4111-8111-111111111111', a, b, ARRAY['A'], 'Synthetic scene ' || a, 'Synthetic reason', 'LOW',
  'HUMAN_RESEARCH_OBSERVATION', 'human-observation:synthetic-0001', 'HUMAN_VIEWED_LICENSED_PLATFORM', now(), 'TEST',
  encode(sha256(convert_to(:'ep' || '|' || (a / 1000)::text || '|' || ((b + 999) / 1000)::text, 'UTF8')), 'hex'), 'DRAFT', :'rid', 'v0.1'
  FROM (VALUES (190000, 245000), (600000, 650000)) v(a, b);
SELECT cf_test.expect_true('T12 two legitimate scenes of one episode coexist (source_episode_id is not unique in scenes)', (SELECT count(*) FROM cf.anime_scene_intelligence WHERE source_episode_id = :'ep') = 2);
SELECT cf_test.expect_true('T12b no unique constraint or index on source_episode_id alone',
  NOT EXISTS (SELECT 1 FROM pg_index i WHERE i.indrelid = 'cf.anime_scene_intelligence'::regclass AND i.indisunique AND i.indnatts = 1 AND i.indkey[0] = (SELECT attnum FROM pg_attribute WHERE attrelid = i.indrelid AND attname = 'source_episode_id')));
SELECT scene_id::text AS sc1 FROM cf.anime_scene_intelligence WHERE start_ms = 190000 \gset
SELECT cf_test.expect_true('T10 dedupe_key = sha256(episode|floor(start s)|ceil(end s)), no summary/timestamp/random in it',
  (SELECT dedupe_key = encode(sha256(convert_to(source_episode_id::text || '|190|245', 'UTF8')), 'hex') FROM cf.anime_scene_intelligence WHERE scene_id = :'sc1'));

-- T11 duplicate-scene rejection / replay
SELECT cf_test.expect_err('T11a plain duplicate scene insert rejected (23505)', format($q$INSERT INTO cf.anime_scene_intelligence (source_episode_id, anime_title_id, start_ms, end_ms, scene_summary, why_scene_matters, spoiler_level, research_source_platform, research_source_reference, research_access_basis, research_observed_at, dedupe_key, status, agent_run_id, agent_version)
  SELECT %L::uuid, '22222222-2222-4222-8222-222222222222', 190000, 245000, 'x', 'y', 'LOW', 'HUMAN_RESEARCH_OBSERVATION', 'human-observation:other', 'SECONDARY_REFERENCE', now(), dedupe_key, 'DRAFT', %L::uuid, 'v0.1' FROM cf.anime_scene_intelligence WHERE scene_id = %L::uuid$q$, :'ep', :'rid', :'sc1'), '23505');
WITH i AS (INSERT INTO cf.anime_scene_intelligence (source_episode_id, anime_title_id, start_ms, end_ms, scene_summary, why_scene_matters, spoiler_level, research_source_platform, research_source_reference, research_access_basis, research_observed_at, dedupe_key, status, agent_run_id, agent_version)
  SELECT source_episode_id, anime_title_id, 190000, 245000, 'rediscovered with other words', 'y', 'LOW', 'OFFICIAL_YOUTUBE', 'https://example.org/watch/abc', 'PUBLIC_OFFICIAL_UPLOAD', now(), dedupe_key, 'DRAFT', agent_run_id, 'v0.1' FROM cf.anime_scene_intelligence WHERE scene_id = :'sc1'
  ON CONFLICT (dedupe_key) DO NOTHING RETURNING 1)
SELECT cf_test.expect_true('T11b same scene discovered twice (new words, new source) inserts 0 rows; original provenance kept', (SELECT count(*) FROM i) = 0 AND (SELECT count(*) FROM cf.anime_scene_intelligence) = 2
  AND (SELECT research_source_reference FROM cf.anime_scene_intelligence WHERE scene_id = :'sc1') = 'human-observation:synthetic-0001' AND (SELECT scene_id::text FROM cf.anime_scene_intelligence WHERE start_ms = 190000) = :'sc1');
-- overlapping but materially distinct range (<80% of the shorter span) is its own scene
INSERT INTO cf.anime_scene_intelligence (source_episode_id, anime_title_id, start_ms, end_ms, scene_summary, why_scene_matters, spoiler_level, research_source_platform, research_source_reference, research_access_basis, research_observed_at, dedupe_key, status, agent_run_id, agent_version)
SELECT source_episode_id, anime_title_id, 230000, 330000, 'overlapping distinct scene', 'y', 'LOW', 'HUMAN_RESEARCH_OBSERVATION', 'human-observation:synthetic-0002', 'SECONDARY_REFERENCE', now(),
  encode(sha256(convert_to(source_episode_id::text || '|230|330', 'UTF8')), 'hex'), 'DRAFT', agent_run_id, 'v0.1' FROM cf.anime_scene_intelligence WHERE scene_id = :'sc1';
SELECT cf_test.expect_true('T11c overlapping-but-distinct range gets its own scene id (3 scenes, 3 distinct keys)', (SELECT count(DISTINCT dedupe_key) FROM cf.anime_scene_intelligence) = 3);

-- T13 invalid timestamps
SELECT cf_test.expect_err('T13a end = start rejected (23514)', format($q$UPDATE cf.anime_scene_intelligence SET status = status WHERE false; INSERT INTO cf.anime_scene_intelligence (source_episode_id, anime_title_id, start_ms, end_ms, scene_summary, why_scene_matters, spoiler_level, research_source_platform, research_source_reference, research_access_basis, research_observed_at, dedupe_key, status, agent_run_id, agent_version) VALUES (%L, '22222222-2222-4222-8222-222222222222', 5000, 5000, 'x', 'y', 'LOW', 'HUMAN_RESEARCH_OBSERVATION', 'human-observation:t', 'SECONDARY_REFERENCE', now(), repeat('1', 64), 'DRAFT', %L, 'v0.1')$q$, :'ep', :'rid'), '23514', 'scene_positive_span');
SELECT cf_test.expect_err('T13b end < start rejected (23514)', format($q$INSERT INTO cf.anime_scene_intelligence (source_episode_id, anime_title_id, start_ms, end_ms, scene_summary, why_scene_matters, spoiler_level, research_source_platform, research_source_reference, research_access_basis, research_observed_at, dedupe_key, status, agent_run_id, agent_version) VALUES (%L, '22222222-2222-4222-8222-222222222222', 9000, 5000, 'x', 'y', 'LOW', 'HUMAN_RESEARCH_OBSERVATION', 'human-observation:t', 'SECONDARY_REFERENCE', now(), repeat('2', 64), 'DRAFT', %L, 'v0.1')$q$, :'ep', :'rid'), '23514');
SELECT cf_test.expect_err('T13c negative start rejected (23514)', format($q$INSERT INTO cf.anime_scene_intelligence (source_episode_id, anime_title_id, start_ms, end_ms, scene_summary, why_scene_matters, spoiler_level, research_source_platform, research_source_reference, research_access_basis, research_observed_at, dedupe_key, status, agent_run_id, agent_version) VALUES (%L, '22222222-2222-4222-8222-222222222222', -1, 5000, 'x', 'y', 'LOW', 'HUMAN_RESEARCH_OBSERVATION', 'human-observation:t', 'SECONDARY_REFERENCE', now(), repeat('3', 64), 'DRAFT', %L, 'v0.1')$q$, :'ep', :'rid'), '23514');
SELECT cf_test.expect_err('T13d end beyond 24h rejected (23514)', format($q$INSERT INTO cf.anime_scene_intelligence (source_episode_id, anime_title_id, start_ms, end_ms, scene_summary, why_scene_matters, spoiler_level, research_source_platform, research_source_reference, research_access_basis, research_observed_at, dedupe_key, status, agent_run_id, agent_version) VALUES (%L, '22222222-2222-4222-8222-222222222222', 5000, 86400001, 'x', 'y', 'LOW', 'HUMAN_RESEARCH_OBSERVATION', 'human-observation:t', 'SECONDARY_REFERENCE', now(), repeat('4', 64), 'DRAFT', %L, 'v0.1')$q$, :'ep', :'rid'), '23514');

-- T14 missing / invalid provenance (each statement varies exactly one provenance field)
CREATE TEMP TABLE prov_cases (n text, col text, val text, st text);
INSERT INTO prov_cases VALUES
 ('NULL source reference', 'research_source_reference', 'NULL', '23502'), ('empty source reference', 'research_source_reference', $v$''$v$, '23514'),
 ('secret-looking reference (token=)', 'research_source_reference', $v$'https://example.org/w?token=abc'$v$, '23514'), ('cookie in reference', 'research_source_reference', $v$'cookie:abc123'$v$, '23514'),
 ('NULL access basis', 'research_access_basis', 'NULL', '23502'), ('access basis not in enum (LICENSED)', 'research_access_basis', $v$'LICENSED'$v$, '22P02'),
 ('NULL observed_at', 'research_observed_at', 'NULL', '23502'), ('NULL platform', 'research_source_platform', 'NULL', '23502'), ('lower-case platform', 'research_source_platform', $v$'crunchyroll'$v$, '23514'),
 ('NULL summary', 'scene_summary', 'NULL', '23502'), ('blank summary', 'scene_summary', $v$'   '$v$, '23514'), ('summary over 800 chars', 'scene_summary', $v$repeat('x', 801)$v$, '23514'),
 ('NULL why_scene_matters', 'why_scene_matters', 'NULL', '23502'), ('bad spoiler level', 'spoiler_level', $v$'ALL'$v$, '23514'), ('NULL agent_run_id', 'agent_run_id', 'NULL', '23502');
DO $$
DECLARE c record;
BEGIN
  FOR c IN SELECT * FROM prov_cases LOOP
    PERFORM cf_test.expect_err('T14 rejected: ' || c.n, 'INSERT INTO cf.anime_scene_intelligence (source_episode_id, anime_title_id, start_ms, end_ms, scene_summary, why_scene_matters, spoiler_level, research_source_platform, research_source_reference, research_access_basis, research_observed_at, dedupe_key, status, agent_run_id, agent_version) SELECT source_episode_id, anime_title_id, 7000, 8000, '
      || CASE WHEN c.col = 'scene_summary' THEN c.val ELSE '''x''' END || ', ' || CASE WHEN c.col = 'why_scene_matters' THEN c.val ELSE '''y''' END || ', ' || CASE WHEN c.col = 'spoiler_level' THEN c.val ELSE '''LOW''' END || ', '
      || CASE WHEN c.col = 'research_source_platform' THEN c.val ELSE '''HUMAN_RESEARCH_OBSERVATION''' END || ', ' || CASE WHEN c.col = 'research_source_reference' THEN c.val ELSE '''human-observation:t''' END || ', '
      || CASE WHEN c.col = 'research_access_basis' THEN c.val ELSE '''SECONDARY_REFERENCE''' END || '::cf.research_access_basis, ' || CASE WHEN c.col = 'research_observed_at' THEN c.val ELSE 'now()' END || ', repeat(''5'', 64), ''DRAFT'', '
      || CASE WHEN c.col = 'agent_run_id' THEN c.val ELSE 'agent_run_id' END || ', ''v0.1'' FROM cf.anime_scene_intelligence LIMIT 1', c.st);
  END LOOP;
END $$;
SELECT cf_test.expect_err('T14 rejected: bad editorial_strength / visual_strength (separate columns)', $q$INSERT INTO cf.anime_scene_intelligence (source_episode_id, anime_title_id, start_ms, end_ms, scene_summary, why_scene_matters, spoiler_level, research_source_platform, research_source_reference, research_access_basis, research_observed_at, dedupe_key, status, agent_run_id, agent_version, editorial_strength) SELECT source_episode_id, anime_title_id, 7000, 8000, 'x', 'y', 'LOW', 'HUMAN_RESEARCH_OBSERVATION', 'human-observation:t', 'SECONDARY_REFERENCE', now(), repeat('6', 64), 'DRAFT', agent_run_id, 'v0.1', 'APPROVED' FROM cf.anime_scene_intelligence LIMIT 1$q$, '23514');
SELECT cf_test.expect_err('T14 rejected: scene with a title that does not own the episode (composite FK)', $q$INSERT INTO cf.anime_scene_intelligence (source_episode_id, anime_title_id, start_ms, end_ms, scene_summary, why_scene_matters, spoiler_level, research_source_platform, research_source_reference, research_access_basis, research_observed_at, dedupe_key, status, agent_run_id, agent_version) SELECT source_episode_id, '33333333-3333-4333-8333-333333333333', 7000, 8000, 'x', 'y', 'LOW', 'HUMAN_RESEARCH_OBSERVATION', 'human-observation:t', 'SECONDARY_REFERENCE', now(), repeat('7', 64), 'DRAFT', agent_run_id, 'v0.1' FROM cf.anime_scene_intelligence LIMIT 1$q$, '23503');
INSERT INTO cf.anime_source_episodes (anime_title_id, season_number, episode_number, status) VALUES ('33333333-3333-4333-8333-333333333333', 1, 1, 'DRAFT');
SELECT cf_test.expect_err('T14 rejected: candidate that belongs to a different title (scene_candidate_title_fk)', format($q$INSERT INTO cf.anime_scene_intelligence (source_episode_id, anime_title_id, research_candidate_id, start_ms, end_ms, scene_summary, why_scene_matters, spoiler_level, research_source_platform, research_source_reference, research_access_basis, research_observed_at, dedupe_key, status, agent_run_id, agent_version) SELECT e.source_episode_id, e.anime_title_id, '11111111-1111-4111-8111-111111111111', 7000, 8000, 'x', 'y', 'LOW', 'HUMAN_RESEARCH_OBSERVATION', 'human-observation:t', 'SECONDARY_REFERENCE', now(), repeat('8', 64), 'DRAFT', %L::uuid, 'v0.1' FROM cf.anime_source_episodes e WHERE e.anime_title_id = '33333333-3333-4333-8333-333333333333'$q$, :'rid'), '23503', 'scene_candidate_title_fk');
SELECT cf_test.expect_err('T14 rejected: visual_strength above 1', $q$INSERT INTO cf.anime_scene_intelligence (source_episode_id, anime_title_id, start_ms, end_ms, scene_summary, why_scene_matters, spoiler_level, research_source_platform, research_source_reference, research_access_basis, research_observed_at, dedupe_key, status, agent_run_id, agent_version, visual_strength) SELECT source_episode_id, anime_title_id, 7000, 8000, 'x', 'y', 'LOW', 'HUMAN_RESEARCH_OBSERVATION', 'human-observation:t', 'SECONDARY_REFERENCE', now(), repeat('9', 64), 'DRAFT', agent_run_id, 'v0.1', 1.2 FROM cf.anime_scene_intelligence LIMIT 1$q$, '23514|22003');
SELECT cf_test.expect_err('T14 rejected: bad dedupe_key shape', $q$INSERT INTO cf.anime_scene_intelligence (source_episode_id, anime_title_id, start_ms, end_ms, scene_summary, why_scene_matters, spoiler_level, research_source_platform, research_source_reference, research_access_basis, research_observed_at, dedupe_key, status, agent_run_id, agent_version) SELECT source_episode_id, anime_title_id, 7000, 8000, 'x', 'y', 'LOW', 'HUMAN_RESEARCH_OBSERVATION', 'human-observation:t', 'SECONDARY_REFERENCE', now(), 'not-a-hash', 'DRAFT', agent_run_id, 'v0.1' FROM cf.anime_scene_intelligence LIMIT 1$q$, '23514');

-- T15 publication defaults fail closed
SELECT cf_test.expect_true('T15a every scene reads publication_source_status UNKNOWN', (SELECT count(*) FROM cf.v_scene_publication_status) = (SELECT count(*) FROM cf.anime_scene_intelligence) AND (SELECT bool_and(publication_source_status = 'UNKNOWN') FROM cf.v_scene_publication_status));
SELECT cf_test.expect_err('T15b cannot insert a publication_source_status column (42703)', $q$INSERT INTO cf.anime_scene_intelligence (publication_source_status) VALUES ('APPROVED')$q$, '42703');
SELECT cf_test.expect_err('T15c cannot write the status view (not updatable; no privilege)', $q$UPDATE cf.v_scene_publication_status SET publication_source_status = 'APPROVED'$q$, '42501|0A000');
SELECT cf_test.expect_err('T15d status APPROVED / PUBLISHED / CLEARED refused on scenes', $q$UPDATE cf.anime_scene_intelligence SET status = 'APPROVED'$q$, '23514|P0001|42501|22P02');
SELECT cf_test.expect_err('T15e status PUBLISHED refused on scenes', $q$UPDATE cf.anime_scene_intelligence SET status = 'PUBLISHED'$q$, '23514|P0001|42501|22P02');
SELECT cf_test.expect_err('T15f research_access_basis cannot be changed afterwards (no column grant)', $q$UPDATE cf.anime_scene_intelligence SET research_access_basis = 'PUBLIC_OFFICIAL_UPLOAD'$q$, '42501');
SELECT cf_test.expect_true('T15g no scene row carries a rights claim in its stored notes', NOT EXISTS (SELECT 1 FROM cf.anime_scene_intelligence WHERE research_access_notes ~* '(approved|cleared|fair use|licensed for|safe to)'));

-- T5 / T7 / T8 runtime privilege matrix (behavioural)
SELECT cf_test.expect_err('T7a runtime DELETE on scenes denied', $q$DELETE FROM cf.anime_scene_intelligence$q$, '42501');
SELECT cf_test.expect_err('T7b runtime DELETE on episodes denied', $q$DELETE FROM cf.anime_source_episodes$q$, '42501');
SELECT cf_test.expect_err('T7c runtime TRUNCATE denied', $q$TRUNCATE cf.anime_scene_intelligence$q$, '42501');
SELECT cf_test.expect_err('T5a runtime cannot UPDATE scene text (column-level grant only)', $q$UPDATE cf.anime_scene_intelligence SET scene_summary = 'changed'$q$, '42501');
SELECT cf_test.expect_err('T5b runtime cannot UPDATE source_episode_id', $q$UPDATE cf.anime_scene_intelligence SET source_episode_id = source_episode_id$q$, '42501');
SELECT cf_test.expect_err('T5c runtime cannot UPDATE episode season/number', $q$UPDATE cf.anime_source_episodes SET episode_number = 99$q$, '42501');
SELECT cf_test.expect_err('T5d runtime cannot write reviewers', $q$INSERT INTO cf.reviewers DEFAULT VALUES$q$, '42501');
SELECT cf_test.expect_err('T5e runtime cannot enable a kill switch', $q$UPDATE cf.system_flags SET enabled = true$q$, '42501');
SELECT cf_test.expect_err('T5f runtime cannot add a transition', $q$INSERT INTO cf.allowed_transitions (object_type, from_status, to_status, mode) VALUES ('scene', 'READY', 'PUBLISHED', 'DETERMINISTIC')$q$, '42501');
SELECT cf_test.expect_err('T5g runtime cannot disable a trigger', $q$ALTER TABLE cf.anime_scene_intelligence DISABLE TRIGGER USER$q$, '42501');
SELECT cf_test.expect_err('T5h runtime cannot change session_replication_role', $q$SET session_replication_role = replica$q$, '42501');
SELECT cf_test.expect_err('T5i runtime cannot call cf functions', $q$SELECT cf.forbid_delete()$q$, '42501');
GRANT DELETE ON cf.anime_scene_intelligence TO cf_n8n_runtime;
SELECT cf_test.expect_true('T5j a GRANT by the runtime role grants nothing (it is not the owner)', NOT has_table_privilege('cf_n8n_runtime', 'cf.anime_scene_intelligence', 'DELETE'));
SELECT cf_test.expect_err('T5k runtime cannot SET ROLE postgres', $q$SET ROLE postgres$q$, '42501');
SELECT cf_test.expect_err('T8a runtime cannot CREATE TABLE in cf', $q$CREATE TABLE cf.cf003_probe (i int)$q$, '42501');
SELECT cf_test.expect_err('T8b runtime cannot CREATE TABLE in public', $q$CREATE TABLE public.cf003_probe (i int)$q$, '42501');
SELECT cf_test.expect_err('T8c runtime cannot CREATE a function in cf', $q$CREATE FUNCTION cf.probe() RETURNS int LANGUAGE sql AS 'select 1'$q$, '42501');
SELECT cf_test.expect_true('T6 Supabase API roles have no access to the new tables and view', NOT (SELECT bool_or(has_table_privilege(r, t, p)) FROM unnest(ARRAY['anon','authenticated','service_role']) r, unnest(ARRAY['cf.anime_scene_intelligence','cf.anime_source_episodes','cf.v_scene_publication_status']) t, unnest(ARRAY['SELECT','INSERT','UPDATE','DELETE']) p));
SELECT cf_test.expect_true('T5l no CF-003+ table exists (10 cf objects)', (SELECT count(*) FROM pg_class WHERE relnamespace = 'cf'::regnamespace AND relkind IN ('r','v','p','m','f')) = 10);

-- T16 F-2: HUMAN_ADMIN edges stay denied to the runtime on the new objects
SELECT cf_test.expect_err('T16a runtime scene DRAFT -> REJECTED (HUMAN_ADMIN) denied', $q$UPDATE cf.anime_scene_intelligence SET status = 'REJECTED' WHERE status = 'DRAFT'$q$, '42501', 'CF_GOVERNANCE_DENIED');
SELECT cf_test.expect_err('T16b runtime episode READY -> RETIRED (HUMAN_ADMIN) denied', $q$UPDATE cf.anime_source_episodes SET status = 'RETIRED' WHERE status = 'READY'$q$, '42501', 'CF_GOVERNANCE_DENIED');
UPDATE cf.anime_source_episodes SET status = 'BLOCKED' WHERE episode_variant = 'OVA';
SELECT cf_test.expect_true('T16c DRAFT -> BLOCKED (deterministic) works for the runtime', (SELECT status::text FROM cf.anime_source_episodes WHERE episode_variant = 'OVA') = 'BLOCKED');
SELECT cf_test.expect_err('T16d runtime episode BLOCKED -> READY (HUMAN_ADMIN) denied', $q$UPDATE cf.anime_source_episodes SET status = 'READY' WHERE status = 'BLOCKED'$q$, '42501', 'CF_GOVERNANCE_DENIED');

-- scene lifecycle: DRAFT -> READY (deterministic) and the one mutable evidence column
UPDATE cf.anime_scene_intelligence SET status = 'READY' WHERE scene_id = :'sc1';
SELECT cf_test.expect_true('T10b scene DRAFT -> READY works; scene_id and key unchanged', (SELECT status::text = 'READY' AND dedupe_key = encode(sha256(convert_to(source_episode_id::text || '|190|245', 'UTF8')), 'hex') FROM cf.anime_scene_intelligence WHERE scene_id = :'sc1'));
UPDATE cf.anime_scene_intelligence SET timestamps_human_verified = true WHERE scene_id = :'sc1';
SELECT cf_test.expect_true('T17a timestamps_human_verified is the one mutable evidence column and works', (SELECT timestamps_human_verified FROM cf.anime_scene_intelligence WHERE scene_id = :'sc1'));
SELECT cf_test.expect_true('T0b kill switches stay false', NOT EXISTS (SELECT 1 FROM cf.system_flags WHERE enabled));
