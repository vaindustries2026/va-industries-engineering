# CF-002 test plan and results

| Layer | Result | Evidence |
|---|---|---|
| Static node tests (stage code, parser, validators, idempotency basis, zero input) | pass | `evidence/cf-002-tools/results/static_node_tests.txt` |
| Local SQL on PostgreSQL 16 and 17 (0004 apply, VERIFY, TESTS, rollback/reapply, runtime-role privilege tests, dedupe, overlap, mismatch) | 302/302 | `results/local_sql_tests_pg16_pg17.txt` |
| Live VERIFY on the dedicated project | 25/25 | executed after apply |
| Live rolled-back negative block as `cf_n8n_runtime` (33 checks: denied DELETE/TRUNCATE, no rights column, grants, mismatches, duplicates, HUMAN_ADMIN denial) | 0 failures | n8n execution 597, workflow `TEST — CF-002 DB negative tests` (`HFdXgTMf5eQ57sQo`, inactive) |
| Pin-data workflow paths: happy, failure, zero input, replay | pass | executions 593-596 (592 failed correctly: fixture `observed_at` in the future) |
| Live zero-input run and its replay | pass | executions 598, 599 |
| Supabase advisor | 0 lints | |

All pinned scenarios used rolled-back or no live writes; the happy path touched no persistent rows. Not exercised: a live non-empty persistence (no legitimate observation), forced DB connection loss.
