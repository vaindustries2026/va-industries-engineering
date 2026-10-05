# EP005 Suno Audio Candidates: Stopped Before Generation (commercial rights not verified)

**Date:** 2026-10-05 (UTC)
**Actor:** Claude Code (bounded engineering operator)
**Requested by:** Company Brain. The task was Suno candidates for AMB-BATHROOM-QUIET-v01, FOLEY-CLOTH-SOFT-v01 and SFX-COMPLETION-POP-v01, using existing access and credits only, and gated on Step 1: verify the commercial-use basis first.
**Scope:** Mikko & Lumi only.
**Result:** `STOPPED_PRE_GENERATION_SUNO_COMMERCIAL_RIGHTS_NOT_VERIFIED`. Zero generations.

## 1. Step 1 findings: commercial-use basis

| Item | Finding | Source checked (2026-10-05) |
|---|---|---|
| Current Suno plan/tier | **Not recorded anywhere** | Repository (CLAUDE.md, company-brain/, evidence/, changelog): the only "Suno" mention is the zero-call line in the local-candidates evidence |
| Billing / plan evidence | **None available** | Repository; registry metadata |
| Prior Suno generation evidence | Only `metadata_json.source = "Suno"` and `human_approved: true` on SFX-LUMI-CLUE-CHIME, SFX-MIKKO-TRY-WHOOSH and SFX-WIN-SPARKLE-CHORD. **No plan, generation id, generation date, prompt, licence text or file hash.** | Live `asset_registry` (read-only) |
| Suno access from this environment | **None.** No Suno tool or connector; no Suno credential among the 10 n8n credentials (Slack ×3, OpenAI ×2, Supabase ×2, Google API key, YouTube, Runway); no Suno environment secret; the agent proxy injects only the Supabase key. Suno is a logged-in web app, and no account session is available here. | Tool search; `n8n list_credentials` (names and types only, no secrets); environment; proxy status |
| Commercial-use entitlement under the current plan | **Cannot be demonstrated.** Suno's rights are plan-dependent: free-tier output is generally non-commercial, while paid tiers grant commercial use for songs generated *while subscribed*. Without the actual current plan and account, the rights for any new generation can't be established. This is general knowledge and was not verified against a live terms page or the account. | none authoritative available |
| Attribution / ownership limits | Undetermined, for the same reason | none |

Following the instruction, rights were **not** inferred from V&A having used Suno before, or from the existing files being downloadable.

## 2. Consequence for the existing Suno SFX (finding, no action)

The three APPROVED Suno SFX already registered and resolving in EP005 have the same gap: there is no recorded plan or generation date, so their commercial-use basis is also undocumented. This was noted in the audio sourcing brief, and it is now confirmed by a fuller search.

## 3. What would unblock a Suno path

All of these need a human with the V&A Suno account:
1. Read the current plan from Suno account settings (plan name, billing period, active since) and capture a dated screenshot or export.
2. Capture the Suno terms or rights page in force on that date for that plan: commercial use, ownership, attribution, and whether rights depend on being subscribed at generation time.
3. Either generate the candidates in the Suno web app personally, recording the song id, prompt, model version, timestamp and the original downloaded file, or provide a sanctioned programmatic access method. Claude would then hash the original bytes and assemble the review package.
4. The same plan and date evidence can retroactively document the three existing SFX, if their generation dates fall inside a commercial-plan period.

Alternative already available at zero cost: the six owned local candidates (`evidence/EP005_LOCAL_AUDIO_CANDIDATES_v1.0.md`, commit 6599baa) for ambience and pop, plus the separately planned human cloth recording.

## 4. Safety confirmation

- Suno generations: 0. Other provider calls (OpenAI, ElevenLabs, Gemini, Runway): 0. Paid calls: 0.
- Subscription purchases, plan upgrades, credit purchases and billing changes: 0.
- Registry and storage writes: 0. Manifest changes: 0. n8n writes: 0 (credential names were listed only).
- Agent-006 executions: 0. Agent-007 executions: 0. Readiness approvals: 0. Migrations: 0.
- C1, Agent-000, S3-B and Anime Clip Farming: untouched.

**Final status:** `STOPPED_PRE_GENERATION_SUNO_COMMERCIAL_RIGHTS_NOT_VERIFIED + ZERO_GENERATION + ZERO_SUBSCRIPTION_PURCHASE + ZERO_PLAN_UPGRADE + ZERO_CREDIT_PURCHASE + ZERO_BILLING_CHANGE + ZERO_REGISTRY_CHANGE + ZERO_STORAGE_CHANGE + ZERO_AGENT006_RUN + ZERO_AGENT007_RUN + ZERO_READINESS_APPROVAL`
