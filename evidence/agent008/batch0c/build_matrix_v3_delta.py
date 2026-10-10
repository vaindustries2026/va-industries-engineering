"""EP005 production matrix v3 = accepted v2 (Batch 0) + Batch 0C deltas only. Offline, zero spend.

Usage (repo root): python3 evidence/agent008/batch0c/build_matrix_v3_delta.py
v1/v2 are read, never regenerated. Episode spec status comes from agent008.episode over the committed
read-only v2 approved-state capture (live state after the approved whoosh metadata repair).
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from agent008.config import load_output_spec  # noqa: E402
from agent008.episode import PINS, resolve_episode  # noqa: E402
from agent008.inputs import load_hash_pins, load_snapshot  # noqa: E402
from agent008.still import check_still_contract  # noqa: E402
from agent008.errors import FailClosed  # noqa: E402

V2 = json.loads((ROOT / 'evidence/agent008/batch0/EP005_AGENT008_PRODUCTION_MATRIX_v2.json').read_text())
CAPTURE = ROOT / 'agent008/tests/fixtures/ep005_approved_state_capture_v2.json'
episode = {r['shot_id']: r for r in resolve_episode(load_snapshot(CAPTURE), load_hash_pins(PINS), load_output_spec())}

CLOSED_0C = {'G02_PRODUCTION_STILL_SHOT_PATH': 'IMPLEMENTED: agent008.still.compose_still_shot (overlays -> G03, treatments -> G08, fail closed)',
             'G04_DERIVED_FRAME_FROM_APPROVED_MOTION': 'IMPLEMENTED: agent008.derive.derive_frame (REVIEW candidate; registration separate)',
             'G10_WHOOSH_HASH_PIN': 'REPAIRED: registry metadata_json.sha256 = 53d06150...d0c3 (row 0e10bf46), Agent-006 unchanged'}

# Human-decision gates after the Batch 0C decisions.
DECISIONS = {
 'H1_LUMI_VOICE': ['S001', 'S003', 'S004', 'S010', 'S012', 'S016', 'S018', 'S022', 'S025', 'S028'],   # still pending
 'H2_SCRIPT_AMENDMENT_AUTHORISATION': ['S004', 'S012', 'S018'],    # Alternative B chosen; package ready, not authorised
 'H4_VISIBLE_SPEECH': ['S001', 'S002', 'S003', 'S004', 'S006', 'S007', 'S010', 'S012', 'S014', 'S016', 'S020',
                       'S022', 'S025', 'S026', 'S028'],             # no global policy; shot-specific (S027 only approved VO)
 'H5_S028_DERIVED_FRAME_AUTHORISATION': ['S028', 'S029'],          # spec ready; creation + exact-SHA approval pending
}
RESOLVED_DECISIONS = {
 'H3_HELD_POSE_SIGNOFF': 'APPROVED for every SAFE_HELD_POSE / SAFE_DETERMINISTIC_TREATMENT shot except S006',
 'H6_SMUDGE_REMOVAL_METHOD': 'DIRECTION APPROVED; implementation deferred to the overlay-anchor/wipe sprint (G11 stays open)',
 'H4_GLOBAL_VO_POLICY': 'NO GLOBAL POLICY; S027 is the only approved voice-over case',
}
# S006: natural motion required for planning (no forced held pointing pose).
S006 = {'classification': 'HIGGSFIELD_MOTION_REQUIRED (planning; Batch 0C)',
        'code_gaps': ['G03_OVERLAY_ANCHOR_PLACEMENT', 'G08_TREATMENTS_ON_STILL_PRODUCTION'],
        'gap_notes': {'G03_OVERLAY_ANCHOR_PLACEMENT': 'persistent smudges pre-composited into the motion base frame',
                      'G08_TREATMENTS_ON_STILL_PRODUCTION': 'MIRROR-REFLECTION treatment: motion compose rejects '
                                                             'treatments (MOTION_TREATMENTS_NEED_TRACKING_V02)'},
        'provider_calls_delta': {'video': +1}}

rows, changes = [], []
for r in V2['shots']:
    sid = r['shot_id']
    if r.get('status') == 'COMPLETE_APPROVED':
        rows.append(r)
        continue
    ep = episode[sid]
    spec_status = 'SPEC' if ep['status'] == 'SPEC' else f"BLOCKED:{ep['blocker']['code']}"
    before = list(r['code_gaps_v2'])
    gaps = [g for g in before if g not in CLOSED_0C]
    cls = r['classification']
    notes = {g: n for g, n in r['gap_notes'].items() if g in gaps}
    calls = dict(r['provider_calls'])
    if sid == 'S006':
        cls, gaps, notes = S006['classification'], list(S006['code_gaps']), dict(S006['gap_notes'])
        calls['video'] = calls['video'] + 1
    if 'G11_TRACKED_OVERLAY_REMOVAL' in gaps:
        notes['G11_TRACKED_OVERLAY_REMOVAL'] = 'DESIGN APPROVED; NOT IMPLEMENTED (overlay-anchor/wipe sprint)'
    decisions = [h for h, shots in DECISIONS.items() if sid in shots]
    still_fit = None
    if ep['status'] == 'SPEC' and not ep['spec']['video_generation_required']:
        try:
            check_still_contract(ep['spec'], load_output_spec())
            still_fit = 'OK'
        except FailClosed as e:
            still_fit = e.code
    row = {'shot_id': sid, 'classification': cls, 'spec_v3': spec_status, 'code_gaps_v2': before, 'code_gaps_v3': gaps,
           'code_gaps_closed_0c': [] if sid == 'S006' else [g for g in before if g in CLOSED_0C], 'gap_notes': notes,
           'reclassified_0c': sid == 'S006',
           'g02_still_contract': still_fit, 'human_decisions': decisions,
           'voice_blocked': 'H1_LUMI_VOICE' in decisions,
           'technically_supported': not gaps and ep['status'] == 'SPEC', 'provider_calls': calls}
    rows.append(row)
    if row['code_gaps_closed_0c'] or sid == 'S006' or spec_status != r['spec_v2'] or decisions != r['human_decisions']:
        changes.append({'shot_id': sid, 'closed': row['code_gaps_closed_0c'], 'spec': [r['spec_v2'], spec_status],
                        'decisions': [r['human_decisions'], decisions], 'technically_supported':
                        [r['technically_supported'], row['technically_supported']]})

rem = [x for x in rows if x.get('status') != 'COMPLETE_APPROVED']
v2 = {x['shot_id']: x for x in V2['shots']}
newly = lambda g: [x['shot_id'] for x in rem if g in x['code_gaps_closed_0c'] and x['technically_supported']
                   and not v2[x['shot_id']]['technically_supported']]
summary = {
 'REMAINING_SHOTS': len(rem),
 'SPEC_RESOLVED_SHOTS': sum(1 for x in rem if x['spec_v3'] == 'SPEC') + 1,
 'SPEC_BLOCKED_SHOTS': [x['shot_id'] for x in rem if x['spec_v3'] != 'SPEC'],
 'NEWLY_TECHNICALLY_SUPPORTED_BY_G02': newly('G02_PRODUCTION_STILL_SHOT_PATH'),
 'NEWLY_TECHNICALLY_SUPPORTED_BY_G04': newly('G04_DERIVED_FRAME_FROM_APPROVED_MOTION'),
 'G02_CLOSED_BUT_STILL_CODE_BLOCKED': {x['shot_id']: x['code_gaps_v3'] for x in rem
                                       if 'G02_PRODUCTION_STILL_SHOT_PATH' in x['code_gaps_closed_0c'] and x['code_gaps_v3']},
 'G04_CLOSED_BUT_STILL_CODE_BLOCKED': {x['shot_id']: x['code_gaps_v3'] for x in rem
                                       if 'G04_DERIVED_FRAME_FROM_APPROVED_MOTION' in x['code_gaps_closed_0c'] and x['code_gaps_v3']},
 'TECHNICALLY_SUPPORTED_SHOTS': [x['shot_id'] for x in rem if x['technically_supported']],
 'CODE_BLOCKED_SHOTS': sum(1 for x in rem if x['code_gaps_v3']),
 'CODE_BLOCKED_SHOTS_V2': V2['summary_v2']['CODE_BLOCKED_SHOTS'],
 'HUMAN_DECISION_BLOCKED_SHOTS': sum(1 for x in rem if x['human_decisions']),
 'HUMAN_DECISION_BLOCKED_SHOTS_V2': V2['summary_v2']['HUMAN_DECISION_BLOCKED_SHOTS'],
 'VOICE_BLOCKED_SHOTS': sum(1 for x in rem if x['voice_blocked']),
 'AGENT008_CODE_GAPS_OPEN': sorted({g for x in rem for g in x['code_gaps_v3']}),
 'AGENT008_CODE_GAPS_CLOSED': sorted(set(V2['summary_v2']['AGENT008_CODE_GAPS_CLOSED']) | set(CLOSED_0C)),
 'ESTIMATED_VIDEO_GENERATIONS': V2['summary_v2']['ESTIMATED_VIDEO_GENERATIONS'] + 1,
 'ESTIMATED_VIDEO_GENERATIONS_IF_UNBLOCKED': V2['summary_v2']['ESTIMATED_VIDEO_GENERATIONS_IF_UNBLOCKED'] + 1,
 'ESTIMATED_IMAGE_GENERATIONS': V2['summary_v2']['ESTIMATED_IMAGE_GENERATIONS'],
}
out = {'base': 'EP005_AGENT008_PRODUCTION_MATRIX_v2 (Batch 0, accepted; not regenerated)',
       'capture': 'agent008/tests/fixtures/ep005_approved_state_capture_v2.json',
       'changes_from_v2': changes, 'gaps_closed_0c': CLOSED_0C, 'decision_gates': DECISIONS,
       'decisions_resolved_0c': RESOLVED_DECISIONS, 's006_reclassification': S006, 'summary_v3': summary, 'shots': rows}
(Path(__file__).parent / 'EP005_AGENT008_PRODUCTION_MATRIX_v3_DELTA.json').write_text(
    json.dumps(out, indent=1, ensure_ascii=False) + '\n')
print(json.dumps(summary, indent=1))
for c in changes:
    print(c)
