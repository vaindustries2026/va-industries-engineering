# V&A Industries — Current State, Active Work & Next Actions

**Knowledge-base file:** 3 of 3  
**Checkpoint date:** 30 September 2026  
**Purpose:** The frequently updated operational checkpoint. A new chat should read this file first to know exactly where work stopped and what is currently authorised.  
**Update rule:** Replace/update this file after every meaningful milestone. Keep completed facts, current blockers, current human decisions, the active Claude task, and explicit “do not do” rules current.

---

# 1. Current state in one paragraph

V&A has completed Agent-005 planning/safety stabilisation, approved the clean 29-shot/15-video EP005 production plan, proven Agent-006's real write path once, patched Agent-006 further in an unpublished S5.2 draft, and completed **ENG-20260929-021 / S6.1** for Agent-007. The creative visual-canon workstream has now also reached human approval: **Mikko Master v1.0, Lumi Master v1.0, the Mikko & Lumi Duo Scale Sheet v1.0, and the simplified EP005 Child-Friendly Bathroom Master v1.0 are approved as the visual source-of-truth set.** These approvals are human decisions in Company Brain; operational `asset_registry` registration is still pending. Agent-007 remains unpublished, disconnected, and paid dispatch remains closed.

# 2. Current authoritative EP005 lineage

Approved script:

`14471926-f6fb-4bba-b355-109f3ae9e21c`

Episode:

`EP-CANDIDATE-005 v02 — Three Gentle Wipes`

Approved production plan run:

`A005O-1790400144423`

Approved production manifest:

`670b201b-6793-4518-ad5a-d051eb98d90c`

Current production-plan workload:
- 29 shots;
- 26 image-generation shots;
- 15 video-generation shots;
- 28 compositor shots;
- paid generation not authorised.

Controlled Agent-006 live run:

`A006-1790421221809`

Agent-006 execution:

`520`

Current readiness manifest:

`30b6046e-fe5e-46ab-9b9f-772fa6951efc`

Readiness state:

`NEEDS_HUMAN_REVIEW`

Readiness status:

`REVIEW`

Current requirement result:
- 3 REUSE_EXISTING;
- 3 CREATE_NEW;
- 10 NEEDS_HUMAN_REVIEW;
- 0 BLOCKED.

Do not approve the readiness manifest yet.

---

# 3. Current agent states

## Agent-001

Research path validated. Schedules disabled. Credential may need future permanent OAuth/API strategy.

## Agent-002

Configured and published. Topic/corpus correctness fixed. Paid end-to-end synthesis deferred to a genuine later research run.

## Agent-003

Existing strategy layer. UUID-output cleanup S3-003 still future work.

## Agent-004

UUID identity hardening completed/published on authoritative production model baseline.

## Agent-005

Current safety draft:

`517b11ef-cd04-4779-bb44-a5cdb4d86ac8`

Unpublished.

Pilot production plan is already approved through the deterministic optimisation lineage. Do not modify/publish Agent-005 during current S6.1 work.

## Agent-006

Latest S5.2 draft:

`9bf6bbef-d49a-4f50-bce5-f8f146d43ca8`

Unpublished.

What is proven:
- one controlled real production run passed before S5.2;
- exact manifest UUID gate;
- APPROVED/LOCKED registry semantics;
- visual/audio TBD preservation;
- current draft derives reused SFX shot placement from shot plans and fails closed on conflict;
- three approved SFX storage paths have been corrected.

Do not publish or rerun production Agent-006 yet.

## Agent-007

Published: `45c20c99-eeb2-4067-8065-7923746d3afc`  
Current unpublished S6.1 draft: `b135f8a5-7800-4169-b2f4-9cf3a7d5904d`

Status:
`S6.1_CANON_PROTECTION_CONFIGURED + HUMAN_RESOLUTION_DESIGN_V0.2_READY + PAID_AUTHORISATION_EVENT_MODEL_V0.2_READY + FREE_VALIDATION_PASSED + ZERO_PAID_CALLS + UNPUBLISHED`

Proven:
- exact persisted readiness UUID required;
- caller fake approval/paid fields ignored;
- paid gate before reservation/claim/provider submission;
- paid switch disabled and no persisted paid-authorisation source wired;
- second fresh paid attempt blocked under current conservative policy;
- already-paid provider task can resume without resubmission;
- canonical match blocks duplicate creation;
- registry candidate path is pre-read + insert-only/ignore-conflict;
- existing REVIEW/APPROVED/LOCKED rows cannot be downgraded by replay;
- new candidates remain REVIEW only;
- parent Execute Workflow trigger remains disconnected;
- no production Agent-007 execution occurred.

Later publication-readiness items: node-13 reporting truth, replay-safe history writes in nodes 09/14, unreachable test/orphan cleanup, and optional 01C diagnostic improvement. Do not publish/connect Agent-007 yet.

## Agent-000

Not built yet by design.

---

# 4. Latest completed engineering milestone — ENG-20260929-021

