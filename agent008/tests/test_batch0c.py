"""AGENT-008 Batch 0C tests: G04 derived-frame path and G02 production still-shot path.

Synthetic fixtures only (ffmpeg testsrc2 video, flat-colour PNGs, synthetic tones). No network, no provider,
no production asset, no registry or storage access. Shot specs come from the committed read-only approved-state
capture (v2: after the approved whoosh metadata repair), relabelled TEST-* so no output resembles a production shot.
"""
import copy
import os
import shutil
import socket
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy as np

from agent008 import derive, media, still
from agent008.derive import derive_frame
from agent008.episode import resolve_episode
from agent008.errors import FailClosed
from agent008.hashing import sha256_bytes, sha256_file
from agent008.inputs import load_hash_pins, load_snapshot
from agent008.still import check_still_contract, compose_still_shot
from agent008.tests.test_motion import PINS, SMALL, _wav

FIXTURE_V2 = Path(__file__).resolve().parent / 'fixtures' / 'ep005_approved_state_capture_v2.json'
WHOOSH_SHA = '53d06150dc0acc73cc972890510ba406486b178e4222eca253f848129bbed0c3'
SR = SMALL.audio_sample_rate


def _video(path, frames, size='320x180', rate=24):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', f'testsrc2=s={size}:r={rate}',
                    '-frames:v', str(frames), '-c:v', 'libx264', '-preset', 'ultrafast', '-pix_fmt', 'yuv420p',
                    '-threads', '1', str(path)], check=True)


def _png(path, w, h, color):
    a = np.zeros((h, w, 3), np.uint8)
    a[...] = color
    a[h // 3: h // 2, w // 3: w // 2] = (30, 40, 220)          # asymmetric block so crops are observable
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{w}x{h}', '-i', '-',
                    '-frames:v', '1', str(path)], input=a.tobytes(), check=True)


def _no_network(*a, **k):
    raise AssertionError('network access attempted')


class _Tmp(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)


