"""EP005 Batch 1: bind the Company Brain review decisions, preserve + register F09, derive the F15 REVIEW candidate.

Usage (repo root):
  python3 evidence/ep005/batch1_base_frames/b1_review_decisions.py bridge <work dir>
  python3 evidence/ep005/batch1_base_frames/b1_review_decisions.py preserve_f09 <work dir>
  python3 evidence/ep005/batch1_base_frames/b1_review_decisions.py derive_f15 <work dir>
bridge: SHA256(Image.open(f).convert('RGB').tobytes()) of each local normalised candidate must equal the pixel hash
Company Brain reviewed; only then is the decision bound (F01 REJECTED, F03 REJECTED, F09 APPROVED) to the exact file SHA.
preserve_f09: no-overwrite storage upload (x-upsert false), SHA readback, single registry insert (no upsert), row readback.
derive_f15: governed F15 = DERIVE_CROP of the approved F09, crop MEASURED_AFTER_F09_APPROVAL, scale 1920x1080 (G04).
The crop is measured from the approved pixels (pink flower-head bbox) and pinned; two derivations must be byte-identical.
No provider call is made by any step.
"""
import hashlib
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from agent008.derive import derive_frame  # noqa: E402
from agent008.errors import FailClosed  # noqa: E402
from agent008.hashing import sha256_file  # noqa: E402
from agent008.motion.authorisation import AttemptLedger  # noqa: E402
from agent008.motion.http import UrllibHttpClient  # noqa: E402

HERE = Path(__file__).resolve().parent
LEDGER = AttemptLedger(HERE / 'B1_REVIEW_LEDGER_v1.jsonl')
SB = 'https://ziluiwrwwbayhcskeere.supabase.co'
BUCKET = 'production-assets'
DECISION_BY = 'Company Brain (human review decision, EP005 Batch 1 base frames, 2026-10-20)'
REVIEWED = {  # family: (authoritative normalised file sha, Company Brain reviewed RGB pixel sha, decision)
    'F01': ('c191a513a4987cc0be6ea713f8a8dc88566c952db0250b122270786e0aa11e10',
            'a61459c5cfdb1b178f1a641f079914ca8c3151f9475c3dbacc02585c88e7831b', 'REJECTED'),
    'F03': ('e8571476c5be0b1c263c4b9c3be2c155ed1af265c87aa0c18786b69b409c5968',
            'ff22ecffe85e866cd6727fc2bc97a71b5f3f8c5f456c30f8c4c48b18615480df', 'REJECTED'),
    'F09': ('d442b0f7ac9524319fb2d171b7891e35ea94b4877f131de77f2bced74050f13e',
            'bf6ee47c083ba484ce8174b6bde078d6f5bc196abbe15d4c52cbedd03027e117', 'APPROVED'),
}
REASONS = {
    'F01': ["Lumi's arm / hand anatomy drifts materially from the governed character design.",
            'Lumi must remain a simple floating round-orb character with tiny simple hands close to her body.',
            'The generated arm appears too elongated / limb-like.',
            'Mikko is shown predominantly from behind, reducing the robustness of this image as the shared F01 production '
            'master for S001, S005, S013 and S025.',
            'The mirror/reflection itself is useful, but the character-canon issue is sufficient for rejection.'],
    'F03': ["Lumi's lower silhouette contains extra rounded forms that read as additional lower-body appendages / lobes.",
            "This is inconsistent with Lumi's governed simple orb silhouette.",
            'The mirror glass is too small for comfortable downstream G03/G08 operation.',
            'F03 must support readable smudge placement and mirror-glint treatment for S004 and S012.',
            'The overall camera direction is close, but these production/canon issues are sufficient for rejection.'],
    'F09': ['Accepted: Mikko identity, Lumi identity, character scale relationship, bathroom continuity, medium two-shot '
            'composition, mirror placement, cloth / prop state, clean-face state, overall F09 composition for S017.'],
}
F09_ID = 'FRAME-EP005-F09-BASE-CAND-v01'
F09_KEY = f'visual/production/ep005/frames/{F09_ID}.png'
F15_ID = 'FRAME-EP005-F15-BASE-CAND-v01'
F15_HEAD_PINNED = {'x0': 836, 'x1': 1186, 'y0': 234, 'y1': 583}   # measured once on the approved F09 pixels
F15_MARGIN = 16
http = UrllibHttpClient()


