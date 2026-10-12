"""READ-ONLY G08 live-spec validation + updated remaining-shot factory matrix (no render, no production write, no provider).

Usage (repo root): python3 evidence/agent008/g08/g08_live_spec_validation.py <out_json>
For every remaining EP005 shot (live Agent-008 specs of APPROVED readiness 69bff641, GET snapshot) this runs, in memory,
the gate the shot's production path would hit once its approved inputs exist: the G02 still contract (with a G03 overlay
set, a G08 reflection certificate and a treatment record standing in for the future approved inputs) or the motion
base-frame gate. It checks the manifest-governed G08 constraints (sync audio present as a shot event, glint target active)
on the live specs, and joins the Batch 0D plan (method, base frames, provider calls), the live registry (approved base
frames / dialogue) and the recorded continuity dependencies. Nothing is composited or written to production.
"""
import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from agent008 import g08  # noqa: E402
from agent008.config import load_output_spec  # noqa: E402
from agent008.episode import PINS, resolve_episode  # noqa: E402
from agent008.errors import FailClosed  # noqa: E402
from agent008.inputs import load_hash_pins  # noqa: E402
from agent008.motion.http import UrllibHttpClient  # noqa: E402
from agent008.still import check_still_contract  # noqa: E402
from agent008.tools.snapshot_inputs import build_snapshot  # noqa: E402

SB = 'https://ziluiwrwwbayhcskeere.supabase.co'
READINESS = '69bff641-e056-4701-a23f-d91dbc2039b2'
COMPLETE = ('S027', 'S028', 'S029')
CONTINUITY_FROM = {'S005': 'S004', 'S008': 'S007', 'S011': 'S010', 'S013': 'S012', 'S019': 'S018', 'S022': 'S021', 'S023': 'S022'}
MOTION_FOR_PLANNING = {'S006'}
OPEN_GAPS = {'S024': ['G06_KEYFRAMED_CROP_SCALE'], 'S018': ['G07_IN_SHOT_CUT'],
             'S009': ['G11_TRACKED_OVERLAY_REMOVAL'], 'S015': ['G11_TRACKED_OVERLAY_REMOVAL'], 'S021': ['G11_TRACKED_OVERLAY_REMOVAL']}
PENDING = 'G0X-INPUT-PENDING'


def plan_table():
    tree = ast.parse((ROOT / 'evidence/agent008/scaleout/build_ep005_production_matrix.py').read_text())
    for node in tree.body:
        if isinstance(node, ast.Assign) and [t.id for t in node.targets if isinstance(t, ast.Name)] == ['C']:
            return ast.literal_eval(node.value)
    sys.exit('STOP: plan table not found')


PLAN = plan_table()
matrix = {s['shot_id']: s for s in json.loads((ROOT / 'evidence/agent008/batch0d/EP005_AGENT008_PRODUCTION_MATRIX_v3.json').read_text())['shots']}
before = json.loads((ROOT / 'evidence/agent008/g03/G03_LIVE_SPEC_VALIDATION_AND_MATRIX_v1.json').read_text())
audit = json.loads((ROOT / 'evidence/agent008/g08/G08_REQUIREMENT_AUDIT_v1.json').read_text())
spec = load_output_spec()
resolved = {r['shot_id']: r for r in resolve_episode(build_snapshot(READINESS), load_hash_pins(PINS), spec)}
r = UrllibHttpClient().send('GET', f'{SB}/rest/v1/asset_registry?select=asset_id,status,asset_type,asset_subtype,metadata_json',
                            {'Accept': 'application/json'})
reg = json.loads(r.body)
frames_ok = {(x['metadata_json'] or {}).get('shot_id') for x in reg if x['asset_type'] == 'SHOT_FRAME' and x['status'] in ('APPROVED', 'LOCKED')}

