"""AGENT008_BATCH_DRIVER_v0.1: governed batch layer over the existing Agent-008 capabilities (still part of Agent-008).

Input: an explicit allowlist of shot IDs, the authoritative specs (resolve_episode output), the frame-family map and an
inventory of approved / pending artifacts read from authoritative records. For every allowlisted shot the driver
resolves the requirements and computes one state with a deterministic ladder (earliest unmet requirement wins), the
next human gate and the next automated stage. Each shot is evaluated independently; a failure in one never changes
another. Execution modes are local only: PLAN_ONLY (no writes), LOCAL_PREPARE_ONLY (deterministic intermediates in a
scratch dir), LOCAL_RENDER_ONLY (G02 still renders, two runs, scratch dir), PROVIDER_PREFLIGHT_ONLY (a frozen provider
package in a scratch dir, never submitted). There is no paid mode, no retry, no replacement candidate and no provider
fallback. Nothing here writes production storage or the registry, or calls a provider.
"""
import json
from pathlib import Path

from .errors import FailClosed
from .hashing import canonical_sha256, sha256_file
from .spec import IN_SHOT_CUT_SHOTS

DRIVER_VERSION = 'AGENT008_BATCH_DRIVER_v0.1'
MODES = ('PLAN_ONLY', 'LOCAL_PREPARE_ONLY', 'LOCAL_RENDER_ONLY', 'PROVIDER_PREFLIGHT_ONLY')
APPROVED = ('APPROVED', 'LOCKED')
G06_SHOTS = {'S024'}                                  # keyframed crop/scale (G06) not built; Batch 0D matrix
FRAME_KINDS = ('GENERATE', 'REUSE_APPROVED_ASSET', 'DERIVE_CROP', 'DERIVE_MOTION_END')

# state -> (category, next human gate, next automated stage)
STATES = {
    'FAILED': ('FAILED', 'review the failure; nothing is retried', None),
    'COMPLETE_APPROVED': ('COMPLETE', None, None),
    'BLOCKED_ENGINEERING': ('BLOCKED', 'engineering decision / build', None),
    'WAITING_FOR_FINAL_SHOT_APPROVAL': ('HUMAN', 'APPROVE/REJECT the assembled shot by exact SHA', None),
    'WAITING_FOR_UPSTREAM': ('HUMAN', 'complete the upstream shot / source approval', 'derive the base frame once the source is approved'),
    'WAITING_FOR_BASE_FRAME': ('HUMAN', 'authorise the base-frame generation (paid) for the family', 'normalise + hash the generated frame (G04)'),
    'READY_FOR_FRAME_DERIVATION': ('AUTOMATED', None, 'derive the base frame locally (G04 / G04 certificate chain)'),
    'WAITING_FOR_FRAME_APPROVAL': ('HUMAN', 'APPROVE/REJECT the base frame (or the reuse binding) by exact SHA', None),
    'WAITING_FOR_G03_RECORD': ('HUMAN', 'approve the G03 placement record measured on the approved frame', 'apply G03 once approved'),
    'WAITING_FOR_G08_RECORD': ('HUMAN', 'approve the G08 treatment record measured on the approved frame', 'apply G08 once approved'),
    'WAITING_FOR_AUDIO_TIMING': ('HUMAN', 'approve the event-audio timing (SFX/foley start frames)', None),
    'WAITING_FOR_DIALOGUE': ('HUMAN', 'authorise TTS for the missing lines', 'bind clips with G09 once approved'),
    'WAITING_FOR_DIALOGUE_APPROVAL': ('HUMAN', 'APPROVE/REJECT each clip by exact SHA', 'bind clips with G09'),
    'READY_FOR_LOCAL_RENDER': ('AUTOMATED', None, 'G03/G08 static stages -> G02 still render x2 -> QC -> REVIEW'),
    'READY_FOR_PROVIDER_PREFLIGHT': ('AUTOMATED', None, 'G03/G08 static stages -> freeze provider package (no submit)'),
    'WAITING_FOR_PROVIDER_AUTHORISATION': ('HUMAN', 'authorise the provider spend (scope, ceiling, balance)', None),
    'WAITING_FOR_PROVIDER_OUTPUT': ('PROVIDER', None, 'retrieve + preserve the raw output exactly'),
    'WAITING_FOR_RAW_MOTION_APPROVAL': ('HUMAN', 'APPROVE/REJECT the raw motion by exact SHA', None),
    'READY_FOR_ASSEMBLY': ('AUTOMATED', None, 'deterministic motion assembly x2 -> QC -> REVIEW'),
}


