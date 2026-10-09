"""AGENT-008 v0.2 official Higgsfield transport tests (T-A008-HF01..HF13 + upload security).

Zero spend: every HTTP exchange goes through MockHttp (no sockets). No POST, upload or
generation reaches Higgsfield. Fixtures follow the official contract recorded in
evidence/AGENT008_V02_HIGGSFIELD_TRANSPORT_WIRED_v1.0.md.
"""
import json
import logging
import os
import shutil
import subprocess
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest import mock

from agent008.errors import FailClosed
from agent008.hashing import sha256_bytes, sha256_file
from agent008.inputs import load_hash_pins, load_snapshot, validate_readiness
from agent008.motion import compose as compose_module
from agent008.motion.authorisation import AttemptLedger, SpendAuthorisation
from agent008.motion.compose import compose_motion_shot
from agent008.motion.contracts import MotionRequest
from agent008.motion.higgsfield import HiggsfieldProvider
from agent008.motion.higgsfield_transport import HiggsfieldApiTransport, load_api_models, serialize_request
from agent008.motion.http import EnvironmentProxyAuth, HttpClient, HttpResponse, SuppliedHeaderAuth
from agent008.motion.provider import MotionGenerationProvider
from agent008.motion.runner import run_once
from agent008.motion.source_upload import (SourceFrame, UploadAuthorisation, bind_request_to_upload,
                                           check_source_frame, stage_source_frame)
from agent008.resolve import Resolver
from agent008.spec import build_shot_spec
from agent008.tests.test_motion import JOB, PINS, SMALL, SNAP, FakeMotionProvider, _png, _wav

API = 'https://api.higgsfield.ai'
SEEDANCE = 'bytedance/seedance-2.0/image-to-video'
KLING = 'kling-video/v3.0/std/image-to-video'
RID = 'd7e6c0f3-6699-4f6c-bb45-2ad7fd9158ff'
UPLOAD_URL = 'https://storage.example-cdn.com/uploads/abc?X-Signature=sig'
PUBLIC_URL = 'https://cdn.example-cdn.com/uploads/abc.png'
VIDEO_URL = 'https://cdn.example-cdn.com/results/hf_output_abc.mp4'
SECRET = 'Key fake-key-id:FAKE-SECRET-VALUE-0123456789'


def J(obj, status=200):
    return HttpResponse(status, {'Content-Type': 'application/json'}, json.dumps(obj).encode())


class MockHttp(HttpClient):
    """Records every call; responds from a queue per (method, url). Unknown requests fail the test."""

    def __init__(self):
        self.calls, self.routes = [], {}

    def on(self, method, url, *responses):
        self.routes.setdefault((method, url), []).extend(responses)
        return self

    def send(self, method, url, headers, body=None, timeout=60.0):
        self.calls.append({'method': method, 'url': url, 'headers': dict(headers), 'body': body})
        q = self.routes.get((method, url))
        if not q:
            raise AssertionError(f'unexpected {method} {url}')
        r = q.pop(0) if len(q) > 1 else q[0]
        if isinstance(r, Exception):
            raise r
        return r(method, url, headers, body) if callable(r) else r

    def posts(self):
        return [c for c in self.calls if c['method'] == 'POST']


def submit_ok():
    return J({'status': 'queued', 'request_id': RID, 'status_url': f'{API}/requests/{RID}/status',
              'cancel_url': f'{API}/requests/{RID}/cancel'})


def mp4_bytes(tmp, seconds=5.2):
    p = Path(tmp) / 'served.mp4'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', f'testsrc2=size=640x360:rate=30:duration={seconds}',
                    '-c:v', 'libx264', '-preset', 'ultrafast', '-pix_fmt', 'yuv420p', '-threads', '1', '-fflags',
                    '+bitexact', '-flags:v', '+bitexact', '-map_metadata', '-1', str(p)], check=True)
    return p.read_bytes()


