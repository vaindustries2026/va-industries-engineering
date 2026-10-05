# V&A Industries — C1 Evidence Gap Repair & Authoritative Implementation Spec v1.0

**Status:** COMPANY BRAIN AUTHORITATIVE FOR C1  
**Issued:** 2026-10-05  
**Purpose:** Repair the missing durable evidence for ENG-20260929-021, ENG-20260930-022 and ENG-20260930-023, and remove ambiguity from the exact C1 storage/registry write specification.

> Important provenance note: the three historical entries below are **reconstructed records**, not recovered originals. They are reconstructed from the V&A Company Brain project history and are now explicitly adopted as the authoritative durable record for C1. If an original contemporaneous artifact later appears and materially conflicts with this reconstruction, STOP and escalate before writes.

---

## 1. Reconstructed historical record — ENG-20260929-021

```yaml
change_id: "ENG-20260929-021"
change_type: "FIX"
actor: "Claude engineering"
requested_by: "Gilang / Company Brain"
workflow_name: "AGENT-007 — Asset Creation & Canonicalization Producer v0.1"
workflow_id: "hlwQHO8FEcn4gDXE"
status: "UNPUBLISHED_SAFETY_DRAFT"
summary: >
  S6.1 safety patch preventing Agent-007 candidate writes from downgrading an
  already human-APPROVED or LOCKED canonical asset row back to REVIEW.
result:
  safer_draft_version: "b135f8a5-7800-4169-b2f4-9cf3a7d5904d"
  node_count: 76
  trigger_state: "intentionally disconnected"
  paid_dispatch_switch: "DISABLED"
  persisted_paid_authorisation: null
  canon_protection:
    - "pre-read existing canonical row"
    - "classify existing status before candidate write"
    - "route writes so APPROVED/LOCKED rows are preserved"
    - "candidate insert uses ON CONFLICT DO NOTHING"
  human_governance: "Agent-007 creates candidates; humans decide canon"
paid_calls: 0
generation_calls: 0
publication: false
migrations: 0
notes:
  - "Minor reporting/history defects remain deferred."
  - "Agent-007 remains outside Agent-000 safe boundary until defects are resolved."
```

---

## 2. Reconstructed historical record — ENG-20260930-022

```yaml
change_id: "ENG-20260930-022"
change_type: "C1_PRECHECK_STOP"
actor: "Claude engineering"
requested_by: "Gilang / Company Brain"
scope: "C1 visual canon durable storage + registry registration"
summary: >
  First C1 execution attempt stopped before writes because the then-supplied
  expected SHA-256 values did not match the exact final image bytes available
  to the engineering environment.
result: "STOPPED_HASH_MISMATCH"
writes: 0
paid_calls: 0
generation_calls: 0
supabase_writes: 0
n8n_writes: 0
governance_rule_reconfirmed: >
  Human visual approval -> save exact final file -> hash the saved file ->
  record that hash -> only then register/store canon.
```

---

## 3. Reconstructed historical record — ENG-20260930-023

```yaml
change_id: "ENG-20260930-023"
change_type: "C1_CANON_BYTES_REAPPROVAL"
actor: "Company Brain"
approved_by: "Gilang"
summary: >
  The exact final PNG bytes were explicitly re-approved as the authoritative
  C1 canon bytes. Earlier hashes for similarly named image files were declared
  superseded and invalid for C1.
state_after: "ACTUAL_CANON_BYTES_REAPPROVED + ZERO_WRITES"
drift_recheck: "CLEAN"
writes: 0
paid_calls: 0
generation_calls: 0
authoritative_files:
  CHAR-MIKKO-MASTER-v01:
    repo_path: "canon/c1/mikko_the_bear_character_master_sheet.png"
    sha256: "41c9480a847c962c1ecfda4fe076e0abcd86548ba67f692621cfc6e13d61f1a8"
    bytes: 2207008
    dimensions: "1448x1086"
    mode: "RGB"
  CHAR-LUMI-MASTER-v01:
    repo_path: "canon/c1/lumi_character_master_sheet.png"
    sha256: "8b29c1abea53cb253eea39cdd41d5001ed38036945b049078915ac5993c43a41"
    bytes: 1887897
    dimensions: "1448x1086"
    mode: "RGB"
  DUO-MIKKO-LUMI-SCALE-v01:
    repo_path: "canon/c1/mikko_lumi_duo_scale_sheet.png"
    sha256: "735d64075af999d8a00d35afe2674174f5e0feea9b1b4acb9ec2208f1e1d121f"
    bytes: 1704130
    dimensions: "1448x1086"
    mode: "RGB"
  WORLD-EP005-BATHROOM-MASTER-v01:
    repo_path: "canon/c1/mikko_lumi_child_friendly_bathroom_board.png"
    sha256: "ab79c560d3c79a05cb957331149ee4b8a176e109b06010480ba6c26903bd3733"
    bytes: 1756516
    dimensions: "1448x1086"
    mode: "RGB"
superseded_hashes:
  - "70a88421..."
  - "8bf26e70..."
  - "245d6453..."
  - "3c64daed..."
```

