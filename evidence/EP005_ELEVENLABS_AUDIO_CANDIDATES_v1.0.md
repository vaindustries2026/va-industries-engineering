# EP005 ElevenLabs Audio Candidates for Human Review (v1)

**Date:** 2026-10-07 (UTC; generations ran 03:11–03:13Z)
**Actor:** Claude Code (bounded engineering operator)
**Authorised by:** Company Brain. Use the existing ElevenLabs Starter-plan credits only, with ElevenLabs Sound Effects (`eleven_text_to_sound_v2`) through the connected MCP. Maximum 9 generations (3 per requirement). No purchase, upgrade or billing change.
**Scope:** Mikko & Lumi only.
**Status of every file:** CANDIDATE_FOR_HUMAN_REVIEW. None is approved, registered or uploaded.

## 1. Generations

| Item | Value |
|---|---|
| Generations performed | **9** (ceiling 9, respected) |
| Failures / retries | **0 / 0** |
| Flow (ElevenLabs canvas) | `NRRpsJcWc7UzYPkRv6e3`, with nine labelled sfx nodes |
| Run order | one `estimate_only` (nothing generated), then three run calls of 3 nodes each, run once and never repeated |
| `generations_count` | explicitly **1** on every run. The connector default is 4, which could have exceeded the cap. |
| Prompt influence | 0.5 for all nine. The model default is 0.3; I chose 0.5 uniformly so that the negative constraints are followed more strictly. |
| Durations requested | ambience 25 s with seamless loop on; cloth 1.0 s; pop 0.5 s (the minimum the model allows) |
| Credits reported per generation | ambience 83.33 each, cloth 3.33 each, pop 1.67 each: **265 credits in total** (about 5.3 US cents at the reported prices) |

**Credit and usage information from the MCP:**
- It returns only a per-generation cost. There is no balance or usage lookup, so the remaining Starter credits are not known.
- The `estimate_only` call returned **795 credits** for the same nine generations, exactly 3 times the 265 reported afterwards. I can't tell which figure matches the account deduction, and I couldn't check the balance. It's worth a look in the ElevenLabs usage page.

## 2. Candidates

Provider output was never altered. Review copies below are byte-identical renamed copies, and the SHA-256 is that of the original download.

| Candidate | Asset | Variant | Generation id | Duration (provider / decoded file) | Bytes | SHA-256 (original) |
|---|---|---|---|---|---|---|
| AMB-BATHROOM-QUIET-v01-EL-CAND-A | AMB-BATHROOM-QUIET-v01 | A: neutral / clean | `jBDhcy9ESwGyI8gN3IP9` | 25.00 s / 25.05 s | 418410 | `e5930ba7886e9889075bc2c26203296f58319c0959b0581efb8e41b3a44c5192` |
| AMB-BATHROOM-QUIET-v01-EL-CAND-B | AMB-BATHROOM-QUIET-v01 | B: warmer / softer | `7CeuAy9P4ig5O05cOFJs` | 25.00 s / 25.05 s | 418410 | `87ca37d5a5feda35f3f5d40485b3c6ff6697574452d278a636e16f2534b67906` |
| AMB-BATHROOM-QUIET-v01-EL-CAND-C | AMB-BATHROOM-QUIET-v01 | C: airier / more open | `Oe9nvpw0JuR3zKjs6Vib` | 25.00 s / 25.05 s | 418410 | `baee962c86f8725ffa595331f452a698bde7d5e69871165696bf43e933317d6b` |
| FOLEY-CLOTH-SOFT-v01-EL-CAND-A | FOLEY-CLOTH-SOFT-v01 | A: clean gentle wipe | `1svFoVNd2k9YUGYk5BK1` | 1.00 s / 1.04 s | 34306 | `6eee9b2447a9525853105a9146daae3f47f5142a55d54b7e12846c546c327a6a` |
| FOLEY-CLOTH-SOFT-v01-EL-CAND-B | FOLEY-CLOTH-SOFT-v01 | B: softer / lighter brush | `n8T2LIFiBNMbroS3VjgQ` | 1.00 s / 1.04 s | 34306 | `d7a7786e01a5e69fae7465d91eea5aaf8efdeea5f03aad32bbfe3a719d3c58c2` |
| FOLEY-CLOTH-SOFT-v01-EL-CAND-C | FOLEY-CLOTH-SOFT-v01 | C: slightly fuller pass | `eiW0bnQ9IsbkD6qwPVuQ` | 1.00 s / 1.04 s | 34306 | `b0c80ce840bc39f0f306b8f84dcf5fb8b654a011249bcd03a63933911f6b9080` |
| SFX-COMPLETION-POP-v01-EL-CAND-A | SFX-COMPLETION-POP-v01 | A: balanced soft pop | `75tahAZ0wFnzcjSADUkx` | 0.48 s / 0.52 s | 25947 | `26cbfe89678e68b4826a8179c29ffa427492bd521a8df300c51d9c8f4b9d4a6d` |
| SFX-COMPLETION-POP-v01-EL-CAND-B | SFX-COMPLETION-POP-v01 | B: softer / rounder | `9nbCjtJHleIzRbpza0DP` | 0.48 s / 0.52 s | 25947 | `3f2fc41f6da27abc4e1abbf285b3a02f9a9ac319529ccfbbecba97cce48923ba` |
| SFX-COMPLETION-POP-v01-EL-CAND-C | SFX-COMPLETION-POP-v01 | C: brighter / shorter-feeling | `w7nMUcbVodYoUbfbm0KZ` | 0.48 s / 0.52 s | 25947 | `9c816983d5e05f36ba5f14d5463769ce371fd1affccb79d3f01354876f26aecc` |

