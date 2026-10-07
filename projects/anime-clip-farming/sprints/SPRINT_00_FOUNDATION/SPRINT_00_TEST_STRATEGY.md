# Sprint 0 — Free-First Test Strategy

**Status:** PROPOSED for Sprints 1–11. Nothing in this file authorises a paid call, a live write, or a publication.

## 1. The ladder (every agent, every sprint)

| Step | What | Cost | Writes |
|---|---|---|---|
| 1 Static validation | n8n `validate_workflow`, node config validation, JSON-schema of every model response, SQL loaded into a throwaway local Postgres | free | none |
| 2 Deterministic / unit | Pure code nodes run on fixtures in a `TEST — CF-00x` harness (copies of the live nodes, no provider nodes, no DB writes) | free | none |
| 3 Mock data | Mock provider responses shaped exactly like production (precedent: `TEST - Mock Gemini Result` in the Anime Lab workflow) | free | none |
| 4 No-write regression | Real read-only DB reads + in-memory "would write" nodes; assert the exact rows that would be written | free | none |
| 5 Negative / fail-closed | The mandatory cases in §3 | free | none |
| 6 Replay / idempotency | Run the same input twice; assert identical outputs and zero new rows on the second run | free | test schema only |
| 7 Explicit human approval | Human reviews steps 1–6 evidence and authorises the next step in writing (brief ID) | — | — |
| 8 Smallest paid smoke | One item, one call, retries 0, `paid_authorisation_ref` recorded, cost captured in `agent_runs` | **paid** | minimal |
| 9 Evidence inspection | Inspect stored rows, IDs, cost, provider output before anything else | free | none |
| 10 Controlled scale-up | Tranches (e.g. 5 → 5 → 10 → 10 for the 30-video batch), review between each | paid | yes |

Steps 1–6 must be green before step 8 is even proposed. Step 6 for writing agents uses a disposable test schema (`cf_test_<sprint>`) or the local Postgres, never production tables, until a migration and a live-write test are separately authorised.

## 2. Universal negative cases (all agents)

| ID | Case | Expected |
|---|---|---|
| N-01 | Duplicate input | no new row; duplicate counted; same IDs returned |
| N-02 | Missing input | `NO_INPUT`, zero rows, zero provider calls |
| N-03 | Malformed UUID | `MALFORMED_UUID` before any read |
| N-04 | Wrong-topic contamination | candidate/idea rejected (`TOPIC_CONTAMINATION`) |
| N-05 | Wrong-franchise contamination | rejected (`FRANCHISE_CONTAMINATION`) where a franchise applies |
| N-06 | Missing approval | `G#_NOT_APPROVED`, zero writes, zero provider calls |
| N-07 | Rejected approval | same as N-06 |
| N-07b | Revoked approval upstream | same as N-06 (`UPSTREAM_REVOKED`) |
| N-08 | Ambiguous source identity | object BLOCKED (`AMBIGUOUS_SOURCE_IDENTITY`); never "pick first" |
| N-09 | Replay | identical outputs, zero new rows, zero provider calls |
| N-10 | Stale state | upstream changed between read and write → `STALE_UPSTREAM_STATE`, rollback |
| N-11 | Provider failure (timeout, 4xx, 5xx, malformed body) | run FAILED, no partial rows, no automatic paid retry |
| N-12 | Database failure (connection, constraint) | run FAILED, no partial rows, error captured |
| N-13 | External publication disabled | nothing uploaded; posts BLOCKED with `PUBLISH_DISABLED` |
| N-14 | Paid calls disabled / no authorisation ref | provider node never reached; `PAID_NOT_AUTHORISED` |
| N-15 | Kids-object isolation | static scan: no node references `public.*`, `AGENT-00x`, the Router, or Kids credentials |

## 3. Minimum free tests per agent before any paid call

| Agent | Must pass (beyond N-01…N-15 where applicable) |
|---|---|
| CF-001 | zero-corpus window exit; title resolver: exact external-ID match, two-match ambiguity → BLOCKED, no-match → no candidate; dedupe per ISO week; signal arithmetic on fixtures; evidence completeness; lane vocabulary; scope isolation (no Kids tables read) |
| CF-002 | span validation (start < end, inside episode duration); overlap ≥80 % flagged not merged; multiple scenes from one episode; missing provenance → BLOCKED; `research_access_basis` taken from intake never from the model; output contains no publication/rights field; mock video-model response through parse + validate (reuse 05/06 patterns) |
| CF-003 | G-independence (does not need a gate); wrong-franchise scene mix rejected; duration inside format band; live dedupe; IDEA → REVIEW only after validation; `recommend_for_review=true` does not change status (T-GATE-01 pattern) |
| CF-004 | G1 missing / rejected / revoked / stale-hash → zero writes; revision numbering; word count vs target duration; mock LLM output schema |
| CF-005 | G2 checks; approved script + no acceptable source → package BLOCKED (T-SRC-02 pattern); `OFFICIAL_*` category impossible without a human-verified origin; catalog scan for forbidden legal-determination fields (T-RIGHTS-01); no download step exists in the workflow |
| CF-006 | both gates; third-party segment outside the approved item span → BLOCKED; runtime arithmetic; `input_hash` replay returns the same manifest |
| CF-007 | paid job without authorisation → never reaches provider; attempt cap; asset checksum dedupe; unapproved material in manifest → BLOCKED; mock TTS/render responses; render registers as DRAFT → REVIEW only |
| CF-008 | `v_publish_eligibility` empty → no upload; flag off → no upload; platform not in `approved_platforms` → BLOCKED; idempotency key prevents double upload; mock platform API including ambiguous timeout (must check before retry) |
| CF-009 | hour-bucket dedupe; append-only (UPDATE/DELETE fail); lineage join completeness on fixtures; no status writes anywhere |

## 4. Gate tests (Sprint 3 onward)

GATE-01 recommendation ≠ approval · GATE-02 unauthorised reviewer · GATE-03 stale hash · GATE-04 unknown object · GATE-05 approve persists · GATE-06 revoke supersedes · RPL-01 idempotent resubmission · ROLE-01/02/03 agent role cannot write decisions, call the gate function, or flip kill switches · APP-01/02 decisions append-only.

## 5. Evidence format

Every test run produces: harness workflow ID + version ID, execution IDs, fixture file hashes, PASS/FAIL per test ID, provider-call count, paid-call count, rows written (expected 0 for steps 1–5). Stored under `projects/anime-clip-farming/evidence/SPRINT_xx_*`.

## 6. What Sprint 0 itself tested

The draft DDL was loaded into a **throwaway local PostgreSQL 16.15 instance inside the engineering container** (not Supabase, not any shared system) and exercised by `architecture/data-contracts/migrations-draft/0001_cf_backbone.STATIC_TESTS.sql` with fictional fixtures.

Result: DDL loads with `ON_ERROR_STOP=1` (23 tables, 3 views, 57 triggers), **33/33 static tests PASS**: T-ID-01…07, T-ST-01/02, T-GATE-01…06, T-IMM-01, T-RPL-01, T-APP-01…03, T-SRC-01…05, T-RIGHTS-01, T-PAID-01/02, T-PUB-01/02, T-ROLE-01…03. Full output in `evidence/SPRINT_00_STATIC_TEST_OUTPUT.txt`. The local instance was stopped and deleted after the run.
