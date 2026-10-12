"""READ-ONLY EP005 shot-production checkpoint (after S029 approval). No writes to production, no provider calls.

Usage (repo root): python3 evidence/agent008/phase1/ep005_shot_checkpoint.py <out_json>
Joins the live Agent-008 spec resolution of approved readiness 69bff641 (v05 lineage), the live asset registry
(approved SHOT_RENDER/ASSEMBLED_SHOT rows) and the Batch 0D production matrix v3 plan (method, base-frame source,
open code gaps, provider calls), and classifies each remaining shot.
"""
import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from agent008.config import load_output_spec  # noqa: E402
from agent008.episode import PINS, resolve_episode  # noqa: E402
from agent008.inputs import load_hash_pins  # noqa: E402
from agent008.motion.http import UrllibHttpClient  # noqa: E402
from agent008.tools.snapshot_inputs import build_snapshot  # noqa: E402

SB = 'https://ziluiwrwwbayhcskeere.supabase.co'
READINESS = '69bff641-e056-4701-a23f-d91dbc2039b2'


def load_plan():
    """The per-shot plan table C from the scaleout matrix builder, read by AST (the builder itself is not executed)."""
    tree = ast.parse((ROOT / 'evidence/agent008/scaleout/build_ep005_production_matrix.py').read_text())
    for node in tree.body:
        if isinstance(node, ast.Assign) and [t.id for t in node.targets if isinstance(t, ast.Name)] == ['C']:
            return ast.literal_eval(node.value)
    raise SystemExit('STOP: plan table not found')


PLAN = load_plan()
# Recorded continuity facts that the plan table's base-frame column does not carry (Batch 0C factory-paths record):
DERIVED_FROM = {'S023': 'S022 end state: derived frame from approved S022 raw motion (EP005_BATCH0C_FACTORY_PATHS_v1.md)'}
matrix = {s['shot_id']: s for s in json.loads((ROOT / 'evidence/agent008/batch0d/EP005_AGENT008_PRODUCTION_MATRIX_v3.json').read_text())['shots']}
h = UrllibHttpClient()
rows = json.loads(h.send('GET', f'{SB}/rest/v1/asset_registry?asset_type=eq.SHOT_RENDER&asset_subtype=eq.ASSEMBLED_SHOT'
                              f'&select=asset_id,id,status,metadata_json', {'Accept': 'application/json'}).body)
final = {r['metadata_json']['shot_id']: r for r in rows
         if r['status'] == 'APPROVED' and r['metadata_json'].get('episode_code') == 'EP-CANDIDATE-005'
         and r['metadata_json'].get('human_decision') in ('APPROVED', None)}
spec = load_output_spec()
resolved = resolve_episode(build_snapshot(READINESS), load_hash_pins(PINS), spec)
complete, remaining = [], []
for r in resolved:
    sid, s = r['shot_id'], r.get('spec') or {}
    if sid in final:
        complete.append({'shot_id': sid, 'asset_id': final[sid]['asset_id'], 'registry_id': final[sid]['id'],
                         'sha256': final[sid]['metadata_json']['sha256']})
        continue
    m = matrix[sid]
    method, base_src, base_status = PLAN[sid][0], PLAN[sid][1], PLAN[sid][2]
    gaps = m['code_gaps_v3']
    calls = {k: v for k, v in m['provider_calls'].items() if k != 'cost'}
    if r['status'] == 'BLOCKED' or method == 'D':
        cls = 'blocked'
    elif method == 'B' or (method == 'A' and m['classification'] == 'HIGGSFIELD_MOTION_REQUIRED'):
        cls = 'provider motion required'
    elif method == 'C':
        cls = 'provider motion required (hybrid: provider motion + deterministic composite)'
    elif s.get('active_overlays') or s.get('treatments'):
        cls = 'deterministic composite'
    elif sid in DERIVED_FROM or base_status == 'CAN_DERIVE_DETERMINISTICALLY' and (base_src.endswith('-END') or 'end frame' in PLAN[sid][4]
                                                             or 'last frame' in PLAN[sid][4] or 'end state' in PLAN[sid][4]):
        cls = 'deterministic derived-frame'
    else:
        cls = 'deterministic still'
    remaining.append({
        'shot_id': sid, 'agent008_classification': cls, 'spec_state': r['status'], 'plan_method': method,
        'matrix_v3_classification': m['classification'], 'frames': s.get('frames'), 'duration_s': s.get('duration_seconds'),
        'video_generation_required_in_spec': s.get('video_generation_required'), 'dialogue_lines': len(s.get('dialogue_slots') or []),
        'overlays': len(s.get('active_overlays') or []), 'treatments': len(s.get('treatments') or []),
        'base_frame_source': base_src, 'base_frame_status': base_status, 'open_code_gaps': gaps,
        'zero_spend_code_ready': not gaps and not any(calls.values()) and r['status'] == 'SPEC',
        'provider_calls_planned': calls, 'human_decisions_open': m['blockers'].get('visible_speech_decision', []) + m['blockers'].get('other_human_decisions', []),
        'derived_from': DERIVED_FROM.get(sid), 'dialogue_text': [d.get('text') for d in s.get('dialogue_slots') or []],
        'note': PLAN[sid][4]})
out = {'readiness': READINESS, 'authoritative_shots': len(resolved), 'final_approved_assembled_shots': len(complete),
       'complete_approved': complete, 'remaining_count': len(remaining), 'remaining': remaining,
       'by_classification': {}}
for x in remaining:
    out['by_classification'].setdefault(x['agent008_classification'], []).append(x['shot_id'])
Path(sys.argv[1]).write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))
print(json.dumps({k: out[k] for k in ('authoritative_shots', 'final_approved_assembled_shots', 'remaining_count', 'by_classification')}, indent=1))
print([c['shot_id'] for c in out['complete_approved']])
for x in remaining:
    print(x['shot_id'], '|', x['agent008_classification'], '|', x['base_frame_source'], x['base_frame_status'], '|', x['open_code_gaps'], '|',
          x['provider_calls_planned'], '|', x['dialogue_lines'], x['overlays'], x['treatments'])
