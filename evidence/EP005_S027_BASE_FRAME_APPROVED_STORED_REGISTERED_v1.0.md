# EP005 S027 base frame: human APPROVED, exact bytes preserved, registered

Date: 2026-10-09 (UTC). Mikko & Lumi only.
**Result: EP005_S027_BASE_FRAME_APPROVED.**
This is a shot-specific EP005 production asset. It is **not** C1/global character canon.

## 1. Human decision
- **APPROVE** by Gilang, against exact SHA-256 `81b841a6ab53219b26755c4e83a9777953a2d03f37213875e38691c112f0061b`.
- Approved: Mikko and Lumi identity and appearance, their relative composition, clean Mikko face, cleaning cloth, pink flower mirror, bathroom, clean two-shot, animation-friendly pose, zero berry smudges, and no unacceptable defects.
- Accepted deviations:
  - Boot crop, for this knees-up S027 composition.
  - Outfit texture and detail.
  - Existing backpack badge.
- Approval record: `ENG-20261009-EP005-S027-BASE-FRAME-APPROVED`. Full record: `ep005/s027_base_frame/HUMAN_QC_RECORD_v1.json`.

## 2. Asset facts
| Field | Value |
|---|---|
| Frame / asset_id | `FRAME-EP005-S027-BASE-v01` |
| Provider request ID | `0d6997fe-6c53-487e-8477-242e60c80c75` (Higgsfield Marketing Studio Image 2.5 Flare) |
| Original provider URL | `https://d3u0tzju9qaucj.cloudfront.net/b253ddaf-db92-485d-a71c-c161961cb73b/a943a133-cbcb-4fee-875c-63f2f995a6dd.png` (expires 2026-10-17) |
| SHA-256 | `81b841a6ab53219b26755c4e83a9777953a2d03f37213875e38691c112f0061b` |
| Bytes | 4,746,496 |
| Dimensions | 2688 × 1520, PNG 8-bit RGB |
| Content type | `image/png` |

## 3. Pre-write reconciliation (live, read-only)
| Item | Live | Recorded | Match |
|---|---|---|---|
| `asset_registry` | 23 (APPROVED 14 / REVIEW 9) | 20 after the visual pack, +3 audio rows (ENG audio ingestion, 2026-10-07) | yes |
| `storage.objects` | 19, latest 2026-10-07T03:49:26Z | audio ingestion was the last write | yes |
| Target key | `404 NoSuchKey` | absent | yes |
| asset_id / name / path collisions (`S027`, `FRAME-EP005-S027-BASE-v01`) | 0 | 0 | yes |
| Latest APPROVED manifest | `45cc7493-80b4-4e8d-b71d-fbd7fd3656ed` | audio ingestion final derived manifest | yes |

## 4. Storage: exact-byte preservation
1. The local copy was re-hashed immediately before upload: SHA-256 matched.
2. Upload: `POST /storage/v1/object/production-assets/visual/production/ep005/frames/FRAME-EP005-S027-BASE-v01.png`, with `x-upsert: false` and `Content-Type: image/png`.
   - Response: HTTP 200, object id `cfb3bb48-2ca5-4146-835d-d27da6723891`.
3. Readback: `GET /storage/v1/object/authenticated/...` returned HTTP 200 with 4,746,496 bytes.
   - The readback SHA-256 is `81b841a6…0061b` (**match**).
   - `cmp` against the provider original shows the files are byte-identical. `storage.objects` reports a size of 4746496 and mimetype `image/png`.

## 5. Registry: plain insert of one APPROVED row
- The row was inserted with a single `POST /rest/v1/asset_registry`, with no `Prefer: resolution` header (an insert, not an upsert). Result: HTTP 201.
- `id d2a07b22-cf25-42ff-b86a-c4080ff24bc2`, created_at `2026-10-09T06:17:25.940513Z`. Exact JSON: `ep005/s027_base_frame/REGISTRY_ROW_v1.json` (as sent) and `REGISTRY_ROW_INSERTED_v1.json` (as returned).

