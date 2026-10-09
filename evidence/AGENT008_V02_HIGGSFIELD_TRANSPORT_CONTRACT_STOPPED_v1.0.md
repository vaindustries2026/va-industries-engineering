# AGENT-008 v0.2 — Higgsfield transport: official API contract check (STOPPED before code)

Date: 2026-10-09. Mikko & Lumi only. **Result: STOPPED_OFFICIAL_API_CONFLICTS_WITH_AGENT008_ASSUMPTIONS** (task Step 1 stop rule).
Code changes: **0**. Live Higgsfield calls in this task: **0** (the one allowed GET was not needed). POSTs: 0. Generations: 0. Credits: 0. Uploads or signed URLs: 0.

Authentication was verified earlier the same day: `GET https://api.higgsfield.ai/marketing-studio/image/presets?size=1` returned HTTP 200 with the preset-catalogue shape `{total, cursor, items[{id, type, name, cover_image, metadata, format_slugs}]}`. Credential injection by the environment proxy works; the credential was never read.

## 1. Sources and access limits
| Source | Status |
|---|---|
| `docs.higgsfield.ai` (official docs) | **Blocked by this environment's egress policy** (`CONNECT 403`). Pages could not be read directly. Only search-engine excerpts of official pages were available. |
| Official SDK `@higgsfield/client` 0.2.6 (npm; repo `github.com/higgsfield-ai/higgsfield-js`, published 2026-09-17) | Read in full (`dist/v2/client.js`, `dist/v2/types.d.ts`, `dist/config.js`, README). Published by Higgsfield; not an unofficial wrapper. |
| Third-party wrappers or blogs (Segmind, Apidog, Scribd copy, GitHub PRs in other projects) | **Not used** for the contract. |

## 2. Contract that IS confirmed (official SDK source plus official docs excerpts)
| Item | Official contract |
|---|---|
| Base URL | `https://api.higgsfield.ai` |
| Auth | `Authorization: Key <KEY_ID>:<KEY_SECRET>`, injected by the environment proxy. Agent-008 must not construct it. |
| Submit | `POST /<model-endpoint-id>` with a JSON body of the model's inputs (not wrapped). Optional `?hf_webhook=<url>`. Docs examples also send an optional `Idempotency-Key` header. |
| Submit response | `{status, request_id, status_url, cancel_url}` |
| Status polling | **`GET /requests/{request_id}/status`** (SDK `pollV2Request`; docs `status_url` example `https://api.higgsfield.ai/requests/<uuid>/status`) |
| Status values | `queued`, `in_progress` (cannot cancel), `completed`, `failed` (credits refunded), `nsfw` (moderation reject, credits refunded); `canceled` in SDK job handling |
| Completed output | `video.url` (video models) / `images[].url` |
| Cancel | `cancel_url` = `/requests/{request_id}/cancel` (not used by Agent-008) |
| Errors | 401 invalid credentials · 403 **not enough credits** · 400 bad input · 422 validation (`detail`) · 5xx (the SDK keeps polling) |
| SDK retry behaviour | The SDK's `subscribe` **retries the POST up to 3 times with backoff**. Agent-008 must NOT reuse that behaviour (no automatic retry); a direct single POST is required. |

**Status-route correction (Step 8):** the documented current route is exactly `/requests/{request_id}/status`. The earlier probe `GET /requests/VA_AUTH_TEST_DO_NOT_EXIST/status` → `404 {"detail":"Not Found"}` is consistent with an unknown request id on that route. It does not show the route is wrong, and it was not an auth signal either way.

## 3. Material conflicts with Agent-008 assumptions (reason for STOP)
**C-1. The source image must be a public HTTPS URL, not a local file.**
Agent-008's `MotionRequest` carries `source_frame_path` + `source_frame_sha256` and assumes the provider takes the hashed local frame. The official API takes `image_url` (a publicly reachable HTTPS URL; `asset://` refs rejected on at least Seedance 2.5). Local media needs the official 3-step upload: `POST https://platform.higgsfield.ai/files/generate-upload-url {content_type}` → `PUT upload_url` with `upload_headers` → pass `public_url`.
This adds a new stage that this task forbids (no uploads, no signed upload URLs). It also leaves open decisions that are not engineering's to make:
- (a) Who hosts the approved frame: the Higgsfield upload, or a V&A-owned public URL such as Supabase storage?
- (b) How is the hosted bytes' SHA-256 bound to the approved frame SHA? For example, re-download it and verify before submit.
- (c) Is the upload part of the single paid authorisation, or a separately authorised step?
- (d) The upload uses `platform.higgsfield.ai`, a host that is not in this environment's proxy injection list.