def sha(b):
    return hashlib.sha256(b).hexdigest()


def rgb_sha(path):
    return sha(Image.open(path).convert('RGB').tobytes())


def cand_path(work, fam):
    return Path(work) / fam / 'norm_A' / f'FRAME-EP005-{fam}-BASE-CAND-v01_DERIVED_FRAME_CANDIDATE.png'


def candidate(fam):
    return json.loads((HERE / f'FRAME-EP005-{fam}-BASE-CAND-v01_REVIEW_CANDIDATE.json').read_text())


def bridge(work):
    out = {}
    for fam, (file_sha, px_sha, decision) in REVIEWED.items():
        p = cand_path(work, fam)
        got_file, got_px = sha256_file(p), rgb_sha(p)
        c = candidate(fam)
        ok = got_file == file_sha == c['NORMALISED_SHA_A'] and got_px == px_sha == c['CANONICAL_RGB_PIXEL_SHA']
        out[fam] = {'local_file_sha256': got_file, 'local_rgb_pixel_sha256': got_px, 'reviewed_rgb_pixel_sha256': px_sha,
                    'PIXEL_BRIDGE': 'PASS' if ok else 'FAIL',
                    'method': "SHA256(PIL Image.open(file).convert('RGB').tobytes())"}
        LEDGER.append('PIXEL_BRIDGE_PASS' if ok else 'PIXEL_BRIDGE_FAIL', f'EP005-B1-REVIEW-{fam}', family=fam, **out[fam])
        if not ok:
            print(f'STOP {fam}: pixel bridge mismatch; decision NOT bound')
            continue
        LEDGER.append(f'HUMAN_{decision}', f'EP005-B1-REVIEW-{fam}', family=fam, frame_id=c['frame_id'],
                      reviewed_normalised_sha256=file_sha, reviewed_rgb_pixel_sha256=px_sha, decided_by=DECISION_BY,
                      reasons=REASONS[fam],
                      restrictions=([] if decision == 'APPROVED' else
                                    ['NOT approved', 'NOT for G03', 'NOT for G08', 'NOT a production base frame',
                                     'no replacement generation authorised']))
        out[fam]['decision'] = decision
    print(json.dumps(out, indent=1))
    return out


def sb(method, path, headers=None, body=None):
    return http.send(method, SB + path, {'Accept': 'application/json', **(headers or {})}, body, 120.0)