class HFBase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.snap = load_snapshot(SNAP)
        self.frame_path = self.tmp / 'S027_base_TEST_FIXTURE.png'      # synthetic test fixture, not a production frame
        _png(self.frame_path)
        self.sha = sha256_file(self.frame_path)
        self.approval = {'sha256': self.sha, 'status': 'APPROVED_FOR_MOTION_INPUT'}
        self.frame = SourceFrame('FRAME-TEST-FIXTURE', str(self.frame_path), self.sha, 'APPROVED', 'image/png')
        self.http = MockHttp()
        self.auth_boundary = EnvironmentProxyAuth()
        self.transport = HiggsfieldApiTransport(auth=self.auth_boundary, http=self.http)
        self.hp = HiggsfieldProvider(transport=self.transport)
        self.req = MotionRequest('S027', str(self.frame_path), self.sha, JOB['motion_prompt'], JOB['negative_constraints'],
                                 5, '16:9', '1080p', 24, 'higgsfield', SEEDANCE, 'SCOPE-HF-1')
        self.auth = SpendAuthorisation('SCOPE-HF-1', 'test-human', 'HIGGSFIELD', SEEDANCE, 'S027', self.sha,
                                       self.req.prompt_sha256, 1, human_approved=True)
        self.uauth = UploadAuthorisation('UPLOAD-HF-1', 'test-human', 'HIGGSFIELD', 'FRAME-TEST-FIXTURE', self.sha,
                                         'image/png', 1, human_approved=True)
        self.ledger = AttemptLedger(self.tmp / 'ledger.jsonl')

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def mock_upload(self, upload_headers=None, served=None, upload_url=UPLOAD_URL):
        self.http.on('POST', f'{API}/files/generate-upload-url',
                     J({'upload_url': upload_url, 'public_url': PUBLIC_URL,
                        'upload_headers': {'Content-Type': 'image/png'} if upload_headers is None else upload_headers}))
        self.http.on('PUT', upload_url, HttpResponse(200))
        self.http.on('GET', PUBLIC_URL, HttpResponse(200, {}, self.frame_path.read_bytes() if served is None else served))

    def staged(self):
        self.mock_upload()
        rec = stage_source_frame(self.frame, self.hp, self.uauth, self.ledger)
        return rec, bind_request_to_upload(self.req, rec)

    def run_hf(self, req, rec, auth=None, provider=None):
        return run_once(req, provider or self.hp, self.auth if auth is None else auth, self.ledger, self.tmp / 'raw',
                        self.snap, self.approval, poll_interval=0, sleep=lambda s: None, source_upload=rec)


