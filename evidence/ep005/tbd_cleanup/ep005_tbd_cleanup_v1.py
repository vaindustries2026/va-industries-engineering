#!/usr/bin/env python3
"""EP005_TBD_CLEANUP_v1 - deterministic, LLM-free derivation of a second EP005 manifest from the approved
derived manifest 3bcde9ee (never modified), applying the recorded human decisions on the remaining TBDs:

  - Mirror glint treatment                   -> compositing treatment (not an asset)
  - Mirror reflection/compositing treatment  -> compositing treatment (not an asset)
  - Soft completion pop visual accent        -> compositing treatment (not an asset), KEPT
  - FOLEY_TOUCH                              -> dropped (no sound asset; S028 visual pat untouched)
  - AMBIENCE, FOLEY_CLOTH, COMPLETION_SFX    -> remain unresolved audio TBDs (not mapped)

Shot-level creative text (usage/element/overlay_role, audio phrases, actions) is copied verbatim.
Usage: ep005_tbd_cleanup_v1.py <source_row.json> <derived_row_out.json>
Fails closed on any invariant breach.
"""
import copy, json, sys

SOURCE_ID = '3bcde9ee-6676-480f-90da-5695b64532a7'
SOURCE_RUN = 'DRV-EP005-BERRY-SPLIT-1-A005O-1790400144423'
SOURCE_A006_RUN = 'A006-1791181098027'
SOURCE_READINESS = 'e32ef7eb-448d-4da8-8271-fabf51bdc81e'
DERIVED_RUN = 'DRV-EP005-TBD-CLEANUP-1-A005O-1790400144423'
TREATMENTS = [  # (treatment id, original dependency label, human decision, handling)
    ('TREATMENT-EP005-MIRROR-GLINT-v01', 'Mirror glint treatment', 'DERIVE/COMPOSITE FROM EXISTING; not a standalone production asset',
     'One deterministic compositor preset across all listed shots: small soft specular glint, short opacity/scale envelope of '
     'approximately 6-10 frames, placed on the mirror glass near the relevant reflected mark, non-magical, same established look each time.'),
    ('TREATMENT-EP005-MIRROR-REFLECTION-v01', 'Mirror reflection/compositing treatment', 'NOT A SEPARATE ASSET; shot-level compositing logic',
     'Composite using PROP-EP005-HAND-MIRROR-v01, CHAR-MIKKO-MASTER-v01 and the berry overlays active per continuity '
     '(OVERLAY-EP005-BERRY-SMUDGE-CHEEK/MOUTH/NOSE-v01); mirror-glass treatment and continuity logic stay in the shot instructions.'),
    ('TREATMENT-EP005-COMPLETION-POP-ACCENT-v01', 'Soft completion pop visual accent', 'NOT A SEPARATE ASSET; human decision: KEEP the effect',
     'Deterministic subtle brightness/bloom pulse on the mirror glass at S025, approximately 6-8 frames, synchronised with the '
     'completion-pop audio (COMPLETION_SFX). Must not imply that anything is being removed.'),
]
DROP_AUDIO = 'FOLEY_TOUCH'
KEEP_AUDIO = ['AMBIENCE', 'FOLEY_CLOTH', 'COMPLETION_SFX']
KEEP_VISUAL = ['Lumi', 'Mikko', 'Canonical environment/background']
DECISIONS = {
    'Mirror glint treatment': 'DERIVE/COMPOSITE_FROM_EXISTING (compositor preset; not an asset; never Agent-007)',
    'Mirror reflection/compositing treatment': 'NOT_A_SEPARATE_ASSET (shot-level compositing; never Agent-007)',
    'Soft completion pop visual accent': 'NOT_A_SEPARATE_ASSET, KEEP (deterministic bloom pulse; never Agent-007)',
    'AMBIENCE': 'CREATE_NEW_AUDIO later (proposed AMB-BATHROOM-QUIET-v01); unresolved, not mapped',
    'FOLEY_CLOTH': 'CREATE_NEW_AUDIO later (proposed FOLEY-CLOTH-SOFT-v01); unresolved, not mapped',
    'COMPLETION_SFX': 'CREATE_NEW_AUDIO later (proposed SFX-COMPLETION-POP-v01); unresolved, not mapped',
    'FOLEY_TOUCH': 'DROPPED: barely audible, narratively non-essential; no sound asset; S028 visual shoulder-pat action unchanged',
}


def fail(msg):
    sys.exit(f'FAIL_CLOSED: {msg}')


def load_plan(e):
    p = e['shot_plan']
    return (json.loads(p), True) if isinstance(p, str) else (p, False)


