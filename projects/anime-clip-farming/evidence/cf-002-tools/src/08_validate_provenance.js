// @include common
const ctx = $input.first().json;
const cfg = $('Run Config').first().json;
if (!ctx.ok) return [{ json: ctx }];
if (ctx.zero_input) {
  return [{ json: { ok: true, zero_input: true, payload: null, summary: { result: 'NO_INPUT', agent: CF_AGENT_CODE + ' ' + CF_AGENT_VERSION, model: 'none', llm_calls: 0, provider_calls: 0, paid_calls: 0, estimated_cost_usd: 0, scenes_in_payload: 0, notice: CF_NOTICE, reason: 'no research observation was supplied; nothing was created' } } }];
}
const errs = [];
ctx.scenes_built.forEach(function (s, i) {
  if (!s.research_source_platform || !s.research_source_reference || !s.research_access_basis || !s.research_observed_at) errs.push('CF002_PROVENANCE_INCOMPLETE: scenes[' + i + ']');
  if (CF_SECRETISH.test(s.research_source_reference)) errs.push('CF002_BAD_SOURCE_REFERENCE: scenes[' + i + ']');
  if (!(s.end_ms > s.start_ms && s.start_ms >= 0)) errs.push('CF002_NON_POSITIVE_SPAN: scenes[' + i + ']');
  if (Object.keys(s).some(function (k) { return CF_FORBIDDEN_KEY.test(k) && k !== 'research_access_basis' && k !== 'research_access_notes'; })) errs.push('CF002_PUBLICATION_ASSERTION_REJECTED: scenes[' + i + '] carries a rights field');
});
if (errs.length > 0) return [{ json: { ok: false, zero_input: false, error_code: errs[0].split(':')[0], error_detail: errs.join(' | ').slice(0, 900), intake: ctx.intake, now_iso: ctx.now_iso } }];
const ep = ctx.intake.episode;
const episode = { season_number: ep.season_number, episode_number: ep.episode_number, episode_variant: ep.episode_variant === undefined ? 'TV' : ep.episode_variant,
  episode_title_display: ep.episode_title === undefined || clean(ep.episode_title) === '' ? null : clean(ep.episode_title), duration_seconds: ep.duration_seconds === undefined ? null : ep.duration_seconds };
const payload = { research_candidate_id: ctx.intake.research_candidate_id.toLowerCase(), anime_title_id: ctx.intake.anime_title_id.toLowerCase(), episode: episode,
  scenes: ctx.scenes_built, boundaries: ctx.scenes_built.map(function (s) { return { start_ms: s.start_ms, end_ms: s.end_ms }; }) };
const summary = { result: 'COMPLETED', agent: CF_AGENT_CODE + ' ' + CF_AGENT_VERSION, model: 'none', llm_calls: 0, provider_calls: 0, paid_calls: 0, estimated_cost_usd: 0,
  config_version: CF_CONFIG_VERSION, notice: CF_NOTICE, publication_source_status: 'UNKNOWN', research_candidate_id: payload.research_candidate_id, anime_title_id: payload.anime_title_id,
  title: ctx.title.display_title, episode: { season_number: episode.season_number, episode_number: episode.episode_number, episode_variant: episode.episode_variant },
  source: { platform: ctx.scenes_built[0].research_source_platform, reference: ctx.scenes_built[0].research_source_reference, research_access_basis: ctx.scenes_built[0].research_access_basis, observed_at: ctx.scenes_built[0].research_observed_at },
  scenes_in_payload: payload.scenes.length, scenes: payload.scenes.map(function (s) { return { ordinal: s.ordinal, start: s.start_display, end: s.end_display, start_ms: s.start_ms, end_ms: s.end_ms }; }) };
return [{ json: JSON.parse(JSON.stringify({ ok: true, zero_input: false, payload: payload, summary: summary })) }];
