# AGENT-008 v0.2 — Phase 1 Motion Layer: build + Higgsfield access audit (STOPPED before generation)

Date: 2026-10-09. Mikko & Lumi only. **Result: STOPPED_HIGGSFIELD_ACCESS_NOT_CONFIGURED** (also STOPPED_BASE_FRAME_REQUIRED_BEFORE_MOTION). Higgsfield generations: **0**. The single authorised paid job is unused and remains available once both blockers are cleared.

## 1. Higgsfield access audit (Step 1)
| Route | Found | Detail |
|---|---|---|
| MCP | Connected, **read-only** | Tools: list_workspaces, workspace_select, balance, models_list, models_get, show_generations, import-claude-motion-from-url. The connector's own instructions: it "cannot generate media, upload arbitrary files, or make purchases". There is no submit or generate tool. |
| API | None | No Higgsfield credential in environment variables, repo or Supabase-proxied hosts; no Higgsfield host in the proxy injection list |
| n8n | None | Credential list: Slack x3, OpenAI x2, Supabase x2, Google API key, YouTube, Runway. No Higgsfield. |
| Repo adapters | None before this sprint | |
**HIGGSFIELD_ACCESS = MCP (read-only; generation NONE)**
- Account (read-only `balance`): private workspace, **plan `free`, 10 credits**. Cost per generation is not exposed by the connector (COST_UNKNOWN). 10 free credits are very likely insufficient for a 5 s 1080p image-to-video job (unverified).
- Capabilities visible in the catalogue (models_list): image-to-video with start/end image, duration, aspect ratio, resolution, model selection. Job status polling, output retrieval, job ids and cost reporting cannot be verified without a generation route.
- `workspace_select` was not called (it would change a saved setting). No browser cookies, no unofficial APIs.

What the human must connect (one of):
1. A sanctioned Higgsfield **API key** for an official, documented generation API, provided as a secret to this environment (or to an n8n credential). Agent-008 then injects a transport bound to that API into `HiggsfieldProvider`.
2. Or a Higgsfield MCP connector version that exposes generation (submit, status, result) for the V&A workspace.
Plus sufficient credits on the V&A Higgsfield account (currently free plan, 10 credits). Buying credits is a human billing decision; not done here.

## 2. Built (non-paid)
| Item | Location |
|---|---|
| Provider abstraction `MotionGenerationProvider` (submit / poll / fetch / capabilities / validate_request) | `agent008/motion/provider.py` |
| Contracts `MotionRequest` / `MotionResult` (all fields requested; prompt and negative SHA-256) | `agent008/motion/contracts.py` |
| Higgsfield adapter (fails closed without a sanctioned transport; no guessed endpoints) | `agent008/motion/higgsfield.py` |
| Catalogue snapshot (read-only, 2026-10-09) | `agent008/motion/higgsfield_video_models_2026-10-09.json` |
| Spend authorisation and append-only ledger (reserve-before-submit, exact scope, max count, no retry) | `agent008/motion/authorisation.py` |
| Runner (pre-generation validation, one submit, read-only polling, raw freeze and hash) | `agent008/motion/runner.py` |
| Motion compositor pass and automatic QC (consumes exact raw SHA; fps/aspect normalise; trim to shot frames; beds and named cues with fade-by; black, freeze, frame, resolution and peak checks; provenance) | `agent008/motion/compose.py` |
| Human QC decision log (APPROVE / REJECT / REGENERATE; REJECT terminal; humans only) | `agent008/motion/qc.py` |
| Preflight (lists every blocker; never submits) | `agent008/motion/preflight.py` |
| Contract v0.2 (stages 8A-8G, kinds, provider boundary, data model, n8n design) | `agent008/CONTRACT.md` §13-18 |
| Tests M01-M12 (17 tests) | `agent008/tests/test_motion.py` |
Phase-0 change: `spec.build_shot_spec(..., motion_phase=False)` (opt-in; default unchanged). The Phase-0 S004/S005 render reproduces byte-identically (MP4 `8fd26508…89b7`, WAV `caebec5d…ca64`). Pin added for `SFX-WIN-SPARKLE-CHORD` (`84e0d57c…bd9b`, from the 2026-10-05 storage audit; the registry row has no sha256).

## 3. Model selection (Step 3) — recommendation, not used
**`seedance_2_0`** (Bytedance via Higgsfield): image-to-video with start_image and optional end_image, plus **image_references** (the canon sheets can be passed as identity references), duration 4-15 s (5 s exact), 16:9, 480p-4k (1080p in `std` mode), `generate_audio=false`, catalogue tags "identity, consistent". Chosen for identity consistency and low drift over spectacle. Fallback: `kling3_0` (start and end image, 3-15 s, 16:9, sound off; no explicit resolution control). Not chosen: cinema-grade models (camera embellishment), `seedance1_5` (no 5 s option), `minimax_hailuo` (6/10 s only), `wan2_6` (no start image). Cost: **COST_UNKNOWN**.

