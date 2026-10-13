'use strict';
const { run } = require('./harness');
const J = (r) => r[0].json;
function runPipeline(trigger, upstreamRow, now) {
  const cfg = J(run('01_run_config.js', [trigger || {}], {}, { now: now }));
  const nodes = { 'Run Config': [cfg] };
  const t = J(run('04_resolve_title.js', [upstreamRow || {}], nodes));
  if (!t.ok) return { cfg, t, final: t };
  const v = J(run('05_validate_observation.js', [t], nodes));
  if (!v.ok) return { cfg, t, v, final: v };
  const n = J(run('06_normalise_boundaries.js', [v], nodes));
  if (!n.ok) return { cfg, t, v, n, final: n };
  const b = J(run('07_build_intelligence.js', [n], nodes));
  if (!b.ok) return { cfg, t, v, n, b, final: b };
  const p = J(run('08_validate_provenance.js', [b], nodes));
  return { cfg, t, v, n, b, p, final: p };
}
module.exports = { runPipeline, J };
