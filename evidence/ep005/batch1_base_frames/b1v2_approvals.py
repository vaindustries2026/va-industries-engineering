"""EP005 Batch 1 v2: bind the Company Brain approvals (F01 v02, F03 v02, F15 dedicated), preserve + register them, and
register the F11/S026 reuse binding of the approved S027 base frame. No provider call.

Usage (repo root):
  python3 evidence/ep005/batch1_base_frames/b1v2_approvals.py bridge <work dir>
  python3 evidence/ep005/batch1_base_frames/b1v2_approvals.py preserve F01_V02|F03_V02|F15_V02 <work dir>
  python3 evidence/ep005/batch1_base_frames/b1v2_approvals.py bind_f11
Same governance pattern as the F09 preservation (b1_review_decisions.py): no-overwrite storage upload (x-upsert false),
SHA readback, a single registry insert (no upsert), row readback. Family binding follows the authoritative frame-family
map (EP005_BASE_FRAME_PREFLIGHT_v1.json): the row's shot_id is the family's primary shot and frame_family_members lists
every member shot (the batch driver binds the family frame to each member). F11 is a reuse binding only: a registry row
pointing at the existing S027 storage object (no copy, no pixel change).
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))
from agent008.hashing import sha256_file  # noqa: E402
from agent008.motion.authorisation import AttemptLedger  # noqa: E402
from b1_review_decisions import BUCKET, rgb_sha, sb, sha  # noqa: E402

LEDGER = AttemptLedger(HERE / 'B1V2_APPROVAL_LEDGER_v1.jsonl')
PRE = json.loads((ROOT / 'evidence/ep005/base_frame_preflight/EP005_BASE_FRAME_PREFLIGHT_v1.json').read_text())
FAMILY = {f['id']: f for f in PRE['families']}
DECIDED_BY = 'Company Brain / Gilang (human decision 2026-10-20; product-first production tolerance)'
APPROVALS = {  # package: (family id, normalised file sha, reviewed RGB sha, accepted variances, accepted items)
    'F01_V02': ('F01-MIRROR-OPEN', '5710032060494eea80bb6ac95bb31a3a1345caadfb8f711fa118de4ebcb1a845',
                'c963f4d2e01997d49b3d5bc85082ae204e883340405e39ad8744af57601ce0fd',
                ["part of Mikko's real rear head/shoulder remains visible at frame-left: accepted as an over-the-shoulder "
                 'compositional element', "Mikko's mirror reflection remains the primary readable facial performance",
                 "Lumi's corrected anatomy is accepted"], []),
    'F03_V02': ('F03-OVERSHOULDER-LUMI', 'ac93ecfb986dbed9ea32525dc8be7851cb790f6b59c656d7cd41815588ed5410',
                'df5e11f9477be96151ec3a8c1127b20081cacad41302fa191a3f00ac3136c253',
                ['mirror glass is approximately 34% of frame height rather than the requested approximate 40%',
                 'camera reads slightly more beside-Lumi than strict over-shoulder',
                 'Company Brain determines the mirror area is sufficient for G03 smudge readability and G08 glint treatment'], []),
    'F15_V02': ('F15-MACRO-REFLECTION', 'e7a3936d8ab6f3fff5d2d39a5b349f6159f4eeb22953dbf715f45df8dfbdc690',
                '671b79d22abc1f8d26566d9c73c14b75b14bc47b1535a913c029a42234f5deba',
                ['top-petal proximity to the upper frame edge'],
                ['deliberate macro composition', 'large readable Mikko reflection', 'no distracting edge intrusion',
                 'bathroom continuity', 'Lumi hand / mirror interaction', 'image quality']),
}
S027 = ('FRAME-EP005-S027-BASE-v01', '81b841a6ab53219b26755c4e83a9777953a2d03f37213875e38691c112f0061b')
F11_ID = 'FRAME-EP005-S026-BASE-REUSE-v01'


def cand(p):
    return json.loads((HERE / f"FRAME-EP005-{p[:3]}-BASE-CAND-v02_REVIEW_CANDIDATE.json").read_text())


def local_path(work, p):
    return Path(work) / p / 'norm_A' / f"FRAME-EP005-{p[:3]}-BASE-CAND-v02_DERIVED_FRAME_CANDIDATE.png"


def bridge(work):
    ok_all = True
    for p, (fam, file_sha, px_sha, variances, accepted) in APPROVALS.items():
        path = local_path(work, p)
        got_f, got_px = sha256_file(path), rgb_sha(path)
        ok = got_f == file_sha == cand(p)['NORMALISED_SHA_A'] and got_px == px_sha == cand(p)['CANONICAL_RGB_PIXEL_SHA']
        LEDGER.append('PIXEL_BRIDGE_PASS' if ok else 'PIXEL_BRIDGE_FAIL', f'EP005-B1V2-REVIEW-{p}', package=p,
                      local_file_sha256=got_f, local_rgb_pixel_sha256=got_px, reviewed_rgb_pixel_sha256=px_sha,
                      method="SHA256(PIL Image.open(file).convert('RGB').tobytes())")
        if ok:
            LEDGER.append('HUMAN_APPROVED', f'EP005-B1V2-REVIEW-{p}', package=p, frame_family=fam,
                          frame_id=cand(p)['frame_id'], approved_normalised_sha256=file_sha, decided_by=DECIDED_BY,
                          accepted_variances=variances, accepted=accepted, family_state='CLOSED_APPROVED',
                          no_further_generation=f'{p[:3]} v03 requires explicit Company Brain reopening')
        ok_all &= ok
        print(p, 'PIXEL_BRIDGE', 'PASS' if ok else 'FAIL', got_px)
    return ok_all


def preserve(p, work):
    fam, file_sha, px_sha, variances, accepted = APPROVALS[p]
    if not any(r['event'] == 'HUMAN_APPROVED' for r in LEDGER.entries(f'EP005-B1V2-REVIEW-{p}')):
        sys.exit(f'STOP {p}: approval not bound (pixel bridge)')
    c = cand(p)
    fid, key = c['frame_id'], f"visual/production/ep005/frames/{c['frame_id']}.png"
    data = local_path(work, p).read_bytes()
    if sha(data) != file_sha:
        sys.exit(f'STOP {p}: local bytes differ from the approved SHA')
    f = FAMILY[fam]
    name = f"EP005 {fam.split('-')[0]} Base Frame v02 ({f['primary']})"
    scope = f'EP005-B1V2-PRESERVE-{p}'
    pre_obj = sb('GET', f'/storage/v1/object/authenticated/{BUCKET}/{key}')
    pre_row = json.loads(sb('GET', f'/rest/v1/asset_registry?asset_id=eq.{fid}&select=id').body)
    pre_name = json.loads(sb('GET', '/rest/v1/asset_registry?asset_name=eq.' + name.replace(' ', '%20') + '&select=id').body)
    if pre_obj.status == 200 or pre_row or pre_name:
        sys.exit(f'STOP {p}: target exists (storage {pre_obj.status}, rows {len(pre_row)}, names {len(pre_name)})')
    LEDGER.append('PRESERVE_PRECHECK_PASS', scope, storage_key=key, storage_get_status=pre_obj.status, registry_rows=0,
                  name_rows=0)
    up = sb('POST', f'/storage/v1/object/{BUCKET}/{key}', {'Content-Type': 'image/png', 'x-upsert': 'false'}, data)
    upj = json.loads(up.body or b'{}')
    LEDGER.append('STORAGE_UPLOADED' if up.status == 200 else 'STORAGE_UPLOAD_FAILED', scope, http_status=up.status,
                  object_key=key, object_id=upj.get('Id'), bytes=len(data))
    if up.status != 200:
        sys.exit(f'STOP {p}: storage upload HTTP {up.status}')
    rb = sb('GET', f'/storage/v1/object/authenticated/{BUCKET}/{key}')
    rb_sha = sha(rb.body) if rb.status == 200 else None
    LEDGER.append('STORAGE_READBACK_SHA256_MATCH' if rb_sha == file_sha else 'STORAGE_READBACK_FAILED', scope,
                  http_status=rb.status, readback_sha256=rb_sha, readback_bytes=len(rb.body))
    if rb_sha != file_sha:
        sys.exit(f'STOP {p}: storage readback mismatch')
    (Path(work) / p / 'stored_readback.png').write_bytes(rb.body)
    pkg_file = 'B1_F15_DEDICATED_PACKAGE_v1.json' if p == 'F15_V02' else 'B1_V02_CORRECTION_PACKAGES_v1.json'
    lock = '90689a7f56d2550a22cec079c4d6cb09c211ce8e' if p == 'F15_V02' else '3775b46d81bc6ba4c4251b0e669671ecbc25c881'
    gen = [json.loads(x) for x in (HERE / 'B1V2_GENERATION_LEDGER_v1.jsonl').read_text().splitlines() if x.strip()]
    raw = next(r for r in gen if r['event'] == 'RAW_OUTPUT_PRESERVED' and r['PACKAGE'] == p)
    row = {
        'asset_id': fid, 'asset_name': name, 'asset_type': 'SHOT_FRAME', 'asset_subtype': 'BASE_FRAME', 'version': 'v02',
        'status': 'APPROVED', 'aliases': [], 'storage_path': f'{BUCKET}/{key}', 'source_url': None,
        'metadata_json': {
            'canon_scope': 'MIKKO_LUMI_EP005_SHOT_SPECIFIC_PRODUCTION_ASSET', 'not_c1_canon': True,
            'canon_role': f'{fam} base frame (shot-specific; not global character canon)',
            'episode_code': 'EP-CANDIDATE-005', 'shot_id': f['primary'], 'frame_family': fam,
            'frame_family_members': f['members'], 'frame_family_code_ready_members': f['code_ready_members'],
            'frame_family_blocked_members': f['blocked_only_members'], 'frame_family_state': 'CLOSED_APPROVED',
            'frame_family_kind': 'GENERATE' + (' (dedicated; supersedes the REJECTED F09 crop FRAME-EP005-F15-BASE-CAND-v01)'
                                               if p == 'F15_V02' else ''),
            'frame_id': fid, 'sha256': file_sha, 'rgb24_sha256': px_sha, 'bytes': len(data), 'width': 1920, 'height': 1080,
            'dimensions': '1920x1080', 'format': 'PNG 8-bit RGB non-interlaced', 'content_type': 'image/png',
            'has_alpha': False, 'storage_object_key': key, 'storage_object_id': upj.get('Id'),
            'provenance': {
                'provider': 'HIGGSFIELD', 'model': 'Marketing Studio Image 2.5 Flare',
                'endpoint': 'POST https://api.higgsfield.ai/marketing-studio/image/flare',
                'provider_request_id': c['provider_request_id'], 'raw_provider_sha256': c['raw']['RAW_SHA256'],
                'raw_bytes': c['raw']['RAW_BYTE_SIZE'], 'raw_dimensions': c['raw']['RAW_DIMENSIONS'],
                'raw_format': c['raw']['RAW_FORMAT'], 'raw_provider_md5_etag': raw['md5'],
                'raw_state': 'LOCKED_ORIGINAL_FOR_NORMALISATION (not creative approval)',
                'prompt_sha256': c['prompt_sha256'], 'request_body_sha256': c['request_body_sha256'],
                'reference_sha256s': c['reference_sha256s'], 'generation_attempts': 1, 'automatic_retries': 0,
                'package': f'evidence/ep005/batch1_base_frames/{pkg_file}', 'package_lock_commit': lock},
            'normalisation': {**c['normalisation'], 'two_run_determinism': {
                'runs': 2, 'run_sha256': [c['NORMALISED_SHA_A'], c['NORMALISED_SHA_B']],
                'byte_identical': c['NORMALISATION_DETERMINISM_PASS']}, 'generative_modification': False,
                'raw_unchanged': c['raw_unchanged']},
            'pixel_equivalence': {'method': "SHA256(PIL Image.open(file).convert('RGB').tobytes())",
                                  'company_brain_reviewed_rgb_sha256': px_sha, 'local_rgb_sha256': px_sha, 'result': 'PASS'},
            'approved': True, 'human_decision': 'APPROVED', 'human_approval': 'APPROVED', 'approved_sha256': file_sha,
            'approve_by': f'exact sha256 {file_sha}', 'approval_authority': 'Company Brain / Gilang',
            'approval_record': 'ENG-20261020-EP005-BATCH1-FRAMES-APPROVED-PLACEMENT-REVIEW',
            'accepted_human_variances': variances, 'accepted_items': accepted,
            'governance_mode': 'PRODUCT_FIRST production tolerance (Company Brain 2026-10-20)',
            'g03_applied': False, 'g08_applied': False,
            'generation_record': 'evidence/ep005/batch1_base_frames/B1V2_GENERATION_RECORD_v1.json'},
        'notes': f"Approved EP005 {fam} base frame v02 (Higgsfield Flare request {c['provider_request_id']}, G04 normalised "
                 f"1920x1080). SHA-256 {file_sha[:8]}...{file_sha[-4:]}. Members {', '.join(f['members'])}. Not C1/global "
                 'canon. Company Brain approval 2026-10-20 (product-first; variances recorded).'}
    ins = sb('POST', '/rest/v1/asset_registry', {'Content-Type': 'application/json', 'Prefer': 'return=representation'},
             json.dumps(row).encode())
    insj = json.loads(ins.body or b'[]')
    rid = insj[0]['id'] if ins.status == 201 and insj else None
    LEDGER.append('REGISTRY_INSERTED' if rid else 'REGISTRY_INSERT_FAILED', scope, http_status=ins.status,
                  asset_registry_id=rid, asset_id=fid)
    if not rid:
        sys.exit(f'STOP {p}: registry insert HTTP {ins.status}')
    back = json.loads(sb('GET', f'/rest/v1/asset_registry?asset_id=eq.{fid}&select=*').body)
    ok = (len(back) == 1 and back[0]['status'] == 'APPROVED' and back[0]['metadata_json']['sha256'] == file_sha
          and back[0]['metadata_json']['approved'] is True)
    LEDGER.append('REGISTRY_READBACK_OK' if ok else 'REGISTRY_READBACK_MISMATCH', scope, asset_registry_id=rid,
                  created_at=back[0]['created_at'] if back else None)
    (HERE / f'{fid}_REGISTRY_ROW_INSERTED.json').write_text(json.dumps(back, indent=1) + '\n')
    print(p, 'preserved', up.status, upj.get('Id'), 'readback', rb_sha == file_sha, 'row', rid, 'readback ok', ok)


def bind_f11():
    src = json.loads(sb('GET', f'/rest/v1/asset_registry?asset_id=eq.{S027[0]}&select=id,status,storage_path,metadata_json').body)
    if len(src) != 1 or src[0]['status'] != 'APPROVED' or src[0]['metadata_json']['sha256'] != S027[1]:
        sys.exit('STOP: S027 source not APPROVED at the authoritative SHA')
    key = src[0]['storage_path'].split('/', 1)[1]
    b = sb('GET', f'/storage/v1/object/authenticated/{BUCKET}/{key}')
    if b.status != 200 or sha(b.body) != S027[1]:
        sys.exit('STOP: S027 stored bytes differ from the authoritative SHA')
    if json.loads(sb('GET', f'/rest/v1/asset_registry?asset_id=eq.{F11_ID}&select=id').body):
        sys.exit('STOP: F11 binding row exists')
    md = src[0]['metadata_json']
    row = {
        'asset_id': F11_ID, 'asset_name': 'EP005 S026 Base Frame (reuse of S027 base frame)', 'asset_type': 'SHOT_FRAME',
        'asset_subtype': 'BASE_FRAME', 'version': 'v01', 'status': 'APPROVED', 'aliases': [],
        'storage_path': src[0]['storage_path'], 'source_url': None,
        'metadata_json': {
            'canon_scope': 'MIKKO_LUMI_EP005_SHOT_SPECIFIC_PRODUCTION_ASSET', 'not_c1_canon': True,
            'canon_role': 'S026 motion base frame = REUSE_EXISTING binding of the approved S027 base frame (no copy)',
            'episode_code': 'EP-CANDIDATE-005', 'shot_id': 'S026', 'frame_family': 'F11-S027-START-REUSE',
            'frame_family_members': ['S026'], 'frame_family_state': 'APPROVED_REUSE', 'binding_type': 'REUSE_EXISTING',
            'reuse_of_asset_id': S027[0], 'reuse_of_registry_id': src[0]['id'], 'frame_id': F11_ID, 'sha256': S027[1],
            'bytes': md.get('bytes'), 'dimensions': md.get('dimensions'), 'content_type': 'image/png',
            'storage_object_key': key, 'storage_object_id': md.get('storage_object_id'),
            'storage_note': 'points at the existing S027 object; no duplicate bytes were written',
            'pixel_operations': {'crop': None, 'scale': None, 'pixel_edit': None, 'bytes_unchanged': True,
                                 'verified_sha256_at_binding': sha(b.body)},
            'approved': True, 'human_decision': 'APPROVED', 'human_approval': 'APPROVED', 'approved_sha256': S027[1],
            'approve_by': f'exact sha256 {S027[1]}', 'approval_authority': 'Company Brain / Gilang',
            'approval_record': 'ENG-20261020-EP005-BATCH1-FRAMES-APPROVED-PLACEMENT-REVIEW'},
        'notes': 'S026 reuse binding of FRAME-EP005-S027-BASE-v01 (REUSE_EXISTING; bytes unchanged, same storage object, '
                 'SHA 81b841a6...061b). Company Brain approval 2026-10-20. S027 row untouched.'}
    ins = sb('POST', '/rest/v1/asset_registry', {'Content-Type': 'application/json', 'Prefer': 'return=representation'},
             json.dumps(row).encode())
    insj = json.loads(ins.body or b'[]')
    rid = insj[0]['id'] if ins.status == 201 and insj else None
    LEDGER.append('F11_REUSE_BINDING_INSERTED' if rid else 'F11_REUSE_BINDING_FAILED', 'EP005-B1V2-F11-S026',
                  http_status=ins.status, asset_registry_id=rid, asset_id=F11_ID, reuse_of=S027[0], sha256=S027[1],
                  source_bytes_verified=True, storage_objects_written=0)
    if not rid:
        sys.exit(f'STOP: F11 insert HTTP {ins.status}')
    back = json.loads(sb('GET', f'/rest/v1/asset_registry?asset_id=eq.{F11_ID}&select=*').body)
    src_after = json.loads(sb('GET', f'/rest/v1/asset_registry?asset_id=eq.{S027[0]}&select=updated_at,status').body)
    LEDGER.append('F11_REUSE_BINDING_READBACK_OK' if len(back) == 1 and back[0]['metadata_json']['sha256'] == S027[1] else
                  'F11_REUSE_BINDING_READBACK_MISMATCH', 'EP005-B1V2-F11-S026', asset_registry_id=rid,
                  s027_row_after=src_after)
    (HERE / f'{F11_ID}_REGISTRY_ROW_INSERTED.json').write_text(json.dumps(back, indent=1) + '\n')
    print('F11 binding', rid, 'S027 row after', src_after)


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'bridge':
        sys.exit(0 if bridge(sys.argv[2]) else 'STOP: a pixel bridge failed')
    elif cmd == 'preserve':
        preserve(sys.argv[2], sys.argv[3])
    elif cmd == 'bind_f11':
        bind_f11()
