# Engine 2 — Agent Contracts CF-001 … CF-009 v0.1

**Status:** PROPOSED — DESIGN ONLY. **No CF agent exists.** No n8n workflow named `CF-*` was found or created in Sprint 0.
**Naming:** n8n workflow names exactly as listed (e.g. `CF-001 — Market & Trend Radar`). Never `AGENT-00x` (that namespace is the YouTube Kids system). Test harnesses: `TEST — CF-00x <purpose>`.

## 0. Contract shared by every agent

1. **First node is deterministic:** validate input UUIDs (`MALFORMED_UUID`), compute the run `idempotency_key`, insert or find `cf.agent_runs`. Found + `SUCCEEDED` → return the existing outputs and stop (replay). No model call happens before this node.
2. **Upstream check:** re-read upstream status and gate decisions; any mismatch → named fail-closed exit, zero writes.
3. **Model output is data, never control:** parse → schema-validate → contamination checks → only then persist. A model never writes IDs, status, timestamps, counters or gate data.
4. **Persist in one transaction** with the upstream re-check (stale-safe).
5. **Kill switches:** read `cf.system_flags`; paid calls need `PAID_CALLS_ENABLED` **and** a per-run `paid_authorisation_ref`; publishing needs `PUBLISH_ENABLED` and the item's G4 decision.
6. **Zero-input exit:** no usable input → `agent_runs.run_state = SUCCEEDED`, `output_summary = {"result":"NO_INPUT"}`, zero output rows, zero provider calls.
7. **Failure:** any error → `run_state = FAILED`, `error_code`, no partial outputs (transaction rollback). Automatic retries default to 0 for paid nodes, ≤1 for free reads.
8. **Out of bounds for all agents:** downloading episodes, defeating DRM, scraping or logging into streaming services, extracting clips from streams, writing any `public.*` (YouTube Kids) object, calling any `AGENT-00x` workflow or the Slack Command Router, approving anything, deciding rights or legality.

---

## CF-001 — Market & Trend Radar

| | |
|---|---|
| **A. Core question** | Which anime, franchises, topics, eras or fandom moments are worth investigating this week? |
| **B. Inputs** | Run parameters only: `observation_window` (ISO week), lane mix targets, optional seed `anime_title_id[]`. No upstream approval needed. Soft input: `content_learning_log` rows (READY learnings) and prior `research_candidates`. |
| **C. Outputs** | `cf.research_candidates` (status IDEA → READY/REJECTED), plus resolver-created `cf.anime_franchises` / `cf.anime_titles` (DRAFT/READY/BLOCKED). IDs: `research_candidate_id`, `anime_title_id`, `franchise_id`, `agent_run_id`. |
| **D. Allowed intelligence** | Summarise signals, classify content lane and trend state, score editorial potential, nostalgia and timeliness, write `topic_display`. |
| **E. Deterministic** | Title/franchise resolution against external IDs (AniList/MAL), `topic_key` normalisation, `dedupe_key`, window calculation, signal arithmetic from raw metrics, evidence completeness, contamination checks (title must belong to the stated franchise; topic must match the lane list), status. |
| **F. Human gate** | None. CF-002 consumes READY candidates. |
| **G. Forbidden** | Create scripts or editorial ideas; choose footage; approve; upload; write rights fields; touch Kids tables (`public.videos`, `video_snapshots`, `market_scout_rankings` are Kids objects and must not be read as CF state either); paid search. |
| **H. Replay** | Same window + same inputs → same `agent_runs.idempotency_key` → existing outputs returned. A candidate already in the window → `dedupe_key` conflict → no new row (`ON CONFLICT DO NOTHING`, counted as duplicate). |
| **I. Zero input** | No signals for the window → `NO_INPUT`, zero rows. Ambiguous titles → BLOCKED title, candidate not created. |
| **J. Paid / external** | Possible later: LLM summarisation/ranking (paid unless a free credit pool is explicitly authorised); YouTube Data API (free quota, needs a dedicated key); AniList GraphQL (free, public). No uploads. First version should be deterministic scoring with **no model**. |

## CF-002 — Scene Intelligence & Provenance

