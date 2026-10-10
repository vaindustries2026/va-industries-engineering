"""EP005 production matrix v4 = accepted v3 delta (Batch 0C) + the Lumi production-voice approval only.

Usage (repo root): python3 evidence/agent008/voice/build_matrix_v4_voice_delta.py
Offline, zero spend. Removes ONLY the H1_LUMI_VOICE gate. Every other blocker (script amendment, missing
dialogue clip, visible-speech / lip-sync decision, base frame, motion generation, code gaps) is kept, and each
Lumi line is re-stated as a dialogue asset that does not exist yet.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
V3 = json.loads((ROOT / 'evidence/agent008/batch0c/EP005_AGENT008_PRODUCTION_MATRIX_v3_DELTA.json').read_text())
V1 = {r['shot_id']: r for r in json.loads((ROOT / 'evidence/agent008/scaleout/EP005_AGENT008_PRODUCTION_MATRIX_v1.json').read_text())['shots']}
AMEND = json.loads((ROOT / 'evidence/agent008/batch0c/EP005_S004_S012_S018_SCRIPT_AMENDMENT_PACKAGE_v1.json').read_text())

LUMI = {'voice_name': 'Lola – Soft, Innocent and Calming', 'voice_id': 'f9imtLc2jfOLXtqe3Ihb', 'model': 'eleven_multilingual_v2'}
MIKKO = {'voice_name': 'Teddy Twinkle – Cute Cartoon Boy', 'voice_id': 'XjGYkUkzth8BPs29fmcV', 'model': 'eleven_multilingual_v2'}
AMENDED = set(AMEND['affected_shots'])

rows, cleared, newly_free = [], [], []
for r in V3['shots']:
    sid = r['shot_id']
    if r.get('status') == 'COMPLETE_APPROVED':
        rows.append(r)
        continue
    before = list(r['human_decisions'])
    after = [h for h in before if h != 'H1_LUMI_VOICE']
    lines = []
    for d in V1[sid]['dialogue']:
        if d['speaker'] == 'Lumi':
            state = ('NOT_GENERATED_AWAITING_SCRIPT_AMENDMENT' if sid in AMENDED else 'NOT_GENERATED')
            lines.append({'speaker': 'Lumi', 'authoritative_text_v02': d['text'], 'voice_id': LUMI['voice_id'],
                          'clip_status': state, 'registry_status': None})
        else:
            lines.append({'speaker': d['speaker'], 'authoritative_text_v02': d['text'], 'voice_id': MIKKO['voice_id'],
                          'clip_status': 'APPROVED (S027 only)' if sid == 'S027' else 'NOT_GENERATED', 'registry_status': None})
    row = {**r, 'human_decisions': after, 'voice_blocked': False, 'dialogue_assets': lines,
           'asset_blockers': (['LUMI_DIALOGUE_CLIP_MISSING'] if any(l['speaker'] == 'Lumi' for l in lines) else [])
                             + (['MIKKO_DIALOGUE_CLIP_MISSING'] if any(l['speaker'] == 'Mikko' for l in lines) else [])}
    if 'H1_LUMI_VOICE' in before:
        cleared.append(sid)
        if not after:
            newly_free.append(sid)
    rows.append(row)

rem = [x for x in rows if x.get('status') != 'COMPLETE_APPROVED']
lumi_lines = [(x['shot_id'], l) for x in rem for l in x['dialogue_assets'] if l['speaker'] == 'Lumi']
s3 = V3['summary_v3']
summary = {
 'LUMI_VOICE_SELECTION_PENDING_HUMAN': False,
 'LUMI_PRODUCTION_VOICE_APPROVED': True,
 'LUMI_VOICE_ID': LUMI['voice_id'],
 'NEW_VOICE_AUDITIONS_REQUIRED': False,
 'SHOTS_NO_LONGER_BLOCKED_BY_MISSING_LUMI_VOICE': cleared,
 'SHOTS_WHOSE_ONLY_HUMAN_GATE_WAS_LUMI_VOICE': newly_free,
 'VOICE_BLOCKED_SHOTS': sum(1 for x in rem if x['voice_blocked']),
 'VOICE_BLOCKED_SHOTS_V3': s3['VOICE_BLOCKED_SHOTS'],
 'HUMAN_DECISION_BLOCKED_SHOTS': sum(1 for x in rem if x['human_decisions']),
 'HUMAN_DECISION_BLOCKED_SHOTS_V3': s3['HUMAN_DECISION_BLOCKED_SHOTS'],
 'CODE_BLOCKED_SHOTS': sum(1 for x in rem if x['code_gaps_v3']),
 'TECHNICALLY_SUPPORTED_SHOTS': [x['shot_id'] for x in rem if x['technically_supported']],
 'LUMI_DIALOGUE_LINES_TO_GENERATE': len(lumi_lines),
 'LUMI_LINES_WITH_FINAL_V02_TEXT_GENERATION_NOT_AUTHORISED': [s for s, l in lumi_lines if l['clip_status'] == 'NOT_GENERATED'],
 'LUMI_LINES_AWAITING_SCRIPT_AMENDMENT': [s for s, l in lumi_lines if l['clip_status'] != 'NOT_GENERATED'],
 'LUMI_DIALOGUE_CLIPS_EXISTING': 0,
 'SHOTS_WITH_LUMI_DIALOGUE_CLIP_MISSING': sorted({s for s, _ in lumi_lines}),
 'PRODUCTION_READY_SHOTS': [],
}
out = {'base': 'EP005_AGENT008_PRODUCTION_MATRIX_v3_DELTA (Batch 0C, not regenerated)',
       'voice_state': {'LUMI': {**LUMI, 'status': 'APPROVED (human, Gilang, 2026-10-10)'},
                       'MIKKO': {**MIKKO, 'status': 'APPROVED (human, Gilang, 2026-10-09)'}},
       'gate_removed': 'H1_LUMI_VOICE', 'gates_remaining': {k: v for k, v in V3['decision_gates'].items() if k != 'H1_LUMI_VOICE'},
       'summary_v4': summary, 'shots': rows}
(Path(__file__).parent / 'EP005_AGENT008_PRODUCTION_MATRIX_v4_VOICE_DELTA.json').write_text(
    json.dumps(out, indent=1, ensure_ascii=False) + '\n')
print(json.dumps(summary, indent=1, ensure_ascii=False))
for x in rem:
    if x['shot_id'] in cleared:
        print(x['shot_id'], 'gates', x['human_decisions'], 'code', x['code_gaps_v3'], 'assets', x['asset_blockers'],
              'spec', x['spec_v3'])
