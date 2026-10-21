"""Preserve the four raw Kling 3.0 Turbo outputs (SHOT_MOTION / RAW_MOTION_SOURCE, REVIEW, S027/S028 raw-motion pattern)
and register the assembled v03 review candidates that passed visual QC (SHOT_RENDER / ASSEMBLED_SHOT, REVIEW).
Nothing is APPROVED. Usage (repo root): python3 evidence/ep005/batch1_motion/b1_register_motion_v03.py <work dir>"""
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE.parent / 'batch1_base_frames'))
from b1_review_decisions import BUCKET, sb, sha  # noqa: E402
from b1_motion_v03 import LEDGER, MODEL, PKG, raw_rec, scope  # noqa: E402

VERDICTS = json.loads((HERE / 'B1_MOTION_V03_VISUAL_QC_v1.json').read_text())['verdicts']


def put(key, data, ctype):
    if sb('GET', f'/storage/v1/object/authenticated/{BUCKET}/{key}').status == 200:
        sys.exit(f'STOP: {key} exists (no overwrite)')
    up = sb('POST', f'/storage/v1/object/{BUCKET}/{key}', {'Content-Type': ctype, 'x-upsert': 'false'}, data)
    rb = sb('GET', f'/storage/v1/object/authenticated/{BUCKET}/{key}')
    if up.status != 200 or rb.status != 200 or sha(rb.body) != sha(data):
        sys.exit(f'STOP: upload/readback {key}')
    return json.loads(up.body).get('Id')


def insert(row):
    if json.loads(sb('GET', f"/rest/v1/asset_registry?asset_id=eq.{row['asset_id']}&select=id").body):
        sys.exit(f"STOP: {row['asset_id']} exists")
    ins = sb('POST', '/rest/v1/asset_registry', {'Content-Type': 'application/json', 'Prefer': 'return=representation'},
             json.dumps(row).encode())
    body = json.loads(ins.body or b'[]')
    back = json.loads(sb('GET', f"/rest/v1/asset_registry?asset_id=eq.{row['asset_id']}&select=*").body)
    if ins.status != 201 or not back or back[0]['metadata_json']['sha256'] != row['metadata_json']['sha256'] or back[0]['status'] != 'REVIEW':
        sys.exit(f"STOP: insert/readback {row['asset_id']}")
    return back[0]