| | |
|---|---|
| **A. Core question** | Which exact scenes are worth discussing, where are they, and why do they matter? |
| **B. Inputs** | `research_candidate_id` (READY) or a human scene-intake record (`anime_title_id`, season, episode, start/end, research provenance). For model-assisted analysis: a public video URL whose `research_access_basis` is `PUBLIC_OFFICIAL_UPLOAD` and which a human authorised for analysis. |
| **C. Outputs** | `cf.anime_source_episodes` (via resolver), `cf.anime_scene_intelligence` (DRAFT → READY/BLOCKED). IDs: `scene_id`, `source_episode_id`. |
| **D. Allowed intelligence** | Describe the scene, its narrative function, why it matters, possible angles, context needed, spoiler level, visual strength, editorial strength label; propose timestamps (marked unverified). |
| **E. Deterministic** | Episode resolution, timestamp parsing and span validation, `dedupe_key`, overlap detection, provenance completeness, `research_access_basis` from the intake record (never from the model), status. |
| **F. Human gate** | None, but `timestamps_human_verified` must be true before a scene can be the primary scene of a G1 review packet (CF-003 check). |
| **G. Forbidden** | Infer publication permission from research access; write any publication/rights field; download, clip or store footage; log into streaming services; analyse non-public or DRM content. |
| **H. Replay** | Same episode + same rounded span → existing `scene_id`. Overlapping span → new DRAFT flagged `possible_duplicate_of_scene_id`, never merged. |
| **I. Zero input** | No READY candidate and no intake → `NO_INPUT`. Candidate with no locatable episode → scene not created; reason in `output_summary`. |
| **J. Paid / external** | Video-understanding model call (e.g. Gemini) is **paid**; the existing `ANIME-LAB — VIDEO-SMOKE-001` workflow is the experimental precedent and has never been executed. No uploads. |

## CF-003 — Editorial Opportunity Planner (→ G1)

