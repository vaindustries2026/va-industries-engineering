// ---- CF-002 common helpers (deterministic, no network, no randomness) ----
const CF_AGENT_CODE = 'CF-002';
const CF_AGENT_VERSION = 'v0.1.1';
const CF_CONFIG_VERSION = 'cf002-config-v0.1.1';
const CF_NOTICE = 'Scene intelligence for research only. Research access is not publication permission; publication_source_status stays UNKNOWN until the human-governed rights process (CF-005) says otherwise.';
const CF_BASES = ['HUMAN_VIEWED_LICENSED_PLATFORM', 'PUBLIC_OFFICIAL_UPLOAD', 'PUBLIC_UPLOAD_OWNER_UNVERIFIED', 'PRESS_OR_PROMO_KIT', 'SECONDARY_REFERENCE'];
const CF_VARIANTS = ['TV', 'OVA', 'MOVIE', 'SPECIAL', 'RECAP', 'DIRECTORS_CUT'];
const CF_SPOILERS = ['NONE', 'LOW', 'MEDIUM', 'HIGH'];
const CF_STRENGTHS = ['EDITORIALLY_STRONG', 'EDITORIALLY_MODERATE', 'EDITORIALLY_WEAK', 'UNASSESSED'];
const CF_MAX_SCENES = 3;
const CF_MAX_MS = 86400000;
const CF_KEYS_INTAKE = ['research_candidate_id', 'anime_title_id', 'episode', 'source', 'scenes', 'validation_mode', 'catalog'];
// v0.1.1: explicit, bounded engineering-validation mode for a source outside the CF-001 batch. Never implies CF-001 selected the title.
const CF_VALIDATION_MODE = 'CF002_VALIDATION_SOURCE_OUTSIDE_CF001_BATCH';
const CF_KEYS_CATALOG = ['franchise', 'title'];
const CF_KEYS_CAT_FRANCHISE = ['normalised_key', 'display_name'];
const CF_KEYS_CAT_TITLE = ['normalised_title_key', 'display_title', 'media_type', 'start_year'];
const CF_MEDIA_TYPES = ['TV', 'OVA', 'ONA', 'MOVIE', 'SPECIAL'];
const CF_CATKEY = /^[a-z0-9][a-z0-9 _:.\-]{0,118}$/;
const CF_KEYS_EPISODE = ['season_number', 'episode_number', 'episode_variant', 'episode_title', 'duration_seconds'];
const CF_KEYS_SOURCE = ['platform', 'reference', 'research_access_basis', 'observed_at', 'observer', 'notes'];
const CF_KEYS_SCENE = ['start_ms', 'start', 'end_ms', 'end', 'characters_present', 'scene_summary', 'scene_function', 'why_scene_matters', 'possible_editorial_angles', 'context_requirement', 'spoiler_level', 'visual_strength', 'nostalgia_signal', 'editorial_strength', 'timestamps_human_verified'];
// any key that looks like a rights / publication assertion is rejected, never ignored silently
const CF_FORBIDDEN_KEY = /(publication|rights?|licen[cs]|fair[_ ]?use|monetis|monetiz|approv|cleared|copyright|permission|permitted|safe)/i;
const CF_CLAIM_TEXT = /(approved? (for|to) (publi|use|post|upload|monet)|cleared? (for|to)|fair use|copyright[- ]safe|safe to (publish|use|post)|licen[cs]ed? (for|to)|monetis|monetiz|permission (granted|to publish)|ok to publish|publication[_ ]?(source[_ ]?)?status)/i;
const CF_SECRETISH = /(token=|session[_-]?id|cookie|auth=|authorization|passw|secret|api[_-]?key|signature=|sig=|x-amz-|expires=)/i;
const CF_UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

function r4(x) { return Math.round(x * 10000) / 10000; }
function isNum(x) { return typeof x === 'number' && isFinite(x); }
function isObj(x) { return x !== null && typeof x === 'object' && !Array.isArray(x); }
function clean(s) { return typeof s === 'string' ? s.replace(/\s+/g, ' ').trim() : ''; }
function canon(v) {
  if (Array.isArray(v)) return '[' + v.map(canon).join(',') + ']';
  if (v && typeof v === 'object') return '{' + Object.keys(v).sort().map(function (k) { return JSON.stringify(k) + ':' + canon(v[k]); }).join(',') + '}';
  return JSON.stringify(v === undefined ? null : v);
}
// canonical unit is integer milliseconds. Accepts an integer ms number, or "[HH:]MM:SS[.mmm]".
function parseTs(v) {
  if (typeof v === 'number') return Number.isInteger(v) && v >= 0 ? v : null;
  if (typeof v !== 'string') return null;
  const m = /^(?:(\d{1,2}):)?(\d{1,2}):(\d{2})(?:\.(\d{1,3}))?$/.exec(v.trim());
  if (!m) return null;
  const h = m[1] === undefined ? 0 : Number(m[1]), mi = Number(m[2]), s = Number(m[3]);
  if (s > 59 || (m[1] !== undefined && mi > 59)) return null;
  const ms = m[4] === undefined ? 0 : Number((m[4] + '00').slice(0, 3));
  return ((h * 60 + mi) * 60 + s) * 1000 + ms;
}
function fmtMs(ms) {
  const h = Math.floor(ms / 3600000), mi = Math.floor(ms / 60000) % 60, s = Math.floor(ms / 1000) % 60, r = ms % 1000;
  const p = function (n, w) { return String(n).padStart(w, '0'); };
  return p(h, 2) + ':' + p(mi, 2) + ':' + p(s, 2) + '.' + p(r, 3);
}
function overlapRatio(a, b) {
  const ov = Math.min(a.end_ms, b.end_ms) - Math.max(a.start_ms, b.start_ms);
  if (ov <= 0) return 0;
  return ov / Math.min(a.end_ms - a.start_ms, b.end_ms - b.start_ms);
}
// ---- end common ----
