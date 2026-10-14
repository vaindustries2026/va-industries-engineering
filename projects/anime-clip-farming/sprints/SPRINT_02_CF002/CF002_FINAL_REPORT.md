# CF-002 Sprint 2 final report

**Final status:** `CF002_BUILD_COMPLETE_LIVE_SOURCE_PENDING` (v0.1.1 validation mode built and tested; only the official-clip timestamps are missing). Stopped before CF-003.

- **Git:** branch `engine2/clip-farming-sprint-02-cf002`, started from `e9023df`. Only `projects/anime-clip-farming/` changed. No merge, no PR.
- **Database:** migration 0004 applied (version `20261013044838`); `cf` has 10 objects, 25 transitions, 20 triggers; 0001-0003 untouched; advisor 0 lints; kill switches false. Rows: 0 episodes, 0 scenes.
- **n8n:** `CF-002 — Scene Intelligence & Provenance v0.1` `tmqsoycNV6k4iKr6`, inactive, 24 nodes; `TEST — CF-002 DB negative tests` `HFdXgTMf5eQ57sQo`, inactive. Executions 592-599.
- **Input/output:** zero-input run recorded; no scene persisted (see live smoke evidence for the exact requirement).
- **Testing:** static pass; 302/302 SQL on PG16 and 17; 33/33 live rolled-back negative checks; pin-data paths pass.
- **Economics:** LLM calls 0, provider calls 0, paid 0, cost $0.
- **Security:** runtime role only; credential secret and password never seen; no admin bypass; CF-SSL-001 unchanged; publication status UNKNOWN.
- **Design notes:** scene dedupe ignores source reference; 80% overlap is held as DRAFT not BLOCKED.
- **Rollback:** `0004 ... ROLLBACK.sql` (refuses if rows exist unless confirmed); archive the n8n workflows (human); delete the branch.

## Addendum 2026-10-13: v0.1.1 validation mode
- Workflow `tmqsoycNV6k4iKr6` now `CF-002 — Scene Intelligence & Provenance v0.1.1`, versionId `140ea945-91a1-4330-b288-3478d6dfc635`, 25 nodes, inactive. No migration. Test workflow `CbY7LN3BDrFMa6ar` (inactive). Executions 600-602.
- Decisions CF002-POLICY-SPOILER-001 and CF002-VALIDATION-POKEMON-001: see CF002_POLICY_AND_VALIDATION_DECISIONS.md.
- Tests: 48 static, 316 SQL (PG16/17), live rolled-back block fails=0, deployed code identical to tested code.
- Live data unchanged. Pending: clip duration, scene start/end, real observation time.
- Rollback: restore workflow version `ee46f03f-a945-4baa-b35b-bece0c4fa8a1` in n8n (human), or archive; repo: revert the commit.

## Addendum 2026-10-14: validation case changed
Pokémon cancelled (SUPERSEDED_BEFORE_LIVE_PERSISTENCE). New case: Digimon Adventure tri., Crunchyroll E4 Reunion Part 4, timebase CRUNCHYROLL_REUNION_PART_4, same v0.1.1 mode. Live data still 0 episodes and 0 scenes. Pending: E4 player duration, scene start/end, real observation time.
