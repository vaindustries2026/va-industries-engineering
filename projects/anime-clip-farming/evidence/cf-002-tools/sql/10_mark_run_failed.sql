-- Mark Run Failed. $1 agent_run_id, $2 error_code, $3 error_detail, $4 provider_call_count, $5 output_summary json. No candidates are touched.
UPDATE cf.agent_runs
   SET run_state = 'FAILED', error_code = $2::text, error_detail = $3::text, provider_call_count = $4::int, finished_at = now(), output_summary = $5::jsonb
 WHERE agent_run_id = $1::uuid AND run_state = 'RUNNING'
RETURNING agent_run_id, run_state::text AS run_state, error_code;
