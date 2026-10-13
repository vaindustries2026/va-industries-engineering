-- Load Existing Run Outputs (replay / in-progress branch). $1 agent_run_id. Read-only.
SELECT r.agent_run_id, r.run_state::text AS run_state, r.attempt_count, r.output_summary,
       (SELECT coalesce(jsonb_agg(jsonb_build_object('scene_id', s.scene_id, 'source_episode_id', s.source_episode_id, 'anime_title_id', s.anime_title_id,
                                                      'dedupe_key', s.dedupe_key, 'status', s.status::text, 'start_ms', s.start_ms, 'end_ms', s.end_ms,
                                                      'research_source_platform', s.research_source_platform, 'research_source_reference', s.research_source_reference,
                                                      'research_access_basis', s.research_access_basis::text, 'publication_source_status', v.publication_source_status)
                                  ORDER BY s.start_ms, s.end_ms), '[]'::jsonb)
          FROM cf.anime_scene_intelligence s JOIN cf.v_scene_publication_status v ON v.scene_id = s.scene_id
         WHERE s.scene_id IN (SELECT (e ->> 'scene_id')::uuid FROM jsonb_array_elements(coalesce(r.output_summary -> 'verification' -> 'scenes', '[]'::jsonb)) e)) AS scenes
  FROM cf.agent_runs r WHERE r.agent_run_id = $1::uuid;
