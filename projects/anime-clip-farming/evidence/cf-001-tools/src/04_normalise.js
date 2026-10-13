// @include common
// Normalise Media Records: pure mapping from AniList media objects to CF-001 records. Missing data stays null, never invented.
const ctx = $input.first().json;
if (!ctx.ok) return [{ json: ctx }];
const byId = {};
const rejected = [];
let rawCount = 0;
function numOrNull(x) { return isNum(x) ? x : null; }
for (const ln of ctx.lanes) {
  for (let i = 0; i < ln.media.length; i++) {
    const m = ln.media[i];
    rawCount++;
    if (!m || !Number.isInteger(m.id) || m.id <= 0) { rejected.push({ lane: ln.lane, rank: i + 1, anilist_id: null, reason: 'MISSING_IDENTITY' }); continue; }
    if (CF_SUPPORTED_FORMATS.indexOf(m.format) < 0) { rejected.push({ lane: ln.lane, rank: i + 1, anilist_id: m.id, reason: 'UNSUPPORTED_FORMAT' }); continue; }
    const t = m.title || {};
    const display = [t.romaji, t.english, t.native].filter(function (s) { return typeof s === 'string' && s.trim() !== ''; })[0];
    if (!display) { rejected.push({ lane: ln.lane, rank: i + 1, anilist_id: m.id, reason: 'MISSING_TITLE' }); continue; }
    const nk = normKey(display);
    if (nk === '') { rejected.push({ lane: ln.lane, rank: i + 1, anilist_id: m.id, reason: 'UNNORMALISABLE_TITLE' }); continue; }
    const hit = { lane: ln.lane, rank: i + 1, sort: ln.sort };
    if (byId[m.id]) { byId[m.id].lanes.push(hit); continue; }
    const sd = m.startDate || {}, ed = m.endDate || {};
    let startYear = Number.isInteger(sd.year) ? sd.year : (Number.isInteger(m.seasonYear) ? m.seasonYear : null);
    if (startYear !== null && (startYear < 1917 || startYear > 2100)) startYear = null;
    const alts = [];
    [t.english, t.native, t.romaji].forEach(function (s) { if (typeof s === 'string' && s.trim() !== '' && s !== display && alts.indexOf(s) < 0) alts.push(s); });
    byId[m.id] = {
      anilist_id: m.id,
      mal_id: Number.isInteger(m.idMal) && m.idMal > 0 ? m.idMal : null,
      display_title: display,
      alt_titles: alts,
      normalised_title_key: nk,
      franchise_key: franchiseKey(nk),
      media_type: m.format,
      status: typeof m.status === 'string' ? m.status : null,
      season: typeof m.season === 'string' ? m.season : null,
      season_year: Number.isInteger(m.seasonYear) ? m.seasonYear : null,
      start_year: startYear,
      start_date: { year: numOrNull(sd.year), month: numOrNull(sd.month), day: numOrNull(sd.day) },
      end_date: { year: numOrNull(ed.year), month: numOrNull(ed.month), day: numOrNull(ed.day) },
      episodes: numOrNull(m.episodes),
      popularity: numOrNull(m.popularity),
      favourites: numOrNull(m.favourites),
      trending: numOrNull(m.trending),
      average_score: numOrNull(m.averageScore),
      mean_score: numOrNull(m.meanScore),
      lanes: [hit],
    };
  }
}
const records = Object.keys(byId).map(function (k) { return byId[k]; }).sort(function (a, b) { return a.anilist_id - b.anilist_id; });
const out = Object.assign({}, ctx);
delete out.lanes;
out.records = records;
out.rejected = rejected;
out.raw_record_count = rawCount;
out.unique_title_count = records.length;
out.zero_input = records.length === 0;
return [{ json: out }];
