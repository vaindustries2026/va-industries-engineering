#!/usr/bin/env python3
"""EP005 script v05 + derived manifest: deterministic, LLM-free application of the Company-Brain-approved
Alternative B wording (S004 / S012 / S018) to the APPROVED script v02 and the APPROVED manifest 45cc7493.
Neither parent is modified. Fails closed on any invariant breach.

v05 = the amendment planned as "v03" in Batch 0C/0D; v03/v04 numbers are taken by older unrelated REVIEW drafts
(6b14e140, b5567e13) and UNIQUE(episode_code, script_version_number) forbids reuse (human decision 2026-10-11).

Usage:
  derive_v05_lineage.py script  <v02_row.json> <v05_row_out.json> <diff_out.json>
  derive_v05_lineage.py manifest <m45_row.json> <v05_script_row_readback.json> <manifest_row_out.json> <diff_out.json>
"""
import copy
import hashlib
import json
import sys

V02_ID = '14471926-f6fb-4bba-b355-109f3ae9e21c'
M45_ID = '45cc7493-80b4-4e8d-b71d-fbd7fd3656ed'
M45_RUN = 'DRV-EP005-AUDIO-MAPPED-1-A005O-1790400144423'
V05_RUN = 'AMD-EP005-SCRIPT-V05-ALTB-1-FROM-A004-1788849454482'
M_RUN = 'DRV-EP005-SCRIPT-V05-ALTB-1-A005O-1790400144423'
AUTH = ('Company Brain approved the exact Alternative B wording for S004/S012/S018 (Gilang instruction 2026-10-11, '
        'EP005 SCRIPT V03 GOVERNANCE + S028 BASE FRAME PREFLIGHT); version v05 and lineage placement per human answers 2026-10-11')
OLD_RITUAL, NEW_RITUAL = 'Lumi: “Can you help Mikko find the next berry smudge?”', 'Lumi: “Find the next smudge!”'
LINES = {  # shot index -> (shot_id, old line 1, new line 1)
    3: ('S004', 'Lumi: “A little glint! Look at his cheek.”', 'Lumi: “A glint on his cheek!”'),
    11: ('S012', 'Lumi: “I see a spot near your mouth.”', 'Lumi: “By your mouth!”'),
    17: ('S018', 'Lumi: “One tiny spot is still here.”', 'Lumi: “One spot left!”'),
}
# Part 1 classification: the DERIVED_ACTIVE_FIELD copies inside architecture_json (exact substring replacements).
ARCH = [
    (['cue', 'lumi_notice'], '“A little glint! Look at his cheek.”', '“A glint on his cheek!”'),
    (['cue', 'child_prompt'], OLD_RITUAL, NEW_RITUAL),
    (['three', 1, 'lumi_line'], '“I see a spot near your mouth.”', '“By your mouth!”'),
    (['three', 1, 'child_prompt'], OLD_RITUAL, NEW_RITUAL),
    (['three', 2, 'lumi_line'], '“One tiny spot is still here.”', '“One spot left!”'),
    (['three', 2, 'child_prompt'], OLD_RITUAL, NEW_RITUAL),
    (['character_voice_check', 'lumi'], '“I see a spot near your mouth”', '“By your mouth!”'),
]
OLD_FRAGMENTS = ['A little glint! Look at his cheek', 'I see a spot near your mouth', 'One tiny spot is still here',
                 'Can you help Mikko find the next berry smudge']


def fail(m):
    sys.exit(f'FAIL_CLOSED: {m}')


def canon(o):
    return hashlib.sha256(json.dumps(o, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()


def diff(a, b, path='$'):
    out = []
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b), key=str):
            if k not in a:
                out.append({'path': f'{path}.{k}', 'op': 'added', 'after': b[k]})
            elif k not in b:
                out.append({'path': f'{path}.{k}', 'op': 'removed', 'before': a[k]})
            else:
                out += diff(a[k], b[k], f'{path}.{k}')
    elif isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        for i, (x, y) in enumerate(zip(a, b)):
            out += diff(x, y, f'{path}[{i}]')
    elif a != b:
        out.append({'path': path, 'op': 'changed', 'before': a, 'after': b})
    return out


def at(o, path):
    for p in path[:-1]:
        o = o[p]
    return o, path[-1]


def replace_once(o, path, old, new):
    parent, key = at(o, path)
    if parent[key].count(old) != 1:
        fail(f'{path}: expected exactly one "{old}", found {parent[key].count(old)}')
    parent[key] = parent[key].replace(old, new)


def no_old_fragments(obj, where, allow=()):
    s = json.dumps(obj, ensure_ascii=False)
    for f in OLD_FRAGMENTS:
        n = s.count(f) - sum(a.count(f) for a in allow)
        if n:
            fail(f'{where}: {n} stale occurrence(s) of "{f}"')


