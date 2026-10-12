"""AGENT-008 G08 tests: governed visual treatments (mirror reflection, mirror glint, completion pop).

Synthetic fixtures only (generated base frames with a 'face' region and a 'mirror glass' ellipse, generated RGBA overlays,
synthetic tones). No network, no provider, no production asset, no registry or storage access. Shot specs come from the
committed read-only approved-state capture (v2), relabelled TEST-*; the manifest-governed sync and glint-target tables are
patched to the TEST-* ids.
"""
import copy
import os
import socket
import subprocess
import unittest
from pathlib import Path
from unittest import mock

import numpy as np

from agent008 import g08, media
from agent008.derive import decode_png_rgb
from agent008.episode import resolve_episode
from agent008.errors import FailClosed
from agent008.g08 import CONTRACT_ID, GLINT, POP, REFL, apply_reflection, plan_timed, render_frame
from agent008.hashing import canonical_sha256, sha256_file
from agent008.inputs import load_hash_pins, load_snapshot
from agent008.overlay import CONTRACT_ID as G03_CONTRACT, place_overlays
from agent008.motion.compose import compose_motion_shot
from agent008.still import check_still_contract, compose_still_shot
from agent008.tests.test_batch0c import FIXTURE_V2, _no_network, _Tmp
from agent008.tests.test_g03 import _rgba_png
from agent008.tests.test_motion import PINS, SMALL, ComposeFixture, _wav

W, H = 480, 270
RED, BLUE, GREEN = (220, 20, 30), (20, 40, 230), (30, 200, 60)
GLASS = {'shape': 'ELLIPSE', 'cx': 360, 'cy': 135, 'rx': 90, 'ry': 110, 'feather_px': 0}
GOV = {'sync': {('TEST-S004', GLINT): 'SFX-LUMI-CLUE-CHIME', ('TEST-S025', POP): 'SFX-COMPLETION-POP-v01'},
       'glint_target': {'TEST-S004': 'TEST-OVERLAY-CHEEK'}}
OV = ('TEST-OVERLAY-CHEEK', 'TEST-OVERLAY-MOUTH', 'TEST-OVERLAY-NOSE')


def _base_png(path):
    """Grey-blue backdrop; left 'face' region with a red/blue split block (so a left-right reversal is observable)."""
    a = np.zeros((H, W, 3), np.uint8)
    a[...] = (90, 110, 140)
    a[60:200, 40:200] = (200, 160, 120)                       # face region
    a[100:130, 60:100] = RED                                  # asymmetric face feature: red left, blue right
    a[100:130, 100:140] = BLUE
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-i', '-',
                    '-frames:v', '1', str(path)], input=a.tobytes(), check=True)


