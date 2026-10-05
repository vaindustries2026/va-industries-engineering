# EP005 Working Visual Pack: Five Production Assets Stored, Hash-Verified and Registered

**Date:** 2026-10-05 (UTC)
**Actor:** Claude Code (bounded engineering operator)
**Requested by:** Gilang / Company Brain
**Approval record:** `ENG-20261005-EP005-WORKING-VISUAL-PACK-APPROVED`. This covers the file mapping, the WebP bytes, the storage location, the aliases, and the cheek alias decision (Option 1).
**Scope:** Mikko & Lumi only. These five assets are approved EP005 working production assets, not core visual canon.
**Result:** `COMPLETE`

## 1. History of this task

| Step | Outcome |
|---|---|
| Pre-ingestion manifest (read-only) | Proposed rows, collision checks, in-memory Agent-006 simulation. Zero writes. |
| First authorisation | Stopped before any write. The approved cheek alias `Berry smudge on Mikko's anatomical left cheek` is byte-identical to the primary label of the combined berry requirement. In simulation it made that requirement resolve `REUSE_EXISTING` to the cheek row, which contradicted the decision to leave it unresolved. Zero writes. |
| Option 1 authorisation | Cheek `aliases = []`. Executed as recorded below. |

## 2. Authoritative source bytes (session attachments; WebP accepted by Company Brain)

| Session file | asset_id | SHA-256 | Bytes | Dimensions | Format | Alpha |
|---|---|---|---|---|---|---|
| `images/6.webp` | PROP-EP005-HAND-MIRROR-v01 | `34fa31a132144c355714480fa82b22916fc2f825d418658bb787791a0b9c56ac` | 47670 | 1448x1086 | WebP lossy VP8, sRGB ICC | no (opaque) |
| `images/7.webp` | PROP-EP005-CLEANING-CLOTH-v01 | `afaa3a9fcfc5b562023080318425457c5b4dda8eb58065f56ae542786637c1db` | 237724 | 1447x1087 | WebP lossy VP8, sRGB ICC | no (opaque) |
| `images/8.webp` | OVERLAY-EP005-BERRY-SMUDGE-CHEEK-v01 | `b2c735f270fccda76861e28212bec2cd60bd20564aa8c35d9a7affa394ca78ac` | 257966 | 1447x1087 | WebP lossy VP8 + ALPH, sRGB ICC | yes |
| `images/10.webp` | OVERLAY-EP005-BERRY-SMUDGE-MOUTH-v01 | `df7c2adb446daaae3eafc0a5fce3090b4b5c2c1409d12fd82d4b242b0f637b0e` | 294014 | 1448x1086 | WebP lossy VP8 + ALPH, sRGB ICC | yes |
| `images/9.webp` | OVERLAY-EP005-BERRY-SMUDGE-NOSE-v01 | `c11691271bcdbfc7b20ca253d59518560ec17e446a28f72cc3ab88da1da00bc1` | 285032 | 1446x1087 | WebP lossy VP8 + ALPH, sRGB ICC | yes |

All five source hashes were reconfirmed immediately before the upload. The files were not converted or transformed.

## 3. Pre-write checks (live, read-only)

- **Registry:** 15 rows (APPROVED 6 / REVIEW 9), unchanged since the pre-ingestion read.
- **APPROVED/LOCKED collisions:** none on asset_id, asset_name or alias (Agent-006 normalisation).
- **REVIEW collisions:** the mirror and cloth aliases also appear on 5 Agent-007 REVIEW candidates. Agent-006's `status=in.(APPROVED,LOCKED)` filter excludes those rows, so there is no effect on matching. They were left untouched.
- **Storage paths:** no existing registry storage_path collides with a proposed one.
- **`TMP_EP005_BERRY_SMUDGE_OVERLAYS`:** on none of the five rows.
- **Storage keys:** all five target keys returned `404 NoSuchKey`.
- **Agent-006:** live `ZTBdnKFO8STSjJU4` is at version `9bf6bbef-d49a-4f50-bce5-f8f146d43ca8`, active false, activeVersionId null. Its node 05 and 07 code is identical to the repo export.
- **Pre-write simulation:** mirror and cloth resolve `REUSE_EXISTING`, berry resolves `CREATE_NEW`, and the C1 mappings are unchanged.

## 4. Storage: no-overwrite upload and readback (bucket `production-assets`)

Uploads used `POST /storage/v1/object/production-assets/<key>` with `x-upsert: false` and `Content-Type: image/webp`. Readbacks used `GET /storage/v1/object/authenticated/...`.