### Filename clarification

The human-facing labels previously used in Company Brain documents, such as **Mikko Master**, **Lumi Master**, **Duo Scale**, and **Bathroom master**, identify the logical canon roles. They do **not** authorize any older local file with a similar display filename.

For C1, the only authoritative bytes are the four exact files under `canon/c1/` listed above and verified by their full SHA-256 values.

---

# 4. Authoritative C1 implementation specification

This section is a **new explicit Company Brain implementation decision** issued on 2026-10-05. It removes the remaining ambiguity identified by the C1 precheck.

## 4.1 Supabase storage

**Bucket:** `production-assets`

The exact **object keys inside the bucket** are:

```text
visual/canonical/characters/CHAR-MIKKO-MASTER-v01.png
visual/canonical/characters/CHAR-LUMI-MASTER-v01.png
visual/canonical/references/DUO-MIKKO-LUMI-SCALE-v01.png
visual/canonical/worlds/WORLD-EP005-BATHROOM-MASTER-v01.png
```

The exact `asset_registry.storage_path` values for the three registered assets are the bucket-qualified paths:

```text
production-assets/visual/canonical/characters/CHAR-MIKKO-MASTER-v01.png
production-assets/visual/canonical/characters/CHAR-LUMI-MASTER-v01.png
production-assets/visual/canonical/worlds/WORLD-EP005-BATHROOM-MASTER-v01.png
```

### Storage safety
- Create only if the exact object key does not already exist.
- **NO OVERWRITE / NO UPSERT** for storage objects.
- If any target key exists, download/read it and compare SHA-256.
  - If hash matches the authoritative hash, treat storage as already satisfied and do not rewrite.
  - If hash differs, STOP before any C1 registry write.
- After any successful new upload, read the object back and recompute SHA-256 before registry registration.

---

## 4.2 Exact `asset_registry` rows

Use the existing `asset_registry` table. Do not migrate or add columns.

For fields not listed below, use the table default or `NULL`. In particular:
- `asset_subtype = NULL`
- `source_url = NULL`
- `version = "v01"`
- `status = "APPROVED"`

### A. Mikko

```json
{
  "asset_id": "CHAR-MIKKO-MASTER-v01",
  "asset_name": "Mikko",
  "asset_type": "CHARACTER",
  "asset_subtype": null,
  "version": "v01",
  "status": "APPROVED",
  "aliases": [
    "Mikko",
    "TBD::CHARACTER::Mikko"
  ],
  "storage_path": "production-assets/visual/canonical/characters/CHAR-MIKKO-MASTER-v01.png",
  "source_url": null,
  "metadata_json": {
    "canon_scope": "MIKKO_LUMI_VISUAL_CANON",
    "canon_role": "CHARACTER_MASTER",
    "human_approval": "APPROVED",
    "approval_authority": "Gilang",
    "approval_record": "ENG-20260930-023",
    "source_repo_commit": "5055f760c5f00e3e0f8eab9ab5288a808b27b0c5",
    "source_repo_path": "canon/c1/mikko_the_bear_character_master_sheet.png",
    "sha256": "41c9480a847c962c1ecfda4fe076e0abcd86548ba67f692621cfc6e13d61f1a8"
  },
  "notes": "C1 human-approved Mikko character master. Exact bytes governed by ENG-20260930-023 and SHA-256."
}
```

### B. Lumi

```json
{
  "asset_id": "CHAR-LUMI-MASTER-v01",
  "asset_name": "Lumi",
  "asset_type": "CHARACTER",
  "asset_subtype": null,
  "version": "v01",
  "status": "APPROVED",
  "aliases": [
    "Lumi",
    "TBD::CHARACTER::Lumi"
  ],
  "storage_path": "production-assets/visual/canonical/characters/CHAR-LUMI-MASTER-v01.png",
  "source_url": null,
  "metadata_json": {
    "canon_scope": "MIKKO_LUMI_VISUAL_CANON",
    "canon_role": "CHARACTER_MASTER",
    "human_approval": "APPROVED",
    "approval_authority": "Gilang",
    "approval_record": "ENG-20260930-023",
    "source_repo_commit": "5055f760c5f00e3e0f8eab9ab5288a808b27b0c5",
    "source_repo_path": "canon/c1/lumi_character_master_sheet.png",
    "sha256": "8b29c1abea53cb253eea39cdd41d5001ed38036945b049078915ac5993c43a41"
  },
  "notes": "C1 human-approved Lumi character master. Exact bytes governed by ENG-20260930-023 and SHA-256."
}
```

