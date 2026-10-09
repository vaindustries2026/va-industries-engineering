# Agent-008: smallest compositor change to support S027 dialogue (PLAN ONLY, not applied)

## Current gap (audited)
- `motion/compose.compose_motion_shot` takes no dialogue input.
- `mix_motion_audio` mixes only `mapped_audio` (beds) and `named_sfx`.
- `timeline.dialogue_track` exists, but only as an unused interface.
- Nothing checks `spec_shot['dialogue_slots']`, so a shot that requires dialogue renders **silently without it**. That is a fail-open defect.

## Change set: one module plus tests, about 60 lines
1. **`compose_motion_shot(..., dialogue_tracks=())`.** Add a keyword argument; its default keeps existing calls unchanged. Each track is built with `timeline.dialogue_track(...)` and extended with: `expected_sha256`, `text`, `text_sha256`, `registry_status`.
2. **Fail-closed guard,** checked before any decode:
   - `len(dialogue_tracks) != len(spec_shot['dialogue_slots'])` → `DIALOGUE_SLOT_UNFILLED` (or `DIALOGUE_UNEXPECTED`).
   - For each slot and track pair:
     - speaker must match, and `sha256(text) == sha256(slot.text)`, or `DIALOGUE_TEXT_MISMATCH`.
     - `registry_status in (APPROVED, LOCKED)`, or `DIALOGUE_NOT_APPROVED`.
     - `verify_file(path, expected_sha256)`, or `SHA_MISMATCH`.
3. **`mix_motion_audio(..., dialogue_tracks)`:**
   - Load with `media.load_audio`. Place it **once** at `round(start * sr)` with `gain_db`. No loop, no stretch, no trim of speech.
   - If `start + clip_len > shot_len` → `DIALOGUE_OVERRUNS_SHOT`.
   - Append a cue `{'kind': 'DIALOGUE', asset_id, start_s, end_s, gain_db, sha256}`.
   - The existing peak-ceiling check still applies to the full mix.
4. **Provenance:** add `dialogue_tracks` (ids, sha, text hash, timing) to `prov`. The `deterministic_core_sha256` then covers them.
5. **Timing source:** the dialogue start and the chord start/fade come from the same `timing` dict the runner already passes in, for example:
   - `timing['dialogue'] = [{'asset_id': 'DLG-EP005-S027-L1-MIKKO-v01', 'start_seconds': 0.5, 'gain_db': 0.0}]`
   - `timing['named']['SFX-WIN-SPARKLE-CHORD'] = {'start_seconds': 1.917, 'gain_db': -10, 'fade_out_seconds': 1.0, 'fade_complete_by_seconds': 5.0}`
   - **Not changed:** spec building, the Resolver, Phase-0 `render.mix`, the provider layer, and the registry code. The dialogue asset is resolved from its registry row by exact `asset_id` and SHA, through the existing hash-verification path.

## Tests (added to `agent008/tests/test_motion.py`)
- T-D1: a shot with a dialogue slot and no track → `DIALOGUE_SLOT_UNFILLED`. This covers today's silent-omission case.
- T-D2: an approved clip is placed at the exact sample offset, and the decoded mix region equals the clip × gain.
- T-D3: overrun past the shot end → `DIALOGUE_OVERRUNS_SHOT`.
- T-D4: SHA mismatch → `SHA_MISMATCH`.
- T-D5: text mismatch with the slot → `DIALOGUE_TEXT_MISMATCH`.
- T-D6: a non-approved row → `DIALOGUE_NOT_APPROVED`.
- T-D7: regression. Shots with no dialogue slots produce byte-identical outputs to today's.

## Dependencies outside code
- The dialogue clip needs an APPROVED registry row (`AUDIO / DIALOGUE`, proposed) for the resolution path.
- Until that exists, the runner can pass the exact SHA from committed evidence, as the existing `hash_pins` mechanism already allows.
