# EP005 S027 Mikko voice audition v1.0 (bounded, 3 takes)

Date: 2026-10-09. Mikko & Lumi only. Authorised by Company Brain / human: exactly 3 TTS generations, no retries.
- Existing ElevenLabs credits only. No cloning, no custom voice, no purchase, no billing change.
- Data: `evidence/ep005/voice_audition/MIKKO_S027_AUDITION_RESULTS_v1.json`.

## Setup
- **Text, all three takes:** `We did it! I feel fresh.` (24 characters, 6 syllables).
  - SHA-256 `90053d06…` is recorded in the JSON.
  - The text was sent exactly, with no tags, markup or stage directions.
- **Model:** `eleven_multilingual_v2`, the same as the Lumi audition. Controls were voice + model only, with `generations_count=1` per candidate.
- **Flow:** `bh8NqpJJuJRvkW42JSay`.
- **Run:** 3 generations, 0 failures, 0 retries.
- **Credits:** 24 per take, **72 total** (0.48 US cents per take at the account rate).
  - M2's start response quoted 48; the completed generation billed 24.

## Takes
All three files are provider-original MP3: mono, 44.1 kHz, 128 kbps. They are status REVIEW and not committed.

| | Voice | voice_id | generation_id | duration | speech extent | pace (syl/s) | median F0* | SHA-256 |
|---|---|---|---|---|---|---|---|---|
| M1 | Teddy Twinkle – Cute Cartoon Boy | `XjGYkUkzth8BPs29fmcV` | `Yp0rHGo5tJSND55ELxJl` | 1.625 s | 1.19 s | **5.0** | **≈340 Hz** (child range) | `81a0b038e0e81114f88079dd3f42aeafbbe47ba39cb8e8a706933e6ba531da50` (44,337 B) |
| M2 | Austin Boy | `Xb3zeLrTi6F4ziIcXdwk` | `jCMBcewfJiO8VBKiFnXf` | 2.043 s | 1.65 s | 3.6 | **≈126 Hz** (adult-male range) | `728f0ab40983c7d5cf1d80a967aeca233871a8b02f591c0475f5f34346dcacff` (51,024 B) |
| M3 | Aaron – Conversational American Male | `B6uUx2p7cRgxseOUyP6P` | `7l4OyxGjMbE4jqX7qeJ7` | 1.811 s | 1.51 s | 4.0 | ≈150 Hz (young-adult male) | `020c67578bccd8c8161507f19e85eae2f0207bc4ceee7cbd84265e5df931a946` (47,263 B) |

\*Autocorrelation estimate over voiced frames. Octave errors are possible; listening decides.
- Each take has one natural pause between the two sentences: M1 0.19 s, M2 0.29 s, M3 0.24 s.

**Technical notes for the listener.** These are not a selection.
- **M1:** the only take whose pitch is in a child range. It is fast for preschool delivery (about 5 syllables/s), so check that it doesn't sound rushed or squeaky.
- **M2:** despite the voice name, its pitch measures in the adult-male range. Check against "not deep or adult-masculine".
- **M3:** an earnest young-adult male. Likely too adult for a bear cub, but warm and natural-paced.

## S027 timing fit
- **Assumptions (illustrative only, nothing assigned):**
  - 5.000 s shot.
  - The line starts after a 0.50 s visual settle.
  - The chord needs at least 1.0 s audible plus a 1.0 s fade, ending by 5.000 s.
  - A 0.20 s gap between the line and the chord.

| | speech | earliest chord start | room to 5.000 s | needs | fits |
|---|---|---|---|---|---|
| M1 | 0.50–1.69 s | 1.89 s | 3.11 s | 2.0 s | **yes** |
| M2 | 0.50–2.15 s | 2.35 s | 2.65 s | 2.0 s | **yes** |
| M3 | 0.50–2.01 s | 2.21 s | 2.79 s | 2.0 s | **yes** |

- All three fit with margin, and no time-stretch or edit is needed.
- The chord could also start on "I feel fresh." if preferred.
- The chord timestamp is **not** assigned.

## Pending decisions
- HUMAN_VOICE_SELECTION = **PENDING**.
- **S027_DIALOGUE_VISUAL_SYNC_DECISION = PENDING_HUMAN.** The approved raw motion has no lip-sync. No lip-sync provider was run, no regeneration was done, and voice-over is not assumed to be accepted.

## Counts and safety
- ElevenLabs TTS generations: 3. Credits: 72.
- Not done: retries, cloning, custom voices.
- Seedance, Higgsfield, lip-sync, compositor and render: none.
- Video modified: no.
- Writes: registry 0, production storage 0, script/manifest/readiness 0.
- Agent-006 and Agent-007: not run. Billing changes: none. Anime Clip Farming: untouched.
