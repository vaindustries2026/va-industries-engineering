# Engine 2 — pre-CF-001 database hardening (migration 0003) — evidence

**Date:** 2026-10-07 · **Operator:** Claude Engineer-2 (human owner Viva) · **Target:** Supabase `mkeldytatorxxszjdngt` only.

## 1. Migration
| Item | Value |
|---|---|
| File | `architecture/data-contracts/migrations/0003_cf_freeze_generated_columns_and_search_path.sql` |
| sha256 | `d6aca6551153d20bda97b930510a9dc555cc69c33d9e0350cd7aa605aa0217f3` |
| Also | `.ROLLBACK.sql` `e36ef27b...94`, `.VERIFY.sql` `c06dba21...f4`, `.TESTS.sql` (local only) `cfd00527...f4` |
| Live | migration `cf_freeze_generated_columns_and_search_path`, version **20261007113241** |
| Bodies (md5 of `prosrc`) | freeze `e4b4d9c6...` -> `f957a25df6e08a74a21b6a64e5181a47`; guard `0dac745a...` unchanged; forbid `4097ad56...` unchanged; touch `c28bbd99...` unchanged |
| SQL diff | freeze: added `v_gen text[]`, a catalog query for generated columns of `TG_RELID`, and `v_old := v_old - v_gen; v_new := v_new - v_gen;`, plus `SET search_path = pg_catalog, cf`. Other three: `ALTER FUNCTION ... SET search_path = pg_catalog, cf`. Full text in the file; the freeze body diff against 0001 is exactly those lines. |

## 2. Pre-apply live check (11:32Z, no drift)
Ref `mkeldytatorxxszjdngt`, `ACTIVE_HEALTHY`, history `cf_sprint01` + `cf_runtime_human_admin_guard`, guard md5 `0dac745af135d4772111d92fd2b168c9`, other three bodies as 0001, all `proconfig` NULL, SECURITY INVOKER, owner postgres, ACL `{postgres=X/postgres}`, runtime role `LOGIN` and every elevated attribute off, no memberships, passwordless, 0 sessions, inventory 7 tables / 4 functions / 12 triggers, 0 data rows. 0001/0002 file sha256 unchanged. Advisor before: 4 WARN `function_search_path_mutable`.

## 3. Local tests (PostgreSQL 16.15 and 17.10; raw output `PRE_CF001_0003_TEST_OUTPUT.txt`)
**62 of 62 harness checks passed (31 per version).**
- **F-6 reproduced first** (A1): on 0001+0002 a dated READY title: admin and runtime `READY->RETIRED` and `BLOCKED->READY` all fail `CF_IMMUTABLE_ROW`. Generic fixture also fails on the baseline (A2). F-7 shown with a hostile schema (A3).
- **0003 tests, 60 of 60:** dated `NEW->DRAFT->READY` and `NEW->DRAFT->BLOCKED` (runtime); admin `BLOCKED->READY` and `READY->RETIRED`; runtime `BLOCKED->READY` and `READY->RETIRED` fail `CF_GOVERNANCE_DENIED` (SET ROLE, upsert, real login); `normalised_title_key`, `franchise_id`, `start_year`, `media_type` on READY and BLOCKED titles still `CF_IMMUTABLE_ROW`; generic fixtures (two generated columns not `era_decade`, a dropped column, and a table with none): status-only change succeeds, source-column change fails; function security (four search_paths, INVOKER, owner, no EXECUTE grants, no public/`$user`/pg_temp, hostile session path ignored).
- **Regression on the 0003 state:** 0001 tests 33/33, 0002 tests 43/43 (H2-51 and H2-52 updated to 0003's two deltas, nothing else edited), VERIFY 0003 15/15, VERIFY 0001 11/11, VERIFY 0002 only column 2 differs (intentional). Guard branches G3-01..08 and rollback/reapply R3-01..09 pass, including apply -> rollback -> reapply and 0003 -> 0002 -> 0001 chain rollback.

## 4. Live verification (11:35Z)
- 0003 VERIFY: **15 of 15 true** (incl. `runtime_role_passwordless`, `runtime_privileges_exact`, `no_data_rows_left_behind`).
- 0001 VERIFY re-run: 11 of 11 true. 0002 equivalent: guard body exact with HUMAN_ADMIN block, four HUMAN_ADMIN edges unchanged, only the intentional `proconfig IS NULL` expectation false.
- **Advisor (security) after: 0 findings** (before: 4 WARN). Nothing suppressed.
- Rolled-back sentinel as `postgres` on dated titles: `DRAFT>READY`, `DRAFT>BLOCKED`, admin `BLOCKED>READY`, admin `READY>RETIRED` ok; `start_year` and `media_type` changes `CF_IMMUTABLE_ROW`; the block ended in `RAISE EXCEPTION`, nothing committed.
- Runtime privilege matrix unchanged: INSERT/SELECT/UPDATE on `agent_runs`, `anime_franchises`, `anime_titles`, `research_candidates`; SELECT on `allowed_transitions`, `reviewers`, `system_flags`; USAGE on `cf`, no CREATE; no EXECUTE on any function.
- Role: attributes exact, no memberships, **passwordless**, 0 sessions. Data rows 0; kill switches enabled 0.
- Not testable live: the runtime denial (role cannot log in). Evidence is body md5 identity with the tested function.

## 5. Counters
CF workflows 0, n8n executions 0, provider calls 0, paid calls 0, publications 0, schedules 0, passwords set 0, credentials created 0, spend $0.
