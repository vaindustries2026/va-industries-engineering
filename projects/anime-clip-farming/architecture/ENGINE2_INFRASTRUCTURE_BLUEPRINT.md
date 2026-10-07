# V&A Industries — Anime Clip Farming / Engine 2
## Infrastructure Blueprint, Agent Build Sprints & Claude Engineering Boundaries v1.0

**Project:** V&A Industries / Anime Shorts Lab / Clip Farming  
**Engine:** Engine 2 — Claude Engineering Stream  
**Version:** v1.0  
**Date:** 5 October 2026  
**Status:** PROPOSED BUILD BLUEPRINT — HUMAN APPROVAL REQUIRED BEFORE IMPLEMENTATION  
**Primary implementation platform:** n8n  
**Operational data layer:** Supabase  
**Engineering record / version control:** GitHub  
**Primary human governance:** Gilang / Viva / V&A Company Brain  

---

# 0. READ THIS FIRST — HARD PROJECT BOUNDARY

This document applies **ONLY** to the V&A Anime Clip Farming / Anime Shorts Lab / Engine 2 project.

## Absolute exclusion rule

Claude must **NOT** modify, migrate, publish, rename, connect, refactor, test against, or otherwise interfere with any workflow, database object, project file, automation, credential, agent, asset registry, production manifest, or GitHub path belonging to the separate **Mikko & Lumi / YouTube Kids** project.

This prohibition includes, but is not limited to:

- Mikko & Lumi project workflows;
- the existing YouTube Kids Agent-001 through Agent-007 workflows;
- any future YouTube Kids Agent-000;
- Mikko & Lumi Supabase tables;
- Mikko & Lumi asset registries;
- Mikko & Lumi production manifests;
- Mikko & Lumi readiness manifests;
- Mikko & Lumi paid-authorisation designs;
- Mikko & Lumi visual canon;
- Mikko & Lumi character assets;
- Mikko & Lumi Slack routing;
- Mikko & Lumi production credentials;
- Mikko & Lumi GitHub folders or branches.

Claude may reuse **general engineering lessons and architecture patterns** already learned by V&A, such as:

- stable UUID identity;
- fail-closed gates;
- immutable history;
- approval-state separation;
- exact-diff auditing;
- deterministic bookkeeping;
- replay-safe design;
- provenance preservation;
- separating creative decisions from permissions;
- separating research access from publication rights.

However, those patterns must be implemented as **new Clip Farming-specific objects**, not by altering the existing Mikko & Lumi implementation.

> **Reuse the engineering pattern, not the production system.**

If any task would require modifying a Mikko & Lumi object, Claude must **STOP** and return the dependency/blocker to the human team.

---

# 1. PURPOSE

The purpose of this blueprint is to define the order in which the Anime Clip Farming / Engine 2 system should be built.

The system should not be built as one giant autonomous workflow.

It should be built as a sequence of narrow, specialist agents with explicit contracts, persisted IDs, approval gates, and evidence between stages.

The intended end-state is:

```text
Market / Trend Intelligence
        ↓
Scene Intelligence
        ↓
Editorial Opportunity
        ↓
Human Content Approval
        ↓
Script / Commentary
        ↓
Human Script Approval
        ↓
Publication-Source Resolution
        ↓
Human Source / Rights Approval
        ↓
Edit / Production Planning
        ↓
Production Assembly
        ↓
Human Final QC
        ↓
Publishing / Distribution
        ↓
Analytics / Learning
        ↓
Feedback into future planning

LATER:
Deterministic CF-000 Orchestrator
```

The first commercial objective is **not maximum automation**.

The first commercial objective is to validate a repeatable anime commentary format through a **30-video validation batch**.

---

# 2. CORE OPERATING PRINCIPLES

## 2.1 Editorial idea first

The system must not begin with:

> “Find a cool anime clip and repost it.”

It should begin with:

> “What original idea, explanation, interpretation, observation, comparison, memory, or argument are we making?”

