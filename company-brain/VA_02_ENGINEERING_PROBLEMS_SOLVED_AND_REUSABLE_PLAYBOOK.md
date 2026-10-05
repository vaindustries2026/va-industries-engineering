# V&A Industries — Engineering Problems Solved & Reusable Playbook

**Knowledge-base file:** 2 of 3  
**Checkpoint date:** 30 September 2026  
**Purpose:** Preserve hard-earned debugging lessons, failure patterns, safeguards and reusable engineering techniques so V&A does not solve the same class of problem twice.  
**Update rule:** Append a new entry whenever a problem is materially understood and the fix/lesson is proven. Never delete old lessons simply because the immediate incident is closed.

---

# 1. How to use this playbook

For each new V&A workflow, before inventing a new solution:

1. search this playbook for the failure class;
2. reuse the proven pattern where appropriate;
3. adapt only the domain-specific parts;
4. add the new result back here if the lesson expands.

Every entry below is structured as:

**Problem → Root cause → Proven fix → Reusable lesson → Checklist.**

---

# 2. Source-of-truth drift between published and draft workflows

## Problem

A live Agent-004 draft had silently changed its model while the published production version still used the original model. Editing/publishing the draft would have unintentionally promoted an unrelated model change.

## Root cause

A workflow can have:
- a published/active version;
- a newer unpublished draft;
- human assumptions based on only one of them.

## Proven fix

Before every material edit:
- read published version ID;
- read current draft version ID;
- diff nodes/connections/model settings;
- stop if unrelated drift exists;
- preserve disputed work in an archive rather than overwriting it.

## Reusable lesson

**Never start engineering from “the workflow” as an abstract concept. Start from an exact version ID.**

## Checklist

- [ ] published version ID recorded
- [ ] draft version ID recorded
- [ ] activeVersionId recorded
- [ ] node/model diff checked
- [ ] unrelated drift = stop
- [ ] rollback version identified

This should be mandatory for every future channel.

---

# 3. Human-readable labels used as operational identity

## Problem

Episode codes could repeat across batches. Workflows that used `episode_code + version` could resolve the wrong logical episode or become ambiguous.

## Root cause

Display labels were treated as stable primary keys.

## Proven fix

Move to UUID identity:
- `episode_backlog_id` = stable episode identity;
- `episode_script_id` = stable script identity;
- exact UUID is authoritative;
- label-only compatibility paths detect ambiguity and fail closed.

## Reusable lesson

**Persist IDs, display labels. Do not confuse the two.**

For Viva's clip-farming channel this means using stable IDs for:
- source video;
- anime franchise;
- episode/source segment;
- clip candidate;
- edit version;
- published short.

Never make a title string the operational key.

---

# 4. Broken approval gates caused by expression/literal mistakes

## Problem

An Agent-005 approval IF used a literal string instead of evaluating the actual row ID, so the condition effectively always passed.

## Root cause

Automation tools can silently treat expression-looking text as literal text when syntax is wrong.

## Proven fix

- explicitly use evaluated expressions;
- check both exact identity and persisted approval status;
- add negative tests for REVIEW, missing and malformed inputs.

## Reusable lesson

**Every approval gate needs at least one positive and multiple negative tests.**

Do not assume a visually correct IF node is logically correct.

---

# 5. Wrong-field manifest mappings

## Problem

Agent-005 stored incorrect metrics because fields were mapped to the wrong source values.

## Root cause

Copy/paste mapping errors in long manifest nodes.

## Proven fix

- verify field-to-source mappings against real records;
- create regression tests over historical manifests;
- compare computed values to independent recalculation.

## Reusable lesson

Treat manifest construction like an API contract, not a cosmetic summary.

---

# 6. OAuth works today, fails a week later

## Problem

Agent-001 YouTube OAuth stopped working after previously succeeding.

## Root cause

Google OAuth app was External + Testing, which can result in short-lived refresh-token behaviour.

## Proven fix

Human disconnected/re-authenticated the credential and validated a live research path.

## Reusable lesson

When a connector “randomly expires,” inspect the provider's app publishing/testing mode before rebuilding the workflow.

