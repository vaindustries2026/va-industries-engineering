"""EP005 Batch 1 base frames: the three authorised Flare calls (F01, F03, F09), one attempt each, no retry.

Usage (repo root):
  python3 evidence/ep005/batch1_base_frames/b1_generate.py verify <work dir>
  python3 evidence/ep005/batch1_base_frames/b1_generate.py run F01|F03|F09 <work dir>     (submit once, poll, retrieve)
  python3 evidence/ep005/batch1_base_frames/b1_generate.py poll F01|F03|F09 <work dir>    (read-only resume of polling)
  python3 evidence/ep005/batch1_base_frames/b1_generate.py normalise F01|F03|F09 <work dir>
Packages are read from the accepted commit c6a7dd2 and must equal the working copy byte for byte. The POST sends the
compact sorted-key JSON whose sha256 is the locked REQUEST_BODY_SHA256. A family with any GENERATION_RESERVED row in
the ledger is never submitted again. Raw outputs are kept unmodified as LOCKED_ORIGINAL_FOR_NORMALISATION (not a
creative approval); the review target is the deterministic G04 1920x1080 frame.
"""
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from agent008.derive import count_frames, derive_frame  # noqa: E402
from agent008.errors import FailClosed  # noqa: E402
from agent008.hashing import sha256_file  # noqa: E402
from agent008.motion.authorisation import AttemptLedger  # noqa: E402
from agent008.motion.higgsfield_transport import STATE_MAP, HiggsfieldApiTransport  # noqa: E402
from agent008.motion.http import UrllibHttpClient  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from b1_normalisation_proof import normalisation_crop  # noqa: E402

HERE = Path(__file__).resolve().parent
ACCEPTED = 'c6a7dd2258846e228da0dc0b6ae8cf10058ef781'
PKG_REL = 'evidence/ep005/batch1_base_frames/B1_GENERATION_PACKAGES_v1.json'
LEDGER = AttemptLedger(HERE / 'B1_GENERATION_LEDGER_v1.jsonl')
ROUTE = '/marketing-studio/image/flare'
SB = 'https://ziluiwrwwbayhcskeere.supabase.co/rest/v1/'
LOCKED = {
    'F01': ('559d3ba7b0c9ed9023df8376cdcd160b9047578418fb55bd492fdf155804cf97',
            '008adeb425bc0edea374a0b8ac6e2b09decd485db2df4d56a71f62992ac3421c'),
    'F03': ('c51d9670c8065c587a06ade5470e2908a3439bd88c64d742cc44e7e06cc9446f',
            'd86ec189aa6c3af3eecbfad88c780b8b40a3cab1076125dc5b6db329654b8411'),
    'F09': ('5bd2edc1364a1c4f5187fbe5d515c06fe19131294b13aa967a34ba4e04a12abd',
            '36d91d95cf72825ccfa9d526870b34d92ae0b3a103f1cef3ba229dd1494893cc'),
}
GOVERNED = {'CHAR-MIKKO-MASTER-v01': '41c9480a847c962c1ecfda4fe076e0abcd86548ba67f692621cfc6e13d61f1a8',
            'CHAR-LUMI-MASTER-v01': '8b29c1abea53cb253eea39cdd41d5001ed38036945b049078915ac5993c43a41',
            'WORLD-EP005-BATHROOM-MASTER-v01': 'ab79c560d3c79a05cb957331149ee4b8a176e109b06010480ba6c26903bd3733',
            'PROP-EP005-HAND-MIRROR-v01': '34fa31a132144c355714480fa82b22916fc2f825d418658bb787791a0b9c56ac',
            'PROP-EP005-CLEANING-CLOTH-v01': 'afaa3a9fcfc5b562023080318425457c5b4dda8eb58065f56ae542786637c1db',
            'DUO-MIKKO-LUMI-SCALE-v01': '735d64075af999d8a00d35afe2674174f5e0feea9b1b4acb9ec2208f1e1d121f'}
COST_KEYS = ('cost', 'price', 'credits', 'credit', 'usage', 'estimate', 'billing', 'amount')
POLL_INTERVAL_S, POLL_MAX = 6, 150
http = UrllibHttpClient()


def scope(fam):
    return f'EP005-B1-BASEFRAME-FLARE-{fam}'


