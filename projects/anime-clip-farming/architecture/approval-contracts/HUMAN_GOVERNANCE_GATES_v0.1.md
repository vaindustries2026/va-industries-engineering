# Engine 2 — Human Governance Gates v0.1

**Status:** PROPOSED — DESIGN ONLY. No gate, reviewer, surface or table exists yet.
**Mechanism (proposed):** `cf.gate_decisions` (append-only) written only by `cf.record_gate_decision()`; status edges into `APPROVED` / out of `APPROVED` are rejected by trigger unless an effective matching decision exists. See `../data-contracts/migrations-draft/0001_cf_backbone.DESIGN_ONLY.sql` §9–12.

---

## 1. Rules for every gate

| # | Rule |
|---|---|
| GOV-1 | **Recommendation is not approval.** No status, flag, rank, score, confidence or LLM text ever counts as approval. Only an effective row in `cf.gate_decisions` does. |
| GOV-2 | **Exact object.** A decision names one object UUID and the `content_sha256` the reviewer saw. A new revision (new UUID) needs its own decision. |
| GOV-3 | **Attributable.** Every decision has a `reviewer_id` of an active human whose `allowed_gates` includes that gate, a `decided_at`, the `surface` it came from, and an `idempotency_key`. |
| GOV-4 | **Only one write path.** `cf.record_gate_decision()` (SECURITY DEFINER). The n8n agent role (`cf_agent`) has no INSERT on `gate_decisions` and no EXECUTE on the function. Static tests T-ROLE-01/02 prove this in the draft. |
| GOV-5 | **Append-only.** Decisions are never updated or deleted. Corrections are new rows: `REVOKE` supersedes an `APPROVE`. A mistaken `REJECT` is not reopened; the agent creates a new revision. |
| GOV-6 | **Fail closed downstream.** Every consumer validates: (a) object status is `APPROVED`, (b) an effective `APPROVE` decision exists for this gate, object ID and current `content_sha256`, (c) no upstream approval in the chain has been revoked. Any check missing or false → stop with a named error, write nothing. |
| GOV-7 | **No proxy approval.** Approving at one gate never implies another. G2 does not imply G3; G3 does not imply G4; G4 does not imply that publishing is switched on. |
| GOV-8 | **Humans, not services.** Reviewers are named people. A service account, the Company Brain, or a Claude session can prepare a review packet but cannot be a reviewer. |
| GOV-9 | **Replay-safe.** Re-submitting the same decision (same `idempotency_key`) returns the existing `gate_decision_id` and writes nothing (T-RPL-01). |
| GOV-10 | **Stale-safe.** If the object changed after the reviewer opened it (`p_expected_sha256` ≠ current), the decision is refused (`CF_STALE_REVIEW`, T-GATE-03). |

**Reviewer identities are not decided.** Who sits on G1–G4 (Viva, Gilang, others) is a human decision (D-GOV-1). The blueprint lists "Gilang / Viva / V&A Company Brain" as governance; under GOV-8 the Company Brain authorises sprints but does not click gate decisions.

**Surface is not decided.** Options for the human surface (D-GOV-2): (1) Supabase Studio calling the function directly — free, available now, clunky; (2) a Slack interactive approval in a new dedicated CF channel — needs a new Slack app/workflow and must not touch the existing Router; (3) a small internal web page. Recommended start: (1) for Sprints 3–5, revisit before the 30-video batch.

## 2. Gate contracts

### G1 — Content Idea Approval
| Field | Contract |
|---|---|
| Object | `cf.editorial_opportunities.content_candidate_id` |
| Entry state | `REVIEW` (CF-003 moves IDEA → REVIEW deterministically after validation) |
| Decision values | `APPROVE` → `APPROVED`; `REJECT` → `REJECTED`; `REVOKE` (from APPROVED) → `RETIRED` |
| Writer | `cf.record_gate_decision('G1', …)` from the human surface |
| Reviewer sees | hook, angle, format class, duration, hypothesis, primary metric, linked scene summaries + research provenance, model rank (labelled as advice) |
| Notes | optional free text |
| Downstream validator | CF-004 before drafting and again before writing: status APPROVED + effective G1 APPROVE on (id, sha) |
| Fail-closed | missing / rejected / revoked / stale → CF-004 exits `G1_NOT_APPROVED` with zero writes and zero provider calls |

