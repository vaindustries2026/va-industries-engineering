'use strict';
// Builds negative_phase_b.sql: one DO block, run AS cf_n8n_runtime, that attempts forbidden operations and records the outcome of each.
// It ends with RAISE EXCEPTION, so everything (including the positive-control rows) rolls back; the report travels in the error message.
const fs = require('fs');
const path = require('path');
const T = [];
const deny = (id, name, stmt) => T.push({ id, name, stmt, state: '42501' });
const gov = (id, name, stmt) => T.push({ id, name, stmt, state: '42501', like: 'CF_GOVERNANCE_DENIED' });
// --- no DELETE anywhere ---
['agent_runs', 'anime_franchises', 'anime_titles', 'research_candidates', 'reviewers', 'system_flags', 'allowed_transitions'].forEach((t, i) =>
  deny('N0' + (i + 1), 'DELETE on cf.' + t + ' is denied', 'DELETE FROM cf.' + t));
deny('N08', 'TRUNCATE cf.research_candidates is denied', 'TRUNCATE cf.research_candidates');
// --- no writes to reviewers / system flags / transitions ---
deny('N10', 'INSERT into cf.reviewers is denied', "INSERT INTO cf.reviewers (display_name) VALUES ('x')");
deny('N11', 'UPDATE cf.reviewers is denied', "UPDATE cf.reviewers SET display_name = 'x'");
deny('N12', 'UPDATE cf.system_flags (kill switches) is denied', "UPDATE cf.system_flags SET enabled = true");
deny('N13', 'INSERT into cf.system_flags is denied', "INSERT INTO cf.system_flags (flag_key, enabled) VALUES ('PUBLISH_ENABLED', true)");
deny('N14', 'INSERT into cf.allowed_transitions is denied', "INSERT INTO cf.allowed_transitions (object_type, from_status, to_status, mode) VALUES ('anime_franchise','READY','RETIRED','DETERMINISTIC')");
deny('N15', 'UPDATE cf.allowed_transitions is denied', "UPDATE cf.allowed_transitions SET mode = 'DETERMINISTIC'");
// --- no schema objects ---
deny('N20', 'CREATE TABLE in schema cf is denied', 'CREATE TABLE cf.rogue (x int)');
deny('N21', 'CREATE SCHEMA is denied', 'CREATE SCHEMA rogue');
deny('N22', 'CREATE FUNCTION in schema cf is denied', 'CREATE FUNCTION cf.rogue() RETURNS int LANGUAGE sql AS $f$ SELECT 1 $f$');
deny('N23', 'CREATE TABLE in schema public is denied', 'CREATE TABLE public.rogue (x int)');
deny('N24', 'CREATE TRIGGER on a cf table is denied', 'CREATE TRIGGER rogue BEFORE UPDATE ON cf.agent_runs FOR EACH ROW EXECUTE FUNCTION cf.touch_updated_at()');
deny('N25', 'ALTER TABLE cf.anime_titles ADD COLUMN is denied', 'ALTER TABLE cf.anime_titles ADD COLUMN rogue int');
// --- cannot weaken guards ---
deny('N30', 'ALTER TABLE ... DISABLE TRIGGER ALL is denied', 'ALTER TABLE cf.research_candidates DISABLE TRIGGER ALL');
deny('N31', 'ALTER TABLE ... DISABLE a named trigger is denied', 'ALTER TABLE cf.anime_titles DISABLE TRIGGER anime_titles_freeze');
deny('N32', 'SET session_replication_role = replica is denied', "SET LOCAL session_replication_role = 'replica'");
deny('N33', 'SET ROLE postgres is denied', 'SET LOCAL ROLE postgres');
deny('N34', 'SET ROLE service_role is denied', 'SET LOCAL ROLE service_role');
deny('N35', 'ALTER FUNCTION cf.guard_status_transition() is denied', "ALTER FUNCTION cf.guard_status_transition() SET search_path = public");
deny('N36', 'CREATE OR REPLACE the freeze function is denied', 'CREATE OR REPLACE FUNCTION cf.freeze_after_first_status() RETURNS trigger LANGUAGE plpgsql AS $f$ BEGIN RETURN NEW; END $f$');
T.push({ id: 'N37', name: 'GRANT DELETE on a cf table grants nothing (PostgreSQL warns, privilege check stays false)', stmt: 'GRANT DELETE ON cf.agent_runs TO cf_n8n_runtime', post: "NOT has_table_privilege('cf_n8n_runtime','cf.agent_runs','DELETE')", state: '42501' });
// --- no EXECUTE on cf functions ---
['guard_status_transition', 'freeze_after_first_status', 'forbid_delete', 'touch_updated_at'].forEach((f, i) =>
  deny('N4' + (i + 1), 'EXECUTE on cf.' + f + '() is denied', 'SELECT cf.' + f + '()'));
