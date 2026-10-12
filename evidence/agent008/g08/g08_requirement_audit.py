"""READ-ONLY G08 requirement audit: every remaining EP005 shot whose production path requires a visual treatment.

Usage (repo root): python3 evidence/agent008/g08/g08_requirement_audit.py <out_json>
Sources (HTTP GET only): APPROVED manifest 0325d35c (shot_plans + compositing_treatments), APPROVED readiness 69bff641
(Agent-008 spec resolution), the Batch 0C held-pose decision, and the code as it stands before G08. Values are quoted from
the authoritative records; anything deterministic production needs but the records do not define is G08_SPEC_GAP.
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
from agent008.spec import TREATMENT_CLASS  # noqa: E402
from agent008.tools.snapshot_inputs import build_snapshot  # noqa: E402
from agent008.treatments import TREATMENTS  # noqa: E402

SB = 'https://ziluiwrwwbayhcskeere.supabase.co'
MANIFEST, READINESS = '0325d35c-d567-4488-bf78-c3887e819382', '69bff641-e056-4701-a23f-d91dbc2039b2'
COMPLETE, GAP = ('S027', 'S028', 'S029'), 'G08_SPEC_GAP'
HELD_POSE_APPROVED = {'S003', 'S004', 'S005', 'S008', 'S012', 'S013', 'S017', 'S018', 'S019', 'S023', 'S024', 'S025', 'S029'}
MOTION_FOR_PLANNING = {'S006'}                         # Batch 0C: S006_MOTION_REQUIRED_FOR_PLANNING
GLINT, REFL, POP = 'TREATMENT-EP005-MIRROR-GLINT-v01', 'TREATMENT-EP005-MIRROR-REFLECTION-v01', 'TREATMENT-EP005-COMPLETION-POP-ACCENT-v01'

r = UrllibHttpClient().send('GET', f'{SB}/rest/v1/episode_production_manifests?id=eq.{MANIFEST}&select=status,manifest_json',
                            {'Accept': 'application/json'})
m = json.loads(r.body)
if r.status != 200 or len(m) != 1 or m[0]['status'] != 'APPROVED':
    sys.exit('STOP: manifest not exactly one APPROVED row')
mj = m[0]['manifest_json']
plans = {s['shot_id']: s for s in mj['shot_plans']}
ct = {c['treatment_id']: c for c in mj['compositing_treatments']}
spec = load_output_spec()
resolved = {x['shot_id']: x for x in resolve_episode(build_snapshot(READINESS), load_hash_pins(PINS), spec)}


def instr(tid, sid):
    return next((i for i in ct[tid]['shot_instructions'] if i['shot_id'] == sid), {})


def qc_lines(p, *words):
    return [q for q in p.get('qc_checks') or [] if any(w in q.lower() for w in words)]


shots = []
for sid, s in sorted(plans.items()):
    if sid in COMPLETE:
        continue
    p = s['shot_plan']
    tids = [o['asset_id'] for o in p.get('overlay_vfx_requirements') or []
            if o.get('requirement_class') == TREATMENT_CLASS or o.get('asset_status') == 'COMPOSITING_TREATMENT']
    if not tids:
        continue
    sp = resolved[sid].get('spec') or {}
    n = sp.get('frames') or int(round((s['end_seconds'] - s['start_seconds']) * spec.fps))
    motion = p['animation_plan']['video_generation_required'] or sid in MOTION_FOR_PLANNING
    entries = []
    for tid in tids:
        i, t = instr(tid, sid), ct[tid]
        e = {'TREATMENT_ID': tid, 'TREATMENT_TYPE': TREATMENTS[tid]['kind'], 'TREATMENT_PURPOSE': i.get('usage'),
             'element': i.get('element'), 'overlay_role': i.get('overlay_role'), 'manifest_handling': t['handling'],
             'classification': t['classification'], 'paid_generation_required': t['paid_generation_required']}
        if tid == GLINT:
            sync = [x for x in p['audio_plan'].get('sfx_requirements') or [] if 'glint' in x.lower()]
            e.update({
                'AFFECTED_FRAME_RANGE': f'one window of {TREATMENTS[tid]["min_frames"]}-{TREATMENTS[tid]["max_frames"]} frames inside 0-{n - 1}, '
                                        f'ending before the shot end; start frame: {GAP} (not numerically defined)',
                'VISUAL_SOURCE': 'deterministic procedural soft specular sprite (compositor.glint_sprite); not an asset',
                'TIMING_REQUIREMENT': {'S004': 'synchronised with the initial mirror tilt and the Lumi clue chime; complete before S005',
                                       'S012': 'after Lumi angles the mirror; finishes within the shot before any later response hold',
                                       'S018': 'appears exactly once and ends before S019 (in the macro part after the in-shot cut)'}[sid],
                'audio_sync_evidence': sync + qc_lines(p, 'chime'),
                'PLACEMENT_REQUIREMENT': f"on the mirror glass near the relevant reflected mark ({i.get('element')}); coordinates: {GAP}",
                'MIRROR_BEHAVIOUR': 'glint is a specular on the glass surface: drawn above the reflected content; not mirrored',
                'COMPOSITING_REQUIREMENT': 'small, soft, brief, non-magical, same established look each time; opacity envelope',
                'qc_evidence': qc_lines(p, 'glint')})
        elif tid == REFL:
            e.update({
                'AFFECTED_FRAME_RANGE': f'whole shot 0-{n - 1} (persistent composition)',
                'VISUAL_SOURCE': t['handling'],
                'TIMING_REQUIREMENT': 'static for the whole shot',
                'PLACEMENT_REQUIREMENT': f'reflection inside the mirror glass of the shot frame; glass region and (if composited) reflected-face mapping: {GAP}',
                'MIRROR_BEHAVIOUR': 'reflected marks are the left-right reversal of the face marks; "Composite or preserve" the reflection; '
                                    'the glass itself stays clean (no mark on the glass surface)',
                'COMPOSITING_REQUIREMENT': i.get('usage'),
                'qc_evidence': qc_lines(p, 'mirror glass', 'reflect')})
        elif tid == POP:
            e.update({
                'AFFECTED_FRAME_RANGE': f'one window of {TREATMENTS[tid]["min_frames"]}-{TREATMENTS[tid]["max_frames"]} frames inside 0-{n - 1}; '
                                        f'start frame = completion-pop audio start ({GAP}: audio start not numerically defined)',
                'VISUAL_SOURCE': 'deterministic brightness/bloom pulse (compositor.brightness_pulse, max gain 0.12); not an asset',
                'TIMING_REQUIREMENT': 'synchronised with the completion-pop audio (SFX-COMPLETION-POP-v01 mapped to S025) at the clean mirror reveal',
                'PLACEMENT_REQUIREMENT': f'on the mirror glass; glass region: {GAP}',
                'MIRROR_BEHAVIOUR': 'not mirrored; lifts the glass region',
                'COMPOSITING_REQUIREMENT': 'subtle; must not imply that anything is being removed; overlay state unchanged (zero berry overlays)',
                'qc_evidence': qc_lines(p, 'pop', 'smudges remain absent')})
        entries.append(e)
    shots.append({
        'SHOT_ID': sid, 'frames': n, 'video_generation_required_in_spec': p['animation_plan']['video_generation_required'],
        'planned_path': 'PROVIDER_MOTION' if motion else 'G02_STILL', 'held_pose_approved': sid in HELD_POSE_APPROVED,
        'active_overlays': [o['asset_id'] for o in sp.get('active_overlays') or []],
        'named_sfx': [x['asset_id'] for x in sp.get('named_sfx') or []], 'event_audio': [x['asset_id'] for x in sp.get('event_audio') or []],
        'motion_description': p['animation_plan']['motion_description'],
        'CURRENT_CODE_SUPPORT': ('motion compose rejects any treatment (MOTION_TREATMENTS_NEED_TRACKING_V02)' if motion else
                                 'G02 still rejects any treatment (STILL_TREATMENTS_NEED_G08)') +
                                '; primitives exist (compositor.glint_sprite / brightness_pulse / flip_h / disc_mask / tint, '
                                'treatments.envelope / validate_window) but are only wired into the Phase-0 stand-in render',
        'SPEC_GAPS': sorted({GAP + ': ' + x for x in (
            ['mirror-glass region in base-frame pixels (no approved base frame exists)'] +
            (['glint centre, size and start frame'] if GLINT in tids else []) +
            (['reflection mode (preserve vs composite) and, if composited, the face source region and its mapping into the glass'] if REFL in tids else []) +
            (['completion-pop start time (audio start not numerically defined)'] if POP in tids else []) +
            (['in-shot cut frame (G07)'] if sid == 'S018' else []))}),
        'treatments': entries})

out = {'manifest': MANIFEST, 'readiness': READINESS,
       'G08_DEPENDENT_SHOTS': [s['SHOT_ID'] for s in shots],
       'G08_TREATMENT_TYPES_REQUIRED': sorted({e['TREATMENT_TYPE'] for s in shots for e in s['treatments']}),
       'treatment_definitions': {k: {kk: v[kk] for kk in ('handling', 'affected_shots', 'classification', 'human_decision')}
                                 for k, v in ct.items()},
       'shots': shots}
Path(sys.argv[1]).write_text(json.dumps(out, indent=1, ensure_ascii=False))
print(out['G08_DEPENDENT_SHOTS'], out['G08_TREATMENT_TYPES_REQUIRED'])
for s in shots:
    print(s['SHOT_ID'], s['planned_path'], s['held_pose_approved'], [e['TREATMENT_TYPE'] for e in s['treatments']], s['named_sfx'], s['event_audio'],
          len(s['active_overlays']))
