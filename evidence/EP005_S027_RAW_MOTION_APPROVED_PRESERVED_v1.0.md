# EP005 S027: raw Seedance motion APPROVED and preserved; registry insertion STOPPED pending type approval

Date: 2026-10-09 (UTC). Mikko & Lumi only.
**Result: EP005_S027_RAW_MOTION_APPROVED_AND_PRESERVED + REGISTRY_INSERT_STOPPED_TYPE_PROPOSAL_PENDING.**

## 1. Human decision
- **APPROVE** by Gilang / Company Brain, against raw-video SHA-256 `86dddea5a37cbe5b35a5c7540e0914ebebb1abcf1365cbc778b47ffc0b450e25`.
- Candidate `MOTION-EP005-S027-SEEDANCE20-CAND-v01`, provider request `09bd5c9b-b04a-4137-b2f4-519f18a14c33`.
- Accepted observations:
  - Mikko's small positional drift.
  - Mikko's slight fur-tone change.
  - Lumi's change from an open-mouth laugh to a closed smile.
- All other checklist items passed. The full record is in `agent008/phase1/s027_v2/S027_MOTION_HUMAN_QC_RECORD_v1.json`.
- Scope: an approved S027 **raw motion source**. It is shot-specific, not C1 canon, and not the final composited or rendered shot.

## 2. Exact-byte preservation
| Step | Result |
|---|---|
| Pre-write live state | `storage.objects` 20, `asset_registry` 24, manifests 11, readiness 7 (equal to the recorded state). Nothing under `visual/production/ep005/motion/`. Target key: NoSuchKey |
| Pre-upload SHA of local raw file | `86dddea5…0e25` (match) |
| Upload | `POST /storage/v1/object/production-assets/visual/production/ep005/motion/MOTION-EP005-S027-SEEDANCE20-CAND-v01.mp4`, `x-upsert: false`, `Content-Type: video/mp4`. HTTP 200, object id `db6dfae1-f5a9-4203-8bed-ada8743ab285` |
| Readback | HTTP 200, 3,411,040 bytes, `video/mp4`, SHA-256 `86dddea5…0e25`. **Match**; `cmp` shows the files are byte-identical |
| Post-write | `storage.objects` 21 (+1, this object). Registry 24, manifests 11 and readiness 7 are all unchanged |

The video was not re-encoded, trimmed, resized or modified. The binary is not committed to git.

## 3. Registry decision: STOPPED before insertion
- **Existing `asset_type` values:**
  - CHARACTER, ENVIRONMENT
  - PROP
  - OVERLAY_VFX (subtype BERRY_SMUDGE_OVERLAY)
  - AUDIO (subtypes SFX / AMBIENCE / FOLEY)
  - SHOT_FRAME (subtype BASE_FRAME)
- None of these describes a video motion source.
- **Agent-008 contract:** the CONTRACT keeps generated motion in the proposed tables `motion_generation_jobs` and `shot_render_candidates`, outside `asset_registry`. Neither table exists live.
- Per the instruction, I did not invent a type.

**Proposal for Company Brain** (not inserted). The exact row is in `agent008/phase1/s027_v2/S027_RAW_MOTION_REGISTRY_ROW_PROPOSED_v1.json`.

| Field | Proposed value | Rationale |
|---|---|---|
| asset_type | `SHOT_MOTION` | Mirrors the accepted `SHOT_FRAME`: a shot-specific visual production asset, here moving instead of still |
| asset_subtype | `RAW_MOTION_SOURCE` | Unmodified provider output, which is the input to the 8D compositor. It is distinct from a later composited or rendered shot (CONTRACT `shot_render_candidates`) |
| asset_id | `MOTION-EP005-S027-SEEDANCE20-CAND-v01` | The human-approved candidate id; also the storage file name |
| asset_name | `EP005 S027 Raw Motion Source` | A unique name |
| aliases | `[]` | So the row cannot capture any Agent-006 requirement, as with SHOT_FRAME |
| status | APPROVED | |

- `metadata_json` carries the full provenance:
  - S027, frame `FRAME-EP005-S027-BASE-v01` and its SHA
  - prompt SHA and request-body SHA
  - provider, model, request id and original output URL
  - raw SHA, duration, dimensions, fps, content type and bytes
  - the human APPROVE and the storage key
- **Alternative:** keep motion out of `asset_registry` entirely and create the CONTRACT's motion tables instead. That is a migration, so it needs its own authorisation.

## 4. Safety
- Regenerations: 0. Seedance POSTs this task: 0. Retries: 0. Kling: not used. Image generations: 0.
- Provider calls this task: 0.
- Writes: registry 0, manifest/readiness 0, canon 0. Compositor and render: not run.
- Not touched: Agent-006, Agent-007, publication, Anime Clip Farming.

Rollback: storage `DELETE /storage/v1/object/production-assets` with `{"prefixes":["visual/production/ep005/motion/MOTION-EP005-S027-SEEDANCE20-CAND-v01.mp4"]}`, and revert the evidence commit.

## 5. Status
```text
EP005_S027_RAW_MOTION_APPROVED_AND_PRESERVED
+ SHOT_ID = S027
+ HUMAN_DECISION = APPROVED
+ APPROVED_RAW_VIDEO_SHA256 = 86dddea5a37cbe5b35a5c7540e0914ebebb1abcf1365cbc778b47ffc0b450e25
+ EXACT_ORIGINAL_PRESERVED_TO_PRODUCTION_STORAGE
+ STORAGE_READBACK_SHA256_MATCH
+ ZERO_REGENERATIONS
+ REGISTRY_INSERT_STOPPED (proposed SHOT_MOTION / RAW_MOTION_SOURCE awaiting Company Brain)
+ EVIDENCE_COMMITTED_TO_GITHUB
```
**Stop condition:** waiting for Company Brain on the registry type, and before any compositor run or final shot assembly.