def preserve_f09(work):
    if not any(r['event'] == 'HUMAN_APPROVED' for r in LEDGER.entries('EP005-B1-REVIEW-F09')):
        sys.exit('STOP: F09 approval not bound (pixel bridge)')
    c = candidate('F09')
    p = cand_path(work, 'F09')
    data = p.read_bytes()
    if sha(data) != REVIEWED['F09'][0]:
        sys.exit('STOP: F09 local bytes differ from the approved SHA')
    pre_obj = sb('GET', f'/storage/v1/object/authenticated/{BUCKET}/{F09_KEY}')
    pre_row = json.loads(sb('GET', f'/rest/v1/asset_registry?asset_id=eq.{F09_ID}&select=id').body)
    pre_name = json.loads(sb('GET', '/rest/v1/asset_registry?asset_name=eq.EP005%20F09%20Base%20Frame%20(S017)&select=id').body)
    if pre_obj.status == 200 or pre_row or pre_name:
        sys.exit(f'STOP: target exists (storage {pre_obj.status}, rows {len(pre_row)}, names {len(pre_name)})')
    LEDGER.append('PRESERVE_PRECHECK_PASS', 'EP005-B1-F09-PRESERVE', storage_key=F09_KEY, storage_get_status=pre_obj.status,
                  registry_rows=0, name_rows=0)
    up = sb('POST', f'/storage/v1/object/{BUCKET}/{F09_KEY}', {'Content-Type': 'image/png', 'x-upsert': 'false'}, data)
    upj = json.loads(up.body or b'{}')
    LEDGER.append('STORAGE_UPLOADED' if up.status == 200 else 'STORAGE_UPLOAD_FAILED', 'EP005-B1-F09-PRESERVE',
                  http_status=up.status, object_key=F09_KEY, object_id=upj.get('Id'), bytes=len(data))
    if up.status != 200:
        sys.exit(f'STOP: storage upload HTTP {up.status}')
    rb = sb('GET', f'/storage/v1/object/authenticated/{BUCKET}/{F09_KEY}')
    rb_sha = sha(rb.body) if rb.status == 200 else None
    LEDGER.append('STORAGE_READBACK_SHA256_MATCH' if rb_sha == REVIEWED['F09'][0] else 'STORAGE_READBACK_FAILED',
                  'EP005-B1-F09-PRESERVE', http_status=rb.status, readback_sha256=rb_sha, readback_bytes=len(rb.body))
    if rb_sha != REVIEWED['F09'][0]:
        sys.exit('STOP: storage readback mismatch')
    rb_path = Path(work) / 'F09' / 'stored_readback.png'
    rb_path.write_bytes(rb.body)
    pkg = json.loads((HERE / 'B1_GENERATION_PACKAGES_v1.json').read_text())
    raw = c['raw']
    row = {
        'asset_id': F09_ID, 'asset_name': 'EP005 F09 Base Frame (S017)', 'asset_type': 'SHOT_FRAME',
        'asset_subtype': 'BASE_FRAME', 'version': 'v01', 'status': 'APPROVED', 'aliases': [],
        'storage_path': f'{BUCKET}/{F09_KEY}', 'source_url': None,
        'metadata_json': {
            'canon_scope': 'MIKKO_LUMI_EP005_SHOT_SPECIFIC_PRODUCTION_ASSET', 'not_c1_canon': True,
            'canon_role': 'F09 medium two-shot base frame (shot-specific; not global character canon)',
            'episode_code': 'EP-CANDIDATE-005', 'shot_id': 'S017', 'frame_family': 'F09-MEDIUM-TWOSHOT-MIRROR-FRONT',
            'frame_family_members': ['S017'], 'derivative_source_for': ['F15-MACRO-REFLECTION (S019; S018 G07-blocked) - NOT approved'],
            'frame_id': F09_ID, 'sha256': REVIEWED['F09'][0], 'rgb24_sha256': REVIEWED['F09'][1], 'bytes': len(data),
            'width': 1920, 'height': 1080, 'dimensions': '1920x1080', 'format': 'PNG 8-bit RGB non-interlaced',
            'content_type': 'image/png', 'has_alpha': False, 'storage_object_key': F09_KEY, 'storage_object_id': upj.get('Id'),
            'provenance': {
                'provider': 'HIGGSFIELD', 'model': 'Marketing Studio Image 2.5 Flare',
                'endpoint': 'POST https://api.higgsfield.ai/marketing-studio/image/flare',
                'provider_request_id': c['provider_request_id'], 'raw_provider_sha256': raw['RAW_SHA256'],
                'raw_bytes': raw['RAW_BYTE_SIZE'], 'raw_dimensions': raw['RAW_DIMENSIONS'], 'raw_format': raw['RAW_FORMAT'],
                'raw_state': 'LOCKED_ORIGINAL_FOR_NORMALISATION (not creative approval)',
                'prompt_sha256': c['prompt_sha256'], 'request_body_sha256': c['request_body_sha256'],
                'reference_sha256s': c['reference_sha256s'], 'generation_attempts': 1, 'automatic_retries': 0,
                'package': 'evidence/ep005/batch1_base_frames/B1_GENERATION_PACKAGES_v1.json',
                'package_reference_order': [r['asset_id'] for r in pkg['references_in_order']]},
            'normalisation': {**c['normalisation'], 'two_run_determinism': {
                'runs': 2, 'run_sha256': [c['NORMALISED_SHA_A'], c['NORMALISED_SHA_B']],
                'byte_identical': c['NORMALISATION_DETERMINISM_PASS']}, 'generative_modification': False,
                'raw_unchanged': c['raw_unchanged']},
            'pixel_equivalence': {'method': "SHA256(PIL Image.open(file).convert('RGB').tobytes())",
                                  'company_brain_reviewed_rgb_sha256': REVIEWED['F09'][1], 'local_rgb_sha256': REVIEWED['F09'][1],
                                  'result': 'PASS'},
            'approved': True, 'human_decision': 'APPROVED', 'human_approval': 'APPROVED',
            'approved_sha256': REVIEWED['F09'][0], 'approve_by': f"exact sha256 {REVIEWED['F09'][0]}",
            'approval_authority': 'Company Brain / Gilang', 'approval_record': 'ENG-20261020-EP005-BATCH1-REVIEW-RECONCILED',
            'approval_notes': REASONS['F09'][0], 'g03_applied': False, 'g08_applied': False,
            'generation_record': 'evidence/ep005/batch1_base_frames/B1_GENERATION_RECORD_v1.json'},
        'notes': f"Approved EP005 F09 base frame for S017 (Higgsfield Flare request {c['provider_request_id']}, G04 normalised "
                 f"1920x1080). SHA-256 {REVIEWED['F09'][0][:8]}...{REVIEWED['F09'][0][-4:]}. Not C1/global canon. Company Brain "
                 'approval 2026-10-20. F15 derivative not approved.'}
    ins = sb('POST', '/rest/v1/asset_registry', {'Content-Type': 'application/json', 'Prefer': 'return=representation'},
             json.dumps(row).encode())
    insj = json.loads(ins.body or b'[]')
    rid = insj[0]['id'] if ins.status == 201 and insj else None
    LEDGER.append('REGISTRY_INSERTED' if rid else 'REGISTRY_INSERT_FAILED', 'EP005-B1-F09-PRESERVE', http_status=ins.status,
                  asset_registry_id=rid, asset_id=F09_ID)
    if not rid:
        sys.exit(f'STOP: registry insert HTTP {ins.status}')
    back = json.loads(sb('GET', f'/rest/v1/asset_registry?asset_id=eq.{F09_ID}&select=*').body)
    ok = (len(back) == 1 and back[0]['status'] == 'APPROVED' and back[0]['metadata_json']['sha256'] == REVIEWED['F09'][0]
          and back[0]['metadata_json']['approved'] is True)
    LEDGER.append('REGISTRY_READBACK_OK' if ok else 'REGISTRY_READBACK_MISMATCH', 'EP005-B1-F09-PRESERVE',
                  asset_registry_id=rid, created_at=back[0]['created_at'] if back else None)
    (HERE / 'F09_REGISTRY_ROW_INSERTED_v1.json').write_text(json.dumps(back, indent=1) + '\n')
    print('F09 preserved', up.status, upj.get('Id'), 'readback', rb_sha == REVIEWED['F09'][0], 'row', rid, 'readback ok', ok)


