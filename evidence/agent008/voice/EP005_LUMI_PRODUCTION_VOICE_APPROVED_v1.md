# EP005: Lumi production voice approved, planning update (2026-10-10)

Mikko & Lumi only. Zero TTS, zero provider calls, zero writes to the script, manifest, readiness, registry or storage.

## Human decision (Gilang)
**Lumi** is approved (identity only):
- Voice: L1, "Lola – Soft, Innocent and Calming"
- voice_id: `f9imtLc2jfOLXtqe3Ihb`
- Model: eleven_multilingual_v2
- Record: `evidence/ep005/voice_audition/LUMI_PRODUCTION_VOICE_v1.json`

**Mikko** was already approved: "Teddy Twinkle – Cute Cartoon Boy", `XjGYkUkzth8BPs29fmcV`.

Both are human-approved production voice identities. No new auditions are required. A voice may only be replaced with new explicit human approval.

## Existing L1 audition take: evidence only
- Generation `ICmQjlhIOueTir68xc0u`, SHA `832fa7cc…2797`, 112,464 B.
- Text: "A little glint! Look at his cheek. Can you find the next berry smudge?"
- That is the D-3 review wording. It matches no authoritative dialogue slot, predates the Alternative B decision, and runs 1.25 s over the S004 window.
- It is preserved as evidence (ids, SHA and timing in `LUMI_AUDITION_RESULTS_v1.json`).
- It is not registered and not production dialogue. Its bytes were never written to production storage.

## Planning delta v4
Built by `build_matrix_v4_voice_delta.py`; output in `EP005_AGENT008_PRODUCTION_MATRIX_v4_VOICE_DELTA.json`. Only the `H1_LUMI_VOICE` gate was removed.

| Metric | v3 | v4 |
|---|---|---|
| Voice-blocked shots (missing Lumi voice) | 10 | **0** |
| Human-decision-blocked shots | 17 | **17** |
| Code-blocked shots | 24 | 24 |
| Technically supported | S022, S023, S026, S029 | unchanged |
| Production-ready shots | 0 | **0** |

The human-decision count does not drop because no shot had the Lumi voice as its only human gate.

**No longer blocked by MISSING_LUMI_VOICE (10):** S001, S003, S004, S010, S012, S016, S018, S022, S025, S028.

Each of these keeps all its other blockers, plus `LUMI_DIALOGUE_CLIP_MISSING`:

| Shot | Still blocked by |
|---|---|
| S001 | H4 visible speech; G03, G09; Mikko clip missing |
| S003 | H4; G03 |
| S004 | H2 script amendment authorisation; H4; G03, G08, G09 |
| S010 | H4; G03 |
| S012 | H2; H4; G03, G08, G09 |
| S016 | H4; G03 |
| S018 | H2; G03, G07, G08, G09 |
| S022 | H4 (technically supported; also needs its base frame and motion generation) |
| S025 | H4; G08 |
| S028 | H4; H5 derived-frame authorisation; G09; Mikko clip missing; motion generation |

**Lumi dialogue lines:** 13 required, 0 exist.
- 7 shots (S001, S003, S010, S016, S022, S025, S028) have final v02 text; generation is not authorised.
- 6 lines in S004, S012 and S018 wait on the S004/S012/S018 script amendment being authorised and formally applied (`SCRIPT_AMENDMENT_AUTHORISED = FALSE`).

## Rollback
Revert the commit. Nothing outside the repository changed.