class _G08(_Tmp):
    @classmethod
    def setUpClass(cls):
        cls.episode = {r['shot_id']: r for r in resolve_episode(load_snapshot(FIXTURE_V2), load_hash_pins(PINS), SMALL)}

    def setUp(self):
        super().setUp()
        self.patch = mock.patch.object(g08, 'GOVERNED', GOV)
        self.patch.start()
        self.addCleanup(self.patch.stop)
        (self.tmp / 'in').mkdir()
        self.base = self.tmp / 'in' / 'base.png'
        _base_png(self.base)
        self.ov = {}
        for i, aid in enumerate(OV):
            p = self.tmp / 'in' / f'{aid}.png'
            _rgba_png(p, 120, 90, (30 + i, 20, 40, 30), (GREEN, GREEN))
            self.ov[aid] = p
        for name, sec, f in (('chime', 0.4, 880), ('pop', 0.2, 660), ('amb', 2.0, 0)):
            _wav(self.tmp / 'in' / f'{name}.wav', sec, f, 0.003 if f == 0 else 0.2)
        self.audio = {'SFX-LUMI-CLUE-CHIME': self.tmp / 'in' / 'chime.wav', 'SFX-COMPLETION-POP-v01': self.tmp / 'in' / 'pop.wav',
                      'AMB-BATHROOM-QUIET-v01': self.tmp / 'in' / 'amb.wav'}

    # --- specs ---
    def spec(self, sid, overlays=3):
        s = copy.deepcopy(self.episode[sid]['spec'])
        s['shot_id'] = f'TEST-{sid}'
        s['dialogue_slots'] = []                              # dialogue is covered by the G09 tests
        s['active_overlays'] = [{'asset_id': aid, 'registry_row_id': f'test-{aid}', 'asset_type': 'OVERLAY_VFX',
                                 'asset_subtype': 'BERRY_SMUDGE_OVERLAY', 'status': 'APPROVED',
                                 'expected_sha256': sha256_file(self.ov[aid])} for aid in OV[:overlays]]
        return s

    def frame(self, sid, path=None, cls='SHOT_FRAME/BASE_FRAME', **extra):
        p = Path(path or self.base)
        return {'asset_id': f'TEST-FRAME-{sid}', 'registry_id': 'test-row', 'classification': cls, 'registry_status': 'APPROVED',
                'shot_id': f'TEST-{sid}', 'path': str(p), 'expected_sha256': sha256_file(p), **extra}

    # --- G03 stage for overlay shots ---
    def g03(self, spec, sid, placements, sub='g03'):
        rec = {'contract': G03_CONTRACT, 'record_id': 'TEST-G03', 'shot_id': spec['shot_id'],
               'base_frame': {'asset_id': f'TEST-FRAME-{sid}', 'sha256': sha256_file(self.base)}, 'frame_size': [W, H],
               'frame_range': [0, spec['frames'] - 1], 'placements': placements}
        prov = place_overlays(spec, self.frame(sid), {o['asset_id']: self.ov[o['asset_id']] for o in spec['active_overlays']},
                              {'record': rec, 'approval_status': 'APPROVED', 'expected_sha256': canonical_sha256(rec)},
                              self.tmp / sub)
        f = self.frame(sid, self.tmp / sub / prov['output']['file'], 'SHOT_FRAME/DERIVED_FRAME',
                       overlays_composited=prov['overlays_composited'])
        return f, prov

    def pl(self, aid, surface, x, y, w=30):
        return {'asset_id': aid, 'overlay_sha256': sha256_file(self.ov[aid]), 'surface': surface, 'anchor': 'CENTER',
                'x': x, 'y': y, 'width_px': w, 'mirror': surface == 'REFLECTION'}

    # --- G08 record ---
    def rec(self, spec, frame_sha, **sections):
        r = {'contract': CONTRACT_ID, 'record_id': 'TEST-G08', 'shot_id': spec['shot_id'],
             'input_frame': {'asset_id': 'x', 'sha256': frame_sha}, 'frame_size': [W, H],
             'frame_range': [0, spec['frames'] - 1], 'mirror_glass': dict(GLASS)}
        r.update({k: v for k, v in sections.items() if v is not None})
        return {'record': r, 'approval_status': 'APPROVED', 'expected_sha256': canonical_sha256(r)}

    def composite(self, reflected=(), **over):
        return {'mode': 'COMPOSITE', 'reflected_overlays': list(reflected), 'source_rect': [40, 60, 160, 140],
                'flip': 'HORIZONTAL', 'target_center': [360, 135], 'target_width_px': 120, 'tint_rgb': [214, 232, 246],
                'tint_amount': 0.07, **over}

    def glint(self, **over):
        return {'treatment_id': GLINT, 'start_frame': 12, 'frames': 8, 'cx': 360, 'cy': 100, 'size_px': 24, **over}

    def pop(self, **over):
        return {'treatment_id': POP, 'start_frame': 24, 'frames': 7, 'gain': 0.12, 'sync_audio_asset_id': 'SFX-COMPLETION-POP-v01',
                **over}

    def code(self, fn, *a, **k):
        with self.assertRaises(FailClosed) as e:
            fn(*a, **k)
        return e.exception.code

    # --- common shot builds ---
    def s025(self, sub='refl', mode='COMPOSITE', pop=None, **refl_over):
        spec = self.spec('S025', overlays=0)
        f = self.frame('S025')
        refl = self.composite(**refl_over) if mode == 'COMPOSITE' else {'mode': 'PRESERVE', 'reflected_overlays': []}
        t = self.rec(spec, f['expected_sha256'], reflection=refl, pop=pop or self.pop())
        prov = apply_reflection(spec, f, t, self.tmp / sub)
        out = self.tmp / sub / prov['output']['file'] if prov['output']['file'] else self.base
        held = self.frame('S025', out, 'SHOT_FRAME/DERIVED_FRAME', treatments_composited=prov['treatments_composited'])
        return spec, f, t, prov, held

    def s004(self):
        spec = self.spec('S004')
        placements = [self.pl('TEST-OVERLAY-CHEEK', 'FACE', 70, 90), self.pl('TEST-OVERLAY-MOUTH', 'FACE', 120, 170),
                      self.pl('TEST-OVERLAY-NOSE', 'FACE', 170, 80), self.pl('TEST-OVERLAY-CHEEK', 'REFLECTION', 360, 100)]
        f, prov = self.g03(spec, 'S004', placements)
        t = self.rec(spec, f['expected_sha256'], glint=self.glint(target_overlay='TEST-OVERLAY-CHEEK',
                                                                  sync_audio_asset_id='SFX-LUMI-CLUE-CHIME'))
        timing = {'named': {'SFX-LUMI-CLUE-CHIME': {'start_seconds': 0.5, 'gain_db': -12.0}}}
        return spec, f, t, timing, prov

    def still(self, spec, frame, sub, timing=None, t=None, **k):
        return compose_still_shot(spec, frame, SMALL, self.audio, timing or {}, self.tmp / sub, treatment_record=t, **k)