Long-term options should be designed separately:
- production/published OAuth app where appropriate;
- API key for public-data-only use cases where appropriate.

---

# 7. Autonomous schedules publishing stale information

## Problem

A daily collection failed but a downstream director brief could still publish stale rankings as if fresh.

## Root cause

Scheduling and freshness were coupled poorly; downstream publication did not prove upstream success/freshness.

## Proven fix

Disable autonomous schedules until orchestration/freshness ownership is explicit.

## Reusable lesson

**A schedule is not proof that fresh data exists.**

Future Agent-000 should own:
- scheduling;
- run status;
- freshness checks;
- downstream release.

---

# 8. Cross-topic corpus contamination and duplicate analysis

## Problem

Agent-002 could build synthesis over mixed/duplicate corpus rows.

## Root cause

Insufficient filtering by topic/prompt version and library reads occurring multiple times through loops.

## Proven fix

- normalise one `search_term` source;
- filter by exact topic and prompt version;
- dedupe by video ID, latest row wins;
- use `executeOnce` for the corpus read;
- fail/exit cleanly on no corpus.

## Reusable lesson

Every research pipeline needs explicit **scope identity** and **dedupe identity** before synthesis.

This is directly reusable for anime clip-farming research: franchise/topic contamination will otherwise destroy ranking intelligence.

---

# 9. No-input / zero-corpus path accidentally invokes paid models

## Problem

A pipeline with no valid corpus could still continue toward a paid synthesis/model step.

## Proven fix

Introduce an explicit corpus-ready gate and a deterministic `NO_CORPUS` result.

## Reusable lesson

Every paid path should have a cheap deterministic eligibility gate before the provider call.

---

# 10. Model output should not own deterministic bookkeeping

## Problem

Agent-005's single paid run generated all 29 shots correctly in prose/creative content, but S022's structured `visible_at_start` copied the prior shot's start rather than the prior shot's end.

## Root cause

A language model was asked to populate a value that is actually deterministic system state.

## Proven fix

System-owned continuity chaining:

`visible_at_start(N) = validated visible_at_end(N-1)`

The system may normalise that bookkeeping field and log the change, while creative prose/visual instructions remain model-owned and are validated for contradiction.

## Reusable lesson

**If a value can be derived deterministically, do not ask a model to be authoritative for it.**

Use the model for interpretation/creative choices; use code for state transitions, counters, IDs, timing arithmetic, sequence chaining and permissions.

---

# 11. Fail closed even when the model output “looks good”

## Problem

All 29 Agent-005 model calls completed and the plan was semantically good, but one structured continuity defect remained.

## Proven fix

The sequence validator refused to create a production manifest.

## Reusable lesson

A good-looking output is not enough. **Downstream artifacts should only exist if validators pass.**

This is why the failure was a system success rather than wasted work.

---

# 12. Avoid paying twice: recover already-paid outputs with provenance

## Problem

After the 29-call paid run failed only on one deterministic continuity field, rerunning the whole model would have paid for essentially the same creative work again.

## Proven fix

Build a single-use recovery replay:
- preserve original failed run unchanged;
- load exact stored model outputs;
- new unique recovery run ID;
- deterministic normalization;
- full validators rerun;
- explicit recovery provenance;
- create a REVIEW manifest only if all checks pass;
- zero new model calls.

## Reusable lesson

**Do not regenerate expensive outputs when the creative payload is valid and the defect is deterministic. Replay and revalidate instead.**

This pattern is highly reusable for video, transcription, image, speech and LLM pipelines.

---

# 13. Historical evidence must remain immutable

## Problem

The easiest “fix” for the failed run would have been to correct S022 in place and attach a manifest.

## Why rejected

That would erase evidence that the original run failed closed.

## Proven pattern

- original run stays untouched;
- corrected/recovered output gets a new run ID;
- provenance points to the original;
- historical evidence is never rewritten just to make state look clean.

## Reusable lesson

Auditability is more valuable than cosmetic neatness.

---

# 14. Cost optimisation should be separate from creative generation

## Problem

A technically clean plan asked for 20 video generations against a 15-shot baseline.

## Proven fix

