"""AGENT-008 G03 tests: deterministic overlay placement on an approved shot frame.

Synthetic fixtures only (flat-colour PNG base frames, generated RGBA overlay PNGs). No network, no provider, no
production asset, no registry or storage access. Shot specs come from the committed read-only approved-state capture
(v2) and are relabelled TEST-*; their overlay identities are replaced by TEST-OVERLAY-* fixtures.
"""
import copy
import os
import socket
import subprocess
import unittest
from dataclasses import replace
from pathlib import Path
from unittest import mock

import numpy as np

from agent008 import media, overlay
from agent008.derive import decode_png_rgb
from agent008.episode import resolve_episode
from agent008.errors import FailClosed
from agent008.hashing import canonical_sha256, sha256_bytes, sha256_file
from agent008.inputs import load_hash_pins, load_snapshot
from agent008.overlay import CONTRACT_ID, place_overlays, precomposited_overlay_set
from agent008.still import compose_still_shot
from agent008.tests.test_batch0c import FIXTURE_V2, _no_network, _png, _Tmp
from agent008.tests.test_motion import PINS, SMALL, ComposeFixture, _wav
from agent008.motion.compose import compose_motion_shot

W, H = 480, 270
RED, BLUE, GREEN = (220, 20, 30), (20, 40, 230), (30, 200, 60)


def _rgba_png(path, w, h, box, colors):
    """Transparent w x h canvas with an opaque box (x, y, bw, bh); left half colors[0], right half colors[1]."""
    a = np.zeros((h, w, 4), np.uint8)
    x, y, bw, bh = box
    a[y:y + bh, x:x + bw, :3] = colors[0]
    a[y:y + bh, x + bw // 2:x + bw, :3] = colors[1]
    a[y:y + bh, x:x + bw, 3] = 255
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', f'{w}x{h}', '-i', '-',
                    '-frames:v', '1', '-pix_fmt', 'rgba', str(path)], input=a.tobytes(), check=True)


class _G03(_Tmp):
    @classmethod
    def setUpClass(cls):
        cls.episode = {r['shot_id']: r for r in resolve_episode(load_snapshot(FIXTURE_V2), load_hash_pins(PINS), SMALL)}

    def setUp(self):
        super().setUp()
        self.base = self.tmp / 'in' / 'base.png'
        self.base.parent.mkdir()
        _png(self.base, W, H, (200, 160, 120))
        self.ov_paths = {}
        for i, aid in enumerate(('TEST-OVERLAY-CHEEK', 'TEST-OVERLAY-MOUTH', 'TEST-OVERLAY-NOSE')):
            p = self.tmp / 'in' / f'{aid}.png'
            _rgba_png(p, 120, 90, (30 + i, 20, 40, 30), (RED, BLUE) if i != 2 else (GREEN, GREEN))
            self.ov_paths[aid] = p
        spec = copy.deepcopy(self.episode['S005']['spec'])          # three persistent smudges, still, protected hold
        assert len(spec['active_overlays']) == 3
        spec['active_overlays'] = [{**o, 'asset_id': aid, 'registry_row_id': f'test-{aid}', 'asset_type': 'OVERLAY_VFX',
                                    'asset_subtype': 'BERRY_SMUDGE_OVERLAY', 'status': 'APPROVED',
                                    'expected_sha256': sha256_file(self.ov_paths[aid])}
                                   for o, aid in zip(spec['active_overlays'], self.ov_paths)]
        self.spec = {**spec, 'shot_id': 'TEST-S005'}
        self.frame = {'asset_id': 'TEST-FRAME', 'registry_id': 'test-row', 'classification': 'SHOT_FRAME/BASE_FRAME',
                      'registry_status': 'APPROVED', 'shot_id': 'TEST-S005', 'path': str(self.base),
                      'expected_sha256': sha256_file(self.base)}
        self.placements = [
            self.pl('TEST-OVERLAY-CHEEK', 'FACE', 100, 80),
            self.pl('TEST-OVERLAY-MOUTH', 'FACE', 200, 150),
            self.pl('TEST-OVERLAY-NOSE', 'FACE', 300, 90),
            self.pl('TEST-OVERLAY-CHEEK', 'REFLECTION', 400, 200, mirror=True),
        ]

    def pl(self, aid, surface, x, y, width=40, mirror=False, **extra):
        return {'asset_id': aid, 'overlay_sha256': sha256_file(self.ov_paths[aid]), 'surface': surface,
                'anchor': 'CENTER', 'x': x, 'y': y, 'width_px': width, 'mirror': mirror, **extra}

    def record(self, placements=None, **over):
        rec = {'contract': CONTRACT_ID, 'record_id': 'TEST-G03-REC', 'shot_id': 'TEST-S005',
               'base_frame': {'asset_id': 'TEST-FRAME', 'sha256': sha256_file(self.base)}, 'frame_size': [W, H],
               'frame_range': [0, self.spec['frames'] - 1],
               'placements': self.placements if placements is None else placements, **over}
        return {'record': rec, 'approval_status': 'APPROVED', 'expected_sha256': canonical_sha256(rec)}

    def place(self, sub, placement=None, spec=None, frame=None, paths=None):
        return place_overlays(spec or self.spec, frame or self.frame, self.ov_paths if paths is None else paths,
                              placement or self.record(), self.tmp / sub)

    def out_rgb(self, sub, prov):
        return decode_png_rgb(self.tmp / sub / prov['output']['file'])

    def code(self, fn, *a, **k):
        with self.assertRaises(FailClosed) as e:
            fn(*a, **k)
        return e.exception.code