def _err(code, detail=''):
    return {'code': code, 'detail': detail}


def validate_batch(batch):
    if not isinstance(batch, dict):
        raise FailClosed('BATCH_INVALID', 'batch must be a dict')
    ids = batch.get('shot_ids')
    if not isinstance(ids, list) or not ids or any(not isinstance(s, str) or not s or '*' in s or s.upper() == 'ALL' for s in ids):
        raise FailClosed('BATCH_ALLOWLIST_INVALID', 'an explicit non-empty list of shot IDs is required (no wildcard / ALL)')
    if len(ids) != len(set(ids)):
        raise FailClosed('BATCH_ALLOWLIST_INVALID', 'duplicate shot IDs')
    if batch.get('mode') not in MODES:
        raise FailClosed('BATCH_MODE_NOT_AUTHORISED', f"{batch.get('mode')!r} (allowed: {', '.join(MODES)}; no paid mode exists)")
    if not batch.get('batch_id'):
        raise FailClosed('BATCH_INVALID', 'batch_id required')
    return ids


def _sha_check(entry, label, errors):
    """If a local path is supplied, its bytes must equal the recorded SHA."""
    p = (entry or {}).get('path')
    if p and Path(p).is_file() and sha256_file(p) != entry.get('sha256'):
        errors.append(_err('SHA_MISMATCH', f'{label}: {p}'))


def _status(entry):
    return (entry or {}).get('status')


