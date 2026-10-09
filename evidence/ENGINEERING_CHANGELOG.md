# V&A Industries — ENGINEERING_CHANGELOG

Append-only log of authorised engineering changes (bootstrap §17 schema). Newest entries at the bottom.

---

## ENG-20260925-001: Read-only engineering audit

```yaml
change_id: "ENG-20260925-001"
change_type: "TEST"   # read-only inspection
actor: "Claude"
requested_by: "Gilang"
summary: "Engineering inventory, Agent-000 design, Supabase verification and source reconciliation. No changes."
docs_updated: ["ENGINEERING_INVENTORY_CURRENT.md", "AGENT_000_DESIGN_PROPOSAL_v0.1.md", "11_SUPABASE_Verification_Results_2026-09-25.md", "SOURCE_RECONCILIATION_REPORT_v1.0.md"]
paid_action_triggered: false
```

---

## ENG-20260925-002: S1, Agent-001 schedules disabled

```yaml
change_id: "ENG-20260925-002"
timestamp: "2026-09-25T02:20:48Z"
actor: "Claude"
requested_by: "Gilang"          # Decision A, 25 Sep 2026
workflow_name: "AGENT-001 — YouTube Market Scout v0.1"
workflow_id: "jENr4e8zkSo1pTKn"
change_type: "EDIT"
risk_class: "LOW"
reason: >
  07:45 autonomous collection was failing daily (invalid YouTube OAuth credential and
  null search_term from the schedule trigger). The 08:00 Director Brief was publishing
  stale rankings to #market-intelligence while appearing successful. Agent-000 will own
  scheduling and freshness validation in future.
before_state: >
  Published/active version bb18343a-12a7-4b9a-91fe-d455b384fb0d (draft = published).
  triggerCount = 2 (both schedules live). Manual + Execute Workflow triggers present.
after_state: >
  Published/active version fb66446b-e0ea-49d6-b82c-3b1f52ec83c8 (draft = published).
  triggerCount = 0. Both Schedule Trigger nodes present but disabled.
  "When Executed by Another Workflow" (search_term input) and the manual trigger unchanged
  and still wired to "Scout Search Parameters". Workflow remains active, so it stays callable
  as a sub-workflow by the Router.
nodes_changed:
  - "07:45 — Daily Market Collection → disabled = true"
  - "08:00 — Daily Director Brief → disabled = true"
nodes_not_changed: "All 14 other nodes: parameters, credentials and connections identical (verified by re-reading the published definition)."
database_changes: []
paid_action_triggered: false
external_side_effects: []
test_execution_ids: []
validation:
  static_validation: "PASSED. The server-side update validation reported only 2 pre-existing warnings (orphan node 'Create a row1'; canvas grouping advice). No new warnings."
  n8n_execution_succeeded: "N/A (no execution performed; the research-path test is blocked on OAuth reconnection)"
  semantic_output_validated: false
  database_state_validated: "N/A"
  duplicate_side_effect_check: "N/A"
  published_definition_verified: true   # triggerCount 0, disabled flags present, activeVersionId = versionId
status: "CONFIGURED_NOT_TESTED (schedule disablement takes effect immediately; research path awaits OAuth)"
human_approval_required: true
human_approval_status: "APPROVED (Decision A)"
known_limitations:
  - "The YouTube OAuth credential 'YouTube account' (youTubeOAuth2Api) is still invalid. Manual/sub-workflow research will fail at 'Get many videos' until reconnected by a human."
  - "The Director Brief branch nodes remain in the workflow (unreachable). Not deleted, by design."
docs_updated: ["ENGINEERING_CHANGELOG.md"]
next_action: "Human: reconnect the YouTube OAuth credential (see the S1 handoff). Then Claude runs one safe research-path test on your confirmation."
rollback_notes: >
  Restore workflow version bb18343a-12a7-4b9a-91fe-d455b384fb0d and publish it, or re-enable
  the two Schedule Trigger nodes and publish. Rolling back re-enables the broken daily
  collection and the stale 08:00 brief.
```

---

## ENG-20260925-003: S1, credential restored + safe research-path test (S1 CLOSED)

```yaml
change_id: "ENG-20260925-003"
timestamp: "2026-09-25T02:36:43Z"
actor: "Claude (test); Gilang (credential reconnection)"
requested_by: "Gilang"
workflow_name: "AGENT-001 — YouTube Market Scout v0.1 (published fb66446b), via new test harness"
workflow_id: "jENr4e8zkSo1pTKn; harness nm9MehhBdRLpJ9YE"
change_type: "TEST"
risk_class: "LOW"
human_action: >
  Gilang disconnected and re-signed-in the n8n credential 'YouTube account' (youTubeOAuth2Api,
  Custom OAuth2 client in Google Cloud project 'VA Company Brain'). No credential values were
  viewed or handled by Claude.
root_cause_of_credential_failure: >
  The Google OAuth consent screen is External + publishing status 'Testing', so Google revokes
  refresh tokens after 7 days. A first reconnection attempt (UI still showed 'Account connected')
  failed in test exec #457/#458; a full Disconnect → Sign in succeeded.
test_harness_created: >
  'TEST — S1 Agent-001 Research Path Check' (nm9MehhBdRLpJ9YE), unpublished, in project
  'VA Industries <vaindustries26@gmail.com>'. Manual Trigger → Set search_term → Execute Workflow
  (published Agent-001, identical mapping to the Router's '03 - Run Agent-001') → Code summary.
  Retained for regression reuse; contains no credentials; never publishes.
test_execution_ids: ["457 (fail, credential)", "458 (Agent-001 child, fail)", "459 (PASS)"]
test_input: "search_term = 'kids brushing teeth' (existing topic; no new topic introduced before S2)"
result:
  n8n_execution_succeeded: true
  semantic_output_validated: true      # 25 items returned, 25 unique video_ids, search_term preserved
  database_state_validated: true       # videos: 25 rows upserted for the term with last_seen ≥ run (38 total, +2 new); video_snapshots: +25 rows (300 → 325), 25 distinct videos
  duplicate_side_effect_check: true    # upsert on video_id, no duplicate videos; snapshots append by design
paid_action_triggered: false           # YouTube Data API quota only (~1 search + 25 video gets); no OpenAI/Gemini/Runway
not_run: ["Agent-002", "Slack Router", "Director Brief", "Slack posting"]
status: "LIVE_TEST_PASSED (Agent-001 sub-workflow research path)"
known_limitations:
  - "The credential will expire again ~7 days after reconnection (≈ 2 Oct 2026) while the Google app stays in 'Testing'. Permanent fix pending a human decision: (B) publish the app with a V&A-owned domain, home page and privacy URL, or (C) switch Agent-001's two YouTube nodes to a YouTube Data API key (public data only)."
  - "The full Slack 'research' chain was not tested end-to-end, because it invokes Agent-002 (paid Gemini + known S2 defects). Deferred until after S2."
next_action: "Begin S2 (Agent-002): present the exact node changes for approval before editing."
rollback_notes: "Test only. The harness can be archived at any time. Agent-001 was not modified by this entry."
```

---

## ENG-20260925-004: S2, Agent-002 corpus correctness + DO/SEE synthesis labels

```yaml
change_id: "ENG-20260925-004"
timestamp: "2026-09-25T03:00:27Z"
actor: "Claude"
requested_by: "Gilang"          # S2 approval + Decision C, 25 Sep 2026
workflow_name: "AGENT-002 — Algorithm & Content Intelligence Analyst v0.1"
workflow_id: "Vl3lwR5w0UAoeDhh"
change_type: "FIX"
risk_class: "MEDIUM"
previous_version: "2366276e-afbd-49da-9775-f21ff4bc55b4 (rollback target)"
new_version: "44156330-2407-46ab-922c-0ff97986487c (published; activeVersionId = versionId)"
nodes_added:
  - "00 - Normalize Research Request (Code): trims and requires search_term; single source of the run's topic"
  - "01B - New Candidates Found? (IF v2.3, ={{ $json.video_id }} notEmpty): TRUE → existing loop; FALSE → library"
  - "03B - Corpus Ready? (IF v2.3, corpus_status == READY): TRUE → Message a model; FALSE → 03C"
  - "03C - No Corpus Result (Set): workflow_status NO_CORPUS, search_term, video_count 0, human-readable synthesis_report; no OpenAI, no DB write"
nodes_changed:
  - "Get Agent-001 Top Videos: alwaysOutputData = true (filter unchanged)"
  - "Get Content Genome Library: matchType allFilters; search_term = normalized request; prompt_version = 'agent002-content-genome-v0.1'; returnAll; executeOnce = true; alwaysOutputData = true"
  - "Build Synthesis Dataset: search_term from request (not rows[0]); defensive topic + version re-filter; de-dup by video_id (latest analyzed_at); corpus_status READY/NO_CORPUS; diagnostics rows_received / rows_excluded_filter / duplicate_rows_removed; corpus format unchanged"
  - "Message a model (system prompt only): 'Mikko = TRY…/Lumi = NOTICE…' → 'Mikko = DO — the Hands… \"What can we try?\" / Lumi = SEE — the Eyes… \"What are we missing?\"' + verbatim duo grammar. NOTICE → CHOOSE → TRY → LEARN → SOLVE TOGETHER and ONE → CUE → THREE → WIN retained. User prompt, model and options unchanged."
connections_changed:
  - "Both triggers → 00 → Get Agent-001 Top Videos (was: triggers → Get Agent-001 Top Videos)"
  - "Get Agent-001 Top Videos → 01B (was: → Process Videos One at a Time)"
  - "01B TRUE → Process Videos One at a Time; 01B FALSE → Get Content Genome Library (added)"
  - "Build Synthesis Dataset → 03B → (Message a model | 03C) (was: Build → Message a model)"
nodes_explicitly_unchanged: >
  Analyse Video with Gemini (prompt text incl. its TRY/NOTICE wording, per Decision C), Prepare Video for
  Analysis (prompt_version 'agent002-content-genome-v0.1' NOT incremented), Check Existing Content Genome,
  Is Content Genome Already Saved?, Restore Video Data, Prepare Content Genome Record, Save Content Genome,
  Process Videos One at a Time, Save Content Synthesis, loop-return connections. Verified by re-reading the
  draft after the update (Gemini body still contains its original text; prompt_version value unchanged).
database_changes: []   # no DDL/DML; malformed prompt_version rows retained (3) and excluded by filter only
static_validation: >
  PASSED. Server-side update validation: 0 errors; only warning is canvas-grouping advice (non-functional).
  The draft was re-read and the node graph, filters and settings were verified before publishing.
tests:
  T-S2a:
    harness: "TEST — S2a Agent-002 Zero-Corpus Check (EifvRoEaSk9ER5va, unpublished) → published Agent-002"
    execution_ids: ["461 (harness)", "462 (Agent-002 child, mode integrated)"]
    input: "s2-test-empty-topic"
    node_path: "trigger → 00 → Get Top Videos ({}) → 01B FALSE → Library ({}) → Build (NO_CORPUS) → 03B FALSE → 03C"
    result: "PASS. workflow_status NO_CORPUS; search_term correct; valid synthesis_report returned; Gemini, Message a model and Save Content Synthesis did not execute."
  T-S2-pre-model:
    harness: "TEST — S2 Agent-002 Pre-Model Corpus Check (PeeV82rw0h7D8oHu, unpublished): exact copies of production nodes 00 / Get Agent-001 Top Videos / 01B / Get Content Genome Library / Build Synthesis Dataset (generated from the published definition) + a STOP on the new-candidate branch + assertions. Contains no Gemini or OpenAI node."
    execution_id: "463"
    input: "kids brushing teeth"
    assertions: "ALL PASSED (9/9)"
    evidence:
      new_agent002_candidates: 0          # 01B routed FALSE; STOP node not reached
      gemini_calls: 0
      library_node_runs: 1                # executeOnce: a single run in runData
      library_rows: 15                    # all prompt_version = agent002-content-genome-v0.1, all search_term = kids brushing teeth
      malformed_rows_in_corpus: 0         # rows_excluded_filter 0 (excluded at query level)
      distinct_video_ids: 15
      duplicate_rows_removed: 0
      final_video_count: 15
      corpus_chars: 292547
      openai_calls: 0
    status: "LIVE_PRE_MODEL_VALIDATION_PASSED (corpus construction)"
database_read_validation: >
  Before tests (02:58:52Z): content_syntheses 3, content_genomes 18. After tests (03:00:27Z): content_syntheses 3,
  content_genomes 18, malformed prompt_version rows retained 3. No writes occurred.
paid_action_triggered: false   # 0 Gemini, 0 OpenAI, 0 Runway calls during S2 validation
not_run: ["T-S2b paid synthesis (awaiting explicit approval)", "Agent-003", "Slack Router", "Gemini analysis path"]
known_limitations:
  - "The new-candidate path (loop done → library with N items) was not exercised live, because there are 0 candidates today. executeOnce is statically verified; the first real research run with new videos will prove the ×N fix live."
  - "Videos first analysed under topic A are attributed to A and are not re-analysed for topic B (DB unique key). A future many-to-many video↔term design would address this."
  - "Existing Content Genome analysis_text still uses the Gemini prompt's TRY/NOTICE framing (unchanged by design, Decision C)."
  - "The pre-model test ran production-identical node copies in a harness, not the production workflow itself (no partial-execution support via MCP)."
docs_updated: ["ENGINEERING_CHANGELOG.md"]
next_action: "Human decision: approve T-S2b (one OpenAI synthesis on the 15-video corpus) or defer. S3 not started."
rollback_notes: >
  Restore Agent-002 version 2366276e-afbd-49da-9775-f21ff4bc55b4 and publish (restore_workflow_version + publish).
  No DB changes to reverse. Test harnesses EifvRoEaSk9ER5va and PeeV82rw0h7D8oHu can be archived at any time.
```

---

## ENG-20260925-004a: S2 status (human decision, 25 Sep 2026)

```yaml
change_id: "ENG-20260925-004a"
change_type: "STATUS"
decided_by: "Gilang"
workflow_id: "Vl3lwR5w0UAoeDhh"
status: "CONFIGURED + STATIC_VALIDATION_PASSED + LIVE_PRE_MODEL_VALIDATION_PASSED"
PAID_END_TO_END_SYNTHESIS_VALIDATION: "DEFERRED (to the first appropriate genuine end-to-end research run after pre-orchestration stabilisation)"
T-S2b: "NOT RUN (deferred)"
carried_limitation: "First run with genuinely new Agent-002 candidates = first live validation of 'analysis loop done → Get Content Genome Library (executeOnce)' after N analysed items."
further_agent002_changes_authorised: false
```

## ENG-20260925-005: S3, stable episode identity (DESIGN ONLY)

```yaml
change_id: "ENG-20260925-005"
change_type: "DESIGN"
actor: "Claude"
requested_by: "Gilang"
deliverable: "S3_STABLE_EPISODE_IDENTITY_MIGRATION_PROPOSAL_v1.0.md"
read_only_queries_run: ["episode_scripts audit", "cross-table identity consistency", "identity column types"]
database_changes: []
n8n_changes: []
paid_action_triggered: false
next_action: "Human review of the S3 proposal (Phase A / S3-004 / S4 / S3-005 / S3-003 / Phase B sequence)."
```

---

## ENG-20260925-006: S3-A, Supabase additive identity migration (DB_MIGRATION_PASSED)

```yaml
change_id: "ENG-20260925-006"
timestamp: "2026-09-25T04:34:29Z"
actor: "Claude"
requested_by: "Gilang"         # S3 approval with amendments, 25 Sep 2026
target: "Supabase project VA-Company-Brain (ziluiwrwwbayhcskeere), table public.episode_scripts"
change_type: "EDIT (DDL, additive)"
risk_class: "LOW"
migration_record: "supabase_migrations.schema_migrations: 20260925043429 s3a_episode_scripts_backlog_identity"
execution: >
  Applied via the Supabase migration API as ONE transaction (the migration runner wraps the body; explicit
  BEGIN/COMMIT omitted accordingly). Body = approved Phase A SQL: SET LOCAL lock_timeout '5s',
  statement_timeout '30s'; DO-block preflight (NULL backlog IDs, duplicate (backlog_id, version),
  code/backlog mismatch, legacy-constraint presence); ALTER COLUMN episode_backlog_id SET NOT NULL;
  ADD CONSTRAINT episode_scripts_backlog_id_version_key UNIQUE (episode_backlog_id, script_version_number);
  DO-block postcheck (new present AND legacy still present).
preflight_rerun_before_execution:   # read-only, immediately before the migration
  rows: 4
  null_episode_backlog_id: 0
  duplicate_backlog_id_version: 0
  code_vs_backlog_mismatch: 0
  legacy_constraint_present: true
  new_constraint_present: false
  episode_backlog_id_nullable: "YES"
  rows_md5: "9f51ef6fc1fb15ee0a0d69624a6e1a2a"
post_commit_verification:
  episode_backlog_id_nullable: "NO"                                                  # NOT NULL present
  new_constraint: "episode_scripts_backlog_id_version_key = UNIQUE (episode_backlog_id, script_version_number)"
  legacy_constraint: "episode_scripts_episode_code_script_version_number_key = UNIQUE (episode_code, script_version_number)  # retained"
  row_count: 4                                                                     # unchanged
  rows_md5: "9f51ef6fc1fb15ee0a0d69624a6e1a2a"                                       # byte-identical rows
  relationships: "3cc15b9a→07d622e9 v1, 14471926→07d622e9 v2, 6b14e140→07d622e9 v3, b5567e13→07d622e9 v4 (unchanged)"
status: "DB_MIGRATION_PASSED"
not_done: ["S3-B (legacy constraint drop) NOT authorised: requires Agent-004 AND Agent-005 UUID identity live and validated (Amendment 2)"]
paid_action_triggered: false
rollback_sql: |
  BEGIN;
  SET LOCAL lock_timeout = '5s';
  ALTER TABLE public.episode_scripts DROP CONSTRAINT IF EXISTS episode_scripts_backlog_id_version_key;
  ALTER TABLE public.episode_scripts ALTER COLUMN episode_backlog_id DROP NOT NULL;
  COMMIT;
```

---

## ENG-20260925-007: S3-004, Agent-004 UUID identity (STOPPED_PRE_EDIT: live drift found)

```yaml
change_id: "ENG-20260925-007"
timestamp: "2026-09-25"
actor: "Claude"
requested_by: "Gilang"
target: "AGENT-004 Script Architect (n8n zcWjXBD1PXcRWNoK)"
change_type: "PRE-EDIT CHECK ONLY (no edit)"
pre_edit_record:
  published_active_version: "fd4a7946-4eaa-45bf-896e-897760b76110"   # rollback target (2026-09-08)
  current_draft_version: "72424e5d-5faf-48ac-917d-739b670edd0f"      # autosaved 2026-09-09T03:39:23Z, never published
  draft_vs_audit_copy: "identical (no drift since the audit/proposal)"
drift_found:
  description: "The draft is NOT equal to the published version. There are unpublished model changes."
  diff_published_to_draft:
    "05 - Generate Script Architecture": "modelId gpt-6-astra (published) -> gpt-5.6-luna (draft)"
    "07 - Generate Production Script":   "modelId gpt-6-astra (published) -> gpt-5.6-luna (draft)"
  other_differences: "none (no node, connection or prompt changes)"
  data_timeline: >
    Scripts v1 (06:26) and v2 APPROVED (06:40) were created 2026-09-08. Scripts v3/v4 (REVIEW) were created
    2026-09-09 03:40/03:41, one minute after the draft model switch, so they were most likely manual runs of
    the luna draft. Sub-workflow/production calls run the published (astra) version.
  inventory_correction: "The ENGINEERING_INVENTORY model entry for Agent-004 (gpt-5.6-luna) described the DRAFT; the live published model is gpt-6-astra."
why_stopped: >
  Editing the draft and publishing would silently promote the model change to production, which violates
  'do not alter models'. Restoring the published version as the edit base would discard someone's unpublished
  work. Which model is intended is a human decision (standing rule: live evidence contradicts → stop the stage and ask).
n8n_changes: []
database_changes: []
tests_run: []
openai_calls: 0
paid_action_triggered: false
status: "STOPPED_PRE_EDIT — awaiting model-baseline decision"
next_action: "Human decides the Agent-004 model baseline (see the S3-004 stop report), then S3-004 resumes from the chosen base."
```

---

## ENG-20260925-008: S3-004, Agent-004 UUID identity on the gpt-6-astra production baseline

```yaml
change_id: "ENG-20260925-008"
timestamp: "2026-09-25T05:00Z"
actor: "Claude"
requested_by: "Gilang"            # model-baseline decision + S3-004 authorisation, 25 Sep 2026
target: "AGENT-004 Script Architect (n8n zcWjXBD1PXcRWNoK)"
change_type: "EDIT (identity plumbing only)"
risk_class: "MEDIUM"
decision_applied: "Published version fd4a7946 is the authoritative production baseline (gpt-6-astra in 05 and 07). The unpublished gpt-5.6-luna draft is NOT promoted."

luna_draft_preservation:
  source: "Agent-004 draft version 72424e5d-5faf-48ac-917d-739b670edd0f (autosaved 2026-09-09T03:39:23Z)"
  archive_workflow:
    id: "AeIgRsDQYVHw0YTu"
    name: "ARCHIVE — AGENT-004 Luna Draft — 2026-09-09"
    version: "67813297-e63c-4e80-97f7-21266657eeae"
    active: false                    # never published; activeVersionId = null
    callerPolicy: "none"             # the Execute Workflow node cannot call it
    contents: "all 15 nodes + connections of the draft; 05 and 07 = gpt-5.6-luna (re-read verified). Node IDs regenerated by n8n; parameters copied from the draft JSON."
  native_copy: "Version 72424e5d is still in Agent-004's n8n version history (not callable)."
  exact_json_export: "ARCHIVE_AGENT004_luna_draft_72424e5d.json (byte copy of the API payload; no secrets; credential references only)"
  deleted: false

baseline_reset:
  method: "restore_workflow_version(fd4a7946) → new draft 27042f57-c76b-4fdc-8e55-a6d20c027425"
  verification: "versions diff fd4a7946 → 27042f57: 0 nodes added/removed/modified, 0 connection changes (models, prompts and graph identical to production)"

rollback_target: "fd4a7946-4eaa-45bf-896e-897760b76110"   # original production version
new_published_version: "a1ff6060-0f3d-4849-b714-29b0856e0c80"  # published = draft (sameAsDraft)
intermediate_version: "f77e5ed2-bd68-4007-82d9-93975e850dd3"   # first edit batch (never published)

identity_changes:   # full diff fd4a7946 → a1ff6060
  - "Trigger: adds input episode_backlog_id (episode_code kept)"
  - "00 Normalize: episode_code and episode_backlog_id trimmed to strings (other fields unchanged)"
  - "NEW 00A Resolve Lookup Mode (Code): valid UUID → BY_ID; malformed → throws INVALID_EPISODE_BACKLOG_ID; code only → BY_CODE_COMPAT; neither → throws MISSING_EPISODE_IDENTITY"
  - "NEW 00B Lookup By ID? (IF)"
  - "NEW 01A Get Approved Episode By ID (id eq + status APPROVED, limit 1, alwaysOutputData)"
  - "01 Get Approved Episode (compat path): limit 1 → 2 so ambiguity can be detected"
  - "NEW 01C Resolve Approved Episode (Code): 0 rows → NOT_APPROVED; >1 → AMBIGUOUS_EPISODE_CODE; BY_ID + non-empty code ≠ row code → INPUT_IDENTITY_MISMATCH; else RESOLVED"
  - "02 condition: episode_code notEmpty → resolution_status equals RESOLVED"
  - "02B: workflow_status = resolution_status; adds episode_backlog_id, match_count; report = resolution_message"
  - "03 Latest Script Version: filter episode_code → episode_backlog_id (resolved)"
  - "04 Prepare Context: episode source = 01C.resolved_episode (one-line change; code/batch/search_term come from the DB row)"
  - "10 Director Brief: output adds episode_backlog_id and episode_script_id (= saved row id), plus two report lines"
unchanged_verified: "05/07 prompts, json_schema, options, credentials; 06, 08 validators; 09 save mapping; both OpenAI models"

model_verification:
  before: {"05": "gpt-6-astra", "07": "gpt-6-astra"}   # published fd4a7946
  after:  {"05": "gpt-6-astra", "07": "gpt-6-astra"}   # draft re-read before publish AND published a1ff6060 re-read after publish
  luna_present_in_agent004: false

static_validation: "update_workflow schema validation passed (only the canvas-grouping warning, as before); version diff reviewed node by node; published definition re-read = draft"

tests:   # harness k4ZPhHyLDEklBWPM "TEST — S3-004 Agent-004 Identity (free, pre-OpenAI)": copies of live nodes 00–04, no OpenAI node, no write node
  T-S3-1: {exec: 464, input: "IDEA UUID 932f971f…", result: "NOT_APPROVED at 02B", pass: true}
  T-S3-2: {exec: 465, input: "not-a-uuid-123", result: "error at 00A INVALID_EPISODE_BACKLOG_ID; no downstream nodes ran", pass: true}
  T-S3-3: {exec: 466, input: "07d622e9-a152-4107-b300-f052546405e3", result: "BY_ID RESOLVED; code EP-CANDIDATE-005, batch A003-1788411280266, term 'kids brushing teeth' from DB; latest v4 (same backlog id); next = 5 / v05; stopped before OpenAI", pass: true}
  T-S3-4: {exec: 469, input: "EP-FIXTURE-AMB with a 2-row fixture replacing node 01 (test-only)", result: "AMBIGUOUS_EPISODE_CODE, match_count 2", pass: true}
  T-S3-5: {exec: 467, input: "07d622e9… + EP-CANDIDATE-002", result: "INPUT_IDENTITY_MISMATCH at 02B", pass: true}
  T-S3-6: {exec: 468, input: "code EP-CANDIDATE-005 only", result: "BY_CODE_COMPAT RESOLVED → 07d622e9…; next = 5 / v05", pass: true}
  note: "Ambiguity is a real risk: episode_backlog is only UNIQUE (batch_run_id, episode_code)."

persistence_check:
  episode_scripts_rows: 4                       # unchanged
  rows_md5: "9f51ef6fc1fb15ee0a0d69624a6e1a2a"  # identical to before S3-A
  max_script_version: 4                         # no v05 created
  backlog_statuses: "07d622e9 APPROVED, 932f971f IDEA (unchanged)"
openai_calls: 0
paid_action_triggered: false
agent004_executions_during_s3004: 0            # only the harness ran

blast_radius: "Router → Agent-004 calls pass episode_code only → compat path, same behaviour for the single approved row. It now fails closed on ambiguity. Output gains episode_backlog_id / episode_script_id. Error-path workflow_status can now be NOT_APPROVED | AMBIGUOUS_EPISODE_CODE | INPUT_IDENTITY_MISMATCH."
correction_to_ENG-20260925-007: "The history shows fd4a7946 was saved at 2026-09-08T06:45:33Z, AFTER script v2 (06:40:55). So which model produced v1/v2 is UNVERIFIED (not 'most likely astra')."
status: "CONFIGURED + STATIC_VALIDATION_PASSED + FREE_IDENTITY_VALIDATION_PASSED"
not_done: ["S4", "Agent-005 identity (S3-005)", "S3-B", "Agent-003 UUID output (S3-003)", "any paid run"]
rollback: "publish_workflow(zcWjXBD1PXcRWNoK, versionId=fd4a7946-4eaa-45bf-896e-897760b76110). No DB changes to undo."
```

