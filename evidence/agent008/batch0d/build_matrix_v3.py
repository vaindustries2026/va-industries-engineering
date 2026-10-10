"""EP005_AGENT008_PRODUCTION_MATRIX_v3 (Batch 0D) = accepted v2 + the accepted deltas only. Offline, zero spend.

Usage (repo root): python3 evidence/agent008/batch0d/build_matrix_v3.py
Deltas applied to v2, in order (v1/v2 are read, never regenerated):
  1. Batch 0C (802d2d8): G02, G04, G10 closed; held-pose sign-off; S006 motion-required; smudge design approved.
  2. Lumi production voice (2f89854): H1_LUMI_VOICE removed; dialogue clips still missing.
  3. Batch 0D: G09 closed (agent008.dialogue_timing).
Spec status per shot comes from agent008.episode over the committed v2 approved-state capture.
This consolidated v3 supersedes the interim batch0c/..._v3_DELTA.json and voice/..._v4_VOICE_DELTA.json files.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from agent008.config import load_output_spec  # noqa: E402
from agent008.episode import PINS, resolve_episode  # noqa: E402
from agent008.inputs import load_hash_pins, load_snapshot  # noqa: E402

V1 = {r['shot_id']: r for r in json.loads((ROOT / 'evidence/agent008/scaleout/EP005_AGENT008_PRODUCTION_MATRIX_v1.json').read_text())['shots']}
V2 = json.loads((ROOT / 'evidence/agent008/batch0/EP005_AGENT008_PRODUCTION_MATRIX_v2.json').read_text())
AMEND = json.loads((ROOT / 'evidence/agent008/batch0c/EP005_S004_S012_S018_SCRIPT_AMENDMENT_PACKAGE_v1.json').read_text())
CAPTURE = ROOT / 'agent008/tests/fixtures/ep005_approved_state_capture_v2.json'
episode = {r['shot_id']: r for r in resolve_episode(load_snapshot(CAPTURE), load_hash_pins(PINS), load_output_spec())}

CLOSED = {
 'G02_PRODUCTION_STILL_SHOT_PATH': 'Batch 0C 802d2d8: agent008.still.compose_still_shot',
 'G04_DERIVED_FRAME_FROM_APPROVED_MOTION': 'Batch 0C 802d2d8: agent008.derive.derive_frame',
 'G10_WHOOSH_HASH_PIN': 'Batch 0C 802d2d8: registry metadata_json.sha256 repaired (row 0e10bf46)',
 'G09_DIALOGUE_OVERLAP_AND_HOLD_GUARD': 'Batch 0D: agent008.dialogue_timing.govern_dialogue_timing',
}
VOICES = {'Mikko': {'voice_name': 'Teddy Twinkle – Cute Cartoon Boy', 'voice_id': 'XjGYkUkzth8BPs29fmcV'},
          'Lumi': {'voice_name': 'Lola – Soft, Innocent and Calming', 'voice_id': 'f9imtLc2jfOLXtqe3Ihb'}}
VISIBLE_SPEECH = ['S001', 'S002', 'S003', 'S004', 'S006', 'S007', 'S010', 'S012', 'S014', 'S016', 'S020', 'S022',
                  'S025', 'S026', 'S028']                                    # H4: shot-specific, no global VO policy
SCRIPT_AMENDMENT = AMEND['affected_shots']                                   # H2: authorised = FALSE
OTHER_DECISIONS = {'H5_S028_DERIVED_FRAME_AUTHORISATION': ['S028', 'S029']}
S006_GAPS = ['G03_OVERLAY_ANCHOR_PLACEMENT', 'G08_TREATMENTS_ON_STILL_PRODUCTION']   # Batch 0C reclassification

rows = []
for r in V2['shots']:
    sid = r['shot_id']
    if r.get('status') == 'COMPLETE_APPROVED':
        rows.append({'shot_id': sid, 'status': 'COMPLETE_APPROVED'})
        continue
    ep = episode[sid]
    v1 = V1[sid]
    gaps = S006_GAPS if sid == 'S006' else [g for g in r['code_gaps_v2'] if g not in CLOSED]
    cls = 'HIGGSFIELD_MOTION_REQUIRED' if sid == 'S006' else r['classification']
    calls = dict(r['provider_calls'])
    if sid == 'S006':
        calls['video'] += 1
    dialogue = [{'speaker': d['speaker'], 'text_v02': d['text'], **VOICES.get(d['speaker'], {}),
                 'clip': 'APPROVED' if sid == 'S027' else
                         ('NOT_GENERATED_AWAITING_SCRIPT_AMENDMENT' if sid in SCRIPT_AMENDMENT and d['speaker'] == 'Lumi'
                          else 'NOT_GENERATED')} for d in v1['dialogue']]
    blockers = {
        'code_gaps': gaps,
        'spec': None if ep['status'] == 'SPEC' else ep['blocker']['code'],
        'voice_identity': [],
        'missing_dialogue_assets': [f"{d['speaker']}: {d['text_v02']}" for d in dialogue if d['clip'] != 'APPROVED'],
        'script_amendment': ['H2_SCRIPT_AMENDMENT_AUTHORISATION'] if sid in SCRIPT_AMENDMENT else [],
        'visible_speech_decision': ['H4_VISIBLE_SPEECH'] if sid in VISIBLE_SPEECH else [],
        'other_human_decisions': [h for h, s in OTHER_DECISIONS.items() if sid in s],
    }
    rows.append({'shot_id': sid, 'classification': cls, 'spec_v3': 'SPEC' if ep['status'] == 'SPEC' else
                 f"BLOCKED:{ep['blocker']['code']}", 'code_gaps_v2': r['code_gaps_v2'], 'code_gaps_v3': gaps,
                 'code_gaps_closed_since_v2': [] if sid == 'S006' else [g for g in r['code_gaps_v2'] if g in CLOSED],
                 'technically_supported': not gaps and ep['status'] == 'SPEC', 'dialogue': dialogue,
                 'blockers': blockers, 'base_frame_status_v1': v1['BASE_FRAME_STATUS'], 'provider_calls': calls})

rem = [x for x in rows if x.get('status') != 'COMPLETE_APPROVED']
human = lambda x: x['blockers']['script_amendment'] + x['blockers']['visible_speech_decision'] + x['blockers']['other_human_decisions']
for x in rem:
    is_provider = x['classification'] in ('HIGGSFIELD_MOTION_REQUIRED', 'HYBRID')
    x['provider_ready'] = (is_provider and x['technically_supported'] and not human(x)
                           and not x['blockers']['missing_dialogue_assets'])
ids = lambda pred: [x['shot_id'] for x in rem if pred(x)]
v2s = {x['shot_id']: x for x in V2['shots']}
summary = {
 'TOTAL_EP005_SHOTS': len(rows),
 'COMPLETE_APPROVED_SHOTS': sum(1 for x in rows if x.get('status') == 'COMPLETE_APPROVED'),
 'REMAINING_SHOTS': len(rem),
 'TECHNICALLY_SUPPORTED_SHOTS': ids(lambda x: x['technically_supported']),
 'CODE_BLOCKED_SHOTS': ids(lambda x: x['code_gaps_v3']),
 'VOICE_IDENTITY_BLOCKED_SHOTS': ids(lambda x: x['blockers']['voice_identity']),
 'MISSING_DIALOGUE_ASSET_SHOTS': ids(lambda x: x['blockers']['missing_dialogue_assets']),
 'SCRIPT_AMENDMENT_BLOCKED_SHOTS': ids(lambda x: x['blockers']['script_amendment']),
 'VISIBLE_SPEECH_DECISION_SHOTS': ids(lambda x: x['blockers']['visible_speech_decision']),
 'OTHER_HUMAN_DECISION_BLOCKED_SHOTS': ids(lambda x: x['blockers']['other_human_decisions']),
 'PROVIDER_READY_SHOTS': ids(lambda x: x['provider_ready']),
 'SPEC_BLOCKED_SHOTS': ids(lambda x: x['blockers']['spec']),
 'NEWLY_TECHNICALLY_SUPPORTED_SINCE_V2': ids(lambda x: x['technically_supported'] and not v2s[x['shot_id']]['technically_supported']),
 'NEWLY_SUPPORTED_BY_G09': ids(lambda x: 'G09_DIALOGUE_OVERLAP_AND_HOLD_GUARD' in x['code_gaps_closed_since_v2'] and x['technically_supported']),
 'AGENT008_CODE_GAPS_OPEN': sorted({g for x in rem for g in x['code_gaps_v3']}),
 'AGENT008_CODE_GAPS_CLOSED': sorted(set(V2['summary_v2']['AGENT008_CODE_GAPS_CLOSED']) | set(CLOSED)),
 'DIALOGUE_LINES_MISSING': {'Mikko': sum(1 for x in rem for d in x['dialogue'] if d['speaker'] == 'Mikko' and d['clip'] != 'APPROVED'),
                            'Lumi': sum(1 for x in rem for d in x['dialogue'] if d['speaker'] == 'Lumi' and d['clip'] != 'APPROVED')},
 'ESTIMATED_IMAGE_GENERATIONS': V2['summary_v2']['ESTIMATED_IMAGE_GENERATIONS'],
 'ESTIMATED_VIDEO_GENERATIONS': V2['summary_v2']['ESTIMATED_VIDEO_GENERATIONS'] + 1,
 'ESTIMATED_VIDEO_GENERATIONS_IF_UNBLOCKED': V2['summary_v2']['ESTIMATED_VIDEO_GENERATIONS_IF_UNBLOCKED'] + 1,
}
s028 = next(x for x in rem if x['shot_id'] == 'S028')
summary['S028_READY_STATE'] = {
 'state': 'TECHNICALLY_SUPPORTED_NOT_PRODUCTION_READY',
 'spec': s028['spec_v3'], 'code_gaps': s028['code_gaps_v3'],
 'blockers': [
  'H4_VISIBLE_SPEECH: S028 visual-speech decision (decision pack: VISIBLE_SPEECH_DECISION_REQUIRED)',
  'H5_S028_DERIVED_FRAME_AUTHORISATION: create frame 119 derivative, human-approve exact PNG SHA',
  'S028 derived base frame not registered (SHOT_FRAME/DERIVED_FRAME; separate authorised write)',
  'LUMI dialogue clip missing: "You look comfy. Story time." (voice f9imtLc2jfOLXtqe3Ihb; TTS not authorised)',
  'MIKKO dialogue clip missing: "I’m ready to rest." (voice XjGYkUkzth8BPs29fmcV; TTS not authorised)',
  'S028 G09 timing plan (start times, holds, any authorised overlap) needs human acceptance once clips exist',
  'S028 Seedance motion package + spend authorisation (1 x 5 s, ~$3.40 list) not prepared/authorised',
  'S028 raw motion human approval + RAW_MOTION_SOURCE registration (after generation)',
  'FOLEY-CLOTH-SOFT-v01 event timing (hand-off/pat) to be set from the approved motion',
  'S028 final assembled-shot human QC + registration',
 ]}
out = {'matrix': 'EP005_AGENT008_PRODUCTION_MATRIX_v3', 'base': 'EP005_AGENT008_PRODUCTION_MATRIX_v2 (accepted; not regenerated)',
       'deltas': ['Batch 0C 802d2d8ef71eaff9bcee9452779768311f3d6de5', 'Lumi voice 2f89854eba42766dcff2472d9201723844fe67b9',
                  'Batch 0D G09'],
       'capture': 'agent008/tests/fixtures/ep005_approved_state_capture_v2.json',
       'voices': VOICES, 'gaps_closed_since_v2': CLOSED, 'summary_v3': summary, 'shots': rows}
(Path(__file__).parent / 'EP005_AGENT008_PRODUCTION_MATRIX_v3.json').write_text(json.dumps(out, indent=1, ensure_ascii=False) + '\n')
counts = {k: (len(v) if isinstance(v, list) and k.endswith('SHOTS') else v) for k, v in summary.items()}
print(json.dumps(counts, indent=1, ensure_ascii=False))
print(json.dumps({k: v for k, v in summary.items() if isinstance(v, list)}, ensure_ascii=False))
