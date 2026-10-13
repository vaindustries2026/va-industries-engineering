// @include common
const ctx = $input.first().json;
if (!ctx.ok || ctx.zero_input) return [{ json: ctx }];
const errs = [];
function e(code, detail) { errs.push({ error_code: code, error_detail: detail }); }
function quotedWords(t) { let max = 0; (t.match(/["“”][^"“”]{1,2000}["“”]/g) || []).forEach(function (q) { max = Math.max(max, q.trim().split(/\s+/).length); }); return max; }
function unit(v, name, i) {
  if (v === undefined || v === null) return null;
  if (!isNum(v) || v < 0 || v > 1) { e('CF002_BAD_SIGNAL', 'scenes[' + i + '].' + name + ' must be a number from 0 to 1'); return null; }
  return r4(v);
}
function list(v, name, i, max, itemMax) {
  if (v === undefined) return [];
  if (!Array.isArray(v) || v.length > max || !v.every(function (x) { return typeof x === 'string' && clean(x) !== '' && clean(x).length <= itemMax; })) { e('CF002_BAD_LIST', 'scenes[' + i + '].' + name + ' must be an array of up to ' + max + ' short strings'); return []; }
  const seen = {}; const out = [];
  v.forEach(function (x) { const c = clean(x); if (!seen[c.toLowerCase()]) { seen[c.toLowerCase()] = true; out.push(c); } });
  return out;
}
const so = ctx.intake.source;
const scenes = ctx.scenes_norm.map(function (sn, idx) {
  const s = sn._src, i = idx;
  const summary = clean(s.scene_summary), why = clean(s.why_scene_matters);
  if (summary === '' || why === '') e('CF002_MISSING_INTELLIGENCE', 'scenes[' + i + '] needs scene_summary and why_scene_matters');
  if (summary.length > 800 || why.length > 800) e('CF002_TEXT_TOO_LONG', 'scenes[' + i + '] summary and reason are limited to 800 characters (copyright-minimal storage)');
  [s.scene_summary, s.why_scene_matters, s.scene_function, s.context_requirement].forEach(function (t) { if (typeof t === 'string' && quotedWords(t) > 25) e('CF002_VERBATIM_TEXT_LIMIT', 'scenes[' + i + '] quotes more than 25 words; write an original summary instead'); });
  if (typeof s.spoiler_level !== 'string' || CF_SPOILERS.indexOf(s.spoiler_level) < 0) e('CF002_BAD_SPOILER_LEVEL', 'scenes[' + i + '].spoiler_level must be one of ' + CF_SPOILERS.join(','));
  const strength = s.editorial_strength === undefined ? 'UNASSESSED' : s.editorial_strength;
  if (CF_STRENGTHS.indexOf(strength) < 0) e('CF002_BAD_EDITORIAL_STRENGTH', 'scenes[' + i + '].editorial_strength must be one of ' + CF_STRENGTHS.join(','));
  const fn = s.scene_function === undefined ? null : clean(s.scene_function), cr = s.context_requirement === undefined ? null : clean(s.context_requirement);
  if ((fn !== null && fn.length > 300) || (cr !== null && cr.length > 400)) e('CF002_TEXT_TOO_LONG', 'scenes[' + i + '] scene_function (300) or context_requirement (400) too long');
  if (s.timestamps_human_verified !== undefined && typeof s.timestamps_human_verified !== 'boolean') e('CF002_BAD_FLAG', 'scenes[' + i + '].timestamps_human_verified must be true or false');
  return {
    ordinal: sn.ordinal, start_ms: sn.start_ms, end_ms: sn.end_ms, start_display: sn.start_display, end_display: sn.end_display,
    characters_present: list(s.characters_present, 'characters_present', i, 30, 80),
    scene_summary: summary, scene_function: fn === '' ? null : fn, why_scene_matters: why,
    possible_editorial_angles: list(s.possible_editorial_angles, 'possible_editorial_angles', i, 8, 160),
    context_requirement: cr === '' ? null : cr, spoiler_level: s.spoiler_level,
    visual_strength: unit(s.visual_strength, 'visual_strength', i), nostalgia_signal: unit(s.nostalgia_signal, 'nostalgia_signal', i),
    editorial_strength: strength,
    research_source_platform: so.platform, research_source_reference: so.reference.trim(), research_access_basis: so.research_access_basis,
    research_access_notes: so.notes === undefined || clean(so.notes) === '' ? null : clean(so.notes),
    research_observed_at: new Date(Date.parse(so.observed_at)).toISOString(), research_observer: so.observer === undefined || clean(so.observer) === '' ? null : clean(so.observer),
    timestamps_human_verified: s.timestamps_human_verified === true,
  };
});
if (errs.length > 0) return [{ json: { ok: false, zero_input: false, error_code: errs[0].error_code, error_detail: errs.map(function (x) { return x.error_code + ': ' + x.error_detail; }).join(' | ').slice(0, 900), all_errors: errs, intake: ctx.intake, now_iso: ctx.now_iso } }];
const out = Object.assign({}, ctx, { scenes_built: scenes });
delete out.scenes_norm;
return [{ json: out }];