def resolve_shot(sid, specs, families, inventory, _seen=()):
    """Requirements + state for one shot. Pure function of its inputs."""
    if sid in _seen:
        raise FailClosed('UPSTREAM_CYCLE', ' -> '.join(_seen + (sid,)))
    r = specs.get(sid)
    inv = inventory.get(sid) or {}
    errors, blockers, outstanding = [], [], []
    out = {'SHOT_ID': sid}
    if not r or (r.get('status') == 'SPEC' and not r.get('spec')):
        return {**out, 'STATE': 'FAILED', 'CATEGORY': 'FAILED', 'NEXT_REQUIRED_HUMAN_GATE': STATES['FAILED'][1],
                'NEXT_REQUIRED_AUTOMATED_STAGE': None, 'ERRORS': [_err('SPEC_MISSING', sid)], 'CURRENT_BLOCKERS': ['SPEC_MISSING'],
                'OUTSTANDING': []}
    sp = r.get('spec') or {}
    fam = families.get(sid)
    g11 = r.get('status') == 'BLOCKED'
    g07, g06 = sid in IN_SHOT_CUT_SHOTS, sid in G06_SHOTS
    motion = bool(fam and fam.get('provider_motion'))
    overlays = [o['asset_id'] for o in sp.get('active_overlays') or []]
    treatments = [t['treatment_id'] for t in sp.get('treatments') or []]
    events = [x['asset_id'] for x in (sp.get('named_sfx') or []) + (sp.get('event_audio') or [])]
    slots = sp.get('dialogue_slots') or []
    frame = inv.get('frame')
    frame_certs = {'overlays': bool((frame or {}).get('overlays_composited')),
                   'treatments': bool((frame or {}).get('treatments_composited'))}
    out.update({
        'AUTHORITATIVE_SPEC': {'status': r.get('status'), 'sha256': canonical_sha256(sp) if sp else None,
                               'frames': sp.get('frames'), 'duration_s': sp.get('duration_seconds')},
        'PRODUCTION_MODE': 'BLOCKED' if g11 else ('PROVIDER_MOTION' if motion else 'G02_STILL'),
        'BASE_FRAME_REQUIREMENT': fam,
        'G03_REQUIREMENT': {'overlays': overlays, 'record_required': bool(overlays) and not frame_certs['overlays'],
                            'satisfied_by_inherited_certificate': frame_certs['overlays']},
        'G08_REQUIREMENT': {'treatments': treatments,
                            'record_required': bool(treatments) and not (frame_certs['treatments'] and motion),
                            'satisfied_by_inherited_certificate': frame_certs['treatments']},
        'G06_REQUIREMENT': g06, 'G07_REQUIREMENT': g07, 'G11_REQUIREMENT': g11,
        'DIALOGUE_REQUIREMENTS': [{'speaker': d['speaker'], 'text': d['text']} for d in slots],
        'AUDIO_REQUIREMENTS': {'beds': [b['asset_id'] for b in sp.get('mapped_audio') or []], 'events': events,
                               'event_timing_required': bool(events)},
        'PROVIDER_MOTION_REQUIRED': motion,
        'UPSTREAM_CONTINUITY_DEPENDENCIES': [fam['source']] if fam and fam.get('kind') != 'GENERATE' else [],
    })

    def done(state, *blk):
        blockers.extend(blk)
        cat, gate, auto = STATES[state]
        return {**out, 'STATE': state, 'CATEGORY': cat, 'NEXT_REQUIRED_HUMAN_GATE': gate,
                'NEXT_REQUIRED_AUTOMATED_STAGE': auto, 'CURRENT_BLOCKERS': blockers, 'OUTSTANDING': outstanding,
                'ERRORS': errors}

    # outstanding inputs (all of them, independent of the ladder)
    for d in slots:
        if not any(c.get('text') == d['text'] and c.get('speaker') == d['speaker'] for c in inv.get('dialogue') or []):
            outstanding.append(f"DIALOGUE: {d['speaker']}: {d['text']}")
    if out['G03_REQUIREMENT']['record_required'] and _status(inv.get('g03_record')) not in APPROVED:
        outstanding.append('G03_RECORD')
    if out['G08_REQUIREMENT']['record_required'] and _status(inv.get('g08_record')) not in APPROVED:
        outstanding.append('G08_RECORD')
    if _status(frame) not in APPROVED:
        outstanding.append('BASE_FRAME')

    final = inv.get('final')
    if final and _status(final) not in ('APPROVED', 'LOCKED', 'REVIEW', 'REJECTED'):
        errors.append(_err('UNEXPECTED_PRODUCTION_STATE', f'final status {_status(final)!r}'))
    if frame and _status(frame) not in ('APPROVED', 'LOCKED', 'REVIEW', 'REJECTED'):
        errors.append(_err('UNEXPECTED_PRODUCTION_STATE', f'frame status {_status(frame)!r}'))
    _sha_check(frame, 'base frame', errors)
    for c in inv.get('dialogue') or []:
        _sha_check(c, f"dialogue {c.get('audio_asset_id')}", errors)
    if errors:
        return done('FAILED', *[e['code'] for e in errors])
    if _status(final) in APPROVED:
        return done('COMPLETE_APPROVED')
    if g11 or g07 or g06:
        return done('BLOCKED_ENGINEERING', *(['G11_TRACKED_OVERLAY_REMOVAL'] * g11 + ['G07_IN_SHOT_CUT'] * g07
                                             + ['G06_KEYFRAMED_CROP_SCALE'] * g06))
    if _status(final) == 'REVIEW':
        return done('WAITING_FOR_FINAL_SHOT_APPROVAL')
    if _status(final) == 'REJECTED' or _status(frame) == 'REJECTED':
        return done('FAILED', 'REJECTED_BY_HUMAN_NO_AUTOMATIC_REPLACEMENT')
    if not fam:
        return done('FAILED', 'FRAME_FAMILY_UNDECLARED')
    if fam.get('kind') not in FRAME_KINDS:
        return done('FAILED', f"FRAME_KIND_UNSUPPORTED:{fam.get('kind')}")

    # base frame
    if not frame:
        kind, src = fam['kind'], fam.get('source') or {}
        if kind == 'GENERATE':
            fr = (inventory.get('__families__') or {}).get(fam['family_id'])
            if _status(fr) == 'REVIEW':
                return done('WAITING_FOR_FRAME_APPROVAL', f"FAMILY_FRAME_IN_REVIEW:{fam['family_id']}")
            return done('WAITING_FOR_BASE_FRAME', f"FAMILY_FRAME_NOT_GENERATED:{fam['family_id']}")
        if kind == 'REUSE_APPROVED_ASSET':
            a = (inventory.get('__assets__') or {}).get(src.get('asset_id'))
            if _status(a) not in APPROVED or a.get('sha256') != src.get('sha256'):
                return done('WAITING_FOR_UPSTREAM', f"REUSE_SOURCE_NOT_APPROVED:{src.get('asset_id')}")
            return done('WAITING_FOR_FRAME_APPROVAL', f"REUSE_BINDING_NOT_APPROVED:{src.get('asset_id')}")
        if kind == 'DERIVE_CROP':
            fr = (inventory.get('__families__') or {}).get(src.get('family_id'))
            if _status(fr) not in APPROVED:
                return done('WAITING_FOR_UPSTREAM', f"CROP_SOURCE_FAMILY_NOT_APPROVED:{src.get('family_id')}")
            return done('READY_FOR_FRAME_DERIVATION')
        up = src.get('shot_id')                                   # DERIVE_MOTION_END
        up_r = resolve_shot(up, specs, families, inventory, _seen + (sid,)) if up in specs else None
        if not up_r or up_r['STATE'] in ('BLOCKED_ENGINEERING', 'FAILED'):
            return done('BLOCKED_ENGINEERING', f'UPSTREAM_CONTINUITY_BLOCKER:{up}')
        res = ((inventory.get(up) or {}).get('motion') or {}).get('result') or {}
        if _status(res) not in APPROVED:
            return done('WAITING_FOR_UPSTREAM', f'UPSTREAM_MOTION_NOT_APPROVED:{up}')
        if (overlays or treatments) and not (inventory.get(up) or {}).get('motion', {}).get('certificate'):
            return done('FAILED', f'UPSTREAM_CERTIFICATE_MISSING:{up}')
        return done('READY_FOR_FRAME_DERIVATION')
    if _status(frame) == 'REVIEW':
        return done('WAITING_FOR_FRAME_APPROVAL')

    # records, audio timing, dialogue
    if out['G03_REQUIREMENT']['record_required'] and _status(inv.get('g03_record')) not in APPROVED:
        return done('WAITING_FOR_G03_RECORD')
    if out['G08_REQUIREMENT']['record_required'] and _status(inv.get('g08_record')) not in APPROVED:
        return done('WAITING_FOR_G08_RECORD')
    timing = inv.get('timing') or {}
    if events and (_status(timing) not in APPROVED or any(e not in (timing.get('named') or {}) for e in events)):
        return done('WAITING_FOR_AUDIO_TIMING')
    clips = inv.get('dialogue') or []
    for d in slots:
        c = [c for c in clips if c.get('speaker') == d['speaker'] and c.get('text') == d['text']]
        if not c:
            return done('WAITING_FOR_DIALOGUE')
        if _status(c[0]) not in APPROVED:
            return done('WAITING_FOR_DIALOGUE_APPROVAL')
    if not motion:
        return done('READY_FOR_LOCAL_RENDER')

    m = inv.get('motion') or {}
    res = m.get('result')
    if res:
        if _status(res) == 'FAILED':
            return done('FAILED', 'PROVIDER_FAILED_NO_RETRY')
        if _status(res) in APPROVED:
            return done('READY_FOR_ASSEMBLY')
        if _status(res) == 'COMPLETED':
            return done('WAITING_FOR_RAW_MOTION_APPROVAL')
        return done('FAILED', f'UNEXPECTED_PRODUCTION_STATE:motion {_status(res)!r}')
    if m.get('submitted'):
        return done('WAITING_FOR_PROVIDER_OUTPUT')
    if m.get('preflight_sha256'):
        auth = m.get('authorisation') or {}
        if not auth.get('human_approved'):
            return done('WAITING_FOR_PROVIDER_AUTHORISATION', 'PROVIDER_AUTHORISATION_MISSING')
        if not auth.get('spend_ceiling_usd'):
            return done('WAITING_FOR_PROVIDER_AUTHORISATION', 'SPEND_CEILING_MISSING')
        return done('WAITING_FOR_PROVIDER_AUTHORISATION', 'PAID_MODE_NOT_AVAILABLE_IN_DRIVER_v0.1')
    return done('READY_FOR_PROVIDER_PREFLIGHT')


