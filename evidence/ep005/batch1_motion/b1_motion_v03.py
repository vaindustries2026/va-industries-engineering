"""EP005 Batch 1 real motion pass v03: Kling 3.0 Turbo image-to-video for S005 / S013 / S017 / S019 (one call each).

Usage (repo root):
  python3 evidence/ep005/batch1_motion/b1_motion_v03.py prepare <work dir>          (G03 frames, uploads, lock packages)
  python3 evidence/ep005/batch1_motion/b1_motion_v03.py run <SID> <work dir>        (ONE paid POST, poll, retrieve; no retry)
  python3 evidence/ep005/batch1_motion/b1_motion_v03.py poll <SID> <work dir>       (read-only resume)
  python3 evidence/ep005/batch1_motion/b1_motion_v03.py sample <SID> <work dir>     (frame samples for visual QC)
  python3 evidence/ep005/batch1_motion/b1_motion_v03.py assemble <SID> <work dir> <label>
Authorisation: Company Brain / Gilang 2026-10-21, max USD 1.50 total, 1 call per shot, 4 total, no retry, no fallback,
model kling-video/v3.0-turbo/image-to-video at 720p. Start image = the exact approved composed frame (approved G03 record
re-applied to the approved base frame; SHA = the record's reproduced output). Assembly = the governed
motion.compose.compose_motion_shot (G03 travels with the motion; nothing re-applied), approved ambience bed only at
+11.5 dB (the v02 corrected level), provider audio ignored (only the governed mix is muxed).
"""
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urlsplit

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
from agent008.config import load_output_spec  # noqa: E402
from agent008.episode import PINS, resolve_episode  # noqa: E402
from agent008.errors import FailClosed  # noqa: E402
from agent008.hashing import sha256_file  # noqa: E402
from agent008.inputs import load_hash_pins  # noqa: E402
from agent008.motion.authorisation import AttemptLedger  # noqa: E402
from agent008.motion.compose import compose_motion_shot  # noqa: E402
from agent008.motion.contracts import MotionRequest, MotionResult  # noqa: E402
from agent008.motion.higgsfield_transport import STATE_MAP, HiggsfieldApiTransport  # noqa: E402
from agent008.motion.http import UrllibHttpClient  # noqa: E402
from agent008.overlay import place_overlays  # noqa: E402
from agent008.tools.snapshot_inputs import build_snapshot  # noqa: E402

SB = 'https://ziluiwrwwbayhcskeere.supabase.co'
MODEL = 'kling-video/v3.0-turbo/image-to-video'
ROUTE = '/kling-video/v3.0-turbo/image-to-video'
RESOLUTION = '720p'
CEILING_USD = 1.50
AMB, BED_GAIN_DB = 'AMB-BATHROOM-QUIET-v01', 11.5
ORDER = ['S005', 'S013', 'S017', 'S019']
FRAMES = {'S005': 'FRAME-EP005-F01-BASE-CAND-v02', 'S013': 'FRAME-EP005-F01-BASE-CAND-v02',
          'S017': 'FRAME-EP005-F09-BASE-CAND-v01', 'S019': 'FRAME-EP005-F15-BASE-CAND-v02'}
COMMON = ('Locked camera: no zoom, no pan, no cut. Keep everything exactly as in the image: Mikko the honey-brown bear cub, '
          'Lumi the small round glowing golden-white orb with tiny hands, the bathroom, and the pink flower-shaped hand mirror. '
          "The berry smudges stay fixed on the same spots of Mikko's face and do not move, change or disappear. No speaking, "
          'no talking mouth movement, no new objects or characters, no extra limbs, no morphing.')