def main(work):
    work = Path(work)
    pk = json.loads(PKG.read_text())['packages']
    qc = json.loads((work / 'ASSEMBLY_QC_v03.json').read_text())
    out = {'raw': {}, 'assembled': {}}
    for sid in ('S005', 'S013', 'S017', 'S019'):
        rr, v = raw_rec(sid), VERDICTS[sid]
        aid = f'MOTION-EP005-{sid}-KLING30T-CAND-v01'
        data = (work / 'raw' / sid / rr['raw_file']).read_bytes()
        if sha(data) != rr['RAW_VIDEO_SHA256']:
            sys.exit(f'STOP {sid}: raw bytes changed')
        key = f'visual/production/ep005/motion/{aid}.mp4'
        oid = put(key, data, 'video/mp4')
        row = insert({'asset_id': aid, 'asset_name': f'EP005 {sid} raw motion (Kling 3.0 Turbo 720p) candidate v01',
                      'asset_type': 'SHOT_MOTION', 'asset_subtype': 'RAW_MOTION_SOURCE', 'version': 'v01', 'status': 'REVIEW',
                      'aliases': [], 'storage_path': f'{BUCKET}/{key}', 'source_url': None,
                      'metadata_json': {'episode_code': 'EP-CANDIDATE-005', 'shot_id': sid, 'sha256': rr['RAW_VIDEO_SHA256'],
                                        'bytes': rr['RAW_BYTES'], 'duration_s': rr['RAW_DURATION'], 'dimensions': rr['RAW_DIMENSIONS'],
                                        'fps': rr['RAW_FPS'], 'frames': rr['RAW_FRAMES'], 'codec': rr['RAW_CODEC'],
                                        'provider_audio_present': rr['RAW_AUDIO_PRESENT'], 'storage_object_key': key, 'storage_object_id': oid,
                                        'provider': 'HIGGSFIELD', 'model': MODEL, 'provider_request_id': rr['REQUEST_ID'], 'attempt': 1,
                                        'prompt_sha256': pk[sid]['PROMPT_SHA256'], 'request_body_sha256': pk[sid]['REQUEST_BODY_SHA256'],
                                        'start_image_sha256': pk[sid]['start_image']['sha256'], 'provider_original_md5': rr['md5'],
                                        'visual_qc_verdict': v['verdict'], 'visual_qc_notes': v['notes'],
                                        'approved': False, 'human_decision': 'PENDING',
                                        'record': 'ENG-20261021-EP005-BATCH1-REAL-MOTION-V03'},
                      'notes': f"Raw Kling 3.0 Turbo output for {sid} (request {rr['REQUEST_ID']}), exact provider bytes. "
                               f"Visual QC: {v['verdict']}. Not approved."})
        LEDGER.append('RAW_MOTION_PRESERVED_PRODUCTION', scope(sid), asset_id=aid, storage_object_id=oid, registry_id=row['id'],
                      sha256=rr['RAW_VIDEO_SHA256'])
        out['raw'][sid] = row
        print('raw', sid, aid, oid, row['id'])
        if v['verdict'] != 'PASS' or sid not in qc or qc[sid]['result'] != 'PASS':
            continue
        q = qc[sid]
        cid = f'SHOT-EP005-{sid}-ASSEMBLED-CAND-v03'
        mp4 = work / 'review' / f'{cid}.mp4'
        mp4.parent.mkdir(exist_ok=True)
        shutil.copyfile(work / 'assembly' / 'A' / sid / 'MOTION_SMOKE_REVIEW.mp4', mp4)
        data = mp4.read_bytes()
        if sha(data) != q['mp4_sha256']:
            sys.exit(f'STOP {sid}: assembled copy differs')
        key = f'visual/production/ep005/shots/{cid}.mp4'
        oid = put(key, data, 'video/mp4')
        row = insert({'asset_id': cid, 'asset_name': f'EP005 {sid} assembled shot candidate v03 (Kling 3.0 Turbo real motion)',
                      'asset_type': 'SHOT_RENDER', 'asset_subtype': 'ASSEMBLED_SHOT', 'version': 'v03', 'status': 'REVIEW', 'aliases': [],
                      'storage_path': f'{BUCKET}/{key}', 'source_url': None,
                      'metadata_json': {'episode_code': 'EP-CANDIDATE-005', 'shot_id': sid, 'sha256': q['mp4_sha256'], 'bytes': len(data),
                                        'container': 'mp4', 'video': 'h264 yuv420p 1920x1080 24/1, 96 frames', 'audio': 'aac LC 48 kHz stereo',
                                        'frames': 96, 'fps': '24/1', 'dimensions': '1920x1080', 'duration_s': 4.0,
                                        'storage_object_key': key, 'storage_object_id': oid, 'approved': False, 'human_decision': 'PENDING',
                                        'approve_by': f"exact sha256 {q['mp4_sha256']}",
                                        'supersedes_presentation_of': [f'SHOT-EP005-{sid}-ASSEMBLED-CAND-v01', f'SHOT-EP005-{sid}-ASSEMBLED-CAND-v02'],
                                        'record': 'ENG-20261021-EP005-BATCH1-REAL-MOTION-V03',
                                        'provenance': {'raw_motion_asset_id': f'MOTION-EP005-{sid}-KLING30T-CAND-v01',
                                                       'raw_sha256': rr['RAW_VIDEO_SHA256'], 'provider_request_id': rr['REQUEST_ID'],
                                                       'assembly': 'Agent-008 motion.compose.compose_motion_shot (fps 24, lanczos fit 1280x720 -> '
                                                                   '1920x1080, first 96 frames; G03 pre-composited in the start image, not re-applied)',
                                                       'audio': {'bed': 'AMB-BATHROOM-QUIET-v01', 'gain_db': 11.5, 'measured': q['audio'],
                                                                 'provider_audio': 'stripped (not mapped)'},
                                                       'two_run_determinism': {'byte_identical': True, 'sha256': q['mp4_sha256']},
                                                       'qc': {'assembly': q['checks'], 'visual': VERDICTS[sid]}}},
                      'notes': f'REVIEW v03 real-motion candidate for {sid} (Kling 3.0 Turbo 720p, governed assembly, ambience only). '
                               'Human decision pending on exact SHA-256.'})
        LEDGER.append('REVIEW_V03_REGISTERED', scope(sid), asset_id=cid, storage_object_id=oid, registry_id=row['id'], sha256=q['mp4_sha256'])
        out['assembled'][sid] = row
        print('v03', sid, cid, q['mp4_sha256'], oid, row['id'])
    (HERE / 'B1_MOTION_V03_ROWS_READBACK_v1.json').write_text(json.dumps(out, indent=1) + '\n')


if __name__ == '__main__':
    main(sys.argv[1])
