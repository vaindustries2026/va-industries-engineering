# EP005 S027: raw motion registered (SHOT_MOTION / RAW_MOTION_SOURCE); final-shot assembly preflight

Date: 2026-10-09 (UTC). Mikko & Lumi only. Zero spend, and no render was run.

## Part 1: registration
- **Pre-checks, all passing:**
  - Storage readback of `visual/production/ep005/motion/MOTION-EP005-S027-SEEDANCE20-CAND-v01.mp4`: 3,411,040 bytes, SHA-256 `86dddea5…0e25`.
  - No existing row for the asset_id.
  - The proposed row has SHOT_MOTION / RAW_MOTION_SOURCE / APPROVED / aliases [] and the full provenance.
  - Registry had 24 rows.
- **Changes from the drafted row,** both shown in a diff in the evidence:
  - The `notes` prefix "PROPOSED - NOT INSERTED." was removed.
  - `metadata_json.classification_approval` was added, recording the Company Brain definition.
  - All provenance fields are unchanged.
- **Insert:** one plain `POST /rest/v1/asset_registry`, with no `Prefer: resolution` header. Result: HTTP 201.
  - Row **`2ebed34b-92b5-47dc-8131-c3716849f5eb`**, created_at 2026-10-09T08:17:54.176061Z.
  - Exact row: `agent008/phase1/s027_v2/S027_RAW_MOTION_REGISTRY_ROW_FINAL_v1.json` (sent) and `…_INSERTED_v1.json` (returned).
- **Post-insert verification** (`…_POSTINSERT_VERIFICATION_v1.json`): all checks pass.
  - asset_id, type/subtype, APPROVED, SHA and storage key are exact.
  - S027, the source frame and its SHA, the provider request, the prompt SHA and the request-body SHA are exact.
  - Every sent field equals the stored field.
  - All 24 pre-existing rows are identical.
- **Side effects:**
  - Registry 24 → **25**.
  - storage.objects **21** (unchanged).
  - Manifests 11 and readiness 7 (unchanged).
  - C1 `visual/canonical/*`: same 4 objects with 2026-10-05 timestamps.
- **Agent-006 non-interference:** local, read-only (`evidence/c1/agent006_readonly_match_proof.js`, nodes 03/05/07 of `9bf6bbef`). No workflow was run.
  - Run against manifest 45cc7493: 14 requirements. Governed rows went from 15 to 16, with 0 excluded.
  - The resolution lines are **identical** (empty diff), and the new row matches nothing.
  - Outputs: `AGENT006_READONLY_PROOF_MOTION_{PREWRITE,POSTWRITE}.txt`.

## Part 2: S027 final-shot assembly preflight (read-only)
- **Authority:** approved manifest `45cc7493` (shot_plans[26], shot_queue, audio_workload, audio_asset_mappings, compositing_treatments) and approved readiness `edc4ad58` (canonical_reuse_map).
- **Spec builder:** Agent-008 `build_shot_spec(motion_phase=True)`.
- **Audio hashes:** both required audio objects were read from storage and hashed.

```text
S027_FINAL_SHOT_ASSEMBLY_PREFLIGHT
+ RAW_MOTION_REGISTERED_APPROVED = YES
+ RAW_MOTION_SHA_VERIFIED = YES
+ AGENT006_RESOLUTION_UNCHANGED = YES
+ REQUIRED_VIDEO_TREATMENTS = [trim 121->120 frames (5.000 s), review encode x264 CRF16 yuv420p]
+ REQUIRED_AUDIO_ASSETS = [AMB-BATHROOM-QUIET-v01 ea28fad4…4d2f (bed, 0 dB), SFX-WIN-SPARKLE-CHORD 84e0d57c…bd9b (at shared smile, -10 dB, faded out by 5.0 s)]
+ REQUIRED_DIALOGUE = YES (Mikko: "We did it! I feel fresh.")
+ REQUIRED_OVERLAYS = []
+ TARGET_DURATION = 5.000 s (episode 104–109 s, 120 frames)
+ TARGET_RESOLUTION = 1920x1080
+ TARGET_FPS = 24
+ COMPOSITOR_SUPPORT = PARTIAL
+ REMAINING_BLOCKERS = [DIALOGUE_VOICE_ASSET_MISSING, COMPOSITOR_DIALOGUE_UNSUPPORTED, WIN_CHORD_START_TIME_UNSET, DIALOGUE_VS_NO_LIPSYNC_DECISION, ASSEMBLY_AUTHORISATION_ABSENT]
```

