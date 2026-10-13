"""READ-ONLY EP005 base-frame batch preflight (no generation, no provider call, no production write).

Usage (repo root): python3 evidence/ep005/base_frame_preflight/base_frame_preflight.py <out_json>
Joins: live Agent-008 specs of APPROVED readiness 69bff641 (GET snapshot), the APPROVED manifest 0325d35c shot plans
(camera/framing/animation), the live registry (GET: approved frames, motions, C1/world/prop references), the G03 and G08
audits and the G08 factory matrix. The family grouping below is the evidence-backed judgement recorded in
EP005_BASE_FRAME_BATCH_PREFLIGHT_v1.0.md; this script attaches the live data to it and derives every count.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from agent008.config import load_output_spec  # noqa: E402
from agent008.episode import PINS, resolve_episode  # noqa: E402
from agent008.inputs import load_hash_pins  # noqa: E402
from agent008.motion.http import UrllibHttpClient  # noqa: E402
from agent008.tools.snapshot_inputs import build_snapshot  # noqa: E402

SB = 'https://ziluiwrwwbayhcskeere.supabase.co'
MANIFEST, READINESS = '0325d35c-d567-4488-bf78-c3887e819382', '69bff641-e056-4701-a23f-d91dbc2039b2'
REFL, GLINT, POP = ('TREATMENT-EP005-MIRROR-REFLECTION-v01', 'TREATMENT-EP005-MIRROR-GLINT-v01',
                    'TREATMENT-EP005-COMPLETION-POP-ACCENT-v01')
http = UrllibHttpClient()


def get(path):
    r = http.send('GET', f'{SB}/rest/v1/{path}', {'Accept': 'application/json'})
    if r.status != 200:
        sys.exit(f'STOP: GET {path} HTTP {r.status}')
    return json.loads(r.body)


# Families: GEN = new image generation required; DER = derivable / reusable. 'members' = shots whose base frame it is.
FAMILIES = [
    {'id': 'F01-MIRROR-OPEN', 'kind': 'GEN', 'primary': 'S001', 'members': ['S001', 'S005', 'S013', 'S024', 'S025'],
     'reflection_visible': True,
     'state': 'CLOSE, front-facing into Lumi\'s hand mirror; reflection of Mikko\'s face large and centred; enough of Mikko\'s face '
              'and Lumi\'s holding hand; Mikko\'s hands at rest, cloth not in hand (resting out of frame / below frame); clean face, '
              'clean glass, clean reflection (G03 adds smudges, G08 measures the glass)',
     'variance': 'S025 calls for Lumi\'s soft smile and Mikko\'s settled gaze (held pose approved for S025): accept the neutral-'
                 'attentive F01 expression for S025, else S025 needs its own generation. S024 is G06-blocked (shares the frame).'},
    {'id': 'F02-OVERSHOULDER-MIKKO', 'kind': 'GEN', 'primary': 'S003', 'members': ['S003'], 'reflection_visible': True,
     'state': 'CLOSE over MIKKO\'s shoulder toward the mirror; Mikko\'s face side-on plus his readable reflection; Lumi holds the '
              'mirror; cloth lowered within reach', 'variance': None},
    {'id': 'F03-OVERSHOULDER-LUMI', 'kind': 'GEN', 'primary': 'S004', 'members': ['S004', 'S012'], 'reflection_visible': True,
     'state': 'CLOSE over LUMI\'s shoulder toward the mirror; Lumi\'s tiny hands holding the mirror angled; Mikko\'s reflection '
              'readable; Mikko attentive, cloth lowered, not pointing', 'variance': 'S004 (3 marks) and S012 (2 marks) differ only '
              'in G03 overlays; the mirror tilt/angle animation is represented by the held pose + glint (Batch 0C approval).'},
    {'id': 'F04-FACE-MIRROR-3Q', 'kind': 'GEN', 'primary': 'S006', 'members': ['S006', 'S007'], 'reflection_visible': True,
     'state': 'CLOSE front three-quarter: Mikko\'s physical anatomical-left cheek and its reflection both readable; Lumi holds '
              'the mirror; Mikko\'s free hand at rest, cloth held low in the other hand', 'variance': 'motion start frame for both '
              'S006 (pointing) and S007 (cloth lift); S007 is "cheek-focused" but explicitly "consistent with the preceding face-'
              'and-mirror view".'},
    {'id': 'F05-MIRROR-CLOTH-RAISED-CHEEK', 'kind': 'GEN', 'primary': 'S010', 'members': ['S010'], 'reflection_visible': True,
     'state': 'CLOSE mirror-centric: tiny hand mirror and Mikko\'s reflected face; Mikko\'s cloth hand raised near the (clear) '
              'cheek, about to lower', 'variance': 'continuity source S009 end is G11-blocked; an independent start frame unblocks S010.'},
    {'id': 'F06-MIRROR-HAND-RAISED-MOUTH', 'kind': 'GEN', 'primary': 'S016', 'members': ['S016'], 'reflection_visible': True,
     'state': 'CLOSE mirror-centric with face context; Mikko\'s hand (cloth) raised near the (clear) mouth area, about to lower',
     'variance': 'continuity source S015 end is G11-blocked; an independent start frame unblocks S016.'},
    {'id': 'F07-FACE-CLOTH-LOW', 'kind': 'GEN', 'primary': 'S014', 'members': ['S014', 'S020'], 'reflection_visible': True,
     'state': 'CLOSE front-facing face-and-mirror; Mikko\'s face (closed mouth, nose) and the clean reflection readable; cloth '
              'held low in Mikko\'s hand, ready to approach; Lumi visibly holding/angling the mirror', 'variance': 'motion start '
              'frame for S014 (toward mouth) and S020 (toward nose).'},
    {'id': 'F08-MEDIUM-TWOSHOT-REACH', 'kind': 'GEN', 'primary': 'S002', 'members': ['S002'], 'reflection_visible': False,
     'state': 'MEDIUM two-shot, straight-on/slight 3/4; Lumi holds the mirror; the cloth rests within Mikko\'s reach (NOT in hand)',
     'variance': 'the old plan derived S002 from the shared two-shot frame; live specs give a different cloth state (pick-up '
                 'start), so it is not derivable.'},
    {'id': 'F09-MEDIUM-TWOSHOT-MIRROR-FRONT', 'kind': 'GEN', 'primary': 'S017', 'members': ['S017'], 'reflection_visible': True,
     'state': 'MEDIUM two-shot front-facing, mirror visible between the characters, Mikko\'s reflection readable; Mikko\'s relaxed '
              'cloth hand', 'variance': 'source of the S018/S019 macro crop (F15).'},
    {'id': 'F10-MEDIUM-MIKKO-FACING-MIRROR', 'kind': 'GEN', 'primary': 'S023', 'members': ['S023'], 'reflection_visible': True,
     'state': 'MEDIUM three-quarter toward Mikko facing the hand mirror; Lumi\'s supporting hand / partial presence; lowered cloth; '
              'clean face and reflection', 'variance': 'Batch 0C recorded S023 = S022 end state, but S022 is CLOSE and S023 MEDIUM: '
                                                      'an S023 frame of its own removes the S021/G11 upstream dependency (human decision).'},
    {'id': 'F11-S027-START-REUSE', 'kind': 'DER', 'primary': 'S026', 'members': ['S026'], 'reflection_visible': False,
     'source_asset_id': 'FRAME-EP005-S027-BASE-v01',
     'method': 'REUSE the exact approved bytes as the S026 motion base frame (no pixel change; provider input as-is, like S027)',
     'expected_output': 'S026 base = knees-up two-shot, clean face, cloth folded at chest height, Lumi holding the mirror upright',
     'continuity': 'S026 precedes S027 and the frame is S027\'s approved opening state: identical characters, props, clean face, '
                   'setting and framing. S026\'s lift motion moves away from it, so the S026->S027 cut returns to this pose '
                   '(human acceptance). S026 has no overlays or treatments.',
     'state': 'see source', 'variance': 'MEDIUM (spec) vs knees-up two-shot: same class as S027; human acceptance.'},
    {'id': 'F12-S007-END', 'kind': 'DER', 'primary': 'S008', 'members': ['S008', 'S009'], 'reflection_visible': True,
     'source_asset_id': 'future approved S007 raw motion', 'source_frame_index': 'last frame used by the approved S007 shot',
     'method': 'G04 derive_frame (exact index; crop/scale only if needed)', 'expected_output': 'S007 end: cloth resting still '
     'on the marked cheek, three smudges as composited into the S007 base frame', 'continuity': 'manifest: S008 "Same face-to-'
     'mirror angle as S007"; protected hold of S007 end (visible_at_start(N)=visible_at_end(N-1))',
     'state': 'see source', 'variance': 'needs S007 motion first; the smudges are baked into the motion, so the G03 overlay set '
                                        'must be inherited through G04 (engineering gap G04_OVERLAY_CHAIN). S009 is G11-blocked.'},
    {'id': 'F13-S010-END', 'kind': 'DER', 'primary': 'S011', 'members': ['S011'], 'reflection_visible': True,
     'source_asset_id': 'future approved S010 raw motion', 'source_frame_index': 'last frame used by the approved S010 shot',
     'method': 'G04 derive_frame', 'expected_output': 'S010 end: cloth lowered, clear cheek, mouth + nose smudges, readable reflection',
     'continuity': 'plan: "base = last frame of approved S010 raw motion"', 'state': 'see source',
     'variance': 'live S011 framing is a "relaxed two-shot" while S010 is mirror-centric: human must accept the S010 end framing '
                 'for S011, else S011 needs its own generation. Also needs G04_OVERLAY_CHAIN (overlays + reflection certificate).'},
    {'id': 'F14-S014-END', 'kind': 'DER', 'primary': 'S015', 'members': ['S015'], 'reflection_visible': True,
     'source_asset_id': 'future approved S014 raw motion', 'method': 'G04 derive_frame', 'expected_output': 'S014 end',
     'continuity': 'S015 continues S014', 'state': 'see source', 'variance': 'S015 is G11-blocked: do not prioritise.'},
    {'id': 'F15-MACRO-REFLECTION', 'kind': 'DER', 'primary': 'S019', 'members': ['S018', 'S019'], 'reflection_visible': True,
     'source_asset_id': 'future approved F09 frame (S017)', 'method': 'deterministic crop (+ lanczos scale) of the mirror '
     'reflection region (G04 crop/scale on the still)', 'expected_output': 'tighter macro of the clean-glass reflection',
     'continuity': 'manifest S018: image_generation_required=false, "cut to a tighter macro reframe of the approved reflection '
                   'artwork", production notes "Prepare the approved S017 artwork"; S019 holds the S018 macro view',
     'state': 'see source', 'variance': 'quality risk: a macro crop of a MEDIUM frame upscales the reflection (human check). '
                                        'S018 is G07-blocked; S019 (static macro hold) can use F15 without G07.'},
    {'id': 'F16-S020-S021-END', 'kind': 'DER', 'primary': 'S022', 'members': ['S021', 'S022'], 'reflection_visible': True,
     'source_asset_id': 'future approved S020 raw motion (S021) / S021 raw motion (S022)', 'method': 'G04 derive_frame',
     'expected_output': 'cloth at the nose, then lowered from the clear nose', 'continuity': 'S021 continues S020; S022 continues S021',
     'state': 'see source', 'variance': 'S021 is G11-blocked, so S022 waits on G11 unless a human accepts F07 (cloth low, '
                                        'clean face) as S022\'s start.'},
]

mrow = get(f'episode_production_manifests?id=eq.{MANIFEST}&select=status,manifest_json')
if len(mrow) != 1 or mrow[0]['status'] != 'APPROVED':
    sys.exit('STOP: manifest not APPROVED')
plans = {s['shot_id']: s['shot_plan'] for s in mrow[0]['manifest_json']['shot_plans']}
spec = load_output_spec()
resolved = {r['shot_id']: r for r in resolve_episode(build_snapshot(READINESS), load_hash_pins(PINS), spec)}
matrix = {r['SHOT_ID']: r for r in json.loads((ROOT / 'evidence/agent008/g08/G08_LIVE_SPEC_VALIDATION_AND_MATRIX_v1.json').read_text())['matrix']}
REFS = ['FRAME-EP005-S027-BASE-v01', 'CHAR-MIKKO-MASTER-v01', 'CHAR-LUMI-MASTER-v01', 'WORLD-EP005-BATHROOM-MASTER-v01',
        'PROP-EP005-HAND-MIRROR-v01', 'PROP-EP005-CLEANING-CLOTH-v01']
refs = {r['asset_id']: {'id': r['id'], 'status': r['status'], 'type': f"{r['asset_type']}/{r['asset_subtype']}",
                        'sha256': (r['metadata_json'] or {}).get('sha256'), 'dimensions': (r['metadata_json'] or {}).get('dimensions'),
                        'storage_path': r['storage_path']}
        for r in get('asset_registry?asset_id=in.(' + ','.join(REFS) + ')&select=id,asset_id,status,asset_type,asset_subtype,storage_path,metadata_json')}
covered = [s for f in FAMILIES for s in f['members']]
assert sorted(covered) == [f'S{i:03d}' for i in range(1, 27)] and len(covered) == len(set(covered)), 'family coverage'

fam_of = {s: f['id'] for f in FAMILIES for s in f['members']}
shots = {}
for sid in sorted(fam_of):
    sp, p, m = resolved[sid].get('spec') or {}, plans[sid], matrix[sid]
    shots[sid] = {'family': fam_of[sid], 'code_ready': m['CAN_PRODUCE_AFTER_INPUTS_EXIST'], 'code_blockers': m['OTHER_CODE_BLOCKERS'],
                  'provider_motion': m['PROVIDER_MOTION_REQUIRED'], 'framing_scale': p['camera_setup'].get('framing_scale'),
                  'angle': p['camera_setup'].get('angle'), 'framing': p['camera_setup'].get('framing'),
                  'image_generation_required_manifest': p['animation_plan']['image_generation_required'],
                  'video_generation_required_manifest': p['animation_plan']['video_generation_required'],
                  'overlays': [o['asset_id'] for o in sp.get('active_overlays') or []],
                  'treatments': [t['treatment_id'] for t in sp.get('treatments') or []],
                  'dialogue': [{'speaker': d['speaker'], 'text': d['text']} for d in sp.get('dialogue_slots') or []]}

# G03 / G08 future record maps
g03, g08 = [], []
for sid, s in shots.items():
    f = next(x for x in FAMILIES if x['id'] == s['family'])
    for o in s['overlays']:
        g03.append({'SHOT_ID': sid, 'FRAME_FAMILY_ID': f['id'], 'OVERLAY_ASSET': o,
                    'PLACEMENT_RECORD_REQUIRED': f['kind'] == 'GEN' or f['id'] == 'F15-MACRO-REFLECTION',
                    'MIRROR_COPY_REQUIRED': f['reflection_visible'] and REFL not in s['treatments'] or None,
                    'HUMAN_MEASUREMENT_REQUIRED': f['kind'] == 'GEN' or f['id'] == 'F15-MACRO-REFLECTION',
                    'note': ('inherited from the source motion via G04 (needs G04_OVERLAY_CHAIN), no new record'
                             if f['kind'] == 'DER' and f['id'] != 'F15-MACRO-REFLECTION' else
                             'REFLECTION placement only if the reflection is PRESERVEd; COMPOSITE copies the FACE marks'
                             if REFL in s['treatments'] else None),
                    'code_ready': s['code_ready']})
    for t in s['treatments']:
        g08.append({'SHOT_ID': sid, 'FRAME_FAMILY_ID': f['id'], 'TREATMENT_TYPE': t.split('EP005-')[1][:-4],
                    'MIRROR_REGION_RECORD_REQUIRED': True, 'GLINT_RECORD_REQUIRED': t == GLINT, 'POP_RECORD_REQUIRED': t == POP,
                    'REFLECTION_RECORD_REQUIRED': t == REFL, 'HUMAN_MEASUREMENT_REQUIRED': True,
                    'audio_sync': {'S004': 'SFX-LUMI-CLUE-CHIME', 'S025': 'SFX-COMPLETION-POP-v01'}.get(sid),
                    'code_ready': s['code_ready']})
dialogue = []
for f in FAMILIES:
    lines = [(sid, d) for sid in f['members'] for d in shots[sid]['dialogue']]
    dialogue.append({'FRAME_FAMILY_ID': f['id'], 'SHOTS': f['members'],
                     'MIKKO_LINES_REQUIRED': [f"{sid}: {d['text']}" for sid, d in lines if d['speaker'] == 'Mikko'],
                     'LUMI_LINES_REQUIRED': [f"{sid}: {d['text']}" for sid, d in lines if d['speaker'] == 'Lumi'],
                     'TOTAL_TTS_LINES': len(lines)})

gen = [f for f in FAMILIES if f['kind'] == 'GEN']
der = [f for f in FAMILIES if f['kind'] == 'DER']
for f in FAMILIES:
    f['code_ready_members'] = [s for s in f['members'] if shots[s]['code_ready']]
    f['blocked_only_members'] = [s for s in f['members'] if not shots[s]['code_ready']]
first = ['F01-MIRROR-OPEN', 'F03-OVERSHOULDER-LUMI', 'F09-MEDIUM-TWOSHOT-MIRROR-FRONT', 'F11-S027-START-REUSE', 'F15-MACRO-REFLECTION']
first_shots = sorted({s for f in FAMILIES if f['id'] in first for s in f['code_ready_members']})
out = {
    'manifest': MANIFEST, 'readiness': READINESS,
    'TOTAL_FRAME_FAMILIES': len(FAMILIES), 'FAMILIES_REQUIRING_NEW_IMAGE_GENERATION': [f['id'] for f in gen],
    'FAMILIES_DERIVABLE_FROM_APPROVED_ASSETS': [f['id'] for f in der],
    'derivable_now_from_existing_approved_assets': [f['id'] for f in der if f.get('source_asset_id') in refs],
    'derivable_only_after_future_approvals': [f['id'] for f in der if f.get('source_asset_id') not in refs],
    'reference_assets_live': refs, 'families': FAMILIES, 'shots': shots,
    'G03_FUTURE_RECORDS': g03, 'G08_FUTURE_RECORDS': g08, 'DIALOGUE_DEPENDENCY': dialogue,
    'families_only_for_blocked_shots': [f['id'] for f in FAMILIES if not f['code_ready_members']],
    'RECOMMENDED_FIRST_FRAME_BATCH': {
        'families': first, 'image_calls_required': sum(1 for f in FAMILIES if f['id'] in first and f['kind'] == 'GEN'),
        'shots_unlocked': first_shots,
        'stills_no_video': [s for s in first_shots if not shots[s]['provider_motion']],
        'motion_shots_needing_separate_seedance_authorisation': [s for s in first_shots if shots[s]['provider_motion']],
        'tts_lines': [f"{s}: {d['speaker']}: {d['text']}" for s in first_shots for d in shots[s]['dialogue']],
        'g03_records': sorted({r['SHOT_ID'] for r in g03 if r['SHOT_ID'] in first_shots and r['PLACEMENT_RECORD_REQUIRED']}),
        'g08_records': sorted({r['SHOT_ID'] for r in g08 if r['SHOT_ID'] in first_shots})},
}
Path(sys.argv[1]).write_text(json.dumps(out, indent=1, ensure_ascii=False))
print('families', len(FAMILIES), 'gen', len(gen), 'der', len(der))
for f in FAMILIES:
    print(f['id'], f['kind'], f['members'], 'ready', f['code_ready_members'], 'blocked', f['blocked_only_members'])
print('refs', {k: (v['status'], v['sha256'][:12] if v['sha256'] else None, v['dimensions']) for k, v in refs.items()})
print('only-blocked families', out['families_only_for_blocked_shots'])
print(json.dumps(out['RECOMMENDED_FIRST_FRAME_BATCH'], indent=1, ensure_ascii=False))
for d in dialogue:
    print(d['FRAME_FAMILY_ID'], len(d['MIKKO_LINES_REQUIRED']), len(d['LUMI_LINES_REQUIRED']), d['TOTAL_TTS_LINES'])
print('g03', len(g03), 'g08', len(g08))
