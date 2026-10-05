# Human Asset-Requirement Resolution Mechanism — Design v0.1 (PROPOSAL, NOT APPLIED)

**Change:** ENG-20260928-020 (S5.2 Part E)
**Status:** proposal for Company Brain approval. **No migration applied, no workflow changed.**

## Goal
Give humans an immutable, auditable way to resolve each Agent-006 requirement. Agent-006 consumes the decisions deterministically, with no LLM in the control path.

The design is **additive**:
- no existing table or column changes;
- no historical manifest is touched.

The same pattern supplies the persisted paid-generation authorisation that the S6 Agent-007 gate (07A0) currently lacks (§6).

## Live schema facts this design relies on (verified 28 Sep)

| Fact | Consequence |
|---|---|
| `asset_registry.asset_id` is `UNIQUE` | A foreign key to it is possible. |
| `asset_resolution_items.resolution_status` and `production_readiness_manifests.status` / `readiness_state` are plain `text` with **no CHECK constraints** | New outcome values are additive at the DB level. |
| `asset_resolution_items.production_manifest_id` is `text`; `episode_production_manifests.id` is `uuid` | The decision table stores the manifest id as `uuid` with an FK to `episode_production_manifests(id)`. |

---

## 1. Table `asset_requirement_decisions` (append-only)

```sql
-- PROPOSED. Do not apply without approval.
create table public.asset_requirement_decisions (
  id                      uuid primary key default gen_random_uuid(),
  created_at              timestamptz not null default now(),

  production_manifest_id  uuid not null references public.episode_production_manifests(id),
  requirement_key         text not null,           -- exactly as Agent-006 emits it, e.g. 'TBD::AUDIO::AMBIENCE'
  decision                text not null check (decision in
                            ('CREATE_NEW','MAP_EXISTING_CANONICAL','COMPOSITOR_ONLY_NO_ASSET','DEFER')),
  canonical_asset_id      text references public.asset_registry(asset_id),
  compositor_instruction  text,
  notes                   text,

  -- provenance (who / how / on what authority)
  decided_by              text not null,           -- human identity, e.g. 'gilang', 'viva'
  decided_at              timestamptz not null default now(),
  decision_channel        text not null,           -- e.g. 'COMPANY_BRAIN_RECONCILIATION'
  authority_reference     text not null,           -- e.g. change ID / Company Brain decision reference
  recorded_by             text not null,           -- operator/agent that inserted the row

  supersedes_decision_id  uuid unique references public.asset_requirement_decisions(id),

  constraint ard_map_needs_asset check (
    (decision = 'MAP_EXISTING_CANONICAL') = (canonical_asset_id is not null)),
  constraint ard_compositor_needs_instruction check (
    decision <> 'COMPOSITOR_ONLY_NO_ASSET'
    or length(trim(coalesce(compositor_instruction,''))) > 0),
  constraint ard_defer_needs_notes check (
    decision <> 'DEFER' or length(trim(coalesce(notes,''))) > 0)
);
```

### Immutability and single-current rule

These are enforced by triggers. A trigger also binds service-role writes, whereas RLS does not.

- **`BEFORE UPDATE OR DELETE`** raises an exception. Corrections are **new rows** with `supersedes_decision_id` pointing to the row they replace.
- **`BEFORE INSERT`**:
  1. If an un-superseded decision already exists for (`production_manifest_id`, `requirement_key`), the new row **must** supersede exactly that row. Otherwise it is rejected. This guarantees at most one current decision.
  2. `supersedes_decision_id` must reference a row with the same manifest and requirement key.
  3. For `MAP_EXISTING_CANONICAL`, the target registry row must currently be `APPROVED` or `LOCKED` and must not be a dev/mock/test row (same exclusion rule as the governed registry: `metadata_json.development_mock`, `/mock/i` provider, `mock://` path, `TEST_`/`MOCK_` prefix). The check runs at insert time; Agent-006 re-checks at read time (§3).

### Supporting objects

- **View `asset_requirement_decisions_current`:** rows whose `id` is not referenced by any `supersedes_decision_id`.
- **Grants:** `insert, select` for the service role used by humans/operator tooling; `select` only for the Agent-006 read credential. **No update/delete grant** for anyone.
- **Not stored here:** approval of assets themselves. The registry `status` remains the only canon switch; "Agent-007 creates candidates; humans decide canon."

---

## 2. Semantics of each decision