Perform a **read-only cost review** after creative validation. Classify shots as:
- VIDEO_ESSENTIAL;
- VIDEO_PREFERRED;
- STATIC_OR_COMPOSITE_SAFE.

Then create a deterministic, human-authorised optimisation run that changed only five allowed animation fields.

Result: 20 → 15 video shots with no story/fidelity changes.

## Reusable lesson

Do not ask the model to optimise cost and creative quality in one opaque decision. Separate:
1. creative correctness;
2. deterministic cost review;
3. explicit human production decision.

---

# 15. Exact-diff auditing for deterministic transforms

## Problem

When recovering or optimising model output, it is easy to accidentally change unrelated fields.

## Proven fix

Recursive source-vs-result diff with an explicit allow-list of permitted fields.

Any unexpected field difference fails the stage.

## Reusable lesson

Use exact-diff allow-lists for:
- migrations;
- recoveries;
- cost optimisations;
- formatting transforms;
- metadata repairs.

This is stronger than “looks equivalent.”

---

# 16. Registry query semantics: APPROVED OR LOCKED must be explicit

## Problem

Asset-reuse logic relied on ambiguous filter semantics.

## Proven fix

Use explicit `status in (APPROVED, LOCKED)` semantics and re-filter defensively in code.

Exclude:
- REVIEW;
- mock;
- test;
- development rows.

## Reusable lesson

Security/governance filters should not depend on UI-default AND/OR behaviour.

---

# 17. Generic placeholder labels can create false exact matches

## Problem

Agent-004 inventory labels such as “Agent-004 approved new asset” were placeholders, not identities. If treated as exact labels, unrelated assets could match the same generic name.

## Proven fix

Ignore generic placeholder labels in canonical matching; use actual IDs, meaningful labels and aliases.

## Reusable lesson

**A label is not an identity merely because it is non-empty.**

Watch for AI-generated placeholder names in every new project.

---

# 18. Preserve visual and audio TBD dependencies separately

## Problem

Audio TBD dependencies could collapse into generic UNKNOWN records, losing category and shot coverage.

## Proven fix

Preserve:
- dependency class;
- audio category;
- affected shots;
- source phrases;
- unresolved status;
- no invented canonical ID.

Merge duplicate keys by unioning shots/labels rather than silently dropping them.

## Reusable lesson

When normalising requirements, preserve the dimensions needed later for production decisions. Do not over-normalise into “unknown asset.”

---

# 19. Exact UUID gate before any production write

## Problem

Historical workflows could discover/accept records by loose labels or status alone.

## Proven fix

Agent-006 now requires:
- valid UUID;
- exact row ID match;
- exact persisted APPROVED status;
- malformed/missing/nonexistent IDs fail before writes.

## Reusable lesson

Every production workflow should receive an exact upstream artifact ID and verify it before side effects.

---

# 20. Unpublished n8n drafts can still be executable as sub-workflows

## Problem

The team previously treated unpublished as equivalent to non-executable.

## Discovery

A single-use caller proved that on this n8n instance, Execute Workflow can execute the current unpublished sub-workflow draft.

## Reusable lesson

**Publication state is not a universal execution-security boundary.**

Therefore use:
- disconnected triggers;
- caller policies;
- deterministic gates;
- explicit IDs;
- side-effect checks;
not merely “unpublished.”

This is a high-value lesson for every future n8n system.

---

# 21. Storage metadata can be wrong even when the asset is approved

## Problem

Three approved SFX registry `storage_path` values did not point to the files that actually existed. The objects had doubled/mixed extensions.

## Risk

Downstream retrieval by canonical `storage_path` would fail despite the asset being APPROVED.

## Proven fix

- independently verify exact storage object;
- update only `storage_path`;
- checksum before/after;
- prove all other fields unchanged.

## Reusable lesson

Canon approval and physical retrievability are separate checks.

A canonical-asset health check should eventually verify:
- registry path exists;
- MIME/type expected;
- checksum/etag valid;
- file decodes;
- no duplicate/overwritten object anomaly.

---

# 22. Upstream inventory can omit usage even when downstream plan knows it

## Problem

