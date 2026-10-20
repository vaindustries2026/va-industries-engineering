"""Freeze the EP005 Batch 1 base-frame generation packages (F01, F03, F09). Nothing is submitted or generated.

Usage (repo root): python3 evidence/ep005/batch1_base_frames/build_b1_packages.py
Prompt = the audited brief (EP005_BASE_FRAME_IMAGE_BRIEFS_v1.json, EXACT_VISUAL_BRIEF) with one reference-binding sentence
for the governed C1 duo scale sheet (reference image 6) inserted after Lumi's description. No other wording changes.
Body = the S027 Flare precedent key set; image_urls = the six fresh transport copies, in reference order, from
B1_REFERENCE_UPLOAD_LEDGER_v1.jsonl (readback SHA match required). Body hash = sha256 of compact JSON with sorted keys.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
BRIEFS = json.loads((ROOT / 'evidence/ep005/base_frame_preflight/EP005_BASE_FRAME_IMAGE_BRIEFS_v1.json').read_text())
S027 = json.loads((ROOT / 'evidence/ep005/s027_base_frame/GENERATION_PACKAGE_v2.json').read_text())
ANCHOR = 'gentle glow, not touching the floor. '
SCALE = ('Mikko and Lumi keep exactly the relative sizes shown in reference image 6 (scale reference only: do not copy its '
         'layout, poses, labels or background). ')
FAMILIES = {'F01': 'F01-MIRROR-OPEN', 'F03': 'F03-OVERSHOULDER-LUMI', 'F09': 'F09-MEDIUM-TWOSHOT-MIRROR-FRONT'}
REFS = ['CHAR-MIKKO-MASTER-v01', 'CHAR-LUMI-MASTER-v01', 'WORLD-EP005-BATHROOM-MASTER-v01', 'PROP-EP005-HAND-MIRROR-v01',
        'PROP-EP005-CLEANING-CLOTH-v01', 'DUO-MIKKO-LUMI-SCALE-v01']
ENDPOINT = 'POST https://api.higgsfield.ai/marketing-studio/image/flare'


def sha(b):
    return hashlib.sha256(b).hexdigest()


def body_sha(body):
    return sha(json.dumps(body, sort_keys=True, separators=(',', ':')).encode())


rows = [json.loads(l) for l in (HERE / 'B1_REFERENCE_UPLOAD_LEDGER_v1.jsonl').read_text().splitlines() if l.strip()]
up = {r['frame_id']: r for r in rows if r['event'] == 'UPLOADED'}
rb = {r['frame_id']: r for r in rows if r['event'] == 'READBACK_SHA256_MATCH'}
refs = []
for n, aid in enumerate(REFS, 1):
    u, r = up[aid], rb[aid]
    assert u['public_url'] == r['public_url'] and u['sha256'] == r['expected_sha256'] == r['readback']['sha256'], aid
    assert '?' not in u['public_url'] and '#' not in u['public_url'], aid
    refs.append({'n': n, 'asset_id': aid, 'sha256': u['sha256'], 'content_type': u['content_type'], 'bytes': u['bytes'],
                 'public_url': u['public_url'], 'readback_sha256': r['readback']['sha256'],
                 'upload_scope_id': u['approval_scope_id']})
assert [r['asset_id'] for r in BRIEFS['references_required']] == REFS[:5]
assert all(b['sha256'] == refs[i]['sha256'] for i, b in enumerate(BRIEFS['references_required']))

prec = S027['request_body_exact']
fixed = {k: prec[k] for k in ('aspect_ratio', 'resolution', 'quality', 'enhance_prompt')}
assert fixed == {'aspect_ratio': '16:9', 'resolution': '2k', 'quality': 'high', 'enhance_prompt': False}
packages = {}
for short, fid in FAMILIES.items():
    brief = next(b for b in BRIEFS['briefs'] if b['FRAME_FAMILY_ID'] == fid)
    src = brief['EXACT_VISUAL_BRIEF']
    assert sha(src.encode()) == brief['brief_sha256'] and src.count(ANCHOR) == 1, fid
    prompt = src.replace(ANCHOR, ANCHOR + SCALE)
    body = {'prompt': prompt, 'image_urls': [r['public_url'] for r in refs], **fixed}
    assert sorted(body) == sorted(prec), 'key set must equal the S027 precedent'
    packages[short] = {
        'FRAME_FAMILY_ID': fid, 'status': 'LOCKED_NOT_SUBMITTED', 'endpoint': ENDPOINT,
        'mode': 'DIRECT (no preset field; S027 precedent)', 'generation_count': 1,
        'source_brief_sha256': brief['brief_sha256'],
        'prompt_delta_vs_brief': {'inserted_after': ANCHOR.strip(), 'inserted_text': SCALE.strip(),
                                  'reason': 'binds governed C1 reference DUO-MIKKO-LUMI-SCALE-v01 (image 6); no other change'},
        'prompt_exact': prompt, 'prompt_chars': len(prompt), 'PROMPT_SHA256': sha(prompt.encode()),
        'request_body_exact': body, 'REQUEST_BODY_SHA256': body_sha(body),
        'request_body_sha256_note': 'sha256 of compact JSON with sorted keys (S027 convention)',
        'target_frame_id': f'FRAME-EP005-{short}-BASE-v01', 'target_status_after_generation': 'REVIEW',
        'submitted': False}
out = {'scope': 'EP005 Batch 1 base frames: F01, F03, F09 (3 future paid calls); F11 reuse and F15 crop are not generated',
       'model': 'Higgsfield Marketing Studio Image 2.5 Flare', 'endpoint': ENDPOINT,
       'precedent': {'package': 'evidence/ep005/s027_base_frame/GENERATION_PACKAGE_v2.json',
                     'request_body_sha256': S027['request_body_sha256'], 'fixed_keys': fixed},
       'references_in_order': refs,
       'reference_url_expiry': 'provider CDN x-amz-expiration expiry-date Wed, 28 Oct 2026 00:00:00 GMT (all six); HEAD-check '
                               'every image_url immediately before submit; any non-200 = STOP (re-upload changes the body '
                               'hash, so the package must be re-locked and re-approved)',
       'packages': packages}
(HERE / 'B1_GENERATION_PACKAGES_v1.json').write_text(json.dumps(out, indent=1, ensure_ascii=False) + '\n')
for k, p in packages.items():
    print(k, 'PROMPT', p['PROMPT_SHA256'], 'BODY', p['REQUEST_BODY_SHA256'], p['prompt_chars'])
