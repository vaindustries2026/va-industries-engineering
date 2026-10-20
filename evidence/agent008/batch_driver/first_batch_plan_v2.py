"""READ-ONLY first-batch PLAN_ONLY v2 after the Company Brain Batch 1 base-frame review (no provider call, no write).

Usage (repo root): python3 evidence/agent008/batch_driver/first_batch_plan_v2.py <out_json>
Same driver, allowlist and family map as first_batch_dry_run.py (v1), plus the human decisions now recorded:
  __families__: F01 REJECTED (c191a513...), F03 REJECTED (e8571476...), F09 APPROVED (d442b0f7..., live registry row)
  S017 frame: the live APPROVED registry row FRAME-EP005-F09-BASE-CAND-v01 (shot_id S017)
  S019 frame: the local F15 REVIEW candidate FRAME-EP005-F15-BASE-CAND-v01 (no registry row; human approval pending)
"""
import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from agent008 import batch as B  # noqa: E402
from agent008.config import load_output_spec  # noqa: E402
from agent008.episode import PINS, resolve_episode  # noqa: E402
from agent008.inputs import load_hash_pins  # noqa: E402
from agent008.motion.http import UrllibHttpClient  # noqa: E402
from agent008.tools.snapshot_inputs import build_snapshot  # noqa: E402

SB = 'https://ziluiwrwwbayhcskeere.supabase.co'
READINESS = '69bff641-e056-4701-a23f-d91dbc2039b2'
FIRST = ['S001', 'S004', 'S005', 'S012', 'S013', 'S017', 'S019', 'S025', 'S026']
B1 = ROOT / 'evidence/ep005/batch1_base_frames'
pre = json.loads((ROOT / 'evidence/ep005/base_frame_preflight/EP005_BASE_FRAME_PREFLIGHT_v1.json').read_text())
r = UrllibHttpClient().send('GET', f'{SB}/rest/v1/asset_registry?select=asset_id,status,asset_type,asset_subtype,metadata_json',
                            {'Accept': 'application/json'})
if r.status != 200:
    sys.exit('STOP: registry GET failed')
reg = json.loads(r.body)
specs = {x['shot_id']: x for x in resolve_episode(build_snapshot(READINESS), load_hash_pins(PINS), load_output_spec())}

families = {}
for f in pre['families']:
    for sid in f['members']:
        if f['id'] == 'F11-S027-START-REUSE':
            src = pre['reference_assets_live']['FRAME-EP005-S027-BASE-v01']
            fam = {'kind': 'REUSE_APPROVED_ASSET', 'source': {'asset_id': 'FRAME-EP005-S027-BASE-v01', 'sha256': src['sha256']}}
        elif f['id'] == 'F15-MACRO-REFLECTION':
            fam = {'kind': 'DERIVE_CROP', 'source': {'family_id': 'F09-MEDIUM-TWOSHOT-MIRROR-FRONT'},
                   'crop': 'MEASURED_AFTER_F09_APPROVAL', 'scale': {'w': 1920, 'h': 1080}}
        elif f['kind'] == 'GEN':
            fam = {'kind': 'GENERATE'}
        else:
            fam = {'kind': 'DERIVE_MOTION_END', 'source': {'shot_id': {'F12-S007-END': 'S007', 'F13-S010-END': 'S010',
                                                                       'F14-S014-END': 'S014', 'F16-S020-S021-END': 'S021'}[f['id']]}}
        families[sid] = {'family_id': f['id'], **fam, 'provider_motion': pre['shots'][sid]['provider_motion']}

