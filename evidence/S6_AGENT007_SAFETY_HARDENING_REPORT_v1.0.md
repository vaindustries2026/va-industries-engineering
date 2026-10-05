# S6 — Agent-007 Safety Hardening (FREE ONLY) + Legacy Readiness Inspection — Report v1.0

**Change:** ENG-20260928-020 (S5.2 Parts F and G)
**Workflow:** `hlwQHO8FEcn4gDXE`, "AGENT-007 — Asset Creation & Canonicalization Producer v0.1"
**Result:** `S6_AGENT007_SAFETY_DRAFT_CONFIGURED + FREE_VALIDATION_PASSED + UNPUBLISHED`

| | Version |
|---|---|
| Published (unchanged) | `45c20c99-eeb2-4067-8065-7923746d3afc` (`activeVersionId`) |
| S6 draft | `42ce4565-0d6d-4c4c-b492-bdf5c5777bcf` (72 nodes; export sha256 of nodes+connections `147d33d9…`) |

**Spend / execution counts:**
- OpenAI 0 · Gemini 0 · Runway 0 (no submission, status or download call)
- paid generation 0 · Agent-007 executions 0 (last remains #455, 2026-09-24)
- DB writes 0

---

## 1. Drift check (before editing)

- **Live state:** one version, `45c20c99`, with published = draft. 70 nodes; `updatedAt` 2026-09-25T01:32:33Z.
- **Match:** it matched the inventory and the S5.1 notes, so there was **no material drift** and the edit went ahead.
- **Approach:** v0.1 was patched in place. The v0.2 skeleton was **not** used. The reserve → claim → checkpoint → recovery architecture is unchanged:
  - 07A3 reserve RPC
  - 07A4 verify
  - 07A5 claim RPC
  - 07A6 verify
  - 07B submit (still **disabled**)
  - 07C/07D checkpoint
  - 07D2–07J poll, download and store
  - 08–15 validate, register REVIEW, summarise

## 2. Draft changes (only these)

| Req | Node | Change |
|---|---|---|
| R-012 | **00** | The hard-coded `c0012923…` is removed (the ID survives only in a comment). The caller's `production_readiness_manifest_id` is required: missing → `BLOCKED (MISSING_…)`; non-UUID → `BLOCKED (MALFORMED_…)`. It is lower-cased, and output `is_mock_input:false`. |
| R-012 | **01D** | `manifest_found` is true only if the Supabase row's `id` **equals** the requested UUID. Otherwise `manifest_found:false` with `manifest_id_mismatch`. |
| R-012/013 | **02** | The IF now also requires `manifest_found === true && manifest_source === 'SUPABASE'`. |
| R-013 | **00** | Caller-supplied `status`, `readiness_state`, `readiness_manifest_json` and `paid_generation_authoris(z)ation(ed)` are ignored and listed in `ignored_caller_supplied_fields`. |
| R-013 | **01A/01B removed** | The mock-approval bypass (`01A Is Mock Input?` → `01B Use Mock Readiness Manifest` → 02) is deleted. 00 connects straight to 01C, the live read. |
| R-013 | **TEST - Set Mock AGENT-006 Payload** | Now emits a blank ID, so the manual TEST path fails closed at 00. The other TEST fixture nodes are not connected to any trigger (§5). |
| R-014 | **new 07A0R** | Read-only Supabase `getAll` of `asset_registry` `status=in.(APPROVED,LOCKED)`. |
| R-014 | **new 07A0 gate** | Deterministic code with no API, DB write or LLM. It sets `paid_dispatch_authorised` only if **all** contract checks pass (§3). |
| R-014 | **new 07A0B IF / 07A0C stop** | TRUE → 07A3. FALSE → 07A0C, a terminal `STOPPED / PAID_DISPATCH_NOT_AUTHORISED / database_writes: 0`. |
| R-014 | **edge removed** | `07A1[false] → 07A3` removed. **07A3's only predecessor is now 07A0B[true].** The disabled 07B is no longer the paid switch. |
| R-015 | **05A** | `MAX_PAID_ATTEMPTS_PER_REQUIREMENT = 1`. A new attempt ≥ 2 throws `SAFETY STOP (PAID_ATTEMPT_LIMIT) … Stopped before reservation; no writes.` Historical records up to attempt 3 remain valid evidence (`HISTORICAL_ATTEMPT_CEILING = 3`). The resume path (step 08) is unchanged. |

Everything else is untouched, including 03B's own ≤3 history rule, 06, 07B, the RPCs, and node 10.

## 3. Authorisation contract: where each condition is enforced

| Condition (all required) | Enforced at |
|---|---|
| Exact persisted readiness UUID | 00 (format), 01C (query by id), 01D (id equality), 02, 07A0 (`READINESS_MANIFEST_ID_MISMATCH`) |
| Status APPROVED | 01C filter, 02, 07A0 |
| Readiness NEEDS_ASSET_CREATION | 02, 07A0 |
| Explicit paid authorisation for that exact manifest/run | 07A0: `persistedAuthorisation` (currently `null`, since no source table exists; see the design doc §6) **and** `PAID_DISPATCH_SWITCH === 'ENABLED'` (currently `'DISABLED'`). Caller input is never a source. |
| Requirement still CREATE_NEW | 07A0: must be in the persisted `asset_creation_queue`, and its `all_resolution_records` status must be `CREATE_NEW` |
| No existing canonical asset satisfies it | 07A0 + 07A0R: `CANONICAL_ASSET_ALREADY_EXISTS:<ids>` (normalised id/name/alias match) |
| No active/paid task except a legitimate resume | 03B / 05A (active task → resume; ambiguous → stop); 07A0 rejects any provider-task field on the new-paid path; 05A caps new attempts at 1 |

**No natural-language statement can open the gate.** It reads only constants and persisted rows.

## 4. Free validation

### Harness
- **Workflow:** `OfoGdHzLpg9n2675` (now archived; export in `s6_agent007/`).
- **Byte-identical copies** of 20 draft nodes (all equal to 42ce4565, verified programmatically): 00, 01C, 01D, 02, 02B, 03, 03B, 03C, 04, 05, 05A, 06, 07, 07A, 07A1, 07A2, 07A0R, 07A0, 07A0B, 07A0C.
- **Reads only:** 01C and 07A0R are Supabase getAll; `HARNESS - 03A LIVE READ` is an HTTP GET. The credential is "Supabase account", the same one already used by the production read nodes.
- **In-memory fixtures:** a readiness-row fixture sits between 01C and 01D; a job-history fixture is exposed under the name `03A - Get Existing Asset Creation Jobs`.
- **No write, RPC or provider node exists in the harness.** 07A3 is replaced by a **TRIPWIRE** node that throws if ever reached.

### Results

| Test | Exec | Setup | Result |
|---|---|---|---|
| T-S6-1 | 531 | Missing UUID | ✅ Fails at 00, `MISSING_PRODUCTION_READINESS_MANIFEST_ID` |
| T-S6-2 | 532 | Malformed id `not-a-uuid; drop table x` | ✅ Fails at 00, `MALFORMED_…` |
| T-S6-3 | 533 | Nonexistent UUID | ✅ 01D `manifest_found:false` → 02B `ASSET_CREATION_NOT_AUTHORIZED` |
| T-S6-4 | 534 | `30b6046e` (REVIEW) | ✅ 02B (01C returns no row, because it reads APPROVED only) |
| T-S6-5 | 535 | Fixture APPROVED + NEEDS_HUMAN_REVIEW | ✅ 02B (`received_readiness_state: NEEDS_HUMAN_REVIEW`) |
| T-S6-6 | 536 | Caller fakes APPROVED / NEEDS_ASSET_CREATION / manifest JSON / paid auth for `30b6046e` | ✅ All 4 fields listed in `ignored_caller_supplied_fields`; 02B |
| T-S6-7 | 537 | **Fully valid** fixture (APPROVED + NEEDS_ASSET_CREATION, CREATE_NEW, no history) + caller paid auth | ✅ Gate → 07A0C: `PAID_DISPATCH_SWITCH_DISABLED`, `NO_PERSISTED_PAID_GENERATION_AUTHORISATION`; `database_writes 0`; **tripwire not reached** |
| T-S6-8 | 538 | History: attempt 1 PROVIDER_FAILED (clear error) | ✅ 05A `SAFETY STOP (PAID_ATTEMPT_LIMIT)` for attempt 2, before reservation |
| T-S6-9 | 539 | History: PROVIDER_JOB_SUBMITTED with provider_job_id | ✅ 07A1 → 07A2 → recovery terminal with the same task id `HARNESS-FIXTURE-TASK-0001`, `resumed_provider_task:true`; gate, registry read and tripwire **not run** |
| T-S6-10 | 540 | Requirement identity "WIN sparkle chord" | ✅ Gate adds `CANONICAL_ASSET_ALREADY_EXISTS:SFX-WIN-SPARKLE-CHORD` |
| T-S6-11 | 541 | Live legacy `d124ba28` | ✅ 03B → 0 remaining (berry, cloth, mirror all QC_PASSED) → NO_REMAINING_JOBS; generation path not reached |
| T-S6-12 | 542 | Live legacy `c0012923` | ✅ NO_REMAINING_JOBS (smoke star QC_PASSED) |

### Static checks on draft 42ce4565
- 07B disabled.
- 07A3's only predecessor is 07A0B[true].
- 01A/01B absent.
- `c0012923` appears only in a node-00 comment.
- Node 10 writes `status: REVIEW` only; there is no auto-canonicalisation.
- Workflow `active` = true refers to the **published** 45c20c99; the draft is not published.

### DB proof

Before (11:21:28Z) and after (11:23:53Z) are identical:

| Table | Rows | md5 |
|---|---|---|
| `asset_creation_jobs` | 11 | 8b022236… |
| `asset_creation_batches` | 3 | 1317c854… |
| `asset_registry` | 12 | 779a9cd2… |
| `production_readiness_manifests` | 5 | 55ae0066… |
| `asset_resolution_items` | 40 | a7a0e611… |
| `storage.objects` | 7 | |

**No reservation or claim row was created** by any test.

## 5. Findings (recorded; not changed in S6)

- **F-S6-1: node 10 upsert.** Node 10 registers candidates with `on_conflict=asset_id` and `Prefer: resolution=merge-duplicates`. It always writes `REVIEW`, so it cannot canonicalise. But re-registering a candidate `asset_id` that a human has since APPROVED would **overwrite it back to REVIEW**. Recommendation: `resolution=ignore-duplicates` (or insert-only with a conflict error). This is a separate change.
- **F-S6-2: entry-point trigger unconnected (pre-existing).** "When Executed by Another Workflow" has **no outgoing connection**, both in published 45c20c99 and in the draft. The only way Agent-007 runs today is the manual TEST path, which in the S6 draft fails closed at 00. Consequences:
  - no parent workflow can currently invoke Agent-007;
  - wiring it to 00 is a separate, reviewable change;
  - it was deliberately **not bundled** into S6.
- **F-S6-3: orphan nodes (pre-existing).** These are not connected to any trigger:
  - `07B-MOCK - Generate Asset Candidate` (enabled)
  - several `TEST - …` fixtures, including `TEST - Report Batch Input`, which hard-codes `d124ba28`

  They are unreachable in both versions. They could be removed or moved to a separate test workflow later (a separate change).
- **F-S6-4: resume path is ungated by design.**
  - *What the path does:* 07A1[true] → 07A2 → 07D2 → 07E (Runway **GET task status**) → 07H download → Supabase upload → 09/10 writes.
  - *What it cannot do:* it never submits a new generation.
  - *When it can fire:* only when a persisted `PROVIDER_JOB_SUBMITTED / IN_PROGRESS / WAITING` row exists for the targeted manifest.
  - *Current state:* the only such row is test fixture `d3106cf4…` with manifest id `TEST-MANIFEST-CHECKPOINT-001`. That ID is not a UUID, so node 00 now rejects it and the row is unreachable.
  - *Decision for humans:* whether a resume (a status poll of already-paid work) should also require a persisted authorisation.
- **F-S6-5: 01C diagnostics.** 01C filters `status=APPROVED`, so a REVIEW manifest appears as "not found" (`received_status: null`). It is safe but less informative. An optional later improvement is to read by id only and let 02 decide.
- **X-9 (from S5.1):** unpublished drafts are executable via Execute Workflow on this instance. The S6 draft is therefore live-callable as a sub-workflow **once F-S6-2 is wired**. The gate remains the protection.

## 6. Part G: legacy readiness manifests (read-only)

| | `d124ba28-2dc5-4b86-8608-f363eeb3f8d2` | `c0012923-d22e-4b5e-b497-53d1c0ff3938` |
|---|---|---|
| status / readiness | APPROVED / NEEDS_ASSET_CREATION | APPROVED / NEEDS_ASSET_CREATION |
| Origin | Agent-006 run A006-1789454294235 from historical manifest `c56cabc0` | TEST smoke manifest (1 requirement: TEST_A007_PAID_SMOKE_STAR) |
| Creation queue | 3 (berry smudge, soft cloth, hand mirror) | 1 |
| Existing jobs | Batch A007-1789527180412: berry A01, cloth A01, mirror A02 QC_PASSED; mirror A01 PROVIDER_FAILED | Batch A007-1790282420409: star A01 QC_PASSED |
| Row `md5(t::text)` now | `cc4b76c5…` | `b895894c…` |
| Unchanged? | Yes: the whole `production_readiness_manifests` table md5 `55ae0066…` is identical to the pre-S5.2 baseline (10:58Z) and after S6 (11:23Z) | Same |

### Why the published Agent-007 (45c20c99) accepts them
- 01C and 02 check only `status = APPROVED` and `readiness_state = NEEDS_ASSET_CREATION`.
- Node 00 **hard-codes** `c0012923`, so any manual run targets the smoke manifest.
- The 01A/01B mock branch could supply an approved manifest without any database read.

### After S6 (draft), are they inert unless deliberately targeted?

| Protection | Effect |
|---|---|
| **R-012** | No default target. A run must name the exact UUID, so they can only be reached by deliberate, exact targeting. |
| **R-013** | Nothing can fake them or another approved manifest. |
| **R-014** | Even when targeted, all remaining requirements are already QC_PASSED, so 03B yields **0 jobs** (T-S6-11/12). If a job were remaining, the gate stops before reservation, because no persisted authorisation exists and the switch is DISABLED. |
| **R-015** | The failed mirror A01 cannot trigger an automatic attempt 3. |

**Conclusion:** with R-012/013/014/015 the two manifests are **inert for paid generation** in the S6 draft. They still carry the APPROVED + NEEDS_ASSET_CREATION pair, which is misleading to humans and to any future consumer that does not share these gates.

### Governance proposal (not executed; needs approval)
Do **not** invent SUPERSEDED. Two options within existing semantics:
- **(a) Leave as is**, protected by the S6 gates and exact-UUID discipline. Record them in the Company Brain as `DO_NOT_USE_FOR_NEW_PAID_PRODUCTION`, like `c56cabc0`, `751814b1` and `ff5afc70`.
- **(b) If a status transition is wanted:** a separately approved governance change that moves them to an existing, non-authorising status value (e.g. `REVIEW`), with an audit note. It must not delete them or change their JSON. The readiness vocabulary has no retirement state, so any new state (e.g. `RETIRED`) would first need schema/governance approval.

**Recommendation:** (a) now; revisit (b) together with the §6 paid-authorisation table design.

## 7. Rollback
- **Discard the draft:** restore version `45c20c99` as the draft (`restore_workflow_version`). The published version was never changed, so production behaviour is unaffected by S6.
- The harness `OfoGdHzLpg9n2675` is archived and can be deleted if desired.
- There is no DB rollback, because no DB writes occurred.

## 8. Not done
- No Agent-007 execution
- No publish
- No Runway enablement or call
- No generation
- No approvals
- No historical manifest change
- No SUPERSEDED status
- No Agent-005 change
- No S3-B
- F-S6-1..5 not fixed; each needs its own approval
