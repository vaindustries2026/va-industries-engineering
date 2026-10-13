'use strict';
// Generates psql scripts that replay the CF-001 SQL statements (as PREPARE/EXECUTE, i.e. parameterised) against a local database.
// Usage: node gen_sql_tests.js <out-dir>
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { runPipeline } = require('./pipeline');
const FX = require('../fixtures/make_fixtures');
const out = process.argv[2];
const SQLD = path.join(__dirname, '..', 'sql');
const sql = (f) => fs.readFileSync(path.join(SQLD, f), 'utf8').split('\n').filter((l) => !/^\s*--/.test(l)).join('\n').trim().replace(/;$/, '');
const lit = (s) => '$cf$' + s + '$cf$';
function prep(name, f, types) { return 'PREPARE ' + name + (types.length ? '(' + types.join(',') + ')' : '') + ' AS\n' + sql(f) + ';\n'; }
const PREPS =
  prep('s_begin', '01_begin_run.sql', ['text', 'text', 'text', 'text', 'text']) +
  prep('s_outputs', '02_load_run_outputs.sql', ['text']) +
  prep('s_fkeys', '03_load_franchise_keys.sql', []) +
  prep('s_ins_f', '04_insert_franchises.sql', ['text', 'text']) +
  prep('s_ins_t', '05_insert_titles.sql', ['text', 'text']) +
  prep('s_promo_ref', '06_promote_reference_rows.sql', ['text', 'text']) +
  prep('s_ins_c', '07_insert_candidates.sql', ['text', 'text', 'text']) +
  prep('s_promo_c', '08_promote_candidates.sql', ['text', 'text']) +
  prep('s_complete', '09_complete_run.sql', ['text', 'int', 'text', 'text', 'text']) +
  prep('s_failed', '10_mark_run_failed.sql', ['text', 'text', 'text', 'int', 'text']);
