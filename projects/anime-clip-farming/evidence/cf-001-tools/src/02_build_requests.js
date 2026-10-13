// @include common
// Build AniList Requests: the fixed, small query set (4 requests, one per lane). No catalogue harvesting.
const cfg = $('Run Config').first().json;
const Q = 'query ($page: Int, $perPage: Int, $sort: [MediaSort], $status: MediaStatus, $startLesser: FuzzyDateInt) {\n' +
  '  Page(page: $page, perPage: $perPage) {\n' +
  '    pageInfo { total currentPage hasNextPage }\n' +
  '    media(type: ANIME, isAdult: false, format_in: [TV, MOVIE, OVA, ONA], sort: $sort, status: $status, startDate_lesser: $startLesser) {\n' +
  '      id idMal title { romaji english native } format status season seasonYear\n' +
  '      startDate { year month day } endDate { year month day } episodes\n' +
  '      popularity favourites trending averageScore meanScore\n' +
  '    }\n' +
  '  }\n}';
const nostalgiaCutoff = (cfg.window_year - 10) * 10000 + 101;
const defs = [
  { lane: 'CURRENT_TRENDING', sort: 'TRENDING_DESC', status: null, startLesser: null },
  { lane: 'POPULAR_PROVEN', sort: 'POPULARITY_DESC', status: 'FINISHED', startLesser: null },
  { lane: 'EVERGREEN_DEMAND', sort: 'FAVOURITES_DESC', status: 'FINISHED', startLesser: null },
  { lane: 'NOSTALGIA_ELIGIBLE', sort: 'POPULARITY_DESC', status: 'FINISHED', startLesser: nostalgiaCutoff },
];
return defs.map(function (d) {
  const variables = { page: 1, perPage: cfg.per_page, sort: [d.sort] };
  if (d.status) variables.status = d.status;
  if (d.startLesser) variables.startLesser = d.startLesser;
  return { json: { lane: d.lane, sort: d.sort, filters: { status: d.status, start_date_lesser: d.startLesser }, query: Q, variables: variables } };
});