def plan_batch(batch, specs, families, inventory):
    """Read-only plan of the allowlisted shots. Deterministic: same inputs -> same plan and plan SHA."""
    ids = validate_batch(batch)
    shots = []
    for sid in ids:
        try:
            shots.append(resolve_shot(sid, specs, families, inventory))
        except FailClosed as e:                                 # one shot never affects another
            shots.append({'SHOT_ID': sid, 'STATE': 'FAILED', 'CATEGORY': 'FAILED', 'NEXT_REQUIRED_HUMAN_GATE': STATES['FAILED'][1],
                          'NEXT_REQUIRED_AUTOMATED_STAGE': None, 'ERRORS': [_err(e.code, e.detail)],
                          'CURRENT_BLOCKERS': [e.code], 'OUTSTANDING': []})
    plan = {'driver': DRIVER_VERSION, 'batch_id': batch['batch_id'], 'mode': batch['mode'], 'shot_ids': ids, 'shots': shots}
    plan['plan_sha256'] = canonical_sha256(plan)
    return plan


def _require_allowed(plan, sid):
    if sid not in plan['shot_ids']:
        raise FailClosed('BATCH_SHOT_NOT_ALLOWED', sid)


def execute(batch, specs, families, inventory, work_dir=None, runners=None):
    """Run the batch in its mode. runners: {stage: fn(shot_plan, inventory, out_dir) -> result} for the local stages
    (default: none, so nothing executes); PLAN_ONLY never accepts a work_dir."""
    plan = plan_batch(batch, specs, families, inventory)
    mode = batch['mode']
    if mode == 'PLAN_ONLY':
        if work_dir is not None:
            raise FailClosed('PLAN_ONLY_NO_WRITES', 'PLAN_ONLY takes no work_dir')
        return plan, {}
    if work_dir is None:
        raise FailClosed('LOCAL_WORK_DIR_REQUIRED', mode)
    work_dir = Path(work_dir)
    runners = runners or {}
    stage_for = {'LOCAL_PREPARE_ONLY': {'READY_FOR_FRAME_DERIVATION': 'derive_frame', 'READY_FOR_LOCAL_RENDER': 'prepare',
                                        'READY_FOR_PROVIDER_PREFLIGHT': 'prepare'},
                 'LOCAL_RENDER_ONLY': {'READY_FOR_LOCAL_RENDER': 'render'},
                 'PROVIDER_PREFLIGHT_ONLY': {'READY_FOR_PROVIDER_PREFLIGHT': 'provider_preflight'}}[mode]
    results = {}
    for s in plan['shots']:
        sid = s['SHOT_ID']
        _require_allowed(plan, sid)
        stage = stage_for.get(s['STATE'])
        if not stage:
            results[sid] = {'executed': False, 'reason': f"state {s['STATE']} has no {mode} stage"}
            continue
        if stage not in runners:
            results[sid] = {'executed': False, 'reason': f'no runner for {stage}'}
            continue
        try:                                                     # exactly one attempt; failures are terminal
            results[sid] = {'executed': True, 'stage': stage, 'attempts': 1,
                            'result': runners[stage](s, inventory, work_dir / sid)}
        except FailClosed as e:
            results[sid] = {'executed': True, 'stage': stage, 'attempts': 1, 'failed': _err(e.code, e.detail)}
    return plan, results