---

## ENG-20260925-009: S4, Agent-005 confirmed-defect repair (unpublished) + EP005 successor review

```yaml
change_id: "ENG-20260925-009"
timestamp: "2026-09-25T05:25Z"
actor: "Claude"
requested_by: "Gilang"
target: "AGENT-005 Storyboard & Shot Production Planner v0.1 (n8n oHXIgg7khm0FgLvB)"
change_type: "EDIT (3 defect fixes only)"
risk_class: "LOW (workflow remains unpublished)"

pre_edit_drift_check:
  previous_draft_version: "ea1451b2-21d0-419f-bd3d-1fbf76c860e8"   # rollback target; only history entry (2026-09-11)
  activeVersionId: null                                             # never published
  vs_audit_copy: "identical: no node, connection, prompt or model drift"
  model_note: "07 uses gpt-5.6-luna, unchanged, same as at audit (Agent-005 model not in scope)"
new_draft_version: "ec8e831e-c591-4dae-ba8d-733c81d95087"
published: false        # activeVersionId still null after the edit (re-read verified)

fixes:   # version diff ea1451b2 → ec8e831e shows exactly these changes, nothing else
  S4-A_gate: "02 - Approved Script Found?: leftValue '{{ $json.id }}' (no '=' prefix → literal string, always non-empty → always TRUE) → '={{ $json.id ?? \"\" }}' notEmpty AND NEW condition '={{ $json.status ?? \"\" }}' equals 'APPROVED'. FALSE → existing 02B BLOCKED path."
  S4-B_mapping: "13 - Save Episode Production Manifest: tbd_asset_reference_count ← {{ $json.tbd_asset_reference_count }} (was {{ $json.unique_reused_asset_count }})"
  S4-C_mapping: "13 - Save Episode Production Manifest: low_complexity_shot_count ← {{ $json.low_complexity_shot_count }} (was {{ $json.compositor_shot_count }})"
not_changed: "model, prompts, methodology, script interpretation, shot loop, asset/audio logic, 03A cleanup, retired 09A–09D branch (its pre-existing 09C missing-'=' warning left as is), identity inputs, schema, historical rows"
static_validation: "update_workflow validation: only pre-existing warnings (09C, disconnected 09A/09B, canvas grouping); version diff reviewed"

tests:
  T-S4-1: {harness: "5gE7wq8ItL8QggdL (TEST — S4-A Agent-005 Approval Gate)", exec: 470, input: "EP-CANDIDATE-005 v02", result: "01 returned 14471926 (APPROVED); new gate → TRUE; harness stops before 03/03A/OpenAI", pass: true}
  T-S4-2: {harness: "5gE7wq8ItL8QggdL", exec: 471, input: "EP-CANDIDATE-005 v04 (REVIEW)", result: "01 returned an empty item; new gate → FALSE → 02B BLOCKED. The copy of the OLD gate routed TRUE on the same empty item (defect reproduced).", pass: true}
  T-S4-3_T-S4-4: {harness: "roiROf6Qa21iDR8x (TEST — S4-B/C Manifest Mapping)", exec: 472, method: "read all 6 stored manifests → rebuild node-12 scalars from manifest_json the same way node 12 derives them → Set node carrying the exact live node-13 field expressions → assert", result: "6/6 fixtures: mapped.tbd == len(unresolved_tbd_references) (e.g. 751814b1: 90, not unique_reused 5); mapped.low == complexity_summary.LOW (e.g. 751814b1: 1, not compositor 27)", pass: true}
openai_calls: 0
paid_calls: 0
supabase_writes_during_tests: 0     # manifests 6 rows md5 70ecd429…, shot_production_plans 232 rows md5 c56e909f…, episode_scripts 4 rows md5 9f51ef6f…, identical before and after
historical_rows: "not rewritten: the 6 manifests keep their incorrect historical scalar values (tbd = unique_reused, low = compositor)"

status: "S4_DEFECT_FIXES_CONFIGURED + STATIC_VALIDATION_PASSED + FREE_VALIDATION_PASSED"
publication: "withheld: Agent-005 stays unpublished until S3-005 adds the episode_script_id identity path"
rollback: "restore_workflow_version(oHXIgg7khm0FgLvB, ea1451b2-21d0-419f-bd3d-1fbf76c860e8). Nothing published, no DB changes."

ep005_successor_review:
  deliverable: "EP005_MANIFEST_SUCCESSOR_REVIEW.md"
  verdict: "NOT_SAFE_TO_APPROVE_AS_SUCCESSOR"
  summary: "751814b1 matches the script on shot IDs, order, sections, timing, dialogue, prompts, pauses and DO/SEE roles, and fixes c56cabc0's audio workload (pause holds 29→4) and TBD dedup (5 dependencies). But: S014 still instructs the 'exact three-smudge state' (would restore the cheek); the glint is carried into the S013 response pause (new regression); macro framing leaks into beats 1–2 and S022 (primary test variable diluted; also in c56cabc0); music falsely flagged on S005/S025/S028/S029; WIN chord at S025 not S027; 2 invented REUSE character IDs; +3 paid video-generation shots vs c56cabc0. c56cabc0 (currently APPROVED) has most of the same defects, some worse."
  statuses_changed: false
  new_findings:
    N-2: "Agent-005 node 12 music detector counts 'None. …' phrases as music (false positives)"
    N-3: "Agent-005 TBD tracking covers visual assets only; audio TBDs (soft pop, ambience, cloth/pat SFX) are not tracked"
    N-4: "Agent-005 shot plans apply macro framing outside the beat-3 correction point and invent REUSE character IDs (prompt/validator matter)"
next_action: "Human decision on the EP005 manifest path and N-2/N-3/N-4. Next stage per plan: S3-005 (not started)."
```

---

## ENG-20260925-010: S3-005, Agent-005 UUID script identity (unpublished) + S4B design

```yaml
change_id: "ENG-20260925-010"
timestamp: "2026-09-25T06:37Z"
actor: "Claude"
requested_by: "Gilang"
target: "AGENT-005 Storyboard & Shot Production Planner v0.1 (n8n oHXIgg7khm0FgLvB)"
change_type: "EDIT (identity plumbing only)"
recorded_decisions_this_stage:
  S4_status: "S4_DEFECT_FIXES_CONFIGURED + STATIC_VALIDATION_PASSED + FREE_VALIDATION_PASSED (accepted by Gilang)"
  ep005_review: "751814b1 = NOT_SAFE_TO_APPROVE_AS_SUCCESSOR (accepted). c56cabc0 and 751814b1 = DO_NOT_USE_FOR_NEW_PAID_PRODUCTION. Statuses unchanged (c56cabc0 APPROVED, 751814b1 REVIEW). No Agent-006/007 for EP005."
pre_edit_check:
  previous_draft_version: "ec8e831e-c591-4dae-ba8d-733c81d95087"   # S4 draft; identical to the S4 re-read (no drift)
  activeVersionId: null
  history_note: "n8n history now lists only ec8e831e (and f83f00d1). The pre-S4 version ea1451b2 is no longer in the n8n version history (retention). Exact JSON of ea1451b2 and ec8e831e exported as RECOVERY_AGENT005_ea1451b2_pre_S4.json / RECOVERY_AGENT005_ec8e831e_S4.json."
new_draft_version: "f83f00d1-b886-4379-b5b6-8cd79c6cc0fc"
published: false          # activeVersionId null (re-read verified after edit)

identity_changes:   # version diff ec8e831e → f83f00d1: exactly these
  - "Trigger: adds input episode_script_id (episode_code, script_version kept)"
  - "00 Normalize: episode_script_id authoritative; malformed → throws INVALID_EPISODE_SCRIPT_ID (no lookup runs); absent → requires episode_code AND script_version else throws MISSING_SCRIPT_IDENTITY; outputs lookup_mode BY_ID | BY_LABEL_COMPAT; run/agent/prompt version fields unchanged"
  - "NEW 00B Lookup By Script ID? (IF)"
  - "NEW 01A Get Approved Script By ID (episode_scripts id eq + status APPROVED, limit 1, alwaysOutputData)"
  - "01 Get Approved Script (compat): limit 1 → 2 (ambiguity detection); filters unchanged"
  - "NEW 01C Resolve Approved Script: 0 rows → NOT_APPROVED; >1 → AMBIGUOUS_SCRIPT_LABEL; BY_ID with supplied episode_code/script_version ≠ row → INPUT_IDENTITY_MISMATCH; else emits the resolved DB row (source of truth) + resolution metadata"
  - "02B: reports resolution_status/workflow_status, lookup_mode, episode_script_id, match_count, reason; status stays BLOCKED"
  - "14 Director Brief: output adds episode_backlog_id; brief shows episode_script_id and production_manifest_id (production_plan_run_id, production_manifest_id, episode_script_id already present)"
preserved_verified: "02 gate (S4-A), 13 mappings (S4-B/C), 03, 03A, 07 (model + prompt), 12: byte-identical to ec8e831e"

tests:   # harness rjWJkzqtSvNtonv4 "TEST — S3-005 Agent-005 Identity": copies of live 00, 00B, 01A, 01, 01C, 02, 02B, 03; stops before 03A (delete) and any OpenAI node
  T-S3-005-1: {exec: 473, input: "14471926-…", result: "BY_ID RESOLVED; id 14471926, backlog 07d622e9-a152-4107-b300-f052546405e3, EP-CANDIDATE-005 v02, APPROVED, 29 shots", pass: true}
  T-S3-005-2: {exec: 474, input: "b5567e13-… (v04 REVIEW)", result: "NOT_APPROVED → BLOCKED", pass: true}
  T-S3-005-3: {exec: 475, input: "14471926-not-a-uuid", result: "error at 00: INVALID_EPISODE_SCRIPT_ID; no lookup node ran", pass: true}
  T-S3-005-4: {exec: 476, input: "14471926 + EP-CANDIDATE-002", result: "INPUT_IDENTITY_MISMATCH (episode_code)", pass: true}
  T-S3-005-5: {exec: 477, input: "14471926 + EP-CANDIDATE-005 + v04", result: "INPUT_IDENTITY_MISMATCH (script_version)", pass: true}
  T-S3-005-6: {exec: 478, input: "EP-CANDIDATE-005 + v02", result: "BY_LABEL_COMPAT RESOLVED → 14471926, match_count 1", pass: true}
  T-S3-005-7: {exec: 479, input: "EP-FIXTURE-AMB v01 with test-only 2-row fixture replacing node 01", result: "AMBIGUOUS_SCRIPT_LABEL, match_count 2", pass: true}
paid_calls: {openai: 0, gemini: 0, runway: 0}
supabase_writes: 0    # manifests 6 md5 70ecd429…, shot_production_plans 232 md5 c56e909f…, episode_scripts 4 md5 9f51ef6f…, identical before/after; manifest statuses unchanged
status: "S3-005_CONFIGURED + STATIC_VALIDATION_PASSED + FREE_IDENTITY_VALIDATION_PASSED + UNPUBLISHED"
rollback: "restore_workflow_version(oHXIgg7khm0FgLvB, ec8e831e-c591-4dae-ba8d-733c81d95087) (returns to S4-only draft). Pre-S4 state: re-import RECOVERY_AGENT005_ea1451b2_pre_S4.json. Nothing published; no DB changes."

s4b_design:
  deliverable: "S4B_AGENT005_PRODUCTION_SAFETY_REMEDIATION_DESIGN_v1.0.md (design only, not implemented)"
  evidence: "s4b_validator.js prototype + run_fixtures.js/fixture_output.txt + negative_control.js/negative_control_output.txt (local, free)"
  results: "N-2 classifier → music_required_shots = [S027] on v02; N-3 extraction → AMBIENCE, FOLEY_CLOTH, COMPLETION_SFX (S025), FOLEY_TOUCH (S028), all TBD; N-4 rules R2–R8 flag every listed EP005 defect on both stored manifests; negative control = 0 violations"
  decisions_requested: ["D-S4B-1 schema fields + prompt_version bump", "D-S4B-2 retry policy", "D-S4B-3 video-generation cap", "D-S4B-4 FAILED_VALIDATION status", "D-S4B-5 confirm Agent-005 model", "D-S4B-6 optional Agent-004 structured state"]
blocked: ["S3-B (Agent-005 not yet production-safe)", "Agent-005 publication", "Agent-006/007 for EP005"]
```

---

## ENG-20260925-011: S4B, Agent-005 production-safety remediation (unpublished)

```yaml
change_id: "ENG-20260925-011"
timestamp: "2026-09-25T07:27Z"
actor: "Claude"
requested_by: "Gilang"
target: "AGENT-005 Storyboard & Shot Production Planner v0.1 (n8n oHXIgg7khm0FgLvB)"
change_type: "EDIT (fidelity validation, prompt constraints, schema, readiness/cost gate)"
approved_decisions:
  D-S4B-1: "APPROVED: schema fields camera_setup.framing_scale, audio_plan.music_present, audio_plan.named_audio_assets, overlay_vfx_requirements[].overlay_role, animation_plan.video_justification, continuity_state.tracked_elements[]; prompt_version v0.1 → v0.2"
  D-S4B-2: "Retry policy NONE: any R1–R8 violation fails closed; run stops; no automatic retry"
  D-S4B-3: "Cost baseline = latest human-APPROVED manifest for the same script (else same episode). Proposed video count > baseline → NEEDS_COST_REVIEW. No baseline → human cost approval required. ≤ baseline is NOT a cost approval. EP005 baseline c56cabc0 = 15 video shots (financial threshold only, not creative truth)."
  D-S4B-4: "No FAILED_VALIDATION status and no schema change. On failure: shot rows already saved keep their production_plan_run_id; no manifest is written; the failed execution surfaces the rules."
  D-S4B-5: "Model stays gpt-5.6-luna"
  D-S4B-6: "Agent-004 not modified. Future hardening item: structured continuity state emitted by Agent-004 (source-side tracked elements), so 03C need not infer state from prose."
corrected_R2_rule: >
  REUSE is valid only when the ID is in Agent-004 unique_reused_asset_ids OR in the governed reusable registry.
  An ID that is only in Agent-004 unique_new_asset_ids must stay NEW_REQUIRED (REUSE → R2_INVENTED_REUSE).
  Characters and environment with no governed ID → TBD (R2_CHARACTER_IDENTITY otherwise). Literal names (Mikko, Lumi, the character_name) are never valid asset IDs.
  Registry: none exists and no schema change is authorised, so 03C uses GOVERNED_REUSABLE_REGISTRY = [] (REUSE effectively = Agent-004 reused IDs only).
  Extension to report: R2_UNAPPROVED_NEW_ASSET fires when NEW_REQUIRED is used for an ID Agent-004 did not approve as new (the plan must use TBD). Strictly within the design intent ("do not invent IDs"), but flagged here for explicit acceptance.
N3_amendment: "audio TBD dependencies carry reference_count (actual matched references) and shot_count (distinct shots), plus shots[], source_phrases[], canonical_id TBD, governance_status UNRESOLVED"

baseline_version: "f83f00d1-b886-4379-b5b6-8cd79c6cc0fc"   # re-read before editing: identical to the S3-005 export (no drift)
new_draft_version: "aedd1743-56c9-4660-b3c3-f48dd8336903"
intermediate_versions: [c903f870 (00+07), 2ac032a0 (03C), 369b60a1 (06), 10bd2656 (08), 60f614f7 (11A/11B), 41fd5ef9 (12)]
published: false        # active false, activeVersionId null (re-read after final edit)
model: "gpt-5.6-luna (07 model and options unchanged; only the json_schema changed)"
prompt_version: "agent005-shot-planning-v0.1 → agent005-shot-planning-v0.2"

library: "S4B-LIB v1 (classifyMusicCue, extractAudioTbds, buildProfile, validateShot R1–R7, validateSequence R8 structured + prose fallback), sha256 04179ff04c478bd97d725547c2160bbb2c349f63c949e05928325e49afe79468, embedded verbatim in 03C, 08, 11A, 12 and the test runner"
nodes_added:
  03C - Build Source Fidelity Profile: "Code. Deterministic per-shot profile from the APPROVED script only (music state, pause hold, framing ceiling, static eligibility, placed approved audio assets, restore flag, audio TBDs). Throws SOURCE_MUSIC_CUE_UNCERTAIN before any paid call. Wired 03B → 03C → 04."
  11A - Sequence Fidelity Validation: "Code. R8 over all shot plans: structured continuity_state is mandatory (R8_STRUCTURED_STATE_MISSING); removed state never returns (R8_STATE_REINTRODUCED); adjacent end→start must chain (R8_CONTINUITY_BREAK); prose count fallback always on. Throws → no manifest. Outputs fidelity_status PASSED."
  11B - Get Approved Manifest Cost Baseline: "Supabase getAll, READ-ONLY (episode_production_manifests where episode_backlog_id = run's backlog AND status = APPROVED), executeOnce, alwaysOutputData."
  12A - Readiness & Cost Gate: "Code. Asserts fidelity PASSED, R2 defence on inventory, requires paid_generation_summary. Readiness order: NEEDS_COST_REVIEW > NEEDS_ASSET_REVIEW (pre-existing, retained) > PLANNING_COMPLETE_WITH_TBDS > PLANNING_COMPLETE. Status always REVIEW. Adds readiness_flags and fidelity_validation to manifest_json."
nodes_changed:
  00 - Normalize Production Request: "prompt_version literal only (v0.2) + header comment"
  06 - Prepare Shot Planner Prompt: "HARD CONSTRAINTS block (music, named audio assets, response hold, framing ceiling, asset identity, paid generation, continuity chain, no rewriting) + ASSET STATUS MEANING + requirement 25. Reads the previous shot's validated continuity_state from 08 (runIndex − 1); fails closed PREVIOUS_CONTINUITY_STATE_UNAVAILABLE before the model call."
  07 - Generate Shot Production Plan: "json_schema only: adds the six D-S4B-1 fields (required, strict). Model/options unchanged."
  08 - Validate & Prepare Shot Record: "S4B-LIB + R1_SCHEMA_V02_MISSING + validateShot R1–R7 → throws FIDELITY_VALIDATION_FAILED (run stopped, no retry, no manifest). Output shape unchanged."
  12 - Build Episode Production Manifest: "reads 11A; music via classifyMusicCue (N-2); R2 defence in registerAsset; audio TBD dependencies (N-3) merged into unique_tbd_asset_dependencies (VISUAL + AUDIO) with visual_tbd_dependency_count, audio_tbd_dependencies/_count/_reference_count; paid_generation_summary (R9) with comparison_baseline; source_fidelity summary. tbd_asset_reference_count column semantics unchanged (visual)."
  14 - Build Agent-005 Director Brief: "reads 12A; adds NEEDS_COST_REVIEW message"
connections: "removed 03B→04, 11→12, 12→13; added 03B→03C→04, 11→11A→11B→12, 12→12A→13"
untouched_verified: "01, 01A, 01C, 02, 02B, 03, 03A, 03B, 04, 05, 09, 10, 10A, 11, 13 and the retired 09A–09D branch (version diff f83f00d1 → aedd1743 lists only the nodes above)"

static_validation:
  result: PASSED
  method: "fresh get_workflow_details of aedd1743 compared with the generated node codes: 00, 03C, 06, 08, 12, 12A, 14 byte-identical; 11A identical except one trailing newline (whitespace only); 07 schema identical; LIB embedded verbatim in 03C/08/11A/12; model gpt-5.6-luna; active false; activeVersionId null. n8n validation warnings are all pre-existing (09C expression prefix, disconnected retired 09A/09B, canvas grouping)."
  db_constraint_check: "episode_production_manifests has no CHECK on readiness_state/status, so NEEDS_COST_REVIEW is storable without a schema change"

free_tests:   # all free: zero OpenAI/Gemini/Runway calls, zero Supabase writes
  suite_harness: "JjO4UuM4PTqBNVUQ TEST — S4B Free Safety Suite (read-only reads of script 14471926 and EP005 manifests + S4B-LIB + suite v1)"
  F-1:  {exec: 480, result: "music_required_shots = [S027] from the generic classifier (not hard-coded); uncertain = []", pass: true}
  F-2:  {exec: 480, result: "'None. Chord enters at 2s' → UNCERTAIN; 'No music bed.' → ABSENT; 'Soft bed under dialogue.' → PRESENT; also 'None yet.', 'None. Success chord has fully faded.', 'None. No closing sting.' → ABSENT", pass: true}
  F-3:  {exec: 480, result: "AMBIENCE ref 20 / shots 20; FOLEY_CLOTH 7/7; COMPLETION_SFX 1/1 (S025); FOLEY_TOUCH 1/1 (S028); all canonical_id TBD, UNRESOLVED", pass: true}
  F-4:  {exec: 480, fixture: 751814b1, result: "32 violations; every design-listed (rule, shot) pair fires (R2 S007/S020 + other invented REUSE; R3 S009 S010 S012 S013 S015 S022; R4 S013; R5 S025; R6 S002 S025; R7 S029; R8 S012 S014 S017); missing_expected = []", pass: true}
  F-5:  {exec: 480, fixture: c56cabc0, result: "46 violations; all expected pairs fire (R2, R3 ×6, R5 S025, R6 S002/S025, R7 S024, R8 S014/S015); missing_expected = []", pass: true}
  F-6:  {exec: 480, result: "negative control (751814b1 with the defects patched out) → 0 violations", pass: true}
  F-7:  {exec: 480, result: "structured-state R8: clean chain 0; reintroduced element → R8_STATE_REINTRODUCED; adjacent flip → R8_CONTINUITY_BREAK; source-authorised restore suppresses the reintroduction flag", pass: true}
  F-10: {exec: 480, result: "TMP_EP005_BERRY_SMUDGE_OVERLAYS (Agent-004 NEW) marked REUSE → R2_INVENTED_REUSE; passes only when the same ID is in the registry fixture; NEW_REQUIRED status → no R2", pass: true}
  F-8:
    harness: "cRAen1RG5zhqIxtD TEST — S4B F-8 Fail-Closed Loop: byte-identical copies of live 00, 01A, 01C, 03, 03B, 03C, 04, 05, 06, 08, 10A, 11, 11A, 11B, 12, 12A; 07 replaced by a fixture (no OpenAI); 10 replaced by a fixture collecting 08 runs (no DB); 03A, 09, 13 absent (no writes). Real splitInBatches loop."
    CLEAN: {exec: 481, result: "29/29 shots through 06→08; previous-state chain works in real n8n (S014 prompt carries S013 end state); 11A PASSED; reached TEST - WRITE PATH REACHED; readiness NEEDS_COST_REVIEW (flags NEEDS_COST_REVIEW + UNRESOLVED_TBDS); video 17 > baseline 15 (c56cabc0, SAME_SCRIPT); image 17 vs 14, compositor 27 vs 28; music [S027]; holds [S005,S008,S013,S019]; reused = 3 approved audio assets only; status REVIEW", pass: true}
    SHOT_VIOLATION: {exec: 482, result: "stopped at 08 on S013: R4_CLUE_IN_RESPONSE_HOLD; 10A/11/11A/11B/12/12A and the write path never ran", pass: true}
    SEQUENCE_VIOLATION: {exec: 483, result: "all 29 shots passed 08; stopped at 11A: S014 R8_STATE_REINTRODUCED + R8_CONTINUITY_BREAK (S014, S015); 11B/12/12A and the write path never ran", pass: true}
  F-9:
    S4 gate harness 5gE7wq8ItL8QggdL: {T-S4-1: "exec 492 → TRUE (14471926 APPROVED)", T-S4-2: "exec 493 → FALSE → 02B BLOCKED (old-gate copy still reproduces the pre-S4 defect)", pass: true, note: "harness 00/02B are the historical pre-S3-005 copies; the 02 gate under test is unchanged by S4B"}
    S4 mapping harness roiROf6Qa21iDR8x: {T-S4-3/4: "exec 485 → all 6 stored manifests: tbd and low-complexity mapping correct", pass: true, note: "node 13 unchanged; 12A output is a superset of the 12 fields node 13 maps"}
    S3-005 harness rjWJkzqtSvNtonv4: {sync: "00 copy synced to live v0.2", T-1: 486, T-2: 487, T-3: 488, T-4: 489, T-5: 490, T-6: 491, T-7: 484, result: "all 7 identical outcomes to ENG-20260925-010", pass: true, note: "wiring restored to real node 01 after T-7; fixture node left disconnected"}
paid_calls: {openai: 0, gemini: 0, runway: 0}
agent005_executions: 0   # search_workflow_executions(oHXIgg7khm0FgLvB, since 2026-09-20) = none
supabase_writes: 0       # manifests 6 md5 70ecd4294857afae72d2f95038ea9866, shot_production_plans 232 md5 c56e909f0a8da959822c37ce3960125f, episode_scripts 4 md5 9f51ef6fc1fb15ee0a0d69624a6e1a2a — identical before and after
manifest_statuses: "unchanged: c56cabc0 APPROVED, 751814b1 REVIEW (both DO_NOT_USE_FOR_NEW_PAID_PRODUCTION)"
financial_actions: "none (no purchases, renewals, reloads, upgrades, limit changes)"
status: "S4B_CONFIGURED + STATIC_VALIDATION_PASSED + FREE_SAFETY_VALIDATION_PASSED + UNPUBLISHED"

rollback:
  primary: "restore_workflow_version(oHXIgg7khm0FgLvB, f83f00d1-b886-4379-b5b6-8cd79c6cc0fc) returns to the S3-005 draft (prompt v0.1, no S4B nodes)"
  offline: "RECOVERY_AGENT005_f83f00d1_pre_S4B.json (pre-S4B) and RECOVERY_AGENT005_aedd1743_S4B.json (this draft)"
  data: "nothing to roll back: no DB writes, nothing published"
artifacts: ["s4b_tests/S4B_LIB_v1.js", "s4b_tests/S4B_TEST_SUITE_v1.js", "s4b_tests/S4B_FIXTURE07_v1.js", "s4b_tests/S4B_node_codes.json"]
known_limits:
  - "03C prose heuristics (static cues, restore flag, framing ceiling) are tuned on the EP005 v02 script; other episodes may need a false-positive review on their first run (fail closed, not silent)."
  - "Previous-state chaining uses 08 output of runIndex − 1; verified in the real loop (F-8), but a manual partial re-run of the loop would fail closed rather than continue."
  - "D-S4B-6 future item: Agent-004 structured continuity state."
next_human_decision: "Whether to authorise exactly ONE paid Agent-005 regeneration of episode_script_id 14471926-f6fb-4bba-b355-109f3ae9e21c with gpt-5.6-luna, no retries. Not performed."
blocked: ["Agent-005 publication", "paid regeneration", "Agent-006/007 (EP005 and generally)", "S3-B (legacy UNIQUE(episode_code, script_version_number) stays)", "Node 07B", "Agent-000 build"]
```

