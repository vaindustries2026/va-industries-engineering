# CF-002 workflow design

Workflow `CF-002 — Scene Intelligence & Provenance v0.1.1` (renamed in place from v0.1): n8n id `tmqsoycNV6k4iKr6`, versionId `140ea945-91a1-4330-b288-3478d6dfc635` (v0.1 was `ee46f03f-a945-4baa-b35b-bece0c4fa8a1`, restorable from n8n version history), INACTIVE, 25 nodes, Manual Trigger only (no schedule, cron, webhook or CF-001 chain). Credential `e08pNFP1Th42jXyO` by id only. Deployed SDK source: `evidence/cf-002-tools/generated/cf002_workflow.sdk.ts`; stage code in `evidence/cf-002-tools/src/`.

## Principle
The workflow is deterministic. There is no model node, no HTTP node and no paid call. Humans supply the observation; code validates, normalises and persists. Identity, dedupe, timestamps (integer ms), provenance, lifecycle and run bookkeeping are owned by code and the database, never by text a model or human typed into a free field.

## Input
`execute_workflow` cannot pass manual-trigger inputs, so a live intake is embedded in `DEFAULT_INTAKE` in the Run Config node (tests use pinned trigger data). Intake: `research_candidate_id`, `anime_title_id`, episode locator (season, number, variant), source platform and durable reference, `research_access_basis`, observer, `observed_at`, and 1-3 scenes (start/end as MM:SS or ms, original summary, why it matters, spoiler level). Zero input is a valid, recorded no-op.

## Node map
Run Config → Begin Run → Run Started? → Validate Upstream → Resolve Title → Validate Observation → Normalise Boundaries → Build Intelligence → Validate Provenance → Run Still OK? → Has Input? → Bootstrap Catalog (v0.1.1; no-op unless validation mode) → Upsert Episode → Promote Episode → Insert Scenes → Promote Scenes → Verify Persisted → Complete Run → Return Run Summary.
Failure path: Shape Failure → Mark Run Failed → Raise Failure. Replay path: Load Existing Run Outputs → Replay Summary. Plus the Manual Trigger.

## Lifecycle and idempotency
Every run writes `cf.agent_runs` (agent_code CF-002; paid=0, cost=0). Idempotency basis `CF-002|v0.1|canon(input_ids)` where input_ids are candidate, title, episode locator, source platform and reference, and sorted boundary ms. Summaries and notes are not identity. A second execution with the same basis returns the existing run (REPLAY) with 0 writes. Zero input uses `CF-002|v0.1|NO_INPUT`.

## Fail closed
Mismatched candidate/title, missing or future `observed_at`, boundary out of order, more than 3 scenes, credential-like source reference, or any rights-state field in the intake: run marked FAILED, nothing persisted, error raised. Timestamps are never guessed.

## v0.1.1 validation mode
Explicit mode `CF002_VALIDATION_SOURCE_OUTSIDE_CF001_BATCH` (see CF002_POLICY_AND_VALIDATION_DECISIONS.md). The patch is workflow-only: Run Config adds the mode and catalog keys to the idempotency identity only when the mode is present; Resolve Title branches; Validate Observation validates the catalog; Build Intelligence stamps the lineage marker; Validate Provenance carries a null candidate; the new Bootstrap Catalog node resolves or creates one DRAFT franchise and one DRAFT title; Insert Scenes stores a NULL candidate. Begin Run now writes the agent version from the run input instead of a literal. Production-mode identities, validators and SQL are unchanged apart from the version string.