class G03Placement(_G03):
    """C-G01..G06: placement, position, scale, opacity, frame range, order."""

    def test_G01_valid_overlay_placement(self):
        p = self.place('a')
        self.assertEqual(p['status'], 'REVIEW')
        self.assertEqual(p['proposed_registry']['asset_subtype'], 'DERIVED_FRAME')
        self.assertFalse(p['proposed_registry']['registered'])
        self.assertFalse(p['human_approval']['approved'])
        self.assertEqual(len(p['placements']), 4)
        self.assertEqual(sorted({o['asset_id'] for o in p['overlays_composited']['overlays']}), sorted(self.ov_paths))
        self.assertEqual(p['overlays_composited']['frame_sha256'], p['output']['sha256'])
        self.assertEqual(p['output']['sha256'], sha256_file(self.tmp / 'a' / 'TEST-S005_G03_OVERLAY_FRAME_CANDIDATE.png'))
        self.assertEqual((p['output']['width'], p['output']['height']), (W, H))

    def test_G02_exact_pixel_position(self):
        pl = [self.pl('TEST-OVERLAY-NOSE', 'FACE', 101, 77, width=40)]   # trimmed nose fixture is 40x30 solid green
        spec = {**self.spec, 'active_overlays': [o for o in self.spec['active_overlays'] if o['asset_id'] == 'TEST-OVERLAY-NOSE']}
        p = self.place('a', self.record(pl), spec=spec, paths={'TEST-OVERLAY-NOSE': self.ov_paths['TEST-OVERLAY-NOSE']})
        out, base = self.out_rgb('a', p), decode_png_rgb(self.base)
        x0, y0 = 101 - 40 // 2, 77 - 30 // 2
        self.assertEqual(p['placements'][0]['visible_box'], [x0, y0, x0 + 40, y0 + 30])
        self.assertTrue((out[y0:y0 + 30, x0:x0 + 40] == GREEN).all())
        mask = np.ones((H, W), bool)
        mask[y0:y0 + 30, x0:x0 + 40] = False
        self.assertTrue(np.array_equal(out[mask], base[mask]))                 # nothing else touched

    def test_G03_exact_deterministic_scale(self):
        pl = [self.pl('TEST-OVERLAY-NOSE', 'FACE', 200, 100, width=20)]
        spec = {**self.spec, 'active_overlays': [o for o in self.spec['active_overlays'] if o['asset_id'] == 'TEST-OVERLAY-NOSE']}
        paths = {'TEST-OVERLAY-NOSE': self.ov_paths['TEST-OVERLAY-NOSE']}
        a = self.place('a', self.record(pl), spec=spec, paths=paths)
        b = self.place('b', self.record(pl), spec=spec, paths=paths)
        g = a['placements'][0]
        self.assertEqual((g['trimmed_size'], g['scaled_size']), ([40, 30], [20, 15]))   # aspect kept, rounded height
        self.assertEqual(g['visible_box'], [190, 93, 210, 108])
        expect = media.scale_rgba(media.load_rgba(self.ov_paths['TEST-OVERLAY-NOSE'])[20:50, 32:72], 20, 15)
        self.assertTrue(np.array_equal(self.out_rgb('a', a)[93:108, 190:210], expect[..., :3]))
        self.assertEqual(a['output']['sha256'], b['output']['sha256'])
        self.assertEqual(self.code(self.place, 'c', self.record([{**pl[0], 'width_px': 41}]), spec=spec, paths=paths),
                         'OVERLAY_SCALE_INVALID')                              # no upscale beyond the trimmed width

    def test_G04_opacity_is_full_only(self):
        p = self.place('a', self.record([{**pl, 'opacity': 1.0} for pl in self.placements]))
        out = self.out_rgb('a', p)
        x, y = p['placements'][0]['x'], p['placements'][0]['y']
        self.assertTrue(any(tuple(out[y, x]) == c for c in (RED, BLUE, GREEN)))   # opaque centre, no blend with base
        for bad in (0.5, 0.0, 0.999, '1', True):
            self.assertEqual(self.code(self.place, 'x', self.record([{**self.placements[0], 'opacity': bad}]
                                                                    + self.placements[1:])), 'OVERLAY_OPACITY_INVALID')

    def test_G05_frame_range_enforced(self):
        n = self.spec['frames']
        for fr in ([0, n - 2], [1, n - 1], [0, n], [0], 'all'):
            self.assertEqual(self.code(self.place, 'x', self.record(frame_range=fr)), 'OVERLAY_FRAME_RANGE_INVALID')
        rec = self.record()
        del rec['record']['frame_range']
        rec['expected_sha256'] = canonical_sha256(rec['record'])
        self.assertEqual(self.code(self.place, 'x', rec), 'OVERLAY_TIMING_UNDECLARED')
        for key in ('remove_at_frame', 'start_frame', 'end_frame', 'frame_range'):
            bad = [{**self.placements[0], key: 10}] + self.placements[1:]
            self.assertEqual(self.code(self.place, 'x', self.record(bad)), 'OVERLAY_REMOVAL_UNSUPPORTED_G11')

    def test_G06_order_and_overlap(self):
        a = self.place('a')
        b = self.place('b', self.record(list(reversed(self.placements))))     # declaration order does not matter
        self.assertEqual(a['output']['rgb24_sha256'], b['output']['rgb24_sha256'])
        for key in ('z_order', 'z', 'layer'):
            bad = [{**self.placements[0], key: 1}] + self.placements[1:]
            self.assertEqual(self.code(self.place, 'x', self.record(bad)), 'OVERLAY_Z_ORDER_UNSUPPORTED')
        overlap = self.placements[:1] + [self.pl('TEST-OVERLAY-MOUTH', 'FACE', 110, 85)] + self.placements[2:]
        self.assertEqual(self.code(self.place, 'x', self.record(overlap)), 'OVERLAY_OVERLAP_UNDECLARED')

    def test_G06b_mirror_and_rotation(self):
        p = self.place('a')
        out = self.out_rgb('a', p)
        face = next(g for g in p['placements'] if g['surface'] == 'FACE' and g['asset_id'] == 'TEST-OVERLAY-CHEEK')
        refl = next(g for g in p['placements'] if g['surface'] == 'REFLECTION')
        fx0, fy0, fx1, _ = face['visible_box']
        rx0, ry0, rx1, _ = refl['visible_box']
        self.assertEqual((tuple(out[fy0 + 2, fx0 + 2]), tuple(out[fy0 + 2, fx1 - 3])), (RED, BLUE))
        self.assertEqual((tuple(out[ry0 + 2, rx0 + 2]), tuple(out[ry0 + 2, rx1 - 3])), (BLUE, RED))   # mirror reversed
        for surface, mirror in (('FACE', True), ('REFLECTION', False)):
            bad = [self.pl('TEST-OVERLAY-CHEEK', surface, 100, 80, mirror=mirror)] + self.placements[1:3]
            self.assertEqual(self.code(self.place, 'x', self.record(bad)), 'OVERLAY_MIRROR_RULE')
        rot = [{**g, 'rotation_deg': 90} for g in self.placements[:3]]
        r1, r2 = self.place('r1', self.record(rot)), self.place('r2', self.record(rot))
        self.assertEqual(r1['output']['sha256'], r2['output']['sha256'])
        g = r1['placements'][0]
        self.assertGreater(g['visible_box'][3] - g['visible_box'][1], g['visible_box'][2] - g['visible_box'][0])
        for bad in (float('nan'), 181, '5', True):
            self.assertEqual(self.code(self.place, 'x', self.record([{**self.placements[0], 'rotation_deg': bad}]
                                                                    + self.placements[1:])), 'OVERLAY_ROTATION_INVALID')