## 4. First motion smoke shot (Step 4): **S027** (104-109 s, 5.0 s, 120 frames)
- The only planned `IMAGE_TO_VIDEO` shot besides S002, and `compositor_required: false`.
- Locked-off camera; zero berry overlays (clean face); no mirror-reflection treatment; no glint; no berry removal; no hand-object action (the cloth and mirror are just held).
- One simple action: smiles plus one gentle shoulder lift and breathing.
- Audio is approved assets only (ambience bed and WIN sparkle chord). The Mikko line can be absent in a visual-only smoke.
- Trade-offs: both characters are on screen (every one of the 15 video shots has both); Mikko's line "We did it! I feel fresh." means the mouth should only smile, not lip-sync.
- Rejected as first test: S001/S007/S010/S011/S014 (mirror reflection plus overlays), S009/S015/S021 (berry removal), S002/S028 (hand-object interaction), S020 (camera move), S016/S022/S026 (dialogue-driven).

## 5. Base frame (Step 5): **BLOCKED_BASE_FRAME_REQUIRED**
No approved S027 production frame exists (registry and storage hold canon sheets, props, overlays and audio only). It cannot be built deterministically without misrepresentation: the approved assets are model and turnaround sheets with no image of Mikko holding the cloth or Lumi holding the mirror in a two-shot, and a collage would be animated as a collage. Required frame `FRAME-EP005-S027-BASE-v01`: close 16:9 eye-level two-shot of clean-faced Mikko (cloth held away from his face) and Lumi (holding the pink flower mirror, clean glass) in the approved EP005 bathroom, continuous with S026, no text. Creating it needs its own authorisation (image-provider spend or human-made art) and human approval by SHA-256. The one Higgsfield authorisation was not spent on it.

## 6. Motion prompt contract (Step 6)
Recorded in the job file. Prompt SHA-256 `9850629271d25db1275c776c1a71b617ba92de907ebd2cab242c1aa5bdfbb8a8` (841 characters); negative constraints SHA-256 `02d943191ac9a76cebccdccfac12d487b98c05db7d6a8146d0e9bda2bb171495`. It describes only the contracted movement (smiles, one gentle shoulder lift each, breathing, gentle hover), locks the camera, restates the Mikko and Lumi canon traits, and excludes props, characters, text, morphing, costume changes, berries, background change and effects.

## 7. Pre-generation validation (Step 7): `evidence/agent008/phase1/S027_PREFLIGHT_v1.json`
PASS: approved shot contract (120 frames), shot in the approved video shots, manifest ids (45cc7493 / edc4ad58, APPROVED), model capability (seedance_2_0, 5 s, 16:9, 1080p), prompt hash, duration and resolution, paid generations so far = 0.
**FAIL: `SOURCE_FRAME_MISSING`, `PROVIDER_CREDENTIAL_MISSING`.** Stopped here: Steps 8-12 were not executed and no review video exists.

## 8. Tests: 54/54 pass (`python3 -m unittest discover -s agent008/tests -t .`)
M01 credential missing (2) · M02 missing frame · M03 SHA mismatch (+ unapproved / stand-in frame rejected) · M04 unapproved shot (+ Phase 0 still rejects video shots) · M05 count exceeded (+ scope mismatch) · M06 provider failure = one submit, counted, no retry · M07 raw preserved read-only and unchanged by the compositor · M08 raw SHA recorded and ledger sequence · M09 compositor consumes exact SHA (tampered fails) and auto-QC PASS · M10 REVIEW required; agent cannot approve · M11 REJECT terminal; REGENERATE needs new spend · M12 two implementations of the abstraction · plus a short raw clip fails closed. The 37 Phase-0 tests are unchanged and pass.

## 9. Counts
Higgsfield generations 0 · Higgsfield credits spent 0 · workspace changes 0 · other provider generations 0 (ElevenLabs, Runway, OpenAI, Gemini) · Agent-006 0 · Agent-007 0 · Agents 001-007 modified 0 · manifests/readiness modified 0 · Supabase/storage writes 0 · migrations 0 · n8n changes 0 · purchases or billing 0 · video binaries committed 0.

## 10. To unblock (human)
1. Connect a sanctioned Higgsfield generation route (API key secret or a generation-capable connector) and confirm credits; the free plan has 10.
2. Create and approve `FRAME-EP005-S027-BASE-v01` by SHA-256 (separately authorised).
3. Confirm the model (seedance_2_0 recommended) and the end_image choice.
Then the existing authorisation (one job) can run through `run_once` with a `SpendAuthorisation` bound to the exact frame and prompt SHA-256.