class G08Glint(_G08):
    """C-T01..T02: mirror glint (S004 / S012 / S018 class)."""

    def test_T01_valid_mirror_glint(self):
        spec, f, t, timing, _ = self.s004()
        p = self.still(spec, f, 'a', timing, t)
        self.assertEqual(p['qc']['automatic_result'], 'PASS', p['qc']['issues'])
        self.assertEqual(p['qc']['treatments_applied'], 1)
        self.assertEqual(p['qc']['distinct_frames'], 1 + 8)
        w = p['treatments']['windows'][0]
        self.assertEqual((w['treatment_id'], w['start_frame'], w['frames'], w['target_overlay']),
                         (GLINT, 12, 8, 'TEST-OVERLAY-CHEEK'))
        self.assertEqual(w['sync'], {'audio_asset_id': 'SFX-LUMI-CLUE-CHIME', 'audio_start_seconds': 0.5, 'frame': 12})

    def test_T02_glint_exact_placement_and_timing(self):
        spec, f, t, timing, _ = self.s004()
        img = decode_png_rgb(f['path'])
        plan = plan_timed(spec, t, f['expected_sha256'], (W, H), timing, 24, overlays_composited=f['overlays_composited'])
        x0, y0, x1, y1 = plan['windows'][0]['box']
        self.assertEqual([x0, y0, x1, y1], [348, 88, 372, 112])
        mask = np.ones((H, W), bool)
        mask[y0:y1, x0:x1] = False
        energy = []
        for i in range(spec['frames']):
            fr = render_frame(img, plan, i)
            if not 12 <= i < 20:
                self.assertIs(fr, img, i)                     # untouched outside the window
                continue
            self.assertTrue(np.array_equal(fr[mask], img[mask]), i)   # only the sprite box changes
            energy.append(int(np.abs(fr.astype(int) - img.astype(int)).sum()))
        self.assertEqual(len(energy), 8)
        self.assertEqual(int(np.argmax(energy)), round(8 * 0.3))      # soft attack/decay peak
        self.assertTrue(all(e > 0 for e in energy))
        bad = self.rec(spec, f['expected_sha256'], glint=self.glint(start_frame=13, target_overlay='TEST-OVERLAY-CHEEK',
                                                                    sync_audio_asset_id='SFX-LUMI-CLUE-CHIME'))
        self.assertEqual(self.code(self.still, spec, f, 'x', timing, bad), 'TREATMENT_AUDIO_SYNC_MISMATCH')
        nosync = self.rec(spec, f['expected_sha256'], glint=self.glint(target_overlay='TEST-OVERLAY-CHEEK'))
        self.assertEqual(self.code(self.still, spec, f, 'x', timing, nosync), 'TREATMENT_AUDIO_SYNC_MISSING')
        wrong = self.rec(spec, f['expected_sha256'], glint=self.glint(target_overlay='TEST-OVERLAY-MOUTH',
                                                                      sync_audio_asset_id='SFX-LUMI-CLUE-CHIME'))
        self.assertEqual(self.code(self.still, spec, f, 'x', timing, wrong), 'GLINT_TARGET_INVALID')


class G08Reflection(_G08):
    """C-T03..T06: mirror reflection (COMPOSITE / PRESERVE), orientation, clipping, mirrored overlays."""

    def test_T03_valid_mirror_reflection(self):
        spec, f, t, prov, held = self.s025()
        self.assertEqual(prov['status'], 'REVIEW')
        self.assertEqual(prov['treatments_composited']['treatments'], [REFL])
        self.assertEqual(prov['treatments_composited']['input_frame_sha256'], f['expected_sha256'])
        self.assertNotEqual(prov['output']['sha256'], f['expected_sha256'])
        self.assertEqual(prov['proposed_registry']['asset_subtype'], 'DERIVED_FRAME')
        out, base = decode_png_rgb(held['path']), decode_png_rgb(self.base)
        outside = g08.glass_mask(H, W, GLASS) == 0
        self.assertTrue(np.array_equal(out[outside], base[outside]))
        self.assertFalse(np.array_equal(out[~outside], base[~outside]))

    def test_T04_correct_mirror_orientation(self):
        spec, f, t, prov, held = self.s025(tint_amount=0.0)
        out = decode_png_rgb(held['path']).astype(int)
        # source block rows 100..129: red x 60..99, blue x 100..139; source rect x 40..199 (160 wide), copy 120x105 at (300, 83)
        # reversal: blue -> u 60..99 -> x 345..374, red -> u 100..139 -> x 375..404; rows -> y 113..135
        y = 135 - 105 // 2 + int((115 - 60) * 0.75)
        left, right = out[y, 352], out[y, 395]
        self.assertGreater(left[2], left[0])               # blue on the viewer's left after reversal
        self.assertGreater(right[0], right[2])             # red on the right
        bad = copy.deepcopy(t)
        bad['record']['reflection']['flip'] = 'VERTICAL'
        bad['expected_sha256'] = canonical_sha256(bad['record'])
        self.assertEqual(self.code(apply_reflection, spec, f, bad, self.tmp / 'x'), 'MIRROR_SEMANTICS_UNSUPPORTED')
        for mode in ('TILTED', None):
            r = copy.deepcopy(t)
            r['record']['reflection']['mode'] = mode
            r['expected_sha256'] = canonical_sha256(r['record'])
            self.assertEqual(self.code(apply_reflection, spec, f, r, self.tmp / 'x'), 'MIRROR_SEMANTICS_UNSUPPORTED')

    def test_T05_mirror_clipping(self):
        # 250x260 copy placed at (235, 5): larger than the 180x220 glass ellipse in both directions
        spec, f, t, prov, held = self.s025(source_rect=[0, 0, 260, 270], target_width_px=250)
        out, base = decode_png_rgb(held['path']), decode_png_rgb(self.base)
        outside = g08.glass_mask(H, W, GLASS) == 0
        self.assertTrue(np.array_equal(out[outside], base[outside]))   # nothing of the copy outside the glass
        self.assertTrue(np.array_equal(out[135, 265], base[135, 265]))  # inside the copy, left of the ellipse: untouched
        self.assertFalse(np.array_equal(out[135, 275], base[135, 275])) # just inside the left glass edge: reflection
        self.assertTrue(np.array_equal(out[10, 360], base[10, 360]))    # above the ellipse, inside the copy: untouched

    def test_T06_mirrored_overlay_behaviour(self):
        spec = self.spec('S007', overlays=2)
        spec['video_generation_required'] = False
        face = [self.pl('TEST-OVERLAY-CHEEK', 'FACE', 70, 90), self.pl('TEST-OVERLAY-MOUTH', 'FACE', 120, 170)]
        f, fp = self.g03(spec, 'S007', face)
        # COMPOSITE: marks inside the source region are carried into the glass, reversed
        t = self.rec(spec, f['expected_sha256'], reflection=self.composite(['TEST-OVERLAY-CHEEK', 'TEST-OVERLAY-MOUTH']))
        prov = apply_reflection(spec, f, t, self.tmp / 'c', fp)
        self.assertEqual(prov['treatments_composited']['reflected_overlays'], ['TEST-OVERLAY-CHEEK', 'TEST-OVERLAY-MOUTH'])
        out = decode_png_rgb(self.tmp / 'c' / prov['output']['file']).astype(int)
        # cheek at x 55..85 -> reversed u = 160 - (85-40) = 115..145 -> x 300 + 86..109; y 75..105 -> 135-52+11..34
        self.assertGreater(out[100, 395, 1], out[100, 395, 0])   # green mark visible at the mirrored position
        under = self.rec(spec, f['expected_sha256'], reflection=self.composite(['TEST-OVERLAY-CHEEK']))
        self.assertEqual(self.code(apply_reflection, spec, f, under, self.tmp / 'x', fp), 'REFLECTED_OVERLAYS_MISMATCH')
        # PRESERVE: reflected marks are the G03 REFLECTION placements and must lie inside the glass
        g, gp = self.g03(spec, 'S007', face + [self.pl('TEST-OVERLAY-CHEEK', 'REFLECTION', 360, 100)], sub='g2')
        ok = self.rec(spec, g['expected_sha256'], reflection={'mode': 'PRESERVE', 'reflected_overlays': ['TEST-OVERLAY-CHEEK']})
        pv = apply_reflection(spec, g, ok, self.tmp / 'p', gp)
        self.assertEqual((pv['output']['sha256'], pv['output']['new_pixels']), (g['expected_sha256'], False))
        dbl = self.rec(spec, g['expected_sha256'], reflection=self.composite(['TEST-OVERLAY-CHEEK']))
        self.assertEqual(self.code(apply_reflection, spec, g, dbl, self.tmp / 'x', gp), 'REFLECTION_DOUBLE_SOURCE')
        h, hp = self.g03(spec, 'S007', face + [self.pl('TEST-OVERLAY-CHEEK', 'REFLECTION', 280, 30)], sub='g3')
        out_glass = self.rec(spec, h['expected_sha256'], reflection={'mode': 'PRESERVE', 'reflected_overlays': ['TEST-OVERLAY-CHEEK']})
        self.assertEqual(self.code(apply_reflection, spec, h, out_glass, self.tmp / 'x', hp), 'REFLECTED_MARK_OUTSIDE_GLASS')
        k, kp = self.g03(spec, 'S007', [self.pl('TEST-OVERLAY-CHEEK', 'FACE', 70, 90),
                                       self.pl('TEST-OVERLAY-MOUTH', 'FACE', 360, 200)], sub='g4')
        on_glass = self.rec(spec, k['expected_sha256'], reflection={'mode': 'PRESERVE', 'reflected_overlays': []})
        self.assertEqual(self.code(apply_reflection, spec, k, on_glass, self.tmp / 'x', kp), 'OVERLAY_ON_MIRROR_GLASS')
        m, mp = self.g03(spec, 'S007', [self.pl('TEST-OVERLAY-CHEEK', 'FACE', 40, 90),
                                       self.pl('TEST-OVERLAY-MOUTH', 'FACE', 120, 170)], sub='g5')
        clip = self.rec(spec, m['expected_sha256'], reflection=self.composite(['TEST-OVERLAY-MOUTH']))
        self.assertEqual(self.code(apply_reflection, spec, m, clip, self.tmp / 'x', mp), 'REFLECTED_MARK_CLIPPED')


