# AGENT-008 v0.1 — Phase-0 Compositor Build and S004/S005 Technical Smoke Render

Date: 2026-10-07. Mikko & Lumi only. Phase 0: no provider, paid, ElevenLabs, Runway, OpenAI, Gemini or LLM calls; no Supabase, storage, registry or n8n writes; Agent-006 and Agent-007 not run.

## 1. What was built
| Deliverable | Location |
|---|---|
| Architecture / contract (inputs, resolution priority, 15 deterministic functions, treatments, S025 rule, determinism semantics, future tables, n8n proposal) | `agent008/CONTRACT.md` |
| Deterministic compositor (Python 3.11 + numpy + ffmpeg/ffprobe) | `agent008/*.py` |
| Configurable output spec (REVIEW, not canon) | `agent008/config/output_spec_phase0_review.json` |
| Non-canon stand-in layout and S004 timing | `agent008/layouts/ep005_s004_s005_standin_v1.json` |
| Read-only input snapshot + tool (HTTP GET only) | `agent008/inputs/ep005_phase0_input_snapshot.json`, `agent008/tools/snapshot_inputs.py` |
| Hash pin for the chime (registry row has no sha256) | `agent008/inputs/hash_pins.json` |
| Provenance schema | `agent008/schemas/provenance.schema.json` |
| Test suite (37 tests) | `agent008/tests/test_agent008.py` |
| Render provenance, raw frame hashes, verification | `evidence/agent008/phase0/` |
| QC checklist | `evidence/agent008/phase0/QC_CHECKLIST_S004_S005_PHASE0.md` |

## 2. Authority inputs (verified)
- Readiness `edc4ad58-3e5d-4ac2-9c74-c9af03af363f`: APPROVED, READY_FOR_HUMAN_APPROVAL, 14/14 REUSE_EXISTING, run `A006-1791346204213`. Readiness JSON canonical SHA-256 `205e4347…5f46`.
- Production manifest `45cc7493-80b4-4e8d-b71d-fbd7fd3656ed`: APPROVED, canonical SHA-256 `e0c2e849…0d55` (matches the approval evidence).
- Snapshot SHA-256 is recorded in the provenance; snapshot taken with GET only.

## 3. Resolved S004 / S005 contract (from the canonical map, not stale labels)
| | S004 (13.0–18.0 s) | S005 (18.0–22.0 s) |
|---|---|---|
| Frames @24 | 120 | 96 |
| Active overlays | CHEEK, MOUTH, NOSE (`OVERLAY-EP005-BERRY-SMUDGE-*-v01`) | same three |
| Treatments | `TREATMENT-EP005-MIRROR-GLINT-v01` | none |
| Props | `PROP-EP005-HAND-MIRROR-v01`, `PROP-EP005-CLEANING-CLOTH-v01` (manifest says `TMP_EP005_*`) | same |
| Characters | `CHAR-MIKKO-MASTER-v01`, `CHAR-LUMI-MASTER-v01` (manifest says `TBD`) | same |
| Environment | `WORLD-EP005-BATHROOM-MASTER-v01` (manifest says `TBD`) | same |
| Named SFX | `SFX-LUMI-CLUE-CHIME` ("Lumi clue chime") | none (protected participation hold) |
| Mapped bed (manifest) | none | `AMB-BATHROOM-QUIET-v01` |
| Dialogue | 2 Lumi lines, DEFERRED_NO_VOICE_ASSET | none |

## 4. Input asset hashes (all verified before use)
| Asset | Registry row | Bytes | SHA-256 | Hash source |
|---|---|---|---|---|
| WORLD-EP005-BATHROOM-MASTER-v01 | 8cdeea80-1eb3-4a75-b50a-c209f1aae434 | 1,756,516 | `ab79c560d3c79a05cb957331149ee4b8a176e109b06010480ba6c26903bd3733` | registry |
| CHAR-MIKKO-MASTER-v01 | 0d7a47e0-0adf-47d6-9cf9-f71ad7439747 | 2,207,008 | `41c9480a847c962c1ecfda4fe076e0abcd86548ba67f692621cfc6e13d61f1a8` | registry |
| CHAR-LUMI-MASTER-v01 | 75cf9e5d-78ec-4cac-b1bb-49e696629bc2 | 1,887,897 | `8b29c1abea53cb253eea39cdd41d5001ed38036945b049078915ac5993c43a41` | registry |
| PROP-EP005-HAND-MIRROR-v01 | a61c0af2-1e8d-40e2-88d1-8848390f2a17 | 47,670 | `34fa31a132144c355714480fa82b22916fc2f825d418658bb787791a0b9c56ac` | registry |
| PROP-EP005-CLEANING-CLOTH-v01 | ab33c77c-5fde-4642-9efb-706f619c4a7e | 237,724 | `afaa3a9fcfc5b562023080318425457c5b4dda8eb58065f56ae542786637c1db` | registry |
| OVERLAY-EP005-BERRY-SMUDGE-CHEEK-v01 | e2fc6426-bf97-437e-9515-d86419a0498a | 257,966 | `b2c735f270fccda76861e28212bec2cd60bd20564aa8c35d9a7affa394ca78ac` | registry |
| OVERLAY-EP005-BERRY-SMUDGE-MOUTH-v01 | b960c11c-6b88-4223-854b-e9ba44c7aad4 | 294,014 | `df7c2adb446daaae3eafc0a5fce3090b4b5c2c1409d12fd82d4b242b0f637b0e` | registry |
| OVERLAY-EP005-BERRY-SMUDGE-NOSE-v01 | dfaa3b89-8366-44dc-ace9-542b4a764a80 | 285,032 | `c11691271bcdbfc7b20ca253d59518560ec17e446a28f72cc3ab88da1da00bc1` | registry |
| AMB-BATHROOM-QUIET-v01 | 2ba504eb-43ad-45c2-a3bc-67ce72282359 | 7,200,174 | `ea28fad468e353b99d48070d12853620f08e8b05c8d912706122d31176544d2f` | registry |
| SFX-LUMI-CLUE-CHIME | 8eda97e0-38c1-4676-a0f5-e31b5a127967 | 206,753 | `adf415b3f23abaa93f20e510e6ac6cf3fc3c68665cd3e9cca91ff60a0a93b136` | pin (registry has none) |
Files were read from `production-assets` with authenticated GET into session scratch; nothing was written back.

