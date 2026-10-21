"""EP005 Batch 1 motion replacements v04: S013 + S019, Kling 3.0 Turbo i2v 720p, ONE call each (Gilang USD 1.00 authorisation).

Usage (repo root):
  python3 evidence/ep005/batch1_motion_v04/b1_motion_v04.py prepare <work dir>
  python3 evidence/ep005/batch1_motion_v04/b1_motion_v04.py run <SID> <work dir> <lock commit>
  python3 evidence/ep005/batch1_motion_v04/b1_motion_v04.py poll|sample <SID> <work dir>
  python3 evidence/ep005/batch1_motion_v04/b1_motion_v04.py assemble <SID> <work dir> <label>
Reuses the v03 mechanics (b1_motion_v03: same route, model, resolution, governed assembly, ambience +11.5 dB) with a
separate ledger/package, a USD 1.00 ceiling and a 2-call cap. Start images = the exact v03 start images (the approved
composed frames, re-verified by SHA from the provider copy). Prompts = the v03 motion translations + the Company Brain
hard negatives for the defect each v03/raw result showed.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE.parent / 'batch1_motion'))
import b1_motion_v03 as M  # noqa: E402
from agent008.motion.authorisation import AttemptLedger  # noqa: E402

M.LEDGER = AttemptLedger(HERE / 'B1_MOTION_V04_LEDGER_v1.jsonl')
M.PKG = HERE / 'B1_MOTION_V04_PACKAGES_v1.json'
M.CEILING_USD = 1.00
M.scope = lambda sid: f'EP005-B1V4-MOTION-{sid}'
V03_PKG = HERE.parent / 'batch1_motion' / 'B1_MOTION_V03_PACKAGES_v1.json'
ORDER = ['S013', 'S019']
PROMPTS = {
    'S013': ("Gentle, restrained children's cartoon animation. Mikko calmly studies the two remaining berry smudges in the hand "
             'mirror: in the mirror his face blinks once naturally and his eyes move slowly from the smudge on his nose to the '
             'smudge beside his mouth, with very small breathing and head movement. In the foreground Mikko stays turned away from '
             'the camera: only the back and side of his furry head and his shoulder are visible, moving only gently with his '
             'breathing; his real face never turns toward the camera. Lumi hovers gently and keeps the mirror steady. Exactly two '
             'berry smudges exist for the whole shot, both in the reflection: one on his nose and one beside his mouth. No new red '
             'mark, stain, berry mark or blush patch appears anywhere, on the foreground Mikko or in the reflection, and no smudge '
             'appears, disappears, duplicates, moves, changes colour or changes side. ' + M.COMMON),
    'S019': ("Gentle, restrained children's cartoon animation. Close-up of the pink flower-shaped hand mirror. Mikko's reflected "
             'face shows restrained natural life: a soft blink, subtle breathing and a tiny reaction in his eyes as he notices the '
             'berry smudge on his nose, which stays fixed. Exactly one hand is visible for the whole shot: Lumi\'s small round '
             'golden-white glowing hand that already holds the bottom of the mirror handle; it stays where it is, moving only a '
             'tiny amount to steady the mirror. No second hand, no human hand, no glove, no furry paw, no sleeve, no arm and no '
             'other character ever enters the frame; nothing reaches toward the mirror. The mirror stays stable and readable and '
             'keeps its exact shape. ' + M.COMMON),
}


def locked(sid, lock_commit):
    want = M.subprocess.run(['git', 'show', f'{lock_commit}:evidence/ep005/batch1_motion_v04/{M.PKG.name}'], cwd=ROOT,
                            capture_output=True, check=True).stdout
    if M.PKG.read_bytes() != want:
        raise SystemExit('STOP: package file differs from the lock commit')
    p = json.loads(want)['packages'][sid]
    if M.sha(p['PROMPT_TEXT'].encode()) != p['PROMPT_SHA256'] or M.body_sha(p['REQUEST_BODY']) != p['REQUEST_BODY_SHA256']:
        raise SystemExit(f'STOP {sid}: locked hashes do not verify')
    return p


M.locked = locked


def prepare(work):
    v03 = json.loads(V03_PKG.read_text())['packages']
    pk = {'authorisation': {'by': 'Gilang / Company Brain', 'date': '2026-10-21', 'max_total_spend_usd': 1.00, 'shots': ORDER,
                            'calls_max_per_shot': 1, 'total_calls_max': 2, 'retries': 0, 'alternate_candidates': 0,
                            'fallback_model': 'NONE', 'model': M.MODEL, 'resolution': M.RESOLUTION,
                            'replaces': {'S013': 'SHOT-EP005-S013-ASSEMBLED-CAND-v03 (REJECTED: new red mark on foreground Mikko)',
                                         'S019': 'MOTION-EP005-S019-KLING30T-CAND-v01 (REJECTED / CANON_FAIL: extra gloved hand)'}},
          'endpoint': 'POST https://api.higgsfield.ai' + M.ROUTE, 'packages': {}}
    for sid in ORDER:
        old = v03[sid]
        url, want = old['REQUEST_BODY']['image_url'], old['start_image']['sha256']
        g = M.http.send('GET', url, {}, None, 120.0)
        if g.status != 200 or M.sha(g.body) != want:
            raise SystemExit(f'STOP {sid}: start image copy not readable at the approved SHA')
        body = {'prompt': PROMPTS[sid], 'image_url': url, 'duration': old['duration_s'], 'resolution': M.RESOLUTION}
        pk['packages'][sid] = {'SHOT_ID': sid, 'PROMPT_TEXT': PROMPTS[sid], 'PROMPT_SHA256': M.sha(PROMPTS[sid].encode()),
                               'REQUEST_BODY': body, 'REQUEST_BODY_SHA256': M.body_sha(body), 'START_IMAGE_SHA': want,
                               'MODEL': M.MODEL, 'RESOLUTION': M.RESOLUTION, 'DURATION': old['duration_s'],
                               'start_image': old['start_image'], 'duration_s': old['duration_s'],
                               'frames_required': old['frames_required'], 'start_image_readback': 'SHA256_MATCH', 'submitted': False}
        print(sid, pk['packages'][sid]['PROMPT_SHA256'], pk['packages'][sid]['REQUEST_BODY_SHA256'], want[:16])
    M.PKG.write_text(json.dumps(pk, indent=1, ensure_ascii=False) + '\n')


def run(sid, work, lock):
    calls = [json.loads(x) for x in M.LEDGER.path.read_text().splitlines() if x.strip()] if M.LEDGER.path.exists() else []
    if sum(1 for c in calls if c['event'] == 'GENERATION_RESERVED') >= 2:
        raise SystemExit('STOP: TOTAL_NEW_CALLS_MAX (2) reached')
    M.run(sid, work, lock)


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'prepare':
        prepare(sys.argv[2])
    elif cmd == 'run':
        run(sys.argv[2], sys.argv[3], sys.argv[4])
    elif cmd == 'poll':
        M.retrieve(sys.argv[2], sys.argv[3], M.poll(sys.argv[2]))
    elif cmd == 'sample':
        print(M.sample(sys.argv[2], sys.argv[3]))
    elif cmd == 'assemble':
        M.assemble(sys.argv[2], sys.argv[3], sys.argv[4])
