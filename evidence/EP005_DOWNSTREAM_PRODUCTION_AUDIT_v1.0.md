# EP005 Downstream Production Audit v1.0 (read-only)

Date: 2026-10-07. Mikko & Lumi only. Read-only: no provider calls, no n8n writes, no Supabase or storage writes, no Agent-006 or Agent-007 run.
The n8n workflow list also shows an "ANIME-LAB" workflow; it belongs to a separate project, was not opened and is excluded.
Method: live n8n (workflow list, versions, credentials, executions), live Supabase (read-only SQL), the approved manifest `45cc7493`, the readiness manifest `edc4ad58`, repo files and docs. A document saying a component "should exist" was not treated as proof that it does.

## 1. Classification: **C. NEW_PRODUCTION_WORKFLOW_REQUIRED**
Nothing downstream of Agent-006 exists that can take the approved manifests and assets and produce an episode candidate.

## 2. Live inventory (verified)
| Item | Live state |
|---|---|
| Agent-006 `ZTBdnKFO8STSjJU4` | version `9bf6bbef`, unpublished, latest execution 579; last run before it was 577 |
| Agent-007 v0.1 `hlwQHO8FEcn4gDXE` | `active=true`; published `45c20c99` (70 nodes, no paid gate); unpublished draft `b135f8a5` (76 nodes, paid gate `PAID_DISPATCH_SWITCH='DISABLED'`); entry trigger has no outgoing connection |
| Agent-007 v0.2 `SVWr32vunweTrvnf` | inactive, experimental |
| Other workflows | Agents 001-005, Slack router, TEST/HARNESS/ARCHIVE copies; none does shot generation, assembly, audio or render |
| n8n credentials | Slack x3, OpenAI x2 (one managed), Supabase x2, Google API key header, YouTube OAuth, Runway API ("AGENT-007"). **No ElevenLabs, no TTS, no render credential** |
| Provider HTTP nodes in any production workflow | only Agent-007: Runway `text_to_image`, task status, download. **No image-to-video or text-to-video call anywhere** |
| ffmpeg / compositor / caption / render code | none in n8n workflows, repo `workflows/`, or docs (repo ffmpeg use is my own local audio scripts) |
| Supabase tables | `shot_production_plans` (319 planning rows, 12 runs), manifests, registry, resolution items, readiness, `asset_creation_jobs` (11), `asset_creation_batches` (3); functions `a007_*` only. **No tables for shot frames, clips, voice, timeline, render, QC or publish** |
| Storage | one private bucket `production-assets` (19 objects: audio 6, canonical visual 4, generated 4, production visual 5). **No shot frames, clips, voice, timeline or render objects** |
| Registry (APPROVED) | 14 rows: 6 audio (incl. the 3 new masters), Mikko, Lumi, bathroom world (PNG), 3 berry overlays, mirror, cloth (WEBP) |
| Docs | VA_01 flow ends at Agent-007 / canon; phase 7 "Assembly and Human QC Handoff" in the manifest is a label only; Agent-008+ is not defined anywhere; Agent-000 is deliberately unbuilt |

## 3. What the approved manifest actually requires
- 29 shots, 120 s (`estimated_duration_seconds` 120); 28 compositor shots, 26 image-generation shots, **15 video-generation shots** (63 s) = S001, S002, S007, S009, S010, S011, S014, S015, S016, S020, S021, S022, S026, S027, S028. Methods: 26 COMPOSITE, 2 IMAGE_TO_VIDEO (S002, S027), 1 STATIC_HOLD (S008).
- 17 voice shots with exact dialogue lines; music only in S027 (the approved WIN sparkle chord, faded by 109 s); protected child-response holds S005, S008, S013, S019.
- Treatments: MIRROR-GLINT (S004, S012, S018), MIRROR-REFLECTION (S006, S007, S010, S011, S014, S025), COMPLETION-POP-ACCENT (S025). They are `COMPOSITING_TREATMENT_NOT_AN_ASSET` and `agent007_eligible=false`.
- The manifest has no caption, subtitle, resolution, fps or aspect-ratio fields.

Spec hazards for any downstream consumer:
1. Shot plans still say `TMP_EP005_HAND_MIRROR`, `TMP_EP005_SOFT_CLOTH`, "environment TBD", and audio "identity TBD". The authoritative mapping is the readiness `canonical_reuse_map` and `audio_asset_mappings`, not the shot text.
2. The manifest header still carries `readiness_flags=[UNRESOLVED_TBDS]` and `readiness_state=PLANNING_COMPLETE_WITH_TBDS` (unchanged by design); do not gate on these.
3. S025 lists the reflection treatment but no active overlays. S025 is the clean reveal, so it must have zero active berry overlays; this needs one explicit line in the contract.
4. The approved "video" shots are image-to-video or direct video; the approved asset set contains no shot base frames to start from.

