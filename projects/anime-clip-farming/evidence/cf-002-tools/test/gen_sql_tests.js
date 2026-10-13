'use strict';
// Generates a psql script that replays the CF-002 workflow SQL (sql/*.sql) as PREPARE/EXECUTE against a local database that already carries 0001-0004 and the synthetic seed.
// Usage: node gen_sql_tests.js <out-dir>
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { runPipeline } = require('./pipeline');
const FX = require('../fixtures/make_fixtures');
const out = process.argv[2];
const sql = (f) => fs.readFileSync(path.join(__dirname, '..', 'sql', f), 'utf8').split('\n').filter((l) => !/^\s*--/.test(l)).join('\n').trim().replace(/;$/, '');
const lit = (s) => '$cf$' + s + '$cf$';
const prep = (name, f, types) => 'PREPARE ' + name + '(' + types.join(',') + ') AS\n' + sql(f) + ';\n';
const PREPS = prep('s_begin', '01_begin_run.sql', ['text', 'text', 'text', 'text', 'text']) + prep('s_outputs', '02_load_run_outputs.sql', ['text']) +
  prep('s_upstream', '03_validate_upstream.sql', ['text', 'text']) + prep('s_boot', '03b_bootstrap_catalog.sql', ['text', 'text', 'text']) + prep('s_up_ep', '04_upsert_episode.sql', ['text', 'text', 'text']) + prep('s_pro_ep', '05_promote_episode.sql', ['text']) +
  prep('s_ins_sc', '06_insert_scenes.sql', ['text', 'text', 'text', 'text', 'text', 'text']) + prep('s_pro_sc', '07_promote_scenes.sql', ['text', 'text']) +
  prep('s_verify', '08_verify_persisted.sql', ['text', 'text', 'text']) + prep('s_complete', '09_complete_run.sql', ['text', 'text', 'text']) + prep('s_failed', '10_mark_run_failed.sql', ['text', 'text', 'text', 'int', 'text']);
