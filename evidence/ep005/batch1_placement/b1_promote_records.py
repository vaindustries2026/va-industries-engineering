"""EP005 Batch 1: promote the reviewed G03 (7) and G08 (3) candidate records to APPROVED production records.

Usage (repo root): python3 evidence/ep005/batch1_placement/b1_promote_records.py <scratch dir>
The records are the exact reviewed candidates (B1_PLACEMENT_CANDIDATES_v1.json @ 5be76f01, byte-identical working copy);
nothing is recomputed. Before any write, each G03 record is re-applied by the unchanged G03 module to the approved frame
(read back from storage) and its output SHA must equal the reviewed preview SHA; each G08 record must be bound to exactly
that output (S004/S012) or to the approved F01 frame (S025). Any mismatch stops before writes. Each record becomes one
asset_registry row (PRODUCTION_RECORD / G03_PLACEMENT_RECORD | G08_TREATMENT_RECORD, APPROVED) carrying the exact record
and its canonical SHA-256; a single insert (no upsert) and a readback that recomputes the canonical SHA.
"""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE.parent / 'batch1_base_frames'))
from agent008.config import load_output_spec  # noqa: E402
from agent008.episode import PINS, resolve_episode  # noqa: E402
from agent008.hashing import canonical_sha256  # noqa: E402
from agent008.inputs import load_hash_pins  # noqa: E402
from agent008.motion.authorisation import AttemptLedger  # noqa: E402
from agent008.overlay import place_overlays  # noqa: E402
from agent008.tools.snapshot_inputs import build_snapshot  # noqa: E402
from b1_review_decisions import sb, sha  # noqa: E402

REVIEW_COMMIT = '5be76f01cb160a404a23ec8431d0e1df4fb82f0f'
REL = 'evidence/ep005/batch1_placement/B1_PLACEMENT_CANDIDATES_v1.json'
LEDGER = AttemptLedger(HERE / 'B1_RECORD_PROMOTION_LEDGER_v1.jsonl')
AUTH = 'Company Brain / Gilang'
DECISIONS = {
    'DECISION_1_REAL_FACE_SMUDGES': 'APPROVED for S004, S012, S017: keep the matching physical smudges on the real face '
                                    '(mirror and real face are the same physical face state); exact candidate geometry',
    'DECISION_2_MOUTH_SIDE': "APPROVED: Mikko's RIGHT side of the mouth, opposite the cheek smudge (S001, S004, S005, S012, "
                             'S013); supersedes the Phase-0 placeholder side for these production records',
    'DECISION_3_G08_TIMINGS': 'APPROVED: S004 glint + clue chime from 0.5 s (frame 12); S012 glint from 1.0 s (frame 24); '
                              'S025 completion pop from 0.5 s (frame 12); exact reviewed geometry and timing',
}