The anime scene is supporting evidence.

The editorial layer is the product.

---

## 2.2 Research source is not publication permission

Crunchyroll or another legal viewing platform may be used as a **research/reference source** for identifying:

- titles;
- episodes;
- scenes;
- timestamps;
- characters;
- moments;
- narrative context;
- editorial opportunities.

Research access must never automatically become publication approval.

The system must preserve separate concepts for:

```text
RESEARCH_SOURCE
PUBLICATION_SOURCE
PUBLICATION_APPROVAL
```

No agent may autonomously declare copyrighted material legally safe to publish.

---

## 2.3 Human-governed publication

The following decisions remain human-governed:

- whether an editorial idea should be made;
- whether a script is worth publishing;
- whether a publication-source package is acceptable;
- whether the final rendered video is approved;
- whether a paid provider call is authorised where relevant;
- whether an external platform upload is allowed.

---

## 2.4 Stable IDs

Every operational object must have a stable UUID or equivalent immutable primary identifier.

Use:

```text
scene_id
content_candidate_id
script_id
source_package_id
production_manifest_id
render_id
published_content_id
```

Do not use anime titles, episode labels, filenames, or human-readable content titles as operational identity.

> Persist IDs. Display labels.

---

## 2.5 Deterministic state control

LLMs may assist with:

- interpretation;
- research synthesis;
- ranking;
- idea generation;
- script generation;
- editorial reasoning.

LLMs must not be authoritative for deterministic functions such as:

- approval state;
- IDs;
- retry count;
- publication permission;
- run state;
- dedupe logic;
- timestamps;
- budget permission;
- rights approval;
- exact workflow sequencing.

---

# 3. TARGET AGENT ARCHITECTURE

The full target system contains **nine operational agents** and **one later orchestrator**.

| ID | Agent | Core Question |
|---|---|---|
| CF-001 | Market & Trend Radar | What anime, franchises, topics or moments are worth investigating? |
| CF-002 | Scene Intelligence & Provenance | Which exact scenes are useful, where are they, and why do they matter? |
| CF-003 | Editorial Opportunity Planner | What original V&A content should we make from the intelligence? |
| CF-004 | Script & Commentary Architect | What exactly are we saying, and in what format? |
| CF-005 | Publication Source & Rights Resolver | What approved visual/audio material may support the editorial idea? |
| CF-006 | Edit & Production Planner | How should the approved idea become a finished short-form video? |
| CF-007 | Production Assembly | Build the clean master video candidate. |
| CF-008 | Publisher & Distribution | Publish approved masters to approved platforms with tracked IDs. |
| CF-009 | Analytics & Learning Engine | What worked, what failed, and what should change next? |
| CF-000 | Deterministic Orchestrator — LATER | Which exact state transition is authorised next? |

CF-000 must **not** be built first.

---

# 4. HUMAN GOVERNANCE GATES

The proposed minimum human gates are:

```text
G1 — CONTENT IDEA APPROVAL
CF-003 IDEA → APPROVED

G2 — SCRIPT APPROVAL
CF-004 DRAFT → APPROVED

G3 — PUBLICATION SOURCE / RIGHTS APPROVAL
CF-005 REVIEW → APPROVED

G4 — FINAL VIDEO QC / PUBLISH APPROVAL
CF-007 REVIEW → APPROVED_FOR_PUBLISH
```

No downstream workflow may infer approval from an upstream recommendation.

Approval must be persisted explicitly.

---

# 5. SPRINT BATCH OVERVIEW

The build is divided into **eight batches**.

```text
BATCH A — FOUNDATION
    Sprint 0

BATCH B — INTELLIGENCE
    Sprint 1 — CF-001
    Sprint 2 — CF-002

BATCH C — EDITORIAL
    Sprint 3 — CF-003 + G1
    Sprint 4 — CF-004 + G2

BATCH D — SOURCE GOVERNANCE
    Sprint 5 — CF-005 + G3

BATCH E — PRODUCTION
    Sprint 6 — CF-006
    Sprint 7 — CF-007 + G4

BATCH F — DISTRIBUTION
    Sprint 8 — CF-008

BATCH G — LEARNING & VALIDATION
    Sprint 9 — CF-009
    Sprint 10 — 30-video validation + system hardening

BATCH H — ORCHESTRATION
    Sprint 11 — CF-000, only after explicit human go-ahead
```