class G08CompletionPop(_G08):
    """C-T07..T08: completion pop on the clean reveal."""

    def test_T07_valid_completion_pop(self):
        spec, f, t, prov, held = self.s025()
        timing = {'named': {'SFX-COMPLETION-POP-v01': {'start_seconds': 1.0, 'gain_db': -6.0}}}
        p = self.still(spec, held, 'a', timing, t)
        self.assertEqual(p['qc']['automatic_result'], 'PASS', p['qc']['issues'])
        self.assertEqual((p['qc']['treatments_applied'], p['qc']['treatments_precomposited']), (1, 1))
        w = p['treatments']['windows'][0]
        self.assertEqual((w['treatment_id'], w['start_frame'], w['frames'], w['gain']), (POP, 24, 7, 0.12))
        img = decode_png_rgb(held['path'])
        plan = plan_timed(spec, t, held['expected_sha256'], (W, H), timing, 24, held['treatments_composited'])
        peak = render_frame(img, plan, 24 + 3)
        inside = g08.glass_mask(H, W, GLASS) > 0
        self.assertTrue(np.array_equal(peak[~inside], img[~inside]))
        self.assertGreater(float(peak[inside].mean()), float(img[inside].mean()))      # brighter glass only
        late = {'named': {'SFX-COMPLETION-POP-v01': {'start_seconds': 1.5, 'gain_db': -6.0}}}
        self.assertEqual(self.code(self.still, spec, held, 'x', late, t), 'TREATMENT_AUDIO_SYNC_MISMATCH')

    def test_T08_clean_reveal_excludes_overlays(self):
        spec = self.spec('S025', overlays=0)
        dirty_spec = {**spec, 'active_overlays': self.spec('S025', overlays=1)['active_overlays']}
        f = self.frame('S025')
        t = self.rec(spec, f['expected_sha256'], reflection=self.composite(), pop=self.pop())
        self.assertEqual(self.code(apply_reflection, dirty_spec, f, t, self.tmp / 'x'), 'CLEAN_REVEAL_HAS_ACTIVE_OVERLAYS')
        g, _ = self.g03(self.spec('S025', overlays=1), 'S025', [self.pl('TEST-OVERLAY-CHEEK', 'FACE', 70, 90)])
        t2 = self.rec(spec, g['expected_sha256'], reflection=self.composite(), pop=self.pop())
        self.assertEqual(self.code(apply_reflection, spec, g, t2, self.tmp / 'x'), 'CLEAN_REVEAL_HAS_ACTIVE_OVERLAYS')
        t3 = self.rec(spec, f['expected_sha256'], reflection=self.composite(['TEST-OVERLAY-CHEEK']), pop=self.pop())
        self.assertEqual(self.code(apply_reflection, spec, f, t3, self.tmp / 'x'), 'REFLECTED_OVERLAYS_INVALID')
        spec_pop = {**self.spec('S012', overlays=0), 'treatments': [{'treatment_id': POP}], 'clean_reveal': False}
        spec_pop['active_overlays'] = self.spec('S012', overlays=1)['active_overlays']
        h, _ = self.g03(spec_pop, 'S012', [self.pl('TEST-OVERLAY-CHEEK', 'FACE', 70, 90)], sub='g6')
        tp = self.rec(spec_pop, h['expected_sha256'], pop=self.pop(sync_audio_asset_id=None))
        self.assertEqual(self.code(plan_timed, spec_pop, tp, h['expected_sha256'], (W, H), {}, 24, None,
                                   h['overlays_composited']), 'CLEAN_REVEAL_HAS_ACTIVE_OVERLAYS')


