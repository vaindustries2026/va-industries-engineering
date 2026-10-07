# Pre-Sprint 1 — Migration preflight

**Result: READY TO APPLY. Not applied.** Applying needs an explicit human / Company Brain approval that names the file and sha256 below.

| | |
|---|---|
| Migration | `architecture/data-contracts/migrations/0001_cf_sprint01.sql` |
| sha256 | `24c01ae7fca4adb7b59f24598629fb7bd9ead993609ce02c1814f48b24aca7ea` |
| Target | Supabase project `mkeldytatorxxszjdngt` ("V&A Anime Clip Farming — Engine 2", eu-north-1) only |
| Apply as | `apply_migration(project_id = "mkeldytatorxxszjdngt", name = "cf_sprint01", query = <file contents>)` |
| Companion files | `0001_cf_sprint01.ROLLBACK.sql` (`09025a94…76da`), `0001_cf_sprint01.VERIFY.sql` (read-only, `99c821d6…392e`), `0001_cf_sprint01.TESTS.sql` (local only, `dd0fbd63…2d75`) |
| Raw test output | `PRE_SPRINT_01_TEST_OUTPUT.txt` |
| Scripts that produced this evidence | `pre-sprint-01-tools/` |

## 1. Preflight checklist (brief step 9)

| # | Brief requirement | Result | Evidence |
|---|---|---|---|
| 1 | Compare the migration with the accepted Sprint 0 architecture | **Match.** 38 of 38 objects are byte-identical to the design (commit 5190db5). The only differences are listed in §2 and none changes a table, column, constraint, type, function body or trigger. | §2 |
| 2 | Verify it targets the new project | **Yes.** Section 0 of the file aborts on any database without `cf_n8n_runtime` (exact attributes, no memberships), with the YouTube Kids tables, or with an existing `cf`. Every guard condition evaluates true on `mkeldytatorxxszjdngt` today (read-only check, §3). The shared project would fail it. | §3 |
| 3 | Prove there are no cross-project references | **None.** No project ref, host, URL, foreign server, `dblink`, `postgres_fdw`, `pg_net`/`http`, extension or non-`cf` schema is referenced. The only `public.*` names are the four absence checks in the guard. | §4 |
| 4 | Rerun the existing 33 fail-closed tests locally | **33/33 pass**, on PostgreSQL 16.15 and 17.10, both on the Sprint 0 design as committed and on the revised design. The migration also passes its own 33 tests. | §5 |
| 5 | Inspect the SQL diff | **Done.** 31 SQL lines of the migration are not verbatim design lines: 25 guard lines, 4 grant lines and 2 list terminators. The design file's own SQL changes are role names only. | §2, §6 |
| 6 | Rollback and recovery documented | **Yes**, and tested: refuses the wrong database, stops if anything else depends on `cf`, removes everything cleanly, and re-apply works after it. | §7 |

The accepted data model is unchanged. Two access-model consequences of the brief are recorded explicitly (ADR-001): the dedicated project, and direct grants to the `NOINHERIT` runtime role instead of the `cf_agent` group role.

## 2. Comparison with the accepted design

The file is assembled by script (`pre-sprint-01-tools/build_sprint01.py`) from line ranges of the committed Sprint 0 design, so object bodies cannot drift by hand-editing. An independent script (`compare_s1_to_design.py`) then compares objects.

| Object group (in the migration) | Count | Versus design |
|---|---|---|
| Enum types `lifecycle_status`, `run_state`, `gate_code`, `gate_decision_value` | 4 | identical |
| Tables `reviewers`, `agent_runs`, `system_flags`, `anime_franchises`, `anime_titles`, `research_candidates`, `allowed_transitions` | 7 | identical |
| `allowed_transitions` rows (anime_franchise 5, anime_title 5, research_candidate 4) | 14 | identical |
| Functions `touch_updated_at`, `guard_status_transition`, `freeze_after_first_status`, `forbid_delete` | 4 | identical |
| Trigger sets (guard, freeze, no-delete, touch) on the 3 lifecycle tables | 3 | identical |
| Kill-switch seed rows (all `false`) | 3 | identical |
| Comments on schema and tables | 3 | identical |
| **Total** | **38** | **38 identical, 0 changed, 0 new** |

Deliberate differences from §15 of the Sprint 0 architecture report and from the design file:

| # | Difference | Why |
|---|---|---|
| D-1 | `cf.reviewers` is included although §15 did not list it | `cf.system_flags.changed_by_reviewer_id` references it, so §15's list could not load. The table stays empty in Sprint 1 and the runtime role cannot write it (test S1-ROLE-01). |
| D-2 | Section 0 target guard (25 lines, new) | Brief: verify the migration targets the new project. |
| D-3 | Grants go to `cf_n8n_runtime` directly; `cf_agent` is not created | ADR-001: a `NOINHERIT` login role does not receive a group role's grants. Same privilege set as Sprint 0 gave `cf_agent`, limited to the Sprint 1 tables. |
| D-4 | Last row of two VALUES lists ends in `;` / no comma | The lists are shorter. Row contents are identical. |

