# V&A Industries — Architecture Progress & System Design

**Knowledge-base file:** 1 of 3  
**Checkpoint date:** 30 September 2026  
**Purpose:** Durable architecture, system progress, governance and design principles that should survive individual chats and individual projects.  
**Update rule:** Update this file only when the architecture, agent responsibilities, source-of-truth model, governance gates, or a major system capability materially changes.

---

# 1. What V&A is building

V&A is not only building a YouTube Kids episode pipeline. It is building a **human-governed AI production operating system** that can later be reused across other channels and businesses, including Viva's future YouTube clip-farming/anime channel.

The operating principle is:

> **Humans decide the goals, canon, approvals and spending. AI systems perform bounded work inside explicit rules, return evidence, and fail closed when state is unclear.**

The target end-state is not “one big autonomous agent.” It is a deterministic operating system in which specialist agents perform narrow roles and a future Agent-000 orchestrates them.

---

# 2. Core system architecture

```text
Humans: Gilang / Viva / FIFA
    │
    │ strategy, approval, canon, spend authority
    ▼
ChatGPT — Company Brain
    │
    │ architecture, governance, reconciliation,
    │ bounded Claude engineering prompts
    ▼
Claude — Engineering Operator
    │
    │ live n8n/Supabase inspection,
    │ bounded edits, testing, rollback evidence
    ▼
n8n — Execution Engine
    │
    ├── Agent workflows
    ├── deterministic gates
    ├── API/provider dispatch
    └── test harnesses
    │
    ▼
Supabase — Operational State
    │
    ├── episode state
    ├── scripts
    ├── shot plans
    ├── manifests
    ├── asset-resolution records
    ├── asset creation jobs
    └── canonical asset registry

Supporting layers:
- Slack: research/command surface now; possible future Agent-000 command surface.
- Project files / Drive: human-readable checkpoint and knowledge layer.
- Future GitHub: engineering/versioned artifacts where useful.
```

The rule for engineering handoff is:

> **ChatGPT decides and bounds → Claude engineers → Claude returns raw evidence → ChatGPT reconciles → humans approve the next bounded step.**

Claude must never become an isolated alternate source of truth.

---

# 3. Source-of-truth precedence

When two sources disagree, use this order:

1. latest explicit human decision from Gilang/Viva;
2. live n8n workflow/version state;
3. live Supabase state;
4. newest engineering changelog / execution evidence;
5. current Company Brain checkpoint documents;
6. older project documents;
7. inference.

**Never silently reconcile contradictions.** A drift or contradiction is a reason to stop and surface the conflict.

This rule has already prevented production mistakes, including an Agent-004 model-baseline drift where the unpublished draft used a different model from the published workflow.

---

# 4. Cross-AI engineering SOP

For every meaningful engineering stage:

1. ChatGPT reads the current checkpoint and latest Claude evidence.
2. ChatGPT defines one bounded task with:
   - exact scope;
   - forbidden actions;
   - free vs paid limits;
   - expected tests;
   - stop conditions;
   - rollback expectations.
3. FIFA/Viva sends the exact prompt to Claude.
4. Claude changes live systems only inside that scope.
5. Claude returns:
   - workflow/version IDs;
   - exact diff;
   - test execution IDs;
   - database before/after evidence;
   - paid-call confirmation;
   - rollback instructions;
   - updated engineering changelog;
   - exports/artifacts.
6. FIFA/Viva returns the full evidence to ChatGPT.
7. ChatGPT accepts/rejects and defines the next bounded stage.
8. A new checkpoint is created at major milestones.

This cross-AI loop is now a reusable V&A operating capability, not a one-off project habit.

---

# 5. Production agent architecture

Current production flow:

```text
Research Router
  ↓
Agent-001 — YouTube Market Scout
  ↓
Agent-002 — Algorithm & Content Intelligence
  ↓
Agent-003 — Content Strategist
  ↓  G1 human episode approval
Agent-004 — Script Architect
  ↓  G2 human script approval
Agent-005 — Storyboard & Shot Production Planner
  ↓  G3 human production-manifest approval
Agent-006 — Asset Resolution & Production Readiness
  ↓  human asset decisions / readiness approval
Agent-007 — Candidate Asset Creation
  ↓  human canon approval
asset_registry APPROVED / LOCKED

Future:
Agent-000 — deterministic orchestrator over the above
```

The architecture deliberately separates **planning**, **readiness**, **asset creation**, and **canon approval**. A generator never gets to declare its own output canonical.

---

# 6. Human governance gates

Persisted gates currently used or designed:

- **G1:** `episode_backlog.status = APPROVED` before Agent-004.
- **G2:** `episode_scripts.status = APPROVED` before Agent-005.
- **G3:** `episode_production_manifests.status = APPROVED` before Agent-006.
- **Readiness gate:** Agent-007 requires an exact persisted readiness manifest with the correct status/state.
- **Canon gate:** only `asset_registry.status IN (APPROVED, LOCKED)` is canonical.
- **Future paid gate:** paid generation must require a persisted exact-scope authorisation, separate from general workflow approval.

A critical principle discovered during this build:

> **“This asset should exist” and “you may spend money generating it” are different approvals and must be stored separately.**

---

# 7. Agent-by-agent current progress

## Research Router

Established as the Slack research command router. It routes human research intent into the research agents.

## Agent-001 — Market Scout

**Status:** functioning research sub-workflow; autonomous schedules intentionally disabled.

Completed improvements:
- disabled stale/broken autonomous schedules;
- repaired YouTube OAuth by human re-authentication;
- validated the live research path;
- preserved manual/sub-workflow invocation.

Known lesson: a Google OAuth app in External + Testing can cause refresh tokens to expire on a short cycle. Long-term credential strategy still needs a permanent solution.

## Agent-002 — Content Intelligence

**Status:** configured/published; static and live pre-model validation passed; paid end-to-end synthesis intentionally deferred.

Completed improvements:
- topic isolation;
- corpus prompt-version filtering;
- dedupe by video ID;
- zero-corpus safe exit;
- `executeOnce` library handling;
- Mikko=DO / Lumi=SEE synthesis framing.

## Agent-003 — Content Strategist

**Status:** existing strategy layer remains usable; stable-identity output cleanup still pending later.

Future identity work: S3-003.

## Agent-004 — Script Architect

**Status:** UUID identity hardening completed and published on the intended production baseline.

Major architecture decisions:
- `episode_backlog_id` is the stable episode identity;
- `episode_code` is display/compatibility identity only;
- exact UUID path is authoritative;
- code-only compatibility path remains fail-closed on ambiguity;
- unpublished model drift was preserved separately rather than silently promoted.

## Agent-005 — Storyboard & Shot Production Planner

**Status:** pilot planning/safety architecture substantially complete; current safety draft remains unpublished.

Agent-005 became the major proving ground for the V&A governance model.

Capabilities now proven:
- exact script UUID identity;
- structured shot planning;
- deterministic source-fidelity checks;
- continuity state tracking;
- child-response hold protection;
- framing/macro constraints;
- music placement validation;
- audio TBD preservation;
- governed asset reuse;
- cost baseline checks;
- fail-closed episode validation;
- deterministic recovery of already-paid model output;
- deterministic human-authorised cost optimisation.

A single real paid planning run generated all 29 shots. The validator caught one structured S022 continuity-start flag after all model calls and refused to create a manifest. Instead of paying for another 29 calls, V&A replayed the already-paid output through corrected deterministic continuity logic, preserved provenance, and recovered it without a second model run.

A later cost review showed 20 proposed video shots could safely be reduced to 15 by converting only S003, S004, S017, S023 and S025 to compositor/static treatment.

The authoritative EP005 production manifest is:

`670b201b-6793-4518-ad5a-d051eb98d90c`

It represents:
- 29 shots;
- 26 image-generation shots;
- 15 video-generation shots;
- 28 compositor shots;
- approved G3 production plan;
- paid generation still not authorised.

## Agent-006 — Asset Resolution & Production Readiness

**Status:** one controlled real production write path has passed; latest hardened draft remains unpublished.

Production proof:
- exec 520;
- run `A006-1790421221809`;
- readiness manifest `30b6046e-fe5e-46ab-9b9f-772fa6951efc`;
- 16 requirements;
- 3 `REUSE_EXISTING`;
- 3 `CREATE_NEW`;
- 10 `NEEDS_HUMAN_REVIEW`;
- 0 blocked;
- zero provider/LLM calls.

Later S5.2 draft improvements:
- exact reused SFX shot attribution from manifest audio placement;
- conflict detection between inventory and actual plan placement;
- corrected three approved SFX storage paths;
- audio/visual TBDs preserved separately;
- explicit APPROVED/LOCKED registry semantics;
- generic placeholder labels removed from exact matching.

## Agent-007 — Asset Creation & Canonicalization

**Status:** published v0.1 remains unchanged, while the current production-safe direction is the **unpublished S6.1 draft**. It must not yet be wired into parent orchestration.

Published version: `45c20c99-eeb2-4067-8065-7923746d3afc`  
Current unpublished S6.1 draft: `b135f8a5-7800-4169-b2f4-9cf3a7d5904d`

