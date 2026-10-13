// Raise Failure: the run row is already FAILED; make the n8n execution fail visibly too.
const f = $('Shape Failure').first().json;
const m = $input.first().json;
if (!m || !m.agent_run_id) { throw new Error('CF001_FAILURE_NOT_RECORDED: ' + f.error_code + ' - could not mark run FAILED'); }
throw new Error(f.error_code + ': ' + f.error_detail + ' (agent_run recorded as FAILED)');
