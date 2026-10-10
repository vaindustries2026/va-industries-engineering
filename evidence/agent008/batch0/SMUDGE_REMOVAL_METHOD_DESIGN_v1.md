# S009 / S015 / S021 smudge removal: minimum viable deterministic method (DESIGNED, not implemented)

**Principle:** the provider never decides when a berry disappears. Agent-008 decides, deterministically, from human-keyed values.

## Facts
| Shot | Length | Removed overlay | Persistent overlays | Camera |
|---|---|---|---|---|
| S009 | 1.5 s / 36 frames | CHEEK | MOUTH, NOSE | locked |
| S015 | 3.0 s / 72 frames | MOUTH | NOSE | stable, minimal follow-through |
| S021 | 4.0 s / 96 frames | NOSE | none | locked |

- The approved overlays (`OVERLAY-EP005-BERRY-SMUDGE-{CHEEK,MOUTH,NOSE}-v01`) are static RGBA WebP layers.
- The spec builder already fails closed on these transitions with `OVERLAY_TRANSITION_UNSUPPORTED_V01`, and motion compose fails closed on any overlay. Today they are explicit blockers, not silent ones.

## Options evaluated
| Option | Verdict |
|---|---|
| Let the provider paint and remove the smudge | **Rejected.** Timing and shape would be provider-decided and unreviewable |
| Timed overlay hard-cut (alpha 1→0 over 2–3 frames at a keyed frame) | Viable fallback. Simple, but the smudge can draw over the cloth between cloth arrival and the cut |
| Deterministic reveal sweep along the wipe path (keyed start/end frame, from/to point, feather) | **Chosen.** The smudge erodes just ahead of the cloth's leading edge, so it never sits on top of the cloth |
| Clean-state layer under the berry | Free: generate the provider motion from a base frame **without** the removed smudge. The clean skin then exists in the video. Persistent smudges are pre-composited into that base frame (G03) |
| Motion tracking | **Not required if** the head stays still in the keyed window. That is enforced by a drift QC gate (below). If the gate fails, the shot needs tracking and stays BLOCKED |
| Are the approved overlays sufficient? | Yes. The same asset and anchor used for the baked persistent smudges in adjacent shots guarantees the same look |

## Minimum viable implementation (bounded plan, after G03)
1. **Spec:** replace the hard blocker with `overlay_transitions: [{asset_id, visible_at_start: true, visible_at_end: false}]`. Missing reveal keys fail closed (`OVERLAY_REMOVAL_UNKEYED`).
2. **Timing input** (human-keyed from the approved raw clip; recorded and hashed):
   `{"removal": {"asset_id", "anchor_ref", "start_frame", "end_frame", "from_xy", "to_xy", "feather_px"}}`
3. **Compose:**
   - Allow exactly this overlay kind on motion.
   - Per frame f: `alpha = overlay_alpha × mask_f`, where `mask_f` is 1 before the sweep line and 0 behind it, and the line moves linearly from `from_xy` to `to_xy` between `start_frame` and `end_frame`.
   - Every other overlay on motion still fails closed.
4. **Drift QC gate:** measure the face-region displacement (phase correlation of the anchor ROI, excluding the cloth window) across the shot. Above the threshold (proposed 2 px at 1080p), fail with `OVERLAY_DRIFT_REQUIRES_TRACKING`.
5. **Continuity:** the anchor is carried from the previous shot's approved end frame (S008 → S009, S014 → S015, S020 → S021). The persistent set must equal the previous shot's end state.
6. **Tests:** sweep timing per frame, no overlay pixels behind the line, unkeyed → fail, drift → fail, persistent overlays untouched, determinism.

**Size:** about 150–200 lines plus tests. It depends on G03 (anchors). It is new per-frame overlay architecture in the motion compositor, which today accepts no overlays at all, so per the task rule it is **not implemented** in Batch 0.

**Spend impact:** none for the method. Each shot still needs 1 video (generated from a smudge-free base frame) once approved.
