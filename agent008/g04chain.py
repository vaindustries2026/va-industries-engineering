"""G04 overlay/treatment certificate chain (zero spend, no provider, no pixel change).

When a shot's base frame is the last frame of an APPROVED raw motion whose base frame already carried G03 overlays
(and possibly the G08 mirror reflection), the derived frame already contains those pixels: re-running G03/G08 would
double them, and the G02 still / motion gates would refuse the frame because nothing certifies it. This module derives
the frame through the unchanged G04 path and re-issues the source certificates for the target shot, bound to the
derived frame SHA, with the full chain recorded. It is provenance inheritance only: no G03 or G08 pixels are applied.

certificate (from the approved source motion and its base frame's G03/G08 provenance):
  {motion_asset_id, motion_sha256, motion_source_frame_sha256, source_shot_id, declared_frame_index,
   frame_rgb_sha256 (optional pin of the declared frame), overlays_composited (G03), treatments_composited (G08, optional)}
inherit (what the caller asks to carry forward): {overlays: [asset_id, ...], treatments: [treatment_id, ...]}
"""
import json
from pathlib import Path

from . import AGENT_NAME
from .derive import derive_frame
from .errors import FailClosed
from .hashing import canonical_sha256
from .overlay import precomposited_overlay_set

AGENT_VERSION_CHAIN = 'agent008-v0.3-g04-certificate-chain'
DERIVATION_METHOD = 'G04 derive_frame: exact decoded frame index, lossless PNG, no crop/scale; G03/G08 certificates inherited'
REQUIRED = ('motion_asset_id', 'motion_sha256', 'motion_source_frame_sha256', 'source_shot_id')


def validate_certificate(certificate, source, frame_index):
    if not certificate:
        raise FailClosed('CERTIFICATE_MISSING', 'no source certificate supplied')
    missing = [k for k in REQUIRED if not certificate.get(k)]
    if missing:
        raise FailClosed('CERTIFICATE_INCOMPLETE', ','.join(missing))
    if certificate['motion_sha256'] != source.get('expected_sha256'):
        raise FailClosed('CERTIFICATE_STALE', f"certificate is for {certificate['motion_sha256']}, source is "
                                              f"{source.get('expected_sha256')}")
    if certificate['motion_asset_id'] != source.get('asset_id'):
        raise FailClosed('CERTIFICATE_STALE', f"certificate names {certificate['motion_asset_id']}, source is {source.get('asset_id')}")
    declared = certificate.get('declared_frame_index')
    if not isinstance(declared, int) or isinstance(declared, bool):
        raise FailClosed('CERTIFICATE_FRAME_INDEX_UNDECLARED', repr(declared))
    if frame_index != declared:
        raise FailClosed('CERTIFICATE_FRAME_INDEX_MISMATCH', f'requested {frame_index}, certificate declares {declared}')
    oc, tc = certificate.get('overlays_composited'), certificate.get('treatments_composited')
    if not oc and not tc:
        raise FailClosed('CERTIFICATE_MISSING', 'the source carries no G03 or G08 certificate to inherit')
    base = certificate['motion_source_frame_sha256']
    if tc:
        if tc.get('frame_sha256') != base or tc.get('shot_id') != certificate['source_shot_id']:
            raise FailClosed('CERTIFICATE_CHAIN_INVALID', 'G08 certificate is not bound to the motion base frame')
    if oc:
        bound = tc['input_frame_sha256'] if tc else base
        if oc.get('frame_sha256') != bound or oc.get('shot_id') != certificate['source_shot_id']:
            raise FailClosed('CERTIFICATE_CHAIN_INVALID', 'G03 certificate is not bound to the motion base frame chain')
    return oc, tc


