# EP005 S028: real dialogue preflight (2026-10-12)

Mikko & Lumi only. Base commit: `15fa499a7decda31321ee727d6856677bc68b200` (accepted).

## 1. v05 readiness approved
- Record: `69bff641-e056-4701-a23f-d91dbc2039b2`, transition REVIEW → **APPROVED**.
- Status-only: the readback diff is exactly `{status: REVIEW → APPROVED}`.
- No new readiness record and no Agent-006 run.

## 2. S028 frame pixel-equivalence bridge
`ep005/s028_base_frame/S028_PIXEL_EQUIVALENCE_PROOF_v1.json`

The authoritative stored PNG was re-downloaded:
- SHA `9ac6ccc3239fd08a69e9a570f13a8b857d0d9d7257fb37d24f8ad676476c6ff0`, 3,091,468 B, RGB 1920×1080.

Check: `sha256(Image.open(f).convert("RGB").tobytes())` (Pillow 12.3.0).

| Hash | Value |
|---|---|
| Computed from the stored PNG | **`f5dad881b8b8e48498b93381db225b034be867cec90d3950376284716570bc12`** |
| Expected (copy Company Brain inspected; its file SHA `d47e1eb0…1dd1` differs because of transport re-encoding) | `f5dad881…bc12` |
| Result | **MATCH** |

Pixel equivalence is verified despite the re-encoding in transport.

**Status change:** row `739b9aec-d908-4699-baea-10bf9e6b4f3e` (`FRAME-EP005-S028-BASE-CAND-v01`) REVIEW → **APPROVED**.
- Status-only; the readback diff is exactly `{status}`.
- Approval is bound to the stored SHA `9ac6ccc3…6ff0`, which `metadata_json.approve_by` already names.

**Open note (not changed; the instruction was status-only):** `metadata_json.human_decision` / `human_approval` still read "PENDING", as written at insert time. Proposed follow-up, which needs authorisation: a metadata-only merge recording `human_decision: APPROVED`, the approval record, and the pixel-equivalence bridge.

**Agent-006 local proof after the approval:** 19 governed rows (the frame joins the governed set); the 14 resolutions are identical. No workflow run.

## 3–5. Two authorised ElevenLabs generations
`ep005/s028_dialogue/`

- **Estimates first** (`estimate_only`): 27 + 18 = **45 credits, $0.009**, within the 60-credit / $0.10 limits.
- **Then exactly one generation per line**, `generations_count = 1`, no retry.

| | Lumi | Mikko |
|---|---|---|
| Asset | `DLG-EP005-S028-LUMI-v01` | `DLG-EP005-S028-MIKKO-v01` |
| Exact text | You look comfy. Story time. | I’m ready to rest. |
| Voice / model | Lola `f9imtLc2jfOLXtqe3Ihb` / eleven_multilingual_v2 | Teddy Twinkle `XjGYkUkzth8BPs29fmcV` / eleven_multilingual_v2 |
| Generation id | `oeayskQWHY46ky1NAxYO` | `I9rtpWNtSGSJp9gqVrfE` |
| SHA-256 | `970f55a95f73f0949be74c5d5424318811d5fa2add0438abd42e3f37f639a8bc` | `ab81173ee7ddb15eeb8b3bbb0bdd7eed6840d76f9100d5edb1e6ca5d04b230b0` |
| Bytes | 58,965 | 43,501 |
| Format | mp3, 44.1 kHz, mono | mp3, 44.1 kHz, mono |
| Duration (decoded; = provider) | **2.554195 s** (container header 2.586 s) | **1.578957 s** (container 1.620 s) |
| Audible region (10 ms RMS > −50 dBFS) | 0.12 – 2.21 s (lead 0.12, tail 0.344) | 0.08 – 1.25 s (lead 0.08, tail 0.329) |
| Peak | −19.5 dBFS | −3.2 dBFS |
| Credits / cost | 27 / $0.0054 | 18 / $0.0036 |
| Storage | `audio/dialogue/DLG-EP005-S028-LUMI-v01.mp3` (obj `c75fabf4…`) | `audio/dialogue/DLG-EP005-S028-MIKKO-v01.mp3` (obj `1a549382…`) |
| Registry | `11880cb2-37f2-4ab8-a99d-179e1d8a33d9`, AUDIO/DIALOGUE, **REVIEW**, decision PENDING | `349d79ee-05c5-42ca-bd9f-ce8270b3f877`, AUDIO/DIALOGUE, **REVIEW**, decision PENDING |

