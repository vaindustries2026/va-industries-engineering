'use strict';
// Deterministic SYNTHETIC AniList-shaped fixtures. Titles and ids are invented test data, not real catalogue records.
function m(id, romaji, o) {
  o = o || {};
  return Object.assign({ id: id, idMal: id + 100000, title: { romaji: romaji, english: null, native: null }, format: 'TV', status: 'FINISHED',
    season: 'FALL', seasonYear: 2012, startDate: { year: 2012, month: 10, day: 1 }, endDate: { year: 2013, month: 3, day: 25 }, episodes: 24,
    popularity: 200000, favourites: 20000, trending: 10, averageScore: 80, meanScore: 80 }, o);
}
const trending = [
  m(9001, 'Synthetic Alpha', { status: 'RELEASING', seasonYear: 2026, startDate: { year: 2026, month: 7, day: 5 }, endDate: { year: null, month: null, day: null }, trending: 900, popularity: 150000, favourites: 9000, averageScore: 83 }),
  m(9002, 'Synthetic Bravo Season 2', { status: 'RELEASING', seasonYear: 2026, startDate: { year: 2026, month: 7, day: 6 }, endDate: { year: null, month: null, day: null }, trending: 700, popularity: 400000, favourites: 30000, averageScore: 86 }),
  m(9003, 'Synthetic Charlie', { status: 'RELEASING', seasonYear: 2026, startDate: { year: 2026, month: 7, day: 8 }, endDate: { year: null, month: null, day: null }, trending: 400, popularity: 50000, favourites: 1000, averageScore: null, meanScore: null }),
  m(9004, 'Synthetic Delta Movie', { format: 'MOVIE', status: 'FINISHED', seasonYear: 2025, startDate: { year: 2025, month: 11, day: 1 }, endDate: { year: 2025, month: 11, day: 1 }, trending: 300, popularity: 120000, favourites: 8000, episodes: 1 }),
  { id: null, title: { romaji: 'Synthetic NoIdentity' }, format: 'TV' },
  m(9005, 'Synthetic Echo Special', { format: 'SPECIAL', trending: 100 }),
  m(9006, '合成テスト', { title: { romaji: null, english: null, native: '合成テスト' }, trending: 50 }),
];
const popular = [
  m(9101, 'Synthetic Foxtrot', { popularity: 480000, favourites: 45000, averageScore: 88, endDate: { year: 2016, month: null, day: null } }),
  m(9002, 'Synthetic Bravo Season 2', { status: 'FINISHED' }),
  m(9102, 'Synthetic Golf', { popularity: null, favourites: null, trending: null, averageScore: null, meanScore: null }),
  m(9103, 'Synthetic Hotel', { popularity: 90000, favourites: 700, averageScore: 71, startDate: { year: null, month: null, day: null }, seasonYear: null, endDate: { year: null, month: null, day: null } }),
];
const evergreen = [
  m(9101, 'Synthetic Foxtrot', {}),
  m(9201, 'Synthetic India', { popularity: 350000, favourites: 52000, averageScore: 90, startDate: { year: 2004, month: 4, day: 3 }, endDate: { year: 2005, month: 3, day: 26 } }),
  m(9202, 'Synthetic Juliet Final Season', { popularity: 300000, favourites: 40000, averageScore: 85, startDate: { year: 2019, month: 4, day: 3 }, endDate: { year: 2019, month: 9, day: 1 } }),
  m(9203, 'Synthetic Juliet', { popularity: 310000, favourites: 41000, averageScore: 86, startDate: { year: 2016, month: 4, day: 3 }, endDate: { year: 2016, month: 9, day: 1 } }),
];
const nostalgia = [
  m(9201, 'Synthetic India', { startDate: { year: 2004, month: 4, day: 3 } }),
  m(9301, 'Synthetic Kilo', { popularity: 260000, favourites: 33000, averageScore: 84, startDate: { year: 2001, month: 1, day: 6 }, endDate: { year: 2001, month: 12, day: 29 } }),
  m(9302, 'Synthetic Lima Seasons', { popularity: 100000, favourites: 6000, startDate: { year: 2008, month: 4, day: 1 }, endDate: { year: 2008, month: 9, day: 1 } }),
  m(9303, 'Synthetic Lima Season', { popularity: 90000, favourites: 5000, startDate: { year: 2008, month: 10, day: 1 }, endDate: { year: 2009, month: 3, day: 1 } }),
];
function resp(media, o) {
  o = o || {};
  return { body: o.body !== undefined ? o.body : { data: { Page: { pageInfo: { total: media.length, currentPage: 1, hasNextPage: true }, media: media } } },
    headers: Object.assign({ 'x-ratelimit-limit': '30', 'x-ratelimit-remaining': '29', 'content-type': 'application/json' }, o.headers || {}),
    statusCode: o.status || 200, statusMessage: 'OK' };
}
const lanes = ['CURRENT_TRENDING', 'POPULAR_PROVEN', 'EVERGREEN_DEMAND', 'NOSTALGIA_ELIGIBLE'];
module.exports = { good: [resp(trending), resp(popular), resp(evergreen), resp(nostalgia)], resp, lanes, data: { trending, popular, evergreen, nostalgia } };
