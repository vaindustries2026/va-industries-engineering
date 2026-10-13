# CF-001 live smoke evidence

Run: n8n execution 584 of workflow `AJklHNEXHrtqkb0x`, 2026-10-13 04:12:02Z to 04:12:10Z, manual. Replay: execution 585.
Role: `cf_n8n_runtime` only (verified by the Phase B probe, execution 582). No admin credential used for any write. Reads for verification were done afterwards, read-only, by the engineer's own Supabase connector.

## Before and after
| | before | after run | after replay |
|---|---|---|---|
| cf.agent_runs | 0 | 1 | 1 |
| cf.anime_franchises | 0 | 8 | 8 |
| cf.anime_titles | 0 | 8 | 8 |
| cf.research_candidates | 0 | 8 | 8 |

## Run row
agent_run_id `0c4cd0eb-94fc-4279-af84-db0baf5a9cf3`; CF-001 / v0.1; SUCCEEDED; attempt_count 1; idempotency_key `953bf6e52938852c6d4a674dd952e8d00967865cf168e3ff0835f6681b4e38bb`; window 2026-W42; n8n_workflow_id `AJklHNEXHrtqkb0x`; n8n_execution_id 584; model fields NULL; paid_call_count 0; estimated_cost_usd 0; paid_authorisation_ref NULL; provider_call_count 4 (the four free AniList requests, not paid); db_verified: ready 8, rejected 0, idea_left 0, created_by_this_run 8.

## AniList
4 POST requests, all HTTP 200, 1.5 s apart: CURRENT_TRENDING (remaining 28), POPULAR_PROVEN (27), EVERGREEN_DEMAND (26), NOSTALGIA_ELIGIBLE (25); limit 30. 60 records returned, 0 rejected, 41 unique titles, 8 accepted. No token used. Plus 1 request in the Phase C smoke (execution 583). Total 5.

## Candidates (all status READY; franchise and title READY; agent_version v0.1; 3-element signal_evidence each)
| AniList id | Title | Lane | trend | demand | nostalgia | editorial | timeliness |
|---|---|---|---|---|---|---|---|
| 21 | ONE PIECE | CURRENT_TRENDING | UNKNOWN | 0.9256 | 1.0000 | 0.9415 | 0.8809 |
| 1535 | DEATH NOTE | NOSTALGIA_ELIGIBLE | EVERGREEN | 0.8602 | 1.0000 | 0.9111 | 0.1763 |
| 30 | Shin Seiki Evangelion | EVERGREEN_DEMAND | EVERGREEN | 0.8520 | 0.9936 | 0.9019 | 0.1673 |
| 20 | NARUTO | NOSTALGIA_ELIGIBLE | EVERGREEN | 0.8744 | 0.9920 | 0.9013 | 0.2042 |
| 189046 | Re:Zero kara Hajimeru Isekai Seikatsu 4th Season | CURRENT_TRENDING | STEADY | 0.8332 | 0.0000 | 0.8549 | 0.8470 |
| 20954 | Koe no Katachi | EVERGREEN_DEMAND | EVERGREEN | 0.8525 | 0.3333 | 0.7850 | 0.1640 |
| 20958 | Shingeki no Kyojin Season 2 | POPULAR_PROVEN | STEADY | 0.8358 | 0.2555 | 0.7395 | 0.1640 |
| 21459 | Boku no Hero Academia | POPULAR_PROVEN | EVERGREEN | 0.8275 | 0.3256 | 0.7380 | 0.1388 |

Candidate ids and dedupe keys (observation window 2026-W42): 
57652836-9c98-4079-9729-35d35bfdf060 `8a704210…d726`; 0d650154-2a77-4384-92d0-f9a778b8c92d `bdacffb0…b7f3c`; 46ae92bf-90e3-4307-8548-8aff4f4bf6d4 `67706f5a…e40d`; a8569739-295d-49bd-adcb-84531b7bb596 `b5838d8a…bf2a`; 8235a539-66bb-413d-8d51-eac599b10e77 `d06b63c7…810e`; 81e66bcd-be48-4da4-82ec-97110454f6e3 `432fcd32…e9e0`; 2cf48ae6-e978-48bb-93a0-53e140aac08d `2ecb9773…d0ca`; e9a3eb19-9e19-41ee-9018-2c819ec91dc5 `32bf38b7…db71b9`. Franchise keys: one piece, death note, shin seiki evangelion, naruto, re zero kara hajimeru isekai seikatsu (season marker stripped), koe no katachi, shingeki no kyojin, boku no hero academia. No franchise or title was blocked.

Every written row was inspected: statuses, lane, signal range, observation window, dedupe key uniqueness (8 of 8 distinct), run linkage (all 8 candidates carry the run id), evidence length 3.

## Observations
- Lane spread is as designed (2 trending, 2 nostalgia, 2 evergreen, 2 popular).
- "NOSTALGIA_ELIGIBLE" and "EVERGREEN_DEMAND" overlap heavily on very old, very popular titles (see calibration note in the scoring doc).
- Death Note and Naruto were assigned the nostalgia lane by the primary-lane priority rule (nostalgia ranks above popular); their lane hits are listed in each row's evidence.

## Replay (execution 585)
Disposition REPLAY, result `REPLAY_EXISTING_RUN`, the same run id and the same 8 candidate ids and dedupe keys returned, `provider_calls_this_execution` 0, paid 0. Table counts unchanged (see above).

## Post-run security state (read-only)
Kill switches PAID_CALLS_ENABLED / PUBLISH_ENABLED / SCHEDULES_ENABLED all false; function md5 prefixes guard `0dac745a`, freeze `f957a25d`, forbid_delete `4097ad56`, touch `c28bbd99` unchanged, all with `search_path=pg_catalog, cf`; 0 disabled triggers; 0 DELETE/TRUNCATE grants for the runtime role; 0 non-owner EXECUTE on cf functions; Supabase security advisors: 0 lints; runs with paid calls or cost: 0.
