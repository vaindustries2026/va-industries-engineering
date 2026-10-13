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

## Lineage constraint found (2026-10-13)
`anime_scene_intelligence.research_candidate_id` is nullable, so no fake candidate is needed. But `anime_title_id` and the episode FK require an existing `cf.anime_titles` row, and no Pokémon title exists (the 8 CF-001 titles are different). Also the v0.1 workflow validators require a candidate id. Smallest safe mechanism proposed: workflow patch v0.1.1 with an explicit `validation_mode = CF002_VALIDATION_SOURCE_OUTSIDE_CF001_BATCH` that allows a null candidate, plus a title/franchise insert by the CF-002 run (runtime role already has INSERT; rows carry the CF-002 agent_run_id, DRAFT status, and the lineage marker in notes). Not built yet: awaiting the timestamps and a go on creating those two rows.