// --- governance / lifecycle ---
T.push({ id: 'N50', name: 'franchise insert straight to READY (NEW->READY) is rejected', stmt: "INSERT INTO cf.anime_franchises (normalised_key, display_name, status) VALUES ('neg direct ready','x','READY')", any: true });
gov('N51', 'HUMAN_ADMIN transition franchise READY->RETIRED is denied', "UPDATE cf.anime_franchises SET status = 'RETIRED' WHERE normalised_key = 'neg franchise'");
gov('N52', 'HUMAN_ADMIN transition title READY->RETIRED is denied', "UPDATE cf.anime_titles SET status = 'RETIRED' WHERE anilist_id = 990001");
gov('N53', 'HUMAN_ADMIN transition BLOCKED->READY is denied', "UPDATE cf.anime_franchises SET status = 'READY' WHERE normalised_key = 'neg blocked'");
T.push({ id: 'N54', name: 'candidate READY->IDEA (regression) is rejected', stmt: "UPDATE cf.research_candidates SET status = 'IDEA' WHERE topic_key = 'neg-topic'", any: true });
T.push({ id: 'N55', name: 'franchise normalised_key is frozen after READY (CF_IMMUTABLE_ROW)', stmt: "UPDATE cf.anime_franchises SET normalised_key = 'neg changed' WHERE normalised_key = 'neg franchise'", state: '23514', like: 'CF_IMMUTABLE_ROW' });
T.push({ id: 'N56', name: 'title start_year is frozen after READY (CF_IMMUTABLE_ROW, generated column era_decade does not interfere)', stmt: "UPDATE cf.anime_titles SET start_year = 1999 WHERE anilist_id = 990001", state: '23514', like: 'CF_IMMUTABLE_ROW' });
T.push({ id: 'N57', name: 'candidate content (signal_evidence) is frozen after READY', stmt: "UPDATE cf.research_candidates SET signal_evidence = '[{\"x\":1}]'::jsonb WHERE topic_key = 'neg-topic'", state: '23514', like: 'CF_IMMUTABLE_ROW' });
T.push({ id: 'N58', name: 'candidate demand_signal is frozen after READY', stmt: "UPDATE cf.research_candidates SET demand_signal = 0.0001 WHERE topic_key = 'neg-topic'", state: '23514', like: 'CF_IMMUTABLE_ROW' });
// --- duplicates ---
T.push({ id: 'N60', name: 'plain duplicate same-window candidate (same dedupe_key) is a unique violation', stmt: "INSERT INTO cf.research_candidates (anime_title_id, franchise_id, topic_key, topic_display, content_lane, signal_evidence, observation_window, dedupe_key, agent_run_id, agent_version) SELECT anime_title_id, franchise_id, topic_key, topic_display, content_lane, signal_evidence, observation_window, dedupe_key, agent_run_id, agent_version FROM cf.research_candidates WHERE topic_key = 'neg-topic'", state: '23505' });
T.push({ id: 'N61', name: 'duplicate anilist_id title is a unique violation', stmt: "INSERT INTO cf.anime_titles (franchise_id, normalised_title_key, display_title, anilist_id) SELECT franchise_id, 'other key', 'Other', 990001 FROM cf.anime_titles WHERE anilist_id = 990001", state: '23505' });
T.push({ id: 'N62', name: 'duplicate franchise normalised_key is a unique violation', stmt: "INSERT INTO cf.anime_franchises (normalised_key, display_name) VALUES ('neg franchise','dup')", state: '23505' });
T.push({ id: 'N63', name: 'duplicate run idempotency_key is a unique violation', stmt: "INSERT INTO cf.agent_runs (agent_code, agent_version, idempotency_key, input_state_hash) VALUES ('CF-001','v0.1','neg-run-key','h')", state: '23505' });
T.push({ id: 'N64', name: 'a paid call without an authorisation ref is rejected by the CHECK', stmt: "UPDATE cf.agent_runs SET paid_call_count = 1, provider_call_count = 1 WHERE idempotency_key = 'neg-run-key'", state: '23514' });
T.push({ id: 'N65', name: 'out-of-range signal (1.5) is rejected', stmt: "INSERT INTO cf.research_candidates (anime_title_id, franchise_id, topic_key, topic_display, content_lane, demand_signal, signal_evidence, observation_window, dedupe_key, agent_run_id, agent_version) SELECT anime_title_id, franchise_id, 'neg-t2','x','L', 1.5, '[{\"a\":1}]', '2026-W42','neg-dk-2', agent_run_id, 'v0.1' FROM cf.research_candidates WHERE topic_key = 'neg-topic'", state: '23514' });
T.push({ id: 'N66', name: 'empty signal_evidence is rejected', stmt: "INSERT INTO cf.research_candidates (anime_title_id, franchise_id, topic_key, topic_display, content_lane, signal_evidence, observation_window, dedupe_key, agent_run_id, agent_version) SELECT anime_title_id, franchise_id, 'neg-t3','x','L', '[]', '2026-W42','neg-dk-3', agent_run_id, 'v0.1' FROM cf.research_candidates WHERE topic_key = 'neg-topic'", state: '23514' });
T.push({ id: 'N67', name: 'malformed observation_window is rejected', stmt: "INSERT INTO cf.research_candidates (anime_title_id, franchise_id, topic_key, topic_display, content_lane, signal_evidence, observation_window, dedupe_key, agent_run_id, agent_version) SELECT anime_title_id, franchise_id, 'neg-t4','x','L', '[{\"a\":1}]', '2026-42','neg-dk-4', agent_run_id, 'v0.1' FROM cf.research_candidates WHERE topic_key = 'neg-topic'", state: '23514' });
T.push({ id: 'N68', name: 'candidate pointing at a nonexistent title is rejected (foreign key)', stmt: "INSERT INTO cf.research_candidates (anime_title_id, franchise_id, topic_key, topic_display, content_lane, signal_evidence, observation_window, dedupe_key, agent_run_id, agent_version) SELECT gen_random_uuid(), franchise_id, 'neg-t5','x','L', '[{\"a\":1}]', '2026-W42','neg-dk-5', agent_run_id, 'v0.1' FROM cf.research_candidates WHERE topic_key = 'neg-topic'", state: '23503' });
const plain = T.filter((t) => !t.post);
const post = T.filter((t) => t.post)[0];
const lit = (x) => '$s$' + x + '$s$';
const rows = plain.map((t) => "    (" + lit(t.id) + ", " + lit(t.name) + ", " + lit(t.stmt) + ", " + (t.state ? lit(t.state) : 'NULL') + ", " + (t.like ? lit(t.like) : 'NULL') + ")").join(',\n');
const body = `  FOR t IN SELECT * FROM (VALUES
${rows}
  ) AS v(id, name, stmt, state, likepat) LOOP
    BEGIN
      EXECUTE t.stmt;
      rep := rep || 'FAIL ' || t.id || ' ' || t.name || ': statement SUCCEEDED' || E'\\n'; nfail := nfail + 1;
    EXCEPTION WHEN others THEN
      IF (t.state IS NULL OR SQLSTATE = t.state) AND (t.likepat IS NULL OR SQLERRM LIKE '%' || t.likepat || '%') THEN
        rep := rep || 'PASS ' || t.id || ' ' || t.name || ' [' || SQLSTATE || ']' || E'\\n'; npass := npass + 1;
      ELSE rep := rep || 'FAIL ' || t.id || ' ' || t.name || ': got ' || SQLSTATE || ' ' || left(SQLERRM, 90) || E'\\n'; nfail := nfail + 1; END IF;
    END;
  END LOOP;
  BEGIN
    EXECUTE ${lit(post.stmt)};
    IF ${post.post} THEN rep := rep || 'PASS ${post.id} ${post.name} [statement ran, nothing granted]' || E'\\n'; npass := npass + 1; ELSE rep := rep || 'FAIL ${post.id} privilege was granted' || E'\\n'; nfail := nfail + 1; END IF;
  EXCEPTION WHEN others THEN
    IF SQLSTATE = '42501' THEN rep := rep || 'PASS ${post.id} ${post.name} [' || SQLSTATE || ']' || E'\\n'; npass := npass + 1;
    ELSE rep := rep || 'FAIL ${post.id}: got ' || SQLSTATE || ' ' || left(SQLERRM, 90) || E'\\n'; nfail := nfail + 1; END IF;
  END;
`;
const sql = `-- CF-001 Phase B negative tests. Run AS cf_n8n_runtime (the restricted n8n login). Generated by test/build_negative.js.
-- Single DO block: positive controls first, then every forbidden operation. It ends with RAISE EXCEPTION, which rolls everything
-- back (no rows, no objects remain); the report is the exception message prefixed CF001_NEG_REPORT.
DO $neg$
DECLARE t record; rep text := ''; npass int := 0; nfail int := 0; fid uuid; bid uuid; tid uuid; rid uuid; cnt int; ok boolean;
BEGIN
  -- positive controls: the runtime CAN do its intended work
  INSERT INTO cf.agent_runs (agent_code, agent_version, idempotency_key, input_state_hash, run_state) VALUES ('CF-001','v0.1','neg-run-key','h','RUNNING') RETURNING agent_run_id INTO rid;
  INSERT INTO cf.anime_franchises (normalised_key, display_name, status, agent_run_id) VALUES ('neg franchise','Neg Franchise','DRAFT', rid) RETURNING franchise_id INTO fid;
  UPDATE cf.anime_franchises SET status = 'READY' WHERE franchise_id = fid;
  INSERT INTO cf.anime_franchises (normalised_key, display_name, status, agent_run_id) VALUES ('neg blocked','Neg Blocked','DRAFT', rid) RETURNING franchise_id INTO bid;
  UPDATE cf.anime_franchises SET status = 'BLOCKED' WHERE franchise_id = bid;
  INSERT INTO cf.anime_titles (franchise_id, normalised_title_key, display_title, anilist_id, media_type, start_year, status, agent_run_id) VALUES (fid,'neg title','Neg Title',990001,'TV',2001,'DRAFT', rid) RETURNING anime_title_id INTO tid;
  UPDATE cf.anime_titles SET status = 'READY' WHERE anime_title_id = tid;
  INSERT INTO cf.research_candidates (anime_title_id, franchise_id, topic_key, topic_display, content_lane, trend_state, demand_signal, signal_evidence, observation_window, dedupe_key, status, agent_run_id, agent_version)
    VALUES (tid, fid, 'neg-topic','Neg Topic','CURRENT_TRENDING','UNKNOWN',0.5,'[{"type":"control"}]','2026-W42','neg-dedupe-key','IDEA', rid,'v0.1');
  UPDATE cf.research_candidates SET status = 'READY' WHERE topic_key = 'neg-topic';
  UPDATE cf.anime_franchises SET display_name = 'Neg Franchise Renamed' WHERE franchise_id = fid;   -- display_name is a mutable column
  INSERT INTO cf.research_candidates (anime_title_id, franchise_id, topic_key, topic_display, content_lane, signal_evidence, observation_window, dedupe_key, agent_run_id, agent_version)
    SELECT anime_title_id, franchise_id, topic_key, topic_display, content_lane, signal_evidence, observation_window, dedupe_key, agent_run_id, agent_version FROM cf.research_candidates WHERE topic_key = 'neg-topic'
    ON CONFLICT (dedupe_key) DO NOTHING;
  GET DIAGNOSTICS cnt = ROW_COUNT;
  IF cnt = 0 THEN rep := rep || 'PASS P01 ON CONFLICT (dedupe_key) DO NOTHING inserts 0 rows (expected dedupe, not an error)' || E'\\n'; npass := npass + 1;
  ELSE rep := rep || 'FAIL P01 duplicate candidate inserted' || E'\\n'; nfail := nfail + 1; END IF;
  SELECT status::text = 'READY' INTO ok FROM cf.research_candidates WHERE topic_key = 'neg-topic';
  IF ok THEN rep := rep || 'PASS P02 positive controls: franchise, title, candidate walked DRAFT/IDEA -> READY as the runtime role' || E'\\n'; npass := npass + 1; ELSE rep := rep || 'FAIL P02 positive controls' || E'\\n'; nfail := nfail + 1; END IF;
${body}  SELECT count(*) INTO cnt FROM cf.system_flags WHERE enabled IS TRUE;
  IF cnt = 0 THEN rep := rep || 'PASS Z01 all kill switches still false' || E'\\n'; npass := npass + 1; ELSE rep := rep || 'FAIL Z01 a kill switch is true' || E'\\n'; nfail := nfail + 1; END IF;
  RAISE EXCEPTION 'CF001_NEG_REPORT pass=% fail=%
%', npass, nfail, rep;
END
$neg$;
`;
fs.writeFileSync(path.join(__dirname, 'negative_phase_b.sql'), sql);
console.log('negative tests: ' + T.length + ' + controls');
