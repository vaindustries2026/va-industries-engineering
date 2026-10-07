# Sprint 0 — Final Architecture Report

**Batch A / Sprint 0 — Engine 2 Foundation.** Operator: Claude Engineer-2 (owner Viva). Date: 2026-10-07.
**Everything in this report is PROPOSED unless it says IMPLEMENTED.** The only IMPLEMENTED items are documentation files on the Sprint 0 Git branch.

| | PROPOSED | IMPLEMENTED |
|---|---|---|
| GitHub `projects/anime-clip-farming/` docs | — | ✅ on branch `engine2/clip-farming-sprint-00-foundation` (not merged) |
| Supabase `cf` schema, 23 tables, functions, roles | ✅ draft SQL marked DESIGN ONLY | ❌ not applied anywhere except a throwaway local test DB that was deleted |
| CF-001 … CF-009, CF-000 workflows | ✅ contracts | ❌ none built |
| Gates G1–G4, reviewers, surfaces | ✅ contracts | ❌ none exist |
| Credentials, buckets, Slack channels | ✅ named as future needs | ❌ none created |

---

## 1. What currently exists?
One unpublished, never-executed experimental n8n workflow, `WStqWRlqax7iocOx` "ANIME-LAB — VIDEO-SMOKE-001 — Scene Intelligence". No CF workflow, no Clip Farming table/view/function/trigger, no Clip Farming GitHub path, no dedicated credential, no Slack channel. Design inputs exist only as project files. Evidence: `evidence/SPRINT_00_BASELINE_EVIDENCE.md`.

## 2. What is genuinely reusable?
Patterns, not objects: from the Anime Lab workflow, its fail-closed input validation, placeholder guard, strict response schema, deterministic parse/validate nodes, "no rights assessment" prompt rules and mock-branch testing (→ CF-002). From A1-FOUNDATION, the `reviewers`, `agent_runs` and `gate_decisions` concepts. From the V&A playbook, UUID identity, exact-version starts, fail-closed gates, append-only history.

## 3. What should be preserved but not used?
`WStqWRlqax7iocOx` (keep unpublished, unexecuted); the A0 design and A1-FOUNDATION schema as history; the shared `Google API - x-goog-api-key` and `YouTube account` credentials until ownership/channel are confirmed; all Kids-lane credentials (never for CF).

## 4. What is missing?
Everything operational: the `cf` schema and tables, a dedicated DB role + n8n credential, all CF agents, reviewer roster, gate surface, asset bucket, confirmed publishing accounts, a verified Google Cloud project ID, and the A0 document itself.

## 5. What exact tables are proposed?
In schema `cf` (23): `reviewers`, `agent_runs`, `system_flags`, `anime_franchises`, `anime_titles`, `anime_source_episodes`, `research_candidates`, `anime_scene_intelligence`, `editorial_opportunities`, `editorial_opportunity_scenes`, `content_scripts`, `publication_source_packages`, `publication_source_items`, `gate_decisions`, `production_manifests`, `production_jobs`, `content_assets`, `renders`, `published_content`, `platform_posts`, `performance_snapshots`, `content_learning_log`, `allowed_transitions`. Views: `v_effective_gate_decisions`, `v_scene_publication_status`, `v_publish_eligibility`. Changes vs the brief's 13: `publication_source_decisions` replaced by `gate_decisions`; added research_candidates, franchises, opportunity_scenes, source_items, renders, platform_posts, reviewers, agent_runs, system_flags, allowed_transitions. Rationale per table: `architecture/data-contracts/DATA_MODEL_v0.1.md` §2.

## 6. What exact identities are proposed?
All 14 from the brief (`anime_title_id`, `source_episode_id`, `scene_id`, `research_candidate_id`, `content_candidate_id`, `script_id`, `source_package_id`, `production_manifest_id`, `production_job_id`, `asset_id`, `render_id`, `published_content_id`, `performance_snapshot_id`, `learning_log_id`) plus `franchise_id`, `source_item_id`, `gate_decision_id`, `platform_post_id`, `agent_run_id`, `reviewer_id`. All database-generated UUIDs; never model- or human-assigned; revisions get new IDs. `learning_log_id` proposed as canonical over the blueprint's `learning_record_id`. Owner, creation point, immutability, consumers, dedupe, FKs per identity: `IDENTITY_CONTRACTS_v0.1.md`.

