-- Load Run Outputs (replay / in-progress branch). $1 agent_run_id. Read-only.
SELECT r.agent_run_id, r.run_state::text AS run_state, r.attempt_count, r.output_summary,
       (SELECT coalesce(jsonb_agg(jsonb_build_object('research_candidate_id', c.research_candidate_id, 'anime_title_id', c.anime_title_id,
                                                      'dedupe_key', c.dedupe_key, 'status', c.status::text) ORDER BY c.dedupe_key), '[]'::jsonb)
          FROM cf.research_candidates c WHERE c.agent_run_id = r.agent_run_id) AS candidates
  FROM cf.agent_runs r WHERE r.agent_run_id = $1::uuid;