S6.1 completed without provider calls, production writes, migrations or publication.

### Agent-007 canon protection
- baseline S6 draft `42ce4565...` matched expected with no drift;
- new draft `b135f8a5...` has 76 nodes; published version remains `45c20c99...`;
- node-10 path changed from merge-upsert to pre-read + insert-only `ON CONFLICT DO NOTHING` + confirmation;
- existing REVIEW/APPROVED/LOCKED rows preserved; differences reported only;
- new candidates still register REVIEW;
- T-S61-1 through T-S61-7 and critical S6 safety regressions passed;
- harness archived; watched production checksums unchanged.

### Governance designs
Human-resolution v0.2 now specifies append-only decisions, exact scope, advisory locking, structural anti-fork constraints, READ COMMITTED writers and concurrency tests. Paid-authorisation v0.2 now specifies append-only GRANT/REVOKE events, exact-scope current-grant view, expiry/revocation/consumption, advisory locking and proposed atomic grant consumption at reservation. Neither is migrated or wired.

### Company Brain reconciliation
S6.1 is accepted. No further Agent-007 patch is authorised now. Before future migration, verify server-side provenance identity semantics under `SECURITY DEFINER`/Supabase PostgREST. Before Agent-007 publication, revisit node-13 reporting and nodes 09/14 history writes. A later human-authorised second fresh paid attempt would require a separate policy/workflow change because the current attempt cap remains 1.

# 5. Current unresolved EP005 asset decisions

Agent-006 currently sees 16 total requirements.

Already governed reuse:
- Lumi clue chime;
- Mikko TRY whoosh;
- WIN sparkle chord.

Existing upstream NEW_REQUIRED:
- berry-smudge overlays;
- soft cloth;
- tiny hand mirror.

Unresolved human-review requirements include:
- Lumi visual character asset;
- Mikko visual character asset;
- canonical environment/background;
- mirror glint treatment;
- mirror reflection/compositing treatment;
- soft completion-pop visual accent;
- AMBIENCE;
- FOLEY_CLOTH;
- COMPLETION_SFX;
- FOLEY_TOUCH.

Current governance recommendation for those 10 TBD requirements:

**CREATE_CANONICAL_ASSET (6):**
- Lumi;
- Mikko;
- environment;
- ambience;
- cloth foley;
- completion-pop audio.

**COMPOSITOR_ONLY_NO_ASSET (3):**
- mirror glint;
- reflection/compositing treatment;
- completion-pop visual accent.

**DEFER (1):**
- FOLEY_TOUCH.

These are recommendations only; no decision rows have been persisted yet.

---

# 6. Current human-resolution design state

Human-resolution design **v0.2** is complete and accepted as the current architecture proposal, but **not migrated**. It uses append-only immutable history, exact manifest+requirement scope, derived current state, explicit supersession, transaction-scoped advisory locking, structural anti-fork backstops, READ COMMITTED writers, deterministic Agent-006 consumption and no LLM control path. No schema object or decision row exists yet.

Future migration-review item: verify trusted caller/provenance identity semantics for the proposed `SECURITY DEFINER` trigger under the real Supabase/PostgREST path.

# 7. Current paid-authorisation design state

Paid-authorisation event-model **v0.2** is complete and accepted as the current architecture proposal, but **not migrated or wired**. It uses append-only GRANT/REVOKE events, exact scope, derived current-live view, expiry/revocation/consumption semantics, advisory locking and proposed atomic consumption at reservation.

Current system still has no paid-authorisation persistence. Agent-007 remains closed: `PAID_DISPATCH_SWITCH = DISABLED`, persisted authorisation unavailable/null, zero new paid dispatch can pass. The design's 72-hour expiry is still a policy knob to confirm later.

# 8. Active Claude task

**None. S6.1 has returned, been reconciled and accepted.**

Do not issue another Agent-007 engineering task merely because the workflow is unpublished. Engineering resumes only for a separately authorised governance migration, Agent-007 publication cleanup, exact paid-production stage, or future Agent-000 work.

# 9. Immediate next action

**Persist the approved visual canon into the operational asset layer without generating anything new.**

Approved visual canon:
- `CHAR-MIKKO-MASTER-v01` — exact file `Mikko Master.png` — human APPROVED.
- `CHAR-LUMI-MASTER-v01` — exact file `Lumi Master.png` — human APPROVED.
- `DUO-MIKKO-LUMI-SCALE-v01` — exact file `Duo Scale.png` — human APPROVED reference.
- `WORLD-EP005-BATHROOM-MASTER-v01` — exact file `Bathroom master.png` — human APPROVED EP005 environment reference.

Next engineering stage should be a bounded **canon registration only** task: store the exact approved files durably, register the Mikko/Lumi/environment assets as `APPROVED` with exact requirement aliases, preserve provenance/hashes, and do not publish Agent-007, run generation providers, or approve readiness. The duo scale sheet may be stored as an approved reference asset but is not required to satisfy Agent-006.

