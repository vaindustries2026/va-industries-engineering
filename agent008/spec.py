"""Shot assembly specification: approved manifest + readiness + registry -> exact per-shot contract.

The spec is derived deterministically. It never reads asset identity from
stale shot-plan text (TMP_*, TBD); identities come from the readiness
canonical_reuse_map and the governed registry.
"""
import re

from .errors import FailClosed
from .resolve import is_stale_label
from .treatments import treatment

BERRY_PREFIX = 'Berry smudge'
TREATMENT_CLASS = 'COMPOSITING_TREATMENT_NOT_AN_ASSET'
SPEAKER_LINE = re.compile(r'^\s*([^:]+):\s*[“"](.*)[”"]\s*$')

# Future validation rules (encoded now, applied whenever these shots are specified).
CLEAN_REVEAL_SHOTS = {'S025'}


def _shot(manifest_reduced, shot_id):
    for s in manifest_reduced['shot_plans']:
        if s['shot_id'] == shot_id:
            return s
    raise FailClosed('SHOT_NOT_IN_MANIFEST', shot_id)


def _check_affected(resolver, reference, shot_id):
    """Cross-check: the readiness reuse map must list this shot for the reference."""
    for e in resolver.reuse_map:
        if reference in (e.get('source_asset_id'), e.get('source_label'), e.get('requirement_key')):
            if shot_id not in (e.get('affected_shots') or []):
                raise FailClosed('REUSE_MAP_SHOT_MISMATCH', f'{reference} not mapped for {shot_id}')
            return
    # exact registry ids used directly by the shot contract (overlays) are also in the map by source_asset_id


def parse_voice_line(line):
    m = SPEAKER_LINE.match(line)
    if not m:
        raise FailClosed('VOICE_LINE_UNPARSEABLE', line)
    return m.group(1).strip(), m.group(2).strip()


def build_shot_spec(snapshot, resolver, shot_id, output_spec):
    pm = snapshot['production_manifest']['manifest_json_reduced']
    s = _shot(pm, shot_id)
    plan = s['shot_plan']
    seconds = round(s['end_seconds'] - s['start_seconds'], 6)
    frames = output_spec.frames_for(seconds)

    # --- overlays and treatments from the exact shot contract ---
    req_overlays, req_treatments = {}, []
    for o in plan.get('overlay_vfx_requirements') or []:
        if o.get('requirement_class') == TREATMENT_CLASS or o.get('asset_status') == 'COMPOSITING_TREATMENT':
            req_treatments.append(o['asset_id'])
        else:
            req_overlays[o['element']] = o['asset_id']
    tracked = {t['element']: t for t in plan['continuity_state']['tracked_elements']}
    berries = {k: v for k, v in tracked.items() if k.startswith(BERRY_PREFIX)}
    active = []
    for element, t in sorted(berries.items()):
        if t['visible_at_start'] != t['visible_at_end']:
            raise FailClosed('OVERLAY_TRANSITION_UNSUPPORTED_V01', f'{shot_id}: {element}')
        if t['visible_at_start']:
            if element not in req_overlays:
                raise FailClosed('ACTIVE_OVERLAY_WITHOUT_CONTRACT', f'{shot_id}: {element}')
            active.append(element)
    for element in req_overlays:
        if element not in berries:
            raise FailClosed('OVERLAY_CONTRACT_WITHOUT_CONTINUITY', f'{shot_id}: {element}')
        if not berries[element]['visible_at_start']:
            raise FailClosed('OVERLAY_CONTRACT_FOR_INVISIBLE_ELEMENT', f'{shot_id}: {element}')
    overlays = []
    for element in active:
        ref = req_overlays[element]
        _check_affected(resolver, ref, shot_id)
        overlays.append({'element': element, **resolver.resolve(ref)})

    treatments = []
    for tid in req_treatments:
        ct = [c for c in pm.get('compositing_treatments') or [] if c['treatment_id'] == tid]
        if len(ct) != 1 or shot_id not in ct[0]['affected_shots']:
            raise FailClosed('TREATMENT_NOT_ASSIGNED_IN_MANIFEST', f'{shot_id}: {tid}')
        if ct[0].get('agent007_eligible') is not False or ct[0].get('paid_generation_required') is not False:
            raise FailClosed('TREATMENT_NOT_DETERMINISTIC', tid)
        treatment(tid)
        instr = [i for i in ct[0].get('shot_instructions') or [] if i['shot_id'] == shot_id]
        treatments.append({'treatment_id': tid, 'shot_instruction': instr[0]['usage'] if instr else None})
    for c in pm.get('compositing_treatments') or []:
        if shot_id in c['affected_shots'] and c['treatment_id'] not in req_treatments:
            raise FailClosed('TREATMENT_ASSIGNMENT_INCONSISTENT', f"{shot_id}: {c['treatment_id']}")

    # --- props, characters, environment via the canonical map only ---
    props = []
    for p in plan.get('prop_requirements') or []:
        _check_affected(resolver, p['asset_id'], shot_id)
        props.append({'manifest_label': p['asset_id'], 'label_is_stale': is_stale_label(p['asset_id']),
                      **resolver.resolve(p['asset_id'])})
    characters = []
    for c in plan.get('character_requirements') or []:
        key = f"TBD::CHARACTER::{c['character_name']}" if is_stale_label(c.get('asset_id')) else c['asset_id']
        _check_affected(resolver, key, shot_id)
        characters.append({'character_name': c['character_name'], 'manifest_label': c.get('asset_id'),
                           **resolver.resolve(key)})
    env = plan.get('environment_requirement') or {}
    env_key = 'TBD::ENVIRONMENT::Canonical environment/background' if is_stale_label(env.get('background_asset_id')) \
        else env['background_asset_id']
    _check_affected(resolver, env_key, shot_id)
    environment = {'manifest_label': env.get('background_asset_id'), **resolver.resolve(env_key)}

    # --- audio ---
    ap = plan['audio_plan']
    sfx = []
    for name in ap.get('named_audio_assets') or []:
        _check_affected(resolver, name, shot_id)
        sfx.append({'manifest_label': name, **resolver.resolve(name)})
    mapped_beds = []
    for mapping in pm.get('audio_asset_mappings') or []:
        if shot_id in mapping['shots']:
            mapped_beds.append({'replaces_requirement': mapping['replaces_requirement'],
                                **resolver.resolve(mapping['asset_id'])})
    dialogue = []
    for line in ap.get('voice_lines') or []:
        speaker, text = parse_voice_line(line)
        dialogue.append({'shot_id': shot_id, 'speaker': speaker, 'text': text, 'audio_asset_id': None,
                         'status': 'DEFERRED_NO_VOICE_ASSET'})
    holds = (pm.get('audio_workload') or {}).get('protected_participation_hold_shots') or []

    spec = {
        'shot_id': shot_id, 'shot_index': s['shot_index'],
        'episode_start_seconds': s['start_seconds'], 'episode_end_seconds': s['end_seconds'],
        'duration_seconds': seconds, 'frames': frames,
        'animation_method': plan['animation_plan']['method'],
        'video_generation_required': plan['animation_plan']['video_generation_required'],
        'protected_participation_hold': shot_id in holds,
        'clean_reveal': shot_id in CLEAN_REVEAL_SHOTS,
        'active_overlays': overlays, 'treatments': treatments,
        'props': props, 'characters': characters, 'environment': environment,
        'named_sfx': sfx, 'mapped_audio': mapped_beds, 'music_present': ap.get('music_present'),
        'dialogue_slots': dialogue,
        'continuity_start_authority': plan.get('continuity_start_authority'),
        'informational_stale_labels': sorted({x for x in [env.get('world'), env.get('background_asset_id')]
                                              + [p['asset_id'] for p in plan.get('prop_requirements') or []]
                                              + [c.get('asset_id') for c in plan.get('character_requirements') or []]
                                              if is_stale_label(x)}),
    }
    validate_shot_contract(spec)
    return spec


