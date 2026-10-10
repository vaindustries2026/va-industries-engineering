"""EP005 production matrix v2 = accepted v1 (ec9b7d1) + Batch 0 deltas only. Offline, zero spend.

Usage (repo root): python3 evidence/agent008/batch0/build_matrix_v2_delta.py
v1 is read, never regenerated. Episode spec status comes from agent008.episode over the committed
read-only approved-state capture. Decision assignments below are the Batch 0 decision packs.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from agent008.config import load_output_spec  # noqa: E402
from agent008.episode import PINS, resolve_episode  # noqa: E402
from agent008.inputs import load_hash_pins, load_snapshot  # noqa: E402

V1 = json.loads((ROOT / 'evidence/agent008/scaleout/EP005_AGENT008_PRODUCTION_MATRIX_v1.json').read_text())
CAPTURE = ROOT / 'agent008/tests/fixtures/ep005_approved_state_capture_v1.json'
episode = {r['shot_id']: r for r in resolve_episode(load_snapshot(CAPTURE), load_hash_pins(PINS), load_output_spec())}

FIXED = {'G01_INPUT_SNAPSHOT_COVERAGE': 'RESOLVED: agent008.episode resolves all 29 shots from approved state',
         'G05_ROLE_AWARE_MAPPED_AUDIO': 'FIXED: governed audio roles; FOLEY/SFX are one-shot timed events'}
PROPOSED = {'G10_WHOOSH_HASH_PIN': 'REPAIR_PROPOSED (sha 53d06150...d0c3); still blocking until applied'}
DESIGNED = {'G11_TRACKED_OVERLAY_REMOVAL': 'DESIGNED (fixed-anchor overlay + keyed reveal sweep + drift QC); not implemented'}

# Human-decision gates (Batch 0B decision packs). A shot listed here cannot be finished without the decision.
DECISIONS = {
 'H1_LUMI_VOICE': ['S001', 'S003', 'S004', 'S010', 'S012', 'S016', 'S018', 'S022', 'S025', 'S028'],
 'H2_DIALOGUE_TIMING_WORDING': ['S004', 'S012', 'S018'],
 'H3_HELD_POSE_SIGNOFF': ['S004', 'S006', 'S012', 'S017', 'S018', 'S023', 'S024', 'S025', 'S029'],
 'H4_VISIBLE_SPEECH': ['S001', 'S002', 'S003', 'S004', 'S006', 'S007', 'S010', 'S012', 'S014', 'S016', 'S020',
                       'S022', 'S025', 'S026', 'S028'],
 'H5_S028_BASE_FRAME': ['S028', 'S029'],
 'H6_SMUDGE_REMOVAL_METHOD': ['S009', 'S015', 'S021'],
}

rows, changes = [], []
for r in V1['shots']:
    sid = r['shot_id']
    if r['PRODUCTION_STATUS'] == 'COMPLETE_APPROVED':
        rows.append({'shot_id': sid, 'status': 'COMPLETE_APPROVED'})
        continue
    before = list(r['code_gaps'])
    gaps = [g for g in before if g not in FIXED]
    ep = episode[sid]
    spec_status = 'SPEC' if ep['status'] == 'SPEC' else f"BLOCKED:{ep['blocker']['code']}"
    decisions = [h for h, shots in DECISIONS.items() if sid in shots]
    row = {'shot_id': sid, 'classification': r['classification'], 'spec_v2': spec_status,
           'code_gaps_v1': before, 'code_gaps_v2': gaps,
           'code_gaps_removed': [g for g in before if g in FIXED],
           'gap_notes': {g: PROPOSED.get(g) or DESIGNED.get(g) for g in gaps if g in PROPOSED or g in DESIGNED},
           'human_decisions': decisions,
           'voice_blocked': 'H1_LUMI_VOICE' in decisions,
           'technically_supported': not gaps and ep['status'] == 'SPEC',
           'provider_calls': r['PROVIDER_CALLS_REQUIRED']}
    is_provider = r['classification'] in ('HIGGSFIELD_MOTION_REQUIRED', 'HYBRID')
    picture_decisions = [h for h in decisions if h not in ('H1_LUMI_VOICE',)]
    row['provider_ready'] = is_provider and row['technically_supported'] and not picture_decisions
    rows.append(row)
    if row['code_gaps_removed'] or spec_status != 'SPEC':
        changes.append({'shot_id': sid, 'removed_gaps': row['code_gaps_removed'], 'spec_v2': spec_status})

rem = [x for x in rows if x.get('status') != 'COMPLETE_APPROVED']
v1s = V1['summary']
summary = {
 'REMAINING_SHOTS': len(rem),
 'SPEC_RESOLVED_SHOTS': sum(1 for x in rem if x['spec_v2'] == 'SPEC') + 1,   # + S027
 'SPEC_BLOCKED_SHOTS': sum(1 for x in rem if x['spec_v2'] != 'SPEC'),
 'TECHNICALLY_SUPPORTED_SHOTS': sum(1 for x in rem if x['technically_supported']),
 'CODE_BLOCKED_SHOTS': sum(1 for x in rem if x['code_gaps_v2']),
 'HUMAN_DECISION_BLOCKED_SHOTS': sum(1 for x in rem if x['human_decisions']),
 'VOICE_BLOCKED_SHOTS': sum(1 for x in rem if x['voice_blocked']),
 'PROVIDER_READY_SHOTS': [x['shot_id'] for x in rem if x['provider_ready']],
 'AGENT008_CODE_GAPS_OPEN': sorted({g for x in rem for g in x['code_gaps_v2']}),
 'AGENT008_CODE_GAPS_CLOSED': sorted(FIXED),
 'ESTIMATED_IMAGE_GENERATIONS': v1s['ESTIMATED_IMAGE_GENERATIONS_REQUIRED'],
 'ESTIMATED_VIDEO_GENERATIONS': v1s['ESTIMATED_VIDEO_GENERATIONS_REQUIRED'],
 'ESTIMATED_VIDEO_GENERATIONS_IF_UNBLOCKED': v1s['ESTIMATED_VIDEO_GENERATIONS_IF_BLOCKED_SHOTS_UNBLOCKED'],
 'ESTIMATED_NEW_TTS_GENERATIONS_MIKKO': v1s['ESTIMATED_NEW_TTS_GENERATIONS_REQUIRED'],
 'ESTIMATED_LUMI_TTS_AFTER_VOICE_APPROVAL': v1s['ESTIMATED_LUMI_TTS_AFTER_VOICE_APPROVAL'],
}
out = {'base': 'EP005_AGENT008_PRODUCTION_MATRIX_v1 @ ec9b7d1 (accepted; not regenerated)',
       'changes_from_v1': changes, 'gap_status': {**FIXED, **PROPOSED, **DESIGNED},
       'decision_gates': DECISIONS, 'summary_v2': summary, 'shots': rows}
(Path(__file__).parent / 'EP005_AGENT008_PRODUCTION_MATRIX_v2.json').write_text(json.dumps(out, indent=1))
print(json.dumps(summary, indent=1))
for c in changes:
    print(c)
