# EP005 S027: Mikko production voice approved; M1 line preserved; registry STOPPED (subtype); timing, sync options and compositor plan

Date: 2026-10-09 (UTC). Mikko & Lumi only.

## 1. Voice lock (human decision)
- **MIKKO_PRODUCTION_VOICE = APPROVED:** Teddy Twinkle – Cute Cartoon Boy, `XjGYkUkzth8BPs29fmcV` (an existing ElevenLabs library voice), approved by Gilang.
- Record: `ep005/voice_audition/MIKKO_PRODUCTION_VOICE_v1.json`.

## 2. Approved S027 dialogue clip (exact existing M1 take, no regeneration)

| Field | Value |
|---|---|
| Generation id | `Yp0rHGo5tJSND55ELxJl` (session `CR75vFeMW3tXZ0fIfjPx`, flow `bh8NqpJJuJRvkW42JSay`) |
| Model | `eleven_multilingual_v2` |
| Text | `We did it! I feel fresh.` The provider generation record equals the manifest line. No speech-to-text was run |
| Duration | 1.625 s (speech 0.04–1.23 s) |
| Bytes / format | 44,337 bytes, MP3 mono 44.1 kHz 128 kbps |
| SHA-256 | `81a0b038e0e81114f88079dd3f42aeafbbe47ba39cb8e8a706933e6ba531da50` (local equals audition evidence) |
| Credits | 24 (spent in the audition task; **0 new**) |

- **Storage:** `production-assets/audio/dialogue/DLG-EP005-S027-L1-MIKKO-v01.mp3`, object id `953752d9-9cb6-415e-bd6a-fbb4079d8cb5`.
  - Uploaded with `x-upsert: false`; the key was absent before.
  - **Readback:** 44,337 bytes, `audio/mpeg`. The SHA matches and the bytes are identical.
  - No conversion, normalisation, trim or any other edit.
- Record: `ep005/voice_audition/S027_M1_DIALOGUE_APPROVED_PRESERVED_v1.json`.

## 3. Registry: STOPPED before insert
- **Existing AUDIO subtypes:** `SFX`, `AMBIENCE`, `FOLEY`. None of them is dialogue or voice.
- **Proposed:** AUDIO / **`DIALOGUE`**, asset_id `DLG-EP005-S027-L1-MIKKO-v01`, status APPROVED, aliases `[]`.
- The metadata follows the existing ElevenLabs audio-row conventions:
  - canon_scope `MIKKO_LUMI_PRODUCTION_AUDIO`, asset_role `DIALOGUE`, rights_status UNRECONCILED
  - voice_id, voice name, line, text SHA, generation id, model, SHA, bytes, duration, storage key, S027, human approval
- Exact row: `ep005/voice_audition/S027_M1_DIALOGUE_REGISTRY_ROW_PROPOSED_v1.json`. It is **not inserted**.
- The voice choice itself, proposed as `VOICE-MIKKO-v01`, is recorded in evidence and not registered, because it has no file.

## 4. Proposed S027 timing (frame grid, 24 fps)

| Cue | Time |
|---|---|
| Dialogue clip placed | 0.500 s (frame 12) |
| **DIALOGUE_START** (first audible) | **0.540 s** |
| **DIALOGUE_END** (last audible) | **1.730 s** |
| Clip end (provider tail silence kept) | 2.125 s |
| **WIN_CHORD_START** | **1.917 s** (frame 46), −10 dB |
| **WIN_CHORD_FADE_START** | **4.000 s** (frame 96) |
| **WIN_CHORD_END** | **5.000 s** (frame 120), silent at the cut |
| Ambience | 0.000–5.000 s, 0 dB |

- **Basis:** the raw motion profile. The settle runs 0–0.6 s; the main lift runs 0.8–1.6 s, so "We did it!" rides it. The chord lands just after the last word, in the quiet window from 1.8 to 2.6 s.
- **Headroom:** an offline numeric mix peaks at −8.55 dBFS against a −1.0 ceiling.
- Data: `ep005/voice_audition/S027_DIALOGUE_TIMING_PROPOSAL_v1.json`.

## 5. Visual sync
S027_DIALOGUE_VISUAL_SYNC_DECISION = **PENDING_HUMAN**. Option A (voice-over) and Option B (minimum lip-sync step) are written up in `agent008/phase1/s027_v2/S027_VISUAL_SYNC_OPTIONS_v1.md`.

## 6. Compositor
A dialogue patch plan is ready (not applied), at about 60 lines plus 7 tests: `agent008/phase1/s027_v2/S027_COMPOSITOR_DIALOGUE_PATCH_PLAN_v1.md`. It also closes today's **fail-open** gap, where a dialogue slot is silently dropped.

## 7. Safety
- New TTS: 0. Cloning: 0. Seedance, Higgsfield, lip-sync: 0. Video generations: 0.
- Compositor: not run, not modified.
- Writes: registry 0, storage +1 object (the dialogue clip), script/manifest/readiness 0.
- Agent-006 and Agent-007: not run. Billing: no changes. Anime Clip Farming: untouched.

Rollback: storage `DELETE` of `audio/dialogue/DLG-EP005-S027-L1-MIKKO-v01.mp3`, and revert the evidence commit.