rows = []
for sid, rr in sorted(resolved.items()):
    if sid in COMPLETE:
        continue
    sp, m = rr.get('spec') or {}, matrix[sid]
    method = PLAN[sid][0]
    motion = method in ('B', 'C') or m['classification'] == 'HIGGSFIELD_MOTION_REQUIRED' or sid in MOTION_FOR_PLANNING
    ids = [t['treatment_id'] for t in sp.get('treatments') or []]
    other = list(OPEN_GAPS.get(sid, []))
    g08_status, gate, governed = 'NOT_REQUIRED', None, []
    if rr['status'] == 'SPEC':
        comp = ({'shot_id': sid, 'frame_sha256': PENDING + '-G03',
                 'overlays': [{'asset_id': o['asset_id'], 'sha256': o['expected_sha256'], 'surface': 'FACE'} for o in sp['active_overlays']]}
                if sp['active_overlays'] else None)
        tcomp = ({'shot_id': sid, 'input_frame_sha256': PENDING + '-G03' if comp else PENDING + '-BASE', 'frame_sha256': PENDING,
                  'record_sha256': PENDING + '-REC', 'treatments': [g08.REFL], 'mode': 'PRESERVE|COMPOSITE', 'reflected_overlays': []}
                 if g08.REFL in ids else None)
        frame_sha = PENDING if (tcomp or comp) else None
        if comp and not tcomp:
            comp['frame_sha256'] = PENDING
        try:
            if ids:
                g08.spec_treatments(sp)
            if motion:
                g08.motion_gate(sp, PENDING, comp, tcomp)
                gate = 'MOTION_BASE_FRAME_GATE_PASS'
            else:
                check_still_contract(sp, spec, comp, frame_sha, tcomp, {'record': 'pending'} if ids else None)
                gate = 'G02_STILL_GATE_PASS'
        except FailClosed as e:
            gate = e.code
        for (gsid, tid), aid in g08.GOVERNED['sync'].items():
            if gsid == sid:
                ev = [x['asset_id'] for x in (sp.get('named_sfx') or []) + (sp.get('event_audio') or [])]
                governed.append(f"sync {tid[15:]} -> {aid}: {'PRESENT as shot event' if aid in ev else 'MISSING'}")
        if sid in g08.GOVERNED['glint_target']:
            tgt = g08.GOVERNED['glint_target'][sid]
            governed.append(f"glint target {tgt}: {'ACTIVE overlay' if tgt in [o['asset_id'] for o in sp['active_overlays']] else 'NOT ACTIVE'}")
        if ids:
            ok = gate in ('MOTION_BASE_FRAME_GATE_PASS', 'G02_STILL_GATE_PASS') or gate == 'STILL_IN_SHOT_CUT_NEEDS_G07'
            g08_status = 'SUPPORTED' if ok and all('MISSING' not in x and 'NOT ACTIVE' not in x for x in governed) else f'BLOCKED ({gate})'
            if motion and any(t != g08.REFL for t in ids):
                g08_status = 'BLOCKED (timed treatment on motion)'
        if gate == 'STILL_IN_SHOT_CUT_NEEDS_G07' and 'G07_IN_SHOT_CUT' not in other:
            other.append('G07_IN_SHOT_CUT')
        if gate and gate not in ('MOTION_BASE_FRAME_GATE_PASS', 'G02_STILL_GATE_PASS', 'STILL_IN_SHOT_CUT_NEEDS_G07'):
            other.append(gate)
    else:
        g08_status = 'NOT_APPLICABLE (spec BLOCKED: in-shot removal, G11)'
    slots = sp.get('dialogue_slots') or []
    rows.append({'SHOT_ID': sid, 'treatments': ids, 'G08_STATUS': g08_status, 'gate': gate, 'governed_checks': governed,
                 'OTHER_CODE_BLOCKERS': other, 'MISSING_BASE_FRAME': sid not in frames_ok,
                 'base_frame_plan': f'{PLAN[sid][1]} ({PLAN[sid][2]})',
                 'needs_g03_placement_record': bool(sp.get('active_overlays')), 'needs_g08_treatment_record': bool(ids),
                 'MISSING_DIALOGUE': [f"{d['speaker']}: {d['text']}" for d in slots],
                 'PROVIDER_MOTION_REQUIRED': motion, 'planned_provider_calls': {k: v for k, v in m['provider_calls'].items() if k != 'cost'},
                 'CAN_PRODUCE_AFTER_INPUTS_EXIST': rr['status'] == 'SPEC' and not other})
ready = {x['SHOT_ID']: x['CAN_PRODUCE_AFTER_INPUTS_EXIST'] for x in rows}


def upstream(sid):
    up = CONTINUITY_FROM.get(sid)
    if not up or up in COMPLETE:
        return None
    return up if not ready.get(up) else upstream(up)


for x in rows:
    x['UPSTREAM_CONTINUITY_BLOCKER'] = upstream(x['SHOT_ID'])
    x['continuity_source_shot'] = CONTINUITY_FROM.get(x['SHOT_ID'])
