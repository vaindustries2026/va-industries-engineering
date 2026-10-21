"""Preserve the two v04 replacement raw Kling 3.0 Turbo outputs (SHOT_MOTION / RAW_MOTION_SOURCE, REVIEW; exact provider bytes,
x-upsert false + readback). Both failed visual QC (B1_MOTION_V04_VISUAL_QC_v1.json), so no SHOT-...-ASSEMBLED-CAND-v04 is made.
Nothing is APPROVED or REJECTED here (human decisions). Usage (repo root):
  python3 evidence/ep005/batch1_motion_v04/b1_register_motion_v04.py <work dir>"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import b1_motion_v04  # noqa: E402,F401  (rebinds b1_motion_v03 to the v04 ledger/package/scope)
import b1_motion_v03 as M  # noqa: E402
from b1_register_motion_v03 import BUCKET, insert, put, sha  # noqa: E402

VERDICTS = json.loads((HERE / 'B1_MOTION_V04_VISUAL_QC_v1.json').read_text())['verdicts']
PREV = {'S013': 'MOTION-EP005-S013-KLING30T-CAND-v01', 'S019': 'MOTION-EP005-S019-KLING30T-CAND-v01'}


def main(work):
    work = Path(work)
    pk = json.loads(M.PKG.read_text())['packages']
    out = {'raw': {}, 'assembled': {}}
    for sid in b1_motion_v04.ORDER:
        rr, v = M.raw_rec(sid), VERDICTS[sid]
        aid = f'MOTION-EP005-{sid}-KLING30T-CAND-v02'
        data = (work / 'raw' / sid / rr['raw_file']).read_bytes()
        if sha(data) != rr['RAW_VIDEO_SHA256'] or v['raw_sha256'] != rr['RAW_VIDEO_SHA256']:
            sys.exit(f'STOP {sid}: raw bytes changed')
        key = f'visual/production/ep005/motion/{aid}.mp4'
        oid = put(key, data, 'video/mp4')
        row = insert({'asset_id': aid, 'asset_name': f'EP005 {sid} raw motion (Kling 3.0 Turbo 720p) replacement candidate v02',
                      'asset_type': 'SHOT_MOTION', 'asset_subtype': 'RAW_MOTION_SOURCE', 'version': 'v02', 'status': 'REVIEW',
                      'aliases': [], 'storage_path': f'{BUCKET}/{key}', 'source_url': None,
                      'metadata_json': {'episode_code': 'EP-CANDIDATE-005', 'shot_id': sid, 'sha256': rr['RAW_VIDEO_SHA256'],
                                        'bytes': rr['RAW_BYTES'], 'duration_s': rr['RAW_DURATION'], 'dimensions': rr['RAW_DIMENSIONS'],
                                        'fps': rr['RAW_FPS'], 'frames': rr['RAW_FRAMES'], 'codec': rr['RAW_CODEC'],
                                        'provider_audio_present': rr['RAW_AUDIO_PRESENT'], 'storage_object_key': key, 'storage_object_id': oid,
                                        'provider': 'HIGGSFIELD', 'model': M.MODEL, 'provider_request_id': rr['REQUEST_ID'], 'attempt': 1,
                                        'prompt_sha256': pk[sid]['PROMPT_SHA256'], 'request_body_sha256': pk[sid]['REQUEST_BODY_SHA256'],
                                        'start_image_sha256': pk[sid]['START_IMAGE_SHA'], 'provider_original_md5': rr['md5'],
                                        'replacement_for': PREV[sid] if sid == 'S019' else 'SHOT-EP005-S013-ASSEMBLED-CAND-v03',
                                        'visual_qc_verdict': v['verdict'], 'visual_qc': {k: x for k, x in v.items() if k != 'notes'},
                                        'visual_qc_notes': v['notes'], 'assembled': False,
                                        'approved': False, 'human_decision': 'PENDING',
                                        'record': 'ENG-20261021-EP005-BATCH1-MOTION-REVIEW-RECONCILED'},
                      'notes': f"Raw Kling 3.0 Turbo replacement output for {sid} (request {rr['REQUEST_ID']}, attempt 1, no retry), "
                               f"exact provider bytes. Visual QC: {v['verdict']} (hard negative violated). Kept as evidence; not approved."})
        M.LEDGER.append('RAW_MOTION_PRESERVED_PRODUCTION', M.scope(sid), asset_id=aid, storage_object_id=oid, registry_id=row['id'],
                        sha256=rr['RAW_VIDEO_SHA256'], visual_qc_verdict=v['verdict'])
        if v['verdict'] != 'PASS':
            M.LEDGER.append('SHOT_FAILED_NO_RETRY', M.scope(sid), reason='; '.join(v['notes'][2:3]), v04_created=False)
        out['raw'][sid] = row
        print('raw', sid, aid, oid, row['id'], v['verdict'])
    (HERE / 'B1_MOTION_V04_ROWS_READBACK_v1.json').write_text(json.dumps(out, indent=1) + '\n')


if __name__ == '__main__':
    main(sys.argv[1])