class HF01_AuthConfiguration(HFBase):
    def test_environment_proxy_boundary_configured_without_reading_env(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop('HF_CREDENTIALS', None)
            t = HiggsfieldApiTransport(http=MockHttp())
            self.assertTrue(t.credentials_present())
            self.assertTrue(HiggsfieldProvider(transport=t).credentials_present())
        self.assertEqual(self.auth_boundary.headers_for(f'{API}/requests/x/status'), {})   # proxy injects; app adds none
        self.assertTrue(self.auth_boundary.injects_for(f'{API}/x'))
        self.assertFalse(self.auth_boundary.injects_for(UPLOAD_URL))
        src = (Path(__file__).resolve().parents[1] / 'motion').glob('*.py')
        self.assertFalse(any('HF_CREDENTIALS' in p.read_text() for p in src))

    def test_supplied_header_boundary_only_for_api_host(self):
        a = SuppliedHeaderAuth(lambda: SECRET)
        self.assertEqual(a.headers_for(f'{API}/x'), {'Authorization': SECRET})
        self.assertEqual(a.headers_for(UPLOAD_URL), {})
        self.assertEqual(a.headers_for('https://api.higgsfield.ai.evil.example/x'), {})

    def test_undeclared_boundary_fails_closed(self):
        hp = HiggsfieldProvider(transport=HiggsfieldApiTransport(auth=EnvironmentProxyAuth(declared=False), http=self.http))
        with self.assertRaises(FailClosed) as e:
            hp.poll(RID)
        self.assertEqual(e.exception.code, 'PROVIDER_CREDENTIAL_MISSING')
        self.assertEqual(self.http.calls, [])


class HF02_SecretNeverExposed(HFBase):
    def test_secret_not_in_exception_logs_repr_or_ledger(self):
        http = MockHttp().on('POST', f'{API}/{SEEDANCE}',
                             J({'detail': f'invalid credentials {SECRET}'}, 401))
        t = HiggsfieldApiTransport(auth=SuppliedHeaderAuth(lambda: SECRET), http=http)
        hp = HiggsfieldProvider(transport=t)
        req = replace(self.req, source_frame_url=PUBLIC_URL)
        rec = {'sha256': self.sha, 'public_url': PUBLIC_URL}
        with self.assertLogs('agent008.motion.higgsfield', level='INFO') as logs, self.assertRaises(FailClosed) as e:
            self.run_hf(req, rec, provider=hp)
        text = str(e.exception) + repr(e.exception) + '\n'.join(logs.output) + repr(t) + repr(hp.transport.auth)
        text += (self.tmp / 'ledger.jsonl').read_text()
        self.assertIn('PROVIDER_AUTH_REJECTED', str(e.exception))
        for s in (SECRET, 'FAKE-SECRET-VALUE-0123456789'):
            self.assertNotIn(s, text)
        self.assertEqual(http.calls[0]['headers']['Authorization'], SECRET)   # sent only to the API host


class HF03_Serialization(HFBase):
    def test_seedance_body_matches_official_schema(self):
        rec = load_api_models()['models'][SEEDANCE]
        body = serialize_request(self.req, rec, PUBLIC_URL)
        self.assertEqual(body, {'prompt': JOB['motion_prompt'], 'image_url': PUBLIC_URL, 'duration': 5,
                                'resolution': '1080p', 'generate_audio': False})
        self.assertIsInstance(body['duration'], int)
        self.assertTrue(set(body) <= set(rec['allowed_fields']))
        for bad, code in ((replace(self.req, duration_seconds=5.5), 'DURATION_NOT_SUPPORTED'),
                          (replace(self.req, duration_seconds=16), 'DURATION_NOT_SUPPORTED'),
                          (replace(self.req, resolution='2k'), 'RESOLUTION_NOT_SUPPORTED')):
            with self.assertRaises(FailClosed) as e:
                serialize_request(bad, rec, PUBLIC_URL)
            self.assertEqual(e.exception.code, code)

    def test_post_target_headers_and_body(self):
        rec, req = self.staged()
        self.http.on('POST', f'{API}/{SEEDANCE}', submit_ok())
        self.hp.bind_authorisation(self.auth, {'attempt_number': 1})
        self.assertEqual(self.hp.submit(req), RID)
        call = self.http.posts()[-1]
        self.assertEqual(call['url'], f'{API}/bytedance/seedance-2.0/image-to-video')
        self.assertEqual(call['headers']['Idempotency-Key'], 'SCOPE-HF-1:1')
        self.assertNotIn('Authorization', call['headers'])          # proxy boundary: app never sets it
        self.assertEqual(json.loads(call['body'])['image_url'], PUBLIC_URL)   # public_url propagation
        self.assertEqual(self.transport.requests[RID]['cancel_url'], f'{API}/requests/{RID}/cancel')


class HF04_ModelConfig(HFBase):
    def test_explicit_configurable_models(self):
        cfg = load_api_models()
        self.assertEqual(cfg['default_primary'], SEEDANCE)
        self.assertEqual(cfg['default_fallback'], KLING)
        self.assertEqual(self.hp.official_model('seedance_2_0')[0], SEEDANCE)
        self.assertEqual(self.hp.official_model('kling3_0')[0], KLING)
        self.assertEqual(cfg['models'][SEEDANCE]['fixed_fields'], {'generate_audio': False})
        self.assertEqual(JOB['provider_model'], SEEDANCE)
        self.assertEqual(JOB['provider_params']['duration'], 5)
        self.assertEqual(JOB['provider_params']['resolution'], '1080p')
        self.assertIs(JOB['provider_params']['generate_audio'], False)

    def test_unverified_or_unknown_model_cannot_submit(self):
        for model, code in ((KLING, 'MODEL_CONTRACT_NOT_VERIFIED'), ('made-up/model', 'MODEL_NOT_SUPPORTED')):
            req = replace(self.req, provider_model=model, source_frame_url=PUBLIC_URL)
            with self.assertRaises(FailClosed) as e:
                self.transport.submit(req, PUBLIC_URL, 'k')
            self.assertEqual(e.exception.code, code)
        self.assertEqual(self.http.calls, [])


class HF05_SourceImageRequired(HFBase):
    def test_submit_and_runner_require_hosted_source(self):
        self.hp.bind_authorisation(self.auth, {'attempt_number': 1})
        with self.assertRaises(FailClosed) as e:
            self.hp.submit(self.req)
        self.assertEqual(e.exception.code, 'SOURCE_URL_MISSING')
        with self.assertRaises(FailClosed) as e:
            self.run_hf(self.req, None)
        self.assertEqual(e.exception.code, 'SOURCE_URL_MISSING')
        with self.assertRaises(FailClosed):
            serialize_request(self.req, load_api_models()['models'][SEEDANCE], 'http://insecure.example/a.png')
        self.assertEqual(self.http.calls, [])
        self.assertEqual(self.ledger.attempts('SCOPE-HF-1'), 0)

    def test_missing_frame_rejected_before_upload(self):
        with self.assertRaises(FailClosed) as e:
            stage_source_frame(replace(self.frame, path=str(self.tmp / 'nope.png')), self.hp, self.uauth, self.ledger)
        self.assertEqual(e.exception.code, 'SOURCE_FRAME_MISSING')
        with self.assertRaises(FailClosed) as e:
            stage_source_frame(None, self.hp, self.uauth, self.ledger)
        self.assertEqual(e.exception.code, 'SOURCE_FRAME_MISSING')
        self.assertEqual(self.http.calls, [])


class HF06_SourceSha(HFBase):
    def test_sha_required_and_verified(self):
        cases = ((replace(self.frame, expected_sha256=''), 'SOURCE_SHA_MISSING'),
                 (replace(self.frame, expected_sha256='a' * 64), 'SOURCE_SHA_MISMATCH'),
                 (replace(self.frame, status='REVIEW'), 'SOURCE_FRAME_NOT_APPROVED'),
                 (replace(self.frame, content_type=''), 'SOURCE_CONTENT_TYPE_INVALID'),
                 (replace(self.frame, content_type='image/jpeg'), 'SOURCE_CONTENT_TYPE_MISMATCH'))
        for frame, code in cases:
            with self.assertRaises(FailClosed) as e:
                check_source_frame(frame)
            self.assertEqual(e.exception.code, code)
        with self.assertRaises(FailClosed) as e:
            stage_source_frame(self.frame, self.hp, replace(self.uauth, source_frame_sha256='b' * 64), self.ledger)
        self.assertEqual(e.exception.code, 'UPLOAD_AUTHORISATION_SCOPE_MISMATCH')
        self.assertEqual(self.http.calls, [])

    def test_readback_mismatch_and_request_binding(self):
        self.mock_upload(served=b'\x89PNG\r\n\x1a\n-different-bytes')
        with self.assertRaises(FailClosed) as e:
            stage_source_frame(self.frame, self.hp, self.uauth, self.ledger)
        self.assertEqual(e.exception.code, 'SOURCE_READBACK_SHA_MISMATCH')
        with self.assertRaises(FailClosed) as e:
            bind_request_to_upload(self.req, {'sha256': 'c' * 64, 'public_url': PUBLIC_URL})
        self.assertEqual(e.exception.code, 'SOURCE_UPLOAD_MISMATCH')
        rec = {'sha256': self.sha, 'public_url': PUBLIC_URL}
        with self.assertRaises(FailClosed) as e:     # request points at a different URL than the recorded upload
            self.run_hf(replace(self.req, source_frame_url='https://cdn.example-cdn.com/other.png'), rec)
        self.assertEqual(e.exception.code, 'SOURCE_UPLOAD_MISMATCH')


class HF07_SpendAuthorisation(HFBase):
    def test_missing_or_unapproved_authorisation_fails_closed(self):
        rec = {'sha256': self.sha, 'public_url': PUBLIC_URL}
        req = replace(self.req, source_frame_url=PUBLIC_URL)
        for auth, code in ((None, 'SPEND_AUTHORISATION_MISSING'),
                           (replace(self.auth, human_approved=False), 'AUTHORISATION_NOT_HUMAN_APPROVED'),
                           (replace(self.auth, provider='OTHER'), 'AUTHORISATION_SCOPE_MISMATCH'),
                           (replace(self.auth, prompt_sha256='d' * 64), 'AUTHORISATION_SCOPE_MISMATCH')):
            with self.assertRaises(FailClosed) as e:
                run_once(req, self.hp, auth, self.ledger, self.tmp / 'raw', self.snap, self.approval,
                         poll_interval=0, sleep=lambda s: None, source_upload=rec)
            self.assertEqual(e.exception.code, code)
        with self.assertRaises(FailClosed) as e:      # direct submit without a runner-bound authorisation
            self.hp.submit(req)
        self.assertEqual(e.exception.code, 'SPEND_AUTHORISATION_MISSING')
        with self.assertRaises(FailClosed) as e:
            stage_source_frame(self.frame, self.hp, None, self.ledger)
        self.assertEqual(e.exception.code, 'UPLOAD_AUTHORISATION_MISSING')
        with self.assertRaises(FailClosed) as e:
            stage_source_frame(self.frame, self.hp, replace(self.uauth, human_approved=False), self.ledger)
        self.assertEqual(e.exception.code, 'UPLOAD_AUTHORISATION_NOT_HUMAN_APPROVED')
        self.assertEqual(self.http.calls, [])
        self.assertEqual(self.ledger.entries(), [])

    def test_bound_authorisation_is_single_use(self):
        req = replace(self.req, source_frame_url=PUBLIC_URL)
        self.http.on('POST', f'{API}/{SEEDANCE}', submit_ok())
        self.hp.bind_authorisation(self.auth, {'attempt_number': 1})
        self.hp.submit(req)
        with self.assertRaises(FailClosed) as e:
            self.hp.submit(req)
        self.assertEqual(e.exception.code, 'SPEND_AUTHORISATION_MISSING')
        self.assertEqual(len(self.http.posts()), 1)


class HF08_AttemptLimit(HFBase):
    def test_more_than_one_attempt_fails_closed(self):
        rec = {'sha256': self.sha, 'public_url': PUBLIC_URL}
        with self.assertRaises(FailClosed) as e:
            self.run_hf(replace(self.req, source_frame_url=PUBLIC_URL), rec, auth=replace(self.auth, max_generations=2))
        self.assertEqual(e.exception.code, 'AUTHORISATION_ATTEMPTS_NOT_ONE')
        with self.assertRaises(FailClosed) as e:
            stage_source_frame(self.frame, self.hp, replace(self.uauth, max_uploads=2), self.ledger)
        self.assertEqual(e.exception.code, 'UPLOAD_AUTHORISATION_ATTEMPTS_NOT_ONE')
        self.assertEqual(self.http.calls, [])

    def test_second_upload_refused(self):
        self.staged()
        with self.assertRaises(FailClosed) as e:
            stage_source_frame(self.frame, self.hp, self.uauth, self.ledger)
        self.assertEqual(e.exception.code, 'UPLOAD_COUNT_EXCEEDED')
        self.assertEqual(sum(1 for c in self.http.calls if c['method'] == 'PUT'), 1)


class HF09_NoAutoRetry(HFBase):
    def _attempt(self, *responses):
        rec, req = self.staged()
        self.http.on('POST', f'{API}/{SEEDANCE}', submit_ok())
        self.http.on('GET', f'{API}/requests/{RID}/status', *responses)
        return rec, req

    def test_failed_nsfw_canceled_counted_once_no_retry(self):
        for state in ('failed', 'nsfw', 'canceled'):
            with self.subTest(state=state):
                self.tearDown()
                self.setUp()
                rec, req = self._attempt(J({'status': 'in_progress', 'request_id': RID}),
                                         J({'status': state, 'request_id': RID}))
                with self.assertRaises(FailClosed) as e:
                    self.run_hf(req, rec)
                self.assertEqual(e.exception.code, 'PROVIDER_FAILED_NO_RETRY')
                self.assertIn(state, e.exception.detail)
                self.assertEqual(len([c for c in self.http.posts() if SEEDANCE in c['url']]), 1)
                self.assertEqual(self.ledger.attempts('SCOPE-HF-1'), 1)
                with self.assertRaises(FailClosed) as e2:
                    self.run_hf(req, rec)
                self.assertEqual(e2.exception.code, 'GENERATION_COUNT_EXCEEDED')

    def test_submit_http_error_and_network_error_not_retried(self):
        for resp, inner in ((J({'detail': 'boom'}, 500), 'PROVIDER_SERVER_ERROR'),
                            (J({'detail': 'Not enough credits'}, 403), 'PROVIDER_INSUFFICIENT_CREDITS_OR_FORBIDDEN'),
                            (FailClosed('HTTP_TRANSPORT_ERROR', 'POST api.higgsfield.ai: TimeoutError'),
                             'HTTP_TRANSPORT_ERROR')):
            with self.subTest(inner=inner):
                self.tearDown()
                self.setUp()
                rec, req = self.staged()
                self.http.on('POST', f'{API}/{SEEDANCE}', resp)
                with self.assertRaises(FailClosed) as e:
                    self.run_hf(req, rec)
                self.assertEqual(e.exception.code, 'PROVIDER_SUBMIT_FAILED_NO_RETRY')
                self.assertIn(inner, e.exception.detail)
                self.assertEqual(len([c for c in self.http.posts() if SEEDANCE in c['url']]), 1)
                self.assertEqual(self.ledger.attempts('SCOPE-HF-1'), 1)

    def test_upload_failure_not_retried(self):
        self.http.on('POST', f'{API}/files/generate-upload-url',
                     J({'upload_url': UPLOAD_URL, 'public_url': PUBLIC_URL, 'upload_headers': {}}))
        self.http.on('PUT', UPLOAD_URL, HttpResponse(500))
        with self.assertRaises(FailClosed) as e:
            stage_source_frame(self.frame, self.hp, self.uauth, self.ledger)
        self.assertEqual(e.exception.code, 'SOURCE_UPLOAD_FAILED_NO_RETRY')
        self.assertEqual(len(self.http.calls), 2)
        self.assertEqual([r['event'] for r in self.ledger.entries()], ['UPLOAD_RESERVED', 'UPLOAD_FAILED'])


class HF10_PollingRoute(HFBase):
    def test_documented_status_route_and_states(self):
        url = f'{API}/requests/{RID}/status'
        self.assertEqual(url, 'https://api.higgsfield.ai/requests/d7e6c0f3-6699-4f6c-bb45-2ad7fd9158ff/status')
        self.http.on('GET', url, J({'status': 'queued'}), J({'status': 'in_progress'}), HttpResponse(502, {}, b''),
                     J({'status': 'completed', 'video': {'url': VIDEO_URL}}))
        states = [self.hp.poll(RID)['status'] for _ in range(4)]
        self.assertEqual(states, ['QUEUED', 'RUNNING', 'RUNNING', 'COMPLETED'])
        self.assertTrue(all(c['method'] == 'GET' and c['url'] == url and c['body'] is None for c in self.http.calls))

    def test_unexpected_status_url_or_bad_request_id_fails_closed(self):
        req = replace(self.req, source_frame_url=PUBLIC_URL)
        for resp in (J({'request_id': RID, 'status_url': f'{API}/v1/other/{RID}'}),
                     J({'request_id': '../../files', 'status_url': None}),
                     J({'status': 'queued'})):
            self.http.routes.clear()
            self.http.on('POST', f'{API}/{SEEDANCE}', resp)
            self.hp.bind_authorisation(self.auth, {'attempt_number': 1})
            with self.assertRaises(FailClosed) as e:
                self.hp.submit(req)
            self.assertIn(e.exception.code, ('PROVIDER_STATUS_URL_UNEXPECTED', 'PROVIDER_RESPONSE_MALFORMED'))


class HF11_CompletedParsing(HFBase):
    def test_video_url_extracted(self):
        self.http.on('GET', f'{API}/requests/{RID}/status',
                     J({'status': 'completed', 'request_id': RID, 'video': {'url': VIDEO_URL}}))
        st = self.hp.poll(RID)
        self.assertEqual((st['status'], st['provider_status'], st['output_url']), ('COMPLETED', 'completed', VIDEO_URL))

    def test_malformed_responses_fail_closed(self):
        bad = (J({'status': 'completed'}), J({'status': 'completed', 'video': {'url': 'http://x/y.mp4'}}),
               J({'status': 'teleported'}), J({}), HttpResponse(200, {}, b'<html>'), J(['completed']),
               J({'detail': 'Not Found'}, 404))
        for r in bad:
            self.http.routes.clear()
            self.http.on('GET', f'{API}/requests/{RID}/status', r)
            with self.assertRaises(FailClosed) as e:
                self.hp.poll(RID)
            self.assertIn(e.exception.code, ('PROVIDER_RESPONSE_MALFORMED', 'PROVIDER_NOT_FOUND'))
        with self.assertRaises(FailClosed) as e:
            self.hp.fetch(RID, self.tmp)
        self.assertEqual(e.exception.code, 'OUTPUT_NOT_COMPLETED')

    def test_signed_upload_response_parsing(self):
        for info, code in (({'public_url': PUBLIC_URL}, 'PROVIDER_RESPONSE_MALFORMED'),
                           ({'upload_url': UPLOAD_URL, 'public_url': 'ftp://x'}, 'PROVIDER_RESPONSE_MALFORMED'),
                           ({'upload_url': UPLOAD_URL, 'public_url': PUBLIC_URL, 'upload_headers': ['x']},
                            'PROVIDER_RESPONSE_MALFORMED'),
                           ({'upload_url': UPLOAD_URL, 'public_url': PUBLIC_URL,
                             'upload_headers': {'Content-Type': 'image/jpeg'}}, 'UPLOAD_CONTENT_TYPE_MISMATCH')):
            self.http.routes.clear()
            self.http.on('POST', f'{API}/files/generate-upload-url', J(info))
            with self.assertRaises(FailClosed) as e:
                self.transport.prepare_source_upload(self.frame_path.read_bytes(), 'image/png', self.sha)
            self.assertEqual(e.exception.code, code)
        self.assertFalse(any(c['method'] == 'PUT' for c in self.http.calls))


class HF_Security_NoAuthLeakToStorage(HFBase):
    """Regression: the credential for api.higgsfield.ai is NEVER forwarded to the signed storage upload_url."""

    def test_put_uses_only_returned_upload_headers(self):
        http = MockHttp()
        t = HiggsfieldApiTransport(auth=SuppliedHeaderAuth(lambda: SECRET), http=http)
        returned = {'Content-Type': 'image/png', 'x-amz-acl': 'public-read'}
        http.on('POST', f'{API}/files/generate-upload-url',
                J({'upload_url': UPLOAD_URL, 'public_url': PUBLIC_URL, 'upload_headers': returned}))
        http.on('PUT', UPLOAD_URL, HttpResponse(200))
        http.on('GET', PUBLIC_URL, HttpResponse(200, {}, self.frame_path.read_bytes()))
        rec = t.prepare_source_upload(self.frame_path.read_bytes(), 'image/png', self.sha)
        post, put, get = http.calls
        self.assertEqual(post['headers']['Authorization'], SECRET)        # API host only
        self.assertEqual(put['headers'], returned)                        # exactly the returned headers
        self.assertEqual(put['body'], self.frame_path.read_bytes())       # exact approved bytes
        self.assertEqual(get['headers'], {})
        for c in (put, get):
            self.assertNotIn('authorization', {k.lower() for k in c['headers']})
            self.assertFalse(any(SECRET in v or 'FAKE-SECRET' in v for v in c['headers'].values()))
        self.assertEqual((rec['public_url'], rec['readback']), (PUBLIC_URL, 'SHA256_MATCH'))

    def test_upload_url_on_api_host_refused(self):
        for auth in (EnvironmentProxyAuth(), SuppliedHeaderAuth(lambda: SECRET)):
            http = MockHttp().on('POST', f'{API}/files/generate-upload-url',
                                 J({'upload_url': f'{API}/storage/put?sig=1', 'public_url': PUBLIC_URL}))
            t = HiggsfieldApiTransport(auth=auth, http=http)
            with self.assertRaises(FailClosed) as e:
                t.prepare_source_upload(self.frame_path.read_bytes(), 'image/png', self.sha)
            self.assertEqual(e.exception.code, 'UPLOAD_URL_WOULD_RECEIVE_PROVIDER_AUTH')
            self.assertFalse(any(c['method'] == 'PUT' for c in http.calls))

    def test_output_download_sends_no_auth(self):
        http = MockHttp().on('GET', f'{API}/requests/{RID}/status',
                             J({'status': 'completed', 'video': {'url': VIDEO_URL}}))
        http.on('GET', VIDEO_URL, HttpResponse(200, {}, b'video-bytes'))
        t = HiggsfieldApiTransport(auth=SuppliedHeaderAuth(lambda: SECRET), http=http)
        t.poll(RID)
        t.retrieve(RID, self.tmp)
        self.assertEqual(http.calls[-1]['headers'], {})


class HF12_HF13_EndToEndMocked(HFBase):
    """Full staged -> submit -> poll -> retrieve -> freeze -> compose path on mocks (no network, no spend)."""

    def setUp(self):
        super().setUp()
        self.video = mp4_bytes(self.tmp)
        self.rec, self.sreq = self.staged()
        self.http.on('POST', f'{API}/{SEEDANCE}', submit_ok())
        self.http.on('GET', f'{API}/requests/{RID}/status', J({'status': 'queued'}),
                     J({'status': 'completed', 'video': {'url': VIDEO_URL}}))
        self.http.on('GET', VIDEO_URL, HttpResponse(200, {}, self.video))
        self.result = self.run_hf(self.sreq, self.rec)

    def test_HF12_raw_output_preserved(self):
        p = Path(self.result.raw_output_path)
        self.assertEqual(self.result.raw_output_sha256, sha256_bytes(self.video))
        self.assertEqual(sha256_file(p), sha256_bytes(self.video))
        self.assertFalse(os.stat(p).st_mode & 0o222)
        self.assertEqual(self.result.raw_original_filename, 'hf_output_abc.mp4')
        self.assertEqual((self.result.provider_job_id, self.result.source_frame_url), (RID, PUBLIC_URL))
        mr = json.loads((p.parent / 'MOTION_RESULT.json').read_text())
        self.assertEqual(mr['source_upload']['public_url'], PUBLIC_URL)
        self.assertEqual(mr['source_upload']['sha256'], self.sha)
        events = [e['event'] for e in self.ledger.entries()]
        self.assertEqual(events, ['UPLOAD_RESERVED', 'UPLOADED', 'RESERVED', 'SUBMITTED', 'COMPLETED'])
        self.assertEqual(len([c for c in self.http.posts() if SEEDANCE in c['url']]), 1)

    def test_HF13_compositor_unchanged_across_providers(self):
        self.assertFalse(any(m in compose_module.__dict__ for m in ('HiggsfieldProvider', 'HiggsfieldApiTransport')))
        self.assertNotIn('higgsfield', Path(compose_module.__file__).read_text().lower())
        r = validate_readiness(self.snap, JOB['readiness_manifest_id'])
        spec_shot = build_shot_spec(self.snap, Resolver(r, self.snap['asset_registry'], load_hash_pins(PINS)), 'S027',
                                    SMALL, motion_phase=True)
        _wav(self.tmp / 'amb.wav', 2.0, 0, 0.003)
        _wav(self.tmp / 'chord.wav', 3.0, 660, 0.2)
        _wav(self.tmp / 'dlg.wav', 1.2, 330, 0.25)
        assets = {'AMB-BATHROOM-QUIET-v01': self.tmp / 'amb.wav', 'SFX-WIN-SPARKLE-CHORD': self.tmp / 'chord.wav',
                  'DLG-TEST-S027-L1': self.tmp / 'dlg.wav'}
        dialogue = {'shot_id': 'S027', 'speaker': 'Mikko', 'text': 'We did it! I feel fresh.',
                    'audio_asset_id': 'DLG-TEST-S027-L1', 'expected_sha256': sha256_file(self.tmp / 'dlg.wav'),
                    'registry_status': 'APPROVED', 'start_seconds': 0.5, 'gain_db': 0.0}
        timing = {'beds': {}, 'named': {'SFX-WIN-SPARKLE-CHORD': {'start_seconds': 1.0, 'gain_db': -10.0,
                                                                  'fade_out_seconds': 1.0, 'fade_complete_by_seconds': 5.0}},
                  'dialogue': [dialogue]}
        prov = compose_motion_shot(self.result, self.sreq, spec_shot, SMALL, assets, timing, self.tmp / 'out_hf')
        self.assertEqual(prov['raw_output_verified_sha256'], self.result.raw_output_sha256)
        self.assertEqual(prov['qc']['automatic_result'], 'PASS')
        # the same compositor call accepts the fake provider's result unchanged
        fake = FakeMotionProvider()
        freq = replace(self.req, provider='fake-motion', provider_model='fake-i2v', approval_scope_id='SCOPE-F')
        fauth = SpendAuthorisation('SCOPE-F', 't', 'fake-motion', 'fake-i2v', 'S027', self.sha, freq.prompt_sha256, 1)
        fres = run_once(freq, fake, fauth, self.ledger, self.tmp / 'raw_f', self.snap, self.approval,
                        poll_interval=0, sleep=lambda s: None)
        fprov = compose_motion_shot(fres, freq, spec_shot, SMALL, assets, timing, self.tmp / 'out_fake')
        self.assertEqual(fprov['qc']['automatic_result'], 'PASS')
        self.assertTrue(issubclass(HiggsfieldProvider, MotionGenerationProvider))


class HF_NoLiveNetwork(unittest.TestCase):
    def test_suite_never_opens_sockets(self):
        import socket
        with mock.patch.object(socket.socket, 'connect', side_effect=AssertionError('network used')):
            t = HiggsfieldApiTransport(http=MockHttp().on('GET', f'{API}/requests/{RID}/status', J({'status': 'queued'})))
            self.assertEqual(t.poll(RID)['status'], 'QUEUED')


if __name__ == '__main__':
    unittest.main()
