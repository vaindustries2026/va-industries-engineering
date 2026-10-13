# CF-001 Sprint 1 final report

**Final status:** SPRINT_01_CF001_COMPLETE + CF001_WORKFLOW_BUILT + ANILIST_PUBLIC_SOURCE_CONNECTED + NO_LLM_V01_CONFIRMED + DETERMINISTIC_SCORING_IMPLEMENTED + DATABASE_RUNTIME_ROLE_VALIDATED + LIVE_CF001_SMOKE_PASS + REPLAY_IDEMPOTENCY_PASS + F2_F6_F7_PROTECTIONS_PRESERVED + ZERO_PAID_CALLS + ZERO_PUBLICATIONS + ZERO_SCHEDULES + STOPPED_BEFORE_CF002

Caveats that do not change the status but must be read: the test-plan "Not independently exercised" list (403 branch, forced DB-connection failure, real 429, live FAILED-run replay); the scoring calibration finding; `CF-SSL-001`.

## n8n
- Workflow `CF-001 — Market & Trend Radar v0.1`, id `AJklHNEXHrtqkb0x`, versionId `121cfea5-9634-4911-91b3-b16acea54aa8`, INACTIVE (unpublished, no trigger other than Manual), 25 nodes (map in the design doc), personal project, no schedule.
- Credential: id `e08pNFP1Th42jXyO`, referenced by id, never read or changed.
- Executions: 582 (probe + rolled-back negative tests), 583 (AniList smoke), 584 (live run), 585 (replay), 586-591 (pin-data error paths, no live calls).
- Test workflows left inactive and unreferenced by anything: `TEST — CF-001 DB negative tests` `lNeYt1t1KmMxn5mn`, `TEST — CF-001 AniList smoke (1 request)` `g4IlvDOWWGTkrksR`. No archive or delete was done.

## AniList
Queries: 4 lane queries + 1 smoke query (see data-source doc). 5 requests total, all HTTP 200, limit 30/min, lowest remaining 25. 60 records in the run: accepted 60, rejected 0, selected 8. No token.

## Database (project mkeldytatorxxszjdngt)
Run `0c4cd0eb-94fc-4279-af84-db0baf5a9cf3`, 8 franchises, 8 titles, 8 candidates (ids and keys in the live smoke evidence). Counts 0/0/0/0 before, 1/8/8/8 after, unchanged by replay. Idempotency: second execution returned REPLAY with 0 calls and 0 writes.

## Economics
LLM calls 0. Paid calls 0. Cost $0. No model fields set. Billing, plans and spend limits untouched.

## Security
Runtime role only, proven live (`current_user = cf_n8n_runtime`). No postgres, service_role, other-project credential, or admin bypass in any write. Password never seen. No secrets in Git or workflow JSON (credential id only). F-2 (HUMAN_ADMIN guard), F-6 (generated-column freeze) and F-7 (search_path) protections re-verified live: function bodies unchanged, 53 live negative checks pass, 0 advisor lints. Kill switches all false. `SCHEDULES_ENABLED` false, no schedule exists.

## Findings and risks (for Company Brain)
1. **CF-SSL-001 (known infrastructure security debt, not an application blocker):** the n8n Postgres credential uses SSL Require with Ignore SSL Issues ON, because the connection test failed with certificate verification enabled and succeeded when bypassed. Left unchanged by instruction. Risk: the pooler certificate is not validated, so a man-in-the-middle is not excluded. Fix path: supply the Supabase CA certificate or an n8n image trust store entry, then turn the toggle off (separate authorised task).
2. **Scoring calibration:** popularity and favourites reference constants are below live maxima, so the top titles saturate at 1.0. Recommended v0.2 constants are in the scoring doc. v0.1 rows are frozen, so recalibration is a new scoring version for a later window, not an edit.
3. **Persisted smoke rows:** the 8 candidates are real v0.1 output for window 2026-W42 and are READY. They are market-research suggestions only. Per the standing rule they were not deleted (the runtime cannot delete by design). If Company Brain wants them marked as test evidence, that is a human-admin action; the schema has no test flag on these tables.
4. **No `n8n_workflow_version_id`:** left NULL because n8n does not expose it to expressions; the version is recorded here.
5. **Connector display name:** the n8n connector still shows the credential as "Postgres account".
6. **Hand transcription:** the Code nodes were transcribed from tested local sources into the SDK. Live behaviour matches, but there is no automated diff between the repo sources and the deployed nodes.

## Git
Branch `engine2/clip-farming-sprint-01-cf001` from `74f57c4`. Commits listed in the changelog entry and the handoff. Diff scope: `projects/anime-clip-farming/` only. No merge, no PR.

## Rollback
n8n: archive or delete the workflow (human action; none needed to keep the DB safe since it is inactive). DB: the 8-candidate dataset cannot be removed by the runtime role; if required, a human admin migration is the only path (not recommended; rows are READY research output and frozen). Repo: delete the branch.

## Stop condition
STOPPED before CF-002. Waiting for Company Brain reconciliation and a separate authorisation.