PROMPTS = {
    'S005': ('Gentle, restrained children\'s cartoon animation. Mikko studies his reflection in the hand mirror: in the mirror '
             'his face blinks once naturally, breathes softly and his head settles very slightly, his eyes moving gently over the '
             'three berry smudges on his cheek, his nose and beside his mouth. Mikko\'s own head and shoulder in the foreground '
             'move slightly with his breathing, matching the reflection. Lumi hovers gently with a tiny up-and-down float while '
             'holding the mirror steady; the mirror settles slightly in her tiny hands. ' + COMMON),
    'S013': ('Gentle, restrained children\'s cartoon animation. Mikko calmly studies the two remaining berry smudges in the hand '
             'mirror: in the mirror his face blinks once naturally and his eyes move slowly from the smudge on his nose to the '
             'smudge beside his mouth, with very small breathing and head movement. Mikko\'s own head and shoulder in the '
             'foreground move slightly with his breathing, matching the reflection. Lumi hovers gently and keeps the mirror '
             'steady. ' + COMMON),
    'S017': ('Gentle, restrained children\'s cartoon animation. Mikko, standing on the left with the blue cloth in his hand, '
             'shifts his attention slightly toward the hand mirror with a small natural head turn, blinks once and his eyes move '
             'gently. His reflection in the mirror follows the same small movement exactly, as one and the same Mikko. Lumi '
             'floats gently beside him with a soft hovering motion, holding the mirror steady. The berry smudge stays on Mikko\'s '
             'nose and on the nose of his reflection. ' + COMMON),
    'S019': ('Gentle, restrained children\'s cartoon animation. Close-up of the pink flower-shaped hand mirror. Mikko\'s reflected '
             'face shows restrained natural life: a soft blink, subtle breathing and a tiny reaction in his eyes as he notices '
             'the berry smudge on his nose. Lumi\'s tiny hand holding the mirror handle makes a very small steadying movement. '
             'The mirror stays stable and readable and keeps its exact shape. ' + COMMON),
}
LEDGER = AttemptLedger(HERE / 'B1_MOTION_V03_LEDGER_v1.jsonl')
PKG = HERE / 'B1_MOTION_V03_PACKAGES_v1.json'
http = UrllibHttpClient()


def sha(b):
    return hashlib.sha256(b).hexdigest()


def body_sha(body):
    return sha(json.dumps(body, sort_keys=True, separators=(',', ':')).encode())


def get(path):
    r = http.send('GET', f'{SB}{path}', {'Accept': 'application/json'}, None, 120.0)
    if r.status != 200:
        raise SystemExit(f'STOP: GET {path} HTTP {r.status}')
    return r


def specs():
    return {x['shot_id']: x.get('spec') for x in resolve_episode(build_snapshot('69bff641-e056-4701-a23f-d91dbc2039b2'),
                                                                 load_hash_pins(PINS), load_output_spec())}


def registry():
    return {r['asset_id']: r for r in json.loads(get('/rest/v1/asset_registry?or=(asset_id.like.FRAME-EP005-F*,asset_id.like.'
                                                     'OVERLAY-EP005-BERRY-SMUDGE-*,asset_id.like.G03-REC-EP005-*,asset_id.eq.'
                                                     f'{AMB})&select=*').body)}


def inputs(work, reg):
    out = {}
    for aid, r in reg.items():
        if not r['storage_path']:
            continue
        p = Path(work) / 'inputs' / Path(r['storage_path']).name
        p.parent.mkdir(parents=True, exist_ok=True)
        if not p.exists():
            p.write_bytes(get(f"/storage/v1/object/authenticated/{r['storage_path']}").body)
        if r['status'] != 'APPROVED' or sha256_file(p) != r['metadata_json']['sha256']:
            raise SystemExit(f'STOP: {aid} not APPROVED at its registry SHA')
        out[aid] = p
    return out


