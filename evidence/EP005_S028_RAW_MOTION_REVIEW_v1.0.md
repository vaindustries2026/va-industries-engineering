# EP005 S028: raw motion ready for human review (2026-10-12)

Mikko & Lumi only.

Bases:
- Accepted stop: `a0ceda0`
- In-progress commit: `fe9cc03`

## 1. Approval metadata cleaned (metadata-only)
| Row | Change |
|---|---|
| Lumi `11880cb2` | `human_decision`, `human_approval` → APPROVED |
| Mikko `349d79ee` | `human_decision`, `human_approval` → APPROVED |
| Frame `739b9aec` | `human_approval` → APPROVED, `approved` → true |

No other column or key changed (pre/post files in `phase1/s028/`).

## 2. New authoritative package (v1 obsolete)
v1 (prompt `d025c3cc…`, body `172ba858…`) is superseded and was **not used**.

v2 action comes from the approved v05 manifest 0325d35c S028 (motion_description, character/prop requirements, production_summary, qc_checks) and script v05:
1. **Mikko passes the soft cloth to Lumi.**
2. Lumi lowers the mirror (approved "lap" interpretation).
3. **Lumi gives exactly one gentle cloth pat on Mikko's shoulder** (never the face).
4. Mikko settles beside her.

Other constraints in the prompt:
- Camera locked.
- Visual sync: VOICE_OVER_WITH_SOFT_NATURAL_MOUTH_MOTION.

Locked hashes:
- **NEW_PROMPT_SHA256** = `18090c35fedbb28804646a636e31083b70cebd9d8b7ac2161b43117a33371b77` (`S028_MOTION_PROMPT_v2.txt`)
- **NEW_FINAL_REQUEST_BODY_SHA256** = `8c80d5ac784ea638d822a60b9efd51e8fc3ea9e9946eaefc7ed4b5e28eaf41af`

## 3. Final gate: PASS (`S028_PRESUBMIT_VALIDATION_v2.json`, `S028_FINAL_GATE_v2.json`)
- Readiness 69bff641: APPROVED.
- Frame: APPROVED; decision, approval and `approved` all set; SHA `9ac6ccc3…6ff0`. The reused upload was read back fresh and is byte-identical.
- Both dialogue rows: APPROVED, metadata APPROVED.
- G09: PASS.
- Action checks: hand-off, pat, mirror and settle present; camera locked.
- Request: 5 s, 1080p, `generate_audio` false, 1 image, 1 attempt, no retry.
- Cost: worst case $3.456, at most $3.50. Balance confirmed by Gilang at ≥ $3.46.

## 4. One submission
- Provider request: **`5c3072bd-d998-4e90-8b88-6c54a83f3e27`**; attempt 1, retries 0.
- Queued at 02:13:19Z, then 17 read-only polls, then **COMPLETED**.
- Ledger: `S028_MOTION_LEDGER_v1.jsonl`.
- No cost was returned by the provider. Calculated list cost on 121 frames: **$3.4304** (≤ $3.50).

## 5. Raw output (exact provider bytes)
| Field | Value |
|---|---|
| SHA-256 | **`341683c40de8d71ebed564b7739f9b338add2f954d00e347e0561c7fbe7a9b58`** |
| Bytes | 4,028,811 |
| Container / codec | mp4 / h264 High, yuv420p |
| Picture | 1920×1080, 24/1 fps, **121 frames**, 5.041667 s |
| Audio | none |
| Storage | `visual/production/ep005/motion/MOTION-EP005-S028-SEEDANCE20-CAND-v01.mp4` (obj `b32ddd44…`), no-overwrite; read-back byte-identical |
| Registry | **`2e13b73d-a328-4cb9-b366-8d3cba5f350e`**, `MOTION-EP005-S028-SEEDANCE20-CAND-v01`, SHOT_MOTION / RAW_MOTION_SOURCE, **REVIEW**, human_decision **PENDING**, no aliases, full provenance |

## 6. Engineering observations for the human review (not a decision)
From frames sampled at 0–5 s:
- The hand-off happens around 2–3 s. Around 3 s the cloth briefly reads as loose near Lumi rather than clearly held.
- Lumi's cloth pat on Mikko's shoulder comes around 4–5 s.
- The mirror ends lowered at Lumi's side rather than squarely in front of her lower body.
- Mikko turns toward Lumi and closes his eyes contentedly at the end.
- Identities, bathroom and clean face look preserved, with no sparkles or text seen.
- Check prop count and hand/finger anatomy frame by frame.

## Side-effect audit
- Seedance generations: **1**. Retries: **0**.
- ElevenLabs: 0. Image generation: 0. Second Higgsfield generation: 0.
- Agent-006/007: 0.
- Script, manifest and readiness unchanged (5 / 12 / 8 rows, hashes as before); resolution items unchanged.
- `asset_registry` 31 rows: the 27 unrelated rows are unchanged (`899d7f33…`). Changes: metadata on 3 rows, +1 REVIEW motion row.
- Storage: 27 objects; the prior 26 are unchanged (`350c1fcf…`), +1 motion object.
- S027 unchanged. S029 not started. No assembly, mix, dialogue, ambience or foley.
- Billing unchanged. Anime Clip Farming untouched.
