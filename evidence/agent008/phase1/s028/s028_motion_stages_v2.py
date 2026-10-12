"""S028 motion v2 package (authoritative hand-off + pat), mirroring the S027 v2 stages. One authorised generation, no retry.

Usage (repo root):
  python3 evidence/agent008/phase1/s028/s028_motion_stages_v2.py validate <work_dir>   # no provider calls
  python3 evidence/agent008/phase1/s028/s028_motion_stages.py upload   <work_dir>   # ONE source upload + readback
  python3 evidence/agent008/phase1/s028/s028_motion_stages.py gate     <work_dir>   # freeze body + final gate (no provider writes)
  python3 evidence/agent008/phase1/s028/s028_motion_stages.py submit   <work_dir>   # EXACTLY ONE submit, read-only polling, raw retrieval
"""
import hashlib
import json
import math
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from agent008.config import load_output_spec  # noqa: E402
from agent008.dialogue_timing import govern_dialogue_timing  # noqa: E402
from agent008.episode import PINS, resolve_episode  # noqa: E402
from agent008.errors import FailClosed  # noqa: E402
from agent008.hashing import sha256_bytes, sha256_file  # noqa: E402
from agent008.inputs import load_hash_pins  # noqa: E402
from agent008.motion.authorisation import AttemptLedger, SpendAuthorisation  # noqa: E402
from agent008.motion.compose import resolve_dialogue  # noqa: E402
from agent008.motion.contracts import MotionRequest, text_sha256  # noqa: E402
from agent008.motion.higgsfield import HiggsfieldProvider  # noqa: E402
from agent008.motion.higgsfield_transport import HiggsfieldApiTransport, resolve_model, serialize_request  # noqa: E402
from agent008.motion.http import UrllibHttpClient  # noqa: E402
from agent008.motion.preflight import preflight  # noqa: E402
from agent008.motion.runner import run_once, validate_pre_generation  # noqa: E402
from agent008.motion.source_upload import SourceFrame, UploadAuthorisation, check_source_frame  # noqa: E402
from agent008.tools.snapshot_inputs import build_snapshot  # noqa: E402

FRAME_ID = 'FRAME-EP005-S028-BASE-CAND-v01'
FRAME_ROW = '739b9aec-d908-4699-baea-10bf9e6b4f3e'
FRAME_SHA = '9ac6ccc3239fd08a69e9a570f13a8b857d0d9d7257fb37d24f8ad676476c6ff0'
PROMPT_SHA = '18090c35fedbb28804646a636e31083b70cebd9d8b7ac2161b43117a33371b77'
READINESS = '69bff641-e056-4701-a23f-d91dbc2039b2'
DLG = {'DLG-EP005-S028-LUMI-v01': '970f55a95f73f0949be74c5d5424318811d5fa2add0438abd42e3f37f639a8bc',
       'DLG-EP005-S028-MIKKO-v01': 'ab81173ee7ddb15eeb8b3bbb0bdd7eed6840d76f9100d5edb1e6ca5d04b230b0'}
MODEL = 'bytedance/seedance-2.0/image-to-video'
SCOPE_UP = 'S028-MOTION-SOURCE-UPLOAD-1'
SCOPE_GEN = 'S028-MOTION-SEEDANCE20-1'
MAX_COST = 3.50
SB = 'https://ziluiwrwwbayhcskeere.supabase.co'
D = ROOT / 'evidence/agent008/phase1/s028'
JOB = json.loads((ROOT / 'agent008/motion/jobs/ep005_s028_motion_v2.json').read_text())
LEDGER = AttemptLedger(D / 'S028_MOTION_LEDGER_v1.jsonl')
http = UrllibHttpClient()


def get_rows(q):
    r = http.send('GET', f'{SB}/rest/v1/{q}', {'Accept': 'application/json'})
    if r.status != 200:
        sys.exit(f'STOP: GET {q.split("?")[0]} HTTP {r.status}')
    return json.loads(r.body)


def cost_table():
    out = {}
    for w, h in [(1920, 1080), (1920, 1088)]:
        for label, secs in (('5.000s', 5.0), ('121_frames', 121 / 24)):
            out[f'{w}x{h}_{label}'] = round(math.ceil(secs * w * h * 24 / 1024) / 1000 * 0.014, 4)
    return out