def measure_head(path):
    """Pink flower-head bbox of the hand mirror on the approved F09 (deterministic rule; result pinned)."""
    a = np.asarray(Image.open(path).convert('RGB')).astype(int)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    pink = (r > 200) & (g < 170) & (b > 110) & (b < 200) & (r - g > 60)
    X0, X1, Y0, Y1 = 800, 1230, 150, 620                       # search window around the mirror (F09 composition)
    w = pink[Y0:Y1, X0:X1]
    rows = [i for i in range(w.shape[0]) if w[i].sum() >= 20]
    top = rows[0]
    bot = top
    while bot + 1 in rows:                                      # first contiguous block = flower head (handle follows a gap)
        bot += 1
    cols = np.nonzero(w[rows[0]:rows[-1] + 1].sum(0) >= 10)[0]
    return {'x0': int(cols.min() + X0), 'x1': int(cols.max() + X0), 'y0': top + Y0, 'y1': bot + Y0}


def f15_crop(head, W=1920, H=1080, margin=F15_MARGIN):
    need_h = head['y1'] - head['y0'] + 1 + 2 * margin
    k = math.ceil(need_h / 9)
    cw, ch = 16 * k, 9 * k
    assert cw >= head['x1'] - head['x0'] + 1 + 2 * margin
    x = round((head['x0'] + head['x1']) / 2 - cw / 2)
    y = round((head['y0'] + head['y1']) / 2 - ch / 2)
    x, y = min(max(x, 0), W - cw), min(max(y, 0), H - ch)
    return {'x': x, 'y': y, 'w': cw, 'h': ch}