const NOW = '2026-10-13T04:00:00.000Z';
const P = runPipeline(FX.good, NOW);
const cfg = P.cfg, r = P.r, pl = r.payload;
function persist(run_id_expr, tag) {
  const summary = JSON.stringify({ result: pl.candidates.length ? 'SUCCEEDED' : 'NO_INPUT', model: 'none', llm_calls: 0, paid_calls: 0 });
  return [
    "\\echo STEP " + tag + " insert franchises",
    "EXECUTE s_ins_f(" + lit(JSON.stringify(pl.franchises)) + ", " + run_id_expr + ");",
    "\\echo STEP " + tag + " insert titles",
    "EXECUTE s_ins_t(" + lit(JSON.stringify(pl.titles)) + ", " + run_id_expr + ");",
    "\\echo STEP " + tag + " promote reference rows",
    "EXECUTE s_promo_ref(" + lit(JSON.stringify(pl.franchises)) + ", " + lit(JSON.stringify(pl.titles)) + ");",
    "\\echo STEP " + tag + " insert candidates",
    "EXECUTE s_ins_c(" + lit(JSON.stringify(pl.candidates)) + ", " + lit(cfg.window) + ", " + run_id_expr + ");",
    "\\echo STEP " + tag + " promote candidates",
    "EXECUTE s_promo_c(" + lit(JSON.stringify(pl.candidates)) + ", " + lit(cfg.window) + ");",
    "\\echo STEP " + tag + " complete run",
    "EXECUTE s_complete(" + run_id_expr + ", 4, " + lit(summary) + ", " + lit(cfg.window) + ", " + lit(JSON.stringify(r.anilist_ids)) + ");",
  ].join('\n');
}
const beginArgs = [lit(cfg.idempotency_basis), lit(cfg.input_state_basis), lit(JSON.stringify(cfg.input_ids)), lit('wf-local'), lit('exec-1')].join(', ');
const idemKey = crypto.createHash('sha256').update(cfg.idempotency_basis).digest('hex');
const GSET = (k) => 'SELECT agent_run_id::text AS rid FROM cf.agent_runs WHERE idempotency_key = ' + k + ' \\gset\n';
const RIDV = ":'rid'";
const CHK = (name, cond) => "SELECT cf_test.expect_true(" + lit(name) + ", " + cond + ");";
const RID = "(SELECT agent_run_id::text FROM cf.agent_runs WHERE idempotency_key = " + lit(idemKey) + ")";
let s1 = '\\set ON_ERROR_STOP on\n' + PREPS;
s1 += "\\echo === S1 first run ===\nEXECUTE s_begin(" + beginArgs + ");\n";
s1 += CHK('S1 run row RUNNING attempt 1, key = sha256(basis) computed in SQL', "(SELECT run_state::text||attempt_count FROM cf.agent_runs WHERE idempotency_key = " + lit(idemKey) + ") = 'RUNNING1'");
s1 += "\nEXECUTE s_fkeys;\n" + GSET(lit(idemKey)) + persist(RIDV, 'S1') + '\n';
s1 += CHK('S1 run SUCCEEDED, paid=0, cost=0, calls=4, no model', "(SELECT run_state::text='SUCCEEDED' AND paid_call_count=0 AND estimated_cost_usd=0 AND provider_call_count=4 AND model_requested IS NULL AND agent_code='CF-001' AND agent_version='v0.1' AND finished_at IS NOT NULL FROM cf.agent_runs WHERE idempotency_key = " + lit(idemKey) + ")") + '\n';
s1 += CHK('S1 franchise/title/candidate counts match payload', "(SELECT count(*) FROM cf.anime_franchises)=" + pl.franchises.length + " AND (SELECT count(*) FROM cf.anime_titles)=" + pl.titles.length + " AND (SELECT count(*) FROM cf.research_candidates)=" + pl.candidates.length) + '\n';
const nReady = pl.candidates.filter((c) => c.ready).length, nRej = pl.candidates.length - nReady;
s1 += CHK('S1 READY/REJECTED split as planned; evidence present; signals bounded', "(SELECT count(*) FILTER (WHERE status::text='READY')=" + nReady + " AND count(*) FILTER (WHERE status::text='REJECTED' AND rejection_reason='INSUFFICIENT_SIGNAL_DATA')=" + nRej + " AND bool_and(jsonb_array_length(signal_evidence)=3 AND coalesce(demand_signal,0) BETWEEN 0 AND 1 AND observation_window='2026-W42') FROM cf.research_candidates)") + '\n';
s1 += CHK('S1 blocked franchises/titles carry no candidates', "NOT EXISTS (SELECT 1 FROM cf.research_candidates c JOIN cf.anime_titles t USING (anime_title_id) WHERE t.status::text<>'READY')") + '\n';
s1 += CHK('S1 dedupe_key = sha256(title|topic|lane|window)', "(SELECT bool_and(dedupe_key = encode(sha256(convert_to(anime_title_id::text||'|'||topic_key||'|'||content_lane||'|'||observation_window,'UTF8')),'hex')) FROM cf.research_candidates)") + '\n';
s1 += CHK('S1 db_verified summary present and consistent', "(SELECT (output_summary->'db_verified'->>'created_by_this_run')::int = " + pl.candidates.length + " FROM cf.agent_runs WHERE idempotency_key = " + lit(idemKey) + ")") + '\n';
s1 += "\\echo === S2 replay: same logical input ===\nEXECUTE s_begin(" + beginArgs + ");\n";
s1 += CHK('S2 replay did not touch run (still SUCCEEDED attempt 1)', "(SELECT run_state::text||attempt_count FROM cf.agent_runs WHERE idempotency_key = " + lit(idemKey) + ") = 'SUCCEEDED1'") + '\n';
s1 += CHK('S2 exactly one run row for the key', "(SELECT count(*) FROM cf.agent_runs)=1") + '\n';
s1 += "\\echo === S3 simulated failed run then re-claim and full re-persist (idempotent write path) ===\n";
s1 += GSET(lit(idemKey)) + "EXECUTE s_failed(" + RIDV + ", 'X', 'mark-failed on a non-RUNNING run must change nothing', 0, '{}');\n" + CHK('S3 mark-failed refuses a SUCCEEDED run', "(SELECT run_state::text='SUCCEEDED' FROM cf.agent_runs WHERE idempotency_key = " + lit(idemKey) + ")") + '\n';
s1 += "UPDATE cf.agent_runs SET run_state='RUNNING', finished_at=NULL WHERE idempotency_key = " + lit(idemKey) + ";\n";
s1 += GSET(lit(idemKey)) + "EXECUTE s_failed(" + RIDV + ", 'CF001_TEST', 'simulated', 4, '{\"result\":\"FAILED\"}');\n";
s1 += "EXECUTE s_begin(" + beginArgs + ");\n";
s1 += CHK('S3 re-claim -> same run id, RUNNING, attempt 2', "(SELECT run_state::text||attempt_count FROM cf.agent_runs WHERE idempotency_key = " + lit(idemKey) + ") = 'RUNNING2' AND (SELECT count(*) FROM cf.agent_runs)=1") + '\n';
s1 += GSET(lit(idemKey)) + persist(RIDV, 'S3') + '\n';
s1 += CHK('S3 no duplicate franchise/title/candidate after re-persist', "(SELECT count(*) FROM cf.anime_franchises)=" + pl.franchises.length + " AND (SELECT count(*) FROM cf.anime_titles)=" + pl.titles.length + " AND (SELECT count(*) FROM cf.research_candidates)=" + pl.candidates.length) + '\n';
s1 += CHK('S3 candidate statuses not regressed and run SUCCEEDED attempt 2', "(SELECT count(*) FILTER (WHERE status::text='READY')=" + nReady + " AND count(*) FILTER (WHERE status::text='REJECTED')=" + nRej + " FROM cf.research_candidates) AND (SELECT run_state::text||attempt_count FROM cf.agent_runs)='SUCCEEDED2'") + '\n';
s1 += "\\echo === S4 fresh-RUNNING run is IN_PROGRESS (not re-claimed) ===\n";
const cfg2 = { ...cfg };
s1 += "UPDATE cf.agent_runs SET run_state='RUNNING', finished_at=NULL, started_at=now() WHERE agent_run_id=" + RID + "::uuid;\n";
s1 += "EXECUTE s_begin(" + beginArgs + ");\n";
s1 += CHK('S4 fresh RUNNING stays RUNNING attempt 2', "(SELECT run_state::text||attempt_count FROM cf.agent_runs)='RUNNING2'") + '\n';
s1 += "UPDATE cf.agent_runs SET started_at=now()-interval '20 minutes' WHERE agent_run_id=" + RID + "::uuid;\n";
s1 += "EXECUTE s_begin(" + beginArgs + ");\n";
s1 += CHK('S4 stale RUNNING (>15 min) re-claimed attempt 3', "(SELECT run_state::text||attempt_count FROM cf.agent_runs)='RUNNING3'") + '\n';
s1 += "\\echo === S5 output replay lookup ===\n" + GSET(lit(idemKey)) + "EXECUTE s_outputs(" + RIDV + ");\n";
fs.writeFileSync(path.join(out, 's1_flow.sql'), s1);

