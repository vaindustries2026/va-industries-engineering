"""AGENT-008 v0.2 motion layer tests (T-A008-M01..M12). No network, no paid calls.

A deterministic in-process FakeMotionProvider stands in for a real provider; it renders
a synthetic clip with ffmpeg so stages 8C -> 8D -> 8F run end to end offline.
"""
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

import numpy as np

from agent008.config import load_output_spec
from agent008.errors import FailClosed
from agent008.hashing import sha256_file
from agent008.inputs import load_hash_pins, load_snapshot, validate_readiness
from agent008.motion.authorisation import AttemptLedger, SpendAuthorisation
from agent008.motion.compose import compose_motion_shot
from agent008.motion.contracts import MotionRequest
from agent008.motion.higgsfield import HiggsfieldProvider
from agent008.motion.provider import MotionGenerationProvider
from agent008.motion.qc import QCDecisionLog
from agent008.motion.runner import run_once, validate_pre_generation
from agent008.resolve import Resolver
from agent008.spec import build_shot_spec

PKG = Path(__file__).resolve().parents[1]
SNAP = PKG / 'inputs' / 'ep005_motion_s027_input_snapshot.json'
PINS = PKG / 'inputs' / 'hash_pins.json'
JOB = json.loads((PKG / 'motion' / 'jobs' / 'ep005_s027_motion_smoke_v1.json').read_text())
SMALL = replace(load_output_spec(), width=480, height=270, x264_preset='ultrafast')


def _png(path, color=(200, 160, 120)):
    a = np.zeros((270, 480, 4), np.uint8)
    a[...] = (*color, 255)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', '480x270', '-i', '-',
                    '-frames:v', '1', str(path)], input=a.tobytes(), check=True)


def _wav(path, seconds, freq, level):
    t = np.arange(int(seconds * 48000)) / 48000
    x = level * (np.random.default_rng(3).standard_normal(len(t)) if freq == 0 else np.sin(2 * np.pi * freq * t))
    a = np.stack([x, x], 1)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'f64le', '-ar', '48000', '-ac', '2', '-i', '-', '-c:a', 'pcm_s24le',
                    str(path)], input=a.astype('<f8').tobytes(), check=True)


class FakeTransport:
    sanctioned = True

    def credentials_present(self):
        return True


class FakeMotionProvider(MotionGenerationProvider):
    """Second implementation of the abstraction (M12). Deterministic synthetic output."""
    name = 'fake-motion'

    def __init__(self, fail=False, seconds=5.2, fps=30):
        self.fail, self.seconds, self.fps = fail, seconds, fps
        self.submits = 0

    def credentials_present(self):
        return True

    def capabilities(self, model):
        return {'duration_range': [3, 15], 'aspect_ratios': ['16:9'], 'resolutions': ['1080p'],
                'media_roles': ['start_image']} if model == 'fake-i2v' else None

    def submit(self, request):
        self.validate_request(request)
        self.submits += 1
        return f'job-{self.submits}'

    def poll(self, job_id):
        return {'status': 'FAILED', 'detail': 'synthetic failure'} if self.fail else \
            {'status': 'COMPLETED', 'usage': {'credits': 0, 'note': 'fake'}}

    def fetch(self, job_id, dest_dir):
        p = Path(dest_dir) / 'provider_original.mp4'
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i',
                        f'testsrc2=size=640x360:rate={self.fps}:duration={self.seconds}', '-c:v', 'libx264', '-preset',
                        'ultrafast', '-pix_fmt', 'yuv420p', '-threads', '1', '-fflags', '+bitexact', '-flags:v', '+bitexact',
                        '-map_metadata', '-1', str(p)], check=True)
        return p, p.name


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.snap = load_snapshot(SNAP)
        self.frame = self.tmp / 'S027_base.png'
        _png(self.frame)
        self.sha = sha256_file(self.frame)
        self.approval = {'sha256': self.sha, 'status': 'APPROVED_FOR_MOTION_INPUT'}
        self.req = MotionRequest('S027', str(self.frame), self.sha, JOB['motion_prompt'], JOB['negative_constraints'], 5,
                                 '16:9', '1080p', 24, 'fake-motion', 'fake-i2v', 'SCOPE-TEST-1')
        self.auth = SpendAuthorisation('SCOPE-TEST-1', 'test-human', 'fake-motion', 'fake-i2v', 'S027', self.sha,
                                       self.req.prompt_sha256, 1)
        self.ledger = AttemptLedger(self.tmp / 'ledger.jsonl')

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_fake(self, provider):
        return run_once(self.req, provider, self.auth, self.ledger, self.tmp / 'raw', self.snap, self.approval,
                        poll_interval=0, sleep=lambda s: None)


