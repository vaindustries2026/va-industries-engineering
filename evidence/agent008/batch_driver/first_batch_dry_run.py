"""READ-ONLY first-batch dry run of AGENT008_BATCH_DRIVER_v0.1 (PLAN_ONLY; no generation, provider call or production write).

Usage (repo root): python3 evidence/agent008/batch_driver/first_batch_dry_run.py <out_json>
1. Live specs of APPROVED readiness 69bff641 (GET snapshot) and the live registry (GET) build the inventory of approved
   artifacts; the frame-family map comes from the committed preflight (EP005_BASE_FRAME_PREFLIGHT_v1.json).
2. PLAN_ONLY over the explicit allowlist S001, S004, S005, S012, S013, S017, S019, S025, S026, run twice (determinism).
3. FUTURE_FLOW_SIMULATION: the same driver over status-only synthetic inventories (no files, no writes) showing the state
   sequence a still shot and a provider-motion shot will walk once approvals arrive.
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

KIND = {'GEN': 'GENERATE'}
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
    if x['asset_subtype'] == 'DIALOGUE' and md.get('shot_id'):
        inventory.setdefault(md['shot_id'], {}).setdefault('dialogue', []).append(
            {'audio_asset_id': x['asset_id'], 'status': x['status'], 'sha256': md.get('sha256'), 'speaker': md.get('speaker'),
             'text': md.get('text')})
    if x['asset_type'] == 'SHOT_RENDER' and md.get('shot_id'):
        inventory.setdefault(md['shot_id'], {})['final'] = {'status': x['status'], 'sha256': md.get('sha256')}

batch = {'batch_id': 'EP005-FIRST-FRAME-BATCH-DRY-RUN-v1', 'shot_ids': FIRST, 'mode': 'PLAN_ONLY'}
plan_a, _ = B.execute(batch, specs, families, inventory)
plan_b, _ = B.execute(copy.deepcopy(batch), specs, families, copy.deepcopy(inventory))
manifest = B.review_manifest(plan_a)
rows = []
for s in plan_a['shots']:
    sid = s['SHOT_ID']
    t = s['G08_REQUIREMENT']['treatments']
    rows.append({'SHOT_ID': sid, 'FRAME_FAMILY': families[sid]['family_id'], 'FRAME_KIND': families[sid]['kind'],
                 'CURRENT_BATCH_STATE': s['STATE'], 'BLOCKER': (s['CURRENT_BLOCKERS'] or [None])[0],
                 'NEXT_REQUIRED_HUMAN_GATE': s['NEXT_REQUIRED_HUMAN_GATE'], 'NEXT_REQUIRED_AUTOMATED_STAGE': s['NEXT_REQUIRED_AUTOMATED_STAGE'],
                 'DIALOGUE_COUNT': len(s['DIALOGUE_REQUIREMENTS']),
                 'G03_RECORD_COUNT': 1 if s['G03_REQUIREMENT']['record_required'] else 0,
                 'G03_OVERLAYS': len(s['G03_REQUIREMENT']['overlays']),
                 'G08_RECORD_COUNT': 1 if s['G08_REQUIREMENT']['record_required'] else 0,
                 'G08_TREATMENTS': [x.split('EP005-')[1][:-4] for x in t],
                 'EVENT_TIMING_REQUIRED': s['AUDIO_REQUIREMENTS']['events'],
                 'PROVIDER_VIDEO_CALL_REQUIRED': s['PROVIDER_MOTION_REQUIRED'],
                 'EXPECTED_FINAL_PRODUCTION_PATH': ('frame -> G03 static -> provider preflight -> [spend auth] -> Seedance -> '
                                                    '[raw approval] -> motion assembly x2 -> REVIEW') if s['PROVIDER_MOTION_REQUIRED'] else
                                                   ('frame -> G03 -> ' + ('G08 reflection -> ' if 'TREATMENT-EP005-MIRROR-REFLECTION-v01' in t else '')
                                                    + 'G02 still x2 (' + ('glint/pop frame-exact, ' if any('GLINT' in x or 'POP' in x for x in t) else '')
                                                    + 'dialogue G09) -> QC -> REVIEW'),
                 'OUTSTANDING': s['OUTSTANDING']})


# ---- FUTURE_FLOW_SIMULATION: status-only inventories, same driver, PLAN_ONLY ----
def walk(sid, steps):
    inv, seq = {sid: {}}, []
    for label, upd in steps:
        upd(inv)
        s = B.plan_batch({'batch_id': 'SIM', 'shot_ids': [sid], 'mode': 'PLAN_ONLY'}, specs, families, inv)['shots'][0]
        seq.append({'after': label, 'STATE': s['STATE'], 'human_gate': s['NEXT_REQUIRED_HUMAN_GATE'],
                    'automated_stage': s['NEXT_REQUIRED_AUTOMATED_STAGE']})
    return seq


def setp(sid, key, val):
    return lambda inv: inv[sid].__setitem__(key, val)


lines25 = [{'speaker': d['speaker'], 'text': d['text']} for d in specs['S025']['spec']['dialogue_slots']]
lines01 = [{'speaker': d['speaker'], 'text': d['text']} for d in specs['S001']['spec']['dialogue_slots']]
FR = {'asset_id': 'FUTURE', 'classification': 'SHOT_FRAME/BASE_FRAME', 'sha256': 'f' * 64}
still = walk('S025', [
    ('start (no frame)', lambda inv: None),
    ('F01 frame generated -> REVIEW', setp('S025', 'frame', {**FR, 'status': 'REVIEW'})),
    ('frame APPROVED', setp('S025', 'frame', {**FR, 'status': 'APPROVED'})),
    ('G08 record approved', setp('S025', 'g08_record', {'status': 'APPROVED'})),
    ('pop SFX timing approved', setp('S025', 'timing', {'status': 'APPROVED', 'named': {'SFX-COMPLETION-POP-v01': {}}})),
    ('Lumi clip generated -> REVIEW', setp('S025', 'dialogue', [{**l, 'status': 'REVIEW'} for l in lines25])),
    ('Lumi clip APPROVED', setp('S025', 'dialogue', [{**l, 'status': 'APPROVED'} for l in lines25])),
    ('LOCAL_RENDER_ONLY produced REVIEW shot', setp('S025', 'final', {'status': 'REVIEW'})),
    ('final shot APPROVED', setp('S025', 'final', {'status': 'APPROVED'}))])
motion = walk('S001', [
    ('start (no frame)', lambda inv: None),
    ('F01 frame APPROVED', setp('S001', 'frame', {**FR, 'status': 'APPROVED'})),
    ('G03 record approved', setp('S001', 'g03_record', {'status': 'APPROVED'})),
    ('both clips APPROVED', setp('S001', 'dialogue', [{**l, 'status': 'APPROVED'} for l in lines01])),
    ('PROVIDER_PREFLIGHT_ONLY froze the package', setp('S001', 'motion', {'preflight_sha256': 'a' * 64})),
    ('spend authorised with ceiling', setp('S001', 'motion', {'preflight_sha256': 'a' * 64,
                                                              'authorisation': {'human_approved': True, 'spend_ceiling_usd': 3.5}})),
    ('(future paid mode) submitted', setp('S001', 'motion', {'submitted': True})),
    ('raw output retrieved', setp('S001', 'motion', {'result': {'status': 'COMPLETED'}})),
    ('raw motion APPROVED', setp('S001', 'motion', {'result': {'status': 'APPROVED'}})),
    ('assembly produced REVIEW shot', setp('S001', 'final', {'status': 'REVIEW'})),
    ('final shot APPROVED', setp('S001', 'final', {'status': 'APPROVED'}))])

out = {'batch': batch, 'plan_sha256_run_a': plan_a['plan_sha256'], 'plan_sha256_run_b': plan_b['plan_sha256'],
       'deterministic': plan_a == plan_b, 'FIRST_BATCH_DRY_RUN': rows, 'BATCH_REVIEW_MANIFEST': manifest, 'plan': plan_a,
       'FUTURE_FLOW_SIMULATION': {'S025_deterministic_still': still, 'S001_provider_motion': motion},
       'production_writes': 0, 'provider_calls': 0}
Path(sys.argv[1]).write_text(json.dumps(out, indent=1, ensure_ascii=False))
print('deterministic', out['deterministic'], plan_a['plan_sha256'][:16])
for x in rows:
    print(x['SHOT_ID'], x['FRAME_FAMILY'], x['CURRENT_BATCH_STATE'], x['BLOCKER'], 'dlg', x['DIALOGUE_COUNT'], 'g03', x['G03_RECORD_COUNT'],
          x['G03_OVERLAYS'], 'g08', x['G08_RECORD_COUNT'], x['G08_TREATMENTS'], 'events', x['EVENT_TIMING_REQUIRED'], 'video', x['PROVIDER_VIDEO_CALL_REQUIRED'])
print({k: v for k, v in manifest.items() if k.endswith('COUNT')})
for name, seq in out['FUTURE_FLOW_SIMULATION'].items():
    print(name, ' -> '.join(f"{x['STATE']}" for x in seq))