---

# 6. BATCH A — FOUNDATION

# Sprint 0 — Engine 2 Architecture & Data Contracts

## Objective

Create the Clip Farming technical foundation before building production agents.

## No production agent is considered complete in this sprint.

## Claude tasks

1. Inspect current Engine 2 / Clip Farming work only.
2. Identify any existing Clip Farming-specific workflows or tables.
3. Record exact workflow IDs and states.
4. Define naming conventions.
5. Define UUID identity contracts.
6. Define statuses.
7. Define agent input/output contracts.
8. Define proposed Supabase schema.
9. Define GitHub folder structure.
10. Define approval-gate contracts.
11. Define free-test strategy.
12. Define paid-call and publishing stop rules.
13. Produce a dependency map for CF-001 through CF-009.
14. Identify anything already built that can safely be reused **inside Engine 2 only**.

## Proposed state vocabulary

Use the smallest sensible set, for example:

```text
IDEA
DRAFT
REVIEW
APPROVED
REJECTED
BLOCKED
READY
PUBLISHED
RETIRED
```

Do not add statuses casually.

## Proposed database backbone

Design only unless the sprint instruction separately authorises migrations.

Candidate objects:

```text
anime_titles
anime_source_episodes
anime_scene_intelligence
editorial_opportunities
content_scripts
publication_source_packages
publication_source_decisions
production_manifests
production_jobs
content_assets
published_content
performance_snapshots
content_learning_log
```

## Exit criteria

Sprint 0 passes only when:

- every object has an authoritative identity;
- every agent has defined inputs and outputs;
- approval gates are explicit;
- research source and publication source are separate;
- no Mikko & Lumi object is touched;
- no paid provider calls occur;
- no social publication occurs;
- proposed migrations are reviewed before being applied;
- GitHub structure is documented;
- human team receives a clear architecture report.

## Sprint 0 stop point

STOP after design/reconciliation.

Do not proceed automatically to CF-001.

---

# 7. BATCH B — INTELLIGENCE

# Sprint 1 — CF-001 Market & Trend Radar

## Objective

Build the first Clip Farming intelligence agent.

## Core question

> What anime, franchises, topics, eras, trends or fandom opportunities are worth investigating?

## Responsibilities

CF-001 may collect and rank:

- anchor / evergreen franchises;
- current and seasonal anime;
- breakout anime;
- nostalgia opportunities;
- 2000s opportunities;
- cult / prestige opportunities;
- obscure experiments;
- rising characters;
- notable episodes;
- current fandom conversation;
- prior V&A performance once available.

## Output

A structured research-candidate record with a stable ID.

Possible fields:

```text
research_candidate_id
anime_title_id
topic
content_lane
trend_state
demand_signal
nostalgia_signal
editorial_potential
timeliness
source_references
created_at
agent_version
prompt_version
status
```

## Must not do

CF-001 must not:

- create final scripts;
- choose publication footage;
- approve ideas;
- upload content;
- modify Mikko & Lumi workflows.

## Validation

Free tests should prove:

- duplicate handling;
- scope isolation;
- correct ID persistence;
- zero-corpus / no-result safe exit;
- no unrelated-topic contamination;
- no paid calls unless explicitly authorised.

## Exit criteria

CF-001 can reliably create useful research candidates without downstream side effects.

---

# Sprint 2 — CF-002 Scene Intelligence & Provenance

## Objective

Create the compounding Anime Scene Intelligence Library.

## Core question

> Which exact scenes or moments are worth discussing, where are they, and why?

## Responsibilities

Record:

```text
scene_id
anime_title_id
season
episode_number
episode_title
scene_start
scene_end
characters_present
scene_summary
scene_function
why_scene_matters
possible_editorial_angles
context_requirement
spoiler_level
visual_strength
nostalgia_signal
source_platform
source_reference
research_access_basis
publication_source_status
rights_notes
created_at
agent_version
prompt_version
status
```

## Hard source rule

CF-002 may identify a scene as:

```text
EDITORIALLY_STRONG
```

while leaving:

```text
publication_source_status = UNKNOWN
```

That is valid and expected.

## Must not do

CF-002 must not infer commercial publication permission merely because a scene was legally viewed through Crunchyroll or another service.

## Validation

Test:

- stable scene identity;
- exact source provenance;
- dedupe of the same scene;
- multiple scenes from one episode;
- scene-level scope;
- safe missing-source path;
- publication status remains separate.

## Exit criteria

The system can search and retrieve scene intelligence without conflating research access and publication approval.

---

# 8. BATCH C — EDITORIAL

# Sprint 3 — CF-003 Editorial Opportunity Planner + G1

## Objective

Turn intelligence into original V&A content ideas.

## Core question

> What should V&A actually say about this?

## Responsibilities

Generate ranked content opportunities using the project strategy:

- meaning;
- nostalgia;
- character insight;
- scene interpretation;
- adaptation analysis;
- storytelling;
- anime history;
- cultural observation;
- comparison;
- debate;
- overlooked detail;
- growing-up reinterpretation.

## Output

```text
content_candidate_id
scene_id
anime_title_id
editorial_angle
working_hook
audience_type
content_lane
format_recommendation
estimated_duration
why_now
why_viewer_cares
hypothesis
primary_metric
production_difficulty
rank
recommend_for_review
status = IDEA
```

## G1 — Human Content Approval

Only persisted:

```text
status = APPROVED
```

may proceed to CF-004.

Recommendations are not approvals.

## Must not do

CF-003 must not:

- approve itself;
- create publication permission;
- publish;
- force every idea into one duration;
- reduce the channel to raw clip reposting.

## Exit criteria

The team can generate a ranked editorial backlog and approve individual ideas by stable ID.

---

# Sprint 4 — CF-004 Script & Commentary Architect + G2

## Objective

Turn one approved editorial opportunity into a strong commentary-first script.

## Core question

> What exactly are we saying?

## Supported format ladder

```text
Discovery Short:      20–40 sec
Core Analysis:        40–75 sec
Mini Analysis/Essay:  75–180 sec
Long-form Expansion:  4–10+ min
```

Initial short-form center of gravity:

```text
approximately 35–60 seconds
```

## Responsibilities

Create:

- hook;
- thesis;
- minimum required context;
- narration;
- evidence points;
- interpretation;
- payoff;
- CTA where appropriate;
- caption plan;
- factual claims to verify;
- spoiler handling;
- proposed visual-evidence requirements.

## Narration Independence Test

A mandatory editorial test:

> If the anime footage were temporarily removed, would the narration still contain an interesting argument, observation, explanation, interpretation, or story?

If no, the script should fail editorial review.

## G2 — Human Script Approval

Only persisted:

```text
status = APPROVED
```

may proceed to CF-005.

## Exit criteria

One approved content idea can deterministically resolve to one approved script with provenance back to its source opportunity.

---

# 9. BATCH D — SOURCE GOVERNANCE

# Sprint 5 — CF-005 Publication Source & Rights Resolver + G3

## Objective

Create a hard boundary between editorial intelligence and publication-source approval.

## Core question

> What visual/audio material may support this approved script?

## Possible source-package categories

Examples:

```text
OFFICIAL_PROMO
OFFICIAL_TRAILER
PLATFORM_PERMITTED_SOURCE
LICENSED_SOURCE
HUMAN_REVIEWED_SOURCE
ORIGINAL_GRAPHICS
ORIGINAL_MOTION_GRAPHICS
ORIGINAL_DIAGRAM
ORIGINAL_STILL
NO_ACCEPTABLE_SOURCE
HUMAN_REVIEW_REQUIRED
```