def validate(work):
    """All pre-submit checks that need no provider call. Returns (checks, problems, frame_path, snapshot)."""
    work.mkdir(parents=True, exist_ok=True)
    checks, problems = {}, []
    fr = get_rows(f'asset_registry?asset_id=eq.{FRAME_ID}&select=*')
    fr = fr[0] if len(fr) == 1 else {}
    md = fr.get('metadata_json') or {}
    checks['frame'] = {'row': fr.get('id'), 'status': fr.get('status'), 'human_decision': md.get('human_decision'), 'sha256': md.get('sha256')}
    checks['frame'].update({'human_approval': md.get('human_approval'), 'approved': md.get('approved')})
    if fr.get('id') != FRAME_ROW or fr.get('status') != 'APPROVED' or md.get('human_decision') != 'APPROVED' or md.get('sha256') != FRAME_SHA \
            or md.get('human_approval') != 'APPROVED' or md.get('approved') is not True:
        problems.append('FRAME_NOT_APPROVED_OR_SHA')
    r = http.send('GET', f'{SB}/storage/v1/object/authenticated/production-assets/{md.get("storage_object_key")}', {})
    frame_path = work / f'{FRAME_ID}.png'
    frame_path.write_bytes(r.body)
    checks['frame_stored_sha256'] = sha256_file(frame_path)
    if r.status != 200 or checks['frame_stored_sha256'] != FRAME_SHA:
        problems.append('FRAME_STORED_BYTES_SHA')
    dl = {x['asset_id']: x for x in get_rows('asset_registry?asset_id=in.(' + ','.join(DLG) + ')&select=*')}
    checks['dialogue'] = {a: [dl.get(a, {}).get('status'), (dl.get(a, {}).get('metadata_json') or {}).get('sha256')] for a in DLG}
    checks['dialogue_metadata'] = {a: [(dl.get(a, {}).get('metadata_json') or {}).get('human_decision'),
                                       (dl.get(a, {}).get('metadata_json') or {}).get('human_approval')] for a in DLG}
    if any(dl.get(a, {}).get('status') != 'APPROVED' or dl[a]['metadata_json']['sha256'] != s
           or dl[a]['metadata_json'].get('human_decision') != 'APPROVED' or dl[a]['metadata_json'].get('human_approval') != 'APPROVED'
           for a, s in DLG.items()):
        problems.append('DIALOGUE_NOT_APPROVED_OR_SHA')
    snap = build_snapshot(READINESS, shots=['S028'])
    checks['readiness'] = [snap['readiness_manifest']['id'], snap['readiness_manifest']['status']]
    checks['manifest'] = [snap['production_manifest']['id'], snap['production_manifest']['status']]
    if snap['readiness_manifest']['status'] != 'APPROVED' or snap['production_manifest']['status'] != 'APPROVED':
        problems.append('LINEAGE_NOT_APPROVED')
    spec = load_output_spec()
    ep = {x['shot_id']: x for x in resolve_episode(build_snapshot(READINESS), load_hash_pins(PINS), spec)}
    s028 = ep['S028']
    checks['S028_spec'] = s028['status']
    if s028['status'] != 'SPEC':
        problems.append('S028_SPEC_BLOCKED')
    else:
        sp = s028['spec']
        checks['S028_engineering'] = {'video_generation_required': sp['video_generation_required'], 'overlays': len(sp['active_overlays']),
                                      'treatments': len(sp['treatments']), 'frames': sp['frames'], 'duration_s': sp['duration_seconds']}
        if sp['active_overlays'] or sp['treatments'] or sp['frames'] != 120:
            problems.append('S028_ENGINEERING_BLOCKER')
        # G09 on the approved real clips with the accepted timing (bytes read from production storage)
        paths = {}
        for a, s in DLG.items():
            rr = http.send('GET', f'{SB}/storage/v1/object/authenticated/production-assets/audio/dialogue/{a}.mp3', {})
            p = work / f'{a}.mp3'
            p.write_bytes(rr.body)
            if sha256_file(p) != s:
                problems.append(f'DIALOGUE_STORED_SHA:{a}')
            paths[a] = p
        t = {'dialogue': [dict(e, gain_db=0.0) for e in JOB['audio_timing_for_compositor']['dialogue']],
             'dialogue_window': JOB['audio_timing_for_compositor']['dialogue_window']}
        rep = govern_dialogue_timing(sp, resolve_dialogue(sp, paths, t), paths, t, spec)
        checks['G09'] = {'status': 'PASS', 'lines': [(x['speaker'], x['start_s'], x['end_s']) for x in rep['lines']],
                         'end_hold_s': rep['visual_holds']['after_last_line_s']}
    prompt = (D / 'S028_MOTION_PROMPT_v2.txt').read_bytes().decode('utf-8')
    checks['prompt_sha256'] = text_sha256(prompt)
    checks['authoritative_action'] = {
        'cloth_handoff_mikko_to_lumi': 'passes it to Lumi' in prompt and 'takes the cloth' in prompt,
        'single_shoulder_pat_by_lumi_on_mikko': "exactly one soft, gentle, reassuring pat with the cloth on Mikko's shoulder" in prompt,
        'pat_never_face': 'never his face' in prompt,
        'mirror_lowered_to_rest': 'relaxed resting position in front of her lower body' in prompt,
        'settled_end_state': 'settles beside Lumi' in prompt,
        'camera_locked': 'The camera is completely locked' in prompt}
    if not all(checks['authoritative_action'].values()):
        problems.append('AUTHORITATIVE_ACTION_MISSING')
    checks['balance'] = {'HIGGSFIELD_BALANCE_CONFIRMED': 'YES (Gilang, >= USD 3.46)', 'max_authorised_usd': MAX_COST}
    if text_sha256(prompt) != PROMPT_SHA or JOB['motion_prompt'] != prompt or JOB['motion_prompt_sha256'] != PROMPT_SHA:
        problems.append('PROMPT_SHA')
    checks['request'] = {'duration': JOB['duration_seconds'], 'resolution': JOB['resolution'], 'generate_audio': JOB['generate_audio'],
                         'source_frames': 1, 'max_attempts': JOB['maximum_attempts'], 'auto_retries': JOB['automatic_retries'],
                         'model': JOB['provider_model']}
    if (JOB['duration_seconds'], JOB['resolution'], JOB['generate_audio'], JOB['maximum_attempts'], JOB['automatic_retries'],
            JOB['provider_model']) != (5, '1080p', False, 1, 0, MODEL):
        problems.append('REQUEST_PARAMS')
    checks['expected_cost_usd'] = cost_table()
    if max(checks['expected_cost_usd'].values()) > MAX_COST:
        problems.append('EXPECTED_COST_ABOVE_CEILING')
    checks['ledger'] = {'upload_attempts': LEDGER.upload_attempts(SCOPE_UP), 'generation_attempts': LEDGER.attempts(SCOPE_GEN)}
    return checks, problems, frame_path, snap


