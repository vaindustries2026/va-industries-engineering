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

## Addendum 2026-10-13: validation mode needs no schema change
`research_candidate_id` was already nullable, and the DRAFT catalog rows use the existing runtime INSERT grants from 0001. The v0.1.1 validation mode (CF002_VALIDATION_SOURCE_OUTSIDE_CF001_BATCH) is therefore workflow-only: no migration, no new privilege. The lineage marker lives in the scene's `research_access_notes` and the run's input and output evidence because the catalog tables have no notes column and none was added. Spoiler policy is a business rule (CF002-POLICY-SPOILER-001), not a schema rule: `spoiler_level` stays NOT NULL descriptive metadata and gates nothing.