---

## ENG-20260925-012: S4B.1, governed asset registry reconciliation for Agent-005 R2 (unpublished)

```yaml
change_id: "ENG-20260925-012"
timestamp: "2026-09-25T08:16Z"
actor: "Claude"
requested_by: "Gilang"
target: "AGENT-005 Storyboard & Shot Production Planner v0.1 (n8n oHXIgg7khm0FgLvB)"
change_type: "EDIT (R2 registry source only)"
recorded_decisions:
  S4B: "accepted as S4B_CONFIGURED + STATIC_VALIDATION_PASSED + FREE_SAFETY_VALIDATION_PASSED + UNPUBLISHED"
  R2_UNAPPROVED_NEW_ASSET: "explicitly accepted (consistent with 'Agent-005 must not invent canonical asset IDs')"
  correction: "S4B wrongly assumed no governed registry exists (GOVERNED_REUSABLE_REGISTRY = []). public.asset_registry exists and Agent-006 already resolves canonical assets from it."
  registry_rule: "Governed reusable = asset_registry rows with status APPROVED or LOCKED. REVIEW, test, mock and unapproved candidates never qualify. Rows identifiable as development/mock fail closed (excluded) even with an inconsistent status. No registry rows altered, approved or created."
  allowed_REUSE_set: "Agent-004 asset_summary.unique_reused_asset_ids ∪ governed APPROVED/LOCKED asset_registry.asset_id"

baseline_version: "aedd1743-56c9-4660-b3c3-f48dd8336903"   # re-checked: still the latest version, no drift
new_draft_version: "9d2649af-eb2b-421a-91ea-1989b35e4274"
published: false          # active false, activeVersionId null
model: "gpt-5.6-luna (unchanged)"
prompt_version: "agent005-shot-planning-v0.2 (unchanged)"

changes:   # full-workflow compare aedd1743 → 9d2649af: exactly these
  added_node:
    03B2 - Get Governed Reusable Assets: "Supabase getAll on asset_registry, READ-ONLY. Filter type 'string' with the PostgREST expression status=in.(APPROVED,LOCKED): explicit OR via IN, no reliance on implicit match semantics. returnAll, orderBy asset_id, executeOnce, alwaysOutputData (an empty or failed-to-match registry yields a stricter, empty governed set; a read error stops the run)."
  changed_node:
    03C - Build Source Fidelity Profile: "S4B-LIB v1 unchanged (sha256 04179ff0…). Driver now reads the context from 03B and the registry rows from 03B2; keeps only rows whose status is exactly APPROVED or LOCKED (code-level re-check of the DB filter) and excludes rows identifiable as development/mock/test (metadata_json.development_mock true, a mock provider, a mock:// storage path, or a TEST_/MOCK_ asset_id or alias). Builds GOVERNED_REUSABLE_REGISTRY from the remaining asset_id values and records governed_registry_source (rows read, governed count, exclusions) in the profile."
  connections: "removed 03B→03C; added 03B→03B2→03C"
  unchanged_verified: "all other 32 nodes byte-identical to aedd1743 (00, 06, 07, 08, 11A, 11B, 12, 12A, 13, 14 …). 06/08/12/12A consume the registry through the existing fidelity profile, so no code change was needed there; the 06 prompt now lists the governed registry IDs as allowed REUSE IDs."
preserved_R2_behaviour: "Agent-004 NEW never becomes REUSE by ID knowledge; unknown identity stays TBD; literal names are never asset IDs; R2_UNAPPROVED_NEW_ASSET active; REVIEW candidates do not qualify; no status promotion."

tests:   # free only; F-8 loop harness cRAen1RG5zhqIxtD now carries byte-identical copies of live 03B2 and 03C, plus a test-only 'Registry Fixture Injector' that passes live rows through unchanged except in two named cases
  R-S4B1-1_live_registry_read:
    exec: 494
    registry_totals: "12 rows: APPROVED 3, LOCKED 0, REVIEW 9 (read-only SQL and 03B2 agree)"
    governed_ids_selected: ["SFX-LUMI-CLUE-CHIME (AUDIO/SFX, APPROVED)", "SFX-MIKKO-TRY-WHOOSH (AUDIO/SFX, APPROVED)", "SFX-WIN-SPARKLE-CHORD (AUDIO/SFX, APPROVED)"]
    review_excluded: "all 9 REVIEW rows excluded (6 Agent-007 candidates for TMP_EP005_* overlays/props and TEST_A007_PAID_SMOKE_STAR are REVIEW; the DB filter returns none of them)"
    mock_excluded: "the 4 identifiable mock/development rows (MOCK_IMAGE_PROVIDER, mock:// paths, development_mock true) are all REVIEW and excluded; code-level mock exclusion additionally proven by the REG_MOCK_APPROVED case below"
    pass: true
  R-S4B1-2_approved_registry_reuse: {exec: 495, input: "S002 prop SFX-WIN-SPARKLE-CHORD, status REUSE (a registry asset_id that is NOT in Agent-004 unique_reused_asset_ids, which uses the name 'WIN sparkle chord')", result: "passes R2 at 08 and 12A; 29/29; reaches write path; inventory SFX-WIN-SPARKLE-CHORD:REUSE", pass: true}
  R-S4B1-3_review_candidate: {exec: 497, input: "S002 prop CAND-A007-1789527180412-PROP-TMP_EP005_SOFT_CLOTH-A01 (live REVIEW, RUNWAY, non-mock), status REUSE", result: "08 stops S002: R2_INVENTED_REUSE; no manifest path", pass: true}
  R-S4B1-4_agent004_new_stays_new:
    absent_from_registry: {exec: 498, input: "TMP_EP005_SOFT_CLOTH (Agent-004 NEW) as REUSE", result: "08 stops S002: R2_INVENTED_REUSE (it is an Agent-004 NEW_REQUIRED asset)", pass: true}
    present_in_registry_fixture: {exec: 499, input: "same ID injected into the registry fixture as APPROVED (in memory only)", result: "REUSE passes R2; run completes; manifest inventory still classifies it NEW_REQUIRED because node 12 keeps the Agent-004 classification", pass: true}
  mock_exclusion_fixture: {exec: 500, input: "synthetic APPROVED row MOCK-S4B1-FIXTURE-ASSET with development_mock true (in memory only) used as REUSE", result: "03C excludes the row; 08 stops S002: R2_INVENTED_REUSE", pass: true}
  R-S4B1-5_EP005_regression:
    loop: {exec: 494, result: "CLEAN identical to S4B exec 481: 29/29, music [S027], holds [S005,S008,S013,S019], NEEDS_COST_REVIEW (video 17 > baseline 15), approved audio reuse (Lumi clue chime, Mikko TRY whoosh, WIN sparkle chord) still REUSE, reused count 3, no REVIEW visual candidate reusable, S014 prompt carries previous state"}
    suite: {exec: 496, harness: "JjO4UuM4PTqBNVUQ", result: "F-1..F-7, F-10 all pass, outputs identical to exec 480"}
    pass: true
  not_rerun: "S4 gate/mapping and S3-005 identity harnesses: their surfaces (00–03, 13) are unchanged by S4B.1"

static_verification: "03C equals the generated code and embeds S4B-LIB verbatim; 03B2 is getAll only (no write operation exists on the node); model gpt-5.6-luna; prompt v0.2; active false; activeVersionId null"
paid_calls: {openai: 0, gemini: 0, runway: 0}
agent005_executions: 0
supabase_writes: 0    # manifests 6 md5 70ecd429…, shot_production_plans 232 md5 c56e909f…, episode_scripts 4 md5 9f51ef6f… unchanged; asset_registry 12 rows md5 9854a316ac7d9504409d530793749274, latest created/updated 2026-09-24T21:11Z (no change today)
manifest_statuses: "unchanged: c56cabc0 APPROVED, 751814b1 REVIEW (both DO_NOT_USE_FOR_NEW_PAID_PRODUCTION)"
status: "S4B.1_REGISTRY_RECONCILED + FREE_VALIDATION_PASSED + UNPUBLISHED"

observations_for_humans:
  - "Registry IDs and Agent-004 names differ for the same audio assets (SFX-WIN-SPARKLE-CHORD vs 'WIN sparkle chord', the latter being a registry alias). Both are valid REUSE IDs now. Registry aliases are deliberately NOT treated as governed IDs (asset_id only, as instructed); if aliases should count, that is a separate decision."
  - "There are no APPROVED or LOCKED visual assets yet; characters and environment therefore stay TBD for EP005, as before."
rollback: "restore_workflow_version(oHXIgg7khm0FgLvB, aedd1743-56c9-4660-b3c3-f48dd8336903) returns to S4B; offline copy RECOVERY_AGENT005_9d2649af_S4B1.json (this draft) and RECOVERY_AGENT005_aedd1743_S4B.json"
next_human_decision: "Authorise exactly ONE paid Agent-005 regeneration of episode_script_id 14471926-f6fb-4bba-b355-109f3ae9e21c with gpt-5.6-luna, no retries. Not performed."
blocked: ["Agent-005 publication", "paid regeneration", "Agent-006/007", "S3-B", "Node 07B", "Agent-000 build"]
```

---

## ENG-20260925-013: Authorised single paid Agent-005 regeneration of EP005 v02 (failed closed at R8)

```yaml
change_id: "ENG-20260925-013"
timestamp: "2026-09-25T09:45Z"
actor: "Claude"
requested_by: "Gilang"
type: "AUTHORISED PAID RUN (one execution, OpenAI planner only, max 29 calls, no retries)"
recorded_decision: "S4B.1 accepted: S4B.1_REGISTRY_RECONCILED + FREE_VALIDATION_PASSED + UNPUBLISHED"
preflight:
  versionId: "9d2649af-eb2b-421a-91ea-1989b35e4274 (latest in history; nodes and connections byte-identical to the ENG-20260925-012 export)"
  activeVersionId: null
  model: "gpt-5.6-luna; node 07 has no retryOnFail"
  prompt_version: "agent005-shot-planning-v0.2"
  s4b_s4b1_nodes: "present (03B2, 03C, 06, 08, 11A, 11B, 12, 12A, 14 as recorded)"
  03B2: "getAll only, filter status=in.(APPROVED,LOCKED)"
  db_baseline: "manifests 6 md5 70ecd429…, shot_production_plans 232 md5 c56e909f…, episode_scripts 4 md5 9f51ef6f…, asset_registry 12 md5 9854a316…; script 14471926 = EP-CANDIDATE-005 v02 — Three Gentle Wipes, APPROVED"
invocation: "Single-use caller workflow 3lwnN46SfU3IkC8V (Execute Workflow → oHXIgg7khm0FgLvB, input episode_script_id only), because Agent-005's manual test path supplies label identity and editing it would change the authorised version. Agent-005 was not modified. The caller ran once (exec 501) and has been archived."
execution:
  agent005_execution_id: "502"
  caller_execution_id: "501"
  production_plan_run_id: "A005-1790328680362"
  lookup: "BY_ID → 14471926 (EP-CANDIDATE-005 v02, APPROVED), backlog 07d622e9-a152-4107-b300-f052546405e3"
  openai_calls: 29
  per_shot_validation_08: "29/29 passed R1–R7"
  shot_rows_written: 29
  result: "FAILED CLOSED at 11A"
  failed_shot: "S022"
  failed_rules: ["R8_STATE_REINTRODUCED", "R8_CONTINUITY_BREAK"]
  message: "AGENT-005 FIDELITY_VALIDATION_FAILED run A005-1790328680362: S022 [R8_STATE_REINTRODUCED] \"Berry smudge on Mikko's nose\" was removed by S021 but is visible again | S022 [R8_CONTINUITY_BREAK] \"Berry smudge on Mikko's nose\" start=true but previous shot ended false — run stopped; no automatic retry (D-S4B-2); no production manifest will be written (D-S4B-4)."
  manifest_created: false
  retries: 0
root_cause: "The model set S022 continuity_state nose visible_at_start=true, copying S021's start value, despite the 06 instruction to chain from the previous end state. S022's written plan (summary, QC, camera, no overlays) correctly describes a clear nose. Structured data defect; creative content correct."
audit_summary: "EP005_AGENT005_PAID_REGENERATION_REVIEW.md — identity, dialogue, roles, structure: pass; continuity 3→2→1→0 correct at S009/S015/S021, S014 does not restore the cheek, only S022's structured start flag is wrong; holds S005/S008/S013/S019 clean (no glint); MACRO only S018/S019 (source-justified); music only S027 (WIN sparkle chord); audio TBDs AMBIENCE 20/20, FOLEY_CLOTH 7/7, COMPLETION_SFX 1/1, FOLEY_TOUCH 1/1; REUSE only the 3 approved audio assets; NEW_REQUIRED mirror/cloth/overlays; Mikko/Lumi/environment TBD; workload image 26, video 20 (> baseline 15 → would be NEEDS_COST_REVIEW), compositor 28"
verdict: "NOT_SAFE_FOR_HUMAN_MANIFEST_APPROVAL (no manifest exists; the run failed closed on S022)"
post_run_checks:
  manifests: "6 rows, md5 70ecd4294857afae72d2f95038ea9866 (unchanged); 0 for this run; c56cabc0 APPROVED, 751814b1 REVIEW (unchanged)"
  shot_production_plans: "232 pre-existing rows md5 c56e909f0a8da959822c37ce3960125f (unchanged) + 29 new REVIEW rows under A005-1790328680362 (retained per D-S4B-4)"
  episode_scripts: "md5 9f51ef6f… unchanged"
  asset_registry: "md5 9854a316… unchanged"
  agent005: "versionId 9d2649af unchanged; active false; activeVersionId null"
  executions_since_09:00Z: "501 (caller) and 502 (Agent-005) only"
not_done: ["no retry or second run", "no Agent-006/007", "no publication", "no S3-B", "no Gemini/Runway/image/video/audio generation", "no billing/subscription/credit/limit changes", "no status changes to scripts, manifests or registry"]
options_for_humans: ["(a) deterministic start-state chaining in 08 (needs a decision beyond D-S4B-2 'no silent correction')", "(b) check start flags against the previous shot inside 08 so the error fails at the shot itself, before later calls", "(c) another single paid run under the current design"]
status: "PAID_RUN_FAILED_CLOSED (R8 at S022) + NO_MANIFEST + UNPUBLISHED"
```

## ENG-20260926-014: S4B.2, deterministic continuity start-state chaining for Agent-005 (unpublished)

```yaml
change_id: "ENG-20260926-014"
date: "2026-09-26"
requested_by: "Gilang"
type: "WORKFLOW CHANGE (draft only) + FREE replay/tests"
recorded_decision: "ENG-20260925-013 accepted as a valid fail-closed result; the 29 REVIEW rows of A005-1790328680362 are preserved unchanged"
workflow: "AGENT-005 — Storyboard & Shot Production Planner v0.1 (oHXIgg7khm0FgLvB)"
previous_version: "9d2649af-eb2b-421a-91ea-1989b35e4274"
intermediate_version: "8cd85184 (06 only)"
new_version: "517b11ef-cd04-4779-bb44-a5cdb4d86ac8"
publish_state: "active false, activeVersionId null (unpublished)"
unchanged: "model gpt-5.6-luna; prompt_version agent005-shot-planning-v0.2; S4-S4B.1 behaviour; 11A R8 kept as defence in depth; all nodes except 06 and 08; connections identical"
node_06_change:
  - "adds previousValidatedShot from $('08 …').all(0,$runIndex-1)[0].json → {shot_id, shot_index, tracked_elements, continuity_ledger}; passed downstream as s4b2_previous"
  - "constraint 7 wording only: visible_at_start is system-set bookkeeping from the previous validated end state; prose, overlays, actions and QC must be consistent with that start state; the model remains responsible for visible_at_end"
node_08_change:
  - "embeds S4B2-CONT v1 (sha256 f4d0718fb6ab93072d8a8265db6393ae9428a554ccfd028a141e4d22a3d11e27) after S4B-LIB v1 (unchanged, verbatim)"
  - "after R1-R7: for shot_index > 1, missing or mismatched previous state → fail closed"
  - "visible_at_start := previous visible_at_end per normalised element key; each change logged in shot_plan_json.continuity_normalizations[] {element, field: visible_at_start, model_value, authoritative_value, source_shot_id, reason: PREVIOUS_VALIDATED_END_STATE}; plan.continuity_start_authority recorded"
  - "visible_at_end never rewritten; creative prose/visual instructions never rewritten"
  - "fail closed: R8_STATE_REINTRODUCED (removed element visible again, early per-shot) and R8A_START_STATE_SEMANTIC_CONTRADICTION (plan text/overlay contradicting the authoritative start state); no retry (D-S4B-2), no manifest (D-S4B-4)"
  - "first shot: existing behaviour, no EP005 hard-coding; R8A heuristic is generic (element-token + family-token matching)"
  - "output adds continuity_ledger (not persisted; 09 maps fields explicitly)"
code_hashes_sha256_prefix: {"06": "45464bc9de1d1c53", "08": "24affebf6d4554cc", "06_prev": "4ae0be9c6e352745", "08_prev": "9f4f22c010c6d3d5"}
static_validation: "only 06 and 08 differ from 9d2649af; connections identical; live 06/08 equal generated code; LIB verbatim; model/prompt unchanged; unpublished — PASS"
tests_harness: "cRAen1RG5zhqIxtD (06/08 synced to live, parity verified; added read-only node 'TEST - Read Paid Run A005-1790328680362'; case reset to CLEAN)"
tests:
  T-S4B2-5_replay_29_paid_plans: "exec 503 PASS — 29 processed, 1 normalization, 0 R8A, 11A PASS"
  T-S4B2-1_start_flag_wrong_prose_ok: "exec 504 PASS — S022 nose forced true → normalized to false, run passes"
  T-S4B2-2_prose_contradiction_false: "exec 505 FAIL CLOSED as expected — 08 S022 R8A (overlay keeps nose smudge visible at start)"
  T-S4B2-3_start_true_model_false: "exec 506 PASS — S016 nose false → normalized to true"
  T-S4B2-3B_prose_contradiction_true: "exec 507 FAIL CLOSED as expected — 08 S016 R8A (QC says nose smudge already absent at start)"
  T-S4B2-4_clean_fixture: "exec 508 PASS — 0 normalizations; readiness NEEDS_COST_REVIEW"
  regression_sequence_violation: "exec 509 FAIL CLOSED as expected — now caught earlier at 08 S014 R8_STATE_REINTRODUCED (cheek removed by S009)"
normalizations_in_replay:
  - {shot: "S022", element: "Berry smudge on Mikko's nose", field: "visible_at_start", model_value: true, authoritative_value: false, source_shot_id: "S021", reason: "PREVIOUS_VALIDATED_END_STATE"}
replay_assertions: "chain S009 cheek / S015 mouth / S021 nose, final 0, S014 never restores; holds S005=4 S008=3 S013=4 S019=5; MACRO only S018/S019; music only S027; REUSE only the 3 governed SFX; NEW_REQUIRED mirror/cloth/overlays; audio TBDs AMBIENCE 20, FOLEY_CLOTH 7, COMPLETION_SFX 1, FOLEY_TOUCH 1 — PASS"
manifest_readiness_preview: "11B/12/12A only, stopped before Node 13: image 26 / video 20 / compositor 28; baseline c56cabc0 image 14 / video 15 / compositor 28; VIDEO_GENERATION_INCREASE 20 > 15; readiness NEEDS_COST_REVIEW, flags [NEEDS_COST_REVIEW, UNRESOLVED_TBDS]; no manifest written"
fixture_note: "harness fixture 07 v1.1 scrubs a real stored S014 sentence from 751814b1 ('Maintain the selected cheek smudge and nose smudge in continuity where visible.'); R8A now catches this latent prose defect, which the previous CLEAN fixture carried"
paid_calls: "0 (no OpenAI, Gemini or Runway calls; no Agent-005 executions)"
production_writes: "0"
db_checks_after: "manifests 6 md5 70ecd4294857afae72d2f95038ea9866; shot_production_plans 261 md5 2d55036e516cf077dfac995f24944590; run A005-1790328680362 29 rows md5 00da99ba8ee90cdb3ea85511b1d318fb (identical before/after); episode_scripts md5 9f51ef6f…; asset_registry 12 md5 9854a316… — all unchanged"
historical_run: "A005-1790328680362 unchanged: not corrected, no manifest attached, 29 REVIEW rows retained"
recovery_assessment: "S4B2_EXISTING_PAID_OUTPUT_RECOVERY_OPTIONS.md — design only, not executed; recommends a single-use recorded-output replay workflow under a new run ID with provenance, if authorised"
rollback: "restore_workflow_version(oHXIgg7khm0FgLvB, 9d2649af-eb2b-421a-91ea-1989b35e4274); offline exports RECOVERY_AGENT005_9d2649af_S4B1.json (previous) and RECOVERY_AGENT005_517b11ef_S4B2.json (this version); keep unpublished"
artifacts: ["RECOVERY_AGENT005_517b11ef_S4B2.json", "s4b_tests/S4B2_CONT_v1.js", "s4b_tests/S4B2_node_codes_06_08.json", "s4b_tests/S4B2_FIXTURE07_v1.1.js", "S4B2_EXISTING_PAID_OUTPUT_RECOVERY_OPTIONS.md"]
not_done: ["no publish", "no paid run", "no manifest", "no Agent-006/007", "no S3-B", "no registry/script/manifest status changes", "no billing/subscription/credit/limit changes"]
status: "S4B.2_DETERMINISTIC_CONTINUITY_CONFIGURED + FREE_REPLAY_PASSED + UNPUBLISHED"
```

## ENG-20260926-015: Option B recovery replay of EP005 exec 502 (AGENT-005R, zero paid calls)