## 5. Smoke render
- Stand-in: crops of the canon sheets (bathroom main view blurred; Mikko head close-up mirrored inside the hand-mirror glass with the three berry overlays; Lumi front view beside the mirror; folded cloth within reach). Banner in every frame: `NON_CANON_TECHNICAL_STANDIN | REVIEW_ONLY | NOT_FOR_EPISODE_PUBLICATION | AGENT-008 v0.1 PHASE-0`. Not registered, not uploaded.
- Timing: rigid mirror tilt 0 → −2.5° (frames 0–11, smoothstep); glint frames 12–19 (8 frames, soft attack/decay); frames 20–119 steady; S005 frames 120–215 = byte-identical hold of frame 119.
- Audio (48 kHz working, 24-bit master): ambience bed 0–9.0 s at 0 dB (20 ms clip-edge fades); clue chime from 0.500 s at −12 dB, trimmed by the declared `TRIM_WITH_FADE` policy from its natural 7.97 s to 4.375 s with a 0.5 s fade, ending at 4.875 s (S005 starts at 5.000 s).

| Output | SHA-256 | Bytes |
|---|---|---|
| **Review MP4** `A008_EP005_S004_S005_PHASE0_REVIEW.mp4` (H.264 High yuv420p 1920×1080 24 fps, 216 frames, AAC LC 48 kHz stereo, 9.000 s) | **`8fd265089c2c93538375c3dc258ad2f225f69d58332894a560c17a2c323989b7`** | 739,945 |
| Mix master WAV (pcm_s24le 48 kHz stereo) | `caebec5d2c34ac07b0d0628a00571eb8d0777424ed3b100fdbd5066b4d33ca64` | 2,592,068 |
| Provenance JSON | `4f3f6adbe3f41695031b4172b90ec87fc8ba971618821a97a1bde18ceb08a667` | 28,211 |
| Raw frame hash list (216 rgb24 frames) | `fe3ab2589cd25fe927492446fc054ed47986d2fe5d7bce4b93f879ead253fc4c` (sha of list) | — |
| Provenance deterministic core | `63a5742d03b4e9a3af77b15b45a594ef068b93dde37688fa7d15b29e81e6b7ec` | — |
Code fingerprint (sha of module hashes): `ab62a2946fb0fb7b957c02b7fbf7dc2cb9ce2b1b1f8de7cdb44b82085819eca0`. Toolchain: ffmpeg 6.1.1-3ubuntu5, numpy 2.4.6. Layout sha256 `5f93a9a3…8c0e`.
Determinism: two independent runs produced byte-identical MP4, WAV, provenance and frame-hash list.

Verification (`evidence/agent008/phase0/verification.json`): 216 frames; raw frame changes only at 1–20; S005 hold identical to the last S004 frame; chime 0.500–4.875 s; mix peak −16.83 dBFS; AAC peak −16.84 dBFS; minimum 10 ms RMS −56.8 dBFS (0 windows below −100 dBFS); decoded H.264 hold drift ≤ 7 code values (encoder-level, not compositor-level).

## 6. ffmpeg recipes
- Image decode: `ffmpeg -i <asset> -frames:v 1 -f rawvideo -pix_fmt rgba -`
- Scaling: `-vf scale=W:H:flags=lanczos+accurate_rnd+full_chroma_int+bitexact` on raw RGBA
- Background blur: `-vf gblur=sigma=4.0:steps=3`
- Banner: `drawtext=fontfile=DejaVuSans.ttf (sha256 in provenance):fontsize=26` on a `color=…@0.588` RGBA strip
- Audio decode: `-map 0:a:0 -f f64le -ac 2 -ar 48000 -af aresample=resampler=soxr:precision=28`
- Mix master: `-f f64le -ar 48000 -ac 2 -i - -c:a pcm_s24le -fflags +bitexact -flags:a +bitexact -map_metadata -1`
- Review encode (exact command in provenance `recipes.encode_command`): raw rgb24 pipe → `scale=out_color_matrix=bt709:out_range=tv`, `libx264 -preset medium -crf 16 -threads 1`, BT.709 tags, `aac -b:a 192k`, `+bitexact`, `-map_metadata -1`, `+faststart`.