## Responsibilities

Create a `source_package_id` linked to:

- approved script;
- source provenance;
- candidate publication materials;
- required original assets;
- rights/risk notes;
- human decision.

## Prohibited conclusions

No agent may independently persist:

```text
FAIR_USE_CONFIRMED
LEGAL_SAFE
COPYRIGHT_SAFE
```

unless a separately authorised legal/governance process explicitly defines such semantics.

## G3 — Human Source / Rights Approval

Only a human-approved publication-source package may proceed.

## Exit criteria

A script can be approved while its publication source remains blocked or unresolved without creating a system error.

That separation must be proven.

---

# 10. BATCH E — PRODUCTION

# Sprint 6 — CF-006 Edit & Production Planner

## Objective

Convert the approved script and approved publication-source package into a production manifest.

## Core question

> Exactly how should this video be made?

## Responsibilities

Plan:

- timecode;
- narration;
- source-evidence placement;
- original graphics;
- captions;
- text emphasis;
- crops;
- punch-ins;
- transitions;
- SFX;
- music;
- visual-safe zones;
- platform-safe composition;
- aspect ratio;
- target runtime;
- required generated assets.

## Output

```text
production_manifest_id
script_id
source_package_id
shot_or_segment_plan
audio_plan
caption_plan
asset_requirements
target_runtime
target_aspect_ratio
render_specification
status
```

## Rule

The production manifest is an execution contract, not creative prose.

Deterministic fields should be system-owned.

## Exit criteria

The same approved script/source package produces a stable, reviewable production plan.

---

# Sprint 7 — CF-007 Production Assembly + G4

## Objective

Build the actual clean master video candidate.

## Core question

> Can we execute the approved production manifest faithfully?

## Responsibilities

Depending on approved providers/tools:

- narration generation;
- captions;
- original graphics;
- approved visual evidence;
- transitions;
- motion;
- sound;
- rendering;
- asset registration.

## Preferred master strategy

Create:

```text
MASTER_VERTICAL_9x16
```

as the clean master where feasible.

Do not separately recreate the same editorial video from scratch for every platform.

## Output

```text
render_id
production_manifest_id
master_asset_path
duration
resolution
checksum
provider_provenance
status = REVIEW
```

## G4 — Human Final QC

Human review should check:

- commentary quality;
- factual accuracy;
- source package compliance;
- edit quality;
- caption accuracy;
- visual problems;
- audio problems;
- spoiler handling;
- brand fit;
- whether the content is worth publishing.

Only persisted:

```text
APPROVED_FOR_PUBLISH
```

may proceed to CF-008.

## Initial production validation

Do **not** immediately render 30 videos.

First produce **three smoke-test videos**:

1. one mainstream / evergreen;
2. one nostalgia / cult;
3. one current / trending.

## Exit criteria

All three smoke tests can traverse the full production path with traceable IDs and human approval.

---

# 11. BATCH F — DISTRIBUTION

# Sprint 8 — CF-008 Publisher & Distribution

## Objective

Publish only human-approved masters and preserve the platform identity of every post.

## Primary destination

YouTube.

## Initial distribution surfaces

- YouTube Shorts;
- TikTok;
- Instagram Reels.

## Responsibilities

Manage:

- approved platform selection;
- title;
- description;
- hashtags;
- thumbnail where relevant;
- scheduling;
- upload;
- publish response;
- external platform post IDs;
- publish timestamp;
- failure state;
- retry state.

## Required identity mapping

Example:

```text
published_content_id
render_id
youtube_post_id
tiktok_post_id
instagram_post_id
published_at
status
```

## Rule

Platform posts are distributions of the same underlying V&A content object.

## Must not do

No automatic publishing before explicit human authorisation for the sprint and the specific content item.

## Exit criteria

