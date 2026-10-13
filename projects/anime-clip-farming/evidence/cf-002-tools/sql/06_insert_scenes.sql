-- Persist Scene Intelligence (deterministic scene dedupe). $1 scenes json, $2 source_episode_id, $3 anime_title_id, $4 research_candidate_id, $5 agent_run_id, $6 agent_version.
-- dedupe_key = sha256(source_episode_id | floor(start_ms/1000) | ceil(end_ms/1000)); a replay conflicts and inserts nothing.
-- A different span that overlaps an existing scene of the episode by >= 80% of the shorter span is inserted as DRAFT and flagged, never merged.
WITH x AS (
  SELECT s.*, encode(sha256(convert_to($2::text || '|' || (s.start_ms / 1000)::text || '|' || ((s.end_ms + 999) / 1000)::text, 'UTF8')), 'hex') AS dk
    FROM jsonb_to_recordset($1::jsonb) AS s(ordinal int, start_ms int, end_ms int, characters_present jsonb, scene_summary text, scene_function text, why_scene_matters text,
         possible_editorial_angles jsonb, context_requirement text, spoiler_level text, visual_strength numeric, nostalgia_signal numeric, editorial_strength text,
         research_source_platform text, research_source_reference text, research_access_basis text, research_access_notes text,
         research_observed_at timestamptz, research_observer text, timestamps_human_verified boolean)
)
INSERT INTO cf.anime_scene_intelligence (source_episode_id, anime_title_id, research_candidate_id, start_ms, end_ms, characters_present, scene_summary, scene_function,
       why_scene_matters, possible_editorial_angles, context_requirement, spoiler_level, visual_strength, nostalgia_signal, editorial_strength,
       research_source_platform, research_source_reference, research_access_basis, research_access_notes, research_observed_at, research_observer,
       timestamps_human_verified, possible_duplicate_of_scene_id, dedupe_key, status, agent_run_id, agent_version)
SELECT $2::uuid, $3::uuid, NULLIF($4::text, '')::uuid, x.start_ms, x.end_ms,
       coalesce(ARRAY(SELECT jsonb_array_elements_text(x.characters_present)), ARRAY[]::text[]), x.scene_summary, x.scene_function,
       x.why_scene_matters, coalesce(ARRAY(SELECT jsonb_array_elements_text(x.possible_editorial_angles)), ARRAY[]::text[]), x.context_requirement,
       x.spoiler_level, x.visual_strength, x.nostalgia_signal, x.editorial_strength,
       x.research_source_platform, x.research_source_reference, x.research_access_basis::cf.research_access_basis, x.research_access_notes, x.research_observed_at, x.research_observer,
       coalesce(x.timestamps_human_verified, false),
       (SELECT o.scene_id FROM cf.anime_scene_intelligence o
         WHERE o.source_episode_id = $2::uuid AND o.dedupe_key <> x.dk
           AND LEAST(o.end_ms, x.end_ms) - GREATEST(o.start_ms, x.start_ms) > 0
           AND (LEAST(o.end_ms, x.end_ms) - GREATEST(o.start_ms, x.start_ms))::numeric >= 0.8 * LEAST(o.end_ms - o.start_ms, x.end_ms - x.start_ms)
         ORDER BY (LEAST(o.end_ms, x.end_ms) - GREATEST(o.start_ms, x.start_ms)) DESC, o.scene_id LIMIT 1),
       x.dk, 'DRAFT', $5::uuid, $6::text
  FROM x ORDER BY x.ordinal
ON CONFLICT (dedupe_key) DO NOTHING
RETURNING scene_id, dedupe_key, start_ms, end_ms, possible_duplicate_of_scene_id;
