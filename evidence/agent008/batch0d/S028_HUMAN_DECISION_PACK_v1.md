# S028 human decision pack v1 (Batch 0D)

**Not generated, not rendered. The final decision belongs to Gilang / Company Brain.**

Sources:
- Approved script v02 14471926, `production_script_json.shots[27]`
- Approved manifest 45cc7493, `shot_plans[27]`
- Agent-008 spec from the v2 capture
- `S028_DERIVED_FRAME_SPEC_v1.json` (Batch 0C)
- `S028_G09_FIT_SIMULATION_v1.json`

## 1. Authoritative shot
| Item | Authoritative value |
|---|---|
| Shot / section | S028 / COMFORT; episode 109.0–114.0 s |
| Duration | **5.0 s = 120 frames @ 24 fps** |
| Action (script) | "Mikko passes Lumi the cloth. Once the success chord has faded, she gives one cozy cloth pat on his shoulder. Mikko settles beside her." |
| Visual (script) | "Comfortable medium two-shot. Lumi lowers the mirror to her lap." |
| Approved interpretation | "Lumi lowers the mirror to a relaxed resting position in front of her lower body while floating." |
| Camera (manifest) | Eye-level, gentle front-facing; static hold, natural character movement only; no push-in, pan or reframing; framing_scale **MEDIUM** |
| Music | None; the S027 chord has already faded |
| Audio | Quiet ambience bed (AMB-BATHROOM-QUIET-v01). FOLEY-CLOTH-SOFT-v01, one-shot, at the hand-off/pat. No pat sound (FOLEY_TOUCH dropped). |
| Overlays / treatments | None (spec: `active_overlays: []`, `treatments: []`) |

## 2. Dialogue (exact, authoritative v02; no amendment applies to S028)
| Order | Speaker | Exact text | Voice | Estimated speech | Estimated clip file (lead + speech + tail) |
|---|---|---|---|---|---|
| 1 | Lumi | You look comfy. Story time. | Lola `f9imtLc2jfOLXtqe3Ihb` | 7 syl → 2.36 s at the measured L1 rate (2.96 syl/s); 2.33–2.66 s planning range | ≈ 2.87–3.16 s |
| 2 | Mikko | I’m ready to rest. | Teddy Twinkle `XjGYkUkzth8BPs29fmcV` | committed estimate ≈ 1.64–1.84 s; likely shorter at the S027 M1 measured pace | ≈ 2.08–2.28 s |

The lead and tail come from measured takes:
- L1 audition: 0.08 / 0.42 s.
- S027 M1: 0.04 / 0.395 s.

**Speech alone** totals ≈ 4.0–4.5 s of 5.0 s. Both lines must sit alongside the hand-off, the pat and the settle.

## 3. Dialogue timing window and holds (G09)
Shot window: 0.000–5.000 s.

Proposed holds:
- Pre-hold 0.25 s: hand-off begins before Lumi speaks.
- Post-hold 0 s: the shot may end on Mikko's line tail. S029 then holds 6 s of silence (ambience only).

**G09 simulation** (synthetic clips sized to the estimates; no TTS):

| Scenario | Plan | G09 result |
|---|---|---|
| L1 measured rate (Lumi 2.865 s file, Mikko 2.075 s) | strictly sequential files | **FAIL_CLOSED `DIALOGUE_OVERRUNS_SHOT`** (ends 5.19 s) |
| L1 measured rate | Mikko starts inside Lumi's silent tail: authorised overlap ≤ 0.40 s | **PASS**: Lumi 0.250–3.115, Mikko 2.715–4.790, tail hold 0.21 s |
| slowest estimate (3.162 / 2.275 s) | authorised silent-tail overlap 0.40 s | **FAIL_CLOSED `DIALOGUE_OVERRUNS_SHOT`** (ends 5.29 s) |

**Finding: TIGHT. S028 fits only when:**
- the takes come out near the measured voice rates, and
- a human authorises Mikko's clip to start inside Lumi's trailing silence.

That overlap covers silence only. The audible turn gap would be about 0.05–0.10 s, which is a brisk hand-over.

G09 fails closed otherwise. Nothing is trimmed or stretched silently.

Fallbacks, if the generated takes do not fit:
- **(a)** re-take at a slightly faster delivery (TTS spend);
- **(b)** a new governed deterministic edge-silence trim of dialogue clips (new scope, not implemented);
- **(c)** a script change (not proposed).

Final start times can only be set from measured, approved clips.