## 7. Tests (37, all pass): `python3 -m unittest discover -s agent008/tests -t .`
| Id | Covered by | Result |
|---|---|---|
| T-A008-01 exact approved asset-id resolution | T01_ExactResolution (2) | PASS |
| T-A008-02 hash mismatch fails closed | T02_HashMismatch (4: file, tampered asset in plan, pin conflict, no hash) | PASS |
| T-A008-03 missing asset fails closed | T03_MissingAsset (3: registry row, local file, not approved) | PASS |
| T-A008-04 ambiguous registry match fails closed | T04_Ambiguity (3: duplicate row, alias collision, reuse-map conflict) | PASS |
| T-A008-05 stale TMP label cannot override canonical map | T05_StaleLabels (5, incl. a planted `TMP_EP005_HAND_MIRROR` row) | PASS |
| T-A008-06 S004 overlay set matches continuity | T06_S004Overlays (3) | PASS |
| T-A008-07 glint 6–10 frames, ends before S005 | T07_Glint (3, incl. completion-pop bounds) | PASS |
| T-A008-08 S005 frame state unchanged for full hold | RenderPipeline.test_T08 (+ negative) | PASS |
| T-A008-09 ambience covers clip, no gap | RenderPipeline.test_T09 (looping a 2 s bed over 9 s; + negative gap detection) | PASS |
| T-A008-10 audio peak does not clip | RenderPipeline.test_T10 (+ forced +30 dB fails closed) | PASS |
| T-A008-11 S025 requires zero active berry overlays | T11_S025CleanReveal (2) | PASS |
| T-A008-12 determinism | RenderPipeline.test_T12 (two synthetic renders byte-identical) and the real smoke render (two runs byte-identical) | PASS |
| Extra | readiness gate (legacy deny-list, explicit id, status/state/counts, wrong manifest or run), protected hold, SFX overrun default, caption/dialogue interfaces, REVIEW labels | PASS |
Render tests use a synthetic asset set generated in a temp dir (no production assets, no network).

## 8. Findings
- **F-A008-01 Chime longer than its window.** `SFX-LUMI-CLUE-CHIME` is a sustained 8.0 s cue (integrated −14.3 LUFS, true peak −2.7 dBTP), but S004 requires it to start with the glint and end before S005 (≤ 4.5 s available). The default policy fails closed; the smoke uses an explicit, recorded `TRIM_WITH_FADE`. Human decision D-1.
- **F-A008-02 Ambience not mapped to S004.** Manifest `audio_asset_mappings` maps `AMB-BATHROOM-QUIET-v01` to S003 and S005 but not S004 (S004's audio text lists only the chime). The bed runs under S004 per the Company Brain instruction (policy `CONTINUOUS_ACROSS_RENDER_RANGE`, recorded in the layout). Human decision D-2.
- **F-A008-03 Legacy SFX rows lack registry SHA-256.** `SFX-LUMI-CLUE-CHIME` (and the other two Suno-era SFX rows) have no `metadata_json.sha256`. Agent-008 pins the chime from committed evidence; a governed registry backfill is recommended (not done: no registry writes).
- **F-A008-04 Legacy readiness safety.** `d124ba28…` and `c0012923…` (APPROVED + NEEDS_ASSET_CREATION) can never be Agent-008 inputs: explicit-id-only input, a hard deny-list, and a state check that requires READY_FOR_HUMAN_APPROVAL with zero unresolved. Not modified.
- **F-A008-05 Stand-in limits.** The canon sheets are model sheets, so the stand-in cannot show Lumi holding the mirror or an over-shoulder angle; it proves layering, overlays, treatment timing, audio and continuity only. A Phase-1 base frame (separately authorised) is required for real shots.
- **F-A008-06 Decoded hold drift.** The H.264 review copy shows ≤ 7 code-value drift inside the static hold (lossy encoder). The raw frames are identical; a lossless or lower-CRF review copy can be produced if QC prefers.

## 9. Rollback
Nothing was written outside the repository and session scratch. To roll back: revert the commit (removes `agent008/`, `evidence/agent008/`, this report and the changelog entry). Delete the session scratch render directory. No database, storage, registry, workflow or manifest change exists to undo.

## 10. Counts
Provider calls 0 · paid calls 0 · Runway 0 · ElevenLabs 0 · OpenAI 0 · Gemini 0 · LLM calls in the compositor 0 · production DB writes 0 · production storage writes 0 · registry writes 0 · migrations 0 · n8n calls 0 · Agent-006 runs 0 · Agent-007 runs 0 · audio/video binaries committed 0.
