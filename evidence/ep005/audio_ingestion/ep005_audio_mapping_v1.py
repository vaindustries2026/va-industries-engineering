#!/usr/bin/env python3
"""EP005_AUDIO_MAPPING_v1 - deterministic, LLM-free derivation of the audio-mapped EP005 manifest from the APPROVED manifest 96df250f
(never modified). Replaces the three generic unresolved audio TBD requirements with exact approved registry assets:
  TBD::AUDIO::AMBIENCE       -> AMB-BATHROOM-QUIET-v01
  TBD::AUDIO::FOLEY_CLOTH    -> FOLEY-CLOTH-SOFT-v01
  TBD::AUDIO::COMPLETION_SFX -> SFX-COMPLETION-POP-v01
They become APPROVED_REUSE requirements (the same path the three approved SFX use), keyed by exact asset_id; shots come from the original
audio TBD shot lists. Nothing else changes (11 existing reusable requirements, visual/compositing decisions, dropped FOLEY_TOUCH, shot plans).
Usage: ep005_audio_mapping_v1.py <source_row.json> <registry_rows.json> <derived_row_out.json> <diff_out.json>
Fails closed on any invariant breach."""
import copy, hashlib, json, sys

SOURCE_ID = '96df250f-7182-4d5f-a556-b0448e518375'
SOURCE_RUN = 'DRV-EP005-TBD-CLEANUP-1-A005O-1790400144423'
DERIVED_RUN = 'DRV-EP005-AUDIO-MAPPED-1-A005O-1790400144423'
MAP = [('AMBIENCE', 'AMB-BATHROOM-QUIET-v01', 20), ('FOLEY_CLOTH', 'FOLEY-CLOTH-SOFT-v01', 7), ('COMPLETION_SFX', 'SFX-COMPLETION-POP-v01', 1)]
ALLOWED_TOP = {'source_approved_assets', 'unique_reused_assets', 'asset_inventory', 'unique_tbd_asset_dependencies', 'audio_tbd_dependencies',
               'unique_tbd_asset_dependency_count', 'audio_tbd_dependency_count', 'audio_tbd_reference_count', 'manifest_version', 'derivation', 'audio_asset_mappings'}

