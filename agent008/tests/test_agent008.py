"""AGENT-008 v0.1 test suite (stdlib unittest; needs ffmpeg/ffprobe and numpy).

Run:  python3 -m unittest discover -s agent008/tests -v

Contract tests use the committed read-only snapshot of the approved EP005
manifests. Render tests (T-08, T-09, T-10, T-12) build a SYNTHETIC asset set
with the same dimensions and identities in a temp dir, so the full pipeline
runs without production assets and without any network access.
"""
import copy
import json
import shutil
import subprocess
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

import numpy as np

from agent008 import media
from agent008.config import load_output_spec
from agent008.errors import FailClosed
from agent008.hashing import sha256_file, verify_file
from agent008.inputs import LEGACY_DENYLIST, load_hash_pins, load_snapshot, validate_readiness
from agent008.render import mix, plan, run
from agent008.resolve import Resolver
from agent008.spec import build_shot_spec, validate_continuity
from agent008.standin import load_layout
from agent008.timeline import dialogue_track, timed_text_from_slots, to_srt, to_webvtt
from agent008.treatments import validate_window
from agent008.verify import audio_report, check_hold, verify

PKG = Path(__file__).resolve().parents[1]
SNAP = PKG / 'inputs' / 'ep005_phase0_input_snapshot.json'
PINS = PKG / 'inputs' / 'hash_pins.json'
RID = 'edc4ad58-3e5d-4ac2-9c74-c9af03af363f'
PMID = '45cc7493-80b4-4e8d-b71d-fbd7fd3656ed'
RUN = 'A006-1791346204213'
IDS = {'readiness_manifest_id': RID, 'production_manifest_id': PMID, 'agent006_run_id': RUN}
BERRIES = ['OVERLAY-EP005-BERRY-SMUDGE-CHEEK-v01', 'OVERLAY-EP005-BERRY-SMUDGE-MOUTH-v01',
           'OVERLAY-EP005-BERRY-SMUDGE-NOSE-v01']


def snap():
    return load_snapshot(SNAP)


def resolver(s=None, pins=None):
    s = s or snap()
    r = validate_readiness(s, RID, PMID, RUN)
    return Resolver(r, s['asset_registry'], load_hash_pins(PINS) if pins is None else pins)


def shot(s, sid):
    return next(x for x in s['production_manifest']['manifest_json_reduced']['shot_plans'] if x['shot_id'] == sid)


# ------------------------------------------------------------------ synthetic asset set
def _png(arr, path):
    h, w = arr.shape[:2]
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', f'{w}x{h}', '-i', '-',
                    '-frames:v', '1', str(path)], input=arr.tobytes(), check=True)


def _tone(path, seconds, freq, level, sr=48000, noise=False):
    t = np.arange(int(seconds * sr)) / sr
    rng = np.random.default_rng(7)
    x = level * (rng.standard_normal(len(t)) if noise else np.sin(2 * np.pi * freq * t))
    a = np.stack([x, x], axis=1)
    fmt = ['-c:a', 'libmp3lame', '-b:a', '128k'] if str(path).endswith('.mp3') else ['-c:a', 'pcm_s24le']
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'f64le', '-ar', str(sr), '-ac', '2', '-i', '-', *fmt,
                    '-fflags', '+bitexact', '-map_metadata', '-1', str(path)], input=a.astype('<f8').tobytes(), check=True)