inventory = {'__assets__': {}, '__families__': {}}
for x in reg:
    md = x['metadata_json'] or {}
    if x['asset_type'] == 'SHOT_FRAME':
        inventory['__assets__'][x['asset_id']] = {'status': x['status'], 'sha256': md.get('sha256')}
        if md.get('shot_id') in specs:
            inventory.setdefault(md['shot_id'], {})['frame'] = {'asset_id': x['asset_id'], 'status': x['status'],
                                                               'sha256': md.get('sha256'), 'classification': f"{x['asset_type']}/{x['asset_subtype']}"}
        if md.get('frame_family'):
            inventory['__families__'][md['frame_family']] = {'asset_id': x['asset_id'], 'status': x['status'], 'sha256': md.get('sha256')}
    if x['asset_subtype'] == 'DIALOGUE' and md.get('shot_id'):
        inventory.setdefault(md['shot_id'], {}).setdefault('dialogue', []).append(
            {'audio_asset_id': x['asset_id'], 'status': x['status'], 'sha256': md.get('sha256'), 'speaker': md.get('speaker'),
             'text': md.get('text')})
    if x['asset_type'] == 'SHOT_RENDER' and md.get('shot_id'):
        inventory.setdefault(md['shot_id'], {})['final'] = {'status': x['status'], 'sha256': md.get('sha256')}

# human decisions recorded in evidence (rejected candidates were never registered)
review = [json.loads(l) for l in (B1 / 'B1_REVIEW_LEDGER_v1.jsonl').read_text().splitlines() if l.strip()]
for e in review:
    if e['event'] == 'HUMAN_REJECTED':
        fid = {'F01': 'F01-MIRROR-OPEN', 'F03': 'F03-OVERSHOULDER-LUMI'}[e['family']]
        inventory['__families__'][fid] = {'asset_id': e['frame_id'], 'status': 'REJECTED', 'sha256': e['reviewed_normalised_sha256']}
assert inventory['__families__'].get('F09-MEDIUM-TWOSHOT-MIRROR-FRONT', {}).get('status') == 'APPROVED', 'F09 not approved live'
f15 = json.loads((B1 / 'FRAME-EP005-F15-BASE-CAND-v01_REVIEW_CANDIDATE.json').read_text())
inventory.setdefault('S019', {})['frame'] = {'asset_id': f15['frame_id'], 'status': 'REVIEW', 'sha256': f15['F15_OUTPUT_SHA_A'],
                                            'classification': 'SHOT_FRAME/BASE_FRAME'}

batch = {'batch_id': 'EP005-FIRST-FRAME-BATCH-PLAN-v2', 'shot_ids': FIRST, 'mode': 'PLAN_ONLY'}
plan_a, _ = B.execute(batch, specs, families, inventory)
plan_b, _ = B.execute(copy.deepcopy(batch), specs, families, copy.deepcopy(inventory))
rows = [{'SHOT_ID': s['SHOT_ID'], 'FRAME_FAMILY': families[s['SHOT_ID']]['family_id'], 'STATE': s['STATE'],
         'BLOCKER': (s['CURRENT_BLOCKERS'] or [None])[0], 'NEXT_HUMAN_GATE': s['NEXT_REQUIRED_HUMAN_GATE'],
         'NEXT_AUTOMATED_STAGE': s['NEXT_REQUIRED_AUTOMATED_STAGE'], 'OUTSTANDING': s['OUTSTANDING']} for s in plan_a['shots']]
out = {'batch': batch, 'plan_sha256_run_a': plan_a['plan_sha256'], 'plan_sha256_run_b': plan_b['plan_sha256'],
       'deterministic': plan_a == plan_b, 'families_state': inventory['__families__'], 'FIRST_BATCH_STATE_v2': rows,
       'BATCH_REVIEW_MANIFEST': B.review_manifest(plan_a), 'plan': plan_a, 'production_writes': 0, 'provider_calls': 0}
Path(sys.argv[1]).write_text(json.dumps(out, indent=1, ensure_ascii=False))
print('deterministic', out['deterministic'], plan_a['plan_sha256'][:16])
for x in rows:
    print(x['SHOT_ID'], x['FRAME_FAMILY'], x['STATE'], '|', x['BLOCKER'], '|', x['NEXT_HUMAN_GATE'], '|', x['NEXT_AUTOMATED_STAGE'])
