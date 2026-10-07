# Human QC checklist — AGENT-008 v0.1 Phase-0 smoke render (EP005 S004 + S005)

Review file: `A008_EP005_S004_S005_PHASE0_REVIEW.mp4`
Approve or reject by exact SHA-256: `8fd265089c2c93538375c3dc258ad2f225f69d58332894a560c17a2c323989b7`
Status until a human decides: **REVIEW**. Approval of this technical clip does not approve the stand-in as art, as an asset or for publication.

| # | Check | What to look for | Machine evidence |
|---|---|---|---|
| 1 | Mikko / Lumi visual consistency | Canon crops are used unaltered (stand-in only; not final art) | input SHA-256 table |
| 2 | Background consistency | Same blurred bathroom crop in every frame | raw frames 20–215 identical |
| 3 | Berry overlay continuity | Cheek, beside-mouth and nose smudges on the reflected face in all 216 frames; none removed | overlays_drawn = 3; S004→S005 continuity validator |
| 4 | Anatomical side | Cheek smudge sits on Mikko's anatomical left cheek as seen in a mirror (viewer's left in the reflection) | layout `mirror_flip=true` |
| 5 | Mirror / glint correctness | One small, soft, non-magical glint near the cheek, frames 12–19 (8 frames), gone before S005 | verification.json `glint_frames` |
| 6 | Mirror tilt | Small rigid tilt to −2.5° over frames 0–11, then steady | frames 0–11 distinct |
| 7 | Shot timing | S004 = 5.000 s (120 frames), S005 = 4.000 s (96 frames), total 9.000 s | ffprobe, timeline |
| 8 | S004 → S005 continuity | No jump at 5.0 s; S005 is the held final S004 frame | raw hash equality |
| 9 | Ambience quality | Quiet bed continuous for the full 9 s, no gaps or clicks | silent windows = 0 |
| 10 | Clue-chime placement | Starts with the glint (0.500 s); trimmed with a 0.5 s fade, ends at 4.875 s, before S005 | audio_cues |
| 11 | No clipping | Mix peak −16.83 dBFS; AAC peak −16.84 dBFS (ceiling −1 dBFS) | verification.json |
| 12 | No unintended motion | No frame change after frame 20 | `raw_frame_changes_at` = 1…20 |
| 13 | No hidden frame discontinuity | 216 decoded frames; decoded hold drift ≤ 7 code values (H.264 lossy only) | verification.json |
| 14 | Labels | Banner `NON_CANON_TECHNICAL_STANDIN · REVIEW_ONLY · NOT_FOR_EPISODE_PUBLICATION` in every frame | layout classification |

Decisions the reviewer should also record (not decided by Agent-008):
- D-1: accept the chime trim (natural 7.97 s → 4.375 s with fade) or require a shorter chime edit for S004.
- D-2: confirm the ambience bed should run under S004 (Company Brain instruction) although the manifest's `audio_asset_mappings` lists S005 but not S004.
- D-3: dialogue for S004 (two Lumi lines) is deferred; the 5 s shot is not yet timed against real voice.
