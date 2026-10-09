# EP005 Agent-008 capability-gap matrix v1 (current code at 4978208, no changes made)

| Gap | What fails today | Smallest change | Shots |
|---|---|---|---|
| G01 Input snapshot coverage | `build_shot_spec` → `SHOT_NOT_IN_MANIFEST` for 24 shots. The snapshots hold S004/S005/S025 and S026/S027 only | Run the existing read-only `agent008/tools/snapshot_inputs.py` for all 29 shots and commit the result. No code change | all except S026, S027 |
| G02 Production still-shot path | Stills render only via the Phase-0 stand-in path, hard-wired to S004/S005 and a NON-CANON layout | `compose_still_shot`: hold a hash-verified approved/derived frame for N frames, reusing the existing treatments, `mix_motion_audio` (with dialogue) and `encode_review` | the 14 static (A) shots |
| G03 Overlay anchor placement | No placement spec for berry overlays on production frames (face + mirrored reflection). Motion compose fails closed on overlays | A human-approved anchor JSON per frame (x, y, scale, rotation, mirror). Applied deterministically on stills, and **pre-composited into base frames before provider upload**, so no motion tracking is needed for persistent smudges | 21 shots with overlays (A + C) |
| G04 Derived frame from approved motion | No governed "last frame of approved raw motion" | Exact-index ffmpeg extract; record source SHA, index and output SHA; human approval; SHOT_FRAME/DERIVED_FRAME | S008, S011, S028, S029 |
| G05 Role-aware mapped audio | Foley (0.94 s) and the completion pop (0.2 s) would be **looped across the whole shot** as beds | Split by registry subtype: AMBIENCE is a bed; FOLEY/SFX are timed one-shots that fail closed without timing | S002, S009, S014, S015, S020, S021, S025, S028 |
| G06 Keyframed crop/scale | No deterministic camera settle on stills | Smoothstep crop-rectangle ramp, no upscale above 1.0 | S024 |
| G07 In-shot cut | No two-segment shot | Concatenate two deterministic segments at an exact frame, with per-segment provenance | S018 |
| G08 Treatments on production stills | The reflection/pop-accent primitives have never run in a production path. Motion compose rejects treatments | Wire `treatments.TREATMENTS` (glint 6–10 frames, pop 6–8 frames, reflection) into G02 with frame windows from timing | S004, S006, S012, S018, S025 |
| G09 Dialogue overlap / hold guard | Multiple clips are allowed, but overlap and protected-window violations are not rejected | Add non-overlap and window checks in `resolve_dialogue` | S001, S004, S007, S012, S018, S028 |
| G10 Whoosh hash pin | `SFX-MIKKO-TRY-WHOOSH` has no registry SHA and no pin, so Agent-008 fails closed | Read-only storage hash audit plus a committed pin (data only) | S007 |
| G11 Tracked overlay removal | A smudge must vanish exactly under a provider-generated moving cloth | **Not small.** Tracking, or a human-designed masked transition on cloth-occluded frames. Needs a design decision before spend | S009, S015, S021 |

**Already supported, no gap:**
- Single and multiple dialogue clips, with fail-closed checks on missing, wrong, unapproved or SHA-mismatched clips.
- Ambience bed. Named SFX with start, gain and fade-by.
- Provider clips at least 4 s trimmed to an exact frame count (S002 and S022 generate 4 s).
- 1080p24 encode, two-render determinism, raw-source SHA verification.
- Seedance 2.0 transport with upload readback, frozen body and one-attempt spend gate.
