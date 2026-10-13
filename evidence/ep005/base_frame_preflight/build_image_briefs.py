"""Build the EP005 base-frame image briefs (text only; nothing is submitted, uploaded or generated).

Usage (repo root): python3 evidence/ep005/base_frame_preflight/build_image_briefs.py <out_json>
Character, prop and setting wording is copied from the APPROVED S027 Flare package (GENERATION_PACKAGE_v2.json, the only
approved EP005 image-generation request) so every family stays on-model. Each brief is hashed; a later authorised task
must freeze the final body, hash it and submit at most once.
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
pkg = json.loads((ROOT / 'evidence/ep005/s027_base_frame/GENERATION_PACKAGE_v2.json').read_text())
s027 = pkg['request_body_exact']['prompt']
MIKKO = s027[s027.index('Mikko from reference image 1'):s027.index('His face is completely clean.')].strip()
LUMI = s027[s027.index('Lumi from reference image 2'):s027.index('Warm, pleased')].strip()
SETTING = s027[s027.index('Setting:'):s027.index('Left of centre')].strip()
HEAD = ('Create one single new image (not a character sheet, not a collage, no panels, no labels): a 16:9 still frame from a '
        'child-friendly stylised 3D animated preschool episode. ')
CLEAN = ('Mikko\'s face is completely clean: no berry smudges, stains or marks anywhere on his face or fur. The pink flower-shaped '
         'hand mirror from reference image 4 is held by Lumi; its glass is perfectly clean (no smears, dirt or marks on the '
         'glass) and its full round outline is visible and unobstructed. ')
REFLECT = ('The mirror clearly shows Mikko\'s own clean reflected face, correctly mirror-reversed, sharp and readable inside '
           'the glass. ')
NEG = ('Only these two characters, one cloth and one mirror. No berry smudges or marks anywhere (they are added later), no '
       'marks on the mirror glass, no text, letters, logos, watermarks or captions, no extra characters, no extra limbs, no '
       'duplicate props, no costume or colour changes, no sparkles, glints, glows or effects on the mirror, no dramatic '
       'lighting or camera angle, no motion blur, no tilt, no lens distortion.')
CLOTH = 'the soft light-blue fleece cleaning cloth from reference image 5'

F = {
 'F01-MIRROR-OPEN': {'shots': ['S001', 'S005', 'S013', 'S024', 'S025'], 'camera': 'CLOSE, slightly front-facing view into the hand mirror, locked',
   'composition': 'the hand mirror large and centred, Mikko\'s reflection filling most of the glass; the edge of Mikko\'s face/cheek '
                  'and Lumi\'s tiny holding hand visible at the frame edge',
   'pose': f'Mikko looks calmly and attentively into the mirror, hands relaxed and out of the way; {CLOTH} is not in his hands and '
           'is not in view. Lumi holds the mirror steady by its handle with a gentle, attentive expression.', 'reflect': True},
 'F02-OVERSHOULDER-MIKKO': {'shots': ['S003'], 'camera': 'CLOSE, over Mikko\'s shoulder toward the mirror, locked',
   'composition': 'Mikko\'s shoulder and the side of his head in the foreground, the hand mirror held by Lumi beyond it, Mikko\'s '
                  'reflected face readable in the glass',
   'pose': f'Mikko looks into the mirror, calm; {CLOTH} lowered, resting within his reach. Lumi floats beside the mirror holding it '
           'steady.', 'reflect': True},
 'F03-OVERSHOULDER-LUMI': {'shots': ['S004', 'S012'], 'camera': 'CLOSE, over Lumi\'s shoulder toward the mirror and Mikko, locked',
   'composition': 'Lumi\'s round glowing back and tiny hands in the foreground holding the mirror slightly angled; Mikko\'s reflected '
                  'face readable in the glass, Mikko watching attentively',
   'pose': f'Mikko watches calmly, not pointing, {CLOTH} lowered in his hand. Lumi gently angles the mirror toward him.', 'reflect': True},
 'F04-FACE-MIRROR-3Q': {'shots': ['S006', 'S007'], 'camera': 'CLOSE, front three-quarter, locked',
   'composition': 'Mikko\'s face (his anatomical left cheek toward camera) and the hand mirror beside it, so the physical cheek and '
                  'its reflection can be compared directly',
   'pose': f'Mikko\'s free hand rests relaxed at his side; {CLOTH} is held low in his other hand. Lumi holds the mirror steady.',
   'reflect': True},
 'F05-MIRROR-CLOTH-RAISED-CHEEK': {'shots': ['S010'], 'camera': 'CLOSE, slightly front-facing toward the mirror, locked',
   'composition': 'the tiny hand mirror and Mikko\'s reflected face prominent, enough of Mikko\'s real face for context',
   'pose': f'Mikko holds {CLOTH} raised near (not touching) his anatomical left cheek, about to lower it; calm, pleased expression. '
           'Lumi holds the mirror steady.', 'reflect': True},
 'F06-MIRROR-HAND-RAISED-MOUTH': {'shots': ['S016'], 'camera': 'CLOSE, aligned with the mirror reflection, locked',
   'composition': 'the tiny hand mirror and its reflection centred, with surrounding face context',
   'pose': f'Mikko\'s hand holding {CLOTH} is raised near (not touching) the skin beside his mouth, about to lower; Lumi holds the '
           'mirror and looks at the result.', 'reflect': True},
 'F07-FACE-CLOTH-LOW': {'shots': ['S014', 'S020'], 'camera': 'CLOSE, front-facing, aligned with the mirror reflection, locked',
   'composition': 'Mikko\'s face (closed mouth and nose readable) with the hand mirror and its clean reflection beside it',
   'pose': f'Mikko holds {CLOTH} low in front of his chest, ready to bring it up slowly; Lumi visibly holds and angles the mirror.',
   'reflect': True},
 'F08-MEDIUM-TWOSHOT-REACH': {'shots': ['S002'], 'camera': 'MEDIUM, straight-on or slight three-quarter, locked',
   'composition': 'Mikko and Lumi both fully readable, Lumi holding the hand mirror, a little space between them',
   'pose': f'{CLOTH} lies neatly within Mikko\'s reach (for example on the vanity edge beside him), not in his hands; Mikko about '
           'to reach for it, Lumi holds the mirror.', 'reflect': False},
 'F09-MEDIUM-TWOSHOT-MIRROR-FRONT': {'shots': ['S017', 'S018 (macro source)', 'S019 (macro source)'],
   'camera': 'MEDIUM, front-facing, locked',
   'composition': 'Mikko and Lumi both readable with the hand mirror visible between them; the mirror large enough that Mikko\'s '
                  'reflection is readable and can later be cropped to a macro view',
   'pose': f'Mikko relaxed, {CLOTH} loosely in his lowered hand; Lumi holds the mirror up between them.', 'reflect': True},
 'F10-MEDIUM-MIKKO-FACING-MIRROR': {'shots': ['S023'], 'camera': 'MEDIUM, three-quarter toward Mikko and the mirror, locked',
   'composition': 'Mikko facing the hand mirror, his reflected face readable; Lumi\'s supporting hand and partial presence in frame',
   'pose': f'Mikko checks his reflection with a calm, pleased look; {CLOTH} lowered in his hand.', 'reflect': True},
}
out = {'source_wording': 'APPROVED S027 Flare package (GENERATION_PACKAGE_v2.json, prompt_sha256 ' + pkg['prompt_sha256'] + ')',
       'references_required': [{'n': r['n'], 'asset_id': r['asset_id'], 'sha256': r['sha256']} for r in pkg['references_in_order']],
       'briefs': []}
for fid, f in F.items():
    prompt = (HEAD + f"{f['camera']}. " + SETTING + ' ' + f"Composition: {f['composition']}. " + f'{MIKKO} ' + f'{LUMI} '
              + f"Pose: {f['pose']} " + CLEAN + (REFLECT if f['reflect'] else 'The mirror glass shows a plain pale-blue sheen. ')
              + 'Calm, simple, stable pose suitable as a held frame or the first frame of a gentle animation. ' + NEG)
    out['briefs'].append({'FRAME_FAMILY_ID': fid, 'REQUIRED_SHOTS': f['shots'], 'CAMERA': f['camera'], 'COMPOSITION': f['composition'],
                          'CHARACTERS': ['CHAR-MIKKO-MASTER-v01 (ref 1)', 'CHAR-LUMI-MASTER-v01 (ref 2)'],
                          'PROPS': ['PROP-EP005-HAND-MIRROR-v01 (ref 4)', 'PROP-EP005-CLEANING-CLOTH-v01 (ref 5)'],
                          'BACKGROUND': 'WORLD-EP005-BATHROOM-MASTER-v01 (ref 3), unchanged, softly out of focus',
                          'FACIAL_STATE': f['pose'], 'MIRROR_STATE': 'clean glass, full outline visible' + (
                              ', clean readable mirror-reversed reflection of Mikko (G03 REFLECTION marks + G08 PRESERVE)'
                              if f['reflect'] else ', plain sheen'),
                          'CLEAN_FACE_OR_SMUDGE_STATE': 'CLEAN (zero smudges; G03 adds the shot\'s smudges deterministically)',
                          'CONTINUITY_CONSTRAINTS': 'same character models, outfits, cloth, mirror and bathroom as S027-S029; locked camera; '
                                                    'output normalised by G04 (crop to 16:9, scale to 1920x1080) before approval',
                          'NEGATIVE_CONSTRAINTS': NEG, 'EXACT_VISUAL_BRIEF': prompt,
                          'brief_sha256': hashlib.sha256(prompt.encode()).hexdigest(), 'brief_chars': len(prompt)})
Path(sys.argv[1]).write_text(json.dumps(out, indent=1, ensure_ascii=False))
for b in out['briefs']:
    print(b['FRAME_FAMILY_ID'], b['brief_chars'], b['brief_sha256'][:12])
