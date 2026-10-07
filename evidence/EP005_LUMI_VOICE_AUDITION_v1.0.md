# EP005 Lumi Voice Audition v1.0 (bounded, 3 takes)

Date: 2026-10-07. Mikko & Lumi only. Human-authorised (D-3). Existing ElevenLabs Starter credits only; no purchase, no billing change.

## 1. D-3 creative decision recorded; S012 / S018 check (no script or manifest change made)
- Approved S004 prompt replaced (decision): "Can you help Mikko find the next berry smudge?" → **"Can you find the next berry smudge?"** (8 syllables instead of 11; 36 vs 46 characters). First S004 line unchanged: "A little glint! Look at his cheek."
- **Is the repeated prompt exactly the same in S012 and S018? Yes.** In approved script `14471926…` v02 (`production_script_json.shots[].child_prompt`) and in manifest `45cc7493…` (`audio_plan.voice_lines`) the identical string "Lumi: “Can you help Mikko find the next berry smudge?”" appears in S004, S012 and S018 (and nowhere else; S007's prompt is Mikko's different line).
- **Proposal (not applied; needs explicit authorisation):** use the same shortened prompt "Can you find the next berry smudge?" in S012 and S018 so the ritual stays identical. Rough fit (audition rates 2.6–3.0 syl/s, 15 syllables for line 1 + shortened prompt, window = shot − 0.85 s): S012 (5 s, window about 4.15 s): conflict likely; S018 (6 s, window about 5.15 s): fits narrowly (about 5.0 s) with L1 or L3, not with L2. These are estimates; S012/S018 glint offsets were not measured.
- Not changed: script row, manifest, readiness, other dialogue. No other dialogue altered.
- Hygiene note for the human: the approved script/manifest text still holds the old prompt; the new wording is a recorded decision that needs a governed script/manifest update before Agent-008 can accept it (the Agent-008 contract compares line text hash with the manifest).

## 2. Generations (exactly 3; flow `v156SWeKdkuYy8Crv8ag`)
Text (all three): "A little glint! Look at his cheek. Can you find the next berry smudge?" (70 characters). Model `eleven_multilingual_v2`. One take each. Credits: **70 per take, 210 total** (reported price 1.4 US cents per take at the account rate). Starter balance before/after not readable through the connector.
| | Voice | voice_id | generation_id | duration (decoded) | speech extent* | syllables/s | file SHA-256 (mp3) |
|---|---|---|---|---|---|---|---|
| L1 | Lola – Soft, Innocent and Calming | `f9imtLc2jfOLXtqe3Ihb` | `ICmQjlhIOueTir68xc0u` (session `Fp6R66oDts693PqH3PwA`) | **5.898 s** | 5.40 s (0.08 s lead, 0.42 s tail) | 2.96 | `832fa7cc217755daa4f7a00d4701899d865ba60cd2bcf89549f2ba99a4c32797` |
| L2 | Libby-Animated | `Wu9A8zlwvFHoEpuX7MGo` | `ceoShU0y1UDdJvn7lck3` (session `h32Oy2hl1r0FWwRGWUgL`) | **6.687 s** | 6.08 s (0.16 s lead, 0.45 s tail) | 2.63 | `bf296ebd77da0a2657910acc6f4ea4dfcd0ec2d816165dbab18f42e456138229` |
| L3 | celine – cuddly, thin and soft | `mHX7OoPk2G45VMAuinIt` | `LyA1OJnk187PvD0U0PG2` (session `WGynKYSI5XkjxBsP0LEL`) | **5.341 s** | 5.32 s (0.00 s lead, 0.02 s tail) | 3.01 | `e7a0986dad22a2bde1df9df37936cbef983ec409683c75f57aa39dff3e369520` |
*Speech extent = first to last 10 ms window above max(−55 dBFS, peak−35 dB). Files: MP3, mono, 44.1 kHz, 128 kbps (provider format; unchanged originals). Review files were delivered in the session and not committed.

## 3. Fit against the S004 dialogue budget (window 0.65–4.80 s = 4.15 s)
| | Speech extent | Overrun vs 4.15 s | Speech ends if started at 0.65 s | vs 4.80 s guard | vs 5.00 s shot end |
|---|---|---|---|---|---|
| L1 | 5.40 s | +1.25 s | 6.05 s | −1.25 s | −1.05 s |
| L2 | 6.08 s | +1.93 s | 6.73 s | −1.93 s | −1.73 s |
| L3 | 5.32 s | +1.17 s | 5.97 s | −1.17 s | −0.97 s |
**No take fits comfortably; none fits at all.** Even the shortest runs about 1 s past the end of the 5.0 s shot. **TIMING_CONFLICT remains YES for the combined two-line S004 dialogue**, even with the shortened prompt.

## 4. Rushed? (duration only, no listening judgement)
All three run at 2.6–3.0 syllables/s over their speech extent, i.e. at or below the 3.0 syl/s "comfortable preschool" rate used in the budget; none is rushed on duration alone. Internal pauses ≥ 120 ms: L1 four (1.15, 1.40, 2.59, 2.73 s), L2 six, L3 none detected (continuous delivery, which may sound less natural; to be judged by listening). Fitting 4.15 s would require about 1.28× (L3), 1.30× (L1) or 1.47× (L2) speed-up: ruled out by the decision not to speed Lumi up.
No winner selected. The human reviews the three files by ear.

## 5. What this means (for the human decision, no action taken)
- Under the three constraints (no lengthening, no speed-up, no dialogue into protected holds) the current wording cannot fit S004. About 1.2 s more of room (or about 1.2 s less speech) would be needed even with the shortened prompt.
- Options (not applied): (a) shorten line 1 as well (about 5 syllables would put speech near 3.3–3.6 s at these rates); (b) drop one line from S004 and place the prompt where there is room; (c) revisit the shot length decision; (d) adjust the leading offset: starting speech at 0.15 s instead of 0.65 s gains 0.5 s but is still not enough.

## 6. Counts
ElevenLabs generations 3 · credits 210 · Mikko 0 · registry rows 0 · production storage uploads 0 · Agent-008 changes 0 · renders 0 · Agent-006 0 · Agent-007 0 · Runway 0 · billing changes 0 · script/manifest/readiness changes 0.
Data: `evidence/ep005/voice_audition/LUMI_AUDITION_RESULTS_v1.json`.
