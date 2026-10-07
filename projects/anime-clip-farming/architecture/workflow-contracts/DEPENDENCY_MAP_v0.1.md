# Engine 2 — Dependency Map CF-001 … CF-009 v0.1

**Status:** PROPOSED — DESIGN ONLY.

Legend: `══►` hard dependency (downstream cannot run without it) · `──►` soft dependency (used if present) · `┄┄►` optional enrichment / feedback · `[G#]` human gate · `$` possible paid call · `⚑` first possible external publication.

## 1. Main chain

```text
 INPUT                        PERSISTED OBJECT                 AUTHORITATIVE ID          APPROVAL STATE            NEXT
 ─────                        ────────────────                 ────────────────          ──────────────            ────
 run params, public signals   research_candidates              research_candidate_id     READY (deterministic)     CF-002
   │  CF-001 $(optional LLM)  + anime_titles / franchises      anime_title_id, franchise_id
   ▼
 READY research candidate     anime_source_episodes            source_episode_id         READY                     CF-002
 or human scene intake        anime_scene_intelligence         scene_id                  READY (deterministic)     CF-003
   │  CF-002 $(video model)   (research source only)
   ▼
 READY scenes                 editorial_opportunities          content_candidate_id      IDEA → REVIEW             G1
   │  CF-003 $(LLM)
   ▼
 ┌──────────── [G1] human: content idea approval ────────────┐   gate_decisions(G1)        REVIEW → APPROVED
 └───────────────────────────────────────────────────────────┘
   ▼
 G1-approved opportunity      content_scripts                  script_id                 DRAFT → REVIEW            G2
   │  CF-004 $(LLM)
   ▼
 ┌──────────── [G2] human: script approval ──────────────────┐   gate_decisions(G2)        REVIEW → APPROVED
 └───────────────────────────────────────────────────────────┘
   ▼
 G2-approved script           publication_source_packages      source_package_id         DRAFT → REVIEW | BLOCKED  G3
   │  CF-005 $(optional LLM)  + publication_source_items       source_item_id
   ▼                          ◄── RIGHTS / SOURCE GOVERNANCE ENTERS HERE
 ┌──────────── [G3] human: publication source approval ──────┐   gate_decisions(G3)        REVIEW → APPROVED
 └───────────────────────────────────────────────────────────┘
   ▼
 G2 script + G3 package       production_manifests             production_manifest_id    DRAFT → READY             CF-007
   │  CF-006 $(optional LLM)
   ▼
 READY manifest               production_jobs, content_assets, production_job_id,        render DRAFT → REVIEW     G4
   │  CF-007 $$ (TTS, gen,    renders                          asset_id, render_id
   │          render, store)
   ▼
 ┌──────────── [G4] human: final QC / publish approval ──────┐   gate_decisions(G4)        REVIEW → APPROVED
 └───────────────────────────────────────────────────────────┘   + approved_platforms
   ▼
 v_publish_eligibility        published_content, platform_posts published_content_id,     READY → PUBLISHED  ⚑      CF-009
 + PUBLISH_ENABLED            (external platform IDs)          platform_post_id
   │  CF-008 ⚑ (irreversible)
   ▼
 PUBLISHED posts              performance_snapshots,           performance_snapshot_id,  append-only               (feedback)
   │  CF-009 (free reads,     content_learning_log             learning_log_id
   │          $ optional LLM)
   ┄┄► soft feedback into CF-001 (what to research) and CF-003 (what to propose) — always re-enters through G1
```

## 2. Dependency table

| Consumer | Hard dependencies | Soft dependencies | Optional enrichment |
|---|---|---|---|
| CF-001 | none (run params) | prior research_candidates (dedupe) | content_learning_log; public trend sources |
| CF-002 | READY research_candidate **or** human intake; READY anime_title | — | public official video for model-assisted analysis ($) |
| CF-003 | READY scene(s) or READY research candidate; READY anime_title | live opportunities (dedupe) | learning log; lane mix targets |
| CF-004 | **G1** APPROVED opportunity (hash-bound) | linked READY scenes | — |
| CF-005 | **G2** APPROVED script (hash-bound) | scene research provenance | official-channel metadata |
| CF-006 | **G2** script + **G3** package for the same script | — | brand/edit grammar config (future) |
| CF-007 | READY manifest with effective G2 + G3 upstream; `PAID_CALLS_ENABLED` + per-job authorisation for any paid job | — | — |
| CF-008 | **G4** APPROVED render (hash-bound) in `v_publish_eligibility`; platform in `approved_platforms`; `PUBLISH_ENABLED`; item authorisation | — | packaging drafts |
| CF-009 | PUBLISHED platform_posts | prior snapshots | baseline config |

## 3. Circular-dependency check

- The only loop is **CF-009 ┄┄► CF-001 / CF-003**. It is a soft, read-only feedback edge: CF-009 writes append-only learnings; CF-001/CF-003 may read them. CF-009 never calls, triggers, or changes status in an upstream agent. Any learning that changes the backlog still produces new IDEA rows that must pass G1. **No hard cycle exists.**
- Revision loops (G2 REJECT → new script revision) create **new IDs**, so the graph of IDs stays acyclic.
- `v_scene_publication_status` reads packages (downstream) to describe scenes (upstream); it is a read-only view, not a dependency of CF-002 or CF-003.

## 4. Where things enter

| Concern | Entry point |
|---|---|
| Human decisions | G1 (after CF-003), G2 (after CF-004), G3 (after CF-005), G4 (after CF-007); plus HUMAN_ADMIN unblocking of identities/scenes and kill-switch changes |
| Rights / source governance | CF-005 + G3 only. Upstream objects carry research provenance only |
| Paid services (eventually) | CF-001 (optional LLM), CF-002 (video understanding), CF-003, CF-004 (LLM), CF-005, CF-006 (optional LLM), **CF-007 (TTS, generation, rendering, storage — highest)**, CF-009 (optional LLM). Every one gated by `PAID_CALLS_ENABLED` + per-run authorisation |
| External publication | **CF-008 only**, after G4 and the publish flag. Nothing before CF-008 can publish |

## 5. CF-000

```text
 CF-000 (LATER, Sprint 11, explicit human go-ahead only)
   reads: agent_runs, all lifecycle tables, gate_decisions, system_flags
   may own: sequencing, wait-for-gate, retry eligibility, budget guard, schedules
   is NOT upstream of any CF-001..CF-009 — every agent runs alone by manual trigger
```
