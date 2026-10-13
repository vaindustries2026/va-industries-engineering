const begin = $('Begin Run').first().json;
const row = $input.first().json || {};
const replay = begin.disposition === 'REPLAY';
return [{ json: { result: replay ? 'REPLAY_EXISTING_RUN' : 'RUN_IN_PROGRESS_OR_UNAVAILABLE', disposition: begin.disposition,
  agent_run_id: row.agent_run_id || begin.agent_run_id, run_state: row.run_state || begin.run_state, attempt_count: row.attempt_count || begin.attempt_count,
  existing_output_summary: row.output_summary || begin.output_summary, existing_scenes: row.scenes || [], provider_calls_this_execution: 0, paid_calls: 0 } }];
