#!/usr/bin/env python3
"""EP005_BERRY_REQUIREMENT_SPLIT_v1 - deterministic, LLM-free derivation of a corrected EP005
production manifest from the approved source manifest 670b201b (which is never modified).

Splits the combined Agent-004 asset TMP_EP005_BERRY_SMUDGE_OVERLAYS into three requirements whose
identity is the already-registered APPROVED asset_registry row. Shot attribution is taken ONLY from
shot_plans[].shot_plan.continuity_state.tracked_elements (visible_at_start OR visible_at_end).
Free text is never parsed; the two legacy free-text production_order_notes are left verbatim.

Usage: ep005_berry_requirement_split_v1.py <source_row.json> <derived_row_out.json>
  source_row.json = PostgREST GET of episode_production_manifests?id=eq.670b201b-...&select=*
Approved by Company Brain (EP005 berry requirement repair design). Fails closed on any invariant breach.
"""
import copy, json, sys

SOURCE_ID = '670b201b-6793-4518-ad5a-d051eb98d90c'
SOURCE_RUN = 'A005O-1790400144423'
DERIVED_RUN = 'DRV-EP005-BERRY-SPLIT-1-A005O-1790400144423'
OLD = 'TMP_EP005_BERRY_SMUDGE_OVERLAYS'
MARKS = [  # (registry asset_id, exact continuity element label, removal shot, expected shots)
    ('OVERLAY-EP005-BERRY-SMUDGE-CHEEK-v01', "Berry smudge on Mikko's anatomical left cheek", 'S009', [f'S{i:03d}' for i in range(1, 10)]),
    ('OVERLAY-EP005-BERRY-SMUDGE-MOUTH-v01', "Berry smudge on skin beside Mikko's mouth", 'S015', [f'S{i:03d}' for i in range(1, 16)]),
    ('OVERLAY-EP005-BERRY-SMUDGE-NOSE-v01', "Berry smudge on Mikko's nose", 'S021', [f'S{i:03d}' for i in range(1, 22)]),
]
EXPECTED_GAP_FILLS = {('S013', 'OVERLAY-EP005-BERRY-SMUDGE-NOSE-v01')}  # approved: S013 nose entry from continuity


def fail(msg):
    sys.exit(f'FAIL_CLOSED: {msg}')


def canon(s):
    return str(s or '').replace('’', "'").strip()


def load_plan(entry):
    p = entry['shot_plan']
    return (json.loads(p), True) if isinstance(p, str) else (p, False)


