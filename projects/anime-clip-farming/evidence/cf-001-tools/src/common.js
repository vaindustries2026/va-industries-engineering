// ---- CF-001 common helpers (deterministic, no network, no randomness) ----
const CF_AGENT_CODE = 'CF-001';
const CF_AGENT_VERSION = 'v0.1';
const CF_QUERYSET_VERSION = 'cf001-queryset-v0.1';
const CF_SCORING_VERSION = 'cf001-score-v0.1';
const CF_SOURCE_LABEL = 'AniList public GraphQL (https://graphql.anilist.co), no authentication';
const CF_NOTICE = 'Market-signal research input only. Not rights, publication, copyright or monetisation permission.';
const CF_LANES = ['CURRENT_TRENDING', 'POPULAR_PROVEN', 'EVERGREEN_DEMAND', 'NOSTALGIA_ELIGIBLE'];
// primary-lane priority when several lanes found the same title (first wins)
const CF_LANE_PRIORITY = ['CURRENT_TRENDING', 'NOSTALGIA_ELIGIBLE', 'EVERGREEN_DEMAND', 'POPULAR_PROVEN'];
const CF_SUPPORTED_FORMATS = ['TV', 'MOVIE', 'OVA', 'ONA'];
const CF_REF = { popularity: 500000, favourites: 50000, trending: 1000 };

function r4(x) { return Math.round(x * 10000) / 10000; }
function clamp(x, lo, hi) { return Math.min(hi, Math.max(lo, x)); }
function isNum(x) { return typeof x === 'number' && isFinite(x); }
function normLog(x, ref) { return isNum(x) && x > 0 ? Math.min(1, Math.log(1 + x) / Math.log(1 + ref)) : 0; }
function asciiFold(s) { return String(s).normalize('NFKD').replace(/[̀-ͯ]/g, ''); }
function normKey(s) { return asciiFold(s).toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim().replace(/\s+/g, ' '); }
function franchiseKey(nk) {
  let k = ' ' + nk + ' ';
  k = k.replace(/ (the )?final season( part \d+)? /g, ' ')
       .replace(/ \d+(st|nd|rd|th) (season|cour) /g, ' ')
       .replace(/ (season|part|cour) \d+ /g, ' ')
       .replace(/ (ii|iii|iv|vi|vii|viii|ix) $/g, ' ')
       .replace(/ [2-9] $/g, ' ');
  k = k.trim().replace(/\s+/g, ' ');
  return k === '' ? nk : k;
}
function isoWeekOf(d) {
  const t = new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate()));
  const dow = t.getUTCDay() || 7;
  t.setUTCDate(t.getUTCDate() + 4 - dow);
  const y = t.getUTCFullYear();
  const w = Math.ceil(((t.getTime() - Date.UTC(y, 0, 1)) / 86400000 + 1) / 7);
  return { year: y, week: w };
}
function isoWeekStart(y, w) {
  const jan4 = new Date(Date.UTC(y, 0, 4));
  const dow = jan4.getUTCDay() || 7;
  return new Date(jan4.getTime() + ((w - 1) * 7 - (dow - 1)) * 86400000);
}
function windowLabel(y, w) { return y + '-W' + (w < 10 ? '0' : '') + w; }
function canon(v) {
  if (Array.isArray(v)) return '[' + v.map(canon).join(',') + ']';
  if (v && typeof v === 'object') return '{' + Object.keys(v).sort().map(function (k) { return JSON.stringify(k) + ':' + canon(v[k]); }).join(',') + '}';
  return JSON.stringify(v);
}
function lev(a, b) {
  const m = a.length, n = b.length;
  let prev = [];
  for (let j = 0; j <= n; j++) prev.push(j);
  for (let i = 1; i <= m; i++) {
    const cur = [i];
    for (let j = 1; j <= n; j++) cur.push(Math.min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1)));
    prev = cur;
  }
  return prev[n];
}
// ---- end common ----
