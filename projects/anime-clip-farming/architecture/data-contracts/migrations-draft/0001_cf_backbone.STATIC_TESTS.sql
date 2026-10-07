-- =============================================================================
-- DESIGN ONLY — NOT APPLIED — STATIC TESTS FOR 0001_cf_backbone.DESIGN_ONLY.sql
-- =============================================================================
-- Run ONLY against a throwaway local PostgreSQL instance that has just loaded
-- 0001_cf_backbone.DESIGN_ONLY.sql. Never run against Supabase.
-- All data below is fictional fixture data. Every assertion raises on failure.
--   psql -v ON_ERROR_STOP=1 -f 0001_cf_backbone.DESIGN_ONLY.sql
--   psql -v ON_ERROR_STOP=1 -f 0001_cf_backbone.STATIC_TESTS.sql
-- Expected output: one "PASS <id>" notice per test and no "FAIL".
-- =============================================================================

SET client_min_messages = warning;

-- Test helpers live in a throwaway schema so the role tests can call them.
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

SET client_min_messages = notice;

-- ---------------------------------------------------------------------------
-- Fixtures (fictional). UUID suffixes: a=run f=franchise b=title e=episode
-- c=research d=scene 1x=opportunity 2x=script 3x=package 4x=manifest
-- ---------------------------------------------------------------------------
INSERT INTO cf.reviewers (reviewer_id, display_name, allowed_gates) VALUES
  ('00000000-0000-4000-8000-000000000001', 'Fixture Reviewer (all gates)', '{G1,G2,G3,G4}'),
  ('00000000-0000-4000-8000-000000000002', 'Fixture Reviewer (G1 only)',   '{G1}');

INSERT INTO cf.agent_runs (agent_run_id, agent_code, agent_version, idempotency_key, input_state_hash)
VALUES ('00000000-0000-4000-8000-0000000000a1', 'CF-001', 'fixture', 'run-key-1', 'h');

INSERT INTO cf.anime_franchises (franchise_id, normalised_key, display_name, agent_run_id)
VALUES ('00000000-0000-4000-8000-0000000000f1', 'fixture franchise', 'Fixture Franchise', '00000000-0000-4000-8000-0000000000a1');
INSERT INTO cf.anime_franchises (franchise_id, normalised_key, display_name, agent_run_id)
VALUES ('00000000-0000-4000-8000-0000000000f2', 'other franchise', 'Other Franchise', '00000000-0000-4000-8000-0000000000a1');

INSERT INTO cf.anime_titles (anime_title_id, franchise_id, normalised_title_key, display_title, start_year, anilist_id)
VALUES ('00000000-0000-4000-8000-0000000000b1', '00000000-0000-4000-8000-0000000000f1', 'fixture title', 'Fixture Title', 2004, 999001);

INSERT INTO cf.anime_source_episodes (source_episode_id, anime_title_id, season_number, episode_number)
VALUES ('00000000-0000-4000-8000-0000000000e1', '00000000-0000-4000-8000-0000000000b1', 1, 7);

INSERT INTO cf.research_candidates (research_candidate_id, anime_title_id, franchise_id, topic_key, topic_display,
  content_lane, signal_evidence, observation_window, dedupe_key, agent_run_id, agent_version)
VALUES ('00000000-0000-4000-8000-0000000000c1', '00000000-0000-4000-8000-0000000000b1', '00000000-0000-4000-8000-0000000000f1',
  'fixture topic', 'Fixture topic', '2000s Nostalgia', '[{"source":"fixture","url":"https://example.invalid"}]', '2026-W41',
  'rc-dedupe-1', '00000000-0000-4000-8000-0000000000a1', 'fixture');

INSERT INTO cf.anime_scene_intelligence (scene_id, source_episode_id, anime_title_id, start_ms, end_ms, scene_summary,
  why_scene_matters, spoiler_level, research_source_platform, research_source_reference, research_access_basis,
  dedupe_key, agent_run_id, agent_version)