| # | Question | Answer (source) |
|---|---|---|
| 1 | Dialogue? | **Yes.** Mikko says "We did it! I feel fresh." (`audio_plan.voice_required=true`; the spec builder's `dialogue_slots` status is `DEFERRED_NO_VOICE_ASSET`) |
| 2 | Silent except ambience? | **No.** Ambience, the WIN sparkle chord, and the dialogue |
| 3 | Audio assets | `AMB-BATHROOM-QUIET-v01` (registry SHA, storage SHA match) and `SFX-WIN-SPARKLE-CHORD` (hash pin `84e0d57c…`, storage SHA match; its registry row has no hash). No foley and no other SFX: the manifest QC says the chord is the only named asset, with no extra music, sting, chime or whoosh |
| 4 | Berry overlays | **Zero.** `overlay_vfx_requirements=[]`, `active_overlays=[]`, and all three smudges are false at start and end |
| 5 | Mirror glint / reflection | No glint (tracked false/false) and no treatment (`compositing_treatments=[]`). Note: continuity lists "Mikko's reflection" visible true/true, but the approved frame and video show plain glass. This is covered by the human approvals and recorded only as a note |
| 6 | Treatments that alter raw pixels | None. The final candidate is a derived 1-frame trim plus a lossy review encode. The registered raw is never modified |
| 7 | Final duration | 5.000 s |
| 8 | fps / resolution | 24 fps, 1920×1080 |
| 9 | Trim needed? | **Yes.** 121 → 120 frames (drop the final frame, 0.0417 s). `decode_normalised` already takes exactly the spec frame count |
| 10 | Compositor support | **PARTIAL.** Supported: decode/trim/QC/encode, the ambience bed, and a timed named cue with gain and fade-by. Missing: dialogue. `compose_motion_shot` has no dialogue input (`timeline.dialogue_track` is only an interface), and it **does not fail closed** on non-empty `dialogue_slots`, so running it now would silently drop Mikko's line |

**Blockers:**
1. **DIALOGUE_VOICE_ASSET_MISSING.** There is no approved Mikko voice or S027 line clip. The registry has no VOICE or DLG rows, and the Lumi audition takes are candidates only. Proposed identities, per the voice-input contract proposal: `VOICE-MIKKO-v01` and `DLG-EP005-S027-L1-MIKKO-v01`. I did not create any audio and did not use ElevenLabs.
2. **COMPOSITOR_DIALOGUE_UNSUPPORTED.** The compositor needs dialogue-track mixing and a fail-closed guard for unfilled dialogue slots. That is a code change and needs authorisation.
3. **WIN_CHORD_START_TIME_UNSET.** The manifest says "at the shared smile". A human must set the shot-relative time from the approved raw motion.
4. **DIALOGUE_VS_NO_LIPSYNC_DECISION.** The approved motion has no lip-sync, by the approved prompt, so Mikko's mouth does not form the line. A human decision is needed on how to place the line. This is not a regeneration request.
5. **ASSEMBLY_AUTHORISATION_ABSENT** (expected).

**Proposed assembly spec:** `agent008/phase1/s027_v2/S027_ASSEMBLY_SPEC_PROPOSED_v1.json`, with **ASSEMBLY_AUTHORISED = FALSE**. Full audit: `S027_FINAL_SHOT_ASSEMBLY_PREFLIGHT_v1.json`.

## Safety
- Generations: 0. Provider calls: 0. Spend: $0.
- Not used: ElevenLabs, the Agent-006 workflow, Agent-007. Agents 001–007: not modified.
- Compositor and render: not run. Publishing: none.
- Writes: C1 0, manifest/readiness 0, migrations 0.
- Agent-008 code changes: 0. Anime Clip Farming: untouched.

Rollback (registry only): `delete from public.asset_registry where id = '2ebed34b-92b5-47dc-8131-c3716849f5eb';`
