"""AGENT008_BATCH_DRIVER_v0.1 + G04 certificate chain tests.

Synthetic fixtures only: shot specs from the committed read-only approved-state capture (v2), relabelled TEST-* (plus the
real ids S018/S024 only where the engineering-blocker tables are under test); generated PNG frames, RGBA overlays,
testsrc2 videos and tones. No network, provider, production asset, registry or storage access.
"""
import copy
import os
import socket
import unittest
from pathlib import Path
from unittest import mock

from agent008 import batch as B
from agent008.episode import resolve_episode
from agent008.errors import FailClosed
from agent008.g04chain import derive_certified_frame
from agent008.g08 import REFL, apply_reflection, motion_gate
from agent008.hashing import canonical_sha256, sha256_file
from agent008.inputs import load_hash_pins, load_snapshot
from agent008.overlay import CONTRACT_ID as G03, place_overlays
from agent008.still import compose_still_shot
from agent008.tests.test_batch0c import FIXTURE_V2, _no_network, _png, _Tmp, _video
from agent008.tests.test_g03 import GREEN, _rgba_png
from agent008.tests.test_motion import PINS, SMALL, _wav

OV = ('TEST-OVERLAY-CHEEK', 'TEST-OVERLAY-MOUTH', 'TEST-OVERLAY-NOSE')


class _Batch(_Tmp):
    @classmethod
    def setUpClass(cls):
        cls.episode = {r['shot_id']: r for r in resolve_episode(load_snapshot(FIXTURE_V2), load_hash_pins(PINS), SMALL)}

    def setUp(self):
        super().setUp()
        (self.tmp / 'in').mkdir()
        self.paths = {}
        for i, aid in enumerate(OV):
            p = self.tmp / 'in' / f'{aid}.png'
            _rgba_png(p, 120, 90, (30 + i, 20, 40, 30), (GREEN, GREEN))
            self.paths[aid] = p
        _wav(self.tmp / 'in' / 'amb.wav', 2.0, 0, 0.003)
        self.paths['AMB-BATHROOM-QUIET-v01'] = self.tmp / 'in' / 'amb.wav'
        self.base = self.tmp / 'in' / 'frame.png'
        _png(self.base, 480, 270, (200, 160, 120))
        self.specs = {
            'TEST-A': self.spec('S023', 'TEST-A', 0),          # still, no overlays, no dialogue
            'TEST-B': self.spec('S005', 'TEST-B', 3),          # still, 3 overlays (protected hold)
            'TEST-C': self.spec('S004', 'TEST-C', 3),          # still, glint, 2 dialogue lines, chime
            'TEST-M': self.spec('S026', 'TEST-M', 0),          # provider motion, 1 dialogue line
            'TEST-M7': self.spec('S007', 'TEST-M7', 3),        # provider motion, overlays + reflection
            'TEST-D': self.spec('S008', 'TEST-D', 3),          # still from TEST-M7 motion end (G04 chain)
            'TEST-X': self.spec('S019', 'TEST-X', 1),          # still from a crop of family FAM-9
            'TEST-G11': {'shot_id': 'TEST-G11', 'status': 'BLOCKED', 'spec': None},
            'S018': self.spec('S018', 'S018', 1, keep_id=True),
            'S024': self.spec('S024', 'S024', 0, keep_id=True),
        }
        self.families = {
            'TEST-A': {'family_id': 'FAM-1', 'kind': 'GENERATE', 'provider_motion': False},
            'TEST-B': {'family_id': 'FAM-1', 'kind': 'GENERATE', 'provider_motion': False},
            'TEST-C': {'family_id': 'FAM-3', 'kind': 'GENERATE', 'provider_motion': False},
            'TEST-M': {'family_id': 'FAM-11', 'kind': 'REUSE_APPROVED_ASSET', 'provider_motion': True,
                       'source': {'asset_id': 'TEST-APPROVED-FRAME', 'sha256': sha256_file(self.base)}},
            'TEST-M7': {'family_id': 'FAM-4', 'kind': 'GENERATE', 'provider_motion': True},
            'TEST-D': {'family_id': 'FAM-12', 'kind': 'DERIVE_MOTION_END', 'provider_motion': False,
                       'source': {'shot_id': 'TEST-M7'}},
            'TEST-X': {'family_id': 'FAM-15', 'kind': 'DERIVE_CROP', 'provider_motion': False, 'source': {'family_id': 'FAM-9'},
                       'crop': {'x': 120, 'y': 68, 'w': 240, 'h': 134}, 'scale': {'w': 480, 'h': 268}},
            'TEST-G11': {'family_id': 'FAM-14', 'kind': 'DERIVE_MOTION_END', 'provider_motion': True, 'source': {'shot_id': 'TEST-M7'}},
            'S018': {'family_id': 'FAM-15', 'kind': 'DERIVE_CROP', 'provider_motion': False, 'source': {'family_id': 'FAM-9'}},
            'S024': {'family_id': 'FAM-1', 'kind': 'GENERATE', 'provider_motion': False},
        }

    def spec(self, src, sid, n_ov, keep_id=False):
        s = copy.deepcopy(self.episode[src]['spec'])
        s['shot_id'] = sid
        s['active_overlays'] = [{'asset_id': a, 'registry_row_id': f'test-{a}', 'asset_type': 'OVERLAY_VFX',
                                 'asset_subtype': 'BERRY_SMUDGE_OVERLAY', 'status': 'APPROVED',
                                 'expected_sha256': sha256_file(self.paths[a])} for a in OV[:n_ov]]
        return {'shot_id': sid, 'status': 'SPEC', 'spec': s}

    def frame(self, status='APPROVED', **extra):
        return {'asset_id': 'TEST-BASE', 'sha256': sha256_file(self.base), 'status': status, 'path': str(self.base),
                'classification': 'SHOT_FRAME/BASE_FRAME', **extra}

    def g03_record(self, sid, status='APPROVED'):
        n = len(self.specs[sid]['spec']['active_overlays'])
        pl = [{'asset_id': a, 'overlay_sha256': sha256_file(self.paths[a]), 'surface': 'FACE', 'anchor': 'CENTER',
               'x': 80 + 120 * i, 'y': 90, 'width_px': 30, 'mirror': False} for i, a in enumerate(OV[:n])]
        rec = {'contract': G03, 'record_id': f'REC-{sid}', 'shot_id': sid,
               'base_frame': {'asset_id': 'TEST-BASE', 'sha256': sha256_file(self.base)}, 'frame_size': [480, 270],
               'frame_range': [0, self.specs[sid]['spec']['frames'] - 1], 'placements': pl}
        return {'record': rec, 'approval_status': status, 'status': status, 'expected_sha256': canonical_sha256(rec)}

    def batch(self, ids, mode='PLAN_ONLY'):
        return {'batch_id': 'TEST-BATCH', 'shot_ids': ids, 'mode': mode}

    def plan(self, ids, inventory, mode='PLAN_ONLY'):
        return B.plan_batch(self.batch(ids, mode), self.specs, self.families, inventory)

    def states(self, plan):
        return {s['SHOT_ID']: s['STATE'] for s in plan['shots']}

    def code(self, fn, *a, **k):
        with self.assertRaises(FailClosed) as e:
            fn(*a, **k)
        return e.exception.code