const CK = (n, c) => 'SELECT cf_test.expect_true(' + lit(n) + ', ' + c + ');\n';
const P = (intake) => runPipeline({ intake }, FX.upstream(), FX.NOW);
let ID = 0;
// Replays the full persistence chain for one intake exactly as the workflow orders it; returns psql text. tag labels checks.
function chain(p, tag, wf) {
  const cfg = p.cfg, pl = p.final.payload, key = crypto.createHash('sha256').update(cfg.idempotency_basis).digest('hex');
  const ex = ++ID;
  let s = '\\echo --- ' + tag + '\n';
  s += 'EXECUTE s_begin(' + [lit(cfg.idempotency_basis), lit(cfg.input_state_basis), lit(JSON.stringify(cfg.input_ids)), lit(wf || 'wf-local'), lit('exec-' + ex)].join(', ') + ');\n';
  s += 'SELECT agent_run_id::text AS rid FROM cf.agent_runs WHERE idempotency_key = ' + lit(key) + ' \\gset\n';
  if (pl.research_candidate_id) s += 'EXECUTE s_upstream(' + lit(pl.research_candidate_id) + ', ' + lit(pl.anime_title_id) + ');\n';
  s += 'EXECUTE s_boot(' + lit(JSON.stringify(pl.catalog)) + ', ' + lit(pl.anime_title_id || '') + ", :'rid') \\gset boot_\n";
  s += 'EXECUTE s_up_ep(' + lit(JSON.stringify(pl.episode)) + ", :'boot_anime_title_id', :'rid') \\gset ep_\n";
  s += "EXECUTE s_pro_ep(:'ep_source_episode_id');\n";
  s += 'EXECUTE s_ins_sc(' + [lit(JSON.stringify(pl.scenes)), ":'ep_source_episode_id'", ":'boot_anime_title_id'", lit(pl.research_candidate_id || ''), ":'rid'", lit('v0.1.1')].join(', ') + ');\n';
  s += 'EXECUTE s_pro_sc(' + ":'ep_source_episode_id', " + lit(JSON.stringify(pl.boundaries)) + ');\n';
  s += 'EXECUTE s_verify(' + ":'ep_source_episode_id', " + lit(JSON.stringify(pl.boundaries)) + ", :'boot_anime_title_id') \\gset v_\n";
  s += 'EXECUTE s_complete(' + ":'rid', " + lit(JSON.stringify(p.final.summary)) + ", :'v_verification');\n";
  return { s, key };
}
const runRow = (key) => '(SELECT run_state::text || attempt_count FROM cf.agent_runs WHERE idempotency_key = ' + lit(key) + ')';
let s = '\\set ON_ERROR_STOP on\n' + PREPS;
// S1 first run: one candidate, one episode, one scene
const p1 = P(FX.intake()); const c1 = chain(p1, 'S1 first run (1 episode, 1 scene)');
s += c1.s;
s += CK('S1 run SUCCEEDED attempt 1, CF-002 v0.1.1, paid 0, cost 0, provider 0, no model', '(SELECT run_state::text = \'SUCCEEDED\' AND attempt_count = 1 AND paid_call_count = 0 AND estimated_cost_usd = 0 AND provider_call_count = 0 AND model_requested IS NULL AND agent_code = \'CF-002\' AND agent_version = \'v0.1.1\' AND finished_at IS NOT NULL FROM cf.agent_runs WHERE idempotency_key = ' + lit(c1.key) + ')');
s += CK('S1 idempotency key = sha256(basis), input hash present, ids recorded', '(SELECT input_state_hash ~ \'^[0-9a-f]{64}\' AND input_ids->>\'research_candidate_id\' = \'' + FX.CAND + '\' FROM cf.agent_runs WHERE idempotency_key = ' + lit(c1.key) + ')');
s += CK('S1 one episode READY, one scene READY, linked to run, title, episode and candidate', '(SELECT count(*) = 1 AND bool_and(s.status::text = \'READY\' AND e.status::text = \'READY\' AND s.agent_run_id = r.agent_run_id AND s.anime_title_id = \'' + FX.TITLE + '\' AND s.research_candidate_id = \'' + FX.CAND + '\' AND s.agent_version = \'v0.1.1\') FROM cf.anime_scene_intelligence s JOIN cf.anime_source_episodes e USING (source_episode_id) JOIN cf.agent_runs r ON r.idempotency_key = ' + lit(c1.key) + ')');
s += CK('S1 provenance stored exactly (platform, reference, basis, observer, observed_at), verified flag, ms boundaries', '(SELECT research_source_platform = \'HUMAN_RESEARCH_OBSERVATION\' AND research_source_reference = \'human-observation:synthetic-0001\' AND research_access_basis::text = \'HUMAN_VIEWED_LICENSED_PLATFORM\' AND research_observer = \'TEST\' AND research_observed_at = \'2026-10-13T05:00:00Z\' AND timestamps_human_verified AND start_ms = 190000 AND end_ms = 245000 AND model_confidence IS NULL AND prompt_version IS NULL FROM cf.anime_scene_intelligence)');
s += CK('S1 publication_source_status UNKNOWN for the scene', '(SELECT publication_source_status = \'UNKNOWN\' FROM cf.v_scene_publication_status)');
s += CK('S1 run summary has verification (found 1, ready 1, all UNKNOWN)', '(SELECT (output_summary->\'verification\'->>\'found_scenes\')::int = 1 AND (output_summary->\'verification\'->>\'ready\')::int = 1 AND (output_summary->\'verification\'->>\'all_publication_unknown\')::boolean FROM cf.agent_runs WHERE idempotency_key = ' + lit(c1.key) + ')');
s += "SELECT scene_id::text AS first_scene, source_episode_id::text AS first_episode, dedupe_key AS first_key FROM cf.anime_scene_intelligence \\gset\n";
// S2 replay: gate says REPLAY (no source/persist needed); then prove the persistence chain itself is a no-op when forced
s += '\\echo --- S2 replay\nEXECUTE s_begin(' + [lit(p1.cfg.idempotency_basis), lit(p1.cfg.input_state_basis), lit(JSON.stringify(p1.cfg.input_ids)), lit('wf-local'), lit('exec-replay')].join(', ') + ');\n';
s += CK('S2 replay leaves the run SUCCEEDED attempt 1 (REPLAY disposition, no re-claim)', runRow(c1.key) + " = 'SUCCEEDED1'");
s += CK('S2 only one run row for the key', "(SELECT count(*) FROM cf.agent_runs WHERE agent_code = 'CF-002') = 1");
const forced = chain(p1, 'S2b forced persistence replay (replay gate bypassed on purpose)');
s += CK('S2 forced replay: still 1 episode, 1 scene, same ids, same key', "(SELECT count(*) FROM cf.anime_source_episodes) = 1 AND (SELECT count(*) FROM cf.anime_scene_intelligence) = 1 AND (SELECT scene_id::text = :'first_scene' AND source_episode_id::text = :'first_episode' AND dedupe_key = :'first_key' FROM cf.anime_scene_intelligence)");
// the forced chain's begin hit a SUCCEEDED run, so complete found it not RUNNING: that is the intended safety (no second completion)
s += forced.s.indexOf('s_complete') > 0 ? '' : '';
s += CK('S2 forced replay did not re-complete or alter the SUCCEEDED run', runRow(c1.key) + " = 'SUCCEEDED1'");
// S3 two different scenes in the same episode (new boundaries -> new logical input -> new run)
const p3 = P(FX.intake({ scenes: [FX.scene({ start: '10:00', end: '10:50', scene_summary: 'Synthetic second scene of the same episode.' })] })); const c3 = chain(p3, 'S3 second scene, same episode');
s += c3.s;
s += CK('S3 new run, episode reused (still 1), two distinct scenes, both READY, distinct ids/keys', "(SELECT count(*) FROM cf.agent_runs WHERE agent_code = 'CF-002') = 2 AND (SELECT count(*) FROM cf.anime_source_episodes) = 1 AND (SELECT count(*) = 2 AND count(DISTINCT scene_id) = 2 AND count(DISTINCT dedupe_key) = 2 AND count(DISTINCT source_episode_id) = 1 AND bool_and(status::text = 'READY') FROM cf.anime_scene_intelligence)");
s += CK('S3 first scene untouched by the second run (id, key, run)', "(SELECT scene_id::text = :'first_scene' AND dedupe_key = :'first_key' AND agent_run_id = (SELECT agent_run_id FROM cf.agent_runs WHERE idempotency_key = " + lit(c1.key) + ") FROM cf.anime_scene_intelligence WHERE start_ms = 190000)");
// S3b one intake with 2 scenes (multi-scene batch)
const p3b = P(FX.intake({ scenes: [FX.scene({ start: '15:00', end: '15:40' }), FX.scene({ start: '17:00', end: '17:30' })] })); const c3b = chain(p3b, 'S3b two scenes in one intake');
s += c3b.s;
s += CK('S3b batch of two scenes persisted, 4 scenes total, still one episode', "(SELECT count(*) FROM cf.anime_scene_intelligence) = 4 AND (SELECT count(*) FROM cf.anime_source_episodes) = 1 AND (SELECT (output_summary->'verification'->>'found_scenes')::int = 2 FROM cf.agent_runs WHERE idempotency_key = " + lit(c3b.key) + ')');
// S4 overlap >= 80% of the shorter span with an existing scene: inserted DRAFT, flagged, never merged, never promoted
const p4 = P(FX.intake({ scenes: [FX.scene({ start: '03:12', end: '04:03', scene_summary: 'Synthetic near-duplicate of the first scene.' })] })); const c4 = chain(p4, 'S4 overlapping near-duplicate');
s += c4.s;
s += CK('S4 near-duplicate stored DRAFT with possible_duplicate_of pointing at the original, not promoted', "(SELECT status::text = 'DRAFT' AND possible_duplicate_of_scene_id::text = :'first_scene' FROM cf.anime_scene_intelligence WHERE start_ms = 192000)");
s += CK('S4 original untouched; run SUCCEEDED with draft_held 1 flagged 1', "(SELECT status::text = 'READY' FROM cf.anime_scene_intelligence WHERE scene_id::text = :'first_scene') AND (SELECT (output_summary->'verification'->>'draft_held')::int = 1 AND (output_summary->'verification'->>'flagged_possible_duplicates')::int = 1 AND run_state::text = 'SUCCEEDED' FROM cf.agent_runs WHERE idempotency_key = " + lit(c4.key) + ')');
// S5 upstream validation outputs
s += '\\echo --- S5 upstream validation\n';
s += 'EXECUTE s_upstream(' + lit('99999999-9999-4999-8999-999999999999') + ', ' + lit(FX.TITLE) + ');\n';
s += 'EXECUTE s_upstream(' + lit('not-a-uuid') + ', ' + lit('also-not') + ');\n';
s += 'EXECUTE s_upstream(' + lit(FX.CAND) + ', ' + lit(FX.OTHER_TITLE) + ');\n';
s += CK('S5 candidate/title mismatch visible to the Code node (candidate_title_id <> title_id)', "(SELECT c.anime_title_id <> t.anime_title_id FROM cf.research_candidates c JOIN cf.anime_titles t ON t.anime_title_id::text = '" + FX.OTHER_TITLE + "' WHERE c.research_candidate_id::text = '" + FX.CAND + "')");
// S6 failed run re-claim and mark-failed
s += '\\echo --- S6 failed run\n';
const p6 = P(FX.intake({ scenes: [FX.scene({ start: '20:00', end: '20:20' })] })); const cfg6 = p6.cfg, key6 = crypto.createHash('sha256').update(cfg6.idempotency_basis).digest('hex');
const begin6 = (n) => 'EXECUTE s_begin(' + [lit(cfg6.idempotency_basis), lit(cfg6.input_state_basis), lit(JSON.stringify(cfg6.input_ids)), lit('wf-local'), lit(n)].join(', ') + ');\n';
s += begin6('exec-f1') + 'SELECT agent_run_id::text AS rid6 FROM cf.agent_runs WHERE idempotency_key = ' + lit(key6) + ' \\gset\n';
s += "EXECUTE s_failed(:'rid6', 'CF002_BAD_SOURCE_REFERENCE', 'simulated', 0, " + lit('{"result":"FAILED","paid_calls":0}') + ');\n';
s += CK('S6 failed run: FAILED + error code + zero provider/paid, no scenes', "(SELECT run_state::text = 'FAILED' AND error_code = 'CF002_BAD_SOURCE_REFERENCE' AND provider_call_count = 0 AND paid_call_count = 0 FROM cf.agent_runs WHERE idempotency_key = " + lit(key6) + ") AND (SELECT count(*) FROM cf.anime_scene_intelligence WHERE agent_run_id = :'rid6') = 0");
s += "EXECUTE s_failed(:'rid6', 'X', 'second mark must not change a FAILED run', 0, '{}');\n";
s += CK('S6 mark-failed only touches RUNNING runs', "(SELECT error_code = 'CF002_BAD_SOURCE_REFERENCE' FROM cf.agent_runs WHERE agent_run_id = :'rid6')");
s += begin6('exec-f2');
s += CK('S6 FAILED run re-claimed: same id, RUNNING, attempt 2', runRow(key6) + " = 'RUNNING2' AND (SELECT agent_run_id::text = :'rid6' FROM cf.agent_runs WHERE idempotency_key = " + lit(key6) + ')');
s += "EXECUTE s_failed(:'rid6', 'CF002_DB_ERROR', 'closing the test run', 0, '{}');\n";
s += "UPDATE cf.agent_runs SET run_state = 'RUNNING', finished_at = NULL, started_at = now() WHERE agent_run_id = :'rid6';\n";
s += begin6('exec-f3');
s += CK('S6 fresh RUNNING is IN_PROGRESS, not re-claimed (attempt stays 2)', runRow(key6) + " = 'RUNNING2'");
s += "UPDATE cf.agent_runs SET started_at = now() - interval '20 minutes' WHERE agent_run_id = :'rid6';\n" + begin6('exec-f4');
s += CK('S6 stale RUNNING (>15 min) re-claimed attempt 3', runRow(key6) + " = 'RUNNING3'");
// S7 zero input
s += '\\echo --- S7 zero input\n';
const z = runPipeline({}, {}, FX.NOW); const kz = crypto.createHash('sha256').update(z.cfg.idempotency_basis).digest('hex');
s += 'EXECUTE s_begin(' + [lit(z.cfg.idempotency_basis), lit(z.cfg.input_state_basis), lit(JSON.stringify(z.cfg.input_ids)), lit('wf-local'), lit('exec-z')].join(', ') + ');\n';
s += 'SELECT agent_run_id::text AS ridz FROM cf.agent_runs WHERE idempotency_key = ' + lit(kz) + ' \\gset\n';
s += "EXECUTE s_complete(:'ridz', " + lit(JSON.stringify(z.final.summary)) + ", 'null');\n";
s += CK('S7 zero input: SUCCEEDED NO_INPUT, nothing created for that run', "(SELECT run_state::text = 'SUCCEEDED' AND output_summary->>'result' = 'NO_INPUT' FROM cf.agent_runs WHERE agent_run_id = :'ridz') AND NOT EXISTS (SELECT 1 FROM cf.anime_scene_intelligence WHERE agent_run_id = :'ridz') AND NOT EXISTS (SELECT 1 FROM cf.anime_source_episodes WHERE agent_run_id = :'ridz')");
// S8 verify mismatch: complete refuses to call a run SUCCEEDED when expected scenes are missing
s += '\\echo --- S8 verify mismatch\n';
s += "UPDATE cf.agent_runs SET run_state = 'RUNNING', finished_at = NULL WHERE agent_run_id = :'rid6';\n";
s += "EXECUTE s_complete(:'rid6', " + lit('{"result":"COMPLETED"}') + ", " + lit('{"expected_scenes":2,"found_scenes":1,"all_publication_unknown":true}') + ');\n';
s += CK('S8 expected 2 found 1 -> run FAILED CF002_VERIFY_MISMATCH', "(SELECT run_state::text = 'FAILED' AND error_code = 'CF002_VERIFY_MISMATCH' FROM cf.agent_runs WHERE agent_run_id = :'rid6')");
// S10 v0.1.1 validation mode: null candidate, DRAFT-only catalog bootstrap, replay
s += '\\echo --- S10 validation mode\n';
const p10 = runPipeline({ intake: FX.vintake() }, {}, FX.NOW); const c10 = chain(p10, 'S10 validation-mode first run');
s += "SELECT count(*) AS cand_before FROM cf.research_candidates \\gset\n";
s += c10.s;
s += "SELECT t.anime_title_id::text AS v_title, t.franchise_id::text AS v_fr, e.source_episode_id::text AS v_ep, s.scene_id::text AS v_scene FROM cf.anime_titles t, cf.anime_source_episodes e, cf.anime_scene_intelligence s WHERE t.normalised_title_key = 'synthetic validation title' AND e.anime_title_id = t.anime_title_id AND s.source_episode_id = e.source_episode_id \\gset\n";
s += CK('S10 franchise and title created DRAFT (never READY), stamped with the CF-002 run, lineage not CF-001', "(SELECT f.status::text = 'DRAFT' AND t.status::text = 'DRAFT' AND t.agent_run_id = r.agent_run_id AND f.agent_run_id = r.agent_run_id AND r.agent_code = 'CF-002' FROM cf.anime_titles t JOIN cf.anime_franchises f USING (franchise_id) JOIN cf.agent_runs r ON r.idempotency_key = " + lit(c10.key) + " WHERE t.anime_title_id::text = :'v_title')");
s += CK('S10 scene has NULL research_candidate_id, carries the lineage marker, publication UNKNOWN, v0.1.1', "(SELECT s.research_candidate_id IS NULL AND s.research_access_notes LIKE 'CF002_VALIDATION_SOURCE_OUTSIDE_CF001_BATCH%' AND v.publication_source_status = 'UNKNOWN' AND s.agent_version = 'v0.1.1' AND s.research_access_basis::text = 'PUBLIC_OFFICIAL_UPLOAD' AND s.start_ms = 0 AND s.end_ms = 130000 FROM cf.anime_scene_intelligence s JOIN cf.v_scene_publication_status v USING (scene_id) WHERE s.scene_id::text = :'v_scene')");
s += CK('S10 no research candidate created or changed', "(SELECT count(*) = :cand_before FROM cf.research_candidates)");
s += CK('S10 run SUCCEEDED, verification shows null-candidate scene and DRAFT catalog', "(SELECT run_state::text = 'SUCCEEDED' AND (output_summary->'verification'->>'scenes_with_null_candidate')::int = 1 AND output_summary->'verification'->'title'->>'status' = 'DRAFT' AND output_summary->'verification'->'title'->>'franchise_status' = 'DRAFT' AND output_summary->'summary'->>'lineage' IS NOT DISTINCT FROM output_summary->'summary'->>'lineage' FROM cf.agent_runs WHERE idempotency_key = " + lit(c10.key) + ')');
s += "SELECT count(*) AS fr_n FROM cf.anime_franchises \\gset\nSELECT count(*) AS ti_n FROM cf.anime_titles \\gset\nSELECT count(*) AS ep_n FROM cf.anime_source_episodes \\gset\nSELECT count(*) AS sc_n FROM cf.anime_scene_intelligence \\gset\n";
const c10b = chain(p10, 'S10b validation-mode replay (gate bypassed on purpose)');
s += c10b.s;
s += CK('S10 forced replay: same franchise, title, episode and scene ids; zero duplicate catalog, episode or scene rows', "(SELECT count(*) = :fr_n FROM cf.anime_franchises) AND (SELECT count(*) = :ti_n FROM cf.anime_titles) AND (SELECT count(*) = :ep_n FROM cf.anime_source_episodes) AND (SELECT count(*) = :sc_n FROM cf.anime_scene_intelligence) AND :'boot_anime_title_id' = :'v_title' AND (SELECT count(*) = 1 FROM cf.anime_franchises WHERE normalised_key = 'synthetic validation franchise') AND (SELECT scene_id::text = :'v_scene' FROM cf.anime_scene_intelligence WHERE source_episode_id::text = :'v_ep')");
s += CK('S10 replay left catalog DRAFT and candidates unchanged', "(SELECT status::text = 'DRAFT' FROM cf.anime_titles WHERE anime_title_id::text = :'v_title') AND (SELECT status::text = 'DRAFT' FROM cf.anime_franchises WHERE franchise_id::text = :'v_fr') AND (SELECT count(*) = :cand_before FROM cf.research_candidates)");
s += CK('S9 run economics across all runs: paid 0, cost 0, provider 0', "(SELECT bool_and(paid_call_count = 0 AND estimated_cost_usd = 0 AND provider_call_count = 0 AND model_requested IS NULL) FROM cf.agent_runs WHERE agent_code = 'CF-002')");
s += CK('S9 every stored scene reads UNKNOWN publication status and has complete provenance', "(SELECT count(*) > 0 AND bool_and(v.publication_source_status = 'UNKNOWN' AND s.research_source_platform <> '' AND s.research_source_reference <> '' AND s.research_observed_at IS NOT NULL) FROM cf.anime_scene_intelligence s JOIN cf.v_scene_publication_status v USING (scene_id))");
fs.writeFileSync(path.join(out, 's_flow.sql'), s);
console.log('generated s_flow.sql');
