# EP005 S029: final shot assembled, in REVIEW (2026-10-12)

Mikko & Lumi only. Anime Clip Farming not touched. Paid or provider calls: **0**.

## Human decisions applied (Company Brain / Gilang, 2026-10-12)
1. **Continuity exception:** `S029_CLOTH_LOCATION = MIKKO_SHOULDER_IN_LUMI_HAND`.
   - S029 inherits the approved S028 end state: the cloth rests against Mikko's shoulder in Lumi's hand, with the mirror lowered. This replaces the written "cloth in Lumi's lap".
   - Applies to S029 only. Script and manifest records are unchanged; S028 was not reopened.
   - Recorded in both S029 registry rows.
2. **Implementation variance (S029 only):** `STATIC_HELD_POSE = APPROVED`; `MINIMAL_BREATHING_IMPLEMENTATION = OMITTED`.
   - No breathing, camera motion, zoom or pixel animation.

## 1. Base frame (G04)
| Item | Value |
|---|---|
| Source | `MOTION-EP005-S028-SEEDANCE20-CAND-v01` (registry 2e13b73d), SHA `341683c4…9b58`, verified before and after (also size and mtime unchanged) |
| Frame | **119** (t = 4.958333 s); the last raw frame used by the approved S028 shot |
| Output | `a8b0d0fc597d9ad009fe96745485e89c2bae5d8764734a0cdec5ca00f7b023e4`, 3,100,547 B, 1920×1080 PNG RGB |
| Canonical RGB | `5e328d86…bc86`, equal to the decoded source frame 119 |
| Determinism | two runs byte-identical; crop/scale null |
| Script | `s029_derive_base_frame.py` |

**Stored:** object `878200e1`, key `visual/production/ep005/frames/FRAME-EP005-S029-BASE-CAND-v01.png`, written with no-overwrite. Read back byte-identical.

**Registry:** row `c920490b-ba92-4af5-9966-7df78276731a`, SHOT_FRAME/BASE_FRAME.
- Created as REVIEW and read back equal.
- Then set to **APPROVED**: `human_decision` APPROVED, `human_approval` APPROVED, `approved` true, `approved_sha256` bound.
- This approval was pre-authorised in the task. Only status and approval metadata changed.

## 2. Ambience continuity S028→S029 (read-only, before render)
Script: `s029_ambience_continuity.py`. Result: **CLEAN**.

| Measure | Value |
|---|---|
| Junction | the 20 ms ramps take the bed to silence and back (envelope −44 → −85 → −49 dBFS over about 30 ms) |
| Largest sample step at the seam | 1.5e-5, against 8.5e-3 inside the steady bed: no click |
| Level change (500 ms windows) | −1.09 dB |
| Loop points | none: the bed is 25.0 s and S029 is 6 s |
| Repeated transient | none; bed head peak/RMS 4.45 (room tone) |

Note: S029 restarts the bed at 0 s, as S028 did, so roughly its first 5 s of room tone repeat. This is the governed Agent-008 behaviour, and the bed has no salient transient, so nothing distinctive is heard twice.

## 3. Assembly (G02 `compose_still_shot`)
- Script: `s029_assemble.py`.
- Inputs verified against their APPROVED rows: the base frame `a8b0d0fc…` and `AMB-BATHROOM-QUIET-v01` (2ba504eb), whose full governed SHA is `ea28fad468e353b99d48070d12853620f08e8b05c8d912706122d31176544d2f`.
- Spec from readiness 69bff641:
  - 144 frames / 6 s, COMPOSITE, no generation
  - no overlays, treatments, dialogue, named SFX or event audio
  - bed `AMB-BATHROOM-QUIET-v01` (AMBIENCE) at 0.0 dB, 0.000–6.000 s
- Layout: fit_scale 1.0, no crop, no pad.

