# CF-002 data and provenance contract (migration 0004)

Migration `0004_cf002_scene_intelligence` (history version `20261013044838`) adds to schema `cf`: type `research_access_basis`; tables `anime_source_episodes`, `anime_scene_intelligence`; view `v_scene_publication_status`; one unique index on `research_candidates (research_candidate_id, anime_title_id)` for composite FKs. 11 new transitions (25 total), 8 new triggers (20 total). Migrations 0001-0003 untouched.

## Keys and dedupe
- Episode: natural key UNIQUE (title, season, episode_number numeric(6,1), variant).
- Scene: `dedupe_key = sha256(source_episode_id | floor(start_ms/1000) | ceil(end_ms/1000))`. Rediscovery of the same scene with a different source or summary inserts nothing (ON CONFLICT DO NOTHING); original provenance is kept.
- Overlap of at least 80% of the shorter span with an existing scene: stored DRAFT with `possible_duplicate_of_scene_id`, never promoted. Choice: DRAFT hold (identity contract) rather than BLOCKED (state model); recorded in ADR-004.
- Composite FKs bind scene→episode and scene→candidate to the same title; mismatches cannot be stored.

## Provenance (per scene)
Source platform, durable source reference (slug or https URL; a CHECK rejects credential-like strings), `research_access_basis`, `research_observer`, `research_observed_at` (NOT NULL), integer ms boundaries, `timestamps_human_verified`, agent_run_id. Copyright-minimal: original short summary and reason only; no transcript, no frames, no media, text-length CHECKs enforce it.

## Publication status
There is no rights or publication column on any table. `v_scene_publication_status` is a constant view returning `UNKNOWN`. Nothing in CF-002 can set APPROVED, CLEARED, SAFE, LICENSED, FAIR_USE or MONETISABLE; CF-005 owns rights.

## Runtime grants (`cf_n8n_runtime`)
SELECT on both tables and the view; INSERT on both tables; column-level UPDATE only on episodes (status, episode_title_display, duration_seconds) and scenes (status, timestamps_human_verified). No DELETE, TRUNCATE, CREATE or TRIGGER. Nothing for PUBLIC, anon, authenticated or service_role. Delete is forbidden by trigger for every role; HUMAN_ADMIN transitions stay denied to the runtime identity (ADR-002).
