"""Phase-0 renderer: verified inputs -> deterministic frames + mix -> REVIEW clip + provenance."""
import json
from pathlib import Path

import numpy as np

from . import AGENT_NAME, AGENT_VERSION
from . import compositor as C
from . import media, standin, treatments
from .errors import FailClosed
from .hashing import canonical_sha256, sha256_bytes, sha256_file, verify_file
from .inputs import validate_readiness
from .resolve import Resolver
from .spec import build_shot_spec, validate_continuity
from .timeline import build_timeline

LABELS = ['NON_CANON_TECHNICAL_STANDIN', 'REVIEW_ONLY', 'NOT_FOR_EPISODE_PUBLICATION']


def db_to_gain(db):
    return 10.0 ** (db / 20.0)


def smoothstep(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


# ---------------------------------------------------------------- planning
def plan(snapshot, hash_pins, layout, spec, readiness_manifest_id, production_manifest_id, agent006_run_id, asset_dir):
    r = validate_readiness(snapshot, readiness_manifest_id, production_manifest_id, agent006_run_id)
    res = Resolver(r, snapshot['asset_registry'], hash_pins)
    shots = snapshot['render_shots']
    specs = [build_shot_spec(snapshot, res, s, spec) for s in shots]
    for a, b in zip(specs, specs[1:]):
        validate_continuity(a, b)
    for v in snapshot.get('validator_only_shots') or []:
        build_shot_spec(snapshot, res, v, spec)   # e.g. S025 clean-reveal rule; never rendered here

    timing = layout['timing']
    # Every asset the stand-in or the mix uses must resolve through the spec or the canonical map.
    needed = {}
    for sp in specs:
        for group in ('active_overlays', 'props', 'characters', 'named_sfx', 'mapped_audio'):
            for a in sp[group]:
                needed[a['asset_id']] = a
        needed[sp['environment']['asset_id']] = sp['environment']
    bed = timing['ambience_bed']
    bed_res = res.resolve(bed['asset_id'])
    needed.setdefault(bed_res['asset_id'], bed_res)
    for key in ('background', 'cloth', 'mirror', 'lumi'):
        if layout[key]['asset_id'] not in needed:
            raise FailClosed('STANDIN_USES_UNCONTRACTED_ASSET', layout[key]['asset_id'])
    if layout['reflection']['character_asset_id'] not in needed:
        raise FailClosed('STANDIN_USES_UNCONTRACTED_ASSET', layout['reflection']['character_asset_id'])

    inputs = {}
    for aid, a in sorted(needed.items()):
        local = Path(asset_dir) / Path(a['object_key']).name
        actual = verify_file(local, a['expected_sha256'], aid)
        inputs[aid] = {**{k: a[k] for k in ('asset_id', 'registry_row_id', 'status', 'asset_type', 'storage_path',
                                            'expected_sha256', 'sha256_source')},
                       'verified_sha256': actual, 'bytes': local.stat().st_size, 'local_path': str(local)}

    s004 = next(sp for sp in specs if sp['shot_id'] == 'S004')
    s005 = next(sp for sp in specs if sp['shot_id'] == 'S005')
    g = timing['S004']['glint']
    if [t['treatment_id'] for t in s004['treatments']] != [g['treatment_id']]:
        raise FailClosed('TIMING_TREATMENT_MISMATCH', 'S004 timing must cover exactly the assigned treatments')
    treatments.validate_window(g['treatment_id'], g['start_frame'], g['frames'], s004['frames'])
    if s005['treatments']:
        raise FailClosed('UNEXPECTED_TREATMENT', 'S005')
    chime = timing['S004']['clue_chime']
    if [x['asset_id'] for x in s004['named_sfx']] != [chime['asset_id']]:
        raise FailClosed('TIMING_SFX_MISMATCH', 'S004')
    if chime['start_frame'] != g['start_frame']:
        raise FailClosed('CHIME_NOT_SYNCED_TO_GLINT')
    if timing['S005'].get('visual_source') != 'HOLD_LAST_FRAME_OF_S004':
        raise FailClosed('S005_VISUAL_SOURCE_UNSUPPORTED')
    return {'readiness': r, 'resolver': res, 'specs': specs, 'inputs': inputs,
            'timeline': build_timeline(specs, spec, timing)}


# ---------------------------------------------------------------- video
def frames(stack, layout, spec, specs):
    """Yield uint8 RGB frames for the clip. S005 repeats S004's final frame byte-for-byte."""
    t4 = layout['timing']['S004']
    tilt, g = t4['mirror_tilt'], t4['glint']
    env = treatments.envelope(treatments.treatment(g['treatment_id'])['envelope'], g['frames'])
    sprite = C.glint_sprite(max(4, int(round(g['size'] * stack['scale']))))
    gx, gy = stack['reflection_to_group'](g['center_in_reflection_unflipped'])
    s004 = next(sp for sp in specs if sp['shot_id'] == 'S004')
    n4 = s004['frames']

    def compose(angle, glint_alpha):
        grp = stack['group']
        if glint_alpha > 0:
            grp = C.over(grp, sprite, int(round(gx - sprite.shape[1] / 2)), int(round(gy - sprite.shape[0] / 2)),
                         opacity=glint_alpha)
        grp = C.rotate(grp, angle, *stack['pivot'])
        out = C.over(stack['under'], grp, *stack['group_pos'])
        for layer, x, y in stack['over']:
            out = C.over(out, layer, x, y)
        return C.to_rgb_u8(out)

    cache = {}
    last = None
    for n in range(n4):
        k = (n - tilt['start_frame']) / max(tilt['frames'] - 1, 1)
        angle = round(tilt['to_degrees'] * smoothstep(k), 9) if n >= tilt['start_frame'] else 0.0
        gi = n - g['start_frame']
        ga = env[gi] if 0 <= gi < g['frames'] else 0.0
        key = (angle, ga)
        if key not in cache:
            cache = {key: compose(angle, ga)}   # keep only the latest (static runs reuse it)
        last = cache[key]
        yield last
    s005 = next(sp for sp in specs if sp['shot_id'] == 'S005')
    for _ in range(s005['frames']):
        yield last


# ---------------------------------------------------------------- audio
def mix(inputs, layout, spec, timeline):
    sr, ch = spec.audio_sample_rate, spec.audio_channels
    total = int(round(timeline['total_seconds'] * sr))
    if total * spec.fps != timeline['total_frames'] * sr:
        raise FailClosed('AUDIO_VIDEO_LENGTH_MISMATCH')
    bed = layout['timing']['ambience_bed']
    amb = media.load_audio(inputs[bed['asset_id']]['local_path'], sr, ch)
    off = int(round(bed['source_offset_seconds'] * sr))
    reps = int(np.ceil((off + total) / len(amb)))
    amb_ext = np.tile(amb, (reps, 1))[off:off + total] * db_to_gain(bed['gain_db'])   # loop-safe master
    fade = int(round(bed['edge_fade_seconds'] * sr))
    ramp = np.linspace(0.0, 1.0, fade, endpoint=False)[:, None]
    amb_ext[:fade] *= ramp
    amb_ext[-fade:] *= ramp[::-1]
    out = amb_ext.copy()

    c = layout['timing']['S004']['clue_chime']
    shot = next(s for s in timeline['shots'] if s['shot_id'] == 'S004')
    chime = media.load_audio(inputs[c['asset_id']]['local_path'], sr, ch) * db_to_gain(c['gain_db'])
    start = int(round((shot['start_frame'] + c['start_frame']) / spec.fps * sr))
    boundary = int(round((shot['start_frame'] + shot['frames'] - c['end_guard_frames']) / spec.fps * sr))
    natural_end = start + len(chime)
    trim = None
    if natural_end > boundary:
        if c['overrun_policy'] != 'TRIM_WITH_FADE':
            raise FailClosed('SFX_OVERRUNS_SHOT_BOUNDARY',
                             f"{c['asset_id']} ends {natural_end / sr:.3f}s, boundary {boundary / sr:.3f}s")
        keep = boundary - start
        f = int(round(c['fade_out_seconds'] * sr))
        chime = chime[:keep].copy()
        chime[-f:] *= np.linspace(1.0, 0.0, f)[:, None]
        trim = {'natural_seconds': round(natural_end / sr - start / sr, 6), 'kept_seconds': round(keep / sr, 6),
                'fade_out_seconds': c['fade_out_seconds'], 'policy': 'TRIM_WITH_FADE'}
    out[start:start + len(chime)] += chime
    cues = [{'asset_id': c['asset_id'], 'clip_start_seconds': start / sr, 'clip_end_seconds': (start + len(chime)) / sr,
             'gain_db': c['gain_db'], 'trim': trim},
            {'asset_id': bed['asset_id'], 'clip_start_seconds': 0.0, 'clip_end_seconds': total / sr,
             'gain_db': bed['gain_db'], 'policy': bed['policy'], 'source_offset_seconds': bed['source_offset_seconds']}]
    peak = float(np.max(np.abs(out)))
    peak_db = 20 * np.log10(peak) if peak > 0 else -np.inf
    if peak_db > spec.peak_ceiling_dbfs:
        raise FailClosed('AUDIO_PEAK_EXCEEDS_CEILING', f'{peak_db:.2f} dBFS > {spec.peak_ceiling_dbfs}')
    return out, cues, round(peak_db, 3)


# ---------------------------------------------------------------- run
def run(snapshot, snapshot_path, hash_pins, layout, layout_path, spec, ids, asset_dir, out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    p = plan(snapshot, hash_pins, layout, spec, ids['readiness_manifest_id'], ids['production_manifest_id'],
             ids['agent006_run_id'], asset_dir)
    paths = {aid: v['local_path'] for aid, v in p['inputs'].items()}
    active = {o['asset_id'] for sp in p['specs'] for o in sp['active_overlays']}
    stack_paths = {aid: pth for aid, pth in paths.items()
                   if not aid.startswith('OVERLAY-') or aid in active}
    stack = standin.build(stack_paths, layout, spec)
    if sorted(stack['overlays_drawn']) != sorted(active):
        raise FailClosed('OVERLAY_SET_MISMATCH', f"drawn {stack['overlays_drawn']} vs contract {sorted(active)}")

    audio, cues, peak_db = mix(p['inputs'], layout, spec, p['timeline'])
    wav = out_dir / 'A008_EP005_S004_S005_PHASE0_MIX.wav'
    media.write_wav24(audio, spec.audio_sample_rate, wav)

    frame_hashes = []

    def tap():
        for fr in frames(stack, layout, spec, p['specs']):
            frame_hashes.append(sha256_bytes(fr.tobytes()))
            yield fr

    mp4 = out_dir / 'A008_EP005_S004_S005_PHASE0_REVIEW.mp4'
    cmd = media.encode_review(tap(), p['timeline']['total_frames'], spec, wav, mp4)
    if len(frame_hashes) != p['timeline']['total_frames']:
        raise FailClosed('FRAME_COUNT_MISMATCH', f"{len(frame_hashes)} vs {p['timeline']['total_frames']}")
    (out_dir / 'raw_frame_sha256.txt').write_text('\n'.join(f'{i:04d} {h}' for i, h in enumerate(frame_hashes)) + '\n')

    prov = provenance(p, spec, layout, layout_path, snapshot, snapshot_path, ids, stack, cues, peak_db,
                      frame_hashes, wav, mp4, cmd)
    (out_dir / 'A008_EP005_S004_S005_PHASE0_PROVENANCE.json').write_text(json.dumps(prov, indent=1, sort_keys=True) + '\n')
    return prov


REPO_ROOT = Path(__file__).resolve().parents[1]


def _rel(path):
    p = Path(path).resolve()
    try:
        return str(p.relative_to(REPO_ROOT))
    except ValueError:
        return p.name


def code_fingerprint():
    files = sorted(Path(__file__).resolve().parent.glob('*.py'))
    per = {f.name: sha256_file(f) for f in files}
    return {'modules': per, 'sha256_of_module_hashes': sha256_bytes(json.dumps(per, sort_keys=True).encode())}


def provenance(p, spec, layout, layout_path, snapshot, snapshot_path, ids, stack, cues, peak_db,
               frame_hashes, wav, mp4, cmd):
    mp4_probe = media.probe(mp4)
    core = {
        'agent': AGENT_NAME, 'agent_version': AGENT_VERSION,
        'status': 'REVIEW', 'labels': LABELS,
        'human_approval': {'required': True, 'approved': False, 'approve_by': 'exact output sha256 of the review mp4'},
        'authority_inputs': {
            **ids,
            'production_manifest_canonical_sha256': snapshot['production_manifest']['manifest_json_canonical_sha256'],
            'readiness_manifest_json_canonical_sha256': snapshot['readiness_manifest_json_canonical_sha256'],
            'asset_registry_canonical_sha256': snapshot['asset_registry_canonical_sha256'],
            'input_snapshot_file': _rel(snapshot_path), 'input_snapshot_sha256': sha256_file(snapshot_path),
        },
        'output_spec': spec.to_dict(),
        'layout': {'file': _rel(layout_path), 'sha256': sha256_file(layout_path), 'layout_id': layout['layout_id'],
                   'classification': layout['classification']},
        'input_assets': {aid: {k: v for k, v in a.items() if k != 'local_path'} for aid, a in p['inputs'].items()},
        'shot_specs': [{k: v for k, v in sp.items()} for sp in p['specs']],
        'timeline': p['timeline'],
        'audio_cues': cues, 'mix_peak_dbfs': peak_db,
        'overlays_drawn': sorted(stack['overlays_drawn']),
        'banner_font_sha256': stack['font_sha256'],
        'raw_frames': {'count': len(frame_hashes), 'format': f'rgb24 {spec.width}x{spec.height}',
                       'sha256_of_frame_hash_list': sha256_bytes('\n'.join(frame_hashes).encode()),
                       'first': frame_hashes[0], 'last': frame_hashes[-1]},
        'outputs': {
            'review_mp4': {'file': mp4.name, 'sha256': sha256_file(mp4), 'bytes': mp4.stat().st_size,
                           'streams': [{k: s.get(k) for k in ('codec_name', 'pix_fmt', 'width', 'height',
                                                              'r_frame_rate', 'nb_frames', 'sample_rate', 'channels',
                                                              'duration')} for s in mp4_probe['streams']]},
            'mix_wav': {'file': wav.name, 'sha256': sha256_file(wav), 'bytes': wav.stat().st_size,
                        'format': 'pcm_s24le 48 kHz stereo'},
        },
        'recipes': {'encode_command': [c if not c.startswith('/') else '<OUT>/' + Path(c).name for c in cmd]},
        'toolchain': media.toolchain(),
        'code': code_fingerprint(),
        'safety': {'provider_calls': 0, 'paid_calls': 0, 'network_writes': 0, 'llm_calls': 0,
                   'registry_writes': 0, 'storage_writes': 0, 'registered_as_asset': False},
    }
    core['deterministic_core_sha256'] = canonical_sha256(core)
    return core