```yaml
change_id: "ENG-20260926-015"
date: "2026-09-26"
requested_by: "Gilang"
recorded_decision: "S4B.2 accepted (S4B.2_DETERMINISTIC_CONTINUITY_CONFIGURED + FREE_REPLAY_PASSED + UNPUBLISHED); Option B chosen: bounded recovery replay under a new run ID"
authorisation: "ONE single-use recovery workflow; ONE execution; 29 new REVIEW shot rows under a new A005R- run ID; at most ONE REVIEW manifest only if all validators pass; archive afterwards. No paid provider call; no delete; no historical update."
amendment_applied: "Source integrity guard runs BEFORE any database write; Agent-005's 03A delete replaced by read-only '03A-R - Confirm Recovery Run ID Is Unused' (checks shot_production_plans AND episode_production_manifests; STOP on collision, no alternate ID)"
recovery_workflow:
  id: "x4gfTmR7veGxCYvB"
  name: "AGENT-005R — Recovery Replay — EP005 Exec 502"
  executed_version: "4938a040-0085-4035-bb72-9627b318441b"
  published: false
  archived: true
  export: "ARCHIVE_AGENT005R_x4gfTmR7veGxCYvB_4938a040.json"
  static_diff_vs_agent005_517b11ef:
    byte_identical: ["01A","01C","02","02B","03","03B","03B2","03C","04","05","06","08","09 (insert)","10","10A","11","11A","11B","12","12A","13 (insert)","14"]
    changed: ["00 (run ID prefix A005R- only)"]
    removed: ["Execute Workflow trigger","TEST triggers","00B","01","07 OpenAI","03A delete","09A-09D (disconnected update path)"]
    added: ["R - Manual Trigger","R - Recovery Request","03R - Read Source Run (read-only)","03S - Source Integrity Guard","03A-R1/03A-R2 (read-only)","03A-R - Confirm Recovery Run ID Is Unused","07R - Load Recorded Model Output","08R - Attach Recovery Provenance","12R - Recovery Manifest Provenance & Gate"]
    node_types: "code, if, limit, manualTrigger, set, splitInBatches, supabase only — no OpenAI/Gemini/Runway/HTTP/sub-workflow node; only credential = Supabase"
    write_nodes: "09 insert, 13 insert (no update, no delete)"
    settings: "callerPolicy none; no retryOnFail anywhere"
agent005: "oHXIgg7khm0FgLvB unchanged at 517b11ef-cd04-4779-bb44-a5cdb4d86ac8, activeVersionId null; no Agent-005 executions"
source_run:
  production_plan_run_id: "A005-1790328680362"
  execution_id: "502"
  model_workflow_version: "9d2649af-eb2b-421a-91ea-1989b35e4274"
  prompt_version: "agent005-shot-planning-v0.2"
  rows: 29
  md5_sql: "00da99ba8ee90cdb3ea85511b1d318fb"
  content_fingerprint_sha256: "da20f514a40db739e1c40263d55bae9dbaa9d62865c0787535a707e88909621a (in-workflow guard; SQL md5 not executable inside n8n without a Postgres credential, so verified by operator before/after)"
  row_uuids: ["S001 8c57ce0a-681f-4af4-a94c-ff22db2991ed","S002 f90ae020-0d53-4e8e-ad97-b71059e8159c","S003 52f3f6aa-0882-45be-8b84-4e4d02942aa5","S004 ae16ebfe-668d-4483-81c5-85fc7a72dc06","S005 c759c5c2-b5d6-4ab3-836a-f5e4b1442c6f","S006 9d73c2cd-1a33-488d-ab4f-e8a6eda0904e","S007 6815c34b-985e-4146-862d-8d47cbcae2e2","S008 2a4e5c37-eb88-43e6-9bb1-71142b93d1d8","S009 d33f546e-85f6-4dc3-8a62-4bac159164a4","S010 7d6f0224-4f0d-4476-967f-4c9ca55a955f","S011 63de8d7b-3543-4f02-9fe1-81fa1c0fd5b6","S012 f1340ca3-0f32-46ba-a7cf-e28e7430e720","S013 70d1c835-be38-402a-8a7b-de61b556e9fe","S014 dc400bd1-1978-4b1c-926f-45224b256430","S015 7b8cf02f-350b-4cb7-aca5-f87345d567f0","S016 7d0a8fe2-037b-40f7-af82-c6d63876dd55","S017 4f2cd222-b861-43de-9014-017cba0c9128","S018 c52ac2cb-384a-4fff-ad02-a0c234aaa83e","S019 82724f6e-680a-48c6-b5e9-f29a765ea42e","S020 100f6d76-4860-4972-9787-040243e7a376","S021 c0f149e9-2d92-4e3d-9e91-5eb77589a851","S022 f93cf5b5-a9d1-45e3-93e1-5af68c68446c","S023 f85fbf65-6fea-4ea5-9fab-6f79845a5c53","S024 fef7f018-4b9a-4436-96d8-a3f05457d5d3","S025 1448abb0-2301-4de9-bc1a-be972e1c632a","S026 9dbb9c0d-a7ef-4eeb-8f31-5378f6d5ad82","S027 773f3b63-7c06-4a1c-ac2c-e28be24955a4","S028 52d20721-be6f-45b7-8f8b-73b690699d45","S029 565c095b-5850-4066-98ce-ab84ad6d0d23"]
pre_run_checksums_03_47_54Z: "manifests 6 md5 70ecd4294857afae72d2f95038ea9866; shot_production_plans 261 md5 2d55036e516cf077dfac995f24944590; source run 29 md5 00da99ba8ee90cdb3ea85511b1d318fb; episode_scripts 4 md5 9f51ef6fc1fb15ee0a0d69624a6e1a2a; asset_registry 12 md5 9854a316ac7d9504409d530793749274; 0 A005R rows; 0 manifests on source run"
pre_run_local_simulation: "live 517b11ef code + recovery nodes: happy path = 1 normalization, NEEDS_COST_REVIEW 26/20/28; negative cases stopped: tampered plan (guard fingerprint), missing row (guard), altered source shot (guard), run-ID collision (03A-R), extra normalization (08R)"
execution:
  id: "510"
  mode: "manual, single; no retry"
  window: "2026-09-26T03:48:05Z → 03:48:33Z"
  status: "success"
  recovery_run_id: "A005R-1790394486839"
  guards: "03S PASSED (29 rows, S001–S029, pinned UUIDs, script/prompt/agent labels, source shots equal APPROVED v02, fingerprint, exec-502 time window); 03A-R: 0 plans / 0 manifests for the new run ID"
  loop: "07R 29 runs, model_call_made=false, stripped fields none; 08 R1–R7 + S4B.2 passed 29/29; 08R expected-normalization assertion passed"
  normalizations: [{shot: "S022", element: "Berry smudge on Mikko's nose", field: "visible_at_start", model_value: true, authoritative_value: false, source_shot_id: "S021", reason: "PREVIOUS_VALIDATED_END_STATE"}]
  normalization_count: 1
  validators: "11 COMPLETE; 11A R8 PASSED (structured_continuity true); 11B baseline c56cabc0 SAME_SCRIPT; 12A passed; 12R passed (29 rows provenance ok, exactly 1 normalization, status REVIEW)"
writes:
  shot_production_plans: "29 inserts under A005R-1790394486839, all REVIEW (S001 18745d59-54c8-4aa0-bb46-9590f1cca9f1 … S022 891d72bf-e9b4-474d-ba7f-a916b6fea22b … S029 3970d716-def3-4830-b445-21e4df544084; full list in EP005_AGENT005_RECOVERY_REPLAY_REVIEW.md §4)"
  episode_production_manifests: "1 insert: ff5afc70-02ed-46d7-acd1-b69ae15fd0dd, status REVIEW, readiness NEEDS_COST_REVIEW, flags [NEEDS_COST_REVIEW, UNRESOLVED_TBDS], image 26 / video 20 / compositor 28, LOW 1 / MEDIUM 26 / HIGH 2, new 3 / reuse 3 / visual TBD refs 97; cost reason VIDEO_GENERATION_INCREASE 20 > 15 (c56cabc0)"
  other: "none; no update; no delete"
provenance:
  rows: "shot_plan_json.recovery = {recovered_from_run_id A005-1790328680362, recovered_from_execution_id 502, recovered_from_row_id <exact source UUID>, source_model_workflow_version 9d2649af…, validator_workflow_version 517b11ef…, source_prompt_version agent005-shot-planning-v0.2, recovery_mode RECORDED_MODEL_OUTPUT_REPLAY, model_call_made false, recovery_change_id ENG-20260926-015, source_run_md5, recovered_from_shot_id/index}"
  manifest: "manifest_json.recovery = same constants + recovery_run_id, source_content_fingerprint_sha256, source_row_ids (29), model_calls_for_recovery 0, normalization_count 1, normalization_summary, note 'Recorded model output from Agent-005 exec 502 … Not newly model-generated.'"
exact_diff_audit: "read-only diff exec-502 rows vs recovery rows: permitted = new IDs/run ID, recovery block, continuity_normalizations, continuity_start_authority, S022 tracked_elements[nose].visible_at_start true→false; unexpected = 0 (no prose/overlay/audio/animation/camera/asset/QC/source_shot/row-column change)"
fidelity: "29/29; removal S009 cheek / S015 mouth / S021 nose; final 0; no reintroduction; S014 no restore; S013 no clue; holds S005=4 S008=3 S013=4 S019=5; MACRO S018,S019; music S027; characters TBD; REUSE only 3 approved audio assets; NEW_REQUIRED mirror/cloth/overlays; audio TBDs AMBIENCE 20, FOLEY_CLOTH 7, COMPLETION_SFX 1, FOLEY_TOUCH 1"
post_run_checks: "source run 29 rows md5 00da99ba8ee90cdb3ea85511b1d318fb, UUIDs unchanged, 0 manifests; 6 historical manifests md5 70ecd429… unchanged (c56cabc0 APPROVED, 751814b1 REVIEW, both DO_NOT_USE_FOR_NEW_PAID_PRODUCTION) + ff5afc70 REVIEW; 261 historical shot rows md5 2d55036e… unchanged (+29 new); episode_scripts 9f51ef6f… and asset_registry 9854a316… unchanged"
paid_calls: "0 (no OpenAI, Gemini, Runway, image/video/audio generation)"
verdict: "SAFE_FOR_HUMAN_MANIFEST_APPROVAL (EP005_AGENT005_RECOVERY_REPLAY_REVIEW.md) — not a cost approval"
rollback_recovery_notes:
  - "Nothing to roll back in Agent-005 (unchanged, 517b11ef)."
  - "AGENT-005R is archived; restorable from archive or ARCHIVE_AGENT005R_x4gfTmR7veGxCYvB_4938a040.json. It must not be re-run without a new explicit authorisation (a re-run would create a second A005R run ID)."
  - "If humans reject the recovery, leave ff5afc70 as REVIEW (or set a human-chosen rejection status) and leave the 29 A005R rows as REVIEW; no deletion is authorised by this change."
  - "Source run A005-1790328680362 remains immutable historical evidence."
not_done: ["no retry/second execution","no model/provider call","no Agent-006/007","no S3-B","no manifest approval","no asset approval/canonicalisation","no Agent-005 publish or change","no billing/subscription/credit/auto-renew/auto-reload/limit changes"]
status: "A005R_RECOVERY_REPLAY_PASSED + REVIEW_MANIFEST_CREATED + NEEDS_COST_REVIEW + ZERO_PAID_CALLS"
```

## ENG-20260926-016: EP005 video-generation cost review (READ ONLY / DESIGN ONLY)

```yaml
change_id: "ENG-20260926-016"
date: "2026-09-26"
requested_by: "Gilang"
type: "READ-ONLY ANALYSIS / DESIGN ONLY — no production change"
recorded_decision: "ENG-20260926-015 accepted and closed: A005R_RECOVERY_REPLAY_PASSED + REVIEW_MANIFEST_CREATED + NEEDS_COST_REVIEW + ZERO_PAID_CALLS; manifest ff5afc70 stays REVIEW / NEEDS_COST_REVIEW (video 20 vs baseline 15); do not approve"
sources: "manifest ff5afc70-02ed-46d7-acd1-b69ae15fd0dd; run A005R-1790394486839 (29 rows, read only); script 14471926 (EP-CANDIDATE-005 v02). c56cabc0/751814b1 used only as historical cost references"
video_shots_20: [S001, S002, S003, S004, S007, S009, S010, S011, S014, S015, S016, S017, S020, S021, S022, S023, S025, S026, S027, S028]
video_seconds: 82.5
classification:
  VIDEO_ESSENTIAL: [S002, S007, S009, S014, S015, S021, S027, S028]
  VIDEO_PREFERRED: [S001, S010, S011, S016, S020, S022, S026]
  STATIC_OR_COMPOSITE_SAFE: [S003, S004, S017, S023, S025]
minimum_defensible_video_shots: [S002, S007, S009, S014, S015, S021, S027, S028]  # 8 shots, 31.0 s
scenarios:
  A_current: "20 video, 82.5 s, +5 vs baseline (+33.33%)"
  B_balanced_RECOMMENDED: "15 video, 63.0 s; video removed from S003, S004, S017, S023, S025 (rigid mirror-layer transforms, deterministic glint/clean-reveal overlays, expression swaps, composited holds); image 26 and compositor 28 unchanged; creative risk low"
  C_le15: "safe; identical to B (15). Stricter C-12 (also composite S010/S016/S022, 12 video, 51.0 s) documented but NOT recommended"
cost_delta: "shots +5 (+33.33%) current vs baseline; B = baseline. Monetary: ACTUAL_COST_DELTA_NOT_VERIFIED (no cost/credit/price columns in public schema; no pricing in asset_creation_jobs or project docs; no Runway video path/rate configured; no browsing or billing access)"
protected: "all three wipes (S009/S015/S021), slow-hand LEARN beat (S014), participation model (S007), TRY set-up (S002), holds S005/S008/S013/S019 (static), correction point S018/S019 (macro, non-video), WIN S027 + S026, COMFORT hand-over S028; ONE→CUE→THREE→WIN, NOTICE→CHOOSE→TRY→LEARN→SOLVE TOGETHER, Mikko=DO, Lumi=SEE preserved in B"
artifact: "EP005_VIDEO_GENERATION_COST_REVIEW.md"
db_checks: "before and after (04:58 UTC) identical: manifests 7 md5 2bfa589546a2d466ca88e3e1ccae6a90; shot_production_plans 290 md5 8568acd2503f2facbb8e89baa007cbda; A005R rows md5 25b208abb584f6001683ce01ec41e338; ff5afc70 REVIEW/NEEDS_COST_REVIEW/20; episode_scripts 9f51ef6f…; asset_registry 9854a316…; asset_creation_jobs 11 / batches 3"
executions: "none (no n8n executions since the ENG-20260926-015 run)"
production_writes: 0
paid_calls: 0
not_done: ["no manifest approval or edit", "no row or animation_plan change", "no replacement manifest or recovery run", "no Agent-005/006/007 change or run", "no publish", "no S3-B", "no billing/credit/subscription/limit changes"]
next_decision: "Gilang/Viva: choose A/B/C; if B, decide how the override is recorded (hand-off decision vs new authorised manifest revision); then decide manifest approval separately"
status: "EP005_COST_REVIEW_COMPLETE + NO_PRODUCTION_CHANGE + NO_PAID_CALLS"
```

## ENG-20260926-017: S4B.3 EP005 balanced optimisation (Scenario B, 15 video, zero paid calls)

```yaml
change_id: "ENG-20260926-017"
date: "2026-09-26"
requested_by: "Gilang"
recorded_decision: "ENG-20260926-016 accepted; human production decision: approve Scenario B (Balanced Optimisation), target video count 15; remove paid video from S003, S004, S017, S023, S025 only; deterministic plan revision; no model/provider call"
source_evidence_immutable: "run A005-1790328680362; recovery run A005R-1790394486839; recovery manifest ff5afc70-02ed-46d7-acd1-b69ae15fd0dd; exec 510; validator baseline 517b11ef; recovery verdict SAFE_FOR_HUMAN_MANIFEST_APPROVAL; cost review ENG-20260926-016"
optimiser_workflow:
  id: "ttGfDO4oTZMb6Wfa"
  name: "AGENT-005O — EP005 Balanced Optimisation — single use"
  executed_version: "d62dc894-e407-4eb1-90f0-881768ea6b05"
  published: false
  archived: true
  export: "ARCHIVE_AGENT005O_ttGfDO4oTZMb6Wfa_d62dc894.json"
  byte_identical_to_517b11ef: ["01A","01C","02","02B","03","03B","03B2","03C","04","05","06","08","09 (insert)","10","10A","11","11A","11B","12","12A","13 (insert)","14"]
  changed: ["00 (run ID prefix A005O-)"]
  removed: ["triggers other than one manual trigger (callerPolicy none)","00B","01","07 OpenAI","03A delete","09A-09D"]
  added: ["03M/03R read-only source reads","03S Source Integrity Guard (before any write)","03A-O1/03A-O2 read-only + 03A-O collision check (no delete, no alternate ID)","07O Load Validated Plan & Apply Scenario B","08O per-shot exact-diff gate + provenance (before each insert)","12O manifest gate vs ff5afc70 + provenance (before 13)"]
  node_types: "code, if, limit, manualTrigger, set, splitInBatches, supabase only; only credential Supabase; no provider/HTTP/sub-workflow node; no retry"
pre_write_guards: "A005R 29 rows S001-S029 REVIEW, pinned UUIDs, APPROVED v02 source shots, exec-510 window, recovery provenance to exec 502, S022 normalization exact, rows fingerprint 61221b4a… (= SQL md5 25b208ab… state); ff5afc70 REVIEW/NEEDS_COST_REVIEW/26/20/28, fingerprint 19b16cd8…; new run ID unused (0 plans / 0 manifests)"
authorised_changes:
  shots: [S003, S004, S017, S023, S025]
  permitted_fields: ["animation_plan.video_generation_required true→false", "animation_plan.method → COMPOSITE (S017, S023 were IMAGE_TO_VIDEO; S003/S004/S025 already COMPOSITE)", "animation_plan.video_justification → explicit non-video rationale", "shot_plan_json.production_optimization (all 29 rows)"]
  preserved: "image_generation_required, compositor_required, prose, actions, dialogue, timing, continuity, assets, audio, overlays, camera, source_shot_json, recovery block, S022 continuity normalization + authority"
execution:
  id: "511"
  window: "2026-09-26T05:22:22Z → 05:22:54Z"
  status: "success; single run; no retry"
  run_id: "A005O-1790400144423"
  validators: "08 (R1-R7 + S4B.2 authority + R8A) 29/29, 0 new normalizations; 08O exact diff 29/29; 11 complete; 11A R8 PASSED; 12A pass; 12O manifest equality vs ff5afc70 pass"
writes:
  shot_production_plans: "29 inserts under A005O-1790400144423, all REVIEW (S001 d14c1c2b-4475-44c3-b1c9-49d79eaae985 … S029 cb8efa7c-e158-4ad7-9f06-7dfef40d3d64; full list in EP005_AGENT005_BALANCED_OPTIMISATION_REVIEW.md §4)"
  episode_production_manifests: "1 insert: 670b201b-6793-4518-ad5a-d051eb98d90c, status REVIEW"
  other: "none; no update; no delete"
workload: "image 26 / video 15 / compositor 28 (calculated); video seconds 63.0 (from 82.5); video shots S001,S002,S007,S009,S010,S011,S014,S015,S016,S020,S021,S022,S026,S027,S028"
readiness: "PLANNING_COMPLETE_WITH_TBDS (computed by unchanged 12/12A, not forced); flags [UNRESOLVED_TBDS]; cost reason WITHIN_BASELINE 15 <= 15 (not a cost approval)"
provenance: "rows: production_optimization {decision_id ENG-20260926-016, change_id ENG-20260926-017, SCENARIO_B_BALANCED_OPTIMISATION, source_run_id, source_manifest_id, optimization_run_id, source_row_id, human_authorised true, model_call_made false; modified shots add original/optimized video flags, original_method, replacement_method COMPOSITE, rationale, changed_fields}; manifest: production_optimization {video_removed_shots [S003,S004,S017,S023,S025], source_video_count 20, optimized_video_count 15, seconds 82.5→63, fingerprints, source_row_ids, recovery_lineage, paid_generation_authorised false}"
exact_diff_audit: "post-run recursive A005R vs A005O: permitted differences only; unexpected 0"
protected_beats: "S002/S007/S009/S014/S015/S021/S027/S028 video unchanged; holds S005=4 S008=3 S013=4 S019=5 no clue; MACRO S018,S019; music S027; removal S009/S015/S021, final 0, S014 no restore, S022 nose start false"
post_run_checks: "A005 md5 00da99ba… unchanged; A005R md5 25b208ab… unchanged; ff5afc70 row md5 3a498a57… unchanged (REVIEW/NEEDS_COST_REVIEW/26/20/28); prior 7 manifests md5 2bfa5895… unchanged; prior 290 shot rows md5 8568acd2… unchanged; scripts 9f51ef6f…, asset_registry 9854a316… unchanged; Agent-005 517b11ef unpublished, not executed"
paid_calls: 0
verdict: "SAFE_FOR_HUMAN_MANIFEST_APPROVAL (EP005_AGENT005_BALANCED_OPTIMISATION_REVIEW.md) — not a paid-generation authorisation"
rollback_notes: ["Agent-005 unchanged; nothing to roll back there", "AGENT-005O archived; must not be re-run without new authorisation (would create a second A005O run)", "If rejected, leave 670b201b and the 29 A005O rows as REVIEW (no deletion authorised)"]
not_done: ["no OpenAI/Gemini/Runway/generation","no Agent-006/007","no S3-B","no manifest or asset approval","no Agent-005 change/publish","no billing/credit/subscription/limit changes"]
status: "S4B.3_BALANCED_OPTIMISATION_PASSED + 15_VIDEO_REVIEW_MANIFEST_CREATED + ZERO_PAID_CALLS"
```

---

## ENG-20260926-018: G3 approval of EP005 manifest 670b201b + S5 Agent-006 hardening (unpublished, free validation only)

```yaml
change_id: "ENG-20260926-018"
date: "2026-09-26"
requested_by: "Gilang"
recorded_decisions:
  prior: "ENG-20260926-017 accepted: S4B.3_BALANCED_OPTIMISATION_PASSED + 15_VIDEO_REVIEW_MANIFEST_CREATED + ZERO_PAID_CALLS"
  G3: "APPROVE EP005 v02 balanced production manifest 670b201b-6793-4518-ad5a-d051eb98d90c (run A005O-1790400144423, script 14471926-f6fb-4bba-b355-109f3ae9e21c). Production-plan approval only; NOT approval of paid generation."
  historical_manifests: "c56cabc0, 751814b1, ff5afc70 unchanged; operationally DO_NOT_USE_FOR_NEW_PAID_PRODUCTION; authoritative EP005 manifest is the exact UUID 670b201b"

part_A_G3_manifest_approval:
  pre_write_verification:   # all read live before the write; all matched
    id: "670b201b-6793-4518-ad5a-d051eb98d90c"
    status: "REVIEW"
    production_plan_run_id: "A005O-1790400144423"
    episode_script_id: "14471926-f6fb-4bba-b355-109f3ae9e21c"
    counts: "shot_count 29, image 26, video 15 (column and manifest_json video list both 15), compositor 28"
    readiness: "PLANNING_COMPLETE_WITH_TBDS, manifest_json.readiness_flags [UNRESOLVED_TBDS]"
    provenance: "production_optimization.decision_id ENG-20260926-016, change_id ENG-20260926-017, paid_generation_authorised false"
    a005o_rows: "29 rows, all REVIEW, S001-S029 at the recorded UUIDs; content identical to the ENG-017 post-run audit snapshot on every audited field (snapshot omitted created_at; all created_at inside exec 511 window 05:22:32-05:22:49Z); md5 2939e2c4364d7e4d1d9c1c94a518930e (first pinned here)"
    table: "no updated_at column; no user triggers on episode_production_manifests"
  write: "UPDATE episode_production_manifests SET status='APPROVED' WHERE id='670b201b-6793-4518-ad5a-d051eb98d90c' AND status='REVIEW'  -- 1 row, 2026-09-26T07:53:11Z"
  before_after:
    status: "REVIEW → APPROVED"
    row_md5_excluding_status: "0891c9e003c2c698f136dc3cac82205f before = 0891c9e003c2c698f136dc3cac82205f after (no other field changed)"
  historical_manifests_unchanged: "7 other manifests md5 2bfa589546a2d466ca88e3e1ccae6a90 before = after; c56cabc0 APPROVED, 751814b1 REVIEW, ff5afc70 REVIEW (row md5 3a498a57… unchanged)"
  other_tables_unchanged: "all 290 non-A005O shot rows 8568acd2…; A005O 29 rows 2939e2c4…; episode_scripts 9f51ef6f…; asset_registry 9854a316…"
  agent005_baseline_readonly_check:
    logic: "live 517b11ef node 11B (episode_backlog_id = 07d622e9-a152-4107-b300-f052546405e3 AND status = APPROVED) → node 12 (APPROVED only, prefer same episode_script_id, newest created_at first, video count = manifest_json.generation_workload.video_generation_shots length)"
    candidates: "670b201b (created 2026-09-26T05:22:53Z, same script, video 15); c56cabc0 (created 2026-09-11T04:45:49Z, same script, video 15)"
    selected: "670b201b-6793-4518-ad5a-d051eb98d90c, match SAME_SCRIPT"
    future_financial_baseline_video: 15
    note: "Agent-005 not executed, not modified, not published (latest version still 517b11ef, activeVersionId null)"

part_B_S5_agent006:
  target: "AGENT-006 — Asset Resolution & Production Readiness Manager v0.1 (ZTBdnKFO8STSjJU4)"
  pre_edit_drift_check:
    version_before: "c4d54cf8-7e4b-4d6f-be60-e863080c541b (only saved version, autosaved 2026-09-15T04:50:42Z)"
    publication: "active false, activeVersionId null, never published, 0 executions"
    vs_audited_definition: "matches ENGINEERING_INVENTORY_CURRENT.md §2.7: 20 nodes; R-010 literal gate leftValue '02 - Approved Production Manifest Found?'; R-011 two status eq filters without matchType; TEST node hard-coded c56cabc0; updatedAt 2026-09-25T01:32:33Z = X-10 bulk MCP enable"
    verdict: "NO_UNRELATED_DRIFT"
  version_after: "0c1c34b3-487e-4ecf-b9e6-62a0da558477 (unpublished; activeVersionId null)"
  change_scope: "8 of 20 nodes changed; 12 byte-identical (triggers, 01, 06, 06B, 07, 08, 09, 10, 11, 13, 14); connections identical except the gate rename; exports + unified diffs in s5_agent006/"

  S5_A_manifest_gate:
    "00 - Normalize Asset Resolution Request": "missing ID → throw 'AGENT-006 BLOCKED (MISSING_PRODUCTION_MANIFEST_ID)'; NEW: UUID regex ^[0-9a-f]{8}-…-[0-9a-f]{12}$ (case-insensitive) → throw 'AGENT-006 BLOCKED (MALFORMED_PRODUCTION_MANIFEST_ID)' before any DB read; ID lower-cased"
    "01": "unchanged (id eq production_manifest_id AND status eq APPROVED, limit 1, alwaysOutputData)"
    gate_IF: "renamed 'production_manifest_id' → '02 - Approved Production Manifest Found?'. Old: leftValue literal text (always non-empty, always TRUE). New (AND): String($json.id).trim().toLowerCase() == String($('00…').production_manifest_id).trim().toLowerCase(); String($json.status).trim() == 'APPROVED'"
    "02B": "message now 'AGENT-006 BLOCKED (MANIFEST_NOT_APPROVED_OR_NOT_FOUND): production_manifest_id <id> does not resolve to an APPROVED episode_production_manifests row … No writes performed.' (stopAndError, was unreachable)"
    "03": "defence in depth: throws BLOCKED unless row.id == requested id AND status == APPROVED; manifest never rediscovered by episode_code or labels"
  S5_B_governed_registry:
    "04": "filterType string, filterString 'status=in.(APPROVED,LOCKED)' (PostgREST IN; replaces two status eq conditions of unverified AND/OR semantics); returnAll; executeOnce; alwaysOutputData"
    "05": "re-applies exact status ∈ {APPROVED, LOCKED} and excludes development/mock/test rows (metadata_json.development_mock true, provider /mock/i, storage_path mock://, asset_id or alias TEST_/MOCK_) — same rule as Agent-005 S4B.1 03C; no registry rows changed"
  S5_C_manifest_compatibility:
    "03": "carries audio_tbd_dependencies and source_manifest_context (manifest status/version, run, backlog, readiness_state + flags, workload counts, TBD counts, production_optimization, recovery_lineage, paid_generation_authorised); full manifest_json still passed through unchanged"
    defect_fixed: "live 05 turned the 4 audio TBDs (audio_category/shots, no asset_type) into ONE key 'TBD::UNKNOWN::Unresolved asset' with 0 shots — 3 audio TBDs silently dropped (proven by running live c4d54cf8 code on 670b201b)"
    "05": "audio TBD → key TBD::AUDIO::<audio_category>, requirement_type AUDIO, shots kept; reads unique_tbd_asset_dependencies ∪ audio_tbd_dependencies; duplicate keys merged (shots/labels unioned), never dropped; fail-closed invariants: visual/audio TBD counts equal manifest visual_/audio_tbd_dependency_count, every audio category present, every TBD ≥1 shot, no TBD carries an asset ID"
    "12": "readiness manifest gains dependency_breakdown (reuse/new/visual TBD/audio TBD, unresolved visual/audio) and source_manifest_context; readiness precedence unchanged"
  S5_D_requirement_construction:
    "05": "generic Agent-004 inventory labels ('Agent-004 approved new/reused asset') no longer used as the registry match label (a live REVIEW row carries exactly that name; if ever APPROVED it would have exact-matched all three NEW requirements — proven against live c4d54cf8 code)"
    unchanged: "07 resolution rules (only exact APPROVED/LOCKED matches resolve; TBDs never get invented IDs; REVIEW candidates never promoted)"
  TEST_node: "'TEST - Set Production Manifest ID' value c56cabc0 (historical, APPROVED, DO_NOT_USE) → '' so an accidental manual run blocks at 00"

  static_validation:
    byte_check: "all changed code in n8n == locally simulated files (4/4)"
    local_simulation: "real 670b201b manifest_json + live registry; 20 cases incl. missing/malformed/SQL-ish/uppercase ID, REVIEW row, nonexistent, id mismatch, 03 gate-bypass, audio-only-in-one-list, dropped audio TBD, audio without category, TBD without shots, REVIEW-only reuse, APPROVED mock row, generic-label collision — all as expected"

  free_validation:
    harness: "HARNESS — Agent-006 S5 Free Validation (no-write) — QvfBBHAVYCqAsbo1; 12 nodes byte-identical to 0c1c34b3 (00, 01, 02, 02B, 03, 04, 05, 06, 07, 08, 11, 12); 09/10/13/14 absent (in-memory no-op stand-ins); only credential Supabase 'Supabase account', getAll only; no HTTP/provider/sub-workflow nodes; callerPolicy none; unpublished"
    T-S5-1: {exec: 512, input: "670b201b", result: "PASS — exact UUID resolved, status APPROVED, gate TRUE, parse OK, manifest_json preserved identical (28 keys), 3 new / 3 reuse / 6 inventory / 10 unique TBD / 4 audio TBD / 29 shot plans, provenance ENG-016/017 + paid_generation_authorised false + recovery lineage carried; stopped before 04; 0 writes"}
    T-S5-2: {exec: 513, input: "ff5afc70 (REVIEW)", result: "PASS — 01 empty, gate FALSE, 02B BLOCKED (MANIFEST_NOT_APPROVED_OR_NOT_FOUND); nothing after the gate ran"}
    T-S5-3: {exec: 514, input: "00000000-0000-4000-8000-000000000000", result: "PASS — BLOCKED at 02B"}
    T-S5-3b: {exec: 515, input: "malformed \"670b201b' or status=REVIEW--\"", result: "PASS — fail closed at 00 (MALFORMED_PRODUCTION_MANIFEST_ID) before any DB read"}
    T-S5-3c: {exec: 516, input: "missing ''", result: "PASS — fail closed at 00 (MISSING_PRODUCTION_MANIFEST_ID) before any DB read"}
    T-S5-4: {exec: 517, result: "PASS — live registry 12 rows (APPROVED 3, REVIEW 9, LOCKED 0); in.(APPROVED,LOCKED) returned exactly SFX-LUMI-CLUE-CHIME, SFX-MIKKO-TRY-WHOOSH, SFX-WIN-SPARKLE-CHORD = independent IN over full read; 0 REVIEW rows; 4 identifiable mock rows (all REVIEW) excluded"}
    T-S5-5: {exec: 517, result: "PASS — 16 requirements: 3 APPROVED_REUSE resolved (Lumi clue chime→SFX-LUMI-CLUE-CHIME, Mikko TRY whoosh→SFX-MIKKO-TRY-WHOOSH, WIN sparkle chord→SFX-WIN-SPARKLE-CHORD); 3 NEW_REQUIRED → CREATE_NEW (TMP_EP005_BERRY_SMUDGE_OVERLAYS 21 shots, TMP_EP005_SOFT_CLOTH 28, TMP_EP005_HAND_MIRROR 29); 6 unresolved visual TBDs (Lumi, Mikko, environment, mirror glint, mirror reflection/compositing, completion-pop visual); 4 unresolved audio TBDs (AMBIENCE 20 shots, FOLEY_CLOTH 7, COMPLETION_SFX 1, FOLEY_TOUCH 1); 0 blocked; 0 canonical IDs on TBDs; expected readiness NEEDS_HUMAN_REVIEW"}
    T-S5-6: {exec: 518, fixture: "in-memory only: all 9 live REVIEW rows passed straight to 05; APPROVED SFX-WIN-SPARKLE-CHORD withheld and replaced by a REVIEW copy; APPROVED-status mock row aliased TMP_EP005_SOFT_CLOTH added", result: "PASS — 05 kept 2 governed rows, excluded 11 (10 STATUS_NOT_GOVERNED, 1 DEVELOPMENT_OR_MOCK); WIN sparkle chord → BLOCKED_MISSING_REUSE; Soft cloth stays CREATE_NEW; readiness BLOCKED"}
    db_after_tests: "asset_resolution_items 24 rows md5 ed7ba909… and production_readiness_manifests 4 rows md5 1a9bf5df… identical before/after; manifests b8efa78a…, shot plans 898343d1… (319), registry 9854a316…, asset_creation_jobs 11 / batches 3 unchanged"
    production_agent006_executions: 0
    agent007_executions: "none (last remains #455, 2026-09-24)"

paid_calls: 0   # zero OpenAI, Gemini, Runway calls; zero generation; zero credit/subscription/auto-renew/auto-reload/plan/spending-limit changes
production_agent006_writes: 0
not_done: ["Agent-006 not published, not run live against 670b201b", "Agent-005 not modified/published/executed", "Agent-007 not run", "S3-B not executed (legacy UNIQUE(episode_code, script_version_number) retained)", "no asset_registry rows created/changed/approved", "no historical manifest changed"]
open_items_for_humans:
  - "c56cabc0 remains status APPROVED. Agent-006's gate is status-based, so it would accept c56cabc0 if explicitly passed; operational DO_NOT_USE is not enforced in code. Options (human decision): leave as is and rely on exact-UUID discipline, or change c56cabc0 status (e.g. SUPERSEDED) in a separate authorised change."
  - "Expected live readiness for 670b201b is NEEDS_HUMAN_REVIEW: 10 TBD mappings (6 visual, 4 audio) need human decisions before Agent-007 could be authorised; the 3 NEW_REQUIRED props/overlays have REVIEW candidates from earlier Agent-007 batches that are not canonical."
  - "Audio TBD requirement_type is AUDIO, so same-type suggestions list the three SFX assets; suggestions never auto-resolve."
rollback_notes:
  - "Agent-006: restore version c4d54cf8-7e4b-4d6f-be60-e863080c541b via n8n version history (restore_workflow_version), or re-import s5_agent006/AGENT006_ZTBdnKFO8STSjJU4_BEFORE_c4d54cf8.json. Unpublished, so no production impact either way."
  - "G3 approval: UPDATE episode_production_manifests SET status='REVIEW' WHERE id='670b201b-6793-4518-ad5a-d051eb98d90c' AND status='APPROVED' (only with human authorisation; also reverts the Agent-005 baseline selection to c56cabc0, still video 15)."
  - "Harness QvfBBHAVYCqAsbo1: no-write; may be archived at any time."
status: "S5_AGENT006_CONFIGURED + STATIC_VALIDATION_PASSED + FREE_VALIDATION_PASSED + UNPUBLISHED"
```