class G08FailClosed(_G08):
    """C-T09..T16: frame range, unsupported, approval, hashes, geometry, duplicates, immutability."""

    def test_T09_treatment_frame_range(self):
        spec, f, t, timing, _ = self.s004()
        args = (spec, None, f['expected_sha256'], (W, H), timing, 24, None, f['overlays_composited'])

        def run(**g):
            r = self.rec(spec, f['expected_sha256'], glint=self.glint(target_overlay='TEST-OVERLAY-CHEEK', **g))
            return plan_timed(spec, r, *args[2:], governed={'sync': {}, 'glint_target': GOV['glint_target']})
        for frames in (6, 10):
            self.assertEqual(run(frames=frames)['windows'][0]['frames'], frames)
        for g in ({'frames': 5}, {'frames': 11}, {'start_frame': 115}, {'start_frame': -1}, {'start_frame': 12.0}):
            self.assertEqual(self.code(run, **g), 'TREATMENT_FRAME_RANGE_INVALID', g)
        r = self.rec(spec, f['expected_sha256'], glint=self.glint(target_overlay='TEST-OVERLAY-CHEEK'))
        self.assertEqual(self.code(plan_timed, spec, r, *args[2:], governed={'sync': {}, 'glint_target': {}}, segment=(60, 119)),
                         'TREATMENT_OUTSIDE_GOVERNED_RANGE')            # G07 segment bound (S018)
        bad = self.rec(spec, f['expected_sha256'], glint=self.glint())
        bad['record']['frame_range'] = [0, 100]
        bad['expected_sha256'] = canonical_sha256(bad['record'])
        self.assertEqual(self.code(plan_timed, spec, bad, *args[2:]), 'TREATMENT_FRAME_RANGE_INVALID')

    def test_T10_unsupported_treatment_rejected(self):
        spec, f, t, timing, _ = self.s004()
        self.assertEqual(self.code(self.still, {**spec, 'treatments': [{'treatment_id': 'TREATMENT-EP005-SPARKLE-v01'}]},
                                   f, 'x', timing, t), 'TREATMENT_UNSUPPORTED')
        extra = self.rec(spec, f['expected_sha256'], glint=self.glint(target_overlay='TEST-OVERLAY-CHEEK',
                                                                      sync_audio_asset_id='SFX-LUMI-CLUE-CHIME'), pop=self.pop())
        self.assertEqual(self.code(self.still, spec, f, 'x', timing, extra), 'TREATMENT_UNDECLARED')
        missing = self.rec(spec, f['expected_sha256'])
        self.assertEqual(self.code(self.still, spec, f, 'x', timing, missing), 'TREATMENT_RECORD_INCOMPLETE')
        self.assertEqual(self.code(self.still, spec, f, 'x', timing), 'STILL_TREATMENTS_NEED_G08')
        rect = self.rec(spec, f['expected_sha256'], glint=self.glint())
        rect['record']['mirror_glass']['shape'] = 'RECT'
        rect['expected_sha256'] = canonical_sha256(rect['record'])
        self.assertEqual(self.code(self.still, spec, f, 'x', timing, rect), 'TREATMENT_MASK_UNSUPPORTED')
        odd = self.rec(spec, f['expected_sha256'], glint={**self.glint(), 'scale_envelope': True})
        self.assertEqual(self.code(self.still, spec, f, 'x', timing, odd), 'TREATMENT_FIELD_UNSUPPORTED')
        wrong_id = self.rec(spec, f['expected_sha256'], glint=self.glint(treatment_id=POP))
        self.assertEqual(self.code(self.still, spec, f, 'x', timing, wrong_id), 'TREATMENT_UNSUPPORTED')

    def test_T11_unapproved_source_rejected(self):
        spec, f, t, prov, held = self.s025(sub='ok')
        self.assertEqual(self.code(apply_reflection, spec, {**f, 'registry_status': 'REVIEW'}, t, self.tmp / 'x'),
                         'TREATMENT_SOURCE_NOT_APPROVED')
        self.assertEqual(self.code(apply_reflection, spec, {**f, 'classification': 'SHOT_MOTION/RAW_MOTION_SOURCE'}, t,
                                   self.tmp / 'x'), 'TREATMENT_SOURCE_NOT_A_SHOT_FRAME')
        for st in ('REVIEW', None):
            self.assertEqual(self.code(apply_reflection, spec, f, {**t, 'approval_status': st}, self.tmp / 'x'),
                             'TREATMENT_RECORD_NOT_APPROVED')
        self.assertEqual(self.code(self.still, spec, {**held, 'registry_status': 'REVIEW'}, 'x', {}, t), 'STILL_SOURCE_NOT_APPROVED')
        self.assertEqual(self.code(apply_reflection, spec, f, {'approval_status': 'APPROVED'}, self.tmp / 'x'),
                         'TREATMENT_RECORD_MISSING')

    def test_T12_source_sha_mismatch_rejected(self):
        spec, f, t, prov, held = self.s025(sub='ok')
        self.assertEqual(self.code(apply_reflection, spec, {**f, 'expected_sha256': 'a' * 64}, t, self.tmp / 'x'), 'HASH_MISMATCH')
        other = self.rec(spec, 'b' * 64, reflection=self.composite(), pop=self.pop())
        self.assertEqual(self.code(apply_reflection, spec, f, other, self.tmp / 'x'), 'TREATMENT_RECORD_FRAME_MISMATCH')
        cert = copy.deepcopy(held)
        cert['treatments_composited']['frame_sha256'] = 'c' * 64
        self.assertEqual(self.code(self.still, spec, cert, 'x', {}, t), 'TREATMENT_CERTIFICATE_FRAME_MISMATCH')
        self.assertEqual(self.code(self.still, spec, {**held, 'expected_sha256': 'd' * 64}, 'x', {}, t),
                         'TREATMENT_CERTIFICATE_FRAME_MISMATCH')

    def test_T13_treatment_input_hash_mismatch_rejected(self):
        """Treatments are procedural (COMPOSITING_TREATMENT_NOT_AN_ASSET): the governed treatment inputs are the approved
        record and the authenticated G03 provenance; each is hash-bound."""
        spec, f, t, prov, held = self.s025(sub='ok')
        edited = copy.deepcopy(t)
        edited['record']['pop']['gain'] = 0.1
        self.assertEqual(self.code(apply_reflection, spec, f, edited, self.tmp / 'x'), 'TREATMENT_RECORD_HASH_MISMATCH')
        timing = {'named': {'SFX-COMPLETION-POP-v01': {'start_seconds': 1.0, 'gain_db': -6.0}}}
        other = self.rec(spec, f['expected_sha256'], reflection=self.composite(), pop=self.pop(gain=0.1))
        self.assertEqual(self.code(self.still, spec, held, 'x', timing, other), 'TREATMENT_RECORD_HASH_MISMATCH')
        spec7 = self.spec('S007', overlays=1)
        g, g03prov = self.g03(spec7, 'S007', [self.pl('TEST-OVERLAY-CHEEK', 'FACE', 70, 90)])
        r = self.rec(spec7, g['expected_sha256'], reflection=self.composite(['TEST-OVERLAY-CHEEK']))
        self.assertEqual(self.code(apply_reflection, spec7, g, r, self.tmp / 'x'), 'G03_PROVENANCE_MISMATCH')
        forged = copy.deepcopy(g03prov)
        forged['placements'][0]['visible_box'] = [0, 0, 1, 1]
        self.assertEqual(self.code(apply_reflection, spec7, g, r, self.tmp / 'x', forged), 'G03_PROVENANCE_MISMATCH')
        apply_reflection(spec7, g, r, self.tmp / 'ok7', g03prov)

    def test_T14_invalid_geometry_rejected(self):
        spec = self.spec('S025', overlays=0)
        f = self.frame('S025')
        cases = (({'mirror_glass': {**GLASS, 'cx': 450}}, 'TREATMENT_COORDINATE_INVALID'),
                 ({'mirror_glass': {**GLASS, 'rx': 1}}, 'TREATMENT_MASK_UNSUPPORTED'),
                 ({'mirror_glass': {**GLASS, 'cx': 360.5}}, 'TREATMENT_COORDINATE_INVALID'),
                 ({'mirror_glass': {**GLASS, 'feather_px': 9}}, 'TREATMENT_MASK_UNSUPPORTED'),
                 ({'reflection': self.composite(target_width_px=161)}, 'TREATMENT_SCALE_INVALID'),
                 ({'reflection': self.composite(target_width_px=1)}, 'TREATMENT_SCALE_INVALID'),
                 ({'reflection': self.composite(source_rect=[300, 60, 100, 100])}, 'REFLECTION_SOURCE_ON_GLASS'),
                 ({'reflection': self.composite(source_rect=[400, 60, 100, 100])}, 'TREATMENT_COORDINATE_INVALID'),
                 ({'reflection': self.composite(target_center=[200, 135])}, 'TREATMENT_COORDINATE_INVALID'),
                 ({'reflection': self.composite(tint_amount=0.5)}, 'TREATMENT_FIELD_INVALID'),
                 ({'reflection': self.composite(tint_rgb=[0, 0])}, 'TREATMENT_FIELD_INVALID'))
        for over, code in cases:
            sec = {'reflection': self.composite(), 'pop': self.pop()}
            sec.update({k: v for k, v in over.items() if k != 'mirror_glass'})
            t = self.rec(spec, f['expected_sha256'], **sec)
            if 'mirror_glass' in over:
                t['record']['mirror_glass'] = over['mirror_glass']
                t['expected_sha256'] = canonical_sha256(t['record'])
            self.assertEqual(self.code(apply_reflection, spec, f, t, self.tmp / 'x'), code, over)
        s4, f4, _, timing, _ = self.s004()
        args = (f4['expected_sha256'], (W, H), timing, 24, None, f4['overlays_composited'])
        for g, code in (({'cx': 270, 'cy': 135}, 'GLINT_OUTSIDE_GLASS'), ({'size_px': 3}, 'TREATMENT_SCALE_INVALID'),
                        ({'size_px': 400}, 'GLINT_OUTSIDE_GLASS'), ({'cx': 360.0}, 'TREATMENT_COORDINATE_INVALID')):
            r = self.rec(s4, f4['expected_sha256'], glint=self.glint(target_overlay='TEST-OVERLAY-CHEEK',
                                                                     sync_audio_asset_id='SFX-LUMI-CLUE-CHIME', **g))
            self.assertEqual(self.code(plan_timed, s4, r, *args), code, g)
        for gain in (0.0, 0.2, -0.1, True):
            spec25, _, t25, _, held = self.s025(sub=f'p{gain}', pop=self.pop(gain=gain))
            timing = {'named': {'SFX-COMPLETION-POP-v01': {'start_seconds': 1.0, 'gain_db': -6.0}}}
            self.assertEqual(self.code(plan_timed, spec25, t25, held['expected_sha256'], (W, H), timing, 24,
                                       held['treatments_composited']), 'TREATMENT_FIELD_INVALID', gain)

    def test_T15_duplicate_treatment_rejected(self):
        spec, f, t, prov, held = self.s025(sub='ok')
        dup = {**spec, 'treatments': spec['treatments'] + [spec['treatments'][0]]}
        self.assertEqual(self.code(apply_reflection, dup, f, t, self.tmp / 'x'), 'TREATMENT_DUPLICATE_INVOCATION')
        self.assertEqual(self.code(apply_reflection, spec, held, t, self.tmp / 'x'), 'TREATMENT_DUPLICATE_INVOCATION')
        cert = copy.deepcopy(held)
        cert['treatments_composited']['treatments'] = [REFL, REFL]
        self.assertEqual(self.code(self.still, spec, cert, 'x', {}, t), 'TREATMENT_CERTIFICATE_INVALID')

    def test_T16_source_immutability_and_no_overwrite(self):
        before = (sha256_file(self.base), os.stat(self.base).st_mtime_ns)
        spec, f, t, prov, held = self.s025(sub='a')
        self.assertEqual(before, (sha256_file(self.base), os.stat(self.base).st_mtime_ns))
        self.assertEqual(self.code(apply_reflection, spec, f, t, self.tmp / 'a'), 'OUTPUT_EXISTS')
        clash = self.tmp / 'c' / 'TEST-S025_G08_REFLECTION_FRAME_CANDIDATE.png'
        clash.parent.mkdir()
        clash.write_bytes(self.base.read_bytes())
        t2 = self.rec(spec, sha256_file(clash), reflection=self.composite(), pop=self.pop())
        self.assertEqual(self.code(apply_reflection, spec, self.frame('S025', clash), t2, self.tmp / 'c'), 'OUTPUT_EXISTS')
        self.assertEqual(sha256_file(clash), before[0])
        spec4, f4, t4, timing, _ = self.s004()
        b4 = sha256_file(f4['path'])
        self.still(spec4, f4, 's', timing, t4)
        self.assertEqual(sha256_file(f4['path']), b4)