One approved master can be published to approved destinations while preserving each external platform ID and status.

---

# 12. BATCH G — LEARNING & VALIDATION

# Sprint 9 — CF-009 Analytics & Learning Engine

## Objective

Turn publishing data into structured learning.

## Core question

> Why did one V&A anime video outperform another?

## Candidate metrics

Where available:

- views;
- impressions;
- viewed vs swiped;
- retention;
- average view duration;
- completion;
- replays;
- likes;
- comments;
- shares;
- saves;
- subscriber/follower conversion;
- platform;
- publish time;
- traffic source.

## Required upstream dimensions

Analytics should be joinable to:

- anime;
- franchise;
- anime era;
- scene;
- hook type;
- editorial angle;
- content lane;
- audience type;
- format;
- duration;
- script version;
- production version;
- platform.

## Output

```text
learning_record_id
published_content_id
hypothesis
result
performance_vs_baseline
what_worked
what_failed
confidence
next_test
recommended_backlog_effect
status
```

## Rule

CF-009 may recommend future production.

It must not rewrite history or silently change old records.

## Exit criteria

The team can answer:

> Which combination of franchise + scene + editorial angle + hook + duration + platform is producing the strongest business signal?

---

# Sprint 10 — 30-Video Validation Batch & System Hardening

## Objective

Use the completed system to validate the business before building full orchestration.

## Validation target

Produce and publish up to **30 controlled test videos**, subject to human approval and rights/source governance.

Do not dump all 30 at once.

Recommended staged release:

```text
Tranche 1: 5 videos
Review data

Tranche 2: 5 videos
Review data

Tranche 3: 10 videos
Review data

Tranche 4: up to 10 videos
Complete validation batch
```

The exact tranche size may be adjusted based on evidence.

## Portfolio intent

Maintain deliberate variation across:

- mainstream / proven;
- current / trending;
- 2000s nostalgia;
- cult / prestige;
- niche / obscure wildcard.

## Hardening work

Use real executions to fix:

- idempotency;
- duplicate publication;
- stale state;
- retry behavior;
- failed provider calls;
- source-package mismatches;
- analytics gaps;
- missing provenance;
- state drift;
- cost issues.

## Exit criteria for Batch G

Before CF-000 is authorised, the team should have:

- meaningful completed-video evidence;
- a stable agent contract chain;
- known approval gates;
- known failure paths;
- known provider costs;
- known publishing behavior;
- known analytics joins;
- a preliminary Clip Farming Formula v1.0;
- evidence that continued automation is commercially justified.

---

# 13. BATCH H — ORCHESTRATION

# Sprint 11 — CF-000 Deterministic Orchestrator

## DO NOT BUILD WITHOUT EXPLICIT HUMAN AUTHORISATION

CF-000 exists to orchestrate a proven system.

It is not an LLM creative agent.

## Responsibilities

CF-000 may eventually own:

- exact current stage;
- exact persisted upstream IDs;
- next authorised stage;
- idempotency;
- resume;
- retry eligibility;
- approval waiting states;
- budget guard;
- kill switch;
- run status;
- freshness checks;
- publishing readiness.

## CF-000 must not

- invent editorial angles;
- approve content;
- approve scripts;
- approve rights;
- approve publication;
- bypass humans;
- infer payment permission;
- create legal conclusions;
- make hidden changes to upstream artifacts.

## Exit criteria

Only build CF-000 after the specialist agents and governance model have survived real production.

---

# 14. DEPENDENCY GRAPH

```text
Sprint 0
  ↓
CF-001
  ↓
CF-002
  ↓
CF-003
  ↓ G1
CF-004
  ↓ G2
CF-005
  ↓ G3
CF-006
  ↓
CF-007
  ↓ G4
CF-008
  ↓
CF-009
  ↓
30-video validation / hardening
  ↓
Human go/no-go
  ↓
CF-000
```

No sprint should assume the next sprint is automatically authorised.

---

# 15. CLAUDE EXECUTION PROTOCOL FOR EVERY SPRINT

