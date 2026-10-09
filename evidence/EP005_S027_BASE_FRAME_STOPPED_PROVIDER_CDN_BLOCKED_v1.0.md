# EP005 S027 base frame — STOPPED before generation (provider CDN blocked by egress policy)

Date: 2026-10-09. Mikko & Lumi only. Target `FRAME-EP005-S027-BASE-v01` (shot-specific production input, REVIEW only).
**Result: STOPPED_PROVIDER_CDN_EGRESS_BLOCKED.**

Counts:
- Higgsfield image generations **0**; paid generation POSTs **0**; credits spent by generation **0**
- Reference uploads **1 of 5 attempted** (completed; readback impossible); video generations 0

## 1. What was done
1. **References resolved and reconciled (read-only).**
   - The live `asset_registry` GET matches the repo snapshot and the local bytes.
   - All five rows are APPROVED, with identical SHA-256: Mikko `41c9480a…a8`, Lumi `8b29c1ab…41`, Bathroom `ab79c560…33`, Hand mirror `34fa31a1…ac`, Cleaning cloth `afaa3a9f…db`.
   - The props were downloaded read-only from V&A storage (webp; 47,670 and 237,724 bytes; SHA match). No writes.
2. **Model contract.**
   - Flare endpoint and fields as given by Company Brain.
   - The `docs.higgsfield.ai` host is egress-blocked here, and `GET /openapi.json` returned 405.
   - DIRECT mode is interpreted as **no preset field**: a third-party summary of the docs says presets are applied via a preset id. This interpretation is recorded in the package.
3. **Upload 1 (CHAR-MIKKO-MASTER-v01) via the official flow** (`stage_source_frame`; local SHA verified; human-approved per-reference UploadAuthorisation):
   - `POST /files/generate-upload-url` → PUT of the exact bytes (only `upload_headers`; no API credential) completed.
   - The readback `GET public_url` on `d3snorpfx4xhv8.cloudfront.net` was **refused by the environment egress proxy** (`CONNECT 403`, policy denial; proxy log 05:50:41Z and 05:50:58Z).
   - The flow failed closed: ledger `UPLOAD_RESERVED` → `UPLOAD_FAILED HTTP_TRANSPORT_ERROR`; `public_url` was not recorded. See `evidence/ep005/s027_base_frame/UPLOAD_LEDGER_v1.jsonl`.
   - Note: the Mikko master sheet bytes now sit at a provider CDN URL as a temporary provider input. The URL was not captured because the flow stops before returning it.
4. Uploads 2-5 were not attempted. The generation package was prepared and **not submitted**: `evidence/ep005/s027_base_frame/GENERATION_PACKAGE_v1.json` (prompt SHA-256 `d24d0bab891cd9ea0eece2039f3980b989e8fc2d0c890d5f43c05dabfa70e2d9`, 2,102 chars).

## 2. Why generation was not run
Higgsfield serves uploaded and generated media from its CDN (`*.cloudfront.net`), which this environment cannot reach. Spending the single authorised generation now would:
- prevent downloading the ORIGINAL output unchanged, hashing it and presenting it for review (required by the task);
- leave the reference readback unverifiable.

The attempt would be consumed with no reviewable result, so it was not spent.

## 3. To unblock (human)
- Add `d3snorpfx4xhv8.cloudfront.net` to the environment's allowed domains (Network access → Allowed domains). If Higgsfield uses more than one CDN host, add those too.
- Then re-run: the remaining uploads with readback, and the single Flare generation from the recorded package.
- The Mikko reference needs a fresh upload. Its per-reference upload authorisation is consumed by the failed attempt, so a new human authorisation is needed for that one reference (still within the 5-upload cap if counted as the 2nd of 6, so Company Brain should confirm the cap).
- Balance (read-only MCP): 10 credits, free plan. Flare cost is not exposed. If insufficient, the API returns 403 and the run stops without charge.

## 4. Not done / unchanged
No image or video generation. No Seedance POST. No registry, storage, manifest, readiness or C1 canon writes. ElevenLabs, Agent-006 and Agent-007 not run. No purchases or billing changes. The revised S027 motion prompt (negative constraints folded in) is deferred until the base frame exists, per the task. The Agent-008 transport is unchanged.
