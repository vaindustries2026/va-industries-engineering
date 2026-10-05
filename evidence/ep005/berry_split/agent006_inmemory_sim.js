// In-memory, read-only Agent-006 simulation. Runs the UNMODIFIED jsCode of nodes 03, 05, 07 and 08
// taken from the Agent-006 workflow export (workflows/AGENT006_ZTBdnKFO8STSjJU4_S52_DRAFT_9bf6bbef.json,
// identical to live 9bf6bbef) against a manifest row and APPROVED/LOCKED registry rows read by GET.
// No n8n execution, no writes. The manifest row's status is forced to APPROVED in memory only (models the
// post-human-approval state) unless KEEP_STATUS=1 is set.
// Usage: node agent006_inmemory_sim.js <workflow_export.json> <manifest_row.json> <governed_registry.json>
const fs = require('fs');
const [wfPath, rowPath, regPath] = process.argv.slice(2);
let wf = JSON.parse(fs.readFileSync(wfPath)); wf = wf.workflow || wf;
const code = p => wf.nodes.find(n => n.name.startsWith(p)).parameters.jsCode;
const run = (src, input, refs) => new Function('$input', '$', src)(
  { first: () => input[0], all: () => input, item: input[0] },
  name => ({ first: () => refs[name][0], all: () => refs[name] }));
let row = JSON.parse(fs.readFileSync(rowPath)); if (Array.isArray(row)) row = row[0];
row = Object.assign({}, row, { id: row.id || '00000000-0000-0000-0000-00000000d001' });
if (process.env.KEEP_STATUS !== '1') row.status = 'APPROVED';
const gov = JSON.parse(fs.readFileSync(regPath));
const req = [{ json: { production_manifest_id: row.id, asset_resolution_run_id: 'INMEMORY-SIM', agent_version: 'sim', prompt_version: 'sim' } }];
const ctx = run(code('03 '), [{ json: row }], { '00 - Normalize Asset Resolution Request': req });
const items = run(code('05 '), gov.map(r => ({ json: r })), { '03 - Prepare Resolution Context': ctx });
const out = items.map(it => {
  const o = run(code('07 '), [it], {})[0];
  let v08 = 'ok'; try { run(code('08 '), [o], { '07 - Resolve Current Asset Requirement': [o] }); } catch (e) { v08 = 'ERR ' + e.message; }
  const j = o.json;
  return { requirement_key: j.requirement_key, origin: j.requirement_origin, label: j.source_label, shots: j.source_shot_ids,
           exact: j.exact_candidate_asset_ids, resolution: j.resolution_status, canonical_asset_id: j.canonical_asset_id, node08: v08 };
});
console.log(JSON.stringify({ manifest: row.id, status_in_memory: row.status, governed: items[0].json.governed_registry_summary, requirement_count: out.length, requirements: out }, null, 1));
