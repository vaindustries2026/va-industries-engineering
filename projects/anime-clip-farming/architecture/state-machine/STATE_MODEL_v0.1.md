# Engine 2 — State Model v0.1

**Status:** PROPOSED — DESIGN ONLY.
**Enforcement (proposed):** `cf.allowed_transitions` rows + `cf.guard_status_transition()` trigger in `../data-contracts/migrations-draft/0001_cf_backbone.DESIGN_ONLY.sql`. Every edge below is a row there; anything not listed is rejected with `CF_INVALID_TRANSITION`.

---

## 1. Principle

One shared **vocabulary**, many small **per-object machines**. A status word means the same thing everywhere it is allowed, but each object type has its own explicit allowed edges. No object uses all nine words.

Status is owned by code. A model may *recommend* (`recommend_for_review`, `model_rank`, `narration_independence_selfcheck`); it can never write a status.

## 2. Shared lifecycle vocabulary (9 words, unchanged from the brief)

| Status | Exact meaning | Allowed on | Who may set it | Human approval? |
|---|---|---|---|---|
| `IDEA` | Machine-generated proposal, not yet checked or queued for a human | research_candidates, editorial_opportunities | CF-001, CF-003 at insert | No |
| `DRAFT` | Object exists and may still be edited by its owning agent | reference data, scenes, scripts, source packages, manifests, assets, renders | owning agent at insert | No |
| `REVIEW` | Content frozen; waiting for a named human gate decision | editorial_opportunities (G1), content_scripts (G2), publication_source_packages (G3), renders (G4) | owning agent, deterministically, after validation passes | No (entering); exit needs G-decision |
| `APPROVED` | An effective human gate decision approves this exact ID + content hash | the four gated objects only | `cf.record_gate_decision()` only | **Yes** |
| `REJECTED` | Will not proceed. Final for this ID (a new revision gets a new ID) | research_candidates, scenes, opportunities, scripts, packages, manifests, assets, renders | gate decision (gated objects) or deterministic validation failure | Gate objects: yes. Others: no |
| `BLOCKED` | Cannot proceed until an external condition changes; not a failure | reference data, scenes, opportunities, scripts, packages, manifests, platform_posts | deterministic code | No (leaving BLOCKED is a human admin action where allowed) |
| `READY` | Validated and usable by the next stage without a human gate | reference data, research_candidates, scenes, manifests, assets, published_content, platform_posts | deterministic code | No |
| `PUBLISHED` | Live on an external platform with a recorded external ID | published_content, platform_posts only | CF-008 after the platform confirms | Needs prior G4 + flags (see gates) |
| `RETIRED` | No longer used; kept for history. Never deleted | all lifecycle objects | deterministic (stale/superseded), human admin, or G-REVOKE for approved objects | Approved objects: yes (REVOKE) |

**Transition modes:** `DETERMINISTIC` (code decides from facts), `HUMAN_GATE` (needs an effective G1–G4 decision), `HUMAN_ADMIN` (a person resolves a block or retires a record; logged, not an editorial approval). There is no `EDITORIAL` mode that a model can trigger: editorial judgement enters only through the human gates.

## 3. The one justified addition: run state

`agent_runs.run_state` and `production_jobs.run_state` use a **separate** enum: `QUEUED → RUNNING → SUCCEEDED | FAILED | CANCELLED`.

Reason: "the render job crashed" is execution state, not a content lifecycle fact. Putting `RUNNING`/`FAILED` into the content vocabulary would make every content object ambiguous ("is FAILED a rejected idea or a crashed job?"), which is the giant-state-machine problem the brief warns against. **For human decision** (D-STATE-1): accept the separate run-state enum.

## 4. Per-object machines

Notation: `A → B [mode]`. `NEW` = row insert.

### 4.1 Reference data — anime_franchises, anime_titles, anime_source_episodes
```
NEW → DRAFT [DETERMINISTIC]
DRAFT → READY [DETERMINISTIC]     external ID resolved or natural key unique and complete
DRAFT → BLOCKED [DETERMINISTIC]   AMBIGUOUS_SOURCE_IDENTITY (e.g. two AniList matches)
BLOCKED → READY [HUMAN_ADMIN]     a person picks the correct identity
READY → RETIRED [HUMAN_ADMIN]
```
Invalid: anything → APPROVED/REVIEW/PUBLISHED; RETIRED → anything.

### 4.2 research_candidates (CF-001)
```
NEW → IDEA [DETERMINISTIC]
IDEA → READY [DETERMINISTIC]      evidence non-empty, title READY, no contamination flags
IDEA → REJECTED [DETERMINISTIC]   validation failed (wrong topic, wrong franchise, no evidence)
READY → RETIRED [DETERMINISTIC]   observation window older than the freshness limit
```
Invalid: IDEA → APPROVED (CF-001 has no gate and must not approve), READY → IDEA.

### 4.3 anime_scene_intelligence (CF-002)
```
NEW → DRAFT [DETERMINISTIC]
DRAFT → READY [DETERMINISTIC]     provenance complete, episode READY, span valid, no ≥80% overlap flag
DRAFT → BLOCKED [DETERMINISTIC]   missing provenance / episode BLOCKED / possible duplicate
DRAFT → REJECTED [HUMAN_ADMIN]
BLOCKED → DRAFT [HUMAN_ADMIN]
READY → RETIRED [HUMAN_ADMIN]     superseded by a corrected scene
```
Publication status is not a scene state. Invalid: any edge to APPROVED/PUBLISHED.

