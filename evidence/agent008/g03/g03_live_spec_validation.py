"""READ-ONLY G03 live-spec validation for the remaining EP005 shots (no render, no production write, no provider).

Usage (repo root): python3 evidence/agent008/g03/g03_live_spec_validation.py <scratch_dir> <out_json>
1. Resolves the live Agent-008 specs of approved readiness 69bff641 (HTTP GET snapshot).
2. For every shot with active overlays, applies the G03 governance checks to the live overlay identities (type,
   status, governed SHA) and reads each overlay object from production storage (GET) into <scratch_dir> to verify its
   bytes against the registry SHA and that it decodes with an alpha layer (trimmed size recorded for placement design).
3. Runs the downstream contract gates in memory with the overlay set a G03 frame for that shot would carry:
   G02 check_still_contract for still shots; the compose_motion_shot gate for provider-motion shots.
4. Joins the Batch 0D plan (open gaps, base-frame source, planned provider calls) and the live registry
   (approved base frames, approved dialogue clips) into the updated remaining-shot matrix.
Nothing is composited and nothing is written outside <scratch_dir> and <out_json>.
"""
import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from agent008 import compositor as C, media  # noqa: E402
from agent008.config import load_output_spec  # noqa: E402
from agent008.episode import PINS, resolve_episode  # noqa: E402
from agent008.errors import FailClosed  # noqa: E402
from agent008.hashing import sha256_bytes  # noqa: E402
from agent008.inputs import load_hash_pins  # noqa: E402
from agent008.motion.http import UrllibHttpClient  # noqa: E402
from agent008.overlay import ALPHA_TRIM_THRESHOLD, APPROVED_STATES, OVERLAY_ASSET_TYPE, precomposited_overlay_set  # noqa: E402
from agent008.still import check_still_contract  # noqa: E402
from agent008.tools.snapshot_inputs import build_snapshot  # noqa: E402

SB = 'https://ziluiwrwwbayhcskeere.supabase.co'
READINESS = '69bff641-e056-4701-a23f-d91dbc2039b2'
COMPLETE = ('S027', 'S028', 'S029')
scratch, out_json = Path(sys.argv[1]), Path(sys.argv[2])
scratch.mkdir(parents=True, exist_ok=True)
http = UrllibHttpClient()


def get(path):
    r = http.send('GET', f'{SB}/rest/v1/{path}', {'Accept': 'application/json'})
    if r.status != 200:
        sys.exit(f'STOP: GET {path} HTTP {r.status}')
    return json.loads(r.body)


def plan_table():
    tree = ast.parse((ROOT / 'evidence/agent008/scaleout/build_ep005_production_matrix.py').read_text())
    for node in tree.body:
        if isinstance(node, ast.Assign) and [t.id for t in node.targets if isinstance(t, ast.Name)] == ['C']:
            return ast.literal_eval(node.value)
    sys.exit('STOP: plan table not found')


PLAN = plan_table()
# Continuity start-state dependencies recorded in the plan table notes and the Batch 0C factory-paths record: the shot's
# base frame is the end state of the named upstream shot, so it cannot be produced before that shot is.
CONTINUITY_FROM = {'S005': 'S004', 'S008': 'S007', 'S011': 'S010', 'S013': 'S012', 'S019': 'S018',
                   'S022': 'S021', 'S023': 'S022'}
matrix = {s['shot_id']: s for s in json.loads((ROOT / 'evidence/agent008/batch0d/EP005_AGENT008_PRODUCTION_MATRIX_v3.json').read_text())['shots']}
audit = json.loads((ROOT / 'evidence/agent008/g03/G03_REQUIREMENT_AUDIT_v1.json').read_text())
spec = load_output_spec()
resolved = {r['shot_id']: r for r in resolve_episode(build_snapshot(READINESS), load_hash_pins(PINS), spec)}
reg = get('asset_registry?select=asset_id,status,asset_type,asset_subtype,metadata_json')
frames_ok = {(r['metadata_json'] or {}).get('shot_id') for r in reg if r['asset_type'] == 'SHOT_FRAME' and r['status'] in APPROVED_STATES}
dlg_ok = {r['asset_id'] for r in reg if r['asset_subtype'] == 'DIALOGUE' and r['status'] in APPROVED_STATES}

