# EP005 S027 — five reference uploads verified by CDN readback (generation NOT submitted)

Date: 2026-10-09. Mikko & Lumi only. Authorised by Company Brain: exactly 5 fresh reference uploads, with no generation.
**Result: EP005_S027_REFERENCE_UPLOADS_VERIFIED.**

## Reconciliation
- The `d3snorpfx4xhv8.cloudfront.net` CDN is now reachable. `GET /` returns an S3 `AccessDenied` from CloudFront (not a proxy denial), so the egress block is cleared.
- The batch-1 `CHAR-MIKKO-MASTER-v01` upload (`UPLOAD_LEDGER_v1.jsonl`) is treated as a **failed/orphaned provider input**: its public URL was never captured. It was not reused.
- Upload attempts:
  - historical: 1
  - this batch: 5 (cap 5)
  - all-time: 6
- Each reference was checked three ways and all agreed:
  - live `asset_registry`: status APPROVED, `metadata_json.sha256` (read-only GET)
  - V&A storage bytes (read-only download)
  - repo `canon/c1` bytes (C1 canon)

## Uploads (official flow: `POST /files/generate-upload-url`, then a PUT of the exact bytes)
How each upload was made:
- **Storage PUT:** sent to `fnf-api-input-prod-…s3.amazonaws.com` with only the returned `upload_headers`.
- **No credential on the PUT:**
  - `_storage_put` refuses any API or proxy-injected host.
  - The proxy injects credentials for `api.higgsfield.ai` only.
- **Readback:** an unauthenticated `GET public_url`. Readback ran after the `public_url` was ledgered, so a failed readback could not lose the URL.

| # | Asset | Bytes | Approved SHA-256 = readback SHA-256 | public_url |
|---|---|---|---|---|
| 1 | CHAR-MIKKO-MASTER-v01 | 2,207,008 | `41c9480a…1f1a8` ✓ | https://d3snorpfx4xhv8.cloudfront.net/b253ddaf-db92-485d-a71c-c161961cb73b/025418b7-5693-4e04-8859-0513ce660da1.png |
| 2 | CHAR-LUMI-MASTER-v01 | 1,887,897 | `8b29c1ab…c43a41` ✓ | https://d3snorpfx4xhv8.cloudfront.net/b253ddaf-db92-485d-a71c-c161961cb73b/938ce2f7-0f99-4020-b67c-783cda0b3ea4.png |
| 3 | WORLD-EP005-BATHROOM-MASTER-v01 | 1,756,516 | `ab79c560…3bd3733` ✓ | https://d3snorpfx4xhv8.cloudfront.net/b253ddaf-db92-485d-a71c-c161961cb73b/1f631ac5-56d0-4869-9587-d94b451ee5c9.png |
| 4 | PROP-EP005-HAND-MIRROR-v01 | 47,670 | `34fa31a1…b9c56ac` ✓ | https://d3snorpfx4xhv8.cloudfront.net/b253ddaf-db92-485d-a71c-c161961cb73b/d7da1cda-b974-4ac1-9f6b-f8ba936ce516.webp |
| 5 | PROP-EP005-CLEANING-CLOTH-v01 | 237,724 | `afaa3a9f…37c1db` ✓ | https://d3snorpfx4xhv8.cloudfront.net/b253ddaf-db92-485d-a71c-c161961cb73b/6d186991-ae32-4b92-8737-b904b93e27dd.webp |

All five readbacks returned HTTP 200, with byte counts and content types identical to the source.

Provenance records:
- `evidence/ep005/s027_base_frame/UPLOAD_LEDGER_v2.jsonl` (15 append-only events: RESERVED, then UPLOADED, then READBACK_SHA256_MATCH, ×5)
- `evidence/ep005/s027_base_frame/REFERENCE_UPLOADS_READBACK_v2.json`

Signed upload URLs are not recorded.

## Generation package (prepared, NOT submitted)
`evidence/ep005/s027_base_frame/GENERATION_PACKAGE_v2.json` (supersedes v1):
- Flare `POST https://api.higgsfield.ai/marketing-studio/image/flare`, DIRECT (no preset field)
- prompt SHA-256 `d24d0bab…70e2d9`, unchanged
- `image_urls` = the 5 verified URLs above, in reference order
- 16:9, 2k, high quality, `enhance_prompt=false`, 1 generation
- exact request body SHA-256 `13af2150d3ca8413d050505e5fc1db38d80ab854131f03deb3083cad3a2899d1` (compact, sorted-key JSON)

## Counts
- Uploads: 5. Readback matches: 5.
- Image generations: 0. Video generations: 0. Generation POSTs: 0.
- Credits: balance read-only via MCP was 10 (free plan) before and 10 after.
- Writes: 0 registry, 0 storage, 0 manifest, 0 canon, 0 n8n.
- Agent runs: Agent-006 0, Agent-007 0.
- Billing: no changes.

## Rollback
- Revert this commit.
- The provider-side inputs cannot be deleted through the official API. They are temporary provider inputs: copies of approved bytes under unguessable UUID paths.

## Stop
Do not generate `FRAME-EP005-S027-BASE-v01` until Company Brain separately authorises the paid Flare POST, against the package's body SHA-256.