ids_ = lambda f: [x['SHOT_ID'] for x in rows if f(x)]  # noqa: E731
code_ready = ids_(lambda x: x['CAN_PRODUCE_AFTER_INPUTS_EXIST'])
first = ids_(lambda x: x['CAN_PRODUCE_AFTER_INPUTS_EXIST'] and not x['UPSTREAM_CONTINUITY_BLOCKER'])
impact = {
    'G08_DEPENDENT_SHOTS': audit['G08_DEPENDENT_SHOTS'],
    'G08_DEPENDENT_SHOTS_NOW_SUPPORTED': ids_(lambda x: x['treatments'] and x['G08_STATUS'] == 'SUPPORTED'),
    'TOTAL_REMAINING_SHOTS': len(rows),
    'SHOTS_WITH_ALL_CODE_PATHS_SUPPORTED_BEFORE_G08': before['impact']['SHOTS_WITH_ALL_CODE_PATHS_SUPPORTED_AFTER_G03'],
    'SHOTS_WITH_ALL_CODE_PATHS_SUPPORTED_AFTER_G08': code_ready,
    'SHOTS_STILL_BLOCKED_BY_G08': ids_(lambda x: x['treatments'] and x['G08_STATUS'] != 'SUPPORTED'),
    'SHOTS_STILL_BLOCKED_BY_G06': ids_(lambda x: any(g.startswith('G06') for g in x['OTHER_CODE_BLOCKERS'])),
    'SHOTS_STILL_BLOCKED_BY_G07': ids_(lambda x: any(g.startswith('G07') for g in x['OTHER_CODE_BLOCKERS'])),
    'SHOTS_STILL_BLOCKED_BY_G11': ids_(lambda x: any(g.startswith('G11') for g in x['OTHER_CODE_BLOCKERS'])),
    'SHOTS_BLOCKED_ONLY_BY_BASE_FRAMES': ids_(lambda x: x['CAN_PRODUCE_AFTER_INPUTS_EXIST'] and not x['MISSING_DIALOGUE']),
    'SHOTS_BLOCKED_ONLY_BY_DIALOGUE': ids_(lambda x: x['CAN_PRODUCE_AFTER_INPUTS_EXIST'] and x['MISSING_DIALOGUE'] and not x['MISSING_BASE_FRAME']),
    'SHOTS_BLOCKED_BY_BASE_FRAMES_AND_DIALOGUE': ids_(lambda x: x['CAN_PRODUCE_AFTER_INPUTS_EXIST'] and x['MISSING_DIALOGUE'] and x['MISSING_BASE_FRAME']),
    'SHOTS_REQUIRING_PROVIDER_MOTION': ids_(lambda x: x['PROVIDER_MOTION_REQUIRED']),
    'CODE_READY_BUT_UPSTREAM_CONTINUITY_BLOCKED': {x['SHOT_ID']: x['UPSTREAM_CONTINUITY_BLOCKER'] for x in rows
                                                   if x['CAN_PRODUCE_AFTER_INPUTS_EXIST'] and x['UPSTREAM_CONTINUITY_BLOCKER']},
    'SHOTS_POTENTIALLY_PRODUCIBLE_IN_FIRST_BATCH': first,
}
impact['counts'] = {k: len(v) if isinstance(v, (list, dict)) else v for k, v in impact.items()}
fb = [x for x in rows if x['SHOT_ID'] in first]
impact['first_batch_inputs'] = {
    'base_frames_needed': {x['SHOT_ID']: x['base_frame_plan'] for x in fb},
    'dialogue_lines_needed': sum(len(x['MISSING_DIALOGUE']) for x in fb),
    'planned_provider_calls': {k: sum(x['planned_provider_calls'].get(k, 0) for x in fb)
                               for k in ('image', 'video', 'tts_mikko', 'tts_lumi_after_voice_approval')},
    'g03_placement_records': [x['SHOT_ID'] for x in fb if x['needs_g03_placement_record']],
    'g08_treatment_records': [x['SHOT_ID'] for x in fb if x['needs_g08_treatment_record']]}
out = {'readiness': READINESS, 'matrix': rows, 'impact': impact}
Path(sys.argv[1]).write_text(json.dumps(out, indent=1, ensure_ascii=False))
for x in rows:
    print(x['SHOT_ID'], '|', [t[15:-4] for t in x['treatments']], '|', x['G08_STATUS'], '|', x['gate'], '|', x['OTHER_CODE_BLOCKERS'], '|',
          len(x['MISSING_DIALOGUE']), '|', x['PROVIDER_MOTION_REQUIRED'], '|', x['UPSTREAM_CONTINUITY_BLOCKER'], '|',
          x['CAN_PRODUCE_AFTER_INPUTS_EXIST'], '|', x['governed_checks'])
print(json.dumps({k: v for k, v in impact.items() if k != 'counts'}, indent=0))
print(json.dumps(impact['counts']))