- **Format (all nine):** MP3 (MPEG-1 Layer III, ID3v2.4), 44.1 kHz, stereo, 128 kbps. The decoded durations are slightly longer than the provider's because of MP3 padding.
- **Original provider filename:** `content.mp3`. **Tool and model:** ElevenLabs MCP `creative_run_flow_nodes`, `eleven_text_to_sound_v2`.
- **Automatic alteration or extension by the provider:** not indicated. The ambience used the provider's own seamless-loop option; no extension tool was used.
- **Exact prompts, node ids, session ids and timestamps for each:** `evidence/ep005/elevenlabs_candidates/EP005_ELEVENLABS_CANDIDATES_MANIFEST_v1.json`.

## 3. Prompts used (disclosed deviation)

Your suggested prompt directions were condensed slightly, following the model's own guide (short, single sound, concrete texture words, no visual terms). The variant wording changes only as much as needed:
- **Ambience:** "Very quiet {clean | warm | airy} indoor bathroom room tone, soft {neutral | low-pitched | open} interior ambience, extremely subtle and {calm | gentle | calm}, steady {low background | muted | light spacious} hush, no voices, no water, no music, no distinct events."
- **Cloth:** "Close-up {very soft microfiber cloth gently wiping | very light microfiber cloth brushing | soft microfiber cloth wiping} a smooth surface, {one delicate dry brushing pass | one soft delicate dry pass | one slightly fuller dry pass}, quiet and …, no scrape, no paper rustle, no wet sound."
- **Pop:** "Tiny soft {friendly | rounded | bright} pop, {clean gentle | gentle low-pitched | crisp light} transient, subtle and {satisfying | warm | quick}, a single {short | short | very short} pop, no bell, no sparkle, no chime, no music."

The full text of each is in the manifest. Dropped from your suggestions: "toilet", "plumbing", "traffic" and "fan" in the ambience prompt (naming those sounds can invite them in), and the "no exaggerated cartoon effect" wording in the cloth prompt.

## 4. Numerical QC (not listening; I can't hear audio)

Full output in `EP005_ELEVENLABS_CANDIDATES_QC_v1.txt`.

**Ambience:**

| Candidate | RMS | Peak | Loop seam | Tonal prominence |
|---|---|---|---|---|
| A | −60.2 dBFS | −47.7 dBFS | **fails** my click test: boundary step 6× the typical sample step; end/start level differ by 2.2 dB | 27.6 dB |
| B | −67.8 dBFS | −50.7 dBFS | **fails**: step 5× typical; end/start differ by 2.9 dB | 32.1 dB |
| C | −63.7 dBFS | −50.4 dBFS | passes (end/start differ by 1.3 dB) | 30.0 dB |