| | |
|---|---|
| **A. Core question** | What original V&A content should we make from this intelligence? |
| **B. Inputs** | READY `scene_id[]` and/or READY `research_candidate_id`, `anime_title_id`; soft: learning log, existing live opportunities (to avoid duplicates), lane mix targets. |
| **C. Outputs** | `cf.editorial_opportunities` (IDEA, then REVIEW if valid) + `cf.editorial_opportunity_scenes`. ID: `content_candidate_id`. |
| **D. Allowed intelligence** | Editorial angle, territory, working hook, audience, format class and duration proposal, why now / why viewer cares, hypothesis, primary metric, difficulty, rank, `recommend_for_review`. |
| **E. Deterministic** | `editorial_angle_key` normalisation against the angle list, `dedupe_key`, `output_ordinal`, `content_sha256`, format/duration consistency (duration inside the format's band), wrong-franchise check (all linked scenes share the title), IDEA → REVIEW transition. |
| **F. Human gate** | **G1** blocks CF-004. |
| **G. Forbidden** | Approve itself; set APPROVED; create publication permission; force one duration; propose raw reposting (an idea whose value is only the clip fails validation: `hypothesis` and `why_viewer_cares` must not be empty and the format must be commentary). |
| **H. Replay** | `(agent_run_id, output_ordinal)` and live `dedupe_key` UNIQUE → no duplicate ideas. |
| **I. Zero input** | No READY scenes/candidates → `NO_INPUT`. |
| **J. Paid / external** | LLM ideation (paid). No external side effects. |

## CF-004 — Script & Commentary Architect (→ G2)

| | |
|---|---|
| **A. Core question** | What exactly are we saying, and in what format? |
| **B. Inputs** | One `content_candidate_id` with status APPROVED and an effective G1 APPROVE matching its `content_sha256`. Linked scenes (READY). |
| **C. Outputs** | `cf.content_scripts` (DRAFT → REVIEW). ID: `script_id`, `revision_number`. |
| **D. Allowed intelligence** | Hook, thesis, context, narration, evidence points, interpretation, payoff, CTA, caption plan, claims to verify, spoiler handling, visual-evidence requirements, narration-independence self-check (advice). |
| **E. Deterministic** | G1 validation, revision numbering, `content_sha256`, word-count vs target duration bounds, format class inherited from the opportunity unless a revision says otherwise, DRAFT → REVIEW. |
| **F. Human gate** | **G2** blocks CF-005. |
| **G. Forbidden** | Draft for an unapproved idea; approve; choose publication footage; quote dialogue beyond a few words; state legal conclusions. |
| **H. Replay** | Same candidate + same run key → existing script. New revision only on an explicit revision request. |
| **I. Zero input** | Candidate not APPROVED → `G1_NOT_APPROVED`, zero writes, zero provider calls. |
| **J. Paid / external** | LLM scripting (paid). No external side effects. |

## CF-005 — Publication Source & Rights Resolver (→ G3)

| | |
|---|---|
| **A. Core question** | What visual/audio material may support this approved script, and what must be original? |
| **B. Inputs** | One `script_id` APPROVED with effective G2; its scenes' research provenance; the script's visual-evidence requirements. |
| **C. Outputs** | `cf.publication_source_packages` (DRAFT → REVIEW, or → BLOCKED with `NO_ACCEPTABLE_SOURCE` / `HUMAN_REVIEW_REQUIRED`) + `cf.publication_source_items`. IDs: `source_package_id`, `source_item_id`. |
| **D. Allowed intelligence** | Suggest candidate official promos/trailers and original-graphic substitutes, draft provenance and risk *notes*, estimate commentary ratio, suggest source minimisation. |
| **E. Deterministic** | G2 validation; category assignment rules (an item can only be `OFFICIAL_*` if the origin is a verified official channel recorded by a human); every third-party item has an origin reference; span arithmetic; BLOCKED when no item qualifies; `content_sha256`; DRAFT → REVIEW. |
| **F. Human gate** | **G3** blocks CF-006. |
| **G. Forbidden** | Persist or imply FAIR_USE_CONFIRMED / LEGAL_SAFE / COPYRIGHT_SAFE; approve; turn a scene's research access into a source item automatically; download or rip material; use "rule-of-thumb" safety rules (short duration, crop, mirror, speed change, subtitles) as a reason a source is acceptable. |
| **H. Replay** | `(script_id, revision_number)` UNIQUE; same run key → existing package. |
| **I. Zero input** | Script not APPROVED → `G2_NOT_APPROVED`. No acceptable material → package BLOCKED (valid, not an error). |
| **J. Paid / external** | Optional LLM note drafting (paid). Possibly free public metadata lookups (official channel listings). No downloads, no uploads. |

## CF-006 — Edit & Production Planner

| | |
|---|---|
| **A. Core question** | Exactly how should this approved idea become a finished short? |
| **B. Inputs** | `script_id` (G2) + `source_package_id` (G3) for the same script. |
| **C. Outputs** | `cf.production_manifests` (DRAFT → READY/BLOCKED). ID: `production_manifest_id`. |
| **D. Allowed intelligence** | Creative segment plan: evidence placement, emphasis, crops, punch-ins, transitions, SFX/music intent, caption styling. |
| **E. Deterministic** | Both gate validations; every planned third-party segment maps to an item in the approved package and fits its span; timecode arithmetic sums to target runtime ± tolerance; aspect ratio and safe zones; `input_hash`; manifest schema validation; status. |
| **F. Human gate** | None (blueprint). G4 later reviews the result. |
| **G. Forbidden** | Use material not in the approved package; change the approved script text; trigger rendering or paid generation. |
| **H. Replay** | `input_hash` UNIQUE → same inputs + planner version → same manifest. |
| **I. Zero input** | Missing gate → `G2_NOT_APPROVED` / `G3_NOT_APPROVED`. |
| **J. Paid / external** | Optional LLM planning (paid). No external side effects. |

## CF-007 — Production Assembly (→ G4)

| | |
|---|---|
| **A. Core question** | Can we execute the READY manifest faithfully into one clean master? |
| **B. Inputs** | `production_manifest_id` READY whose script (G2) and package (G3) approvals are still effective. |
| **C. Outputs** | `cf.production_jobs`, `cf.content_assets`, `cf.renders` (DRAFT → REVIEW). IDs: `production_job_id`, `asset_id`, `render_id`. |
| **D. Allowed intelligence** | None required for assembly. Optional: TTS voice, generated original graphics (provider models), only where the manifest asks. |
| **E. Deterministic** | Job expansion, idempotency keys, attempt caps, paid-job authorisation check, asset checksum and probe, manifest compliance check (every third-party asset links to an approved source item), master render spec, DRAFT → REVIEW. |
| **F. Human gate** | **G4** blocks CF-008. |
| **G. Forbidden** | Run a paid job without `paid_authorisation_ref` and `PAID_CALLS_ENABLED`; include unapproved material; approve; publish; render 30 videos before the three smoke renders pass G4. |
| **H. Replay** | Job `idempotency_key` UNIQUE; asset `sha256` UNIQUE; render `(manifest, revision)` UNIQUE. A replayed paid job with SUCCEEDED state is never re-run. |
| **I. Zero input** | Manifest not READY or upstream revoked → `UPSTREAM_NOT_READY`. |
| **J. Paid / external** | **Yes**: TTS, image/motion generation, cloud rendering, storage. Highest spend risk. No publishing. |

## CF-008 — Publisher & Distribution

| | |
|---|---|
| **A. Core question** | Publish this G4-approved master to the approved platforms and record every platform ID. |
| **B. Inputs** | `render_id` present in `cf.v_publish_eligibility`; target platform in the G4 decision's `approved_platforms`; `PUBLISH_ENABLED = true`; sprint/item publish authorisation reference. |
| **C. Outputs** | `cf.published_content` (READY → PUBLISHED), `cf.platform_posts` (READY → PUBLISHED/BLOCKED), platform variant assets. IDs: `published_content_id`, `platform_post_id`, external post IDs. |
| **D. Allowed intelligence** | Draft titles, descriptions, hashtags per platform (shown to the G4 reviewer or a packaging reviewer before upload). |
| **E. Deterministic** | Eligibility view check immediately before each upload; `publish_idempotency_key`; one live post per platform; external ID capture; retry state; scheduling only when `SCHEDULES_ENABLED`. |
| **F. Human gate** | Requires G4 (already passed) plus item-level publish authorisation. |
| **G. Forbidden** | Upload without all checks; publish to a platform not in `approved_platforms`; re-upload on ambiguous failure (check the platform first); use any credential not confirmed as the V&A anime channel (the existing `YouTube account` credential's channel is unknown). |
| **H. Replay** | `publish_idempotency_key` UNIQUE → an upload is attempted at most once per key; a replay reads the stored external ID. |
| **I. Zero input** | Nothing eligible → `NO_INPUT`. Flag off → posts stay READY or go BLOCKED with `PUBLISH_DISABLED`; no upload. |
| **J. Paid / external** | **First point where external publication is possible.** Irreversible. Platform APIs are free but public. |

## CF-009 — Analytics & Learning Engine

| | |
|---|---|
| **A. Core question** | What worked, what failed, and what should change next? |
| **B. Inputs** | PUBLISHED `platform_post_id[]`, their lineage (render → manifest → script → opportunity → scene → title → franchise), prior snapshots. |
| **C. Outputs** | `cf.performance_snapshots` (append-only), `cf.content_learning_log` (append-only). IDs: `performance_snapshot_id`, `learning_log_id`. |
| **D. Allowed intelligence** | Interpret results, compare against hypothesis and baseline, propose next tests and backlog effects. |
| **E. Deterministic** | Metric fetch and storage, hour buckets, window calculation, baseline arithmetic, lineage joins, dedupe. |
| **F. Human gate** | None to write learnings; any backlog change happens only by CF-001/CF-003 reading learnings as soft input and still passing G1. |
| **G. Forbidden** | Update or delete history; change old records; move any status; trigger publishing or production. |
| **H. Replay** | Snapshot `(post, window, hour)` UNIQUE; learning `(run, ordinal)` UNIQUE. |
| **I. Zero input** | No published posts → `NO_INPUT`. |
| **J. Paid / external** | Platform analytics reads (free). Optional LLM interpretation (paid). No external writes. |

## CF-000 — Deterministic Orchestrator (LATER ONLY)

Not designed in detail and **not a dependency of any early agent**. Each CF agent above is runnable alone by a manual trigger. CF-000 may later own sequencing, waiting states, retry eligibility, budget guard, kill switch and scheduling — reading the same tables and gates — and must never approve, invent, or bypass. Build only after Sprint 10 and an explicit human go-ahead (Sprint 11).
