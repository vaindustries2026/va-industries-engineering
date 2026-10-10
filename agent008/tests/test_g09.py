"""AGENT-008 G09 tests: dialogue timing, overlap and visual-hold guard. Synthetic audio only; no network, no provider."""
import copy
import shutil
import tempfile
import unittest
from pathlib import Path

import numpy as np

from agent008 import media
from agent008.dialogue_timing import govern_dialogue_timing
from agent008.episode import resolve_episode
from agent008.errors import FailClosed
from agent008.hashing import sha256_file
from agent008.inputs import load_hash_pins, load_snapshot
from agent008.motion.compose import mix_motion_audio, resolve_dialogue
from agent008.still import compose_still_shot
from agent008.tests.test_batch0 import s027_spec
from agent008.tests.test_batch0c import FIXTURE_V2, _png
from agent008.tests.test_motion import PINS, SMALL, _wav

SR = SMALL.audio_sample_rate
S027_TEXT = 'We did it! I feel fresh.'


class G09(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s027 = s027_spec()                                     # 5.0 s, 1 Mikko slot (authoritative)
        cls.s023 = resolve_episode(load_snapshot(FIXTURE_V2), load_hash_pins(PINS), SMALL)[22]['spec']

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        _wav(self.tmp / 'a.wav', 1.0, 330, 0.2)                    # exactly 48000 samples
        _wav(self.tmp / 'b.wav', 1.0, 440, 0.2)
        _wav(self.tmp / 'mikko.wav', 1.625, 300, 0.2)              # S027 clip length (0.500 -> 2.125 s)
        self.inputs = {'DLG-A': self.tmp / 'a.wav', 'DLG-B': self.tmp / 'b.wav', 'DLG-M': self.tmp / 'mikko.wav'}
        self.two = {**copy.deepcopy(self.s027), 'shot_id': 'TEST-G09', 'dialogue_slots': [
            {'shot_id': 'TEST-G09', 'speaker': 'Lumi', 'text': 'Line one.'},
            {'shot_id': 'TEST-G09', 'speaker': 'Mikko', 'text': 'Line two.'}]}

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def track(self, spec, i, aid, start):
        s = spec['dialogue_slots'][i]
        return {'shot_id': s['shot_id'], 'speaker': s['speaker'], 'text': s['text'], 'audio_asset_id': aid,
                'expected_sha256': sha256_file(self.inputs[aid]), 'registry_status': 'APPROVED',
                'start_seconds': start, 'gain_db': 0.0}

    def govern(self, spec, starts, **extra):
        aids = ['DLG-A', 'DLG-B']
        timing = {'dialogue': [self.track(spec, i, aids[i], s) for i, s in enumerate(starts)], **extra}
        dlg = resolve_dialogue(spec, self.inputs, timing)
        return govern_dialogue_timing(spec, dlg, self.inputs, timing, SMALL), dlg, timing

    def code(self, fn):
        with self.assertRaises(FailClosed) as e:
            fn()
        return e.exception.code

    def test_G01_valid_dialogue_window(self):
        r, _, _ = self.govern(self.two, [0.5, 2.0])
        self.assertEqual([(l['start_sample'], l['end_sample']) for l in r['lines']], [(24000, 72000), (96000, 144000)])
        self.assertEqual([(l['start_s'], l['end_s']) for l in r['lines']], [(0.5, 1.5), (2.0, 3.0)])
        self.assertEqual(r['window'], {'start_s': 0.0, 'end_s': 5.0, 'pre_hold_seconds': 0.0, 'post_hold_seconds': 0.0})
        self.assertEqual(r['visual_holds'], {'before_first_line_s': 0.5, 'after_last_line_s': 2.0})
        self.assertEqual(r['overlaps'], [])
        self.assertEqual(r, self.govern(self.two, [0.5, 2.0])[0])          # deterministic

    def test_G02_dialogue_overrun_fails_closed(self):
        self.assertEqual(self.code(lambda: self.govern(self.two, [0.5, 4.5])), 'DIALOGUE_OVERRUNS_SHOT')
        self.assertEqual(self.code(lambda: self.govern(self.two, [0.5, 3.5], dialogue_window={'post_hold_seconds': 1.0})),
                         'DIALOGUE_OUTSIDE_WINDOW')
        self.assertEqual(self.code(lambda: self.govern(self.two, [0.5, 2.0], dialogue_window={'post_hold_seconds': 5.0})),
                         'DIALOGUE_WINDOW_INVALID')
        self.assertEqual(self.code(lambda: self.govern(self.two, [0.5, 2.0], dialogue_window={'tail': 1.0})),
                         'DIALOGUE_WINDOW_INVALID')

    def test_G03_unauthorised_overlap_fails_closed(self):
        self.assertEqual(self.code(lambda: self.govern(self.two, [0.5, 1.2])), 'DIALOGUE_OVERLAP_UNAUTHORISED')
        self.assertEqual(self.code(lambda: self.govern(self.two, [1.0, 1.0])), 'DIALOGUE_OVERLAP_UNAUTHORISED')
        self.assertEqual(self.code(lambda: self.govern(self.two, [2.0, 0.5])), 'DIALOGUE_ORDER_MISMATCH')
        r, _, _ = self.govern(self.two, [0.5, 1.5])                         # touching (end == next start) is not overlap
        self.assertEqual(r['overlaps'], [])

    def test_G04_authorised_overlap_valid(self):
        ok = [{'slots': [0, 1], 'max_overlap_seconds': 0.3, 'authorised_by': 'TEST human decision'}]
        r, _, timing = self.govern(self.two, [0.5, 1.2], dialogue_overlaps=ok)
        self.assertEqual(r['overlaps'], [{'slots': [0, 1], 'overlap_s': 0.3, 'authorised_by': 'TEST human decision',
                                          'max_overlap_seconds': 0.3}])
        dlg = resolve_dialogue(self.two, self.inputs, timing)
        mix, cues, _ = mix_motion_audio({**self.two, 'mapped_audio': [], 'named_sfx': [], 'event_audio': []},
                                        self.inputs, timing, SMALL, dlg)
        self.assertEqual([c['kind'] for c in cues], ['DIALOGUE', 'DIALOGUE'])     # both lines placed, once each
        self.assertEqual(self.code(lambda: self.govern(self.two, [0.5, 1.1], dialogue_overlaps=ok)),
                         'DIALOGUE_OVERLAP_EXCEEDS_AUTHORISED')
        self.assertEqual(self.code(lambda: self.govern(self.two, [0.5, 2.0], dialogue_overlaps=ok)),
                         'DIALOGUE_OVERLAP_DECLARED_NOT_PRESENT')
        for bad in ({'slots': [0, 1], 'max_overlap_seconds': 0.3}, {'slots': [0, 0], 'max_overlap_seconds': 0.3,
                    'authorised_by': 'x'}, {'slots': [0, 5], 'max_overlap_seconds': 0.3, 'authorised_by': 'x'},
                    {'slots': [0, 1], 'max_overlap_seconds': 0, 'authorised_by': 'x'}):
            self.assertEqual(self.code(lambda: self.govern(self.two, [0.5, 1.2], dialogue_overlaps=[bad])),
                             'DIALOGUE_OVERLAP_DECLARATION_INVALID')

    def test_G05_missing_required_dialogue_fails_closed(self):
        _, dlg, timing = self.govern(self.two, [0.5, 2.0])
        self.assertEqual(self.code(lambda: govern_dialogue_timing(self.two, dlg[:1], self.inputs, timing, SMALL)),
                         'DIALOGUE_SLOT_UNFILLED')
        self.assertEqual(self.code(lambda: mix_motion_audio(self.two, self.inputs, timing, SMALL, ())),
                         'DIALOGUE_SLOT_UNFILLED')                          # cannot vanish at mix time either
        self.assertEqual(self.code(lambda: resolve_dialogue(self.two, self.inputs, {'dialogue': timing['dialogue'][:1]})),
                         'DIALOGUE_SLOT_UNFILLED')
        _wav(self.tmp / 'empty.wav', 0.0, 330, 0.2)
        self.inputs['DLG-A'] = self.tmp / 'empty.wav'
        self.assertEqual(self.code(lambda: self.govern(self.two, [0.5, 2.0])), 'DIALOGUE_CLIP_EMPTY')

    def test_G06_deterministic_pre_dialogue_hold(self):
        w = {'dialogue_window': {'pre_hold_seconds': 1.0}}
        self.assertEqual(self.code(lambda: self.govern(self.two, [0.99, 2.5], **w)), 'DIALOGUE_OUTSIDE_WINDOW')
        r, _, timing = self.govern(self.two, [1.0, 2.5], **w)
        self.assertEqual(r['window']['start_s'], 1.0)
        self.assertEqual(r['visual_holds']['before_first_line_s'], 1.0)
        # through the G02 still path: the pre-hold is silent of dialogue, sample-exact, and reproducible
        spec = {**copy.deepcopy(self.s023), 'shot_id': 'TEST-G09', 'dialogue_slots': self.two['dialogue_slots'],
                'mapped_audio': []}
        _png(self.tmp / 'f.png', 480, 270, (120, 160, 200))
        frame = {'asset_id': 'F', 'classification': 'SHOT_FRAME/BASE_FRAME', 'registry_status': 'APPROVED',
                 'shot_id': 'TEST-G09', 'path': str(self.tmp / 'f.png'), 'expected_sha256': sha256_file(self.tmp / 'f.png')}
        t = {**timing, 'dialogue': [{**x, 'shot_id': 'TEST-G09'} for x in timing['dialogue']]}
        spec['frames'], spec['duration_seconds'] = 120, 5.0
        p1 = compose_still_shot(spec, frame, SMALL, self.inputs, t, self.tmp / 'r1')
        p2 = compose_still_shot(spec, frame, SMALL, self.inputs, t, self.tmp / 'r2')
        self.assertEqual(p1['dialogue_timing'], p2['dialogue_timing'])
        self.assertEqual(p1['outputs'], p2['outputs'])
        mix = media.load_audio(self.tmp / 'r1' / 'TEST-G09_STILL_MIX.wav', SR, 2)
        self.assertEqual(float(np.abs(mix[:SR]).max()), 0.0)                  # nothing before 1.000 s
        self.assertGreater(float(np.abs(mix[SR:SR + 2400]).max()), 0.01)

    def test_G07_deterministic_post_dialogue_hold(self):
        w = {'dialogue_window': {'post_hold_seconds': 1.0}}
        r, _, _ = self.govern(self.two, [0.5, 3.0], **w)                      # ends exactly at 4.000 s
        self.assertEqual((r['window']['end_s'], r['lines'][1]['end_sample']), (4.0, 192000))
        self.assertEqual(r['visual_holds']['after_last_line_s'], 1.0)
        self.assertEqual(self.code(lambda: self.govern(self.two, [0.5, 3.0 + 1 / SR], **w)), 'DIALOGUE_OUTSIDE_WINDOW')
        hold = {**self.s027, 'protected_participation_hold': True}
        t = {'dialogue': [{**self.track(self.s027, 0, 'DLG-M', 0.5)}]}
        self.assertEqual(self.code(lambda: govern_dialogue_timing(hold, resolve_dialogue(hold, self.inputs, t),
                                                                  self.inputs, t, SMALL)), 'DIALOGUE_IN_PROTECTED_HOLD')

    def test_G08_exact_boundary_dialogue_valid(self):
        r, _, _ = self.govern(self.two, [0.0, 4.0])                           # starts at 0.000, ends at 5.000
        self.assertEqual((r['lines'][0]['start_sample'], r['lines'][1]['end_sample']), (0, 240000))
        self.assertEqual(r['visual_holds'], {'before_first_line_s': 0.0, 'after_last_line_s': 0.0})
        self.assertEqual(self.code(lambda: self.govern(self.two, [0.0, 4.0 + 1 / SR])), 'DIALOGUE_OVERRUNS_SHOT')
        r, _, _ = self.govern(self.two, [1.0, 3.0], dialogue_window={'pre_hold_seconds': 1.0, 'post_hold_seconds': 1.0})
        self.assertEqual((r['lines'][0]['start_s'], r['lines'][1]['end_s']), (1.0, 4.0))

    def test_G09_no_dialogue_shot_backward_compatible(self):
        spec = {**copy.deepcopy(self.s023), 'shot_id': 'TEST-S023', 'dialogue_slots': []}
        self.assertEqual(govern_dialogue_timing(spec, [], self.inputs, {}, SMALL)['lines'], [])
        _png(self.tmp / 'f.png', 480, 270, (120, 160, 200))
        _wav(self.tmp / 'amb.wav', 2.0, 0, 0.003)
        frame = {'asset_id': 'F', 'classification': 'SHOT_FRAME/BASE_FRAME', 'registry_status': 'APPROVED',
                 'shot_id': 'TEST-S023', 'path': str(self.tmp / 'f.png'), 'expected_sha256': sha256_file(self.tmp / 'f.png')}
        p = compose_still_shot(spec, frame, SMALL, {'AMB-BATHROOM-QUIET-v01': self.tmp / 'amb.wav'}, {}, self.tmp / 'o')
        self.assertEqual(p['qc']['automatic_result'], 'PASS')
        self.assertEqual((p['dialogue_timing']['lines'], p['dialogue_timing']['overlaps']), ([], []))
        self.assertNotIn('visual_holds', p['dialogue_timing'])
        self.assertEqual([c['kind'] for c in p['audio_cues']], ['BED'])

    def test_G10_s027_unchanged(self):
        self.assertEqual([(s['speaker'], s['text']) for s in self.s027['dialogue_slots']], [('Mikko', S027_TEXT)])
        timing = {'dialogue': [self.track(self.s027, 0, 'DLG-M', 0.5)]}          # the approved S027 timing
        dlg = resolve_dialogue(self.s027, self.inputs, timing)
        before = copy.deepcopy(dlg)
        r = govern_dialogue_timing(self.s027, dlg, self.inputs, timing, SMALL)
        self.assertEqual(dlg, before)                                           # G09 never alters the tracks
        self.assertEqual((r['lines'][0]['start_s'], r['lines'][0]['end_s']), (0.5, 2.125))
        self.assertEqual(r['window'], {'start_s': 0.0, 'end_s': 5.0, 'pre_hold_seconds': 0.0, 'post_hold_seconds': 0.0})
        spec = {**self.s027, 'mapped_audio': [], 'named_sfx': [], 'event_audio': []}
        mix, cues, _ = mix_motion_audio(spec, self.inputs, timing, SMALL, dlg)
        clip = media.load_audio(self.inputs['DLG-M'], SR, 2)
        np.testing.assert_array_equal(mix[24000:24000 + len(clip)], clip)       # placed once, unaltered
        self.assertEqual(float(np.abs(mix[:24000]).max()), 0.0)
        self.assertEqual([(c['kind'], c['start_s'], c['end_s']) for c in cues], [('DIALOGUE', 0.5, 2.125)])


if __name__ == '__main__':
    unittest.main()