def g03_frame(work, sid, sp, reg, files):
    fr, rec = reg[FRAMES[sid]], reg[f'G03-REC-EP005-{sid}-v01']
    md = rec['metadata_json']
    out = Path(work) / 'g03' / sid
    png = out / f'{sid}_G03_OVERLAY_FRAME_CANDIDATE.png'
    if png.exists():
        prov = json.loads((out / f'{sid}_G03_OVERLAY_PROVENANCE.json').read_text())
    else:
        frame = {'asset_id': fr['asset_id'], 'registry_id': fr['id'], 'classification': 'SHOT_FRAME/BASE_FRAME',
                 'registry_status': 'APPROVED', 'shot_id': sid, 'path': str(files[fr['asset_id']]),
                 'expected_sha256': fr['metadata_json']['sha256']}
        prov = place_overlays(sp, frame, {o['asset_id']: str(files[o['asset_id']]) for o in sp['active_overlays']},
                              {'record': md['record'], 'approval_status': 'APPROVED', 'expected_sha256': md['record_sha256']}, out)
    if rec['status'] != 'APPROVED' or prov['output']['sha256'] != md['reproduced_g03_output_sha256'] or sha256_file(png) != prov['output']['sha256']:
        raise SystemExit(f'STOP {sid}: approved composed frame not reproduced exactly')
    return png, prov


def prepare(work):
    sp_all, reg = specs(), registry()
    files = inputs(work, reg)
    t = HiggsfieldApiTransport()
    pk = {'authorisation': {'by': 'Gilang / Company Brain', 'date': '2026-10-21', 'max_total_spend_usd': CEILING_USD,
                            'shots': ORDER, 'calls_max_per_shot': 1, 'total_calls_max': 4, 'retries': 0,
                            'fallback_model': 'NONE', 'alternate_generations': 0, 'model': MODEL, 'resolution': RESOLUTION},
          'endpoint': 'POST https://api.higgsfield.ai' + ROUTE,
          'schema_basis': 'official model id from the authorisation; parameters corroborated by the Higgsfield catalog entry '
                          'kling3_0_turbo (resolution 720p|1080p, duration 3-15 whole seconds, single start_image, no sound '
                          'parameter); image_url field = the governed Higgsfield image-to-video contract (Seedance / Kling 3.0); '
                          'aspect follows the 16:9 source image (no aspect field sent)',
          'packages': {}}
    for sid in ORDER:
        sp = sp_all[sid]
        png, prov = g03_frame(work, sid, sp, reg, files)
        data = png.read_bytes()
        rec = t.prepare_source_upload(data, 'image/png', sha(data), verify_readback=False)
        u = urlsplit(rec['public_url'])
        if u.query or u.fragment:
            raise SystemExit('STOP: public URL carries a query (signed?)')
        rb = http.send('GET', rec['public_url'], {}, None, 120.0)
        if rb.status != 200 or sha(rb.body) != sha(data):
            raise SystemExit(f'STOP {sid}: start-image readback failed')
        LEDGER.append('START_IMAGE_UPLOADED', f'EP005-B1V3-MOTION-{sid}', shot_id=sid, sha256=sha(data), bytes=len(data),
                      public_url=rec['public_url'], upload_host=rec['upload_host'], readback='SHA256_MATCH')
        duration = int(sp['duration_seconds'])
        body = {'prompt': PROMPTS[sid], 'image_url': rec['public_url'], 'duration': duration, 'resolution': RESOLUTION}
        pk['packages'][sid] = {'SHOT_ID': sid, 'PROMPT_TEXT': PROMPTS[sid], 'PROMPT_SHA256': sha(PROMPTS[sid].encode()),
                               'REQUEST_BODY': body, 'REQUEST_BODY_SHA256': body_sha(body),
                               'start_image': {'kind': 'approved composed frame (base frame + approved G03 record)',
                                               'sha256': sha(data), 'base_frame': FRAMES[sid],
                                               'g03_record': f'G03-REC-EP005-{sid}-v01',
                                               'g03_record_sha256': reg[f'G03-REC-EP005-{sid}-v01']['metadata_json']['record_sha256'],
                                               'overlays_composited': prov['overlays_composited']},
                               'duration_s': duration, 'frames_required': sp['frames'], 'submitted': False}
        print(sid, pk['packages'][sid]['PROMPT_SHA256'][:16], pk['packages'][sid]['REQUEST_BODY_SHA256'][:16], len(PROMPTS[sid]))
    PKG.write_text(json.dumps(pk, indent=1, ensure_ascii=False) + '\n')


