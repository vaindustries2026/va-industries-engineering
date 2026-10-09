# S027 dialogue visual sync: options for Company Brain (nothing executed)

S027_DIALOGUE_VISUAL_SYNC_DECISION = **PENDING_HUMAN**

## Option A: voice-over accepted
- **What:** keep the approved raw motion unchanged. Mix M1 at 0.500 s, so "We did it!" lands on Mikko's main shoulder lift (0.8–1.6 s) and the line ends at 1.73 s, with the chord from 1.917 s.
- **Benefits:**
  - Zero spend, and no new provider or model.
  - Every approved asset stays byte-exact (frame, raw motion, M1).
  - The only remaining work is the compositor dialogue patch, plus its authorisation.
- **Risks:**
  - Mikko's mouth stays in a closed smile while he "speaks". Preschool viewers may read it as off-screen or inner voice. It could also look like a defect if other shots do lip-sync.
  - It sets a precedent for the episode that should be decided once, for all 17 voice shots.
  - The manifest says "Mikko says…" but does not explicitly require visible mouth movement. This is an interpretation for the human to make.

## Option B: lip-sync required (minimum additional step)
- **Minimum step:** one video-plus-audio lip-sync pass over the **approved raw motion** (`86dddea5…0e25`), driven by the **approved M1 clip** (`81a0b038…da50`), changing only the mouth region. The output is a new derived candidate (for example `MOTION-EP005-S027-LIPSYNC-CAND-v01`), status REVIEW. The raw source stays registered and unchanged.
- **Prerequisites,** each needing its own authorisation:
  1. **A verified lip-sync route.** None exists in the verified Higgsfield API contract (Seedance 2.0 and Kling 3.0 image-to-video only) or the read-only Higgsfield catalog. A provider and model must be chosen, and its official contract verified, before any spend.
  2. **Spend authorisation:** one attempt, bound to both input SHAs.
  3. **Transport support:** an Agent-008 provider adapter for a video+audio input (the current transport is image-to-video only).
  4. **QC and approval:** human QC of the new candidate by exact SHA, then storage and registration as a new SHOT_MOTION row.
- **Benefits:** Mikko visibly speaks. This matches the conventional preschool animation standard and keeps continuity if other dialogue shots are lip-synced.
- **Risks:**
  - A new provider means new spend and new contract-verification work.
  - Mouth-region models on stylised 3D characters can distort the muzzle or teeth, or change the smile. That puts the already-approved identity at risk, and it may need retries, which would need new authorisations.
  - The output is a re-encoded derivative, so the approved raw pixels change.
  - Doing it per shot multiplies cost across the episode's voice shots.
- **Alternative B′:** regenerate S027 with a provider that takes audio input natively. This is ruled out here, because the approved motion would not be preserved and regeneration is forbidden.

## Deciding factor
The choice should be made at **episode level**, for all dialogue shots, not just S027. The compositor patch is needed under both options.