class G03FailClosed(_G03):
    """C-G07..G14: hashes, approval, presence, coordinates, scale, opacity, anchor, immutability."""

    def test_G07_sha_mismatch_rejected(self):
        spec = copy.deepcopy(self.spec)
        spec['active_overlays'][0]['expected_sha256'] = 'a' * 64
        self.assertEqual(self.code(self.place, 'x', spec=spec), 'HASH_MISMATCH')
        bad = [{**self.placements[0], 'overlay_sha256': 'b' * 64}] + self.placements[1:]
        self.assertEqual(self.code(self.place, 'x', self.record(bad)), 'OVERLAY_SHA_MISMATCH')
        self.assertEqual(self.code(self.place, 'x', frame={**self.frame, 'expected_sha256': 'c' * 64}), 'HASH_MISMATCH')
        rec = self.record()
        rec['record']['placements'][0]['x'] += 1                              # edited after approval
        self.assertEqual(self.code(self.place, 'x', rec), 'PLACEMENT_RECORD_HASH_MISMATCH')
        other = self.record(base_frame={'asset_id': 'TEST-FRAME', 'sha256': 'd' * 64})
        self.assertEqual(self.code(self.place, 'x', other), 'PLACEMENT_RECORD_BASE_FRAME_MISMATCH')
        self.assertFalse((self.tmp / 'x').exists())

    def test_G08_unapproved_asset_rejected(self):
        spec = copy.deepcopy(self.spec)
        spec['active_overlays'][1]['status'] = 'REVIEW'
        self.assertEqual(self.code(self.place, 'x', spec=spec), 'OVERLAY_ASSET_NOT_APPROVED')
        spec = copy.deepcopy(self.spec)
        spec['active_overlays'][1]['asset_type'] = 'PROP'
        self.assertEqual(self.code(self.place, 'x', spec=spec), 'OVERLAY_ASSET_WRONG_TYPE')
        self.assertEqual(self.code(self.place, 'x', frame={**self.frame, 'registry_status': 'REVIEW'}),
                         'OVERLAY_SOURCE_NOT_APPROVED')
        self.assertEqual(self.code(self.place, 'x', frame={**self.frame, 'classification': 'SHOT_MOTION/RAW_MOTION_SOURCE'}),
                         'OVERLAY_SOURCE_NOT_A_SHOT_FRAME')
        self.assertEqual(self.code(self.place, 'x', frame={**self.frame, 'shot_id': 'TEST-S006'}), 'SHOT_IDENTITY_MISMATCH')
        for status in ('REVIEW', None, 'PENDING'):
            self.assertEqual(self.code(self.place, 'x', {**self.record(), 'approval_status': status}),
                             'PLACEMENT_RECORD_NOT_APPROVED')
        self.assertEqual(self.code(self.place, 'x', {'approval_status': 'APPROVED'}), 'PLACEMENT_RECORD_MISSING')

    def test_G09_missing_overlay_rejected(self):
        paths = {k: v for k, v in self.ov_paths.items() if k != 'TEST-OVERLAY-MOUTH'}
        self.assertEqual(self.code(self.place, 'x', paths=paths), 'OVERLAY_ASSET_MISSING')
        os.remove(self.ov_paths['TEST-OVERLAY-NOSE'])
        self.assertEqual(self.code(self.place, 'x'), 'ASSET_FILE_MISSING')

    def test_G09b_active_overlay_without_placement(self):
        self.assertEqual(self.code(self.place, 'x', self.record(self.placements[:2])), 'OVERLAY_PLACEMENT_MISSING')
        self.assertEqual(self.code(self.place, 'x', self.record([])), 'PLACEMENT_RECORD_EMPTY')

    def test_G10_invalid_coordinate_rejected(self):
        for x, y in ((100.0, 80), (100, '80'), (-1, 80), (W, 80), (100, H), (True, 80)):
            bad = [{**self.placements[0], 'x': x, 'y': y}] + self.placements[1:]
            self.assertEqual(self.code(self.place, 'x', self.record(bad)), 'OVERLAY_COORDINATE_INVALID', (x, y))
        edge = [{**self.placements[0], 'x': 5, 'y': 80}] + self.placements[1:]  # anchor inside, overlay crosses edge
        self.assertEqual(self.code(self.place, 'x', self.record(edge)), 'OVERLAY_OUT_OF_BOUNDS')
        self.assertEqual(self.code(self.place, 'x', self.record(frame_size=[W, H + 1])), 'PLACEMENT_FRAME_SIZE_MISMATCH')

    def test_G11_invalid_scale_rejected(self):
        for w in (0, 1, -4, 20.0, '20', True, None, 41):
            bad = [{**self.placements[0], 'width_px': w}] + self.placements[1:]
            self.assertEqual(self.code(self.place, 'x', self.record(bad)), 'OVERLAY_SCALE_INVALID', w)

    def test_G12_invalid_opacity_rejected(self):
        for op in (-0.1, 0.5, 1.5, None, '1.0'):
            bad = [{**self.placements[0], 'opacity': op}] + self.placements[1:]
            self.assertEqual(self.code(self.place, 'x', self.record(bad)), 'OVERLAY_OPACITY_INVALID', op)

    def test_G13_unsupported_anchor_surface_and_fields(self):
        for a in ('TOP_LEFT', 'center', None, 'NOSE_TIP'):
            bad = [{**self.placements[0], 'anchor': a}] + self.placements[1:]
            self.assertEqual(self.code(self.place, 'x', self.record(bad)), 'OVERLAY_ANCHOR_UNSUPPORTED', a)
        bad = [{**self.placements[0], 'surface': 'MIRROR_FRAME'}] + self.placements[1:]
        self.assertEqual(self.code(self.place, 'x', self.record(bad)), 'OVERLAY_SURFACE_UNSUPPORTED')
        bad = [{**self.placements[0], 'blend_mode': 'multiply'}] + self.placements[1:]
        self.assertEqual(self.code(self.place, 'x', self.record(bad)), 'PLACEMENT_FIELD_UNSUPPORTED')
        bad = [{k: v for k, v in self.placements[0].items() if k != 'mirror'}] + self.placements[1:]
        self.assertEqual(self.code(self.place, 'x', self.record(bad)), 'PLACEMENT_FIELD_MISSING')
        self.assertEqual(self.code(self.place, 'x', self.record(clip_permitted=True)), 'PLACEMENT_FIELD_UNSUPPORTED')
        self.assertEqual(self.code(self.place, 'x', self.record(contract='OTHER')), 'PLACEMENT_CONTRACT_UNKNOWN')
        self.assertEqual(self.code(self.place, 'x', self.record(shot_id='TEST-S006')), 'SHOT_IDENTITY_MISMATCH')

    def test_G14_source_immutability_and_no_overwrite(self):
        files = [self.base, *self.ov_paths.values()]
        before = [(sha256_file(f), os.stat(f).st_mtime_ns) for f in files]
        self.place('a')
        self.assertEqual(before, [(sha256_file(f), os.stat(f).st_mtime_ns) for f in files])
        self.assertEqual(self.code(self.place, 'a'), 'OUTPUT_EXISTS')
        inplace = self.tmp / 'c' / 'TEST-S005_G03_OVERLAY_FRAME_CANDIDATE.png'   # base frame at the output name
        inplace.parent.mkdir()
        inplace.write_bytes(self.base.read_bytes())
        self.assertEqual(self.code(self.place, 'c', frame={**self.frame, 'path': str(inplace)}), 'OUTPUT_EXISTS')
        self.assertEqual(sha256_file(inplace), self.frame['expected_sha256'])
        self.assertEqual(self.code(self.place, 'x', frame={**self.frame, 'overlays_composited': {'overlays': [1]}}),
                         'OVERLAY_ALREADY_COMPOSITED')