def build_synthetic(tmp):
    """Synthetic stand-ins for every asset the plan needs, re-pinned into a copy of the snapshot."""
    s = snap()
    d = Path(tmp) / 'assets'
    d.mkdir()
    yy, xx = np.mgrid[0:1086, 0:1448]
    rgba = lambda r, g, b: np.dstack([np.full((1086, 1448), v, np.uint8) for v in (r, g, b, 255)])
    bg = rgba(240, 230, 210)
    bg[..., 0] = (180 + (xx % 64)).astype(np.uint8)
    _png(bg, d / 'WORLD-EP005-BATHROOM-MASTER-v01.png')
    face = rgba(250, 250, 250)
    face[(xx - 1275) ** 2 + (yy - 345) ** 2 < 140 ** 2] = (170, 120, 70, 255)
    _png(face, d / 'CHAR-MIKKO-MASTER-v01.png')
    lumi = rgba(253, 253, 253)
    lumi[(xx - 156) ** 2 + (yy - 260) ** 2 < 100 ** 2] = (255, 236, 150, 255)
    _png(lumi, d / 'CHAR-LUMI-MASTER-v01.png')
    mirror = rgba(253, 253, 253)
    mirror[(xx - 540) ** 2 + (yy - 388) ** 2 < 300 ** 2] = (240, 120, 110, 255)
    mirror[(np.abs(xx - 540) < 60) & (yy > 600) & (yy < 980)] = (240, 120, 110, 255)
    mirror[(xx - 540) ** 2 + (yy - 388) ** 2 < 205 ** 2] = (215, 230, 245, 255)
    _png(mirror, d / 'PROP-EP005-HAND-MIRROR-v01.png')
    cloth = rgba(253, 253, 253)
    cloth[200:450, 60:450] = (110, 160, 220, 255)
    _png(cloth, d / 'PROP-EP005-CLEANING-CLOTH-v01.png')
    for i, aid in enumerate(BERRIES):
        ov = np.zeros((1086, 1448, 4), np.uint8)
        ov[400 + 20 * i:600, 500:900] = (200, 30, 60, 230)
        _png(ov, d / f'{aid}.png')
    _tone(d / 'AMB-BATHROOM-QUIET-v01.wav', 2.0, 0, 0.003, noise=True)     # shorter than the clip: exercises looping
    _tone(d / 'SFX-LUMI-CLUE-CHIME-v01.wav.mp3', 8.0, 880, 0.3)          # longer than S004: exercises trim policy
    files = {p.name: p for p in d.iterdir()}
    pins = {}
    for row in s['asset_registry']:
        base = Path(row['storage_path']).name
        stem = base.split('.')[0]
        match = [f for n, f in files.items() if n.split('.')[0] == stem]
        if not match:
            continue
        f = match[0]
        row['storage_path'] = 'production-assets/synthetic/' + f.name
        md = row.get('metadata_json') or {}
        if 'sha256' in md:
            md['sha256'] = sha256_file(f)
            row['metadata_json'] = md
        else:
            pins[row['asset_id']] = {'sha256': sha256_file(f), 'source': 'synthetic test pin'}
    sp = Path(tmp) / 'snapshot.json'
    sp.write_text(json.dumps(s))
    return s, sp, pins, d


SMALL = replace(load_output_spec(), width=480, height=270, x264_preset='ultrafast')


# ------------------------------------------------------------------ tests
class T01_ExactResolution(unittest.TestCase):
    def test_exact_ids(self):
        res = resolver()
        for aid in BERRIES + ['AMB-BATHROOM-QUIET-v01', 'SFX-LUMI-CLUE-CHIME', 'PROP-EP005-HAND-MIRROR-v01']:
            r = res.resolve(aid)
            self.assertEqual(r['asset_id'], aid)
            self.assertEqual(r['status'], 'APPROVED')
            self.assertEqual(len(r['expected_sha256']), 64)
        self.assertEqual(res.resolve('Lumi clue chime')['asset_id'], 'SFX-LUMI-CLUE-CHIME')

    def test_spec_uses_canonical_ids(self):
        sp = build_shot_spec(snap(), resolver(), 'S004', load_output_spec())
        self.assertEqual(sorted(p['asset_id'] for p in sp['props']),
                         ['PROP-EP005-CLEANING-CLOTH-v01', 'PROP-EP005-HAND-MIRROR-v01'])
        self.assertEqual(sorted(c['asset_id'] for c in sp['characters']), ['CHAR-LUMI-MASTER-v01', 'CHAR-MIKKO-MASTER-v01'])
        self.assertEqual(sp['environment']['asset_id'], 'WORLD-EP005-BATHROOM-MASTER-v01')
        self.assertEqual([x['asset_id'] for x in sp['named_sfx']], ['SFX-LUMI-CLUE-CHIME'])


