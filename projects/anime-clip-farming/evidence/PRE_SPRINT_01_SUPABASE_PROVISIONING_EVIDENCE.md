# Pre-Sprint 1 — Supabase provisioning evidence

**Brief:** ENGINE 2 — PRE-SPRINT 1 SUPABASE PROVISIONING (Company Brain, 2026-10-07T03:24Z).
**Operator:** Claude Engineer-2 (human owner Viva). **Captured:** 2026-10-07 UTC.
**Decision record:** `../architecture/decisions/ADR-001_DEDICATED_SUPABASE_PROJECT.md`.
**Secrets:** none appear in this file. No access token, API key, password or connection string with a password was read, printed or stored.

---

## 1. Access check (brief step 1)

| Check | Result |
|---|---|
| Supabase CLI | Not installed in the engineering container (`supabase: command not found`, no `~/.supabase`, no Supabase environment variables). |
| Authenticated path used | Supabase Management API through the connected Supabase connector (the owner's account). The brief allows "the official Supabase CLI or Management API". |
| Organisations visible | 1: `VA-Company-Brain` (`zjijicmhxlommwvisywp`), plan `free`, tier `tier_free`. This is the existing V&A organisation; no new organisation was needed or created. |
| Projects before creation | 1: `VA-Company-Brain*` (`ziluiwrwwbayhcskeere`, ap-southeast-2, Postgres 17.6.1.166, ACTIVE_HEALTHY), the shared YouTube Kids project. |
| Existing Clip Farming / Engine 2 project | None. |
| Incremental billing | **$0.** Free plan allows "two active free projects" per Owner/Admin ([Billing FAQ](https://supabase.com/docs/guides/platform/billing-faq), [About billing](https://supabase.com/docs/guides/platform/billing-on-supabase)). One was in use, so the new project used the second free slot. No plan change, purchase or spend-limit change was made or needed. |

## 2. Project creation (brief steps 2–4)

Created with the Management API `create_project` call: name `V&A Anime Clip Farming — Engine 2`, organisation `zjijicmhxlommwvisywp`, region `eu-north-1`. The call takes no password from the caller and returned none.

| Field | Value |
|---|---|
| project_name | `V&A Anime Clip Farming — Engine 2` (preferred name accepted; fallback not needed) |
| project_ref | `mkeldytatorxxszjdngt` |
| organisation | `VA-Company-Brain` (`zjijicmhxlommwvisywp`) |
| region | `eu-north-1` |
| project_status | `ACTIVE_HEALTHY` (re-checked 2026-10-07T03:52Z) |
| Postgres version | 17.11 (`17.11.0.003`, engine 17, release channel GA), `aarch64` |
| Database host | `db.mkeldytatorxxszjdngt.supabase.co`, port 5432, database `postgres` |
| Creation timestamp | Created by this session at about 2026-10-07T03:31Z (session clock 03:31:28Z right after the call). The API reports `created_at = 2026-10-06T20:25:33.342666Z`, which matches the instance's own `pg_postmaster_start_time` (2026-10-06 20:28:05Z) and first storage migration (20:28:08Z): Supabase hands out pre-provisioned instances, so `created_at` is when the instance was built, not when it was assigned. |
| Database password | **CREATED / NOT EXPOSED** |

## 3. Region evidence (brief step 2, rule 1)

n8n's tools do not expose where the n8n instance runs, so the location came from the shared project's Supabase edge logs (read-only `query_logs`, aggregated by network and location; no IP addresses selected).

| Window | User agent | Network (AS org) | Location | Cloudflare colo | Requests |
|---|---|---|---|---|---|
| 2026-09-28 | `n8n` | Microsoft Corporation | Gävle, Gävleborg, SE | ARN | 54 (11:03Z–16:53Z) |
| 2026-10-05 | `n8n` | Microsoft Corporation | Gävle, Gävleborg, SE | ARN | 22 |

Gävle hosts Azure's Sweden Central region. The nearest Supabase region is `eu-north-1` (Stockholm). Chosen: `eu-north-1`. The Australian fallback in the brief was not needed.

## 4. Identity and isolation (brief step 4)

Read-only catalog queries on `mkeldytatorxxszjdngt`, 2026-10-07:

| Check | Result |
|---|---|
| Schemas | `auth, extensions, graphql, graphql_public, pgbouncer, public, realtime, storage, vault` (Supabase-managed only) |
| Tables or views in `public` / functions in `public` | 0 / 0 |
| User tables outside Supabase-managed schemas | 0 |
| Clip Farming objects (`cf` schema, CF tables) | none |
| Foreign data wrappers / servers / user mappings / foreign tables | 0 / 0 / 0 / 0 |
| `dblink` or `postgres_fdw` | not installed |
| Subscriptions / publications | 0 / `supabase_realtime` only, with 0 tables |
| Storage buckets / objects / auth users / vault secrets | 0 / 0 / 0 / 0 |
| Extensions | `pg_stat_statements`, `pgcrypto`, `plpgsql`, `supabase_vault`, `uuid-ossp` (Supabase defaults) |
| Event triggers | Supabase defaults only (`pgrst_ddl_watch`, `pgrst_drop_watch`, `issue_graphql_placeholder`, `issue_pg_cron_access`, `issue_pg_net_access`, `issue_pg_graphql_access`) |
| Global default privileges (all schemas) | none; Supabase's defaults are per schema (`public`, `storage`, `auth`, `graphql*`, `extensions`, `realtime`), so new `cf` objects get no automatic grants |
| Migrations recorded | 0 |
| Security advisors | 0 findings |

**Relationship to other V&A systems: none.** The project contains no reference to `ziluiwrwwbayhcskeere` or any other project, no foreign server, no replication link and no copied data. The shared project was not written to; the only call made against it in this task was the read-only edge-log query in §3.

## 5. Runtime role (brief step 6)

Statement run on `mkeldytatorxxszjdngt` (as `postgres`; no password anywhere in it):

```sql
create role cf_n8n_runtime with login noinherit nobypassrls nosuperuser nocreatedb nocreaterole noreplication password null;
comment on role cf_n8n_runtime is 'Engine 2 / Anime Clip Farming n8n runtime role. Password intentionally unset until a human sets it at the n8n credential step. Object grants come only from the Sprint 1 migration.';
```

Verification (read-only, immediately after):

| Check | Result |
|---|---|
| Attributes | `rolcanlogin=true`, `rolinherit=false`, `rolbypassrls=false`, `rolsuper=false`, `rolcreatedb=false`, `rolcreaterole=false`, `rolreplication=false`, no connection limit, no expiry, no per-role settings |
| Password | not set (the role cannot log in yet) |
| Member of | nothing |
| Member of `postgres` / `service_role` / `supabase_admin` / `authenticated` / `anon` / `pg_read_all_data` / `pg_write_all_data` | no / no / no / no / no / no / no |
| Members of the role | `postgres` with ADMIN only (`inherit=false`, `set=false`). PostgreSQL 16+ adds this automatically when a non-superuser `CREATEROLE` role creates a role. It lets `postgres` manage the role; it gives `cf_n8n_runtime` nothing. |
| Objects owned | 0 |
| Database privileges | CONNECT and TEMP (PostgreSQL's PUBLIC defaults); no CREATE |
| Schema privileges | USAGE on `public`, `pg_catalog`, `information_schema` (PUBLIC defaults); none on `auth`, `extensions`, `graphql`, `graphql_public`, `pgbouncer`, `realtime`, `storage`, `vault`; CREATE nowhere |
| Tables it can read or write | none |
| Sensitive functions | cannot execute `pgbouncer.get_auth`, `vault.create_secret`, `vault.update_secret` |

Why no password now: this project logs DDL (`log_statement = ddl`, `pg_stat_statements.track_utility = on`), so a password inside SQL text would land in the Postgres logs. It is set by a human (§6).

## 6. n8n credential (brief step 7) — STOPPED AT THIS STEP

- The n8n tools available to Claude can list credentials but cannot create one, and any route through Claude would put the password in a tool call. Creating it needs **human-only secret entry**.
- Checked 2026-10-07: n8n has 10 credentials, none for Engine 2 and none of type Postgres. No CF-* workflow exists. Nothing was created, and no other credential was reused or offered as a fallback.

Human procedure (non-secret values only):
1. Set the role password without writing it into SQL text: connect with `psql` as `postgres` and run `\password cf_n8n_runtime` (psql sends only a SCRAM-SHA-256 hash), or use the dashboard. Use a long random value from a password manager.
2. In n8n, create a **Postgres** credential named `Engine 2 — Clip Farming Supabase DB`:
   - Host: the **Session pooler** host shown in the project's Connect panel for `mkeldytatorxxszjdngt`. The direct host `db.mkeldytatorxxszjdngt.supabase.co` has an IPv6 address only (DNS checked 2026-10-07: AAAA record, no A record), so n8n should use the pooler.
   - Port `5432` (session mode), Database `postgres`, User `cf_n8n_runtime.mkeldytatorxxszjdngt` (pooler user format `role.projectref`), SSL `require`.
   - Password: type the value from step 1. Do not paste it into chat, Slack, Git or a workflow.
   - If n8n rejects the server certificate chain, its "Ignore SSL Issues" switch keeps the connection encrypted but stops verifying the server. That is a human choice; record it in the changelog if made.
3. Do not use this credential in any workflow until Sprint 1 is authorised. Its first use is a read-only connection test after the migration is applied.

## 7. Counters

| Counter | Value |
|---|---|
| Supabase projects created | 1 (`mkeldytatorxxszjdngt`) |
| Supabase roles created | 1 (`cf_n8n_runtime`) |
| Supabase migrations applied | 0 |
| Tables / rows written | 0 / 0 |
| Shared project (`ziluiwrwwbayhcskeere`) writes | 0 |
| n8n workflows created / modified / published / executed | 0 / 0 / 0 / 0 |
| n8n credentials created | 0 (human step pending) |
| CF agent builds (CF-000…CF-009) | 0 |
| Provider calls / paid calls | 0 / 0 |
| Purchases, plan changes, spend-limit changes | 0 |
| Publications, uploads, schedules, Slack messages | 0 |

## 8. Rollback

| What | How | Who |
|---|---|---|
| Runtime role | `drop role cf_n8n_runtime;` (it owns nothing and holds no grants before the migration) | Claude, with approval |
| Dedicated project | Pause (reversible) or delete (irreversible) in the Supabase dashboard. Deleting frees the second free-plan slot. | Human |