| Decision | Meaning | Agent-006 resolution produced | Blocks readiness? |
|---|---|---|---|
| `CREATE_NEW` | Humans authorise that an asset should exist and be created | `CREATE_NEW`, with a creation brief (joins `asset_creation_queue`) | Yes, until the asset exists and is approved: state `NEEDS_ASSET_CREATION` |
| `MAP_EXISTING_CANONICAL` | Use this exact registry asset | `REUSE_EXISTING`, `canonical_asset_id` = decision value, `resolution_source = HUMAN_DECISION` | No, if the asset is still governed-canonical at run time |
| `COMPOSITOR_ONLY_NO_ASSET` | No durable asset; the compositor instruction satisfies it | **new** `NO_ASSET_REQUIRED`, carrying `compositor_instruction` | No |
| `DEFER` | Not required for this manifest's asset readiness | **new** `DEFERRED`, carrying `notes` | No, but listed in `deferred_requirements[]` |

**Important:** `CREATE_NEW` is **not** a paid-generation authorisation. It only states that the asset should exist. Spending requires the separate authorisation in §6. A general statement such as "continue production" is never an authorisation of either kind.

---

## 3. Agent-006 integration (proposal)

Only nodes that read or map change. No write node changes except that the new values flow into existing text columns.

### New node `03D - Read Human Requirement Decisions (read-only)`
- Supabase `getAll` on `asset_requirement_decisions_current`.
- Filter `production_manifest_id = <exact UUID from node 00>`.
- `alwaysOutputData`, read-only credential.
- It sits alongside the existing registry read.

### Node 05 (build requirements)
Unchanged. Requirement keys stay deterministic.

### Node 07 (resolve)
A pure function applied **before** the existing TBD/NEW logic:

```text
d = current decision for requirement_key (0 or 1 rows; >1 → fail closed)
if no d: existing behaviour (TBD → NEEDS_HUMAN_REVIEW, etc.)

MAP_EXISTING_CANONICAL:
  asset = governed registry row (APPROVED/LOCKED, non-mock) with asset_id == d.canonical_asset_id
  if !asset                         → NEEDS_HUMAN_REVIEW, reason DECISION_TARGET_NOT_GOVERNED
  if type incompatible (see below)  → NEEDS_HUMAN_REVIEW, reason DECISION_TYPE_MISMATCH
  else                              → REUSE_EXISTING (resolution_source HUMAN_DECISION, decision_id)

CREATE_NEW:
  → CREATE_NEW with the existing creation-brief builder
    (+ decision_id; + provider_route_supported flag: PROP/OVERLAY_VFX only)

COMPOSITOR_ONLY_NO_ASSET → NO_ASSET_REQUIRED (+ compositor_instruction, decision_id)
DEFER                    → DEFERRED (+ notes, decision_id)
```

**Type compatibility:** CHARACTER→CHARACTER; ENVIRONMENT→ENVIRONMENT; AUDIO→AUDIO; OVERLAY_VFX→OVERLAY_VFX; PROP→PROP.

### Fail-closed checks
Each of these leaves the run with no writes, or with NEEDS_HUMAN_REVIEW:
- A decision whose `requirement_key` is not in this run's requirement set → **throws** `ORPHAN_DECISION` (no writes). This catches stale keys when Agent-005/006 change key formats.
- More than one current decision per key → throws. It should be impossible given the triggers; the check is defensive.
- An `APPROVED_REUSE` requirement with a contradicting decision (anything other than `MAP_EXISTING_CANONICAL` to the same asset) → throws `DECISION_CONFLICTS_WITH_APPROVED_SCRIPT`.

### Node 10 (readiness)
Deterministic, unchanged precedence plus the new states:
1. any `BLOCKED_*` → `BLOCKED`
2. else any `NEEDS_HUMAN_REVIEW` → `NEEDS_HUMAN_REVIEW`
3. else any `CREATE_NEW` → `NEEDS_ASSET_CREATION`
4. else (all `REUSE_EXISTING` / `NO_ASSET_REQUIRED` / `DEFERRED`) → the existing ready state `READY_FOR_HUMAN_APPROVAL` (vocabulary already in Agent-006; no new readiness state is introduced)

### Readiness manifest
Adds `human_decisions_applied[]` (decision_id, key, decision, decided_by, decided_at) and `deferred_requirements[]`, so every downstream consumer can audit the lineage.