## 7. What states are proposed?
The brief's nine words unchanged (IDEA, DRAFT, REVIEW, APPROVED, REJECTED, BLOCKED, READY, PUBLISHED, RETIRED), restricted per object, with explicit per-object edges stored in `cf.allowed_transitions` and enforced by trigger. One addition for decision: a separate run-state enum (QUEUED, RUNNING, SUCCEEDED, FAILED, CANCELLED) for `agent_runs` and `production_jobs` only. `APPROVED_FOR_PUBLISH` recommended as render `APPROVED` + G4 decision with `approved_platforms`, not a tenth status. `STATE_MODEL_v0.1.md`.

## 8. How do human approvals work?
A named reviewer records APPROVE / REJECT / REVOKE through `cf.record_gate_decision()`, which checks reviewer authority, object state and content hash, appends to `cf.gate_decisions`, and moves the object's status in the same transaction. Triggers reject any APPROVED edge without an effective matching decision, so an agent cannot approve by writing a status. The agent DB role has no grant on decisions. Downstream agents re-validate status + effective decision + content hash + unrevoked chain, and fail closed. `HUMAN_GOVERNANCE_GATES_v0.1.md`.

## 9. How is research-source intelligence separated from publication-source approval?
Structurally: scenes store only research provenance (`research_source_*`, `research_access_basis`) and have **no** publication or rights column. Publication material lives only in `publication_source_packages` / `publication_source_items`, created by CF-005, and becomes usable only by a G3 human decision. A scene's publication status is a derived view that returns `UNKNOWN` unless a G3-approved package includes it, and that approval is scoped to one script. No column anywhere means fair-use / copyright-safe / legal-safe (static test T-RIGHTS-01). Monetisation eligibility and legal determination are not modelled at all.

## 10. What are CF-001 … CF-009's contracts?
Core question, inputs, outputs, allowed intelligence, deterministic duties, gate, forbidden actions, replay, zero-input and paid/external behaviour for each: `architecture/workflow-contracts/AGENT_CONTRACTS_CF001_CF009_v0.1.md`.

## 11. What are the dependencies between agents?
Linear hard chain CF-001 → CF-002 → CF-003 → [G1] → CF-004 → [G2] → CF-005 → [G3] → CF-006 → CF-007 → [G4] → CF-008 → CF-009, with one soft read-only feedback edge CF-009 ┄► CF-001/CF-003 that re-enters through G1. No hard cycle. CF-000 is not upstream of anything. `DEPENDENCY_MAP_v0.1.md`.

## 12. Where can paid activity eventually occur?
CF-001 (optional LLM), CF-002 (video understanding), CF-003/CF-004 (LLM), CF-005/CF-006 (optional LLM), **CF-007 (TTS, generation, rendering, storage — highest risk)**, CF-009 (optional LLM). Each requires `PAID_CALLS_ENABLED` and a per-run `paid_authorisation_ref`, enforced by CHECK constraints (T-PAID-01).

## 13. Where can external publication eventually occur?
Only CF-008, only for renders in `cf.v_publish_eligibility`, only to platforms the G4 reviewer listed, only with `PUBLISH_ENABLED` and an item-level authorisation.

## 14. What tests should precede each side effect?
The ten-step free-first ladder and the per-agent minimum free suites in `SPRINT_00_TEST_STRATEGY.md`. Summary: DB writes need static + no-write regression + replay tests on a disposable schema first; paid calls need steps 1–6 green, written approval, then a one-item smoke with retries 0; publication needs eligibility-view, flag-off, wrong-platform and double-upload tests against a mocked platform API.

## 15. What exact objects would Sprint 1 create? (proposal, needs authorisation)

**Supabase (one migration, only after explicit migration approval):**
- schema `cf`; types `lifecycle_status`, `run_state`, `gate_code`, `gate_decision_value` (the last two only so `allowed_transitions` loads; no gate table yet)
- tables `cf.agent_runs`, `cf.system_flags` (seeded OFF), `cf.anime_franchises`, `cf.anime_titles`, `cf.research_candidates`, `cf.allowed_transitions` (rows for those three object types only)
- functions `cf.touch_updated_at`, `cf.guard_status_transition`, `cf.freeze_after_first_status`, `cf.forbid_delete` and their triggers on the three lifecycle tables
- role `cf_agent` + one login role for n8n (password created by a human, not by Claude)