def build_request(frame_path, public_url):
    return MotionRequest('S028', str(frame_path), FRAME_SHA, JOB['motion_prompt'], '', 5, '16:9', '1080p', 24, 'higgsfield', MODEL,
                         SCOPE_GEN, source_frame_url=public_url)


def auth():
    return SpendAuthorisation(SCOPE_GEN, 'Gilang / Company Brain', 'HIGGSFIELD', MODEL, 'S028', FRAME_SHA, PROMPT_SHA,
                              max_generations=1, no_auto_retry=True, human_approved=True)


mode, work = sys.argv[1], Path(sys.argv[2])

if mode == 'validate':
    checks, problems, _, _ = validate(work)
    out = {'checks': checks, 'problems': problems, 'result': 'PASS' if not problems else 'STOP'}
    (D / 'S028_PRESUBMIT_VALIDATION_v2.json').write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))
    print(json.dumps(out, indent=1, ensure_ascii=False, default=str))

elif mode == 'upload':
    checks, problems, frame_path, _ = validate(work)
    if problems:
        sys.exit(f'STOP: validation problems {problems}')
    transport = HiggsfieldApiTransport()
    provider = HiggsfieldProvider(transport=transport)
    frame = SourceFrame(FRAME_ID, str(frame_path), FRAME_SHA, 'APPROVED', 'image/png')
    ua = UploadAuthorisation(SCOPE_UP, 'Gilang / Company Brain', 'higgsfield', FRAME_ID, FRAME_SHA, 'image/png', max_uploads=1,
                             human_approved=True)
    data = check_source_frame(frame)
    ua.matches(frame, provider.name)
    if not provider.credentials_present():
        sys.exit('STOP: PROVIDER_CREDENTIAL_MISSING')
    if LEDGER.upload_attempts(SCOPE_UP) >= 1:
        sys.exit('STOP: UPLOAD_COUNT_EXCEEDED')
    LEDGER.append('UPLOAD_RESERVED', SCOPE_UP, frame_id=FRAME_ID, source_frame_sha256=FRAME_SHA, content_type='image/png', bytes=len(data))
    try:
        rec = transport.prepare_source_upload(data, 'image/png', FRAME_SHA, verify_readback=False)
    except FailClosed as e:
        LEDGER.append('UPLOAD_FAILED', SCOPE_UP, code=e.code, detail=str(e.detail)[:300])
        sys.exit(f'STOP: upload failed {e.code}')
    LEDGER.append('UPLOADED', SCOPE_UP, frame_id=FRAME_ID, **rec)
    rb = http.send('GET', rec['public_url'], {})
    got = sha256_bytes(rb.body) if rb.status == 200 else None
    ev = {'public_url': rec['public_url'], 'http_status': rb.status, 'bytes': len(rb.body),
          'content_type': {k.lower(): v for k, v in rb.headers.items()}.get('content-type'), 'sha256': got}
    LEDGER.append('READBACK_SHA256_MATCH' if got == FRAME_SHA else 'READBACK_FAILED', SCOPE_UP, **ev)
    out = {'upload': rec, 'readback': ev}
    (D / 'S028_SOURCE_UPLOAD_v1.json').write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))
    if got != FRAME_SHA:
        sys.exit('STOP: readback verification failed')

