# EP005_AGENT008_PRODUCTION_BATCH_PLAN_v2 (delta from v1 @ ec9b7d1)

## Batch 0: status
| Item | v1 | v2 |
|---|---|---|
| G01 snapshot coverage | open | **DONE** (`agent008.episode`) |
| G05 audio roles | open | **DONE** (108/108 tests; S027 mix byte-identical) |
| G10 whoosh | open | **REPAIR PROPOSED.** Needs authorisation: registry metadata merge, or a hash pin |
| G11 smudge removal | open | **DESIGNED.** Implementation is bounded (~150–200 lines) after G03 |
| G02, G03, G04, G06, G07, G08, G09 | open | still open. These are the next zero-spend engineering items |
| H1–H6 | to prepare | **PACKS READY**, awaiting Gilang / Company Brain |

## Batch 1 (unchanged scope: S026, S023, S028, S029). New preconditions from v2:
- **S026:** H4 is required before its video. The manifest asks for natural mouth movement, so it is LIPSYNC_LIKELY_REQUIRED.
- **S028:** H5. The recommendation is to derive from S027 raw frame 119 (needs G04). S028's Lumi line also needs H1.
- **S023 and S029:** need G02. S029 also needs G04 and the approved S028.
- **Spend:** 1 image (F-MEDIUM-TWOSHOT), 2 video, 2 Mikko TTS.

## Recommended next step (zero spend)
Implement **G04 + G02**, the smallest remaining code that unlocks Batch 1, in parallel with the human decisions **H1, H4 and H5**.

Batches 2–6 are unchanged from v1, except that Batch 6 now has a designed method that waits on G03 + G11 and decision H6.