class T02_HashMismatch(unittest.TestCase):
    def test_hash_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as t:
            f = Path(t) / 'x.bin'
            f.write_bytes(b'abc')
            with self.assertRaises(FailClosed) as e:
                verify_file(f, '0' * 64, 'X')
            self.assertEqual(e.exception.code, 'HASH_MISMATCH')

    def test_plan_rejects_tampered_asset(self):
        with tempfile.TemporaryDirectory() as t:
            s, sp, pins, d = build_synthetic(t)
            (d / 'PROP-EP005-HAND-MIRROR-v01.png').write_bytes(b'tampered')
            with self.assertRaises(FailClosed) as e:
                plan(s, pins, load_layout(), SMALL, RID, PMID, RUN, d)
            self.assertEqual(e.exception.code, 'HASH_MISMATCH')

    def test_pin_conflict(self):
        res = resolver(pins={'AMB-BATHROOM-QUIET-v01': {'sha256': 'f' * 64}})
        with self.assertRaises(FailClosed) as e:
            res.resolve('AMB-BATHROOM-QUIET-v01')
        self.assertEqual(e.exception.code, 'HASH_PIN_CONFLICT')

    def test_no_hash_anywhere(self):
        with self.assertRaises(FailClosed) as e:
            resolver(pins={}).resolve('SFX-LUMI-CLUE-CHIME')
        self.assertEqual(e.exception.code, 'NO_EXPECTED_HASH')


class T03_MissingAsset(unittest.TestCase):
    def test_missing_registry_row(self):
        s = snap()
        s['asset_registry'] = [r for r in s['asset_registry'] if r['asset_id'] != 'OVERLAY-EP005-BERRY-SMUDGE-NOSE-v01']
        with self.assertRaises(FailClosed) as e:
            resolver(s).resolve('OVERLAY-EP005-BERRY-SMUDGE-NOSE-v01')
        self.assertIn(e.exception.code, ('ASSET_NOT_IN_REGISTRY', 'UNMAPPED_REFERENCE'))

    def test_missing_local_file(self):
        with tempfile.TemporaryDirectory() as t:
            s, sp, pins, d = build_synthetic(t)
            (d / 'AMB-BATHROOM-QUIET-v01.wav').unlink()
            with self.assertRaises(FailClosed) as e:
                plan(s, pins, load_layout(), SMALL, RID, PMID, RUN, d)
            self.assertEqual(e.exception.code, 'ASSET_FILE_MISSING')

    def test_not_approved(self):
        s = snap()
        for r in s['asset_registry']:
            if r['asset_id'] == 'PROP-EP005-HAND-MIRROR-v01':
                r['status'] = 'REVIEW'
        with self.assertRaises(FailClosed) as e:
            resolver(s).resolve('TMP_EP005_HAND_MIRROR')
        self.assertEqual(e.exception.code, 'ASSET_NOT_APPROVED')


class T04_Ambiguity(unittest.TestCase):
    def test_duplicate_governed_row(self):
        s = snap()
        dup = copy.deepcopy(next(r for r in s['asset_registry'] if r['asset_id'] == 'AMB-BATHROOM-QUIET-v01'))
        dup['id'] = 'dup'
        s['asset_registry'].append(dup)
        with self.assertRaises(FailClosed) as e:
            resolver(s).resolve('AMB-BATHROOM-QUIET-v01')
        self.assertEqual(e.exception.code, 'AMBIGUOUS_REGISTRY_MATCH')

    def test_alias_collision(self):
        s = snap()
        other = next(r for r in s['asset_registry'] if r['asset_id'] == 'FOLEY-CLOTH-SOFT-v01')
        other['aliases'] = ['AMB BATHROOM QUIET v01']
        with self.assertRaises(FailClosed) as e:
            resolver(s).resolve('AMB-BATHROOM-QUIET-v01')
        self.assertEqual(e.exception.code, 'AMBIGUOUS_REGISTRY_MATCH')

    def test_reuse_map_conflict(self):
        s = snap()
        m = s['readiness_manifest']['readiness_manifest_json']['canonical_reuse_map']
        extra = copy.deepcopy(next(e for e in m if e['source_asset_id'] == 'TMP_EP005_HAND_MIRROR'))
        extra['canonical_asset_id'] = 'PROP-EP005-CLEANING-CLOTH-v01'
        m.append(extra)
        r = s['readiness_manifest']
        with self.assertRaises(FailClosed) as e:
            Resolver(r, s['asset_registry'], load_hash_pins(PINS))
        self.assertEqual(e.exception.code, 'REUSE_MAP_AMBIGUOUS')


