# Engine 2 Changelog

Newest first. Each entry: brief ID, date, operator, branch, what changed, what was explicitly not changed, counters, stop state.

---

## 2026-10-14 — ENGINE 2 — CF-002 VALIDATION CASE CHANGE (Pokémon cancelled, Digimon tri. E4)

- **Operator:** Claude Engineer-2 (human owner Viva). Brief: Company Brain, relayed by Aquila, 2026-10-14T02:19Z.
- **Change:** docs and intake template only. Pokémon marked `SUPERSEDED_BEFORE_LIVE_PERSISTENCE`; new `CF002-VALIDATION-DIGIMON-001` and a non-runnable Digimon intake template with timebase `CRUNCHYROLL_REUNION_PART_4`.
- **Live:** no change (read-only check: no Digimon or Pokémon rows, 0 episodes, 0 scenes). n8n workflow unchanged (v0.1.1). No migration. LLM 0, paid 0.
- **Stop state:** `CF002_BUILD_COMPLETE_LIVE_SOURCE_PENDING`. Waiting for the human E4 timestamps. STOPPED before CF-003.

---

## 2026-10-13 — ENGINE 2 — CF-002 v0.1.1 VALIDATION MODE (Pokémon XYZ case approved)

- **Operator:** Claude Engineer-2 (human owner Viva). Brief: Company Brain, relayed by Aquila, 2026-10-13T09:17Z (approval of the bounded validation mechanism).
- **Live n8n:** workflow `tmqsoycNV6k4iKr6` patched in place to `v0.1.1` (versionId `140ea945-91a1-4330-b288-3478d6dfc635`, 25 nodes, inactive). New inactive `TEST — CF-002 v0.1.1 validation-mode DB test` (`CbY7LN3BDrFMa6ar`). Executions 600-602.
- **Live Supabase:** no change (no migration, no data). Rolled-back runtime-role test fails=0; counts afterwards 8/8/8 catalog and candidates, 0 episodes, 0 scenes.
- **Change:** explicit mode `CF002_VALIDATION_SOURCE_OUTSIDE_CF001_BATCH`: NULL candidate, DRAFT-only franchise and title bootstrap, lineage marker in scene notes and run evidence. Production behaviour unchanged.
- **Tests:** 48 static, 316 SQL on PG16 and 17, deployed code identical to tested code.
- **Not changed:** migrations 0001-0004, CF-001 rows, the credential, CF-SSL-001, kill switches. LLM 0, paid 0, cost $0.
- **Rollback:** restore n8n version `ee46f03f-a945-4baa-b35b-bece0c4fa8a1` (human) or archive; revert the repo commit.
- **Stop state:** `CF002_BUILD_COMPLETE_LIVE_SOURCE_PENDING`. Waiting for the official-clip duration, scene start/end and real observation time. STOPPED before CF-003.

---

## 2026-10-13 — ENGINE 2 — CF-002 LIVE VALIDATION DECISION (docs only)

- Recorded CF002-POLICY-SPOILER-001 and CF002-VALIDATION-POKEMON-001 in `sprints/SPRINT_02_CF002/CF002_POLICY_AND_VALIDATION_DECISIONS.md`. No DB, n8n or schema change. Official clip could not be observed from this environment (YouTube blocked); exact scene timestamps requested. Status stays `CF002_BUILD_COMPLETE_LIVE_SOURCE_PENDING`; stopped before CF-003.

---

## 2026-10-13 — ENGINE 2 — SPRINT 2: CF-002 SCENE INTELLIGENCE & PROVENANCE v0.1

- **Operator:** Claude Engineer-2 (human owner Viva). Brief: Company Brain, relayed by Aquila, 2026-10-13T04:31Z.
- **Branch:** `engine2/clip-farming-sprint-02-cf002` from `e9023df`. Not merged; no PR.
- **Live Supabase (`mkeldytatorxxszjdngt`):** applied migration `0004_cf002_scene_intelligence` (version `20261013044838`): 2 tables, 1 view, 1 type, 11 transitions, 8 triggers, minimal runtime grants. Advisor 0 lints. 0001-0003 untouched.
- **Live n8n:** created `CF-002 — Scene Intelligence & Provenance v0.1` (`tmqsoycNV6k4iKr6`, 24 nodes, inactive, manual only) and inactive `TEST — CF-002 DB negative tests` (`HFdXgTMf5eQ57sQo`). Executions 592-599.
- **Result:** 302/302 local SQL checks on PG16 and 17; 33 live rolled-back negative checks pass; zero-input live run and replay pass. No scene persisted: no legitimate human observation supplied.
- **Not changed:** CF-001 rows, migrations 0001-0003, the credential, CF-SSL-001, kill switches.
- **Counters:** LLM 0, paid 0, cost $0 · publications 0, schedules 0.
- **Rollback:** `0004 ... ROLLBACK.sql`; archive the n8n workflows (human); delete the branch.
- **Stop state:** `CF002_BUILD_COMPLETE_LIVE_SOURCE_PENDING`. STOPPED before CF-003.