def provider_preflight_package(shot_plan, motion, out_dir):
    """Freeze the provider request locally (PROVIDER_PREFLIGHT_ONLY). Never submits; there is no submit code here."""
    if not motion or _status(motion.get('prompt_record')) not in APPROVED or not motion.get('prompt'):
        raise FailClosed('MOTION_PROMPT_NOT_APPROVED', shot_plan['SHOT_ID'])
    body = {'prompt': motion['prompt'], 'image_url': 'STAGE_AFTER_AUTHORISATION', 'duration': motion['duration'],
            'resolution': motion['resolution'], 'generate_audio': False}
    pkg = {'driver': DRIVER_VERSION, 'shot_id': shot_plan['SHOT_ID'], 'status': 'PREPARED_NOT_SUBMITTED',
           'provider': motion['provider'], 'model': motion['model'], 'source_frame_sha256': motion['source_frame_sha256'],
           'overlays_composited': motion.get('overlays_composited'), 'treatments_composited': motion.get('treatments_composited'),
           'request_body': body, 'request_body_sha256': canonical_sha256(body),
           'attempt_policy': {'max_generations': 1, 'retry': False, 'alternate_candidate': False, 'provider_fallback': False},
           'requires': ['human spend authorisation naming this body SHA', 'spend ceiling', 'balance confirmation',
                        'source frame staging with readback SHA'],
           'submitted': False}
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    p = out_dir / f"{shot_plan['SHOT_ID']}_PROVIDER_PREFLIGHT.json"
    if p.exists():
        raise FailClosed('OUTPUT_EXISTS', str(p))
    p.write_text(json.dumps(pkg, indent=1, sort_keys=True) + '\n')
    return {'package': p.name, 'request_body_sha256': pkg['request_body_sha256'], 'submitted': False}