def cand_id(fam):
    return f'FRAME-EP005-{fam}-BASE-CAND-v01'


def sha(b):
    return hashlib.sha256(b).hexdigest()


def body_bytes(body):
    return json.dumps(body, sort_keys=True, separators=(',', ':')).encode()


def cost_fields(obj, path=''):
    """Every key anywhere in a provider response that names a cost/credit/usage value."""
    found = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f'{path}.{k}' if path else k
            if any(c in k.lower() for c in COST_KEYS):
                found[p] = v
            found |= cost_fields(v, p)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            found |= cost_fields(v, f'{path}[{i}]')
    return found


def load_packages():
    accepted = subprocess.run(['git', 'show', f'{ACCEPTED}:{PKG_REL}'], cwd=ROOT, capture_output=True, check=True).stdout
    if (ROOT / PKG_REL).read_bytes() != accepted:
        raise FailClosed('PACKAGE_FILE_DIFFERS_FROM_ACCEPTED_COMMIT', PKG_REL)
    return json.loads(accepted)


def check_family(pkgs, fam):
    p = pkgs['packages'][fam]
    want_p, want_b = LOCKED[fam]
    got_p, got_b = sha(p['request_body_exact']['prompt'].encode()), sha(body_bytes(p['request_body_exact']))
    ok = (got_p == want_p == p['PROMPT_SHA256'] and got_b == want_b == p['REQUEST_BODY_SHA256']
          and p['request_body_exact']['image_urls'] == [r['public_url'] for r in pkgs['references_in_order']]
          and p['submitted'] is False)
    return ok, got_p, got_b


def attempts(fam):
    return sum(1 for r in LEDGER.entries(scope(fam)) if r['event'] == 'GENERATION_RESERVED')


def sb_get(path):
    r = http.send('GET', SB + path, {'Accept': 'application/json'})
    if r.status != 200:
        raise FailClosed('SUPABASE_READ_FAILED', f'{path}: HTTP {r.status}')
    return json.loads(r.body)


def verify(work):
    pkgs = load_packages()
    t = HiggsfieldApiTransport()
    out = {'at_unix': time.time(), 'accepted_commit': ACCEPTED, 'auto_retry_mechanism': 'NONE (one http.send per POST; '
           'transport layer never retries; ledger blocks a second reservation)'}
    resp, _ = t._api('GET', t.status_route('0d6997fe-6c53-487e-8477-242e60c80c75'))
    out['auth'] = {'probe': 'GET /requests/0d6997fe-.../status', 'http_status': resp.status,
                   'result': 'VERIFIED' if resp.status == 200 else 'FAILED'}
    refs = []
    for r in pkgs['references_in_order']:
        g = http.send('GET', r['public_url'], {})
        got = sha(g.body) if g.status == 200 else None
        refs.append({'n': r['n'], 'asset_id': r['asset_id'], 'http_status': g.status, 'sha256': got,
                     'matches_governance': got == GOVERNED[r['asset_id']] == r['sha256'],
                     'expiry': g.headers.get('x-amz-expiration') or g.headers.get('X-Amz-Expiration')})
    out['references'] = refs
    out['families'] = {}
    for fam in LOCKED:
        ok, gp, gb = check_family(pkgs, fam)
        out['families'][fam] = {'package_sha_match': ok, 'prompt_sha256': gp, 'request_body_sha256': gb,
                                'attempts_used': attempts(fam), 'attempts_max': 1}
    rows = sb_get('asset_registry?or=(asset_id.like.*F01*,asset_id.like.*F03*,asset_id.like.*F09*)&select=asset_id,status')
    out['existing_f01_f03_f09_registry_rows'] = rows
    out['pre_submit_price_or_estimate'] = ('NOT EXPOSED: no pre-submit price/estimate route on api.higgsfield.ai '
                                           '(pre-submit evidence c6a7dd2); ceiling USD 0.75/call, 2.25 total recorded')
    out['balance_confirmation'] = 'HIGGSFIELD_BALANCE_CONFIRMED = YES (Gilang, Company Brain final authorisation)'
    out['PASS'] = (out['auth']['result'] == 'VERIFIED' and all(r['matches_governance'] for r in refs)
                   and all(f['package_sha_match'] and f['attempts_used'] == 0 for f in out['families'].values())
                   and not rows)
    (Path(work) / 'verify.json').write_text(json.dumps(out, indent=1))
    LEDGER.append('PRE_SUBMIT_VERIFIED' if out['PASS'] else 'PRE_SUBMIT_FAILED', 'EP005-B1-BASEFRAME-FLARE',
                  **{k: out[k] for k in ('auth', 'references', 'families', 'existing_f01_f03_f09_registry_rows',
                                         'pre_submit_price_or_estimate', 'balance_confirmation', 'auto_retry_mechanism',
                                         'PASS')})
    print(json.dumps(out, indent=1))
    return out['PASS']