Agent-005 asset inventory had empty `used_in_shots` for the three reused SFX, even though shot plans explicitly placed them at S004/S007/S027.

## Proven fix

Agent-006 S5.2 derives reused-audio shot coverage from the production plan if inventory is empty, and fails closed if non-empty inventory contradicts the plan.

## Reusable lesson

Use the most authoritative source for each field. If redundant sources exist:
- empty + authoritative populated → derive;
- both populated and agree → validate;
- disagree → fail closed.

---

# 23. Hard-coded production IDs are dangerous

## Problem

Agent-007 node 00 hard-coded an old smoke-test readiness manifest.

## Risk

Manual execution could target the wrong lineage regardless of caller intent.

## Proven fix in S6 draft

- caller supplies exact readiness-manifest UUID;
- UUID validated;
- exact row read from Supabase;
- ID equality rechecked;
- no production manifest is hard-coded.

## Reusable lesson

Hard-coded fixture IDs must never survive in production entry paths.

---

# 24. Caller-supplied approval fields are not trustworthy

## Problem

Agent-007 had a mock/caller path that could supply approval-like fields.

## Risk

A caller could claim `APPROVED + NEEDS_ASSET_CREATION` without persisted state.

## Proven fix

S6 ignores caller-supplied:
- status;
- readiness state;
- manifest JSON;
- paid-authorisation flags.

Authorisation comes only from persisted Supabase rows.

## Reusable lesson

Never treat upstream payload claims as authority for spend, approval or canon.

---

# 25. Paid gate must be before reservation/claim, not at the provider node

## Problem

Disabling the provider-submit node was not enough. Earlier logic could reserve/claim a paid attempt first and then stop, permanently blocking later work.

## Proven fix

S6 introduces a deterministic paid-dispatch gate **before**:
- reservation;
- dispatch claim;
- provider submission.

If no persisted paid authorisation exists, stop with zero reservation/claim writes.

## Reusable lesson

Put permission gates before the first irreversible/consuming side effect, not before the final API call.

---

# 26. Retry configuration must match real enforcement

## Problem

Configuration implied up to three attempts, but other guards effectively allowed only attempt one.

## Proven decision

Conservative rule:
- one new paid attempt per requirement;
- no automatic paid retry;
- a second paid attempt requires a separate future human authorisation;
- recovery of an existing provider task is different from a new attempt.

## Reusable lesson

Retry policy is financial policy. It must be explicit and consistent across configuration, DB constraints and workflow code.

---

# 27. Recovery/polling is not the same as new paid generation

## Problem

Should an already-paid provider task be allowed to resume without opening the new-paid gate?

## Current decision

Yes, only while the recovery path:
- requires an exact persisted existing job;
- already has `provider_job_id`;
- only polls/downloads/stores;
- cannot submit a second generation.

## Reusable lesson

Separate lifecycle operations:
- **new paid dispatch**;
- **resume/poll existing paid task**.

They have different risk profiles and should have different gates.

---

# 28. Candidate registration can accidentally downgrade canon — PENDING FIX

## Problem

Agent-007 node 10 uses merge-upsert on `asset_id` and writes status REVIEW. Re-registering an asset that a human has since APPROVED/LOCKED could downgrade it.

## Current intended fix (S6.1 pending)

Make candidate registration insert-only / ignore duplicates:
- absent asset ID → insert REVIEW;
- existing row → preserve exactly, no update.

## Reusable lesson

A lower-authority producer must never overwrite higher-authority human state.

This is pending until Claude returns S6.1 evidence.

---

# 29. Append-only human decisions need concurrency control — DESIGN PENDING v0.2

## Problem

An append-only decision table can still create two simultaneous “current” decisions if concurrent inserts race.

## Intended fix

Acquire a transaction-scoped advisory lock on exact:

`production_manifest_id + requirement_key`

before checking/superseding current state.

## Reusable lesson

Append-only is not automatically race-safe. Immutable history and concurrency safety are separate concerns.

---

# 30. Paid authorisation should be an immutable event stream — DESIGN PENDING v0.2

## Problem

The initial uniqueness proposal allowed only one grant/revoke pattern and did not naturally support repeated cycles.

## Intended redesign

