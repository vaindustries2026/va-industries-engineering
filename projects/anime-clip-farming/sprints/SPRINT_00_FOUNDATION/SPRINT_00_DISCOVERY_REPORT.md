# Sprint 0 — Discovery Report

**Mode:** read-only. Raw evidence: `../../evidence/SPRINT_00_BASELINE_EVIDENCE.md`.

## Answers to brief §4 (1–13)

| # | Question | Answer |
|---|---|---|
| 1 | Project / repository inspected | GitHub `vaindustries2026/va-industries-engineering`; n8n project `VA Industries <vaindustries26@gmail.com>` (`eMjDEqobimuAbLo7`); Supabase project `VA-Company-Brain*` (`ziluiwrwwbayhcskeere`); Slack workspace (channel search only); Google Cloud (not reachable, see blockers) |
| 2 | Current Git branch | `main` at start; Sprint 0 work on new branch `engine2/clip-farming-sprint-00-foundation` |
| 3 | Current commit / HEAD | `14f66e10664d6f295ef74402998e22949714098b` |
| 4 | Existing Clip Farming GitHub paths | **None.** No `projects/`, no anime/CF path on `main` or on the 3 other branches |
| 5 | Existing Clip Farming n8n workflows | **One experimental Anime Lab workflow.** No `CF-*` workflow |
| 6 | Exact workflow IDs | `WStqWRlqax7iocOx` — "ANIME-LAB — VIDEO-SMOKE-001 — Scene Intelligence" |
| 7 | Published / draft state | `active: false`, `activeVersionId: null` (never published); current version `9ce21a4f-992c-41c8-bbcd-ff29f5d43884` ("E2-VIDEO-SMOKE-001B-RESET"); 0 executions on record |
| 8 | Clip Farming Supabase tables / views / functions / triggers | **None.** Only `public` holds app tables, all YouTube Kids. No A1-FOUNDATION table exists |
| 9 | Clip Farming credentials / integrations | **None dedicated.** The smoke workflow uses the shared `Google API - x-goog-api-key` (`MpX1PC9vapbWYQji`). A `YouTube account` OAuth credential (`bJgwIJkzHaL3SjbT`) exists; its channel is unknown. Supabase / Runway / Slack credentials belong to the Kids lane |
| 10 | Clip Farming scripts / config files | **None** in the repo. Design inputs live only in project files (`/mnt/project-files/knowledge/VA_ANIME_CLIP_FARMING_*`) |
| 11 | Existing work mapping to CF-001…CF-009 | `WStqWRlqax7iocOx` partially maps to **CF-002** (model-assisted candidate moments from a public video, fail-closed validation, explicit "no rights assessment" prompt). Nothing maps to CF-001, CF-003…CF-009. The A1-FOUNDATION schema (design only, never applied) maps conceptually to several CF tables (see gap analysis §3) |
| 12 | Experimental work to preserve, not canonical | `WStqWRlqax7iocOx` (keep unpublished and untouched); A0 design and A1-FOUNDATION schema (historical design records); E2-ANIME-SMOKE-001 / E2-VIDEO-SMOKE-001A/B briefs (history) |
| 13 | Gaps between live state and the blueprint | Everything in the blueprint is still to be built. See `SPRINT_00_GAP_ANALYSIS.md` |

## Drift check (brief §4 stop rule)

**Result: no material contradiction; proceeded to design.**

The expected state for Sprint 0 is "nothing CF-* built yet", and that is what exists. The findings below are recorded, not silently merged:

| Finding | Type | Handling |
|---|---|---|
| Live workflow is "ANIME-LAB — VIDEO-SMOKE-001 — Scene Intelligence" (brief IDs E2-VIDEO-SMOKE-001A, then 001B-RESET). Project memory records the earlier brief as "ANIME-SMOKE-001 — Scene Intelligence Analyst" (E2-ANIME-SMOKE-001) with `rights_status ∈ {ANALYSIS_ONLY, AUTHORIZED_TEST}`; live node 02 accepts only `source_authorisation = AUTHORIZED_TEST` | Documentation drift (live overrides memory) | Recorded. Live object is authoritative. Classified EXPERIMENTAL / LEGACY naming. Not renamed (renaming would be a write) |
| Earlier Anime Shorts Lab stages used `ANIME-*` naming and an 11-table A1-FOUNDATION schema; this brief uses `CF-*` and a 13-table list | Design-level divergence, nothing live | Reconciled explicitly in the gap analysis concept map (§3). CF-* naming adopted per this brief; A1 concepts carried over where they fill a gap (`reviewers`, `agent_runs`, `gate_decisions`); none silently dropped |
| Blueprint filename says v1.4, its header says v1.0, status "PROPOSED BUILD BLUEPRINT — HUMAN APPROVAL REQUIRED" while the brief calls it the approved blueprint | Version label inconsistency | Committed byte-for-byte (sha256 `f9f1013a…0992`) as `architecture/ENGINE2_INFRASTRUCTURE_BLUEPRINT.md`. Company Brain to confirm the approved version label |
| A0 design document `VA_ANIME_SHORTS_LAB_SYSTEM_DESIGN_v0.1.md` not found in the repo or project files | Missing historical record | Recorded as UNKNOWN; human to supply it for the archive |
| Blueprint governance line lists "Gilang / Viva"; the project instructions put Engineer-2 under Viva and say Engineer-1 is Gilang's lane | Ownership ambiguity for reviewers, not for this sprint's work | Reviewer identities left as a human decision (D-GOV-1) |

## Things that are not Engine 2 and were not opened

21 workflows (Router, AGENT-001…007 and their TEST/HARNESS/ARCHIVE copies), all 14 `public` tables, 4 views, 3 `a007_*` functions, the storage bucket, the Kids GitHub evidence. Only names/IDs/row counts from list calls were seen.