For every sprint, Claude must work in bounded stages.

## Before changing anything

Return:

1. exact target project;
2. exact workflows in scope;
3. exact workflow IDs;
4. published and draft version IDs where applicable;
5. exact database objects in scope;
6. Git branch;
7. intended changes;
8. tests;
9. forbidden actions;
10. whether any paid/provider call is possible.

If live state differs materially from the expected state:

> STOP and report drift.

Do not silently reconcile.

---

## During the sprint

Claude must:

- change only the authorised Engine 2 objects;
- preserve historical evidence;
- use new IDs for corrected/recovered artifacts where required;
- prefer free/static tests first;
- fail closed on missing approvals;
- keep logs/evidence;
- avoid paid calls unless explicitly authorised;
- avoid external publication unless explicitly authorised.

---

## At sprint completion

Claude must return:

- exact workflow/version IDs;
- Git commit hash;
- exact changed files;
- exact schema changes;
- test list;
- test results;
- execution IDs;
- before/after evidence;
- provider-call count;
- paid-call count;
- publication count;
- known defects;
- rollback procedure;
- next recommended sprint;
- explicit stop confirmation.

Human/Company Brain reconciliation occurs before the next sprint begins.

---

# 16. GITHUB INSTRUCTIONS

Claude should store this blueprint in the Clip Farming / Engine 2 area of the V&A repository.

## Preferred path

If the repository already has a dedicated Anime Clip Farming area, use that existing structure.

Otherwise propose:

```text
/projects/anime-clip-farming/
```

with:

```text
/projects/anime-clip-farming/
    README.md
    architecture/
        ENGINE2_INFRASTRUCTURE_BLUEPRINT_v1.0.md
        data-contracts/
        workflow-contracts/
    sprints/
        SPRINT_00_FOUNDATION/
        SPRINT_01_CF001/
        SPRINT_02_CF002/
        SPRINT_03_CF003/
        SPRINT_04_CF004/
        SPRINT_05_CF005/
        SPRINT_06_CF006/
        SPRINT_07_CF007/
        SPRINT_08_CF008/
        SPRINT_09_CF009/
        SPRINT_10_VALIDATION/
        SPRINT_11_CF000/
    evidence/
    changelog/
```

## Repository boundary

Claude must not move, rename, rewrite, or reorganise existing Mikko & Lumi folders to make the Clip Farming structure cleaner.

Create a separate Clip Farming subtree.

## Suggested branch naming

```text
engine2/clip-farming-sprint-00-foundation
engine2/clip-farming-sprint-01-cf001
engine2/clip-farming-sprint-02-cf002
...
```

Follow the repository's existing branch policy if one already exists.

Do not overwrite an existing branch with unrelated work.

## Commit discipline

Each sprint should have:

- one bounded objective;
- readable commit messages;
- architecture/evidence committed with the implementation;
- no unrelated project files in the diff.

If the sprint diff contains Mikko & Lumi project files unexpectedly:

> STOP. DO NOT COMMIT.

---

# 17. NAMING RULES

To prevent collision with the separate production system:

Use:

```text
CF-000
CF-001
CF-002
...
CF-009
```

Do **not** call these workflows:

```text
AGENT-001
AGENT-002
...
```

because those names already refer to another V&A production system.

Recommended n8n naming:

```text
CF-001 — Market & Trend Radar
CF-002 — Scene Intelligence & Provenance
CF-003 — Editorial Opportunity Planner
CF-004 — Script & Commentary Architect
CF-005 — Publication Source & Rights Resolver
CF-006 — Edit & Production Planner
CF-007 — Production Assembly
CF-008 — Publisher & Distribution
CF-009 — Analytics & Learning Engine
CF-000 — Orchestrator
```

---

# 18. NO-CROSS-PROJECT DATA RULE

Clip Farming should have its own operational tables or clearly namespaced tables.

Do not store anime clip-farming state in Mikko & Lumi tables.