### C. EP005 bathroom world

```json
{
  "asset_id": "WORLD-EP005-BATHROOM-MASTER-v01",
  "asset_name": "EP005 Child-Friendly Bathroom Master",
  "asset_type": "ENVIRONMENT",
  "asset_subtype": null,
  "version": "v01",
  "status": "APPROVED",
  "aliases": [
    "Canonical environment/background",
    "TBD::ENVIRONMENT::Canonical environment/background"
  ],
  "storage_path": "production-assets/visual/canonical/worlds/WORLD-EP005-BATHROOM-MASTER-v01.png",
  "source_url": null,
  "metadata_json": {
    "canon_scope": "MIKKO_LUMI_VISUAL_CANON",
    "canon_role": "EPISODE_WORLD_MASTER",
    "episode_code": "EP-CANDIDATE-005",
    "human_approval": "APPROVED",
    "approval_authority": "Gilang",
    "approval_record": "ENG-20260930-023",
    "source_repo_commit": "5055f760c5f00e3e0f8eab9ab5288a808b27b0c5",
    "source_repo_path": "canon/c1/mikko_lumi_child_friendly_bathroom_board.png",
    "sha256": "ab79c560d3c79a05cb957331149ee4b8a176e109b06010480ba6c26903bd3733"
  },
  "notes": "C1 human-approved EP005 bathroom/world master. Exact bytes governed by ENG-20260930-023 and SHA-256."
}
```

### Registry write safety

- Before insert, query independently by:
  - exact `asset_id`
  - exact normalized `asset_name`
  - every intended alias
- If any existing row creates an ambiguous match, STOP.
- If the exact target `asset_id` already exists:
  - if the complete intended identity/status/path/hash provenance is equivalent, treat as already satisfied and do not duplicate;
  - otherwise STOP.
- Do not downgrade, overwrite, or mutate any unrelated existing row.
- The intended operation for an absent row is a plain insert, not an upsert that could mutate an existing canonical row.

---

## 4.3 Duo scale sheet

`DUO-MIKKO-LUMI-SCALE-v01` is a **canonical reference object only for C1**.

- Store it at:
  `production-assets/visual/canonical/references/DUO-MIKKO-LUMI-SCALE-v01.png`
- Do **not** create an `asset_registry` row for it in C1.
- Do not invent a new `asset_type`.
- A future registry mapping requires a separate explicit schema/governance decision.

Expected C1 result label:

`DUO_REFERENCE_STORED_NOT_REGISTRY_MAPPED`

---

# 5. Agent-006 read-only proof target

After the three registry rows exist, prove read-only that the current Agent-006 governed matcher finds exactly one APPROVED/LOCKED row for each production requirement label:

```text
Mikko
Lumi
Canonical environment/background
```

The aliases above additionally preserve compatibility with the corresponding TBD keys:

```text
TBD::CHARACTER::Mikko
TBD::CHARACTER::Lumi
TBD::ENVIRONMENT::Canonical environment/background
```

Do not run Agent-006 production. This is a read-only matching proof against its current draft logic and live registry data.

---

# 6. C1 boundary remains unchanged

Still forbidden during C1:
- Agent-006 production execution
- Agent-007 execution
- Agent-006 or Agent-007 publication
- image generation/transformation
- OpenAI/Gemini/Runway provider calls
- paid calls
- readiness approval
- migrations
- Agent-005 changes
- mirror/cloth/berry changes
- S3-B
- Agent-000 work
- billing/subscription/credit changes

---

# 7. Required final C1 state

```text
C1_VISUAL_CANON_DURABLY_STORED
+ STORED_BYTES_HASH_VERIFIED
+ MIKKO_APPROVED_REGISTERED
+ LUMI_APPROVED_REGISTERED
+ EP005_BATHROOM_APPROVED_REGISTERED
+ DUO_REFERENCE_STORED_NOT_REGISTRY_MAPPED
+ AGENT006_MATCH_READINESS_PROVEN_READ_ONLY
+ EVIDENCE_COMMITTED_TO_GITHUB
+ ZERO_GENERATION
+ ZERO_PAID_CALLS
+ ZERO_AGENT006_PRODUCTION_RUN
+ ZERO_AGENT007_PRODUCTION_RUN
+ ZERO_READINESS_APPROVAL
+ ZERO_MIGRATIONS
```

If any live state materially conflicts with this specification, STOP before the conflicting write and return the evidence to Company Brain.