def derive_script(v2):
    if v2.get('id') != V02_ID or v2.get('status') != 'APPROVED' or v2.get('script_version') != 'v02':
        fail('parent is not the APPROVED script v02 14471926')
    p0, a0 = v2['production_script_json'], v2['architecture_json']
    p, a = copy.deepcopy(p0), copy.deepcopy(a0)
    changes = []
    for i, (sid, old1, new1) in LINES.items():
        sh = p['shots'][i]
        if sh.get('shot_id') != sid or sh['dialogue_lyric'] != old1 or sh['child_prompt'] != OLD_RITUAL:
            fail(f'{sid}: parent lines are not the authoritative v02 lines')
        sh['dialogue_lyric'], sh['child_prompt'] = new1, NEW_RITUAL
        changes += [{'shot_id': sid, 'field': f'production_script_json.shots[{i}].dialogue_lyric', 'old': old1, 'new': new1},
                    {'shot_id': sid, 'field': f'production_script_json.shots[{i}].child_prompt', 'old': OLD_RITUAL, 'new': NEW_RITUAL}]
    for path, old, new in ARCH:
        replace_once(a, path, old, new)
    p['lineage'] = {
        'parent_script_id': V02_ID, 'parent_script_version': 'v02', 'parent_status': 'APPROVED (immutable)',
        'parent_production_script_json_canonical_sha256': canon(p0), 'parent_architecture_json_canonical_sha256': canon(a0),
        'transform': 'EP005_SCRIPT_V05_ALTB_v1 (deterministic, no LLM)', 'reason': 'TIMING_FIT (Alternative B)',
        'authority': AUTH, 'dialogue_changes': changes,
        'architecture_json_changes': [{'path': pa, 'old': o, 'new': n} for pa, o, n in ARCH],
        'unchanged': 'all other shots, timing, characterisation, structure, treatments, asset requirements, voices; '
                     'approved_episode_snapshot (HISTORICAL_PROVENANCE_SNAPSHOT of episode_backlog 07d622e9)',
        'version_note': 'planned as "v03" in Batch 0C/0D; v03/v04 numbers belong to older REVIEW drafts 6b14e140/b5567e13'}
    # invariants
    if len(p['shots']) != len(p0['shots']) or len(p['shots']) != 29:
        fail('shot count changed')
    for i, (x, y) in enumerate(zip(p0['shots'], p['shots'])):
        if i not in LINES and x != y:
            fail(f'unrelated shot {i} changed')
        if i in LINES:
            dx = {k for k in set(x) | set(y) if x.get(k) != y.get(k)}
            if dx != {'dialogue_lyric', 'child_prompt'}:
                fail(f'shot {i}: unexpected fields changed {sorted(dx)}')
    if {k for k in set(p0) | set(p) if p0.get(k) != p.get(k)} != {'shots', 'lineage'}:
        fail('production_script_json top-level change beyond shots + lineage')
    if len(diff(a0, a)) != len(ARCH):
        fail('architecture_json changed beyond the classified fields')
    no_old_fragments(p['shots'], 'v05 production shots')
    no_old_fragments(a, 'v05 architecture_json')
    row = {k: v for k, v in v2.items() if k not in ('id', 'created_at')}
    row.update({'script_version': 'v05', 'script_version_number': 5, 'script_run_id': V05_RUN,
                'title_working': 'EP-CANDIDATE-005 v05 — Three Gentle Wipes', 'status': 'REVIEW',
                'agent_version': 'script-amendment-ep005-altb-v1', 'production_script_json': p, 'architecture_json': a})
    if row['approved_episode_snapshot'] != v2['approved_episode_snapshot']:
        fail('approved_episode_snapshot changed')
    rowdiff = {k: {'before': v2[k], 'after': row[k]} for k in row
               if k not in ('production_script_json', 'architecture_json') and v2.get(k) != row[k]}
    return row, {'parent_script_id': V02_ID, 'row_column_changes': rowdiff,
                 'production_script_json_changes': diff(p0, p), 'architecture_json_changes': diff(a0, a),
                 'parent_production_script_json_canonical_sha256': canon(p0),
                 'v05_production_script_json_canonical_sha256': canon(p),
                 'v05_architecture_json_canonical_sha256': canon(a), 'S027_script_entry_canonical_sha256': canon(p['shots'][26])}


ALLOWED_TOP = {'shot_plans', 'episode', 'manifest_version', 'derivation'}


