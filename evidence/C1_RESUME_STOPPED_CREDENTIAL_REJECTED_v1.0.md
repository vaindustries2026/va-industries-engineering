# C1 Resume — Stopped Before Write (Supabase credential rejected)

**Date:** 2026-10-05 (UTC)
**Actor:** Claude Code (bounded engineering operator)
**Requested by:** Gilang / Company Brain
**Spec:** `evidence/C1_EVIDENCE_GAP_REPAIR_AND_IMPLEMENTATION_SPEC_v1.0.md`
**Result:** `STOPPED_PRE_WRITE: SUPABASE_CREDENTIAL_REJECTED`. Zero writes.

## 1. Preconditions

| Check | Result |
|---|---|
| Required reading (CLAUDE.md, C1 spec, changelog, VA_01, VA_03) | done |
| `main` contains `3a7bbb5` and `57ab83c` | yes (`origin/main` = `57ab83c`) |
| Local canon bytes (`canon/c1/`) | 4/4 match spec SHA-256 and byte counts |

## 2. Credential check (BLOCKER)

The environment routes `ziluiwrwwbayhcskeere.supabase.co` through the agent proxy with `SUPABASE_SERVICE_ROLE_KEY` injection. The key is not visible to the session and was not printed, logged or committed.

| Probe (read-only) | Response |
|---|---|
| `GET /storage/v1/bucket` | `400 {"statusCode":"403","error":"Unauthorized","message":"Invalid Compact JWS"}` |
| `GET /storage/v1/bucket/production-assets` | same |
| `POST /storage/v1/object/list/production-assets` | same |
| `GET /rest/v1/asset_registry?limit=1` | `401 "No API key found in request"` |

Interpretation: the proxy sets a bearer value in `Authorization` that Storage does not accept as a JWT, and it sets no `apikey` header. This matches a new-format `sb_secret_…` key (accepted only in the `apikey` header) or a wrong value. In either case the credential cannot list, upload to or read back from `production-assets`. Spec 4.1 requires a no-overwrite upload and a SHA-256 readback before any registry insert, so neither storage nor registry writes were attempted.

Further probing of the injection mechanism was stopped deliberately. No workaround was used: no SQL inserts into `storage.objects`, no n8n uploader.

## 3. Live drift reconfirmation (read-only, Supabase MCP SQL + n8n)

| Item | Live 2026-10-05 | Recorded (C1 precheck / spec reconcile) | Match |
|---|---|---|---|
| `asset_registry` | 12 rows: APPROVED 3, REVIEW 9, LOCKED 0; latest 2026-09-24T21:11:20Z | same | yes |
| C1 target asset_ids present | 0 of 4 | 0 | yes |
| Name/alias tokens (Agent-006 normalisation) equal to any intended name, alias or asset_id | 0 | 0 | yes |
| `storage.buckets` | `production-assets` (private) only | same | yes |
| `storage.objects` | 7; 0 under `visual/canonical/`; latest 2026-09-24T21:11:19Z | same | yes |
| readiness / ARI / jobs / batches | 5 / 40 / 11 / 3 | same | yes |
| migrations | 1 | 1 | yes |
| Agent-006 `ZTBdnKFO8STSjJU4` | `9bf6bbef…`, active false, activeVersionId null, 20 nodes | same | yes |

The spec has no material conflict with live state. Only the credential blocks C1.

## 4. Not performed

Upload, readback, the three APPROVED registrations, duo storage and the Agent-006 read-only match proof were not performed.

## 5. What is needed to resume

Replace the environment secret with a credential the Storage API accepts. Either:
- the legacy JWT `service_role` key (starts `eyJ…`), which works in both `Authorization: Bearer` and `apikey`; or
- keep the `sb_secret_…` key but configure the injection to also set the `apikey` header.

Then start a new session. C1 resumes from spec 4.1 unchanged.

## 6. Safety confirmation

- Supabase writes: 0 (storage 0, DB 0). n8n writes: 0.
- Agent-006 / Agent-007 executions: 0. Publications: 0.
- Generation, transformation and provider calls (OpenAI, Gemini, Runway): 0. Paid calls: 0.
- Readiness approvals: 0. Migrations: 0. Billing changes: 0.
- Mirror/cloth/berry, Agent-005, S3-B and Agent-000: untouched.
- Rollback: not applicable.

**Final status:** `STOPPED_PRE_WRITE + SUPABASE_CREDENTIAL_REJECTED + LOCAL_HASHES_VERIFIED + LIVE_STATE_NO_DRIFT + ZERO_WRITES + ZERO_GENERATION + ZERO_PAID_CALLS + ZERO_AGENT006_PRODUCTION_RUN + ZERO_AGENT007_PRODUCTION_RUN + ZERO_READINESS_APPROVAL + ZERO_MIGRATIONS`