class G03DeterminismAndScope(_G03):
    """C-G15..G17: two-run determinism, no unexpected overlays, downstream integration."""

    def test_G15_two_run_determinism(self):
        a, b = self.place('a'), self.place('b')
        self.assertEqual(sha256_file(self.tmp / 'a' / a['output']['file']), sha256_file(self.tmp / 'b' / b['output']['file']))
        self.assertEqual(a['output'], b['output'])
        self.assertEqual(a['deterministic_core_sha256'], b['deterministic_core_sha256'])
        self.assertEqual((self.tmp / 'a' / 'TEST-S005_G03_OVERLAY_PROVENANCE.json').read_text().replace('/a/', '/'),
                         (self.tmp / 'b' / 'TEST-S005_G03_OVERLAY_PROVENANCE.json').read_text().replace('/b/', '/'))

    def test_G16_no_unexpected_overlays(self):
        p = self.place('a')
        out, base = self.out_rgb('a', p), decode_png_rgb(self.base)
        mask = np.ones((H, W), bool)
        for g in p['placements']:
            x0, y0, x1, y1 = g['visible_box']
            mask[y0:y1, x0:x1] = False
        self.assertTrue(np.array_equal(out[mask], base[mask]))
        self.assertEqual(p['output']['changed_pixels_outside_overlays'], 0)
        extra = dict(self.ov_paths, **{'TEST-OVERLAY-EXTRA': self.ov_paths['TEST-OVERLAY-NOSE']})
        self.assertEqual(self.code(self.place, 'x', paths=extra), 'OVERLAY_NOT_IN_SHOT_CONTRACT')
        spec = copy.deepcopy(self.spec)
        spec['active_overlays'] = spec['active_overlays'][:2]                   # nose not active in this shot
        paths = {k: v for k, v in self.ov_paths.items() if k != 'TEST-OVERLAY-NOSE'}
        self.assertEqual(self.code(self.place, 'x', spec=spec, paths=paths), 'OVERLAY_NOT_IN_SHOT_CONTRACT')
        dup = self.placements + [self.pl('TEST-OVERLAY-NOSE', 'FACE', 420, 60)]
        self.assertEqual(self.code(self.place, 'x', self.record(dup)), 'OVERLAY_DUPLICATE_PLACEMENT')
        spec = copy.deepcopy(self.spec)
        spec['active_overlays'].append(copy.deepcopy(spec['active_overlays'][0]))
        self.assertEqual(self.code(self.place, 'x', spec=spec), 'OVERLAY_DUPLICATE_IDENTITY')
        clean = {**self.spec, 'active_overlays': []}                            # e.g. S025 CLEAN REVEAL
        self.assertEqual(self.code(self.place, 'x', spec=clean, paths={}), 'OVERLAY_NONE_REQUIRED')

    def test_G17_no_provider_or_network(self):
        with mock.patch.object(socket, 'socket', _no_network), mock.patch.object(socket, 'create_connection', _no_network):
            p = self.place('a')
        self.assertEqual(p['safety'], {'provider_calls': 0, 'source_mutated': False, 'auto_approved': False,
                                       'registered': False})
        text = Path(overlay.__file__).read_text()
        for mod in ('higgsfield', 'provider', 'http', 'urllib', 'requests', 'source_upload'):
            self.assertNotIn(f'import {mod}', text)
            self.assertNotIn(f'.{mod} import', text)


