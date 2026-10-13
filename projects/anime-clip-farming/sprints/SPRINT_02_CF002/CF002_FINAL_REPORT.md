# CF-002 Sprint 2 final report

**Final status:** `CF002_BUILD_COMPLETE_LIVE_SOURCE_PENDING`. Stopped before CF-003.

- **Git:** branch `engine2/clip-farming-sprint-02-cf002`, started from `e9023df`. Only `projects/anime-clip-farming/` changed. No merge, no PR.
- **Database:** migration 0004 applied (version `20261013044838`); `cf` has 10 objects, 25 transitions, 20 triggers; 0001-0003 untouched; advisor 0 lints; kill switches false. Rows: 0 episodes, 0 scenes.
- **n8n:** `CF-002 — Scene Intelligence & Provenance v0.1` `tmqsoycNV6k4iKr6`, inactive, 24 nodes; `TEST — CF-002 DB negative tests` `HFdXgTMf5eQ57sQo`, inactive. Executions 592-599.
- **Input/output:** zero-input run recorded; no scene persisted (see live smoke evidence for the exact requirement).
- **Testing:** static pass; 302/302 SQL on PG16 and 17; 33/33 live rolled-back negative checks; pin-data paths pass.
- **Economics:** LLM calls 0, provider calls 0, paid 0, cost $0.
- **Security:** runtime role only; credential secret and password never seen; no admin bypass; CF-SSL-001 unchanged; publication status UNKNOWN.
- **Design notes:** scene dedupe ignores source reference; 80% overlap is held as DRAFT not BLOCKED.
- **Rollback:** `0004 ... ROLLBACK.sql` (refuses if rows exist unless confirmed); archive the n8n workflows (human); delete the branch.