class G08DeterminismOrderAndRegression(_G08):
    """C-T17..T19: two-run determinism, G03 + G08 ordering, treatment-free regression; no network."""

    def test_T17_two_run_determinism(self):
        a = self.s025(sub='a')[3]
        b = self.s025(sub='b')[3]
        self.assertEqual(a['output']['sha256'], b['output']['sha256'])
        self.assertEqual(a['deterministic_core_sha256'], b['deterministic_core_sha256'])
        spec, f, t, timing, _ = self.s004()
        g1, g2 = self.still(spec, f, 'g1', timing, t), self.still(spec, f, 'g2', timing, t)
        self.assertEqual(g1['outputs'], g2['outputs'])
        self.assertEqual(g1['deterministic_core_sha256'], g2['deterministic_core_sha256'])
        spec25, _, t25, _, held = self.s025(sub='c')
        timing = {'named': {'SFX-COMPLETION-POP-v01': {'start_seconds': 1.0, 'gain_db': -6.0}}}
        p1, p2 = self.still(spec25, held, 'p1', timing, t25), self.still(spec25, held, 'p2', timing, t25)
        self.assertEqual(p1['outputs'], p2['outputs'])

    def test_T18_g03_then_g08_order(self):
        spec = self.spec('S007', overlays=1)
        spec['video_generation_required'] = False
        spec['named_sfx'] = []                                   # audio events are covered by the G02/G05 tests
        t_wrong = self.rec(spec, sha256_file(self.base), reflection=self.composite(['TEST-OVERLAY-CHEEK']))
        self.assertEqual(self.code(apply_reflection, spec, self.frame('S007'), t_wrong, self.tmp / 'x'),
                         'STILL_OVERLAYS_NEED_G03_ANCHORS')               # G08 before G03 is refused
        g, gprov = self.g03(spec, 'S007', [self.pl('TEST-OVERLAY-CHEEK', 'FACE', 70, 90)])
        t = self.rec(spec, g['expected_sha256'], reflection=self.composite(['TEST-OVERLAY-CHEEK']))
        p = apply_reflection(spec, g, t, self.tmp / 'r', gprov)
        held = self.frame('S007', self.tmp / 'r' / p['output']['file'], 'SHOT_FRAME/DERIVED_FRAME',
                          overlays_composited=g['overlays_composited'], treatments_composited=p['treatments_composited'])
        s = self.still(spec, held, 's', {}, t)
        self.assertEqual(s['qc']['automatic_result'], 'PASS', s['qc']['issues'])
        self.assertEqual((s['qc']['overlays_precomposited'], s['qc']['treatments_precomposited']), (1, 1))
        self.assertEqual(self.code(self.still, spec, g, 'x', {}, t), 'TREATMENT_NOT_COMPOSITED')   # reflection skipped
        swapped = copy.deepcopy(held)
        swapped['overlays_composited']['frame_sha256'] = p['output']['sha256']                    # chain broken
        self.assertEqual(self.code(self.still, spec, swapped, 'x', {}, t), 'OVERLAY_PRECOMPOSITE_FRAME_MISMATCH')

    def test_T19_treatment_free_and_scope_regression(self):
        spec = {**self.spec('S023', overlays=0)}
        p = self.still(spec, self.frame('S023'), 'a', {})
        self.assertEqual(p['qc']['automatic_result'], 'PASS', p['qc']['issues'])
        self.assertNotIn('treatments', p)
        self.assertNotIn('treatments_precomposited', p['qc'])
        t = self.rec(spec, sha256_file(self.base), glint=self.glint())
        self.assertEqual(self.code(self.still, spec, self.frame('S023'), 'x', {}, t), 'TREATMENT_UNDECLARED')
        s18 = {**spec, 'shot_id': 'S018'}
        self.assertEqual(self.code(check_still_contract, s18, SMALL), 'STILL_IN_SHOT_CUT_NEEDS_G07')
        spec4, f4, t4, timing, _ = self.s004()
        self.assertEqual(self.code(self.still, spec4, f4, 'x', timing, t4, crop={'x': 0, 'y': 0, 'w': 240, 'h': 135}),
                         'TREATMENT_LAYOUT_NOT_IDENTITY')

    def test_T19b_no_provider_or_network(self):
        with mock.patch.object(socket, 'socket', _no_network), mock.patch.object(socket, 'create_connection', _no_network):
            p = self.s025(sub='a')[3]
        self.assertEqual(p['safety'], {'provider_calls': 0, 'source_mutated': False, 'auto_approved': False, 'registered': False})
        text = Path(g08.__file__).read_text()
        for mod in ('higgsfield', 'provider', 'http', 'urllib', 'requests', 'source_upload'):
            self.assertNotIn(f'import {mod}', text)
            self.assertNotIn(f'.{mod} import', text)