class G03FeedsStillPath(_G03):
    """C-G18..G19: an approved G03 frame is the only way a shot with overlays enters the G02 still path."""

    def setUp(self):
        super().setUp()
        _wav(self.tmp / 'amb.wav', 2.0, 0, 0.003)
        self.audio = {'AMB-BATHROOM-QUIET-v01': self.tmp / 'amb.wav'}
        self.g03 = self.place('g03')
        png = self.tmp / 'g03' / self.g03['output']['file']
        self.g03_frame = {**self.frame, 'asset_id': 'TEST-G03-FRAME', 'classification': 'SHOT_FRAME/DERIVED_FRAME',
                          'path': str(png), 'expected_sha256': self.g03['output']['sha256'],
                          'overlays_composited': self.g03['overlays_composited']}

    def still(self, sub, frame, spec=None):
        return compose_still_shot(spec or self.spec, frame, SMALL, self.audio, {}, self.tmp / sub)

    def test_G18_g03_frame_feeds_still_path(self):
        a, b = self.still('a', self.g03_frame), self.still('b', self.g03_frame)
        self.assertEqual(a['qc']['automatic_result'], 'PASS', a['qc']['issues'])
        self.assertEqual(a['qc']['overlays_precomposited'], 3)
        self.assertEqual(a['source_frame']['overlays_composited'], self.g03['overlays_composited'])
        self.assertEqual(a['outputs'], b['outputs'])                           # two-run determinism downstream
        self.assertEqual(a['qc']['output_frames'], self.spec['frames'])

    def test_G19_still_path_rejects_unmatched_frames(self):
        self.assertEqual(self.code(self.still, 'x', self.frame), 'STILL_OVERLAYS_NEED_G03_ANCHORS')
        missing_one = copy.deepcopy(self.g03_frame)
        missing_one['overlays_composited']['overlays'] = [o for o in missing_one['overlays_composited']['overlays']
                                                          if o['asset_id'] != 'TEST-OVERLAY-NOSE']
        self.assertEqual(self.code(self.still, 'x', missing_one), 'OVERLAY_PRECOMPOSITE_MISMATCH')
        self.assertEqual(self.code(self.still, 'x', {**self.g03_frame, 'classification': 'SHOT_FRAME/BASE_FRAME'}),
                         'OVERLAY_PRECOMPOSITE_NOT_DERIVED_FRAME')
        other = {**self.g03_frame, 'expected_sha256': self.frame['expected_sha256'], 'path': str(self.base)}
        self.assertEqual(self.code(self.still, 'x', other), 'OVERLAY_PRECOMPOSITE_FRAME_MISMATCH')
        no_ov = {**self.spec, 'active_overlays': []}
        self.assertEqual(self.code(self.still, 'x', self.g03_frame, spec=no_ov), 'OVERLAY_PRECOMPOSITE_MISMATCH')
        wrong_sha = copy.deepcopy(self.g03_frame)
        wrong_sha['overlays_composited']['overlays'][0]['sha256'] = 'e' * 64
        self.assertEqual(self.code(self.still, 'x', wrong_sha), 'OVERLAY_PRECOMPOSITE_MISMATCH')