class G04DerivedFrame(_Tmp):
    """C-D01..D09: exact-index derived frame, SHA-bound, REVIEW only, source untouched."""

    def setUp(self):
        super().setUp()
        self.src = self.tmp / 'src' / 'motion.mp4'
        self.src.parent.mkdir()
        _video(self.src, 121)                                     # S028 plan shape: 121 frames, 24 fps
        self.source = {'asset_id': 'TEST-MOTION-RAW', 'registry_id': 'test-row', 'classification':
                       'SHOT_MOTION/RAW_MOTION_SOURCE', 'registry_status': 'APPROVED', 'path': str(self.src),
                       'expected_sha256': sha256_file(self.src), 'expected_frames': 121}

    def all_frames(self):
        return media.decode_frames_rgb(self.src, 320, 180)

    def test_D01_exact_frame_extraction(self):
        frames = self.all_frames()
        self.assertEqual(len(frames), 121)
        for k in (0, 60, 119, 120):
            p = derive_frame(self.source, k, f'TEST-K{k}', self.tmp / f'o{k}')
            self.assertEqual(p['selected_frame_rgb_sha256'], sha256_bytes(frames[k].tobytes()), k)
            png = derive.decode_png_rgb(self.tmp / f'o{k}' / p['output']['file'])
            np.testing.assert_array_equal(png, frames[k])                    # lossless, exactly frame k
        self.assertNotEqual(sha256_bytes(frames[119].tobytes()), sha256_bytes(frames[120].tobytes()))

    def test_D02_source_sha_mismatch_fails_closed(self):
        bad = {**self.source, 'expected_sha256': '0' * 64}
        with self.assertRaises(FailClosed) as e:
            derive_frame(bad, 119, 'TEST-S028', self.tmp / 'o')
        self.assertEqual(e.exception.code, 'HASH_MISMATCH')
        self.assertFalse((self.tmp / 'o').exists())

    def test_D03_wrong_frame_index_fails_closed(self):
        for idx, code in ((121, 'FRAME_INDEX_OUT_OF_RANGE'), (500, 'FRAME_INDEX_OUT_OF_RANGE'),
                          (-1, 'FRAME_INDEX_INVALID'), (119.0, 'FRAME_INDEX_INVALID'), (True, 'FRAME_INDEX_INVALID')):
            with self.assertRaises(FailClosed) as e:
                derive_frame(self.source, idx, 'TEST-S028', self.tmp / 'o')
            self.assertEqual(e.exception.code, code, idx)
        pin_118 = sha256_bytes(self.all_frames()[118].tobytes())
        with self.assertRaises(FailClosed) as e:                              # pinned frame != requested index
            derive_frame(self.source, 119, 'TEST-S028', self.tmp / 'o', expected_frame_rgb_sha256=pin_118)
        self.assertEqual(e.exception.code, 'DERIVED_FRAME_MISMATCH')
        with self.assertRaises(FailClosed) as e:
            derive_frame({**self.source, 'expected_frames': 120}, 119, 'TEST-S028', self.tmp / 'o')
        self.assertEqual(e.exception.code, 'DERIVE_SOURCE_GEOMETRY_MISMATCH')
        self.assertFalse(any((self.tmp / 'o').glob('*.png')) if (self.tmp / 'o').exists() else False)

    def test_D04_derived_frame_provenance(self):
        p = derive_frame(self.source, 119, 'TEST-S028', self.tmp / 'o')
        on_disk = (self.tmp / 'o' / 'TEST-S028_DERIVED_FRAME_PROVENANCE.json').read_text()
        self.assertIn(p['deterministic_core_sha256'], on_disk)
        self.assertEqual(p['status'], 'REVIEW')
        self.assertEqual(p['target_shot_id'], 'TEST-S028')
        self.assertEqual(p['frame_index'], 119)
        self.assertEqual(p['frame_timestamp_s'], round(119 / 24, 6))
        self.assertEqual(p['source']['verified_sha256'], self.source['expected_sha256'])
        self.assertEqual(p['source']['asset_id'], 'TEST-MOTION-RAW')
        self.assertEqual(p['source']['decoded_frames'], 121)
        self.assertEqual(p['output']['sha256'], sha256_file(self.tmp / 'o' / p['output']['file']))
        self.assertEqual(p['proposed_registry'], {**p['proposed_registry'], 'asset_type': 'SHOT_FRAME',
                                                  'asset_subtype': 'DERIVED_FRAME', 'registered': False})
        self.assertFalse(p['human_approval']['approved'])
        self.assertEqual(p['safety']['provider_calls'], 0)

    def test_D05_no_source_mutation(self):
        before = (sha256_file(self.src), os.stat(self.src).st_mtime_ns, sorted(os.listdir(self.src.parent)))
        derive_frame(self.source, 119, 'TEST-S028', self.tmp / 'o')
        self.assertEqual(before, (sha256_file(self.src), os.stat(self.src).st_mtime_ns, sorted(os.listdir(self.src.parent))))
        with self.assertRaises(FailClosed) as e:                              # never overwrites an output
            derive_frame(self.source, 119, 'TEST-S028', self.tmp / 'o')
        self.assertEqual(e.exception.code, 'OUTPUT_EXISTS')

    def test_D06_two_run_determinism_with_crop_and_scale(self):
        kw = dict(crop={'x': 80, 'y': 45, 'w': 160, 'h': 90}, scale={'w': 320, 'h': 180})
        a = derive_frame(self.source, 119, 'TEST-S028', self.tmp / 'a', **kw)
        b = derive_frame(self.source, 119, 'TEST-S028', self.tmp / 'b', **kw)
        self.assertEqual(a['output']['sha256'], b['output']['sha256'])
        self.assertEqual(a['deterministic_core_sha256'], b['deterministic_core_sha256'])
        crop = derive_frame(self.source, 119, 'TEST-S028C', self.tmp / 'c', crop=kw['crop'])
        np.testing.assert_array_equal(derive.decode_png_rgb(self.tmp / 'c' / crop['output']['file']),
                                      self.all_frames()[119][45:135, 80:240])
        for bad, code in (({'crop': {'x': 300, 'y': 0, 'w': 100, 'h': 90}}, 'CROP_OUT_OF_BOUNDS'),
                          ({'scale': {'w': 300, 'h': 300}}, 'SCALE_ASPECT_MISMATCH')):
            with self.assertRaises(FailClosed) as e:
                derive_frame(self.source, 119, 'TEST-BAD', self.tmp / 'bad', **bad)
            self.assertEqual(e.exception.code, code)

    def test_D07_unapproved_or_unhashed_source_fails_closed(self):
        for patch, code in (({'registry_status': 'REVIEW'}, 'DERIVE_SOURCE_NOT_APPROVED'),
                            ({'expected_sha256': None}, 'NO_EXPECTED_HASH')):
            with self.assertRaises(FailClosed) as e:
                derive_frame({**self.source, **patch}, 119, 'TEST-S028', self.tmp / 'o')
            self.assertEqual(e.exception.code, code)

    def test_D08_no_provider_or_network(self):
        with mock.patch.object(socket, 'socket', _no_network), mock.patch.object(socket, 'create_connection', _no_network):
            derive_frame(self.source, 119, 'TEST-S028', self.tmp / 'o')
        text = Path(derive.__file__).read_text()
        for mod in ('higgsfield', 'provider', 'http', 'urllib', 'requests', 'source_upload'):
            self.assertNotIn(f'import {mod}', text)
            self.assertNotIn(f'.{mod} import', text)


