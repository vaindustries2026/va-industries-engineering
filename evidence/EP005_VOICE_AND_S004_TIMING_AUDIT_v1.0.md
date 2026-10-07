# EP005 Voice / Dialogue Production Audit + S004 Timing Proof v1.0

Date: 2026-10-07. Mikko & Lumi only. Read-only: no ElevenLabs generation, no credits, no provider spend, no Supabase/storage/registry writes, no script/manifest/readiness changes, no Agent-006/007 runs.
Human decisions recorded: D-1 approved (deterministic shot-level trim of the existing `SFX-LUMI-CLUE-CHIME`; source unchanged). D-2 approved (ambience continuity under S004 as a timeline policy). D-3 open (this audit).

## 1. Exact S004 dialogue (approved script `14471926…` v02 APPROVED; manifest `45cc7493…` APPROVED)
| # | Speaker | Exact text | Script field | sha256 (UTF-8) |
|---|---|---|---|---|
| 1 | Lumi | A little glint! Look at his cheek. | `dialogue_lyric` | `6d237bbb687b809266917937feaacd3e1c74ab3edb089fffa0c61fff905d6e8d` |
| 2 | Lumi | Can you help Mikko find the next berry smudge? | `child_prompt` | `ab9e07dfe0b90d8d011ab6cf22dce0cc05f2ff3f69f0ce533fdaf2fb71179410` |
- Shot: S004, 13.0–18.0 s, **5.0 s** (120 frames @24).
- Timing notes present: script `pause_seconds: 0`; "Deliver dialogue, then prompt"; manifest "No child-response hold; pause_seconds is 0. Preserve natural speech spacing only"; QC "Lumi's dialogue is delivered before the child prompt, with no rewritten wording".
- Chime overlap: the script/manifest require the clue chime to start with the initial glint and be completed before S005. With a 5.0 s shot the chime (0.500–4.875 s after the approved D-1 trim) necessarily runs under both lines; the documents do not forbid the overlap.
- End before S005: yes. S005 is a protected 4.0 s participation hold with "no dialogue, clue audio, reveal audio"; architecture `cue.pause_seconds: 4` puts the child's pause after the prompt. So both lines must finish inside S004.
- Character fit: both lines match Lumi = SEE (observe, locate, invite); VA_01 §12 locked canon; script `character_voice_check.lumi`. Note: no separate "Characterization Bible" file exists in the repo; the locked canon is VA_01 §12 plus the script's `character_voice_check`.

## 2. Voice infrastructure (live state)
| Item | Found | Evidence |
|---|---|---|
| Approved Mikko / Lumi voice | No | registry has no VOICE/DIALOGUE rows (AUDIO rows are 3 SFX + ambience + foley + pop) |
| Voice IDs / ElevenLabs assignments | No | no voice id in repo, registry metadata, script or manifest; ElevenLabs workspace search "Lumi"/"Mikko" returns only public library voices (`is_library_voice: true`), none saved to the workspace |
| TTS model selection | No | none recorded |
| Pronunciation rules | No | none (note: "Mikko" pronunciation not specified) |
| Speaking-style prompts | Partial | behavioural canon only (Lumi observes/invites; Mikko announces actions); no voice-direction spec |
| Voice-clone assets | No | none |
| Dialogue audio in registry / storage | No | `production-assets/audio/` holds ambience, foley, sfx only |
| Dialogue-generation workflow | No | no n8n workflow or credential for ElevenLabs/TTS (credential list verified in the downstream audit); Agent-008 has an attachment interface only |
| Prior approved voice tests | No | none in evidence or changelog |
**VOICE_INFRASTRUCTURE_STATUS = MISSING**

## 3. ElevenLabs capability (read-only calls: node types, model schemas, model guides, voice listing; no generation, no flow created)
- TTS models runnable in this workspace: `eleven_multilingual_v2` (connector default), `eleven_v3`, `eleven_v4`, `eleven_turbo_v2_5`, `eleven_flash_v2_5`.
- Child-safe character voices: available in the public library (e.g. gentle/warm animation voices below). Voice IDs are stable library ids and can be pinned.
- Controls exposed by this connector: **voice and language_code only**. No speed, stability, similarity, style, seed or output-format parameters. Delivery can only be shaped through text: punctuation; on v3/v4 inline audio tags (`[warmly]`, `[softly]`, `[slowly]`, `[pause]`); on v2/turbo/flash `<break time="…"/>` up to 3 s. Changing text or adding tags must not alter the approved words; tags are delivery markup, which still needs a human rule before use.
- Duration: **cannot be set**; only influenced (voice choice, punctuation, tags) and **measured after generation**. No seed control, so takes are not reproducible; an approved take must be stored and hashed.
- Output format: not selectable through the connector; outputs have been MP3 (as with the audio candidates); production use would convert deterministically to 48 kHz WAV like the SFX.
- Credits: listing voices, schemas and guides spend nothing. Library `preview_url` clips are pre-existing and free to listen to. `creative_generate_speech` spends credits and defaults to `generations_count: 4`. It offers `estimate_only`, but I did not call it because it can create a flow in the workspace; it is the right way to price an approved audition.
- Account caveat (unchanged): the connector workspace was reconciled by the human for the audio step; commercial-rights documentation remains deferred.