| Object key | Object id | Upload | Readback bytes | Readback SHA-256 match |
|---|---|---|---|---|
| `visual/production/ep005/props/PROP-EP005-HAND-MIRROR-v01.webp` | `e5ef12f3-baea-4cf8-9ce9-46d1a917abb0` | 200 | 47670 | yes |
| `visual/production/ep005/props/PROP-EP005-CLEANING-CLOTH-v01.webp` | `80744e45-d904-4086-9069-e010b17187bb` | 200 | 237724 | yes |
| `visual/production/ep005/overlays/OVERLAY-EP005-BERRY-SMUDGE-CHEEK-v01.webp` | `48a1acf0-b020-4cbd-b003-2a614d753c03` | 200 | 257966 | yes |
| `visual/production/ep005/overlays/OVERLAY-EP005-BERRY-SMUDGE-MOUTH-v01.webp` | `de46e075-fc63-46ac-a10a-3ad501e829cb` | 200 | 294014 | yes |
| `visual/production/ep005/overlays/OVERLAY-EP005-BERRY-SMUDGE-NOSE-v01.webp` | `e595212b-ca24-44ac-8069-68c40583b088` | 200 | 285032 | yes |

## 5. Registry: plain insert of exactly five APPROVED rows

The five rows were written with a single `POST /rest/v1/asset_registry`, with no `Prefer: resolution` header (an insert, not an upsert). Result: HTTP 201. All five have created_at `2026-10-05T05:43:49.911478Z`. The exact JSON is in `evidence/ep005/EP005_WORKING_VISUAL_PACK_REGISTRY_ROWS_v1.0.json`.

| id | asset_id | asset_name | asset_type | asset_subtype | aliases | storage_path |
|---|---|---|---|---|---|---|
| `a61c0af2-1e8d-40e2-88d1-8848390f2a17` | PROP-EP005-HAND-MIRROR-v01 | EP005 Hand Mirror | PROP | null | TMP_EP005_HAND_MIRROR, Tiny hand mirror | production-assets/visual/production/ep005/props/PROP-EP005-HAND-MIRROR-v01.webp |
| `ab33c77c-5fde-4642-9efb-706f619c4a7e` | PROP-EP005-CLEANING-CLOTH-v01 | EP005 Cleaning Cloth | PROP | null | TMP_EP005_SOFT_CLOTH, Soft cloth | production-assets/visual/production/ep005/props/PROP-EP005-CLEANING-CLOTH-v01.webp |
| `e2fc6426-bf97-437e-9515-d86419a0498a` | OVERLAY-EP005-BERRY-SMUDGE-CHEEK-v01 | EP005 Berry Smudge - Cheek | OVERLAY_VFX | BERRY_SMUDGE_OVERLAY | **[] (intentional)** | production-assets/visual/production/ep005/overlays/OVERLAY-EP005-BERRY-SMUDGE-CHEEK-v01.webp |
| `b960c11c-6b88-4223-854b-e9ba44c7aad4` | OVERLAY-EP005-BERRY-SMUDGE-MOUTH-v01 | EP005 Berry Smudge - Mouth | OVERLAY_VFX | BERRY_SMUDGE_OVERLAY | Berry smudge on skin beside Mikko's mouth | production-assets/visual/production/ep005/overlays/OVERLAY-EP005-BERRY-SMUDGE-MOUTH-v01.webp |
| `dfaa3b89-8366-44dc-ace9-542b4a764a80` | OVERLAY-EP005-BERRY-SMUDGE-NOSE-v01 | EP005 Berry Smudge - Nose | OVERLAY_VFX | BERRY_SMUDGE_OVERLAY | Berry smudge on Mikko's nose | production-assets/visual/production/ep005/overlays/OVERLAY-EP005-BERRY-SMUDGE-NOSE-v01.webp |

Common fields: `version = v01`, `status = APPROVED`, `source_url = NULL`.

`metadata_json` on every row records:
- `canon_scope`: MIKKO_LUMI_EP005_WORKING_PRODUCTION_ASSETS
- `canon_role`, `episode_code` (EP-CANDIDATE-005) and `production_manifest_id` (670b201b)
- `satisfies_requirement` and `agent004_temp_asset_id`
- `human_approval`, `approval_authority` (Gilang) and `approval_record`
- source session file, `sha256`, `bytes`, `dimensions`, `format`, `has_alpha` and `storage_object_key`

The three overlays also record `overlay_set` EP005_BERRY_SMUDGE, the three members, and continuity removal (cheek S009 / mouth S015 / nose S021). There is no anchor field: the anchor workaround was rejected.

**Post-write verification:**
- `asset_registry` has 20 rows (APPROVED 11 / REVIEW 9).
- Every inserted field equals the approved JSON.
- All 15 pre-existing rows, including the 3 C1 rows, are field-for-field identical to the pre-write snapshot.

## 6. Agent-006 read-only resolution proof (after the write)

**Method:** the same as the C1 proof. The unmodified jsCode of nodes 03, 05 and 07 from live `9bf6bbef` was run locally in Node against the live APPROVED manifest `670b201b` and the live `status=in.(APPROVED,LOCKED)` registry. Both were read with GET only. No n8n execution took place and nothing was written. Full output: `evidence/ep005/EP005_WORKING_VISUAL_PACK_AGENT006_POSTWRITE_PROOF.txt`. Governed rows: 11 read, 11 governed, 0 excluded.

