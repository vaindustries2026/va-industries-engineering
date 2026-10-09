# EP005 S027: one Seedance 2.0 motion candidate generated; READY FOR HUMAN REVIEW

Date: 2026-10-09 (UTC). Mikko & Lumi only.
**Result: EP005_S027_SEEDANCE_MOTION_READY_FOR_HUMAN_REVIEW.**
- Authorised by Company Brain / human: exactly 1 source upload and 1 generation, with a ceiling of $3.50.
- Package: commit `195591f`.

## 1. Step 1: reconcile approved inputs (before any provider write)
- Registry row `d2a07b22-…` is `FRAME-EP005-S027-BASE-v01`, status **APPROVED**.
- The frame was re-read from production storage. Its SHA-256 is `81b841a6…0061b` (match).
- The prompt (file and package) has SHA-256 `ab7f92af…cab3` (match).

## 2. Step 2: source upload (exactly one)
- Script: `stage1_reconcile_and_upload.py`.
- **Flow:**
  1. The SHA was re-verified immediately before upload: status, hash and PNG signature checked.
  2. `UPLOAD_RESERVED` was ledgered before any request.
  3. One `POST /files/generate-upload-url` was sent.
  4. One PUT went to `fnf-api-input-prod-…s3.amazonaws.com`, with only the returned headers. `_storage_put` refuses any API or proxy-injected host, so no credential was sent with it.
- **Recorded result:**
  - `public_url = https://d3snorpfx4xhv8.cloudfront.net/b253ddaf-db92-485d-a71c-c161961cb73b/5cfa56ae-c54e-4377-a078-d0e6b1b56329.png`
  - The URL was ledgered **before** readback.
  - Readback: HTTP 200, 4,746,496 bytes, `image/png`, SHA-256 `81b841a6…0061b` (**match**).
- Evidence: `evidence/agent008/phase1/s027_v2/S027_SOURCE_UPLOAD_v1.json`.

## 3. Steps 3–4: frozen request and final spend gate
- Script: `stage2_freeze_and_gate.py`. Output: `S027_FINAL_GATE_v1.json`.
- **Body:** `{prompt, image_url, duration: 5, resolution: "1080p", generate_audio: false}`. There is no negative_prompt field and no extra fields. The prompt is unmodified.
- **FINAL_REQUEST_BODY_SHA256 = `139e98c1799dedace2b7f30b93b34a94e7002b6204bffdbef5a99c4cad38f499`.** This covers 1,967 wire bytes, serialised exactly as the transport sends them.
- **SpendAuthorisation:**
  - HIGGSFIELD, `bytedance/seedance-2.0/image-to-video`, S027
  - frame `81b841a6…`, prompt `ab7f92af…`
  - max_generations 1, no_auto_retry, human_approved
  - maximum cost $3.50
- **Expected cost:** $3.402 for 1920×1080, $3.427 for 1920×1088. Both are at or below $3.50.
- **Checks:** Agent-008 preflight reported **0 blockers**, and the runner's `validate_pre_generation` passed.
- This pre-submit evidence was committed (`6cc6b5e`) before the POST.

## 4. Steps 5–7: one submit, read-only polling, raw retrieval
- Script: `stage3_submit_once.py`, using Agent-008 `run_once`.
- The script refuses to run if any generation reservation exists, or if the body no longer hashes to the frozen SHA.

| Item | Value |
|---|---|
| Ledger | `RESERVED` (attempt 1) before transmission. Then `SUBMIT_ACCEPTED`, `SUBMITTED`, 14 × `POLL`, `COMPLETED` |
| POST | 1 × `https://api.higgsfield.ai/bytedance/seedance-2.0/image-to-video` at 07:52:49Z. HTTP 200 `queued` |
| Provider request_id | **`09bd5c9b-b04a-4137-b2f4-519f18a14c33`** |
| Sent body SHA-256 | `139e98c1…f499` (equals the frozen value) |
| Polls | `queued` ×1, `in_progress` ×12, `completed` ×1. Status route only |
| Output URL | `https://d3u0tzju9qaucj.cloudfront.net/b253ddaf-db92-485d-a71c-c161961cb73b/e40add72-db79-43bf-a1bd-27c7f6c0c85e.mp4` (provider deletes it on 2026-10-17) |
| Content type | `video/mp4` |
| Bytes | 3,411,040 (MD5 `3ec7d7bd…5050` equals the CDN ETag, so the transfer is byte-exact) |
| **Raw video SHA-256** | **`86dddea5a37cbe5b35a5c7540e0914ebebb1abcf1365cbc778b47ffc0b450e25`** |
| Stream | H.264 yuv420p, **1920×1080**, **24 fps**, 121 frames, **5.042 s**, **no audio stream** |
| Modified | No. The raw file was frozen read-only by the runner, and it is not committed (no repo policy allows video binaries) |

## 5. Cost
- The provider reported no cost or usage field.
- Calculated cost:
  - 243,000 tokens gives **$3.402**.
  - If billed on the actual 121 frames (5.0417 s), 245,026 tokens gives **$3.430**.
- Both are **at or below the $3.50 ceiling**.
- The balance is not readable through the documented routes. No purchase, top-up or billing change was made.

## 6. Status and QC
- Candidate `MOTION-EP005-S027-SEEDANCE20-CAND-v01`: STATUS = **REVIEW**, HUMAN_DECISION = **PENDING**.
- QC record: `S027_MOTION_HUMAN_QC_RECORD_v1.json` (full checklist plus advisory observations).
- Advisory flags from 4 sampled frames:
  - Mikko's fur reads darker / less saturated after t=0.
  - Mikko drifts slightly to screen-right.
  - Lumi's open-mouth laugh settles into a closed smile.
- The candidate is not composited, not registered as a production video, and has not replaced the base frame. The shot is not approved.
- **The provider copy expires on 2026-10-17.** If approved, preserving the exact bytes needs its own authorised storage task before that date.

## 7. Counts and safety
- Seedance generations: 1. Generation attempts: 1. Automatic retries: 0. Fallback: none.
- Source uploads: 1. Image generations: 0. Generated audio: none.
- Not touched: ElevenLabs, Agent-006, Agent-007, Agents 001–007 (no changes).
- Writes: compositor 0, render 0, registry 0, production storage 0, manifest/readiness 0, canon 0.
- Billing: no changes. Anime Clip Farming: untouched.

Rollback: revert the evidence commits. The provider-side input, output and spend cannot be reversed.