VALUES ('00000000-0000-4000-8000-0000000000d1', '00000000-0000-4000-8000-0000000000e1', '00000000-0000-4000-8000-0000000000b1',
  60000, 95000, 'Fixture scene', 'Fixture reason', 'LOW', 'FIXTURE_PLATFORM', 'fixture-ref', 'HUMAN_VIEWED_LICENSED_PLATFORM',
  'scene-dedupe-1', '00000000-0000-4000-8000-0000000000a1', 'fixture');

INSERT INTO cf.editorial_opportunities (content_candidate_id, primary_scene_id, anime_title_id, editorial_angle_key,
  working_hook, content_lane, format_class, estimated_duration_seconds, why_viewer_cares, hypothesis, primary_metric,
  content_sha256, dedupe_key, output_ordinal, agent_run_id, agent_version)
VALUES ('00000000-0000-4000-8000-000000000011', '00000000-0000-4000-8000-0000000000d1', '00000000-0000-4000-8000-0000000000b1',
  'growing-up reinterpretation', 'Fixture hook', '2000s Nostalgia', 'CORE_ANALYSIS', 50, 'Fixture', 'Fixture', 'completion_rate',
  'sha-opp-1', 'opp-dedupe-1', 0, '00000000-0000-4000-8000-0000000000a1', 'fixture');

-- ---------------------------------------------------------------------------
-- Identity / dedupe
-- ---------------------------------------------------------------------------
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

SELECT cf_test.expect_error('T-ID-04 duplicate episode natural key rejected',
  $$INSERT INTO cf.anime_source_episodes (anime_title_id, season_number, episode_number)
    VALUES ('00000000-0000-4000-8000-0000000000b1', 1, 7)$$, 'duplicate key');

SELECT cf_test.expect_error('T-ID-05 research candidate without evidence rejected',
  $$INSERT INTO cf.research_candidates (anime_title_id, franchise_id, topic_key, topic_display, content_lane,
      signal_evidence, observation_window, dedupe_key, agent_run_id, agent_version)
    VALUES ('00000000-0000-4000-8000-0000000000b1', '00000000-0000-4000-8000-0000000000f1', 'y', 'y', 'y',
      '[]', '2026-W41', 'rc-dedupe-2', '00000000-0000-4000-8000-0000000000a1', 'fixture')$$, 'signal_evidence');

SELECT cf_test.expect_error('T-ID-06 scene with non-positive span rejected',
  $$INSERT INTO cf.anime_scene_intelligence (source_episode_id, anime_title_id, start_ms, end_ms, scene_summary,
      why_scene_matters, spoiler_level, research_source_platform, research_source_reference, research_access_basis,
      dedupe_key, agent_run_id, agent_version)
    VALUES ('00000000-0000-4000-8000-0000000000e1', '00000000-0000-4000-8000-0000000000b1', 5000, 5000, 'x', 'x', 'LOW',
      'P', 'r', 'SECONDARY_REFERENCE', 'scene-dedupe-2', '00000000-0000-4000-8000-0000000000a1', 'fixture')$$, 'scene_positive_span');

SELECT cf_test.expect_error('T-ID-07 scene without research provenance rejected',
  $$INSERT INTO cf.anime_scene_intelligence (source_episode_id, anime_title_id, start_ms, end_ms, scene_summary,
      why_scene_matters, spoiler_level, research_source_reference, research_access_basis,
      dedupe_key, agent_run_id, agent_version)
    VALUES ('00000000-0000-4000-8000-0000000000e1', '00000000-0000-4000-8000-0000000000b1', 1000, 5000, 'x', 'x', 'LOW',
      'r', 'SECONDARY_REFERENCE', 'scene-dedupe-3', '00000000-0000-4000-8000-0000000000a1', 'fixture')$$, 'research_source_platform');

