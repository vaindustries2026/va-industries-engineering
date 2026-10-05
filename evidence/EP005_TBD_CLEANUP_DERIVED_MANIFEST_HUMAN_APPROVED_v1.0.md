# EP005 TBD-Cleanup Derived Manifest: Human Manifest Approval Applied

**Date:** 2026-10-05 (UTC)
**Actor:** Claude Code (bounded engineering operator), applying a recorded human decision
**Approval:** Gilang, recorded by Company Brain. Derived manifest `96df250f-7182-4d5f-a556-b0448e518375` (run `DRV-EP005-TBD-CLEANUP-1-A005O-1790400144423`, source `3bcde9ee-6676-480f-90da-5695b64532a7`, evidence commit `fba91c0`) is APPROVED.
**Approval covers:** only the evidenced cleanup:
- mirror glint, mirror reflection and the completion-pop visual accent reclassified as compositing treatments
- FOLEY_TOUCH dropped
- AMBIENCE, FOLEY_CLOTH and COMPLETION_SFX left unresolved
- the 11 reusable requirements preserved unchanged

**Manifest approval only.** It is NOT readiness, Agent-006 or Agent-007 execution, generation, provider/spend, or publication approval.
**Scope:** Mikko & Lumi only.

## 1. Pre-write verification (all passed)

| Check | Result |
|---|---|
| `96df250f` status | REVIEW |
| `96df250f` manifest sha256 | `833bf0aab4f28f64bd5db72c129896811cc80705e1e9becbf6b9db123eb2422e` (= evidence); all 21 fields = transform output |
| `96df250f` server md5 excluding status | `0cca23736bf17738855fe8e5eea38854` |
| Source `3bcde9ee` | APPROVED, row md5 `931d64dfaca0b235ea70ea698cef7eea` (unchanged) |
| Source `670b201b` | APPROVED, row md5 `249adbfe4a9ddbc6c75446994979fe0d` (unchanged) |
| Other 9 manifests | md5 `0e9032d68a10a702375f0ce8cac0bc50` |
| asset_registry | 20 rows, md5 `b7b46112661dc0a0d9218e647f747306`, identical to the post-pack snapshot |
| storage.objects | md5 `4c7ef85e9c92af4fca27b775e233b7bc` |
| C1 canon | rows md5 `950ab7244df9c7a90f29ac981cb037a8`; objects fingerprint `7a4ac73df9f283693fb0737b3c7c0d51` |
| Readiness / ARI | `89663d3b…` / `409c215d…` |
| Agent-006 | `9bf6bbef-d49a-4f50-bce5-f8f146d43ca8`, active false, activeVersionId null |

## 2. Write: the existing approval mechanism

This is the same statement used for the G3 approval of `670b201b` (ENG-20260926-018) and for `3bcde9ee`.

```sql
UPDATE episode_production_manifests SET status='APPROVED'
WHERE id='96df250f-7182-4d5f-a556-b0448e518375' AND status='REVIEW';
-- 1 row, applied 2026-10-05T06:52:28.323329Z
```

## 3. Post-write verification

| Check | Before | After |
|---|---|---|
| `96df250f` status | REVIEW | **APPROVED** |
| Fields changed (client readback) | | `['status']` only |
| md5 excluding status | `0cca2373…8854` | same |
| Manifest sha256 | `833bf0aa…422e` | same |
| `3bcde9ee` / `670b201b` | `931d64df…` / `249adbfe…` | same |
| Other 9 manifests | `0e9032d6…` | same |
| APPROVED manifests | 3 | 4 |
| Registry, storage, C1 rows and objects, readiness, ARI | as §1 | same |
| Migrations | 1 | 1 |

**In-memory check after approval** (no n8n execution):
- I ran `agent006_inmemory_sim.js` with `KEEP_STATUS=1`, so the row's real APPROVED status is used.
- Node 03's gate now accepts `96df250f`.
- The result is **14 requirements**, identical to the evidenced simulation: 11 REUSE_EXISTING and 3 audio NEEDS_HUMAN_REVIEW (AMBIENCE, FOLEY_CLOTH, COMPLETION_SFX). It contains no visual-treatment requirement and no FOLEY_TOUCH.
- Output: `evidence/ep005/tbd_cleanup/sim_96df250f_post_approval_real_status.json`.

The three compositing treatments (`TREATMENT-EP005-MIRROR-GLINT-v01`, `-MIRROR-REFLECTION-v01`, `-COMPLETION-POP-ACCENT-v01`) are preserved byte-for-byte in the approved manifest.

## 4. Consequence noted (no action taken)

Agent-005's cost baseline takes the newest APPROVED manifest for backlog `07d622e9…`.

- **Newest-first order now:** `96df250f` > `3bcde9ee` > `670b201b` > `c56cabc0`.
- **Selected baseline:** now `96df250f`.
- **Effect:** none financially. Its video workload is 15, unchanged.

Agent-006 always takes the exact UUID it is given, so having several APPROVED EP005 manifests causes no ambiguity there. A future Agent-006 run must be pointed at `96df250f` explicitly.

## 5. Rollback (only with human authorisation)

```sql
UPDATE episode_production_manifests SET status='REVIEW'
WHERE id='96df250f-7182-4d5f-a556-b0448e518375' AND status='APPROVED';
```

## 6. Safety confirmation

- Supabase writes: 1 status update on `96df250f`. Nothing else was written.
- Source manifests, registry, storage and C1 canon: unchanged.
- n8n writes: 0. Workflow changes: 0.
- Agent-006 executions: 0. Agent-007 executions: 0.
- Readiness approvals: 0. Audio sourcing or generation: 0. Provider and paid calls: 0. Migrations: 0.
- Agent-000, S3-B and Anime Clip Farming: untouched.

## 7. Final status

```text
EP005_TBD_CLEANUP_DERIVED_MANIFEST_HUMAN_APPROVED
+ DERIVED_MANIFEST_96DF250F_APPROVED
+ THREE_VISUAL_TREATMENTS_PRESERVED
+ FOLEY_TOUCH_DROPPED
+ THREE_AUDIO_TBDS_REMAIN
+ ELEVEN_REUSE_EXISTING_PRESERVED
+ SOURCE_MANIFESTS_UNCHANGED
+ ZERO_AGENT006_RUN + ZERO_AGENT007_RUN + ZERO_READINESS_APPROVAL
+ ZERO_GENERATION + ZERO_PAID_CALLS + ZERO_MIGRATIONS
+ EVIDENCE_COMMITTED_TO_GITHUB
```

**Stop condition:** the task is complete.