def derive_manifest(src, v5):
    if src.get('id') != M45_ID or src.get('status') != 'APPROVED' or src.get('production_plan_run_id') != M45_RUN:
        fail('source is not the APPROVED manifest 45cc7493')
    if v5.get('script_version') != 'v05' or v5['production_script_json']['lineage']['parent_script_id'] != V02_ID \
            or src.get('episode_script_id') != V02_ID:
        fail('v05 script lineage does not match the manifest parent')
    m0 = src['manifest_json']
    m = copy.deepcopy(m0)
    changes = []
    for i, (sid, old1, new1) in LINES.items():
        sp = m['shot_plans'][i]
        vl = sp['shot_plan']['audio_plan']['voice_lines']
        if sp['shot_id'] != sid or vl != [old1, OLD_RITUAL]:
            fail(f'{sid}: manifest voice_lines are not the authoritative v02 lines')
        sh = v5['production_script_json']['shots'][i]
        if [sh['dialogue_lyric'], sh['child_prompt']] != [new1, NEW_RITUAL]:
            fail(f'{sid}: v05 script lines differ from the approved wording')
        sp['shot_plan']['audio_plan']['voice_lines'] = [new1, NEW_RITUAL]
        changes += [{'shot_id': sid, 'path': f'manifest_json.shot_plans[{i}].shot_plan.audio_plan.voice_lines[0]', 'old': old1, 'new': new1},
                    {'shot_id': sid, 'path': f'manifest_json.shot_plans[{i}].shot_plan.audio_plan.voice_lines[1]', 'old': OLD_RITUAL, 'new': NEW_RITUAL}]
    m['episode'] = {**m0['episode'], 'script_version': 'v05', 'episode_script_id': v5['id'], 'title_working': v5['title_working']}
    m['manifest_version'] = f"{m0['manifest_version']}+script-v05-altb-1"
    m['derivation'] = {
        'transform': 'EP005_SCRIPT_V05_ALTB_MANIFEST_v1 (deterministic, no LLM)', 'derived_from_manifest_id': M45_ID,
        'derived_from_production_plan_run_id': M45_RUN, 'derived_from_script_id': v5['id'], 'parent_script_id': V02_ID,
        'human_decision': AUTH, 'dialogue_changes': changes,
        'unchanged': 'all asset requirements and inventories, audio_asset_mappings, compositing treatments, dropped requirements, '
                     'all other shot plans (incl. S027) and every non-dialogue field of S004/S012/S018',
        'approval': 'derived row created REVIEW; status-only approval after readback + local Agent-006 proof (human answer 2026-10-11)',
        'previous_derivation': m0.get('derivation')}
    changed_top = {k for k in set(m0) | set(m) if m0.get(k) != m.get(k)}
    if not changed_top <= ALLOWED_TOP:
        fail(f'unexpected top-level changes {sorted(changed_top - ALLOWED_TOP)}')
    for i, (x, y) in enumerate(zip(m0['shot_plans'], m['shot_plans'])):
        if i not in LINES and x != y:
            fail(f'unrelated shot plan {i} changed')
    dm = diff(m0['shot_plans'], m['shot_plans'])
    if len(dm) != 6 or not all('audio_plan.voice_lines' in d['path'] for d in dm):
        fail('shot_plans changed beyond the six voice lines')
    if len(m['shot_plans']) != 29:
        fail('shot count changed')
    end = max(s['shot_plan'].get('end_seconds', 0) if isinstance(s.get('shot_plan'), dict) else 0 for s in m['shot_plans'])
    no_old_fragments(m['shot_plans'], 'derived manifest shot_plans')
    row = {k: v for k, v in src.items() if k not in ('id', 'created_at')}
    row.update({'manifest_json': m, 'episode_script_id': v5['id'], 'script_version': 'v05', 'title_working': v5['title_working'],
                'production_plan_run_id': M_RUN, 'status': 'REVIEW', 'agent_version': 'manifest-derivation-ep005-v05-altb-v1'})
    rowdiff = {k: {'before': src[k], 'after': row[k]} for k in row if k != 'manifest_json' and src.get(k) != row[k]}
    return row, {'parent_manifest_id': M45_ID, 'source_canonical_sha256': canon(m0), 'derived_canonical_sha256': canon(m),
                 'row_column_changes': rowdiff, 'manifest_json_changes': diff(m0, m), 'changed_top_level_keys': sorted(changed_top),
                 'S027_shot_plan_canonical_sha256': canon(m['shot_plans'][26]), 'max_shot_plan_end_seconds': end}


if __name__ == '__main__':
    load = lambda p: (lambda x: x[0] if isinstance(x, list) else x)(json.load(open(p)))
    if sys.argv[1] == 'script':
        row, d = derive_script(load(sys.argv[2]))
        outs = sys.argv[3:5]
    elif sys.argv[1] == 'manifest':
        row, d = derive_manifest(load(sys.argv[2]), load(sys.argv[3]))
        outs = sys.argv[4:6]
    else:
        fail('mode must be script|manifest')
    json.dump(row, open(outs[0], 'w'), indent=1, ensure_ascii=False, sort_keys=True)
    json.dump(d, open(outs[1], 'w'), indent=1, ensure_ascii=False)
    print('INVARIANTS: PASS')
    print(json.dumps({k: v for k, v in d.items() if 'sha256' in k or k in ('changed_top_level_keys', 'max_shot_plan_end_seconds')},
                     ensure_ascii=False, indent=1))
