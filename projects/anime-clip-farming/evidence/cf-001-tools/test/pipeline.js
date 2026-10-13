'use strict';
const { run } = require('./harness');
const J = (r) => r[0].json;
function runPipeline(responses, now, existingFranchises) {
  const cfg = J(run('01_run_config.js', [{}], {}, { now: now }));
  const reqs = run('02_build_requests.js', [{}], { 'Run Config': [cfg] }).map((x) => x.json);
  const nodes = { 'Run Config': [cfg], 'Build AniList Requests': reqs };
  const v = J(run('03_validate_response.js', responses, nodes));
  if (!v.ok) return { cfg, reqs, v };
  const n = J(run('04_normalise.js', [v], nodes));
  const s = J(run('05_score.js', [n], nodes));
  const sel = J(run('06_select.js', [s], nodes));
  nodes['Select Candidates'] = [sel];
  nodes['Load Franchise Keys'] = existingFranchises && existingFranchises.length ? existingFranchises : [{}];
  const r = J(run('07_resolve_identities.js', [{}], nodes));
  return { cfg, reqs, v, n, s, sel, r };
}
module.exports = { runPipeline, J };