Immutable events:
- GRANT;
- REVOKE.

A current view derives active grants that are unrevoked/unexpired and exact-scope matched.

## Reusable lesson

Permissions with lifecycle history are often better represented as events than mutable booleans.

---

# 31. Visual technical validity does not equal creative canon

## Problem

Generated berry/cloth/mirror assets technically passed storage/QC checks, but visual inspection found style/canon concerns.

Examples:
- berry smudges: transparent but too realistic/painterly and not clearly separable into controlled per-location states;
- cloth: technically valid but too photoreal/commercial compared with likely stylised art direction;
- mirror A02: promising, but opaque painted glass and visual style should be judged only after characters/world are locked.

## Reusable lesson

There are at least three independent QA layers:
1. file/technical validity;
2. production usability;
3. creative/canon approval.

Do not collapse them into one “QC PASS.”

---

# 32. Build channel-level canon before generating episode-specific assets

## Problem

EP005 needs Mikko, Lumi and a world, but only behavioural canon exists.

## Risk

Generating props first allows random generated props to accidentally define the channel's art direction.

## Current decision

After S6.1, pause infrastructure and build:
- Mikko visual identity;
- Lumi visual identity;
- duo visual system;
- world/environment;
- channel style bible;
then revisit props.

## Reusable lesson

**Brand/character/world canon should define episode assets, not the reverse.**

This is especially important for Viva's anime/clip-farming channel: lock branding, typography, captions, transitions and edit grammar before scaling automated output.

---

# 33. High-value reusable engineering patterns now in V&A's skill list

V&A should consider these established internal capabilities:

- live/draft/published workflow drift inspection;
- bounded cross-AI engineering handoffs;
- exact UUID identity migration;
- fail-closed approval gates;
- no-corpus / no-input safe exits;
- source-fidelity validators;
- deterministic state chaining;
- structured model-output validation;
- exact-diff allow-list auditing;
- zero-paid replay of already-paid outputs;
- provenance-safe recovery runs;
- deterministic cost optimisation;
- canonical registry governance;
- mock/test/development exclusion;
- requirement normalisation without information loss;
- production-manifest readiness modelling;
- append-only changelog/evidence;
- safe single-use caller workflows;
- proof that unpublished sub-workflows may still execute;
- pre-reservation paid-dispatch gates;
- strict paid-attempt caps;
- separation of new dispatch from resume/recovery;
- storage-path integrity repair;
- technical-vs-creative QC separation;
- human-decision and paid-permission event-model design.

These are reusable assets of the company even when the content niche changes.

---

# 34. Standard troubleshooting checklist for future projects

Before debugging any V&A agent:

1. What exact workflow ID/version is live?
2. Is published equal to draft?
3. What exact input ID is authoritative?
4. Does the gate read persisted state or trust caller data?
5. What is the first side effect?
6. Is permission checked before that side effect?
7. Can the test run be performed in a no-write/no-provider harness?
8. What tables/rows/checksums should remain unchanged?
9. Is any data duplicated in two sources that can conflict?
10. Which field should be deterministic rather than model-owned?
11. Does a REVIEW/test/mock row have any route to production?
12. Does a retry imply additional spend?
13. Can already-paid output be replayed instead of regenerated?
14. Can a lower-authority workflow overwrite a higher-authority human decision?
15. Is “technically valid” being mistaken for “canonically approved”?
16. Is a stable ID being replaced by a human-readable label?
17. Is a hidden hard-coded test value still present?
18. What exact rollback exists?
19. What did we learn that belongs back in this playbook?

---

# 35. Evidence basis

This playbook consolidates proven lessons from:
- engineering changelog through ENG-20260928-020;
- Agent-001 through Agent-007 stabilization work;
- Agent-005 paid fail-closed run and recovery;
- Agent-006 live run and S5.2 corrections;
- Agent-007 S6 safety report;
- current human-resolution and asset-governance designs;
- Company Brain reconciliation decisions made in this chat.

**ENG-20260929-021 / S6.1 is now proven at the free-validation/design level. The v0.2 human-resolution and paid-authorisation mechanisms remain proposals only; no migration or production wiring has occurred.**


---

