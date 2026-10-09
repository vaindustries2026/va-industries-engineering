# EP005 S027 base frame: Flare generation completed, output retrieval blocked by egress policy

Date: 2026-10-09. Mikko & Lumi only.
**Result: STOPPED_OUTPUT_CDN_EGRESS_BLOCKED.**
- The single authorised Flare generation was submitted and completed.
- The original output cannot yet be downloaded or hashed: its host `d3u0tzju9qaucj.cloudfront.net` is not in the environment's allowed domains.

## Sequence
1. **Pre-POST checks** against `GENERATION_PACKAGE_v2.json`: 12/12 PASS.
   - body SHA-256 `13af2150…99d1`
   - prompt SHA-256 `d24d0bab…e2d9`
   - 5 `image_urls` equal to the verified references, and all 5 return HTTP 200
   - 16:9, 2k, high, `enhance_prompt=false`, generation count 1
2. **Ledger entry before the POST:** `GENERATION_RESERVED` written to `s027_base_frame/GENERATION_LEDGER_v1.jsonl`.
3. **One POST** of the exact frozen bytes (compact sorted-key JSON, 2,802 bytes) at 06:01:46Z.
   - No preset, no retry. The auth header was injected by the proxy for `api.higgsfield.ai` only.
   - Response: HTTP 200 `queued`, request_id **`0d6997fe-6c53-487e-8477-242e60c80c75`**.
4. **Polling:** 4 GETs on `/requests/{id}/status`, ending in `completed` at 06:02:24Z with 1 image:
   `https://d3u0tzju9qaucj.cloudfront.net/b253ddaf-db92-485d-a71c-c161961cb73b/a943a133-cbcb-4fee-875c-63f2f995a6dd.png`
5. **Download:** `GET` was refused by the environment proxy (`CONNECT 403`, policy) on 2 attempts.
   - The output CDN host is different from the upload CDN host `d3snorpfx4xhv8.cloudfront.net`, which is already allowed.
   - I did not use any workaround: no other host, no MCP import, no proxy bypass.

## Not yet available
Output SHA-256, byte size, content type and dimensions are not recorded. FRAME-EP005-S027-BASE-v01 stays **REVIEW**. Human QC is pending: `HUMAN_QC_RECORD_v1.json` holds the checklist, and no decision has been made.

## Cost
- Neither the submit response nor the status response reports a cost.
- API balance: $5.00 before (Company Brain). The after-balance is not readable through the routes used.
- The MCP workspace is a separate account: unchanged at 10 credits, with no Marketing Studio generations listed.

## To unblock (human)
- Add `d3u0tzju9qaucj.cloudfront.net` to Allowed domains (Network access).
- Then the only actions needed are read-only:
  - `GET` the recorded output URL
  - hash and measure it unchanged
  - show it to Gilang

No new generation is needed or authorised. The single authorised attempt is consumed.

## Counts
- Flare generations: 1. Generation attempts: 1. Automatic retries: 0.
- Seedance posts: 0. Video generations: 0.
- Writes: 0 registry, 0 production storage, 0 manifest/readiness, 0 canon, 0 n8n.
- Agent runs: Agent-006 0, Agent-007 0. Agent-008 transport changes: 0.
- Billing: no changes.

Rollback: revert this commit. The provider-side output cannot be deleted through the API.
