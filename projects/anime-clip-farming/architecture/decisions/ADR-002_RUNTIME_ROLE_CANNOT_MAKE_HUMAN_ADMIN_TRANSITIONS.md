# ADR-002 — The n8n runtime role cannot make HUMAN_ADMIN transitions

**Status:** ACCEPTED and applied. Company Brain decisions D2 and D3, 2026-10-07 (brief "ENGINE 2 — PRE-CF001 DATABASE ACTIVATION"). Resolves finding F-2 of `../../evidence/PRE_SPRINT_01_MIGRATION_PREFLIGHT.md` §8.
**Recorded by:** Claude Engineer-2 (human owner Viva).
**Related:** [ADR-001](ADR-001_DEDICATED_SUPABASE_PROJECT.md) (dedicated project and runtime role), `../data-contracts/migrations/0002_cf_runtime_human_admin_guard.sql`.

## Context
The accepted state model has three transition modes in `cf.allowed_transitions.mode`: `DETERMINISTIC`, `HUMAN_GATE` and `HUMAN_ADMIN`. Four edges are `HUMAN_ADMIN`:

| Object | Edge |
|---|---|
| `anime_franchise` | `BLOCKED → READY` |
| `anime_franchise` | `READY → RETIRED` |
| `anime_title` | `BLOCKED → READY` |
| `anime_title` | `READY → RETIRED` |

They are documented as human-governed, but the guard trigger `cf.guard_status_transition()` (migration 0001) only checked that an edge exists. The runtime role `cf_n8n_runtime` holds UPDATE on the two tables, so a faulty or misdirected workflow could have made those transitions. Reproduced locally on 0001 alone (harness check F0): the runtime role moved a franchise `BLOCKED → READY → RETIRED`.

## Decision
- **Fix F-2 as a separate migration.** `0001_cf_sprint01.sql` keeps its approved sha256 `24c01ae7fca4adb7b59f24598629fb7bd9ead993609ce02c1814f48b24aca7ea` and its identity. The fix is `0002_cf_runtime_human_admin_guard.sql`.
- **Where the rule lives:** in the existing status-transition trigger function. When the edge's mode is `HUMAN_ADMIN` and `session_user` or `current_user` is `cf_n8n_runtime`, the function raises `CF_GOVERNANCE_DENIED` with SQLSTATE `42501`. The denial is checked after the edge is known to exist, so a non-existent edge still fails as `CF_INVALID_TRANSITION`.
- **By identity, not membership.** `postgres` holds an ADMIN-only membership on `cf_n8n_runtime` (PostgreSQL 16+ adds it when a non-superuser creates a role), so a membership test would block the human path too. Local test H2-45 pins this.
- **Why both `session_user` and `current_user`:** a real login has both equal to `cf_n8n_runtime`; a `SET ROLE` simulation changes only `current_user`. The role has no memberships, so it cannot `SET ROLE` to anything else.

## What does not change
- The runtime role's privileges (still INSERT/UPDATE on the four CF-001 tables, SELECT on all, nothing else), attributes, memberships and passwordless state. No role was added; no `BYPASSRLS`, no superuser behaviour; no fake reviewer.
- The state machine: the 14 `allowed_transitions` rows (md5 `6ea6f7a4fafee461dc64345d400b648c`), every `DETERMINISTIC` edge, the research-candidate lifecycle, immutability, no-delete, dedupe, paid-call and publication protections.
- `HUMAN_GATE` handling. Those edges depend on a persisted gate decision, so the change leaves them alone. Test H2-60 to H2-62 use test-only stand-ins to show a gated edge fails without a decision (`CF_GATE_DECISION_MISSING`) and succeeds for the runtime role once the matching decision exists, while a `HUMAN_ADMIN` edge on the same object stays denied.

## The three modes, as enforced
| Mode | Who may perform the transition |
|---|---|
| `DETERMINISTIC` | the system, including `cf_n8n_runtime`, when the edge exists |
| `HUMAN_GATE` | any identity, but only while a persisted, effective gate decision for that exact object and content hash exists (the gate objects arrive in a later migration) |
| `HUMAN_ADMIN` | a human or admin session only. `cf_n8n_runtime` fails closed |

## Rule for later migrations
Any migration that replaces `cf.guard_status_transition()` must keep the `HUMAN_ADMIN` block. `0002_cf_runtime_human_admin_guard.VERIFY.sql` compares the live function body with the tested body, and 0002's own section 0 refuses to run unless the function is exactly the 0001 version. The Sprint 0 design file (`migrations-draft/0001_cf_backbone.DESIGN_ONLY.sql`) still shows the 0001 body; it is historical design material and was not edited.

## Consequences
- The only way to make a `HUMAN_ADMIN` transition is an admin session (for example the Supabase SQL editor as `postgres`). There is no workflow-level path, by design.
- **Known limit, finding F-6 (FIXED by [ADR-003](ADR-003_FREEZE_IGNORES_GENERATED_COLUMNS_AND_PINNED_SEARCH_PATH.md) / migration 0003, 2026-10-07; text below describes the state at 0002):** `cf.freeze_after_first_status` blocks every status change on an `anime_titles` row that has a `start_year` once the row has left `DRAFT`, for every role including admins, because the stored generated column `era_decade` is not yet computed in `NEW` during a BEFORE trigger. The freeze trigger fires before the status guard, so for dated titles the runtime role is stopped with `CF_IMMUTABLE_ROW` rather than `CF_GOVERNANCE_DENIED`, and the human path for those titles is stopped too. Undated titles and franchises reach the guard and behave as designed. A fix needs its own decision and migration. Details: `../../evidence/PRE_CF001_DATABASE_ACTIVATION_EVIDENCE.md` §7.
- Rollback: `0002_cf_runtime_human_admin_guard.ROLLBACK.sql` restores the exact 0001 body, which reopens F-2. Run it only to undo a faulty 0002, with human approval.
