# Engine 2 Changelog

Newest first. Each entry: brief ID, date, operator, branch, what changed, what was explicitly not changed, counters, stop state.

---

## 2026-10-07 — ENGINE 2 — PRE-CF001 DATABASE ACTIVATION (migrations 0001 and 0002)

- **Operator:** Claude Engineer-2 (human owner Viva). Brief: Company Brain decisions D1–D3, relayed by Aquila, 2026-10-07T10:57Z.
- **Repository / branch:** `vaindustries2026/va-industries-engineering`, `engine2/clip-farming-sprint-01-preflight`. Not merged; no PR.
- **Live changes (Supabase project `mkeldytatorxxszjdngt` only):**
  - Preflight first: ref, `ACTIVE_HEALTHY`, empty migration history, `cf` absent, guard conditions, and file sha256 `24c01ae7fca4adb7b59f24598629fb7bd9ead993609ce02c1814f48b24aca7ea` all matched the approval.
  - Applied `0001_cf_sprint01.sql` as migration `cf_sprint01`, version `20261007105903`. VERIFY 11/11 true. Security advisors: 4 WARN (`function_search_path_mutable`), finding F-7.
  - Created, tested locally and applied `0002_cf_runtime_human_admin_guard.sql` (sha256 `80d44f0420f859a2508a0d8e33e3d7318797849345a41a02840339342be0c66b`) as migration `cf_runtime_human_admin_guard`, version `20261007110907`. It replaces only `cf.guard_status_transition()`: when the edge's mode is `HUMAN_ADMIN` and `session_user` or `current_user` is `cf_n8n_runtime`, it raises `CF_GOVERNANCE_DENIED` (SQLSTATE 42501). 0002 VERIFY 11/11 true; 0001 VERIFY re-run 11/11 true.
- **Repo changes:** migration 0002 with ROLLBACK, VERIFY and local TESTS; ADR-002; `evidence/cf-0002-tools/` (generator and test harness); activation evidence and raw test output; README, DATA_MODEL, ADR-001, preflight and Sprint 1 placeholder status lines. `0001_cf_sprint01.sql` and its sha256 are unchanged.
- **Tests (local, throwaway PostgreSQL 16.15 and 17.10):** 44/44 harness checks (22 per version): F-2 reproduced on 0001 alone; the four HUMAN_ADMIN transitions denied for the runtime role (also via upsert and in a real login); every deterministic CF-001 edge still works; admin path works; the 33 Sprint 1 tests pass after 0002; 0002 guard and rollback checks; HUMAN_GATE compatibility.
- **Not changed:** the data model (14 transition rows identical, md5 `6ea6f7a4…`); the runtime role's attributes, memberships and privileges; the role is still **passwordless**; the shared Supabase project; every n8n workflow and credential; Slack; Google Cloud; everything outside `projects/anime-clip-farming/`.
- **Findings:** F-2 fixed. **F-6** (not fixed, needs a decision): `cf.freeze_after_first_status` blocks every status change on a dated `anime_titles` row after DRAFT, for every role including admins, because the generated column `era_decade` is not computed yet in `NEW` during a BEFORE trigger. F-7 (not changed): advisor `function_search_path_mutable` WARN on the four `cf` functions.
- **Counters:** migrations applied 2, committed rows 0, roles created or altered 0, passwords set 0 · CF workflows built 0, n8n workflows created/modified/published/executed 0/0/0/0, credentials created 0 · provider calls 0, paid calls 0 · purchases or plan changes 0 · publications, uploads, schedules, Slack messages 0.
- **Rollback:** undo 0002 with `0002_cf_runtime_human_admin_guard.ROLLBACK.sql` (reopens F-2); then 0001 with `0001_cf_sprint01.ROLLBACK.sql`; both need human approval and were tested locally.
- **Stop state:** STOPPED. Waiting for a human to set the `cf_n8n_runtime` password and create the n8n credential, and for decisions on F-6 and F-7. CF-001 not authorised.

---

## 2026-10-07 — ENGINE 2 — PRE-SPRINT 1 SUPABASE PROVISIONING (+ Sprint 1 migration preflight)

