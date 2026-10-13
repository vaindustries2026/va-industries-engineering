# Sprint 2 — CF-002 Scene Intelligence & Provenance v0.1

**Status:** `CF002_BUILD_COMPLETE_LIVE_SOURCE_PENDING`. Migration 0004 applied, workflow built and patched to v0.1.1 (inactive, manual trigger only), all tests pass. No scene is persisted live because no legitimate human research observation has been supplied. Stopped before CF-003.

| Document | Content |
|---|---|
| [CF002_WORKFLOW_DESIGN.md](CF002_WORKFLOW_DESIGN.md) | 24-node map, run lifecycle, idempotency |
| [CF002_DATA_AND_PROVENANCE_CONTRACT.md](CF002_DATA_AND_PROVENANCE_CONTRACT.md) | tables, keys, grants, dedupe, publication status |
| [CF002_SOURCE_RESEARCH_RULES.md](CF002_SOURCE_RESEARCH_RULES.md) | research vs publication, Crunchyroll rules, experimental pattern classification |
| [CF002_TEST_PLAN_AND_RESULTS.md](CF002_TEST_PLAN_AND_RESULTS.md) | local and live test results |
| [CF002_LIVE_SMOKE_EVIDENCE.md](CF002_LIVE_SMOKE_EVIDENCE.md) | live runs, DB state, the pending human requirement |
| [CF002_POLICY_AND_VALIDATION_DECISIONS.md](CF002_POLICY_AND_VALIDATION_DECISIONS.md) | spoiler policy, Pokémon validation case, v0.1.1 mode |
| [CF002_FINAL_REPORT.md](CF002_FINAL_REPORT.md) | final status and handoff |

Decisions: [ADR-004](../../architecture/decisions/ADR-004_CF002_SCENE_TABLES_AND_RUNTIME_ACCESS.md). Tools and evidence: `../../evidence/cf-002-tools/`.
