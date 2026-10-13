'use strict';
// Phase A static tests: no network, no database. Exercises the exact Code-node sources against synthetic fixtures.
const assert = require('assert');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const { run } = require('./harness');
const FX = require('../fixtures/make_fixtures');
let pass = 0, fail = 0;
function t(name, fn) { try { fn(); pass++; console.log('PASS ' + name); } catch (e) { fail++; console.log('FAIL ' + name + ' :: ' + e.message); } }
const J = (r) => r[0].json;
const NOW = '2026-10-13T04:00:00.000Z';
function cfgFor(now, extra) { return J(run('01_run_config.js', [{}], {}, { now: now })); }
const cfg = cfgFor(NOW);
const reqs = run('02_build_requests.js', [{}], { 'Run Config': [cfg] });
function httpFrom(responses) { return responses; }
function pipeline(responses, existingFranchises, cfgOverride) {
  const c = cfgOverride || cfg;
  const nodes = { 'Run Config': [c], 'Build AniList Requests': reqs.map((x) => x.json) };
  const v = J(run('03_validate_response.js', responses, nodes));
  if (!v.ok) return { v };
  const n = J(run('04_normalise.js', [v], nodes));
  const s = J(run('05_score.js', [n], nodes));
  const sel = J(run('06_select.js', [s], nodes));
  nodes['Select Candidates'] = [sel];
  nodes['Load Franchise Keys'] = existingFranchises || [{}];
  const r = J(run('07_resolve_identities.js', [{}], nodes));
  return { v, n, s, sel, r };
}
const P = pipeline(FX.good);

