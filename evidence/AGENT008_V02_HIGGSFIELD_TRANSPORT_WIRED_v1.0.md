# AGENT-008 v0.2 — Official Higgsfield transport WIRED (zero spend)

Date: 2026-10-09. Mikko & Lumi only.
**Result: AGENT008_HIGGSFIELD_TRANSPORT_WIRED.** Transport implementation only. Nothing was exercised live.

Counts: live Higgsfield calls in this task **0** (the one allowed GET was not needed; auth was already proven) · POSTs 0 · uploads 0 · signed-upload requests 0 · generations 0 · credits 0.

Authorisation: Company Brain's task resolves/waives the C-1 and C-2 conditions and the status-route condition from `AGENT008_V02_HIGGSFIELD_TRANSPORT_CONTRACT_STOPPED_v1.0.md`, for implementation only.

## 1. Official contract used
Sources:
- Company Brain's verification of docs.higgsfield.ai (2026-10-09). This environment cannot reach that host (egress-blocked).
- The official SDK `@higgsfield/client` 0.2.6 source (`v2/client.js`, `client.js`, `v2/types.d.ts`).

| Purpose | Method + path (base `https://api.higgsfield.ai`) | Request | Response used |
|---|---|---|---|
| Source upload prep | `POST /files/generate-upload-url` | `{"content_type": "image/png"}` | `upload_url`, `upload_headers`, `public_url` |
| Source upload | `PUT <upload_url>` (storage host) | exact bytes; **only** `upload_headers` | 2xx |
| Image-to-video submit | `POST /bytedance/seedance-2.0/image-to-video` | `prompt`, `image_url` (required), `duration` (4-15), `resolution` (480p/720p/1080p/4k), `end_image_url` (not used), `generate_audio` (false) | `request_id`, `status_url`, `cancel_url`, `status` |
| Status polling | `GET /requests/{request_id}/status` | — | `status` ∈ queued, in_progress, completed, failed, nsfw, canceled; `video.url` when completed |
| Output retrieval | `GET <video.url>` | no API credential | video bytes |
| Errors | — | — | 401 auth rejected · 403 insufficient credits/forbidden · 400/422 bad input · 5xx server |

Corrections to the earlier STOP note:
- The upload-URL route is on `api.higgsfield.ai`, not `platform.higgsfield.ai`. This matches the Company Brain contract and the official SDK v1 client, `client.post('/files/generate-upload-url')` on base `https://api.higgsfield.ai`.
- The earlier `404 {"detail":"Not Found"}` on `/requests/VA_AUTH_TEST_DO_NOT_EXIST/status` is consistent with an unknown id on the documented route.

Deliberate difference from the SDK: the SDK retries a failed submit POST up to 3 times with backoff. Agent-008 sends every request exactly once.

## 2. Implementation
| File | Content |
|---|---|
| `agent008/motion/http.py` | `HttpClient` (single send, no retry; proxy and CA from the environment) and the auth boundaries. `EnvironmentProxyAuth` is for Claude cloud (proxy-injected network secret; app adds no header; `HF_CREDENTIALS` never read). `SuppliedHeaderAuth` is for future n8n or other runtimes: a supplier returns the header at send time, only for the API host, and the value is never stored. Also `redact()`. |
| `agent008/motion/higgsfield_transport.py` | `HiggsfieldApiTransport`: `prepare_source_upload`, `submit`, `poll`, `retrieve`. `serialize_request` maps the provider-neutral `MotionRequest` to the official body. State normalisation, plus fail-closed on malformed responses, unexpected `status_url`, non-https URLs and bad request ids. |
| `agent008/motion/higgsfield_api_models.json` | Explicit model config (not canon). Primary `bytedance/seedance-2.0/image-to-video` (alias `seedance_2_0`, VERIFIED, `generate_audio` fixed false). Fallback `kling-video/v3.0/std/image-to-video` (alias `kling3_0`, PARTIAL, `submit_enabled:false`). |
| `agent008/motion/higgsfield.py` | `HiggsfieldProvider`, now backed by the transport. `require_paid_authorisation`. A one-shot `bind_authorisation`, consumed by a single submit. `submit` requires `source_frame_url`. `capabilities` resolves official ids and aliases. |
| `agent008/motion/source_upload.py` | `SourceFrame`, `UploadAuthorisation`, `check_source_frame` (checks 1-4), `stage_source_frame` (checks 5-6 and exactly one upload, ledger-reserved first), `bind_request_to_upload` (check 7). |
| `agent008/motion/{provider,contracts,authorisation,runner,preflight}.py` | Minimal provider-neutral hooks; existing behaviour unchanged for providers that do not opt in. See CONTRACT §14 and §19. |
| `agent008/motion/jobs/ep005_s027_motion_smoke_v1.json` | Model set to the official id. Params: duration 5, resolution 1080p, generate_audio false, image_url = staged public_url (not yet created). Blockers: `STOPPED_BASE_FRAME_REQUIRED_BEFORE_MOTION`, `SOURCE_UPLOAD_NOT_AUTHORISED`, `GENERATION_NOT_AUTHORISED`. Prompt and SHA unchanged (`9850…a8`). |
| `agent008/CONTRACT.md` | §14 updated, §18 updated, §19 added (official transport). |

SHA-256: `higgsfield_transport.py` `4d1b4181fd3e255a4c2b6e659bf3def8b2f866bb06008eaa34d0f031162a6de5`; `higgsfield_api_models.json` `30bdcb094af3ee74267ca7063e8df4104848e9f5a1e93ee3e09b1cc29a7904fc`.

