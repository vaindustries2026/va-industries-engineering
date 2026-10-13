# CF-001 data source and scoring, v0.1

Sprint 1 implementation decisions. No pre-existing lane vocabulary or formulas were found in the repository, so these are decided here and are versioned (`cf001-queryset-v0.1`, `cf001-score-v0.1`). A change to any constant needs a new version.

## Source
AniList public GraphQL, `https://graphql.anilist.co`, POST, no token, no OAuth. Research / market-signal source only; it grants no rights, licence or publication permission. Other sources (Trends, MAL, Kitsu, streaming charts) are FUTURE_RECOMMENDATIONS only and are not called.

Observed live (2026-10-13): HTTP 200; headers `x-ratelimit-limit: 30`, `x-ratelimit-remaining` decreasing by one per request (29 on the smoke call; 28, 27, 26, 25 across the four production requests). No `retry-after` seen (only present on 429). Budget: 4 requests per run (target <= 10), sequential, 1500 ms apart, 20 s timeout, one retry. 429 or 5xx fails the run closed (no loop, no harvesting; one page of 15 per lane).

## Queries (4, `isAdult:false`, `type:ANIME`, formats TV/MOVIE/OVA/ONA, page 1, perPage 15)
| Lane | Sort | Extra filter |
|---|---|---|
| CURRENT_TRENDING | TRENDING_DESC | none |
| POPULAR_PROVEN | POPULARITY_DESC | status FINISHED |
| EVERGREEN_DEMAND | FAVOURITES_DESC | status FINISHED |
| NOSTALGIA_ELIGIBLE | POPULARITY_DESC | status FINISHED, startDate < (windowYear-10)-01-01 |

Fields requested: id, idMal, title (romaji/english/native), format, status, season, seasonYear, startDate, endDate, episodes, popularity, favourites, trending, averageScore, meanScore.
Primary lane when a title appears in several: CURRENT_TRENDING > NOSTALGIA_ELIGIBLE > EVERGREEN_DEMAND > POPULAR_PROVEN (all hits kept in the evidence).

## Observation window
`YYYY-Www`, ISO week of the run timestamp in UTC. The Monday of that week (window start) drives all time arithmetic, so a replay in the same window scores identically.

## Scoring (all values rounded to 4 decimals, range 0.0000 to 1.0000)
- norm(x, ref) = min(1, ln(1+x) / ln(1+ref)); 0 if x missing or <= 0. Refs: popularity 500000, favourites 50000, trending 1000. nP, nF, nT are the normalised values.
- demand_signal = 0.55 nP + 0.25 nT + 0.20 nF
- age = windowYear - startYear; nostalgia_signal = clamp((age-5)/15, 0, 1) x (0.5 nF + 0.5 nP); NULL if the start year is unknown.
- timeliness = min(1, base + 0.4 nT); base: RELEASING 0.6; NOT_YET_RELEASED 0.3; FINISHED 0.6 x max(0, 1 - monthsSinceEnd/36) (missing end month defaults to 6 and is flagged; missing end year gives base 0 and is flagged).
- editorial_potential = 0.35 demand + 0.25 (averageScore/100) + 0.20 max(nostalgia, timeliness) + 0.20 nF
- trend_state: EVERGREEN if FINISHED, age >= 10 and nF >= 0.6; STEADY if FINISHED and nP >= 0.5; otherwise UNKNOWN. There are no rising/falling states because v0.1 holds no history.

Selection: up to 2 per lane by editorial_potential (desc, then AniList id asc), then global fill to a maximum of 8.

## Candidate shape
`topic_key = market-signal`; `topic_display = <title> (<lane label>)`. READY when popularity and favourites are both present, otherwise REJECTED with `INSUFFICIENT_SIGNAL_DATA`. `signal_evidence` (never empty) has three elements: `source_observation` (raw AniList values, retrieval time, notice), `lane_hits`, `scoring` (version, every input, outputs, `missing_inputs`). Missing data is listed, never invented.

## Calibration finding (not changed this sprint)
Live values exceed two reference constants: popularity reaches about 1.07 million (ref 500000) and favourites about 91 thousand (ref 50000). The top few titles therefore saturate at 1.0 for nP / nF, which reduces separation among the most popular titles (ties broken by editorial score parts and id). Recommended for `cf001-score-v0.2`: popularity ref 1,000,000, favourites ref 100,000, trending ref to be set from a multi-day sample. Not changed in v0.1 because the 8 smoke candidates are already persisted under v0.1 and rows are frozen after READY.