| asset_id | asset_name | asset_type | asset_subtype | status | aliases | storage_path |
|---|---|---|---|---|---|---|
| FRAME-EP005-S027-BASE-v01 | EP005 S027 Base Frame | SHOT_FRAME | BASE_FRAME | APPROVED | [] | production-assets/visual/production/ep005/frames/FRAME-EP005-S027-BASE-v01.png |

- `metadata_json` records the following:
  - scope `MIKKO_LUMI_EP005_SHOT_SPECIFIC_PRODUCTION_ASSET`, with `not_c1_canon: true`
  - shot S027, sha256, bytes, dimensions, format and content type
  - storage key and object id
  - full provenance: provider, model, request ID, original URL, provider ETag, request-body and prompt SHA-256, and `bytes_modified: false`
  - `human_approval` APPROVED, `approval_authority` Gilang, `approved_sha256`, the approval record, and the accepted deviations
- **New type value `SHOT_FRAME`.** No existing type fits a shot frame (PROP / OVERLAY_VFX / AUDIO / CHARACTER / ENVIRONMENT), and the table has no type constraint.
  - Aliases are empty, so the row cannot capture any manifest requirement. §6 proves this.
  - Company Brain may rename the type. That is a single-row update.

## 6. Agent-006 read-only proof (no n8n execution, no writes)
- Method: the unmodified jsCode of nodes 03, 05 and 07 (repo export of version `9bf6bbef`) was run through `evidence/c1/agent006_readonly_match_proof.js`.
- Inputs: the live APPROVED manifest `45cc7493` and the live `status=in.(APPROVED,LOCKED)` registry, both read with GET only.

| | Governed rows | Requirements | Resolutions |
|---|---|---|---|
| Before the write | 14 | 14 | baseline |
| After the write | 15 (excluded 0) | 14 | **identical (diff empty)**; the frame matches no requirement |

Outputs: `ep005/s027_base_frame/AGENT006_READONLY_PROOF_{PREWRITE,POSTWRITE}.txt`.

## 7. Post-write side effects (live)
| Item | Before | After | Delta |
|---|---|---|---|
| storage.objects | 19 | 20 | +1 (this frame) |
| asset_registry | 23 | 24 | +1 (this row) |
| Pre-existing registry rows | — | field-for-field identical | 0 |
| episode_production_manifests | 11 | 11 | 0 |
| production_readiness_manifests | 7 | 7 | 0 |
| C1 canon (repo and `visual/canonical/`) | — | untouched | 0 |

## 8. Rollback (only if Company Brain or a human orders it)
```sql
delete from public.asset_registry where id = 'd2a07b22-cf25-42ff-b86a-c4080ff24bc2';
```
Storage rollback: `DELETE /storage/v1/object/production-assets` with `{"prefixes":["visual/production/ep005/frames/FRAME-EP005-S027-BASE-v01.png"]}`.

## 9. Safety
- Regenerations: 0. Flare generations stay at 1. Image generations this task: 0.
- Pixels modified: 0. Provider POSTs: 0.
- Seedance POSTs: 0. Video generations: 0. Reference re-uploads: 0.
- Agent runs: Agent-006 0 (local code proof only), Agent-007 0. n8n writes: 0.
- Writes: manifest 0, readiness 0, canon 0. Billing changes: 0.
- Anime Clip Farming: untouched. Credential values: never printed or committed.

## 10. Final status
```text
EP005_S027_BASE_FRAME_APPROVED
+ FRAME_ID = FRAME-EP005-S027-BASE-v01
+ HUMAN_DECISION = APPROVED
+ APPROVED_SHA256 = 81b841a6ab53219b26755c4e83a9777953a2d03f37213875e38691c112f0061b
+ EXACT_ORIGINAL_PRESERVED_TO_PRODUCTION_STORAGE
+ STORAGE_READBACK_SHA256_MATCH
+ PRODUCTION_ASSET_REGISTERED_APPROVED
+ ZERO_REGENERATIONS
+ ZERO_VIDEO_GENERATIONS
+ ZERO_SEEDANCE_POSTS
+ EVIDENCE_COMMITTED_TO_GITHUB
```
**Stop condition:** Claude Code is stopping here. Motion generation waits on Company Brain.
