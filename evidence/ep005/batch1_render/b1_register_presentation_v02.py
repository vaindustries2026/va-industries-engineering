"""Preserve + register the four v02 presentation MP4s as REVIEW candidates; record the Company Brain v01 presentation
rejection (v01 rows / objects are left untouched as historical REVIEW evidence). Never APPROVED here.

Usage (repo root): python3 evidence/ep005/batch1_render/b1_register_presentation_v02.py <work dir>
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
REJECTION = ('Company Brain 2026-10-21: visual composition / G03 content of S005, S013, S017, S019 ACCEPTED; the v01 MP4s are '
             'REJECTED AS FINAL VIDEO PRESENTATION: effectively static images held 4-5 s, ambience mean about -44.5 dB / peak '
             'about -30.5 dB (inaudible in normal playback); decoded frame differences are H.264 noise, not animation. New QC '
             'principle: a REVIEW shot is not presentation-ready merely because container, duration and hashes are valid.')


def main(work):
    work = Path(work)
    res = json.loads((work / 'RUN_A' / 'PRESENTATION_RESULT.json').read_text())
    qc = json.loads((work / 'PRESENTATION_QC_v02.json').read_text())
    v01 = {r['asset_id']: r for r in json.loads(sb('GET', '/rest/v1/asset_registry?asset_id=like.SHOT-EP005-S0*-ASSEMBLED-CAND-v01'
                                                   '&select=id,asset_id,status,updated_at,metadata_json').body)}
    out = {}
    for sid in ('S005', 'S013', 'S017', 'S019'):
        r, q = res[sid], qc[sid]
        if q['result'] != 'PASS' or q['mp4_sha256'] != r['mp4_sha256']:
            sys.exit(f'STOP {sid}: QC not PASS')
        old = v01[f'SHOT-EP005-{sid}-ASSEMBLED-CAND-v01']
        LEDGER.append('HUMAN_REJECTED_AS_PRESENTATION', f'EP005-B1-SHOT-EP005-{sid}-ASSEMBLED-CAND-v01', shot_id=sid,
                      rejected_sha256=old['metadata_json']['sha256'], reason=REJECTION, visual_content='ACCEPTED',
                      row_left_unchanged={'status': old['status'], 'updated_at': old['updated_at']})
        aid = f'SHOT-EP005-{sid}-ASSEMBLED-CAND-v02'
        key = f'visual/production/ep005/shots/{aid}.mp4'
        cand = work / 'review' / f'{aid}.mp4'
        cand.parent.mkdir(exist_ok=True)
        shutil.copyfile(work / 'RUN_A' / sid / f'{sid}_PRESENTATION_v02.mp4', cand)
        data = cand.read_bytes()
        if sha(data) != r['mp4_sha256']:
            sys.exit(f'STOP {sid}: copy differs')
        if sb('GET', f'/storage/v1/object/authenticated/{BUCKET}/{key}').status == 200 or \
                json.loads(sb('GET', f'/rest/v1/asset_registry?asset_id=eq.{aid}&select=id').body):
            sys.exit(f'STOP {sid}: target exists (no overwrite)')
        up = sb('POST', f'/storage/v1/object/{BUCKET}/{key}', {'Content-Type': 'video/mp4', 'x-upsert': 'false'}, data)
        upj = json.loads(up.body or b'{}')
        rb = sb('GET', f'/storage/v1/object/authenticated/{BUCKET}/{key}')
        if not (up.status == 200 and rb.status == 200 and sha(rb.body) == r['mp4_sha256']):
            sys.exit(f'STOP {sid}: upload/readback failed')
        LEDGER.append('REVIEW_MP4_STORED', f'EP005-B1-{aid}', http_status=up.status, object_key=key, object_id=upj.get('Id'),
                      readback_sha256=sha(rb.body))
        row = {'asset_id': aid, 'asset_name': f'EP005 {sid} assembled shot candidate v02 (deterministic presentation pass)',
               'asset_type': 'SHOT_RENDER', 'asset_subtype': 'ASSEMBLED_SHOT', 'version': 'v02', 'status': 'REVIEW', 'aliases': [],
               'storage_path': f'{BUCKET}/{key}', 'source_url': None,
               'metadata_json': {
                   'episode_code': 'EP-CANDIDATE-005', 'shot_id': sid, 'sha256': r['mp4_sha256'], 'bytes': len(data), 'container': 'mp4',
                   'video': f"h264 yuv420p 1920x1080 24/1, {r['frames']} frames", 'audio': 'aac LC 48 kHz stereo',
                   'frames': r['frames'], 'fps': '24/1', 'dimensions': '1920x1080', 'duration_s': r['duration_s'],
                   'storage_object_key': key, 'storage_object_id': upj.get('Id'),
                   'approved': False, 'human_decision': 'PENDING', 'approve_by': f"exact sha256 {r['mp4_sha256']}",
                   'supersedes_presentation_of': f'SHOT-EP005-{sid}-ASSEMBLED-CAND-v01 (REJECTED as presentation; kept as history)',
                   'record': 'ENG-20261021-EP005-BATCH1-FIRST-FOUR-SHOTS-V02-PRESENTATION',
                   'provenance': {
                       'pipeline': 'approved G03 frame (re-applied from the APPROVED G03 record, SHA-verified) -> deterministic 2D '
                                   'camera transform (whole image) -> governed mix_motion_audio + encode_review '
                                   '(evidence/ep005/batch1_render/b1_presentation_v02.py)',
                       'base_frame_sha256': r['base_frame_sha256'], 'g03_record_sha256': r['g03_record_sha256'],
                       'g03_frame_sha256': r['g03_frame_sha256'], 'camera': r['camera'],
                       'audio': {'bed': 'AMB-BATHROOM-QUIET-v01', 'gain_db': r['audio']['gain_db'],
                                 'measured': {k: q['audio'][k] for k in ('integrated_lufs', 'true_peak_dbtp', 'sample_peak_dbfs',
                                                                         'mean_volume_db', 'max_volume_db')}},
                       'two_run_determinism': {'runs': 2, 'byte_identical': True, 'sha256': r['mp4_sha256']},
                       'qc': {'result': q['result'], 'checks': q['checks'], 'motion': q['motion']},
                       'lineage': {'script': '6498ea8d (v05)', 'manifest': '0325d35c', 'readiness': '69bff641'},
                       'excluded': ['dialogue', 'SFX', 'music', 'generative video', 'interpolation', 'character animation',
                                    'base-frame change', 'G03/G08 change']}},
               'notes': f'REVIEW v02 presentation candidate for {sid}: same approved pixels with a deterministic camera push and '
                        'audible approved ambience. Human decision pending on exact SHA-256.'}
        ins = sb('POST', '/rest/v1/asset_registry', {'Content-Type': 'application/json', 'Prefer': 'return=representation'},
                 json.dumps(row).encode())
        body = json.loads(ins.body or b'[]')
        rid = body[0]['id'] if ins.status == 201 and body else None
        back = json.loads(sb('GET', f'/rest/v1/asset_registry?asset_id=eq.{aid}&select=*').body) if rid else []
        ok = bool(back) and back[0]['status'] == 'REVIEW' and back[0]['metadata_json']['sha256'] == r['mp4_sha256'] \
            and back[0]['metadata_json']['approved'] is False
        LEDGER.append('REVIEW_ROW_INSERTED_READBACK_OK' if ok else 'REVIEW_ROW_FAILED', f'EP005-B1-{aid}', http_status=ins.status,
                      asset_registry_id=rid)
        if not ok:
            sys.exit(f'STOP {sid}: registry insert/readback failed')
        out[sid] = back[0]
        print(sid, aid, r['mp4_sha256'], upj.get('Id'), rid)
    after = {r['asset_id']: (r['status'], r['updated_at']) for r in json.loads(sb('GET', '/rest/v1/asset_registry?asset_id=like.'
             'SHOT-EP005-S0*-ASSEMBLED-CAND-v01&select=asset_id,status,updated_at').body)}
    print('v01 rows after:', after)
    (HERE / 'B1_V02_REVIEW_CANDIDATE_ROWS_READBACK_v1.json').write_text(json.dumps({'v02': out, 'v01_after': after}, indent=1) + '\n')


if __name__ == '__main__':
    main(sys.argv[1])