def validate_shot_contract(spec):
    sid = spec['shot_id']
    if spec['video_generation_required']:
        raise FailClosed('VIDEO_GENERATION_SHOT_NOT_PHASE0', sid)
    if spec['clean_reveal']:
        validate_clean_reveal(spec)
    if spec['protected_participation_hold']:
        if spec['treatments'] or spec['named_sfx'] or spec['dialogue_slots'] or spec['music_present']:
            raise FailClosed('PROTECTED_HOLD_HAS_EVENTS', sid)
    return True


def validate_clean_reveal(spec):
    """S025 = CLEAN REVEAL: zero active berry overlays; bloom must not be tied to an overlay change."""
    if spec['active_overlays']:
        raise FailClosed('CLEAN_REVEAL_HAS_ACTIVE_OVERLAYS',
                         f"{spec['shot_id']}: {[o['asset_id'] for o in spec['active_overlays']]}")
    return True


def validate_continuity(prev_spec, next_spec):
    """visible_at_start(N) must equal visible_at_end(N-1) for overlays; identities must match."""
    a = [o['asset_id'] for o in prev_spec['active_overlays']]
    b = [o['asset_id'] for o in next_spec['active_overlays']]
    if a != b:
        raise FailClosed('OVERLAY_CONTINUITY_BREAK', f"{prev_spec['shot_id']}->{next_spec['shot_id']}: {a} vs {b}")
    auth = next_spec.get('continuity_start_authority') or {}
    if auth.get('source_shot_id') != prev_spec['shot_id']:
        raise FailClosed('CONTINUITY_AUTHORITY_MISMATCH', str(auth))
    for kind in ('props', 'characters'):
        if sorted(x['asset_id'] for x in prev_spec[kind]) != sorted(x['asset_id'] for x in next_spec[kind]):
            raise FailClosed('IDENTITY_CONTINUITY_BREAK', kind)
    if prev_spec['environment']['asset_id'] != next_spec['environment']['asset_id']:
        raise FailClosed('IDENTITY_CONTINUITY_BREAK', 'environment')
    return True