Do not reuse:

- episode backlog rows;
- kids scripts;
- kids production manifests;
- kids readiness manifests;
- kids asset-creation jobs;
- kids asset registry rows.

If a shared generic V&A service is proposed later, that must be a separately reviewed architecture decision.

---

# 19. PAID-CALL RULE

During architecture and early engineering:

> **FREE FIRST.**

For every provider-backed operation:

1. deterministic/static test;
2. mocked test;
3. no-write regression;
4. explicit human approval;
5. smallest possible paid smoke test;
6. inspect evidence;
7. only then scale.

No sprint definition in this document itself authorises spend.

---

# 20. PUBLICATION RULE

Nothing in this blueprint authorises automatic posting.

CF-008 may only publish after:

- upstream IDs are exact;
- source package is approved;
- render is approved;
- human publish approval exists;
- platform credentials are confirmed;
- the specific sprint permits live upload.

---

# 21. RIGHTS / COPYRIGHT GOVERNANCE RULE

The system must preserve this distinction permanently:

```text
Research access
≠
Publication permission
≠
Platform monetisation eligibility
≠
Legal determination
```

No LLM or n8n workflow may collapse those concepts into one Boolean.

---

# 22. WHAT CLAUDE SHOULD DO NEXT

The next Claude assignment after this blueprint is accepted should be:

# `SPRINT 0 — ENGINE 2 FOUNDATION / READ-ONLY DISCOVERY + ARCHITECTURE CONTRACTS`

Claude should:

1. upload/commit this blueprint to the dedicated Clip Farming GitHub path;
2. inspect existing Clip Farming Engine 2 state;
3. identify existing work that maps to this blueprint;
4. identify gaps;
5. propose the exact data contracts and workflow contracts;
6. identify exact objects that would be created in future sprints;
7. return a written Sprint 0 architecture package;
8. STOP.

Claude should **not** immediately build CF-001 through CF-009 in the same assignment.

---

# 23. DEFINITION OF SUCCESS

The Engine 2 build is successful when V&A can trace a finished published video all the way back through:

```text
published_content_id
    ↓
render_id
    ↓
production_manifest_id
    ↓
source_package_id
    ↓
script_id
    ↓
content_candidate_id
    ↓
scene_id
    ↓
anime / episode / research source
```

and trace analytics forward into:

```text
performance_snapshot
    ↓
learning_record
    ↓
next hypothesis
    ↓
future content opportunity
```

without losing:

- provenance;
- rights state;
- human approval;
- version identity;
- publication identity;
- performance history.

---

# 24. FINAL BUILD ORDER

```text
BATCH A
Sprint 0 — Architecture & Data Contracts

BATCH B
Sprint 1 — CF-001 Market & Trend Radar
Sprint 2 — CF-002 Scene Intelligence & Provenance

BATCH C
Sprint 3 — CF-003 Editorial Opportunity Planner + G1
Sprint 4 — CF-004 Script & Commentary Architect + G2

BATCH D
Sprint 5 — CF-005 Publication Source & Rights Resolver + G3

BATCH E
Sprint 6 — CF-006 Edit & Production Planner
Sprint 7 — CF-007 Production Assembly + G4

BATCH F
Sprint 8 — CF-008 Publisher & Distribution

BATCH G
Sprint 9 — CF-009 Analytics & Learning Engine
Sprint 10 — 30-Video Validation + Hardening

BATCH H
Sprint 11 — CF-000 Deterministic Orchestrator
ONLY AFTER EXPLICIT HUMAN GO-AHEAD
```

---

# 25. CLAUDE STOP CONDITION

After completing the exact sprint assigned:

> **STOP. RETURN EVIDENCE. WAIT FOR HUMAN / COMPANY BRAIN RECONCILIATION.**

Do not self-authorise the next sprint.

Do not treat a blueprint as implementation permission.

Do not expand the scope because another improvement appears convenient.

Do not touch the Mikko & Lumi system.

---

**End of document**
