# ADR-004 — CF-002 scene tables and runtime access

**Status:** ACCEPTED and applied under the Sprint 2 brief (2026-10-13). **Recorded by:** Claude Engineer-2 (human owner Viva).
**Related:** ADR-002, ADR-003, `../data-contracts/migrations/0004_cf002_scene_intelligence.sql`.

## Decisions
- **Separate migration 0004**; 0001-0003 unchanged. The guard verifies function md5s, pinned search_path and the HUMAN_ADMIN block before changing anything.
- **No publication column.** Publication status is a constant `UNKNOWN` view; rights belong to CF-005.
- **Additions beyond the Sprint 0 design:** `research_observed_at` NOT NULL, `research_observer`, text-length CHECKs (copyright-minimal), a credential-like regex CHECK on the source reference, composite FKs (scene→episode and scene→candidate on the same title) backed by one unique index on research_candidates, the constant view, column-level grants.
- **Runtime access:** SELECT and INSERT on the two tables, column-level UPDATE on status-type columns only, no DELETE/TRUNCATE/CREATE/TRIGGER, nothing for other roles.
- **Dedupe:** scene key excludes the source reference so rediscovery keeps original provenance; ≥80% overlap is stored DRAFT with a pointer rather than BLOCKED, matching the identity contract (the state model says BLOCKED; flagged for reconciliation).

## Consequences
Runtime cannot delete or alter content; rollback needs a human and an explicit data-destroy flag if rows exist.
