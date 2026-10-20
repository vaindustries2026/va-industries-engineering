# EP005 Batch 1 — Base Frame Provider Pre-Submit (F01, F03, F09)

**Status:** READY TO SUBMIT, NOT SUBMITTED.
- Zero image or video generations, zero spend, zero production writes.
- The only provider writes were six transport-only reference uploads.

**Machine-readable evidence** is in `evidence/ep005/batch1_base_frames/`:
- `B1_PRESUBMIT_RECORD_v1.json`: auth, model, references, cost, ledger, normalisation, handoff.
- `B1_GENERATION_PACKAGES_v1.json`: the exact prompts and request bodies.
- `B1_REFERENCE_UPLOAD_LEDGER_v1.jsonl`
- Scripts:
  - `b1_reference_uploads.py`
  - `build_b1_packages.py` (deterministic: two runs give identical output)
  - `b1_normalisation_proof.py`

## 1. Auth
**HIGGSFIELD_AUTH_STATUS = VERIFIED**
- Probe: one read-only call, `GET /requests/0d6997fe-…/status` (the S027 request).
- Result: HTTP 200, `completed`.
- The `Authorization: Key …` header is injected by the environment proxy. The credential was never read, printed or stored.

## 2. Provider / model
- **IMAGE_PROVIDER:** Higgsfield (`api.higgsfield.ai`).
- **IMAGE_MODEL:** Marketing Studio Image 2.5 Flare, `POST /marketing-studio/image/flare`, DIRECT mode (S027 precedent).
- **MODEL_AVAILABILITY:** ROUTE_PROVEN_BY_PRECEDENT; LIVE_AVAILABILITY_NOT_PROVABLE_READ_ONLY.

Evidence:
- The route served S027 on 2026-10-09.
- The account still authenticates and still serves that record today.

It cannot be re-proved read-only because:
- The API has no catalogue route.
- `docs.higgsfield.ai` is egress-blocked.
- GET on the route is non-discriminating.
- Any POST is a generation.

The Higgsfield MCP catalogue is a separate workspace. It lists "GPT Image 2.5" with a `flare` variant. That is corroboration only, not proof.

At submit, a 404/410/422 means STOP. There is no substitute model and no retry.

## 3. References
All six were SHA-verified before upload. Each was uploaded once through the bounded transport and read back with a SHA-256 match. The public URLs are unsigned. The signed `upload_url` is never recorded.

| n | ASSET_ID | SOURCE_SHA | REMOTE_REFERENCE_STATUS | REMOTE_READBACK_STATUS |
|---|---|---|---|---|
| 1 | CHAR-MIKKO-MASTER-v01 | 41c9480a…1f61a8 | FRESH_TRANSPORT_COPY | SHA256_MATCH |
| 2 | CHAR-LUMI-MASTER-v01 | 8b29c1ab…3c43a41 | FRESH_TRANSPORT_COPY | SHA256_MATCH |
| 3 | WORLD-EP005-BATHROOM-MASTER-v01 | ab79c560…bd3733 | FRESH_TRANSPORT_COPY | SHA256_MATCH |
| 4 | PROP-EP005-HAND-MIRROR-v01 | 34fa31a1…9c56ac | FRESH_TRANSPORT_COPY | SHA256_MATCH |
| 5 | PROP-EP005-CLEANING-CLOTH-v01 | afaa3a9f…37c1db | FRESH_TRANSPORT_COPY | SHA256_MATCH |
| 6 | DUO-MIKKO-LUMI-SCALE-v01 | 735d6407…121f | FRESH_TRANSPORT_COPY | SHA256_MATCH |

Findings:
- **Expired S027 copies:** the old S027 transport copies had expired (CloudFront 403).
- **Free upload:** the upload is classified free under the governed S028 evidence. The S027 uploads left credits unchanged.
- **New copies expire 2026-10-28 00:00 GMT** (S3 rule "Delete after 7 days"). Before submit, HEAD-check all six URLs. A re-upload changes every body hash, so the packages would have to be re-locked and re-approved.
- **DUO-MIKKO-LUMI-SCALE-v01 has no asset_registry row.** It is governed only by its CLAUDE.md C1 canon hash.

## 4–6. Locked packages
Each package uses the audited brief plus **one inserted sentence** that binds reference image 6 (the duo scale sheet):

> "Mikko and Lumi keep exactly the relative sizes shown in reference image 6 (scale reference only: do not copy its layout, poses, labels or background)."

There is no other wording change. The body keys are identical to S027: `prompt`, `image_urls` (6), `aspect_ratio` 16:9, `resolution` 2k, `quality` high, `enhance_prompt` false. Count is 1.