def submit(fam, work):
    pkgs = load_packages()
    ok, gp, gb = check_family(pkgs, fam)
    if not ok:
        LEDGER.append('FAMILY_STOPPED_PACKAGE_SHA_MISMATCH', scope(fam), prompt_sha256=gp, request_body_sha256=gb)
        sys.exit(f'STOP {fam}: package SHA mismatch')
    if attempts(fam) >= 1:
        sys.exit(f'STOP {fam}: ATTEMPT_LIMIT_REACHED (already reserved)')
    for r in pkgs['references_in_order']:
        h = http.send('HEAD', r['public_url'], {})
        if h.status != 200:
            LEDGER.append('FAMILY_STOPPED_REFERENCE_UNREACHABLE', scope(fam), asset_id=r['asset_id'], http_status=h.status)
            sys.exit(f'STOP {fam}: reference {r["asset_id"]} HTTP {h.status}')
    body = pkgs['packages'][fam]['request_body_exact']
    payload = dict(sorted(body.items()))                     # transport serialises compact, in insertion order
    sent = json.dumps(payload, separators=(',', ':')).encode()
    if sha(sent) != LOCKED[fam][1]:
        sys.exit(f'STOP {fam}: serialised bytes differ from the locked body')
    LEDGER.append('GENERATION_RESERVED', scope(fam), family=fam, frame_id=cand_id(fam), attempt_number=1, max_attempts=1,
                  endpoint='https://api.higgsfield.ai' + ROUTE, prompt_sha256=LOCKED[fam][0],
                  request_body_sha256=LOCKED[fam][1], sent_bytes_sha256=sha(sent))
    t = HiggsfieldApiTransport()
    t0 = time.time()
    try:
        resp, _ = t._api('POST', ROUTE, payload, {'Idempotency-Key': f'{scope(fam)}-attempt-1-{LOCKED[fam][1][:16]}'})
    except FailClosed as e:
        LEDGER.append('GENERATION_SUBMIT_TRANSPORT_ERROR', scope(fam), code=e.code, detail=str(e.detail)[:200],
                      note='outcome unknown; NOT retried')
        sys.exit(f'STOP {fam}: transport error {e.code} (no retry)')
    try:
        data = json.loads(resp.body)
    except ValueError:
        data = None
    hdr = {k: v for k, v in resp.headers.items() if k.lower() in ('date', 'cf-ray', 'content-type')}
    LEDGER.append('GENERATION_SUBMITTED', scope(fam), family=fam, http_status=resp.status, elapsed_s=round(time.time() - t0, 3),
                  headers=hdr, response=data if isinstance(data, dict) else resp.body[:300].decode('utf-8', 'replace'),
                  cost_fields=cost_fields(data))
    if resp.status != 200 or not isinstance(data, dict) or not data.get('request_id'):
        LEDGER.append('GENERATION_FAILED', scope(fam), family=fam, stage='submit', http_status=resp.status, retried=False)
        sys.exit(f'STOP {fam}: submit HTTP {resp.status} (no retry)')
    print(fam, 'submitted', resp.status, data.get('request_id'), data.get('status'))
    return data['request_id']


def request_id(fam):
    rows = [r for r in LEDGER.entries(scope(fam)) if r['event'] == 'GENERATION_SUBMITTED' and r['http_status'] == 200]
    if len(rows) != 1:
        raise FailClosed('REQUEST_ID_UNKNOWN', fam)
    return rows[0]['response']['request_id']


