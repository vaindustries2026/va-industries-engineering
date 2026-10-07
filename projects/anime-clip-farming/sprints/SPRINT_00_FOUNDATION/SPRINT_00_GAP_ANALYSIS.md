# Sprint 0 — Gap Analysis

Compares live Engine 2 state (2026-10-07) against the target architecture in `architecture/`. Classification vocabulary from the brief: ALIGNED · PARTIALLY_ALIGNED · EXPERIMENTAL · LEGACY · UNSAFE_TO_REUSE · DUPLICATE · UNKNOWN. Disposition: KEEP · ADAPT · ARCHIVE · REPLACE. **Nothing was removed, renamed or modified.**

## 1. Existing objects

| Object | Where | Class | Disposition | Why |
|---|---|---|---|---|
| `WStqWRlqax7iocOx` ANIME-LAB — VIDEO-SMOKE-001 — Scene Intelligence | n8n | **EXPERIMENTAL** | **KEEP** untouched now; **ADAPT** patterns into CF-002 later | Reusable: fail-closed input validation (02), placeholder guard, strict JSON schema with `additionalProperties:false`, deterministic parse (05) and collect-all-violations validation (06), prompt rules forbidding rights/fair-use assessment and footage extraction, isolated mock branch for free testing. Not canonical: no stable IDs, no persistence, `ANIME-LAB` naming, single-item manual flow, paid node 04 with a shared credential, rights input is a free string not a governed `research_access_basis`. Never executed, so no output evidence exists. Do not publish or run it without a separate brief |
| Node 04 credential `Google API - x-goog-api-key` (`MpX1PC9vapbWYQji`) | n8n | **UNKNOWN** | KEEP; do not reuse for CF until ownership is confirmed | Billing project, quota and whether the Kids lane also uses it are not recorded |
| `YouTube account` (`bJgwIJkzHaL3SjbT`) | n8n | **UNKNOWN** | Do not use for CF-008 | Bound channel unknown; publishing with it could post to the wrong channel |
| `V&A - Supabase Service Role - AGENT007`, `Supabase account`, `Runway API - AGENT-007`, Slack credentials | n8n | **UNSAFE_TO_REUSE** (for CF) | KEEP (not ours) | Kids-lane credentials; service role bypasses the CF grant model |
| `OpenAI account`, `n8n free OpenAI API credits` | n8n | **UNKNOWN** | Decide per sprint | Shared; any use is a paid/credit decision needing authorisation |
| A1-FOUNDATION 11-table schema (memory record) | design only | **LEGACY** (partially aligned concepts) | **ARCHIVE** as history; concepts mapped below | Never applied (0 tables live). Uses ANIME-era naming |
| A0 `VA_ANIME_SHORTS_LAB_SYSTEM_DESIGN_v0.1.md` | not found | **UNKNOWN** | Human to supply → ARCHIVE under `evidence/` | Accepted by the Company Brain per memory, but no copy is reachable |
| E2-ANIME-SMOKE-001 brief (memory) vs live E2-VIDEO-SMOKE-001A/B | memory vs n8n | **LEGACY** (doc drift) | Record only | Live object wins; see discovery report |
| Blueprint + strategy docs (`/mnt/project-files/knowledge/VA_ANIME_CLIP_FARMING_*`) | project files | **ALIGNED** (source inputs) | KEEP; blueprint committed to repo | Version labels inconsistent (file v1.x vs header v1.0) |
| V&A playbook patterns (`company-brain/VA_02_*`) | repo | **ALIGNED** (patterns only) | Reuse conceptually | UUID identity, exact-version starts, fail-closed gates — re-implemented as new CF objects, no Kids object touched |
| `public.*` Kids tables/views (e.g. `market_scout_rankings`, `videos`) | Supabase | **UNSAFE_TO_REUSE** | Do not read as CF state | Blueprint §18 no-cross-project-data rule |

No DUPLICATE objects exist (there is only one Engine 2 object live).

## 2. Target vs live

| Target component | Live state | Gap |
|---|---|---|
| GitHub `projects/anime-clip-farming/` | absent before Sprint 0 | **Closed by this sprint** (documentation only) |
| Supabase `cf` schema + 23 tables | absent | Full build, staged by sprint; Sprint 1 subset in architecture report §15 |
| Dedicated CF DB role + n8n credential | absent | Human must create (blocker for Sprint 1) |
| `CF-001` … `CF-009` workflows | absent | Built one per sprint |
| Reviewer roster + gate surface | absent | Human decision (D-GOV-1/2) before Sprint 3 |
| CF Slack channel | absent | Optional; only if Slack becomes the gate surface |
| Storage bucket for CF assets | absent | Needed by Sprint 7 |
| Confirmed V&A anime publishing accounts | unknown | Needed by Sprint 8 |
| Google Cloud project identity | unverified | Needed only if a sprint uses GCP/BigQuery |

## 3. A1-FOUNDATION → CF concept map (explicit reconciliation, not a silent merge)

| A1-FOUNDATION table | CF v0.1 equivalent | Status |
|---|---|---|
| angle_taxonomy | `editorial_angle_key` normalised against a list; table **deferred** | Future: promote to `cf.editorial_angles` when CF-003 is built |
| reviewers | `cf.reviewers` | Carried over |
| rightsholders | — | **Deferred.** Rights knowledge is human-maintained; useful later as G3 reference data, never as an automated permission source |
| franchises | `cf.anime_franchises` | Carried over (renamed) |
| franchise_rights_map | — | **Deferred**, same reason as rightsholders. Must never become an auto-approve rule |
| short_backlog | `cf.editorial_opportunities` | Replaced (CF naming) |
| scripts | `cf.content_scripts` | Replaced |
| source_usage_items | `cf.publication_source_items` | Replaced |
| source_usage_reviews | `cf.gate_decisions` (gate G3) | Replaced by the unified gate log |
| gate_decisions | `cf.gate_decisions` | Carried over, extended to G1–G4 |
| agent_runs | `cf.agent_runs` | Carried over |

A1 rights decisions that still stand and are built into v0.1: no automated fair_use / copyright_safe field (T-RIGHTS-01); no rule-of-thumb safety rules (CF-005 forbidden list); never download, defeat DRM, scrape/log into streaming services, extract clips, or publish (shared agent contract §0.8).

## 4. FUTURE_RECOMMENDATIONS (recorded, untouched)

- Add `projects/anime-clip-farming/` to the root `README.md` / `CLAUDE.md` reading order and to `SOURCE_PACK_MANIFEST.json` — left untouched because those are shared repo files outside the Sprint 0 boundary.
- Record a written branch policy for the repo (`engine2/*` for Engine 2; `claude/*` is currently harness-generated).
- Consider a CI check that fails a PR touching both `projects/anime-clip-farming/` and Kids paths.
- Consider renaming `WStqWRlqax7iocOx` to a `TEST — CF-002 …` name once CF-002 is authorised (a write, so not done now).
- Ask the Company Brain to settle the blueprint version label (v1.0 vs v1.4).