def cost_fields(o, path=''):
    keys = ('cost', 'price', 'credit', 'usage', 'billing', 'amount', 'charge')
    found = {}
    if isinstance(o, dict):
        for k, v in o.items():
            p = f'{path}.{k}' if path else k
            if any(c in k.lower() for c in keys):
                found[p] = v
            found |= cost_fields(v, p)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            found |= cost_fields(v, f'{path}[{i}]')
    return found


def scope(sid):
    return f'EP005-B1V3-MOTION-{sid}'


def locked(sid, lock_commit):
    want = subprocess.run(['git', 'show', f'{lock_commit}:evidence/ep005/batch1_motion/{PKG.name}'], cwd=ROOT,
                          capture_output=True, check=True).stdout
    if PKG.read_bytes() != want:
        raise SystemExit('STOP: package file differs from the lock commit')
    p = json.loads(want)['packages'][sid]
    if sha(p['PROMPT_TEXT'].encode()) != p['PROMPT_SHA256'] or body_sha(p['REQUEST_BODY']) != p['REQUEST_BODY_SHA256']:
        raise SystemExit(f'STOP {sid}: locked hashes do not verify')
    return p


def known_spend():
    rows = [json.loads(x) for x in LEDGER.path.read_text().splitlines() if x.strip()] if LEDGER.path.exists() else []
    vals = [r['actual_cost_usd'] for r in rows if r['event'] == 'COST_RECORDED' and isinstance(r.get('actual_cost_usd'), (int, float))]
    return round(sum(vals), 4), len(vals)


def run(sid, work, lock_commit):
    p = locked(sid, lock_commit)
    calls = [json.loads(x) for x in LEDGER.path.read_text().splitlines() if x.strip() and json.loads(x)['event'] == 'GENERATION_RESERVED']
    if any(c['approval_scope_id'] == scope(sid) for c in calls):
        raise SystemExit(f'STOP {sid}: ATTEMPT_LIMIT_REACHED')
    if len(calls) >= 4:
        raise SystemExit('STOP: TOTAL_CALLS_MAX reached')
    spent, n_known = known_spend()
    if spent >= CEILING_USD or (n_known and spent / n_known > CEILING_USD - spent):
        raise SystemExit(f'STOP: known spend {spent} leaves no room under the {CEILING_USD} ceiling for another shot')
    if http.send('HEAD', p['REQUEST_BODY']['image_url'], {}).status != 200:
        raise SystemExit(f'STOP {sid}: start image unreachable')
    payload = dict(sorted(p['REQUEST_BODY'].items()))
    if sha(json.dumps(payload, separators=(',', ':')).encode()) != p['REQUEST_BODY_SHA256']:
        raise SystemExit(f'STOP {sid}: serialised body differs from the lock')
    LEDGER.append('GENERATION_RESERVED', scope(sid), shot_id=sid, attempt=1, model=MODEL, endpoint=ROUTE,
                  prompt_sha256=p['PROMPT_SHA256'], request_body_sha256=p['REQUEST_BODY_SHA256'], known_spend_before_usd=spent,
                  pre_submit_price='NOT EXPOSED by the API (no price/estimate route)')
    t = HiggsfieldApiTransport()
    try:
        resp, _ = t._api('POST', ROUTE, payload, {'Idempotency-Key': f'{scope(sid)}-1-{p["REQUEST_BODY_SHA256"][:16]}'})
    except FailClosed as e:
        LEDGER.append('GENERATION_SUBMIT_TRANSPORT_ERROR', scope(sid), code=e.code, note='outcome unknown; NOT retried')
        raise SystemExit(f'STOP {sid}: transport error {e.code}')
    try:
        data = json.loads(resp.body)
    except ValueError:
        data = resp.body[:400].decode('utf-8', 'replace')
    LEDGER.append('GENERATION_SUBMITTED', scope(sid), shot_id=sid, http_status=resp.status, response=data,
                  headers={k: v for k, v in resp.headers.items() if k.lower() in ('date', 'cf-ray')},
                  cost_fields=cost_fields(data) if isinstance(data, dict) else {})
    if resp.status != 200 or not isinstance(data, dict) or not data.get('request_id'):
        LEDGER.append('GENERATION_FAILED', scope(sid), stage='submit', http_status=resp.status, retried=False)
        raise SystemExit(f'STOP {sid}: submit HTTP {resp.status}: {str(data)[:300]}')
    print(sid, 'submitted', data.get('request_id'), data.get('status'))
    retrieve(sid, work, poll(sid))