class T05_StaleLabels(unittest.TestCase):
    def test_tmp_label_cannot_be_identity(self):
        res = resolver()
        with self.assertRaises(FailClosed) as e:
            res.registry_row('TMP_EP005_HAND_MIRROR')
        self.assertEqual(e.exception.code, 'STALE_LABEL_AS_IDENTITY')
        self.assertEqual(res.canonical_id('TMP_EP005_HAND_MIRROR'), 'PROP-EP005-HAND-MIRROR-v01')

    def test_planted_tmp_row_cannot_override_map(self):
        s = snap()
        fake = copy.deepcopy(next(r for r in s['asset_registry'] if r['asset_id'] == 'PROP-EP005-CLEANING-CLOTH-v01'))
        fake.update(id='fake', asset_id='TMP_EP005_HAND_MIRROR', asset_name='Tiny hand mirror (stale)', aliases=[])
        s['asset_registry'].append(fake)
        self.assertEqual(resolver(s).resolve('TMP_EP005_HAND_MIRROR')['asset_id'], 'PROP-EP005-HAND-MIRROR-v01')

    def test_unmapped_tmp_label_fails(self):
        with self.assertRaises(FailClosed) as e:
            resolver().canonical_id('TMP_EP005_UNKNOWN_PROP')
        self.assertEqual(e.exception.code, 'UNMAPPED_REFERENCE')

    def test_tbd_environment_and_audio_text_ignored(self):
        sp = build_shot_spec(snap(), resolver(), 'S005', load_output_spec())
        self.assertIn('TBD', sp['informational_stale_labels'])
        self.assertEqual(sp['environment']['asset_id'], 'WORLD-EP005-BATHROOM-MASTER-v01')
        self.assertEqual([a['asset_id'] for a in sp['mapped_audio']], ['AMB-BATHROOM-QUIET-v01'])

    def test_stale_readiness_flags_not_a_gate(self):
        s = snap()
        self.assertEqual(s['production_manifest']['manifest_json_reduced']['readiness_flags'], ['UNRESOLVED_TBDS'])
        validate_readiness(s, RID, PMID, RUN)   # passes: the approved readiness is authoritative


class T06_S004Overlays(unittest.TestCase):
    def test_overlay_set_matches_continuity(self):
        sp = build_shot_spec(snap(), resolver(), 'S004', load_output_spec())
        self.assertEqual(sorted(o['asset_id'] for o in sp['active_overlays']), BERRIES)
        sp5 = build_shot_spec(snap(), resolver(), 'S005', load_output_spec())
        self.assertTrue(validate_continuity(sp, sp5))

    def test_transition_unsupported(self):
        s = snap()
        for t in shot(s, 'S004')['shot_plan']['continuity_state']['tracked_elements']:
            if t['element'].endswith('nose'):
                t['visible_at_end'] = False
        with self.assertRaises(FailClosed) as e:
            build_shot_spec(s, resolver(s), 'S004', load_output_spec())
        self.assertEqual(e.exception.code, 'OVERLAY_TRANSITION_UNSUPPORTED_V01')

    def test_contract_without_visible_element(self):
        s = snap()
        for t in shot(s, 'S004')['shot_plan']['continuity_state']['tracked_elements']:
            if t['element'].endswith('nose'):
                t['visible_at_start'] = t['visible_at_end'] = False
        with self.assertRaises(FailClosed) as e:
            build_shot_spec(s, resolver(s), 'S004', load_output_spec())
        self.assertEqual(e.exception.code, 'OVERLAY_CONTRACT_FOR_INVISIBLE_ELEMENT')


class T07_Glint(unittest.TestCase):
    G = 'TREATMENT-EP005-MIRROR-GLINT-v01'

    def test_bounds(self):
        for n in range(6, 11):
            self.assertTrue(validate_window(self.G, 12, n, 120))
        for n in (5, 11):
            with self.assertRaises(FailClosed):
                validate_window(self.G, 12, n, 120)
        with self.assertRaises(FailClosed) as e:
            validate_window(self.G, 115, 8, 120)
        self.assertEqual(e.exception.code, 'TREATMENT_CROSSES_SHOT_BOUNDARY')

    def test_layout_glint_ends_before_s005(self):
        g = load_layout()['timing']['S004']['glint']
        sp = build_shot_spec(snap(), resolver(), 'S004', load_output_spec())
        self.assertTrue(6 <= g['frames'] <= 10)
        self.assertLessEqual(g['start_frame'] + g['frames'], sp['frames'])

    def test_completion_pop_bounds(self):
        validate_window('TREATMENT-EP005-COMPLETION-POP-ACCENT-v01', 0, 7, 96)
        with self.assertRaises(FailClosed):
            validate_window('TREATMENT-EP005-COMPLETION-POP-ACCENT-v01', 0, 9, 96)


