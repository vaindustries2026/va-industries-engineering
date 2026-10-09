"""EP005 Agent-008 scale-out production matrix (zero spend, read-only, offline).

Usage (repo root): python3 -I evidence/agent008/scaleout/build_ep005_production_matrix.py <manifest.json> <registry.json>
Inputs are GET snapshots of the APPROVED production manifest 45cc7493 and the live asset_registry
(hashes in AUTHORITATIVE_INPUT_FETCH_SHA256_v1.txt). Shot facts are read from the manifest; the
classification decisions below are the audit's engineering judgement and carry their reasons.
Counts in the summary are computed, never typed.
"""
import json
import re
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parent
manifest = json.loads(Path(sys.argv[1]).read_text())[0]
registry = {r['asset_id']: r for r in json.loads(Path(sys.argv[2]).read_text())}
mj = manifest['manifest_json']
assert manifest['id'] == '45cc7493-80b4-4e8d-b71d-fbd7fd3656ed' and manifest['status'] == 'APPROVED'
FPS = 24

# ---- governed audio (registry SHA, else committed hash pin) --------------------------------------
PINS = json.loads((OUT.parents[2] / 'agent008/inputs/hash_pins.json').read_text())['pins']
def governed(aid):
    r = registry.get(aid)
    if not r or r['status'] not in ('APPROVED', 'LOCKED'):
        return {'asset_id': aid, 'status': 'NOT_GOVERNED'}
    sha = (r.get('metadata_json') or {}).get('sha256') or PINS.get(aid, {}).get('sha256')
    return {'asset_id': aid, 'registry_id': r['id'], 'subtype': r['asset_subtype'], 'sha256': sha,
            'sha256_source': 'registry' if (r.get('metadata_json') or {}).get('sha256') else ('hash_pin' if sha else 'MISSING')}

NAMED_TO_ID = {'Lumi clue chime': 'SFX-LUMI-CLUE-CHIME', 'Mikko TRY whoosh': 'SFX-MIKKO-TRY-WHOOSH',
               'WIN sparkle chord': 'SFX-WIN-SPARKLE-CHORD'}
OVERLAY_ID = {'cheek': 'OVERLAY-EP005-BERRY-SMUDGE-CHEEK-v01', 'mouth': 'OVERLAY-EP005-BERRY-SMUDGE-MOUTH-v01',
              'nose': 'OVERLAY-EP005-BERRY-SMUDGE-NOSE-v01'}
treat = {}
for t in mj['compositing_treatments']:
    for s in t['affected_shots']:
        treat.setdefault(s, []).append(t['treatment_id'])
audio_map = {}
for a in mj['audio_asset_mappings']:
    for s in a['shots']:
        audio_map.setdefault(s, []).append(a['asset_id'])

# ---- base-frame families (visual setups) ----------------------------------------------------------
FAMILIES = {
    'F-MIRROR-OPEN': 'close mirror composition: Lumi holds the hand mirror, Mikko and his reflection readable (S001 opening = S025 match)',
    'F-OVERSHOULDER-MIRROR': 'over-shoulder close: Lumi positions the mirror for Mikko, cloth lowered (S003-S005)',
    'F-FACE-MIRROR': 'close face-and-mirror view, cloth lowered, reflection readable (S010-S013, S016)',
    'F-FACE-MIRROR-POINT': 'pose variant of F-FACE-MIRROR: Mikko points to his anatomical left cheek with his free hand (S006)',
    'F-CHEEK-CLOTH': 'close view of Mikko cheek with soft cloth, Lumi holding mirror (S007-S009)',
    'F-MOUTH-CLOTH': 'close face with cloth approaching the skin beside the mouth (S014-S015)',
    'F-NOSE-CLOTH': 'close face with cloth near the nose (S020-S022)',
    'F-MACRO-REFLECTION': 'distinctly tighter macro of the clean-glass reflection (S018-S019)',
    'F-MEDIUM-TWOSHOT': 'medium two-shot, Lumi holds mirror, Mikko with cloth (S002, S017, S023, S026)',
}

