# C1: Visual Canon Stored, Hash-Verified and Registered (COMPLETE)

**Date:** 2026-10-05 (UTC)
**Actor:** Claude Code (bounded engineering operator)
**Requested by:** Gilang / Company Brain
**Spec:** `evidence/C1_EVIDENCE_GAP_REPAIR_AND_IMPLEMENTATION_SPEC_v1.0.md` (§4.1, §4.2, §4.3, §5)
**Scope:** Mikko & Lumi only.
**Result:** `C1_COMPLETE`

## 1. Preconditions

| Check | Result |
|---|---|
| Required reading: CLAUDE.md, C1 spec, ENGINEERING_CHANGELOG, C1_RESUME_STOPPED_CREDENTIAL_REJECTED | done |
| `main` contains `e7ebdf8` | yes (`origin/main` HEAD = `e7ebdf8`) |
| Local `canon/c1/` bytes vs spec (SHA-256, bytes) | 4/4 match. Source commit `5055f760c5f00e3e0f8eab9ab5288a808b27b0c5` exists |

## 2. Credential connectivity tests (read-only)

The credential value was never printed, logged, inspected or committed.

| Test | Request | Result |
|---|---|---|
| Authenticated list, private bucket | `POST /storage/v1/object/list/production-assets` | **200**: top-level prefixes `audio/`, `visual/` |
| Authenticated read, `asset_registry` | `GET /rest/v1/asset_registry?select=asset_id,status` | **200**: rows returned |

Both tests passed, so C1 continued from spec §4.1.

## 3. Drift reconfirmation before any write (live)

| Item | Live (pre-write) | Recorded (ENG-20261005-C1-CRED-REJECTED) | Match |
|---|---|---|---|
| `asset_registry` | 12 rows (APPROVED 3 / REVIEW 9 / LOCKED 0); latest 2026-09-24T21:11:20Z | same | yes |
| Target asset_ids present | 0 | 0 | yes |
| Name/alias collisions (Agent-006 normalisation, plus SQL by id/name/alias) | 0 / 0 / 0 / 0 | 0 | yes |
| Buckets | `production-assets` (private) only | same | yes |
| `storage.objects` | 7; 0 under `visual/canonical/`; latest 2026-09-24T21:11:19Z | same | yes |
| Target object keys | 4/4 `404 NoSuchKey` | absent | yes |
| readiness / ARI / jobs / batches | 5 / 40 / 11 / 3 | same | yes |
| Migrations | 1 | 1 | yes |
| Agent-006 `ZTBdnKFO8STSjJU4` | version `9bf6bbef-d49a-4f50-bce5-f8f146d43ca8`, active false, activeVersionId null, 20 nodes | same | yes |

No drift was found.

## 4. Storage (spec §4.1): no-overwrite upload and readback

Uploads used `POST /storage/v1/object/production-assets/<key>` with `x-upsert: false` and `Content-Type: image/png`. Each object was then read back with `GET /storage/v1/object/authenticated/...` and its SHA-256 recomputed.

| Object key (bucket `production-assets`) | Object id | Upload | Readback bytes | Readback SHA-256 | Dims / mode | Verified |
|---|---|---|---|---|---|---|
| `visual/canonical/characters/CHAR-MIKKO-MASTER-v01.png` | `06b16cf9-cff5-44a7-9ba7-43d707ea428f` | 200 | 2207008 | `41c9480a847c962c1ecfda4fe076e0abcd86548ba67f692621cfc6e13d61f1a8` | 1448x1086 RGB 8-bit | yes |
| `visual/canonical/characters/CHAR-LUMI-MASTER-v01.png` | `8b729cf0-d22c-47e0-a986-f55072760641` | 200 | 1887897 | `8b29c1abea53cb253eea39cdd41d5001ed38036945b049078915ac5993c43a41` | 1448x1086 RGB 8-bit | yes |
| `visual/canonical/references/DUO-MIKKO-LUMI-SCALE-v01.png` | `9d5c8dd7-6684-48f4-9c4d-8fcfdd9d9486` | 200 | 1704130 | `735d64075af999d8a00d35afe2674174f5e0feea9b1b4acb9ec2208f1e1d121f` | 1448x1086 RGB 8-bit | yes |
| `visual/canonical/worlds/WORLD-EP005-BATHROOM-MASTER-v01.png` | `f45a29b6-b297-42db-bef4-848b0205542a` | 200 | 1756516 | `ab79c560d3c79a05cb957331149ee4b8a176e109b06010480ba6c26903bd3733` | 1448x1086 RGB 8-bit | yes |