---

## ENG-20260926-019: S5.1 controlled live Agent-006 proof on approved manifest 670b201b (single run, unpublished)

```yaml
change_id: "ENG-20260926-019"
date: "2026-09-26"
requested_by: "Gilang"
recorded_decisions:
  prior: "ENG-20260926-018 accepted; checkpoint S5_AGENT006_CONFIGURED + STATIC_VALIDATION_PASSED + FREE_VALIDATION_PASSED + UNPUBLISHED; G3 complete"
  authorisation: "exactly ONE controlled live Agent-006 execution against 670b201b-6793-4518-ad5a-d051eb98d90c; NOT Agent-007, generation, provider/model calls, asset approval, readiness approval or publication"

pre_run_drift_check:   # 2026-09-26T11:12:51Z; all passed, no drift
  agent006: "ZTBdnKFO8STSjJU4 draft 0c1c34b3-487e-4ecf-b9e6-62a0da558477 (only version); active false; activeVersionId null; nodes and connections byte-identical to the S5 export; TEST input blank; write nodes only 09 (insert asset_resolution_items) and 13 (insert production_readiness_manifests); no provider/LLM/HTTP/generation nodes"
  manifest_670b201b: "APPROVED; run A005O-1790400144423; script 14471926-…; 29/26/15/28; PLANNING_COMPLETE_WITH_TBDS [UNRESOLVED_TBDS]; production_optimization ENG-016/ENG-017, source ff5afc70, recovery RECORDED_MODEL_OUTPUT_REPLAY; paid_generation_authorised false; row md5 excl. status 0891c9e0… (unchanged since G3)"
  registry: "12 rows: APPROVED 3 (SFX-LUMI-CLUE-CHIME, SFX-MIKKO-TRY-WHOOSH, SFX-WIN-SPARKLE-CHORD), LOCKED 0, REVIEW 9; md5 9854a316…"

execution_method:
  limitation: "The n8n MCP execute tool passes inputs only to chat/form/webhook triggers, so it cannot feed Agent-006's 'When Executed by Another Workflow' trigger directly"
  method: "single-use caller 'CALLER — Agent-006 S5.1 controlled live run (single use)' puTvOUd0Ivuw1uw2 (2 nodes: manual trigger + Execute Workflow; mode once; wait true; input production_manifest_id = 670b201b-6793-4518-ad5a-d051eb98d90c; no credentials; callerPolicy none); archived after the run. Agent-006 itself not edited; TEST node not touched."
  finding_X9_resolved: "n8n on this instance DOES execute an unpublished sub-workflow's current draft via Execute Workflow (inventory X-9 was UNVERIFIED)"
execution:
  caller_exec: "519 (success, 11:13:39.829Z → 11:13:56.262Z)"
  agent006_exec: "520 (mode integrated, parent 519, success, 11:13:39.989Z → 11:13:56.149Z); single run, no retry"
  input_production_manifest_id: "670b201b-6793-4518-ad5a-d051eb98d90c"
  asset_resolution_run_id: "A006-1790421221809"
  production_readiness_manifest_id: "30b6046e-fe5e-46ab-9b9f-772fa6951efc"
  nodes_run: "trigger, 00, 01, 02 (TRUE), 03, 04, 05, 06×17, 07×16, 08×16, 09×16, 06B, 10, 11, 12, 13, 14; not run: TEST nodes, 02B"

result:
  resolution_records: 16
  status_breakdown: {REUSE_EXISTING: 3, CREATE_NEW: 3, NEEDS_HUMAN_REVIEW: 10, BLOCKED_MISSING_REUSE: 0, other: 0}
  canonical_asset_ids_assigned: ["SFX-LUMI-CLUE-CHIME (APPROVED)", "SFX-MIKKO-TRY-WHOOSH (APPROVED)", "SFX-WIN-SPARKLE-CHORD (APPROVED)"]
  review_registry_rows_selected: 0
  new_required: "TMP_EP005_BERRY_SMUDGE_OVERLAYS (21 shots), TMP_EP005_SOFT_CLOTH (28), TMP_EP005_HAND_MIRROR (29) → CREATE_NEW; REVIEW candidates not used"
  visual_tbd_unresolved: "Lumi, Mikko, environment, mirror glint, mirror reflection/compositing, completion-pop visual (6)"
  audio_tbd_unresolved: "AMBIENCE 20 shots, FOLEY_CLOTH 7, COMPLETION_SFX 1, FOLEY_TOUCH 1 (4)"
  canonical_ids_on_tbd: 0
  readiness: "NEEDS_HUMAN_REVIEW (computed, not forced; identical to S5 harness expectation, exec 517)"
  readiness_manifest: "status REVIEW; production_manifest_id 670b201b; requirement_count 16; dependency_breakdown preserved; canonical_reuse_map 3; source_manifest_context carries ENG-016/017, recovery lineage (from A005-1790328680362), paid_generation_authorised false, source status APPROVED, flags [UNRESOLVED_TBDS], workload 29/26/15/28; governance human_approval_required true"

db_audit:   # BEFORE 11:12:51Z → AFTER 11:14:39Z
  asset_resolution_items: "24 (ed7ba909…) → 40; pre-existing 24 rows md5 ed7ba909… unchanged; +16 rows only under A006-1790421221809 (md5 0aa1b243…)"
  production_readiness_manifests: "4 (1a9bf5df…) → 5; pre-existing 4 unchanged; +1 row 30b6046e… (md5 b7a07973…)"
  episode_production_manifests: "8, b8efa78a… → unchanged (APPROVED 2: 670b201b, c56cabc0; REVIEW 6)"
  shot_production_plans: "319, 898343d1… → unchanged"
  episode_scripts: "4, 9f51ef6f… → unchanged"
  asset_registry: "12, 9854a316… → unchanged (no status change)"
  asset_creation_jobs: "11, 8b022236… → unchanged"
  asset_creation_batches: "3, 1317c854… → unchanged"
  verdict: "only the authorised Agent-006 inserts occurred"

paid_calls: 0   # OpenAI 0, Gemini 0, Runway 0, image/video/audio generation 0 (no such node exists in Agent-006; node list verified from exec 520); no subscription/credit/billing/auto-reload/spending-limit change
agent006_published: false
agent007_run: false   # last Agent-007 execution remains #455 (2026-09-24)
decision_packet: "EP005_AGENT006_ASSET_DECISION_PACKET_v1.0.md (read-only)"

unexpected_findings:
  - "F-1: the 3 APPROVED SFX registry storage_path values (production-assets/audio/sfx/SFX-*-v01.mp3) do not match the stored objects (audio/sfx/SFX-LUMI-CLUE-CHIME-v01.wav.mp3, …-MIKKO-TRY-WHOOSH-v01.mp3.mp3, …-WIN-SPARKLE-CHORD-v01.mp3.mp3); downstream fetch by storage_path would fail"
  - "F-2: Agent-005 asset_inventory has used_in_shots [] for the 3 reuse assets, so Agent-006 records them with no shots; the approved script places them at S004 / S007 / S027"
  - "F-3: REVIEW candidate CAND-A007-1789527180412-PROP-TMP_EP005_HAND_MIRROR-A01 is inconsistent (its job f28609dc… PROVIDER_FAILED; it shares one storage object with A02, which overwrote it; its metadata provider_job_id is the soft-cloth task 2298c8c3…)"
  - "F-4: readiness manifest d124ba28-2dc5-4b86-8608-f363eeb3f8d2 (from historical c56cabc0) and test c0012923 are APPROVED + NEEDS_ASSET_CREATION, the state Agent-007 accepts; together with c56cabc0 APPROVED this is a legacy authorised path to paid generation outside the 670b201b lineage (recorded only; historical status governance is a separate decision)"
  - "F-5: Runway batch A007-1789527180412 candidates were briefed from the c56cabc0 plan; the berry-smudge candidate was generated with requested name 'Agent-004 approved new asset' (the generic-label defect fixed in S5-D)"
  - "X-9 resolved: an unpublished sub-workflow draft is executable via Execute Workflow on this instance"

rollback_containment:
  - "Nothing to roll back in workflows: Agent-006 unchanged (0c1c34b3, unpublished); caller puTvOUd0Ivuw1uw2 archived"
  - "The 16 asset_resolution_items rows (A006-1790421221809) and readiness manifest 30b6046e… are status REVIEW and inert; Agent-007 accepts only APPROVED + NEEDS_ASSET_CREATION, so 30b6046e cannot trigger generation"
  - "If rejected: leave the rows as REVIEW evidence (deletion not authorised); a later Agent-006 run creates a new run ID and does not conflict"
  - "Do not approve 30b6046e; human asset decisions first (see packet), then a fresh Agent-006 run"
not_done: ["no Agent-006 publish", "no Agent-007", "no readiness approval", "no asset/registry change", "no historical manifest change, no deny-list, no SUPERSEDED status", "no S3-B", "no Agent-005 change"]
status: "S5.1_AGENT006_CONTROLLED_LIVE_RUN_PASSED + READINESS_NEEDS_HUMAN_REVIEW + ASSET_DECISION_PACKET_CREATED + UNPUBLISHED"
```

---

## ENG-20260928-020: S5.2 SFX path correction, Agent-006 reuse-shot patch, candidate image export, governance proposals, S6 Agent-007 safety draft (unpublished, free only)

```yaml
change_id: "ENG-20260928-020"
date: "2026-09-28"
requested_by: "Gilang"
recorded_decisions:
  prior: "ENG-20260926-019 accepted; checkpoint S5.1_AGENT006_CONTROLLED_LIVE_RUN_PASSED + READINESS_NEEDS_HUMAN_REVIEW + ASSET_DECISION_PACKET_CREATED + UNPUBLISHED"
  lineage: "production manifest 670b201b-6793-4518-ad5a-d051eb98d90c → plan A005O-1790400144423 → Agent-006 run A006-1790421221809 → readiness 30b6046e-fe5e-46ab-9b9f-772fa6951efc (NEEDS_HUMAN_REVIEW, status REVIEW)"
  not_authorised: "approve 30b6046e; run Agent-007; trigger any paid provider; publish Agent-006/007; approve REVIEW candidates; S3-B; Agent-005 changes"

baselines:   # 2026-09-28T10:58:48Z
  asset_registry: "12, 9854a316ac7d9504409d530793749274 (other 9 rows 167a1f4d…)"
  storage_objects: "7, 1edbb2fa…"
  asset_resolution_items: "40, a7a0e611…"
  production_readiness_manifests: "5, 55ae0066…"
  episode_production_manifests: "8, b8efa78a…"
  shot_production_plans: "319, 898343d1…"
  episode_scripts: "4, 9f51ef6f…"
  asset_creation_jobs: "11, 8b022236…"
  asset_creation_batches: "3, 1317c854…"

part_A_sfx_storage_paths:   # only DB write in this change
  verification_before_change: "each target object found independently in storage.objects (bucket production-assets, single object per asset, audio/mpeg); each uploaded 2–3 min before its registry row was created; no ambiguity → all three corrected"
  rows:
    SFX-LUMI-CLUE-CHIME:   {old: "production-assets/audio/sfx/SFX-LUMI-CLUE-CHIME-v01.mp3",  new: "production-assets/audio/sfx/SFX-LUMI-CLUE-CHIME-v01.wav.mp3",  object: "15b28b51-700b-4cd4-852b-2d413d6f1aa5", bytes: 206753, row_md5_after: "7c8ba721…"}
    SFX-MIKKO-TRY-WHOOSH:  {old: "production-assets/audio/sfx/SFX-MIKKO-TRY-WHOOSH-v01.mp3", new: "production-assets/audio/sfx/SFX-MIKKO-TRY-WHOOSH-v01.mp3.mp3", object: "7e415397-5755-4e24-ae9f-279a1310c688", bytes: 341541, row_md5_after: "f14cffa5…"}
    SFX-WIN-SPARKLE-CHORD: {old: "production-assets/audio/sfx/SFX-WIN-SPARKLE-CHORD-v01.mp3", new: "production-assets/audio/sfx/SFX-WIN-SPARKLE-CHORD-v01.mp3.mp3", object: "a599d118-2eed-4ddf-9d17-a42888a55e25", bytes: 245215, row_md5_after: "fe6cbbeb…"}
  checksums: "registry 9854a316… → 779a9cd239e122ea81798263bdb65e12; other 9 rows 167a1f4d… unchanged"
  only_storage_path_changed_proof: "substituting the three old storage_path values back into the current table reproduces exactly 9854a316ac7d9504409d530793749274 (re-verified 28 Sep after S6)"
  untouched: "status, asset_id, asset_name, aliases, human approval, provider provenance, metadata, updated_at; storage objects not renamed/moved"
  rollback_sql: "update asset_registry set storage_path = <old> where asset_id = <id>  (three rows, values above)"

part_B_agent006_reuse_shot_attribution:
  workflow: "ZTBdnKFO8STSjJU4 draft 0c1c34b3 → 9bf6bbef-d49a-4f50-bce5-f8f146d43ca8; active false; activeVersionId null (unpublished)"
  change: "node 05 only: APPROVED_REUSE source_shot_ids derived from shot_plans[].shot_plan.audio_plan.named_audio_assets (normalised; shot_plan may be a JSON string); no hard-coded shots"
  rule: "inventory empty + plan shots → plan (MANIFEST_AUDIO_PLAN); both empty → [] (NONE); inventory only → INVENTORY; equal → INVENTORY_VALIDATED_AGAINST_AUDIO_PLAN; disagree → throw S5.2_REUSE_SHOT_ATTRIBUTION_CONFLICT (fail closed, no writes)"
  harness: "QvfBBHAVYCqAsbo1 (copies byte-identical to 9bf6bbef; no insert nodes; retained, not archived)"
  tests:
    R-S5-1: {exec: 521, result: "parse OK, 28 keys, provenance intact", pass: true}
    R-S5-2: {exec: 522, result: "ff5afc70 BLOCKED at 02B", pass: true}
    R-S5-3: {exec: 523, result: "nonexistent manifest BLOCKED", pass: true}
    R-S5-3b: {exec: 524, result: "malformed id fails at 00", pass: true}
    R-S5-3c: {exec: 525, result: "missing id fails at 00", pass: true}
    R-S5-4_5_T-S52-1: {exec: 526, result: "16 req 3/3/10/0, NEEDS_HUMAN_REVIEW; IN semantics; reuse shots S004 / S007 / S027", pass: true}
    R-S5-6: {exec: 527, result: "REVIEW-only WIN → BLOCKED_MISSING_REUSE; readiness BLOCKED; governed 2 / excluded 11", pass: true}
    T-S52-2: {exec: 528, result: "inventory S026 vs plan S027 → fails closed at 05", pass: true}
    T-S52-3: {exec: 529, result: "inventory agrees → preserved S027", pass: true}
  local_sim: "no placement → NONE; string shot_plan; case/space variants; all S5 regressions"
  production_executions: 0   # last Agent-006 execution remains #520

part_C_candidate_images:
  method: "read-only harness 4KxaLucJss5jLQoD exec 530: HTTP GET via existing n8n Supabase credential (no key exposed, no signed URL published); harness archived"
  files: "outputs/s52_visual_qc/: TMP_EP005_BERRY_SMUDGE_OVERLAYS.png, TMP_EP005_SOFT_CLOTH.png, TMP_EP005_HAND_MIRROR.png (A02), technical_inspection.json"
  berry_smudge_A01: "1,785,757 B; 1536×1024 RGBA; md5 = eTag 6a9c9f8b…; sha256 c0a87e8c…; alpha 76.66 % fully transparent, 0 % fully opaque (max 254), bbox (33,31)-(1454,1000)"
  soft_cloth_A01: "2,142,534 B; 1536×1024 RGB, NO alpha, near-white opaque background; md5 = eTag 0c44fa83…; sha256 2de223d7…"
  hand_mirror_A02: "921,192 B; 1312×1199 RGB, NO alpha, near-white opaque background; md5 = eTag c094da9d…; sha256 69679a84…"
  integrity: "all three: PNG signature OK, all chunk CRCs OK, full decode OK; chunks IHDR/IDAT/IEND + caBX (likely C2PA provenance)"
  observations_not_approval:
    - "berry smudge: three separable glowing gel-like smudges, soft halo, semi-transparent everywhere (no fully opaque pixel)"
    - "soft cloth: photoreal blue microfibre cloth on white; not transparent despite being a compositing PROP"
    - "hand mirror A02: stylised pink flower-frame toy mirror with heart; glass is painted/opaque (matters for reflection compositing)"
    - "A01 mirror excluded (invalid, F-3)"
  approvals: 0
  files_modified: 0

part_D_governance: "EP005_ASSET_GOVERNANCE_DECISIONS_v1.0.md: CREATE_CANONICAL_ASSET 6 (Lumi, Mikko, environment, AMBIENCE, FOLEY_CLOTH, COMPLETION_SFX), COMPOSITOR_ONLY_NO_ASSET 3 (glint, reflection/compositing, completion-pop visual), MAP_EXISTING 0, DEFER 1 (FOLEY_TOUCH); no identities created; no canonical Mikko/Lumi image exists in registry or source pack"
part_E_mechanism: "S52_HUMAN_RESOLUTION_MECHANISM_DESIGN_v0.1.md: append-only asset_requirement_decisions (+ current view, immutability/single-current triggers), Agent-006 03D read + deterministic 07/10 mapping (NO_ASSET_REQUIRED, DEFERRED new text values; no schema constraint change), companion paid_generation_authorisations; PROPOSAL ONLY, not applied"

part_F_agent007_s6:
  report: "S6_AGENT007_SAFETY_HARDENING_REPORT_v1.0.md"
  drift_check: "45c20c99 only version, published = draft, 70 nodes, updatedAt 2026-09-25T01:32:33Z → no drift"
  workflow: "hlwQHO8FEcn4gDXE draft 42ce4565-0d6d-4c4c-b492-bdf5c5777bcf (72 nodes); activeVersionId 45c20c99 unchanged; NOT published"
  changes: "00 (UUID required, no hard-coded manifest, caller authority fields ignored), 01A/01B removed, 01D id-equality, 02 requires manifest_found+SUPABASE, TEST Set Mock blank, 05A MAX_PAID_ATTEMPTS_PER_REQUIREMENT=1, new 07A0R/07A0/07A0B/07A0C paid gate (switch DISABLED, persisted authorisation null), edge 07A1[1]→07A3 removed"
  harness: "OfoGdHzLpg9n2675 (20 byte-identical copies; reads only; TRIPWIRE in place of 07A3); archived"
  tests: "T-S6-1..12 = execs 531–542, all pass (missing/malformed/nonexistent UUID; REVIEW 30b6046e; APPROVED+NEEDS_HUMAN_REVIEW; caller fake APPROVED; fully valid fixture stops at gate with 0 writes and tripwire not reached; attempt 2 blocked at 05A; active provider task → recovery, no gate/submit; canonical-exists reason; d124ba28 and c0012923 → no remaining jobs)"
  db_proof: "11:21:28Z vs 11:23:53Z identical: jobs 11/8b022236, batches 3/1317c854, registry 12/779a9cd2, readiness 5/55ae0066, ARI 40/a7a0e611, objects 7; no reservation or claim rows"
  findings: ["F-S6-1 node 10 merge-duplicates upsert can downgrade a human-APPROVED row to REVIEW", "F-S6-2 'When Executed by Another Workflow' has no outgoing edge in published and draft (pre-existing); not wired in S6", "F-S6-3 orphan 07B-MOCK and TEST fixtures (incl. hard-coded d124ba28), unreachable", "F-S6-4 resume path ungated by design (status poll, no submission); only active row is non-UUID test fixture d3106cf4, unreachable", "F-S6-5 01C APPROVED filter makes REVIEW manifests look 'not found'"]

part_G_legacy_manifests: "d124ba28 and c0012923 both APPROVED/NEEDS_ASSET_CREATION, unchanged (readiness table md5 55ae0066 unchanged); published 45c20c99 accepts them because 01C/02 check only status+state and 00 hard-codes c0012923; with S6 they are inert for paid generation (exact targeting only, 0 remaining jobs, gate closed); recommendation: keep as is + record as DO_NOT_USE_FOR_NEW_PAID_PRODUCTION; any status transition is a separate approval; SUPERSEDED not invented"

paid_calls: {openai: 0, gemini: 0, runway: 0, generation: 0}
billing_changes: 0
agent007_executions: 0   # last remains #455 (2026-09-24)
agent006_production_executions: 0   # last remains #520
supabase_writes: "3 asset_registry storage_path updates (Part A) only"
published: {agent006: false, agent007: false}

rollback:
  agent006: "restore_workflow_version 0c1c34b3 as draft (unpublished either way)"
  agent007: "restore_workflow_version 45c20c99 as draft; published version never changed"
  sfx_paths: "see part_A rollback_sql"
  harnesses: "4KxaLucJss5jLQoD and OfoGdHzLpg9n2675 archived; QvfBBHAVYCqAsbo1 retained"

status: "S5.2_SFX_PATHS_CORRECTED + AGENT006_REUSE_SHOTS_PATCHED_UNPUBLISHED + CANDIDATE_IMAGES_EXPORTED_FOR_HUMAN_QC + GOVERNANCE_AND_RESOLUTION_PROPOSALS_READY + S6_AGENT007_SAFETY_DRAFT_CONFIGURED + FREE_VALIDATION_PASSED + UNPUBLISHED"
```

