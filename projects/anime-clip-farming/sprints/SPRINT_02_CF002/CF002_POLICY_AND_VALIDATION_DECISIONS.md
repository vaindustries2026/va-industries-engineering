# CF-002 policy and validation decisions

Recorded 2026-10-13 from the Company Brain decision relayed by Aquila (08:59Z).

## CF002-POLICY-SPOILER-001
Spoiler level is descriptive metadata, not a universal eligibility gate. Legacy/nostalgia content is not blocked by spoiler severity. Recent/current content may use spoiler-aware downstream handling.

Product/business-rule correction: the business is built on anime memory and meaning, with a large nostalgia/legacy share, and audiences engage with legacy content because they remember the outcome. So `spoiler_level` must not block CF-002 persistence, reduce eligibility, prevent CF-003 consideration, or imply a scene is unsafe to discuss. The field stays in the schema (needed for current-anime content). Spoiler metadata (the field) is separated from spoiler gating policy (a future downstream rule keyed on content age, to be formalised later). Current code: CF-002 only stores the value and never gates on it; no migration change is needed.

## CF002-VALIDATION-POKEMON-001
Pokémon XYZ / Ash-Greninja vs Alain's Mega Charizard X was selected as the bounded live CF-002 scene-provenance validation case using an official Pokémon public clip.

- Source: Official Pokémon YouTube channel clip "UK: Ash-Greninja versus Mega Charizard X! | Pokémon the Series: XYZ | Official Clip", video id `DiPjyqO-jqU`; episode context "Down to the Fiery Finish!".
- Lineage: Pokémon was NOT part of the original CF-001 eight-candidate batch and is not claimed to come from CF-001. It is treated as `CF002_VALIDATION_SOURCE_OUTSIDE_CF001_BATCH`, for engineering validation only, not as an editorial candidate. The eight CF-001 rows are untouched.
- Access basis: official public Pokémon publication. This is research access only; `publication_source_status` stays UNKNOWN. No download or redistribution.

## Lineage constraint and the approved v0.1.1 mechanism (2026-10-13, Company Brain)
`anime_scene_intelligence.research_candidate_id` is nullable, so no fake candidate is needed. But `anime_title_id` and the episode FK need an existing `cf.anime_titles` row, and no Pokémon title existed (the 8 CF-001 titles are different). The v0.1 validators also required a candidate id.

Approved, workflow-only patch (no migration): CF-002 v0.1.1 with explicit mode `CF002_VALIDATION_SOURCE_OUTSIDE_CF001_BATCH`.
- In the mode: `research_candidate_id` and `anime_title_id` must be absent (a candidate id is refused with `CF002_VALIDATION_MODE_CANDIDATE_FORBIDDEN`); `catalog.franchise` and `catalog.title` are required. A new node, Bootstrap Catalog, resolves or creates exactly one franchise row and one title row, both `DRAFT`, never promoted, existing rows returned untouched. Scenes store `research_candidate_id = NULL`.
- Outside the mode nothing changes: `catalog` is refused without the mode, the candidate and title gates run as before, Bootstrap Catalog is a no-op passthrough.
- Marker: `anime_franchises` and `anime_titles` have no notes field, and no schema change was made for one. The marker `CF002_VALIDATION_SOURCE_OUTSIDE_CF001_BATCH` is written to the scene's `research_access_notes` and to the run's `input_ids` (`validation_mode`) and `output_summary` (`lineage: NOT_FROM_CF001_BATCH`).
- Agent version is now `v0.1.1` (workflow name, `cf.agent_runs.agent_version`, scene `agent_version`).

## Authoritative identity for this validation
Series Pokémon the Series: XYZ, season 19, episode 38, "Down to the Fiery Finish!" (Company Brain, 2026-10-13). The schema has no external-identifier column, so the canonical identity is the natural key (title, season 19, episode 38, TV) and no global or production number is stored. Source platform token `OFFICIAL_POKEMON_YOUTUBE`, reference `https://www.youtube.com/watch?v=DiPjyqO-jqU`, access basis `PUBLIC_OFFICIAL_UPLOAD`, observer `VA_HUMAN_RESEARCHER_01`. Prepared (not runnable) intake: `evidence/cf-002-tools/intake/pokemon_xyz_validation_intake.TEMPLATE.json`.

## Timebase note
The boundaries a human reads from the official clip are on the clip timeline, not the full episode timeline. The scene is therefore stored with clip-relative milliseconds, the source reference names the clip, and the notes say so. Episode `duration_seconds` is left unset (the clip length is not the episode length). Consequence: the scene dedupe key does not reconcile the same moment seen later on a different timeline (full episode); a later sprint must reconcile that.

## Still required from a human before the live write
Clip total duration, scene start and end on the clip timeline, and the real time the clip was watched (`observed_at`). This environment cannot reach YouTube (proxy returns 403), so nothing was guessed.