All four keys were absent before upload, so nothing was overwritten. All four readbacks equal the authoritative ENG-20260930-023 hashes.

## 5. Registry (spec §4.2): plain insert of exactly three APPROVED rows

The pre-insert checks (exact asset_id, normalised asset_name and every intended alias) returned 0 matches, both through Agent-006 normalisation and through independent SQL. The rows were written with a single plain `POST /rest/v1/asset_registry`, with no `Prefer: resolution` header (an insert, not an upsert). Result: HTTP 201.

| id | asset_id | asset_name | asset_type | status | storage_path | aliases |
|---|---|---|---|---|---|---|
| `0d7a47e0-0adf-47d6-9cf9-f71ad7439747` | CHAR-MIKKO-MASTER-v01 | Mikko | CHARACTER | APPROVED | production-assets/visual/canonical/characters/CHAR-MIKKO-MASTER-v01.png | Mikko, TBD::CHARACTER::Mikko |
| `75cf9e5d-78ec-4cac-b1bb-49e696629bc2` | CHAR-LUMI-MASTER-v01 | Lumi | CHARACTER | APPROVED | production-assets/visual/canonical/characters/CHAR-LUMI-MASTER-v01.png | Lumi, TBD::CHARACTER::Lumi |
| `8cdeea80-1eb3-4a75-b50a-c209f1aae434` | WORLD-EP005-BATHROOM-MASTER-v01 | EP005 Child-Friendly Bathroom Master | ENVIRONMENT | APPROVED | production-assets/visual/canonical/worlds/WORLD-EP005-BATHROOM-MASTER-v01.png | Canonical environment/background, TBD::ENVIRONMENT::Canonical environment/background |

All three rows have created_at `2026-10-05T04:38:59.32645Z`, `version = v01`, `asset_subtype = NULL` and `source_url = NULL`. `metadata_json` and `notes` match the spec exactly, including sha256, approval_record ENG-20260930-023 and source_repo_commit 5055f760.

Read-back verification:
- `asset_registry` now has 15 rows (APPROVED 6 / REVIEW 9 / LOCKED 0).
- Every inserted field equals the spec JSON.
- All 12 pre-existing rows are field-for-field identical to the pre-write snapshot. No unrelated row was mutated, downgraded or overwritten.

## 6. Duo (spec §4.3)

`DUO-MIKKO-LUMI-SCALE-v01` is stored and hash-verified at `production-assets/visual/canonical/references/DUO-MIKKO-LUMI-SCALE-v01.png`. It has no `asset_registry` row, and no new asset_type was created. Status: `DUO_REFERENCE_STORED_NOT_REGISTRY_MAPPED`.

## 7. Agent-006 read-only matching proof (spec §5)

**Method:** The jsCode of Agent-006 nodes `03 - Prepare Resolution Context`, `05 - Build Asset Resolution Work Items` and `07 - Resolve Current Asset Requirement` was taken unmodified from live draft version `9bf6bbef-d49a-4f50-bce5-f8f146d43ca8` (unpublished) and run locally in Node v22. The inputs were:
- the live APPROVED EP005 production manifest `670b201b-6793-4518-ad5a-d051eb98d90c`, read by GET;
- the live `asset_registry` rows matching `status=in.(APPROVED,LOCKED)`, the same filter node 04 uses, read by GET.

The run used no n8n execution and wrote nothing to n8n or Supabase. The harness is committed at `evidence/c1/agent006_readonly_match_proof.js`.

**Governed registry seen by 05:** rows_read 6, governed 6, excluded 0.