def derive(src):
    if src.get('id') != SOURCE_ID or src.get('status') != 'APPROVED' or src.get('production_plan_run_id') != SOURCE_RUN:
        fail('source row is not the approved 670b201b / A005O-1790400144423 manifest')
    m0 = src['manifest_json']
    m0 = json.loads(m0) if isinstance(m0, str) else m0
    m = copy.deepcopy(m0)
    lab2id = {canon(l): a for a, l, _, _ in MARKS}
    ids = [a for a, _, _, _ in MARKS]
    ops = []

    # 1. per-mark shot attribution from structured continuity only
    vis = {a: [] for a in ids}
    for e in m['shot_plans']:
        p, _ = load_plan(e)
        te = {canon(t['element']): t for t in p['continuity_state']['tracked_elements']}
        for a, l, _, _ in MARKS:
            t = te.get(canon(l))
            if t is None:
                fail(f'{e["shot_id"]} missing tracked element {l}')
            if t['visible_at_start'] or t['visible_at_end']:
                vis[a].append(e['shot_id'])
    inv0 = [i for i in m0['asset_inventory'] if i['asset_id'] == OLD]
    if len(inv0) != 1:
        fail('expected exactly one combined berry inventory entry')
    for a, l, rm, exp in MARKS:
        if vis[a] != exp:
            fail(f'{a} shots {vis[a]} != approved {exp}')
        last = [e for e in m['shot_plans'] if e['shot_id'] == rm][0]
        p, _ = load_plan(last)
        t = [x for x in p['continuity_state']['tracked_elements'] if canon(x['element']) == canon(l)][0]
        if not (t['visible_at_start'] and not t['visible_at_end']):
            fail(f'{a} removal shot {rm} is not visible_at_start=true/visible_at_end=false')
    if sorted(set().union(*map(set, vis.values()))) != sorted(inv0[0]['used_in_shots']):
        fail('union of per-mark shots != original combined used_in_shots')

    # 2. per-shot overlay entries: retag specific, expand generic, fill continuity gaps
    gap_fills = set()
    for e in m['shot_plans']:
        p, was_str = load_plan(e)
        sid = e['shot_id']
        new, berry_src = [], []
        for o in p['overlay_vfx_requirements']:
            if o.get('asset_id') != OLD:
                new.append(o)
                continue
            berry_src.append(o)
            if canon(o.get('element')) in lab2id:
                aid = lab2id[canon(o['element'])]
                new.append(dict(o, asset_id=aid))
                ops.append((sid, 'RETAG', aid))
            else:
                for a, l, _, _ in MARKS:
                    if sid in vis[a]:
                        new.append(dict(o, element=l, asset_id=a, derived_from_element=o.get('element')))
                        ops.append((sid, 'EXPAND', a))
        present = {o.get('asset_id') for o in new}
        for a, l, _, _ in MARKS:
            if sid in vis[a] and a not in present:
                if not berry_src:
                    fail(f'{sid} needs {a} but has no berry overlay entry to derive from')
                b = berry_src[0]
                new.append({'usage': b.get('usage'), 'element': l, 'asset_id': a,
                            'asset_status': b.get('asset_status'), 'overlay_role': b.get('overlay_role'),
                            'derived_from': 'continuity_state.tracked_elements (EP005_BERRY_REQUIREMENT_SPLIT_v1)'})
                gap_fills.add((sid, a))
                ops.append((sid, 'GAP_FILL', a))
        p['overlay_vfx_requirements'] = new
        e['shot_plan'] = json.dumps(p) if was_str else p
    if gap_fills != EXPECTED_GAP_FILLS:
        fail(f'continuity gap fills {sorted(gap_fills)} != approved {sorted(EXPECTED_GAP_FILLS)}')

    # 3. asset lists
    def split_inv(item):
        return [{'labels': [l], 'asset_id': a, 'asset_types': item['asset_types'], 'asset_status': item['asset_status'],
                 'used_in_shots': vis[a], 'derived_from_asset_id': OLD} for a, l, _, _ in MARKS]
    for key in ('asset_inventory', 'unique_new_assets'):
        out = []
        for it in m[key]:
            out += split_inv(it) if it.get('asset_id') == OLD else [it]
        m[key] = out

    def splice(lst):
        i = lst.index(OLD)
        return lst[:i] + ids + lst[i + 1:]
    m['source_approved_assets']['unique_new_asset_ids'] = splice(m['source_approved_assets']['unique_new_asset_ids'])
    for ph in m.get('production_phases', []):
        if OLD in ph.get('asset_ids', []):
            ph['asset_ids'] = splice(ph['asset_ids'])

    m['manifest_version'] = f"{m0.get('manifest_version')}+berry-split-1"
    m['derivation'] = {
        'transform': 'EP005_BERRY_REQUIREMENT_SPLIT_v1 (deterministic, no LLM)',
        'derived_from_manifest_id': SOURCE_ID,
        'derived_from_production_plan_run_id': SOURCE_RUN,
        'split': {OLD: ids},
        'shot_attribution_source': 'shot_plans[].shot_plan.continuity_state.tracked_elements (visible_at_start OR visible_at_end)',
        'continuity_gap_fills': [f'{s}:{a}' for s, a in sorted(gap_fills)],
        'free_text_note': 'two legacy production_order_notes (S002 shot_plan + shot_queue) mention the combined ID verbatim; intentionally unchanged',
        'approval': 'derived row created REVIEW; requires separate human manifest approval before any Agent-006 use',
    }

    # invariants on output
    s = json.dumps(m)
    structured_old = sum(1 for _ in [0] for e in m['shot_plans'] for o in load_plan(e)[0]['overlay_vfx_requirements'] if o.get('asset_id') == OLD)
    if structured_old or OLD in m['source_approved_assets']['unique_new_asset_ids'] or any(i['asset_id'] == OLD for i in m['asset_inventory'] + m['unique_new_assets']):
        fail('combined ID still present in a structured asset field')
    for e in m['shot_plans']:
        p, _ = load_plan(e)
        aids = [o.get('asset_id') for o in p['overlay_vfx_requirements'] if o.get('asset_id') in ids]
        if len(aids) != len(set(aids)):
            fail(f'{e["shot_id"]} duplicate berry overlay entries')
        if sorted(aids) != sorted(a for a in ids if e['shot_id'] in vis[a]):
            fail(f'{e["shot_id"]} overlay entries {aids} do not match continuity')

    row = {k: v for k, v in src.items() if k not in ('id', 'created_at')}
    row.update({'manifest_json': m, 'production_plan_run_id': DERIVED_RUN, 'unique_new_asset_count': 5,
                'status': 'REVIEW', 'agent_version': 'manifest-derivation-ep005-berry-split-v1'})
    return row, vis, ops


if __name__ == '__main__':
    src = json.load(open(sys.argv[1]))
    src = src[0] if isinstance(src, list) else src
    row, vis, ops = derive(src)
    json.dump(row, open(sys.argv[2], 'w'), indent=1, ensure_ascii=False, sort_keys=True)
    from collections import Counter
    print('INVARIANTS: PASS')
    print('overlay ops:', dict(Counter(o for _, o, _ in ops)))
    print('gap fills:', [(s, a) for s, o, a in ops if o == 'GAP_FILL'])
    for a in vis:
        print(a, len(vis[a]), vis[a][0], '..', vis[a][-1])
