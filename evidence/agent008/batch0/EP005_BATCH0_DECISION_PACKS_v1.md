# EP005 Batch 0B: human decision packs (prepared, NOT executed)

Mikko & Lumi only. Nothing in this pack changes the approved script, manifest or readiness. All wording alternatives are REVIEW proposals.

## 5. Lumi voice: LUMI_VOICE_SELECTION_REQUIRED_BY_HUMAN = YES
- **Source:** `evidence/ep005/voice_audition/LUMI_AUDITION_RESULTS_v1.json`. Recovered from evidence; no new takes were generated and no winner is chosen.
- **Audition text, all three takes:** "A little glint! Look at his cheek. Can you find the next berry smudge?" This uses the D-3 wording, not the manifest wording.
- **Model:** `eleven_multilingual_v2`. 70 credits each.

| | Voice | voice_id | generation_id (session) | duration | speech extent | rate | SHA-256 (mp3) |
|---|---|---|---|---|---|---|---|
| L1 | Lola – Soft, Innocent and Calming | `f9imtLc2jfOLXtqe3Ihb` | `ICmQjlhIOueTir68xc0u` (`Fp6R66oDts693PqH3PwA`) | 5.898 s | 5.40 s | 2.96 syl/s | `832fa7cc217755daa4f7a00d4701899d865ba60cd2bcf89549f2ba99a4c32797` (112,464 B) |
| L2 | Libby-Animated | `Wu9A8zlwvFHoEpuX7MGo` | `ceoShU0y1UDdJvn7lck3` (`h32Oy2hl1r0FWwRGWUgL`) | 6.687 s | 6.08 s | 2.63 syl/s | `bf296ebd77da0a2657910acc6f4ea4dfcd0ec2d816165dbab18f42e456138229` (125,003 B) |
| L3 | celine – cuddly, thin and soft | `mHX7OoPk2G45VMAuinIt` | `LyA1OJnk187PvD0U0PG2` (`WGynKYSI5XkjxBsP0LEL`) | 5.341 s | 5.32 s | 3.01 syl/s | `e7a0986dad22a2bde1df9df37936cbef983ec409683c75f57aa39dff3e369520` (103,687 B) |

- **Where to listen:** ElevenLabs flow **`v156SWeKdkuYy8Crv8ag`** (workspace `a2a81ab0f7fd406cb3fff9eef8e173c2`): https://elevenlabs.io/app/flows/v156SWeKdkuYy8Crv8ag
  - The binaries were never committed, and the 2026-10-07 signed links have expired.
- **Selection must name:** the voice_id. If the take itself is to be reused as a production line, it must also name the take's SHA. Note the take uses the D-3 wording, which is not in the manifest (see §6).

## 6. S004 / S012 / S018 dialogue timing (script unchanged)
- **Method:** the Batch-0 syllable counter at the measured Lumi audition rates (2.63–3.01 syl/s).
- **Window:** shot length − 0.65 s lead − 0.20 s guard before the following protected hold (S005, S013, S019).

| Shot | Function | Current authoritative dialogue | Shot | Window | Est. speech | Conflict |
|---|---|---|---|---|---|---|
| S004 | First clue: draws attention to the cheek mark; invites the child to find the mark during the S005 hold | "A little glint! Look at his cheek." + "Can you help Mikko find the next berry smudge?" (19 syl) | 5.0 s | 4.15 s | 6.31–7.22 s | **YES** (+2.2 to +3.1 s) |
| S012 | Second clue: mouth-area mark plus the same participation ritual | "I see a spot near your mouth." + same prompt (18 syl) | 5.0 s | 4.15 s | 5.98–6.84 s | **YES** (+1.8 to +2.7 s) |
| S018 | Third clue: nose mark plus the same ritual | "One tiny spot is still here." + same prompt (18 syl) | 6.0 s | 5.15 s | 5.98–6.84 s | **YES** (+0.8 to +1.7 s) |

- The recorded D-3 wording ("Can you find the next berry smudge?") gives S004 16 syl = 5.32–6.08 s, which **still does not fit**.

| | ALTERNATIVE A: minimum wording change (ritual prompt "Can you find the next smudge?") | Est. | Fits 4.15 / 4.15 / 5.15 s? |
|---|---|---|---|
| S004 | "A glint on his cheek!" + "Can you find the next smudge?" (11 syl) | 3.65–4.18 s | fits at the faster rate; marginal (+0.03 s) at the slowest |
| S012 | "A spot by your mouth." + "Can you find the next smudge?" (11) | 3.65–4.18 s | same as S004 |
| S018 | "One tiny spot is still here." (unchanged) + "Can you find the next smudge?" (13) | 4.32–4.94 s | yes |

