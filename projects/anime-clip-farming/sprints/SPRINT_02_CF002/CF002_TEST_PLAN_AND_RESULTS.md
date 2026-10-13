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

## v0.1.1 results (2026-10-13)
| Layer | Result | Evidence |
|---|---|---|
| Static node tests (40 original + 8 validation-mode cases V1-V8) | 48/48 | `results/static_node_tests.txt` |
| Local SQL on PostgreSQL 16 and 17 (incl. S10 validation-mode flow with forced replay, and the validation live block) | 316/316 | `results/local_sql_tests_pg16_pg17.txt` |
| Deployed code equals tested code | 0 diffs over 21 nodes | node-by-node comparison of the live workflow against the repo sources |
| Live rolled-back validation-mode block as `cf_n8n_runtime` (bootstrap DRAFT, NULL candidate, replay, deny DELETE/TRUNCATE/candidate insert/publication column) | fails=0, 10 checks | execution 600, `TEST — CF-002 v0.1.1 validation-mode DB test` (`CbY7LN3BDrFMa6ar`, inactive); DB counts unchanged afterwards |
| Pin-data happy path (synthetic ZZ intake) | success, null candidate, lineage NOT_FROM_CF001_BATCH | execution 601 |
| Pin-data forbidden candidate in validation mode | fails closed with CF002_VALIDATION_MODE_CANDIDATE_FORBIDDEN | execution 602 |

Finding fixed during testing: data-modifying CTEs do not see their own inserts, so the first Bootstrap Catalog draft returned NULL statuses; statuses now come from the CTE RETURNING rows.
