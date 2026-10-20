"""READ-ONLY first-batch PLAN_ONLY v3 after the Batch 1 frame approvals (no provider call, no write).

Usage (repo root): python3 evidence/agent008/batch_driver/first_batch_plan_v3.py <out_json>
Inventory comes from the live registry only. A SHOT_FRAME row that names a frame_family binds its frame to every member
shot listed in frame_family_members (the authoritative family map); that is how the driver's frame_dict binds a shared
family frame to each member. Family decision applied: F15 is now a dedicated GENERATE family (Company Brain 2026-10-20;
the DERIVE_CROP-from-F09 candidate was rejected). F11/S026 is bound by its REUSE_EXISTING registry row.
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
        elif f['kind'] == 'GEN' or f['id'] == 'F15-MACRO-REFLECTION':        # F15: dedicated generation (decision)
            fam = {'kind': 'GENERATE'}
        else:
            fam = {'kind': 'DERIVE_MOTION_END', 'source': {'shot_id': {'F12-S007-END': 'S007', 'F13-S010-END': 'S010',
                                                                       'F14-S014-END': 'S014', 'F16-S020-S021-END': 'S021'}[f['id']]}}
        families[sid] = {'family_id': f['id'], **fam, 'provider_motion': pre['shots'][sid]['provider_motion']}

inventory = {'__assets__': {}, '__families__': {}}
for x in reg:
    md = x['metadata_json'] or {}
    if x['asset_type'] == 'SHOT_FRAME':
        entry = {'asset_id': x['asset_id'], 'status': x['status'], 'sha256': md.get('sha256'),
                 'classification': f"{x['asset_type']}/{x['asset_subtype']}"}
        inventory['__assets__'][x['asset_id']] = {'status': x['status'], 'sha256': md.get('sha256')}
        for sid in md.get('frame_family_members') or ([md['shot_id']] if md.get('shot_id') else []):
            if sid in specs:
                if 'frame' in inventory.get(sid, {}):
                    sys.exit(f'STOP: two frames bound to {sid}')
                inventory.setdefault(sid, {})['frame'] = entry
        if md.get('frame_family'):
            inventory['__families__'][md['frame_family']] = entry
    if x['asset_subtype'] == 'DIALOGUE' and md.get('shot_id'):
        inventory.setdefault(md['shot_id'], {}).setdefault('dialogue', []).append(
            {'audio_asset_id': x['asset_id'], 'status': x['status'], 'sha256': md.get('sha256'), 'speaker': md.get('speaker'),
             'text': md.get('text')})
    if x['asset_type'] == 'SHOT_RENDER' and md.get('shot_id'):
        inventory.setdefault(md['shot_id'], {})['final'] = {'status': x['status'], 'sha256': md.get('sha256')}

batch = {'batch_id': 'EP005-FIRST-FRAME-BATCH-PLAN-v3', 'shot_ids': FIRST, 'mode': 'PLAN_ONLY'}
plan_a, _ = B.execute(batch, specs, families, inventory)
plan_b, _ = B.execute(copy.deepcopy(batch), specs, families, copy.deepcopy(inventory))
rows = [{'SHOT_ID': s['SHOT_ID'], 'FRAME_FAMILY': families[s['SHOT_ID']]['family_id'],
         'FRAME': (inventory.get(s['SHOT_ID']) or {}).get('frame'), 'STATE': s['STATE'],
         'BLOCKER': (s['CURRENT_BLOCKERS'] or [None])[0], 'NEXT_HUMAN_GATE': s['NEXT_REQUIRED_HUMAN_GATE'],
         'NEXT_AUTOMATED_STAGE': s['NEXT_REQUIRED_AUTOMATED_STAGE'], 'OUTSTANDING': s['OUTSTANDING']} for s in plan_a['shots']]
fam_state = {k: v for k, v in inventory['__families__'].items() if k.split('-')[0] in ('F01', 'F03', 'F09', 'F11', 'F15')}
out = {'batch': batch, 'plan_sha256_run_a': plan_a['plan_sha256'], 'plan_sha256_run_b': plan_b['plan_sha256'],
       'deterministic': plan_a == plan_b, 'families_state': fam_state, 'FIRST_BATCH_STATE_v3': rows,
       'BATCH_REVIEW_MANIFEST': B.review_manifest(plan_a), 'plan': plan_a, 'production_writes': 0, 'provider_calls': 0}
Path(sys.argv[1]).write_text(json.dumps(out, indent=1, ensure_ascii=False))
print('deterministic', out['deterministic'], plan_a['plan_sha256'][:16])
for k, v in fam_state.items():
    print(' ', k, v['asset_id'], v['status'], v['sha256'][:12])
for x in rows:
    print(x['SHOT_ID'], x['FRAME_FAMILY'], (x['FRAME'] or {}).get('asset_id'), x['STATE'], '|', x['NEXT_HUMAN_GATE'], '|',
          x['NEXT_AUTOMATED_STAGE'], '|', x['OUTSTANDING'])
