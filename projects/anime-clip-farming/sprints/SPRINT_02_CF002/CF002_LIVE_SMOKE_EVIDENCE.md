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
