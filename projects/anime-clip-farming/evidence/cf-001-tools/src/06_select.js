// @include common
// Select Candidates: one candidate per title (primary lane by fixed priority), lane quota first, then global fill, capped.
const ctx = $input.first().json;
if (!ctx.ok) return [{ json: ctx }];
const cfg = $('Run Config').first().json;
function primaryLane(r) {
  const found = r.lanes.map(function (h) { return h.lane; });
  for (const l of CF_LANE_PRIORITY) { if (found.indexOf(l) >= 0) return l; }
  return found[0];
}
function cmp(a, b) { return (b.score.editorial_potential - a.score.editorial_potential) || (a.anilist_id - b.anilist_id); }
const all = ctx.records.map(function (r) { return Object.assign({}, r, { primary_lane: primaryLane(r) }); }).sort(cmp);
const chosen = [];
const taken = {};
for (const lane of CF_LANES) {
  const inLane = all.filter(function (r) { return r.primary_lane === lane; });
  for (let i = 0; i < inLane.length && i < cfg.lane_quota && chosen.length < cfg.max_candidates; i++) { chosen.push(inLane[i]); taken[inLane[i].anilist_id] = true; }
}
for (const r of all) {
  if (chosen.length >= cfg.max_candidates) break;
  if (!taken[r.anilist_id]) { chosen.push(r); taken[r.anilist_id] = true; }
}
chosen.sort(cmp);
const out = Object.assign({}, ctx);
out.records = undefined;
out.selected = chosen;
out.not_selected_count = all.length - chosen.length;
return [{ json: JSON.parse(JSON.stringify(out)) }];
