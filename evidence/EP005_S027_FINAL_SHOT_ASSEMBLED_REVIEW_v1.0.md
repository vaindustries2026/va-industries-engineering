# EP005 S027: dialogue registered, compositor dialogue patch, final shot assembled (REVIEW)

Date: 2026-10-09 (UTC). Mikko & Lumi only. No provider generations.

## 1. Dialogue registered (AUDIO / DIALOGUE)
- **Pre-checks:**
  - Storage readback of `audio/dialogue/DLG-EP005-S027-L1-MIKKO-v01.mp3`: 44,337 bytes, SHA `81a0b038…da50` (match).
  - No existing row for the asset id.
  - APPROVED, aliases `[]`.
- **Insert:** one plain insert, HTTP 201. Row **`451edb4d-3001-4016-bc9b-9e081bf5d68b`**.
  - asset_type AUDIO, subtype DIALOGUE.
  - Metadata: voice Teddy Twinkle `XjGYkUkzth8BPs29fmcV`, generation `Yp0rHGo5tJSND55ELxJl`, model `eleven_multilingual_v2`, text "We did it! I feel fresh.", SHA, 1.625 s, 44,337 bytes, storage path, S027, human APPROVED, rights_status UNRECONCILED.
  - Two fields differ from the draft: the notes prefix "PROPOSED – NOT INSERTED" was removed, and two records were added (`classification_approval`, `s027_visual_sync`).
- **Post-insert:** all fields exact. Registry 25 → 26, and the pre-existing rows are identical.
- **Agent-006 read-only proof:** 14/14 resolutions identical; governed rows 16 → 17; the dialogue row matches nothing.
  - The first pre-write run failed on a transient proxy error (`upstream request failed`) on its GET.
  - The baseline was rebuilt from the post-insert governed set minus the new row, and also checked against the committed 25-row proof. Both diffs are empty.
- Files: `ep005/voice_audition/S027_M1_DIALOGUE_REGISTRY_ROW_{FINAL,INSERTED}_v1.json`, `…_POSTINSERT_VERIFICATION_v1.json`, `AGENT006_READONLY_PROOF_DIALOGUE_{PREWRITE,POSTWRITE}.txt`.

## 2. Voice-over decision
- **S027_DIALOGUE_VISUAL_SYNC_DECISION = VOICE_OVER_ACCEPTED** (S027 only; not a global policy).
- The lack of explicit mouth articulation is human-accepted for S027.
- No lip-sync was run, the mouth was not altered, and there is no new motion candidate.

## 3. Compositor patch (`agent008/motion/compose.py`)
- **New `resolve_dialogue(spec_shot, inputs, timing)`:** binds each manifest `dialogue_slots` entry to exactly one clip from `timing['dialogue']`. It fails closed in each of these cases:

  | Condition | Code |
  |---|---|
  | Slot has no clip | `DIALOGUE_SLOT_UNFILLED` |
  | More clips than slots | `DIALOGUE_UNEXPECTED` |
  | Wrong shot | `DIALOGUE_SHOT_MISMATCH` |
  | Wrong speaker | `DIALOGUE_SPEAKER_MISMATCH` |
  | Wrong text | `DIALOGUE_TEXT_MISMATCH` |
  | Status not APPROVED/LOCKED | `DIALOGUE_NOT_APPROVED` |
  | Unknown asset | `DIALOGUE_REQUIRES_APPROVED_AUDIO` |
  | SHA mismatch | `HASH_MISMATCH` |
  | Start outside the shot | `DIALOGUE_TIMING_INVALID` |

- **`mix_motion_audio(..., dialogue=())`:** places each clip **once** at `round(start × 48000)` with its gain.
  - No loop, stretch or trim. A clip that would overrun the shot raises `DIALOGUE_OVERRUNS_SHOT`.
  - Each clip is recorded as a cue with kind `DIALOGUE`.
- **`compose_motion_shot`:** calls `resolve_dialogue` before any decode, and adds `dialogue_tracks` to provenance.
  - The signature is unchanged. Ambience and SFX code paths are unchanged, and there is no provider dependency.
  - Required dialogue can no longer be silently omitted.
