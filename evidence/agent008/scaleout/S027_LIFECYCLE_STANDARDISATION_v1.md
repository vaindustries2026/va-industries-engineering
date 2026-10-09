# S027 lessons: recommended standard Agent-008 shot lifecycle (no code changed)

Every item below was exercised on S027. Recommendation: **adopt all 11 as standard gates.**

| Gate | Keep as standard? | Evidence from S027 |
|---|---|---|
| Exact source SHA approval (frame, raw motion, audio) | **Yes** | Every hand-off was SHA-bound. Each approval named one SHA |
| Provider upload readback verification | **Yes**, and ledger the URL *before* readback | The batch-1 reference upload lost its URL. The S027 upload ledgered first, then verified the readback |
| One-attempt spend authorisation | **Yes** | `SpendAuthorisation(max_generations=1)` was reserved in the ledger before transmission. The attempt counts as consumed whatever the outcome |
| Motion prompt SHA (constraints folded into the prompt) | **Yes** | Seedance has no negative field, so the constraints were folded into the hashed prompt. The frozen body SHA was verified as sent |
| Raw provider output preservation | **Yes** | The original bytes were downloaded, MD5 matched the ETag, and they were stored no-overwrite before the CDN's 7-day expiry |
| RAW_MOTION_SOURCE registry stage | **Yes** | This separates "approved motion" from "approved shot" and allows derived frames (G04) |
| Dialogue fail-closed | **Yes** | Exposed and fixed silent dialogue omission |
| Deterministic audio timing | **Yes**, plus G05 and G09 | Frame-grid cue times, peak ceiling, and fade-by at the cut |
| Two-render determinism verification | **Yes** | Byte-identical MP4 and WAV across two renders |
| ASSEMBLED_SHOT registry stage | **Yes** | SHOT_RENDER/ASSEMBLED_SHOT with full provenance |
| Human approval by exact output SHA | **Yes** | No approval by implication, at every stage |

## Recommended standard lifecycle (per shot)
1. **Spec:** a full-episode snapshot (G01) and `build_shot_spec`. Fail closed on any unresolved input.
2. **Base frame:** reuse an approved family frame, or derive one (G04, G03 pre-composite), or one authorised image generation. Human APPROVE by SHA, then preserve and register as SHOT_FRAME.
3. **Motion (B/C only):**
   1. Zero-spend package: prompt SHA, cost, preflight.
   2. Human spend authorisation (max 1 attempt).
   3. Source upload: ledger the URL, then verify the readback.
   4. Freeze the body SHA. Ledger the reservation, then send one POST.
   5. Poll read-only. Retrieve the original bytes, then human APPROVE by SHA.
   6. Preserve and register as SHOT_MOTION/RAW_MOTION_SOURCE.
4. **Audio:** approved voice, one TTS take per line, human APPROVE by SHA, then preserve and register as AUDIO/DIALOGUE. Reuse governed ambience and SFX with registry SHAs or hash pins.
5. **Assembly:** deterministic compose with dialogue fail-closed and role-aware audio. Render twice to prove determinism. Human APPROVE by output SHA, then preserve and register as SHOT_RENDER/ASSEMBLED_SHOT.
6. **Non-interference after every registry write:** a local Agent-006 proof, plus checks that manifests, readiness and C1 are unchanged.