| Family | Shots | PROMPT_SHA256 | REQUEST_BODY_SHA256 |
|---|---|---|---|
| F01-MIRROR-OPEN | S001, S005, S013, S025 | 559d3ba7b0c9ed9023df8376cdcd160b9047578418fb55bd492fdf155804cf97 | 008adeb425bc0edea374a0b8ac6e2b09decd485db2df4d56a71f62992ac3421c |
| F03-OVERSHOULDER-LUMI | S004, S012 | c51d9670c8065c587a06ade5470e2908a3439bd88c64d742cc44e7e06cc9446f | d86ec189aa6c3af3eecbfad88c780b8b40a3cab1076125dc5b6db329654b8411 |
| F09-MEDIUM-TWOSHOT-MIRROR-FRONT | S017 (+ F15 source for S019/S018) | 5bd2edc1364a1c4f5187fbe5d515c06fe19131294b13aa967a34ba4e04a12abd | 36d91d95cf72825ccfa9d526870b34d92ae0b3a103f1cef3ba229dd1494893cc |

Body hash convention: SHA-256 of compact JSON with sorted keys (the S027 convention).

Live reconciliation (read-only):
- Manifest 0325d35c and readiness 69bff641 are both APPROVED.
- The camera setups for all 8 member shots equal the preflight evidence.
- No F01/F03/F09 frame exists in the registry.

## 7. Normalisation plan
1. **Preserve the raw output.** Download it once and record its SHA, bytes and dimensions. Run no G03/G08 on the raw image.
2. **Crop.** Take the largest exact centred 16:9 crop. For 2688×1520 that is `{x:0, y:4, w:2688, h:1512}`. If more than 2% of either axis would be trimmed, STOP.
3. **Scale.** G04 `derive_frame` scales to 1920×1080 (lanczos, bitexact). Run it twice; the outputs must be byte-identical.
4. **REVIEW candidate.** A human approves the exact normalised SHA. G03/G08 measure only that approved frame.

Synthetic proof:
- Two runs gave the same output, `69e28878…c48c`.
- The source was unchanged.

**Open decision (before normalisation runs).** The unchanged G04 accepts only APPROVED/LOCKED sources. A REVIEW raw is refused with `DERIVE_SOURCE_NOT_APPROVED` (proven). Options:
- **A (recommended):** record the preserved raw as LOCKED (a byte-pinned provider original, not a creative approval), for normalisation only.
- **B:** a human approves the raw SHA first, then the normalised SHA.

Neither option needs a code change.

## 8. Cost (read-only)
- COST_PER_CALL = UNKNOWN
- TOTAL_COST_FOR_3_CALLS = UNKNOWN
- CREDITS_PER_CALL = UNKNOWN
- TOTAL_CREDITS_REQUIRED = UNKNOWN
- CURRENT_API_BALANCE = UNKNOWN

COST_INFORMATION_SOURCE = none available:
- The API has no price or balance route.
- The docs are blocked.
- The S027 responses carried no cost.

Nothing was inferred from browser-plan credits, the MCP connector or Seedance costs.

## 9. Attempt ledger

| Field | Value |
|---|---|
| F01_ATTEMPT_MAX | 1 |
| F03_ATTEMPT_MAX | 1 |
| F09_ATTEMPT_MAX | 1 |
| TOTAL_IMAGE_GENERATION_MAX | 3 |
| RETRIES | 0 |
| ALTERNATE_CANDIDATES | 0 |
| FALLBACK_MODEL | NONE |
| Attempts used | 0 / 0 / 0 |

Each call is independent. Every returned raw output is preserved, even if it is later rejected.

## 10. Batch Driver handoff

| Family | Member shots | G03 records | G08 records | Dialogue | Deterministic stills | Provider motion | Derived dependencies |
|---|---|---|---|---|---|---|---|
| F01 | S001, S005, S013, S025 | S001 C/N/M, S005 C/N/M, S013 N/M | S025 reflection + pop (pop timing) | S001 M + L, S025 L | S005, S013, S025 | S001 | — |
| F03 | S004, S012 | S004 C/N/M, S012 N/M | S004 glint (+ chime sync), S012 glint | S004 L×2, S012 L×2 | S004, S012 | — | — |
| F09 | S017 | S017 N, S019 N (on F15) | — | — | S017, S019 | — | F15 = G04 crop/scale of the approved normalised F09 frame |
| F11 (not generated) | S026 | — | — | S026 M | — | S026 | reuse FRAME-EP005-S027-BASE-v01 |

Not run against production:
- S024 (shares F01) is G06-blocked.
- S018 (F15) is G07-blocked.

## 11. Non-regression
- `unittest`: 205/205 OK. No agent008 code was changed.
- The S027, S028 and S029 stored frames re-hash equal to their registry SHAs and are APPROVED.
- Production registry, storage and status writes: 0.

## Remaining human authorisation
1. **Paid submit.** Authorise up to 3 Flare POSTs, each exactly the locked body SHA, at most 1 per family, with no retry, before 2026-10-28 00:00 GMT. Cost and balance are UNKNOWN, so Gilang must confirm the balance and accept the unknown cost.
2. **Duo reference.** Accept the inserted duo-scale sentence and image 6. Otherwise, re-lock with 5 references (the S027 precedent).
3. **G04 source state.** Choose option A or B.
4. **Downstream approvals (separate, later).** Each normalised frame's SHA; the S025 expression variance; the F15 crop quality; and Seedance for S001/S026.