## 4. Production gap map
| Component | Existing? | Exact workflow/file/id | Current state | Can EP005 use it now? | Gap / action needed |
|---|---|---|---|---|---|
| Shot-level visual generation (base frames, 26) | No | Agent-007 generates only asset-level stills through Runway `text_to_image` | Gate DISABLED in draft; published `45c20c99` has no gate | No. Wrong scope and unsafe | New shot-frame producer; Runway reference-image model and cost UNKNOWN |
| Still / image animation (15 video shots) | No | none (no video endpoint in any workflow) | n/a | No | New provider call and a human provider decision; COST_UNKNOWN |
| Character consistency | Partial | Canon: `CHAR-MIKKO-MASTER-v01`, `CHAR-LUMI-MASTER-v01` (PNG, APPROVED); no per-shot consistency check | Assets ready | Assets yes, process no | Reference-image conditioning plus a human consistency QC |
| Compositing engine | No | none; n8n cannot be assumed to run ffmpeg (not verified) | n/a | No | Deterministic compositor outside n8n (e.g. ffmpeg runner) |
| Berry overlay handling | Partial | 3 APPROVED WEBP overlays; per-shot `continuity_state` visible flags in the manifest | Assets and rules ready | Data yes, code no | Registration of overlays per shot |
| Mirror reflection | No | TREATMENT-EP005-MIRROR-REFLECTION-v01 (S006, S007, S010, S011, S014, S025), data only | Spec only | No | Implement within the compositor |
| Mirror glint | No | TREATMENT-EP005-MIRROR-GLINT-v01 (S004, S012, S018), 6-10 frames | Spec only | No | Deterministic preset |
| Completion bloom | No | TREATMENT-EP005-COMPLETION-POP-ACCENT-v01 (S025), 6-8 frames | Spec only | No | Deterministic preset; must not imply berry removal |
| Narration | n/a | no narrator in the shot plans | n/a | n/a | Confirm that none is wanted |
| Dialogue (17 shots) | No | only text in `audio_plan.voice_lines` | No voice assets or voice decisions | No | Voice selection and TTS or recording; ElevenLabs is reachable only via the Claude connector, not n8n; costs credits |
| SFX | Yes (assets) | `SFX-LUMI-CLUE-CHIME`, `SFX-MIKKO-TRY-WHOOSH`, `SFX-WIN-SPARKLE-CHORD`, `SFX-COMPLETION-POP-v01`, `FOLEY-CLOTH-SOFT-v01` | APPROVED, in storage | Assets yes | Mixing and placement logic missing |
| Ambience | Yes (asset) | `AMB-BATHROOM-QUIET-v01` (loopable, 25 s, 48 kHz) | APPROVED | Asset yes | Loop and mix logic missing |
| Music | Minimal | S027 uses the WIN sparkle chord | Asset ready | Asset yes | Placement and fade only |
| Captions | No | none | n/a | No | Contract decision plus a caption generator |
| Transitions | No | text hints only ("fade", "cut to") | n/a | No | Cut and fade rules in the contract |
| Timeline assembly | No | none | n/a | No | New assembler |
| Final render | No | none | n/a | No | Needs spec (aspect, resolution, fps); none defined |
| Final QC | No | per-shot `qc_checks` text exists; no gate or table | n/a | No | Human QC gate and a QC record table |
| Output storage | Partial | bucket `production-assets` only | No render paths | Bucket yes | Define a paths convention and a no-overwrite rule |
| Publish handoff | No | n8n YouTube OAuth credential exists for research use; publish scope unverified | n/a | No | Out of scope; keep disabled |

## 5. Implemented / partial / missing / unsafe
- **Implemented:** script, storyboard, shot plans, asset resolution, canon and production assets (visual and audio), approved manifests and readiness (G1-G3 plus readiness), exact-id registry, evidence discipline.
- **Partial:** Runway still-image asset producer (Agent-007, assets only); per-shot continuity and QC text; output bucket.
- **Missing:** shot frames, image-to-video, compositor, treatments, voice, mix, captions, transitions, timeline, render, final QC, publish.
- **Unsafe to run:** Agent-007 (not eligible for `edc4ad58`; accepts only APPROVED + NEEDS_ASSET_CREATION). Standing risk F-4: legacy `d124ba28` (EP005, from `c56cabc0`) and `c0012923` (TEST) are still APPROVED + NEEDS_ASSET_CREATION, and the published `45c20c99` has no paid gate and no persisted paid authorisation. The entry trigger is unconnected and the draft gate is DISABLED, so they are inert today, but a human should retire or relabel them before downstream work. Also unsafe: the "ANIME-LAB" workflow (excluded).

