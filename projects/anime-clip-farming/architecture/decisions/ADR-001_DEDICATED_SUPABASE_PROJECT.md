# ADR-001 — Dedicated Supabase project for Engine 2

**Status:** ACCEPTED. Company Brain decision, 2026-10-07, made after Sprint 0. Brief: "ENGINE 2 — PRE-SPRINT 1 SUPABASE PROVISIONING".
**Recorded by:** Claude Engineer-2 (human owner Viva).
**Supersedes:** D-DB-1 in `../data-contracts/DATA_MODEL_v0.1.md` §1 ("same Supabase project, new `cf` schema") and blocker B-2 in `../../sprints/SPRINT_00_FOUNDATION/SPRINT_00_ARCHITECTURE_REPORT.md` §16. The Sprint 0 reports themselves are kept unchanged as the historical record.

## Context
Sprint 0 proposed putting Clip Farming tables in a new `cf` schema inside the existing shared Supabase project `VA-Company-Brain*` (`ziluiwrwwbayhcskeere`), next to the YouTube Kids tables. It listed a separate project as the alternative, with a cleaner blast radius but possible cost.

## Decision
**DEDICATED SUPABASE PROJECT**, instead of "shared project + `cf` schema".

| Item | Value |
|---|---|
| Project name | `V&A Anime Clip Farming — Engine 2` (the preferred name; it was accepted as given) |
| Project ref | `mkeldytatorxxszjdngt` |
| Organisation | `VA-Company-Brain` (`zjijicmhxlommwvisywp`), the existing V&A organisation, Free plan. No new organisation was created. |
| Region | `eu-north-1` (Stockholm) |
| Postgres | 17.11 (`17.11.0.003`, GA channel) |
| Database host | `db.mkeldytatorxxszjdngt.supabase.co` |

**Region reasoning.** The brief says to use the region closest to the automation runtime when that can be determined. n8n's own tools do not show where the instance runs. The shared project's edge logs do: requests with user agent `n8n` came from Microsoft Corporation (Azure), Gävle, Sweden, Cloudflare colo ARN (Stockholm), on 2026-09-28 (54 requests) and 2026-10-05 (22 requests). The closest Supabase region to Azure Sweden Central is `eu-north-1`. The Australian fallback was not needed. Evidence: `../../evidence/PRE_SPRINT_01_SUPABASE_PROVISIONING_EVIDENCE.md` §3.

## What does not change
- **Schema `cf` is kept** inside the dedicated project. Every table, type, function, trigger and view in the accepted Sprint 0 design keeps its name and definition, so the data model is unchanged. The schema also keeps CF tables out of `public`, which Supabase's Data API exposes by default. `cf` must never be added to the Data API's exposed schemas.
- **D-DB-2:** n8n reaches the database through a Postgres-node credential for a dedicated login role, not through the REST API.
- **D-DB-3:** CF workflows never use a service-role key and never reuse any YouTube Kids credential.
- The shared project `ziluiwrwwbayhcskeere` is untouched and holds no Engine 2 object.

## Runtime role (brief step 6)
`cf_n8n_runtime` is `LOGIN NOINHERIT NOBYPASSRLS NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION`. It was created by the provisioning step, before any migration, with **no password**, no memberships, no owned objects and no grants. It is not equivalent to `postgres`, `service_role` or `supabase_admin`.

**Consequence for the access model (not the data model).** Sprint 0 planned a NOLOGIN group role `cf_agent` holding the agent privileges, with the n8n login role as a member. A `NOINHERIT` login role does not receive a group role's privileges unless it runs `SET ROLE` first, which an n8n Postgres node cannot do reliably. So `cf_agent` is dropped and its exact privilege set is granted **directly** to `cf_n8n_runtime` by each migration, after the objects exist. `cf_governance` (NOLOGIN, gate function only) is unchanged. The Sprint 0 design mentioned a `cf_owner` role that its SQL never created; objects are owned by the role that applies the migration (`postgres`).

Privilege order:
1. Provisioning (done): role exists, no password, no grants.
2. Migration `0001_cf_sprint01` (applied 2026-10-07, version `20261007105903`): creates the objects, revokes everything from PUBLIC, then grants `cf_n8n_runtime` USAGE on `cf`, SELECT on the Sprint 1 tables, and INSERT/UPDATE on the four CF-001 tables only. No default privileges, so later objects get nothing until a later migration grants it.
3. Human (still pending after 0001 and 0002 were applied): sets the role password and creates the n8n credential `Engine 2 — Clip Farming Supabase DB`.

## Secrets
- The project's database password for `postgres` was generated inside the Supabase provisioning call. It was not returned to Claude and is not in any file, commit, log or message. If it is ever needed, a human resets it in the dashboard (Project Settings → Database).
- `cf_n8n_runtime` has no password yet. Setting one in SQL text would write it to the Postgres log, because this project runs with `log_statement = ddl`. So the password is set by a human, either with `psql`'s `\password cf_n8n_runtime` (which sends only a SCRAM hash) or from the dashboard, and is typed straight into the n8n credential.

## Consequences
- Engine 2 has its own blast radius: a CF migration, rollback or outage cannot touch the YouTube Kids tables.
- **Cost: $0 now.** The organisation is on the Free plan, which allows two active free projects. This project uses the second slot, so the organisation now has **no free slot left**: another active project would need a paid plan or a paused project.
- Free-plan projects can be paused for inactivity. A paused project makes CF runs fail closed (no connection) until a human restores it.
- No point-in-time recovery on the Free plan. Rollback of the schema is drop-and-reapply (`../data-contracts/migrations/0001_cf_sprint01.ROLLBACK.sql`).
- Cross-project joins with the Kids data are impossible by construction. Nothing in the Engine 2 design needs one.