## 4. S004 timing budget (deterministic; `evidence/ep005/voice_audit/dialogue_timing_budget.py` → `S004_TIMING_BUDGET_v1.json`)
| Element | Frames / seconds (shot-relative) |
|---|---|
| Mirror tilt | frames 0–11 (0.000–0.458 s) |
| Glint | frames 12–19 (0.500–0.792 s), ends before S005 ✔ |
| Clue chime (approved D-1 trim) | 0.500–4.875 s, ends before S005 ✔ |
| Earliest natural dialogue start | 0.65 s (Lumi reacts to the glint: "A little glint!") |
| Latest dialogue end | 4.80 s (0.20 s guard before the silent protected hold) |
| **Maximum dialogue duration available** | **4.15 s** (absolute ceiling 4.50 s with no reaction gap and no guard) |
| Words / syllables | line 1: 7 / 8 (one internal beat after "glint!"); line 2: 9 / 11; total 16 / 19 |
| Estimated speech incl. 0.45 s between lines | 7.03 s @3.0 syl/s (preschool comfortable) · 6.13 s @3.5 (brisk) · 5.45 s @4.0 (adult conversational) |
| Overrun vs 4.15 s | +2.88 s · +1.98 s · +1.30 s |
Even line 2 alone at a comfortable preschool pace (~3.7 s) leaves no room for line 1. Fitting both would need about 4.6+ syllables per second with no pause — unnaturally fast for preschool viewers.
**TIMING_CONFLICT = YES** (planning estimate; to be confirmed by measuring an approved voice take, but the margin is large).

Episode-wide scan (`EPISODE_VOICE_SHOT_SCAN_v1.json`, heuristic syllables): the same pattern recurs where the recurring prompt follows a Lumi clue line: S004 CONFLICT, S012 CONFLICT, S018 TIGHT (6 s); also TIGHT: S001, S006, S007. 11 voiced shots FIT. The issue is structural (two lines + glint in a 5 s cue shot), not specific to S004.

Options for the human (not applied, no rewrite made):
1. Lengthen S004 (and S012/S018 consistently) to about 7.0–7.5 s; episode grows about +2–2.5 s per affected shot; the chime trim would relax (natural cue 8.0 s).
2. Keep durations; move the child prompt so it starts at the end of S004 and continues into the start of S005. This conflicts with S005's protected silent hold as approved.
3. Keep durations; shorten or rewrite the lines. Requires a separate creative decision, since approved wording is locked.
4. Faster delivery: not recommended (preschool readability).

## 5. Proposed Lumi audition (no generation yet)
Step 0 (free): listen to the library preview clips of the three candidates (no credits).
Step 1 (needs authorisation): one take per candidate (`generations_count: 1`, overriding the default 4), same model and text.
| # | Voice (library) | voice_id | Why it may fit Lumi |
|---|---|---|---|
| L1 | Lola – Soft, Innocent and Calming | `f9imtLc2jfOLXtqe3Ihb` | young female, smooth, friendly, made for animation; calm rather than hyper — fits a gentle observer |
| L2 | Libby-Animated | `Wu9A8zlwvFHoEpuX7MGo` | warm, gentle storybook soprano; kind, nurturing, conversational; bright enough for a glowing orb character |
| L3 | celine – cuddly, thin and soft | `mHX7OoPk2G45VMAuinIt` | soft, natural, cute; lighter and more childlike option to compare against L1/L2 |
Excluded on canon grounds: hyper/peppy, sassy, giggly or whispery/ASMR voices (Lumi is not omniscient, not loud, not a narrator).
- Model: `eleven_multilingual_v2` (stable, no tags; punctuation only).
- Settings: none available beyond voice and language_code (`en`).
- Test line: "A little glint! Look at his cheek." (34 characters, approved S004 line 1).
- Estimated credits: about 34 per take → about 102 for three takes, assuming the published rate of ~1 credit per character for multilingual v2. **Unverified in this session**; confirm with `estimate_only` at authorisation time.
- Optional, to also measure timing: the same three takes speaking both S004 lines (81 characters → about 243 credits estimated).
- Listen for: warmth without baby-talk; clarity of "glint" and "cheek"; observant, gentle tone (not excited or announcing); natural pause after "glint!"; no lecturing or omniscient feel; a timbre that matches a soft glowing orb and contrasts with a future Mikko voice; measured duration.
Mikko is not auditioned (not required for S004).

## 6. Agent-008 voice input contract (proposal; production behaviour unchanged)
`evidence/ep005/voice_audit/AGENT008_VOICE_INPUT_CONTRACT_PROPOSAL_v0.1.json`. Fields: shot_id, line_index, speaker, voice_asset_id, voice_id, tts_model_id, dialogue_text, dialogue_text_sha256, audio_asset_id, audio_path, sha256, duration_s (re-measured), start_time_s, end_time_s, gain_db, approval_status=APPROVED, approved_by, approval_record. Rules: the text hash must equal the approved manifest line; clip, voice and line must be APPROVED and hash-verified; no overlap, no overrun past shot end minus guard, nothing in protected holds; Agent-008 never calls TTS and never regenerates or re-times by resynthesis; captions derive from the record.
Proposed future registry identities: `VOICE-LUMI-v01` (the approved voice choice: voice_id, model, delivery rules) and per-line clips such as `DLG-EP005-S004-L1-LUMI-v01`.

## 7. Counts
ElevenLabs generations 0 · credits 0 · estimate calls 0 · flows created 0 · Runway 0 · paid calls 0 · Supabase writes 0 · storage writes 0 · registry writes 0 · n8n calls 0 · Agent-006 0 · Agent-007 0 · renders 0.
