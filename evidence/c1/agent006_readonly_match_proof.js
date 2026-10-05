// C1 read-only Agent-006 match proof harness. Runs the unmodified jsCode of Agent-006 (ZTBdnKFO8STSjJU4, version 9bf6bbef) nodes 03, 05, 07
// locally against GET-only snapshots of the approved manifest and the APPROVED/LOCKED asset_registry rows. Performs no writes.
// Usage: node agent006_readonly_match_proof.js <dir containing 03.js 05.js 07.js manifest.json gov.json>
const fs=require('fs'),S=process.argv[2];
const code=n=>fs.readFileSync(`${S}/${n}.js`,'utf8');
const run=(src,input,refs)=>{const $input={first:()=>input[0],all:()=>input};const $=name=>({first:()=>refs[name][0],all:()=>refs[name]});return new Function('$input','$',src)($input,$);};
const row=JSON.parse(fs.readFileSync(`${S}/manifest.json`))[0];
const gov=JSON.parse(fs.readFileSync(`${S}/gov.json`));
const req=[{json:{production_manifest_id:row.id,asset_resolution_run_id:'C1-READONLY-PROOF',agent_version:'proof',prompt_version:'proof'}}];
const ctx=run(code('03'),[{json:row}],{'00 - Normalize Asset Resolution Request':req});
const items=run(code('05'),gov.map(r=>({json:r})),{'03 - Prepare Resolution Context':ctx});
const out=items.map(it=>run(code('07'),[it],{})[0].json);
const targets=['Mikko','Lumi','Canonical environment/background'];
console.log('manifest',row.id,row.status,'requirements',out.length,'governed rows',gov.length, 'governed_ids', items[0].json.governed_registry_summary);
for(const o of out) console.log([o.requirement_key,o.requirement_origin,o.source_label,'exact=',JSON.stringify(o.exact_candidate_asset_ids),'=>',o.resolution_status,o.canonical_asset_id].join(' | '));
const res={};for(const t of targets){const m=out.filter(o=>o.source_label===t);res[t]=m.map(o=>({key:o.requirement_key,exact:o.exact_candidate_asset_ids,status:o.resolution_status,canonical:o.canonical_asset_id}));}
console.log('TARGETS',JSON.stringify(res,null,1));