-- ---------------------------------------------------------------------------
-- State machine and G1
-- ---------------------------------------------------------------------------
SELECT cf_test.expect_error('T-ST-01 invalid insert status (APPROVED at birth) rejected',
  $$INSERT INTO cf.editorial_opportunities (anime_title_id, editorial_angle_key, working_hook, content_lane, format_class,
      estimated_duration_seconds, why_viewer_cares, hypothesis, primary_metric, content_sha256, dedupe_key, output_ordinal,
      agent_run_id, agent_version, status)
    VALUES ('00000000-0000-4000-8000-0000000000b1', 'z', 'z', 'z', 'DISCOVERY_SHORT', 30, 'z', 'z', 'z', 's', 'opp-dedupe-z', 9,
      '00000000-0000-4000-8000-0000000000a1', 'fixture', 'APPROVED')$$, 'CF_INVALID_TRANSITION');

SELECT cf_test.expect_error('T-ST-02 skipping REVIEW (IDEA -> APPROVED) rejected',
  $$UPDATE cf.editorial_opportunities SET status = 'APPROVED' WHERE content_candidate_id = '00000000-0000-4000-8000-000000000011'$$,
  'CF_INVALID_TRANSITION');

UPDATE cf.editorial_opportunities SET status = 'REVIEW' WHERE content_candidate_id = '00000000-0000-4000-8000-000000000011';

SELECT cf_test.expect_error('T-GATE-01 REVIEW -> APPROVED without a gate decision rejected (AI recommendation is not approval)',
  $$UPDATE cf.editorial_opportunities SET status = 'APPROVED'
    WHERE content_candidate_id = '00000000-0000-4000-8000-000000000011'$$, 'CF_GATE_DECISION_MISSING');

SELECT cf_test.expect_error('T-IMM-01 editorial content frozen once in REVIEW',
  $$UPDATE cf.editorial_opportunities SET working_hook = 'changed' WHERE content_candidate_id = '00000000-0000-4000-8000-000000000011'$$,
  'CF_IMMUTABLE_ROW');

SELECT cf_test.expect_error('T-GATE-02 unauthorised reviewer for gate rejected',
  $$SELECT cf.record_gate_decision('G2', '00000000-0000-4000-8000-000000000011', 'APPROVE',
      '00000000-0000-4000-8000-000000000002', 'k-unauth', 'TEST')$$, 'CF_REVIEWER_NOT_AUTHORISED');

SELECT cf_test.expect_error('T-GATE-03 stale review (content hash changed since viewing) rejected',
  $$SELECT cf.record_gate_decision('G1', '00000000-0000-4000-8000-000000000011', 'APPROVE',
      '00000000-0000-4000-8000-000000000001', 'k-stale', 'TEST', NULL, NULL, 'sha-old')$$, 'CF_STALE_REVIEW');

SELECT cf_test.expect_error('T-GATE-04 unknown object rejected',
  $$SELECT cf.record_gate_decision('G1', '00000000-0000-4000-8000-0000000000ff', 'APPROVE',
      '00000000-0000-4000-8000-000000000001', 'k-missing', 'TEST')$$, 'CF_OBJECT_NOT_FOUND');

SELECT cf.record_gate_decision('G1', '00000000-0000-4000-8000-000000000011', 'APPROVE',
  '00000000-0000-4000-8000-000000000001', 'k-g1-approve', 'TEST', 'fixture approval', NULL, 'sha-opp-1');

SELECT cf_test.expect_true('T-GATE-05 G1 approval persisted and status APPROVED',
  (SELECT status = 'APPROVED' FROM cf.editorial_opportunities WHERE content_candidate_id = '00000000-0000-4000-8000-000000000011'));

SELECT cf_test.expect_true('T-RPL-01 replaying the same G1 submission writes nothing new',
  cf.record_gate_decision('G1', '00000000-0000-4000-8000-000000000011', 'APPROVE',
     '00000000-0000-4000-8000-000000000001', 'k-g1-approve', 'TEST')
  = (SELECT gate_decision_id FROM cf.gate_decisions WHERE idempotency_key = 'k-g1-approve')
  AND (SELECT count(*) FROM cf.gate_decisions) = 1);

