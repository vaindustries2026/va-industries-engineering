# EP005 S028: raw motion approved, final shot assembled (REVIEW) (2026-10-12)

Mikko & Lumi only. Zero provider generations in this task.

## 1. Raw motion approved
- Row `2e13b73d-a328-4cb9-b366-8d3cba5f350e` (`MOTION-EP005-S028-SEEDANCE20-CAND-v01`) REVIEW → **APPROVED**.
- `human_decision` / `human_approval` APPROVED, `approved` true, `approved_sha256` `341683c40de8d71ebed564b7739f9b338add2f954d00e347e0561c7fbe7a9b58`.
- The human-accepted characteristics are recorded in `approval_notes`.
- The MP4 bytes are unchanged; they were re-downloaded and re-hashed for assembly.

## 2. Foley cue analysis (`s028_assemble.py`, frames reviewed 36–83)
- Frames 54–61: the cloth is still gripped in Mikko's paw while pressed against Lumi.
- **Frame 62** is the first frame where Mikko's paw has released and the cloth is held by Lumi.
- Earlier contact is visually ambiguous: the cloth overlaps Lumi's outline from about frame 36 while still gripped.
- **FOLEY_FRAME = 62, FOLEY_TIMESTAMP = 2.583333 s.** Plays once, 2.583–3.523 s.

## 3. Final mix specification
| Track | Asset (SHA) | Timing | Gain |
|---|---|---|---|
| Lumi | DLG-EP005-S028-LUMI-v01 (`970f55a9…a8bc`) | 0.250000–2.804187 s | **+15.0 dB** |
| Mikko | DLG-EP005-S028-MIKKO-v01 (`ab81173e…30b0`) | 2.804187–4.383146 s | **−4.0 dB** |
| Ambience | AMB-BATHROOM-QUIET-v01 (`ea28fad4…4d2f`) | 0.000–5.000 s, bed, 20 ms edge ramps | **0.0 dB** |
| Foley | FOLEY-CLOTH-SOFT-v01 (`11fe4284…682f`) | once at 2.583333 s (frame 62) | **−12.0 dB** |

Balance check:
- Speech RMS: Lumi −23.7 dB, Mikko −24.1 dB (natural balance).
- Foley: about 9 dB under Mikko where they overlap (2.88–3.52 s), so subtle; not reduced.
- Ambience: about 20 dB under dialogue.

Results:
- **FINAL_MIX_PEAK_DBFS = −7.5** (≤ −1.0). Integrated −21.5 LUFS, matching the S027 dialogue reference.
- G09: **PASS**. No overlap, pre-hold 0.25 s, end hold 0.616854 s.
- Source files were not trimmed, stretched, normalised or modified.

## 4. Assembly, determinism, automatic QC
- **Video:** first 120 of 121 raw frames. fps and scale are identity at 1920×1080. No interpolation, crop, reframe, overlay or treatment.
- **Two renders byte-identical:**
  - MP4 `1d5dfabde957aeabaec89659858eb7a28910de2266513a16b77734ea11a47cc0`
  - Mix WAV `cc959fcb64b2dfec8b776f741d1718be408d3c52202134cd2a062d949318e733`
  - Deterministic core `96328a52…35bd` (identical)
  - **TWO_RENDER_DETERMINISM_PASS**
- **QC: PASS.**
  - H.264 High yuv420p, 1920×1080, 24/1, **120 frames**, **5.000000 s**.
  - AAC LC 48 kHz stereo.
  - 0 black frames.
  - Cues: exactly 2 dialogue, 1 ambience bed and 1 foley event; no other SFX or music.
  - Peak −7.5 dBFS.
  - All five sources re-hashed unchanged after rendering.

## 5. Preserved as REVIEW
- Storage: `visual/production/ep005/shots/SHOT-EP005-S028-ASSEMBLED-v01.mp4` (obj `28250aca…`). No-overwrite; read-back byte-identical.
- Registry: **`2c438190-6fb8-4a92-9161-6b04359c0fb9`**, `SHOT-EP005-S028-ASSEMBLED-v01`, SHOT_RENDER / ASSEMBLED_SHOT, **REVIEW**, human_decision **PENDING**, no aliases, full provenance.

## Side-effect audit
- Script, manifest, readiness and resolution items: unchanged (5 / 12 / 8 / 86 rows; hashes as before).
- `asset_registry`: 32 rows; the 27 unrelated rows are unchanged (`899d7f33…`). Changes: the raw-motion approval and +1 REVIEW assembled row.
- Storage: 28 objects; the prior 27 are unchanged (`116f7164…`), +1 assembled shot.
- Raw motion, dialogue, ambience and foley source bytes: unchanged.
- Zero: provider generations, ElevenLabs, Higgsfield, Agent-006/007.
- S027 unchanged. S029 not started. Nothing published. Billing unchanged. Anime Clip Farming untouched.
