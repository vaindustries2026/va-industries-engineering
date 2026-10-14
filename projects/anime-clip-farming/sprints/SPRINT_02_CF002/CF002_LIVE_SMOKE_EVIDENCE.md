# CF-002 live smoke evidence

## Executed
- Run 598 (live, zero input, basis NO_INPUT): SUCCEEDED, agent run `36d3b817-9650-4df0-b185-0539491aed09`, paid 0, cost 0, 0 scenes.
- Run 599: REPLAY of the same run, 0 writes.

## Database state after (project mkeldytatorxxszjdngt)
agent_runs 2 (1 CF-001, 1 CF-002); research_candidates 8 (unchanged, still READY); anime_source_episodes 0; anime_scene_intelligence 0; kill switches all false. CF-001 rows untouched.

## Why no scene was persisted
The brief requires a real human research observation. None was supplied, and none was invented. Status: `CF002_BUILD_COMPLETE_LIVE_SOURCE_PENDING`.

## Exact human requirement to finish
Provide, for one of the 8 CF-001 candidates (candidate id and its title id), one episode and 1-3 scenes:
1. Episode locator: season, episode number, variant.
2. Durable safe source reference (slug like `human-observation:...` or an https URL with no tokens) and `research_access_basis`.
3. Observer name or initials and `observed_at` (not in the future).
4. Per scene: start and end (MM:SS or ms), an original concise summary, why it matters, spoiler level.
The intake is embedded in Run Config `DEFAULT_INTAKE` and run once via execute_workflow. Needs explicit authorisation as a bounded task.

## Update 2026-10-13 (v0.1.1, Pokémon validation approved) — SUPERSEDED_BEFORE_LIVE_PERSISTENCE
Live state is unchanged: 8 franchises, 8 titles, 8 candidates (all CF-001), 0 episodes, 0 scenes, 2 agent runs, paid 0, cost 0 (checked after the rolled-back execution 600). The Pokémon scene is not persisted: this environment cannot reach the official clip (YouTube returns 403 through the proxy), and exact timestamps were not guessed.
Needed from a human: clip total duration, scene start and end on the clip timeline, and the real time the clip was watched. Everything else is prepared in `evidence/cf-002-tools/intake/pokemon_xyz_validation_intake.TEMPLATE.json`. Once supplied, the intake is embedded in Run Config `DEFAULT_INTAKE`, run once, then replayed.

## Update 2026-10-14: validation case changed to Digimon Adventure tri. E4
Pokémon was cancelled before any live write. Live check 2026-10-14: no Digimon or Pokémon catalog rows; 8 franchises, 8 titles, 8 candidates, 0 episodes, 0 scenes. Waiting for the human observer (`VA_HUMAN_RESEARCHER_01`) to supply the Crunchyroll E4 player duration, scene start and end, and the real observation time. See CF002_POLICY_AND_VALIDATION_DECISIONS.md (CF002-VALIDATION-DIGIMON-001).

Update 2026-10-14 (later): episode identity confirmed (see CF002-VALIDATION-DIGIMON-001). Season 1 is a source-presentation locator only, recorded in the scene note. Still waiting for the human's E4 player duration, scene start/end and observation time.