// next-week window: new run row, new candidates, no collision with the first window
const P2 = runPipeline(FX.good, '2026-10-20T04:00:00.000Z');
const K2 = crypto.createHash('sha256').update(P2.cfg.idempotency_basis).digest('hex');
// S6 zero input
const PZ = runPipeline([FX.resp([]), FX.resp([]), FX.resp([]), FX.resp([])], '2026-10-27T04:00:00.000Z');
let s6 = '\\set ON_ERROR_STOP on\n' + PREPS;
s6 += "EXECUTE s_begin(" + [lit(P2.cfg.idempotency_basis), lit(P2.cfg.input_state_basis), lit(JSON.stringify(P2.cfg.input_ids)), lit('wf-local'), lit('exec-2')].join(', ') + ");\n";
s6 += "EXECUTE s_fkeys;\n" + GSET(lit(K2));
const pl2 = P2.r.payload;   // generated against an empty franchise list; DB keys equal, so the same payload is valid
const RID2 = "(SELECT agent_run_id::text FROM cf.agent_runs WHERE idempotency_key = " + lit(K2) + ")";
s6 += "EXECUTE s_ins_f(" + lit(JSON.stringify(pl2.franchises)) + ", " + RIDV + ");\nEXECUTE s_ins_t(" + lit(JSON.stringify(pl2.titles)) + ", " + RIDV + ");\n";
s6 += "EXECUTE s_promo_ref(" + lit(JSON.stringify(pl2.franchises)) + ", " + lit(JSON.stringify(pl2.titles)) + ");\n";
s6 += "EXECUTE s_ins_c(" + lit(JSON.stringify(pl2.candidates)) + ", " + lit(P2.cfg.window) + ", " + RIDV + ");\nEXECUTE s_promo_c(" + lit(JSON.stringify(pl2.candidates)) + ", " + lit(P2.cfg.window) + ");\n";
s6 += "EXECUTE s_complete(" + RIDV + ", 4, " + lit('{"result":"SUCCEEDED"}') + ", " + lit(P2.cfg.window) + ", " + lit(JSON.stringify(P2.r.anilist_ids)) + ");\n";
s6 += CHK('S6 next window: second run, titles/franchises reused, candidates doubled (one per window)', "(SELECT count(*) FROM cf.agent_runs)=2 AND (SELECT count(*) FROM cf.anime_titles)=" + pl.titles.length + " AND (SELECT count(*) FROM cf.research_candidates)=" + (pl.candidates.length + pl2.candidates.length) + " AND (SELECT count(DISTINCT dedupe_key) FROM cf.research_candidates)=" + (pl.candidates.length + pl2.candidates.length)) + '\n';
// zero input
const KZ = crypto.createHash('sha256').update(PZ.cfg.idempotency_basis).digest('hex');
const RIDZ = "(SELECT agent_run_id::text FROM cf.agent_runs WHERE idempotency_key = " + lit(KZ) + ")";
s6 += "EXECUTE s_begin(" + [lit(PZ.cfg.idempotency_basis), lit(PZ.cfg.input_state_basis), lit(JSON.stringify(PZ.cfg.input_ids)), lit('wf-local'), lit('exec-3')].join(', ') + ");\n";
s6 += GSET(lit(KZ)) + "EXECUTE s_ins_f('[]', " + RIDV + ");\nEXECUTE s_ins_t('[]', " + RIDV + ");\nEXECUTE s_promo_ref('[]','[]');\nEXECUTE s_ins_c('[]', " + lit(PZ.cfg.window) + ", " + RIDV + ");\nEXECUTE s_promo_c('[]', " + lit(PZ.cfg.window) + ");\n";
s6 += "EXECUTE s_complete(" + RIDV + ", 4, " + lit('{"result":"NO_INPUT","model":"none"}') + ", " + lit(PZ.cfg.window) + ", '[]');\n";
s6 += CHK('S6 zero input: SUCCEEDED NO_INPUT, zero outputs for that run', "(SELECT output_summary->>'result'='NO_INPUT' AND run_state::text='SUCCEEDED' FROM cf.agent_runs WHERE agent_run_id=" + RIDZ + "::uuid) AND NOT EXISTS (SELECT 1 FROM cf.research_candidates WHERE agent_run_id=" + RIDZ + "::uuid)") + '\n';
// failure marking
const FK = 'f'.repeat(64);
s6 += "EXECUTE s_begin(" + [lit('CF-001|v0.1|failure-case'), lit('x'), lit('{}'), lit('wf-local'), lit('exec-4')].join(', ') + ");\n";
s6 += GSET("encode(sha256(convert_to('CF-001|v0.1|failure-case','UTF8')),'hex')") + "EXECUTE s_failed(" + RIDV + ", 'CF001_ANILIST_RATE_LIMITED', 'HTTP 429', 2, " + lit('{"result":"FAILED","retry_after":"60"}') + ");\n";
s6 += CHK('S6 failed run: FAILED + error_code + zero candidates', "(SELECT run_state::text='FAILED' AND error_code='CF001_ANILIST_RATE_LIMITED' AND provider_call_count=2 AND paid_call_count=0 FROM cf.agent_runs WHERE idempotency_key=encode(sha256(convert_to('CF-001|v0.1|failure-case','UTF8')),'hex')) AND NOT EXISTS (SELECT 1 FROM cf.research_candidates c JOIN cf.agent_runs r USING (agent_run_id) WHERE r.error_code IS NOT NULL)") + '\n';
fs.writeFileSync(path.join(out, 's6_more.sql'), s6);
console.log('generated; payload: ' + pl.franchises.length + ' franchises, ' + pl.titles.length + ' titles, ' + pl.candidates.length + ' candidates (' + pl.candidates.filter((c) => c.ready).length + ' ready); blocked ' + r.blocked.length);