# ---- per-shot classification (A/B/C/D) and production decisions ------------------------------------
# method: A STATIC_OR_DETERMINISTIC_ONLY, B HIGGSFIELD_MOTION_REQUIRED, C HYBRID, D BLOCKED
C = {
 'S001': ('C', 'F-MIRROR-OPEN', 'NEEDS_NEW_SHOT_FRAME', 'HIGH',
          'Manifest video shot: Mikko head tilt with face, reflection and all three smudges moving together. Provider motion plus deterministic smudges (pre-composited into the base frame on face and reflection).',
          'Gentle Mikko head tilt; Lumi holds mirror steady; reflection follows; locked camera.'),
 'S002': ('C', 'F-MEDIUM-TWOSHOT', 'CAN_DERIVE_DETERMINISTICALLY', 'MEDIUM',
          'Manifest video shot: cloth pick-up and fold (prop interaction). Three smudges present -> pre-composited into the F-MEDIUM-TWOSHOT clean base.',
          'Mikko reaches, picks up the cloth and loosely folds it; Lumi holds mirror; no face contact; static camera. 3.5 s: generate 4 s, deterministic trim to 84 frames.'),
 'S003': ('A', 'F-OVERSHOULDER-MIRROR', 'NEEDS_NEW_SHOT_FRAME', 'MEDIUM',
          'Manifest compositor-only (video_generation_required=false): nearly static over-shoulder hold; smudges as static overlays; Lumi line. Minor mirror positioning represented by the held pose.', None),
 'S004': ('A', 'F-OVERSHOULDER-MIRROR', 'CAN_DERIVE_DETERMINISTICALLY', 'HIGH',
          'Manifest compositor-only: static frame + TREATMENT-EP005-MIRROR-GLINT-v01 + clue chime. Mirror tilt represented by the glint (human acceptance needed). Two Lumi lines: known S004 TIMING_CONFLICT and unapplied D-3 wording decision.', None),
 'S005': ('A', 'F-OVERSHOULDER-MIRROR', 'CAN_DERIVE_DETERMINISTICALLY', 'LOW',
          'Protected 4.0 s participation hold: static frame identical to S004 end state; no events.', None),
 'S006': ('A', 'F-FACE-MIRROR-POINT', 'NEEDS_NEW_SHOT_FRAME', 'MEDIUM',
          'Manifest compositor-only: held pointing pose + reflection treatment + Mikko line; pointing gesture represented by a held pose (human acceptance needed).', None),
 'S007': ('C', 'F-CHEEK-CLOTH', 'NEEDS_NEW_SHOT_FRAME', 'HIGH',
          'Manifest video shot: cloth lift into stationary contact with the marked cheek; smudges + reflection pre-composited into base frame; two Mikko lines; TRY whoosh.',
          'Mikko lifts the cloth and rests it still against the cheek smudge (no wiping); Lumi holds mirror; locked camera.'),
 'S008': ('A', 'F-CHEEK-CLOTH', 'CAN_DERIVE_DETERMINISTICALLY', 'LOW',
          'Protected 3.0 s hold: last frame of the approved S007 raw motion held (continuity rule visible_at_start(N)=visible_at_end(N-1)).', None),
 'S009': ('D', 'F-CHEEK-CLOTH', 'BLOCKED', 'HIGH',
          'Cheek smudge must disappear only under the cloth pass: needs mask removal tracked to provider-generated cloth motion. No governed capability (Agent-008 fails closed on motion overlays; provider prompting cannot be bound to an exact overlay removal).',
          'One short gentle wipe across the cheek, lift away; cheek smudge removed under the cloth only.'),
 'S010': ('C', 'F-FACE-MIRROR', 'NEEDS_NEW_SHOT_FRAME', 'MEDIUM',
          'Manifest video shot: Mikko lowers cloth; mouth+nose smudges and clean reflection pre-composited; Lumi line.',
          'Mikko lowers the cloth; Lumi holds mirror steady; locked camera; no smudge change.'),
 'S011': ('C', 'F-FACE-MIRROR', 'CAN_DERIVE_DETERMINISTICALLY', 'MEDIUM',
          'Manifest video shot: small pleased smile and cloth settle; base = last frame of approved S010 raw motion.',
          'Small pleased smile, checks clear cheek, rests cloth below chin; Lumi steady; locked camera.'),
 'S012': ('A', 'F-FACE-MIRROR', 'CAN_DERIVE_DETERMINISTICALLY', 'MEDIUM',
          'Manifest compositor-only: F-FACE-MIRROR clean base + mouth/nose overlays + glint; two Lumi lines (same D-3/timing review as S004).', None),
 'S013': ('A', 'F-FACE-MIRROR', 'CAN_DERIVE_DETERMINISTICALLY', 'LOW',
          'Protected 4.0 s hold: S012 end frame held.', None),
 'S014': ('C', 'F-MOUTH-CLOTH', 'NEEDS_NEW_SHOT_FRAME', 'HIGH',
          'Manifest video shot: slow hand approach with cloth, no contact; mouth+nose smudges and clean reflection pre-composited; Mikko line; soft cloth foley.',
          'Mikko slowly brings the cloth toward the mouth smudge and visibly slows before contact; no wipe; locked camera.'),
 'S015': ('D', 'F-MOUTH-CLOTH', 'BLOCKED', 'HIGH',
          'Mouth smudge removal synchronised to a provider-generated cloth pass: same unsolved tracked-removal capability as S009.',
          'One slower, smaller wipe beside the mouth, lift away; mouth smudge removed under the cloth only.'),
 'S016': ('C', 'F-FACE-MIRROR', 'CAN_DERIVE_DETERMINISTICALLY', 'MEDIUM',
          'Manifest video shot: Mikko lowers his hand; F-FACE-MIRROR clean base with nose overlay pre-composited; Lumi line.',
          'Mikko lowers his hand; Lumi checks the result holding the mirror; locked camera.'),
 'S017': ('A', 'F-MEDIUM-TWOSHOT', 'CAN_DERIVE_DETERMINISTICALLY', 'LOW',
          'Manifest compositor-only processing hold: F-MEDIUM-TWOSHOT clean base + nose overlay; no dialogue.', None),
 'S018': ('A', 'F-MACRO-REFLECTION', 'NEEDS_NEW_SHOT_FRAME', 'HIGH',
          'Manifest compositor-only: macro reflection + nose overlay + glint; in-shot cut/reframe (CODE_GAP); two Lumi lines.', None),
 'S019': ('A', 'F-MACRO-REFLECTION', 'CAN_DERIVE_DETERMINISTICALLY', 'LOW',
          'Protected 5.0 s hold: S018 end frame held.', None),
 'S020': ('C', 'F-NOSE-CLOTH', 'NEEDS_NEW_SHOT_FRAME', 'HIGH',
          'Manifest video shot: return from macro to close face, Mikko recognises nose and adjusts cloth; nose smudge pre-composited; Mikko line; cloth foley.',
          'Mikko looks up, adjusts the cloth toward the nose without contact; Lumi steady; locked camera (the macro-to-close return is a cut).'),
 'S021': ('D', 'F-NOSE-CLOTH', 'BLOCKED', 'HIGH',
          'Nose smudge removal synchronised to a provider-generated cloth pass: same unsolved tracked-removal capability as S009/S015.',
          'Cloth on nose, one small wipe, lift away; nose smudge removed under the cloth only.'),
 'S022': ('B', 'F-NOSE-CLOTH', 'CAN_DERIVE_DETERMINISTICALLY', 'MEDIUM',
          'Manifest video shot with zero overlays/treatments: Mikko lowers the cloth; clean base = F-NOSE-CLOTH clean; Lumi line. 3.0 s: generate 4 s and trim to 72 frames.',
          'Mikko lowers the cloth from his clear nose; Lumi steady; locked camera.'),
 'S023': ('A', 'F-MEDIUM-TWOSHOT', 'CAN_DERIVE_DETERMINISTICALLY', 'LOW',
          'Manifest compositor-only 3 s readable-result hold, clean face, no overlays.', None),
 'S024': ('A', 'F-MIRROR-OPEN', 'CAN_DERIVE_DETERMINISTICALLY', 'MEDIUM',
          'Manifest compositor-only 2 s camera settle toward the opening composition: deterministic crop/scale ramp on the F-MIRROR-OPEN clean frame ending on the exact S025 framing (CODE_GAP: keyframed crop).', None),
 'S025': ('A', 'F-MIRROR-OPEN', 'CAN_DERIVE_DETERMINISTICALLY', 'MEDIUM',
          'Manifest compositor-only CLEAN REVEAL: F-MIRROR-OPEN clean + clean reflection + completion pop accent + pop SFX; ZERO berry overlays; Lumi line.', None),
 'S026': ('B', 'F-MEDIUM-TWOSHOT', 'NEEDS_NEW_SHOT_FRAME', 'MEDIUM',
          'Manifest video shot, zero overlays/treatments: Mikko lifts cloth proudly and speaks; clean F-MEDIUM-TWOSHOT base (the same new frame also serves S002/S017/S023 with overlays as needed).',
          'Mikko lifts and holds the cloth away from his clear face, then a brief proud smile; Lumi holds the mirror; static camera.'),
 'S027': ('COMPLETE', None, 'APPROVED_EXISTING', None, 'COMPLETE_APPROVED: SHOT-EP005-S027-ASSEMBLED-v01 (7b01c392...8fde). Not to be rebuilt.', None),
 'S028': ('B', 'S027-END', 'CAN_DERIVE_DETERMINISTICALLY', 'HIGH',
          'Manifest video shot, zero overlays: cloth hand-off, mirror lowering, one shoulder pat, settle. Base = last frame of approved S027 raw motion (continuity S027->S028); MEDIUM vs S027 knees-up framing needs human acceptance, else F-MEDIUM-TWOSHOT.',
          'Mikko passes the cloth to Lumi; Lumi lowers the mirror to her lap and gives one gentle shoulder pat (never the face); Mikko settles; static camera.'),
 'S029': ('A', 'S028-END', 'CAN_DERIVE_DETERMINISTICALLY', 'LOW',
          'Manifest compositor-only 6 s safe-state hold: last frame of the approved S028 raw motion (mirror and cloth in Lumi lap).', None),
}
METHOD = {'A': 'STATIC_OR_DETERMINISTIC_ONLY', 'B': 'HIGGSFIELD_MOTION_REQUIRED', 'C': 'HYBRID', 'D': 'BLOCKED',
          'COMPLETE': 'COMPLETE_APPROVED'}