def review_manifest(plan, results=None):
    """Batch-review manifest: the single packet shown to the human after a batch."""
    results = results or {}
    rows = []
    for s in plan['shots']:
        r = results.get(s['SHOT_ID']) or {}
        res = r.get('result') or {}
        state = 'FAILED' if r.get('failed') else s['STATE']
        rows.append({'SHOT_ID': s['SHOT_ID'], 'STATE': state, 'CATEGORY': 'FAILED' if r.get('failed') else s.get('CATEGORY'),
                     'INPUT_SHAS': res.get('input_shas') or {}, 'OUTPUT_SHAS': res.get('output_shas') or {},
                     'QC_STATUS': res.get('qc_status') or ('NOT_RUN' if not r.get('executed') else 'N/A'),
                     'HUMAN_GATE': s.get('NEXT_REQUIRED_HUMAN_GATE'), 'NEXT_AUTOMATED_STAGE': s.get('NEXT_REQUIRED_AUTOMATED_STAGE'),
                     'PROVIDER_COST': res.get('provider_cost'),
                     'BLOCKER': (r.get('failed') or {}).get('code') or (s.get('CURRENT_BLOCKERS') or [None])[0],
                     'OUTSTANDING': s.get('OUTSTANDING') or []})
    cat = [x['CATEGORY'] for x in rows]
    m = {'BATCH_ID': plan['batch_id'], 'DRIVER': DRIVER_VERSION, 'MODE': plan['mode'], 'PLAN_SHA256': plan['plan_sha256'],
         'SHOT_COUNT': len(rows), 'COMPLETE_COUNT': cat.count('COMPLETE'), 'BLOCKED_COUNT': cat.count('BLOCKED'),
         'WAITING_HUMAN_COUNT': cat.count('HUMAN'), 'WAITING_PROVIDER_COUNT': cat.count('PROVIDER'),
         'READY_AUTOMATED_COUNT': cat.count('AUTOMATED'), 'FAILED_COUNT': cat.count('FAILED'), 'shots': rows}
    m['manifest_sha256'] = canonical_sha256(m)
    return m


