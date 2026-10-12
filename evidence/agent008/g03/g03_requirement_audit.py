"""READ-ONLY G03 requirement audit: every remaining EP005 shot whose production path depends on overlay placement.

Usage (repo root): python3 evidence/agent008/g03/g03_requirement_audit.py <out_json>
Sources (HTTP GET only): approved manifest 0325d35c (full manifest_json shot_plans), approved readiness 69bff641
(via the Agent-008 input snapshot + spec resolution), governed registry rows for the overlay assets. No writes.
Every placement value is reported exactly as the authoritative records state it; anything the records do not define
but deterministic placement needs is reported as G03_SPEC_GAP.
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
from agent008.spec import BERRY_PREFIX, TREATMENT_CLASS, element_key  # noqa: E402
from agent008.tools.snapshot_inputs import build_snapshot  # noqa: E402

SB = 'https://ziluiwrwwbayhcskeere.supabase.co'
MANIFEST = '0325d35c-d567-4488-bf78-c3887e819382'
READINESS = '69bff641-e056-4701-a23f-d91dbc2039b2'
COMPLETE = ('S027', 'S028', 'S029')
GAP = 'G03_SPEC_GAP'
PLACEMENT_KEYS = ('x', 'y', 'position', 'center', 'anchor', 'scale', 'width', 'height', 'size', 'opacity', 'z_order',
                  'z', 'layer', 'rotation', 'rotation_deg', 'mirror', 'flip', 'frame_range', 'start_frame', 'end_frame',
                  'placement', 'coordinates')


def get(path):
    r = UrllibHttpClient().send('GET', f'{SB}/rest/v1/{path}', {'Accept': 'application/json'})
    if r.status != 200:
        sys.exit(f'STOP: GET {path} HTTP {r.status}')
    return json.loads(r.body)


m = get(f'episode_production_manifests?id=eq.{MANIFEST}&select=id,status,manifest_json')
if len(m) != 1 or m[0]['status'] != 'APPROVED':
    sys.exit('STOP: manifest not exactly one APPROVED row')
plans = {s['shot_id']: s for s in m[0]['manifest_json']['shot_plans']}
treat = {c['treatment_id']: c for c in m[0]['manifest_json'].get('compositing_treatments') or []}
ov_rows = {r['asset_id']: r for r in get('asset_registry?asset_id=like.OVERLAY-*&select=asset_id,id,status,asset_type,'
                                         'asset_subtype,storage_path,metadata_json')}
spec = load_output_spec()
resolved = {r['shot_id']: r for r in resolve_episode(build_snapshot(READINESS), load_hash_pins(PINS), spec)}

shots, deps = [], []
for sid, s in sorted(plans.items()):
    if sid in COMPLETE:
        continue
    plan = s['shot_plan']
    reqs = [o for o in plan.get('overlay_vfx_requirements') or []
            if not (o.get('requirement_class') == TREATMENT_CLASS or o.get('asset_status') == 'COMPOSITING_TREATMENT')]
    tr_ids = [o['asset_id'] for o in plan.get('overlay_vfx_requirements') or [] if o not in reqs]
    berries = {element_key(t['element']): t for t in plan['continuity_state']['tracked_elements']
               if element_key(t['element']).startswith(BERRY_PREFIX)}
    r = resolved[sid]
    sp = r.get('spec') or {}
    frames = sp.get('frames') or int(round((s['end_seconds'] - s['start_seconds']) * spec.fps))
    entries = []
    for o in reqs:
        t = berries.get(element_key(o['element']), {})
        transition = t.get('visible_at_start') != t.get('visible_at_end')
        row = ov_rows.get(o['asset_id'], {})
        declared = sorted(k for k in o if k in PLACEMENT_KEYS)
        entries.append({
            'OVERLAY_ASSET': o['asset_id'],
            'OVERLAY_REGISTRY': {'id': row.get('id'), 'status': row.get('status'), 'type': f"{row.get('asset_type')}/{row.get('asset_subtype')}",
                                 'sha256': (row.get('metadata_json') or {}).get('sha256'),
                                 'dimensions': (row.get('metadata_json') or {}).get('dimensions')},
            'OVERLAY_ROLE': o.get('overlay_role'),
            'ELEMENT': o['element'],
            'AFFECTED_FRAME_RANGE': (f'0-{frames - 1} (whole shot; continuity visible_at_start=visible_at_end=true)'
                                     if not transition and t.get('visible_at_start') else
                                     f"TRANSITION visible_at_start={t.get('visible_at_start')} visible_at_end={t.get('visible_at_end')}; "
                                     'removal frame not defined -> ' + GAP),
            'PLACEMENT_REQUIREMENT': f"{GAP} (no x/y in manifest; anatomical description only: {o['element']!r})",
            'SCALE_REQUIREMENT': f'{GAP} (no size/scale in manifest)',
            'OPACITY_REQUIREMENT': 'NOT_DECLARED (no partial-opacity requirement in manifest; only full presence/absence is governed)',
            'Z_ORDER_REQUIREMENT': 'NOT_DECLARED (overlays sit on Mikko; no inter-overlay order stated)',
            'ANCHOR_REQUIREMENT': f"{GAP} (anchored to Mikko anatomy {o['element']!r}; no numeric anchor; base frame not yet existing)",
            'REMOVAL_REQUIREMENT': ('REMOVAL_IN_SHOT (G11, not G03): ' + o.get('usage', '') if transition else 'NONE in this shot'),
            'ANY_OTHER_GOVERNED_BEHAVIOUR': {'usage': o.get('usage'), 'derived_from_element': o.get('derived_from_element'),
                                             'manifest_placement_fields_present': declared,
                                             'mirror_reversal_required': 'mirror reversal' in (o.get('usage') or '').lower()
                                             or 'reflect' in (o.get('usage') or '').lower(),
                                             'independently_removable': 'independently removable' in (o.get('usage') or '').lower()},
        })
    if not entries:
        continue
    has_transition = any(e['AFFECTED_FRAME_RANGE'].startswith('TRANSITION') for e in entries)
    path = ('BLOCKED_G11_REMOVAL' if has_transition else
            'HYBRID_PRECOMPOSITE_INTO_MOTION_BASE_FRAME' if sp.get('video_generation_required') else 'STILL_COMPOSITE')
    shot = {'SHOT_ID': sid, 'spec_state': r['status'], 'frames': frames, 'video_generation_required': plan['animation_plan']['video_generation_required'],
            'treatments': tr_ids, 'reflection_treatment': 'TREATMENT-EP005-MIRROR-REFLECTION-v01' in tr_ids,
            'g03_path': path, 'g03_dependent': not has_transition, 'overlays': entries}
    shots.append(shot)
    if not has_transition:
        deps.append(sid)

out = {'manifest': MANIFEST, 'readiness': READINESS, 'shots_with_overlay_requirements': [s['SHOT_ID'] for s in shots],
       'G03_DEPENDENT_SHOTS': deps, 'G03_DEPENDENT_COUNT': len(deps),
       'G11_REMOVAL_SHOTS_NOT_G03': [s['SHOT_ID'] for s in shots if not s['g03_dependent']],
       'overlay_assets': {k: {'id': v['id'], 'status': v['status'], 'sha256': v['metadata_json'].get('sha256'),
                              'dimensions': v['metadata_json'].get('dimensions'), 'has_alpha': v['metadata_json'].get('has_alpha'),
                              'format': v['metadata_json'].get('format')} for k, v in ov_rows.items()},
       'spec_gap_summary': {
           'placement_xy': 'G03_SPEC_GAP for every dependent shot: the manifest names anatomy only',
           'scale': 'G03_SPEC_GAP for every dependent shot',
           'anchor': 'G03_SPEC_GAP for every dependent shot (no approved base frame exists for S001-S026, so no anchor can be measured yet)',
           'resolution': 'per-base-frame human-approved overlay placement record (recorded G03 design: x, y, scale, rotation, mirror)'},
       'shots': shots}
Path(sys.argv[1]).write_text(json.dumps(out, indent=1, ensure_ascii=False))
print('dependent', len(deps), deps)
print('G11', out['G11_REMOVAL_SHOTS_NOT_G03'])
for s in shots:
    print(s['SHOT_ID'], s['g03_path'], s['frames'], [(e['OVERLAY_ASSET'][22:-4], e['OVERLAY_ROLE']) for e in s['overlays']], s['treatments'],
          [e['ANY_OTHER_GOVERNED_BEHAVIOUR']['manifest_placement_fields_present'] for e in s['overlays']])