class BatchPlan(_Batch):
    def test_01_valid_multi_shot_plan(self):
        inv = {'TEST-A': {'frame': self.frame()}, 'TEST-B': {'frame': self.frame(), 'g03_record': self.g03_record('TEST-B')},
               '__assets__': {'TEST-APPROVED-FRAME': {'status': 'APPROVED', 'sha256': sha256_file(self.base)}}}
        p = self.plan(['TEST-A', 'TEST-B', 'TEST-C', 'TEST-M', 'TEST-G11'], inv)
        self.assertEqual(self.states(p), {'TEST-A': 'READY_FOR_LOCAL_RENDER', 'TEST-B': 'READY_FOR_LOCAL_RENDER',
                                          'TEST-C': 'WAITING_FOR_BASE_FRAME', 'TEST-M': 'WAITING_FOR_FRAME_APPROVAL',
                                          'TEST-G11': 'BLOCKED_ENGINEERING'})
        b = next(s for s in p['shots'] if s['SHOT_ID'] == 'TEST-B')
        for k in ('AUTHORITATIVE_SPEC', 'PRODUCTION_MODE', 'BASE_FRAME_REQUIREMENT', 'G03_REQUIREMENT', 'G08_REQUIREMENT',
                  'G06_REQUIREMENT', 'G07_REQUIREMENT', 'G11_REQUIREMENT', 'DIALOGUE_REQUIREMENTS', 'AUDIO_REQUIREMENTS',
                  'PROVIDER_MOTION_REQUIRED', 'UPSTREAM_CONTINUITY_DEPENDENCIES', 'CURRENT_BLOCKERS',
                  'NEXT_REQUIRED_AUTOMATED_STAGE', 'NEXT_REQUIRED_HUMAN_GATE'):
            self.assertIn(k, b)
        self.assertEqual((b['PRODUCTION_MODE'], b['G03_REQUIREMENT']['overlays']), ('G02_STILL', list(OV)))
        m = next(s for s in p['shots'] if s['SHOT_ID'] == 'TEST-M')
        self.assertEqual(m['CURRENT_BLOCKERS'], ['REUSE_BINDING_NOT_APPROVED:TEST-APPROVED-FRAME'])
        self.assertIn('DIALOGUE: Mikko: One little spot at a time!', m['OUTSTANDING'])

    def test_02_allowlist_enforcement(self):
        for ids in ([], ['ALL'], ['*'], ['TEST-A', 'TEST-A'], 'TEST-A', None, ['']):
            self.assertEqual(self.code(self.plan, ids, {}), 'BATCH_ALLOWLIST_INVALID', ids)
        for mode in ('PROVIDER_SUBMIT', 'PAID', None):
            self.assertEqual(self.code(self.plan, ['TEST-A'], {}, mode), 'BATCH_MODE_NOT_AUTHORISED', mode)
        p = self.plan(['TEST-A'], {'TEST-B': {'frame': self.frame()}})
        self.assertEqual([s['SHOT_ID'] for s in p['shots']], ['TEST-A'])            # other inventory is never touched
        self.assertEqual(self.code(B._require_allowed, p, 'TEST-B'), 'BATCH_SHOT_NOT_ALLOWED')
        self.assertEqual(self.states(self.plan(['TEST-NOPE'], {})), {'TEST-NOPE': 'FAILED'})

    def test_03_independent_per_shot_failure(self):
        bad = self.tmp / 'in' / 'tampered.png'
        bad.write_bytes(self.base.read_bytes() + b'x')
        inv = {'TEST-A': {'frame': self.frame(path=str(bad))}, 'TEST-B': {'frame': self.frame(), 'g03_record': self.g03_record('TEST-B')}}
        p = self.plan(['TEST-A', 'TEST-B'], inv)
        self.assertEqual(self.states(p), {'TEST-A': 'FAILED', 'TEST-B': 'READY_FOR_LOCAL_RENDER'})
        self.assertEqual(p['shots'][0]['CURRENT_BLOCKERS'], ['SHA_MISMATCH'])
        alone = self.plan(['TEST-B'], inv)
        self.assertEqual(alone['shots'][0], p['shots'][1])                         # B is identical with or without A
        weird = self.plan(['TEST-A'], {'TEST-A': {'frame': self.frame(status='MAYBE')}})
        self.assertEqual(weird['shots'][0]['CURRENT_BLOCKERS'], ['UNEXPECTED_PRODUCTION_STATE'])

    def test_04_missing_base_frame(self):
        p = self.plan(['TEST-A', 'TEST-B'], {'__families__': {'FAM-1': {'status': 'REVIEW'}}, 'TEST-B': {}})
        self.assertEqual(self.states(p), {'TEST-A': 'WAITING_FOR_FRAME_APPROVAL', 'TEST-B': 'WAITING_FOR_FRAME_APPROVAL'})
        p = self.plan(['TEST-A'], {})
        self.assertEqual((p['shots'][0]['STATE'], p['shots'][0]['CURRENT_BLOCKERS']),
                         ('WAITING_FOR_BASE_FRAME', ['FAMILY_FRAME_NOT_GENERATED:FAM-1']))
        self.assertIn('base-frame generation', p['shots'][0]['NEXT_REQUIRED_HUMAN_GATE'])
        self.assertEqual(self.states(self.plan(['TEST-A'], {'TEST-A': {'frame': self.frame(status='REVIEW')}})),
                         {'TEST-A': 'WAITING_FOR_FRAME_APPROVAL'})

    def test_05_missing_dialogue(self):
        inv = {'TEST-C': {'frame': self.frame(), 'g03_record': self.g03_record('TEST-C'), 'g08_record': {'status': 'APPROVED'},
                          'timing': {'status': 'APPROVED', 'named': {'SFX-LUMI-CLUE-CHIME': {'start_seconds': 0.5}}}}}
        self.assertEqual(self.states(self.plan(['TEST-C'], inv)), {'TEST-C': 'WAITING_FOR_DIALOGUE'})
        slots = self.specs['TEST-C']['spec']['dialogue_slots']
        inv['TEST-C']['dialogue'] = [{'speaker': d['speaker'], 'text': d['text'], 'status': 'REVIEW'} for d in slots]
        self.assertEqual(self.states(self.plan(['TEST-C'], inv)), {'TEST-C': 'WAITING_FOR_DIALOGUE_APPROVAL'})
        for c in inv['TEST-C']['dialogue']:
            c['status'] = 'APPROVED'
        self.assertEqual(self.states(self.plan(['TEST-C'], inv)), {'TEST-C': 'READY_FOR_LOCAL_RENDER'})
        del inv['TEST-C']['timing']
        self.assertEqual(self.states(self.plan(['TEST-C'], inv)), {'TEST-C': 'WAITING_FOR_AUDIO_TIMING'})

    def test_06_unresolved_g03(self):
        for rec in (None, self.g03_record('TEST-B', status='REVIEW')):
            inv = {'TEST-B': {'frame': self.frame(), **({'g03_record': rec} if rec else {})}}
            self.assertEqual(self.states(self.plan(['TEST-B'], inv)), {'TEST-B': 'WAITING_FOR_G03_RECORD'})

    def test_07_unresolved_g08(self):
        inv = {'TEST-C': {'frame': self.frame(), 'g03_record': self.g03_record('TEST-C')}}
        self.assertEqual(self.states(self.plan(['TEST-C'], inv)), {'TEST-C': 'WAITING_FOR_G08_RECORD'})
        inv['TEST-C']['g08_record'] = {'status': 'REVIEW'}
        self.assertEqual(self.states(self.plan(['TEST-C'], inv)), {'TEST-C': 'WAITING_FOR_G08_RECORD'})

    def test_08_provider_authorisation_gate(self):
        clip = [{'speaker': 'Mikko', 'text': 'One little spot at a time!', 'status': 'APPROVED'}]
        base = {'frame': self.frame(), 'dialogue': clip}
        cases = (({}, 'READY_FOR_PROVIDER_PREFLIGHT', []),
                 ({'preflight_sha256': 'a' * 64}, 'WAITING_FOR_PROVIDER_AUTHORISATION', ['PROVIDER_AUTHORISATION_MISSING']),
                 ({'preflight_sha256': 'a' * 64, 'authorisation': {'human_approved': True}}, 'WAITING_FOR_PROVIDER_AUTHORISATION',
                  ['SPEND_CEILING_MISSING']),
                 ({'preflight_sha256': 'a' * 64, 'authorisation': {'human_approved': True, 'spend_ceiling_usd': 3.5}},
                  'WAITING_FOR_PROVIDER_AUTHORISATION', ['PAID_MODE_NOT_AVAILABLE_IN_DRIVER_v0.1']),
                 ({'submitted': True}, 'WAITING_FOR_PROVIDER_OUTPUT', []),
                 ({'result': {'status': 'COMPLETED'}}, 'WAITING_FOR_RAW_MOTION_APPROVAL', []),
                 ({'result': {'status': 'APPROVED'}}, 'READY_FOR_ASSEMBLY', []))
        for motion, state, blockers in cases:
            s = self.plan(['TEST-M'], {'TEST-M': {**base, 'motion': motion}})['shots'][0]
            self.assertEqual((s['STATE'], s['CURRENT_BLOCKERS']), (state, blockers), motion)

    def test_09_upstream_continuity_blocker(self):
        s = self.plan(['TEST-D'], {})['shots'][0]
        self.assertEqual((s['STATE'], s['CURRENT_BLOCKERS']), ('WAITING_FOR_UPSTREAM', ['UPSTREAM_MOTION_NOT_APPROVED:TEST-M7']))
        self.assertEqual(s['UPSTREAM_CONTINUITY_DEPENDENCIES'], [{'shot_id': 'TEST-M7'}])
        specs = {**self.specs, 'TEST-M7': {'shot_id': 'TEST-M7', 'status': 'BLOCKED', 'spec': None}}
        s = B.plan_batch(self.batch(['TEST-D']), specs, self.families, {})['shots'][0]
        self.assertEqual((s['STATE'], s['CURRENT_BLOCKERS']), ('BLOCKED_ENGINEERING', ['UPSTREAM_CONTINUITY_BLOCKER:TEST-M7']))
        s = self.plan(['TEST-D'], {'TEST-M7': {'motion': {'result': {'status': 'APPROVED'}}}})['shots'][0]
        self.assertEqual((s['STATE'], s['CURRENT_BLOCKERS']), ('FAILED', ['UPSTREAM_CERTIFICATE_MISSING:TEST-M7']))
        s = self.plan(['TEST-X'], {})['shots'][0]
        self.assertEqual((s['STATE'], s['CURRENT_BLOCKERS']), ('WAITING_FOR_UPSTREAM', ['CROP_SOURCE_FAMILY_NOT_APPROVED:FAM-9']))
        self.assertEqual(self.states(self.plan(['TEST-X'], {'__families__': {'FAM-9': {'status': 'APPROVED'}}})),
                         {'TEST-X': 'READY_FOR_FRAME_DERIVATION'})

    def test_10_unsupported_engineering_blockers(self):
        p = self.plan(['TEST-G11', 'S018', 'S024'], {'S018': {'frame': self.frame()}, 'S024': {'frame': self.frame()}})
        got = {s['SHOT_ID']: (s['STATE'], s['CURRENT_BLOCKERS']) for s in p['shots']}
        self.assertEqual(got, {'TEST-G11': ('BLOCKED_ENGINEERING', ['G11_TRACKED_OVERLAY_REMOVAL']),
                               'S018': ('BLOCKED_ENGINEERING', ['G07_IN_SHOT_CUT']),
                               'S024': ('BLOCKED_ENGINEERING', ['G06_KEYFRAMED_CROP_SCALE'])})

    def test_11_completed_shot_skipped(self):
        inv = {'TEST-A': {'frame': self.frame(), 'final': {'status': 'APPROVED', 'sha256': 'f' * 64}}}
        calls = []
        plan, res = B.execute(self.batch(['TEST-A'], 'LOCAL_RENDER_ONLY'), self.specs, self.families, inv, self.tmp / 'w',
                              {'render': lambda *a: calls.append(a)})
        self.assertEqual((plan['shots'][0]['STATE'], calls, res['TEST-A']['executed']), ('COMPLETE_APPROVED', [], False))

    def test_12_approved_shot_never_reopened(self):
        inv = {'TEST-B': {'final': {'status': 'APPROVED'}, 'frame': self.frame(status='REVIEW'), 'g03_record': None},
               'TEST-M': {'final': {'status': 'APPROVED'}, 'motion': {'result': {'status': 'FAILED'}}}}
        p = self.plan(['TEST-B', 'TEST-M'], inv)
        self.assertEqual(self.states(p), {'TEST-B': 'COMPLETE_APPROVED', 'TEST-M': 'COMPLETE_APPROVED'})
        self.assertTrue(all(s['NEXT_REQUIRED_AUTOMATED_STAGE'] is None for s in p['shots']))
        for mode in B.MODES[1:]:
            _, res = B.execute(self.batch(['TEST-B', 'TEST-M'], mode), self.specs, self.families, inv, self.tmp / mode,
                               {k: (lambda *a: 1 / 0) for k in ('derive_frame', 'prepare', 'render', 'provider_preflight')})
            self.assertFalse(any(r['executed'] for r in res.values()))

    def test_13_plan_only_performs_no_writes(self):
        before = sorted((str(p), p.stat().st_mtime_ns) for p in self.tmp.rglob('*'))
        with mock.patch.object(socket, 'socket', _no_network), mock.patch.object(socket, 'create_connection', _no_network):
            plan, res = B.execute(self.batch(['TEST-A', 'TEST-B']), self.specs, self.families, {'TEST-A': {'frame': self.frame()}})
        self.assertEqual(res, {})
        self.assertEqual(before, sorted((str(p), p.stat().st_mtime_ns) for p in self.tmp.rglob('*')))
        self.assertEqual(self.code(B.execute, self.batch(['TEST-A']), self.specs, self.families, {}, self.tmp / 'w'),
                         'PLAN_ONLY_NO_WRITES')
        text = Path(B.__file__).read_text()
        for mod in ('higgsfield', 'provider', 'http', 'urllib', 'requests', 'source_upload', 'supabase'):
            self.assertNotIn(f'import {mod}', text)
            self.assertNotIn(f'.{mod} import', text)

    def test_15_no_automatic_retry(self):
        inv = {'TEST-A': {'frame': self.frame()}}
        n = []

        def boom(*a):
            n.append(1)
            raise FailClosed('QC_FAILED', 'synthetic')
        _, res = B.execute(self.batch(['TEST-A'], 'LOCAL_RENDER_ONLY'), self.specs, self.families, inv, self.tmp / 'w', {'render': boom})
        self.assertEqual((len(n), res['TEST-A']['attempts'], res['TEST-A']['failed']['code']), (1, 1, 'QC_FAILED'))
        s = self.plan(['TEST-M'], {'TEST-M': {'frame': self.frame(), 'dialogue': [{'speaker': 'Mikko', 'text':
                       'One little spot at a time!', 'status': 'APPROVED'}], 'motion': {'result': {'status': 'FAILED'}}}})['shots'][0]
        self.assertEqual((s['STATE'], s['CURRENT_BLOCKERS'], s['NEXT_REQUIRED_AUTOMATED_STAGE']),
                         ('FAILED', ['PROVIDER_FAILED_NO_RETRY'], None))
        s = self.plan(['TEST-A'], {'TEST-A': {'frame': self.frame(status='REJECTED')}})['shots'][0]
        self.assertEqual(s['CURRENT_BLOCKERS'], ['REJECTED_BY_HUMAN_NO_AUTOMATIC_REPLACEMENT'])

    def test_16_batch_manifest(self):
        inv = {'TEST-A': {'frame': self.frame()}, 'TEST-B': {'frame': self.frame(status='REVIEW')},
               'TEST-M': {'frame': self.frame(), 'dialogue': [{'speaker': 'Mikko', 'text': 'One little spot at a time!',
                                                             'status': 'APPROVED'}], 'motion': {'submitted': True}},
               'S024': {'final': {'status': 'APPROVED'}}}
        plan = self.plan(['TEST-A', 'TEST-B', 'TEST-M', 'TEST-G11', 'S024', 'TEST-NOPE'], inv)
        m = B.review_manifest(plan, {'TEST-A': {'executed': True, 'result': {'input_shas': {'base_frame': 'x'},
                                                                              'output_shas': {'review_mp4': 'y'},
                                                                              'qc_status': 'PASS'}}})
        self.assertEqual((m['SHOT_COUNT'], m['COMPLETE_COUNT'], m['BLOCKED_COUNT'], m['WAITING_HUMAN_COUNT'],
                          m['WAITING_PROVIDER_COUNT'], m['READY_AUTOMATED_COUNT'], m['FAILED_COUNT']), (6, 1, 1, 1, 1, 1, 1))
        a = m['shots'][0]
        self.assertEqual((a['SHOT_ID'], a['QC_STATUS'], a['OUTPUT_SHAS'], a['INPUT_SHAS']),
                         ('TEST-A', 'PASS', {'review_mp4': 'y'}, {'base_frame': 'x'}))
        for k in ('BATCH_ID', 'SHOT_COUNT', 'COMPLETE_COUNT', 'BLOCKED_COUNT', 'WAITING_HUMAN_COUNT', 'WAITING_PROVIDER_COUNT',
                  'FAILED_COUNT', 'manifest_sha256'):
            self.assertIn(k, m)
        for row in m['shots']:
            for k in ('SHOT_ID', 'STATE', 'INPUT_SHAS', 'OUTPUT_SHAS', 'QC_STATUS', 'HUMAN_GATE', 'PROVIDER_COST', 'BLOCKER'):
                self.assertIn(k, row)
        self.assertEqual(m, B.review_manifest(plan, {'TEST-A': {'executed': True, 'result': {'input_shas': {'base_frame': 'x'},
                                                                                            'output_shas': {'review_mp4': 'y'},
                                                                                            'qc_status': 'PASS'}}}))

    def test_23_deterministic_two_run_plan(self):
        inv = {'TEST-A': {'frame': self.frame()}, 'TEST-B': {'frame': self.frame(), 'g03_record': self.g03_record('TEST-B')}}
        ids = ['TEST-A', 'TEST-B', 'TEST-C', 'TEST-M', 'TEST-D', 'TEST-X', 'TEST-G11', 'S018', 'S024']
        a, b = self.plan(ids, inv), self.plan(ids, copy.deepcopy(inv))
        self.assertEqual(a, b)
        self.assertEqual(a['plan_sha256'], b['plan_sha256'])
        self.assertEqual(B.review_manifest(a)['manifest_sha256'], B.review_manifest(b)['manifest_sha256'])