elif mode == 'gate':
    checks, problems, frame_path, snap = validate(work)
    up = json.loads((D / 'S028_SOURCE_UPLOAD_v1.json').read_text())
    source_upload = {**up['upload'], 'readback': 'SHA256_MATCH'}
    rb = http.send('GET', up['upload']['public_url'], {})                 # fresh readback of the reused upload
    fresh = {'http_status': rb.status, 'bytes': len(rb.body), 'sha256': sha256_bytes(rb.body) if rb.status == 200 else None}
    LEDGER.append('REUSE_READBACK_SHA256_MATCH' if fresh['sha256'] == FRAME_SHA else 'REUSE_READBACK_FAILED', SCOPE_UP,
                  public_url=up['upload']['public_url'], **fresh)
    checks['reused_upload_fresh_readback'] = fresh
    if up['readback']['sha256'] != FRAME_SHA or fresh['sha256'] != FRAME_SHA:
        problems.append('UPLOAD_READBACK')
    req = build_request(frame_path, source_upload['public_url'])
    transport = HiggsfieldApiTransport()
    provider = HiggsfieldProvider(transport=transport)
    _, rec = resolve_model(transport.cfg, MODEL)
    body = serialize_request(req, rec, source_upload['public_url'])
    wire = json.dumps(body, separators=(',', ':')).encode()
    if body != {'prompt': JOB['motion_prompt'], 'image_url': source_upload['public_url'], 'duration': 5, 'resolution': '1080p',
                'generate_audio': False}:
        problems.append('BODY_NOT_EXACTLY_APPROVED_FIELDS')
    a = auth()
    approval = {'sha256': FRAME_SHA, 'status': 'APPROVED', 'asset_registry_id': FRAME_ROW}
    pf = preflight(JOB, snap, load_hash_pins(PINS), str(frame_path), approval, provider, LEDGER, SCOPE_GEN,
                   source_upload=source_upload, authorisation=a)
    if pf['blockers']:
        problems.append('PREFLIGHT_BLOCKERS:' + ','.join(pf['blockers']))
    runner_checks = validate_pre_generation(req, provider, a, LEDGER, snap, approval, source_upload)
    a.matches(req)
    gate = {'validation': checks, 'final_request_body': body, 'final_request_body_wire_bytes': len(wire),
            'FINAL_REQUEST_BODY_SHA256': hashlib.sha256(wire).hexdigest(), 'endpoint': transport.base + rec['endpoint'],
            'spend_authorisation': {**asdict(a), 'maximum_authorised_cost_usd': MAX_COST}, 'preflight': pf,
            'runner_validate_pre_generation': runner_checks, 'generation_attempts_so_far': LEDGER.attempts(SCOPE_GEN),
            'problems': problems, 'gate': 'PASS' if not problems else 'STOP'}
    (D / 'S028_FINAL_GATE_v2.json').write_text(json.dumps(gate, indent=1, default=str, ensure_ascii=False))
    print(json.dumps({k: v for k, v in gate.items() if k not in ('final_request_body', 'preflight', 'validation')}, indent=1, default=str))