After registration, move to EP005-specific visual assets: simple hand mirror, simple cloth, and three separate berry-smudge overlays plus the `3 → 2 → 1 → 0` state guide.

# 10. Planned sequence from here

The intention is to **pause infrastructure work** and solve the real creative bottleneck.

Next workstream:

1. **Register approved visual canon operationally** — Mikko, Lumi and EP005 bathroom; preserve the duo sheet as approved scale reference.

2. **EP005 prop/effect production pack** — create clean standalone hand mirror, simple cloth, three berry-smudge overlays and a deterministic `3 → 2 → 1 → 0` state guide.

3. **Approve/register EP005 prop/effect assets** only after visual QC.

4. **Audio/world-support pack** — ambience, cloth foley and completion-pop audio; keep FOLEY_TOUCH deferred unless needed.

5. **Channel visual-style bible refinement** — now based on approved character masters and the low-clutter environment hierarchy.

6. **Persist the remaining human requirement decisions** when the v0.2 decision mechanism is authorised/migrated.

7. Finalise/approve human-resolution DB design.

8. Record explicit EP005 human decisions.

9. Run one fresh Agent-006 resolution with persisted decisions.

10. Only then consider readiness approval and exact paid authorisations for any actual generation.

11. Publish/connect Agent-007 only when all safety/governance prerequisites are met.

12. Agent-000 comes later.

---

# 11. Current stop / safety rules

A new chat must stop and ask/reconcile if:

- live workflow version differs from this checkpoint unexpectedly;
- a REVIEW candidate appears canonical without explicit human approval;
- any paid provider call would occur without exact persisted permission;
- a task needs billing/credits/subscription changes;
- a historical row would need deletion/rewriting to make a test pass;
- a prompt/model/provider change appears outside the authorised task;
- unpublished is being treated as non-executable by assumption;
- visual canon is being invented from behavioural text alone;
- Agent-007 parent trigger would be connected before human-decision persistence, paid-authorisation persistence (if spending is enabled), publication review and explicit human authorisation;
- someone suggests “just run Agent-007” without an exact readiness + paid-authorisation contract.

---

# 12. Historical states that remain intentionally untouched

Historical old approved/review manifests and old readiness manifests are preserved as evidence. Some older rows may still technically carry statuses that would have been accepted by the old workflow.

Do not rewrite history merely to simplify state.

The current safe practice is exact UUID discipline plus hardened current gates.

---

# 13. What a brand-new chat should understand immediately

If you are a new ChatGPT/Claude session, assume:
- latest completed engineering milestone is **ENG-20260929-021 / S6.1**;
- there is **no active Claude engineering task**;
- Agent-005 pilot planning is effectively complete for EP005;
- Agent-006 has one successful real resolution run and an unpublished S5.2 patch;
- Agent-007 current safety draft is `b135f8a5...`, unpublished, parent trigger disconnected, paid gate closed, canon-downgrade risk fixed;
- human-resolution v0.2 and paid-authorisation v0.2 are proposals only; no migrations applied;
- no paid generation is authorised;
- human-approved visual canon now exists for Mikko, Lumi, duo scale and the EP005 bathroom, but operational registry registration is still pending;
- the bathroom style is intentionally quiet and low-clutter: mostly cream/beige/soft neutral surfaces, with stronger colour reserved for characters and story-focus props;
- current priority is **canon registration**, then EP005 mirror/cloth/smudge production assets;
- the old mirror A02 is now reference-only unless it matches the new bathroom/prop direction; old cloth A01 and berry-smudge A01 remain rejected as canon.

# 14. How to maintain these three knowledge-base files

After each major milestone:

### Update this current-state file

Replace stale “current” values with the new truth:
- current workflow versions;
- latest run IDs;
- current pending task;
- blockers;
- next action.

### Update Architecture file only if architecture changed

Examples:
- new agent responsibility;
- new gate;
- published workflow status change;
- new data model adopted;
- Agent-000 becomes real.

### Append to Technical Playbook when a new reusable lesson is proven

Do not add ordinary execution logs. Add only lessons likely to save future time, money or mistakes.

This three-file discipline is intended to replace sprawling checkpoint folders.

---

# 15. Evidence basis

Current state derives from:
- engineering changelog through ENG-20260929-021;
- Agent-005 S4B/S4B.2/recovery/optimisation evidence;
- Agent-006 S5/S5.1/S5.2 evidence;
- Agent-007 S6 safety report v1.1 and S6.1 draft/export;
- S6.1 free-validation harness/results;
- human-resolution mechanism design v0.2;
- paid-authorisation event-model design v0.2;
- EP005 asset-governance recommendations;
- technical inspection of the three candidate images;
- Company Brain visual-QC decisions and S6.1 reconciliation from this chat.

**Important current boundary:** S6.1 is completed and accepted. The four visual reference files listed above are now human-approved canon, but they are not yet persisted as canonical registry rows. No governance migration, Agent-006 rerun, Agent-007 publication/connection, readiness approval or paid generation has been authorised.