Safety architecture now proven in the draft:
- hard-coded smoke-test readiness manifest removed;
- exact readiness UUID must resolve from persisted Supabase state;
- caller-supplied approval/paid fields cannot bypass persisted state;
- paid-dispatch gate sits before reservation, claim and provider submission;
- paid gate remains closed (`PAID_DISPATCH_SWITCH = DISABLED`; no persisted authorisation source wired);
- one new paid attempt per requirement under the current conservative policy;
- already-paid provider tasks may resume without a second submission;
- canonical-asset match blocks duplicate paid generation;
- candidate registration is canon-protecting: pre-read + insert-only `ON CONFLICT DO NOTHING`;
- existing REVIEW/APPROVED/LOCKED rows are preserved and never merge-overwritten;
- genuinely new candidates register REVIEW only;
- parent Execute Workflow trigger remains intentionally disconnected;
- S6.1 free tests passed with zero provider calls, zero production DB writes and no publication.

Non-blocking items for a later publication-readiness pass:
- node 13 can report preserved canonical rows as REVIEW in the batch summary;
- nodes 09 and 14 still use merge-style job/batch history writes and should become replay-safe before final publication.

## Agent-000 — Future Orchestrator

**Status:** not built yet by design.

It should only be built after pre-orchestration stabilisation.

Planned responsibilities:
- deterministic state machine;
- exact persisted IDs across gates;
- idempotency / exactly-once-ish execution;
- approval records;
- budget guard / kill switch;
- status/resume commands;
- no LLM in the core control path;
- no paid action without persisted permission.

---

# 8. Stable identity architecture

One of the biggest structural improvements was moving away from human-readable labels as operational identity.

Rules now established:

- stable UUIDs are authoritative whenever available;
- labels such as `EP-CANDIDATE-005` are presentation/compatibility fields;
- lookups by labels must detect ambiguity and fail closed;
- downstream agents receive and persist exact upstream IDs;
- future Agent-000 should persist the exact UUID from every human gate.

This matters for every future V&A workflow, including Viva's farming channel. Never use a title/channel/video label as the primary automation identity if a stable ID can be persisted.

---

# 9. Asset/canon architecture

Current canon rule:

> **Generated candidate ≠ canonical asset.**

Asset flow:

```text
Requirement
  ↓
Agent-006 resolves exact governed reuse or identifies CREATE_NEW / human decision
  ↓
Agent-007 may create a candidate
  ↓
Candidate remains REVIEW
  ↓
Human visual/semantic approval
  ↓
asset_registry status APPROVED or LOCKED
```

Only APPROVED/LOCKED registry assets may resolve as governed reuse.

REVIEW, mock, test and development assets are excluded.

This prevents AI-generated output from silently entering permanent brand canon.

---

# 10. Human requirement-decision architecture

Human-resolution design **v0.2** is complete as a proposal but **not migrated**.

Core architecture:
- append-only `asset_requirement_decisions` history;
- exact `production_manifest_id + requirement_key` scope;
- corrections supersede prior rows rather than update/delete;
- current decision derived by view; no mutable `is_current` flag;
- deterministic Agent-006 consumption with no LLM control path;
- `CREATE_NEW`, `MAP_EXISTING_CANONICAL`, `COMPOSITOR_ONLY_NO_ASSET`, `DEFER`;
- transaction-scoped advisory locking per exact scope before state checks;
- structural backstops: one root per scope, unique supersede link and same-scope supersession;
- READ COMMITTED writers;
- branch/disposable-schema concurrency and immutability tests before migration.

No table, view, trigger or decision row has been created yet.

Company Brain migration-review note: the proposed triggers are `SECURITY DEFINER`; before migration, verify that server-side provenance records the intended caller identity under the actual Supabase/PostgREST path rather than merely the function owner/database role.

---

# 11. Paid-authorisation architecture

Paid-authorisation event-model design **v0.2** is complete as a proposal but **not migrated or wired**.

Architecture:
- immutable append-only `GRANT` and `REVOKE` events;
- exact scope: readiness manifest + asset-resolution run + requirement + source asset + provider;
- repeated grant → revoke → grant cycles allowed;
- current-valid grant derived by a view, not stored as a mutable boolean;
- grants cease to be current when expired, revoked or consumed;
- at most one live grant per scope using transaction-scoped advisory locking;
- reservation rechecks and consumes the grant atomically;
- one grant can be consumed by one job only;
- caller fields and natural-language statements are never paid permission;
- `PAID_DISPATCH_SWITCH` remains a second independent lock.

