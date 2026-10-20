"""EP005 Batch 1 v2 image run: F01 v02, F03 v02, F15 dedicated - one Flare call each, no retry.

Usage (repo root):
  python3 evidence/ep005/batch1_base_frames/b1v2_generate.py verify <work dir>
  python3 evidence/ep005/batch1_base_frames/b1v2_generate.py run F01_V02|F03_V02|F15_V02 <work dir>
  python3 evidence/ep005/batch1_base_frames/b1v2_generate.py poll F01_V02|F03_V02|F15_V02 <work dir>   (read-only resume)
  python3 evidence/ep005/batch1_base_frames/b1v2_generate.py normalise F01_V02|F03_V02|F15_V02 <work dir>
Same mechanics as b1_generate.py (v1 run): packages are read from their lock commits and must equal the working copy;
the POST sends the compact sorted-key JSON whose sha256 is the locked body hash; one GENERATION_RESERVED per package,
ever; raw kept unmodified as LOCKED_ORIGINAL_FOR_NORMALISATION; G04 exact 16:9 crop + 1920x1080, two runs identical.
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
sys.path.insert(0, str(HERE))
from agent008.derive import count_frames, derive_frame  # noqa: E402
from agent008.errors import FailClosed  # noqa: E402
from agent008.hashing import sha256_file  # noqa: E402
from agent008.motion.authorisation import AttemptLedger  # noqa: E402
from agent008.motion.higgsfield_transport import STATE_MAP, HiggsfieldApiTransport  # noqa: E402
from b1_generate import GOVERNED, POLL_INTERVAL_S, POLL_MAX, ROUTE, body_bytes, cost_fields, http, sb_get, sha  # noqa: E402
from b1_normalisation_proof import normalisation_crop  # noqa: E402

LEDGER = AttemptLedger(HERE / 'B1V2_GENERATION_LEDGER_v1.jsonl')
PACKAGES = {  # package: (lock commit, file, key in file or None, locked prompt sha, locked body sha, candidate id)
    'F01_V02': ('3775b46d81bc6ba4c4251b0e669671ecbc25c881', 'B1_V02_CORRECTION_PACKAGES_v1.json', 'F01_V02',
                '6e3d11009d290121c19be55b3cc46fc2e91b3918805be42ce3e5159d7ca5d5c3',
                'f46b79b834b13b2a3384b869d1ade2f46ca34a76290dbe397665f3d1e0cb2f30', 'FRAME-EP005-F01-BASE-CAND-v02'),
    'F03_V02': ('3775b46d81bc6ba4c4251b0e669671ecbc25c881', 'B1_V02_CORRECTION_PACKAGES_v1.json', 'F03_V02',
                '4e68b6a408cc259d672ef3158a870cb0a3d35738b1f40cafd9df4d6855832782',
                'a5a5bef2fa28063daf425c97f1622634600dd42b5134f0fb630b4295ee955a2c', 'FRAME-EP005-F03-BASE-CAND-v02'),
    'F15_V02': ('90689a7f56d2550a22cec079c4d6cb09c211ce8e', 'B1_F15_DEDICATED_PACKAGE_v1.json', None,
                '3072bf65e56ace2ca43bb649d4c90c86bd8aad6b55fce05a601e31405a61bbae',
                '0ed33b69d5c4c01e8cd12e9cc637e946a4223897b2c0353a486e47cba80cf6d9', 'FRAME-EP005-F15-BASE-CAND-v02'),
}
REL = 'evidence/ep005/batch1_base_frames/'


def scope(p):
    return f'EP005-B1V2-BASEFRAME-FLARE-{p}'


def load(p):
    commit, fname, key, *_ = PACKAGES[p]
    locked = subprocess.run(['git', 'show', f'{commit}:{REL}{fname}'], cwd=ROOT, capture_output=True, check=True).stdout
    if (HERE / fname).read_bytes() != locked:
        raise FailClosed('PACKAGE_FILE_DIFFERS_FROM_LOCK_COMMIT', fname)
    doc = json.loads(locked)
    return (doc['packages'][key] if key else doc), doc['references_in_order']


def check(p):
    pkg, refs = load(p)
    want_p, want_b = PACKAGES[p][3], PACKAGES[p][4]
    body = pkg['request_body_exact']
    gp, gb = sha(body['prompt'].encode()), sha(body_bytes(body))
    ok = (gp == want_p == pkg['PROMPT_SHA256'] and gb == want_b == pkg['REQUEST_BODY_SHA256'] and pkg['submitted'] is False
          and body['image_urls'] == [r['public_url'] for r in refs]
          and [r['asset_id'] for r in refs] == list(GOVERNED) and all(r['sha256'] == GOVERNED[r['asset_id']] for r in refs))
    return ok, gp, gb, pkg, refs


def attempts(p):
    return sum(1 for r in LEDGER.entries(scope(p)) if r['event'] == 'GENERATION_RESERVED')


def verify(work):
    t = HiggsfieldApiTransport()
    resp, _ = t._api('GET', t.status_route('0d6997fe-6c53-487e-8477-242e60c80c75'))
    out = {'auth': {'probe': 'GET /requests/0d6997fe-.../status', 'http_status': resp.status,
                    'result': 'VERIFIED' if resp.status == 200 else 'FAILED'}}
    _, _, _, _, refs = check('F15_V02')
    rr = []
    for r in refs:
        g = http.send('GET', r['public_url'], {})
        got = sha(g.body) if g.status == 200 else None
        rr.append({'n': r['n'], 'asset_id': r['asset_id'], 'http_status': g.status, 'sha256': got,
                   'matches_governance': got == GOVERNED[r['asset_id']]})
    out['references'] = rr
    out['packages'] = {}
    for p in PACKAGES:
        ok, gp, gb, _, _ = check(p)
        out['packages'][p] = {'package_sha_match': ok, 'prompt_sha256': gp, 'request_body_sha256': gb,
                              'attempts_used': attempts(p), 'attempts_max': 1}
    rows = sb_get('asset_registry?asset_id=like.*-v02&select=asset_id,status')
    out['existing_v02_frame_rows'] = [x for x in rows if x['asset_id'].startswith('FRAME-EP005-F')]
    out['pre_submit_price_or_estimate'] = 'NOT EXPOSED by the provider (no price/estimate route)'
    out['auto_retry_mechanism'] = 'NONE (one http.send per POST; ledger blocks a second reservation)'
    out['PASS'] = (out['auth']['result'] == 'VERIFIED' and all(r['matches_governance'] for r in rr)
                   and all(v['package_sha_match'] and v['attempts_used'] == 0 for v in out['packages'].values())
                   and not out['existing_v02_frame_rows'])
    LEDGER.append('PRE_SUBMIT_VERIFIED' if out['PASS'] else 'PRE_SUBMIT_FAILED', 'EP005-B1V2-BASEFRAME-FLARE', **out)
    (Path(work) / 'v2_verify.json').write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))
    return out['PASS']


def submit(p):
    ok, gp, gb, pkg, refs = check(p)
    if not ok:
        LEDGER.append('PACKAGE_STOPPED_SHA_MISMATCH', scope(p), prompt_sha256=gp, request_body_sha256=gb)
        sys.exit(f'STOP {p}: package SHA mismatch')
    if attempts(p) >= 1:
        sys.exit(f'STOP {p}: ATTEMPT_LIMIT_REACHED')
    for r in refs:
        h = http.send('HEAD', r['public_url'], {})
        if h.status != 200:
            LEDGER.append('PACKAGE_STOPPED_REFERENCE_UNREACHABLE', scope(p), asset_id=r['asset_id'], http_status=h.status)
            sys.exit(f'STOP {p}: reference {r["asset_id"]} HTTP {h.status}')
    payload = dict(sorted(pkg['request_body_exact'].items()))
    sent = json.dumps(payload, separators=(',', ':')).encode()
    if sha(sent) != PACKAGES[p][4]:
        sys.exit(f'STOP {p}: serialised bytes differ from the locked body')
    LEDGER.append('GENERATION_RESERVED', scope(p), package=p, frame_id=PACKAGES[p][5], attempt_number=1, max_attempts=1,
                  endpoint='https://api.higgsfield.ai' + ROUTE, prompt_sha256=PACKAGES[p][3],
                  request_body_sha256=PACKAGES[p][4], sent_bytes_sha256=sha(sent))
    t = HiggsfieldApiTransport()
    t0 = time.time()
    try:
        resp, _ = t._api('POST', ROUTE, payload, {'Idempotency-Key': f'{scope(p)}-attempt-1-{PACKAGES[p][4][:16]}'})
    except FailClosed as e:
        LEDGER.append('GENERATION_SUBMIT_TRANSPORT_ERROR', scope(p), code=e.code, detail=str(e.detail)[:200],
                      note='outcome unknown; NOT retried')
        sys.exit(f'STOP {p}: transport error {e.code} (no retry)')
    try:
        data = json.loads(resp.body)
    except ValueError:
        data = None
    hdr = {k: v for k, v in resp.headers.items() if k.lower() in ('date', 'cf-ray', 'content-type')}
    LEDGER.append('GENERATION_SUBMITTED', scope(p), package=p, http_status=resp.status, elapsed_s=round(time.time() - t0, 3),
                  headers=hdr, response=data if isinstance(data, dict) else resp.body[:300].decode('utf-8', 'replace'),
                  cost_fields=cost_fields(data))
    if resp.status != 200 or not isinstance(data, dict) or not data.get('request_id'):
        LEDGER.append('GENERATION_FAILED', scope(p), package=p, stage='submit', http_status=resp.status, retried=False)
        sys.exit(f'STOP {p}: submit HTTP {resp.status} (no retry)')
    print(p, 'submitted', resp.status, data.get('request_id'), data.get('status'))


def request_id(p):
    rows = [r for r in LEDGER.entries(scope(p)) if r['event'] == 'GENERATION_SUBMITTED' and r['http_status'] == 200]
    if len(rows) != 1:
        raise FailClosed('REQUEST_ID_UNKNOWN', p)
    return rows[0]['response']['request_id']


def poll(p):
    rid = request_id(p)
    t = HiggsfieldApiTransport()
    route, last = t.status_route(rid), None
    for i in range(1, POLL_MAX + 1):
        resp, _ = t._api('GET', route)
        data = json.loads(resp.body) if resp.status == 200 else None
        st = data.get('status') if isinstance(data, dict) else None
        if st != last:
            LEDGER.append('POLL', scope(p), package=p, request_id=rid, poll=i, http_status=resp.status, provider_status=st)
            last = st
        if st in STATE_MAP and STATE_MAP[st] in ('COMPLETED', 'FAILED'):
            LEDGER.append('TERMINAL', scope(p), package=p, request_id=rid, polls=i, provider_status=st,
                          final_status_response=data, cost_fields=cost_fields(data))
            return data
        time.sleep(POLL_INTERVAL_S)
    LEDGER.append('POLL_WINDOW_EXHAUSTED', scope(p), package=p, request_id=rid, polls=POLL_MAX, last_status=last)
    sys.exit(f'PAUSE {p}: not terminal; resume with poll (no resubmit)')


def retrieve(p, work, data):
    if data.get('status') != 'completed':
        LEDGER.append('GENERATION_FAILED', scope(p), package=p, stage='terminal', provider_status=data.get('status'),
                      retried=False)
        print(f'{p}: terminal {data.get("status")} (recorded; no retry)')
        return
    imgs = data.get('images') or []
    if len(imgs) != 1 or not str((imgs[0] or {}).get('url', '')).startswith('https://'):
        LEDGER.append('GENERATION_OUTPUT_MALFORMED', scope(p), package=p, images=len(imgs))
        sys.exit(f'STOP {p}: expected exactly 1 image')
    url = imgs[0]['url']
    raw_dir = Path(work) / p / 'raw'
    raw_dir.mkdir(parents=True, exist_ok=False)
    r = http.send('GET', url, {}, None, 120.0)
    if r.status != 200 or not r.body:
        LEDGER.append('OUTPUT_DOWNLOAD_FAILED', scope(p), package=p, http_status=r.status, output_url=url)
        sys.exit(f'STOP {p}: output download HTTP {r.status} (provider copy stays on the CDN)')
    raw = raw_dir / Path(urlsplit(url).path).name
    raw.write_bytes(r.body)
    fmt = 'PNG' if r.body[:8] == b'\x89PNG\r\n\x1a\n' else 'JPEG' if r.body[:3] == b'\xff\xd8\xff' else 'OTHER'
    n, w, h, _ = count_frames(raw)
    raw.chmod(0o444)
    rec = {'PACKAGE': p, 'PROVIDER_REQUEST_ID': data['request_id'], 'RAW_SHA256': sha(r.body), 'RAW_BYTE_SIZE': len(r.body),
           'RAW_DIMENSIONS': f'{w}x{h}', 'RAW_FORMAT': fmt, 'decoded_frames': n, 'ATTEMPT_NUMBER': 1, 'RETRY_COUNT': 0,
           'output_url': url, 'raw_file': raw.name, 'md5': hashlib.md5(r.body).hexdigest(),
           'response_headers': {k: v for k, v in r.headers.items() if k.lower() in (
               'content-type', 'content-length', 'last-modified', 'etag', 'x-amz-expiration')},
           'local_state': 'LOCKED_ORIGINAL_FOR_NORMALISATION (immutable provider bytes; NOT creative approval)'}
    LEDGER.append('RAW_OUTPUT_PRESERVED', scope(p), **rec)
    print(json.dumps(rec, indent=1))


def normalise(p, work):
    raws = [r for r in LEDGER.entries(scope(p)) if r['event'] == 'RAW_OUTPUT_PRESERVED']
    if len(raws) != 1:
        sys.exit(f'STOP {p}: no single preserved raw output')
    raw = raws[0]
    path = Path(work) / p / 'raw' / raw['raw_file']
    if sha256_file(path) != raw['RAW_SHA256']:
        sys.exit(f'STOP {p}: raw bytes changed')
    w, h = (int(x) for x in raw['RAW_DIMENSIONS'].split('x'))
    try:
        crop = normalisation_crop(w, h)
    except FailClosed as e:
        LEDGER.append('NORMALISATION_STOPPED', scope(p), package=p, code=e.code, detail=e.detail)
        sys.exit(f'STOP {p}: {e.code} {e.detail}')
    crop_arg = None if crop == {'x': 0, 'y': 0, 'w': w, 'h': h} else crop
    scale = None if (w, h) == (1920, 1080) else {'w': 1920, 'h': 1080}
    cid = PACKAGES[p][5]
    src = {'asset_id': f'{cid}-RAW', 'registry_id': None, 'classification': 'LOCKED_ORIGINAL_FOR_NORMALISATION',
           'registry_status': 'LOCKED', 'path': str(path), 'expected_sha256': raw['RAW_SHA256'], 'expected_frames': 1,
           'expected_width': w, 'expected_height': h}
    provs = [derive_frame(src, 0, cid, Path(work) / p / f'norm_{x}', crop_arg, scale) for x in ('A', 'B')]
    a, b = provs[0]['output'], provs[1]['output']
    passed = a['sha256'] == b['sha256'] and a['rgb24_sha256'] == b['rgb24_sha256'] and (a['width'], a['height']) == (1920, 1080)
    pkg, refs = load(p)
    cand = {'frame_id': cid, 'status': 'REVIEW (local candidate; no registry row; no production storage)',
            'package': p, 'family': pkg['FRAME_FAMILY_ID'], 'provider_request_id': raw['PROVIDER_REQUEST_ID'],
            'prompt_sha256': PACKAGES[p][3], 'request_body_sha256': PACKAGES[p][4],
            'reference_sha256s': {r['asset_id']: r['sha256'] for r in refs},
            'raw': {k: raw[k] for k in ('RAW_SHA256', 'RAW_BYTE_SIZE', 'RAW_DIMENSIONS', 'RAW_FORMAT')},
            'normalisation': {'method': 'G04 derive_frame: frame 0, exact centred 16:9 crop, scale 1920x1080 '
                                        f"({provs[0]['recipe']['scale_flags']}), lossless PNG; no other operation",
                              'crop': crop_arg, 'scale': scale, 'source_state': 'LOCKED_ORIGINAL_FOR_NORMALISATION'},
            'NORMALISED_SHA_A': a['sha256'], 'NORMALISED_SHA_B': b['sha256'], 'NORMALISATION_DETERMINISM_PASS': passed,
            'CANONICAL_RGB_PIXEL_SHA': a['rgb24_sha256'], 'normalised_bytes': a['bytes'],
            'normalised_dimensions': f"{a['width']}x{a['height']}", 'raw_unchanged': sha256_file(path) == raw['RAW_SHA256'],
            'g03_applied': False, 'g08_applied': False,
            'human_approval': {'required': True, 'approved': False, 'approve_by': 'exact NORMALISED_SHA'}}
    LEDGER.append('NORMALISED_REVIEW_CANDIDATE' if passed else 'NORMALISATION_DETERMINISM_FAILED', scope(p), **cand)
    (HERE / f'{cid}_REVIEW_CANDIDATE.json').write_text(json.dumps(cand, indent=1) + '\n')
    print(json.dumps(cand, indent=1))
    if not passed:
        sys.exit(f'STOP {p}: normalisation A != B')


if __name__ == '__main__':
    cmd, args = sys.argv[1], sys.argv[2:]
    if cmd == 'verify':
        sys.exit(0 if verify(args[0]) else 'STOP: pre-submit verification failed')
    p, work = args
    if p not in PACKAGES:
        sys.exit(f'unknown package {p}')
    if cmd == 'run':
        submit(p)
        retrieve(p, work, poll(p))
    elif cmd == 'poll':
        retrieve(p, work, poll(p))
    elif cmd == 'normalise':
        normalise(p, work)
