# EP005 S028: approvals, Seedance package, upload and gate; paused before the paid submit (2026-10-12)

Mikko & Lumi only. Base commit: `fc98e4a0666c75ad356e92ec92f4571254cbc7b6` (accepted).

## Done
1. **Dialogue approved** (status-only; PATCH guarded on exact SHA and REVIEW). Both rows read back APPROVED with speaker, voice, model, text, SHA, duration and path unchanged.

   | Line | Row | SHA | Duration |
   |---|---|---|---|
   | Lumi | `11880cb2` | `970f55a9…a8bc` | 2.554 s |
   | Mikko | `349d79ee` | `ab81173e…30b0` | 1.579 s |

2. **Frame metadata repaired.** Row `739b9aec`: `metadata_json.human_decision` PENDING → APPROVED. No other key or column changed.
3. **Timing accepted:** Lumi 0.250 s, Mikko 2.804187 s, end 4.383146 s, hold 0.616854 s. G09 PASS, re-verified against the stored approved bytes.
4. **Visual sync:** `VOICE_OVER_WITH_SOFT_NATURAL_MOUTH_MOTION`, S028 only.
5. **Gain plan (proposed; source files untouched):** `LUMI_DIALOGUE_GAIN_DB = +15.0`, `MIKKO_DIALOGUE_GAIN_DB = −4.0`.
   - Both lines then land at about −21.3 LUFS, matching the approved S027 line (−21.4 LUFS).
   - Ambience bed stays at 0 dB, about −42 LUFS.
   - Proposed cloth foley: −12 dB.
6. **Seedance package.**
   - Prompt: `evidence/agent008/phase1/s028/S028_MOTION_PROMPT_v1.txt`, **SHA-256 `d025c3cc2ef5ff56b56c886cc9e164c8506f9d7cdfe698fba08916b4278d6c74`**.
   - Job: `agent008/motion/jobs/ep005_s028_motion_v1.json`.
7. **Pre-submit validation: PASS.** `S028_PRESUBMIT_VALIDATION_v1.json` checks:
   - Frame APPROVED, human_decision APPROVED, SHA match on the stored bytes.
   - Both dialogue rows APPROVED with SHA match.
   - v05 readiness and manifest APPROVED.
   - S028 SPEC with no overlays, treatments or engineering blockers.
   - G09 PASS.
   - Request: 5 s, 1080p, `generate_audio` false, 1 source frame, 1 attempt, 0 retries.
   - Expected cost, worst case: **$3.456** (1920×1088, 121 frames), at most $3.50.
8. **Source upload (one, authorised).** Higgsfield signed upload of the exact PNG; public read-back is byte-identical. Ledger: `S028_MOTION_LEDGER_v1.jsonl`.
9. **Final gate: PASS** (`S028_FINAL_GATE_v1.json`).
   - Frozen body: prompt, image_url, duration 5, resolution 1080p, generate_audio false.
   - **FINAL_REQUEST_BODY_SHA256 `172ba8584ad3076922970794ba223e0fba1d3c7f7f0cb377dda2423c7efdfc41`.**
   - Preflight and runner checks: no blockers. Generation attempts: 0.

## Paused (human decision, 2026-10-12)
The Higgsfield API-key balance can't be read through the documented routes:
- The API balance was $5.00 before the S027 Flare image; that image's cost was not exposed.
- The S027 Seedance run cost about $3.43.
- The MCP workspace reads 10 credits on the free plan.

On your answer ("upload + gate, then pause"), the single paid submit was **not** sent. The authorisation is unspent: ledger generation attempts = 0.

## Action note for Company Brain
Company Brain's S028 action list keeps the cloth with Mikko and has no cloth hand-off or shoulder pat. The manifest's S028 motion_description includes a hand-off and one cloth pat. The prompt follows the explicit Company Brain direction; this is recorded here so the human can confirm.

## Open metadata notes (status-only instructions honoured)
- Dialogue rows: `metadata_json.human_decision` and `human_approval` still read PENDING.
- Frame row: `human_approval` still PENDING, `approved: false`.
- A metadata-only merge needs separate authorisation.

## Side-effect audit
Unchanged: scripts (5), manifests (12), readiness (8), resolution items (86), creation jobs, shot plans, storage (26 objects).

`asset_registry` has 30 rows; the 27 unrelated rows are unchanged (`899d7f33…`). The only changes:
- 2 dialogue status changes
- 1 frame metadata key

Provider calls this task:
- Higgsfield: one signed upload (free) and its public read-back.
- Seedance POSTs: 0. Generations: 0.
- ElevenLabs: 0. Paid: 0. Billing: unchanged.