| Requirement | Exact matches | Resolution | Expected |
|---|---|---|---|
| APPROVED_NEW::TMP_EP005_HAND_MIRROR ("Tiny hand mirror") | PROP-EP005-HAND-MIRROR-v01 | REUSE_EXISTING | ✓ MIRROR_MATCH_READY |
| APPROVED_NEW::TMP_EP005_SOFT_CLOTH ("Soft cloth") | PROP-EP005-CLEANING-CLOTH-v01 | REUSE_EXISTING | ✓ CLOTH_MATCH_READY |
| APPROVED_NEW::TMP_EP005_BERRY_SMUDGE_OVERLAYS | none | CREATE_NEW | ✓ intentionally unresolved |
| TBD::CHARACTER::Mikko | CHAR-MIKKO-MASTER-v01 | REUSE_EXISTING | ✓ C1 unchanged |
| TBD::CHARACTER::Lumi | CHAR-LUMI-MASTER-v01 | REUSE_EXISTING | ✓ C1 unchanged |
| TBD::ENVIRONMENT::Canonical environment/background | WORLD-EP005-BATHROOM-MASTER-v01 | REUSE_EXISTING | ✓ C1 unchanged |
| 3 APPROVED_REUSE audio | SFX rows | REUSE_EXISTING | unchanged |
| 3 visual TBDs (mirror glint, mirror reflection, completion pop) and 4 audio TBDs | none | NEEDS_HUMAN_REVIEW | unchanged, out of scope |

**Open item for a separate task:** the single combined berry requirement still needs its structure repaired. The registered cheek, mouth and nose rows are ready to be mapped once that happens.

## 7. Post-write side-effect check (live)

| Item | Before | After | Delta |
|---|---|---|---|
| storage.objects | 11 | 16 | +5 (all under `visual/production/ep005/`) |
| C1 objects under `visual/canonical/` | 4 (last updated 2026-10-05T04:38:09Z) | 4 (same) | 0 |
| asset_registry | 15 | 20 | +5 |
| readiness / ARI / jobs / batches | 5 / 40 / 11 / 3 | 5 / 40 / 11 / 3 | 0 |
| episode_production_manifests | 8 | 8 | 0 |
| Migrations | 1 | 1 | 0 |
| Agent-006 | 9bf6bbef, unpublished | 9bf6bbef, unpublished | 0 |

## 8. Rollback (only if Company Brain or a human orders it)

```sql
delete from public.asset_registry where id in (
  'a61c0af2-1e8d-40e2-88d1-8848390f2a17','ab33c77c-5fde-4642-9efb-706f619c4a7e',
  'e2fc6426-bf97-437e-9515-d86419a0498a','b960c11c-6b88-4223-854b-e9ba44c7aad4',
  'dfaa3b89-8366-44dc-ace9-542b4a764a80');
```

Storage rollback: `DELETE /storage/v1/object/production-assets` with `{"prefixes":[...the five keys in §4...]}`.

## 9. Safety confirmation

- Supabase writes: storage 5 objects (no-overwrite), DB 5 rows (plain insert). Nothing else was written.
- n8n writes: 0. Agent-006 modification: none.
- Agent-006 production executions: 0. Agent-007 executions: 0. Publications: 0.
- Image generation and transformation: 0. Provider calls: 0. Paid calls: 0.
- Migrations: 0. Readiness approvals: 0.
- Continuity references: not ingested.
- Untouched: Agent-005, S3-B, Agent-000, C1 canon.
- Credential value: never printed, logged or committed.

## 10. Final status

```text
EP005_FIVE_WORKING_PRODUCTION_ASSETS_STORED
+ FIVE_STORED_BYTES_HASH_VERIFIED
+ HAND_MIRROR_APPROVED_REGISTERED
+ CLEANING_CLOTH_APPROVED_REGISTERED
+ CHEEK_SMUDGE_APPROVED_REGISTERED_WITH_NO_ALIAS
+ MOUTH_SMUDGE_APPROVED_REGISTERED
+ NOSE_SMUDGE_APPROVED_REGISTERED
+ MIRROR_MATCH_READY
+ CLOTH_MATCH_READY
+ BERRY_COMBINED_REQUIREMENT_INTENTIONALLY_UNRESOLVED
+ C1_CANON_UNCHANGED
+ EVIDENCE_COMMITTED_TO_GITHUB
+ ZERO_GENERATION + ZERO_PAID_CALLS + ZERO_AGENT006_PRODUCTION_RUN + ZERO_AGENT007_PRODUCTION_RUN + ZERO_MIGRATIONS
```

**Stop condition:** the task is complete. Claude Code is stopping here and will not continue into the berry requirement repair or any other task without Company Brain authorisation.