---

## 2026-10-13 — ENGINE 2 — SPRINT 1: CF-001 MARKET & TREND RADAR v0.1

- **Operator:** Claude Engineer-2 (human owner Viva). Brief: Company Brain, relayed by Aquila, 2026-10-13T03:30Z; credential confirmation 03:48Z.
- **Branch:** `engine2/clip-farming-sprint-01-cf001` from `74f57c4`. Not merged; no PR.
- **Live n8n:** created `CF-001 — Market & Trend Radar v0.1` (`AJklHNEXHrtqkb0x`, 25 nodes, inactive, versionId `121cfea5-9634-4911-91b3-b16acea54aa8`) and two inactive TEST workflows (`lNeYt1t1KmMxn5mn`, `g4IlvDOWWGTkrksR`). Executions 582-591. Credential `e08pNFP1Th42jXyO` used by id only.
- **Live Supabase (`mkeldytatorxxszjdngt`):** runtime-role writes only: 1 agent_run, 8 franchises, 8 titles, 8 candidates (window 2026-W42, all READY). No schema, grant or flag change; migrations still 0001-0003.
- **Result:** live run SUCCEEDED (4 AniList requests, 60 records, 8 accepted), replay returned the same run with 0 calls and 0 writes, 53 live negative checks passed (rolled back), error paths 429/5xx/GraphQL/malformed/timeout/zero-input behave as specified.
- **Repo:** sprint docs, `CF-SSL-001` record, `evidence/cf-001-tools/` (sources, SQL, generated SDK code, tests, results). Nothing outside `projects/anime-clip-farming/`.
- **Not changed:** migrations 0001-0003 and their companions, Sprint 0 history, the credential, any other V&A project or workflow.
- **Counters:** LLM calls 0, paid calls 0, cost $0 · AniList requests 5 (free, public) · publications 0, schedules 0, Slack messages 0 · kill switches all false.
- **Findings:** CF-SSL-001 (SSL verification bypass, known debt); scoring reference constants below live maxima (v0.2 recommendation); 8 smoke rows persist by design.
- **Rollback:** archive the n8n workflows (human); repo: delete the branch; DB rows cannot be removed by the runtime role by design.
- **Stop state:** STOPPED before CF-002. Awaiting Company Brain reconciliation.

---

## 2026-10-07 — ENGINE 2 — PRE-CF001 DATABASE HARDENING (migration 0003: F-6 + F-7)

- **Operator:** Claude Engineer-2 (human owner Viva). Brief: Company Brain, relayed by Aquila, 2026-10-07T11:23Z.
- **Branch:** `engine2/clip-farming-sprint-01-preflight`. Not merged; no PR.
- **Live (Supabase `mkeldytatorxxszjdngt` only):** pre-apply re-check showed no drift; applied `0003_cf_freeze_generated_columns_and_search_path.sql` (sha256 `d6aca6551153d20bda97b930510a9dc555cc69c33d9e0350cd7aa605aa0217f3`) as `cf_freeze_generated_columns_and_search_path`, version `20261007113241`. VERIFY 0003 15/15, 0001 11/11, advisor 0 findings (was 4 WARN), privileges unchanged, role still passwordless, 0 data rows.
- **Change:** freeze function ignores generated columns (catalog-driven); `search_path = pg_catalog, cf` pinned on all four `cf` functions; guard body untouched (HUMAN_ADMIN block retained).
- **Repo:** migration 0003 + ROLLBACK/VERIFY/TESTS, ADR-003, hardening evidence and raw test output, `evidence/cf-0003-tools/`, README, ADR-002 note.
- **Tests:** 62/62 harness checks on PostgreSQL 16.15 and 17.10 (F-6 reproduced first; 60 new tests; 0001 33/33; 0002 43/43; rollback/reapply).
- **Not changed:** 0001/0002 files, data model, runtime role attributes/privileges, password (none), n8n, other projects.
- **Counters:** CF workflows 0, n8n executions 0, provider/paid calls 0, publications 0, schedules 0.
- **Rollback:** `0003 ... ROLLBACK.sql` (reopens F-6/F-7; remove the history row by hand); human approval needed.
- **Stop state:** STOPPED. Next: a human sets the runtime password and creates the n8n credential. CF-001 not authorised.

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