## 4. Character, prop and camera state
| | Start (= S027 end, raw frame 119) | During | End (= S029 start) |
|---|---|---|---|
| Mikko | Screen-left; blue cloth in hand at chest height; clean face; gentle smile | Passes the cloth to Lumi (readable, central, unobstructed) | Settled beside Lumi, relaxed, clean face visible |
| Lumi | Screen-right, floating glowing orb; holds the pink flower mirror upright; warm expression | Takes the cloth; one cozy cloth pat on Mikko's **shoulder only** (never the face); lowers the mirror | Floating relaxed; mirror and cloth resting in front of her lower body ("lap" interpretation) |
| Mirror | Upright in Lumi's hand, clean glass | Controlled lowering; glass stays clean and the reflection consistent | Resting low in front of Lumi's lower body |
| Cloth | Mikko's hand | Hand-off → Lumi; used only for the single pat | With Lumi, at rest |
| Camera | S027 knees-up framing (medium-close) | Locked; no reframe | Same framing |

## 5. Continuity
**S027 → S028:**
- `visible_at_start(S028) = visible_at_end(S027)`.
- No smudges; mirror held by Lumi with clean glass; reflection present; cloth within Mikko's reach; no glint.
- All are satisfied by raw frame 119, the last frame used by the approved S027 shot (7b01c392…8fde).
- There is no cut, only a continuous action change.

**S028 → S029:** both relaxed and settled, clean face visible, mirror and cloth resting low with Lumi, no new effects. S029 is derived from the approved S028 motion's last used frame via G04 and held for 144 frames (G02).

**Framing note for the human (confirm, not a new gate):**
- Manifest scales: S027 CLOSE, S028 MEDIUM, S029 CLOSE.
- Deriving from frame 119 keeps the S027 framing throughout, which reads as medium-close.
- This was the Batch 0 recommendation ("accept S028 in S027's framing"), and the frame-119 direction is now approved.
- Confirm that the manifest MEDIUM / CLOSE labels are satisfied by that single continuous framing.

## 6. Base frame
- **Is derived frame 119 sufficient? YES, subject to human QC of the exact PNG.**
  - It is the authoritative start state.
  - Lossless G04 extract (no crop, no scale, 1920×1080).
  - The source is the approved raw `86dddea5…0e25` (121 frames, 24/1).
  - Risk: a motion frame may carry slight motion blur. If QC finds a defect, STOP and propose.
- **Is a new generated still unnecessary? YES.** Generating one would risk a continuity break with S027 and adds image spend.

## 7. Visual speech classification: **VISIBLE_SPEECH_DECISION_REQUIRED**
Engineering reasoning:
- Both speakers are on screen in a static two-shot with faces readable, for the whole shot.
- Speech covers about 80% of the 5 s, against about 1.2 s audible in S027.
- Seedance motion is generated without audio and without lip-sync, so the mouths will not track the words.
- S027's voice-over acceptance was explicitly S027-only.
- Not `VOICEOVER_VISUALLY_SAFE`: faces are visible and both characters speak.
- Not `LIPSYNC_LIKELY_REQUIRED`:
  - the dialogue is soft and short;
  - characters' attention is on the hand-off and pat, not on camera;
  - a cartoon register tolerates gentle non-articulated mouth motion;
  - no lip-sync capability is in scope (Agent-008 G09 excludes it).

**Recommendation (not a decision):** accept voice-over for S028 under the same S027 pattern, with two additions:
- **(i)** the Seedance motion brief asks for small, soft mouth movement for Lumi early in the shot and for Mikko late, without exaggerated articulation;
- **(ii)** human QC judges the visual speech on the raw motion before assembly.

If that is rejected, S028 needs a lip-sync capability, which is new scope plus spend.

## 8. Agent-008 support after G09
- Spec: SPEC.
- Code gaps: **none**. G04 covers the derived frame, `compose_motion_shot` the motion assembly, and G09 the dialogue timing.
- `compose_motion_shot` handles S028 completely: no overlays or treatments; ambience bed; FOLEY-CLOTH-SOFT-v01 as a timed one-shot; two dialogue slots governed by G09.
- **Technically supported; not production-ready.**

## 9. Remaining production assets / actions (none authorised)
1. S028 derived frame: create via G04 → human-approve the PNG SHA → authorised storage write → register SHOT_FRAME/DERIVED_FRAME.
2. Lumi TTS ×1, "You look comfy. Story time.", voice f9imtLc2jfOLXtqe3Ihb → approve → register AUDIO/DIALOGUE.
3. Mikko TTS ×1, "I’m ready to rest.", voice XjGYkUkzth8BPs29fmcV → approve → register AUDIO/DIALOGUE.
4. Seedance 2.0 image-to-video ×1 (5 s, 1080p, ≈ $3.40 list), from the approved derived frame → raw approval → register RAW_MOTION_SOURCE.
5. G09 timing plan from the measured clips (start times, the authorised silent-tail overlap if needed), plus FOLEY-CLOTH-SOFT-v01 timing from the approved motion.
6. Deterministic assembly (2 renders, byte-identical) → final QC → register SHOT_RENDER/ASSEMBLED_SHOT.

Paid actions in this task: 0. Frames created: 0.