| | renderA | renderB |
|---|---|---|
| MP4 | `b8a4e3b4233a31646d046000ffac5332aef0fe19d0a2a3f1ab67285fb3b137d6` | identical |
| Mix WAV | `24cd56b86d516a1d1848e7bf48715f17f3a48b219d1073a3a5a88fbbea569f05` | identical |
| Deterministic core | `ce8f4911…e385` | identical |

**Two-render determinism: PASS** (`cmp` byte-identical). The encoder was not changed.

## 4. Automatic QC: PASS
**Agent-008 QC:**
- PASS, 144/144 frames, 1920×1080, 24/1, 6.000 s
- 1 AAC stream at 48 kHz
- distinct encoder-input frames: 1 (RGB `5e328d86…`, equal to the base frame)
- no black frames; 0 overlays, 0 treatments

**Independent probe** (`s029_independent_qc.py`, `s029_decoded_frame_variation.py`):
- Video: H.264 High yuv420p; nb_read_frames 144; 6.000 s.
- Audio: one AAC stream, stereo, 48 kHz, 6.000 s.
- Ambience is present throughout: 50 ms RMS between −47.5 and −41.2 dBFS.
- Levels: peak −30.2 dBFS, integrated −42.1 LUFS. No clipped samples.
- No dialogue, foley, SFX or music (single bed cue).
- Lowest frame mean is 155.6/255: no black frames.

**Decoded frame differences:** decoded frames differ from one another only by H.264 quantisation residue.
- Mean absolute difference ≤ 0.011 levels; at most 14 of about 3.1 M samples differ by more than 2 levels.
- GOP is I/B/P. There is no motion; every encoded frame is the same picture.
- My strict exact-hash check of decoded frames (74 distinct hashes) is not meaningful for a lossy codec. It is replaced by these measured limits.

**Sources after render:** the S028 raw, the ambience and the base frame were re-hashed and are unchanged.

## 5. Preserved: REVIEW, not approved
**Storage:** object `9ee8412a-9e55-4746-acd5-fa46bdd390da`, key `visual/production/ep005/shots/SHOT-EP005-S029-ASSEMBLED-v01.mp4`.
- Written with no-overwrite after confirming no prior object or row.
- Read back byte-identical: `b8a4e3b4…37d6`, 680,070 B.

**Registry:** row `cf6584d5-9a4d-4788-b509-1d7320a8e28e`, `SHOT-EP005-S029-ASSEMBLED-v01`, SHOT_RENDER/ASSEMBLED_SHOT.
- **Status REVIEW**, `human_decision` **PENDING**, `approved` false, aliases [].
- Every field reads back equal.
- Provenance recorded in the row:
  - S028 raw source and SHA, frame 119
  - base-frame asset and SHA
  - continuity exception, static-hold approval, breathing omission
  - ambience asset and SHA
  - duration, frames, fps, resolution
  - determinism result and the measured codec variation
  - final SHA

## 6. Side-effect audit
Details: `S029_SIDE_EFFECT_AUDIT_v1.json`.
- Every scripts, manifests, readiness and resolution-items fingerprint is equal to the baseline.
- Registry outside S028/S029 is equal to the baseline: 27:899d7f33…
- Storage outside S029 is equal to the baseline: 28:c50f2619…
- S027 and S028 rows are unchanged.
- New: 2 registry rows and 2 storage objects. Update: 1 approval of the base frame (pre-authorised).
- Zero: ElevenLabs, Higgsfield, Seedance, generation, Agent-006, Agent-007, n8n writes, billing.

## Rollback (requires human instruction)
- Delete registry row `cf6584d5` and storage object `9ee8412a` (S029 shot).
- Delete registry row `c920490b` and storage object `878200e1` (S029 base frame).
- Nothing else was changed.

## Open human decision
APPROVE or REJECT `SHOT-EP005-S029-ASSEMBLED-v01` by exact SHA-256 `b8a4e3b4233a31646d046000ffac5332aef0fe19d0a2a3f1ab67285fb3b137d6`.
