"""AGENT-008 Batch 0 tests: governed audio roles (no short-audio looping) and full-episode spec coverage.

No network, no paid calls. The episode fixture is a read-only GET capture of the approved state
(readiness edc4ad58 -> manifest 45cc7493 + registry), produced by `python3 -m agent008.episode --capture-out`.
"""
import copy
import json
import shutil
import tempfile
import unittest
from pathlib import Path

import numpy as np

from agent008 import media
from agent008.config import load_output_spec
from agent008.episode import resolve_episode
from agent008.errors import FailClosed
from agent008.hashing import canonical_sha256
from agent008.inputs import load_hash_pins, load_snapshot, validate_readiness
from agent008.motion.compose import mix_motion_audio, resolve_dialogue
from agent008.resolve import Resolver
from agent008.spec import audio_role, build_shot_spec
from agent008.tests.test_motion import PINS, SMALL, SNAP, _wav

FIXTURE = Path(__file__).resolve().parent / 'fixtures' / 'ep005_approved_state_capture_v1.json'
SR = SMALL.audio_sample_rate
EXPECTED_BLOCKERS = {'S007': 'NO_EXPECTED_HASH', 'S009': 'OVERLAY_TRANSITION_UNSUPPORTED_V01',
                     'S015': 'OVERLAY_TRANSITION_UNSUPPORTED_V01', 'S021': 'OVERLAY_TRANSITION_UNSUPPORTED_V01'}


def s027_spec(snapshot_path=SNAP):
    snap = load_snapshot(snapshot_path)
    rd = validate_readiness(snap, 'edc4ad58-3e5d-4ac2-9c74-c9af03af363f')
    return build_shot_spec(snap, Resolver(rd, snap['asset_registry'], load_hash_pins(PINS)), 'S027', SMALL,
                           motion_phase=True)