- **Test fixture changes:** the existing S027 compositor tests (M07–M11 and short_raw in `test_motion.py`; HF13 in `test_higgsfield_transport.py`) now fail closed without dialogue, by design.
  - Their fixtures now supply a synthetic approved test clip. Their assertions are unchanged.
  - `ComposeFixture` was split out as a shared base, so no test runs twice.
- **New tests D01–D09:**
  - D01: exact-sample placement (mix difference equals the clip), once only, no stretch.
  - D02: missing dialogue fails closed.
  - D03: SHA mismatch fails closed.
  - D04: unapproved clip fails closed.
  - D05: wrong shot, text, speaker or asset fails closed.
  - D06: extra clip fails closed.
  - D07: overrun fails closed.
  - D08: full mix (BED + DIALOGUE + NAMED); output 120 frames at 24/1; mix exactly 5 × 48000 samples.
  - D09: a no-dialogue shot is unchanged and deterministic; a clip on a no-slot shot is refused.
- **Full suite: 93 tests, OK** (84 existing + 9 new). Output: `agent008/phase1/s027_v2/AGENT008_TEST_OUTPUT_DIALOGUE_PATCH_v1.txt`.

## 4. S027 assembly (one authorised run, plus one determinism re-render)
- **Script:** `stage4_assemble_s027.py`.
  - Inputs are read from production storage. Each is checked against its live registry row (status APPROVED) and its governed SHA (registry, or hash pin for the chord).
  - The approved raw motion is still `86dddea5…0e25` after rendering.

| Item | Value |
|---|---|
| Visual | MOTION-EP005-S027-SEEDANCE20-CAND-v01 `86dddea5…0e25`. First 120 of 121 frames; no interpolation, crop, reframe or overlay |
| Dialogue | DLG-EP005-S027-L1-MIKKO-v01 `81a0b038…da50`. File at 0.500 s, 0 dB, once; ends at 2.125 s |
| Ambience | AMB-BATHROOM-QUIET-v01 `ea28fad4…4d2f`. 0–5.000 s, 0 dB |
| WIN chord | SFX-WIN-SPARKLE-CHORD `84e0d57c…bd9b`. Start 1.9167 s (frame 46), −10 dB, fade 4.000→5.000 s, zero at the cut |
| Not included | Foley, other SFX, music, captions, overlays, glint/reflection |
| Output | MP4, H.264 High yuv420p **1920×1080, 24 fps, 120 frames**; AAC LC 48 kHz stereo; **5.000 s**; 4,307,940 bytes |
| **Output SHA-256** | **`7b01c392948e477ed24241e1ed28156628d498d234613121561bee0ff15b8fde`** |
| Mix WAV SHA-256 | `c67da3f3d7cf0a2aeca0e9d8736db64c09aa2b819b9a3a607338bf1893e2a863` |
| Automatic QC | PASS: 120 distinct frames, 0 black, peak −8.55 dBFS, 0 silent windows |
| Determinism | Two renders, **byte-identical** MP4 and WAV |

- Spec: `S027_FINAL_ASSEMBLY_SPEC_v1.json`. Provenance: `S027_FINAL_ASSEMBLY_PROVENANCE_v1.json`. Summary: `S027_FINAL_ASSEMBLY_SUMMARY_v1.json`.
- QC record: `S027_FINAL_SHOT_QC_RECORD_v1.json`. Status **REVIEW**, decision **PENDING**.
- The candidate is not registered, the binary is not committed, and it is not uploaded to storage.

## 5. Safety
- ElevenLabs, Higgsfield, Seedance and lip-sync generations: 0. Provider calls: 0.
- Not run: the Agent-006 workflow, Agent-007. Agents 001–007: not modified.
- Changes: script/manifest/readiness 0, C1 0. Publishing: none. Billing: no changes. Anime Clip Farming: untouched.
- Writes: registry +1 (the dialogue row). Storage: 0 this task.

Rollback:
- `delete from public.asset_registry where id='451edb4d-3001-4016-bc9b-9e081bf5d68b';`
- Revert the commit (code and evidence).