# --- overlay assets: governance + storage read-verify (GET only) ---
overlays = {}
for o_id in sorted({o['asset_id'] for r in resolved.values() for o in (r.get('spec') or {}).get('active_overlays') or []}):
    o = next(o for r in resolved.values() for o in (r.get('spec') or {}).get('active_overlays') or [] if o['asset_id'] == o_id)
    issues = []
    if o.get('asset_type') != OVERLAY_ASSET_TYPE:
        issues.append(f"OVERLAY_ASSET_WRONG_TYPE {o.get('asset_type')}")
    if o.get('status') not in APPROVED_STATES:
        issues.append(f"OVERLAY_ASSET_NOT_APPROVED {o.get('status')}")
    if not o.get('expected_sha256'):
        issues.append('NO_EXPECTED_HASH')
    g = http.send('GET', f"{SB}/storage/v1/object/authenticated/production-assets/{o['object_key']}", {})
    p = scratch / Path(o['object_key']).name
    p.write_bytes(g.body)
    got = sha256_bytes(g.body)
    if g.status != 200 or got != o.get('expected_sha256'):
        issues.append(f'STORAGE_SHA_MISMATCH {g.status} {got}')
    rgba = media.load_rgba(p)
    trimmed = C.trim_alpha(rgba, ALPHA_TRIM_THRESHOLD)
    overlays[o_id] = {'registry_row_id': o['registry_row_id'], 'status': o['status'], 'type': f"{o['asset_type']}/{o.get('asset_subtype')}",
                      'expected_sha256': o['expected_sha256'], 'storage_sha256': got, 'canvas_size': [rgba.shape[1], rgba.shape[0]],
                      'alpha_min_max': [int(rgba[..., 3].min()), int(rgba[..., 3].max())],
                      'trimmed_size': [trimmed.shape[1], trimmed.shape[0]], 'g03_governance': 'PASS' if not issues else issues}

rows = []
for sid, r in sorted(resolved.items()):
    if sid in COMPLETE:
        continue
    sp, m = r.get('spec') or {}, matrix[sid]
    method = PLAN[sid][0]
    gaps = [g for g in m['code_gaps_v3'] if g != 'G03_OVERLAY_ANCHOR_PLACEMENT']
    provider_motion = method in ('B', 'C') or m['classification'] == 'HIGGSFIELD_MOTION_REQUIRED'
    active = sp.get('active_overlays') or []
    if r['status'] == 'BLOCKED':
        g03, gate = 'NOT_APPLICABLE_BLOCKED_G11 (in-shot removal; spec fails closed OVERLAY_TRANSITION_UNSUPPORTED_V01)', None
    elif not active:
        g03, gate = 'NOT_REQUIRED', None
    else:
        comp = {'shot_id': sid, 'frame_sha256': 'G03-FRAME-PENDING',
                'overlays': [{'asset_id': o['asset_id'], 'sha256': o['expected_sha256'], 'surface': 'FACE'} for o in active]}
        try:
            if provider_motion:
                if sp['treatments']:
                    raise FailClosed('MOTION_TREATMENTS_NEED_TRACKING_V02', 'treatment on generated motion (G08)')
                precomposited_overlay_set(sp, comp, 'G03-FRAME-PENDING')
                gate = 'MOTION_BASE_FRAME_GATE_PASS'
            else:
                check_still_contract(sp, spec, comp, 'G03-FRAME-PENDING')
                gate = 'G02_STILL_GATE_PASS'
        except FailClosed as e:
            gate = f'{e.code}'
        assets_ok = all(overlays[o['asset_id']]['g03_governance'] == 'PASS' for o in active)
        g03 = 'SUPPORTED' if assets_ok else 'BLOCKED_OVERLAY_ASSET_GOVERNANCE'
    other = list(gaps)
    if gate and gate.startswith('MOTION_TREATMENTS') and 'G08_TREATMENTS_ON_STILL_PRODUCTION' not in other:
        other.append('G08_TREATMENTS_ON_MOTION (reflection treatment on provider motion)')
    if gate and gate.startswith('STILL_TREATMENTS') and not any(g.startswith('G08') for g in other):
        other.append('G08_TREATMENTS_ON_STILL_PRODUCTION')
    slots = sp.get('dialogue_slots') or []
    rows.append({
        'SHOT_ID': sid, 'G03_STATUS': g03, 'downstream_gate_with_g03_frame': gate,
        'OTHER_CODE_BLOCKERS': other,
        'MISSING_BASE_FRAME': (f"YES ({PLAN[sid][1]}, {PLAN[sid][2]})" if sid not in frames_ok else 'NO')
                              + (' + G03 placement record (needs the approved base frame first)' if g03 == 'SUPPORTED' else ''),
        'MISSING_DIALOGUE': [f"{d['speaker']}: {d['text']}" for d in slots],
        'PROVIDER_MOTION_REQUIRED': provider_motion,
        'planned_provider_calls': {k: v for k, v in m['provider_calls'].items() if k != 'cost'},
        'CAN_PRODUCE_AFTER_INPUTS_EXIST': r['status'] == 'SPEC' and not other,
        'human_decisions_open': m['blockers'].get('visible_speech_decision', []) + m['blockers'].get('other_human_decisions', []),
        'active_overlays': [o['asset_id'] for o in active], 'treatments': [t['treatment_id'] for t in sp.get('treatments') or []],
        'spec_video_generation_required': sp.get('video_generation_required'), 'plan_method': method})

