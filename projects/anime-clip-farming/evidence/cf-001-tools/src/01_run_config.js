// @include common
// Run Config: version constants, observation window, query-set parameters, canonical input identity.
const REQUESTED_WINDOW = null;      // null = derive from the run timestamp; or 'YYYY-Www'
const MAX_CANDIDATES = 8;           // first-run cap (Sprint 1 smoke guidance 5-10)
const LANE_QUOTA = 2;               // per-lane minimum before global fill
const PER_PAGE = 15;                // AniList page size per lane query
const NOW = (typeof $now !== 'undefined' && $now && $now.toISO) ? new Date($now.toISO()) : new Date();
let wy, ww;
if (REQUESTED_WINDOW) {
  const m = /^([0-9]{4})-W([0-9]{2})$/.exec(REQUESTED_WINDOW);
  if (!m || Number(m[2]) < 1 || Number(m[2]) > 53) {
    return [{ json: { ok: false, error_code: 'CF001_BAD_WINDOW', error_detail: 'requested_window must be YYYY-Www' } }];
  }
  wy = Number(m[1]); ww = Number(m[2]);
} else {
  const w = isoWeekOf(NOW); wy = w.year; ww = w.week;
}
const windowStart = isoWeekStart(wy, ww);
const input_ids = {
  agent_version: CF_AGENT_VERSION,
  lanes: CF_LANES,
  max_candidates: MAX_CANDIDATES,
  lane_quota: LANE_QUOTA,
  per_page: PER_PAGE,
  query_set_version: CF_QUERYSET_VERSION,
  scoring_version: CF_SCORING_VERSION,
  window: windowLabel(wy, ww),
};
const config_canonical = canon(input_ids);
return [{ json: {
  ok: true,
  agent_code: CF_AGENT_CODE, agent_version: CF_AGENT_VERSION,
  scoring_version: CF_SCORING_VERSION, query_set_version: CF_QUERYSET_VERSION,
  window: windowLabel(wy, ww), window_year: wy, window_week: ww,
  window_start: windowStart.toISOString().slice(0, 10),
  max_candidates: MAX_CANDIDATES, lane_quota: LANE_QUOTA, per_page: PER_PAGE,
  input_ids, config_canonical,
  idempotency_basis: CF_AGENT_CODE + '|' + CF_AGENT_VERSION + '|' + config_canonical,
  input_state_basis: config_canonical,
  notice: CF_NOTICE,
} }];
