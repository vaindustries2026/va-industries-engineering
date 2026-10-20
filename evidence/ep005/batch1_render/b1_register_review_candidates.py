"""Preserve + register the four Batch 1 review MP4s as REVIEW candidates (S029 lifecycle; never APPROVED here).

Usage (repo root): python3 evidence/ep005/batch1_render/b1_register_review_candidates.py <render work dir>
Exact RUN1/renderA bytes (equal to RUN1/renderB, RUN2/renderA, RUN2/renderB) are copied to the candidate file name, uploaded
with x-upsert false (no overwrite), read back by SHA, and registered SHOT_RENDER / ASSEMBLED_SHOT, status REVIEW,
human_decision PENDING, approved false (single insert, readback).
"""
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE.parent / 'batch1_base_frames'))
from agent008.motion.authorisation import AttemptLedger  # noqa: E402
from b1_review_decisions import BUCKET, sb, sha  # noqa: E402

LEDGER = AttemptLedger(HERE / 'B1_REVIEW_CANDIDATE_LEDGER_v1.jsonl')


def main(work):
    work = Path(work)
    res = json.loads((work / 'RENDER_RESULT.json').read_text())
    qc = json.loads((work / 'INDEPENDENT_QC.json').read_text())
    out = {}
    for sid in ('S005', 'S013', 'S017', 'S019'):
        s, q = res['shots'][sid], qc[sid]
        if not (s['DETERMINISM_PASS'] and q['result'] == 'PASS' and q['mp4_sha256'] == s['SHOT_A_SHA']):
            sys.exit(f'STOP {sid}: determinism/QC not PASS')
        aid = f'SHOT-EP005-{sid}-ASSEMBLED-CAND-v01'
        key = f'visual/production/ep005/shots/{aid}.mp4'
        src = work / 'RUN1' / sid / 'renderA' / f'{sid}_STILL_REVIEW.mp4'
        cand = work / 'review' / f'{aid}.mp4'
        cand.parent.mkdir(exist_ok=True)
        shutil.copyfile(src, cand)
        data = cand.read_bytes()
        if sha(data) != s['SHOT_A_SHA']:
            sys.exit(f'STOP {sid}: copy differs')
        if sb('GET', f'/storage/v1/object/authenticated/{BUCKET}/{key}').status == 200 or \
                json.loads(sb('GET', f'/rest/v1/asset_registry?asset_id=eq.{aid}&select=id').body):
            sys.exit(f'STOP {sid}: target exists (no overwrite)')
        up = sb('POST', f'/storage/v1/object/{BUCKET}/{key}', {'Content-Type': 'video/mp4', 'x-upsert': 'false'}, data)
        upj = json.loads(up.body or b'{}')
        rb = sb('GET', f'/storage/v1/object/authenticated/{BUCKET}/{key}')
        ok_rb = up.status == 200 and rb.status == 200 and sha(rb.body) == s['SHOT_A_SHA']
        LEDGER.append('REVIEW_MP4_STORED' if ok_rb else 'REVIEW_MP4_STORE_FAILED', f'EP005-B1-{aid}', http_status=up.status,
                      object_key=key, object_id=upj.get('Id'), readback_sha256=sha(rb.body) if rb.status == 200 else None)
        if not ok_rb:
            sys.exit(f'STOP {sid}: upload/readback failed')
        r1 = s['run1']['result']
        rec_rows = res['records_bound'][sid]
        row = {'asset_id': aid, 'asset_name': f'EP005 {sid} assembled shot candidate (Agent-008 still-shot compositor)',
               'asset_type': 'SHOT_RENDER', 'asset_subtype': 'ASSEMBLED_SHOT', 'version': 'v01', 'status': 'REVIEW',
               'aliases': [], 'storage_path': f'{BUCKET}/{key}', 'source_url': None,
               'metadata_json': {
                   'episode_code': 'EP-CANDIDATE-005', 'shot_id': sid, 'sha256': s['SHOT_A_SHA'], 'bytes': len(data),
                   'container': 'mp4', 'video': f"h264 {q['video']['profile']} {q['video']['pix_fmt']} 1920x1080 24/1, {q['expected_frames']} frames",
                   'audio': 'aac LC 48 kHz stereo', 'frames': q['expected_frames'], 'fps': '24/1', 'dimensions': '1920x1080',
                   'duration_s': q['video']['duration_s'], 'storage_object_key': key, 'storage_object_id': upj.get('Id'),
                   'approved': False, 'human_decision': 'PENDING', 'approve_by': f"exact sha256 {s['SHOT_A_SHA']}",
                   'record': 'ENG-20261020-EP005-BATCH1-FIRST-FOUR-SHOTS',
                   'provenance': {
                       'compositor': 'Agent-008 batch driver LOCAL_RENDER_ONLY -> G03 place_overlays -> G02 compose_still_shot '
                                     '(evidence/ep005/batch1_render/b1_render_first_four.py)',
                       'inputs': {'base_frame': q['approved_frame_sha256'], 'g03_record_asset_id': rec_rows['g03_record'],
                                  'g03_record_sha256': q['approved_record_sha256'], 'g03_frame_sha256': q['g03_frame_sha256'],
                                  'overlays': 'approved overlay SHAs as bound in the G03 record',
                                  'AMB-BATHROOM-QUIET-v01': 'ea28fad468e353b99d48070d12853620f08e8b05c8d912706122d31176544d2f'},
                       'input_shas_runner': r1['input_shas'], 'two_run_determinism': {
                           'runs': 4, 'run1_renderA_eq_renderB': True, 'run1_eq_run2': True, 'sha256': s['SHOT_A_SHA']},
                       'qc': {'agent008': q['agent008_qc'], 'independent': q['result'], 'checks': q['checks']},
                       'lineage': {'script': '6498ea8d (v05)', 'manifest': '0325d35c', 'readiness': '69bff641'},
                       'excluded': ['dialogue', 'foley', 'SFX', 'music', 'camera motion', 'zoom', 'treatments', 'fade', 'text',
                                    'additional generation']}},
               'notes': f'REVIEW assembled {sid} candidate (Agent-008 still path, approved G03 record, deterministic, four renders '
                        'identical). Human decision pending on exact SHA-256.'}
        ins = sb('POST', '/rest/v1/asset_registry', {'Content-Type': 'application/json', 'Prefer': 'return=representation'},
                 json.dumps(row).encode())
        body = json.loads(ins.body or b'[]')
        rid = body[0]['id'] if ins.status == 201 and body else None
        back = json.loads(sb('GET', f'/rest/v1/asset_registry?asset_id=eq.{aid}&select=*').body) if rid else []
        ok = bool(back) and back[0]['status'] == 'REVIEW' and back[0]['metadata_json']['sha256'] == s['SHOT_A_SHA'] \
            and back[0]['metadata_json']['approved'] is False
        LEDGER.append('REVIEW_ROW_INSERTED_READBACK_OK' if ok else 'REVIEW_ROW_FAILED', f'EP005-B1-{aid}', http_status=ins.status,
                      asset_registry_id=rid)
        if not ok:
            sys.exit(f'STOP {sid}: registry insert/readback failed')
        out[sid] = {'asset_id': aid, 'sha256': s['SHOT_A_SHA'], 'storage_object_id': upj.get('Id'), 'registry_id': rid,
                    'review_file': str(cand), 'row': back[0]}
        print(sid, aid, s['SHOT_A_SHA'], upj.get('Id'), rid)
    (HERE / 'B1_REVIEW_CANDIDATE_ROWS_READBACK_v1.json').write_text(json.dumps({k: v['row'] for k, v in out.items()}, indent=1) + '\n')


if __name__ == '__main__':
    main(sys.argv[1])