code_ready = {r['SHOT_ID']: r['CAN_PRODUCE_AFTER_INPUTS_EXIST'] for r in rows}


def upstream_block(sid, seen=()):
    up = CONTINUITY_FROM.get(sid)
    if not up or up in COMPLETE:
        return None
    if not code_ready.get(up):
        return up
    return upstream_block(up, seen + (sid,))


for r in rows:
    r['CONTINUITY_SOURCE_SHOT'] = CONTINUITY_FROM.get(r['SHOT_ID'])
    r['UPSTREAM_CODE_BLOCKED_SHOT'] = upstream_block(r['SHOT_ID'])
    r['PRODUCIBLE_NOW_IN_DEPENDENCY_ORDER_ONCE_INPUTS_EXIST'] = r['CAN_PRODUCE_AFTER_INPUTS_EXIST'] and not r['UPSTREAM_CODE_BLOCKED_SHOT']
dep = audit['G03_DEPENDENT_SHOTS']
by = lambda key: [r['SHOT_ID'] for r in rows if any(g.startswith(key) for g in r['OTHER_CODE_BLOCKERS'])]
impact = {
    'G03_DEPENDENT_SHOTS_BEFORE': dep,
    'G03_DEPENDENT_SHOTS_NOW_SUPPORTED': [r['SHOT_ID'] for r in rows if r['SHOT_ID'] in dep and r['G03_STATUS'] == 'SUPPORTED'],
    'SHOTS_STILL_BLOCKED_BY_G03': [r['SHOT_ID'] for r in rows if r['SHOT_ID'] in dep and r['G03_STATUS'] != 'SUPPORTED'],
    'TOTAL_REMAINING_SHOTS': len(rows),
    'SHOTS_WITH_ALL_CODE_PATHS_SUPPORTED_AFTER_G03': [r['SHOT_ID'] for r in rows if r['CAN_PRODUCE_AFTER_INPUTS_EXIST']],
    'SHOTS_STILL_BLOCKED_BY_G06': by('G06'), 'SHOTS_STILL_BLOCKED_BY_G07': by('G07'),
    'SHOTS_STILL_BLOCKED_BY_G08': by('G08'), 'SHOTS_STILL_BLOCKED_BY_G11': [r['SHOT_ID'] for r in rows if 'BLOCKED_G11' in r['G03_STATUS']
                                                                            or any(g.startswith('G11') for g in r['OTHER_CODE_BLOCKERS'])],
    'SHOTS_BLOCKED_ONLY_BY_MISSING_ASSETS_OR_DIALOGUE': [r['SHOT_ID'] for r in rows if r['CAN_PRODUCE_AFTER_INPUTS_EXIST']],
    'CODE_READY_BUT_UPSTREAM_CONTINUITY_BLOCKED': {r['SHOT_ID']: r['UPSTREAM_CODE_BLOCKED_SHOT'] for r in rows
                                                   if r['CAN_PRODUCE_AFTER_INPUTS_EXIST'] and r['UPSTREAM_CODE_BLOCKED_SHOT']},
    'CODE_READY_AND_DEPENDENCY_CLEAR': [r['SHOT_ID'] for r in rows if r['PRODUCIBLE_NOW_IN_DEPENDENCY_ORDER_ONCE_INPUTS_EXIST']],
    'SHOTS_BLOCKED_ONLY_BY_G08': [r['SHOT_ID'] for r in rows if r['OTHER_CODE_BLOCKERS']
                                 and all(g.startswith('G08') for g in r['OTHER_CODE_BLOCKERS'])],
}
impact['counts'] = {k: len(v) if isinstance(v, list) else v for k, v in impact.items()}
out = {'readiness': READINESS, 'overlay_assets': overlays, 'matrix': rows, 'impact': impact}
out_json.write_text(json.dumps(out, indent=1, ensure_ascii=False))
print(json.dumps(overlays, indent=1))
for r in rows:
    print(r['SHOT_ID'], '|', r['G03_STATUS'][:30], '|', r['downstream_gate_with_g03_frame'], '|', r['OTHER_CODE_BLOCKERS'], '|',
          len(r['MISSING_DIALOGUE']), '|', r['PROVIDER_MOTION_REQUIRED'], '|', r['CAN_PRODUCE_AFTER_INPUTS_EXIST'], '|',
          r['UPSTREAM_CODE_BLOCKED_SHOT'])
print(json.dumps(impact['counts'], indent=1))
print(json.dumps({k: v for k, v in impact.items() if k != 'counts'}))
