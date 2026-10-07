# EP005 Audio Ingestion and Final Derived Manifest v1.0

Date: 2026-10-07. Scope: Mikko & Lumi EP005 only. Anime Clip Farming not touched.
Machine-readable record: `evidence/ep005/audio_ingestion/EP005_AUDIO_INGESTION_MANIFEST_v1.json`.

## 1. Input verification
All three human-approved 44.1 kHz masters matched their full SHA-256 (see manifest JSON) before conversion.

## 2. Conversion (`finalize_ep005_audio_48k_v1.sh`)
ffmpeg bitexact, libsoxr resampling only, `pcm_s24le`, 48 kHz, stereo preserved. Run twice; outputs byte-identical.
The ambience is loop-aware (looped x3, resampled, middle copy kept) so the seam is preserved (wrap-step percentile 57.57).
Cloth is 45,120 samples (2 short of the exact ratio, resampler flush; disclosed). Levels, LUFS and band RMS are unchanged by resampling (`EP005_FINAL_48K_MEASUREMENTS_v1.json`).

## 3. Storage
Uploaded with `x-upsert: false` to `production-assets` (no overwrite); readback size and SHA-256 match. Paths and object ids are in the manifest JSON.

## 4. Registry
Three plain-insert APPROVED AUDIO rows (HTTP 201) with exact identities and `aliases=[]`. No generic alias (AMBIENCE / FOLEY_CLOTH / COMPLETION_SFX) exists.
Provenance: ElevenLabs, generation ids, original MP3 sha, review master sha, final sha, human_approved, approval authority Gilang, approval date 2026-10-07, record `ENG-20261007-EP005-AUDIO-INGESTION`, `rights_status: UNRECONCILED`.
Pre/post snapshots: `EP005_REGISTRY_PRE_v1.json`, `EP005_REGISTRY_POST_v1.json`; the 20 prior rows are field-identical. Inserted rows: `EP005_REGISTRY_ROWS_INSERTED_v1.json`.

## 5. Derived manifest
`45cc7493-80b4-4e8d-b71d-fbd7fd3656ed`, status **REVIEW**, derived from `96df250f` (unmodified, still APPROVED, md5 unchanged) by `ep005_audio_mapping_v1.py`.
Mapping: TBD::AUDIO::AMBIENCE to AMB-BATHROOM-QUIET-v01 (20 shots); FOLEY_CLOTH to FOLEY-CLOTH-SOFT-v01 (7); COMPLETION_SFX to SFX-COMPLETION-POP-v01 (1).
Changed: reused-asset lists/inventory, TBD dependency lists and counts (6 to 3, audio 3 to 0, audio refs 28 to 0), manifest_version, derivation, new `audio_asset_mappings`; row: run id, reused count 3 to 6, status, agent_version.
Unchanged (asserted): shot_plans, compositing_treatments, dropped_requirements, unresolved_tbd_references, unique_new_assets. Full field diff (36 entries): `EP005_DERIVED_MANIFEST_DIFF_v1.json`.
Canonical SHA-256: source `32e2dee8...7082`, derived `e0c2e849...0d55`. Requirements before 14 (11 reuse + 3 audio needing review), after 14 (all REUSE_EXISTING).

## 6. Validation (deterministic / read-only)
- Each of the three ids resolves exactly once; no alias ambiguity; no duplicate rows.
- Objects retrievable, hashes match.
- Exact ids present in the manifest; zero `TBD::AUDIO`; FOLEY_TOUCH not reintroduced; visual requirements unchanged; count = 14.
- In-memory simulation of unmodified Agent-006 nodes 03/05/07/08 (no n8n execution): `EP005_AGENT006_INMEMORY_SIM_DERIVED_v1.json`.
- Agent-006 still at version `9bf6bbef`, unpublished; no n8n executions during the task.

## 7. Open items (not authorised here)
- Human approval of `45cc7493` (not given; still REVIEW).
- A later authorised Agent-006 run.
- ElevenLabs workspace (`a2a81ab0f7fd406cb3fff9eef8e173c2`) vs VA account, commercial-rights reconciliation (UNRECONCILED), and the credit-estimate discrepancy (795 estimated vs 265 reported).
- The ambience is MP3-derived with faint likely-codec tonal lines (untouched).

## Rollback
Derived manifest: delete row `45cc7493...` (or keep REVIEW). Registry: delete the three row ids. Storage: remove the three objects. `96df250f` untouched.
