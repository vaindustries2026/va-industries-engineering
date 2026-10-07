# AGENT-008 — Shot Assembly Specification & Deterministic Compositor v0.1 (Phase 0)

Status: built for the Phase-0 technical smoke test only (EP005 S004 + S005).
Mikko & Lumi only. Agent-007 stays asset creation and canonicalisation only. Nothing here makes a provider call.

## 1. Position in the pipeline
```
Agent-006 readiness (APPROVED, zero unresolved)  ──►  AGENT-008  ──►  REVIEW clip + provenance  ──►  human QC (by exact SHA-256)
```
Agent-008 consumes approved identities and produces REVIEW outputs. It never creates, registers or approves assets, and never writes to Supabase or storage in v0.1.

## 2. Input contract
| Input | Rule |
|---|---|
| `readiness_manifest_id` | Required and explicit. There is **no** "latest approved readiness" lookup. Legacy `d124ba28-2dc5-4b86-8608-f363eeb3f8d2` and `c0012923-d22e-4b5e-b497-53d1c0ff3938` are deny-listed and fail closed even though they are APPROVED. |
| Readiness checks | `status = APPROVED`; `readiness_state = READY_FOR_HUMAN_APPROVAL`; `resolved_reuse_count = requirement_count`; create_new, human_review and blocked counts all 0; empty queues; every resolution record REUSE_EXISTING with exactly one exact candidate; readiness JSON canonical hash matches the snapshot. |
| `production_manifest_id` | Must equal the readiness link and be APPROVED. |
| `agent006_run_id` | Must equal the readiness `asset_resolution_run_id`. |
| Input snapshot | `agent008/tools/snapshot_inputs.py` fetches the rows with HTTP GET only and writes a reduced, hashed snapshot (`agent008/inputs/ep005_phase0_input_snapshot.json`). The compositor runs offline from it. |
| Asset files | Local copies of the approved storage objects. Every file is SHA-256-verified before use. |

## 3. Identity resolution priority (fixed)
1. Approved readiness `canonical_reuse_map`.
2. Exact approved registry identity (`asset_id`, status APPROVED/LOCKED, exactly one governed row, no alias or name collision with another governed row).
3. Exact manifest shot contract (shot timing, continuity, overlay and treatment assignment, named audio).

Stale human-readable labels are informational only and never select an asset: `TMP_EP005_*`, `TBD`, "environment TBD", "audio identity TBD", and the manifest header `readiness_flags=[UNRESOLVED_TBDS]` / `PLANNING_COMPLETE_WITH_TBDS`. A `TMP_*` string is never accepted as a registry identity, even if a row with that id were planted (regression test T-A008-05).

Expected hashes: `asset_registry.metadata_json.sha256` first; if a governed row has none, a pin in `agent008/inputs/hash_pins.json` that cites committed evidence; a disagreement or no hash at all fails closed. (`SFX-LUMI-CLUE-CHIME` has no registry hash today; it is pinned from the 2026-10-05 read-only storage audit.)

## 4. Deterministic functions (no AI / LLM)
| # | Function | Where |
|---|---|---|
| 1 | Asset resolution by exact id | `resolve.Resolver.resolve` |
| 2 | Hash verification | `hashing.verify_file`, `render.plan` |
| 3 | Scene canvas construction | `standin.build` (Phase-0 stand-in), `compositor.over` |
| 4 | Deterministic placement and scaling | `standin.Scaler`, `media.scale_rgba` (lanczos, accurate_rnd, bitexact) |
| 5 | Alpha overlay application | `compositor.over` (premultiplied float64), `compositor.trim_alpha`, `compositor.key_light_background` |
| 6 | Treatment timing by frame | `treatments.validate_window`, `treatments.envelope`, `render.frames` |
| 7 | Shot duration enforcement | `config.OutputSpec.frames_for` (fails on non-frame-aligned durations), `timeline.build_timeline` |
| 8 | Audio placement | `render.mix` (sample-accurate cue start from frame index) |
| 9 | Ambience looping and extension | `render.mix` (tiling of the loop-safe master from a declared offset) |
| 10 | Audio gain | `render.db_to_gain`, per-cue `gain_db` |
| 11 | Shot concatenation | `render.frames` (frame-exact, S005 = held last S004 frame) |
| 12 | Final review encoding | `media.encode_review` (H.264 yuv420p + AAC, bitexact flags, single thread) |
| 13 | Output hashing | per-frame SHA-256 of raw RGB frames, SHA-256 of MP4 and WAV |
| 14 | Provenance manifest | `render.provenance` (schema `agent008/schemas/provenance.schema.json`) |
| 15 | REVIEW status | `config.load_output_spec` refuses non-REVIEW specs; provenance `status=REVIEW`, `human_approval.approved=false` |

## 5. Shot contract rules
- **Overlays**: active set = berry elements with `visible_at_start = visible_at_end = true` in the shot's continuity state, each backed by an `overlay_vfx_requirements` entry and mapped to that shot in the readiness map. A start/end change (a removal shot) fails closed in v0.1 (`OVERLAY_TRANSITION_UNSUPPORTED_V01`). Inactive overlays are never passed to the compositor.
- **Treatments** are deterministic operations, never assets. A treatment runs only if the shot contract and `compositing_treatments.affected_shots` both assign it.
  - `TREATMENT-EP005-MIRROR-GLINT-v01`: 6–10 frames; must end inside its shot; procedural soft specular sprite; soft attack/decay opacity envelope.
  - `TREATMENT-EP005-MIRROR-REFLECTION-v01`: defined (hflip of the character face, clip to the glass disc, shot-active overlays only, light glass tint). The primitives exist; not executed in Phase 0 because S004/S005 are not assigned it.
  - `TREATMENT-EP005-COMPLETION-POP-ACCENT-v01`: 6–8 frame brightness pulse (`compositor.brightness_pulse`, max gain 0.12) that must not change overlay state. Defined and bounds-tested; not executed in Phase 0.
