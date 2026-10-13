// @include common
const cfg = $('Run Config').first().json;
if (cfg.zero_input) return [{ json: { ok: true, zero_input: true, intake: null, now_iso: cfg.now_iso } }];
const row = $input.first().json || {};
const it = cfg.intake;
function bad(code, detail) { return [{ json: { ok: false, zero_input: false, error_code: code, error_detail: detail, intake: it, now_iso: cfg.now_iso } }]; }
if (!isObj(it)) return bad('CF002_INTAKE_NOT_OBJECT', 'intake must be a JSON object');
if (it.validation_mode !== undefined) {
  // v0.1.1 validation mode: no CF-001 lineage is claimed or fabricated; the catalog rows are resolved or created later, DRAFT only.
  if (it.validation_mode !== CF_VALIDATION_MODE) return bad('CF002_BAD_VALIDATION_MODE', 'validation_mode must be ' + CF_VALIDATION_MODE);
  if (it.research_candidate_id !== undefined && it.research_candidate_id !== null) return bad('CF002_VALIDATION_MODE_CANDIDATE_FORBIDDEN', 'validation mode never carries a research_candidate_id (no CF-001 lineage is claimed)');
  if (it.anime_title_id !== undefined && it.anime_title_id !== null) return bad('CF002_VALIDATION_MODE_TITLE_ID_FORBIDDEN', 'validation mode resolves the title from catalog, not from an id');
  const ct = isObj(it.catalog) && isObj(it.catalog.title) ? it.catalog.title : {};
  return [{ json: { ok: true, zero_input: false, validation_mode: CF_VALIDATION_MODE, intake: it, now_iso: cfg.now_iso, title: { anime_title_id: null, display_title: typeof ct.display_title === 'string' ? ct.display_title : null, start_year: ct.start_year === undefined ? null : ct.start_year } } }];
}
if (it.catalog !== undefined) return bad('CF002_CATALOG_REQUIRES_VALIDATION_MODE', 'catalog is only accepted in the explicit validation mode');
if (typeof it.research_candidate_id !== 'string' || !CF_UUID.test(it.research_candidate_id)) return bad('CF002_BAD_CANDIDATE_ID', 'research_candidate_id must be a UUID');
if (typeof it.anime_title_id !== 'string' || !CF_UUID.test(it.anime_title_id)) return bad('CF002_BAD_TITLE_ID', 'anime_title_id must be a UUID');
if (!row.research_candidate_id) return bad('CF002_UNKNOWN_CANDIDATE', 'research_candidate_id does not exist');
if (row.candidate_status !== 'READY') return bad('CF002_CANDIDATE_NOT_READY', 'candidate status is ' + row.candidate_status + ', READY required');
if (!row.title_id) return bad('CF002_UNKNOWN_TITLE', 'anime_title_id does not exist');
if (row.candidate_title_id !== row.title_id) return bad('CF002_CANDIDATE_TITLE_MISMATCH', 'the candidate belongs to a different anime title');
if (row.title_status !== 'READY') return bad('CF002_TITLE_NOT_READY', 'title status is ' + row.title_status + ', READY required');
if (row.franchise_status !== 'READY') return bad('CF002_FRANCHISE_NOT_READY', 'franchise status is ' + row.franchise_status + ', READY required');
return [{ json: { ok: true, zero_input: false, intake: it, now_iso: cfg.now_iso, title: { anime_title_id: row.title_id, display_title: row.display_title, start_year: row.start_year } } }];
