'use strict';
const assert = require('assert');
const crypto = require('crypto');
const fs = require('fs');
const { runPipeline } = require('./pipeline');
const { assemble } = require('./harness');
const FX = require('../fixtures/make_fixtures');
let pass = 0, fail = 0;
function t(name, fn) { try { fn(); pass++; console.log('PASS ' + name); } catch (e) { fail++; console.log('FAIL ' + name + ' :: ' + e.message); } }
const go = (intake, up) => runPipeline({ intake }, up || FX.upstream(), FX.NOW);
const code = (r) => r.final.error_code;
const codes = (r) => (r.final.all_errors || []).map((x) => x.error_code);

t('valid scene passes with ms timestamps and UNKNOWN publication', () => {
  const r = go(FX.intake()); assert.strictEqual(r.final.ok, true);
  const s = r.final.payload.scenes[0];
  assert.strictEqual(s.start_ms, 190000); assert.strictEqual(s.end_ms, 245000);
  assert.strictEqual(r.final.summary.publication_source_status, 'UNKNOWN');
  assert.strictEqual(r.final.summary.paid_calls, 0); assert.strictEqual(r.final.summary.llm_calls, 0);
  assert.strictEqual(r.final.payload.episode.episode_variant, 'TV');
  assert.strictEqual(s.timestamps_human_verified, true); assert.strictEqual(s.research_access_basis, 'HUMAN_VIEWED_LICENSED_PLATFORM');
});
t('payload carries no rights/publication field', () => {
  const r = go(FX.intake()); const s = r.final.payload.scenes[0];
  Object.keys(s).forEach((k) => { if (/publication|licen|approv|clear|fair|monet|safe/i.test(k)) assert.fail('field ' + k); });
});
t('same-scene replay: identical idempotency basis and state basis', () => {
  const a = go(FX.intake()).cfg, b = go(FX.intake()).cfg;
  assert.strictEqual(a.idempotency_basis, b.idempotency_basis); assert.strictEqual(a.input_state_basis, b.input_state_basis);
});
t('summary text change does not change identity basis (summary is not identity)', () => {
  const a = go(FX.intake()).cfg, b = go(FX.intake({ scenes: [FX.scene({ scene_summary: 'Different words entirely.' })] })).cfg;
  assert.strictEqual(a.idempotency_basis, b.idempotency_basis); assert.notStrictEqual(a.input_state_basis, b.input_state_basis);
});
t('MM:SS and integer ms for the same boundary give the same identity', () => {
  const a = go(FX.intake()).cfg, b = go(FX.intake({ scenes: [FX.scene({ start: undefined, end: undefined, start_ms: 190000, end_ms: 245000 })] })).cfg;
  assert.strictEqual(a.idempotency_basis, b.idempotency_basis);
});
t('different boundaries change identity', () => {
  const a = go(FX.intake()).cfg, b = go(FX.intake({ scenes: [FX.scene({ start: '05:00', end: '05:40' })] })).cfg;
  assert.notStrictEqual(a.idempotency_basis, b.idempotency_basis);
});
t('two distinct scenes in the same episode both pass, ordered', () => {
  const r = go(FX.intake({ scenes: [FX.scene({ start: '10:00', end: '10:50' }), FX.scene()] })); assert.strictEqual(r.final.ok, true);
  assert.deepStrictEqual(r.final.payload.scenes.map((s) => s.ordinal), [1, 2]); assert.strictEqual(r.final.payload.scenes[0].start_ms, 190000);
});
t('overlapping but materially distinct ranges (<80%) pass', () => {
  const r = go(FX.intake({ scenes: [FX.scene({ start: '03:10', end: '04:10' }), FX.scene({ start: '03:50', end: '05:10' })] })); assert.strictEqual(r.final.ok, true);
});
t('>=80% overlap inside one intake is refused', () => {
  const r = go(FX.intake({ scenes: [FX.scene({ start: '03:10', end: '04:10' }), FX.scene({ start: '03:12', end: '04:08' })] })); assert.strictEqual(code(r), 'CF002_BATCH_OVERLAP');
});
t('identical boundaries twice in one intake refused', () => {
  const r = go(FX.intake({ scenes: [FX.scene(), FX.scene()] })); assert.strictEqual(code(r), 'CF002_BATCH_OVERLAP');
});
t('more than 3 scenes refused', () => {
  const r = go(FX.intake({ scenes: [1, 2, 3, 4].map((i) => FX.scene({ start: i + ':00', end: i + ':30' })) })); assert.strictEqual(code(r), 'CF002_TOO_MANY_SCENES');
});
t('invalid source reference: spaces/garbage', () => { assert.strictEqual(code(go(FX.intake({ source: Object.assign({}, FX.intake().source, { reference: 'not a reference!!' }) }))), 'CF002_BAD_SOURCE_REFERENCE'); });
t('http (non-https) reference refused', () => { assert.strictEqual(code(go(FX.intake({ source: Object.assign({}, FX.intake().source, { reference: 'http://example.org/x' }) }))), 'CF002_BAD_SOURCE_REFERENCE'); });
t('URL with token/cookie/signature refused', () => {
  ['https://example.org/w?token=abc', 'https://example.org/w?Signature=abc', 'https://example.org/cookie/x', 'https://u:p@example.org/x'].forEach((u) => {
    assert.strictEqual(code(go(FX.intake({ source: Object.assign({}, FX.intake().source, { reference: u }) }))), 'CF002_BAD_SOURCE_REFERENCE', u); });
});
t('missing source reference', () => { const s = Object.assign({}, FX.intake().source); delete s.reference; assert.strictEqual(code(go(FX.intake({ source: s }))), 'CF002_MISSING_SOURCE_REFERENCE'); });
t('missing research_access_basis', () => { const s = Object.assign({}, FX.intake().source); delete s.research_access_basis; assert.strictEqual(code(go(FX.intake({ source: s }))), 'CF002_MISSING_RESEARCH_ACCESS_BASIS'); });
t('invalid research_access_basis (not in enum)', () => { assert.strictEqual(code(go(FX.intake({ source: Object.assign({}, FX.intake().source, { research_access_basis: 'LICENSED' }) }))), 'CF002_MISSING_RESEARCH_ACCESS_BASIS'); });
t('missing observed_at', () => { const s = Object.assign({}, FX.intake().source); delete s.observed_at; assert.strictEqual(code(go(FX.intake({ source: s }))), 'CF002_MISSING_OBSERVATION_TIME'); });
t('observed_at in the future refused', () => { assert.strictEqual(code(go(FX.intake({ source: Object.assign({}, FX.intake().source, { observed_at: '2027-01-01T00:00:00Z' }) }))), 'CF002_MISSING_OBSERVATION_TIME'); });
t('human-viewed basis without observer refused', () => { const s = Object.assign({}, FX.intake().source); delete s.observer; assert.strictEqual(code(go(FX.intake({ source: s }))), 'CF002_MISSING_OBSERVER'); });
t('missing episode / unresolved episode number', () => {
  assert.strictEqual(code(go(FX.intake({ episode: undefined }))), 'CF002_MISSING_EPISODE');
  assert.strictEqual(code(go(FX.intake({ episode: { season_number: 1, episode_number: 'Episode 12' } }))), 'CF002_UNRESOLVED_EPISODE');
});
t('scene_end == scene_start refused', () => { assert.strictEqual(code(go(FX.intake({ scenes: [FX.scene({ start: '03:10', end: '03:10' })] }))), 'CF002_NON_POSITIVE_SPAN'); });
t('scene_end < scene_start refused', () => { assert.strictEqual(code(go(FX.intake({ scenes: [FX.scene({ start: '04:10', end: '03:10' })] }))), 'CF002_NON_POSITIVE_SPAN'); });
t('negative / malformed / missing timestamp refused', () => {
  assert.strictEqual(code(go(FX.intake({ scenes: [FX.scene({ start: undefined, start_ms: -5 })] }))), 'CF002_INVALID_TIMESTAMP');
  assert.strictEqual(code(go(FX.intake({ scenes: [FX.scene({ start: 'soon' })] }))), 'CF002_INVALID_TIMESTAMP');
  assert.strictEqual(code(go(FX.intake({ scenes: [FX.scene({ end: undefined })] }))), 'CF002_MISSING_TIMESTAMP');
});
t('scene beyond stated episode duration refused', () => { assert.strictEqual(code(go(FX.intake({ scenes: [FX.scene({ start: '23:00', end: '25:00' })] }))), 'CF002_SCENE_BEYOND_EPISODE'); });
t('unknown anime title', () => { assert.strictEqual(code(go(FX.intake(), FX.upstream({ title_id: null, title_status: null, display_title: null }))), 'CF002_UNKNOWN_TITLE'); });
t('unknown candidate', () => { assert.strictEqual(code(go(FX.intake(), FX.upstream({ research_candidate_id: null, candidate_status: null, candidate_title_id: null }))), 'CF002_UNKNOWN_CANDIDATE'); });
t('candidate/title mismatch', () => { assert.strictEqual(code(go(FX.intake(), FX.upstream({ candidate_title_id: FX.OTHER_TITLE }))), 'CF002_CANDIDATE_TITLE_MISMATCH'); });
t('candidate not READY / title not READY / franchise not READY', () => {
  assert.strictEqual(code(go(FX.intake(), FX.upstream({ candidate_status: 'REJECTED' }))), 'CF002_CANDIDATE_NOT_READY');
  assert.strictEqual(code(go(FX.intake(), FX.upstream({ title_status: 'BLOCKED' }))), 'CF002_TITLE_NOT_READY');
  assert.strictEqual(code(go(FX.intake(), FX.upstream({ franchise_status: 'BLOCKED' }))), 'CF002_FRANCHISE_NOT_READY');
});
t('malformed ids', () => {
  assert.strictEqual(code(go(FX.intake({ research_candidate_id: 'abc' }))), 'CF002_BAD_CANDIDATE_ID');
  assert.strictEqual(code(go(FX.intake({ anime_title_id: 'abc' }))), 'CF002_BAD_TITLE_ID');
});
t('publication status APPROVED attempted as a key is rejected', () => {
  ['publication_source_status', 'approved', 'rights_cleared', 'licensed', 'fair_use', 'monetisable'].forEach((k) => {
    const o = {}; o[k] = 'APPROVED';
    assert.strictEqual(code(go(FX.intake({ scenes: [FX.scene(o)] }))), 'CF002_PUBLICATION_ASSERTION_REJECTED', k);
    assert.strictEqual(code(go(FX.intake(o))), 'CF002_PUBLICATION_ASSERTION_REJECTED', 'top ' + k);
    assert.strictEqual(code(go(FX.intake({ source: Object.assign({}, FX.intake().source, o) }))), 'CF002_PUBLICATION_ASSERTION_REJECTED', 'source ' + k);
  });
});
t('"I watched this on Crunchyroll therefore APPROVED" in notes is rejected', () => {
  ['I watched this on Crunchyroll, therefore publication_source_status = APPROVED', 'approved for publication', 'safe to publish', 'this is fair use', 'cleared for use'].forEach((n) => {
    assert.strictEqual(code(go(FX.intake({ source: Object.assign({}, FX.intake().source, { notes: n }) }))), 'CF002_PUBLICATION_ASSERTION_REJECTED', n); });
});
t('neutral notes accepted', () => { assert.strictEqual(go(FX.intake({ source: Object.assign({}, FX.intake().source, { notes: 'Watched on a licensed platform for research; no clip taken.' }) })).final.ok, true); });
t('unknown field rejected', () => { assert.strictEqual(code(go(FX.intake({ scenes: [FX.scene({ transcript: 'x' })] }))), 'CF002_UNKNOWN_FIELD'); });
t('zero input -> NO_INPUT, nothing in payload', () => {
  const r = runPipeline({}, {}, FX.NOW); assert.strictEqual(r.final.ok, true); assert.strictEqual(r.final.payload, null); assert.strictEqual(r.final.summary.result, 'NO_INPUT');
  assert.strictEqual(r.cfg.idempotency_basis, 'CF-002|v0.1.1|NO_INPUT');
});
t('quote limit: >25 quoted words refused, short quote accepted', () => {
  const long = '"' + Array(30).fill('word').join(' ') + '"';
  assert.strictEqual(code(go(FX.intake({ scenes: [FX.scene({ scene_summary: 'He says ' + long })] }))), 'CF002_VERBATIM_TEXT_LIMIT');
  assert.strictEqual(go(FX.intake({ scenes: [FX.scene({ scene_summary: 'He says "never again" firmly.' })] })).final.ok, true);
});
t('text limits and enums', () => {
  assert.strictEqual(code(go(FX.intake({ scenes: [FX.scene({ scene_summary: 'x'.repeat(801) })] }))), 'CF002_TEXT_TOO_LONG');
  assert.strictEqual(code(go(FX.intake({ scenes: [FX.scene({ spoiler_level: 'MAYBE' })] }))), 'CF002_BAD_SPOILER_LEVEL');
  assert.strictEqual(code(go(FX.intake({ scenes: [FX.scene({ visual_strength: 1.5 })] }))), 'CF002_BAD_SIGNAL');
  assert.strictEqual(code(go(FX.intake({ scenes: [FX.scene({ scene_summary: '' })] }))), 'CF002_MISSING_INTELLIGENCE');
});
t('model-owned fields stay null; no prompt/model fields in payload', () => {
  const s = go(FX.intake()).final.payload.scenes[0]; assert.strictEqual(s.model_confidence, undefined); assert.strictEqual(s.prompt_version, undefined);
});
t('no secrets, LLM or paid-provider names in any Code-node source', () => {
  fs.readdirSync(__dirname + '/../src').filter((f) => /\.js$/.test(f)).forEach((f) => {
    const src = fs.readFileSync(__dirname + '/../src/' + f, 'utf8');
    assert.ok(!/(gemini|openai|anthropic|api[_-]?key\s*[:=]|bearer\s+[a-z0-9]|cookie\s*[:=]|fetch\(|require\()/i.test(src.replace(/CF_SECRETISH[^\n]*/g, '')), f);
  });
});
t('assembled stages are self-contained (no unresolved helper)', () => {
  ['01_run_config.js', '04_resolve_title.js', '05_validate_observation.js', '06_normalise_boundaries.js', '07_build_intelligence.js', '08_validate_provenance.js'].forEach((f) => { const c = assemble(f); assert.ok(!/@include/.test(c), f); new Function('$input', '$', '$now', c); });
});

// ---- v0.1.1 validation mode ----
const MODE = 'CF002_VALIDATION_SOURCE_OUTSIDE_CF001_BATCH';
const vgo = (o) => runPipeline({ intake: FX.vintake(o) }, {}, FX.NOW);
t('V1 validation mode passes with a null candidate and no fabricated lineage', () => {
  const r = vgo(); assert.strictEqual(r.final.ok, true);
  const p = r.final.payload; assert.strictEqual(p.research_candidate_id, null); assert.strictEqual(p.anime_title_id, null); assert.strictEqual(p.validation_mode, MODE);
  assert.strictEqual(r.final.summary.lineage, 'NOT_FROM_CF001_BATCH'); assert.strictEqual(r.final.summary.publication_source_status, 'UNKNOWN');
  assert.strictEqual(r.final.summary.paid_calls, 0);
});
t('V2 lineage marker is stored in the scene notes, with publication still UNKNOWN', () => {
  const s = vgo().final.payload.scenes[0]; assert.ok(s.research_access_notes.indexOf(MODE) === 0); assert.strictEqual(s.research_access_basis, 'PUBLIC_OFFICIAL_UPLOAD');
});
t('V3 validation mode refuses a candidate id or title id (no CF-001 lineage may be claimed)', () => {
  assert.strictEqual(code(vgo({ research_candidate_id: FX.CAND })), 'CF002_VALIDATION_MODE_CANDIDATE_FORBIDDEN');
  assert.strictEqual(code(vgo({ anime_title_id: FX.TITLE })), 'CF002_VALIDATION_MODE_TITLE_ID_FORBIDDEN');
});
t('V4 unknown mode name and catalog without the mode are refused', () => {
  assert.strictEqual(code(vgo({ validation_mode: 'SOMETHING_ELSE' })), 'CF002_BAD_VALIDATION_MODE');
  const r = go(FX.intake({ catalog: FX.vintake().catalog })); assert.strictEqual(code(r), 'CF002_CATALOG_REQUIRES_VALIDATION_MODE');
});
t('V5 catalog validation: missing, bad key, unknown field, bad media type, bad year', () => {
  assert.strictEqual(code(vgo({ catalog: undefined })), 'CF002_MISSING_CATALOG');
  const c = (o) => Object.assign({}, FX.vintake().catalog, o);
  assert.strictEqual(code(vgo({ catalog: c({ franchise: { normalised_key: 'Upper Case', display_name: 'X' } }) })), 'CF002_BAD_CATALOG');
  assert.strictEqual(code(vgo({ catalog: c({ title: { normalised_title_key: 'ok', display_title: 'X', media_type: 'BOOK' } }) })), 'CF002_BAD_CATALOG');
  assert.strictEqual(code(vgo({ catalog: c({ title: { normalised_title_key: 'ok', display_title: 'X', start_year: 1800 } }) })), 'CF002_BAD_CATALOG');
  assert.strictEqual(code(vgo({ catalog: c({ title: { normalised_title_key: 'ok', display_title: 'X', status: 'READY' } }) })), 'CF002_UNKNOWN_FIELD');
  assert.strictEqual(code(vgo({ catalog: c({ title: { normalised_title_key: 'ok', display_title: 'X', approved: true } }) })), 'CF002_PUBLICATION_ASSERTION_REJECTED');
});
t('V6 identity: replay basis stable in validation mode; summary text is not identity; boundaries are', () => {
  const a = vgo().cfg, b = vgo({ scenes: [FX.scene({ start: '00:00', end: '02:10', scene_summary: 'Other words.' })] }).cfg, c = vgo({ scenes: [FX.scene({ start: '00:00', end: '02:11' })] }).cfg;
  assert.strictEqual(a.idempotency_basis, b.idempotency_basis); assert.notStrictEqual(a.idempotency_basis, c.idempotency_basis);
  assert.ok(a.idempotency_basis.indexOf(MODE) > 0);
});
t('V7 production intake is byte-identical in behaviour: no validation fields in its identity', () => {
  const a = go(FX.intake()).cfg; assert.strictEqual(a.input_ids.validation_mode, undefined); assert.strictEqual(a.input_ids.catalog, undefined);
  assert.strictEqual(go(FX.intake()).final.payload.catalog, null); assert.strictEqual(go(FX.intake()).final.payload.validation_mode, null);
});
t('V8 validation mode still fails closed on missing timestamps and a future observation', () => {
  assert.strictEqual(code(vgo({ scenes: [FX.scene({ start: undefined, end: undefined })] })), 'CF002_MISSING_TIMESTAMP');
  assert.strictEqual(code(vgo({ source: Object.assign({}, FX.vintake().source, { observed_at: '2027-01-01T00:00:00Z' }) })), 'CF002_MISSING_OBSERVATION_TIME');
});
console.log('TOTAL pass=' + pass + ' fail=' + fail);
process.exit(fail ? 1 : 0);