def poll(fam, work):
    rid = request_id(fam)
    t = HiggsfieldApiTransport()
    route = t.status_route(rid)
    last = None
    for i in range(1, POLL_MAX + 1):
        resp, _ = t._api('GET', route)
        data = json.loads(resp.body) if resp.status == 200 else None
        st = data.get('status') if isinstance(data, dict) else None
        if st != last:
            LEDGER.append('POLL', scope(fam), family=fam, request_id=rid, poll=i, http_status=resp.status, provider_status=st)
            last = st
        if st in STATE_MAP and STATE_MAP[st] in ('COMPLETED', 'FAILED'):
            LEDGER.append('TERMINAL', scope(fam), family=fam, request_id=rid, polls=i, provider_status=st,
                          final_status_response=data, cost_fields=cost_fields(data))
            return data
        time.sleep(POLL_INTERVAL_S)
    LEDGER.append('POLL_WINDOW_EXHAUSTED', scope(fam), family=fam, request_id=rid, polls=POLL_MAX, last_status=last,
                  note='not terminal; polling may resume read-only; no resubmit')
    sys.exit(f'PAUSE {fam}: not terminal after {POLL_MAX} polls')


def retrieve(fam, work, data):
    if data.get('status') != 'completed':
        LEDGER.append('GENERATION_FAILED', scope(fam), family=fam, stage='terminal', provider_status=data.get('status'),
                      retried=False)
        print(f'{fam}: terminal {data.get("status")} (recorded; no retry)')
        return None
    imgs = data.get('images') or []
    if len(imgs) != 1 or not isinstance(imgs[0], dict) or not str(imgs[0].get('url', '')).startswith('https://'):
        LEDGER.append('GENERATION_OUTPUT_MALFORMED', scope(fam), family=fam, images=len(imgs))
        sys.exit(f'STOP {fam}: expected exactly 1 image, got {len(imgs)}')
    url = imgs[0]['url']
    raw_dir = Path(work) / fam / 'raw'
    raw_dir.mkdir(parents=True, exist_ok=False)
    r = http.send('GET', url, {}, None, 120.0)
    if r.status != 200 or not r.body:
        LEDGER.append('OUTPUT_DOWNLOAD_FAILED', scope(fam), family=fam, http_status=r.status, output_url=url)
        sys.exit(f'STOP {fam}: output download HTTP {r.status} (the provider copy stays on the CDN)')
    name = Path(urlsplit(url).path).name
    raw = raw_dir / name
    raw.write_bytes(r.body)
    fmt = 'PNG' if r.body[:8] == b'\x89PNG\r\n\x1a\n' else 'JPEG' if r.body[:3] == b'\xff\xd8\xff' else \
        'WEBP' if r.body[:4] == b'RIFF' and r.body[8:12] == b'WEBP' else 'UNKNOWN'
    n, w, h, _ = count_frames(raw)
    raw.chmod(0o444)
    rec = {'FAMILY_ID': fam, 'PROVIDER_REQUEST_ID': data['request_id'], 'RAW_SHA256': sha(r.body),
           'RAW_BYTE_SIZE': len(r.body), 'RAW_DIMENSIONS': f'{w}x{h}', 'RAW_FORMAT': fmt, 'decoded_frames': n,
           'ATTEMPT_NUMBER': 1, 'RETRY_COUNT': 0, 'output_url': url, 'raw_file': name,
           'response_headers': {k: v for k, v in r.headers.items() if k.lower() in (
               'content-type', 'content-length', 'last-modified', 'etag', 'x-amz-expiration')},
           'md5': hashlib.md5(r.body).hexdigest(),
           'local_state': 'LOCKED_ORIGINAL_FOR_NORMALISATION (immutable provider bytes; NOT creative approval; NOT a '
                          'production frame)'}
    LEDGER.append('RAW_OUTPUT_PRESERVED', scope(fam), **rec)
    print(json.dumps(rec, indent=1))
    return rec


def run(fam, work):
    submit(fam, work)
    retrieve(fam, work, poll(fam, work))


