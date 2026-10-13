// @include common
// Validate Response: fail closed on any provider problem. Records rate-limit evidence. No partial runs.
const cfg = $('Run Config').first().json;
const reqs = $('Build AniList Requests').all();
const resp = $input.all();
const retrievedAt = new Date().toISOString();
const http = [];
const lanes = [];
let err = null;
function hdr(h, name) { return h && h[name] !== undefined ? String(h[name]) : null; }
function fail(code, detail, extra) { if (!err) err = Object.assign({ error_code: code, error_detail: detail }, extra || {}); }
for (let i = 0; i < reqs.length; i++) {
  const rq = reqs[i].json;
  const r = resp[i] ? resp[i].json : null;
  const row = { lane: rq.lane, status_code: null, rate_limit_limit: null, rate_limit_remaining: null, retry_after: null, records: 0, outcome: 'OK' };
  if (!r || r.error !== undefined && r.statusCode === undefined) {
    row.outcome = 'NETWORK_ERROR';
    fail('CF001_ANILIST_NETWORK_ERROR', 'no HTTP response for lane ' + rq.lane + ' (timeout or connection failure)');
    http.push(row); continue;
  }
  const h = r.headers || {};
  row.status_code = r.statusCode;
  row.rate_limit_limit = hdr(h, 'x-ratelimit-limit');
  row.rate_limit_remaining = hdr(h, 'x-ratelimit-remaining');
  row.retry_after = hdr(h, 'retry-after');
  if (r.statusCode === 429) { row.outcome = 'RATE_LIMITED'; fail('CF001_ANILIST_RATE_LIMITED', 'HTTP 429 on lane ' + rq.lane, { retry_after: row.retry_after }); http.push(row); continue; }
  if (r.statusCode === 401 || r.statusCode === 403) { row.outcome = 'FORBIDDEN'; fail('CF001_ANILIST_UNAVAILABLE', 'HTTP ' + r.statusCode + ' on lane ' + rq.lane); http.push(row); continue; }
  if (r.statusCode >= 500) { row.outcome = 'SERVER_ERROR'; fail('CF001_ANILIST_5XX', 'HTTP ' + r.statusCode + ' on lane ' + rq.lane); http.push(row); continue; }
  let body = r.body;
  if (typeof body === 'string') { try { body = JSON.parse(body); } catch (e) { body = null; } }
  if (r.statusCode !== 200 && !(body && Array.isArray(body.errors))) { row.outcome = 'HTTP_ERROR'; fail('CF001_ANILIST_HTTP_ERROR', 'HTTP ' + r.statusCode + ' on lane ' + rq.lane); http.push(row); continue; }
  if (!body || typeof body !== 'object') { row.outcome = 'MALFORMED'; fail('CF001_ANILIST_MALFORMED_RESPONSE', 'body is not a JSON object on lane ' + rq.lane); http.push(row); continue; }
  if (Array.isArray(body.errors) && body.errors.length > 0) {
    row.outcome = 'GRAPHQL_ERROR';
    fail('CF001_ANILIST_GRAPHQL_ERROR', 'GraphQL error on lane ' + rq.lane + ': ' + String((body.errors[0] && body.errors[0].message) || 'unknown').slice(0, 200));
    http.push(row); continue;
  }
  const media = body.data && body.data.Page && body.data.Page.media;
  if (!Array.isArray(media)) { row.outcome = 'MALFORMED'; fail('CF001_ANILIST_MALFORMED_RESPONSE', 'data.Page.media is not an array on lane ' + rq.lane); http.push(row); continue; }
  row.records = media.length;
  http.push(row);
  lanes.push({ lane: rq.lane, sort: rq.sort, filters: rq.filters, media: media });
}
const base = { request_count: reqs.length, http: http, retrieved_at: retrievedAt };
if (err) return [{ json: Object.assign({ ok: false }, base, err) }];
return [{ json: Object.assign({ ok: true }, base, { lanes: lanes }) }];