class T11_S025CleanReveal(unittest.TestCase):
    def test_s025_has_zero_overlays(self):
        sp = build_shot_spec(snap(), resolver(), 'S025', load_output_spec())
        self.assertTrue(sp['clean_reveal'])
        self.assertEqual(sp['active_overlays'], [])

    def test_s025_with_berry_fails(self):
        s = snap()
        p = shot(s, 'S025')['shot_plan']
        for t in p['continuity_state']['tracked_elements']:
            if t['element'].endswith('nose'):
                t['visible_at_start'] = t['visible_at_end'] = True
        p['overlay_vfx_requirements'].append({'element': "Berry smudge on Mikko's nose",
                                              'asset_id': 'OVERLAY-EP005-BERRY-SMUDGE-NOSE-v01'})
        # Also map the nose overlay to S025 so the reuse-map cross-check passes and the clean-reveal rule decides.
        rj = s['readiness_manifest']['readiness_manifest_json']
        for e in rj['canonical_reuse_map']:
            if e['canonical_asset_id'] == 'OVERLAY-EP005-BERRY-SMUDGE-NOSE-v01':
                e['affected_shots'].append('S025')
        res = Resolver(s['readiness_manifest'], s['asset_registry'], load_hash_pins(PINS))
        with self.assertRaises(FailClosed) as e:
            build_shot_spec(s, res, 'S025', load_output_spec())
        self.assertEqual(e.exception.code, 'CLEAN_REVEAL_HAS_ACTIVE_OVERLAYS')


class ReadinessGate(unittest.TestCase):
    def test_legacy_denied(self):
        for lid in LEGACY_DENYLIST:
            with self.assertRaises(FailClosed) as e:
                validate_readiness(snap(), lid)
            self.assertEqual(e.exception.code, 'LEGACY_READINESS_DENIED')

    def test_requires_explicit_id(self):
        with self.assertRaises(FailClosed) as e:
            validate_readiness(snap(), None)
        self.assertEqual(e.exception.code, 'READINESS_ID_REQUIRED')

    def test_status_and_state(self):
        for field, value, code in (('status', 'REVIEW', 'READINESS_NOT_APPROVED'),
                                   ('readiness_state', 'NEEDS_ASSET_CREATION', 'READINESS_STATE_INCOMPATIBLE'),
                                   ('human_review_count', 1, 'READINESS_HAS_UNRESOLVED')):
            s = snap()
            s['readiness_manifest'][field] = value
            with self.assertRaises(FailClosed) as e:
                validate_readiness(s, RID)
            self.assertEqual(e.exception.code, code)

    def test_wrong_production_manifest_or_run(self):
        with self.assertRaises(FailClosed):
            validate_readiness(snap(), RID, '96df250f-7182-4d5f-a556-b0448e518375')
        with self.assertRaises(FailClosed):
            validate_readiness(snap(), RID, PMID, 'A006-0')


class AudioAndInterfaces(unittest.TestCase):
    def test_protected_hold_rejects_events(self):
        s = snap()
        shot(s, 'S005')['shot_plan']['audio_plan']['named_audio_assets'] = ['Lumi clue chime']
        with self.assertRaises(FailClosed):
            build_shot_spec(s, resolver(s), 'S005', load_output_spec())

    def test_sfx_overrun_fails_without_policy(self):
        with tempfile.TemporaryDirectory() as t:
            s, sp, pins, d = build_synthetic(t)
            lay = load_layout()
            lay['timing']['S004']['clue_chime']['overrun_policy'] = 'FAIL'
            p = plan(s, pins, lay, SMALL, RID, PMID, RUN, d)
            with self.assertRaises(FailClosed) as e:
                mix(p['inputs'], lay, SMALL, p['timeline'])
            self.assertEqual(e.exception.code, 'SFX_OVERRUNS_SHOT_BOUNDARY')

    def test_captions_and_dialogue_interfaces(self):
        slots = [{'shot_id': 'S004', 'speaker': 'Lumi', 'text': 'A little glint! Look at his cheek.'}]
        with self.assertRaises(FailClosed):
            to_srt(timed_text_from_slots(slots))
        cues = timed_text_from_slots(slots, {0: (0.6, 2.4)})
        self.assertIn('00:00:00,600 --> 00:00:02,400', to_srt(cues))
        self.assertTrue(to_webvtt(cues).startswith('WEBVTT'))
        with self.assertRaises(FailClosed):
            dialogue_track('S004', 'Lumi', None, None, 0, 1)
        self.assertEqual(dialogue_track('S004', 'Lumi', 'VO-X', 'p.wav', 0.5, 2.0, -3)['gain_db'], -3.0)


