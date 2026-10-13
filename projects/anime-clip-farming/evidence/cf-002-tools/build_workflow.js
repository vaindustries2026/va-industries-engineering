'use strict';
// Builds the n8n Workflow SDK source for CF-002 from the tested Code-node files and SQL files, so the deployed code is the tested code.
// Usage: node build_workflow.js   (writes generated/cf002_workflow.sdk.ts and generated/cf002_test_workflow.sdk.ts)
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
const RC = "$('Run Config').first().json", BR = "$('Begin Run').first().json", VP = "$('Validate Provenance').first().json", PL = VP + '.payload';
const EP = "$('Upsert Episode').first().json.source_episode_id";
const IF = (v, name, leftExpr, op) => `const ${v} = ifElse({ version: 2.3, config: { name: ${S(name)}, parameters: { conditions: { options: { caseSensitive: true, leftValue: '', typeValidation: 'strict', version: 2 }, conditions: [{ leftValue: expr(${S('{{ ' + leftExpr + ' }}')}), rightValue: ${op.right}, operator: ${op.op} }], combinator: 'and' } } } });\n`;
let w = "import { workflow, node, trigger, ifElse, expr } from '@n8n/workflow-sdk';\n\n";
w += "const manual = trigger({ type: 'n8n-nodes-base.manualTrigger', version: 1, config: { name: 'Manual Trigger' } });\n";
w += cd('runConfig', 'Run Config', '01_run_config.js');
w += pg('beginRun', 'Begin Run', '01_begin_run.sql', `[${RC}.idempotency_basis, ${RC}.input_state_basis, JSON.stringify(${RC}.input_ids), $workflow.id, String($execution.id)]`);
w += IF('isStarted', 'Run Started?', '$json.disposition', { right: "'STARTED'", op: "{ type: 'string', operation: 'equals' }" });
w += pg('loadOutputs', 'Load Existing Run Outputs', '02_load_run_outputs.sql', `[${BR}.agent_run_id]`);
w += cd('replaySummary', 'Replay Summary', '12_replay_summary.js');
const E = " onError: 'continueErrorOutput',";
w += pg('upstream', 'Validate Upstream', '03_validate_upstream.sql', `[String((${RC}.intake || {}).research_candidate_id || ''), String((${RC}.intake || {}).anime_title_id || '')]`, E + ' alwaysOutputData: true,');
w += cd('resolveTitle', 'Resolve Title', '04_resolve_title.js');
w += cd('validateObs', 'Validate Observation', '05_validate_observation.js');
w += cd('normalise', 'Normalise Boundaries', '06_normalise_boundaries.js');
w += cd('buildIntel', 'Build Intelligence', '07_build_intelligence.js');
w += cd('validateProv', 'Validate Provenance', '08_validate_provenance.js');
w += IF('runOk', 'Run Still OK?', '$json.ok', { right: "''", op: "{ type: 'boolean', operation: 'true', singleValue: true }" });
w += IF('hasInput', 'Has Input?', '$json.zero_input', { right: "''", op: "{ type: 'boolean', operation: 'false', singleValue: true }" });
const TID = "$('Bootstrap Catalog').first().json.anime_title_id";
w += pg('bootCat', 'Bootstrap Catalog', '03b_bootstrap_catalog.sql', `[JSON.stringify(${PL}.catalog), String(${PL}.anime_title_id || ''), ${BR}.agent_run_id]`, E);
w += pg('upEp', 'Upsert Episode', '04_upsert_episode.sql', `[JSON.stringify(${PL}.episode), ${TID}, ${BR}.agent_run_id]`, E);
w += pg('proEp', 'Promote Episode', '05_promote_episode.sql', `[${EP}]`, E);
w += pg('insSc', 'Insert Scenes', '06_insert_scenes.sql', `[JSON.stringify(${PL}.scenes), ${EP}, ${TID}, String(${PL}.research_candidate_id || ''), ${BR}.agent_run_id, 'v0.1.1']`, E + ' alwaysOutputData: true,');
w += pg('proSc', 'Promote Scenes', '07_promote_scenes.sql', `[${EP}, JSON.stringify(${PL}.boundaries)]`, E + ' alwaysOutputData: true,');
w += pg('verify', 'Verify Persisted', '08_verify_persisted.sql', `[${EP}, JSON.stringify(${PL}.boundaries), ${TID}]`, E);
w += pg('complete', 'Complete Run', '09_complete_run.sql', `[${BR}.agent_run_id, JSON.stringify(${VP}.summary), ${VP}.payload === null ? 'null' : JSON.stringify($('Verify Persisted').first().json.verification)]`, E + ' alwaysOutputData: true,');
w += cd('retSummary', 'Return Run Summary', '09_return_summary.js');
w += cd('shapeFail', 'Shape Failure', '10_shape_failure.js');
w += pg('markFailed', 'Mark Run Failed', '10_mark_run_failed.sql', "[$json.agent_run_id, $json.error_code, $json.error_detail, $json.provider_call_count, JSON.stringify($json.output_summary)]", ' alwaysOutputData: true,');
w += cd('raiseFail', 'Raise Failure', '11_raise_failure.js');
w += `
export default workflow('cf002-scene-intelligence-v011', 'CF-002 — Scene Intelligence & Provenance v0.1.1')
  .add(manual).to(runConfig).to(beginRun).to(isStarted
    .onTrue(upstream.to(resolveTitle).to(validateObs).to(normalise).to(buildIntel).to(validateProv).to(runOk
      .onTrue(hasInput
        .onTrue(bootCat.to(upEp).to(proEp).to(insSc).to(proSc).to(verify).to(complete).to(retSummary))
        .onFalse(complete))
      .onFalse(shapeFail.to(markFailed).to(raiseFail))))
    .onFalse(loadOutputs.to(replaySummary)));
upstream.onError(shapeFail);
bootCat.onError(shapeFail);
upEp.onError(shapeFail);
proEp.onError(shapeFail);
insSc.onError(shapeFail);
proSc.onError(shapeFail);
verify.onError(shapeFail);
complete.onError(shapeFail);
`;
fs.mkdirSync(path.join(__dirname, 'generated'), { recursive: true });
fs.writeFileSync(path.join(__dirname, 'generated', 'cf002_workflow.sdk.ts'), w);
console.log('main ' + w.length + ' chars');