class G02StillShot(_Tmp):
    """C-S01..S10: approved frame held for the exact shot length, governed audio, REVIEW only."""

    @classmethod
    def setUpClass(cls):
        cls.episode = {r['shot_id']: r for r in resolve_episode(load_snapshot(FIXTURE_V2), load_hash_pins(PINS), SMALL)}

    def setUp(self):
        super().setUp()
        self.frame_path = self.tmp / 'frame.png'
        _png(self.frame_path, 960, 540, (200, 160, 120))
        _wav(self.tmp / 'amb.wav', 2.0, 0, 0.003)
        _wav(self.tmp / 'foley.wav', 0.4, 220, 0.2)
        _wav(self.tmp / 'dlg.wav', 1.2, 330, 0.2)
        self.assets = {'AMB-BATHROOM-QUIET-v01': self.tmp / 'amb.wav', 'TEST-FOLEY': self.tmp / 'foley.wav',
                       'TEST-DLG': self.tmp / 'dlg.wav'}
        self.spec = {**copy.deepcopy(self.episode['S023']['spec']), 'shot_id': 'TEST-S023'}
        self.frame = {'asset_id': 'TEST-FRAME', 'registry_id': 'test-row', 'classification': 'SHOT_FRAME/BASE_FRAME',
                      'registry_status': 'APPROVED', 'shot_id': 'TEST-S023', 'path': str(self.frame_path),
                      'expected_sha256': sha256_file(self.frame_path)}

    def run_still(self, sub, spec=None, frame=None, timing=None, **kw):
        return compose_still_shot(spec or self.spec, frame or self.frame, SMALL, self.assets, timing or {}, self.tmp / sub, **kw)

    def with_dialogue(self):
        slot = {'shot_id': 'TEST-S023', 'speaker': 'Mikko', 'text': 'Test line.'}
        spec = {**self.spec, 'dialogue_slots': [slot]}
        track = {**slot, 'audio_asset_id': 'TEST-DLG', 'expected_sha256': sha256_file(self.tmp / 'dlg.wav'),
                 'registry_status': 'APPROVED', 'start_seconds': 0.5, 'gain_db': 0.0}
        return spec, track

    def test_S01_deterministic_still_output(self):
        p = self.run_still('a')
        q = p['qc']
        self.assertEqual(q['automatic_result'], 'PASS', q['issues'])
        self.assertEqual((q['output_frames'], q['output_resolution'], q['output_fps']), (72, '480x270', '24/1'))
        self.assertAlmostEqual(q['output_duration_s'], 3.0, places=3)
        self.assertEqual(p['status'], 'REVIEW')
        self.assertEqual(p['source_frame']['verified_sha256'], self.frame['expected_sha256'])
        self.assertEqual(p['layout']['fit_scale'], 0.5)
        dec = media.decode_frames_rgb(self.tmp / 'a' / p['outputs']['review_mp4']['file'], 480, 270)
        self.assertEqual(len(dec), 72)
        self.assertLess(float(np.abs(dec[0].astype(int) - dec[-1].astype(int)).mean()), 1.0)   # held, not animated

    def test_S02_two_run_determinism(self):
        spec, track = self.with_dialogue()
        timing = {'dialogue': [track]}
        a = self.run_still('a', spec=spec, timing=timing, crop={'x': 0, 'y': 0, 'w': 480, 'h': 270})
        b = self.run_still('b', spec=spec, timing=timing, crop={'x': 0, 'y': 0, 'w': 480, 'h': 270})
        self.assertEqual(a['outputs'], b['outputs'])
        self.assertEqual(sha256_file(self.tmp / 'a' / 'TEST-S023_STILL_REVIEW.mp4'),
                         sha256_file(self.tmp / 'b' / 'TEST-S023_STILL_REVIEW.mp4'))
        self.assertEqual(a['deterministic_core_sha256'], b['deterministic_core_sha256'])
        self.assertEqual(a['layout']['fit_scale'], 1.0)

    def test_S03_source_sha_mismatch_fails_closed(self):
        with self.assertRaises(FailClosed) as e:
            self.run_still('a', frame={**self.frame, 'expected_sha256': 'f' * 64})
        self.assertEqual(e.exception.code, 'HASH_MISMATCH')
        self.assertFalse((self.tmp / 'a').exists())

    def test_S04_source_identity_fails_closed(self):
        for patch, code in (({'registry_status': 'REVIEW'}, 'STILL_SOURCE_NOT_APPROVED'),
                            ({'classification': 'SHOT_MOTION/RAW_MOTION_SOURCE'}, 'STILL_SOURCE_NOT_A_SHOT_FRAME'),
                            ({'shot_id': 'TEST-S024'}, 'SHOT_IDENTITY_MISMATCH'),
                            ({'expected_sha256': None}, 'NO_EXPECTED_HASH')):
            with self.assertRaises(FailClosed) as e:
                self.run_still('a', frame={**self.frame, **patch})
            self.assertEqual(e.exception.code, code)
        derived = self.run_still('d', frame={**self.frame, 'classification': 'SHOT_FRAME/DERIVED_FRAME'})
        self.assertEqual(derived['source_frame']['classification'], 'SHOT_FRAME/DERIVED_FRAME')

    def test_S05_dialogue_requirement_fails_closed(self):
        spec, track = self.with_dialogue()
        cases = (({}, 'DIALOGUE_SLOT_UNFILLED'),
                 ({'dialogue': [{**track, 'registry_status': 'REVIEW'}]}, 'DIALOGUE_NOT_APPROVED'),
                 ({'dialogue': [{**track, 'expected_sha256': '0' * 64}]}, 'HASH_MISMATCH'),
                 ({'dialogue': [{**track, 'text': 'Other line.'}]}, 'DIALOGUE_TEXT_MISMATCH'),
                 ({'dialogue': [{**track, 'start_seconds': 2.5}]}, 'DIALOGUE_OVERRUNS_SHOT'))
        for timing, code in cases:
            with self.assertRaises(FailClosed) as e:
                self.run_still('x', spec=spec, timing=timing)
            self.assertEqual(e.exception.code, code)
        with self.assertRaises(FailClosed) as e:                              # a clip with no slot is rejected too
            self.run_still('x', timing={'dialogue': [track]})
        self.assertEqual(e.exception.code, 'DIALOGUE_UNEXPECTED')
        ok = self.run_still('ok', spec=spec, timing={'dialogue': [track]})
        self.assertEqual([(c['kind'], c['start_s']) for c in ok['audio_cues'] if c['kind'] == 'DIALOGUE'],
                         [('DIALOGUE', 0.5)])

    def test_S06_audio_event_semantics_preserved(self):
        spec = {**self.spec, 'event_audio': [{'asset_id': 'TEST-FOLEY', 'audio_role': 'FOLEY'}]}
        with self.assertRaises(FailClosed) as e:
            self.run_still('x', spec=spec)
        self.assertEqual(e.exception.code, 'EVENT_AUDIO_WITHOUT_TIMING')
        p = self.run_still('ok', spec=spec, timing={'named': {'TEST-FOLEY': {'start_seconds': 1.0, 'gain_db': 0.0}}})
        cues = {c['kind']: c for c in p['audio_cues']}
        self.assertEqual((cues['BED']['asset_id'], cues['BED']['start_s'], cues['BED']['end_s']),
                         ('AMB-BATHROOM-QUIET-v01', 0.0, 3.0))                 # ambience bed spans the shot
        self.assertEqual((cues['EVENT']['start_s'], cues['EVENT']['role']), (1.0, 'FOLEY'))
        self.assertAlmostEqual(cues['EVENT']['end_s'], 1.4, places=6)          # once, never tiled
        mix = media.load_audio(self.tmp / 'ok' / 'TEST-S023_STILL_MIX.wav', SR, 2)
        clip = media.load_audio(self.tmp / 'foley.wav', SR, 2)
        bed_only = self.run_still('bed')
        bed = media.load_audio(self.tmp / 'bed' / 'TEST-S023_STILL_MIX.wav', SR, 2)
        diff = mix - bed
        s = int(1.0 * SR)
        np.testing.assert_allclose(diff[s:s + len(clip)], clip, atol=2e-6)     # 24-bit quantisation tolerance
        self.assertLess(float(np.abs(diff[s + len(clip) + 10:]).max()), 2e-6)
        self.assertLess(float(np.abs(diff[:s - 10]).max()), 2e-6)
        self.assertIn('AMB-BATHROOM-QUIET-v01', [b['asset_id'] for b in self.spec['mapped_audio']])

    def test_S07_unsupported_contracts_fail_closed(self):
        s005 = {**copy.deepcopy(self.episode['S005']['spec']), 'shot_id': 'TEST-S023'}
        cases = ((s005, 'STILL_OVERLAYS_NEED_G03_ANCHORS'),
                 ({**self.spec, 'treatments': [{'treatment_id': 'TREATMENT-EP005-MIRROR-GLINT-v01'}]},
                  'STILL_TREATMENTS_NEED_G08'),
                 ({**self.spec, 'video_generation_required': True}, 'STILL_PATH_NOT_FOR_MOTION_SHOT'),
                 ({**self.spec, 'frames': 71}, 'STILL_DURATION_FRAME_MISMATCH'))
        for spec, code in cases:
            with self.assertRaises(FailClosed) as e:
                self.run_still('x', spec=spec)
            self.assertEqual(e.exception.code, code)
        with self.assertRaises(FailClosed) as e:
            self.run_still('x', crop={'x': 900, 'y': 0, 'w': 200, 'h': 100})
        self.assertEqual(e.exception.code, 'CROP_OUT_OF_BOUNDS')

    def test_S08_no_source_mutation_or_overwrite(self):
        before = (sha256_file(self.frame_path), os.stat(self.frame_path).st_mtime_ns)
        self.run_still('a')
        self.assertEqual(before, (sha256_file(self.frame_path), os.stat(self.frame_path).st_mtime_ns))
        with self.assertRaises(FailClosed) as e:
            self.run_still('a')
        self.assertEqual(e.exception.code, 'OUTPUT_EXISTS')

    def test_S09_no_provider_or_network(self):
        with mock.patch.object(socket, 'socket', _no_network), mock.patch.object(socket, 'create_connection', _no_network):
            p = self.run_still('a')
        self.assertEqual(p['safety'], {'provider_calls': 0, 'auto_approved': False, 'registered': False,
                                       'source_mutated': False})
        text = Path(still.__file__).read_text()
        for mod in ('higgsfield', 'provider', 'http', 'urllib', 'requests', 'source_upload'):
            self.assertNotIn(f'import {mod}', text)
            self.assertNotIn(f'.{mod} import', text)

    def test_S10_derived_frame_feeds_still_path(self):
        src = self.tmp / 'motion.mp4'
        _video(src, 30, size='480x270')
        d = derive_frame({'asset_id': 'TEST-RAW', 'registry_status': 'APPROVED', 'path': str(src),
                          'expected_sha256': sha256_file(src)}, 29, 'TEST-S023', self.tmp / 'derived')
        png = self.tmp / 'derived' / d['output']['file']
        frame = {**self.frame, 'classification': 'SHOT_FRAME/DERIVED_FRAME', 'path': str(png),
                 'expected_sha256': d['output']['sha256']}
        with self.assertRaises(FailClosed):                                   # REVIEW candidate is not usable
            self.run_still('x', frame={**frame, 'registry_status': 'REVIEW'})
        p = self.run_still('a', frame=frame)                                  # only as a (test) approved frame
        self.assertEqual(p['source_frame']['verified_sha256'], d['output']['sha256'])