---

## ENG-20260929-021: S6.1 Agent-007 canon-downgrade protection (RECONSTRUCTED RECORD)

```yaml
change_id: "ENG-20260929-021"
record_provenance: "RECONSTRUCTED by Company Brain on 2026-10-05; NOT a recovered original. Adopted as the authoritative durable record."
authoritative_source: "evidence/C1_EVIDENCE_GAP_REPAIR_AND_IMPLEMENTATION_SPEC_v1.0.md section 1 (sha256 9790ddc4fc9159d71bc289e79a7bcb1fd3488f26b5c3642802097f437aeadac0)"
change_type: "FIX"
target: "AGENT-007 hlwQHO8FEcn4gDXE"
result: "unpublished safety draft b135f8a5-7800-4169-b2f4-9cf3a7d5904d (76 nodes); published 45c20c99 unchanged; trigger disconnected; PAID_DISPATCH_SWITCH DISABLED; node-10 pre-read + insert-only ON CONFLICT DO NOTHING"
live_reconciliation_2026-10-05: "n8n reports versionId b135f8a5…, activeVersionId 45c20c99…, nodeCount 76: consistent"
paid_calls: 0
generation_calls: 0
publication: false
migrations: 0
```

---

## ENG-20260930-022: C1 first execution attempt stopped on hash mismatch (RECONSTRUCTED RECORD)

```yaml
change_id: "ENG-20260930-022"
record_provenance: "RECONSTRUCTED by Company Brain on 2026-10-05; NOT a recovered original. Adopted as the authoritative durable record."
authoritative_source: "evidence/C1_EVIDENCE_GAP_REPAIR_AND_IMPLEMENTATION_SPEC_v1.0.md section 2"
change_type: "C1_PRECHECK_STOP"
result: "STOPPED_HASH_MISMATCH: the expected SHA-256 values supplied then did not match the final image bytes"
writes: 0
paid_calls: 0
generation_calls: 0
governance_rule_reconfirmed: "Human visual approval -> save exact final file -> hash the saved file -> record that hash -> only then register/store canon."
distinct_from: "ENG-20261005-C1-PRECHECK (a later, separate pre-write stop on missing evidence)"
```

---

## ENG-20260930-023: C1 canon bytes re-approved (RECONSTRUCTED RECORD)

```yaml
change_id: "ENG-20260930-023"
record_provenance: "RECONSTRUCTED by Company Brain on 2026-10-05; NOT a recovered original. Adopted as the authoritative durable record."
authoritative_source: "evidence/C1_EVIDENCE_GAP_REPAIR_AND_IMPLEMENTATION_SPEC_v1.0.md section 3"
change_type: "C1_CANON_BYTES_REAPPROVAL"
approved_by: "Gilang"
state_after: "ACTUAL_CANON_BYTES_REAPPROVED + ZERO_WRITES"
authoritative_files:   # all four re-verified on 2026-10-05 against repo commit 5055f76: sha256, bytes, 1448x1086, RGB 8-bit, PNG CRCs OK
  CHAR-MIKKO-MASTER-v01: {path: "canon/c1/mikko_the_bear_character_master_sheet.png", sha256: "41c9480a847c962c1ecfda4fe076e0abcd86548ba67f692621cfc6e13d61f1a8", bytes: 2207008}
  CHAR-LUMI-MASTER-v01: {path: "canon/c1/lumi_character_master_sheet.png", sha256: "8b29c1abea53cb253eea39cdd41d5001ed38036945b049078915ac5993c43a41", bytes: 1887897}
  DUO-MIKKO-LUMI-SCALE-v01: {path: "canon/c1/mikko_lumi_duo_scale_sheet.png", sha256: "735d64075af999d8a00d35afe2674174f5e0feea9b1b4acb9ec2208f1e1d121f", bytes: 1704130}
  WORLD-EP005-BATHROOM-MASTER-v01: {path: "canon/c1/mikko_lumi_child_friendly_bathroom_board.png", sha256: "ab79c560d3c79a05cb957331149ee4b8a176e109b06010480ba6c26903bd3733", bytes: 1756516}
superseded_hashes: ["70a88421…", "8bf26e70…", "245d6453…", "3c64daed…"]
filename_clarification: "Company Brain labels (Mikko Master, Lumi Master, Duo Scale, Bathroom master) name logical roles only; the only authoritative bytes are the four canon/c1/ files above."
writes: 0
paid_calls: 0
generation_calls: 0
```

---

## ENG-20261005-C1-PRECHECK: C1 canon registration, pre-write reconciliation (STOPPED_PRE_WRITE)

```yaml
change_id: "ENG-20261005-C1-PRECHECK"   # deliberately not numbered -022/-023: those IDs are referenced by the instruction but absent from this changelog
timestamp: "2026-10-05"
actor: "Claude"
requested_by: "Gilang"
target: "Supabase ziluiwrwwbayhcskeere (production-assets, public.asset_registry); n8n Agent-006 ZTBdnKFO8STSjJU4 (read-only)"
change_type: "READ_ONLY_RECONCILIATION"
evidence: "evidence/C1_CANON_REGISTRATION_PRECHECK_STOPPED_v1.0.md"
result: "STOPPED_PRE_WRITE: RECORDED_EVIDENCE_MISSING"
blocking_conflicts:
  C-1: "ENG-20260930-022 and ENG-20260930-023 absent from the repo; this changelog ended at ENG-20260928-020"
  C-2: "ENG-20260929-021 referenced by company-brain docs but absent from this changelog"
  C-3: "canon byte re-approval not recorded; hashes come only from CLAUDE.md; VA_03 section 9 names different exact files"
  C-4: "no recorded C1 bucket/object keys, row fields, aliases, provenance fields or duo-sheet storage rule"
local_hashes: "4/4 match CLAUDE.md (mikko 41c9480a…, lumi 8b29c1ab…, duo 735d6407…, bathroom ab79c560…)"
live_state: "registry 12 (APPROVED 3 SFX, REVIEW 9); objects 7 in production-assets; readiness 5; ARI 40; jobs 11; batches 3; migrations 1; Agent-006 9bf6bbef unpublished; Agent-007 draft b135f8a5 / published 45c20c99: matches recorded state"
alias_check: "TBD::CHARACTER::Mikko, TBD::CHARACTER::Lumi, TBD::ENVIRONMENT::Canonical environment/background each have 0 exact APPROVED/LOCKED matches today; no duplicate-match conflict; planned C1 asset_ids unused"
supabase_writes: 0
n8n_writes: 0
paid_calls: {openai: 0, gemini: 0, runway: 0, generation: 0}
agent006_executions: 0
agent007_executions: 0
readiness_approvals: 0
migrations: 0
rollback: "not applicable"
status: "STOPPED_PRE_WRITE + ZERO_WRITES"
next_human_decision: "Provide ENG-20260929-021/-20260930-022/-20260930-023 evidence and the exact approved C1 write specification (object keys, row fields, aliases, duo-sheet handling), then re-authorise C1."
```

---

## ENG-20261005-C1-SPEC-RECONCILE: C1 evidence gap repaired + implementation spec reconciled

```yaml
change_id: "ENG-20261005-C1-SPEC-RECONCILE"
timestamp: "2026-10-05"
actor: "Claude"
requested_by: "Gilang / Company Brain"
added: "evidence/C1_EVIDENCE_GAP_REPAIR_AND_IMPLEMENTATION_SPEC_v1.0.md (sha256 9790ddc4fc9159d71bc289e79a7bcb1fd3488f26b5c3642802097f437aeadac0)"
gap_closed: "ENG-20260929-021, ENG-20260930-022, ENG-20260930-023 now present above as RECONSTRUCTED records"
resolves_precheck_conflicts: {C-1: "closed (-022/-023 recorded)", C-2: "closed (-021 recorded)", C-3: "closed (-023 re-approval + filename clarification)", C-4: "closed (spec section 4: bucket, object keys, rows, aliases, duo handling)"}
reconciliation:
  main: "source_repo_commit 5055f760 in spec = main source-pack commit; canon/c1 bytes match spec sha256/bytes/1448x1086/RGB"
  live_supabase: "bucket production-assets exists (private); 0 objects under visual/canonical/; 0 rows with the 4 target asset_ids; 0 registry tokens (asset_id/asset_name/aliases, Agent-006 normalisation) equal to any intended name/alias; registry 12 rows, objects 7, unchanged since 2026-09-24"
  agent006_draft: "live ZTBdnKFO8STSjJU4 = 9bf6bbef (unpublished) = repo export; matcher uses normalised asset_id/asset_name/aliases of APPROVED/LOCKED non-mock rows; spec rows are non-mock (no TEST_/MOCK_ prefix, no mock:// path)"
  material_conflicts: 0
writes: 0
```

---

## ENG-20261005-C1-UPLOAD-BLOCKED: C1 stopped before storage write (no storage write credential)

```yaml
change_id: "ENG-20261005-C1-UPLOAD-BLOCKED"
timestamp: "2026-10-05"
actor: "Claude"
spec: "evidence/C1_EVIDENCE_GAP_REPAIR_AND_IMPLEMENTATION_SPEC_v1.0.md"
result: "STOPPED_PRE_WRITE: NO_STORAGE_WRITE_PATH"
completed: ["spec reconciled (0 material conflicts)", "local hashes re-verified", "live pre-write checks clean (target keys absent, target asset_ids absent, 0 name/alias collisions)"]
blocker: >
  The engineering environment has no Supabase credential able to write to or read back from the private
  bucket production-assets (no service-role or storage S3 key in the environment; storage.objects has no
  RLS policies; the Supabase MCP has SQL only and no storage upload/download). Spec 4.1 requires a
  no-overwrite upload plus SHA-256 readback BEFORE any registry insert, so neither storage nor registry
  writes were attempted. Inserting storage.objects rows by SQL would not store bytes and was not done.
options_for_human:
  A: "Add a Supabase service-role key to the cloud environment as SUPABASE_SERVICE_ROLE_KEY and start a new session; C1 then resumes from spec 4.1 unchanged."
  B: "Explicitly authorise a single-use, read-back-capable n8n uploader harness using the existing n8n Supabase credential (archived after one run); this is an n8n write outside the current C1 scope."
supabase_writes: 0
n8n_writes: 0
paid_calls: 0
generation_calls: 0
agent006_executions: 0
agent007_executions: 0
migrations: 0
status: "C1_SPEC_RECONCILED + EVIDENCE_GAP_REPAIRED + STOPPED_PRE_WRITE + ZERO_WRITES"
```

---

## ENG-20261005-C1-CRED-REJECTED: C1 resume stopped before write (Supabase credential rejected)

```yaml
change_id: "ENG-20261005-C1-CRED-REJECTED"
timestamp: "2026-10-05"
actor: "Claude"
requested_by: "Gilang / Company Brain"
spec: "evidence/C1_EVIDENCE_GAP_REPAIR_AND_IMPLEMENTATION_SPEC_v1.0.md"
evidence: "evidence/C1_RESUME_STOPPED_CREDENTIAL_REJECTED_v1.0.md"
result: "STOPPED_PRE_WRITE: SUPABASE_CREDENTIAL_REJECTED"
preconditions: "main contains 3a7bbb5 + 57ab83c; canon/c1 4/4 sha256 + bytes match spec"
blocker: >
  Proxy-injected SUPABASE_SERVICE_ROLE_KEY is rejected: Storage returns 'Invalid Compact JWS' (bearer is not a JWT)
  and PostgREST returns 'No API key found' (no apikey header injected). No list/upload/readback path to
  production-assets, so spec 4.1 cannot run and registry inserts must not precede it. Secret value never printed or committed.
live_drift: "none: registry 12 (APPROVED 3 / REVIEW 9 / LOCKED 0), target ids 0, alias/name collisions 0, objects 7 (0 under visual/canonical/), readiness 5, ARI 40, jobs 11, batches 3, migrations 1, Agent-006 9bf6bbef unpublished"
resume_requirement: "environment secret replaced with the legacy JWT service_role key, or injection also sets the apikey header; new session; resume at spec 4.1"
supabase_writes: 0
n8n_writes: 0
paid_calls: 0
generation_calls: 0
agent006_executions: 0
agent007_executions: 0
readiness_approvals: 0
migrations: 0
rollback: "not applicable"
status: "STOPPED_PRE_WRITE + ZERO_WRITES"
```

---

## ENG-20261005-C1-COMPLETE: C1 visual canon stored, hash-verified, registered; Agent-006 match proven read-only

```yaml
change_id: "ENG-20261005-C1-COMPLETE"
timestamp: "2026-10-05"
actor: "Claude"
requested_by: "Gilang / Company Brain"
spec: "evidence/C1_EVIDENCE_GAP_REPAIR_AND_IMPLEMENTATION_SPEC_v1.0.md"
evidence: "evidence/C1_VISUAL_CANON_STORED_AND_REGISTERED_v1.0.md"
preconditions: "main contains e7ebdf8; canon/c1 4/4 sha256 + bytes match spec"
credential_tests: {storage_list_production_assets: 200, rest_read_asset_registry: 200}
live_drift: "none (registry 12, objects 7, 0 under visual/canonical/, target keys/ids absent, 0 collisions, readiness 5 / ARI 40 / jobs 11 / batches 3, migrations 1, Agent-006 9bf6bbef unpublished)"
storage_writes:   # bucket production-assets, x-upsert false, readback sha256 verified
  - {key: "visual/canonical/characters/CHAR-MIKKO-MASTER-v01.png", id: "06b16cf9-cff5-44a7-9ba7-43d707ea428f", sha256: "41c9480a…f1a8", bytes: 2207008}
  - {key: "visual/canonical/characters/CHAR-LUMI-MASTER-v01.png", id: "8b729cf0-d22c-47e0-a986-f55072760641", sha256: "8b29c1ab…3a41", bytes: 1887897}
  - {key: "visual/canonical/references/DUO-MIKKO-LUMI-SCALE-v01.png", id: "9d5c8dd7-6684-48f4-9c4d-8fcfdd9d9486", sha256: "735d6407…121f", bytes: 1704130}
  - {key: "visual/canonical/worlds/WORLD-EP005-BATHROOM-MASTER-v01.png", id: "f45a29b6-b297-42db-bef4-848b0205542a", sha256: "ab79c560…3733", bytes: 1756516}
registry_inserts:   # plain insert, status APPROVED, exact spec 4.2 JSON
  - {asset_id: "CHAR-MIKKO-MASTER-v01", id: "0d7a47e0-0adf-47d6-9cf9-f71ad7439747"}
  - {asset_id: "CHAR-LUMI-MASTER-v01", id: "75cf9e5d-78ec-4cac-b1bb-49e696629bc2"}
  - {asset_id: "WORLD-EP005-BATHROOM-MASTER-v01", id: "8cdeea80-1eb3-4a75-b50a-c209f1aae434"}
duo: "stored + hash-verified; no asset_registry row (DUO_REFERENCE_STORED_NOT_REGISTRY_MAPPED)"
prior_rows_unchanged: "12/12 field-identical to pre-write snapshot"
agent006_readonly_proof: "unmodified 03/05/07 jsCode of 9bf6bbef run locally vs live APPROVED manifest 670b201b + APPROVED/LOCKED registry (GET only): Mikko -> CHAR-MIKKO-MASTER-v01, Lumi -> CHAR-LUMI-MASTER-v01, Canonical environment/background -> WORLD-EP005-BATHROOM-MASTER-v01; each exactly 1 exact match, REUSE_EXISTING"
n8n_writes: 0
paid_calls: 0
generation_calls: 0
agent006_executions: 0
agent007_executions: 0
readiness_approvals: 0
migrations: 0
rollback: "delete the 3 asset_registry ids above; delete the 4 storage keys above"
status: "C1_VISUAL_CANON_DURABLY_STORED + STORED_BYTES_HASH_VERIFIED + MIKKO_APPROVED_REGISTERED + LUMI_APPROVED_REGISTERED + EP005_BATHROOM_APPROVED_REGISTERED + DUO_REFERENCE_STORED_NOT_REGISTRY_MAPPED + AGENT006_MATCH_READINESS_PROVEN_READ_ONLY + EVIDENCE_COMMITTED_TO_GITHUB"
```

---

## ENG-20261005-EP005-PACK-PREINGEST-STOP: EP005 working pack, first authorisation stopped before write (cheek alias conflict)

```yaml
change_id: "ENG-20261005-EP005-PACK-PREINGEST-STOP"
timestamp: "2026-10-05"
actor: "Claude"
result: "STOPPED_PRE_WRITE: CHEEK_ALIAS_RESOLVES_COMBINED_BERRY_REQUIREMENT"
detail: "approved cheek alias \"Berry smudge on Mikko's anatomical left cheek\" == primary source_label of APPROVED_NEW::TMP_EP005_BERRY_SMUDGE_OVERLAYS; in-memory Agent-006 sim resolved it REUSE_EXISTING -> CHEEK, contradicting the 'leave unresolved' decision"
resolution: "Company Brain Option 1: cheek aliases = []"
writes: 0
```

---

## ENG-20261005-EP005-WORKING-VISUAL-PACK-APPROVED: EP005 five working production assets stored, hash-verified, registered

```yaml
change_id: "ENG-20261005-EP005-WORKING-VISUAL-PACK-APPROVED"
timestamp: "2026-10-05"
actor: "Claude"
approved_by: "Gilang / Company Brain"
evidence: "evidence/EP005_WORKING_VISUAL_PACK_INGESTED_v1.0.md"
rows_json: "evidence/ep005/EP005_WORKING_VISUAL_PACK_REGISTRY_ROWS_v1.0.json"
scope: "approved EP005 working production assets (not core canon); exact session WebP bytes accepted as authoritative"
storage_writes:   # production-assets, x-upsert false, readback sha256 verified 5/5
  - {key: "visual/production/ep005/props/PROP-EP005-HAND-MIRROR-v01.webp", id: "e5ef12f3-baea-4cf8-9ce9-46d1a917abb0", sha256: "34fa31a1…56ac", bytes: 47670}
  - {key: "visual/production/ep005/props/PROP-EP005-CLEANING-CLOTH-v01.webp", id: "80744e45-d904-4086-9069-e010b17187bb", sha256: "afaa3a9f…c1db", bytes: 237724}
  - {key: "visual/production/ep005/overlays/OVERLAY-EP005-BERRY-SMUDGE-CHEEK-v01.webp", id: "48a1acf0-b020-4cbd-b003-2a614d753c03", sha256: "b2c735f2…78ac", bytes: 257966}
  - {key: "visual/production/ep005/overlays/OVERLAY-EP005-BERRY-SMUDGE-MOUTH-v01.webp", id: "de46e075-fc63-46ac-a10a-3ad501e829cb", sha256: "df7c2adb…7b0e", bytes: 294014}
  - {key: "visual/production/ep005/overlays/OVERLAY-EP005-BERRY-SMUDGE-NOSE-v01.webp", id: "e595212b-ca24-44ac-8069-68c40583b088", sha256: "c1169127…0bc1", bytes: 285032}
registry_inserts:   # plain insert, APPROVED
  - {asset_id: "PROP-EP005-HAND-MIRROR-v01", id: "a61c0af2-1e8d-40e2-88d1-8848390f2a17", aliases: ["TMP_EP005_HAND_MIRROR", "Tiny hand mirror"]}
  - {asset_id: "PROP-EP005-CLEANING-CLOTH-v01", id: "ab33c77c-5fde-4642-9efb-706f619c4a7e", aliases: ["TMP_EP005_SOFT_CLOTH", "Soft cloth"]}
  - {asset_id: "OVERLAY-EP005-BERRY-SMUDGE-CHEEK-v01", id: "e2fc6426-bf97-437e-9515-d86419a0498a", aliases: []}
  - {asset_id: "OVERLAY-EP005-BERRY-SMUDGE-MOUTH-v01", id: "b960c11c-6b88-4223-854b-e9ba44c7aad4", aliases: ["Berry smudge on skin beside Mikko's mouth"]}
  - {asset_id: "OVERLAY-EP005-BERRY-SMUDGE-NOSE-v01", id: "dfaa3b89-8366-44dc-ace9-542b4a764a80", aliases: ["Berry smudge on Mikko's nose"]}
tmp_berry_alias_assigned: false
synthetic_set_row: false
prior_rows_unchanged: "15/15 field-identical (incl. 3 C1 rows); C1 storage objects untouched"
agent006_readonly_proof: "unmodified 03/05/07 of 9bf6bbef vs live manifest 670b201b + APPROVED/LOCKED registry: mirror REUSE_EXISTING, cloth REUSE_EXISTING, combined berry CREATE_NEW (intentional), Mikko/Lumi/environment unchanged REUSE_EXISTING"
open_followup: "separate bounded task: repair combined berry requirement structure"
n8n_writes: 0
paid_calls: 0
generation_calls: 0
agent006_executions: 0
agent007_executions: 0
readiness_approvals: 0
migrations: 0
rollback: "delete the 5 asset_registry ids above; delete the 5 storage keys above"
status: "EP005_FIVE_WORKING_PRODUCTION_ASSETS_STORED + FIVE_STORED_BYTES_HASH_VERIFIED + 5_APPROVED_REGISTERED + MIRROR_MATCH_READY + CLOTH_MATCH_READY + BERRY_COMBINED_REQUIREMENT_INTENTIONALLY_UNRESOLVED + C1_CANON_UNCHANGED + EVIDENCE_COMMITTED_TO_GITHUB"
```

---

## ENG-20261005-EP005-BERRY-SPLIT-DERIVED-MANIFEST: derived EP005 manifest with berry requirement split 3 ways (REVIEW)

```yaml
change_id: "ENG-20261005-EP005-BERRY-SPLIT-DERIVED-MANIFEST"
timestamp: "2026-10-05"
actor: "Claude"
approved_by: "Gilang / Company Brain (berry requirement repair design)"
evidence: "evidence/EP005_BERRY_DERIVED_MANIFEST_CREATED_REVIEW_v1.0.md"
transform: "evidence/ep005/berry_split/ep005_berry_requirement_split_v1.py (deterministic, no LLM)"
origin: "Agent-004 single shot asset_id -> TMP_EP005_BERRY_SMUDGE_OVERLAYS (script 14471926) -> Agent-005 node 12 groups by asset_id -> Agent-006 node 05 one APPROVED_NEW requirement"
source_manifest: {id: "670b201b-6793-4518-ad5a-d051eb98d90c", status: "APPROVED", unchanged: true, row_md5: "249adbfe4a9ddbc6c75446994979fe0d", manifest_md5: "da69805527dae414efb5d1823c0b7a97"}
derived_manifest: {id: "3bcde9ee-6676-480f-90da-5695b64532a7", status: "REVIEW", production_plan_run_id: "DRV-EP005-BERRY-SPLIT-1-A005O-1790400144423", unique_new_asset_count: 5, manifest_sha256_canonical: "3b855d95b7fc5bbffabbac22bbdebc2c4e702cf113b52192591f7602bb3fd0ec", readback: "21/21 fields exact"}
split:
  - {requirement_key: "APPROVED_NEW::OVERLAY-EP005-BERRY-SMUDGE-CHEEK-v01", label: "Berry smudge on Mikko's anatomical left cheek", shots: "S001-S009", removal: "S009"}
  - {requirement_key: "APPROVED_NEW::OVERLAY-EP005-BERRY-SMUDGE-MOUTH-v01", label: "Berry smudge on skin beside Mikko's mouth", shots: "S001-S015", removal: "S015"}
  - {requirement_key: "APPROVED_NEW::OVERLAY-EP005-BERRY-SMUDGE-NOSE-v01", label: "Berry smudge on Mikko's nose", shots: "S001-S021", removal: "S021"}
overlay_entries: "10 retagged, 17 generic expanded to 34, 1 continuity gap fill (S013 nose); legacy free-text notes unchanged"
inmemory_agent006_proof: "18 requirements (was 16); cheek/mouth/nose each exactly 1 match -> REUSE_EXISTING; mirror, cloth, 3 audio, Mikko, Lumi, environment unchanged REUSE_EXISTING; 7 TBDs unchanged NEEDS_HUMAN_REVIEW; 15 non-berry requirements field-identical to baseline; NC1 REVIEW gate blocks, NC2 no overlay rows -> CREATE_NEW, NC3 duplicate -> NEEDS_HUMAN_REVIEW"
supabase_writes: "1 insert (episode_production_manifests)"
registry_changes: 0
workflow_code_changes: 0
agent006_executions: 0
agent007_executions: 0
manifest_approvals: 0
readiness_approvals: 0
paid_calls: 0
migrations: 0
rollback: "delete episode_production_manifests id 3bcde9ee-6676-480f-90da-5695b64532a7"
next: "separate human G3 approval of 3bcde9ee; Agent-006 run only under separate authorisation"
status: "EP005_BERRY_DERIVED_MANIFEST_CREATED_REVIEW + SOURCE_MANIFEST_670B201B_UNCHANGED + BERRY_REQUIREMENTS_SPLIT_3_WAYS + S013_NOSE_ENTRY_ADDED_FROM_CONTINUITY + DERIVED_REQUIREMENT_COUNT_18 + IN_MEMORY_AGENT006_MATCH_PROOF_PASS + EVIDENCE_COMMITTED_TO_GITHUB"
```