def poll(sid):
    rows = [json.loads(x) for x in LEDGER.path.read_text().splitlines() if x.strip()]
    sub = [r for r in rows if r['approval_scope_id'] == scope(sid) and r['event'] == 'GENERATION_SUBMITTED' and r['http_status'] == 200]
    rid = sub[0]['response']['request_id']
    t = HiggsfieldApiTransport()
    last = None
    for i in range(1, 301):
        resp, _ = t._api('GET', t.status_route(rid))
        data = json.loads(resp.body) if resp.status == 200 else None
        st = data.get('status') if isinstance(data, dict) else None
        if st != last:
            LEDGER.append('POLL', scope(sid), request_id=rid, poll=i, http_status=resp.status, provider_status=st)
            last = st
        if st in STATE_MAP and STATE_MAP[st] in ('COMPLETED', 'FAILED'):
            LEDGER.append('TERMINAL', scope(sid), request_id=rid, polls=i, provider_status=st, final_status_response=data,
                          cost_fields=cost_fields(data))
            return data
        time.sleep(6)
    LEDGER.append('POLL_WINDOW_EXHAUSTED', scope(sid), request_id=rid, last_status=last)
    raise SystemExit(f'PAUSE {sid}: not terminal; resume with poll (no resubmit)')


def retrieve(sid, work, data):
    cf = cost_fields(data)
    usd = next((v for k, v in cf.items() if isinstance(v, (int, float)) and ('usd' in k.lower() or 'cost' in k.lower())), None)
    LEDGER.append('COST_RECORDED', scope(sid), cost_fields=cf, actual_cost_usd=usd,
                  note=None if usd is not None else 'provider exposed no cost for this request')
    if data.get('status') != 'completed':
        LEDGER.append('GENERATION_FAILED', scope(sid), stage='terminal', provider_status=data.get('status'), retried=False)
        print(sid, 'terminal', data.get('status'))
        return
    url = (data.get('video') or {}).get('url') or ((data.get('videos') or [{}])[0] or {}).get('url')
    if not url or not url.startswith('https://'):
        LEDGER.append('GENERATION_OUTPUT_MALFORMED', scope(sid), keys=sorted(data))
        raise SystemExit(f'STOP {sid}: no video url in the completed response')
    d = Path(work) / 'raw' / sid
    d.mkdir(parents=True, exist_ok=False)
    r = http.send('GET', url, {}, None, 300.0)
    if r.status != 200 or not r.body:
        LEDGER.append('OUTPUT_DOWNLOAD_FAILED', scope(sid), http_status=r.status, output_url=url)
        raise SystemExit(f'STOP {sid}: download HTTP {r.status} (the provider copy stays on the CDN)')
    raw = d / Path(urlsplit(url).path).name
    raw.write_bytes(r.body)
    raw.chmod(0o444)
    pr = json.loads(subprocess.run(['ffprobe', '-v', 'error', '-count_frames', '-show_streams', '-show_format', '-of', 'json', str(raw)],
                                   capture_output=True, check=True).stdout)
    v = [s for s in pr['streams'] if s['codec_type'] == 'video'][0]
    a = [s for s in pr['streams'] if s['codec_type'] == 'audio']
    rec = {'SHOT_ID': sid, 'REQUEST_ID': data['request_id'], 'ATTEMPT': 1, 'RAW_VIDEO_SHA256': sha(r.body), 'RAW_BYTES': len(r.body),
           'RAW_DURATION': float(pr['format']['duration']), 'RAW_DIMENSIONS': f"{v['width']}x{v['height']}",
           'RAW_FPS': v['r_frame_rate'], 'RAW_FRAMES': int(v['nb_read_frames']), 'RAW_CODEC': v['codec_name'],
           'RAW_AUDIO_PRESENT': bool(a), 'output_url': url, 'raw_file': raw.name, 'md5': hashlib.md5(r.body).hexdigest(),
           'response_headers': {k: v for k, v in r.headers.items() if k.lower() in ('content-type', 'content-length', 'etag',
                                                                                    'x-amz-expiration', 'last-modified')},
           'status': 'RAW_MOTION_SOURCE / REVIEW (not approved)'}
    LEDGER.append('RAW_OUTPUT_PRESERVED', scope(sid), **rec)
    print(json.dumps({k: v for k, v in rec.items() if k != 'response_headers'}, indent=1))