class M01_Credentials(Base):
    def test_higgsfield_without_transport_fails_closed(self):
        hp = HiggsfieldProvider()
        self.assertFalse(hp.credentials_present())
        req = replace(self.req, provider='higgsfield', provider_model='seedance_2_0')
        with self.assertRaises(FailClosed) as e:
            hp.submit(req)
        self.assertEqual(e.exception.code, 'PROVIDER_CREDENTIAL_MISSING')

    def test_unsanctioned_transport_rejected(self):
        class T(FakeTransport):
            sanctioned = False
        self.assertFalse(HiggsfieldProvider(transport=T()).credentials_present())


class M02_M03_SourceFrame(Base):
    def test_missing_frame(self):
        req = replace(self.req, source_frame_path=str(self.tmp / 'nope.png'))
        with self.assertRaises(FailClosed) as e:
            validate_pre_generation(req, FakeMotionProvider(), self.auth, self.ledger, self.snap, self.approval)
        self.assertEqual(e.exception.code, 'ASSET_FILE_MISSING')

    def test_sha_mismatch(self):
        req = replace(self.req, source_frame_sha256='a' * 64)
        with self.assertRaises(FailClosed) as e:
            validate_pre_generation(req, FakeMotionProvider(), self.auth, self.ledger, self.snap, self.approval)
        self.assertEqual(e.exception.code, 'HASH_MISMATCH')

    def test_unapproved_frame(self):
        with self.assertRaises(FailClosed) as e:
            validate_pre_generation(self.req, FakeMotionProvider(), self.auth, self.ledger, self.snap,
                                    {'sha256': self.sha, 'status': 'NON_CANON_TECHNICAL_STANDIN'})
        self.assertEqual(e.exception.code, 'SOURCE_FRAME_NOT_APPROVED')


class M04_ShotApproval(Base):
    def test_unapproved_shot(self):
        req = replace(self.req, shot_id='S005')   # not a video-generation shot
        auth = replace(self.auth, shot_id='S005')
        with self.assertRaises(FailClosed) as e:
            validate_pre_generation(req, FakeMotionProvider(), auth, self.ledger, self.snap, self.approval)
        self.assertEqual(e.exception.code, 'SHOT_NOT_APPROVED_FOR_MOTION')

    def test_phase0_still_rejects_video_shots(self):
        r = validate_readiness(self.snap, JOB['readiness_manifest_id'])
        res = Resolver(r, self.snap['asset_registry'], load_hash_pins(PINS))
        with self.assertRaises(FailClosed):
            build_shot_spec(self.snap, res, 'S027', load_output_spec())
        self.assertEqual(build_shot_spec(self.snap, res, 'S027', load_output_spec(), motion_phase=True)['frames'], 120)


class M05_M06_SpendGate(Base):
    def test_count_exceeded(self):
        self.run_fake(FakeMotionProvider())
        with self.assertRaises(FailClosed) as e:
            self.run_fake(FakeMotionProvider())
        self.assertEqual(e.exception.code, 'GENERATION_COUNT_EXCEEDED')
        self.assertEqual(self.ledger.attempts('SCOPE-TEST-1'), 1)

    def test_scope_mismatch(self):
        with self.assertRaises(FailClosed) as e:
            run_once(replace(self.req, motion_prompt=self.req.motion_prompt + ' extra'), FakeMotionProvider(), self.auth,
                     self.ledger, self.tmp / 'raw', self.snap, self.approval, poll_interval=0, sleep=lambda s: None)
        self.assertEqual(e.exception.code, 'AUTHORISATION_SCOPE_MISMATCH')
        self.assertEqual(self.ledger.attempts('SCOPE-TEST-1'), 0)

    def test_failure_no_retry_and_counted(self):
        p = FakeMotionProvider(fail=True)
        with self.assertRaises(FailClosed) as e:
            self.run_fake(p)
        self.assertEqual(e.exception.code, 'PROVIDER_FAILED_NO_RETRY')
        self.assertEqual(p.submits, 1)
        self.assertEqual(self.ledger.attempts('SCOPE-TEST-1'), 1)
        with self.assertRaises(FailClosed) as e2:
            self.run_fake(FakeMotionProvider())
        self.assertEqual(e2.exception.code, 'GENERATION_COUNT_EXCEEDED')


