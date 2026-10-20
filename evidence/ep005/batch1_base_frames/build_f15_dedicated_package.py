"""Freeze the dedicated F15 (macro mirror reflection) image package. Nothing is submitted here.

Usage (repo root): python3 evidence/ep005/batch1_base_frames/build_f15_dedicated_package.py
Context: the F15 crop of the approved F09 (FRAME-EP005-F15-BASE-CAND-v01, c5c54675...) was rejected; Company Brain
directs a purpose-made F15 composition instead (2026-10-20). Character, setting and canon wording is copied verbatim
from the approved S027 Flare package and the locked F03 v02 Lumi silhouette sentence; only the camera/composition and
the F15-specific negatives are new. Shots: S019 (macro static hold) and later S018 where governed; continuity with the
approved F09 (S017) reflection. Settings and the six governed references are identical to the locked v1/v02 packages.
"""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
s027 = json.loads((ROOT / 'evidence/ep005/s027_base_frame/GENERATION_PACKAGE_v2.json').read_text())['request_body_exact']['prompt']
V02 = json.loads(subprocess.run(['git', 'show', '3775b46d81bc6ba4c4251b0e669671ecbc25c881:evidence/ep005/batch1_base_frames/'
                                 'B1_V02_CORRECTION_PACKAGES_v1.json'], cwd=ROOT, capture_output=True, check=True).stdout)
MIKKO = s027[s027.index('Mikko from reference image 1'):s027.index('His face is completely clean.')].strip()
LUMI = s027[s027.index('Lumi from reference image 2'):s027.index('Warm, pleased')].strip()
SETTING = s027[s027.index('Setting:'):s027.index('Left of centre')].strip()
f03 = V02['packages']['F03_V02']['prompt_exact']
SCALE = f03[f03.index('Mikko and Lumi keep exactly the relative sizes'):f03.index('Lumi keeps exactly the canonical silhouette')].strip()
HEAD = ('Create one single new image (not a character sheet, not a collage, no panels, no labels): a 16:9 still frame from a '
        'child-friendly stylised 3D animated preschool episode. ')
CAMERA = ('MACRO close-up, straight-on and front-facing into the hand mirror, locked, eye level, no tilt, no lens distortion, '
          'no motion blur. ')
COMPOSITION = ("Composition: a deliberate, cinematic macro of the pink flower-shaped hand mirror from reference image 4, centred "
               "and large, its complete flower-shaped outline fully inside the frame with a calm, even margin on every side; "
               "the clean round glass fills about two thirds of the frame height. Inside the glass, Mikko's reflection: his "
               "clean, front-facing face, large, sharp and attractive (eyes, both cheeks, nose and mouth unobstructed and "
               "clearly readable), a gentle happy expression, his yellow neckerchief just visible at the bottom of the glass, "
               "the same reflected view as in a front-facing medium two-shot of Mikko and Lumi. The only other character "
               "element in frame is Lumi's tiny simple rounded golden-white glowing hand holding the mirror handle at the "
               "lower edge. Mikko's real head, face and body are out of frame (behind the camera), and Lumi's orb body, face "
               "and eyes are out of frame: nothing enters from the left or right edges. ")
BG = ("Behind the mirror, the bathroom from reference image 3 (main view), unchanged and softly out of focus: warm cream walls "
      "and tiles, light wood vanity with grey-blue doors, soft warm even lighting, low clutter, neutral desaturated tones. "
      "Do not redesign it. ")
REFS = (f'{MIKKO} {LUMI} {SCALE} Lumi keeps exactly the canonical silhouette from reference image 2; only her tiny simple '
        'rounded hand is visible here. ')
CLEAN = ("Mikko's reflected face is completely clean: no berry smudges, stains or marks anywhere on his face or fur. The "
         "mirror glass is perfectly clean (no smears, dirt or marks on the glass). The mirror clearly shows Mikko's own clean "
         "reflected face, correctly mirror-reversed, sharp and readable inside the glass. The soft light-blue fleece cleaning "
         "cloth from reference image 5 is not in view. ")
NEG = ('Calm, simple, stable composition suitable as a held frame. No real Mikko or Lumi face, head or body at the frame edges, '
       'no partial faces, eyes or bodies cut by the frame, no berry smudges or marks anywhere (they are added later), no marks '
       'on the mirror glass, no text, letters, logos, watermarks or captions, no extra characters, no extra limbs, no '
       'duplicate props, no costume or colour changes, no sparkles, glints, glows or effects on the mirror, no dramatic '
       'lighting or camera angle, no motion blur, no tilt, no lens distortion.')
prompt = HEAD + CAMERA + COMPOSITION + BG + REFS + CLEAN + NEG
v1 = V02['packages']['F03_V02']['request_body_exact']
body = {**v1, 'prompt': prompt}
assert body['image_urls'] == [r['public_url'] for r in V02['references_in_order']]
out = {'FRAME_FAMILY_ID': 'F15-MACRO-REFLECTION', 'version': 'v02 (dedicated generation; replaces the rejected F09 crop)',
       'status': 'LOCKED_NOT_SUBMITTED', 'kind_change': 'DERIVE_CROP (from F09) -> GENERATE (dedicated), Company Brain 2026-10-20',
       'shots': ['S019', 'S018 (G07-blocked; later where governed)'],
       'continuity': 'reflection matches the approved F09 (S017) front-facing reflected view; S019 = macro static hold',
       'downstream': 'G03 NOSE overlay on the reflection (S019), measured on the approved normalised frame',
       'model': V02['model'], 'endpoint': V02['endpoint'], 'references_in_order': V02['references_in_order'],
       'reference_url_expiry': V02['reference_url_expiry'],
       'wording_sources': {'verbatim_from_S027_package': ['MIKKO', 'LUMI', 'SETTING palette'],
                           'verbatim_from_F03_v02': ['duo scale sentence (reference image 6)'],
                           'new_for_F15': ['CAMERA', 'COMPOSITION', 'background framing', 'F15 negatives']},
       'prompt_exact': prompt, 'prompt_chars': len(prompt), 'PROMPT_SHA256': hashlib.sha256(prompt.encode()).hexdigest(),
       'request_body_exact': body,
       'REQUEST_BODY_SHA256': hashlib.sha256(json.dumps(body, sort_keys=True, separators=(',', ':')).encode()).hexdigest(),
       'settings': {k: body[k] for k in ('aspect_ratio', 'resolution', 'quality', 'enhance_prompt')},
       'target_frame_id': 'FRAME-EP005-F15-BASE-CAND-v02', 'generation_count': 1, 'submitted': False}
(HERE / 'B1_F15_DEDICATED_PACKAGE_v1.json').write_text(json.dumps(out, indent=1, ensure_ascii=False) + '\n')
print('F15_V02 PROMPT', out['PROMPT_SHA256'], 'BODY', out['REQUEST_BODY_SHA256'], out['prompt_chars'])
print(prompt)