Current Agent-007 reads no persisted authorisation and the dispatch switch is disabled, so new paid dispatch is impossible in S6.1.

Policy boundary: the event model supports repeated grant/revoke cycles, but the current conservative `MAX_PAID_ATTEMPTS_PER_REQUIREMENT = 1` still blocks a second fresh paid attempt unless a later separately approved policy/workflow change permits it. Recovery of already-paid work remains distinct.

No paid-authorisation table/view, authoriser table, job-column migration or RPC change has been applied.

---

# 12. Current creative architecture

Locked behavioural canon:

- **Mikko = DO / The Hands** — active physical problem solver; “What can we try?”
- **Lumi = SEE / The Eyes** — observer/guide; “What are we missing?”
- **ONE → CUE → THREE → WIN**
- **NOTICE → CHOOSE → TRY → LEARN → SOLVE TOGETHER**
- preferred duo grammar: Lumi notices → child chooses → Mikko tries → Lumi observes → Mikko adjusts → everyone succeeds.

Important progression after S6.1:

**Behavioural canon and human-approved visual canon now both exist.**

Human-approved visual source-of-truth assets are:
- `CHAR-MIKKO-MASTER-v01` — Mikko Master v1.0;
- `CHAR-LUMI-MASTER-v01` — Lumi Master v1.0;
- `DUO-MIKKO-LUMI-SCALE-v01` — duo relationship/scale reference;
- `WORLD-EP005-BATHROOM-MASTER-v01` — EP005 child-friendly bathroom environment.

The bathroom establishes an important attention-hierarchy rule: **background/world assets should be quieter than the characters.** Use mostly warm white, cream, beige, soft wood and restrained pale accents; stronger colour is reserved for Mikko, Lumi and story-focus props/clues.

These are human-approved creative canon but still need operational registration in `asset_registry` before Agent-006 can resolve them as canonical reuse.

The next creative workstream is episode-specific: standalone mirror/cloth assets, three separable berry-smudge overlays and the controlled `3 → 2 → 1 → 0` state guide; then supporting audio.

---

# 13. How this architecture transfers to Viva's YouTube farming channel

The subject matter can change completely—anime shorts instead of preschool episodes—but the operating system should remain similar.

Reusable pattern:

```text
Research → Strategy → Content Plan → Production Plan → Rights/Asset Readiness
→ Generation/Edit → Review → Publish → Performance Feedback
```

Recommended transfer principles:

- separate **research intelligence** from **content production**;
- keep stable IDs for source clips, franchises, episodes and edits;
- preserve exact source/provenance for every clip;
- use deterministic validators for duration, duplicates, captions, aspect ratio, audio and source rights metadata;
- human approval before publication;
- separate “allowed to use this source” from “allowed to spend money processing it”;
- never let a model declare copyright/licensing permission on its own;
- maintain a canonical registry of reusable templates, overlays, subtitles, sound effects and edit styles;
- use a cost baseline before scaling paid processing;
- keep exact evidence of what generated each output;
- create a knowledge log of every failure so the next channel inherits the fix.

The architecture should be cloned; the business rules/content policies should be channel-specific.

---

# 14. Knowledge-base maintenance rule

This file is one of only three long-lived Company Brain files.

Use the three-file system as follows:

1. **Architecture Progress & System Design** — this file. Curated durable system truth.
2. **Engineering Problems Solved & Reusable Playbook** — append reusable debugging/engineering lessons.
3. **Current State, Active Work & Next Actions** — frequently updated operational checkpoint.

Do not create many overlapping handoffs. When a milestone closes, update these three files instead.

---

# 15. Evidence basis for this checkpoint

Primary source material consolidated into this file:

- `ENGINEERING_CHANGELOG.md` through ENG-20260929-021;
- Agent-005 S4B/S4B.2/recovery/optimisation evidence;
- Agent-006 S5/S5.1/S5.2 evidence;
- `S6_AGENT007_SAFETY_HARDENING_REPORT_v1.1.md`;
- `S52_HUMAN_RESOLUTION_MECHANISM_DESIGN_v0.2.md`;
- `S61_PAID_AUTHORISATION_EVENT_MODEL_DESIGN_v0.2.md`;
- `EP005_ASSET_GOVERNANCE_DECISIONS_v1.0.md`;
- current Company Brain v3.0 checkpoint;
- S6.1 Agent-007 draft/export and free-validation evidence.

**Current boundary:** ENG-20260929-021 / S6.1 is reconciled and accepted. Mikko, Lumi, duo scale and EP005 bathroom references are human-approved visual canon. Operational registry registration remains pending. No governance migration, Agent-007 publication, parent-trigger connection or paid generation is authorised.