def normalise(fam, work):
    pkgs = load_packages()
    raws = [r for r in LEDGER.entries(scope(fam)) if r['event'] == 'RAW_OUTPUT_PRESERVED']
    if len(raws) != 1:
        sys.exit(f'STOP {fam}: no single preserved raw output')
    raw = raws[0]
    path = Path(work) / fam / 'raw' / raw['raw_file']
    if sha256_file(path) != raw['RAW_SHA256']:
        sys.exit(f'STOP {fam}: raw bytes changed')
    w, h = (int(x) for x in raw['RAW_DIMENSIONS'].split('x'))
    try:
        crop = normalisation_crop(w, h)
    except FailClosed as e:
        LEDGER.append('NORMALISATION_STOPPED', scope(fam), family=fam, code=e.code, detail=e.detail)
        sys.exit(f'STOP {fam}: {e.code} {e.detail}')
    crop_arg = None if crop == {'x': 0, 'y': 0, 'w': w, 'h': h} else crop
    scale = None if (w, h) == (1920, 1080) else {'w': 1920, 'h': 1080}
    src = {'asset_id': f'{cand_id(fam)}-RAW', 'registry_id': None, 'classification': 'LOCKED_ORIGINAL_FOR_NORMALISATION',
           'registry_status': 'LOCKED', 'path': str(path), 'expected_sha256': raw['RAW_SHA256'], 'expected_frames': 1,
           'expected_width': w, 'expected_height': h}
    provs = [derive_frame(src, 0, cand_id(fam), Path(work) / fam / f'norm_{x}', crop_arg, scale) for x in ('A', 'B')]
    a, b = provs[0]['output'], provs[1]['output']
    passed = a['sha256'] == b['sha256'] and a['rgb24_sha256'] == b['rgb24_sha256'] and (a['width'], a['height']) == (1920, 1080)
    p = pkgs['packages'][fam]
    cand = {'frame_id': cand_id(fam), 'status': 'REVIEW (local candidate; no registry row; no production storage)',
            'family': p['FRAME_FAMILY_ID'], 'provider_request_id': raw['PROVIDER_REQUEST_ID'],
            'prompt_sha256': p['PROMPT_SHA256'], 'request_body_sha256': p['REQUEST_BODY_SHA256'],
            'reference_sha256s': {r['asset_id']: r['sha256'] for r in pkgs['references_in_order']},
            'raw': {k: raw[k] for k in ('RAW_SHA256', 'RAW_BYTE_SIZE', 'RAW_DIMENSIONS', 'RAW_FORMAT')},
            'normalisation': {'method': 'G04 derive_frame: frame 0, exact centred 16:9 crop, scale 1920x1080 '
                                        f"({provs[0]['recipe']['scale_flags']}), lossless PNG; no other operation",
                              'crop': crop_arg, 'scale': scale, 'source_state': 'LOCKED_ORIGINAL_FOR_NORMALISATION'},
            'NORMALISED_SHA_A': a['sha256'], 'NORMALISED_SHA_B': b['sha256'], 'NORMALISATION_DETERMINISM_PASS': passed,
            'CANONICAL_RGB_PIXEL_SHA': a['rgb24_sha256'], 'normalised_bytes': a['bytes'],
            'normalised_dimensions': f"{a['width']}x{a['height']}", 'raw_unchanged': sha256_file(path) == raw['RAW_SHA256'],
            'g03_applied': False, 'g08_applied': False,
            'human_approval': {'required': True, 'approved': False, 'approve_by': 'exact NORMALISED_SHA'}}
    LEDGER.append('NORMALISED_REVIEW_CANDIDATE' if passed else 'NORMALISATION_DETERMINISM_FAILED', scope(fam), **cand)
    (HERE / f'{cand_id(fam)}_REVIEW_CANDIDATE.json').write_text(json.dumps(cand, indent=1) + '\n')
    print(json.dumps(cand, indent=1))
    if not passed:
        sys.exit(f'STOP {fam}: normalisation A != B')


if __name__ == '__main__':
    cmd, args = sys.argv[1], sys.argv[2:]
    if cmd == 'verify':
        sys.exit(0 if verify(args[0]) else 'STOP: pre-submit verification failed')
    fam, work = args
    if fam not in LOCKED:
        sys.exit(f'unknown family {fam}')
    {'run': run, 'normalise': normalise, 'poll': lambda f, w: retrieve(f, w, poll(f, w))}[cmd](fam, work)
