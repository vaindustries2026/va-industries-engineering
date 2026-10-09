# EP005 Agent-008 scale-out production audit v1.0 (zero spend)

Date: 2026-10-09. Mikko & Lumi only. S027 is COMPLETE and CLOSED (reference implementation; not reopened).

## Sources (read-only GET; hashes in `agent008/scaleout/AUTHORITATIVE_INPUT_FETCH_SHA256_v1.txt`)
- Approved script: v02 `14471926` (APPROVED).
- Approved final production manifest: `45cc7493` (APPROVED; 29 shots; 120 s).
- Approved readiness: `edc4ad58` (APPROVED; READY_FOR_HUMAN_APPROVAL; 14/14 resolved).
- Live asset_registry: 27 rows, plus the hash pins and the Agent-008 code at `4978208`.
- No stale intermediate manifests were used.

## Deliverables (`evidence/agent008/scaleout/`)
- `EP005_AGENT008_PRODUCTION_MATRIX_v1.json` and `.md`: one row per shot. Each row covers:
  - range, frames, intended action, characters, props
  - dialogue, ambience, foley, SFX (governed IDs and SHAs), overlays, treatments, continuity
  - class and reason, base-frame family and status, motion brief
  - voice status, Agent-008 support or code gaps, provider calls, risk
- `EP005_AGENT008_PRODUCTION_BATCH_PLAN_v1.md`: Batch 0 (prerequisites) through Batch 6.
- `EP005_AGENT008_CAPABILITY_GAP_MATRIX_v1.md`: G01–G11, each with its smallest change.
- `S027_LIFECYCLE_STANDARDISATION_v1.md`: 11 gates, all recommended as standard.
- `build_ep005_production_matrix.py`: the offline generator. All counts are computed by it, and it asserts 2,880 frames (120.000 s).

## Executive summary (computed)
```text
TOTAL_EP005_SHOTS = 29
S027_COMPLETE_APPROVED = 1
REMAINING_SHOTS = 28
STATIC_OR_DETERMINISTIC_ONLY = 14   (S003 S004 S005 S006 S008 S012 S013 S017 S018 S019 S023 S024 S025 S029)
HIGGSFIELD_MOTION_REQUIRED = 3      (S022 S026 S028)
HYBRID = 8                          (S001 S002 S007 S010 S011 S014 S016 S020)
BLOCKED = 3                         (S009 S015 S021: smudge removal under a moving cloth, G11)
NEW_BASE_FRAMES_REQUIRED = 9        (F-MIRROR-OPEN, F-OVERSHOULDER-MIRROR, F-FACE-MIRROR, F-FACE-MIRROR-POINT, F-CHEEK-CLOTH, F-MOUTH-CLOTH, F-NOSE-CLOTH, F-MACRO-REFLECTION, F-MEDIUM-TWOSHOT)
MIKKO_DIALOGUE_SHOTS = 9            (8 remaining: S001 S002 S006 S007 S014 S020 S026 S028)
LUMI_DIALOGUE_SHOTS = 10            (S001 S003 S004 S010 S012 S016 S018 S022 S025 S028)
LUMI_VOICE_BLOCKED_SHOTS = 10
AGENT008_CODE_GAPS = 11             (27 of 28 remaining shots touch at least one; S026 is SUPPORTED_NOW)
ESTIMATED_VIDEO_GENERATIONS_REQUIRED = 11   (+3 if S009/S015/S021 are unblocked)
ESTIMATED_IMAGE_GENERATIONS_REQUIRED = 9
ESTIMATED_NEW_TTS_GENERATIONS_REQUIRED = 9  (Mikko lines; plus 13 Lumi lines after a Lumi voice is approved)
```
- One attempt per generation, no retries.
- **Video cost:** about $3.40 list per 5 s 1080p Seedance clip (S027 token basis). Image and TTS cost: COST_UNVERIFIED.

## Key findings
1. **Reuse beats per-shot generation.**
   - The approved manifest marks 15 video shots and 26 image shots. By visual family plus derived frames, only **9 new frames** serve all 28 remaining shots.
   - Video drops to **11**, plus 3 blocked. S027 is done; S008, S011, S028 and S029 derive their base from adjacent approved motion.
2. **14 shots need no motion provider:** they are the manifest's own compositor-only shots. They do need G02 (production still path) and human acceptance (H3) where a micro-action becomes a held pose or glint.
3. **Persistent smudges on motion:** pre-composite the approved overlays into the base frame before upload (G03). This avoids tracking for 8 hybrid shots.
   - Smudge **removal** synchronised to a cloth pass (S009, S015, S021) has no governed method. These shots are **BLOCKED** pending a design decision.
4. **Real code defect found (G05):** the cloth foley (0.94 s) and the completion pop (0.2 s) would be mixed as looped full-length beds in 8 shots.
5. **Governance gaps:**
   - G10: `SFX-MIKKO-TRY-WHOOSH` has no governed SHA.
   - G01: the Agent-008 snapshots cover only 5 shots.
6. **Dialogue timing conflicts** (estimates calibrated on the approved M1 take: S027 estimated 1.64 s vs actual 1.625 s):
   - S004: about 6.3–7.2 s of Lumi speech in 5 s (known).
   - **New:** S012 (6.0–6.8 s in 5 s) and S018 (6.0–6.8 s in 6 s).
   - Tight: S003, S006, S028.
   - The D-3 shortened-prompt decision is still not in the manifest.
7. **Voice:** Mikko is approved (Teddy Twinkle `XjGYkUkzth8BPs29fmcV`). Lumi has **no approved production voice**; the L1–L3 takes are candidates only, which blocks 10 shots.
   - Voice-over was accepted for S027 only. All 16 remaining voiced shots carry a future articulation decision.

## Recommended order
- **Batch 0:** zero-spend engineering (G01, G10, G05, G09, G04, G02, G08, G03, G06, G07) and decisions H1–H6.
- **Batch 1 (clean-face cluster):** S026, S023, S028, S029. 1 image, 2 videos.
- **Batch 2:** Lumi voice decision.
- **Batch 3 (mirror open / clean reveal):** S025, S024, S001.
- **Batch 4 (static holds and face-mirror family):** S003–S006, S010–S013, S016–S019.
- **Batch 5 (cloth motion):** S007, S008, S014, S020, S022, S002.
- **Batch 6 (blocked wipes):** S009, S015, S021.

## Zero-spend confirmation
- Provider calls: 0. Generations (Higgsfield, Seedance, image, ElevenLabs): 0. Uploads: 0.
- Compositor runs: 0. Agent-006 workflow: not run. Agent-007: not run. Agents 001–007: not modified.
- Live state is unchanged by this audit:
  - storage.objects 23 (last created 2026-10-09T23:08:35Z, S027)
  - asset_registry 27 (last 23:09:14Z, S027)
  - manifests 11, readiness 7
- Writes: database 0, storage 0, registry 0. Migrations 0. C1 0. Billing 0. Anime Clip Farming: untouched.
- Agent-008 code: unchanged.