SELECT cf_test.expect_error('T-APP-01 gate decisions are append-only (no UPDATE)',
  $$UPDATE cf.gate_decisions SET notes = 'edited'$$, 'CF_APPEND_ONLY');
SELECT cf_test.expect_error('T-APP-02 gate decisions are append-only (no DELETE)',
  $$DELETE FROM cf.gate_decisions$$, 'CF_APPEND_ONLY');
SELECT cf_test.expect_error('T-APP-03 lifecycle rows are never deleted',
  $$DELETE FROM cf.editorial_opportunities$$, 'CF_NO_DELETE');

-- ---------------------------------------------------------------------------
-- G2 / G3 separation: script approved while publication source stays blocked
-- ---------------------------------------------------------------------------
INSERT INTO cf.content_scripts (script_id, content_candidate_id, format_class, target_duration_seconds, hook, thesis,
  narration_text, content_sha256, agent_run_id, agent_version)
VALUES ('00000000-0000-4000-8000-000000000021', '00000000-0000-4000-8000-000000000011', 'CORE_ANALYSIS', 50,
  'Fixture hook', 'Fixture thesis', 'Fixture narration', 'sha-script-1', '00000000-0000-4000-8000-0000000000a1', 'fixture');
UPDATE cf.content_scripts SET status = 'REVIEW' WHERE script_id = '00000000-0000-4000-8000-000000000021';
SELECT cf.record_gate_decision('G2', '00000000-0000-4000-8000-000000000021', 'APPROVE',
  '00000000-0000-4000-8000-000000000001', 'k-g2-approve', 'TEST');

INSERT INTO cf.publication_source_packages (source_package_id, script_id, package_summary, content_sha256, agent_run_id, agent_version)
VALUES ('00000000-0000-4000-8000-000000000031', '00000000-0000-4000-8000-000000000021', 'Fixture: nothing acceptable found',
  'sha-pkg-1', '00000000-0000-4000-8000-0000000000a1', 'fixture');

SELECT cf_test.expect_error('T-SRC-01 BLOCKED package must say why',
  $$UPDATE cf.publication_source_packages SET status = 'BLOCKED' WHERE source_package_id = '00000000-0000-4000-8000-000000000031'$$,
  'blocked_needs_reason');

UPDATE cf.publication_source_packages SET status = 'BLOCKED', blocked_reason = 'NO_ACCEPTABLE_SOURCE'
 WHERE source_package_id = '00000000-0000-4000-8000-000000000031';

SELECT cf_test.expect_true('T-SRC-02 approved script + blocked source package is a valid state',
  (SELECT status = 'APPROVED' FROM cf.content_scripts WHERE script_id = '00000000-0000-4000-8000-000000000021')
  AND (SELECT status = 'BLOCKED' FROM cf.publication_source_packages WHERE source_package_id = '00000000-0000-4000-8000-000000000031'));

SELECT cf_test.expect_true('T-SRC-03 scene publication status stays UNKNOWN (research access is not permission)',
  (SELECT publication_source_status = 'UNKNOWN' FROM cf.v_scene_publication_status WHERE scene_id = '00000000-0000-4000-8000-0000000000d1'));

SELECT cf_test.expect_error('T-SRC-04 BLOCKED package cannot be approved',
  $$SELECT cf.record_gate_decision('G3', '00000000-0000-4000-8000-000000000031', 'APPROVE',
      '00000000-0000-4000-8000-000000000001', 'k-g3-blocked', 'TEST')$$, 'CF_NOT_IN_REVIEW');

SELECT cf_test.expect_error('T-SRC-05 a manifest needs a source package that exists',
  $$INSERT INTO cf.production_manifests (script_id, source_package_id, manifest_schema_version, planner_version, input_hash,
      segment_plan, audio_plan, caption_plan, asset_requirements, target_runtime_seconds, render_specification, content_sha256,
      agent_run_id, agent_version)
    VALUES ('00000000-0000-4000-8000-000000000021', '00000000-0000-4000-8000-0000000000ff', 'v', 'v', 'ih', '[]', '{}', '{}', '[]', 50, '{}',
      's', '00000000-0000-4000-8000-0000000000a1', 'fixture')$$, 'foreign key');

