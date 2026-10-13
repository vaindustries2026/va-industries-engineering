// @include common
const ctx = $input.first().json;
if (!ctx.ok || ctx.zero_input) return [{ json: ctx }];
const it = ctx.intake;
const errs = [];
function e(code, detail) { errs.push({ error_code: code, error_detail: detail }); }
const limitMs = Number.isInteger(it.episode.duration_seconds) ? it.episode.duration_seconds * 1000 : CF_MAX_MS;
const scenes = it.scenes.map(function (s, i) {
  const rawS = s.start_ms !== undefined ? s.start_ms : s.start, rawE = s.end_ms !== undefined ? s.end_ms : s.end;
  if (rawS === undefined || rawE === undefined || rawS === null || rawE === null) { e('CF002_MISSING_TIMESTAMP', 'scenes[' + i + '] needs start and end'); return null; }
  const a = parseTs(rawS), b = parseTs(rawE);
  if (a === null || b === null) { e('CF002_INVALID_TIMESTAMP', 'scenes[' + i + '] start/end must be integer milliseconds or [HH:]MM:SS[.mmm]'); return null; }
  if (s.start_ms !== undefined && s.start !== undefined && parseTs(s.start_ms) !== parseTs(s.start)) e('CF002_INVALID_TIMESTAMP', 'scenes[' + i + '] start_ms and start disagree');
  if (s.end_ms !== undefined && s.end !== undefined && parseTs(s.end_ms) !== parseTs(s.end)) e('CF002_INVALID_TIMESTAMP', 'scenes[' + i + '] end_ms and end disagree');
  if (b <= a) { e('CF002_NON_POSITIVE_SPAN', 'scenes[' + i + '] end must be after start'); return null; }
  if (b > CF_MAX_MS) { e('CF002_INVALID_TIMESTAMP', 'scenes[' + i + '] end exceeds 24 hours'); return null; }
  if (b > limitMs) { e('CF002_SCENE_BEYOND_EPISODE', 'scenes[' + i + '] ends after the stated episode duration'); return null; }
  return { ordinal: 0, start_ms: a, end_ms: b, _src: s };
});
if (errs.length === 0) {
  const ok = scenes.slice().sort(function (x, y) { return (x.start_ms - y.start_ms) || (x.end_ms - y.end_ms); });
  ok.forEach(function (s, i) { s.ordinal = i + 1; });
  for (let i = 0; i < ok.length; i++) for (let j = i + 1; j < ok.length; j++) {
    if (ok[i].start_ms === ok[j].start_ms && ok[i].end_ms === ok[j].end_ms) e('CF002_BATCH_OVERLAP', 'two scenes in one intake have identical boundaries');
    else if (overlapRatio(ok[i], ok[j]) >= 0.8) e('CF002_BATCH_OVERLAP', 'two scenes in one intake overlap by 80% or more of the shorter span; submit them one at a time for review');
  }
  if (errs.length === 0) return [{ json: Object.assign({}, ctx, { scenes_norm: ok.map(function (s) { return { ordinal: s.ordinal, start_ms: s.start_ms, end_ms: s.end_ms, start_display: fmtMs(s.start_ms), end_display: fmtMs(s.end_ms), _src: s._src }; }) }) }];
}
return [{ json: { ok: false, zero_input: false, error_code: errs[0].error_code, error_detail: errs.map(function (x) { return x.error_code + ': ' + x.error_detail; }).join(' | ').slice(0, 900), all_errors: errs, intake: it, now_iso: ctx.now_iso } }];