def fail(m): sys.exit(f'FAIL_CLOSED: {m}')
def canon(o): return hashlib.sha256(json.dumps(o, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()

def diff(a, b, path='$'):
    out = []
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a: out.append({'path': f'{path}.{k}', 'op': 'added', 'after': b[k]})
            elif k not in b: out.append({'path': f'{path}.{k}', 'op': 'removed', 'before': a[k]})
            else: out += diff(a[k], b[k], f'{path}.{k}')
    elif isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        for i, (x, y) in enumerate(zip(a, b)): out += diff(x, y, f'{path}[{i}]')
    elif a != b:
        out.append({'path': path, 'op': 'changed', 'before': a, 'after': b})
    return out

def derive(src, regrows):
    if src.get('id') != SOURCE_ID or src.get('status') != 'APPROVED' or src.get('production_plan_run_id') != SOURCE_RUN:
        fail('source is not the APPROVED manifest 96df250f')
    reg = {r['asset_id']: r for r in regrows}
    for _, aid, _ in MAP:
        r = reg.get(aid)
        if not r or r['status'] != 'APPROVED' or r['asset_type'] != 'AUDIO': fail(f'registry row for {aid} missing or not APPROVED AUDIO')
        if r['aliases']: fail(f'{aid} must have no aliases')
    m0 = src['manifest_json']; m0 = json.loads(m0) if isinstance(m0, str) else m0; m = copy.deepcopy(m0)

    adeps = {d['audio_category']: d for d in m['audio_tbd_dependencies']}
    if set(adeps) != {c for c, _, _ in MAP}: fail(f'unexpected audio TBDs {sorted(adeps)}')
    if 'FOLEY_TOUCH' in json.dumps(m['audio_tbd_dependencies'] + m['unique_tbd_asset_dependencies']): fail('FOLEY_TOUCH present in requirement lists')
    for cat, aid, n in MAP:
        if adeps[cat]['shot_count'] != n or len(adeps[cat]['shots']) != n: fail(f'{cat} shot count != {n}')
    udeps = [d for d in m['unique_tbd_asset_dependencies'] if d.get('dependency_type') == 'AUDIO']
    if sorted(d['audio_category'] for d in udeps) != sorted(adeps): fail('audio entries in unique_tbd_asset_dependencies do not match audio_tbd_dependencies')
    before_visual = [d for d in m['unique_tbd_asset_dependencies'] if d.get('dependency_type') != 'AUDIO']
    if sorted(d['dependency'] for d in before_visual) != sorted(['Lumi', 'Mikko', 'Canonical environment/background']): fail('visual TBD set changed')

    # replace the 3 generic audio TBDs with exact reuse mappings
    new_entries = []
    for cat, aid, n in MAP:
        new_entries.append({'labels': [reg[aid]['asset_name']], 'asset_id': aid, 'asset_types': ['SOURCE_APPROVED_ASSET', 'AUDIO'], 'asset_status': 'REUSE',
                            'used_in_shots': list(adeps[cat]['shots']), 'mapped_from_audio_tbd': f'TBD::AUDIO::{cat}'})
    m['unique_tbd_asset_dependencies'] = before_visual
    m['audio_tbd_dependencies'] = []
    m['unique_tbd_asset_dependency_count'] = len(before_visual)
    m['audio_tbd_dependency_count'] = 0
    m['audio_tbd_reference_count'] = 0
    m['source_approved_assets']['unique_reused_asset_ids'] = m['source_approved_assets']['unique_reused_asset_ids'] + [aid for _, aid, _ in MAP]
    m['unique_reused_assets'] = m['unique_reused_assets'] + copy.deepcopy(new_entries)
    m['asset_inventory'] = m['asset_inventory'] + copy.deepcopy(new_entries)
    m['audio_asset_mappings'] = [{'replaces_requirement': f'TBD::AUDIO::{cat}', 'new_requirement_key': f'APPROVED_REUSE::{aid}', 'asset_id': aid,
        'shots': list(adeps[cat]['shots']), 'storage_path': reg[aid]['storage_path'], 'sha256': reg[aid]['metadata_json']['sha256'],
        'source_generation_id': reg[aid]['metadata_json']['source_generation_id'], 'original_dependency_entry': adeps[cat]} for cat, aid, _ in MAP]
    m['manifest_version'] = f"{m0.get('manifest_version')}+audio-mapped-1"
    m['derivation'] = {
        'transform': 'EP005_AUDIO_MAPPING_v1 (deterministic, no LLM)', 'derived_from_manifest_id': SOURCE_ID, 'derived_from_production_plan_run_id': SOURCE_RUN,
        'human_decision': 'Gilang approved the three mastered ElevenLabs EP005 audio files (ambience C, cloth C, pop A) on 2026-10-07 and the mapping of the three generic audio TBD requirements to exact approved assets',
        'mapping': {f'TBD::AUDIO::{c}': a for c, a, _ in MAP}, 'unchanged': 'the 11 existing reusable requirements, visual/compositing treatment decisions, dropped FOLEY_TOUCH, all shot plans and assignments',
        'approval': 'derived row created REVIEW; requires separate human manifest approval before any Agent-006 use', 'previous_derivation': m0.get('derivation')}

    changed_top = {k for k in set(m0) | set(m) if m0.get(k) != m.get(k)}
    if not changed_top <= ALLOWED_TOP: fail(f'unexpected top-level changes: {sorted(changed_top - ALLOWED_TOP)}')
    sa0, sa1 = copy.deepcopy(m0['source_approved_assets']), copy.deepcopy(m['source_approved_assets'])
    sa0.pop('unique_reused_asset_ids'); sa1.pop('unique_reused_asset_ids')
    if sa0 != sa1: fail('source_approved_assets changed beyond unique_reused_asset_ids')
    if m['shot_plans'] != m0['shot_plans'] or m['compositing_treatments'] != m0['compositing_treatments'] or m['dropped_requirements'] != m0['dropped_requirements'] \
       or m['unresolved_tbd_references'] != m0['unresolved_tbd_references'] or m['unique_new_assets'] != m0['unique_new_assets']: fail('protected section changed')
    if any('TBD::AUDIO' in json.dumps(x) or x.get('dependency_type') == 'AUDIO' for x in m['unique_tbd_asset_dependencies'] + m['audio_tbd_dependencies']): fail('audio TBD requirement remains')
    ids = [e['asset_id'] for e in m['asset_inventory']]
    if len(ids) != len(set(ids)): fail('duplicate asset ids in inventory')

    row = {k: v for k, v in src.items() if k not in ('id', 'created_at')}
    row.update({'manifest_json': m, 'production_plan_run_id': DERIVED_RUN, 'status': 'REVIEW', 'unique_reused_asset_count': 6, 'agent_version': 'manifest-derivation-ep005-audio-mapped-v1'})
    mdiff = diff(m0, m); rowdiff = {k: {'before': src[k], 'after': row[k]} for k in row if k != 'manifest_json' and src.get(k) != row[k]}
    return row, {'source_manifest_id': SOURCE_ID, 'source_canonical_sha256': canon(m0), 'derived_canonical_sha256': canon(m),
                 'row_column_changes': rowdiff, 'manifest_json_changes': mdiff, 'changed_top_level_keys': sorted(changed_top)}

if __name__ == '__main__':
    src = json.load(open(sys.argv[1])); src = src[0] if isinstance(src, list) else src
    row, d = derive(src, json.load(open(sys.argv[2])))
    json.dump(row, open(sys.argv[3], 'w'), indent=1, ensure_ascii=False, sort_keys=True); json.dump(d, open(sys.argv[4], 'w'), indent=1, ensure_ascii=False)
    print('INVARIANTS: PASS'); print('changed top-level keys:', d['changed_top_level_keys']); print('row column changes:', {k: (v['before'], v['after']) for k, v in d['row_column_changes'].items()})
    print('source canonical sha256 :', d['source_canonical_sha256']); print('derived canonical sha256:', d['derived_canonical_sha256']); print('manifest_json diff entries:', len(d['manifest_json_changes']))