class BatchExecute(_Batch):
    """Local modes on synthetic fixtures: render (G03 -> G02 x2), crop derivation, provider preflight (no submit)."""

    def runners(self):
        return B.local_runners(self.specs, self.families, self.paths, SMALL)

    def test_14_provider_preflight_never_submits(self):
        inv = {'TEST-M': {'frame': self.frame(), 'dialogue': [{'speaker': 'Mikko', 'text': 'One little spot at a time!',
                                                             'status': 'APPROVED'}],
                          'motion': {'prompt': 'Mikko lifts the cloth.', 'prompt_record': {'status': 'APPROVED'},
                                     'provider': 'higgsfield', 'model': 'bytedance/seedance-2.0/image-to-video',
                                     'duration': 5, 'resolution': '1080p'}}}
        with mock.patch.object(socket, 'socket', _no_network), mock.patch.object(socket, 'create_connection', _no_network):
            plan, res = B.execute(self.batch(['TEST-M'], 'PROVIDER_PREFLIGHT_ONLY'), self.specs, self.families, inv,
                                  self.tmp / 'w', self.runners())
        r = res['TEST-M']
        self.assertTrue(r['executed'] and 'failed' not in r, r)
        import json
        pkg = json.loads((self.tmp / 'w' / 'TEST-M' / 'TEST-M_PROVIDER_PREFLIGHT.json').read_text())
        self.assertEqual((pkg['status'], pkg['submitted'], pkg['attempt_policy']['max_generations'], pkg['attempt_policy']['retry']),
                         ('PREPARED_NOT_SUBMITTED', False, 1, False))
        self.assertEqual(pkg['request_body_sha256'], canonical_sha256(pkg['request_body']))
        self.assertEqual(r['result']['state_after'], 'WAITING_FOR_PROVIDER_AUTHORISATION')
        _, again = B.execute(self.batch(['TEST-M'], 'PROVIDER_PREFLIGHT_ONLY'), self.specs, self.families, inv, self.tmp / 'w',
                             self.runners())
        self.assertEqual(again['TEST-M']['failed']['code'], 'OUTPUT_EXISTS')                        # never overwrites
        inv['TEST-M']['motion']['prompt_record'] = {'status': 'REVIEW'}
        _, r2 = B.execute(self.batch(['TEST-M'], 'PROVIDER_PREFLIGHT_ONLY'), self.specs, self.families, inv, self.tmp / 'w2',
                          self.runners())
        self.assertEqual(r2['TEST-M']['failed']['code'], 'MOTION_PROMPT_NOT_APPROVED')

    def test_local_render_and_crop_derivation(self):
        inv = {'TEST-B': {'frame': self.frame(), 'g03_record': self.g03_record('TEST-B')},
               '__families__': {'FAM-9': {'asset_id': 'TEST-BASE', 'status': 'APPROVED', 'sha256': sha256_file(self.base),
                                          'path': str(self.base)}}}
        plan, res = B.execute(self.batch(['TEST-B', 'TEST-X'], 'LOCAL_RENDER_ONLY'), self.specs, self.families, inv,
                              self.tmp / 'w', self.runners())
        r = res['TEST-B']['result']
        self.assertEqual(r['qc_status'], 'PASS (two renders byte-identical)')
        self.assertEqual(sorted(r['output_shas']), ['mix_wav', 'review_mp4'])
        self.assertIn('g03_frame', r['input_shas'])
        self.assertFalse(res['TEST-X']['executed'])                     # derivation belongs to LOCAL_PREPARE_ONLY
        _, prep = B.execute(self.batch(['TEST-X'], 'LOCAL_PREPARE_ONLY'), self.specs, self.families, inv, self.tmp / 'p',
                            self.runners())
        self.assertEqual(prep['TEST-X']['result']['state_after'], 'WAITING_FOR_FRAME_APPROVAL')
        m = B.review_manifest(plan, res)
        self.assertEqual(m['shots'][0]['QC_STATUS'], 'PASS (two renders byte-identical)')


