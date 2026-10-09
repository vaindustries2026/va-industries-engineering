"""Stage 8C runner: pre-generation validation, exactly-one submission, read-only polling, raw preservation."""
import json
import os
import stat
import time
from datetime import datetime, timezone
from pathlib import Path

from .. import media
from ..errors import FailClosed
from ..hashing import sha256_file, verify_file
from .contracts import MotionResult
from .provider import TERMINAL_FAILED, TERMINAL_OK


def validate_pre_generation(req, provider, auth, ledger, snapshot, frame_approval):
    """Every field must resolve, or the run stops before any spend. Returns a checklist dict."""
    req.validate()
    checks = {}
    pm = snapshot['production_manifest']
    vids = (pm['manifest_json_reduced'].get('generation_workload') or {}).get('video_generation_shots') or []
    if pm.get('status') != 'APPROVED' or snapshot['readiness_manifest'].get('status') != 'APPROVED':
        raise FailClosed('MANIFEST_NOT_APPROVED')
    if req.shot_id not in vids or req.shot_id not in snapshot.get('render_shots', []):
        raise FailClosed('SHOT_NOT_APPROVED_FOR_MOTION', req.shot_id)
    checks['shot_id'] = req.shot_id
    checks['production_manifest_id'] = pm['id']
    checks['readiness_manifest_id'] = snapshot['readiness_manifest']['id']
    verify_file(req.source_frame_path, req.source_frame_sha256, f'{req.shot_id} source frame')
    if not frame_approval or frame_approval.get('sha256') != req.source_frame_sha256 \
            or frame_approval.get('status') not in ('APPROVED', 'LOCKED', 'APPROVED_FOR_MOTION_INPUT'):
        raise FailClosed('SOURCE_FRAME_NOT_APPROVED', 'a human-approved base frame bound to this exact sha256 is required')
    checks['source_frame_sha256'] = req.source_frame_sha256
    provider.validate_request(req)
    checks['provider_model'] = req.provider_model
    checks['prompt_sha256'] = req.prompt_sha256
    checks['duration_seconds'] = req.duration_seconds
    checks['resolution'] = req.resolution
    if not provider.credentials_present():
        raise FailClosed('PROVIDER_CREDENTIAL_MISSING', provider.name)
    checks['credentials'] = 'present'
    auth.matches(req)
    used = ledger.attempts(auth.approval_scope_id)
    if used >= auth.max_generations:
        raise FailClosed('GENERATION_COUNT_EXCEEDED', f'{used} of {auth.max_generations}')
    checks['paid_generations_so_far'] = used
    return checks


def _freeze(path):
    os.chmod(path, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)


def run_once(req, provider, auth, ledger, raw_root, snapshot, frame_approval, poll_interval=10.0, max_polls=180,
             sleep=time.sleep):
    """Validate, reserve, submit ONCE, poll read-only, fetch and freeze the raw output. Never retries."""
    validate_pre_generation(req, provider, auth, ledger, snapshot, frame_approval)
    reservation = ledger.reserve(auth, req)                 # counted even if anything below fails
    created = datetime.now(timezone.utc).isoformat()
    job_id = provider.submit(req)
    ledger.append('SUBMITTED', auth.approval_scope_id, provider_job_id=job_id, at_iso=created)
    status = {}
    for _ in range(max_polls):
        status = provider.poll(job_id)
        if status.get('status') in (TERMINAL_OK, TERMINAL_FAILED):
            break
        sleep(poll_interval)
    else:
        ledger.append('POLL_TIMEOUT', auth.approval_scope_id, provider_job_id=job_id)
        raise FailClosed('PROVIDER_POLL_TIMEOUT_NO_RETRY', job_id)
    result = MotionResult(provider=provider.name, provider_model=req.provider_model, provider_job_id=job_id,
                          source_frame_sha256=req.source_frame_sha256, prompt_hash=req.prompt_sha256,
                          provider_status=status['status'], created_at=created,
                          cost_or_usage_if_available=status.get('usage'))
    if status['status'] == TERMINAL_FAILED:
        ledger.append('FAILED', auth.approval_scope_id, provider_job_id=job_id, detail=status.get('detail'))
        raise FailClosed('PROVIDER_FAILED_NO_RETRY', f'{job_id}: {status.get("detail")}')
    dest = Path(raw_root) / req.shot_id / job_id
    if dest.exists() and any(dest.iterdir()):
        raise FailClosed('RAW_OUTPUT_DIR_NOT_EMPTY', str(dest))   # never overwrite raw evidence
    dest.mkdir(parents=True, exist_ok=True)
    path, original = provider.fetch(job_id, dest)
    _freeze(path)
    pr = media.probe(path)
    v = [s for s in pr['streams'] if s['codec_type'] == 'video'][0]
    result.raw_output_path = str(path)
    result.raw_output_sha256 = sha256_file(path)
    result.raw_original_filename = original
    result.raw_bytes = Path(path).stat().st_size
    result.raw_duration = float(pr['format'].get('duration', v.get('duration', 0)))
    result.raw_resolution = f"{v['width']}x{v['height']}"
    result.raw_fps = v.get('r_frame_rate')
    result.raw_codec = f"{pr['format'].get('format_name')}/{v.get('codec_name')}"
    ledger.append('COMPLETED', auth.approval_scope_id, provider_job_id=job_id, raw_output_sha256=result.raw_output_sha256)
    (dest / 'MOTION_RESULT.json').write_text(json.dumps({'reservation': reservation, 'result': result.to_dict()},
                                                       indent=1, sort_keys=True))
    return result
