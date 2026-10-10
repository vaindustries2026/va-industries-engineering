# EP005 Batch 0: Agent-008 engineering stabilisation (zero provider spend)

Date: 2026-10-10. Mikko & Lumi only. Base: accepted audit `ec9b7d1` (not re-audited).

## 0A Engineering (code + tests)
1. **Short-audio loop bug fixed:** governed audio roles.
   - Changes:
     - `resolve.py` now returns `asset_subtype`.
     - `spec.audio_role` derives AMBIENCE/FOLEY/SFX/DIALOGUE from the registry subtype; unknown roles fail closed.
     - The spec splits `mapped_audio` (AMBIENCE beds) from `event_audio` (FOLEY/SFX).
     - `compose.mix_motion_audio`: only AMBIENCE may be a bed or loop. Events play once at a required timestamp.
   - New fail-closed codes: `EVENT_AUDIO_WITHOUT_TIMING`, `EVENT_OVERRUNS_SHOT` (no silent truncation without an explicit `fade_complete_by_seconds`), `AUDIO_ROLE_NOT_LOOPABLE`, `AUDIO_ROLE_NOT_EVENT`, `AUDIO_ROLE_UNKNOWN`.
   - **S027 unchanged:** the S027 mix was rebuilt with the patched code from the approved assets. Mix WAV SHA `c67da3f3…a863` is identical to the approved one (a mix only; no video render).
2. **Full 29-shot coverage.**
   - `agent008/episode.py`: `resolve_episode()` returns one governed SPEC or one explicit BLOCKED entry for every manifest shot, in order. It fails `EPISODE_SNAPSHOT_INCOMPLETE` or `EPISODE_SHOT_LOST` rather than dropping a shot.
   - `tools/snapshot_inputs.build_snapshot()` resolves the approved state live (read-only GET); omitting `--shots` means every shot. There is no hand-maintained snapshot.
   - The test fixture `agent008/tests/fixtures/ep005_approved_state_capture_v1.json` is a machine GET capture: manifest canonical `e0c2e849…`, readiness `205e4347…`, registry `8a059e5c…` (27 rows).
   - **Result: 25 SPEC, 4 BLOCKED** (S007 whoosh hash; S009/S015/S021 smudge removal).
   - **Defect found and fixed:** the approved manifest mixes curly and straight apostrophes in element names. S003, S007 and S013 failed `ACTIVE_OVERLAY_WITHOUT_CONTRACT`; now handled by typographic normalisation of match keys only.
3. **Whoosh:** `WHOOSH_GOVERNANCE_REPAIR_PROPOSED`. SHA `53d06150dc0acc73cc972890510ba406486b178e4222eca253f848129bbed0c3`, 341,541 bytes, 13.848 s. Identity is proven (see `batch0/WHOOSH_GOVERNANCE_REPAIR_PROPOSED_v1.json`). Not applied.
4. **Smudge removal:** designed, not implemented (new per-frame overlay architecture). See `batch0/SMUDGE_REMOVAL_METHOD_DESIGN_v1.md`.

**Tests: 108/108 OK** (93 existing + 15 new; `batch0/AGENT008_TEST_OUTPUT_BATCH0_v1.txt`):
- FOLEY, SFX and DIALOGUE play once.
- AMBIENCE loops correctly.
- A missing event timestamp, an overrun or a role misuse fails closed.
- All 29 shots resolve to a spec or a blocker; the blockers are exactly the expected set; a missing shot cannot disappear.
- Audio roles hold per shot, and the S025 clean reveal is preserved.
- The S027 spec is unchanged.

## 0B Decision packs (prepared, not executed): `batch0/EP005_BATCH0_DECISION_PACKS_v1.md`
- **Lumi:** L1–L3 recovered, with voice IDs, generation IDs, SHAs and the flow link. LUMI_VOICE_SELECTION_REQUIRED_BY_HUMAN = YES.
- **S004/S012/S018 timing:** all conflict, and D-3 wording alone still doesn't fit. Alternatives A and B are offered (REVIEW). S003, S006 and S028 are TIGHT.
- **Held-pose matrix:** 14 shots. 9 need sign-off; none are MOTION_MEANING_LOST; S006 is the highest risk.
- **S028:** derive from S027 raw frame 119. A "Lumi has no lap" interpretation is needed.
- **Visual-sync matrix:** 10 BLOCKED_BY_VOICE, 3 LIPSYNC_LIKELY_REQUIRED, 3 VISIBLE_SPEECH_DECISION_REQUIRED.

## Matrix and plan v2
`batch0/EP005_AGENT008_PRODUCTION_MATRIX_v2.{md,json}` and `batch0/EP005_AGENT008_PRODUCTION_BATCH_PLAN_v2.md`:
- 2 technically supported, 26 code-blocked, 23 decision-blocked, 10 voice-blocked, 0 provider-ready.
- 9 images, 11 videos, 9 Mikko TTS (+13 Lumi).

## Safety
- Provider calls: 0. Uploads: 0. Generations: 0. Production renders: 0.
- Writes: DB 0, storage 0, registry 0. Migrations: 0.
- Unchanged: script, manifest, readiness, C1, S027 assets.
- Not run: Agent-006 workflow, Agent-007. Agents 001–007: unchanged. Billing: unchanged. Anime Clip Farming: untouched.
- Reads only: Supabase GET of the readiness, manifest and registry rows; a storage GET of the whoosh object.
