const done = $input.first().json;
if (!done || !done.agent_run_id) { throw new Error('CF002_COMPLETE_FAILED: run could not be completed (not in RUNNING state)'); }
if (done.run_state !== 'SUCCEEDED') { throw new Error('CF002_VERIFY_MISMATCH: persisted output did not match the expected scenes (run recorded as FAILED)'); }
return [{ json: { result: done.output_summary.result, agent_run_id: done.agent_run_id, run_state: done.run_state, workflow: 'CF-002 — Scene Intelligence & Provenance v0.1', output_summary: done.output_summary } }];