- **Operator:** Claude Engineer-2 (human owner Viva). Brief: Company Brain, 2026-10-07T03:24Z.
- **Repository / branch:** `vaindustries2026/va-industries-engineering`, `engine2/clip-farming-sprint-01-preflight` from the Sprint 0 commit `5190db5` (Sprint 0 branch left as it was). Not merged; no PR.
- **Live changes (Supabase only):**
  - Created project `V&A Anime Clip Farming — Engine 2`, ref `mkeldytatorxxszjdngt`, org `VA-Company-Brain` (`zjijicmhxlommwvisywp`), region `eu-north-1` (n8n runs on Azure in Gävle, Sweden), Postgres 17.11, ACTIVE_HEALTHY. Free plan, second free slot, $0. Database password: CREATED / NOT EXPOSED.
  - Created role `cf_n8n_runtime` (LOGIN NOINHERIT NOBYPASSRLS NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION), no password, no memberships, no grants.
- **Repo changes:** ADR-001 (dedicated project; runtime role and direct grants); DATA_MODEL §1 (D-DB-1 superseded by D-DB-1R, D-DB-2 revised); governance GOV-4 role name; design SQL §14 and header (role change only) and the 3 role tests; new `migrations/0001_cf_sprint01.sql` with ROLLBACK, VERIFY and local TESTS; provisioning and preflight evidence, test output and the scripts that produced them; README; pointer notes on the Sprint 0 architecture report and the Sprint 1 placeholder.
- **Not changed:** the data model (38/38 migration objects byte-identical to the Sprint 0 design); Sprint 0 discovery, gap, test-strategy reports and baseline evidence; the shared Supabase project `ziluiwrwwbayhcskeere` (only a read-only edge-log query); every n8n workflow and credential; Slack; Google Cloud; everything outside `projects/anime-clip-farming/`.
- **Stopped at brief step 7:** the n8n credential `Engine 2 — Clip Farming Supabase DB` needs human-only secret entry (no credential-creation tool; the password must not pass through Claude). Procedure in the provisioning evidence §6.
- **Preflight:** READY TO APPLY, not applied. 33/33 Sprint 0 static tests on PostgreSQL 16.15 and 17.10 (original and revised design); the migration's own 33 tests; guard, rollback and verification checks: 30/30 harness checks passed. Findings F-1…F-5 in the preflight doc (F-2, unenforced HUMAN_ADMIN edges, needs a decision).
- **Counters:** Supabase projects created 1, roles created 1, migrations applied 0, tables 0, rows 0 · shared-project writes 0 · n8n workflows created/modified/published/executed 0/0/0/0, credentials created 0 · CF agent builds 0 · provider calls 0, paid calls 0 · purchases or plan changes 0 · publications, uploads, schedules, Slack messages 0.
- **Rollback:** `drop role cf_n8n_runtime;` and pause or delete the project in the dashboard (human); delete the branch. Migration rollback (for after an apply): `migrations/0001_cf_sprint01.ROLLBACK.sql`.
- **Stop state:** STOPPED. Waiting for (1) approval to apply `0001_cf_sprint01.sql` (sha256 `24c01ae7…a7ea`) and (2) a human to set the role password and create the n8n credential. CF-001 not authorised.

---

## 2026-10-07 — BATCH A / SPRINT 0 — Engine 2 Foundation

- **Operator:** Claude Engineer-2 (human owner Viva)
- **Repository / branch:** `vaindustries2026/va-industries-engineering`, `engine2/clip-farming-sprint-00-foundation` from `main` @ `14f66e10664d6f295ef74402998e22949714098b`. Not merged; no PR opened (Company Brain reconciles first).
- **Changed:** created `projects/anime-clip-farming/` (README, blueprint copy, data model, identity contracts, DESIGN-ONLY SQL + local static tests, agent contracts, dependency map, governance gates, state model, Sprint 0 discovery / gap / test-strategy / architecture reports, baseline evidence, static test output, sprint placeholders 01–11, this changelog).
- **Not changed:** every file outside `projects/anime-clip-farming/`; all n8n workflows (including `WStqWRlqax7iocOx`); all Supabase objects; all credentials; Slack; Google Cloud.
- **Counters:** n8n workflows modified 0, published 0, executed 0 · Supabase schema changes 0, migrations applied 0, rows written 0 · provider calls 0, paid calls 0 · uploads 0, social posts 0, schedules 0 · Slack messages 0.
- **Validation:** draft SQL loaded into a throwaway local PostgreSQL 16.15 in the engineering container; 33/33 static tests passed; instance deleted.
- **Rollback:** delete the branch (`git push origin --delete engine2/clip-farming-sprint-00-foundation`). No live system needs rollback.
- **Stop state:** STOPPED before CF-001. Awaiting human / Company Brain reconciliation.
