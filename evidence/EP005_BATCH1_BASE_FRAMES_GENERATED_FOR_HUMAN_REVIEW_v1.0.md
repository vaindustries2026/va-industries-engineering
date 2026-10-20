# EP005 Batch 1 — Base Frames Generated, Normalised, Ready for Human Review (F01, F03, F09)

**Authorisation:** Company Brain / Gilang final authorisation, recorded on 2026-10-20.

| Item | Value |
|---|---|
| Accepted pre-submit commit | `c6a7dd2258846e228da0dc0b6ae8cf10058ef781` |
| HIGGSFIELD_BALANCE_CONFIRMED | YES |
| Calls authorised | 3, at most 1 per family |
| Retries / alternates / fallback | 0 / 0 / NONE |
| Spend ceiling | USD 0.75 per call, USD 2.25 total |
| Unknown exact cost | accepted |
| Duo reference (image 6 + locked sentence) | APPROVED |
| Normalisation source state | OPTION A, locked raw original |

**Evidence files** are in `evidence/ep005/batch1_base_frames/`:
- `B1_GENERATION_RECORD_v1.json`
- `B1_GENERATION_LEDGER_v1.jsonl`
- `FRAME-EP005-F0x-BASE-CAND-v01_REVIEW_CANDIDATE.json` (×3)
- `b1_generate.py`

## Pre-submit verification: PASS
- **Auth:** HTTP 200.
- **References:** all 6 reachable, each GET re-hashing equal to its governed SHA.
- **Packages:**
  - The package file is byte-identical to commit `c6a7dd2`.
  - All 3 prompt SHAs and 3 body SHAs equal the locked values.
  - The POST bytes are the compact sorted-key JSON whose SHA-256 is the locked body SHA.
- **Ledger:** 0/1 used for each family before submit.
- **Registry:** no F01/F03/F09 registry rows.
- **Balance confirmation:** recorded.
- **Auto-retry:** none. There is one `http.send` per POST, and the ledger blocks a second reservation.
- **Pre-submit price:** the provider exposes none, so the ceiling stop never triggered.

## Results

| FAMILY | REQUEST_ID | RAW_SHA | RAW_DIMENSIONS | NORMALISED_SHA | NORMALISATION_PASS | CALL_STATUS |
|---|---|---|---|---|---|---|
| F01 | 0411644c-ac41-40bf-90fc-8f6508e0ce4b | 6373429df617fe0bcff563e5ef3f0ad248ea88e03daed0885de014304ddd7c37 | 2688×1520 PNG | c191a513a4987cc0be6ea713f8a8dc88566c952db0250b122270786e0aa11e10 | PASS (A = B) | completed, attempt 1, retries 0 |
| F03 | 13440037-6257-4cc9-be46-35cd4efe5aa1 | d6b6b715b5f5012bbc9ffec618550c1c7cd21d50c67a498eb3e4120024ba3cd1 | 2688×1520 PNG | e8571476c5be0b1c263c4b9c3be2c155ed1af265c87aa0c18786b69b409c5968 | PASS (A = B) | completed, attempt 1, retries 0 |
| F09 | 5136a0dd-2d90-4429-90a9-d42e37f3f097 | dd94032637075be656105b8841e7cf6da320ec808f569ea130e39e33f40a1efe | 2688×1520 PNG | d442b0f7ac9524319fb2d171b7891e35ea94b4877f131de77f2bced74050f13e | PASS (A = B) | completed, attempt 1, retries 0 |

Canonical RGB pixel SHAs (raw rgb24 of the 1920×1080 frame):
- F01: `a61459c5…`
- F03: `ff22ecff…`
- F09: `bf6ee47c…`

The full values are in the candidate JSON files.

**Normalisation** (all three are identical in method):
- Crop `{x:0, y:4, w:2688, h:1512}` (0.53% of the height).
- G04 `derive_frame` scale to 1920×1080 with `lanczos+accurate_rnd+full_chroma_int+bitexact`.
- Run twice into separate directories; the outputs are byte-identical.
- The raw file was unchanged afterwards.
- Nothing else was applied: no G03, no G08, no edit, colour change or sharpening.

**Provider cost:** none returned. The submit and status responses carry no cost, credit or usage field.

## Review candidates (local only)
Each candidate is a REVIEW candidate:
- **F01:** `FRAME-EP005-F01-BASE-CAND-v01`
- **F03:** `FRAME-EP005-F03-BASE-CAND-v01`
- **F09:** `FRAME-EP005-F09-BASE-CAND-v01`

Each is bound to:
- family
- raw SHA
- normalised SHA
- request ID
- prompt SHA
- request-body SHA
- the 6 reference SHAs
- the normalisation method

There are no registry rows and no production storage. Approval is by the exact NORMALISED_SHA.

The binaries are kept in the session scratchpad and are not committed. The raw provider copies stay on the provider CDN until 2026-10-28 00:00 GMT. Each normalised frame can be reproduced byte-for-byte from its raw file.

## Engineering observations for the reviewer (not a verdict)
**F01**
- Front-facing mirror view; the clean reflection is large and centred, and the face and glass are clean.
- Mikko is in the foreground and seen mostly from behind.
- Lumi holds the handle with a long arm (canon: tiny rounded hands). Lumi is large in the frame because of foreground perspective.
- The cloth is not in view, as required.

**F03**
- Over-Lumi framing; Mikko is three-quarter with the cloth lowered in his hand, and his face and glass are clean.
- The mirror and reflection are small, about 250 px across the glass. This matters for G03 smudge legibility and for G08 glint measurement.
- Lumi's lower body shows extra rounded shapes.

**F09**
- Medium full-body two-shot; the bathroom closely follows the canon main view, and the cloth is in Mikko's lowered hand.
- The reflection is readable but small. The F15 macro crop for S019 would upscale a region roughly 230 px wide, which is the quality risk already noted.
- Lumi is about the size of Mikko's head, as the canon requires.

## Side-effect audit
**Calls:**
- 3 image generations in total, one each for F01, F03 and F09.
- 0 retries.

**Not used:** video, Seedance, ElevenLabs, Agent-006, Agent-007.

**No changes to:**
- script, manifest or readiness (both APPROVED after)
- S027, S028, S029 (stored bytes re-hash equal, APPROVED)
- production DB or storage (0 writes)
- billing (no purchase, top-up or upgrade)

**Not created:**
- G03/G08 records or dialogue
- any Batch Driver run against production

Anime Clip Farming: untouched.

## Next (human)
APPROVE or REJECT each frame by its exact NORMALISED_SHA.
- Rejected or pending frames do not advance to G03/G08.
- Production storage and registration of approved frames remain a separately gated step.