**C-2. The primary model's API endpoint and schema cannot be verified.**
`seedance_2_0` / `kling3_0` are MCP/web-app catalogue ids, not API endpoint ids.
- Kling 3.0 Standard image-to-video: docs excerpt gives `POST /kling-video/v3.0/std/image-to-video`, with `prompt` (required; truncated past 2,500 chars), `image_url` (first frame), optional `last_image_url`, `duration`, `sound` (default **on**; Agent-008 needs off), `elements`, `multi_shots`/`multi_prompt`. The full parameter table (duration range, aspect ratio, resolution, negative prompt) could not be read.
- **Seedance 2.0 image-to-video: no official page found.** `bytedance/seedance-2.0/image-to-video` is only inferred from the `seedance-2.0/text-to-video` and `seedance-2.5/image-to-video` naming. Third-party sources also say Seedance 2.0 API access may be gated (business verification; region exclusions). The recommended primary cannot be wired to a documented contract.

**C-3. Agent-008's capability catalogue does not match the API schema.** `higgsfield_video_models_2026-10-09.json` comes from the MCP catalogue (model names, `resolutions`, `media_roles`). API request fields are named differently (`image_url`, `last_image_url`, `sound`), and per-model resolution and aspect fields are unverified. `validate_request` would pass requests whose real field names and values have not been confirmed.

**C-4. Cost is still unknown.** The API returns 403 on insufficient credits. The account was on the free plan with 10 credits at the last read. There is an estimate endpoint (mentioned in third-party notes, not verified here).

Not conflicts (already compatible): the read-only poll loop, the terminal-state mapping (`completed`→COMPLETED; `failed`/`nsfw`/`canceled`→FAILED), raw fetch from `video.url`, one-submit-no-retry ledger, and the spend gate.

## 4. Proposed resolution (for Company Brain / human decision; not implemented)
1. **Allow egress to `docs.higgsfield.ai`** (read-only), so the Seedance 2.0 and Kling 3.0 image-to-video schemas can be verified verbatim. Alternatively, a human pastes those two pages.
2. **Decide the source-image hosting route (C-1).** Recommended: a separately authorised step that uses the official `generate-upload-url` flow for the human-approved frame only, followed by a read-back GET and SHA-256 match before submit. Record `public_url` + SHA in the ledger. This also needs `platform.higgsfield.ai` added to the credential injection.
3. **Decide the model id mapping.** Recommended: an explicit config map, e.g. `kling3_0 → kling-video/v3.0/std/image-to-video` (docs-confirmed path). Promote `seedance_2_0` only once its i2v page is verified and access is confirmed. Model selection stays configurable either way.
4. Then implement the transport as specified, behind `MotionGenerationProvider`:
   - single POST with `Idempotency-Key = approval_scope_id:attempt_number` and no SDK retry
   - poll `GET /requests/{id}/status`
   - fetch `video.url`
   - tests T-A008-HF01…HF13

## 5. Preserved / unchanged
Agent-008 code is unchanged (Phase 0 compositor `8ea0776`, Phase 1 motion layer `f0e8e43`, 54 tests). These remain in place:
- the S027 blocker: `FRAME-EP005-S027-BASE-v01` does not exist, and no fake frame was created
- the spend gate, which still fails closed (`PROVIDER_CREDENTIAL_MISSING` until a transport is injected)
- model recommendation unchanged (seedance_2_0 primary, kling3_0 fallback), with the C-2 caveat

## 6. Counts
Higgsfield live calls 0 · POSTs 0 · generations 0 · credits 0 · uploads/signed URLs 0 · ElevenLabs 0 · Agent-006 0 · Agent-007 0 · Agents 001-007 modified 0 · Agent-008 code modified 0 · Supabase/storage/registry writes 0 · manifests/readiness 0 · migrations 0 · n8n 0 · billing 0 · credential read/printed/stored 0.
