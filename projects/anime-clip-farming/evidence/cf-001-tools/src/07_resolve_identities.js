// @include common
// Resolve Identities: franchise/title keys, near-match and collision blocking, candidate payloads. No DB writes here.
const ctx = $('Select Candidates').first().json;
if (!ctx.ok) return [{ json: ctx }];
const cfg = $('Run Config').first().json;
const existing = $('Load Franchise Keys').all().map(function (i) { return i.json; }).filter(function (j) { return j && j.normalised_key; });
const existingKeys = existing.map(function (j) { return j.normalised_key; });
const LABEL = { CURRENT_TRENDING: 'current trending', POPULAR_PROVEN: 'popular proven', EVERGREEN_DEMAND: 'evergreen demand', NOSTALGIA_ELIGIBLE: 'nostalgia eligible' };
const groups = {};
ctx.selected.forEach(function (r) { (groups[r.franchise_key] = groups[r.franchise_key] || []).push(r); });
const fkeys = Object.keys(groups).sort();
const newKeys = fkeys.filter(function (k) { return existingKeys.indexOf(k) < 0; });
function nearOf(k) {
  if (k.length < 8) return null;
  for (const e of existingKeys.concat(newKeys)) { if (e !== k && e.length >= 8 && lev(k, e) <= 2) return e; }
  return null;
}
const franchises = fkeys.map(function (k) {
  const members = groups[k].slice().sort(function (a, b) { return (a.display_title.length - b.display_title.length) || (a.anilist_id - b.anilist_id); });
  const near = existingKeys.indexOf(k) >= 0 ? null : nearOf(k);
  return { normalised_key: k, display_name: members[0].display_title, blocked: near !== null, block_reason: near !== null ? 'NEAR_MATCH_FRANCHISE_KEY:' + near : null };
});
const fBlocked = {};
franchises.forEach(function (f) { fBlocked[f.normalised_key] = f.blocked; });
const sig = {};
ctx.selected.forEach(function (r) { const s = r.franchise_key + '|' + r.normalised_title_key + '|' + r.start_year; (sig[s] = sig[s] || []).push(r.anilist_id); });
const blocked = [];
const titles = [], candidates = [];
ctx.selected.forEach(function (r) {
  const s = r.franchise_key + '|' + r.normalised_title_key + '|' + r.start_year;
  let reason = null;
  if (fBlocked[r.franchise_key]) reason = 'NEAR_MATCH_FRANCHISE_KEY';
  else if (sig[s].length > 1) reason = 'AMBIGUOUS_SOURCE_IDENTITY';
  titles.push({ anilist_id: r.anilist_id, mal_id: r.mal_id, franchise_key: r.franchise_key, normalised_title_key: r.normalised_title_key,
    display_title: r.display_title, alt_titles: r.alt_titles, media_type: r.media_type, start_year: r.start_year, blocked: reason !== null });
  if (reason) { blocked.push({ anilist_id: r.anilist_id, reason: reason }); return; }
  const sc = r.score;
  const ready = r.popularity !== null && r.favourites !== null;
  const evidence = [
    { type: 'source_observation', source: CF_SOURCE_LABEL, retrieved_at: ctx.retrieved_at, signal_use: 'market_research_only', notice: CF_NOTICE,
      anilist_id: r.anilist_id, mal_id: r.mal_id, title: r.display_title, format: r.media_type, status: r.status,
      season: r.season, season_year: r.season_year, start_date: r.start_date, end_date: r.end_date, episodes: r.episodes,
      popularity: r.popularity, favourites: r.favourites, trending: r.trending, average_score: r.average_score, mean_score: r.mean_score },
    { type: 'lane_hits', query_set_version: cfg.query_set_version, hits: r.lanes },
    { type: 'scoring', scoring_version: sc.scoring_version, primary_lane: r.primary_lane, observation_window: cfg.window,
      inputs: sc.inputs, outputs: { demand_signal: sc.demand_signal, nostalgia_signal: sc.nostalgia_signal, editorial_potential: sc.editorial_potential,
      timeliness: sc.timeliness, trend_state: sc.trend_state }, missing_inputs: sc.missing_inputs },
  ];
  candidates.push({ anilist_id: r.anilist_id, topic_key: 'market-signal', topic_display: r.display_title + ' (' + LABEL[r.primary_lane] + ')',
    content_lane: r.primary_lane, trend_state: sc.trend_state, demand_signal: sc.demand_signal, nostalgia_signal: sc.nostalgia_signal,
    editorial_potential: sc.editorial_potential, timeliness: sc.timeliness, signal_evidence: evidence,
    ready: ready, rejection_reason: ready ? null : 'INSUFFICIENT_SIGNAL_DATA' });
});
const out = Object.assign({}, ctx);
out.selected = undefined;
out.payload = { franchises: franchises, titles: titles, candidates: candidates };
out.blocked = blocked;
out.anilist_ids = titles.map(function (t) { return t.anilist_id; });
out.candidate_ids = candidates.map(function (c) { return c.anilist_id; });
const rej = {};
ctx.rejected.forEach(function (x) { rej[x.reason] = (rej[x.reason] || 0) + 1; });
out.summary = {
  result: candidates.length > 0 ? 'COMPLETED' : 'NO_INPUT',
  agent: CF_AGENT_CODE + ' ' + CF_AGENT_VERSION, model: 'none', llm_calls: 0, paid_calls: 0, estimated_cost_usd: 0,
  observation_window: cfg.window, scoring_version: cfg.scoring_version, query_set_version: cfg.query_set_version,
  source: CF_SOURCE_LABEL, notice: CF_NOTICE,
  anilist_requests: ctx.request_count, http: ctx.http,
  records_returned: ctx.raw_record_count, records_rejected: ctx.rejected.length, rejected_by_reason: rej, unique_titles: ctx.unique_title_count,
  selected: titles.length, blocked: blocked, candidates_in_payload: candidates.length,
  candidates_ready_planned: candidates.filter(function (c) { return c.ready; }).length,
  candidates_rejected_planned: candidates.filter(function (c) { return !c.ready; }).length,
  not_selected: ctx.not_selected_count,
};
return [{ json: JSON.parse(JSON.stringify(out)) }];