---

## ENG-20261005-EP005-BERRY-DERIVED-MANIFEST-HUMAN-APPROVED: human manifest approval of derived EP005 manifest 3bcde9ee

```yaml
change_id: "ENG-20261005-EP005-BERRY-DERIVED-MANIFEST-HUMAN-APPROVED"
timestamp: "2026-10-05T06:11:59Z"
actor: "Claude (applying recorded human decision)"
approved_by: "Gilang (recorded by Company Brain)"
evidence: "evidence/EP005_BERRY_DERIVED_MANIFEST_HUMAN_APPROVED_v1.0.md"
approval_scope: "manifest approval only, for EP005 asset-resolution use, covering the evidenced berry split (cheek S001-S009/S009, mouth S001-S015/S015, nose S001-S021/S021, derived S013 nose entry). NOT readiness, generation, spend, Agent-006/007 execution or publication approval."
pre_write: "3bcde9ee REVIEW; manifest sha256 3b855d95…0ec = evidence; 21/21 fields = transform; source 670b201b APPROVED, md5 249adbfe…/da698055… unchanged; registry 20 rows md5 b7b46112…; EP005 objects 048d2985…; C1 objects 7a4ac73d…; Agent-006 9bf6bbef unpublished"
write: "UPDATE episode_production_manifests SET status='APPROVED' WHERE id='3bcde9ee-6676-480f-90da-5695b64532a7' AND status='REVIEW'  -- 1 row (existing G3 mechanism, as ENG-20260926-018)"
post_write: "only status changed (md5 excluding status caafdbd5… before = after); all other fingerprints unchanged; APPROVED manifests 2 -> 3"
inmemory_check: "real APPROVED status passes node 03 gate; 18 requirements identical to evidenced sim; cheek/mouth/nose REUSE_EXISTING"
consequence: "Agent-005 cost baseline for backlog 07d622e9 now selects 3bcde9ee (video 15, same as 670b201b); no financial change"
agent006_executions: 0
agent007_executions: 0
readiness_approvals: 0
registry_changes: 0
storage_changes: 0
paid_calls: 0
migrations: 0
rollback: "UPDATE episode_production_manifests SET status='REVIEW' WHERE id='3bcde9ee-6676-480f-90da-5695b64532a7' AND status='APPROVED'"
status: "EP005_BERRY_DERIVED_MANIFEST_HUMAN_APPROVED + DERIVED_MANIFEST_3BCDE9EE_APPROVED + SOURCE_MANIFEST_670B201B_UNCHANGED + C1_CANON_UNCHANGED + EVIDENCE_COMMITTED_TO_GITHUB"
```

---

## ENG-20261005-EP005-AGENT006-DERIVED-LIVE-RUN: one controlled Agent-006 run on derived EP005 manifest 3bcde9ee

```yaml
change_id: "ENG-20261005-EP005-AGENT006-DERIVED-LIVE-RUN"
timestamp: "2026-10-05T06:18:16Z"
actor: "Claude"
authorised_by: "Company Brain (exactly one Agent-006 run against 3bcde9ee)"
evidence: "evidence/EP005_AGENT006_DERIVED_MANIFEST_LIVE_RUN_v1.0.md"
pre_run: "3bcde9ee APPROVED (row md5 931d64df…); 670b201b unchanged (249adbfe…); registry 20 (b7b46112…), 11 governed, 0 duplicate tokens; Agent-006 9bf6bbef unpublished, no provider/HTTP nodes"
method: "existing single-use caller pattern (ENG-20260926-019): AQ4JEKWd0cQOUmJV (Manual Trigger + Execute Workflow, input production_manifest_id only, no credentials), archived after the run"
execution: {caller: "576 success", agent006: "577 integrated success 06:18:16.155Z-06:18:39.072Z", asset_resolution_run_id: "A006-1791181098027", readiness_manifest: "e32ef7eb-448d-4da8-8271-fabf51bdc81e REVIEW / NEEDS_HUMAN_REVIEW"}
result: "18 requirements: 11 REUSE_EXISTING with exactly 1 match each (cheek, mouth, nose overlays; mirror; cloth; Mikko; Lumi; bathroom; 3 SFX); 7 NEEDS_HUMAN_REVIEW (3 visual + 4 audio TBDs, 0 matches); 0 ambiguous, 0 CREATE_NEW, 0 BLOCKED; 18/18 identical to the in-memory proof"
db_audit: "ARI 40->58 (prior 40 md5 feb133cc… unchanged, +18 under A006-1791181098027); readiness 5->6 (prior md5 9338a06f… unchanged, +e32ef7eb); manifests, registry, storage, jobs, batches, shot plans, scripts, migrations unchanged"
agent007_executions: 0
readiness_approvals: 0
generation_calls: 0
paid_calls: 0
workflow_changes: 0
registry_changes: 0
storage_changes: 0
migrations: 0
containment: "run records REVIEW and inert; Agent-007 accepts only APPROVED + NEEDS_ASSET_CREATION; no deletion authorised"
open_items: ["3 visual + 4 audio TBD human asset decisions", "readiness approval of e32ef7eb (human)", "F-1 SFX storage_path mismatch (ENG-20260926-019)"]
status: "EP005_AGENT006_DERIVED_MANIFEST_LIVE_RESOLUTION_PASS + REQUIREMENT_COUNT_18 + 11_REUSE_EXISTING + TRUE_TBDS_REMAIN_HUMAN_REVIEW + ZERO_AMBIGUOUS_MATCHES + ZERO_AGENT007_RUN + EVIDENCE_COMMITTED_TO_GITHUB"
```

---

## ENG-20261005-EP005-TBD-CLEANUP-DERIVED-MANIFEST: second derived EP005 manifest applying remaining-TBD human decisions (REVIEW) + F-1 erratum

```yaml
change_id: "ENG-20261005-EP005-TBD-CLEANUP-DERIVED-MANIFEST"
timestamp: "2026-10-05T06:47:46Z"
actor: "Claude"
human_decisions_by: "Gilang (recorded by Company Brain)"
evidence: "evidence/EP005_TBD_CLEANUP_DERIVED_MANIFEST_CREATED_REVIEW_v1.0.md"
transform: "evidence/ep005/tbd_cleanup/ep005_tbd_cleanup_v1.py (deterministic, no LLM)"
source_manifest: {id: "3bcde9ee-6676-480f-90da-5695b64532a7", status: "APPROVED", unchanged: true, row_md5: "931d64dfaca0b235ea70ea698cef7eea"}
derived_manifest: {id: "96df250f-7182-4d5f-a556-b0448e518375", status: "REVIEW", production_plan_run_id: "DRV-EP005-TBD-CLEANUP-1-A005O-1790400144423", manifest_sha256_canonical: "833bf0aab4f28f64bd5db72c129896811cc80705e1e9becbf6b9db123eb2422e", readback: "21/21 fields exact"}
decisions_applied:
  compositing_treatments: ["TREATMENT-EP005-MIRROR-GLINT-v01 (S004,S012,S018)", "TREATMENT-EP005-MIRROR-REFLECTION-v01 (S006,S007,S010,S011,S014,S025)", "TREATMENT-EP005-COMPLETION-POP-ACCENT-v01 (S025, KEEP)"]
  dropped: "TBD::AUDIO::FOLEY_TOUCH (S028 visual pat unchanged)"
  unresolved_audio_remaining: ["AMBIENCE", "FOLEY_CLOTH", "COMPLETION_SFX"]
counts: "visual TBD deps 6->3 (C1-resolving only), audio 4->3, unique 10->6, audio refs 29->28, unresolved refs 97->87"
inmemory_agent006_proof: "14 requirements: 11 REUSE_EXISTING identical to live run A006-1791181098027; 3 audio NEEDS_HUMAN_REVIEW; no OVERLAY_VFX or FOLEY_TOUCH requirement; 0 CREATE_NEW; REVIEW status blocked at node 03"
f1_erratum: "appended to evidence/EP005_AGENT006_DERIVED_MANIFEST_LIVE_RUN_v1.0.md: F-1 was already repaired under ENG-20260928-020 Part A; the 'open' note in ENG-20261005-EP005-AGENT006-DERIVED-LIVE-RUN was stale; SFX paths not modified"
supabase_writes: "1 insert (episode_production_manifests)"
registry_changes: 0
storage_changes: 0
workflow_changes: 0
agent006_executions: 0
agent007_executions: 0
manifest_approvals: 0
readiness_approvals: 0
paid_calls: 0
migrations: 0
rollback: "delete episode_production_manifests id 96df250f-7182-4d5f-a556-b0448e518375"
next: "human approval of 96df250f; audio sourcing/approval/registration for AMBIENCE, FOLEY_CLOTH, COMPLETION_SFX under separate authorisation"
status: "EP005_TBD_CLEANUP_DERIVED_MANIFEST_CREATED_REVIEW + THREE_VISUAL_TBDS_RECLASSIFIED_AS_COMPOSITING + FOLEY_TOUCH_DROPPED + THREE_AUDIO_TBDS_REMAIN + EXPECTED_REQUIREMENT_COUNT_14 + ELEVEN_REUSE_EXISTING_PRESERVED + F1_EVIDENCE_ERRATUM_ADDED + SOURCE_MANIFESTS_UNCHANGED + EVIDENCE_COMMITTED_TO_GITHUB"
```

---

## ENG-20261005-EP005-TBD-CLEANUP-MANIFEST-HUMAN-APPROVED: human manifest approval of derived EP005 manifest 96df250f

```yaml
change_id: "ENG-20261005-EP005-TBD-CLEANUP-MANIFEST-HUMAN-APPROVED"
timestamp: "2026-10-05T06:52:28Z"
actor: "Claude (applying recorded human decision)"
approved_by: "Gilang (recorded by Company Brain)"
evidence: "evidence/EP005_TBD_CLEANUP_DERIVED_MANIFEST_HUMAN_APPROVED_v1.0.md"
approval_scope: "manifest approval only: 3 visual TBDs as compositing treatments, FOLEY_TOUCH dropped, AMBIENCE/FOLEY_CLOTH/COMPLETION_SFX unresolved, 11 reusable requirements unchanged. NOT readiness, execution, generation, spend or publication approval."
pre_write: "96df250f REVIEW; manifest sha256 833bf0aa…422e = evidence; 21/21 fields = transform; 3bcde9ee 931d64df…, 670b201b 249adbfe… unchanged; registry b7b46112… (20); storage 4c7ef85e…; C1 rows 950ab724… / objects 7a4ac73d…; Agent-006 9bf6bbef unpublished"
write: "UPDATE episode_production_manifests SET status='APPROVED' WHERE id='96df250f-7182-4d5f-a556-b0448e518375' AND status='REVIEW'  -- 1 row (existing mechanism)"
post_write: "only status changed (md5 excluding status 0cca2373… before = after); all other fingerprints unchanged; APPROVED manifests 3 -> 4"
inmemory_check: "real APPROVED status passes node 03; 14 requirements identical to evidenced sim (11 REUSE_EXISTING, 3 audio NEEDS_HUMAN_REVIEW)"
consequence: "Agent-005 cost baseline for backlog 07d622e9 now selects 96df250f (video 15, unchanged); Agent-006 runs must target 96df250f by exact UUID"
agent006_executions: 0
agent007_executions: 0
readiness_approvals: 0
registry_changes: 0
storage_changes: 0
paid_calls: 0
migrations: 0
rollback: "UPDATE episode_production_manifests SET status='REVIEW' WHERE id='96df250f-7182-4d5f-a556-b0448e518375' AND status='APPROVED'"
status: "EP005_TBD_CLEANUP_DERIVED_MANIFEST_HUMAN_APPROVED + DERIVED_MANIFEST_96DF250F_APPROVED + THREE_VISUAL_TREATMENTS_PRESERVED + FOLEY_TOUCH_DROPPED + THREE_AUDIO_TBDS_REMAIN + ELEVEN_REUSE_EXISTING_PRESERVED + SOURCE_MANIFESTS_UNCHANGED + EVIDENCE_COMMITTED_TO_GITHUB"
```

---

## ENG-20261005-EP005-LOCAL-AUDIO-CANDIDATES: deterministic local audio candidates for human review (ambience x3, completion pop x3)

```yaml
change_id: "ENG-20261005-EP005-LOCAL-AUDIO-CANDIDATES"
timestamp: "2026-10-05T07:00:25Z"
actor: "Claude"
authorised_by: "Company Brain (owned/self-produced audio; local deterministic tools only)"
evidence: "evidence/EP005_LOCAL_AUDIO_CANDIDATES_v1.0.md"
script: "evidence/ep005/audio_candidates/generate_ep005_audio_candidates_v1.sh (ffmpeg 6.1.1 lavfi anoisesrc fixed seeds + aevalsrc; bitexact; no inputs, no network)"
candidates:
  - {id: "AMB-BATHROOM-QUIET-v01-CAND-A", sha256: "b0afccd7a8815cd223048c703155dd66aae58d8dd22b453dd515950a03f8de02", spec: "40 s seamless loop, s24le 48k stereo, -52.6 dBFS RMS"}
  - {id: "AMB-BATHROOM-QUIET-v01-CAND-B", sha256: "f8809a9dcda6f854686734efbeaa4667a86842f734a4110f67c44dc1bb45bb77", spec: "40 s seamless loop, warmer, -51.4 dBFS RMS"}
  - {id: "AMB-BATHROOM-QUIET-v01-CAND-C", sha256: "a2e38046c7aab31e555a5bd3307d3dcc4ba4f296b4f4a79c5c531988bdacce68", spec: "40 s seamless loop, airier, -53.1 dBFS RMS"}
  - {id: "SFX-COMPLETION-POP-v01-CAND-A", sha256: "1dcab105d29bd7dd0bf99dd1eb86c43dabe5a671a36cc230614c0bc13b96e13a", spec: "0.25 s, s24le 48k mono, 900->380 Hz glide"}
  - {id: "SFX-COMPLETION-POP-v01-CAND-B", sha256: "7816c4d7ab4fdb4dd65dcdf65799b1b530ec84145be33bb258c6917be32c8822", spec: "0.30 s, softer 700->300 Hz"}
  - {id: "SFX-COMPLETION-POP-v01-CAND-C", sha256: "fa109e403d25d36e7e2dc5ae674257884ad1fcdb2b2c304ec6cb3e04280b94df", spec: "0.18 s, brighter 1100->450 Hz + faint transient"}
determinism: "two runs inside unshare -n (no network interfaces) -> 6/6 identical SHA-256"
qc: "ambience seams clean (boundary step < p99.9 adjacent step; head/tail RMS within 0.2 dB), max tonal prominence 2.3-2.8 dB (no hum), L/R corr ~0; pops start/end at zero, peak about -6.4 dBFS"
review_location: "session scratch .../scratchpad/ep005_audio_candidates/ (+ review_aids loop-check files); binaries NOT committed"
disclosure: "pip install numpy (PyPI) used for QC only; not an audio source or provider"
provider_calls: 0
paid_calls: 0
registry_changes: 0
storage_changes: 0
agent006_executions: 0
agent007_executions: 0
readiness_approvals: 0
migrations: 0
next: "human listening and selection by exact SHA-256; FOLEY-CLOTH-SOFT-v01 human recording; separate ingestion authorisation"
status: "EP005_LOCAL_AUDIO_CANDIDATES_READY_FOR_HUMAN_REVIEW + DETERMINISTIC_RECIPES_RECORDED + SIX_SHA256_RECORDED + ZERO_PROVIDER_CALLS + EVIDENCE_COMMITTED_TO_GITHUB"
```

---

## ENG-20261005-EP005-SUNO-STOPPED-PRE-GENERATION: Suno candidate task stopped at Step 1 (commercial rights not verified)

```yaml
change_id: "ENG-20261005-EP005-SUNO-STOPPED-PRE-GENERATION"
timestamp: "2026-10-05"
actor: "Claude"
requested_by: "Company Brain (Suno candidates for AMB-BATHROOM-QUIET-v01, FOLEY-CLOTH-SOFT-v01, SFX-COMPLETION-POP-v01; existing access/credits only; rights check first)"
evidence: "evidence/EP005_SUNO_CANDIDATES_STOPPED_PRE_GENERATION_v1.0.md"
result: "STOPPED_PRE_GENERATION_SUNO_COMMERCIAL_RIGHTS_NOT_VERIFIED"
findings:
  - "no Suno plan/tier, billing or rights evidence recorded anywhere (repo, registry)"
  - "existing 3 Suno SFX rows carry only source=Suno + human_approved; no plan, date, id, prompt, licence or hash"
  - "no Suno access from this environment: no tool/connector, no n8n credential (10 listed, names/types only), no env secret, proxy injects Supabase only"
unblock: "human captures current Suno plan + dated terms; generates in the Suno web app (recording id/prompt/model/timestamp) or provides sanctioned access; Claude then hashes the original bytes and builds the review package"
generations: 0
paid_calls: 0
purchases_upgrades_credits_billing_changes: 0
registry_changes: 0
storage_changes: 0
agent006_executions: 0
agent007_executions: 0
migrations: 0
status: "STOPPED_PRE_GENERATION + ZERO_WRITES_OUTSIDE_EVIDENCE"
```

---

## ENG-20261007-EP005-ELEVENLABS-AUDIO-CANDIDATES: nine ElevenLabs Sound Effects candidates for human review (ambience x3, cloth x3, pop x3)

```yaml
change_id: "ENG-20261007-EP005-ELEVENLABS-AUDIO-CANDIDATES"
timestamp: "2026-10-07T03:11:33Z"
actor: "Claude"
authorised_by: "Company Brain (existing ElevenLabs Starter-plan credits only; max 9 generations; no purchase/upgrade/billing change; rights reconciliation separate)"
evidence: "evidence/EP005_ELEVENLABS_AUDIO_CANDIDATES_v1.0.md"
manifest: "evidence/ep005/elevenlabs_candidates/EP005_ELEVENLABS_CANDIDATES_MANIFEST_v1.json (prompts, node/session/generation ids, timestamps, settings, SHA-256 of original downloads)"
tool: "ElevenLabs MCP (restricted connector), flow NRRpsJcWc7UzYPkRv6e3, model eleven_text_to_sound_v2, generations_count=1 on every run, prompt_influence 0.5"
generations: {performed: 9, ceiling: 9, failed: 0, retries: 0}
credits: "265 reported across the 9 generations; estimate_only had returned 795 (3x); account balance not readable via the connector"
candidates:
  - {id: "AMB-BATHROOM-QUIET-v01-EL-CAND-A", sha256: "e5930ba7886e9889075bc2c26203296f58319c0959b0581efb8e41b3a44c5192", gen: "jBDhcy9ESwGyI8gN3IP9"}
  - {id: "AMB-BATHROOM-QUIET-v01-EL-CAND-B", sha256: "87ca37d5a5feda35f3f5d40485b3c6ff6697574452d278a636e16f2534b67906", gen: "7CeuAy9P4ig5O05cOFJs"}
  - {id: "AMB-BATHROOM-QUIET-v01-EL-CAND-C", sha256: "baee962c86f8725ffa595331f452a698bde7d5e69871165696bf43e933317d6b", gen: "Oe9nvpw0JuR3zKjs6Vib"}
  - {id: "FOLEY-CLOTH-SOFT-v01-EL-CAND-A", sha256: "6eee9b2447a9525853105a9146daae3f47f5142a55d54b7e12846c546c327a6a", gen: "1svFoVNd2k9YUGYk5BK1"}
  - {id: "FOLEY-CLOTH-SOFT-v01-EL-CAND-B", sha256: "d7a7786e01a5e69fae7465d91eea5aaf8efdeea5f03aad32bbfe3a719d3c58c2", gen: "n8T2LIFiBNMbroS3VjgQ"}
  - {id: "FOLEY-CLOTH-SOFT-v01-EL-CAND-C", sha256: "b0c80ce840bc39f0f306b8f84dcf5fb8b654a011249bcd03a63933911f6b9080", gen: "eiW0bnQ9IsbkD6qwPVuQ"}
  - {id: "SFX-COMPLETION-POP-v01-EL-CAND-A", sha256: "26cbfe89678e68b4826a8179c29ffa427492bd521a8df300c51d9c8f4b9d4a6d", gen: "75tahAZ0wFnzcjSADUkx"}
  - {id: "SFX-COMPLETION-POP-v01-EL-CAND-B", sha256: "3f2fc41f6da27abc4e1abbf285b3a02f9a9ac319529ccfbbecba97cce48923ba", gen: "9nbCjtJHleIzRbpza0DP"}
  - {id: "SFX-COMPLETION-POP-v01-EL-CAND-C", sha256: "9c816983d5e05f36ba5f14d5463769ce371fd1affccb79d3f01354876f26aecc", gen: "w7nMUcbVodYoUbfbm0KZ"}
qc_flags: "ambience: tonal prominence 27.6-32.1 dB (possible hum; local synthetic candidates were 2.3-2.8); loop-seam click test fails for A and B, passes for C (MP3 padding may affect it); all very quiet (-60 to -68 dBFS RMS). pops: peaks -33 to -43 dBFS; B and C keep low-level content to end of the 0.48 s clip. cloth: A ~0-793 ms, B ~187-510 ms, C ~24-872 ms"
rights_status: "UNRECONCILED (Starter plan stated by Company Brain, not verified from account; not blocking generation per instruction); no ingestion until reconciled and a human approves exact bytes"
prompt_deviation: "suggested prompt directions condensed per the model guide; toilet/plumbing/traffic/fan terms omitted; prompt_influence 0.5 chosen"
review_location: "session scratch .../scratchpad/el_candidates/ (original/, review/ byte-identical renamed copies, review_aids/ loop-check derivatives); audio binaries NOT committed"
purchases_upgrades_billing_changes: 0
registry_changes: 0
storage_changes: 0
agent006_executions: 0
agent007_executions: 0
readiness_approvals: 0
migrations: 0
next: "human listening and selection by exact SHA-256; rights reconciliation; trimming/gain staging of the chosen files; separate ingestion authorisation"
status: "EP005_ELEVENLABS_AUDIO_CANDIDATES_READY_FOR_HUMAN_REVIEW + MAX_NINE_GENERATIONS + ORIGINAL_SHA256_RECORDED + EVIDENCE_COMMITTED_TO_GITHUB"
```

---

## ENG-20261007-EP005-SELECTED-AUDIO-MASTERING: mastered review derivatives of the three human-selected ElevenLabs audio candidates

```yaml
change_id: "ENG-20261007-EP005-SELECTED-AUDIO-MASTERING"
timestamp: "2026-10-07"
actor: "Claude"
authorised_by: "Company Brain (human selection: AMBIENCE C, CLOTH C, COMPLETION POP A; no regeneration; no credits; local review derivatives only)"
evidence: "evidence/EP005_SELECTED_AUDIO_MASTERING_v1.0.md"
recipe: "evidence/ep005/audio_mastering/master_ep005_selected_audio_v1.sh (ffmpeg only, bitexact, verifies source SHA-256; two runs byte-identical)"
manifest: "evidence/ep005/audio_mastering/EP005_MASTERING_MANIFEST_v1.json"
sources_verified:
  - {id: "AMB-BATHROOM-QUIET-v01-EL-CAND-C", gen: "Oe9nvpw0JuR3zKjs6Vib", sha256: "baee962c86f8725ffa595331f452a698bde7d5e69871165696bf43e933317d6b"}
  - {id: "FOLEY-CLOTH-SOFT-v01-EL-CAND-C", gen: "eiW0bnQ9IsbkD6qwPVuQ", sha256: "b0c80ce840bc39f0f306b8f84dcf5fb8b654a011249bcd03a63933911f6b9080"}
  - {id: "SFX-COMPLETION-POP-v01-EL-CAND-A", gen: "75tahAZ0wFnzcjSADUkx", sha256: "26cbfe89678e68b4826a8179c29ffa427492bd521a8df300c51d9c8f4b9d4a6d"}
masters:   # WAV PCM s24le 44.1 kHz stereo
  - {production_id: "AMB-BATHROOM-QUIET-v01", file: "AMB-BATHROOM-QUIET-v01_MASTER_REVIEW.wav", bytes: 6615168, sha256: "4ce88a1a396c3a9dc4f34ee4f9d1ae8464b2ab5bd81ddf0fd375eff5ab5566c7", processing: "loop-aware 80 Hz 4th-order high-pass + gain +34.5 dB; 25.0002 s; -42.0 LUFS; peak -29.9 dBFS"}
  - {production_id: "FOLEY-CLOTH-SOFT-v01", file: "FOLEY-CLOTH-SOFT-v01_MASTER_REVIEW.wav", bytes: 248826, sha256: "e861dd2b7b26a78b7be31ab9db1bef3d5ccc7905f700e5c04bc9eae849805f03", processing: "tail trim 1.000 -> 0.940 s + gain +18.8 dB; peak -6.08 dBFS"}
  - {production_id: "SFX-COMPLETION-POP-v01", file: "SFX-COMPLETION-POP-v01_MASTER_REVIEW.wav", bytes: 53022, sha256: "0c5d136d407b60f9dc6ec65ab98fbd764dcb0e6f7f24b2fd04dd3f5d57f6398f", processing: "30 Hz high-pass + trim 0.480 -> 0.200 s + 0.25 ms fade-in + 20 ms fade-out + gain +26.9 dB; peak -6.02 dBFS"}
deviation: "two high-pass filters beyond gain/trim/fade, each justified by a measured objective defect (ambience: ~99% of power is a 25-40 Hz rumble 17 dB above the audible band; pop: sub-40 Hz unipolar pulse). Comparison file with gain-only ambience provided. Decision requested: accept or redo strictly gain-only."
findings: "ambience loop seam clean (left as provider made it); faint tonal lines 3.6-15.8 kHz ~25 dB below hush (likely MP3 artefacts, untouched); masters kept at native 44.1 kHz while the approved SFX library is 48 kHz; sources are 128 kbps MP3"
rights_status: "UNRECONCILED; connector workspace/account identity (a2a81ab0f7fd406cb3fff9eef8e173c2) vs VA account unresolved; no ingestion until reconciled and a human approves exact bytes"
review_location: "session scratch .../scratchpad/mastering/review_final/ (3 masters + 2 review aids); audio binaries NOT committed"
elevenlabs_calls: 0
credits_used: 0
new_generations: 0
registry_changes: 0
storage_changes: 0
agent006_executions: 0
agent007_executions: 0
readiness_approvals: 0
migrations: 0
next: "final human listening; decision on the two filters; rights/account reconciliation; separate ingestion authorisation (upload with no overwrite, readback, register APPROVED, derived manifest mapping the three audio requirements by name)"
status: "EP005_SELECTED_AUDIO_MASTERING_READY_FOR_FINAL_HUMAN_REVIEW + THREE_MASTERED_REVIEW_FILES + ZERO_NEW_GENERATIONS + EVIDENCE_COMMITTED_TO_GITHUB"
```

