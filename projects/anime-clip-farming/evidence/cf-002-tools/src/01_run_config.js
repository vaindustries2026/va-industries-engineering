// @include common
// Human-assisted intake (v0.1). Paste the structured research observation below, or pin it on the trigger as { intake: {...} }.
// null = no input: the run finishes cleanly with nothing created.
const DEFAULT_INTAKE = null;
const trig = $input.first().json || {};
const intake = trig.intake !== undefined ? trig.intake : DEFAULT_INTAKE;
const NOW = (typeof $now !== 'undefined' && $now && $now.toISO) ? $now.toISO() : new Date().toISOString();
if (intake === null || intake === undefined) {
  const basis = CF_AGENT_CODE + '|' + CF_AGENT_VERSION + '|NO_INPUT';
  return [{ json: { ok: true, zero_input: true, intake: null, now_iso: NOW, agent_code: CF_AGENT_CODE, agent_version: CF_AGENT_VERSION,
    input_ids: { agent_version: CF_AGENT_VERSION, config_version: CF_CONFIG_VERSION, input: 'NONE' }, idempotency_basis: basis, input_state_basis: basis, notice: CF_NOTICE } }];
}
const src = isObj(intake) ? intake : {};
const ep = isObj(src.episode) ? src.episode : {};
const so = isObj(src.source) ? src.source : {};
const sc = Array.isArray(src.scenes) ? src.scenes : [];
function ms(v) { const x = parseTs(v); return x === null ? null : x; }
// identity of the logical input: candidate, title, episode locator, source reference, scene boundaries (never summaries, notes or times)
const boundaries = sc.map(function (s) {
  const o = isObj(s) ? s : {};
  return [ms(o.start_ms !== undefined ? o.start_ms : o.start), ms(o.end_ms !== undefined ? o.end_ms : o.end)];
}).sort(function (a, b) { return ((a[0] === null ? -1 : a[0]) - (b[0] === null ? -1 : b[0])) || ((a[1] === null ? -1 : a[1]) - (b[1] === null ? -1 : b[1])); });
const input_ids = {
  agent_version: CF_AGENT_VERSION, config_version: CF_CONFIG_VERSION,
  research_candidate_id: typeof src.research_candidate_id === 'string' ? src.research_candidate_id.toLowerCase() : null,
  anime_title_id: typeof src.anime_title_id === 'string' ? src.anime_title_id.toLowerCase() : null,
  episode: { season_number: ep.season_number === undefined ? null : ep.season_number, episode_number: ep.episode_number === undefined ? null : ep.episode_number, episode_variant: ep.episode_variant === undefined ? 'TV' : ep.episode_variant },
  source: { platform: so.platform === undefined ? null : so.platform, reference: so.reference === undefined ? null : so.reference },
  scene_boundaries_ms: boundaries,
};
const idem = CF_AGENT_CODE + '|' + CF_AGENT_VERSION + '|' + canon(input_ids);
return [{ json: { ok: true, zero_input: false, intake: intake, now_iso: NOW, agent_code: CF_AGENT_CODE, agent_version: CF_AGENT_VERSION,
  input_ids: input_ids, idempotency_basis: idem, input_state_basis: canon({ config_version: CF_CONFIG_VERSION, intake: intake }), notice: CF_NOTICE } }];
