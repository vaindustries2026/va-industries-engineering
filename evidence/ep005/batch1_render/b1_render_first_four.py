"""EP005 Batch 1: refresh the batch plan after the approved G03/G08 records and render the shots that are READY_FOR_LOCAL_RENDER
(LOCAL_RENDER_ONLY, existing Agent-008 runners; no provider call, no new capability).

Usage (repo root): python3 evidence/ep005/batch1_render/b1_render_first_four.py <scratch dir>
Inventory = live registry only (first_batch_plan_v3 rules) + the APPROVED PRODUCTION_RECORD rows (G03/G08) as the shots'
g03_record / g08_record ({record, approval_status, expected_sha256 = record_sha256}). Inputs (frames, overlays, ambience)
are read from production storage and verified against their registry SHA. The whole LOCAL_RENDER_ONLY batch is executed
twice into independent work dirs (each run already renders A/B inside the runner); all four renders must be identical.
"""
import copy
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
from agent008 import batch as B  # noqa: E402
from agent008.config import load_output_spec  # noqa: E402
from agent008.episode import PINS, resolve_episode  # noqa: E402
from agent008.hashing import sha256_file  # noqa: E402
from agent008.inputs import load_hash_pins  # noqa: E402
from agent008.motion.http import UrllibHttpClient  # noqa: E402
from agent008.tools.snapshot_inputs import build_snapshot  # noqa: E402

SB = 'https://ziluiwrwwbayhcskeere.supabase.co'
FIRST = ['S001', 'S004', 'S005', 'S012', 'S013', 'S017', 'S019', 'S025', 'S026']
http = UrllibHttpClient()


def get(path):
    r = http.send('GET', f'{SB}{path}', {'Accept': 'application/json'}, None, 120.0)
    if r.status != 200:
        sys.exit(f'STOP: GET {path} HTTP {r.status}')
    return r


def build(work):
    pre = json.loads((ROOT / 'evidence/ep005/base_frame_preflight/EP005_BASE_FRAME_PREFLIGHT_v1.json').read_text())
    reg = json.loads(get('/rest/v1/asset_registry?select=id,asset_id,status,asset_type,asset_subtype,storage_path,metadata_json').body)
    specs = {x['shot_id']: x for x in resolve_episode(build_snapshot('69bff641-e056-4701-a23f-d91dbc2039b2'),
                                                      load_hash_pins(PINS), load_output_spec())}
    families = {}
    for f in pre['families']:
        for sid in f['members']:
            if f['id'] == 'F11-S027-START-REUSE':
                src = pre['reference_assets_live']['FRAME-EP005-S027-BASE-v01']
                fam = {'kind': 'REUSE_APPROVED_ASSET', 'source': {'asset_id': 'FRAME-EP005-S027-BASE-v01', 'sha256': src['sha256']}}
            elif f['kind'] == 'GEN' or f['id'] == 'F15-MACRO-REFLECTION':
                fam = {'kind': 'GENERATE'}
            else:
                fam = {'kind': 'DERIVE_MOTION_END', 'source': {'shot_id': {'F12-S007-END': 'S007', 'F13-S010-END': 'S010',
                                                                           'F14-S014-END': 'S014', 'F16-S020-S021-END': 'S021'}[f['id']]}}
            families[sid] = {'family_id': f['id'], **fam, 'provider_motion': pre['shots'][sid]['provider_motion']}
    inventory, rowmap = {'__assets__': {}, '__families__': {}}, {}
    for x in reg:
        md = x['metadata_json'] or {}
        rowmap[x['asset_id']] = x
        if x['asset_type'] == 'SHOT_FRAME':
            e = {'asset_id': x['asset_id'], 'registry_id': x['id'], 'status': x['status'], 'sha256': md.get('sha256'),
                 'classification': f"{x['asset_type']}/{x['asset_subtype']}"}
            inventory['__assets__'][x['asset_id']] = {'status': x['status'], 'sha256': md.get('sha256')}
            for sid in md.get('frame_family_members') or ([md['shot_id']] if md.get('shot_id') else []):
                if sid in specs:
                    if 'frame' in inventory.get(sid, {}):
                        sys.exit(f'STOP: two frames bound to {sid}')
                    inventory.setdefault(sid, {})['frame'] = e
            if md.get('frame_family'):
                inventory['__families__'][md['frame_family']] = e
        if x['asset_type'] == 'PRODUCTION_RECORD' and md.get('shot_id') in specs:
            key = {'G03_PLACEMENT_RECORD': 'g03_record', 'G08_TREATMENT_RECORD': 'g08_record'}[x['asset_subtype']]
            inventory.setdefault(md['shot_id'], {})[key] = {'record': md['record'], 'approval_status': x['status'],
                                                           'expected_sha256': md['record_sha256'], 'asset_id': x['asset_id'],
                                                           'status': x['status']}
        if x['asset_subtype'] == 'DIALOGUE' and md.get('shot_id'):
            inventory.setdefault(md['shot_id'], {}).setdefault('dialogue', []).append(
                {'audio_asset_id': x['asset_id'], 'status': x['status'], 'sha256': md.get('sha256'), 'speaker': md.get('speaker'),
                 'text': md.get('text')})
        if x['asset_type'] == 'SHOT_RENDER' and md.get('shot_id'):
            inventory.setdefault(md['shot_id'], {})['final'] = {'status': x['status'], 'sha256': md.get('sha256')}
    return specs, families, inventory, rowmap