class G04CertificateChain(_Tmp):
    """C-17..22: G04 inherits G03/G08 certificates; stale / mismatched / undeclared rejected; no reapplication."""

    @classmethod
    def setUpClass(cls):
        cls.episode = {r['shot_id']: r for r in resolve_episode(load_snapshot(FIXTURE_V2), load_hash_pins(PINS), SMALL)}

    def setUp(self):
        super().setUp()
        (self.tmp / 'in').mkdir()
        self.raw = self.tmp / 'in' / 'raw.mp4'
        _video(self.raw, 30, size='480x270')
        self.ov = {}
        for i, aid in enumerate(OV):
            p = self.tmp / 'in' / f'{aid}.png'
            _rgba_png(p, 120, 90, (30 + i, 20, 40, 30), (GREEN, GREEN))
            self.ov[aid] = p
        self.source = {'asset_id': 'TEST-RAW-M7', 'registry_status': 'APPROVED', 'path': str(self.raw),
                       'expected_sha256': sha256_file(self.raw)}
        self.overlays = [{'asset_id': a, 'sha256': sha256_file(self.ov[a]), 'surface': 'FACE'} for a in OV]
        self.cert = {'motion_asset_id': 'TEST-RAW-M7', 'motion_sha256': sha256_file(self.raw), 'motion_source_frame_sha256': 'b' * 64,
                     'source_shot_id': 'TEST-M7', 'declared_frame_index': 29,
                     'overlays_composited': {'shot_id': 'TEST-M7', 'frame_sha256': 'b' * 64, 'overlays': self.overlays}}

    def spec(self, src, sid, refl=False):
        s = copy.deepcopy(self.episode[src]['spec'])
        s['shot_id'] = sid
        s['active_overlays'] = [{'asset_id': a, 'asset_type': 'OVERLAY_VFX', 'status': 'APPROVED',
                                 'expected_sha256': sha256_file(self.ov[a])} for a in OV]
        s['treatments'] = [{'treatment_id': REFL}] if refl else []
        return s

    def with_refl(self):
        c = copy.deepcopy(self.cert)
        c['treatments_composited'] = {'shot_id': 'TEST-M7', 'input_frame_sha256': 'a' * 64, 'frame_sha256': 'b' * 64,
                                      'record_sha256': 'c' * 64, 'treatments': [REFL], 'mode': 'COMPOSITE', 'reflected_overlays': []}
        c['overlays_composited']['frame_sha256'] = 'a' * 64                       # G03 frame -> G08 frame -> motion
        return c

    def derive(self, sub, cert=None, idx=29, spec=None, inherit=None):
        return derive_certified_frame(self.source, idx, spec or self.spec('S008', 'TEST-D'), self.tmp / sub,
                                      self.cert if cert is None else cert, inherit or {'overlays': list(OV), 'treatments': []})

    def code(self, fn, *a, **k):
        with self.assertRaises(FailClosed) as e:
            fn(*a, **k)
        return e.exception.code

    def test_17_inherits_g03_certificate(self):
        r = self.derive('a')
        for k in ('SOURCE_ASSET_ID', 'SOURCE_SHA', 'SOURCE_FRAME_INDEX', 'DERIVED_FRAME_SHA', 'G03_CERTIFICATES_INHERITED',
                  'G08_CERTIFICATES_INHERITED', 'CERTIFICATE_SOURCE_SHA', 'DERIVATION_METHOD'):
            self.assertIn(k, r)
        self.assertEqual((r['SOURCE_FRAME_INDEX'], r['G03_CERTIFICATES_INHERITED'], r['pixels_reapplied']),
                         (29, sorted(OV), {'g03': False, 'g08': False}))
        self.assertEqual(r['overlays_composited']['frame_sha256'], r['DERIVED_FRAME_SHA'])
        png = self.tmp / 'a' / 'TEST-D_DERIVED_FRAME_CANDIDATE.png'
        _wav(self.tmp / 'amb.wav', 2.0, 0, 0.003)
        frame = {'asset_id': 'TEST-D-FRAME', 'registry_id': 't', 'classification': 'SHOT_FRAME/DERIVED_FRAME',
                 'registry_status': 'APPROVED', 'shot_id': 'TEST-D', 'path': str(png), 'expected_sha256': r['DERIVED_FRAME_SHA'],
                 'overlays_composited': r['overlays_composited']}
        p = compose_still_shot(self.spec('S008', 'TEST-D'), frame, SMALL, {'AMB-BATHROOM-QUIET-v01': self.tmp / 'amb.wav'}, {},
                               self.tmp / 's')
        self.assertEqual((p['qc']['automatic_result'], p['qc']['overlays_precomposited']), ('PASS', 3))
        self.assertEqual(self.derive('b')['DERIVED_FRAME_SHA'], r['DERIVED_FRAME_SHA'])          # deterministic

    def test_18_inherits_g08_certificate(self):
        r = self.derive('a', self.with_refl(), spec=self.spec('S007', 'TEST-D2', refl=True),
                        inherit={'overlays': list(OV), 'treatments': [REFL]})
        self.assertEqual(r['G08_CERTIFICATES_INHERITED'], [REFL])
        tc = r['treatments_composited']
        self.assertEqual((tc['frame_sha256'], tc['input_frame_sha256'], tc['record_sha256']),
                         (r['DERIVED_FRAME_SHA'], r['DERIVED_FRAME_SHA'], 'c' * 64))
        bound = motion_gate(self.spec('S007', 'TEST-D2', refl=True), r['DERIVED_FRAME_SHA'], r['overlays_composited'], tc)
        self.assertEqual(bound, r['DERIVED_FRAME_SHA'])

    def test_19_rejects_stale_or_missing_certificate(self):
        self.assertEqual(self.code(self.derive, 'x', {**self.cert, 'motion_sha256': 'd' * 64}), 'CERTIFICATE_STALE')
        self.assertEqual(self.code(self.derive, 'x', {**self.cert, 'motion_asset_id': 'OTHER'}), 'CERTIFICATE_STALE')
        self.assertEqual(self.code(self.derive, 'x', {}), 'CERTIFICATE_MISSING')
        bare = {k: v for k, v in self.cert.items() if k != 'overlays_composited'}
        self.assertEqual(self.code(self.derive, 'x', bare), 'CERTIFICATE_MISSING')
        broken = copy.deepcopy(self.cert)
        broken['overlays_composited']['frame_sha256'] = 'e' * 64
        self.assertEqual(self.code(self.derive, 'x', broken), 'CERTIFICATE_CHAIN_INVALID')
        bad_t = self.with_refl()
        bad_t['treatments_composited']['frame_sha256'] = 'e' * 64
        self.assertEqual(self.code(self.derive, 'x', bad_t, spec=self.spec('S007', 'TEST-D2', refl=True),
                                   inherit={'overlays': list(OV), 'treatments': [REFL]}), 'CERTIFICATE_CHAIN_INVALID')
        self.assertFalse((self.tmp / 'x').exists())

    def test_20_rejects_mismatched_frame_index(self):
        self.assertEqual(self.code(self.derive, 'x', idx=28), 'CERTIFICATE_FRAME_INDEX_MISMATCH')
        self.assertEqual(self.code(self.derive, 'x', {**self.cert, 'declared_frame_index': None}), 'CERTIFICATE_FRAME_INDEX_UNDECLARED')
        self.assertEqual(self.code(self.derive, 'x', {**self.cert, 'frame_rgb_sha256': '0' * 64}), 'DERIVED_FRAME_MISMATCH')
        self.assertEqual(self.code(self.derive, 'y', inherit={'overlays': list(OV[:2]), 'treatments': []}), 'CERTIFICATE_SET_MISMATCH')
        two = self.spec('S008', 'TEST-D')
        two['active_overlays'] = two['active_overlays'][:2]
        self.assertEqual(self.code(self.derive, 'y', spec=two), 'CERTIFICATE_SET_MISMATCH')
        self.assertEqual(self.code(self.derive, 'y', self.with_refl(), inherit={'overlays': list(OV), 'treatments': [REFL]}),
                         'CERTIFICATE_SET_MISMATCH')                       # target shot does not assign the reflection

    def test_21_no_duplicate_g03_reapplication(self):
        r = self.derive('a')
        png = self.tmp / 'a' / 'TEST-D_DERIVED_FRAME_CANDIDATE.png'
        frame = {'asset_id': 'TEST-D-FRAME', 'registry_id': 't', 'classification': 'SHOT_FRAME/DERIVED_FRAME',
                 'registry_status': 'APPROVED', 'shot_id': 'TEST-D', 'path': str(png), 'expected_sha256': r['DERIVED_FRAME_SHA'],
                 'overlays_composited': r['overlays_composited']}
        self.assertEqual(self.code(place_overlays, self.spec('S008', 'TEST-D'), frame, self.ov,
                                   {'record': {}, 'approval_status': 'APPROVED', 'expected_sha256': 'x'}, self.tmp / 'g03'),
                         'OVERLAY_ALREADY_COMPOSITED')
        s = B.resolve_shot('TEST-D', {'TEST-D': {'status': 'SPEC', 'spec': self.spec('S008', 'TEST-D')}},
                           {'TEST-D': {'family_id': 'F12', 'kind': 'DERIVE_MOTION_END', 'source': {'shot_id': 'TEST-M7'}}},
                           {'TEST-D': {'frame': {'status': 'APPROVED', 'sha256': r['DERIVED_FRAME_SHA'],
                                                 'overlays_composited': r['overlays_composited']}}})
        self.assertFalse(s['G03_REQUIREMENT']['record_required'])
        self.assertTrue(s['G03_REQUIREMENT']['satisfied_by_inherited_certificate'])

    def test_22_no_duplicate_g08_reapplication(self):
        sp = self.spec('S007', 'TEST-D2', refl=True)
        r = self.derive('a', self.with_refl(), spec=sp, inherit={'overlays': list(OV), 'treatments': [REFL]})
        png = self.tmp / 'a' / 'TEST-D2_DERIVED_FRAME_CANDIDATE.png'
        frame = {'asset_id': 'TEST-D2-FRAME', 'registry_id': 't', 'classification': 'SHOT_FRAME/DERIVED_FRAME',
                 'registry_status': 'APPROVED', 'shot_id': 'TEST-D2', 'path': str(png), 'expected_sha256': r['DERIVED_FRAME_SHA'],
                 'overlays_composited': r['overlays_composited'], 'treatments_composited': r['treatments_composited']}
        self.assertEqual(self.code(apply_reflection, sp, frame, {'approval_status': 'APPROVED'}, self.tmp / 'g08'),
                         'TREATMENT_DUPLICATE_INVOCATION')


if __name__ == '__main__':
    unittest.main()
