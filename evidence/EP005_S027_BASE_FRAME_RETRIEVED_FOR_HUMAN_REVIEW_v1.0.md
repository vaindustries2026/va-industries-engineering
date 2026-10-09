# EP005 S027 base frame: original output retrieved, ready for human review

Date: 2026-10-09. Mikko & Lumi only. Read-only retrieval.
**Result: EP005_S027_BASE_FRAME_READY_FOR_HUMAN_REVIEW.**

## Retrieved output
| Field | Value |
|---|---|
| Frame ID | `FRAME-EP005-S027-BASE-v01` |
| Provider request ID | `0d6997fe-6c53-487e-8477-242e60c80c75` |
| Original output URL | `https://d3u0tzju9qaucj.cloudfront.net/b253ddaf-db92-485d-a71c-c161961cb73b/a943a133-cbcb-4fee-875c-63f2f995a6dd.png` |
| Content type | `image/png` (header and PNG signature) |
| Dimensions | 2688 × 1520 (PNG 8-bit RGB, non-interlaced) |
| Byte size | 4,746,496 (equals `content-length`) |
| SHA-256 | `81b841a6ab53219b26755c4e83a9777953a2d03f37213875e38691c112f0061b` |
| MD5 | `bb9d46d4e2021f8dc99015d9d7222f9a` (equals S3 ETag → byte-exact transfer) |

## How the bytes are tied to FRAME-EP005-S027-BASE-v01
- The URL is the one in the `completed` status response for request `0d6997fe…0c75`, already recorded in `FLARE_GENERATION_RECORD_v1.json` before this task.
- The S3 object's `last-modified` is 06:02:15Z. That is between the submit (06:01:46Z) and the `completed` poll (06:02:24Z).
- The request produced exactly 1 output (`output_count: 1`).

## Method
- One plain HTTPS `GET` at 06:08:13Z, which returned HTTP 200. There were no provider API calls (no POST, no status poll).
- The bytes were written to disk as received. They were not resized, recompressed, cropped, converted or enhanced.
- The binary is **not committed**. The repo only keeps approved canon PNGs, and no policy allows committing generated outputs.
- The local copy is in the ephemeral session scratchpad, and it was shown to Gilang. Nothing was written to V&A production storage.
- **Provider CDN expiry:** `x-amz-expiration` says the object is deleted on **2026-10-17**. After approval, the exact bytes must be archived through an authorised storage task before that date.

## Status
- STATUS = **REVIEW**. HUMAN_DECISION = **PENDING**.
- An APPROVE or REJECT must cite SHA-256 `81b841a6…0061b`.
- `HUMAN_QC_RECORD_v1.json` holds the full checklist and Claude's advisory observations. Those observations are not a decision.
- Advisory flags for the reviewer:
  - Mikko's boots are cropped out of the frame, so "brown boots" and "grounded" cannot be confirmed visually.
  - The yellow speckle texture on the overalls is heavier than in canon.
  - Check Lumi's scale against the duo sheet.

## Counts
- Flare generations: 1 (unchanged). Generation attempts: 1. Automatic retries: 0.
- Provider POSTs this task: 0. Seedance POSTs: 0. Video generations: 0.
- Writes: 0 registry, 0 production storage, 0 manifest/readiness, 0 canon.
- Reference re-uploads: 0. Agent-006 runs: 0. Agent-007 runs: 0. Billing changes: 0.

Rollback: revert this commit. Nothing outside the repo changed.