-- ---------------------------------------------------------------------------
-- Rights vocabulary and spend / publish guards
-- ---------------------------------------------------------------------------
SELECT cf_test.expect_true('T-RIGHTS-01 no automated legal-determination column exists anywhere in cf',
  NOT EXISTS (SELECT 1 FROM information_schema.columns
              WHERE table_schema = 'cf' AND column_name ~* '(fair_?use|copyright_?safe|legal_?safe|is_legal|rights_?cleared)'));

SELECT cf_test.expect_error('T-PAID-01 paid call count without authorisation reference rejected',
  $$INSERT INTO cf.agent_runs (agent_code, agent_version, idempotency_key, input_state_hash, provider_call_count, paid_call_count)
    VALUES ('CF-002', 'fixture', 'run-key-paid', 'h', 1, 1)$$, 'paid_calls_need_authorisation');

SELECT cf_test.expect_error('T-PAID-02 wrong agent namespace rejected (AGENT-00x is the Kids system)',
  $$INSERT INTO cf.agent_runs (agent_code, agent_version, idempotency_key, input_state_hash)
    VALUES ('AGENT-001', 'fixture', 'run-key-ns', 'h')$$, 'agent_runs_agent_code_check');

SELECT cf_test.expect_true('T-PUB-01 all kill switches default OFF',
  NOT EXISTS (SELECT 1 FROM cf.system_flags WHERE enabled));

SELECT cf_test.expect_true('T-PUB-02 nothing is publish-eligible',
  NOT EXISTS (SELECT 1 FROM cf.v_publish_eligibility));

-- ---------------------------------------------------------------------------
-- Privileges: the agent role cannot write approvals
-- ---------------------------------------------------------------------------
GRANT USAGE ON SCHEMA cf_test TO cf_agent;
SET ROLE cf_agent;
SELECT cf_test.expect_error('T-ROLE-01 cf_agent cannot insert gate decisions',
  $$INSERT INTO cf.gate_decisions (gate, object_type, object_id, object_content_sha256, decision, reviewer_id, idempotency_key, surface)
    VALUES ('G1', 'editorial_opportunity', '00000000-0000-4000-8000-000000000011', 'x', 'APPROVE',
            '00000000-0000-4000-8000-000000000001', 'k-agent', 'AGENT')$$, 'permission denied');
SELECT cf_test.expect_error('T-ROLE-02 cf_agent cannot call the gate function',
  $$SELECT cf.record_gate_decision('G1', '00000000-0000-4000-8000-000000000011', 'APPROVE',
      '00000000-0000-4000-8000-000000000001', 'k-agent-2', 'AGENT')$$, 'permission denied');
SELECT cf_test.expect_error('T-ROLE-03 cf_agent cannot turn on publishing',
  $$UPDATE cf.system_flags SET enabled = true WHERE flag_key = 'PUBLISH_ENABLED'$$, 'permission denied');
RESET ROLE;

-- ---------------------------------------------------------------------------
-- REVOKE supersedes approval
-- ---------------------------------------------------------------------------
SELECT cf.record_gate_decision('G2', '00000000-0000-4000-8000-000000000021', 'REVOKE',
  '00000000-0000-4000-8000-000000000001', 'k-g2-revoke', 'TEST', 'fixture revoke');
SELECT cf_test.expect_true('T-GATE-06 revoked script is RETIRED and its approval is no longer effective',
  (SELECT status = 'RETIRED' FROM cf.content_scripts WHERE script_id = '00000000-0000-4000-8000-000000000021')
  AND NOT EXISTS (SELECT 1 FROM cf.v_effective_gate_decisions
                  WHERE object_id = '00000000-0000-4000-8000-000000000021' AND decision = 'APPROVE'));

SELECT 'STATIC TESTS COMPLETE' AS result;