# 36. Protect canon with insert-only registration, not merge-upsert

A lower-authority candidate producer must never merge-update a human-approved canonical row. Agent-007 S6.1 proved the safe pattern:

```text
pre-read exact asset_id
  ↓
existing → preserve/no-op
absent   → INSERT REVIEW with ON CONFLICT DO NOTHING
```

The database conflict policy remains necessary after the pre-read because another writer can insert during the race window. Free tests proved existing REVIEW/APPROVED/LOCKED rows are preserved and new candidates still register REVIEW.

**Reusable lesson:** lower-authority workflows may append candidates, but they must not overwrite higher-authority canon.

---

# 37. Pre-read checks are not enough; make the database conflict policy safe too

Use defence in depth: exact pre-read → deterministic branch → insert-only database command → `ON CONFLICT DO NOTHING` (or safe uniqueness failure) → deterministic confirmation. This pattern applies to clip registries, source registries, publish queues and deduplication tables.

---

# 38. Append-only human decisions need concurrency control and structural backstops

The v0.2 decision design combines a transaction-scoped advisory lock on the exact business key, READ COMMITTED writers, immutable rows, one root per scope, unique supersession and a derived-current view.

**Reusable lesson:** serialize on the business key, keep approval history immutable, and add database constraints that remain safe even if application logic fails.

---

# 39. Paid permission should be an event and a consumable capability

The v0.2 paid-authorisation design uses append-only GRANT/REVOKE events, exact scope, expiry, revocation, a derived current-grant view, advisory locking and atomic consumption at reservation.

**Reusable lesson:** permission to spend should be persisted, exact-scoped, expiring, revocable, auditable and consumed at the first side effect. Never infer it from chat text or caller JSON.

---

# 40. Separate new paid dispatch from recovery of already-paid work

A persisted provider task may be polled/downloaded without a second submission. A job with no provider task is new spend and must cross the paid gate before reservation. If a supposed resume path can submit a fresh provider request, it is not a resume path.

---

# 41. Reporting truth can drift even when canon is safe

S6.1 found two non-blocking issues: node 13 can label a preserved canonical row as REVIEW in the batch summary, and nodes 09/14 can merge-overwrite job/batch history on replay. Neither mutates canon today, but both matter before publication.

**Reusable lesson:** protect state and make summaries/audit history accurately describe what happened.

---

# 42. SECURITY DEFINER provenance needs an explicit identity check before migration

Company Brain review note: the proposed v0.2 PostgreSQL triggers are `SECURITY DEFINER` and set server-side provenance. Before migration, verify which identity function represents the intended caller under the actual Supabase/PostgREST execution path. `current_user` inside a security-definer function may represent the function owner rather than the originating caller.

This is not an applied defect; no migration has occurred. It is a migration-review checklist item.

---

# 43. S6.1 closure / skill-library update

ENG-20260929-021 adds these proven capabilities to the V&A skill library: canon-safe insert-only registration, race-safe duplicate handling, free canonical-preservation harnesses, concurrency-safe append-only decision design, repeatable grant/revoke paid-authorisation design, and separation of canon risk from reporting/history risk.

The current bottleneck is now visual canon, not workflow safety.


---

# 44. Use visual attention hierarchy: characters carry colour, environments stay quieter

## Problem

The first EP005 bathroom master was attractive but used too many competing colours and decorative details. Because Mikko and Lumi already carry strong teal, yellow, brown and glow accents, the environment competed with the story focus.

## Proven creative fix

The bathroom was simplified toward a real-world child-friendly room:
- warm whites, cream, beige and light wood dominate;
- only restrained pale blue/yellow accents remain;
- towels and bath mat are plain rather than patterned;
- decorative props are minimal;
- stronger colour is reserved for Mikko, Lumi and key action objects such as the hand mirror and cloth.

## Reusable lesson

**In children’s visual production, use colour as an attention-control system, not as decoration everywhere.** When characters are already visually rich, keep the environment comparatively quiet so the child’s eye naturally follows the character, clue and action.

This principle should transfer to thumbnails, sets, props, overlays and future V&A channels: define a focal-colour budget and keep nonessential background elements below it.
