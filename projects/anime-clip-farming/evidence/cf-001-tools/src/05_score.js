// @include common
// Score Signals: cf001-score-v0.1. Fixed formulas, fixed reference points, no randomness, no judgement.
const ctx = $input.first().json;
if (!ctx.ok) return [{ json: ctx }];
const cfg = $('Run Config').first().json;
const asOf = cfg.window_start.split('-').map(Number);          // window start date drives all time maths
const asOfMonths = asOf[0] * 12 + (asOf[1] - 1);
const W = { dem: [0.55, 0.25, 0.20], nos: [0.5, 0.5], edi: [0.35, 0.25, 0.20, 0.20], tim: { releasing: 0.6, notYet: 0.3, finished: 0.6, trend: 0.4, decayMonths: 36 } };
const scored = ctx.records.map(function (r) {
  const missing = [];
  ['popularity', 'favourites', 'trending', 'average_score'].forEach(function (f) { if (r[f] === null) missing.push(f); });
  if (r.start_year === null) missing.push('start_year');
  const nP = normLog(r.popularity, CF_REF.popularity), nF = normLog(r.favourites, CF_REF.favourites), nT = normLog(r.trending, CF_REF.trending);
  const demand = W.dem[0] * nP + W.dem[1] * nT + W.dem[2] * nF;
  let nostalgia = null, ageYears = null, ageFactor = null;
  if (r.start_year !== null) {
    ageYears = cfg.window_year - r.start_year;
    ageFactor = clamp((ageYears - 5) / 15, 0, 1);
    nostalgia = ageFactor * (W.nos[0] * nF + W.nos[1] * nP);
  }
  let base = 0, monthsSinceEnd = null;
  if (r.status === 'RELEASING') base = W.tim.releasing;
  else if (r.status === 'NOT_YET_RELEASED') base = W.tim.notYet;
  else if (r.status === 'FINISHED') {
    if (r.end_date.year !== null) {
      let em = r.end_date.month;
      if (em === null) { em = 6; missing.push('end_date.month(defaulted_to_6)'); }
      monthsSinceEnd = Math.max(0, asOfMonths - (r.end_date.year * 12 + (em - 1)));
      base = W.tim.finished * Math.max(0, 1 - monthsSinceEnd / W.tim.decayMonths);
    } else { missing.push('end_date.year'); }
  }
  const timeliness = Math.min(1, base + W.tim.trend * nT);
  const avg = r.average_score === null ? 0 : r.average_score / 100;
  const editorial = W.edi[0] * demand + W.edi[1] * avg + W.edi[2] * Math.max(nostalgia === null ? 0 : nostalgia, timeliness) + W.edi[3] * nF;
  let trend = 'UNKNOWN';
  if (r.status === 'FINISHED' && ageYears !== null && ageYears >= 10 && nF >= 0.6) trend = 'EVERGREEN';
  else if (r.status === 'FINISHED' && nP >= 0.5) trend = 'STEADY';
  return Object.assign({}, r, { score: {
    scoring_version: CF_SCORING_VERSION,
    demand_signal: r4(demand), nostalgia_signal: nostalgia === null ? null : r4(nostalgia),
    editorial_potential: r4(editorial), timeliness: r4(timeliness), trend_state: trend,
    inputs: { norm_popularity: r4(nP), norm_favourites: r4(nF), norm_trending: r4(nT), average_score_fraction: r4(avg),
      age_years: ageYears, age_factor: ageFactor === null ? null : r4(ageFactor), months_since_end: monthsSinceEnd,
      timeliness_base: r4(base), window_start: cfg.window_start, references: CF_REF },
    missing_inputs: missing,
  } });
});
const out = Object.assign({}, ctx);
out.records = scored;
return [{ json: out }];
