'use strict';
// Builds the n8n Workflow SDK source for CF-001 from the tested Code-node files and SQL files, so the deployed code is the tested code.
// Usage: node build_workflow.js   (writes generated/cf001_workflow.sdk.ts and generated/cf001_test_workflow.sdk.ts)
const fs = require('fs');
const path = require('path');
const { assemble } = require('./test/harness');
const S = JSON.stringify;
const sql = (f) => fs.readFileSync(path.join(__dirname, 'sql', f), 'utf8').split('\n').filter((l) => !/^\s*--/.test(l)).join('\n').trim();
const code = (f) => assemble(f).split('\n').filter((l) => !/^\s*\/\/(?! ----)/.test(l)).join('\n').trim();
const CRED = "{ postgres: { id: 'e08pNFP1Th42jXyO', name: 'Postgres account' } }";   // n8n credential reference only; no secret material
const pg = (v, name, file, repl, extra) => `const ${v} = node({ type: 'n8n-nodes-base.postgres', version: 2.7, config: { name: ${S(name)}, credentials: ${CRED},${extra || ''}
  parameters: { resource: 'database', operation: 'executeQuery', query: ${S(sql(file))}${repl ? ',\n    options: { queryReplacement: expr(' + S('{{ ' + repl + ' }}') + ') }' : ''} } } });\n`;
const cd = (v, name, file, extra) => `const ${v} = node({ type: 'n8n-nodes-base.code', version: 2, config: { name: ${S(name)},${extra || ''}
  parameters: { mode: 'runOnceForAllItems', language: 'javaScript', jsCode: ${S(code(file))} } } });\n`;
const RC = "$('Run Config').first().json", RI = "$('Resolve Identities').first().json", BR = "$('Begin Run').first().json";
let w = "import { workflow, node, trigger, ifElse, expr } from '@n8n/workflow-sdk';\n\n";
w += "const manual = trigger({ type: 'n8n-nodes-base.manualTrigger', version: 1, config: { name: 'Manual Trigger' } });\n";
w += cd('runConfig', 'Run Config', '01_run_config.js');
w += pg('beginRun', 'Begin Run', '01_begin_run.sql', `[${RC}.idempotency_basis, ${RC}.input_state_basis, JSON.stringify(${RC}.input_ids), $workflow.id, String($execution.id)]`);
w += "const isStarted = ifElse({ version: 2.3, config: { name: 'Run Started?', parameters: { conditions: { options: { caseSensitive: true, leftValue: '', typeValidation: 'strict', version: 2 }, conditions: [{ leftValue: expr('{{ $json.disposition }}'), rightValue: 'STARTED', operator: { type: 'string', operation: 'equals' } }], combinator: 'and' } } } });\n";
w += pg('loadOutputs', 'Load Existing Run Outputs', '02_load_run_outputs.sql', `[${BR}.agent_run_id]`);
w += cd('replaySummary', 'Replay Summary', '10_replay_summary.js');
w += cd('buildReq', 'Build AniList Requests', '02_build_requests.js');
w += `const anilist = node({ type: 'n8n-nodes-base.httpRequest', version: 4.5, config: { name: 'AniList GraphQL', retryOnFail: true, maxTries: 2, waitBetweenTries: 3000, onError: 'continueRegularOutput',
  parameters: { method: 'POST', url: 'https://graphql.anilist.co', authentication: 'none', sendHeaders: true,
    headerParameters: { parameters: [{ name: 'Content-Type', value: 'application/json' }, { name: 'Accept', value: 'application/json' }] },
    sendBody: true, contentType: 'json', specifyBody: 'json', jsonBody: expr(${S('{{ { query: $json.query, variables: $json.variables } }}')}),
    options: { batching: { batch: { batchSize: 1, batchInterval: 1500 } }, timeout: 20000, response: { response: { fullResponse: true, neverError: true } } } } } });\n`;