# --- local stage runners (scratch only; reuse the existing deterministic capabilities) ---------------------------
def local_runners(specs, families, paths, output_spec):
    """Runners for LOCAL_PREPARE_ONLY / LOCAL_RENDER_ONLY / PROVIDER_PREFLIGHT_ONLY. paths: {asset_id: local file}."""
    from .derive import derive_frame
    from .g04chain import derive_certified_frame
    from .g08 import REFL, apply_reflection
    from .overlay import place_overlays
    from .still import compose_still_shot

    def frame_dict(sid, f):
        d = {'asset_id': f['asset_id'], 'registry_id': f.get('registry_id', 'inventory'), 'classification': f['classification'],
             'registry_status': f['status'], 'shot_id': sid, 'path': str(paths.get(f['asset_id']) or f.get('path')),
             'expected_sha256': f['sha256']}
        for k in ('overlays_composited', 'treatments_composited'):
            if f.get(k):
                d[k] = f[k]
        return d

    def prepare(s, inv, out):
        sid = s['SHOT_ID']
        sp, i = specs[sid]['spec'], inv[sid]
        frame = frame_dict(sid, i['frame'])
        shas = {'base_frame': frame['expected_sha256']}
        g03prov = None
        if sp['active_overlays'] and not frame.get('overlays_composited'):
            g03prov = place_overlays(sp, frame, {o['asset_id']: paths[o['asset_id']] for o in sp['active_overlays']},
                                     i['g03_record'], out / 'g03')
            frame = {**frame, 'asset_id': f'{sid}-G03', 'classification': 'SHOT_FRAME/DERIVED_FRAME',
                     'path': str(out / 'g03' / g03prov['output']['file']), 'expected_sha256': g03prov['output']['sha256'],
                     'overlays_composited': g03prov['overlays_composited']}
            shas['g03_record'] = i['g03_record']['expected_sha256']
            shas['g03_frame'] = frame['expected_sha256']
        if REFL in [t['treatment_id'] for t in sp['treatments']] and not frame.get('treatments_composited'):
            p = apply_reflection(sp, frame, i['g08_record'], out / 'g08', g03prov)
            frame = {**frame, 'treatments_composited': p['treatments_composited'], 'expected_sha256': p['output']['sha256'],
                     **({'path': str(out / 'g08' / p['output']['file']), 'classification': 'SHOT_FRAME/DERIVED_FRAME'}
                        if p['output']['file'] else {})}
            shas['g08_record'] = i['g08_record']['expected_sha256']
            shas['g08_frame'] = frame['expected_sha256']
        return frame, shas

    def derive(s, inv, out):
        sid = s['SHOT_ID']
        fam, sp = families[sid], specs[sid]['spec']
        src = fam['source']
        if fam['kind'] == 'DERIVE_CROP':
            fr = inv['__families__'][src['family_id']]
            p = derive_frame({'asset_id': fr['asset_id'], 'registry_status': fr['status'], 'path': str(paths.get(fr['asset_id']) or fr['path']),
                              'expected_sha256': fr['sha256']}, 0, sid, out, crop=fam.get('crop'), scale=fam.get('scale'))
            return {'input_shas': {'source_frame': fr['sha256']}, 'output_shas': {'derived_frame': p['output']['sha256']},
                    'qc_status': 'LOSSLESS_ROUNDTRIP', 'state_after': 'WAITING_FOR_FRAME_APPROVAL'}
        m = inv[src['shot_id']]['motion']
        rec = derive_certified_frame({'asset_id': m['result']['asset_id'], 'registry_status': m['result']['status'],
                                      'path': str(paths.get(m['result']['asset_id']) or m['result'].get('path')),
                                      'expected_sha256': m['result']['raw_sha256']},
                                     m['certificate']['declared_frame_index'], sp, out, m['certificate'],
                                     {'overlays': [o['asset_id'] for o in sp['active_overlays']],
                                      'treatments': [t for t in (m['certificate'].get('treatments_composited') or {}).get('treatments') or []]})
        return {'input_shas': {'source_motion': rec['SOURCE_SHA']}, 'output_shas': {'derived_frame': rec['DERIVED_FRAME_SHA']},
                'qc_status': 'CERTIFICATES_INHERITED', 'state_after': 'WAITING_FOR_FRAME_APPROVAL'}

    def prepare_only(s, inv, out):
        frame, shas = prepare(s, inv, out)
        return {'input_shas': {'base_frame': shas['base_frame']}, 'output_shas': {k: v for k, v in shas.items() if k != 'base_frame'},
                'qc_status': 'PREPARED', 'state_after': s['STATE']}

    def render(s, inv, out):
        sid = s['SHOT_ID']
        sp, i = specs[sid]['spec'], inv[sid]
        frame, shas = prepare(s, inv, out)
        timing = {'named': (i.get('timing') or {}).get('named') or {},
                  'dialogue': [{'shot_id': sid, 'speaker': c['speaker'], 'text': c['text'], 'audio_asset_id': c['audio_asset_id'],
                                'expected_sha256': c['sha256'], 'registry_status': c['status'], 'start_seconds': c['start_seconds'],
                                'gain_db': c.get('gain_db', 0.0)} for c in i.get('dialogue') or []]}
        rec = i.get('g08_record') if sp['treatments'] else None
        runs = [compose_still_shot(sp, frame, output_spec, paths, timing, out / f'render{k}', treatment_record=rec) for k in 'AB']
        if runs[0]['outputs'] != runs[1]['outputs'] or runs[0]['deterministic_core_sha256'] != runs[1]['deterministic_core_sha256']:
            raise FailClosed('QC_NON_DETERMINISTIC', sid)
        if runs[0]['qc']['automatic_result'] != 'PASS':
            raise FailClosed('QC_FAILED', f"{sid}: {runs[0]['qc']['issues']}")
        shas.update({c['audio_asset_id']: c['sha256'] for c in i.get('dialogue') or []})
        return {'input_shas': shas, 'output_shas': {'review_mp4': runs[0]['outputs']['review_mp4']['sha256'],
                                                    'mix_wav': runs[0]['outputs']['mix_wav']['sha256']},
                'qc_status': 'PASS (two renders byte-identical)', 'state_after': 'WAITING_FOR_FINAL_SHOT_APPROVAL (local REVIEW)'}

    def preflight(s, inv, out):
        frame, shas = prepare(s, inv, out)
        m = {**inv[s['SHOT_ID']]['motion'], 'source_frame_sha256': frame['expected_sha256'],
             'overlays_composited': frame.get('overlays_composited'), 'treatments_composited': frame.get('treatments_composited')}
        r = provider_preflight_package(s, m, out)
        return {'input_shas': shas, 'output_shas': {'request_body': r['request_body_sha256']}, 'qc_status': 'NOT_SUBMITTED',
                'state_after': 'WAITING_FOR_PROVIDER_AUTHORISATION'}

    return {'derive_frame': derive, 'prepare': prepare_only, 'render': render, 'provider_preflight': preflight}