| | ALTERNATIVE B: stronger preschool compression (ritual "Find the next smudge!") | Est. | Fits? |
|---|---|---|---|
| S004 | "A glint on his cheek!" + "Find the next smudge!" (9) | 2.99–3.42 s | yes, about 0.7 s margin |
| S012 | "By your mouth!" + "Find the next smudge!" (7) | 2.33–2.66 s | yes |
| S018 | "One spot left!" + "Find the next smudge!" (7) | 2.33–2.66 s | yes |

- **Trade-offs:**
  - Both keep one identical ritual prompt across all three shots, and keep the cheek/mouth/nose target words.
  - A keeps the question form, which is the participation invitation, but is marginal in S004 and S012 with the slowest voice.
  - B is robust for any candidate voice. It turns the question into an imperative.
- **Governance:** either choice needs a governed script v03 / derived manifest and readiness. The Agent-008 dialogue gate compares clip text with the manifest slot text.

**TIGHT (still supported by the data):**
- **S003** Lumi, 8 syl = 2.66–3.04 s in 3.5 s. Only 0.46–0.84 s is left for a lead and a tail.
- **S006** Mikko, about 2.24 s including the provider tail, in 2.5 s, and it must follow the S005 response pause.
- **S028** Lumi 2.33–2.66 s plus Mikko about 1.64–1.84 s, sequential, in 5.0 s, alongside the cloth hand-off, pat and settle.

## 7. Held-pose matrix (STATIC_OR_DETERMINISTIC_ONLY shots)
| Shot | Authoritative intended action | Deterministic representation | Class | Meaning survives? | Sign-off |
|---|---|---|---|---|---|
| S003 | Lumi positions and holds the mirror; Mikko looks in, cloth lowered; nearly static | Held over-shoulder frame + 3 overlays | SAFE_HELD_POSE | Yes | No |
| S004 | Lumi tilts the mirror → tiny glint on the cheek; chime | Held frame + MIRROR-GLINT treatment synced to the chime | SAFE_DETERMINISTIC_TREATMENT | Yes (the glint carries the clue); the tilt is lost | **Yes** |
| S005 | 4.0 s protected hold, no events | Held S004 end state | SAFE_HELD_POSE | Yes | No |
| S006 | After the pause, Mikko raises his hand, points to the cheek, and speaks | Held **pointing** pose (new frame) + reflection treatment | SAFE_HELD_POSE | Mostly: the identification is shown, but the "raise after pause" beat is lost | **Yes** |
| S008 | 3.0 s protected hold, cloth against the cheek | Last frame of approved S007 motion | SAFE_HELD_POSE | Yes | No |
| S012 | Lumi angles the mirror toward the mouth mark; glint | Held frame + overlays + glint | SAFE_DETERMINISTIC_TREATMENT | Yes; the angle change is lost | **Yes** |
| S013 | 4.0 s protected hold | S012 end frame | SAFE_HELD_POSE | Yes | No |
| S017 | Processing hold: Mikko relaxes his cloth hand; Lumi prepares a slight mirror adjustment | Held medium two-shot + nose overlay | SAFE_HELD_POSE | Yes (processing pause); the micro-movements are lost | **Yes** |
| S018 | Lumi adjusts the mirror, then a cut to the macro reflection; one glint | Two-segment shot (G07): brief held setup, then a macro frame + glint | SAFE_DETERMINISTIC_TREATMENT | Yes (macro, glint); the adjustment is lost | **Yes** |
| S019 | 5.0 s protected macro hold | S018 macro frame | SAFE_HELD_POSE | Yes | No |
| S023 | Mikko quietly checks his clear face (small glance) | Held medium two-shot, clean | SAFE_HELD_POSE | Yes | **Yes** (minor) |
| S024 | Camera settles toward the opening composition; small Lumi framing adjustment | Keyframed crop/scale ramp ending on the exact S025 framing (G06) | SAFE_DETERMINISTIC_TREATMENT | Yes (the camera move carries it); the Lumi adjustment is lost | **Yes** |
| S025 | Clean reveal: Mikko's settled gaze, Lumi's soft smile, subtle reveal emphasis + pop | Held F-MIRROR-OPEN clean + reflection + POP-ACCENT treatment + pop SFX | SAFE_DETERMINISTIC_TREATMENT | Yes (the smile must be in the frame); the smile animation is lost | **Yes** |
| S029 | 6.0 s safe-state ending; minimal breathing | Last frame of approved S028 motion, held | SAFE_HELD_POSE | Yes; the breathing is lost (a 6 s freeze risks looking "stopped") | **Yes** |

- **MOTION_MEANING_LOST:** none.
- **Highest-risk:** S006, because its story beat (identification after the pause) depends on timing a still cannot show. If sign-off is refused, S006 becomes a provider shot: +1 video.

