"""Read-only pre-generation checklist: evaluates every Step-7 field independently and reports all blockers.

Never submits anything. Use before asking a human for spend authorisation.
"""
import json
import sys
from pathlib import Path

from ..config import load_output_spec
from ..errors import FailClosed
from ..inputs import load_hash_pins, load_snapshot, validate_readiness
from ..resolve import Resolver
from ..spec import build_shot_spec
from .authorisation import AttemptLedger
from .contracts import MotionRequest
from .higgsfield import HiggsfieldProvider
from .higgsfield_transport import HiggsfieldApiTransport


def _check(name, fn, out):
    try:
        v = fn()
        out.append({'check': name, 'result': 'PASS', 'value': v})
    except FailClosed as e:
        out.append({'check': name, 'result': 'FAIL', 'code': e.code, 'detail': e.detail})
    except FileNotFoundError as e:
        out.append({'check': name, 'result': 'FAIL', 'code': 'FILE_MISSING', 'detail': str(e)})


def preflight(job, snapshot, pins, source_frame_path, frame_approval, provider, ledger, scope_id, source_upload=None,
              authorisation=None):
    out = []
    spec = load_output_spec()
    r = validate_readiness(snapshot, job['readiness_manifest_id'], job['production_manifest_id'], job['agent006_run_id'])
    res = Resolver(r, snapshot['asset_registry'], pins)
    _check('approved_shot_contract', lambda: build_shot_spec(snapshot, res, job['shot_id'], spec, motion_phase=True)['frames'], out)
    vids = snapshot['production_manifest']['manifest_json_reduced']['generation_workload']['video_generation_shots']
    _check('shot_in_approved_video_shots', lambda: job['shot_id'] in vids or (_ for _ in ()).throw(FailClosed('SHOT_NOT_VIDEO')), out)
    _check('manifest_ids', lambda: [snapshot['production_manifest']['id'], r['id'], r['status']], out)
    def frame():
        p = Path(source_frame_path) if source_frame_path else None
        if not p or not p.is_file():
            raise FailClosed('SOURCE_FRAME_MISSING', 'no approved S027 base frame exists')
        if not frame_approval:
            raise FailClosed('SOURCE_FRAME_NOT_APPROVED')
        return frame_approval['sha256']
    _check('source_frame_sha256', frame, out)
    _check('model_capability', lambda: provider.validate_request(MotionRequest(
        job['shot_id'], 'x', '0' * 64, job['motion_prompt'], job['negative_constraints'], job['duration_seconds'],
        job['aspect_ratio'], job['resolution'], job['fps_target'], job['provider'], job['provider_model'], scope_id)), out)
    out.append({'check': 'prompt_sha256', 'result': 'PASS', 'value': job['motion_prompt_sha256']})
    out.append({'check': 'requested_duration_resolution', 'result': 'PASS',
                'value': [job['duration_seconds'], job['resolution'], job['aspect_ratio']]})
    def contract():
        if not hasattr(provider, 'official_model'):
            return job['provider_model']
        mid, rec = provider.official_model(job['provider_model'])
        if not rec or rec.get('contract_status') != 'VERIFIED' or not rec.get('submit_enabled'):
            raise FailClosed('MODEL_CONTRACT_NOT_VERIFIED', job['provider_model'])
        return mid
    _check('model_official_contract', contract, out)
    _check('provider_credentials', lambda: provider.credentials_present() or (_ for _ in ()).throw(
        FailClosed('PROVIDER_CREDENTIAL_MISSING', 'no sanctioned Higgsfield API transport configured')), out)
    def staged():
        if getattr(provider, 'requires_hosted_source', False) and not source_upload:
            raise FailClosed('SOURCE_URL_MISSING', 'approved frame not staged; source upload needs its own authorisation')
        return (source_upload or {}).get('public_url')
    _check('source_frame_hosted_url', staged, out)
    def spend():
        if authorisation is None:
            raise FailClosed('SPEND_AUTHORISATION_MISSING', 'no human-approved generation authorisation for this job')
        from .higgsfield import require_paid_authorisation
        return require_paid_authorisation(authorisation)
    _check('spend_authorisation', spend, out)
    out.append({'check': 'paid_generation_count_so_far', 'result': 'PASS', 'value': ledger.attempts(scope_id)})
    blockers = [c for c in out if c['result'] == 'FAIL']
    return {'job_id': job['job_id'], 'ready_for_paid_call': not blockers, 'checks': out,
            'blockers': [c['code'] for c in blockers]}


if __name__ == '__main__':
    root = Path(__file__).resolve().parents[1]
    job = json.loads((root / 'motion/jobs/ep005_s027_motion_smoke_v1.json').read_text())
    snap = load_snapshot(root / 'inputs/ep005_motion_s027_input_snapshot.json')
    rep = preflight(job, snap, load_hash_pins(root / 'inputs/hash_pins.json'), None, None,
                    HiggsfieldProvider(transport=HiggsfieldApiTransport()),
                    AttemptLedger(sys.argv[1] if len(sys.argv) > 1 else '/dev/null'), 'UNSET')
    print(json.dumps(rep, indent=1, default=str))
