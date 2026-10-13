// Return Run Summary (success path)
const done = $input.first().json;
if (!done || !done.agent_run_id) { throw new Error('CF001_COMPLETE_FAILED: run could not be completed (not in RUNNING state)'); }
const ctx = $('Run Config').first().json;
return [{ json: { result: done.output_summary.result, agent_run_id: done.agent_run_id, run_state: done.run_state, workflow: 'CF-001 Market & Trend Radar v0.1',
  observation_window: ctx.window, output_summary: done.output_summary } }];