**n8n (unpublished, manual trigger only, no schedule):**
- `CF-001 — Market & Trend Radar` v0.1 — deterministic scoring only, no LLM node
- `TEST — CF-001 Free Suite` — fixtures + mock source responses, no writes

**GitHub:** `sprints/SPRINT_01_CF001/` (sprint report, test evidence), migration file `architecture/data-contracts/migrations/0001_cf_sprint01.sql` (applied version), changelog entry.

Not in Sprint 1: scenes, editorial, gates, production, publishing tables.

## 16. What blockers exist before CF-001?

| # | Blocker | Owner |
|---|---|---|
| B-1 | Company Brain acceptance of this package, including decisions D-DB-1 (same project, `cf` schema), D-DB-2 (Postgres-node access with a dedicated role), D-STATE-1 (run-state enum), D-STATE-2 (G4 as APPROVED + decision), and the table list changes | Company Brain / Viva |
| B-2 | Explicit authorisation to apply the Sprint 1 migration subset to the shared Supabase project | Company Brain / Viva |
| B-3 | A human creates the `cf_agent` login password and the n8n Postgres credential (Claude must not see or print it) | Viva |
| B-4 | CF-001 source decision: which free sources (proposed: AniList GraphQL, public, no key; optionally YouTube Data API with a **dedicated** key, not the shared Google key) and their terms | Company Brain / Viva |
| B-5 | Confirm CF-001 v0.1 runs with no LLM (deterministic scoring); any LLM use later needs a paid-call authorisation | Company Brain |
| B-6 | Google Cloud project identity unverified (only matters if a GCP key/BigQuery is used) | Viva |
| B-7 | Blueprint version label (v1.0 header vs v1.4 filename) and approval status confirmed | Company Brain |
| B-8 | Not blocking Sprint 1, needed by Sprint 3: reviewer roster and gate surface (D-GOV-1/2) | Viva |

## 17. Recommendation for Sprint 1
Authorise **Sprint 1 — CF-001 v0.1 (deterministic, free sources, manual trigger)** in two bounded stages:
1. **1A (free, no production writes):** build `TEST — CF-001 Free Suite` and the unpublished `CF-001` workflow with in-memory writes only; pass §3 CF-001 tests and N-01…N-15; return evidence. Stop.
2. **1B (after a separate yes):** apply the §15 migration subset, create the dedicated credential (human), run the no-write regression against the real schema, then one live manual run writing research candidates for one ISO week. Stop.

Keep the Anime Lab workflow untouched until Sprint 2 (CF-002) is authorised. Decide B-1…B-5 first.

---

## Exit criteria (brief §25)

| Criterion | Met? | Evidence |
|---|---|---|
| Every proposed operational object has an authoritative identity | ✅ | IDENTITY_CONTRACTS_v0.1 |
| CF-001…CF-009 input/output contracts | ✅ | AGENT_CONTRACTS_CF001_CF009_v0.1 |
| Approval gates explicit | ✅ | HUMAN_GOVERNANCE_GATES_v0.1; T-GATE-* |
| Research vs publication source structurally separate | ✅ | DATA_MODEL §4.8/4.12; T-SRC-02/03, T-RIGHTS-01 |
| State semantics documented | ✅ | STATE_MODEL_v0.1 |
| Database design documented | ✅ | DATA_MODEL_v0.1 + DESIGN_ONLY SQL |
| GitHub structure documented | ✅ | README folder map |
| Dependency map complete | ✅ | DEPENDENCY_MAP_v0.1 |
| Free-test strategy documented | ✅ | SPRINT_00_TEST_STRATEGY |
| No production migration | ✅ | Supabase migrations still 1 (Kids `s3a_…`) |
| No paid provider call | ✅ | 0 provider calls |
| No social publication | ✅ | 0 |
| No production agent built | ✅ | 0 CF workflows |
| Enough evidence to authorise or reject Sprint 1 | ✅ | this report §15–17 |

**STOPPED. Waiting for human / Company Brain reconciliation. Sprint 1 is not authorised by this report.**
