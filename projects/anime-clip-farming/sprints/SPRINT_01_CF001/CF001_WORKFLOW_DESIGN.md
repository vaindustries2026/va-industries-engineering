# CF-001 Market & Trend Radar v0.1 — Workflow design

Status: BUILT, manual trigger only, INACTIVE. Operator: Claude Engineer-2. Authorised by Company Brain (Aquila), 2026-10-13T03:30Z.

## Identity
| | |
|---|---|
| n8n workflow | `CF-001 — Market & Trend Radar v0.1`, id `AJklHNEXHrtqkb0x`, versionId `121cfea5-9634-4911-91b3-b16acea54aa8` (n8n-returned, authoritative) |
| State | inactive, not published, triggerCount 0, no Schedule/Cron node, `SCHEDULES_ENABLED` = false |
| Nodes | 25 |
| DB credential | n8n credential id `e08pNFP1Th42jXyO` (Engine 2 — Clip Farming Supabase DB; the connector still lists the old display name "Postgres account"). Role `cf_n8n_runtime` via Supabase session pooler. Referenced by id only; secret never inspected |
| External source | AniList public GraphQL, no authentication. LLM / paid calls: none |

## Node map (purpose)
1. Manual Trigger: only entry point.
2. Run Config (Code): constants, observation window `YYYY-Www` (ISO week, UTC, from run timestamp), canonical run config, idempotency basis.
3. Begin Run (Postgres): `INSERT ... ON CONFLICT (idempotency_key)` into `cf.agent_runs`; hashes computed in SQL (sha256). Disposition STARTED (new run, or re-claim of a FAILED / stale RUNNING >15 min run with attempt_count+1), REPLAY (already SUCCEEDED), IN_PROGRESS.
4. Run Started? (IF): false branch goes to 24-25.
5. Build AniList Requests (Code): 4 lane queries.
6. AniList GraphQL (HTTP): batchSize 1, interval 1500 ms, timeout 20 s, retry 2 tries, neverError + fullResponse.
7. Validate Response (Code): status classes (429 with Retry-After, 401/403, 5xx, network, GraphQL errors, malformed), rate-limit headers captured.
8. Normalise Media Records (Code): identity checks, dedupe across lanes, franchise key.
9. Score Signals (Code): deterministic scoring, see the scoring doc.
10. Select Candidates (Code): lane quota, then global fill, max 8.
11. Load Franchise Keys (Postgres, read): existing franchise keys for near-match detection.
12. Resolve Identities (Code): near-match (edit distance <= 2) and title-collision blocking, candidate payload with 3-part `signal_evidence`.
13. Run Still OK? (IF): failure branch to Shape Failure.
14. Insert Franchises, 15. Insert Titles, 16. Promote Reference Rows, 17. Insert Candidates, 18. Promote Candidates (Postgres): write order franchise, title, candidate. `ON CONFLICT DO NOTHING` so expected dedupe is not an error. New rows enter at DRAFT/IDEA and are promoted by the lifecycle triggers (DETERMINISTIC transitions only).
19. Complete Run (Postgres): run SUCCEEDED, `db_verified` counts read back from the DB.
20. Return Run Summary (Code).
21. Shape Failure, 22. Mark Run Failed, 23. Raise Failure (Code, throws): structured error, run row set FAILED, no READY candidates from a failed run.
24. Load Existing Run Outputs (Postgres, read), 25. Replay Summary (Code): returns the earlier run and its candidates, zero AniList calls.

All Postgres write nodes use `continueErrorOutput` into Shape Failure, so DB failures end as a FAILED run when the run row is still reachable, never as a silent success.

## DB contract (runtime role only)
Writes only `cf.agent_runs`, `cf.anime_franchises`, `cf.anime_titles`, `cf.research_candidates`; the workflow reads only `cf.anime_franchises` and its own run/candidate rows (the permitted reads of `allowed_transitions`, `system_flags` and `reviewers` are not used). No DELETE, no DDL, no EXECUTE on cf functions, no trigger disabling, no `session_replication_role`, no HUMAN_ADMIN transition. UUIDs are persisted; AniList ids are external references only. `n8n_workflow_version_id` is left NULL (n8n does not expose it to expressions); the version is recorded here instead.

## Idempotency
Run key = sha256(`CF-001|v0.1|` canonical JSON of {agent_version, lanes, max_candidates, lane_quota, per_page, query_set_version, scoring_version, window}). Same window and config means the same run: second execution returns REPLAY with no AniList call and no writes. `dedupe_key` = sha256(anime_title_id|topic_key|content_lane|observation_window), no timestamps or random ids.

## Legal / scope wording
Every evidence element carries `signal_use: market_research_only` and the notice "Market-signal research input only. Not rights, publication, copyright or monetisation permission." No field implies authorisation. CF-001 is not a scene finder, script writer, editor, rights resolver or publisher.

## Known limits
Hand-transcribed into the SDK from tested sources (the tested JS is in `evidence/cf-001-tools/src`); fidelity is supported by the live run, replay and pin-data error tests behaving as the local tests predict (52 Node and 142 SQL tests). A byte-for-byte comparison of the n8n node code against the local source on identical live data was not performed. Credential display name in the connector is stale. See `CF001_FINAL_REPORT.md` for findings.
