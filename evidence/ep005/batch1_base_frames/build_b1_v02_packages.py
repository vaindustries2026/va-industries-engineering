"""Freeze the EP005 Batch 1 F01 v02 and F03 v02 correction packages (Company Brain review 2026-10-20). Nothing is submitted.

Usage (repo root): python3 evidence/ep005/batch1_base_frames/build_b1_v02_packages.py
Source = the accepted v1 packages (commit c6a7dd2). Each v02 prompt is the v1 prompt with only the listed minimum
corrections (exact-once string replacements / insertions, recorded as deltas). Settings, model, endpoint and the six
governed references (same transport copies, same order) are unchanged. Body hash = sha256 of compact sorted-key JSON.
"""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
V1 = json.loads(subprocess.run(['git', 'show', 'c6a7dd2258846e228da0dc0b6ae8cf10058ef781:evidence/ep005/batch1_base_frames/'
                                'B1_GENERATION_PACKAGES_v1.json'], cwd=ROOT, capture_output=True, check=True).stdout)
SCALE_END = 'do not copy its layout, poses, labels or background). '
DELTAS = {
    'F01': {
        'rejected_normalised_sha256': 'c191a513a4987cc0be6ea713f8a8dc88566c952db0250b122270786e0aa11e10',
        'edits': [
            ("Composition: the hand mirror large and centred, Mikko's reflection filling most of the glass; the edge of Mikko's "
             "face/cheek and Lumi's tiny holding hand visible at the frame edge.",
             "Composition: the hand mirror large and centred, Mikko's reflection filling most of the glass, with Mikko's whole "
             "face clearly readable, front-facing and large inside the glass (eyes, both cheeks, nose and mouth unobstructed); "
             "only a small edge of Mikko's real cheek and shoulder and Lumi's tiny holding hand visible at the frame edge, not "
             "a large view of the back of Mikko's head or body.",
             'MIKKO/CAMERA: readable centred reflection, large for G03/G08 geometry; no dominant rear-of-head/body view'),
            (SCALE_END,
             SCALE_END + "Lumi keeps exactly the canonical silhouette from reference image 2: a smooth, perfectly round floating "
             "orb with no legs, no lower-body lobes and no long, elongated or noodle-like arms; only her tiny simple rounded "
             "hands, kept close to her body, reaching out just slightly to hold the mirror handle. Mikko keeps his canonical "
             "proportions from reference image 1. ",
             'LUMI: canonical orb silhouette, no legs/lobes/long limbs, tiny hands close to body (small reach for the handle); '
             'MIKKO canonical proportions'),
        ]},
    'F03': {
        'rejected_normalised_sha256': 'e8571476c5be0b1c263c4b9c3be2c155ed1af265c87aa0c18786b69b409c5968',
        'edits': [
            ("Composition: Lumi's round glowing back and tiny hands in the foreground holding the mirror slightly angled; "
             "Mikko's reflected face readable in the glass, Mikko watching attentively.",
             "Composition: Lumi's round glowing back and tiny hands in the foreground holding the mirror slightly angled and "
             "close to camera, so the hand mirror is large in frame: the clean glass is at least about 40% of the frame height "
             "with its full flower outline visible, and Mikko's reflected face (both cheeks, nose and mouth) is large and "
             "clearly readable in the glass; Mikko watching attentively.",
             'MIRROR: materially larger readable glass (>= ~40% of frame height), full outline, readable cheeks/nose/mouth '
             'for G03 + room for G08 glint; over-Lumi\'s-shoulder camera unchanged'),
            (SCALE_END,
             SCALE_END + "Lumi keeps exactly the canonical silhouette from reference image 2: a smooth, perfectly round floating "
             "orb with no legs, no lower-body lobes and no extra rounded appendages or shapes below or around her body; only "
             "her tiny simple rounded hands, holding the mirror close to her body. ",
             'LUMI: canonical smooth orb, no legs/lobes/extra rounded appendages, tiny hands only'),
        ]},
}


def sha(b):
    return hashlib.sha256(b).hexdigest()


out = {'scope': 'EP005 Batch 1 correction packages F01 v02, F03 v02 - LOCKED, NOT SUBMITTED, no spend authorised',
       'source': 'B1_GENERATION_PACKAGES_v1.json @ c6a7dd2258846e228da0dc0b6ae8cf10058ef781',
       'model': V1['model'], 'endpoint': V1['endpoint'], 'references_in_order': V1['references_in_order'],
       'reference_url_expiry': 'Wed, 28 Oct 2026 00:00:00 GMT (same transport copies as v1); after expiry a re-upload changes '
                               'image_urls, so the package must be re-locked and re-approved', 'packages': {}}
for fam, d in DELTAS.items():
    v1 = V1['packages'][fam]
    prompt = v1['prompt_exact']
    for old, new, _ in d['edits']:
        assert prompt.count(old) == 1, (fam, old[:40])
        prompt = prompt.replace(old, new)
    body = {**v1['request_body_exact'], 'prompt': prompt}
    assert {k: v for k, v in body.items() if k != 'prompt'} == {k: v for k, v in v1['request_body_exact'].items() if k != 'prompt'}
    out['packages'][f'{fam}_V02'] = {
        'FRAME_FAMILY_ID': v1['FRAME_FAMILY_ID'], 'version': 'v02', 'status': 'LOCKED_NOT_SUBMITTED',
        'supersedes': {'package': f'{fam} v1', 'v1_prompt_sha256': v1['PROMPT_SHA256'],
                       'v1_request_body_sha256': v1['REQUEST_BODY_SHA256'],
                       'rejected_normalised_sha256': d['rejected_normalised_sha256']},
        'prompt_deltas_vs_v1': [{'replaced': o, 'with': n, 'correction': c} for o, n, c in d['edits']],
        'prompt_exact': prompt, 'prompt_chars': len(prompt), 'PROMPT_SHA256': sha(prompt.encode()),
        'request_body_exact': body,
        'REQUEST_BODY_SHA256': sha(json.dumps(body, sort_keys=True, separators=(',', ':')).encode()),
        'settings_unchanged': {k: body[k] for k in ('aspect_ratio', 'resolution', 'quality', 'enhance_prompt')},
        'target_frame_id': f'FRAME-EP005-{fam}-BASE-CAND-v02', 'generations_authorised': 0, 'submitted': False}
(HERE / 'B1_V02_CORRECTION_PACKAGES_v1.json').write_text(json.dumps(out, indent=1, ensure_ascii=False) + '\n')
for k, p in out['packages'].items():
    print(k, 'PROMPT', p['PROMPT_SHA256'], 'BODY', p['REQUEST_BODY_SHA256'], p['prompt_chars'])