```yaml
id: ENG-20261007-EP005-AUDIO-INGESTION
timestamp: "2026-10-07"
actor: "Claude"
authorised_by: "Company Brain / human (all three mastered audio files approved; ingest, register, create derived manifest in REVIEW)"
evidence: "evidence/EP005_AUDIO_INGESTION_AND_FINAL_DERIVED_MANIFEST_v1.0.md"
manifest: "evidence/ep005/audio_ingestion/EP005_AUDIO_INGESTION_MANIFEST_v1.json"
storage: ["audio/ambience/AMB-BATHROOM-QUIET-v01.wav (cc28320c-8508-4979-824b-0e557a931bb8)", "audio/foley/FOLEY-CLOTH-SOFT-v01.wav (46132a21-7f7b-4052-a0f8-1d0fff576070)", "audio/sfx/SFX-COMPLETION-POP-v01.wav (222a2762-81b0-401e-b02e-abca83b5c00f)"]
final_sha256: {AMB: "ea28fad468e353b99d48070d12853620f08e8b05c8d912706122d31176544d2f", CLOTH: "11fe4284b8540f84dc693f1b5ec9282123a930dfcb9f9209a6bc5c86cb00682f", POP: "0e3d63e607633a199feed76e93f62773bfe006b86e39515cb47fbd3a8f844dfa"}
registry_rows: {AMB: "2ba504eb-43ad-45c2-a3bc-67ce72282359", CLOTH: "34c7e5f4-8250-4058-9b84-3ce80d5f2030", POP: "0d07e835-fa88-4078-87dd-63c35f1226ae"}
derived_manifest: {id: "45cc7493-80b4-4e8d-b71d-fbd7fd3656ed", status: "REVIEW", source: "96df250f-7182-4d5f-a556-b0448e518375 (unmodified)", canonical_sha256: "e0c2e849fa00c8328dd2dd670e4b5bcd477d29dc6de967d70440abc0349b0d55", requirements: "14 before, 14 after, 0 TBD::AUDIO"}
rights_status: "UNRECONCILED (recorded in registry metadata)"
elevenlabs_calls: 0
credits_used: 0
billing_changes: 0
overwrites: 0
agent006_executions: 0
agent007_executions: 0
readiness_approvals: 0
manifest_approvals: 0
workflow_publications: 0
migrations: 0
rollback: "delete derived row 45cc7493 and the three registry rows; remove the three storage objects; 96df250f untouched"
status: "EP005_AUDIO_INGESTION_AND_FINAL_DERIVED_MANIFEST_READY_FOR_HUMAN_APPROVAL + THREE_APPROVED_AUDIO_REGISTRY_ROWS + NEW_DERIVED_MANIFEST_STATUS_REVIEW + ZERO_TBD_AUDIO_REQUIREMENTS + EXPECTED_REQUIREMENT_COUNT_14 + EVIDENCE_COMMITTED_TO_GITHUB"
```

---

## ENG-20261007-EP005-FINAL-AGENT006-PROOF: approve derived manifest 45cc7493 and run Agent-006 once

```yaml
change_id: "ENG-20261007-EP005-FINAL-AGENT006-PROOF"
timestamp: "2026-10-07T04:10:02Z"
actor: "Claude"
authorised_by: "Human via Company Brain (approve 45cc7493 status-only; exactly one Agent-006 run)"
evidence: ["evidence/EP005_FINAL_AGENT006_PROOF_v1.0.md", "evidence/EP005_DERIVED_MANIFEST_APPROVAL_v1.0.md"]
approval: "45cc7493-80b4-4e8d-b71d-fbd7fd3656ed REVIEW -> APPROVED, status only (canonical sha e0c2e849... verified before; all other fields identical); approval commit d1ab62cc2a09e60e7e6c191b241087d5a59abd29; 96df250f unchanged"
method: "single-use caller ntqoBdrDyUHiGjVc (no credentials), archived after the run; Agent-006 ZTBdnKFO8STSjJU4 at 9bf6bbef unchanged and unpublished"
execution: {caller: "578 success", agent006: "579 success 04:10:02Z-04:10:19Z", asset_resolution_run_id: "A006-1791346204213", readiness_manifest: "edc4ad58-3e5d-4ac2-9c74-c9af03af363f REVIEW / READY_FOR_HUMAN_APPROVAL"}
result: "14 requirements: 14 REUSE_EXISTING, 0 NEEDS_HUMAN_REVIEW, 0 CREATE_NEW, 0 BLOCKED, 0 ambiguous"
db_audit: "ARI 58->72 (+14, prior md5 unchanged); readiness 6->7 (prior md5 unchanged); registry (23), manifests (11), storage (19) identical before/after the run"
agent007_executions: 0
readiness_approvals: 0
generation_calls: 0
paid_calls: 0
elevenlabs_calls: 0
registry_changes: 0
storage_changes: 0
migrations: 0
rollback: "delete edc4ad58 and the 14 ARI rows of A006-1791346204213; set 45cc7493 back to REVIEW if required"
open_items: ["human approval of readiness manifest edc4ad58 (not given)", "ElevenLabs commercial-rights documentation (deferred by human)"]
status: "EP005_FINAL_AGENT006_PROOF_COMPLETE + DERIVED_MANIFEST_APPROVED + EXACTLY_ONE_AGENT006_RUN + 14_REUSE_EXISTING + ZERO_NEEDS_HUMAN_REVIEW + ZERO_CREATE_NEW + ZERO_BLOCKED + ZERO_AMBIGUOUS + READY_FOR_HUMAN_APPROVAL + READINESS_MANIFEST_STATUS_REVIEW + ZERO_AGENT007_RUN + ZERO_PROVIDER_GENERATION + ZERO_PAID_CALLS + EVIDENCE_COMMITTED_TO_GITHUB"
```

---

## ENG-20261007-EP005-PRODUCTION-READINESS-APPROVED: approve readiness manifest edc4ad58

```yaml
change_id: "ENG-20261007-EP005-PRODUCTION-READINESS-APPROVED"
timestamp: "2026-10-07"
actor: "Claude"
authorised_by: "Human via Company Brain (approve EP005 production readiness; readiness only)"
evidence: ["evidence/EP005_PRODUCTION_READINESS_APPROVAL_v1.0.md", "evidence/ep005/audio_ingestion/EP005_READINESS_APPROVAL_FIELD_DIFF_v1.json"]
readiness_manifest: "edc4ad58-3e5d-4ac2-9c74-c9af03af363f"
production_manifest: "45cc7493-80b4-4e8d-b71d-fbd7fd3656ed (APPROVED, unmodified)"
agent006_run: "A006-1791346204213 (execution 579)"
change: "status REVIEW -> APPROVED only; readiness_state stays READY_FOR_HUMAN_APPROVAL; readiness_manifest_json, counts and all other columns identical; 14 resolution items and other readiness manifests unchanged"
counts: "requirement 14; 14 REUSE_EXISTING; 0 unresolved/create_new/blocked/ambiguous"
agent006_runs: 0
agent007_runs: 0
provider_calls: 0
paid_calls: 0
downstream_production_executions: 0
registry_changes: 0
storage_changes: 0
migrations: 0
rollback: "set status back to REVIEW for edc4ad58"
next: "Company Brain / human authorisation for any next production stage; none started"
status: "EP005_PRODUCTION_READINESS_APPROVED + READINESS_MANIFEST_APPROVED + PRODUCTION_MANIFEST_APPROVED + 14_REUSE_EXISTING + ZERO_UNRESOLVED + ZERO_AGENT006_RUN + ZERO_AGENT007_RUN + ZERO_PROVIDER_GENERATION + ZERO_PAID_CALLS + ZERO_DOWNSTREAM_PRODUCTION + EVIDENCE_COMMITTED_TO_GITHUB"
```

---

## ENG-20261007-EP005-DOWNSTREAM-PRODUCTION-AUDIT: read-only downstream production audit

```yaml
change_id: "ENG-20261007-EP005-DOWNSTREAM-PRODUCTION-AUDIT"
timestamp: "2026-10-07"
actor: "Claude"
authorised_by: "Company Brain (read-only downstream audit)"
evidence: "evidence/EP005_DOWNSTREAM_PRODUCTION_AUDIT_v1.0.md"
classification: "C NEW_PRODUCTION_WORKFLOW_REQUIRED"
live_workflows: {agent006: "ZTBdnKFO8STSjJU4 9bf6bbef unpublished", agent007_v01: "hlwQHO8FEcn4gDXE active, published 45c20c99 (no paid gate), draft b135f8a5 gate DISABLED", agent007_v02: "SVWr32vunweTrvnf inactive"}
key_findings: ["no downstream shot/video/composite/voice/caption/render/QC/publish workflow, table or storage path exists", "only provider call wired anywhere is Runway text_to_image (assets, not shots)", "15 video shots and 26 base frames required; no base frames exist", "no ElevenLabs or TTS credential in n8n", "legacy APPROVED+NEEDS_ASSET_CREATION readiness manifests d124ba28 and c0012923 remain (F-4)", "shot_plan text still carries TMP_/TBD labels; use canonical_reuse_map"]
next_stage_proposed: "Agent-008 Shot Assembly Specification & Deterministic Compositor (not built); smoke S004+S005"
provider_calls: 0
paid_calls: 0
n8n_writes: 0
supabase_writes: 0
storage_writes: 0
agent006_runs: 0
agent007_runs: 0
status: "EP005_DOWNSTREAM_PRODUCTION_AUDIT_COMPLETE + PRODUCTION_PATH_CLASSIFICATION_C + ZERO_PROVIDER_CALLS + ZERO_PAID_CALLS + ZERO_N8N_WRITES + ZERO_SUPABASE_WRITES + ZERO_STORAGE_WRITES + ZERO_AGENT006_RUN + ZERO_AGENT007_RUN + EVIDENCE_COMMITTED_TO_GITHUB"
```

---

## ENG-20261007-AGENT008-V01-PHASE0: Agent-008 deterministic compositor built; EP005 S004/S005 technical smoke render (REVIEW)

```yaml
change_id: "ENG-20261007-AGENT008-V01-PHASE0"
timestamp: "2026-10-07"
actor: "Claude"
authorised_by: "Company Brain (Agent-008 v0.1 Phase-0 sprint; no provider generation)"
evidence: "evidence/AGENT008_V01_PHASE0_SMOKE_v1.0.md"
contract: "agent008/CONTRACT.md"
inputs: {readiness: "edc4ad58-3e5d-4ac2-9c74-c9af03af363f APPROVED / READY_FOR_HUMAN_APPROVAL", production_manifest: "45cc7493-80b4-4e8d-b71d-fbd7fd3656ed APPROVED (canonical e0c2e849…)", agent006_run: "A006-1791346204213", snapshot: "HTTP GET only"}
render: {shots: "S004 (120 f) + S005 (96 f) = 216 frames, 9.000 s, 1920x1080 24 fps H.264 yuv420p + AAC", review_mp4_sha256: "8fd265089c2c93538375c3dc258ad2f225f69d58332894a560c17a2c323989b7", mix_wav_sha256: "caebec5d2c34ac07b0d0628a00571eb8d0777424ed3b100fdbd5066b4d33ca64", provenance_sha256: "4f3f6adbe3f41695031b4172b90ec87fc8ba971618821a97a1bde18ceb08a667", status: "REVIEW", labels: "NON_CANON_TECHNICAL_STANDIN / REVIEW_ONLY / NOT_FOR_EPISODE_PUBLICATION"}
determinism: "two runs byte-identical (mp4, wav, provenance, raw frame hashes)"
tests: "37/37 pass (T-A008-01..12 + readiness gate, protected hold, SFX overrun, caption/dialogue interfaces)"
findings: ["F-A008-01 chime 8.0 s vs <=4.5 s window: explicit TRIM_WITH_FADE, human decision D-1", "F-A008-02 manifest maps ambience to S005 not S004: bed runs under S004 per Company Brain instruction, decision D-2", "F-A008-03 legacy SFX rows lack registry sha256 (chime pinned from evidence)", "F-A008-04 legacy readiness d124ba28/c0012923 can never be Agent-008 inputs", "F-A008-05 stand-in proves compositor only", "F-A008-06 H.264 hold drift <=7 code values (raw frames identical)"]
provider_calls: 0
paid_calls: 0
runway_calls: 0
elevenlabs_calls: 0
production_db_writes: 0
production_storage_writes: 0
registry_writes: 0
n8n_changes: 0
migrations: 0
agent006_runs: 0
agent007_runs: 0
binaries_committed: 0
rollback: "revert this commit; delete session scratch render; nothing else to undo"
status: "AGENT008_V01_PHASE0_COMPOSITOR_BUILT + S004_S005_TECHNICAL_SMOKE_RENDER_READY_FOR_HUMAN_REVIEW + ZERO_PROVIDER_CALLS + ZERO_PAID_CALLS + ZERO_RUNWAY_CALLS + ZERO_ELEVENLABS_CALLS + ZERO_PRODUCTION_DB_WRITES + ZERO_PRODUCTION_STORAGE_WRITES + ZERO_AGENT006_RUN + ZERO_AGENT007_RUN + TEST_SUITE_PASS + EVIDENCE_COMMITTED_TO_GITHUB"
```

---

## ENG-20261007-EP005-VOICE-S004-TIMING-AUDIT: voice/dialogue audit and S004 timing proof (read-only)

```yaml
change_id: "ENG-20261007-EP005-VOICE-S004-TIMING-AUDIT"
timestamp: "2026-10-07"
actor: "Claude"
authorised_by: "Company Brain (read-only audit; D-1 and D-2 approved, D-3 open)"
evidence: "evidence/EP005_VOICE_AND_S004_TIMING_AUDIT_v1.0.md"
human_decisions_recorded: {D1: "APPROVED deterministic shot-level trim of SFX-LUMI-CLUE-CHIME for S004; source unchanged; no new asset", D2: "APPROVED AMB-BATHROOM-QUIET-v01 continuity under S004 as a timeline policy", D3: "OPEN"}
s004_dialogue: ["Lumi: A little glint! Look at his cheek.", "Lumi: Can you help Mikko find the next berry smudge?"]
voice_infrastructure_status: "MISSING"
elevenlabs: "TTS models multilingual_v2/v3/v4/turbo_2_5/flash_2_5; connector exposes voice + language only (no speed/stability/seed/format); duration measurable only after generation; listing/previews free"
s004_budget: {max_dialogue_s: 4.15, est_speech_s: {comfortable: 7.03, brisk: 6.13, adult: 5.45}}
timing_conflict: "YES (also S012 CONFLICT; S018, S001, S006, S007 TIGHT)"
proposed_audition: "Lumi L1 Lola f9imtLc2jfOLXtqe3Ihb, L2 Libby-Animated Wu9A8zlwvFHoEpuX7MGo, L3 celine mHX7OoPk2G45VMAuinIt; multilingual_v2; 1 take each; line 1; ~102 credits est (unverified)"
agent008_contract: "evidence/ep005/voice_audit/AGENT008_VOICE_INPUT_CONTRACT_PROPOSAL_v0.1.json (proposal only)"
generations: 0
credits: 0
production_writes: 0
status: "EP005_VOICE_AND_S004_TIMING_AUDIT_COMPLETE + TIMING_CONFLICT_YES + VOICE_INFRASTRUCTURE_MISSING + ZERO_GENERATIONS + ZERO_CREDITS + ZERO_PRODUCTION_WRITES"
```

---

## ENG-20261007-EP005-LUMI-VOICE-AUDITION: bounded Lumi audition (3 takes, 210 credits) and D-3 decision record

```yaml
change_id: "ENG-20261007-EP005-LUMI-VOICE-AUDITION"
timestamp: "2026-10-07"
actor: "Claude"
authorised_by: "Company Brain / human (D-3 prompt shortening decision; bounded audition of L1-L3)"
evidence: ["evidence/EP005_LUMI_VOICE_AUDITION_v1.0.md", "evidence/ep005/voice_audition/LUMI_AUDITION_RESULTS_v1.json"]
decision_recorded: "S004 prompt: 'Can you help Mikko find the next berry smudge?' -> 'Can you find the next berry smudge?' (line 1 unchanged); script/manifest NOT yet updated"
s012_s018: "identical repeated prompt in script and manifest (S004, S012, S018); same shortened form proposed, not applied"
generations: {count: 3, model: "eleven_multilingual_v2", flow_id: "v156SWeKdkuYy8Crv8ag", credits_each: 70, credits_total: 210}
takes: [{L1: "Lola f9imtLc2jfOLXtqe3Ihb gen ICmQjlhIOueTir68xc0u 5.898 s sha 832fa7cc…2797"}, {L2: "Libby-Animated Wu9A8zlwvFHoEpuX7MGo gen ceoShU0y1UDdJvn7lck3 6.687 s sha bf296ebd…8229"}, {L3: "celine mHX7OoPk2G45VMAuinIt gen LyA1OJnk187PvD0U0PG2 5.341 s sha e7a0986d…9520"}]
fit: "speech extents 5.40 / 6.08 / 5.32 s vs 4.15 s window: none fits; timing conflict remains; no take rushed by duration (2.6-3.0 syl/s)"
winner_selected: false
mikko_generated: false
registry_rows: 0
storage_uploads: 0
agent008_changes: 0
renders: 0
billing_changes: 0
audio_binaries_committed: 0
status: "EP005_LUMI_VOICE_AUDITION_COMPLETE_THREE_TAKES + TIMING_CONFLICT_REMAINS + NO_WINNER_SELECTED + ZERO_PRODUCTION_WRITES"
```

---

## ENG-20261009-AGENT008-V02-MOTION-LAYER: motion-generation layer built; Higgsfield smoke stopped before generation

```yaml
change_id: "ENG-20261009-AGENT008-V02-MOTION-LAYER"
timestamp: "2026-10-09"
actor: "Claude"
authorised_by: "Company Brain (Agent-008 v0.2 Phase 1; exactly one Higgsfield job authorised)"
evidence: "evidence/AGENT008_V02_PHASE1_MOTION_LAYER_v1.0.md"
higgsfield_access: "MCP connected but read-only (cannot generate, per connector); no API credential in env/n8n/repo; account free plan, 10 credits"
built: ["MotionGenerationProvider abstraction + MotionRequest/MotionResult", "HiggsfieldProvider (fail-closed, transport injection, no guessed endpoints)", "SpendAuthorisation + append-only AttemptLedger (reserve before submit, no retry)", "runner (preflight validation, one submit, read-only poll, raw freeze + sha)", "motion compositor pass + automatic QC", "human QC decision log", "preflight tool", "CONTRACT v0.2 stages 8A-8G, data model, n8n design"]
smoke_shot: "S027 (IMAGE_TO_VIDEO, locked-off, zero overlays, no mirror treatment, simple shoulder lift)"
model_recommended: "seedance_2_0 (start/end image + identity references, 5 s, 16:9, 1080p, audio off); fallback kling3_0; COST_UNKNOWN"
prompt_sha256: "9850629271d25db1275c776c1a71b617ba92de907ebd2cab242c1aa5bdfbb8a8"
preflight_blockers: ["SOURCE_FRAME_MISSING (FRAME-EP005-S027-BASE-v01 required)", "PROVIDER_CREDENTIAL_MISSING"]
phase0_preserved: "S004/S005 render byte-identical (mp4 8fd26508…, wav caebec5d…)"
tests: "54/54 pass (37 Phase-0 + 17 motion M01-M12)"
higgsfield_generations: 0
credits_spent: 0
other_provider_generations: 0
agent006_runs: 0
agent007_runs: 0
production_writes: 0
status: "STOPPED_HIGGSFIELD_ACCESS_NOT_CONFIGURED + STOPPED_BASE_FRAME_REQUIRED_BEFORE_MOTION + MOTION_PROVIDER_ABSTRACTION_BUILT + TEST_SUITE_PASS + ZERO_GENERATIONS + EVIDENCE_COMMITTED_TO_GITHUB"
```

---

## ENG-20261009-AGENT008-HF-TRANSPORT-STOPPED: official Higgsfield API contract check; stopped before code (material conflicts)

```yaml
change_id: "ENG-20261009-AGENT008-HF-TRANSPORT-STOPPED"
timestamp: "2026-10-09"
actor: "Claude"
authorised_by: "Company Brain (Agent-008 v0.2 wire official Higgsfield transport; zero-spend)"
evidence: "evidence/AGENT008_V02_HIGGSFIELD_TRANSPORT_CONTRACT_STOPPED_v1.0.md"
auth_verified_earlier: "GET /marketing-studio/image/presets?size=1 -> 200 (proxy-injected credential; never read)"
sources: "official SDK @higgsfield/client 0.2.6 (read in full) + search excerpts of docs.higgsfield.ai (direct access blocked by egress policy)"
confirmed_contract: "POST /<model-endpoint>; response {status, request_id, status_url, cancel_url}; GET /requests/{request_id}/status; statuses queued|in_progress|completed|failed|nsfw(+canceled); output video.url; 401 auth, 403 credits"
status_route: "GET /requests/{request_id}/status confirmed; the earlier 404 is consistent with an unknown id"
conflicts: ["C-1 API needs a public image_url; local frame needs a platform.higgsfield.ai generate-upload-url (forbidden here; hosting/SHA-binding decision required)", "C-2 seedance_2_0 image-to-video endpoint/schema not documented in reachable sources; kling3_0 -> kling-video/v3.0/std/image-to-video partially confirmed", "C-3 MCP-derived capability catalogue does not match API field names", "C-4 cost unknown"]
code_changes: 0
live_higgsfield_calls_this_task: 0
posts: 0
generations: 0
credits_spent: 0
uploads: 0
production_writes: 0
status: "STOPPED_OFFICIAL_API_CONFLICTS_WITH_AGENT008_ASSUMPTIONS + HIGGSFIELD_AUTH_VERIFIED + S027_BASE_FRAME_BLOCKER_PRESERVED + ZERO_GENERATIONS + ZERO_CREDITS + ZERO_PROVIDER_POSTS"
rollback_notes: "Documentation-only; revert this commit."
```

---

## ENG-20261009-AGENT008-HF-TRANSPORT-WIRED: official Higgsfield transport wired behind MotionGenerationProvider (zero spend)

```yaml
change_id: "ENG-20261009-AGENT008-HF-TRANSPORT-WIRED"
timestamp: "2026-10-09"
actor: "Claude"
authorised_by: "Company Brain (Agent-008 v0.2 official Higgsfield transport wiring; C-1/C-2/status-route stops waived for implementation only)"
evidence: ["evidence/AGENT008_V02_HIGGSFIELD_TRANSPORT_WIRED_v1.0.md", "evidence/agent008/phase1_transport/S027_PREFLIGHT_v2.json", "evidence/agent008/phase1_transport/TEST_RESULTS_v1.txt"]
contract: "POST /files/generate-upload-url -> PUT upload_url (upload_headers only) -> POST /bytedance/seedance-2.0/image-to-video -> GET /requests/{request_id}/status -> GET video.url"
files_added: ["agent008/motion/http.py", "agent008/motion/higgsfield_transport.py", "agent008/motion/higgsfield_api_models.json", "agent008/motion/source_upload.py", "agent008/tests/test_higgsfield_transport.py"]
files_changed: ["agent008/motion/higgsfield.py", "agent008/motion/provider.py", "agent008/motion/contracts.py", "agent008/motion/authorisation.py", "agent008/motion/runner.py", "agent008/motion/preflight.py", "agent008/motion/jobs/ep005_s027_motion_smoke_v1.json", "agent008/CONTRACT.md"]
auth: "EnvironmentProxyAuth (Claude cloud network secret; HF_CREDENTIALS not read) or SuppliedHeaderAuth (future n8n); credential never read/logged/stored"
model: "primary bytedance/seedance-2.0/image-to-video (VERIFIED; S027 duration 5, 1080p, generate_audio false); fallback kling-video/v3.0/std/image-to-video (PARTIAL; submit disabled)"
open_item: "Seedance schema has no negative-prompt field; negative_constraints recorded, not transmitted (Company Brain decision)"
s027_preflight: "blockers SOURCE_FRAME_MISSING, SOURCE_URL_MISSING, SPEND_AUTHORISATION_MISSING; PROVIDER_CREDENTIAL_MISSING cleared"
tests: "84/84 pass (54 existing unchanged + 30 HF transport, all mocked)"
live_higgsfield_calls: 0
posts: 0
uploads: 0
generations: 0
credits_spent: 0
production_writes: 0
status: "AGENT008_HIGGSFIELD_TRANSPORT_WIRED + S027_BASE_FRAME_BLOCKER_PRESERVED + ZERO_UPLOADS + ZERO_GENERATIONS + ZERO_CREDITS + TEST_SUITE_PASS"
rollback_notes: "Revert this commit; the adapter returns to fail-closed without a transport."
```
