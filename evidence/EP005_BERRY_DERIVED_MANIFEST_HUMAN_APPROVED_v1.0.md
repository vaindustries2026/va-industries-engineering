# EP005 Derived Berry Manifest: Human Manifest Approval Applied

**Date:** 2026-10-05 (UTC)
**Actor:** Claude Code (bounded engineering operator), applying a recorded human decision
**Approval:** Gilang, recorded by Company Brain. Derived manifest `3bcde9ee-6676-480f-90da-5695b64532a7` (run `DRV-EP005-BERRY-SPLIT-1-A005O-1790400144423`, source `670b201b-6793-4518-ad5a-d051eb98d90c`, created at commit `5558aea`) is APPROVED for EP005 asset-resolution use.
**Approval covers:** only the evidenced deterministic berry split:
- CHEEK: S001–S009, removal S009
- MOUTH: S001–S015, removal S015
- NOSE: S001–S021, removal S021
- the derived S013 nose entry

**Manifest approval only.** It is NOT readiness, generation, spend, Agent-006 or Agent-007 execution, or publication approval.
**Scope:** Mikko & Lumi only.

## 1. Pre-write verification (all read live; all passed)

| Check | Result |
|---|---|
| Derived row `3bcde9ee` status | REVIEW |
| Derived manifest_json canonical sha256 | `3b855d95b7fc5bbffabbac22bbdebc2c4e702cf113b52192591f7602bb3fd0ec` (= the ENG-20261005-EP005-BERRY-SPLIT-DERIVED-MANIFEST evidence) |
| Derived row, all 21 written fields | identical to the committed transform output |
| Derived row, server md5 excluding status | `caafdbd5c80c4162e58457af1e3f97be` |
| Derived workload | video 15 (column and manifest), backlog `07d622e9…`, script `14471926…` |
| Source `670b201b` | APPROVED; row md5 `249adbfe4a9ddbc6c75446994979fe0d`, manifest md5 `da69805527dae414efb5d1823c0b7a97`, client sha `1666ee3c…6cdb` (all = evidence) |
| asset_registry | 20 rows, identical to the post-pack snapshot; md5 `b7b46112661dc0a0d9218e647f747306` |
| Five EP005 production objects (`visual/production/ep005/`) | 5; fingerprint md5 `048d29857b450192173e916913548d50` (name, id, eTag, size) |
| C1 objects (`visual/canonical/`) | 4; fingerprint md5 `7a4ac73df9f283693fb0737b3c7c0d51` |
| Other 8 manifests | md5 `a37fc5da14c39aab91af33c61a1cbc29` |
| Agent-006 `ZTBdnKFO8STSjJU4` | version `9bf6bbef-d49a-4f50-bce5-f8f146d43ca8`, active false, activeVersionId null |
| Table | `episode_production_manifests` has no updated_at or approval columns and no user triggers |

## 2. Write: the existing approval mechanism

This is the same statement used for the G3 approval of `670b201b` (ENG-20260926-018). There is no new column, migration or mechanism.

```sql
UPDATE episode_production_manifests SET status='APPROVED'
WHERE id='3bcde9ee-6676-480f-90da-5695b64532a7' AND status='REVIEW';
-- 1 row, applied 2026-10-05T06:11:59.844409Z
```

## 3. Post-write verification

| Check | Before | After |
|---|---|---|
| `3bcde9ee` status | REVIEW | **APPROVED** |
| `3bcde9ee` fields changed (client readback) | | `['status']` only |
| `3bcde9ee` server md5 excluding status | `caafdbd5…97be` | `caafdbd5…97be` |
| `3bcde9ee` manifest sha256 | `3b855d95…0ec` | `3b855d95…0ec` |
| `670b201b` row md5 / manifest md5 / status | `249adbfe…` / `da698055…` / APPROVED | same |
| Other 8 manifests md5 | `a37fc5da…` | same |
| APPROVED manifests | 2 | 3 |
| asset_registry md5 / rows | `b7b46112…` / 20 | same |
| EP005 objects fingerprint | `048d2985…` | same |
| C1 objects fingerprint | `7a4ac73d…` | same |
| storage.objects / readiness / ARI / jobs / batches / migrations | 16 / 5 / 40 / 11 / 3 / 1 | same |

**In-memory check after approval** (no n8n execution):
- I ran `evidence/ep005/berry_split/agent006_inmemory_sim.js` with `KEEP_STATUS=1`, so the row's **real** APPROVED status is used with no override.
- Node 03's approval gate now accepts `3bcde9ee`.
- The result is 18 requirements, identical to the evidenced simulation. Cheek, mouth and nose each resolve `REUSE_EXISTING` to their own row.
- Output: `evidence/ep005/berry_split/sim_derived_3bcde9ee_post_approval_real_status.json`.

## 4. Consequence noted (no action taken)

Agent-005's cost baseline (live 517b11ef nodes 11B/12; see ENG-20260926-018) picks the newest APPROVED manifest for backlog `07d622e9…`, preferring the same script.

- **Newest-first order now:** `3bcde9ee` (2026-10-05) > `670b201b` (2026-09-26) > `c56cabc0`.
- **Selected baseline:** now `3bcde9ee`.
- **Effect:** none financially. Its video workload is 15, the same as `670b201b`.
- **Agent-005:** not executed or modified.

## 5. Rollback (only with human authorisation)

```sql
UPDATE episode_production_manifests SET status='REVIEW'
WHERE id='3bcde9ee-6676-480f-90da-5695b64532a7' AND status='APPROVED';
```

This also returns the Agent-005 baseline to `670b201b` (video 15).

## 6. Safety confirmation

- Supabase writes: 1 status update on `3bcde9ee`. Nothing else was written.
- Source `670b201b`, asset_registry, storage, C1 canon and the five EP005 assets: unchanged.
- n8n writes: 0. Workflow changes: 0 (Agent-004, 005, 006 and 007).
- Agent-006 executions: 0. Agent-007 executions: 0. Publications: 0.
- Readiness approvals: 0. Generation, transformation, provider and paid calls: 0. Migrations: 0.
- Agent-000 and S3-B: untouched. No other project's material was read or used.

## 7. Final status

```text
EP005_BERRY_DERIVED_MANIFEST_HUMAN_APPROVED
+ DERIVED_MANIFEST_3BCDE9EE_APPROVED
+ SOURCE_MANIFEST_670B201B_UNCHANGED
+ DERIVED_BERRY_SPLIT_UNCHANGED
+ FIVE_EP005_PRODUCTION_ASSETS_UNCHANGED
+ C1_CANON_UNCHANGED
+ ZERO_AGENT006_PRODUCTION_RUN
+ ZERO_AGENT007_RUN
+ ZERO_READINESS_APPROVAL
+ ZERO_GENERATION
+ ZERO_PAID_CALLS
+ ZERO_MIGRATIONS
+ EVIDENCE_COMMITTED_TO_GITHUB
```

**Stop condition:** the task is complete. Any Agent-006 run against `3bcde9ee` needs separate authorisation.