def fetch_inputs(work, rowmap, ids):
    paths = {}
    for aid in ids:
        r = rowmap[aid]
        p = Path(work) / 'inputs' / Path(r['storage_path']).name
        p.parent.mkdir(parents=True, exist_ok=True)
        if not p.exists():
            p.write_bytes(get(f"/storage/v1/object/authenticated/{r['storage_path']}").body)
        if sha256_file(p) != r['metadata_json']['sha256'] or r['status'] not in ('APPROVED', 'LOCKED'):
            sys.exit(f'STOP: {aid} not APPROVED at its registry SHA')
        paths[aid] = p
    return paths


def main(work):
    work = Path(work)
    specs, families, inventory, rowmap = build(work)
    plan_batch = {'batch_id': 'EP005-FIRST-FRAME-BATCH-PLAN-v4', 'shot_ids': FIRST, 'mode': 'PLAN_ONLY'}
    plan_a, _ = B.execute(plan_batch, specs, families, inventory)
    plan_b, _ = B.execute(copy.deepcopy(plan_batch), specs, families, copy.deepcopy(inventory))
    ready = [s['SHOT_ID'] for s in plan_a['shots'] if s['STATE'] == 'READY_FOR_LOCAL_RENDER']
    need = set()
    for sid in ready:
        need.add(inventory[sid]['frame']['asset_id'])
        sp = specs[sid]['spec']
        need |= {o['asset_id'] for o in sp['active_overlays']} | {b['asset_id'] for b in sp['mapped_audio']}
    paths = fetch_inputs(work, rowmap, sorted(need))
    runners = B.local_runners(specs, families, paths, load_output_spec())
    rb = {'batch_id': 'EP005-BATCH1-FIRST-FOUR-RENDER-v1', 'shot_ids': FIRST, 'mode': 'LOCAL_RENDER_ONLY'}
    runs = {}
    for label in ('RUN1', 'RUN2'):
        plan, results = B.execute(copy.deepcopy(rb), specs, families, copy.deepcopy(inventory), work / label, runners)
        runs[label] = {'plan_sha256': plan['plan_sha256'], 'results': results, 'manifest': B.review_manifest(plan, results)}
    shots = {}
    for sid in ready:
        r1, r2 = runs['RUN1']['results'][sid], runs['RUN2']['results'][sid]
        f1 = work / 'RUN1' / sid / 'renderA' / f'{sid}_STILL_REVIEW.mp4'
        f2 = work / 'RUN2' / sid / 'renderA' / f'{sid}_STILL_REVIEW.mp4'
        shots[sid] = {'run1': r1, 'run2': r2,
                      'SHOT_A_SHA': (r1.get('result') or {}).get('output_shas', {}).get('review_mp4'),
                      'SHOT_B_SHA': (r2.get('result') or {}).get('output_shas', {}).get('review_mp4'),
                      'files': {'run1_renderA': str(f1), 'run2_renderA': str(f2)}}
        shots[sid]['DETERMINISM_PASS'] = bool(shots[sid]['SHOT_A_SHA']) and shots[sid]['SHOT_A_SHA'] == shots[sid]['SHOT_B_SHA'] \
            and sha256_file(f1) == sha256_file(f2) == shots[sid]['SHOT_A_SHA']
    state = [{'SHOT_ID': s['SHOT_ID'], 'FRAME_FAMILY': families[s['SHOT_ID']]['family_id'], 'STATE': s['STATE'],
              'BLOCKER': (s['CURRENT_BLOCKERS'] or [None])[0], 'NEXT_HUMAN_GATE': s['NEXT_REQUIRED_HUMAN_GATE'],
              'NEXT_AUTOMATED_STAGE': s['NEXT_REQUIRED_AUTOMATED_STAGE'], 'OUTSTANDING': s['OUTSTANDING']} for s in plan_a['shots']]
    out = {'plan_only': {'plan_sha256_a': plan_a['plan_sha256'], 'plan_sha256_b': plan_b['plan_sha256'],
                         'deterministic': plan_a == plan_b, 'state': state},
           'ready_for_local_render': ready, 'inputs': {k: {'path_name': Path(v).name, 'sha256': sha256_file(v)} for k, v in paths.items()},
           'records_bound': {sid: {k: inventory.get(sid, {}).get(k, {}).get('asset_id') for k in ('g03_record', 'g08_record')}
                             for sid in FIRST},
           'render_runs': {k: {'plan_sha256': v['plan_sha256'], 'manifest': v['manifest']} for k, v in runs.items()},
           'shots': shots}
    (work / 'RENDER_RESULT.json').write_text(json.dumps(out, indent=1, default=str))
    print('plan deterministic', out['plan_only']['deterministic'], plan_a['plan_sha256'][:16])
    for s in state:
        print(' ', s['SHOT_ID'], s['STATE'], '|', s['BLOCKER'], '|', s['OUTSTANDING'])
    for sid, v in shots.items():
        print(sid, 'A', v['SHOT_A_SHA'], 'B', v['SHOT_B_SHA'], 'PASS' if v['DETERMINISM_PASS'] else 'FAIL',
              v['run1'].get('failed') or v['run1'].get('result', {}).get('qc_status'))


if __name__ == '__main__':
    main(sys.argv[1])