def derive(src):
    if src.get('id') != SOURCE_ID or src.get('status') != 'APPROVED' or src.get('production_plan_run_id') != SOURCE_RUN:
        fail('source is not the APPROVED derived manifest 3bcde9ee')
    m0 = src['manifest_json']
    m0 = json.loads(m0) if isinstance(m0, str) else m0
    m = copy.deepcopy(m0)
    labels = {t[1] for t in TREATMENTS}

    # 1. visual treatments out of unique_tbd_asset_dependencies (keep full original entries for the treatment section)
    deps = m['unique_tbd_asset_dependencies']
    moved = {d['dependency']: d for d in deps if d.get('dependency_type') == 'VISUAL' and d.get('dependency') in labels}
    if set(moved) != labels:
        fail(f'expected the 3 visual treatment dependencies, found {sorted(moved)}')
    dropped_audio = [d for d in deps if d.get('audio_category') == DROP_AUDIO]
    if len(dropped_audio) != 1:
        fail('expected exactly one FOLEY_TOUCH entry in unique_tbd_asset_dependencies')
    m['unique_tbd_asset_dependencies'] = [d for d in deps if not (d.get('dependency') in labels and d.get('dependency_type') == 'VISUAL')
                                          and d.get('audio_category') != DROP_AUDIO]
    a0 = m['audio_tbd_dependencies']
    if sum(1 for d in a0 if d.get('audio_category') == DROP_AUDIO) != 1:
        fail('expected exactly one FOLEY_TOUCH entry in audio_tbd_dependencies')
    m['audio_tbd_dependencies'] = [d for d in a0 if d.get('audio_category') != DROP_AUDIO]

    # 2. unresolved_tbd_references: move the OVERLAY_VFX treatment references out (shot attribution kept in treatments)
    refs = m['unresolved_tbd_references']
    label_to_dep = {}
    for dep in moved.values():
        for l in dep.get('source_labels', []):
            label_to_dep[l] = dep['dependency']
    moved_refs = [r for r in refs if r.get('asset_type') == 'OVERLAY_VFX']
    for r in moved_refs:
        if r.get('label') not in label_to_dep:
            fail(f'OVERLAY_VFX reference {r} does not belong to a reclassified treatment')
    m['unresolved_tbd_references'] = [r for r in refs if r.get('asset_type') != 'OVERLAY_VFX']

    # 3. tag per-shot overlay entries (creative text verbatim) and annotate S028 audio decision
    tagged = []
    tid_by_dep = {t[1]: t[0] for t in TREATMENTS}
    for e in m['shot_plans']:
        p, was_str = load_plan(e)
        for o in p['overlay_vfx_requirements']:
            if o.get('asset_id') == 'TBD' and o.get('element') in label_to_dep:
                dep = label_to_dep[o['element']]
                o['original_asset_id'], o['original_asset_status'] = o['asset_id'], o['asset_status']
                o['asset_id'], o['asset_status'] = tid_by_dep[dep], 'COMPOSITING_TREATMENT'
                o['requirement_class'] = 'COMPOSITING_TREATMENT_NOT_AN_ASSET'
                tagged.append((e['shot_id'], dep))
        if e['shot_id'] == 'S028':
            p['audio_plan']['human_decisions'] = [
                'FOLEY_TOUCH dropped (EP005_TBD_CLEANUP_v1): no shoulder-pat sound asset; the visual shoulder-pat action is unchanged; '
                'cloth handling remains under FOLEY_CLOTH; quiet ambience remains under AMBIENCE.']
        e['shot_plan'] = json.dumps(p) if was_str else p

    # 4. structured treatment section (shot attribution + verbatim instructions)
    sp = {e['shot_id']: load_plan(e)[0] for e in m['shot_plans']}
    treatments = []
    for tid, dep_label, decision, handling in TREATMENTS:
        dep = moved[dep_label]
        shots = dep['affected_shots']
        per_shot = []
        for s in shots:
            entries = [o for o in sp[s]['overlay_vfx_requirements'] if o.get('asset_id') == tid]
            if not entries:
                fail(f'{tid}: no shot instruction found in {s}')
            per_shot += [{'shot_id': s, 'element': o['element'], 'usage': o['usage'], 'overlay_role': o.get('overlay_role')} for o in entries]
        treatments.append({'treatment_id': tid, 'source_dependency': dep_label, 'classification': 'COMPOSITING_TREATMENT_NOT_AN_ASSET',
                           'human_decision': decision, 'handling': handling, 'affected_shots': shots,
                           'source_labels': dep.get('source_labels', []), 'shot_instructions': per_shot,
                           'agent007_eligible': False, 'paid_generation_required': False,
                           'original_dependency_entry': dep})
    m['compositing_treatments'] = treatments
    m['dropped_requirements'] = [{'requirement': f'TBD::AUDIO::{DROP_AUDIO}', 'human_decision': DECISIONS[DROP_AUDIO],
                                  'original_dependency_entry': dropped_audio[0]}]

    # 5. counts
    m['visual_tbd_dependency_count'] = sum(1 for d in m['unique_tbd_asset_dependencies'] if d.get('dependency_type') == 'VISUAL')
    m['audio_tbd_dependency_count'] = len(m['audio_tbd_dependencies'])
    m['unique_tbd_asset_dependency_count'] = len(m['unique_tbd_asset_dependencies'])
    m['audio_tbd_reference_count'] = sum(d.get('reference_count', 0) for d in m['audio_tbd_dependencies'])
    m['manifest_version'] = f"{m0.get('manifest_version')}+tbd-cleanup-1"
    m['derivation'] = {
        'transform': 'EP005_TBD_CLEANUP_v1 (deterministic, no LLM)',
        'derived_from_manifest_id': SOURCE_ID, 'derived_from_production_plan_run_id': SOURCE_RUN,
        'informed_by_agent006_run': SOURCE_A006_RUN, 'informed_by_readiness_manifest': SOURCE_READINESS,
        'human_decisions_applied': DECISIONS,
        'visual_treatment_reclassification': [t[0] + ' <- ' + t[1] for t in TREATMENTS],
        'dropped': [f'TBD::AUDIO::{DROP_AUDIO}'],
        'unresolved_audio_remaining': KEEP_AUDIO,
        'approval': 'derived row created REVIEW; requires separate human manifest approval before any Agent-006 use',
        'previous_derivation': m0.get('derivation'),
    }

    # 6. invariants
    vis = [d['dependency'] for d in m['unique_tbd_asset_dependencies'] if d.get('dependency_type') == 'VISUAL']
    aud = [d['audio_category'] for d in m['audio_tbd_dependencies']]
    aud_u = [d['audio_category'] for d in m['unique_tbd_asset_dependencies'] if d.get('dependency_type') == 'AUDIO']
    if sorted(vis) != sorted(KEEP_VISUAL): fail(f'visual TBDs left {vis}')
    if aud != KEEP_AUDIO or aud_u != KEEP_AUDIO: fail(f'audio TBDs left {aud} / {aud_u}')
    if len(moved_refs) != 10 or len(tagged) != 10: fail(f'expected 10 treatment references/entries, got {len(moved_refs)}/{len(tagged)}')
    if sorted((r['shot_id'], label_to_dep[r['label']]) for r in moved_refs) != sorted(tagged): fail('reference/shot-entry attribution mismatch')
    for t in treatments:
        if sorted({x['shot_id'] for x in t['shot_instructions']}) != sorted(t['affected_shots']): fail(f'{t["treatment_id"]} shot attribution lost')
    for k in ('source_approved_assets', 'asset_inventory', 'unique_new_assets', 'unique_reused_assets', 'episode', 'shot_queue',
              'generation_workload', 'audio_workload', 'production_phases', 'paid_generation_summary', 'production_optimization', 'source_fidelity'):
        if m.get(k) != m0.get(k): fail(f'{k} changed')
    for e0, e1 in zip(m0['shot_plans'], m['shot_plans']):
        p0, p1 = load_plan(e0)[0], copy.deepcopy(load_plan(e1)[0])
        if {k: v for k, v in e0.items() if k != 'shot_plan'} != {k: v for k, v in e1.items() if k != 'shot_plan'}: fail('shot entry changed')
        for o in p1['overlay_vfx_requirements']:
            if 'original_asset_id' in o:
                o['asset_id'], o['asset_status'] = o.pop('original_asset_id'), o.pop('original_asset_status'); o.pop('requirement_class')
        p1['audio_plan'].pop('human_decisions', None)
        if p0 != p1: fail(f'{e0["shot_id"]} shot plan changed beyond the approved tags')
    s = json.dumps(m['unique_tbd_asset_dependencies'] + m['audio_tbd_dependencies'] + m['unresolved_tbd_references'])
    if DROP_AUDIO in s or any(l in s for l in labels): fail('dropped/reclassified item still in a requirement list')

    row = {k: v for k, v in src.items() if k not in ('id', 'created_at')}
    row.update({'manifest_json': m, 'production_plan_run_id': DERIVED_RUN, 'status': 'REVIEW',
                'tbd_asset_reference_count': len(m['unresolved_tbd_references']),
                'agent_version': 'manifest-derivation-ep005-tbd-cleanup-v1'})
    return row, treatments


if __name__ == '__main__':
    src = json.load(open(sys.argv[1]))
    src = src[0] if isinstance(src, list) else src
    row, tr = derive(src)
    json.dump(row, open(sys.argv[2], 'w'), indent=1, ensure_ascii=False, sort_keys=True)
    m = row['manifest_json']
    print('INVARIANTS: PASS')
    print('visual TBD deps:', m['visual_tbd_dependency_count'], '| audio TBD deps:', m['audio_tbd_dependency_count'],
          '| unique TBD deps:', m['unique_tbd_asset_dependency_count'], '| audio refs:', m['audio_tbd_reference_count'],
          '| unresolved refs:', row['tbd_asset_reference_count'])
    for t in tr:
        print(t['treatment_id'], t['affected_shots'], len(t['shot_instructions']), 'instructions')