def derive_certified_frame(source, frame_index, target_spec, out_dir, certificate, inherit):
    """Derive the target shot's base frame from an approved certified motion and inherit its certificates."""
    out_dir = Path(out_dir)
    oc, tc = validate_certificate(certificate, source, frame_index)
    want_o = sorted((inherit or {}).get('overlays') or [])
    want_t = sorted((inherit or {}).get('treatments') or [])
    have_o = sorted({o['asset_id'] for o in (oc or {}).get('overlays') or []})
    have_t = sorted((tc or {}).get('treatments') or [])
    if want_o != have_o or want_t != have_t:
        raise FailClosed('CERTIFICATE_SET_MISMATCH', f'requested overlays {want_o} treatments {want_t}; source carries '
                                                     f'overlays {have_o} treatments {have_t}')
    target_o = {o['asset_id']: o.get('expected_sha256') for o in target_spec['active_overlays']}
    if target_o != {o['asset_id']: o['sha256'] for o in (oc or {}).get('overlays') or []}:
        raise FailClosed('CERTIFICATE_SET_MISMATCH', f"{target_spec['shot_id']} needs overlays {sorted(target_o)}, source "
                                                     f'carries {have_o}')
    if any(t not in [x['treatment_id'] for x in target_spec['treatments']] for t in have_t):
        raise FailClosed('CERTIFICATE_SET_MISMATCH', f"{target_spec['shot_id']} does not assign {have_t}")
    prov = derive_frame(source, frame_index, target_spec['shot_id'], out_dir,
                        expected_frame_rgb_sha256=certificate.get('frame_rgb_sha256'))
    derived = prov['output']['sha256']
    sid = target_spec['shot_id']
    inherited_from = {'source_shot_id': certificate['source_shot_id'], 'motion_asset_id': certificate['motion_asset_id'],
                      'motion_sha256': certificate['motion_sha256'],
                      'motion_source_frame_sha256': certificate['motion_source_frame_sha256'], 'frame_index': frame_index}
    new_oc = ({'shot_id': sid, 'frame_sha256': derived, 'overlays': oc['overlays'], 'inherited_from': inherited_from}
              if oc else None)
    new_tc = ({'shot_id': sid, 'input_frame_sha256': derived, 'frame_sha256': derived, 'record_sha256': tc['record_sha256'],
               'treatments': tc['treatments'], 'mode': tc.get('mode'), 'reflected_overlays': tc.get('reflected_overlays') or [],
               'inherited_from': inherited_from} if tc else None)
    if target_spec['active_overlays'] or new_oc:               # the target shot's contract must match what is inherited
        precomposited_overlay_set(target_spec, new_oc, derived)
    spec_t = sorted(t['treatment_id'] for t in target_spec['treatments'])
    if new_tc and any(t not in spec_t for t in new_tc['treatments']):
        raise FailClosed('CERTIFICATE_SET_MISMATCH', f'{sid} does not assign {new_tc["treatments"]}')
    record = {
        'agent': AGENT_NAME, 'agent_version': AGENT_VERSION_CHAIN, 'status': 'REVIEW', 'target_shot_id': sid,
        'SOURCE_ASSET_ID': source.get('asset_id'), 'SOURCE_SHA': prov['source']['verified_sha256'],
        'SOURCE_FRAME_INDEX': frame_index, 'DERIVED_FRAME_SHA': derived,
        'G03_CERTIFICATES_INHERITED': have_o, 'G08_CERTIFICATES_INHERITED': have_t,
        'CERTIFICATE_SOURCE_SHA': certificate['motion_source_frame_sha256'], 'DERIVATION_METHOD': DERIVATION_METHOD,
        'selected_frame_rgb_sha256': prov['selected_frame_rgb_sha256'], 'derived_frame_provenance_core': prov['deterministic_core_sha256'],
        'overlays_composited': new_oc, 'treatments_composited': new_tc,
        'pixels_reapplied': {'g03': False, 'g08': False},
        'human_approval': {'required': True, 'approved': False, 'approve_by': 'exact DERIVED_FRAME_SHA'},
    }
    record['deterministic_core_sha256'] = canonical_sha256(record)
    (out_dir / f'{sid}_G04_CERTIFICATE_CHAIN.json').write_text(json.dumps(record, indent=1, sort_keys=True) + '\n')
    return record