class G08MotionBaseFrame(ComposeFixture):
    """C-T20: only the certified static reflection may accompany generated motion; timed treatments stay rejected."""

    def test_T20_motion_reflection_precomposite_gate(self):
        src = self.req.source_frame_sha256
        spec = {**self.spec_shot, 'treatments': [{'treatment_id': REFL}]}
        cert = {'shot_id': 'S027', 'input_frame_sha256': 'e' * 64, 'frame_sha256': src, 'record_sha256': 'f' * 64,
                'treatments': [REFL], 'mode': 'COMPOSITE', 'reflected_overlays': []}
        run = lambda sub, sp=spec, **k: compose_motion_shot(self.result, self.req, sp, SMALL, self.assets, self.timing,
                                                            self.tmp / sub, **k)
        with self.assertRaises(FailClosed) as e:
            run('x')
        self.assertEqual(e.exception.code, 'MOTION_TREATMENTS_NEED_TRACKING_V02')
        for sp in ({**spec, 'treatments': [{'treatment_id': GLINT}]}, {**spec, 'treatments': [{'treatment_id': POP}]}):
            with self.assertRaises(FailClosed) as e:
                run('x', sp, treatments_composited=cert)
            self.assertEqual(e.exception.code, 'MOTION_TREATMENTS_NEED_TRACKING_V02')
        with self.assertRaises(FailClosed) as e:
            run('x', treatments_composited={**cert, 'frame_sha256': 'a' * 64})
        self.assertEqual(e.exception.code, 'TREATMENT_CERTIFICATE_FRAME_MISMATCH')
        with self.assertRaises(FailClosed) as e:
            run('x', self.spec_shot, treatments_composited=cert)
        self.assertEqual(e.exception.code, 'TREATMENT_UNDECLARED')
        p = run('ok', treatments_composited=cert)
        self.assertEqual(p['qc']['automatic_result'], 'PASS')
        self.assertEqual(p['qc']['treatments_precomposited_in_base_frame'], 1)
        self.assertEqual(p['treatments_composited_in_base_frame'], cert)
        ov = [{'asset_id': 'TEST-OVERLAY-NOSE', 'expected_sha256': '9' * 64, 'asset_type': 'OVERLAY_VFX', 'status': 'APPROVED'}]
        both = {**spec, 'active_overlays': ov}
        comp = {'shot_id': 'S027', 'frame_sha256': 'e' * 64, 'overlays': [{'asset_id': 'TEST-OVERLAY-NOSE', 'sha256': '9' * 64,
                                                                          'surface': 'FACE'}]}
        q = run('ok2', both, overlays_composited=comp, treatments_composited=cert)       # G03 frame -> G08 frame -> upload
        self.assertEqual(q['qc']['automatic_result'], 'PASS')


if __name__ == '__main__':
    unittest.main()
