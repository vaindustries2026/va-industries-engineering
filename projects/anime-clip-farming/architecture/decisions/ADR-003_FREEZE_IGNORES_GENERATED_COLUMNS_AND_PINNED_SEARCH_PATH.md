# ADR-003 — Freeze check ignores generated columns; cf functions pin search_path

**Status:** ACCEPTED and applied. Company Brain brief "PRE-CF001 DATABASE HARDENING — MIGRATION 0003", 2026-10-07T11:23Z. Resolves findings F-6 and F-7 of `../../evidence/PRE_CF001_DATABASE_ACTIVATION_EVIDENCE.md` §7.
**Recorded by:** Claude Engineer-2 (human owner Viva).
**Related:** [ADR-002](ADR-002_RUNTIME_ROLE_CANNOT_MAKE_HUMAN_ADMIN_TRANSITIONS.md), `../data-contracts/migrations/0003_cf_freeze_generated_columns_and_search_path.sql`.

## Context
- **F-6.** `cf.freeze_after_first_status()` compared `to_jsonb(OLD)` with `to_jsonb(NEW)`. The stored generated column `anime_titles.era_decade` is not computed in `NEW` during a BEFORE trigger, so every status change of a dated title (non-null `start_year`) after DRAFT failed with `CF_IMMUTABLE_ROW`, for every role. Reproduced first on the 0002 baseline (harness A1): admin and runtime, `READY -> RETIRED` and `BLOCKED -> READY`.
- **F-7.** The four `cf` functions had no `search_path` (advisor WARN `function_search_path_mutable` x4). Reproduced (harness A3): with a hostile schema first in the session path, an unpinned function resolved `cf_evil.to_jsonb`.

## Decision
- **Migration 0003, separate file.** 0001 and 0002 keep their hashes and are not edited.
- **F-6 fix is generic.** The freeze function reads the generated columns of the triggering relation from the catalog (`pg_attribute.attgenerated <> ''`, not dropped) and removes them from the OLD/NEW comparison. `era_decade` is not hard-coded. `status`, `updated_at` and the `TG_ARGV` mutable columns work as before; no content column became mutable. Source columns that feed a generated column (`start_year`, ...) are still compared, so changing them still fails with `CF_IMMUTABLE_ROW`.
- **F-7 fix.** `search_path = pg_catalog, cf` on all four functions. All names resolved, so no `public` and no `"$user"`. Still SECURITY INVOKER, owned by `postgres`, no EXECUTE grants.
- **Guard, touch and forbid are not rewritten.** They get `ALTER FUNCTION ... SET search_path`, so their bodies keep their md5 values and the ADR-002 HUMAN_ADMIN block is retained byte for byte (`0dac745a...`).

## Consequences
- A dated title now moves `NEW -> DRAFT -> READY/BLOCKED`; an admin session does `BLOCKED -> READY` and `READY -> RETIRED`; the runtime role is stopped by `CF_GOVERNANCE_DENIED` (SQLSTATE 42501), not `CF_IMMUTABLE_ROW`.
- Any future table bound to the freeze function with generated columns is covered without a change.
- The 0002 VERIFY column 2 (`proconfig IS NULL`) and the 0002 TESTS H2-51/H2-52 describe the pre-0003 state; on the 0003 state column 2 is intentionally false. `0003 ... VERIFY.sql` is the current check. The 0002 test harness check K1 (pins F-6 as broken) is historical and would now fail; use `evidence/cf-0003-tools/run_0003_tests.sh`.
- Rollback: `0003 ... ROLLBACK.sql` restores the 0001 freeze body and clears the four search_path settings (reopens F-6 and F-7); it leaves the guard untouched and does not delete the migration-history row.