def raw_rec(sid):
    rows = [json.loads(x) for x in LEDGER.path.read_text().splitlines() if x.strip()]
    return next(r for r in rows if r['approval_scope_id'] == scope(sid) and r['event'] == 'RAW_OUTPUT_PRESERVED')


def sample(sid, work):
    rr = raw_rec(sid)
    raw = Path(work) / 'raw' / sid / rr['raw_file']
    d = Path(work) / 'qc' / sid
    d.mkdir(parents=True, exist_ok=True)
    n = rr['RAW_FRAMES']
    idx = [0, round((n - 1) * 0.25), round((n - 1) * 0.5), round((n - 1) * 0.75), n - 1]
    for k, i in zip(('000', '025', '050', '075', '100'), idx):
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(raw), '-vf', f'select=eq(n\\,{i})', '-frames:v', '1',
                        str(d / f'{sid}_{k}.png')], check=True)
    return idx


def assemble(sid, work, label):
    p = json.loads(PKG.read_text())['packages'][sid]
    rr = raw_rec(sid)
    sp, reg = specs()[sid], registry()
    files = inputs(work, reg)
    png, prov = g03_frame(work, sid, sp, reg, files)
    req = MotionRequest(sid, str(png), p['start_image']['sha256'], p['PROMPT_TEXT'], '', p['duration_s'], '16:9', RESOLUTION, 24,
                        'higgsfield', MODEL, scope(sid), {}, p['REQUEST_BODY']['image_url'])
    res = MotionResult('higgsfield', MODEL, rr['REQUEST_ID'], p['start_image']['sha256'], req.prompt_sha256, 'COMPLETED',
                       str(Path(work) / 'raw' / sid / rr['raw_file']), rr['RAW_VIDEO_SHA256'], rr['raw_file'], rr['RAW_BYTES'],
                       rr['RAW_DURATION'], rr['RAW_DIMENSIONS'], rr['RAW_FPS'], rr['RAW_CODEC'])
    out = Path(work) / 'assembly' / label / sid
    prov_m = compose_motion_shot(res, req, sp, load_output_spec(), {AMB: files[AMB]}, {'beds': {AMB: {'gain_db': BED_GAIN_DB}}},
                                 out, overlays_composited=prov['overlays_composited'])
    (out / 'ASSEMBLY_PROVENANCE.json').write_text(json.dumps(prov_m, indent=1, default=str))
    print(sid, label, prov_m['outputs']['review_mp4']['sha256'] if 'outputs' in prov_m else prov_m.keys(), prov_m['qc'].get('automatic_result'),
          prov_m['qc'].get('issues'))


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'prepare':
        prepare(sys.argv[2])
    elif cmd == 'run':
        run(sys.argv[2], sys.argv[3], sys.argv[4])
    elif cmd == 'poll':
        retrieve(sys.argv[2], sys.argv[3], poll(sys.argv[2]))
    elif cmd == 'sample':
        print(sample(sys.argv[2], sys.argv[3]))
    elif cmd == 'assemble':
        assemble(sys.argv[2], sys.argv[3], sys.argv[4])