### G2 — Script Approval
| Field | Contract |
|---|---|
| Object | `cf.content_scripts.script_id` |
| Entry state | `REVIEW` |
| Decisions | APPROVE / REJECT / REVOKE as above |
| Reviewer sees | full narration, thesis, evidence points, factual claims to verify, spoiler handling, model's narration-independence self-check (advice), the G1-approved idea it came from |
| Mandatory human check | Narration Independence Test (blueprint §8): would the narration still be interesting with the footage removed? A "no" is a REJECT |
| Downstream validator | CF-005: script APPROVED + effective G2 on (id, sha) + its opportunity still APPROVED |
| Fail-closed | CF-005 exits `G2_NOT_APPROVED`; no package is created |

### G3 — Publication Source / Rights Approval
| Field | Contract |
|---|---|
| Object | `cf.publication_source_packages.source_package_id` |
| Entry state | `REVIEW` (a `BLOCKED` package cannot be approved; T-SRC-04) |
| Decisions | APPROVE / REJECT / REVOKE |
| Reviewer sees | every `publication_source_items` row: category, origin reference, claimed owner, segment span, proposed seconds, provenance notes, risk notes; required original assets; commentary-ratio estimate; source-minimisation notes |
| What the decision means | "A V&A human accepts this exact material for this one script." It is **not** a legal determination, not fair-use confirmation, not monetisation eligibility, and not a licence for the scene in other videos |
| What it never contains | no field named or meaning fair_use, copyright_safe, legal_safe (T-RIGHTS-01) |
| Downstream validator | CF-006: package APPROVED + effective G3 on (id, sha) + package.script_id = the G2-approved script |
| Fail-closed | CF-006 exits `G3_NOT_APPROVED`; a script with no approved package is a valid parked state, not an error |

### G4 — Final Video QC / Publish Approval
| Field | Contract |
|---|---|
| Object | `cf.renders.render_id` |
| Entry state | `REVIEW` |
| Decisions | APPROVE (must list `approved_platforms`) / REJECT / REVOKE |
| Reviewer checks | commentary quality, factual accuracy, source-package compliance, edit, captions, visual/audio problems, spoilers, brand fit, worth publishing (blueprint §10) |
| Status outcome | render `APPROVED` (no separate `APPROVED_FOR_PUBLISH` status — see STATE_MODEL §5) |
| Downstream validator | CF-008 reads `cf.v_publish_eligibility` (G4 hash-bound, manifest READY, package G3-approved, script G2-approved, same chain), checks the target platform is in `approved_platforms`, checks `PUBLISH_ENABLED`, and checks the sprint/item authorisation reference |
| Fail-closed | any check false → platform post `BLOCKED` with a failure code, no upload attempted |

## 3. Supersession and correction

| Situation | Handling |
|---|---|
| Reviewer approved by mistake | `REVOKE` (new row, supersedes the APPROVE). Object → RETIRED. Downstream objects built on it are left in place for history; their own validators now fail because the chain check (GOV-6c) finds a revoked upstream |
| Reviewer rejected by mistake | No reopen. The agent creates a revision (new ID) that re-enters REVIEW |
| Content needs a small fix after approval | New revision, new ID, new review. Revoke the old approval first if the old one must not be used |
| Reviewer leaves | `reviewers.active = false`; their past decisions stay valid history |
| Already-published content later revoked at G4 | REVOKE stops new distribution; taking down live posts is a separate HUMAN_ADMIN action on `platform_posts` (an external action, never automatic) |

## 4. Separation of concepts (must never collapse into one Boolean)

```text
RESEARCH_SOURCE        anime_scene_intelligence.research_source_* + research_access_basis
PUBLICATION_SOURCE     publication_source_packages / publication_source_items
PUBLICATION_APPROVAL   gate_decisions where gate = 'G3' (material) and gate = 'G4' (final video)
PLATFORM MONETISATION  not modelled; a platform decision recorded later from platform data, never inferred
LEGAL DETERMINATION    not modelled; outside the system, by a separately authorised human/legal process
```

A scene can be `EDITORIALLY_STRONG` with `v_scene_publication_status = UNKNOWN` forever. That is a valid, expected state.