class EpisodeAfterWhooshRepair(unittest.TestCase):
    """C-E01..E02: v2 capture differs from v1 only in the whoosh row; S007 now resolves; S023/S029 fit G02."""

    @classmethod
    def setUpClass(cls):
        cls.snap = load_snapshot(FIXTURE_V2)
        from agent008.config import load_output_spec
        cls.res = {r['shot_id']: r for r in resolve_episode(cls.snap, load_hash_pins(PINS), load_output_spec())}

    def test_E01_whoosh_resolves_from_registry_sha(self):
        self.assertEqual(self.res['S007']['status'], 'SPEC')
        named = [s for s in self.res['S007']['spec']['named_sfx'] if s['asset_id'] == 'SFX-MIKKO-TRY-WHOOSH']
        self.assertEqual([(s['expected_sha256'], s['sha256_source'], s['audio_role']) for s in named],
                         [(WHOOSH_SHA, 'asset_registry.metadata_json.sha256', 'SFX')])
        blocked = {k: r['blocker']['code'] for k, r in self.res.items() if r['status'] == 'BLOCKED'}
        self.assertEqual(blocked, {s: 'OVERLAY_TRANSITION_UNSUPPORTED_V01' for s in ('S009', 'S015', 'S021')})

    def test_E02_still_contract_fit(self):
        from agent008.config import load_output_spec
        out = {}
        for sid, r in self.res.items():
            if r['status'] != 'SPEC' or r['spec']['video_generation_required']:
                continue
            try:
                check_still_contract(r['spec'], load_output_spec())
                out[sid] = 'OK'
            except FailClosed as e:
                out[sid] = e.code
        self.assertEqual(out['S023'], 'OK')
        self.assertEqual(out['S029'], 'OK')
        self.assertEqual(out['S005'], 'STILL_OVERLAYS_NEED_G03_ANCHORS')
        self.assertNotIn('S027', out)


if __name__ == '__main__':
    unittest.main()
