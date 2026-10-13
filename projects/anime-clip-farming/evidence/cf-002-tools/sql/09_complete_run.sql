-- Complete agent_run. $1 agent_run_id, $2 summary json (planned), $3 verification json or 'null'.
-- SUCCEEDED only when every expected scene was found; otherwise FAILED / CF002_VERIFY_MISMATCH (rows already written stay, they are valid).
UPDATE cf.agent_runs r
   SET run_state = (CASE WHEN v.verification IS NULL OR ((v.verification ->> 'expected_scenes')::int = (v.verification ->> 'found_scenes')::int
                                                          AND (v.verification ->> 'all_publication_unknown')::boolean) THEN 'SUCCEEDED' ELSE 'FAILED' END)::cf.run_state,
       error_code = CASE WHEN v.verification IS NULL OR ((v.verification ->> 'expected_scenes')::int = (v.verification ->> 'found_scenes')::int
                                                          AND (v.verification ->> 'all_publication_unknown')::boolean) THEN NULL ELSE 'CF002_VERIFY_MISMATCH' END,
       provider_call_count = 0, finished_at = now(),
       output_summary = $2::jsonb || CASE WHEN v.verification IS NULL THEN '{}'::jsonb ELSE jsonb_build_object('verification', v.verification) END
  FROM (SELECT NULLIF($3::jsonb, 'null'::jsonb) AS verification) v
 WHERE r.agent_run_id = $1::uuid AND r.run_state = 'RUNNING'
RETURNING r.agent_run_id, r.run_state::text AS run_state, r.output_summary;