Left for later sprints (as §15 intended): 16 tables, 4 enum types, `forbid_update_delete`, `record_gate_decision`, the 3 views, 10 trigger sets plus the 5 append-only triggers, 58 transition rows, `cf_governance`.

## 3. Target verification

Read-only check on `mkeldytatorxxszjdngt`, 2026-10-07T03:52:53Z (evaluates section 0 without running it):

| Guard condition | Result |
|---|---|
| `cf_n8n_runtime` exists | true |
| Attributes are LOGIN NOINHERIT NOBYPASSRLS NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION | true |
| Member of no role | true |
| No `public.episode_scripts`, `asset_registry`, `production_plans`, `videos` | true (`public` has 0 tables) |
| Schema `cf` absent | true |
| Migrations recorded | 0 |
| Security advisors | 0 findings |

The shared project `ziluiwrwwbayhcskeere` would fail the guard twice: it has the YouTube Kids tables and has no `cf_*` role (Sprint 0 baseline evidence §3 and §8; not queried again). Local tests G-01…G-04 prove each guard branch aborts and creates nothing; G-05 proves a second apply is refused.

## 4. No cross-project references

- **Text scan** of the migration and rollback (comments excluded) for project refs, `supabase.co`, pooler hosts, URLs, `dblink`, `postgres_fdw`, foreign servers, user mappings, `CREATE EXTENSION`, `net.`, `http_*`, `vault.`, `auth.`, `storage.`, `extensions.`, `realtime.`, `graphql`, publications, subscriptions, `COPY`, `lo_import`, `pg_read*`, `SECURITY DEFINER`: no match. `public.*` appears only in the four guard absence checks. The rollback also touches `supabase_migrations.schema_migrations`, which is the same project's own migration history.
- **Catalog proof** after a local apply (tests S1-ISO-02/03/04): every foreign key in `cf` points at a `cf` table; no `cf` function names another schema or is `SECURITY DEFINER`; every column type is built-in or a `cf` type; no `cf` object depends on an extension.
- `guard_status_transition` (copied unchanged) names `cf.v_effective_gate_decisions`, which Sprint 1 does not create. That line runs only for transitions that need a gate, and Sprint 1 has none (S1-GATE-00). If a gated row were ever added without the gate objects, the trigger would fail closed.

## 5. Tests (all local, throwaway clusters; never Supabase)

Clusters: PostgreSQL 16.15 (Ubuntu package) and 17.10 (Supabase runs 17.11). The 17.10 binaries come from npm `@embedded-postgres/linux-x64@17.10.0-beta.17` (tarball sha256 `5bad4801…445b`) because the PostgreSQL apt repository is blocked by this environment's network policy. Each cluster mirrors the Supabase shape that matters: a non-superuser `postgres` with CREATEROLE owns the database; `anon`, `authenticated`, `service_role` exist; `cf_n8n_runtime` is created by `postgres` with the exact statement used live.

| Run | What | PG 16.15 | PG 17.10 |
|---|---|---|---|
| A | Sprint 0 design + the 33 static tests, exactly as committed in 5190db5 (reproduces Sprint 0) | 33/33 | 33/33 |
| B | Revised design (ADR-001 roles) + the 33 static tests, DDL applied by non-superuser `postgres` | 33/33 | 33/33 |
| C | `0001_cf_sprint01.sql` as non-superuser `postgres` in one transaction + its own 33 tests | 33/33 | 33/33 |
| V | `VERIFY.sql` returns all true; with one extra grant it returns false (not vacuous) | pass | pass |
| G-01…G-05 | Guard: role missing, role INHERIT, role in a group, Kids tables present, second apply | 5/5 | 5/5 |
| R-01…R-05 | Rollback: wrong database refused, unknown `cf` object stops it, outside dependency stops it, clean rollback with rows present, re-apply passes all tests again | 5/5 | 5/5 |

**Harness total: 30 checks, 30 passed, 0 failed.**

The 33 Sprint 1 tests cover: object inventory, isolation, the exact runtime privilege matrix, no access for `anon`/`authenticated`/`service_role`/PUBLIC, no gate objects, the CF-001 write path as `cf_n8n_runtime` (run → franchise → title → candidate → READY), the Sprint 0 tests that still apply (T-ID-01/02/03/05, T-PAID-01/02, T-PUB-01, T-RIGHTS-01, T-ROLE-03, T-APP-03), and that the runtime role cannot make reviewers, add state-machine edges, delete, truncate, create objects in `cf` or `public`, disable triggers, call `cf` functions or switch triggers off with `session_replication_role`.

## 6. SQL diff

**Migration vs design:** every SQL line that is not a verbatim design line:

