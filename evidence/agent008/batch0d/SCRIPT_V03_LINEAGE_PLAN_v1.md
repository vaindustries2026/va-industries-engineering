# Script v03 / manifest lineage plan v1 (Batch 0D)

**Plan only; not executed.** `SCRIPT_AMENDMENT_AUTHORISED = FALSE`.

The plan would run only after Gilang approves the Alternative B wording. Each write below would need its own explicit authorisation.

Source of the exact mutations: `evidence/agent008/batch0c/EP005_S004_S012_S018_SCRIPT_AMENDMENT_PACKAGE_v1.json`.

## Sequence once the wording is approved
1. Freeze the approved v02 lineage. Nothing in it is edited.
2. **Insert** script v03: a new `episode_scripts` row, a copy of v02 plus the 6 script mutations.
3. **Derive** a new production manifest from v03: a new `episode_production_manifests` row, a copy of 45cc7493 plus the 6 manifest mutations and lineage fields.
4. Local Agent-006 read-only proof against the new manifest; expected 14/14 resolutions identical to the current proof.
5. One **authorised Agent-006 workflow run** on the new manifest, producing a new `production_readiness_manifests` row.
6. Human approval of v03, the new manifest and the new readiness record.
7. Agent-008: capture `ep005_approved_state_capture_v3.json` read-only against the new readiness record. `agent008.episode` must show only the S004/S012/S018 `dialogue_slots[*].text` changing.

## A. Script records/fields requiring change
New row in `episode_scripts` (v02 `14471926-f6fb-4bba-b355-109f3ae9e21c` is not touched).

**Lineage fields:**
- `id` (new)
- `script_version` = `v03`
- `script_version_number` = 3
- `script_run_id` (new)
- `title_working` = "EP-CANDIDATE-005 v03 — Three Gentle Wipes"
- `status`: pending human approval
- All other columns copied byte-for-byte.

**`production_script_json` (6 values):**

| Path | Old | New |
|---|---|---|
| `shots[3].dialogue_lyric` | `Lumi: “A little glint! Look at his cheek.”` | `Lumi: “A glint on his cheek!”` |
| `shots[3].child_prompt` | `Lumi: “Can you help Mikko find the next berry smudge?”` | `Lumi: “Find the next smudge!”` |
| `shots[11].dialogue_lyric` | `Lumi: “I see a spot near your mouth.”` | `Lumi: “By your mouth!”` |
| `shots[11].child_prompt` | `Lumi: “Can you help Mikko find the next berry smudge?”` | `Lumi: “Find the next smudge!”` |
| `shots[17].dialogue_lyric` | `Lumi: “One tiny spot is still here.”` | `Lumi: “One spot left!”` |
| `shots[17].child_prompt` | `Lumi: “Can you help Mikko find the next berry smudge?”` | `Lumi: “Find the next smudge!”` |

**Human decision required:** whether v03's `architecture_json` and `approved_episode_snapshot` carry the new wording. There are 7 occurrences:
- `architecture_json.cue.lumi_notice`
- `architecture_json.cue.child_prompt`
- `architecture_json.three[1].lumi_line`
- `architecture_json.three[1].child_prompt`
- `architecture_json.three[2].lumi_line`
- `architecture_json.three[2].child_prompt`
- `approved_episode_snapshot.participation_question`

They do not feed Agent-005/006/008 production paths. The recommendation is to copy them unchanged and record the divergence, unless Gilang wants them aligned.

## B. Manifest records/fields requiring change
New row in `episode_production_manifests` (45cc7493 is not touched).

**Lineage fields:**
- `id` (new)
- `episode_script_id` = v03 id
- `script_version` = `v03`
- `title_working` (v03)
- `production_plan_run_id` (new derivation id)
- `manifest_json.production_plan_run_id`, `manifest_json.derivation`, `manifest_json.manifest_version`: the new derivation record
- `status`: pending human approval

**`manifest_json` (6 values):**
- `shot_plans[3|11|17].shot_plan.audio_plan.voice_lines[0]`: the clue line, new text as in A.
- `shot_plans[3|11|17].shot_plan.audio_plan.voice_lines[1]`: the ritual prompt, `Lumi: “Find the next smudge!”`.

**Unchanged:**
- All counts (`shot_count` 29, asset counts) and all other shot plans.
- `qc_checks` hold no dialogue text. The S004/S012/S018 checks say "no altered wording" relative to the approved lines, so they remain valid against v03.

## C. Records that remain immutable
- Script v02 `14471926`.
- Manifest `45cc7493` and readiness `edc4ad58` (Agent-006 run `A006-1791346204213`).
- All 27 `asset_registry` rows and all 23 storage objects.
- The C1 canon files.
- Committed fixtures `ep005_approved_state_capture_v1/v2.json` (historical; new tests use a v3 capture).
- Every committed evidence and proof file.

## D. New manifest ID required? **YES.**
The manifest content changes. The rule is approved rows are immutable, and readiness is bound to a manifest id.

## E. New readiness record required? **YES.**
`production_readiness_manifests` binds `production_manifest_id`, `episode_script_id` and `script_version`. Agent-008's `validate_readiness` fails closed on a manifest mismatch.

## F. Agent-006 rerun after approval? **YES.**
- First the local read-only proof. The wording change does not alter asset requirements, so the expected result is identical.
- Then one separately authorised Agent-006 workflow run, to issue the readiness record bound to the new manifest.

## G. Does any approved asset become invalid? **NO.**
- No registry row is bound to the S004/S012/S018 wording.
- No Lumi production dialogue exists.
- The L1 audition take is evidence-only and was already ruled out as production dialogue.
- SFX-LUMI-CLUE-CHIME, the overlays, props and characters are wording-independent.

## H. Does S027 remain unaffected? **YES.**
- S027's script entry and shot plan are not among the mutations.
- Invariants to verify at derivation:
  - `canonical_sha256(manifest_json.shot_plans[26])` = `576e43ec1eb1489e932b163fb4bbbd6cb7edbcc0881a7e38794f2f2dd4fe747e`
  - `canonical_sha256(production_script_json.shots[26])` = `301d24065b662a43f445e90c16465b6616c7a868759584164ac3e1a8ed20e1b8`
- S027's four approved assets (frame d2a07b22, raw motion 2ebed34b, dialogue 451edb4d, assembled shot 6c290db5) stay valid. They were approved against the v02 lineage (manifest 45cc7493), and their shot plan is byte-identical in v03.

## Rollback
Nothing is executed. If executed later, v02 / 45cc7493 / edc4ad58 remain the governing rows until v03 is approved. Rollback means keeping them; there is no in-place change to revert.