elif mode == 'submit':
    gate = json.loads((D / 'S028_FINAL_GATE_v2.json').read_text())
    up = json.loads((D / 'S028_SOURCE_UPLOAD_v1.json').read_text())
    a = SpendAuthorisation(**{k: v for k, v in gate['spend_authorisation'].items() if k != 'maximum_authorised_cost_usd'})
    if gate['gate'] != 'PASS' or LEDGER.attempts(a.approval_scope_id) != 0:
        sys.exit('STOP: gate not PASS or a generation attempt already exists for this scope')
    source_upload = {**up['upload'], 'readback': 'SHA256_MATCH'}
    frame_path = work / f'{FRAME_ID}.png'
    req = build_request(frame_path, source_upload['public_url'])
    transport = HiggsfieldApiTransport()
    _, rec = resolve_model(transport.cfg, MODEL)
    wire = json.dumps(serialize_request(req, rec, req.source_frame_url), separators=(',', ':')).encode()
    if hashlib.sha256(wire).hexdigest() != gate['FINAL_REQUEST_BODY_SHA256']:
        sys.exit('STOP: body differs from frozen FINAL_REQUEST_BODY_SHA256')

    class LoggedProvider(HiggsfieldProvider):
        def submit(self, request):
            rid = super().submit(request)
            r = self.transport.requests[rid]
            sent = json.dumps(r['payload'], separators=(',', ':')).encode()
            LEDGER.append('SUBMIT_ACCEPTED', a.approval_scope_id, provider_request_id=rid, status_url=r['status_url'],
                          cancel_url=r['cancel_url'], initial_status=r['initial_status'], sent_body_sha256=hashlib.sha256(sent).hexdigest())
            return rid

        def poll(self, rid):
            try:
                s = super().poll(rid)
            except FailClosed as e:
                LEDGER.append('POLL_STOP', a.approval_scope_id, provider_request_id=rid, code=e.code, detail=str(e.detail)[:300])
                raise
            LEDGER.append('POLL', a.approval_scope_id, provider_request_id=rid, status=s.get('provider_status'),
                          output_url=s.get('output_url'), usage=s.get('usage'), detail=s.get('detail'))
            return s

        def fetch(self, rid, dest):
            try:
                return super().fetch(rid, dest)
            except FailClosed as e:
                LEDGER.append('RETRIEVAL_STOP', a.approval_scope_id, provider_request_id=rid, code=e.code,
                              detail=str(e.detail)[:300], output_url=self.transport.outputs.get(rid))
                raise

    provider = LoggedProvider(transport=transport)
    snap = build_snapshot(READINESS, shots=['S028'])
    try:
        result = run_once(req, provider, a, LEDGER, work / 'raw', snap, {'sha256': FRAME_SHA, 'status': 'APPROVED'},
                          poll_interval=10.0, max_polls=180, source_upload=source_upload)
    except FailClosed as e:
        print(json.dumps({'stopped': e.code, 'detail': str(e.detail)[:400]}, indent=1))
        sys.exit(2)
    print(json.dumps({'result': result.to_dict(), 'output_url': transport.outputs}, indent=1, default=str))
else:
    sys.exit('mode must be validate|upload|gate|submit')