def main(work):
    work = Path(work)
    locked = subprocess.run(['git', 'show', f'{REVIEW_COMMIT}:{REL}'], cwd=ROOT, capture_output=True, check=True).stdout
    if (ROOT / REL).read_bytes() != locked:
        sys.exit('STOP: candidate file differs from the reviewed commit')
    cand = json.loads(locked)
    specs = {x['shot_id']: x.get('spec') for x in resolve_episode(build_snapshot('69bff641-e056-4701-a23f-d91dbc2039b2'),
                                                              load_hash_pins(PINS), load_output_spec())}
    rows = {r['asset_id']: r for r in json.loads(sb('GET', '/rest/v1/asset_registry?or=(asset_id.like.FRAME-EP005-F*,'
                                                    'asset_id.like.OVERLAY-EP005-BERRY-SMUDGE-*)&select=*').body)}
    files = {}
    for aid, r in rows.items():
        g = sb('GET', f"/storage/v1/object/authenticated/{r['storage_path']}")
        if g.status != 200 or sha(g.body) != r['metadata_json']['sha256'] or r['status'] != 'APPROVED':
            sys.exit(f'STOP: {aid} not APPROVED at its registry SHA')
        p = work / 'inputs' / Path(r['storage_path']).name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(g.body)
        files[aid] = p

    # ---- verify every G03 record reproduces the reviewed output; build the G03 rows ----
    g03_rows, g03_out = [], {}
    for p in cand['G03']:
        sid, rec = p['SHOT_ID'], p['G03_RECORD']
        rsha = canonical_sha256(rec)
        if rsha != p['G03_RECORD_SHA256']:
            sys.exit(f'STOP {sid}: record SHA differs from the reviewed candidate')
        fr = rows[p['FRAME_ASSET_ID']]
        if rec['base_frame'] != {'asset_id': fr['asset_id'], 'sha256': fr['metadata_json']['sha256']} or p['FRAME_SHA'] != fr['metadata_json']['sha256']:
            sys.exit(f'STOP {sid}: record not bound to the approved frame')
        frame = {'asset_id': fr['asset_id'], 'registry_id': fr['id'], 'classification': 'SHOT_FRAME/BASE_FRAME',
                 'registry_status': 'APPROVED', 'shot_id': sid, 'path': str(files[fr['asset_id']]),
                 'expected_sha256': fr['metadata_json']['sha256']}
        sp = specs[sid]
        prov = place_overlays(sp, frame, {o['asset_id']: str(files[o['asset_id']]) for o in sp['active_overlays']},
                              {'record': rec, 'approval_status': 'APPROVED', 'expected_sha256': rsha}, work / 'verify_g03' / sid)
        if prov['output']['sha256'] != p['G03_PREVIEW_FRAME_SHA256']:
            sys.exit(f"STOP {sid}: G03 output {prov['output']['sha256']} != reviewed {p['G03_PREVIEW_FRAME_SHA256']}")
        g03_out[sid] = prov['output']['sha256']
        LEDGER.append('G03_REPRODUCED_EXACT', f'EP005-B1-G03-{sid}', record_sha256=rsha, output_sha256=prov['output']['sha256'])
        g03_rows.append({
            'asset_id': f'G03-REC-EP005-{sid}-v01', 'asset_name': f'EP005 {sid} G03 placement record v01',
            'asset_type': 'PRODUCTION_RECORD', 'asset_subtype': 'G03_PLACEMENT_RECORD', 'version': 'v01', 'status': 'APPROVED',
            'aliases': [], 'storage_path': None, 'source_url': None,
            'metadata_json': {
                'episode_code': 'EP-CANDIDATE-005', 'shot_id': sid, 'frame_family': fr['metadata_json']['frame_family'],
                'contract': rec['contract'], 'record': rec, 'record_sha256': rsha,
                'record_id_note': 'record_id keeps the reviewed candidate identity (it is part of the approved canonical SHA)',
                'base_frame_asset_id': fr['asset_id'], 'base_frame_sha256': fr['metadata_json']['sha256'],
                'placements': [{k: q[k] for k in ('asset_id', 'overlay_sha256', 'surface', 'x', 'y', 'width_px', 'rotation_deg',
                                                  'mirror', 'anatomical_meaning', 'visible_box')} for q in p['G03_PLACEMENTS']],
                'placement_count': len(p['G03_PLACEMENTS']), 'reproduced_g03_output_sha256': prov['output']['sha256'],
                'approved': True, 'human_decision': 'APPROVED', 'human_approval': 'APPROVED', 'approval_authority': AUTH,
                'approve_by': f'exact canonical record sha256 {rsha}', 'decisions': DECISIONS,
                'source_review_evidence': {'commit': REVIEW_COMMIT, 'file': REL,
                                           'preview': f'previews/{sid}_G03_PREVIEW.png (scratch)'},
                'approval_record': 'ENG-20261020-EP005-BATCH1-FIRST-FOUR-SHOTS'},
            'notes': f'Approved G03 placement record for {sid} ({len(p["G03_PLACEMENTS"])} placements) on '
                     f'{fr["asset_id"]}; exact reviewed candidate; Company Brain 2026-10-20.'})

    # ---- G08 ----
    g08_rows = []
    for sid, g in cand['G08'].items():
        rec = g['record']
        rsha = canonical_sha256(rec)
        if rsha != g['record_sha256']:
            sys.exit(f'STOP {sid}: G08 record SHA differs from the reviewed candidate')
        if sid in g03_out:
            if rec['input_frame']['sha256'] != g03_out[sid]:
                sys.exit(f'STOP {sid}: G08 input frame {rec["input_frame"]["sha256"]} != approved G03 output {g03_out[sid]}')
            dep = {'g03_record_asset_id': f'G03-REC-EP005-{sid}-v01', 'g03_output_sha256': g03_out[sid]}
        else:
            f01 = rows['FRAME-EP005-F01-BASE-CAND-v02']['metadata_json']['sha256']
            if rec['input_frame']['sha256'] != f01:
                sys.exit(f'STOP {sid}: G08 input frame not the approved F01 frame')
            dep = {'base_frame_asset_id': 'FRAME-EP005-F01-BASE-CAND-v02', 'base_frame_sha256': f01}
        g08_rows.append({
            'asset_id': f'G08-REC-EP005-{sid}-v01', 'asset_name': f'EP005 {sid} G08 treatment record v01',
            'asset_type': 'PRODUCTION_RECORD', 'asset_subtype': 'G08_TREATMENT_RECORD', 'version': 'v01', 'status': 'APPROVED',
            'aliases': [], 'storage_path': None, 'source_url': None,
            'metadata_json': {
                'episode_code': 'EP-CANDIDATE-005', 'shot_id': sid, 'contract': rec['contract'], 'record': rec,
                'record_sha256': rsha, 'input_frame_binding': dep,
                'treatments': [k for k in ('reflection', 'glint', 'pop') if k in rec],
                'approved_timing': g['proposed_timing'], 'mirror_glass_measurement': g['glass_measurement'],
                'approved': True, 'human_decision': 'APPROVED', 'human_approval': 'APPROVED', 'approval_authority': AUTH,
                'approve_by': f'exact canonical record sha256 {rsha}', 'decisions': {'DECISION_3_G08_TIMINGS': DECISIONS['DECISION_3_G08_TIMINGS']},
                'source_review_evidence': {'commit': REVIEW_COMMIT, 'file': REL,
                                           'preview': f'previews/{sid}_G08_PREVIEW.png (scratch)'},
                'approval_record': 'ENG-20261020-EP005-BATCH1-FIRST-FOUR-SHOTS'},
            'notes': f'Approved G08 treatment record for {sid}; exact reviewed candidate; Company Brain 2026-10-20.'})

    # ---- writes (after every check passed) ----
    out = []
    for row in g03_rows + g08_rows:
        aid = row['asset_id']
        if json.loads(sb('GET', f'/rest/v1/asset_registry?or=(asset_id.eq.{aid},asset_name.eq.' +
                         row['asset_name'].replace(' ', '%20') + ')&select=id').body):
            sys.exit(f'STOP: {aid} already exists')
        ins = sb('POST', '/rest/v1/asset_registry', {'Content-Type': 'application/json', 'Prefer': 'return=representation'},
                 json.dumps(row).encode())
        body = json.loads(ins.body or b'[]')
        rid = body[0]['id'] if ins.status == 201 and body else None
        if not rid:
            LEDGER.append('RECORD_INSERT_FAILED', f'EP005-B1-{aid}', http_status=ins.status)
            sys.exit(f'STOP: insert {aid} HTTP {ins.status} {ins.body[:200]!r}')
        back = json.loads(sb('GET', f'/rest/v1/asset_registry?asset_id=eq.{aid}&select=*').body)
        ok = (len(back) == 1 and back[0]['status'] == 'APPROVED'
              and canonical_sha256(back[0]['metadata_json']['record']) == row['metadata_json']['record_sha256'])
        LEDGER.append('RECORD_INSERTED_READBACK_OK' if ok else 'RECORD_READBACK_MISMATCH', f'EP005-B1-{aid}',
                      asset_registry_id=rid, record_sha256=row['metadata_json']['record_sha256'])
        if not ok:
            sys.exit(f'STOP: readback mismatch {aid}')
        out.append(back[0])
        print(aid, rid, row['metadata_json']['record_sha256'][:12], 'readback OK')
    (HERE / 'B1_APPROVED_RECORD_ROWS_READBACK_v1.json').write_text(json.dumps(out, indent=1) + '\n')


if __name__ == '__main__':
    main(sys.argv[1])
