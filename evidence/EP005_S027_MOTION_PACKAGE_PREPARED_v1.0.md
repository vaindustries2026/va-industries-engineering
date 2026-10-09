# EP005 S027: Seedance 2.0 motion package prepared (zero spend)

Date: 2026-10-09 (UTC). Mikko & Lumi only.
**Result: EP005_S027_MOTION_PACKAGE_READY_FOR_HUMAN_APPROVAL.**
**GENERATION_AUTHORISED = FALSE.**

## 1. Source frame verification (before anything else)
| Check | Result |
|---|---|
| Registry row `d2a07b22-cf25-42ff-b86a-c4080ff24bc2` | `FRAME-EP005-S027-BASE-v01`, status **APPROVED**, SHOT_FRAME / BASE_FRAME (unchanged since insert) |
| Stored bytes | Read from `production-assets/visual/production/ep005/frames/FRAME-EP005-S027-BASE-v01.png`: HTTP 200, 4,746,496 bytes |
| Recomputed SHA-256 | `81b841a6ab53219b26755c4e83a9777953a2d03f37213875e38691c112f0061b`, **equal to the approved hash** |

The frame was not modified. Nothing was written to storage or the registry.

## 2. Package
- **Job file:** `agent008/motion/jobs/ep005_s027_motion_smoke_v2.json`.
  - This is a new file. v1 is kept for history; v2 supersedes its prompt and negative constraints.
- **Locked settings:**
  - provider: `higgsfield`
  - model: **`bytedance/seedance-2.0/image-to-video`**, locked for this attempt, with no fallback
  - duration: 5 s
  - resolution: 1080p
  - generate_audio: false
  - maximum_attempts: 1, automatic retries: 0
- **Source upload:** source_upload_required = true, and source_public_url = `NOT_YET_ASSIGNED`.
- **Future request body:** `{prompt, image_url, duration: 5, resolution: "1080p", generate_audio: false}`. Its SHA-256 can only be frozen once `image_url` exists.
- **Future sequence**, each step needing its own authorisation:
  1. Read the approved bytes and check their SHA-256.
  2. Authorised Higgsfield upload (`/files/generate-upload-url` + PUT).
  3. Record the public HTTPS URL.
  4. Read the file back and check its SHA-256 again.
  5. Freeze the request body.
  6. Get a human spend authorisation bound to that body, with max 1 generation.
  7. Send a single POST, with no retry.

## 3. Final motion prompt
**SHA-256 `ab7f92afa5d7a8bde2efc621eb86ebe249614762b66e15576ec0b5d9c3f4cab3`**, 1,759 characters, UTF-8.

The exact bytes are in `evidence/agent008/phase1/s027_v2/S027_MOTION_PROMPT_v2.txt`. That file has no trailing newline, so the file SHA-256 equals the prompt SHA-256.

```text
Animate this exact starting image as a calm, gentle preschool moment. The starting frame stays visually dominant: keep the image as it is and add only small, soft movement.

Mikko, the bear on the left, keeps his gentle, satisfied smile. He makes one small, natural, satisfied shoulder lift and then settles back, relaxed and proud. His head may move only very slightly, like soft breathing. He keeps the blue cleaning cloth held securely in his hand, where it is now. He does not wipe his face, does not move the cloth toward his face, does not walk, does not talk and does not change his pose.

Lumi, the glowing orb on the right, keeps her warm, happy expression. She floats in place with a very gentle, buoyant bob, and may give one tiny pleased lift of her body. She keeps holding the pink flower mirror steady and clearly visible in her hand. She does not fly around the bathroom, does not talk and does not change her pose.

The camera is completely locked: no pan, no tilt, no zoom, no dolly, no orbit, no reframing and no cuts. The bathroom stays exactly the same: no background changes, no moving fixtures, no new objects and no environmental effects.

Preserve Mikko's and Lumi's exact identities, clothing and colours from the starting image. Mikko's face stays clean, with zero berry marks or smudges. Keep exactly one cleaning cloth and exactly one pink flower mirror; do not duplicate either prop. Do not create extra limbs, fingers, hands, faces or characters. Do not morph the characters, change Mikko's fur colour, change Lumi's round orb shape, resize Lumi, or change costumes. No text or logos. No mirror reflection event, no mirror glint, no berry-removal action, no magical effects and no sparkles. No lip-sync, no dialogue and no audio.
```