class ComposeFixture(Base):
    def setUp(self):
        super().setUp()
        self.result = self.run_fake(FakeMotionProvider())
        r = validate_readiness(self.snap, JOB['readiness_manifest_id'])
        res = Resolver(r, self.snap['asset_registry'], load_hash_pins(PINS))
        self.spec_shot = build_shot_spec(self.snap, res, 'S027', SMALL, motion_phase=True)
        _wav(self.tmp / 'amb.wav', 2.0, 0, 0.003)
        _wav(self.tmp / 'chord.wav', 3.0, 660, 0.2)
        _wav(self.tmp / 'dlg.wav', 1.2, 330, 0.25)
        self.assets = {'AMB-BATHROOM-QUIET-v01': self.tmp / 'amb.wav', 'SFX-WIN-SPARKLE-CHORD': self.tmp / 'chord.wav',
                       'DLG-TEST-S027-L1': self.tmp / 'dlg.wav'}
        # S027 carries a required Mikko line, so every S027 compose now needs an approved, hash-bound clip.
        self.dialogue = {'shot_id': 'S027', 'speaker': 'Mikko', 'text': 'We did it! I feel fresh.',
                         'audio_asset_id': 'DLG-TEST-S027-L1', 'expected_sha256': sha256_file(self.tmp / 'dlg.wav'),
                         'registry_status': 'APPROVED', 'start_seconds': 0.5, 'gain_db': 0.0}
        self.timing = {'beds': {}, 'named': {'SFX-WIN-SPARKLE-CHORD': {'start_seconds': 1.0, 'gain_db': -10.0,
                                                                       'fade_out_seconds': 1.0,
                                                                       'fade_complete_by_seconds': 5.0}},
                       'dialogue': [self.dialogue]}


class M07_to_M11_Pipeline(ComposeFixture):
    def test_M07_raw_preserved_unchanged(self):
        p = Path(self.result.raw_output_path)
        self.assertFalse(os.access(p, os.W_OK) and os.stat(p).st_mode & 0o222)
        self.assertEqual(sha256_file(p), self.result.raw_output_sha256)
        self.assertEqual(self.result.raw_original_filename, 'provider_original.mp4')
        compose_motion_shot(self.result, self.req, self.spec_shot, SMALL, self.assets, self.timing, self.tmp / 'out')
        self.assertEqual(sha256_file(p), self.result.raw_output_sha256)   # untouched by the compositor

    def test_M08_sha_recorded(self):
        rec = json.loads((Path(self.result.raw_output_path).parent / 'MOTION_RESULT.json').read_text())
        self.assertEqual(rec['result']['raw_output_sha256'], self.result.raw_output_sha256)
        self.assertEqual([e['event'] for e in self.ledger.entries()], ['RESERVED', 'SUBMITTED', 'COMPLETED'])

    def test_M09_compositor_consumes_exact_output(self):
        prov = compose_motion_shot(self.result, self.req, self.spec_shot, SMALL, self.assets, self.timing, self.tmp / 'o1')
        self.assertEqual(prov['raw_output_verified_sha256'], self.result.raw_output_sha256)
        self.assertEqual(prov['qc']['output_frames'], 120)
        self.assertEqual(prov['qc']['automatic_result'], 'PASS')
        self.assertEqual(prov['qc']['black_frames'], [])
        tampered = replace(self.result, raw_output_sha256='b' * 64)
        with self.assertRaises(FailClosed) as e:
            compose_motion_shot(tampered, self.req, self.spec_shot, SMALL, self.assets, self.timing, self.tmp / 'o2')
        self.assertEqual(e.exception.code, 'HASH_MISMATCH')

    def test_M10_review_required(self):
        prov = compose_motion_shot(self.result, self.req, self.spec_shot, SMALL, self.assets, self.timing, self.tmp / 'o3')
        self.assertEqual(prov['status'], 'REVIEW')
        self.assertFalse(prov['human_approval']['approved'])
        log = QCDecisionLog(self.tmp / 'qc.jsonl')
        sha = prov['outputs']['review_mp4']['sha256']
        self.assertEqual(log.status(sha), 'REVIEW')
        self.assertFalse(log.production_approved(sha))
        with self.assertRaises(FailClosed):
            log.record(sha, 'APPROVE', 'agent008')

    def test_M11_rejected_cannot_become_approved(self):
        log = QCDecisionLog(self.tmp / 'qc.jsonl')
        log.record('c' * 64, 'REJECT', 'Gilang', 'drift')
        with self.assertRaises(FailClosed) as e:
            log.record('c' * 64, 'APPROVE', 'Gilang')
        self.assertEqual(e.exception.code, 'QC_REJECTED_IS_TERMINAL')
        self.assertFalse(log.production_approved('c' * 64))
        r = log.record('d' * 64, 'REGENERATE', 'Gilang')
        self.assertEqual(r['follow_up'], 'NEW_SPEND_AUTHORISATION_REQUIRED')

    def test_short_raw_fails_closed(self):
        ledger = AttemptLedger(self.tmp / 'l2.jsonl')
        auth = replace(self.auth, approval_scope_id='SCOPE-2')
        req = replace(self.req, approval_scope_id='SCOPE-2')
        short = run_once(req, FakeMotionProvider(seconds=3.0), auth, ledger, self.tmp / 'raw2', self.snap, self.approval,
                         poll_interval=0, sleep=lambda s: None)
        with self.assertRaises(FailClosed) as e:
            compose_motion_shot(short, req, self.spec_shot, SMALL, self.assets, self.timing, self.tmp / 'o4')
        self.assertEqual(e.exception.code, 'RAW_TOO_SHORT')