```sql
-- section 0 target guard (new, 25 lines): see 0001_cf_sprint01.sql lines 39–63
  ('research_candidate', 'READY', 'RETIRED', NULL, NULL, 'DETERMINISTIC');   -- design ends this row with ','
    ('research_candidates', 'research_candidate', 'research_candidate_id', ARRAY['rejection_reason'])   -- design ends with ','
GRANT USAGE ON SCHEMA cf TO cf_n8n_runtime;
GRANT SELECT ON ALL TABLES IN SCHEMA cf TO cf_n8n_runtime;
  cf.agent_runs, cf.anime_franchises, cf.anime_titles, cf.research_candidates
  TO cf_n8n_runtime;
```

**Design file revision** (`0001_cf_backbone.DESIGN_ONLY.sql`, header and §14 only): `cf_agent` → `cf_n8n_runtime` in the four GRANT statements, and `CREATE ROLE cf_agent` replaced by a precondition that `cf_n8n_runtime` already exists. **Static tests revision:** T-ROLE-01/02/03 run as `cf_n8n_runtime`; the header shows the provisioning statement. Nothing else changed in either file.

## 7. Rollback and recovery

| Situation | Action |
|---|---|
| Apply fails | Nothing to do if it failed as a whole. If it ever stops part-way, run `0001_cf_sprint01.ROLLBACK.sql` (every drop is `IF EXISTS`). |
| Undo after a successful apply | Run `0001_cf_sprint01.ROLLBACK.sql` on `mkeldytatorxxszjdngt`, with human approval. It drops the 7 tables (with any CF-001 rows), 4 functions, 4 types, the `cf` schema and the `cf_sprint01` history row. It uses no CASCADE, so it stops if a later migration or anything outside `cf` depends on these objects. `cf_n8n_runtime` stays, with no table access. |
| Undo the provisioning too | `drop role cf_n8n_runtime;` then pause or delete the project in the dashboard (human). |
| Data recovery | The Free plan has no point-in-time recovery. Before CF-001 runs there is no data to lose; after it runs, CF-001 can regenerate research candidates from its sources. |

## 8. Findings for the Company Brain (none blocks the apply)

| # | Finding | Handling |
|---|---|---|
| F-1 | §15 of the Sprint 0 report missed that `system_flags` needs `reviewers`. | Included `reviewers` (D-1). Confirm with the approval. |
| F-2 | `HUMAN_ADMIN` transitions (franchise/title `BLOCKED → READY`, `READY → RETIRED`) are documented as human-only, but the guard trigger does not check who makes them. The runtime role can update those tables, so a faulty workflow could make them. This is in the accepted design, not new. | Unchanged here. Recommend a small follow-up migration that rejects `HUMAN_ADMIN` edges for `cf_n8n_runtime`, before any workflow writes those statuses. Needs a decision. |
| F-3 | The Sprint 0 design described a `cf_owner` role that its SQL never created. | Objects are owned by `postgres`, the applying role. Recorded in the design file and ADR-001. |
| F-4 | Supabase does not document whether `apply_migration` wraps the file in one transaction. | The file has no BEGIN/COMMIT of its own; the rollback is safe on a partial apply; `VERIFY.sql` checks the result. |
| F-5 | Local tests cannot reproduce Supabase-only pieces (supautils, Supabase event triggers). | Covered by the live read-only checks (§3, provisioning evidence §4) and `VERIFY.sql` after the apply. |

## 9. After approval (runbook)

1. Re-check, read-only: `get_project` (name, ref, eu-north-1, ACTIVE_HEALTHY), `list_migrations` (empty), §3 guard query (all true), file sha256 = `24c01ae7…a7ea`.
2. Apply with `apply_migration` exactly as in the header table.
3. Verify, read-only: `list_migrations` shows `cf_sprint01`; `0001_cf_sprint01.VERIFY.sql` returns 11 × true; `get_advisors(security)`.
4. Human: set the `cf_n8n_runtime` password and create the n8n credential (provisioning evidence §6). Its first use is a read-only connection test.
5. Record versions, results and counters in the changelog. CF-001 itself still needs its own Sprint 1 authorisation.

## 10. Sprint 0 blockers (architecture report §16), updated

| # | Sprint 0 blocker | Now |
|---|---|---|
| B-1 | Company Brain acceptance, incl. D-DB-1/2, D-STATE-1/2 | D-DB-1 replaced by ADR-001 (dedicated project). D-DB-2 revised (direct grants to `cf_n8n_runtime`). The brief refers to "the accepted Sprint 0 architecture"; D-STATE-1/2 were not confirmed separately. |
| B-2 | Authorisation to apply the Sprint 1 migration subset to the shared project | Replaced: authorise applying `0001_cf_sprint01.sql` (sha256 `24c01ae7…a7ea`) to `mkeldytatorxxszjdngt`. READY TO APPLY. |
| B-3 | A human creates the login password and the n8n credential | Role `cf_n8n_runtime` exists without a password. The human step is in the provisioning evidence §6. |
| B-4 … B-8 | CF-001 sources, no-LLM v0.1, GCP identity, blueprint label, reviewers/surface | Unchanged. |

