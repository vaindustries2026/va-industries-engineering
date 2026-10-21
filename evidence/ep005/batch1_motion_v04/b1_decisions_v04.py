"""Bind the Company Brain motion-review decisions (2026-10-21): S005 v03 + S017 v03 APPROVED (S029 final-shot pattern:
in-place status update of the REVIEW row after exact stored-bytes readback; no new object, no re-encode); S013 v03
and S019 raw REJECTED_BY_HUMAN (status + reason recorded; stored files untouched, kept as evidence).
Usage (repo root): python3 evidence/ep005/batch1_motion_v04/b1_decisions_v04.py"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE.parent / 'batch1_base_frames'))
from agent008.motion.authorisation import AttemptLedger  # noqa: E402
from b1_review_decisions import sb, sha  # noqa: E402

LEDGER = AttemptLedger(HERE / 'B1_MOTION_V04_LEDGER_v1.jsonl')
BASIS = 'COMPANY BRAIN FINAL HUMAN APPROVAL 2026-10-21 of exact sha256; evidence basis 5b4aeea8f9684b2541896a832abdd063a15b67b0'
DECISIONS = {
    'SHOT-EP005-S005-ASSEMBLED-CAND-v03': ('APPROVED', '629e2e44fb10e285fe6782dac7724573a823f251e614edbd101de0ef0ca70cc8',
        ['genuine character animation visible', 'Mikko reflection naturally reacts', 'eyes move', 'Lumi floats naturally',
         'all three smudges remain consistent', 'no material canon defect']),
    'SHOT-EP005-S017-ASSEMBLED-CAND-v03': ('APPROVED', '78fdfe927296235dea176f970aeb26554b9864a93789de009acc3f7b6eeaf97f',
        ['genuine character movement', 'Mikko turns / blinks', 'Lumi moves naturally', 'reflection is acceptably consistent',
         'nose smudge continuity holds', 'no material canon defect']),
    'SHOT-EP005-S013-ASSEMBLED-CAND-v03': ('REJECTED', '38c43abbb1e9c57ec7d54a6b92b34a2422f2e42763a4a8eb6704b7f062a33216',
        ['animation acceptable, but late in the shot an unwanted red facial mark appears on foreground Mikko: continuity defect',
         'do not repair the existing moving video; one replacement generation authorised']),
    'MOTION-EP005-S019-KLING30T-CAND-v01': ('REJECTED', 'f107ef3e453bfad26d12426c2c39bd6155f29509ba01b68d7334b1b79969023b',
        ['CANON_FAIL: an unauthorised second hand / yellow glove / brown furry sleeve enters and grabs the mirror',
         'one replacement generation authorised']),
}


def main():
    out = {}
    for aid, (decision, want, reasons) in DECISIONS.items():
        rows = json.loads(sb('GET', f'/rest/v1/asset_registry?asset_id=eq.{aid}&select=*').body)
        if len(rows) != 1 or rows[0]['status'] != 'REVIEW' or rows[0]['metadata_json']['sha256'] != want:
            sys.exit(f'STOP {aid}: not exactly one REVIEW row at the decided SHA')
        row = rows[0]
        g = sb('GET', f"/storage/v1/object/authenticated/{row['storage_path']}")
        if g.status != 200 or sha(g.body) != want:
            sys.exit(f'STOP {aid}: stored bytes differ from the decided SHA')
        md = dict(row['metadata_json'])
        if decision == 'APPROVED':
            md.update({'approved': True, 'human_decision': 'APPROVED', 'human_approval': 'APPROVED', 'approved_sha256': want,
                       'approval_authority': 'Gilang / Company Brain', 'approval_basis': BASIS, 'approval_reasons': reasons,
                       'final_state': 'COMPLETE_APPROVED', 'approval_record': 'ENG-20261021-EP005-BATCH1-MOTION-REVIEW-RECONCILED'})
        else:
            md.update({'approved': False, 'human_decision': 'REJECTED', 'human_approval': 'REJECTED', 'rejected_sha256': want,
                       'rejection_state': 'REJECTED_BY_HUMAN' + (' / CANON_FAIL' if 'S019' in aid else ''),
                       'rejection_authority': 'Gilang / Company Brain', 'rejection_basis': BASIS, 'rejection_reasons': reasons,
                       'kept_as': 'evidence only (stored file untouched)',
                       'approval_record': 'ENG-20261021-EP005-BATCH1-MOTION-REVIEW-RECONCILED'})
        r = sb('PATCH', f'/rest/v1/asset_registry?asset_id=eq.{aid}&id=eq.{row["id"]}',
               {'Content-Type': 'application/json', 'Prefer': 'return=representation'},
               json.dumps({'status': decision, 'metadata_json': md}).encode())
        back = json.loads(sb('GET', f'/rest/v1/asset_registry?asset_id=eq.{aid}&select=*').body)
        g2 = sb('GET', f"/storage/v1/object/authenticated/{row['storage_path']}")
        ok = r.status == 200 and len(back) == 1 and back[0]['status'] == decision and back[0]['metadata_json']['sha256'] == want \
            and g2.status == 200 and sha(g2.body) == want
        LEDGER.append(f'HUMAN_{decision}_BOUND' if ok else 'DECISION_BIND_FAILED', f'EP005-B1V4-{aid}', asset_id=aid,
                      registry_id=row['id'], sha256=want, status_before='REVIEW', status_after=back[0]['status'] if back else None,
                      storage_readback_sha256=sha(g2.body) if g2.status == 200 else None, reasons=reasons)
        if not ok:
            sys.exit(f'STOP {aid}: decision bind/readback failed (HTTP {r.status})')
        out[aid] = {'before': row, 'after': back[0]}
        print(aid, 'REVIEW ->', decision, 'readback sha OK')
    (HERE / 'B1_V04_DECISION_ROWS_READBACK_v1.json').write_text(json.dumps(out, indent=1) + '\n')


if __name__ == '__main__':
    main()