class D01_Dialogue(ComposeFixture):
    """Dialogue support in the motion compositor (T-A008-D01..D11). No network, no paid calls."""

    def compose(self, out, timing=None, spec_shot=None, assets=None):
        return compose_motion_shot(self.result, self.req, spec_shot or self.spec_shot, SMALL, assets or self.assets,
                                   timing or self.timing, self.tmp / out)

    def with_dialogue(self, **kw):
        return {**self.timing, 'dialogue': [{**self.dialogue, **kw}]}

    def mix(self, timing):
        from agent008.motion.compose import mix_motion_audio, resolve_dialogue
        dlg = resolve_dialogue(self.spec_shot, self.assets, timing)
        return mix_motion_audio(self.spec_shot, self.assets, timing, SMALL, dlg)

    def assert_code(self, code, **kw):
        with self.assertRaises(FailClosed) as e:
            self.compose('bad', timing=self.with_dialogue(**kw))
        self.assertEqual(e.exception.code, code)

    def test_D01_dialogue_mixed_at_exact_start(self):
        from agent008 import media
        sr = SMALL.audio_sample_rate
        clip = media.load_audio(self.assets['DLG-TEST-S027-L1'], sr, SMALL.audio_channels)
        no_dlg = {**self.timing, 'dialogue': []}
        with_dlg, cues, _ = self.mix(self.timing)
        spec_wo = {**self.spec_shot, 'dialogue_slots': []}
        from agent008.motion.compose import mix_motion_audio
        without, _, _ = mix_motion_audio(spec_wo, self.assets, no_dlg, SMALL, ())
        diff = with_dlg - without
        start = int(round(0.5 * sr))
        np.testing.assert_allclose(diff[start:start + len(clip)], clip, atol=1e-9)
        self.assertEqual(float(np.abs(diff[:start]).max()), 0.0)
        self.assertEqual(float(np.abs(diff[start + len(clip):]).max()), 0.0)
        d = [c for c in cues if c['kind'] == 'DIALOGUE']
        self.assertEqual(len(d), 1)                                   # D06: once only
        self.assertAlmostEqual(d[0]['end_s'] - d[0]['start_s'], len(clip) / sr)   # D07: no stretching

    def test_D02_required_dialogue_missing_fails_closed(self):
        with self.assertRaises(FailClosed) as e:
            self.compose('missing', timing={**self.timing, 'dialogue': []})
        self.assertEqual(e.exception.code, 'DIALOGUE_SLOT_UNFILLED')

    def test_D03_sha_mismatch_fails_closed(self):
        self.assert_code('HASH_MISMATCH', expected_sha256='e' * 64)

    def test_D04_unapproved_fails_closed(self):
        self.assert_code('DIALOGUE_NOT_APPROVED', registry_status='REVIEW')

    def test_D05_wrong_shot_text_speaker_or_asset_fails_closed(self):
        self.assert_code('DIALOGUE_SHOT_MISMATCH', shot_id='S026')
        self.assert_code('DIALOGUE_TEXT_MISMATCH', text='We did it!')
        self.assert_code('DIALOGUE_SPEAKER_MISMATCH', speaker='Lumi')
        self.assert_code('DIALOGUE_REQUIRES_APPROVED_AUDIO', audio_asset_id='DLG-UNKNOWN')

    def test_D06_extra_dialogue_fails_closed(self):
        with self.assertRaises(FailClosed) as e:
            self.compose('extra', timing={**self.timing, 'dialogue': [self.dialogue, self.dialogue]})
        self.assertEqual(e.exception.code, 'DIALOGUE_UNEXPECTED')

    def test_D07_overrun_fails_closed_never_trimmed(self):
        self.assert_code('DIALOGUE_OVERRUNS_SHOT', start_seconds=4.5)

    def test_D08_full_mix_and_output_spec(self):
        prov = self.compose('full')
        kinds = sorted(c['kind'] for c in prov['audio_cues'])
        self.assertEqual(kinds, ['BED', 'DIALOGUE', 'NAMED'])
        self.assertEqual(prov['qc']['output_frames'], 120)
        self.assertEqual(prov['qc']['automatic_result'], 'PASS')
        self.assertEqual(prov['dialogue_tracks'][0]['sha256'], self.dialogue['expected_sha256'])
        mp4 = self.tmp / 'full' / 'MOTION_SMOKE_REVIEW.mp4'
        from agent008 import media
        pr = media.probe(mp4)
        v = [s for s in pr['streams'] if s['codec_type'] == 'video'][0]
        self.assertEqual(v['r_frame_rate'], '24/1')
        self.assertEqual(int(v['nb_frames']), 120)
        wav = self.tmp / 'full' / 'S027_MOTION_MIX.wav'
        a = [s for s in media.probe(wav)['streams'] if s['codec_type'] == 'audio'][0]
        self.assertEqual(int(a['duration_ts']), 5 * SMALL.audio_sample_rate)     # exactly 5.000 s

    def test_D09_no_dialogue_shot_unchanged(self):
        spec_wo = {**self.spec_shot, 'dialogue_slots': []}
        legacy = {k: v for k, v in self.timing.items() if k != 'dialogue'}
        a = self.compose('l1', timing=legacy, spec_shot=spec_wo)
        b = self.compose('l2', timing=legacy, spec_shot=spec_wo)
        self.assertEqual(a['dialogue_tracks'], [])
        self.assertEqual(a['outputs']['mix_wav']['sha256'], b['outputs']['mix_wav']['sha256'])
        with self.assertRaises(FailClosed) as e:      # a dialogue clip on a shot with no slot is refused
            self.compose('l3', timing=self.timing, spec_shot=spec_wo)
        self.assertEqual(e.exception.code, 'DIALOGUE_UNEXPECTED')


class M12_Abstraction(unittest.TestCase):
    def test_two_implementations_share_contract(self):
        for impl in (HiggsfieldProvider, FakeMotionProvider):
            self.assertTrue(issubclass(impl, MotionGenerationProvider))
        hp = HiggsfieldProvider(transport=FakeTransport())
        self.assertTrue(hp.credentials_present())
        caps = hp.capabilities('seedance_2_0')
        self.assertIn('start_image', caps['media_roles'])
        req = MotionRequest('S027', 'x', '0' * 64, 'p', 'n', 5, '16:9', '1080p', 24, 'higgsfield', 'seedance_2_0', 's')
        self.assertTrue(hp.validate_request(req))
        with self.assertRaises(FailClosed):
            hp.validate_request(replace(req, duration_seconds=20))


if __name__ == '__main__':
    unittest.main()