### 4.4 editorial_opportunities (CF-003, G1)
```
NEW → IDEA [DETERMINISTIC]
IDEA → REVIEW [DETERMINISTIC]     passes validation and is queued for G1 (recommend_for_review is advice only)
IDEA → REJECTED [DETERMINISTIC]   validation failure
IDEA → BLOCKED [DETERMINISTIC]    upstream scene/title not READY
REVIEW → APPROVED [HUMAN_GATE G1 APPROVE]
REVIEW → REJECTED [HUMAN_GATE G1 REJECT]
REVIEW → RETIRED [DETERMINISTIC]  stale: left unreviewed past the freshness limit
APPROVED → RETIRED [HUMAN_GATE G1 REVOKE]
```
Invalid: IDEA → APPROVED, REVIEW → IDEA (content is frozen; make a revision), REJECTED → anything.

### 4.5 content_scripts (CF-004, G2)
```
NEW → DRAFT; DRAFT → REVIEW; DRAFT → BLOCKED (opportunity no longer APPROVED); DRAFT → RETIRED (abandoned draft)  [DETERMINISTIC]
REVIEW → APPROVED [G2 APPROVE];  REVIEW → REJECTED [G2 REJECT];  APPROVED → RETIRED [G2 REVOKE]
```
Approving a new revision while an older one is APPROVED: revoke the older one first (one APPROVED per candidate is a UNIQUE rule).

### 4.6 publication_source_packages (CF-005, G3)
```
NEW → DRAFT; DRAFT → REVIEW; DRAFT → BLOCKED (NO_ACCEPTABLE_SOURCE | HUMAN_REVIEW_REQUIRED); BLOCKED → RETIRED  [DETERMINISTIC]
REVIEW → APPROVED [G3 APPROVE];  REVIEW → REJECTED [G3 REJECT];  APPROVED → RETIRED [G3 REVOKE]
```
`BLOCKED` with an `APPROVED` script is a legitimate end state (proven by static test T-SRC-02).

### 4.7 production_manifests (CF-006)
```
NEW → DRAFT; DRAFT → READY; DRAFT → BLOCKED; DRAFT → REJECTED; READY → RETIRED  [all DETERMINISTIC]
```
READY requires: script APPROVED (G2 effective), package APPROVED (G3 effective) for the same script, schema validation pass.

### 4.8 content_assets (CF-007)
```
NEW → DRAFT; DRAFT → READY (checksum + probe verified); DRAFT → REJECTED  [DETERMINISTIC]
READY → RETIRED [HUMAN_ADMIN]
```

### 4.9 renders (CF-007, G4)
```
NEW → DRAFT; DRAFT → REVIEW (file verified, manifest compliance check passed); DRAFT → REJECTED  [DETERMINISTIC]
REVIEW → APPROVED [G4 APPROVE, with approved_platforms];  REVIEW → REJECTED [G4 REJECT];  APPROVED → RETIRED [G4 REVOKE]
```

### 4.10 published_content and platform_posts (CF-008)
```
published_content:  NEW → READY [DET]; READY → PUBLISHED [DET, first platform confirms]; READY → RETIRED, PUBLISHED → RETIRED [HUMAN_ADMIN]
platform_posts:     NEW → READY [DET]; READY → PUBLISHED [DET, external ID + time recorded]; READY → BLOCKED [DET, upload failed / flag off]
                    BLOCKED → READY, BLOCKED → RETIRED, PUBLISHED → RETIRED [HUMAN_ADMIN]
```
`READY` on a platform post means "authorised and queued", never "publish without checking": CF-008 re-reads `cf.v_publish_eligibility` and `PUBLISH_ENABLED` immediately before each upload.

### 4.11 Objects without status
`gate_decisions` (decision value, append-only), `performance_snapshots` and `content_learning_log` (append-only history), `editorial_opportunity_scenes`, `publication_source_items` (append-only children frozen with their parent).

## 5. APPROVED vs APPROVED_FOR_PUBLISH

The blueprint names G4's outcome `APPROVED_FOR_PUBLISH`. Options:

| Option | Pros | Cons |
|---|---|---|
| A. New status `APPROVED_FOR_PUBLISH` on renders | Readable in a table browser | Adds a tenth word used by one object; status alone still doesn't say *which* platforms; tempts other objects to grow `APPROVED_FOR_X` variants |
| **B. Status `APPROVED` + G4 gate decision (recommended)** | Vocabulary stays at nine; the G4 decision row carries the reviewer, time, hash and `approved_platforms`; CF-008 must validate the decision anyway | Meaning depends on reading the gate (`G4` = final QC / publish approval) |

**Recommendation: B.** "Approved for publish" is precisely "render APPROVED by an effective G4 decision whose `approved_platforms` includes this platform", exposed as `cf.v_publish_eligibility`. Publication additionally needs `PUBLISH_ENABLED = true` and the sprint/item authorisation. **For human decision** (D-STATE-2).

## 6. Stale-state rule

A downstream agent re-reads upstream status inside the same transaction that writes its output (`SELECT … FOR SHARE`). If an upstream approval was revoked between reading and writing, the write fails closed (`STALE_UPSTREAM_STATE`). The gate function locks the object row (`FOR UPDATE`) and rejects stale reviews via `p_expected_sha256`.
