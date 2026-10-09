# EP005 S027: final assembled shot APPROVED, preserved and registered (SHOT_RENDER / ASSEMBLED_SHOT)

Date: 2026-10-09 (UTC). Mikko & Lumi only. No generation and no provider spend.

## 1. Human decision
- **APPROVE** by Gilang / Company Brain, bound **only** to SHA-256 `7b01c392948e477ed24241e1ed28156628d498d234613121561bee0ff15b8fde`. No other render is approved by implication.
- Record: `agent008/phase1/s027_v2/S027_FINAL_SHOT_QC_RECORD_v1.json`.

## 2. Exact-byte preservation
- **Pre-upload:** the local file (from the committed renderA, never re-rendered) has SHA `7b01c392…8fde`, 4,307,940 bytes.
- **Upload:** `POST production-assets/visual/production/ep005/shots/SHOT-EP005-S027-ASSEMBLED-v01.mp4`, `x-upsert: false`, `video/mp4`. Result: HTTP 200, object id `eff11fc4-bf12-4c92-b99c-8ca314bc636f`. The key was absent before.
- **Readback:** HTTP 200, 4,307,940 bytes, SHA `7b01c392…8fde`, **byte-identical**.

## 3. Registry
- **Conventions checked:** the existing type/subtype pairs include `SHOT_FRAME/BASE_FRAME` and `SHOT_MOTION/RAW_MOTION_SOURCE`. There are no constraints beyond the unique asset_id, no existing `SHOT-EP005-S027-ASSEMBLED-v01`, and no conflict, so no migration was needed.
- **Insert:** one plain insert, HTTP 201. Row **`6c290db5-e47b-456c-a51c-736d7568e018`**: `SHOT-EP005-S027-ASSEMBLED-v01`, **SHOT_RENDER / ASSEMBLED_SHOT**, APPROVED, aliases `[]`.
  - Storage: `production-assets/visual/production/ep005/shots/SHOT-EP005-S027-ASSEMBLED-v01.mp4`.
- **Provenance in `metadata_json`:**
  - S027, the final SHA, bytes, and the codec/container.
  - 1920×1080, 24 fps, 120 frames, 5.000 s.
  - Compositor (Agent-008, commit `228248de…`), assembly spec, deterministic-core and mix-WAV SHAs, and determinism (2 identical renders).
  - Raw motion `MOTION-EP005-S027-SEEDANCE20-CAND-v01` `86dddea5…0e25`, and its base frame `81b841a6…`.
  - Dialogue `DLG-EP005-S027-L1-MIKKO-v01` `81a0b038…da50`, its text, and voice `XjGYkUkzth8BPs29fmcV`.
  - Ambience `AMB-BATHROOM-QUIET-v01` `ea28fad4…` and WIN `SFX-WIN-SPARKLE-CHORD` `84e0d57c…`.
  - Trim 121 → first 120 frames. Dialogue file at 0.500 s. Chord at 1.917 s, −10 dB, fade 4.000 → 5.000 s.
  - Voice-over accepted, human APPROVED, accepted characteristics.
  - Flags: not C1, not raw source, not full episode, not publishing.
- Row files: `S027_FINAL_SHOT_REGISTRY_ROW_v1.json` (sent) and `…_INSERTED_v1.json` (returned).
- **Post-insert verification:** all governed identities and SHAs exact, every field equals what was sent, and all 26 pre-existing rows identical. Registry 26 → 27.

## 4. Non-interference
- **Agent-006**, run locally and read-only (nodes 03/05/07 of `9bf6bbef`; no workflow run): 14/14 resolutions identical, governed rows 17 → 18, and the new row matches nothing.
  - Proofs: `AGENT006_READONLY_PROOF_FINALSHOT_{PREWRITE,POSTWRITE}.txt`.
- **Side effects:** storage.objects 22 → 23 (this MP4 only). Manifests 11 and readiness 7 are unchanged.
- **C1:** `visual/canonical/*` last updated 2026-10-05 (unchanged).
- **Raw motion:** storage readback SHA `86dddea5…0e25`; object updated_at still 08:08:10Z.
- **Dialogue:** storage readback SHA `81a0b038…da50`; object updated_at still 09:23:12Z.

## 5. Safety
- Not done: generations, provider calls, re-render, re-encode, remux.
- Not run: Agent-006 workflow, Agent-007. Agents 001–007: not modified. No other shot assembled.
- No full-episode render, no publishing.
- Changes: manifest/readiness 0, C1 0, billing 0. Anime Clip Farming: untouched.

Rollback:
- `delete from public.asset_registry where id='6c290db5-e47b-456c-a51c-736d7568e018';`
- Storage `DELETE` of `visual/production/ep005/shots/SHOT-EP005-S027-ASSEMBLED-v01.mp4`.
- Revert the evidence commit.