// ---- run config / window / idempotency ----
t('window 2026-10-13 is 2026-W42', () => assert.strictEqual(cfg.window, '2026-W42'));
t('window boundaries (ISO week)', () => {
  const w = (d) => cfgFor(d).window;
  assert.strictEqual(w('2026-01-01T00:00:00Z'), '2026-W01');
  assert.strictEqual(w('2027-01-01T00:00:00Z'), '2026-W53');
  assert.strictEqual(w('2024-12-30T00:00:00Z'), '2025-W01');
  assert.strictEqual(w('2026-10-11T23:59:59Z'), '2026-W41');
  assert.strictEqual(w('2026-10-12T00:00:00Z'), '2026-W42');
});
t('window start is the Monday', () => assert.strictEqual(cfg.window_start, '2026-10-12'));
t('same week, different clock time -> identical basis', () => {
  assert.strictEqual(cfgFor('2026-10-12T00:00:01Z').idempotency_basis, cfgFor('2026-10-18T23:59:59Z').idempotency_basis);
});
t('next week -> different basis', () => assert.notStrictEqual(cfgFor('2026-10-19T00:00:01Z').idempotency_basis, cfg.idempotency_basis));
t('idempotency key is sha256 of agent|version|canonical config; stable', () => {
  const k1 = crypto.createHash('sha256').update(cfg.idempotency_basis).digest('hex');
  const k2 = crypto.createHash('sha256').update(cfgFor(NOW).idempotency_basis).digest('hex');
  assert.strictEqual(k1, k2); assert.ok(/^[0-9a-f]{64}$/.test(k1));
  assert.ok(cfg.idempotency_basis.startsWith('CF-001|v0.1|{'));
});
t('canonical config has sorted keys and no timestamp', () => {
  const keys = Object.keys(JSON.parse(cfg.config_canonical));
  assert.deepStrictEqual(keys, keys.slice().sort());
  assert.ok(!/20\d\d-\d\d-\d\dT/.test(cfg.config_canonical));
});
// ---- query set ----
t('query set: exactly 4 requests, one per lane, within request budget', () => {
  assert.deepStrictEqual(reqs.map((r) => r.json.lane), FX.lanes);
  assert.ok(reqs.length <= 10);
  reqs.forEach((r) => { assert.ok(r.json.variables.perPage <= 15); assert.strictEqual(r.json.variables.page, 1); });
});
t('query set: nostalgia cutoff = (window year - 10) 0101', () => assert.strictEqual(reqs[3].json.variables.startLesser, 20160101));
t('query set: adult content excluded, anime only, no auth header in query node', () => {
  assert.ok(/isAdult: false/.test(reqs[0].json.query) && /type: ANIME/.test(reqs[0].json.query));
});
// ---- validation / error paths ----
function withLane(i, r) { const a = FX.good.slice(); a[i] = r; return a; }
t('validate OK: records headers and counts', () => {
  assert.ok(P.v.ok); assert.strictEqual(P.v.request_count, 4); assert.strictEqual(P.v.http[0].rate_limit_remaining, '29');
});
t('HTTP 429 -> CF001_ANILIST_RATE_LIMITED with retry_after, fails closed', () => {
  const v = J(run('03_validate_response.js', withLane(1, FX.resp([], { status: 429, headers: { 'retry-after': '60' }, body: { errors: [{ message: 'Too Many Requests.' }] } })), { 'Run Config': [cfg], 'Build AniList Requests': reqs.map((x) => x.json) }));
  assert.strictEqual(v.ok, false); assert.strictEqual(v.error_code, 'CF001_ANILIST_RATE_LIMITED'); assert.strictEqual(v.retry_after, '60'); assert.strictEqual(v.lanes, undefined);
});
const nodesV = { 'Run Config': [cfg], 'Build AniList Requests': reqs.map((x) => x.json) };
t('HTTP 403 -> CF001_ANILIST_UNAVAILABLE', () => assert.strictEqual(J(run('03_validate_response.js', withLane(0, FX.resp([], { status: 403, body: {} })), nodesV)).error_code, 'CF001_ANILIST_UNAVAILABLE'));
t('HTTP 502 -> CF001_ANILIST_5XX', () => assert.strictEqual(J(run('03_validate_response.js', withLane(2, FX.resp([], { status: 502, body: 'Bad Gateway' })), nodesV)).error_code, 'CF001_ANILIST_5XX'));
t('HTTP 404 plain -> CF001_ANILIST_HTTP_ERROR', () => assert.strictEqual(J(run('03_validate_response.js', withLane(2, FX.resp([], { status: 404, body: 'nope' })), nodesV)).error_code, 'CF001_ANILIST_HTTP_ERROR'));
t('network timeout (no response) -> CF001_ANILIST_NETWORK_ERROR', () => {
  const a = FX.good.slice(); a[3] = { error: 'timeout of 20000ms exceeded' };
  assert.strictEqual(J(run('03_validate_response.js', a, nodesV)).error_code, 'CF001_ANILIST_NETWORK_ERROR');
});
t('missing response item -> CF001_ANILIST_NETWORK_ERROR', () => assert.strictEqual(J(run('03_validate_response.js', FX.good.slice(0, 3), nodesV)).error_code, 'CF001_ANILIST_NETWORK_ERROR'));
t('GraphQL errors (HTTP 200) -> CF001_ANILIST_GRAPHQL_ERROR', () => assert.strictEqual(J(run('03_validate_response.js', withLane(0, FX.resp([], { body: { errors: [{ message: 'Variable "$sort" bad' }], data: null } })), nodesV)).error_code, 'CF001_ANILIST_GRAPHQL_ERROR'));
t('GraphQL errors (HTTP 400) -> CF001_ANILIST_GRAPHQL_ERROR', () => assert.strictEqual(J(run('03_validate_response.js', withLane(0, FX.resp([], { status: 400, body: { errors: [{ message: 'validation' }] } })), nodesV)).error_code, 'CF001_ANILIST_GRAPHQL_ERROR'));
t('malformed JSON string -> CF001_ANILIST_MALFORMED_RESPONSE', () => assert.strictEqual(J(run('03_validate_response.js', withLane(0, FX.resp([], { body: '<html>oops' })), nodesV)).error_code, 'CF001_ANILIST_MALFORMED_RESPONSE'));
t('media not an array -> CF001_ANILIST_MALFORMED_RESPONSE', () => assert.strictEqual(J(run('03_validate_response.js', withLane(0, FX.resp([], { body: { data: { Page: { media: {} } } } })), nodesV)).error_code, 'CF001_ANILIST_MALFORMED_RESPONSE'));
t('error evidence never contains tokens/auth', () => {
  const v = J(run('03_validate_response.js', withLane(1, FX.resp([], { status: 429, headers: { 'retry-after': '5', authorization: 'Bearer SECRET' }, body: {} })), nodesV));
  assert.ok(!JSON.stringify(v).includes('SECRET'));
});
// ---- normalisation ----
t('normalise: 14 raw records over 4 lanes accepted/rejected as designed', () => {
  assert.strictEqual(P.n.raw_record_count, 7 + 4 + 4 + 4 - 0);
  const reasons = P.n.rejected.map((r) => r.reason).sort();
  assert.deepStrictEqual(reasons, ['MISSING_IDENTITY', 'UNNORMALISABLE_TITLE', 'UNSUPPORTED_FORMAT']);
});
t('normalise: duplicates across lanes merged, lanes retained, sorted by id', () => {
  const ids = P.n.records.map((r) => r.anilist_id);
  assert.deepStrictEqual(ids, ids.slice().sort((a, b) => a - b));
  assert.strictEqual(new Set(ids).size, ids.length);
  const bravo = P.n.records.find((r) => r.anilist_id === 9002);
  assert.deepStrictEqual(bravo.lanes.map((l) => l.lane), ['CURRENT_TRENDING', 'POPULAR_PROVEN']);
  assert.strictEqual(bravo.lanes[0].rank, 2);
});
t('normalise: missing metrics stay null, never invented', () => {
  const g = P.n.records.find((r) => r.anilist_id === 9102);
  assert.strictEqual(g.popularity, null); assert.strictEqual(g.favourites, null); assert.strictEqual(g.average_score, null);
  const h = P.n.records.find((r) => r.anilist_id === 9103);
  assert.strictEqual(h.start_year, null);
});
t('normalise: key folding and franchise derivation', () => {
  const by = (id) => P.n.records.find((r) => r.anilist_id === id);
  assert.strictEqual(by(9002).normalised_title_key, 'synthetic bravo season 2');
  assert.strictEqual(by(9002).franchise_key, 'synthetic bravo');
  assert.strictEqual(by(9202).franchise_key, 'synthetic juliet');
  assert.strictEqual(by(9203).franchise_key, 'synthetic juliet');
});
t('normalise: native-only title is used as display only when it folds to a key (CJK rejected, not fabricated)', () => {
  assert.ok(!P.n.records.some((r) => r.anilist_id === 9006));
});
t('keys: ASCII folding of macrons and punctuation', () => {
  const x = run('04_normalise.js', [{ ok: true, lanes: [{ lane: 'CURRENT_TRENDING', sort: 'X', media: [{ id: 5, format: 'TV', title: { romaji: 'Ōkami-san & Zā' }, status: 'FINISHED' }] }] }], {});
  assert.strictEqual(J(x).records[0].normalised_title_key, 'okami san za');
});
// ---- scoring ----
function ref(r, windowYear, startMonths) {
  const nl = (x, rf) => (x > 0 ? Math.min(1, Math.log(1 + x) / Math.log(1 + rf)) : 0);
  const nP = nl(r.popularity, 500000), nF = nl(r.favourites, 50000), nT = nl(r.trending, 1000);
  const dem = 0.55 * nP + 0.25 * nT + 0.2 * nF;
  const age = windowYear - r.start_year, af = Math.min(1, Math.max(0, (age - 5) / 15));
  const nos = af * (0.5 * nF + 0.5 * nP);
  return { dem, nos, nP, nF, nT, af };
}
t('score: independent re-computation matches for a finished older title (9101)', () => {
  const r = P.s.records.find((x) => x.anilist_id === 9101);
  const e = ref(r, 2026);
  assert.strictEqual(r.score.demand_signal, Math.round(e.dem * 10000) / 10000);
  assert.strictEqual(r.score.nostalgia_signal, Math.round(e.nos * 10000) / 10000);
  const months = (2026 * 12 + 9) - (2016 * 12 + 5);          // window start 2026-10 vs end 2016, month defaulted to 6
  const tim = Math.min(1, 0.6 * Math.max(0, 1 - months / 36) + 0.4 * e.nT);
  assert.strictEqual(r.score.timeliness, Math.round(tim * 10000) / 10000);
  const edi = 0.35 * e.dem + 0.25 * 0.88 + 0.2 * Math.max(e.nos, tim) + 0.2 * e.nF;
  assert.strictEqual(r.score.editorial_potential, Math.round(edi * 10000) / 10000);
  assert.ok(r.score.missing_inputs.indexOf('end_date.month(defaulted_to_6)') >= 0);
});
t('score: every numeric signal within 0.0000-1.0000 with <=4 decimals', () => {
  P.s.records.forEach((r) => ['demand_signal', 'nostalgia_signal', 'editorial_potential', 'timeliness'].forEach((k) => {
    const v = r.score[k]; if (v === null) return;
    assert.ok(v >= 0 && v <= 1, k + '=' + v); assert.strictEqual(Math.round(v * 10000) / 10000, v);
  }));
});
t('score: unknown start year -> nostalgia null; all-null metrics -> zeros not invented', () => {
  const h = P.s.records.find((x) => x.anilist_id === 9103); assert.strictEqual(h.score.nostalgia_signal, null); assert.ok(h.score.missing_inputs.indexOf('start_year') >= 0);
  const g = P.s.records.find((x) => x.anilist_id === 9102); assert.strictEqual(g.score.demand_signal, 0); assert.ok(g.score.missing_inputs.indexOf('popularity') >= 0);
});
t('score: trend_state vocabulary, no direction states without history', () => {
  P.s.records.forEach((r) => assert.ok(['EVERGREEN', 'STEADY', 'UNKNOWN'].indexOf(r.score.trend_state) >= 0));
  assert.strictEqual(P.s.records.find((x) => x.anilist_id === 9201).score.trend_state, 'EVERGREEN');
  assert.strictEqual(P.s.records.find((x) => x.anilist_id === 9001).score.trend_state, 'UNKNOWN');
});
t('score: deterministic (two runs byte-identical) and no randomness/clock in scoring source', () => {
  const P2 = pipeline(FX.good);
  assert.strictEqual(JSON.stringify(P.s.records), JSON.stringify(P2.s.records));
  const src = fs.readFileSync(path.join(__dirname, '..', 'src', '05_score.js'), 'utf8');
  assert.ok(!/Math\.random|Date\.|new Date|crypto/.test(src));
});
// ---- selection ----
t('select: capped at max_candidates, deterministic order, one per title', () => {
  assert.ok(P.sel.selected.length <= cfg.max_candidates);
  const ids = P.sel.selected.map((r) => r.anilist_id); assert.strictEqual(new Set(ids).size, ids.length);
  const eds = P.sel.selected.map((r) => r.score.editorial_potential); assert.deepStrictEqual(eds, eds.slice().sort((a, b) => b - a));
  const strip = (o) => JSON.stringify(o, (k, v) => (k === 'retrieved_at' ? undefined : v));
  assert.strictEqual(strip(pipeline(FX.good).sel), strip(P.sel));
});
t('select: primary lane by fixed priority (9002 found by trending+popular -> CURRENT_TRENDING)', () => {
  assert.strictEqual(P.sel.selected.find((r) => r.anilist_id === 9002).primary_lane, 'CURRENT_TRENDING');
  assert.strictEqual(P.sel.selected.find((r) => r.anilist_id === 9201).primary_lane, 'NOSTALGIA_ELIGIBLE');
});
t('select: lane quota honoured (each populated lane contributes up to 2)', () => {
  const by = {}; P.sel.selected.forEach((r) => { by[r.primary_lane] = (by[r.primary_lane] || 0) + 1; });
  Object.keys(by).forEach((l) => assert.ok(by[l] >= 1));
  assert.ok(Object.keys(by).length >= 3);
});
// ---- identity resolution / payloads ----
t('resolve: every candidate has non-empty evidence with source, retrieval time, scoring version, lane hits', () => {
  assert.ok(P.r.payload.candidates.length > 0);
  P.r.payload.candidates.forEach((c) => {
    assert.ok(Array.isArray(c.signal_evidence) && c.signal_evidence.length === 3);
    const src = c.signal_evidence[0], sc = c.signal_evidence[2];
    assert.ok(src.source.indexOf('AniList') >= 0 && src.retrieved_at && src.signal_use === 'market_research_only');
    assert.strictEqual(sc.scoring_version, 'cf001-score-v0.1'); assert.strictEqual(sc.observation_window, '2026-W42');
    assert.ok(c.signal_evidence[1].hits.length >= 1);
    assert.strictEqual(c.topic_key, 'market-signal'); assert.strictEqual(c.topic_key, c.topic_key.toLowerCase());
  });
});
t('resolve: no field implies legal/rights authorisation', () => {
  const s = JSON.stringify(P.r.payload, (k, v) => (k === 'notice' ? undefined : v)).toLowerCase();
  ['licensed', 'cleared', 'rights_approved', 'copyright_ok', 'monetis'].forEach((w) => assert.ok(s.indexOf(w) < 0, w));
});
t('resolve: Juliet seasons share one franchise; Lima near-match keys are BLOCKED and produce no candidates', () => {
  const f = P.r.payload.franchises;
  assert.strictEqual(f.filter((x) => x.normalised_key === 'synthetic juliet').length, 1);
  const lima = f.filter((x) => x.normalised_key.indexOf('synthetic lima') === 0);
  if (lima.length === 2) { lima.forEach((x) => assert.ok(x.blocked)); assert.ok(!P.r.payload.candidates.some((c) => c.anilist_id === 9302 || c.anilist_id === 9303)); }
});
t('resolve: forced near-match against an existing franchise key blocks the new one, exact match does not', () => {
  const Q = pipeline(FX.good, [{ normalised_key: 'synthetic foxtrots', franchise_id: 'x', status: 'READY' }, { normalised_key: 'synthetic india', franchise_id: 'y', status: 'READY' }]);
  const fox = Q.r.payload.franchises.find((x) => x.normalised_key === 'synthetic foxtrot');
  const ind = Q.r.payload.franchises.find((x) => x.normalised_key === 'synthetic india');
  if (fox) { assert.ok(fox.blocked); assert.ok(/^NEAR_MATCH_FRANCHISE_KEY:/.test(fox.block_reason)); assert.ok(!Q.r.payload.candidates.some((c) => c.anilist_id === 9101)); }
  if (ind) assert.strictEqual(ind.blocked, false);
});
t('resolve: title identity collision inside the batch -> both BLOCKED AMBIGUOUS_SOURCE_IDENTITY', () => {
  const dup = FX.data.trending.slice(0, 1).concat([JSON.parse(JSON.stringify(FX.data.trending[0]))]);
  dup[1].id = 9999;
  const q = pipeline([FX.resp(dup), FX.resp([]), FX.resp([]), FX.resp([])]);
  assert.strictEqual(q.r.blocked.length, 2); assert.ok(q.r.blocked.every((b) => b.reason === 'AMBIGUOUS_SOURCE_IDENTITY'));
  assert.strictEqual(q.r.payload.candidates.length, 0);
});
t('resolve: candidate without popularity/favourites is REJECTED INSUFFICIENT_SIGNAL_DATA, not READY', () => {
  const only = FX.data.popular.filter((x) => x.id === 9102);
  const q = pipeline([FX.resp([]), FX.resp(only), FX.resp([]), FX.resp([])]);
  assert.strictEqual(q.r.payload.candidates.length, 1);
  assert.strictEqual(q.r.payload.candidates[0].ready, false); assert.strictEqual(q.r.payload.candidates[0].rejection_reason, 'INSUFFICIENT_SIGNAL_DATA');
});
t('resolve: dedupe-relevant fields contain no timestamp/uuid', () => {
  P.r.payload.candidates.forEach((c) => { assert.ok(/^[a-z0-9-]+$/.test(c.topic_key)); assert.ok(FX.lanes.indexOf(c.content_lane) >= 0); });
});
t('replay of identical input -> identical payload apart from retrieval timestamp', () => {
  const strip = (o) => JSON.stringify(o, (k, v) => (k === 'retrieved_at' ? undefined : v));
  assert.strictEqual(strip(pipeline(FX.good).r.payload), strip(P.r.payload));
});
// ---- zero input ----
t('zero usable records -> ok, zero_input, empty payload, nothing fabricated', () => {
  const q = pipeline([FX.resp([]), FX.resp([]), FX.resp([]), FX.resp([])]);
  assert.ok(q.r.ok && q.r.zero_input); assert.deepStrictEqual(q.r.payload, { franchises: [], titles: [], candidates: [] });
});
t('all records rejected -> zero input with rejection evidence', () => {
  const q = pipeline([FX.resp([{ id: null, format: 'TV' }]), FX.resp([]), FX.resp([]), FX.resp([])]);
  assert.ok(q.r.zero_input); assert.strictEqual(q.r.rejected[0].reason, 'MISSING_IDENTITY');
});
// ---- failure shaping / summaries ----
t('shape failure: pure-stage failure and DB error both normalise; detail truncated', () => {
  const nodes = { 'Begin Run': [{ agent_run_id: 'run-1' }], 'AniList GraphQL': [{}, {}] };
  const a = J(run('08_shape_failure.js', [{ ok: false, error_code: 'CF001_ANILIST_RATE_LIMITED', error_detail: 'x', retry_after: '60' }], nodes));
  assert.strictEqual(a.error_code, 'CF001_ANILIST_RATE_LIMITED'); assert.strictEqual(a.provider_call_count, 2); assert.strictEqual(a.agent_run_id, 'run-1');
  const b = J(run('08_shape_failure.js', [{ error: 'duplicate key value violates unique constraint ' + 'x'.repeat(900) }], nodes));
  assert.strictEqual(b.error_code, 'CF001_DB_ERROR'); assert.ok(b.error_detail.length <= 500);
  assert.strictEqual(b.output_summary.paid_calls, 0);
});
t('raise failure always throws', () => {
  const nodes = { 'Shape Failure': [{ error_code: 'CF001_DB_ERROR', error_detail: 'd' }] };
  assert.throws(() => run('11_raise_failure.js', [{ agent_run_id: 'r' }], nodes), /CF001_DB_ERROR/);
  assert.throws(() => run('11_raise_failure.js', [{}], nodes), /CF001_FAILURE_NOT_RECORDED/);
});
t('replay summary reports zero provider calls and zero paid calls', () => {
  const o = J(run('10_replay_summary.js', [{ agent_run_id: 'r', run_state: 'SUCCEEDED', attempt_count: 1, output_summary: { result: 'OK' }, candidates: [{ a: 1 }] }], { 'Begin Run': [{ disposition: 'REPLAY' }] }));
  assert.strictEqual(o.result, 'REPLAY_EXISTING_RUN'); assert.strictEqual(o.provider_calls_this_execution, 0); assert.strictEqual(o.paid_calls, 0);
});
// ---- zero paid providers / no secrets ----
t('no LLM/paid provider names, secrets or admin roles anywhere in sources or SQL', () => {
  const dirs = ['src', 'sql'];
  const bad = /openai|anthropic|gemini|elevenlabs|replicate|midjourney|stability|api[_-]?key|bearer |password|service_role|supabase\.co|postgres:\/\//i;
  dirs.forEach((d) => fs.readdirSync(path.join(__dirname, '..', d)).forEach((f) => {
    const s = fs.readFileSync(path.join(__dirname, '..', d, f), 'utf8');
    const lines = s.split('\n').filter((l) => !/^\s*(--|\/\/)/.test(l));
    assert.ok(!bad.test(lines.join('\n')), d + '/' + f);
  }));
});
t('SQL touches only cf.* and only allowed verbs (no DELETE/DROP/ALTER/CREATE/GRANT/SET ROLE/TRIGGER/function exec)', () => {
  fs.readdirSync(path.join(__dirname, '..', 'sql')).forEach((f) => {
    const s = fs.readFileSync(path.join(__dirname, '..', 'sql', f), 'utf8').split('\n').filter((l) => !/^\s*--/.test(l)).join('\n');
    assert.ok(!/\b(delete|drop|alter|create|grant|revoke|truncate|set\s+role|session_replication_role|disable|execute|do\s+\$)\b/i.test(s), f);
    assert.ok(!/\bpublic\./i.test(s), f);
    const targets = (s.match(/\b(?:from|join|into|update)\s+(cf\.[a-z_]+)/gi) || []).map((x) => x.split(/\s+/).pop());
    targets.forEach((x) => assert.ok(['cf.agent_runs', 'cf.anime_franchises', 'cf.anime_titles', 'cf.research_candidates'].indexOf(x) >= 0, f + ' ' + x));
  });
});
t('run summary: zero LLM/paid calls, source label, request count, JSON-serialisable', () => {
  const sm = P.r.summary; assert.strictEqual(sm.llm_calls, 0); assert.strictEqual(sm.paid_calls, 0); assert.strictEqual(sm.model, 'none');
  assert.strictEqual(sm.anilist_requests, 4); assert.strictEqual(sm.result, 'COMPLETED'); assert.ok(JSON.parse(JSON.stringify(sm)));
  assert.strictEqual(pipeline([FX.resp([]), FX.resp([]), FX.resp([]), FX.resp([])]).r.summary.result, 'NO_INPUT');
});
console.log('\n' + pass + ' passed, ' + fail + ' failed');
process.exit(fail ? 1 : 0);