w += cd('validate', 'Validate Response', '03_validate_response.js');
w += cd('normalise', 'Normalise Media Records', '04_normalise.js');
w += cd('score', 'Score Signals', '05_score.js');
w += cd('select', 'Select Candidates', '06_select.js');
w += pg('loadFranchises', 'Load Franchise Keys', '03_load_franchise_keys.sql', null, " alwaysOutputData: true, onError: 'continueErrorOutput',");
w += cd('resolve', 'Resolve Identities', '07_resolve_identities.js');
w += "const runOk = ifElse({ version: 2.3, config: { name: 'Run Still OK?', parameters: { conditions: { options: { caseSensitive: true, leftValue: '', typeValidation: 'strict', version: 2 }, conditions: [{ leftValue: expr('{{ $json.ok }}'), rightValue: '', operator: { type: 'boolean', operation: 'true', singleValue: true } }], combinator: 'and' } } } });\n";
const E = " onError: 'continueErrorOutput',";
w += pg('insF', 'Insert Franchises', '04_insert_franchises.sql', `[JSON.stringify(${RI}.payload.franchises), ${BR}.agent_run_id]`, E);
w += pg('insT', 'Insert Titles', '05_insert_titles.sql', `[JSON.stringify(${RI}.payload.titles), ${BR}.agent_run_id]`, E);
w += pg('promoRef', 'Promote Reference Rows', '06_promote_reference_rows.sql', `[JSON.stringify(${RI}.payload.franchises), JSON.stringify(${RI}.payload.titles)]`, E);
w += pg('insC', 'Insert Candidates', '07_insert_candidates.sql', `[JSON.stringify(${RI}.payload.candidates), ${RC}.window, ${BR}.agent_run_id]`, E + ' alwaysOutputData: true,');
w += pg('promoC', 'Promote Candidates', '08_promote_candidates.sql', `[JSON.stringify(${RI}.payload.candidates), ${RC}.window]`, E + ' alwaysOutputData: true,');
w += pg('complete', 'Complete Run', '09_complete_run.sql', `[${BR}.agent_run_id, $('AniList GraphQL').all().length, JSON.stringify(${RI}.summary), ${RC}.window, JSON.stringify(${RI}.anilist_ids)]`, E + ' alwaysOutputData: true,');
w += cd('retSummary', 'Return Run Summary', '09_return_summary.js');
w += cd('shapeFail', 'Shape Failure', '08_shape_failure.js');
w += pg('markFailed', 'Mark Run Failed', '10_mark_run_failed.sql', "[$json.agent_run_id, $json.error_code, $json.error_detail, $json.provider_call_count, JSON.stringify($json.output_summary)]", ' alwaysOutputData: true,');
w += cd('raiseFail', 'Raise Failure', '11_raise_failure.js');
w += `
export default workflow('cf001-market-trend-radar-v01', 'CF-001 — Market & Trend Radar v0.1')
  .add(manual).to(runConfig).to(beginRun).to(isStarted
    .onTrue(buildReq.to(anilist).to(validate).to(normalise).to(score).to(select).to(loadFranchises).to(resolve).to(runOk
      .onTrue(insF.to(insT).to(promoRef).to(insC).to(promoC).to(complete).to(retSummary))
      .onFalse(shapeFail.to(markFailed).to(raiseFail))))
    .onFalse(loadOutputs.to(replaySummary)));
loadFranchises.onError(shapeFail);
insF.onError(shapeFail);
insT.onError(shapeFail);
promoRef.onError(shapeFail);
insC.onError(shapeFail);
promoC.onError(shapeFail);
complete.onError(shapeFail);
`;
fs.mkdirSync(path.join(__dirname, 'generated'), { recursive: true });
fs.writeFileSync(path.join(__dirname, 'generated', 'cf001_workflow.sdk.ts'), w);

// ---- TEST workflow (inactive, manual): parameter probe + rolled-back negative tests as the same restricted credential ----
const neg = fs.readFileSync(path.join(__dirname, 'test', 'negative_phase_b.sql'), 'utf8').split('\n').filter((l) => !/^--/.test(l)).join('\n').trim();
let t = "import { workflow, node, trigger, expr } from '@n8n/workflow-sdk';\n\n";
t += "const manual = trigger({ type: 'n8n-nodes-base.manualTrigger', version: 1, config: { name: 'Manual Trigger' } });\n";
t += `const probe = node({ type: 'n8n-nodes-base.postgres', version: 2.7, config: { name: 'Param Probe (read-only)', credentials: ${CRED},
  parameters: { resource: 'database', operation: 'executeQuery', query: ${S("SELECT current_user::text AS current_user_name, session_user::text AS session_user_name, $1::text AS p1, $2::text AS p2, $3::text AS p3, (SELECT count(*) FROM cf.agent_runs) AS runs, (SELECT count(*) FROM cf.research_candidates) AS candidates, (SELECT count(*) FROM cf.anime_titles) AS titles, (SELECT count(*) FROM cf.anime_franchises) AS franchises, (SELECT string_agg(flag_key || '=' || enabled::text, ',' ORDER BY flag_key) FROM cf.system_flags) AS flags")},
    options: { queryReplacement: expr(${S("{{ ['a,b', 'quote\\'s \"x\"', JSON.stringify({ k: [1, 2], s: 'x,y' })] }}")}) } } } });\n`;
t += `const negative = node({ type: 'n8n-nodes-base.postgres', version: 2.7, config: { name: 'Negative Tests (rolled back)', credentials: ${CRED}, onError: 'continueRegularOutput',
  parameters: { resource: 'database', operation: 'executeQuery', query: ${S(neg)} } } });\n`;
t += "export default workflow('cf001-test-db-negative', 'TEST — CF-001 DB negative tests').add(manual).to(probe).to(negative);\n";
fs.writeFileSync(path.join(__dirname, 'generated', 'cf001_test_workflow.sdk.ts'), t);
console.log('main ' + w.length + ' chars; test ' + t.length + ' chars');
