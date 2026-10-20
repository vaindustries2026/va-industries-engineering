# EP005 Batch 1 v2 — F01 v02, F03 v02, F15 dedicated: ready for human review

**Authorisation:** Company Brain / Gilang, 2026-10-20.
- Up to 3 Higgsfield Flare image generations, exactly 1 per package.
- No retries, no alternate model, no fallback provider.

**F15 change:** the F15 crop of F09 (`c5c54675…`) is REJECTED and recorded in `B1_REVIEW_LEDGER_v1.jsonl`. F15 is now a dedicated generated frame. Its package was locked and pushed in `90689a7f` before any call:
- Prompt `3072bf65e56ace2ca43bb649d4c90c86bd8aad6b55fce05a601e31405a61bbae`
- Body `0ed33b69d5c4c01e8cd12e9cc637e946a4223897b2c0353a486e47cba80cf6d9`
- Same six governed references and the same settings as v02.
- Character, setting and scale wording is verbatim from the S027 and F03 v02 packages. Only the camera, composition and F15 negatives are new.

**Evidence files** in `evidence/ep005/batch1_base_frames/`:
- `B1V2_GENERATION_RECORD_v1.json`
- `B1V2_GENERATION_LEDGER_v1.jsonl`
- `FRAME-EP005-F0x/F15-BASE-CAND-v02_REVIEW_CANDIDATE.json`
- `B1_F15_DEDICATED_PACKAGE_v1.json`
- Scripts: `build_f15_dedicated_package.py`, `b1v2_generate.py`

## Pre-submit verification: PASS
- **Auth:** HTTP 200.
- **References:** all 6 reachable, each GET re-hashing equal to governance.
- **Packages:**
  - The F01 v02 and F03 v02 files are byte-identical to `3775b46d`; F15 is byte-identical to `90689a7f`.
  - All 3 prompt SHAs and 3 body SHAs equal the locked values.
- **Ledger:** 0/1 attempts used for each package.
- **Registry:** no v02 frame rows.
- **Auto-retry:** none.

## Results (3 calls, 3 completed, 0 retries)

| Candidate | REQUEST_ID | RAW_SHA (2688×1520 PNG) | NORMALISED_SHA (1920×1080) | Two-run |
|---|---|---|---|---|
| FRAME-EP005-F01-BASE-CAND-v02 | de184354-7c0e-4632-919b-c63d4d22656b | 684eb945aebb385be1237bedf3de5346a20f2ec9d8d2dd6270605f190af5bd59 | 5710032060494eea80bb6ac95bb31a3a1345caadfb8f711fa118de4ebcb1a845 | PASS (A = B) |
| FRAME-EP005-F03-BASE-CAND-v02 | b7f30c81-7e07-4e06-8335-31528821583a | 7e5ea370f302fd79f1efb09fc6d6d89376f1f844d35d6e1ad172ae50171ecd2b | ac93ecfb986dbed9ea32525dc8be7851cb790f6b59c656d7cd41815588ed5410 | PASS (A = B) |
| FRAME-EP005-F15-BASE-CAND-v02 | 583f34dc-4dd3-4ec1-aa19-9f8e024cd503 | 14fcd488ba032c5dc7e2340d398f1e84dcf9dc8fb3883ee54cfb4fa779080d19 | e7a3936d8ab6f3fff5d2d39a5b349f6159f4eeb22953dbf715f45df8dfbdc690 | PASS (A = B) |

**Normalisation:**
- Crop `{0, 4, 2688, 1512}`, then G04 lanczos bitexact scale to 1920×1080.
- The raw file was unchanged afterwards.
- No G03, G08 or other operation was applied.

**Provider cost:** none returned.

## Composition observations (engineering notes, not a verdict)
Mirror glass was measured on the pink ring along the mirror's centre column.

**F01 v02** — glass 602×628 px, 58% of frame height (v01: 634 px, 59%)
- The reflection is large, front-facing, clean and readable, which is good for G03/G08.
- Lumi now holds the handle with two tiny hands, but a short limb still joins the orb to the hands.
- The back of Mikko's real head and shoulder still fills the left ~350 px.
- The top petal tip touches the top edge.

**F03 v02** — glass 334×369 px, 34% of frame height (v01: 298 px, 28%)
- The mirror is larger and fully outlined, but still below the prompt's ~40% target.
- Lumi is a smooth orb with no visible lower lobes; one short arm holds the handle.
- Mikko's real face is very readable, with the cloth lowered.
- The camera reads as over Lumi's side rather than strictly over her shoulder.

**F15 v02** — glass 614×616 px, 57% of frame height
- This is a clean, deliberate macro with no edge intrusions: no real Mikko, and no Lumi face, eye or body. Only Lumi's tiny hand holds the handle at bottom centre.
- The reflection is large, clean and attractive, and the bathroom canon is softly visible behind.
- The top petal tip just touches the top edge.

## Side-effect audit
- **Generations:** exactly 3 images (1 per package) and 0 retries.
- **Not used:** video, ElevenLabs, Seedance, Agent-006, Agent-007.
- **No changes to:**
  - manifest, script or readiness (both still APPROVED)
  - S027, S028, S029 (stored bytes re-hash equal)
  - F09 (row `c28c7904` unchanged; not used)
  - billing
- **Production writes:** zero DB writes, zero storage writes and zero registry rows.
- Anime Clip Farming: untouched.

The binaries are kept in the scratchpad only. The raw provider copies stay on the CDN until 2026-10-28 00:00 GMT, and each normalised frame can be reproduced byte-for-byte from its raw file.

## Next (human)
APPROVE or REJECT each candidate by its exact NORMALISED_SHA.