- **S025 = CLEAN REVEAL**: zero active berry overlays, enforced by `spec.validate_clean_reveal` whenever S025 is specified (T-A008-11). The bloom never stands in for berry removal.
- **Protected participation holds** (S005, S008, S013, S019): no treatment, no SFX, no dialogue, no music. Fails closed otherwise.
- **SFX that overrun their shot**: fail closed by default (`SFX_OVERRUNS_SHOT_BOUNDARY`). A run may declare `TRIM_WITH_FADE` explicitly; the trim is then recorded in provenance for human QC.
- **Continuity**: consecutive shots must agree on active overlays, props, characters and environment, and the next shot's `continuity_start_authority.source_shot_id` must name the previous shot.

## 6. Output specification (configurable, not canon)
`agent008/config/output_spec_phase0_review.json`: 16:9, 1920×1080, 24 fps, H.264 (libx264, CRF 16), yuv420p, BT.709 tags, AAC 192 kb/s review audio, 48 kHz working audio (24-bit WAV master), peak ceiling −1 dBFS, `output_status = REVIEW`, `canon_decision = false`. Pass `--output-spec` to override.

## 7. Dialogue and captions (interfaces only in Phase 0)
- Dialogue attachment: `timeline.dialogue_track(shot_id, speaker, audio_asset_id, path, start, end, gain_db)`; it requires an approved audio asset id. Manifest voice lines are carried as `dialogue_slots` with status `DEFERRED_NO_VOICE_ASSET`. No voice provider is assumed.
- Timed text: `timeline.timed_text_from_slots` → cues (UNTIMED until voice timing exists) → `to_srt` / `to_webvtt`. Burn-in is a future render option; `captions_burned_in = false`.

## 8. Determinism semantics
- **Byte-identical** for the same inputs, code (module hashes in provenance), output spec, layout, numpy build and ffmpeg build: raw RGB frames, the 24-bit WAV mix, the review MP4 and the provenance JSON reproduce exactly. Verified on the real smoke render and in T-A008-12. Settings that make this hold: pure numpy float64 compositing with one final `np.rint`; ffmpeg `+bitexact` flags, `-map_metadata -1`, single-threaded x264, soxr resampling; no timestamps in provenance.
- **Functionally deterministic** across different ffmpeg/x264/numpy builds: the shot contract, timeline, frame counts, cue times, overlay set and treatment frames are identical; pixel values may differ slightly through scaler or decoder builds; the MP4 bytes may differ through encoder versions. The raw-frame hash list is the strongest cross-machine comparison and is recorded.
- The H.264 review copy is lossy: decoded frames of a byte-identical static hold can differ by a few code values (reported as `max_abs_pixel_diff_within_hold`). Continuity is asserted on the raw frames before encoding.

## 9. Phase-0 stand-in rule
No approved EP005 base frame exists, so the smoke test composes a stand-in from crops of approved canon sheets (layout `agent008/layouts/ep005_s004_s005_standin_v1.json`). It is classified `NON_CANON_TECHNICAL_STANDIN`, `REVIEW_ONLY`, `NOT_FOR_EPISODE_PUBLICATION`; the layout loader refuses a layout without these labels, the banner is burned into every frame, and nothing is registered or uploaded.

## 10. Proposed future data model (NOT created; no migration in v0.1)
| Table | Purpose | Key fields |
|---|---|---|
| `shot_assembly_jobs` | One row per requested assembly (shot range) | id, readiness_manifest_id, production_manifest_id, agent006_run_id, shot_ids[], output_spec_id, layout_or_base_frame_ref, input_snapshot_sha256, code_sha256, status (QUEUED/RUNNING/FAILED_CLOSED/REVIEW), fail_code, created_at |
| `shot_render_candidates` | Per-shot render outputs | id, job_id, shot_id, frames, raw_frame_hash_list_sha256, storage_path (new render prefix, no overwrite), sha256, status REVIEW |
| `episode_render_candidates` | Assembled multi-shot or episode outputs | id, job_id, shot_ids[], mp4_sha256, wav_sha256, provenance_sha256, storage_path, status REVIEW |
| `render_qc_decisions` | Human QC by exact hash | id, candidate_id, candidate_sha256, decision (APPROVED/REJECTED/CHANGES_REQUESTED), checklist_json, reviewer, decided_at; append-only |
Rules: render rows never become canon by themselves; approval is a separate `render_qc_decisions` row bound to the exact SHA-256; paid generation (base frames, video, voice) needs its own persisted exact-scope authorisation.

## 11. n8n (proposal only, not built)
A later minimal wrapper may call Agent-008 as an external job (manual trigger → Execute Command or HTTP to a runner → read provenance), unpublished, with no provider credentials. The compositor stays testable outside n8n.

## 12. Running
```
python3 -m agent008 --readiness-manifest-id edc4ad58-3e5d-4ac2-9c74-c9af03af363f \
  --production-manifest-id 45cc7493-80b4-4e8d-b71d-fbd7fd3656ed --agent006-run-id A006-1791346204213 \
  --asset-dir <verified local asset copies> --out-dir <scratch>
python3 -m unittest discover -s agent008/tests -t . -v
```
Requirements: Python 3.11, numpy, ffmpeg/ffprobe with libx264, libmp3lame (tests only), libfreetype (drawtext), and the DejaVu Sans font.
