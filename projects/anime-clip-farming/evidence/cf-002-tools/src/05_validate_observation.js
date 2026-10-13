// @include common
const ctx = $input.first().json;
if (!ctx.ok || ctx.zero_input) return [{ json: ctx }];
const it = ctx.intake;
const errs = [];
function e(code, detail) { errs.push({ error_code: code, error_detail: detail }); }
function keysOk(obj, allowed, where) {
  Object.keys(obj).forEach(function (k) {
    if (allowed.indexOf(k) >= 0) return;
    if (CF_FORBIDDEN_KEY.test(k)) e('CF002_PUBLICATION_ASSERTION_REJECTED', where + '.' + k + ' looks like a rights or publication assertion; CF-002 never accepts one');
    else e('CF002_UNKNOWN_FIELD', where + '.' + k + ' is not part of the intake contract');
  });
}
keysOk(it, CF_KEYS_INTAKE, 'intake');
if (ctx.validation_mode) {
  const cat = isObj(it.catalog) ? it.catalog : null;
  if (!cat) e('CF002_MISSING_CATALOG', 'validation mode needs catalog.franchise and catalog.title');
  else {
    keysOk(cat, CF_KEYS_CATALOG, 'catalog');
    const fr = isObj(cat.franchise) ? cat.franchise : null, ti = isObj(cat.title) ? cat.title : null;
    if (!fr) e('CF002_MISSING_CATALOG', 'catalog.franchise is required');
    else {
      keysOk(fr, CF_KEYS_CAT_FRANCHISE, 'catalog.franchise');
      if (typeof fr.normalised_key !== 'string' || !CF_CATKEY.test(fr.normalised_key)) e('CF002_BAD_CATALOG', 'catalog.franchise.normalised_key must be lower-case letters, digits, space or . _ : -');
      if (typeof fr.display_name !== 'string' || clean(fr.display_name) === '' || fr.display_name.length > 200) e('CF002_BAD_CATALOG', 'catalog.franchise.display_name is required (max 200)');
    }
    if (!ti) e('CF002_MISSING_CATALOG', 'catalog.title is required');
    else {
      keysOk(ti, CF_KEYS_CAT_TITLE, 'catalog.title');
      if (typeof ti.normalised_title_key !== 'string' || !CF_CATKEY.test(ti.normalised_title_key)) e('CF002_BAD_CATALOG', 'catalog.title.normalised_title_key must be lower-case letters, digits, space or . _ : -');
      if (typeof ti.display_title !== 'string' || clean(ti.display_title) === '' || ti.display_title.length > 200) e('CF002_BAD_CATALOG', 'catalog.title.display_title is required (max 200)');
      if (ti.media_type !== undefined && CF_MEDIA_TYPES.indexOf(ti.media_type) < 0) e('CF002_BAD_CATALOG', 'catalog.title.media_type must be one of ' + CF_MEDIA_TYPES.join(','));
      if (ti.start_year !== undefined && (!Number.isInteger(ti.start_year) || ti.start_year < 1917 || ti.start_year > 2100)) e('CF002_BAD_CATALOG', 'catalog.title.start_year must be a whole year 1917-2100');
    }
  }
}
const ep = isObj(it.episode) ? it.episode : null, so = isObj(it.source) ? it.source : null;
if (!ep) e('CF002_MISSING_EPISODE', 'episode object is required');
else {
  keysOk(ep, CF_KEYS_EPISODE, 'episode');
  if (!Number.isInteger(ep.season_number) || ep.season_number < 0 || ep.season_number > 99) e('CF002_UNRESOLVED_EPISODE', 'episode.season_number must be a whole number 0-99');
  if (!isNum(ep.episode_number) || ep.episode_number < 0 || ep.episode_number > 99999 || Math.round(ep.episode_number * 10) !== ep.episode_number * 10) e('CF002_UNRESOLVED_EPISODE', 'episode.episode_number must be a number >= 0 with at most one decimal');
  if (ep.episode_variant !== undefined && CF_VARIANTS.indexOf(ep.episode_variant) < 0) e('CF002_UNRESOLVED_EPISODE', 'episode.episode_variant must be one of ' + CF_VARIANTS.join(','));
  if (ep.duration_seconds !== undefined && (!Number.isInteger(ep.duration_seconds) || ep.duration_seconds <= 0)) e('CF002_UNRESOLVED_EPISODE', 'episode.duration_seconds must be a positive whole number');
}
if (!so) e('CF002_MISSING_SOURCE', 'source object is required');
else {
  keysOk(so, CF_KEYS_SOURCE, 'source');
  if (typeof so.platform !== 'string' || !/^[A-Z0-9_]{2,40}$/.test(so.platform)) e('CF002_BAD_SOURCE_PLATFORM', 'source.platform must be an upper-case token such as CRUNCHYROLL, OFFICIAL_YOUTUBE, HUMAN_RESEARCH_OBSERVATION');
  const ref = typeof so.reference === 'string' ? so.reference.trim() : '';
  if (ref === '') e('CF002_MISSING_SOURCE_REFERENCE', 'source.reference is required');
  else {
    if (ref.length > 500) e('CF002_BAD_SOURCE_REFERENCE', 'source.reference is longer than 500 characters');
    if (CF_SECRETISH.test(ref)) e('CF002_BAD_SOURCE_REFERENCE', 'source.reference contains credential-like material; store a durable reference without tokens, cookies or signatures');
    if (/^[a-z][a-z0-9+.-]*:\/\//i.test(ref)) {
      if (!/^https:\/\//i.test(ref)) e('CF002_BAD_SOURCE_REFERENCE', 'URL references must be https');
      if (/^https:\/\/[^/]*@/i.test(ref)) e('CF002_BAD_SOURCE_REFERENCE', 'URL references must not carry user info');
      if (/^https:\/\/(localhost|127\.|10\.|192\.168\.)/i.test(ref)) e('CF002_BAD_SOURCE_REFERENCE', 'URL reference points at a local address');
    } else if (!/^[a-z0-9][a-z0-9_.:\/-]{2,200}$/i.test(ref)) e('CF002_BAD_SOURCE_REFERENCE', 'non-URL references must be a plain slug such as human-observation:cf002-0001');
  }
  if (typeof so.research_access_basis !== 'string' || CF_BASES.indexOf(so.research_access_basis) < 0) e('CF002_MISSING_RESEARCH_ACCESS_BASIS', 'source.research_access_basis must be one of ' + CF_BASES.join(','));
  const at = typeof so.observed_at === 'string' ? Date.parse(so.observed_at) : NaN;
  if (!isFinite(at) || !/^\d{4}-\d{2}-\d{2}T/.test(so.observed_at)) e('CF002_MISSING_OBSERVATION_TIME', 'source.observed_at must be an ISO-8601 timestamp');
  else if (at > Date.parse(ctx.now_iso) + 300000) e('CF002_MISSING_OBSERVATION_TIME', 'source.observed_at is in the future');
  if (so.research_access_basis === 'HUMAN_VIEWED_LICENSED_PLATFORM' && clean(so.observer) === '') e('CF002_MISSING_OBSERVER', 'a human-viewed observation needs source.observer (a name or initials, not a credential)');
  if (so.observer !== undefined && (typeof so.observer !== 'string' || so.observer.length > 80)) e('CF002_BAD_OBSERVER', 'source.observer must be a string of at most 80 characters');
  if (so.notes !== undefined) {
    if (typeof so.notes !== 'string' || so.notes.length > 500) e('CF002_BAD_NOTES', 'source.notes must be a string of at most 500 characters');
    else if (CF_CLAIM_TEXT.test(so.notes)) e('CF002_PUBLICATION_ASSERTION_REJECTED', 'source.notes makes a rights or publication claim; research notes must stay neutral');
  }
}
const sc = Array.isArray(it.scenes) ? it.scenes : null;
if (!sc || sc.length === 0) e('CF002_NO_SCENES', 'scenes must be a non-empty array');
else if (sc.length > CF_MAX_SCENES) e('CF002_TOO_MANY_SCENES', 'a single intake may carry at most ' + CF_MAX_SCENES + ' scenes');
else sc.forEach(function (s, i) { if (!isObj(s)) e('CF002_BAD_SCENE', 'scenes[' + i + '] must be an object'); else keysOk(s, CF_KEYS_SCENE, 'scenes[' + i + ']'); });
if (errs.length > 0) return [{ json: { ok: false, zero_input: false, error_code: errs[0].error_code, error_detail: errs.map(function (x) { return x.error_code + ': ' + x.error_detail; }).join(' | ').slice(0, 900), all_errors: errs, intake: it, now_iso: ctx.now_iso } }];
return [{ json: ctx }];