class G03MotionBaseFrame(ComposeFixture):
    """C-G20: persistent overlays pre-composited into an approved motion base frame need no tracking."""

    def test_G20_precomposited_motion_base_frame(self):
        ov = [{'asset_id': 'TEST-OVERLAY-NOSE', 'expected_sha256': 'f' * 64, 'asset_type': 'OVERLAY_VFX', 'status': 'APPROVED'}]
        spec = {**self.spec_shot, 'active_overlays': ov}
        comp = {'shot_id': 'S027', 'frame_sha256': self.req.source_frame_sha256,
                'overlays': [{'asset_id': 'TEST-OVERLAY-NOSE', 'sha256': 'f' * 64, 'surface': 'FACE'}]}
        run = lambda sub, **k: compose_motion_shot(self.result, self.req, k.pop('spec', spec), SMALL, self.assets,
                                                   self.timing, self.tmp / sub, **k)
        with self.assertRaises(FailClosed) as e:
            run('x')
        self.assertEqual(e.exception.code, 'MOTION_TREATMENTS_NEED_TRACKING_V02')
        with self.assertRaises(FailClosed) as e:
            run('x', overlays_composited={**comp, 'frame_sha256': 'a' * 64})
        self.assertEqual(e.exception.code, 'OVERLAY_PRECOMPOSITE_FRAME_MISMATCH')
        with self.assertRaises(FailClosed) as e:
            run('x', spec={**spec, 'treatments': [{'treatment_id': 'TREATMENT-EP005-MIRROR-REFLECTION-v01'}]},
                overlays_composited=comp)
        self.assertEqual(e.exception.code, 'MOTION_TREATMENTS_NEED_TRACKING_V02')    # treatments remain G08
        p = run('ok', overlays_composited=comp)
        self.assertEqual(p['qc']['automatic_result'], 'PASS')
        self.assertEqual(p['qc']['overlays_precomposited_in_base_frame'], 1)
        self.assertEqual(p['overlays_composited_in_base_frame'], comp)
        self.assertEqual(precomposited_overlay_set(spec, comp, self.req.source_frame_sha256), ['TEST-OVERLAY-NOSE'])


if __name__ == '__main__':
    unittest.main()