class RenderPipeline(unittest.TestCase):
    """T-08, T-09, T-10, T-12 on a synthetic asset set (no production assets, no network)."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.s, cls.sp, cls.pins, cls.d = build_synthetic(cls.tmp)
        cls.lay = load_layout()
        lp = PKG / 'layouts' / 'ep005_s004_s005_standin_v1.json'
        cls.out = [Path(cls.tmp) / f'out{i}' for i in (1, 2)]
        cls.prov = [run(cls.s, cls.sp, cls.pins, cls.lay, lp, SMALL, IDS, cls.d, o) for o in cls.out]
        cls.report = verify(cls.out[0])

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_T08_s005_hold_unchanged(self):
        self.assertTrue(self.report['s005_hold_raw_identical_and_equal_to_last_s004_frame'])
        self.assertEqual(self.report['s005_hold_frames'], [120, 215])
        hashes = (self.out[0] / 'raw_frame_sha256.txt').read_text().split('\n')
        h = [x.split()[1] for x in hashes if x]
        h[150] = 'x'
        with self.assertRaises(FailClosed):
            check_hold(h, 120, 216)

    def test_T09_ambience_covers_clip(self):
        self.assertEqual(self.report['mix_master']['silent_windows_below_floor'], 0)
        self.assertEqual(self.report['mix_master']['samples'], 9 * 48000)
        with tempfile.TemporaryDirectory() as t:
            a = np.full((48000, 2), 0.01)
            a[20000:21000] = 0.0
            w = Path(t) / 'gap.wav'
            media.write_wav24(a, 48000, w)
            self.assertGreater(audio_report(w, 48000, [], 1.0)['silent_windows_below_floor'], 0)

    def test_T10_no_clipping(self):
        self.assertLessEqual(self.report['mix_master']['peak_dbfs'], SMALL.peak_ceiling_dbfs)
        self.assertLess(self.report['review_aac_peak_dbfs'], 0.0)
        lay = copy.deepcopy(self.lay)
        lay['timing']['S004']['clue_chime']['gain_db'] = 30.0
        p = plan(self.s, self.pins, lay, SMALL, RID, PMID, RUN, self.d)
        with self.assertRaises(FailClosed) as e:
            mix(p['inputs'], lay, SMALL, p['timeline'])
        self.assertEqual(e.exception.code, 'AUDIO_PEAK_EXCEEDS_CEILING')

    def test_T12_deterministic(self):
        a, b = self.prov
        self.assertEqual(a['outputs']['review_mp4']['sha256'], b['outputs']['review_mp4']['sha256'])
        self.assertEqual(a['outputs']['mix_wav']['sha256'], b['outputs']['mix_wav']['sha256'])
        self.assertEqual(a['raw_frames']['sha256_of_frame_hash_list'], b['raw_frames']['sha256_of_frame_hash_list'])
        self.assertEqual(a['deterministic_core_sha256'], b['deterministic_core_sha256'])

    def test_outputs_are_review_and_labelled(self):
        p = self.prov[0]
        self.assertEqual(p['status'], 'REVIEW')
        self.assertFalse(p['human_approval']['approved'])
        self.assertIn('NON_CANON_TECHNICAL_STANDIN', p['labels'])
        self.assertEqual(p['safety']['provider_calls'], 0)
        self.assertEqual(p['overlays_drawn'], BERRIES)
        chime = next(c for c in p['audio_cues'] if c['asset_id'] == 'SFX-LUMI-CLUE-CHIME')
        self.assertLessEqual(chime['clip_end_seconds'], 5.0)
        self.assertEqual(chime['trim']['policy'], 'TRIM_WITH_FADE')


if __name__ == '__main__':
    unittest.main()