## 6. Is video generation needed?
The approved plan assigns 15 shots (63 s) to video generation, 2 of them image-to-video. The other 14 shots are composite or static, but all 26 image-generation shots need base frames that do not exist.
Whether the 15 can be replaced by composited motion (as was done for S003, S004, S017, S023, S025) is a creative decision that has not been made. Not assumed.
Providers: still frames need an image provider (Runway is the only wired one); the 15 clips need an image-to-video provider (Runway is the only credentialed candidate; the endpoint is not wired); voice needs TTS (ElevenLabs via the connector only). Costs: COST_UNKNOWN (no free estimate tool exists in the current tooling).

## 7. Proposed next stage (do not build yet)
**Exactly one stage:** a new narrow specialist, **"AGENT-008 — Shot Assembly Specification & Deterministic Compositor (EP005 smoke scope)"**, split deliberately from provider generation.
Contract:
- Input: exact UUIDs of manifest `45cc7493` (APPROVED) and readiness `edc4ad58` (APPROVED), plus an explicit shot-id list.
- It consumes only registry rows that are APPROVED; it does not read `TMP_*` text.
- Stage 1 is zero spend: build a per-shot assembly spec (layers, overlays active per shot, treatments with frame counts, audio cues with start times, durations) and a deterministic compositor/assembler outside n8n; write outputs only to new `production-assets/render/ep005/...` paths with no overwrite; write status REVIEW only.
- Provider calls (base frames, video, voice) are separate, each behind a persisted, exact-scope paid authorisation (the paid-gate principle already in VA_01 §6), never inferred from readiness approval.
- Human QC gate: no render is canonical until a human approves its exact SHA-256.
Before it, resolve three decisions: output spec (aspect ratio, resolution, fps, captions), the video-vs-composite question, and the voice source.

## 8. Smallest safe smoke test (design only)
- **Shots:** S004 + S005 (18 s to 22 s; 9 s total). S005 is a 4 s static hold of the S004 composition, so one base frame serves both.
- **Why:** composite-only (no video), no overlay removal, exercises base frame, 3 registered overlays, mirror glint treatment, the clue chime, ambience mix, a protected 4 s silent hold, assembly and QC. S001 and S025 are riskier (video or reveal logic).
- **Required assets:** `CHAR-MIKKO-MASTER-v01`, `CHAR-LUMI-MASTER-v01`, `WORLD-EP005-BATHROOM-MASTER-v01`, `PROP-EP005-HAND-MIRROR-v01`, `PROP-EP005-CLEANING-CLOTH-v01`, three berry overlays, `SFX-LUMI-CLUE-CHIME`, `AMB-BATHROOM-QUIET-v01`, plus treatment `TREATMENT-EP005-MIRROR-GLINT-v01` (S004).
- **Provider/tool calls:**
  - Phase 0 (zero spend): the assembler runs on a stand-in base frame built from approved canon images only. It is marked NON_CANON and proves layering, glint timing, audio sync and the QC record.
  - Phase 1 (separately authorised, paid): one base frame, one candidate, through the existing Runway still-image path with canon references. Voice for Lumi's 2 S004 lines stays out of the smoke (captions or a silent scratch track) and needs its own decision.
- **Expected spend:** Phase 0 zero. Phase 1 COST_UNKNOWN (no free estimator); to be stated by the human before authorising.
- **Expected output:** one REVIEW-status 9 s clip with ambience, chime and glint, in a new render path.
- **Validation:** exactly 3 overlays registered to the face; glint 6-10 frames, once, finishing before S005; S005 identical frame hold for 4.0 s with no glint, dialogue or chime; clean mirror glass; no overlay removal; durations exact; audio levels not clipped; all input hashes match the registry; outputs hashed.
- **Rollback:** delete the new render objects and REVIEW rows; the registry, manifests and canon are untouched.
- **Human QC gate:** human views the clip and approves the exact output SHA-256 before it is reused or any scale-up to all 15 shots.

## 9. Counts
Provider calls 0; paid calls 0; n8n writes 0 (reads only; no new executions after 579); Supabase writes 0; storage writes 0; Agent-006 runs 0; Agent-007 runs 0.
