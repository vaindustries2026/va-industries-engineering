-- Begin Run. $1 idempotency basis, $2 input-state basis, $3 input_ids (json text), $4 n8n workflow id, $5 n8n execution id.
-- New key -> INSERT RUNNING (STARTED). Same key + FAILED, or RUNNING older than 15 minutes -> re-claim, attempt_count + 1 (STARTED).
-- Same key + SUCCEEDED -> untouched (REPLAY). Same key + fresh RUNNING -> untouched (IN_PROGRESS).
WITH k AS (
  SELECT encode(sha256(convert_to($1::text, 'UTF8')), 'hex') AS idem,
         encode(sha256(convert_to($2::text, 'UTF8')), 'hex') AS state_hash
), ins AS (
  INSERT INTO cf.agent_runs (agent_code, agent_version, n8n_workflow_id, n8n_execution_id, idempotency_key, input_ids, input_state_hash,
                             run_state, attempt_count, provider_call_count, paid_call_count, estimated_cost_usd, output_summary, started_at)
  SELECT 'CF-002', $3::jsonb->>'agent_version', $4::text, $5::text, k.idem, $3::jsonb, k.state_hash,
         'RUNNING', 1, 0, 0, 0, '{"model":"none","llm_calls":0,"paid_calls":0}'::jsonb, now()
    FROM k
  ON CONFLICT (idempotency_key) DO UPDATE
     SET run_state = 'RUNNING', attempt_count = cf.agent_runs.attempt_count + 1,
         n8n_workflow_id = EXCLUDED.n8n_workflow_id, n8n_execution_id = EXCLUDED.n8n_execution_id,
         provider_call_count = 0, error_code = NULL, error_detail = NULL, finished_at = NULL, started_at = now(),
         output_summary = '{"model":"none","llm_calls":0,"paid_calls":0}'::jsonb
   WHERE cf.agent_runs.run_state = 'FAILED'
      OR (cf.agent_runs.run_state = 'RUNNING' AND cf.agent_runs.started_at < now() - interval '15 minutes')
  RETURNING agent_run_id, run_state, attempt_count, output_summary
)
SELECT agent_run_id, run_state::text AS run_state, attempt_count, output_summary, 'STARTED' AS disposition FROM ins
UNION ALL
SELECT r.agent_run_id, r.run_state::text, r.attempt_count, r.output_summary,
       CASE WHEN r.run_state = 'SUCCEEDED' THEN 'REPLAY' ELSE 'IN_PROGRESS' END
  FROM cf.agent_runs r, k
 WHERE r.idempotency_key = k.idem AND NOT EXISTS (SELECT 1 FROM ins);