## 8. S028_BASE_FRAME_RECOMMENDATION: DERIVE_FROM_APPROVED_S027 (deterministic, zero image spend)
**Inputs considered:**
- **S027 ending:** the approved raw frame index 119, the last frame used in the approved assembled shot. Clean-faced Mikko holds the blue cloth at chest height; Lumi floats holding the pink flower mirror upright; approved bathroom; knees-up two-shot.
- **S028 action:** Mikko passes the cloth to Lumi; she lowers the mirror to her lap and gives one shoulder pat (never the face); Mikko settles beside her; static MEDIUM camera.
- **Dialogue:** Lumi, then Mikko.
- **S029:** a still close two-shot resting, with the mirror and cloth in Lumi's lap.

**Analysis:**
- Every S028 start condition is satisfied by the S027 end frame: both characters, clean face, cloth in Mikko's hand, mirror in Lumi's hand, same environment. This matches the manifest rule `visible_at_start(N) = visible_at_end(N-1)`.
- The S027 knees-up framing reads as medium-close, so MEDIUM is acceptable. There is no visual cut between S027 and S028, only a continuous action change.

**Recommendation:**
- Derive the S028 base frame as the exact raw frame 119 of `MOTION-EP005-S027-SEEDANCE20-CAND-v01` (`86dddea5…0e25`), via G04: exact-index extract, SHA-bound, human-approved.
- **No new S028 frame.** S029 then derives from the approved S028 end frame.

**Conditions and risks for the human:**
1. Accept S028 in S027's framing, with no reframe at the cut.
2. **Lumi has no lap:** she is a floating orb with tiny feet. "Lowers the mirror to her lap" and S029's "in Lumi's lap" need an interpretation, for example "mirror lowered and held low / resting against her".
3. Four sequential actions in 5 s are a high provider risk whichever base frame is used.

**Fallback:** the new F-MEDIUM-TWOSHOT frame from Batch 1 (+0 images, because that frame is needed for S026 anyway). That would cost continuity with S027.

## 9. Dialogue visual-sync matrix (S027 is the only human-approved voice-over; no global rule)
| Shot | Speaker(s) | View | Class | Note |
|---|---|---|---|---|
| S001 | Mikko + Lumi | close mirror; Mikko and reflection | **BLOCKED_BY_VOICE** | Mikko part: VISIBLE_SPEECH_DECISION_REQUIRED (face and reflection both visible) |
| S002 | Mikko | medium, provider motion | VISIBLE_SPEECH_DECISION_REQUIRED | Medium distance makes voice-over more tolerable |
| S003 | Lumi | over-shoulder, Lumi visible | **BLOCKED_BY_VOICE** | then a visible-speech decision (held frame) |
| S004 | Lumi ×2 | over-shoulder, static | **BLOCKED_BY_VOICE** | plus §6 timing |
| S006 | Mikko | close face, static held pose | VISIBLE_SPEECH_DECISION_REQUIRED | A closed-mouth still for a 9-syllable line in close-up is the most noticeable case |
| S007 | Mikko ×2 | close cheek/face, provider motion | LIPSYNC_LIKELY_REQUIRED | about 4 s of speech in a close shot |
| S010 | Lumi | close face-and-mirror | **BLOCKED_BY_VOICE** | |
| S012 | Lumi ×2 | close face-and-mirror, static | **BLOCKED_BY_VOICE** | plus §6 timing |
| S014 | Mikko | close face, mouth region in focus | VISIBLE_SPEECH_DECISION_REQUIRED | The manifest stresses Mikko's **closed mouth**; voice-over keeps it closed, which may actually suit the shot |
| S016 | Lumi | close mirror | **BLOCKED_BY_VOICE** | |
| S018 | Lumi ×2 | mirror adjust, then macro reflection | **BLOCKED_BY_VOICE** | after voice approval: likely VOICEOVER_VISUALLY_SAFE (macro; Lumi's face mostly off-detail) |
| S020 | Mikko | close face ("My nose!") | LIPSYNC_LIKELY_REQUIRED | |
| S022 | Lumi | close face | **BLOCKED_BY_VOICE** | |
| S025 | Lumi | matched mirror, static | **BLOCKED_BY_VOICE** | |
| S026 | Mikko | medium two-shot | LIPSYNC_LIKELY_REQUIRED | The manifest explicitly says "speaks … with **natural mouth movement**" |
| S028 | Lumi + Mikko | medium two-shot | **BLOCKED_BY_VOICE** | Mikko part: VISIBLE_SPEECH_DECISION_REQUIRED |

**Totals:** BLOCKED_BY_VOICE 10 · LIPSYNC_LIKELY_REQUIRED 3 (S007, S020, S026) · VISIBLE_SPEECH_DECISION_REQUIRED 3 (S002, S006, S014) · VOICEOVER_VISUALLY_SAFE 0 now (S018 likely, after voice).