Both clips:
- Provider bytes were downloaded; the MD5 equals the provider's `x-goog-hash`.
- No conversion, trim, normalisation or EQ.
- Uploaded with `x-upsert: false`; the readback is byte-identical.
- Registry rows are bound to S028, speaker, voice, generation, model, exact text, SHA, duration, storage path and the v05 lineage, with no aliases. Every field reads back equal.

**Level note for the listening review:** Lumi peaks about 16 dB below Mikko. Nothing was normalised; gain is a mix decision for later, at assembly.

## 6. G09 with the real audio
`S028_G09_REAL_AUDIO_TIMING_v1.json`. The S028 spec comes from the approved v05 lineage; the shot is 5.000 s.

| Case | Placement | G09 |
|---|---|---|
| A: strict back-to-back from 0 | Lumi 0.000–2.554, Mikko 2.554–4.133 | **PASS**; end hold 0.867 s |
| A2/B: strict back-to-back, 0.25 s pre-hold | Lumi 0.250–2.804, Mikko 2.804–4.383 | **PASS**; end hold 0.617 s |
| C: Mikko 0.10 s early (undeclared overlap) | — | **FAIL_CLOSED** `DIALOGUE_OVERLAP_UNAUTHORISED` (guard works) |

Results:
- Back-to-back fits: **YES**.
- Minimum required silence-tail overlap: **0.000 s**. No overlap is needed and none was authorised.
- Proposed placement: Lumi starts at **0.250 s** and Mikko at **2.804187 s**.
- Audible speech: Lumi 0.37–2.46 s, Mikko 2.88–4.05 s, a natural turn gap of about 0.42 s.
- Final dialogue end: **4.383146 s** (file end; the audible end is about 4.05 s).
- Remaining end hold: **0.616854 s** (about 0.95 s after audible speech).
- **G09_STATUS = PASS.**

For G09 analysis only, the REVIEW clips were evaluated as if approved. Production assembly stays blocked until each exact SHA is approved.

## 7. Not done (by instruction)
No lip-sync, mouth edits, S028 video, Seedance, or visual-speech decision.

## Side-effect audit (final, server-side md5)
Unchanged:
- `episode_scripts` 5 rows `649d63f9…` and `episode_production_manifests` 12 rows `cefb8fa2…` (both = previous task's final state)
- `asset_resolution_items` 86 rows
- creation jobs and batches, `shot_production_plans`, `episode_backlog`

Changed:
- `production_readiness_manifests` 8 rows `f5c646ee…`; the prior 7 are still `a4990071…`, and the only change is 69bff641's status.
- `asset_registry` 30 rows `0a0b4d55…`; the prior 27 are still `899d7f33…`. Changes: the frame's status, and +2 REVIEW dialogue rows.
- `storage.production-assets` 26 objects `350c1fcf…`; the prior 24 are still `0b98e2b7…`. Change: +2 dialogue objects.

Zero: Higgsfield, Seedance, image or video generation, Agent-006 runs, Agent-007, script or manifest changes, C1, publishing, billing.

## Rollback (human instruction required)
- Set 69bff641 and 739b9aec back to REVIEW.
- Delete registry rows 11880cb2 and 349d79ee and storage objects c75fabf4 and 1a549382.
- The ElevenLabs credits spent (45) are not recoverable.