class AudioRoles(unittest.TestCase):
    """B0-A01..A09: AMBIENCE is the only looping role; FOLEY/SFX/DIALOGUE play once at explicit times."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        _wav(self.tmp / 'amb.wav', 2.0, 0, 0.003)
        _wav(self.tmp / 'chord.wav', 3.0, 660, 0.2)
        _wav(self.tmp / 'foley.wav', 0.3, 220, 0.2)
        _wav(self.tmp / 'pop.wav', 0.2, 880, 0.2)
        self.assets = {'AMB-BATHROOM-QUIET-v01': self.tmp / 'amb.wav', 'SFX-WIN-SPARKLE-CHORD': self.tmp / 'chord.wav',
                       'FOLEY-TEST': self.tmp / 'foley.wav', 'SFX-POP-TEST': self.tmp / 'pop.wav'}
        base = s027_spec()
        self.spec = {**base, 'dialogue_slots': [], 'named_sfx': [], 'mapped_audio': []}
        self.total = int(round(self.spec['frames'] / SMALL.fps * SR))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def mix(self, spec, timing):
        return mix_motion_audio(spec, self.assets, timing, SMALL, ())[0]

    def event(self, aid, role):
        return {'asset_id': aid, 'audio_role': role}

    def assert_once(self, aid, role, start_s, timing_extra=None):
        spec = {**self.spec, 'event_audio': [self.event(aid, role)]}
        t = {'named': {aid: {'start_seconds': start_s, 'gain_db': 0.0, **(timing_extra or {})}}}
        out = self.mix(spec, t)
        clip = media.load_audio(self.assets[aid], SR, 2)
        s = int(round(start_s * SR))
        np.testing.assert_allclose(out[s:s + len(clip)], clip, atol=1e-12)
        self.assertEqual(float(np.abs(out[:s]).max()), 0.0)
        self.assertEqual(float(np.abs(out[s + len(clip):]).max()), 0.0)       # never tiled to the shot length
        return out

    def test_A01_foley_does_not_loop(self):
        self.assert_once('FOLEY-TEST', 'FOLEY', 1.0)

    def test_A02_sfx_does_not_loop(self):
        self.assert_once('SFX-POP-TEST', 'SFX', 2.5)

    def test_A03_named_sfx_once_with_fade_by(self):
        spec = {**self.spec, 'named_sfx': [{'asset_id': 'SFX-WIN-SPARKLE-CHORD', 'audio_role': 'SFX'}]}
        out = self.mix(spec, {'named': {'SFX-WIN-SPARKLE-CHORD': {'start_seconds': 1.0, 'gain_db': 0.0,
                                                                  'fade_out_seconds': 1.0,
                                                                  'fade_complete_by_seconds': 3.5}}})
        self.assertEqual(float(np.abs(out[:SR]).max()), 0.0)
        self.assertEqual(float(np.abs(out[int(3.5 * SR):]).max()), 0.0)     # cut by the fade; no repeat

    def test_A04_dialogue_once(self):
        spec = {**self.spec, 'dialogue_slots': [{'shot_id': 'S027', 'speaker': 'Mikko', 'text': 'We did it! I feel fresh.'}]}
        from agent008.hashing import sha256_file
        t = {'dialogue': [{'shot_id': 'S027', 'speaker': 'Mikko', 'text': 'We did it! I feel fresh.',
                           'audio_asset_id': 'FOLEY-TEST', 'expected_sha256': sha256_file(self.assets['FOLEY-TEST']),
                           'registry_status': 'APPROVED', 'start_seconds': 0.5, 'gain_db': 0.0}]}
        dlg = resolve_dialogue(spec, self.assets, t)
        out = mix_motion_audio(spec, self.assets, t, SMALL, dlg)[0]
        clip = media.load_audio(self.assets['FOLEY-TEST'], SR, 2)
        s = int(round(0.5 * SR))
        self.assertEqual(float(np.abs(out[s + len(clip):]).max()), 0.0)
        self.assertEqual(float(np.abs(out[:s]).max()), 0.0)

    def test_A05_ambience_bed_spans_and_loops(self):
        spec = {**self.spec, 'mapped_audio': [{'asset_id': 'AMB-BATHROOM-QUIET-v01', 'audio_role': 'AMBIENCE'}]}
        out = self.mix(spec, {})
        amb = media.load_audio(self.assets['AMB-BATHROOM-QUIET-v01'], SR, 2)
        self.assertEqual(len(out), self.total)
        f = int(0.02 * SR)
        np.testing.assert_allclose(out[len(amb) + f:2 * len(amb)], amb[f:], atol=1e-12)   # loop seam = exact repeat
        self.assertGreater(float(np.abs(out[self.total - SR:self.total - f]).max()), 0.0)  # reaches the end

    def test_A06_missing_event_timestamp_fails_closed(self):
        spec = {**self.spec, 'event_audio': [self.event('FOLEY-TEST', 'FOLEY')]}
        with self.assertRaises(FailClosed) as e:
            self.mix(spec, {'named': {}})
        self.assertEqual(e.exception.code, 'EVENT_AUDIO_WITHOUT_TIMING')
        spec = {**self.spec, 'named_sfx': [self.event('SFX-POP-TEST', 'SFX')]}
        with self.assertRaises(FailClosed) as e:
            self.mix(spec, {})
        self.assertEqual(e.exception.code, 'NAMED_AUDIO_WITHOUT_TIMING')

    def test_A07_event_overrun_without_explicit_trim_fails_closed(self):
        spec = {**self.spec, 'event_audio': [self.event('SFX-WIN-SPARKLE-CHORD', 'SFX')]}
        with self.assertRaises(FailClosed) as e:
            self.mix(spec, {'named': {'SFX-WIN-SPARKLE-CHORD': {'start_seconds': 3.0}}})
        self.assertEqual(e.exception.code, 'EVENT_OVERRUNS_SHOT')

    def test_A08_role_misuse_fails_closed(self):
        with self.assertRaises(FailClosed) as e:
            self.mix({**self.spec, 'mapped_audio': [self.event('FOLEY-TEST', 'FOLEY')]}, {})
        self.assertEqual(e.exception.code, 'AUDIO_ROLE_NOT_LOOPABLE')
        with self.assertRaises(FailClosed) as e:
            self.mix({**self.spec, 'event_audio': [self.event('AMB-BATHROOM-QUIET-v01', 'AMBIENCE')]},
                     {'named': {'AMB-BATHROOM-QUIET-v01': {'start_seconds': 0.0}}})
        self.assertEqual(e.exception.code, 'AUDIO_ROLE_NOT_EVENT')

    def test_A09_role_comes_from_registry_subtype(self):
        self.assertEqual(audio_role({'asset_id': 'x', 'asset_type': 'AUDIO', 'asset_subtype': 'FOLEY'}), 'FOLEY')
        for bad in ({'asset_id': 'x', 'asset_type': 'AUDIO', 'asset_subtype': None},
                    {'asset_id': 'x', 'asset_type': 'AUDIO', 'asset_subtype': 'MUSIC'}):
            with self.assertRaises(FailClosed) as e:
                audio_role(bad)
            self.assertEqual(e.exception.code, 'AUDIO_ROLE_UNKNOWN')
        with self.assertRaises(FailClosed) as e:
            audio_role({'asset_id': 'x', 'asset_type': 'PROP', 'asset_subtype': None})
        self.assertEqual(e.exception.code, 'AUDIO_ROLE_NOT_AUDIO')


class EpisodeCoverage(unittest.TestCase):
    """B0-E01..E06: every approved EP005 shot resolves to a governed spec or an explicit governed blocker."""

    @classmethod
    def setUpClass(cls):
        cls.snap = load_snapshot(FIXTURE)
        cls.res = resolve_episode(cls.snap, load_hash_pins(PINS), load_output_spec())

    def test_E01_fixture_is_the_approved_state(self):
        pm = self.snap['production_manifest']
        self.assertEqual(pm['id'], '45cc7493-80b4-4e8d-b71d-fbd7fd3656ed')
        self.assertEqual(self.snap['readiness_manifest']['id'], 'edc4ad58-3e5d-4ac2-9c74-c9af03af363f')
        self.assertEqual(pm['status'], 'APPROVED')
        self.assertEqual(canonical_sha256(self.snap['asset_registry']), self.snap['asset_registry_canonical_sha256'])

    def test_E02_all_29_shots_accounted_for(self):
        ids = [r['shot_id'] for r in self.res]
        self.assertEqual(ids, [f'S{i:03d}' for i in range(1, 30)])
        self.assertTrue(all(r['status'] in ('SPEC', 'BLOCKED') for r in self.res))
        self.assertEqual(sum(r['spec']['frames'] for r in self.res if r['status'] == 'SPEC')
                         + sum(int(round((s['end_seconds'] - s['start_seconds']) * 24))
                               for s in self.snap['production_manifest']['manifest_json_reduced']['shot_plans']
                               if s['shot_id'] in EXPECTED_BLOCKERS), 2880)

    def test_E03_blockers_are_explicit_and_governed(self):
        blocked = {r['shot_id']: r['blocker']['code'] for r in self.res if r['status'] == 'BLOCKED'}
        self.assertEqual(blocked, EXPECTED_BLOCKERS)

    def test_E04_missing_shot_cannot_disappear(self):
        snap = copy.deepcopy(self.snap)
        snap['production_manifest']['manifest_json_reduced']['shot_plans'].pop(5)
        with self.assertRaises(FailClosed) as e:
            resolve_episode(snap, load_hash_pins(PINS), load_output_spec())
        self.assertEqual(e.exception.code, 'EPISODE_SNAPSHOT_INCOMPLETE')

    def test_E05_audio_roles_in_episode_specs(self):
        specs = {r['shot_id']: r['spec'] for r in self.res if r['status'] == 'SPEC'}
        for sid in ('S002', 'S014', 'S020', 'S028'):
            self.assertEqual([(e['asset_id'], e['audio_role']) for e in specs[sid]['event_audio']],
                             [('FOLEY-CLOTH-SOFT-v01', 'FOLEY')])
        self.assertEqual([(e['asset_id'], e['audio_role']) for e in specs['S025']['event_audio']],
                         [('SFX-COMPLETION-POP-v01', 'SFX')])
        for s in specs.values():
            self.assertTrue(all(b['audio_role'] == 'AMBIENCE' for b in s['mapped_audio']))
        self.assertEqual(specs['S025']['active_overlays'], [])                    # CLEAN REVEAL rule preserved

    def test_E06_s027_spec_unchanged(self):
        new = build_shot_spec(self.snap, Resolver(validate_readiness(self.snap, 'edc4ad58-3e5d-4ac2-9c74-c9af03af363f'),
                                                  self.snap['asset_registry'], load_hash_pins(PINS)),
                              'S027', SMALL, motion_phase=True)
        old = s027_spec()
        for k in ('frames', 'duration_seconds', 'active_overlays', 'treatments', 'dialogue_slots', 'event_audio',
                  'music_present', 'protected_participation_hold'):
            self.assertEqual(new[k], old[k], k)
        for k in ('mapped_audio', 'named_sfx', 'characters', 'props'):
            self.assertEqual([(a['asset_id'], a['expected_sha256']) for a in new[k]],
                             [(a['asset_id'], a['expected_sha256']) for a in old[k]], k)
        self.assertEqual(new['event_audio'], [])


if __name__ == '__main__':
    unittest.main()
