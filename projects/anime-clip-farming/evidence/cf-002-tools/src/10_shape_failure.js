const j = $input.first().json || {};
const run = $('Begin Run').first().json;
let code, detail;
if (j.ok === false && j.error_code) { code = j.error_code; detail = j.error_detail || ''; }
else { code = 'CF002_DB_ERROR'; const e = j.error !== undefined ? j.error : j; detail = typeof e === 'string' ? e : JSON.stringify(e && e.message ? { message: e.message, code: e.code } : e); }
detail = String(detail).slice(0, 500);
const summary = { result: 'FAILED', error_code: code, model: 'none', llm_calls: 0, provider_calls: 0, paid_calls: 0, publication_source_status: 'UNKNOWN', persisted_scenes: 0 };
return [{ json: { agent_run_id: run.agent_run_id, error_code: code, error_detail: detail, provider_call_count: 0, output_summary: summary } }];