def syllables(text):
    n = 0
    for w in re.findall(r"[A-Za-z']+", text.lower()):
        w = w.replace("'", '')
        groups = len(re.findall(r'[aeiouy]+', w))
        if w.endswith('e') and not w.endswith(('le', 'ee')) and groups > 1:
            groups -= 1
        n += max(1, groups)
    return n

MIKKO_RATE = 5.04   # syl/s of the approved M1 take (single measured sample)
LUMI_RATE = (2.63, 3.01)   # syl/s range of the three Lumi audition takes (candidates, not approved)
CLIP_PAD = 0.45     # provider lead+tail silence observed on M1 (0.04 + 0.40 s)

rows = []
for x in mj['shot_plans']:
    sid = x['shot_id']; p = x['shot_plan']; a = p['audio_plan']; an = p['animation_plan']
    dur = round(x['end_seconds'] - x['start_seconds'], 3)
    cls, fam, frame_status, risk, reason, brief = C[sid]
    tracked = {e['element']: (e['visible_at_start'], e['visible_at_end']) for e in p['continuity_state']['tracked_elements']}
    def ovl(key, label):
        for k, v in tracked.items():
            if label in k.lower():
                return v
        return (False, False)
    overlays = []
    for key, label in (('cheek', 'cheek'), ('mouth', 'mouth'), ('nose', 'nose')):
        st, en = ovl(key, label)
        if st or en:
            overlays.append({'overlay_id': OVERLAY_ID[key], 'visible_at_start': st, 'visible_at_end': en,
                             'event': 'REMOVED_IN_SHOT' if st and not en else 'PERSISTENT'})
    lines = []
    for v in a['voice_lines']:
        spk, txt = v.split(':', 1)
        txt = txt.strip().strip('“”"')
        syl = syllables(txt)
        if spk.strip() == 'Mikko':
            est = round(syl / MIKKO_RATE + CLIP_PAD, 2); voice = 'APPROVED (Teddy Twinkle XjGYkUkzth8BPs29fmcV)'
            clip = 'APPROVED DLG-EP005-S027-L1-MIKKO-v01' if sid == 'S027' else 'NOT_GENERATED (1 TTS take needed)'
            est_txt = f'~{est} s at the M1 rate'
        else:
            est = [round(syl / LUMI_RATE[1], 2), round(syl / LUMI_RATE[0], 2)]; voice = 'BLOCKED: no human-approved Lumi production voice'
            clip = 'BLOCKED_ON_LUMI_VOICE'; est_txt = f'~{est[0]}-{est[1]} s speech at audition rates'
        lines.append({'speaker': spk.strip(), 'text': txt, 'syllables': syl, 'estimated_duration': est_txt,
                      'voice_status': voice, 'clip_status': clip})
    named = [governed(NAMED_TO_ID[n]) for n in a['named_audio_assets']]
    mapped = [governed(m) for m in audio_map.get(sid, [])]
    rows.append({
        'shot_id': sid, 'section': p['section'], 'episode_range_s': [x['start_seconds'], x['end_seconds']],
        'duration_s': dur, 'frames_24fps': int(round(dur * FPS)),
        'intended_action': p['production_summary'], 'camera': p['camera_setup']['framing_scale'] + ' | ' + p['camera_setup']['movement'],
        'characters': [c['character_name'] for c in p['character_requirements']],
        'props': [pp['prop_name'] for pp in p['prop_requirements']],
        'dialogue': lines,
        'ambience': [m for m in mapped if m.get('subtype') == 'AMBIENCE'],
        'foley': [m for m in mapped if m.get('subtype') == 'FOLEY'],
        'sfx': named + [m for m in mapped if m.get('subtype') == 'SFX'],
        'music_present': a['music_present'],
        'protected_participation_hold': sid in (mj['audio_workload'].get('protected_participation_hold_shots') or []),
        'overlays': overlays, 'treatments': treat.get(sid, []),
        'continuity': p['dependencies'],
        'manifest_flags': {'video_generation_required': an['video_generation_required'],
                           'image_generation_required': an['image_generation_required'],
                           'compositor_required': an['compositor_required'], 'method': an['method'],
                           'complexity': p['production_complexity']},
        'PRODUCTION_STATUS': 'COMPLETE_APPROVED' if cls == 'COMPLETE' else 'TODO',
        'classification': METHOD[cls], 'classification_reason': reason,
        'base_frame_family': fam, 'BASE_FRAME_STATUS': frame_status,
        'motion_brief': brief and {'movement': brief, 'camera': 'locked / static (no pan, tilt, zoom, dolly, reframing, cuts)',
                                   'preservation': 'exact approved identities, costumes, colours, props; smudge state exactly as frame; clean mirror glass',
                                   'prohibited': 'extra limbs/characters, prop duplication, morphing, text/logos, sparkles/magic, unscripted wipes, lip-sync, audio',
                                   'model': 'bytedance/seedance-2.0/image-to-video', 'duration_s': max(4, int(-(-dur // 1))),
                                   'trim_to_frames': int(round(dur * FPS)), 'resolution': '1080p', 'generate_audio': False},
        'PRODUCTION_RISK': risk,
    })

# ---- capability gaps -----------------------------------------------------------------------------
GAPS = {
 'G01_INPUT_SNAPSHOT_COVERAGE': ('Agent-008 snapshots hold only S004,S005,S025 (phase0) and S026,S027 (motion); build_shot_spec fails SHOT_NOT_IN_MANIFEST for the other 24.', 'Run the existing read-only agent008/tools/snapshot_inputs.py once for all 29 shots and commit the snapshot (no code change).'),
 'G02_PRODUCTION_STILL_SHOT_PATH': ('Still shots render only through the Phase-0 stand-in path, hard-wired to S004/S005 and a NON-CANON layout.', 'Add compose_still_shot(approved_frame_sha, spec_shot, timing): hold a hash-verified approved/derived frame for N frames and reuse the existing treatment, mix (incl. dialogue) and encode functions.'),
 'G03_OVERLAY_ANCHOR_PLACEMENT': ('Berry overlays have no placement spec on production frames (face plus mirrored reflection).', 'A per-frame anchor JSON (x, y, scale, rotation, mirror flag) per overlay, human-approved, applied deterministically; reused for static shots and for pre-compositing smudges into base frames before provider upload.'),
 'G04_DERIVED_FRAME_FROM_APPROVED_MOTION': ('No governed way to take the last (or Nth) frame of an approved RAW_MOTION_SOURCE as the base of the next shot.', 'Deterministic extract (ffmpeg, exact frame index) recorded with source SHA, frame index and output SHA; registered SHOT_FRAME/DERIVED_FRAME after human approval.'),
 'G05_ROLE_AWARE_MAPPED_AUDIO': ('spec mapped_audio mixes FOLEY-CLOTH-SOFT-v01 and SFX-COMPLETION-POP-v01 as looped full-length beds (mix_motion_audio/BED). Only AMBIENCE should be a bed.', 'Split mapped_audio by registry subtype: AMBIENCE = bed; FOLEY/SFX = timed one-shot cues requiring timing (fail closed without), as named_sfx already does.'),
 'G06_KEYFRAMED_CROP_SCALE': ('No deterministic camera settle (S024) on stills.', 'Keyframed crop/scale ramp (start rect -> end rect, smoothstep) on a still, within source resolution (no upscale beyond 1.0).'),
 'G07_IN_SHOT_CUT': ('S018 needs an adjustment segment then a cut to macro inside one shot.', 'Two-segment shot: concatenate two deterministic segments at an exact frame; provenance per segment.'),
 'G08_TREATMENTS_ON_STILL_PRODUCTION': ('Glint, reflection and pop-accent primitives exist; only the glint has run (Phase-0). Reflection/pop not executed in a production path.', 'Wire treatments.TREATMENTS into G02 with frame windows from timing; reflection only if the frame does not already contain a readable reflection.'),
 'G09_DIALOGUE_OVERLAP_AND_HOLD_GUARD': ('resolve_dialogue supports N slots, but does not reject overlapping clips or clips inside protected holds/before-cue windows.', 'Add non-overlap and window checks to resolve_dialogue (fail closed).'),
 'G10_WHOOSH_HASH_PIN': ('SFX-MIKKO-TRY-WHOOSH has no registry SHA and no hash pin, so Agent-008 fails closed on S007.', 'Read-only storage hash audit and a committed hash pin (data, not code).'),
 'G11_TRACKED_OVERLAY_REMOVAL': ('S009/S015/S021 need a smudge to vanish exactly under a provider-generated moving cloth.', 'Not small: requires tracking (or a human-designed masked crossfade on an occluding frame window). Needs its own design decision before any spend.'),
}
gap_shots = {
 'G01_INPUT_SNAPSHOT_COVERAGE': [r['shot_id'] for r in rows if r['shot_id'] not in ('S026', 'S027')],
 'G02_PRODUCTION_STILL_SHOT_PATH': [r['shot_id'] for r in rows if r['classification'] == METHOD['A']],
 'G03_OVERLAY_ANCHOR_PLACEMENT': [r['shot_id'] for r in rows if r['overlays'] and r['classification'] in (METHOD['A'], METHOD['C'])],
 'G04_DERIVED_FRAME_FROM_APPROVED_MOTION': ['S008', 'S011', 'S028', 'S029'],
 'G05_ROLE_AWARE_MAPPED_AUDIO': [r['shot_id'] for r in rows if r['foley'] or any(s.get('subtype') == 'SFX' and s['asset_id'].startswith('SFX-COMPLETION') for s in r['sfx'])],
 'G06_KEYFRAMED_CROP_SCALE': ['S024'],
 'G07_IN_SHOT_CUT': ['S018'],
 'G08_TREATMENTS_ON_STILL_PRODUCTION': [r['shot_id'] for r in rows if r['treatments'] and r['classification'] == METHOD['A']],
 'G09_DIALOGUE_OVERLAP_AND_HOLD_GUARD': [r['shot_id'] for r in rows if len(r['dialogue']) > 1],
 'G10_WHOOSH_HASH_PIN': [r['shot_id'] for r in rows if any(s['asset_id'] == 'SFX-MIKKO-TRY-WHOOSH' for s in r['sfx'])],
 'G11_TRACKED_OVERLAY_REMOVAL': [r['shot_id'] for r in rows if r['classification'] == METHOD['D']],
}
for r in rows:
    if r['PRODUCTION_STATUS'] == 'COMPLETE_APPROVED':
        r['agent008'] = 'SUPPORTED_NOW (complete)'; r['code_gaps'] = []; continue
    g = [k for k, v in gap_shots.items() if r['shot_id'] in v]
    r['code_gaps'] = g
    r['agent008'] = 'SUPPORTED_NOW' if not g else 'CODE_GAP'

# ---- provider-call estimates ---------------------------------------------------------------------
NEW_FRAMES = sorted({r['base_frame_family'] for r in rows if r['BASE_FRAME_STATUS'] == 'NEEDS_NEW_SHOT_FRAME'})
for r in rows:
    if r['PRODUCTION_STATUS'] == 'COMPLETE_APPROVED':
        r['PROVIDER_CALLS_REQUIRED'] = {'image': 0, 'video': 0, 'tts': 0}; continue
    img = 1 if r['BASE_FRAME_STATUS'] == 'NEEDS_NEW_SHOT_FRAME' else 0
    vid = 1 if r['classification'] in (METHOD['B'], METHOD['C'], METHOD['D']) else 0
    tts = sum(1 for d in r['dialogue'] if d['speaker'] == 'Mikko')
    tts_blocked = sum(1 for d in r['dialogue'] if d['speaker'] == 'Lumi')
    r['PROVIDER_CALLS_REQUIRED'] = {'image': img, 'video': vid, 'tts_mikko': tts, 'tts_lumi_after_voice_approval': tts_blocked,
                                    'cost': 'video: ~$3.40 list per 5 s 1080p Seedance 2.0 (token formula, S027 basis; duration-scaled); image/tts: COST_UNVERIFIED'}

rem = [r for r in rows if r['PRODUCTION_STATUS'] != 'COMPLETE_APPROVED']
count = lambda m: sum(1 for r in rem if r['classification'] == m)
summary = {
 'TOTAL_EP005_SHOTS': len(rows), 'S027_COMPLETE_APPROVED': sum(1 for r in rows if r['PRODUCTION_STATUS'] == 'COMPLETE_APPROVED'),
 'REMAINING_SHOTS': len(rem), 'STATIC_OR_DETERMINISTIC_ONLY': count(METHOD['A']), 'HIGGSFIELD_MOTION_REQUIRED': count(METHOD['B']),
 'HYBRID': count(METHOD['C']), 'BLOCKED': count(METHOD['D']), 'NEW_BASE_FRAMES_REQUIRED': len(NEW_FRAMES), 'NEW_BASE_FRAME_FAMILIES': NEW_FRAMES,
 'MIKKO_DIALOGUE_SHOTS': sum(1 for r in rows if any(d['speaker'] == 'Mikko' for d in r['dialogue'])),
 'MIKKO_DIALOGUE_SHOTS_REMAINING': sum(1 for r in rem if any(d['speaker'] == 'Mikko' for d in r['dialogue'])),
 'LUMI_DIALOGUE_SHOTS': sum(1 for r in rows if any(d['speaker'] == 'Lumi' for d in r['dialogue'])),
 'LUMI_VOICE_BLOCKED_SHOTS': sum(1 for r in rem if any(d['speaker'] == 'Lumi' for d in r['dialogue'])),
 'AGENT008_CODE_GAPS': len(GAPS), 'SHOTS_WITH_CODE_GAPS': sum(1 for r in rem if r['agent008'] == 'CODE_GAP'),
 'ESTIMATED_VIDEO_GENERATIONS_REQUIRED': sum(r['PROVIDER_CALLS_REQUIRED']['video'] for r in rem if r['classification'] != METHOD['D']),
 'ESTIMATED_VIDEO_GENERATIONS_IF_BLOCKED_SHOTS_UNBLOCKED': sum(r['PROVIDER_CALLS_REQUIRED']['video'] for r in rem),
 'ESTIMATED_IMAGE_GENERATIONS_REQUIRED': len(NEW_FRAMES),
 'ESTIMATED_NEW_TTS_GENERATIONS_REQUIRED': sum(r['PROVIDER_CALLS_REQUIRED']['tts_mikko'] for r in rem),
 'ESTIMATED_LUMI_TTS_AFTER_VOICE_APPROVAL': sum(r['PROVIDER_CALLS_REQUIRED']['tts_lumi_after_voice_approval'] for r in rem),
 'MANIFEST_VIDEO_GENERATION_SHOTS': len(mj['generation_workload']['video_generation_shots']),
 'MANIFEST_IMAGE_GENERATION_SHOTS': len(mj['generation_workload']['image_generation_shots']),
 'basis': 'one attempt per generation, no retries assumed; video counts exclude S027 (complete)',
}
total_frames = sum(r['frames_24fps'] for r in rows)
assert total_frames == 120 * FPS, total_frames
json.dump({'source': {'production_manifest_id': manifest['id'], 'readiness_manifest_id': 'edc4ad58-3e5d-4ac2-9c74-c9af03af363f',
                      'script': 'EP-CANDIDATE-005 v02 (14471926), APPROVED'},
           'summary': summary, 'base_frame_families': FAMILIES, 'code_gaps': {k: {'gap': v[0], 'smallest_change': v[1], 'shots': gap_shots[k]} for k, v in GAPS.items()},
           'shots': rows}, open(OUT / 'EP005_AGENT008_PRODUCTION_MATRIX_v1.json', 'w'), indent=1, ensure_ascii=False)
print(json.dumps(summary, indent=1))
for r in rows:
    print(r['shot_id'], r['frames_24fps'], r['classification'], r['BASE_FRAME_STATUS'], r['base_frame_family'], r['PRODUCTION_RISK'],
          r['agent008'], r['code_gaps'], r['PROVIDER_CALLS_REQUIRED'] if r['PRODUCTION_STATUS'] != 'COMPLETE_APPROVED' else '')