- Seedance 2.0 has no negative-prompt field. All 26 required preservation and prohibition constraints are therefore written into the prompt itself, and so are covered by its SHA-256. The package's `negative_constraints` field is intentionally empty and is not sent.
- The prompt is written for motion. It does not re-describe the still image; it relies on the approved frame for identity.

## 4. Expected cost (calculated, not charged)
- **Pricing source:** Higgsfield's official Seedance 2.0 token metering.
  - Billable video tokens = ceil(seconds × width × height × 24 / 1024).
  - The rate is **$0.014 per 1,000 tokens** for 480p/720p/1080p, before customer discount.
  - Image references are not billed as video input.
- **How the source was read:** the official pages (open.higgsfield.ai model page and `/pricing`) were read through the search index. Fetching them directly was blocked by this environment's egress policy, so recheck the live page before authorising.

| Inputs | Output px | Tokens | List price | At the 30% max discount |
|---|---|---|---|---|
| 5 s, 1080p, 24 fps, i2v, no video input, audio off | 1920×1080 | 243,000 | **$3.40** | $2.38 |
| Sensitivity: if the output is 1920×1088 | 1920×1088 | 244,800 | $3.43 | $2.40 |

- Charged: $0.00.
- Funding is unknown. The API account showed $5.00 before the single Flare image, and its current balance is not readable through the routes used. Confirm sufficient funds before authorising.

## 5. Offline preflight (Agent-008 `preflight`; no network calls)
- **Command:**
  `python3 evidence/agent008/phase1/s027_v2/run_preflight_v2.py <verified frame> <live registry row>`
- **Output:** `evidence/agent008/phase1/s027_v2/S027_PREFLIGHT_v2.json`.

| Check | Result |
|---|---|
| approved_shot_contract / shot_in_approved_video_shots / manifest_ids (45cc7493, edc4ad58, APPROVED) | PASS |
| source_frame_sha256 (`81b841a6…0061b`, registry APPROVED) | PASS |
| model_capability / model_official_contract (VERIFIED, submit_enabled) | PASS |
| prompt_sha256 `ab7f92af…cab3` / duration-resolution [5, 1080p, 16:9] | PASS |
| provider_credentials (sanctioned transport, proxy-injected auth declared) | PASS |
| paid_generation_count_so_far | PASS (0) |
| **source_frame_hosted_url** | **FAIL `SOURCE_URL_MISSING`** (expected: upload not authorised) |
| **spend_authorisation** | **FAIL `SPEND_AUTHORISATION_MISSING`** (expected: generation not authorised) |

- **Offline serialisation** with the official serializer:
  - Without a URL, it refuses (`SOURCE_URL_MISSING`).
  - With a placeholder URL, which was never sent, the body keys are exactly `prompt, image_url, duration, resolution, generate_audio`.
  - The transmitted prompt is identical to the package prompt.
- **Tests:** the Agent-008 suite passes, 84 tests.
- **Former blockers now cleared:** missing base frame, missing frame SHA, missing Higgsfield auth and missing transport.

## 6. Safety
- Higgsfield calls of any kind: 0. Source upload: not performed.
- Seedance POSTs: 0. Video generations: 0. Image generations: 0. Credits spent: 0.
- Writes: registry 0, storage 0, manifest/readiness 0, canon 0. Agent-008 code changes: 0.
- Agent runs: Agent-006 0, Agent-007 0. Billing changes: 0. Anime Clip Farming: untouched.

Rollback: revert the commit. Nothing outside the repo changed.

## 7. Status
```text
EP005_S027_MOTION_PACKAGE_READY_FOR_HUMAN_APPROVAL
+ BASE_FRAME_APPROVED + BASE_FRAME_SHA_VERIFIED + SEEDANCE20_MODEL_LOCKED_FOR_THIS_ATTEMPT
+ FINAL_MOTION_PROMPT_PREPARED + MOTION_PROMPT_SHA256_RECORDED + NEGATIVE_CONSTRAINTS_FOLDED_INTO_PROMPT
+ DURATION_5_SECONDS + RESOLUTION_1080P + AUDIO_OFF + EXPECTED_COST_CALCULATED
+ SOURCE_UPLOAD_NOT_PERFORMED + GENERATION_AUTHORISED_FALSE
+ SEEDANCE_POSTS_0 + VIDEO_GENERATIONS_0 + CREDITS_SPENT_0 + EVIDENCE_COMMITTED_TO_GITHUB
```
**Stop condition:** waiting for Gilang / Company Brain approval before the source upload or any generation.