### History
Historical manifests and runs are never rewritten. Decisions are keyed to a **production manifest**, so they apply only to future Agent-006 runs on that exact manifest. `30b6046e` stays as it is.

---

## 4. Worked example (EP005, from the Part D recommendations)

Assume humans accept Part D as written:
- 6 × `CREATE_NEW` (Lumi, Mikko, environment, ambience, cloth foley, completion pop)
- 3 × `COMPOSITOR_ONLY_NO_ASSET` (glint, reflection, visual pop)
- 1 × `DEFER` (touch foley)

A fresh Agent-006 run on `670b201b` would give:
- REUSE 3 · CREATE_NEW 3 + 6 = 9 · NO_ASSET_REQUIRED 3 · DEFERRED 1 · NEEDS_HUMAN_REVIEW 0
- readiness `NEEDS_ASSET_CREATION`

Of the 9 CREATE_NEW items, only the 3 PROP/OVERLAY props are Agent-007-routable. The other 6 would carry `provider_route_supported: false`, and Agent-007 would stop them at `07Z Unsupported`. That is the correct fail-closed behaviour until a separate creation path exists.

---

## 5. Test plan (for when the design is approved; free and no-write first)

Test fixtures in an Agent-006 harness (in-memory decision rows), then a DB migration on a branch or in a transaction with rollback:

| # | Case | Expected |
|---|---|---|
| 1 | Each of the 4 decisions | Produces the mapped status |
| 2 | MAP to a REVIEW / mock / nonexistent asset | NEEDS_HUMAN_REVIEW |
| 3 | Type mismatch | NEEDS_HUMAN_REVIEW |
| 4 | Orphan key | Throws, no writes |
| 5 | Decision contradicting APPROVED_REUSE | Throws |
| 6 | Superseded decision | Only the successor is applied |
| 7 | UPDATE / DELETE attempt | Trigger exception |
| 8 | Second un-superseding insert | Rejected |
| 9 | Readiness precedence | All four outcome combinations |
| 10 | EP005 regression with no decisions | Identical to exec 526 (NEEDS_HUMAN_REVIEW, 3/3/10/0) |

---

## 6. Companion: `paid_generation_authorisations` (for the S6 gate)

The S6 draft gate (07A0) hard-codes `persistedAuthorisation = null`, so paid dispatch is impossible. When humans want spending possible for one exact manifest and requirement, the proposed source of truth is:

```sql
-- PROPOSED. Do not apply without approval.
create table public.paid_generation_authorisations (
  id                                uuid primary key default gen_random_uuid(),
  created_at                        timestamptz not null default now(),
  production_readiness_manifest_id  uuid not null references public.production_readiness_manifests(id),
  asset_resolution_run_id           text not null,
  requirement_key                   text not null,
  source_asset_id                   text not null,
  provider                          text not null check (provider in ('RUNWAY')),
  max_paid_attempts                 int  not null default 1 check (max_paid_attempts = 1),
  cost_ceiling_note                 text not null,
  authorised_by                     text not null,       -- Gilang / Viva only (policy)
  authority_reference               text not null,
  expires_at                        timestamptz not null,
  revokes_authorisation_id          uuid unique references public.paid_generation_authorisations(id),
  is_revocation                     boolean not null default false,
  unique (production_readiness_manifest_id, requirement_key, is_revocation)
);
-- append-only: BEFORE UPDATE/DELETE raise; revocation = a new row with is_revocation = true.
-- Optional additive column: asset_creation_jobs.paid_authorisation_id uuid
--   (lets 07A3 enforce one consumption per authorisation).
```

The 07A0 gate would then read, by exact `production_readiness_manifest_id` + `requirement_key`, one un-revoked and unexpired row whose `asset_resolution_run_id` matches the manifest. The `PAID_DISPATCH_SWITCH` constant stays a second, independent lock, changed only in a separately reviewed version.

Enabling any of this is **out of scope** and requires explicit Gilang/Viva approval.

---

## 7. Rollout order (each step a separate, approved change)

1. Approve this design (or amend it).
2. Migration for `asset_requirement_decisions` (+ view, triggers, grants) on a branch; run the trigger tests.
3. Agent-006 draft: add 03D and the node 07/10 mapping; free harness tests (§5); stays unpublished.
4. Humans record EP005 decisions.
5. One controlled Agent-006 run on `670b201b` (separately authorised).
6. Only then, if ever: the `paid_generation_authorisations` migration and gate wiring (separate approval).
