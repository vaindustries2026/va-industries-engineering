# CF-SSL-001 — n8n Postgres credential SSL verification bypass

Classification: KNOWN INFRASTRUCTURE SECURITY DEBT. Not an application blocker. Recorded 2026-10-13.

- Credential: n8n id `e08pNFP1Th42jXyO` (Engine 2 — Clip Farming Supabase DB), role `cf_n8n_runtime`, Supabase session pooler `aws-0-eu-north-1.pooler.supabase.com:5432`, database `postgres`.
- Setting: SSL = Require, Ignore SSL Issues = ON.
- Reason: the credential connection test failed with certificate verification on and succeeded with it bypassed (reported by Aquila).
- Risk: traffic is encrypted but the server certificate is not validated, so an active man-in-the-middle on the path is not excluded. Mitigations in place: dedicated least-privilege role, no DELETE or DDL, all writes guarded by triggers, free-tier project with no other data.
- Decision: do not change during Sprint 1 (instruction). Not changed.
- Fix path (separate authorised task): provide the Supabase CA certificate to the credential (or the n8n trust store), switch to verify-full, turn Ignore SSL Issues off, re-run the connection test and the Phase B probe.