| Production requirement label | requirement_key | Exact APPROVED/LOCKED matches | 07 resolution | canonical_asset_id |
|---|---|---|---|---|
| Mikko | TBD::CHARACTER::Mikko | 1 (`CHAR-MIKKO-MASTER-v01`) | REUSE_EXISTING | CHAR-MIKKO-MASTER-v01 |
| Lumi | TBD::CHARACTER::Lumi | 1 (`CHAR-LUMI-MASTER-v01`) | REUSE_EXISTING | CHAR-LUMI-MASTER-v01 |
| Canonical environment/background | TBD::ENVIRONMENT::Canonical environment/background | 1 (`WORLD-EP005-BATHROOM-MASTER-v01`) | REUSE_EXISTING | WORLD-EP005-BATHROOM-MASTER-v01 |

Other requirements are shown for context only, and none were acted on:
- The 3 audio REUSE requirements still resolve to their existing SFX rows.
- The 3 APPROVED_NEW props/overlays (mirror, cloth, berry) remain CREATE_NEW.
- The 3 visual OVERLAY_VFX TBDs and 4 audio TBDs remain NEEDS_HUMAN_REVIEW.

These are unchanged and out of C1 scope. The REVIEW-status Agent-007 candidates were excluded by the status filter, as designed.

Status: `AGENT006_MATCH_READINESS_PROVEN_READ_ONLY`.

## 8. Post-write side-effect check (live)

| Item | Before | After | Delta |
|---|---|---|---|
| `storage.objects` (under `visual/canonical/`) | 7 (0) | 11 (4) | +4, all C1 |
| `asset_registry` | 12 | 15 | +3, all C1 |
| readiness / ARI / jobs / batches | 5 / 40 / 11 / 3 | 5 / 40 / 11 / 3 | 0 |
| episode_production_manifests | 8 | 8 | 0 |
| Migrations | 1 | 1 | 0 |
| n8n workflows | not written | not written | 0 |

## 9. Rollback (only if Company Brain or a human orders it)

```sql
-- registry: delete exactly the three C1 rows
delete from public.asset_registry where id in (
  '0d7a47e0-0adf-47d6-9cf9-f71ad7439747',
  '75cf9e5d-78ec-4cac-b1bb-49e696629bc2',
  '8cdeea80-1eb3-4a75-b50a-c209f1aae434');
```

Storage rollback: `DELETE /storage/v1/object/production-assets` with body `{"prefixes":[...the four object keys in §4...]}`. No other state needs reverting.

## 10. Safety confirmation

- Supabase writes: storage 4 objects (no-overwrite), DB 3 rows (plain insert). No other writes.
- n8n writes: 0.
- Agent-006 production executions: 0. Agent-007 executions: 0. Publications: 0.
- Image generation and transformation: 0.
- OpenAI, Gemini and Runway calls: 0. Paid calls: 0.
- Readiness approvals: 0. Migrations: 0. Billing, subscription and credit changes: 0.
- Untouched: mirror/cloth/berry, Agent-005, S3-B, Agent-000.
- Credential value: never printed, logged or committed.

## 11. Final status

```text
C1_VISUAL_CANON_DURABLY_STORED
+ STORED_BYTES_HASH_VERIFIED
+ MIKKO_APPROVED_REGISTERED
+ LUMI_APPROVED_REGISTERED
+ EP005_BATHROOM_APPROVED_REGISTERED
+ DUO_REFERENCE_STORED_NOT_REGISTRY_MAPPED
+ AGENT006_MATCH_READINESS_PROVEN_READ_ONLY
+ EVIDENCE_COMMITTED_TO_GITHUB
+ ZERO_GENERATION
+ ZERO_PAID_CALLS
+ ZERO_AGENT006_PRODUCTION_RUN
+ ZERO_AGENT007_PRODUCTION_RUN
+ ZERO_READINESS_APPROVAL
+ ZERO_MIGRATIONS
```

**Stop condition:** C1 is complete. Claude Code is stopping here and will not continue into any next task without Company Brain authorisation.