## 3. Safety properties
- **Auth header never reaches storage.** The PUT carries only `upload_headers`. An `upload_url` on an authenticated API host is refused before any PUT (`UPLOAD_URL_WOULD_RECEIVE_PROVIDER_AUTH`), which also covers proxy-injected credentials. Readback and output downloads send no auth header. Regression tests: `HF_Security_NoAuthLeakToStorage` (3 tests).
- **Credential never exposed.** Error bodies are redacted, logs carry method and path only, and reprs omit secrets (HF02).
- **Spend gate.** Requires an explicit `SpendAuthorisation` bound to provider HIGGSFIELD, shot_id, provider_model, source_frame_sha256 and prompt_sha256, with `max_generations == 1` and `human_approved is True`. Otherwise it fails closed. The attempt is reserved before submit. A failed or errored submit, or a provider `failed`/`nsfw`/`canceled`, consumes the attempt. No retry path exists.
- **Upload gate.** A separate human-approved `UploadAuthorisation` bound to frame id, SHA and content type, max 1 upload.
- **S027 blocker preserved.** `FRAME-EP005-S027-BASE-v01` does not exist; no frame was created. Tests use a synthetic, clearly named fixture PNG in a temp dir only.

## 4. Open item for Company Brain (not decided here)
The verified Seedance 2.0 schema has **no negative-prompt field**. The S027 `negative_constraints` (SHA `02d94319…1495`) are recorded but **not transmitted**. The motion prompt already states the locked camera and unchanged background. Folding the constraints into the prompt would change `prompt_sha256` and needs new human approval.

## 5. Preflight (offline, no network): `evidence/agent008/phase1_transport/S027_PREFLIGHT_v2.json`
- **PASS:** shot contract (120 frames), approved video shot, manifests APPROVED, model capability, prompt SHA, duration/resolution, `model_official_contract` = `bytedance/seedance-2.0/image-to-video`, `provider_credentials` (transport wired, auth boundary declared), paid generations so far = 0.
- **FAIL:** `SOURCE_FRAME_MISSING` · `SOURCE_URL_MISSING` · `SPEND_AUTHORISATION_MISSING`.
- `ready_for_paid_call: false`.

## 6. Tests: 84/84 pass (`python3 -m unittest discover -s agent008/tests -t .`)
Full log: `evidence/agent008/phase1_transport/TEST_RESULTS_v1.txt`. The 54 existing tests (37 Phase-0 + 17 motion) are unchanged and pass. 30 new tests, all mocked (`MockHttp`; no sockets):

| Test | What it checks |
|---|---|
| HF01 | Auth configuration (proxy boundary without env var; supplied header only for the API host; undeclared boundary fails closed) |
| HF02 | Secret not in exception, logs, repr or ledger |
| HF03 | Seedance body exactly `{prompt, image_url, duration:int, resolution, generate_audio:false}`; POST URL, Idempotency-Key, no app-set Authorization; public_url propagation |
| HF04 | Explicit model config; Kling disabled; unknown model refused; zero HTTP |
| HF05 | Hosted source required; missing frame rejected before upload |
| HF06 | SHA missing, mismatch, unapproved status, content-type invalid or mismatched; readback mismatch; request/upload binding |
| HF07 | Missing, unapproved or mismatched spend authorisation; direct submit refused; authorisation single-use; missing or unapproved upload authorisation |
| HF08 | Attempts > 1 refused; second upload refused |
| HF09 | failed/nsfw/canceled, submit 500/403, network error and upload PUT failure: exactly one request, counted, no retry |
| HF10 | Polling GET is exactly `https://api.higgsfield.ai/requests/<id>/status`; state mapping; 5xx keeps read-only polling; unexpected status_url or bad request_id refused |
| HF11 | `video.url` extraction; malformed responses; signed-upload response parsing |
| HF12 | End-to-end mocked staged → submit → poll → retrieve: raw SHA = served bytes, read-only, source_upload in `MOTION_RESULT.json`, ledger `UPLOAD_RESERVED, UPLOADED, RESERVED, SUBMITTED, COMPLETED` |
| HF13 | Compositor has no Higgsfield dependency and composes both Higgsfield-mocked and fake-provider results (auto-QC PASS) |
| Security | Storage PUT uses only `upload_headers`; API-host `upload_url` refused; output download unauthenticated |
| No-network guard | Test fails if a socket is opened |

## 7. Counts
Higgsfield live calls 0 · POSTs 0 · uploads 0 · signed URLs 0 · generations 0 · credits 0 · cancel calls 0 · ElevenLabs 0 · Agent-006 0 · Agent-007 0 · Agents 001-007 modified 0 · Supabase/storage/registry writes 0 · manifests/readiness 0 · migrations 0 · n8n 0 · C1 canon 0 · billing 0 · credential read/printed/stored 0.

## 8. Next (requires Company Brain / human authorisation)
1. Create and approve `FRAME-EP005-S027-BASE-v01` by SHA-256 (separate authorisation).
2. Authorise one source upload (`UploadAuthorisation`, human_approved, max 1).
3. Decide the negative-constraints handling (§4).
4. Authorise one Seedance 2.0 generation (`SpendAuthorisation`, human_approved, max 1), then run `stage_source_frame` → `bind_request_to_upload` → `run_once`.

Rollback: revert this commit. The previous adapter fails closed without a transport.
