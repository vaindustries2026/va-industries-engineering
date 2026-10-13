-- Complete Run. $1 agent_run_id, $2 provider_call_count, $3 JS-side summary json, $4 window, $5 json array of anilist ids in the payload.
UPDATE cf.agent_runs r
   SET run_state = 'SUCCEEDED', provider_call_count = $2::int, finished_at = now(), error_code = NULL, error_detail = NULL,
       output_summary = $3::jsonb || jsonb_build_object('db_verified', (
         SELECT jsonb_build_object('candidates_for_payload_in_window', count(*),
                                   'created_by_this_run', count(*) FILTER (WHERE c.agent_run_id = r.agent_run_id),
                                   'ready', count(*) FILTER (WHERE c.status = 'READY'),
                                   'rejected', count(*) FILTER (WHERE c.status = 'REJECTED'),
                                   'idea_left', count(*) FILTER (WHERE c.status = 'IDEA'))
           FROM cf.research_candidates c JOIN cf.anime_titles t ON t.anime_title_id = c.anime_title_id
          WHERE c.observation_window = $4::text
            AND t.anilist_id IN (SELECT e::bigint FROM jsonb_array_elements_text($5::jsonb) AS e)))
 WHERE r.agent_run_id = $1::uuid AND r.run_state = 'RUNNING'
RETURNING r.agent_run_id, r.run_state::text AS run_state, r.output_summary;