Points to check by ear:
- **Tonal content.** Tonal prominence is how far the strongest spectral peak sits above its neighbours. The local synthetic candidates measured 2.3–2.8 dB; these measure 27.6–32.1 dB. That suggests narrow tonal components such as a hum or drone, which the brief excludes. Please listen for it.
- **Loop seam.** The first and last samples of a decoded MP3 carry encoder padding, so the click test isn't conclusive. Use the loop-check files, which play each ambience twice. The seam is at about 0:25.
- **Level.** All three are very quiet (−60 to −68 dBFS average), and B is about 7 dB quieter than A. They will need gain staging.

**Cloth:**
- **A:** peak −24.8 dBFS; audible from about 0 to 793 ms.
- **B:** peak −15.1 dBFS; a short, compact event, about 187–510 ms.
- **C:** peak −25.8 dBFS; about 24–872 ms.

**Pop:**
- **A:** peak −32.7 dBFS; audible for about 300 ms.
- **B:** peak −42.5 dBFS; low-level content continues to the end of the 0.48 s clip.
- **C:** peak −43.4 dBFS; same.

All three are quiet. B and C need trimming to the 0.15–0.35 s target, and gain.

## 5. Rights and governance

- **Plan:** Company Brain states the account is on the ElevenLabs **Starter** plan. I couldn't verify that from the account (the connector has no plan lookup).
- **Commercial-use rights:** **unreconciled.** As instructed, generation wasn't blocked on rights research, which will be reconciled separately. **No candidate should be ingested until the rights are documented and a human approves the exact bytes by SHA-256.** I didn't verify ElevenLabs' current terms for the Starter plan.
- **Attribution or licence obligation:** not determined.
- **Spend:** existing Starter credits only. There was no purchase, upgrade, subscription or billing change.

## 6. Review files (session scratch; not committed, not uploaded)

```
/tmp/claude-0/-home-user-va-industries-engineering/26999ca9-2a8f-5871-b737-7fa96a08dad2/scratchpad/el_candidates/
  original/      AMB-{A,B,C}.mp3  CLOTH-{A,B,C}.mp3  POP-{A,B,C}.mp3   (original downloads, hash authoritative)
  review/        the nine files renamed to their candidate ids; byte-identical to the originals
  review_aids/   LOOPCHECK-AMB-EL-CAND-{A,B,C}-x2.wav   (DERIVATIVE: each ambience decoded to 16-bit WAV and played twice; a listening aid, not a candidate)
```

The audio files are not committed. There's no repository policy for audio binaries, and the original bytes and hashes are recorded above. The ElevenLabs flow (`NRRpsJcWc7UzYPkRv6e3`) holds the generations, and the provider-side download links expire after about two hours; the originals are already saved locally.

## 7. Unchanged state (verified after generation)

| Item | State |
|---|---|
| asset_registry | 20 rows, md5 `b7b46112661dc0a0d9218e647f747306` |
| storage.objects | 16, md5 `4c7ef85e9c92af4fca27b775e233b7bc` |
| Manifest `96df250f` | APPROVED, unchanged |
| Readiness manifests | `89663d3b…` |
| Migrations | 1 |

Agent-006 executions: 0. Agent-007 executions: 0. Readiness approvals: 0. Workflow changes: 0. Supabase, n8n and GitHub state were not modified except by this evidence commit.

## 8. Final status

```text
EP005_ELEVENLABS_AUDIO_CANDIDATES_READY_FOR_HUMAN_REVIEW
+ THREE_AMBIENCE_CANDIDATES + THREE_CLOTH_CANDIDATES + THREE_COMPLETION_POP_CANDIDATES
+ MAX_NINE_GENERATIONS (9 of 9, 0 failed, 0 retries)
+ ORIGINAL_SHA256_RECORDED
+ ELEVENLABS_STARTER_EXISTING_CREDITS_ONLY
+ ZERO_CREDIT_PURCHASE + ZERO_PLAN_UPGRADE + ZERO_BILLING_CHANGE
+ ZERO_REGISTRY_CHANGE + ZERO_PRODUCTION_STORAGE_CHANGE
+ ZERO_AGENT006_RUN + ZERO_AGENT007_RUN + ZERO_READINESS_APPROVAL
+ EVIDENCE_COMMITTED_TO_GITHUB
```

**Stop condition:** the nine candidates are ready for human listening. No winner has been chosen.
