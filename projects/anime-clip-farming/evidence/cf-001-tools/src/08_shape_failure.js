// Shape Failure: one structured failure object from either a failed pure stage or a failed DB node.
const j = $input.first().json || {};
const run = $('Begin Run').first().json;
let calls = 0;
try { if ($('AniList GraphQL').isExecuted) calls = $('AniList GraphQL').all().length; } catch (e) { calls = 0; }
let code, detail, retryAfter = null, http = null;
if (j.ok === false && j.error_code) { code = j.error_code; detail = j.error_detail || ''; retryAfter = j.retry_after || null; http = j.http || null; }
else {
  code = 'CF001_DB_ERROR';
  const e = j.error !== undefined ? j.error : j;
  detail = typeof e === 'string' ? e : JSON.stringify(e && e.message ? { message: e.message, code: e.code } : e);
}
detail = String(detail).slice(0, 500);
const summary = { result: 'FAILED', error_code: code, model: 'none', llm_calls: 0, paid_calls: 0, provider_calls: calls, retry_after: retryAfter, http: http };
return [{ json: { agent_run_id: run.agent_run_id, error_code: code, error_detail: detail, provider_call_count: calls, output_summary: summary } }];
