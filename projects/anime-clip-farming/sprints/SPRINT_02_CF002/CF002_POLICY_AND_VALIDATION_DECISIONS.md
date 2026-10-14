# CF-002 policy and validation decisions

Recorded 2026-10-13 from the Company Brain decision relayed by Aquila (08:59Z).

## CF002-POLICY-SPOILER-001
Spoiler level is descriptive metadata, not a universal eligibility gate. Legacy/nostalgia content is not blocked by spoiler severity. Recent/current content may use spoiler-aware downstream handling.

Product/business-rule correction: the business is built on anime memory and meaning, with a large nostalgia/legacy share, and audiences engage with legacy content because they remember the outcome. So `spoiler_level` must not block CF-002 persistence, reduce eligibility, prevent CF-003 consideration, or imply a scene is unsafe to discuss. The field stays in the schema (needed for current-anime content). Spoiler metadata (the field) is separated from spoiler gating policy (a future downstream rule keyed on content age, to be formalised later). Current code: CF-002 only stores the value and never gates on it; no migration change is needed.

## CF002-VALIDATION-POKEMON-001 — SUPERSEDED_BEFORE_LIVE_PERSISTENCE (cancelled 2026-10-14)
The Pokémon case was replaced before anything was written; it is kept as history. No Pokémon catalog row, episode or scene exists (checked live 2026-10-14). Its intake file is renamed `pokemon_xyz_validation_intake.SUPERSEDED_BEFORE_LIVE_PERSISTENCE.json`. The v0.1.1 mechanism below is unchanged and is reused by the new case.

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

## CF002-VALIDATION-DIGIMON-001 (2026-10-14, replaces CF002-VALIDATION-POKEMON-001)
Digimon Adventure tri., Chapter 1 Reunion (released 2015-11-21), Crunchyroll presentation "E4 Reunion Part 4", was selected as the bounded live CF-002 validation case because a human can watch it directly.
- Scene: Alphamon's first major combat confrontation with the DigiDestined, ending with the Alphamon vs Omnimon battle. Described editorially as Alphamon's first major battle and full combat appearance against the DigiDestined in tri., never as its literal first visual appearance.
- Source: platform `CRUNCHYROLL`, basis `HUMAN_VIEWED_LICENSED_PLATFORM`, observer `VA_HUMAN_RESEARCHER_01`. Research access only; `publication_source_status` stays UNKNOWN; nothing about licensing, fair use, monetisation or redistribution is inferred. No download, no DRM bypass.
- Source timebase: `source_timebase=CRUNCHYROLL_REUNION_PART_4`, stored in `source.notes` (existing `research_access_notes`), no migration. Timestamps are on the E4 player timeline and are not converted to the Chapter 1 movie timeline; reconciliation is left to a later sprint.
- Lineage: Digimon is not among the 8 CF-001 candidates (live check 2026-10-14: no Digimon or Pokémon catalog rows, 8 candidates, 0 episodes, 0 scenes). Mode `CF002_VALIDATION_SOURCE_OUTSIDE_CF001_BATCH`, `research_candidate_id = NULL`, Bootstrap Catalog creates at most one `digimon` franchise and one `digimon adventure tri.` title, both DRAFT. No fabricated CF-001 lineage.
- Persistence limit: 1 agent run, 1 franchise and 1 title if absent, 1 source episode, 1 scene. Then a replay of the identical observation.
- Identity CONFIRMED by the Company Brain 2026-10-14: title `Digimon Adventure tri.`, title type MOVIE, variant MOVIE, start_year 2015, part number 4, part title `Reunion Part 4`. The canonical Toei work is Digimon Adventure tri. Chapter 1 Reunion (a movie); Crunchyroll presents it in episodic segments. `season_number` is NOT NULL in 0004 (natural key, integer 0-99), so `season_number = 1` is used only as a Crunchyroll source-presentation locator, with the scene note `SOURCE_PRESENTATION_ONLY - Crunchyroll episodic segmentation; canonical work is Digimon Adventure tri. Chapter 1 "Reunion" (movie)`. No schema change.
- Prepared, not runnable: `evidence/cf-002-tools/intake/digimon_tri_e4_validation_intake.TEMPLATE.json`. Human must supply: E4 player duration, scene start (Alphamon fully confronts the group for the major battle) and end (after the Omnimon confrontation ends and Alphamon retreats) on the E4 timeline, and the real observation time.
- Spoiler: CF002-POLICY-SPOILER-001 applies; `spoiler_level` is informational and blocks nothing.