def derive_f15(work):
    rows = json.loads(sb('GET', f'/rest/v1/asset_registry?asset_id=eq.{F09_ID}&select=id,status,metadata_json').body)
    if len(rows) != 1 or rows[0]['status'] != 'APPROVED' or rows[0]['metadata_json']['sha256'] != REVIEWED['F09'][0]:
        sys.exit('STOP: approved F09 source not found')
    src_path = Path(work) / 'F09' / 'stored_readback.png'
    if sha256_file(src_path) != REVIEWED['F09'][0]:
        sys.exit('STOP: F09 source bytes differ')
    head = measure_head(src_path)
    if head != F15_HEAD_PINNED:
        sys.exit(f'STOP: measured head {head} != pinned {F15_HEAD_PINNED}')
    crop = f15_crop(head)
    scale = {'w': 1920, 'h': 1080}
    src = {'asset_id': F09_ID, 'registry_id': rows[0]['id'], 'classification': 'SHOT_FRAME/BASE_FRAME',
           'registry_status': 'APPROVED', 'path': str(src_path), 'expected_sha256': REVIEWED['F09'][0],
           'expected_frames': 1, 'expected_width': 1920, 'expected_height': 1080}
    provs = [derive_frame(src, 0, F15_ID, Path(work) / 'F15' / f'run_{x}', crop, scale) for x in ('A', 'B')]
    a, b = provs[0]['output'], provs[1]['output']
    passed = a['sha256'] == b['sha256'] and a['rgb24_sha256'] == b['rgb24_sha256']
    rec = {'frame_id': F15_ID, 'status': 'REVIEW (local candidate; NOT approved; no registry row; no production storage)',
           'family': 'F15-MACRO-REFLECTION', 'target_shots': ['S019', 'S018 (G07-blocked; later where governed)'],
           'F15_SOURCE_ASSET_ID': F09_ID, 'F15_SOURCE_REGISTRY_ID': rows[0]['id'], 'F15_SOURCE_SHA': REVIEWED['F09'][0],
           'F15_CROP_GEOMETRY': crop, 'crop_rule': {
               'governed_spec': "batch driver family F15: kind DERIVE_CROP, crop MEASURED_AFTER_F09_APPROVAL, scale 1920x1080",
               'measurement': 'pink flower-head bbox of the hand mirror on the approved F09 pixels (window x800-1230, '
                              'y150-620; rows with >=20 pink px, first contiguous block; cols with >=10 pink px)',
               'measured_head_bbox': head, 'margin_px': F15_MARGIN,
               'rule': 'smallest exact 16:9 crop (16k x 9k) holding the full mirror head height + margin, centred on the head'},
           'scale': scale, 'scale_flags': provs[0]['recipe']['scale_flags'], 'upscale_factor': round(1920 / crop['w'], 4),
           'F15_OUTPUT_SHA_A': a['sha256'], 'F15_OUTPUT_SHA_B': b['sha256'], 'F15_DETERMINISM_PASS': passed,
           'F15_CANONICAL_RGB_SHA': a['rgb24_sha256'], 'F15_DIMENSIONS': f"{a['width']}x{a['height']}", 'bytes': a['bytes'],
           'source_unchanged': sha256_file(src_path) == REVIEWED['F09'][0],
           'operations': 'G04 exact crop + deterministic lanczos resize only; no generative enhancement, sharpening or retouch',
           'human_approval': {'required': True, 'approved': False, 'approve_by': 'exact F15 output sha256',
                              'concern': 'macro crop quality (upscale of the F09 reflection)'}}
    LEDGER.append('F15_REVIEW_CANDIDATE' if passed else 'F15_DETERMINISM_FAILED', 'EP005-B1-F15-DERIVE', **rec)
    (HERE / f'{F15_ID}_REVIEW_CANDIDATE.json').write_text(json.dumps(rec, indent=1) + '\n')
    print(json.dumps(rec, indent=1))
    if not passed:
        sys.exit('STOP: F15 A != B')


if __name__ == '__main__':
    {'bridge': bridge, 'preserve_f09': preserve_f09, 'derive_f15': derive_f15}[sys.argv[1]](sys.argv[2])
