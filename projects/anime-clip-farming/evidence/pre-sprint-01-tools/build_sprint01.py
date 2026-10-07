#!/usr/bin/env python3
"""Assemble migrations/0001_cf_sprint01.sql from the Sprint 0 design file.

Every object body is copied byte-for-byte from the Sprint 0 commit of
0001_cf_backbone.DESIGN_ONLY.sql (git 5190db5) by line range, so the
Sprint 1 file cannot drift from the accepted design by hand-editing.
Only the header, the target guard, the trimmed VALUES lists and the
grants section are new text.
"""
import subprocess, sys, pathlib

REPO = pathlib.Path('/home/claude/va-industries-engineering')
SRC_PATH = 'projects/anime-clip-farming/architecture/data-contracts/migrations-draft/0001_cf_backbone.DESIGN_ONLY.sql'
OUT = REPO / 'projects/anime-clip-farming/architecture/data-contracts/migrations/0001_cf_sprint01.sql'

src = subprocess.run(['git', '-C', str(REPO), 'show', f'5190db5:{SRC_PATH}'],
                     check=True, capture_output=True, text=True).stdout.split('\n')

def lines(a, b):
    """1-based inclusive line range from the Sprint 0 design file."""
    return '\n'.join(src[a - 1:b])

def strip_trailing_comma(text):
    assert text.endswith(','), text[-40:]
    return text[:-1]

header = """-- =============================================================================
-- V&A Anime Clip Farming / Engine 2 — Sprint 1 migration 0001_cf_sprint01
-- =============================================================================
-- Target:  Supabase project "V&A Anime Clip Farming — Engine 2",
--          ref mkeldytatorxxszjdngt, region eu-north-1. No other project.
--          Section 0 aborts on any database that is not that project.
-- Apply:   only after an explicit human / Company Brain approval that names
--          this file and its sha256. Status and evidence live outside this
--          file: evidence/PRE_SPRINT_01_MIGRATION_PREFLIGHT.md and the changelog.
-- Source:  object-for-object subset of the accepted Sprint 0 design
--          migrations-draft/0001_cf_backbone.DESIGN_ONLY.sql (commit 5190db5),
--          limited to SPRINT_00_ARCHITECTURE_REPORT.md §15. Every type, table,
--          seed row, function and trigger body below is copied unchanged.
--          Differences from §15 / the design, all deliberate:
--            1. cf.reviewers is included: cf.system_flags.changed_by_reviewer_id
--               references it, so system_flags cannot exist without it.
--            2. Section 0 target guard (new).
--            3. Section 7 grants go directly to cf_n8n_runtime (ADR-001); the
--               Sprint 0 group role cf_agent is not created, because the
--               runtime role is NOINHERIT and would not receive its grants.
--               The privilege set is cf_agent's, limited to these tables.
--            4. VALUES lists trimmed to the Sprint 1 object types.
-- Order:   provisioning already created cf_n8n_runtime (LOGIN NOINHERIT
--          NOBYPASSRLS NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION, no
--          password, no grants). This migration creates the objects as the
--          applying role (postgres) and then grants the runtime role only what
--          CF-001 needs. A human sets the role password and creates the n8n
--          credential separately; neither appears in this file.
-- Not here: episodes, scenes, editorial, scripts, gate decisions and
--          cf.record_gate_decision, source governance, production, publishing,
--          learning tables, views, cf_governance. Those need later migrations.
-- No BEGIN/COMMIT of its own: apply it as one migration. If an apply ever
-- stops part-way, 0001_cf_sprint01.ROLLBACK.sql removes whatever was created.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 0. Target guard (new): abort unless this is the dedicated Engine 2 project
-- -----------------------------------------------------------------------------
DO $$
DECLARE
  r pg_roles%ROWTYPE;
BEGIN
  SELECT * INTO r FROM pg_roles WHERE rolname = 'cf_n8n_runtime';
  IF NOT FOUND THEN
    RAISE EXCEPTION 'CF_WRONG_TARGET: role cf_n8n_runtime does not exist; it is provisioned only in the dedicated Engine 2 project';
  END IF;
  IF NOT r.rolcanlogin OR r.rolinherit OR r.rolbypassrls OR r.rolsuper
     OR r.rolcreatedb OR r.rolcreaterole OR r.rolreplication THEN
    RAISE EXCEPTION 'CF_WRONG_TARGET: cf_n8n_runtime must be LOGIN NOINHERIT NOBYPASSRLS NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION';
  END IF;
  IF EXISTS (SELECT 1 FROM pg_auth_members WHERE member = r.oid) THEN
    RAISE EXCEPTION 'CF_WRONG_TARGET: cf_n8n_runtime must not be a member of any role';
  END IF;
  IF to_regclass('public.episode_scripts') IS NOT NULL
     OR to_regclass('public.asset_registry') IS NOT NULL
     OR to_regclass('public.production_plans') IS NOT NULL
     OR to_regclass('public.videos') IS NOT NULL THEN
    RAISE EXCEPTION 'CF_WRONG_TARGET: YouTube Kids tables found; this is not the dedicated Engine 2 project';
  END IF;
  IF to_regnamespace('cf') IS NOT NULL THEN
    RAISE EXCEPTION 'CF_ALREADY_APPLIED: schema cf already exists';
  END IF;
END $$;
"""

parts = [header]

# Schema (design lines 27-28; the design's BEGIN on line 25 is not carried over)
parts.append(lines(27, 28))

parts.append("""
-- -----------------------------------------------------------------------------
-- 1. Vocabularies (design §1: the four types §15 names)
-- -----------------------------------------------------------------------------
""")
parts.append(lines(34, 47))

parts.append("""
-- -----------------------------------------------------------------------------
-- 2. Governance and operational tables (design §2)
-- -----------------------------------------------------------------------------
""")
parts.append(lines(73, 81))     # cf.reviewers (FK target of system_flags)
parts.append('')
parts.append(lines(83, 112))    # cf.agent_runs
parts.append('')
parts.append(lines(114, 121))   # cf.system_flags

parts.append("""
-- -----------------------------------------------------------------------------
-- 3. Reference identities (design §3, without anime_source_episodes)
-- -----------------------------------------------------------------------------
""")
parts.append(lines(127, 137))   # cf.anime_franchises
parts.append('')
parts.append(lines(139, 156))   # cf.anime_titles

parts.append("""
-- -----------------------------------------------------------------------------
-- 4. Intelligence (design §4: CF-001 only)
-- -----------------------------------------------------------------------------
""")
parts.append(lines(179, 203))   # cf.research_candidates

parts.append("""
-- -----------------------------------------------------------------------------
-- 5. State machine as data (design §10: rows for the three Sprint 1 object types)
-- -----------------------------------------------------------------------------
""")
parts.append(lines(601, 611))   # cf.allowed_transitions
parts.append('')
parts.append(lines(613, 624))   # INSERT header + anime_franchise + anime_title rows
parts.append(lines(630, 633))   # -- CF-001 + first three research_candidate rows
parts.append(lines(634, 634).replace("'DETERMINISTIC'),", "'DETERMINISTIC');"))

parts.append("""
-- -----------------------------------------------------------------------------
-- 6. Guard functions and triggers (design §11, without the append-only parts)
-- -----------------------------------------------------------------------------
""")
parts.append(lines(701, 705))   # touch_updated_at
parts.append('')
parts.append(lines(707, 752))   # guard_status_transition
parts.append('')
parts.append(lines(754, 776))   # freeze_after_first_status
parts.append('')
parts.append(lines(784, 788))   # forbid_delete
parts.append('')
parts.append(lines(802, 809))   # DO loop head + anime_franchises + anime_titles rows
parts.append(strip_trailing_comma(lines(811, 811)))  # research_candidates row (last)
parts.append(lines(821, 833))   # loop body unchanged

parts.append("""
-- -----------------------------------------------------------------------------
-- 7. Privileges (ADR-001: direct grants to the NOINHERIT runtime role)
-- -----------------------------------------------------------------------------
-- cf_n8n_runtime already exists (section 0 checked it). It gets exactly what the
-- Sprint 0 design gave cf_agent on these tables: read everything in cf, insert
-- and update the CF-001 tables. Deliberately absent: any write to reviewers,
-- system_flags or allowed_transitions; DELETE, TRUNCATE, REFERENCES or TRIGGER
-- anywhere; CREATE on the schema; EXECUTE on any cf function. No default
-- privileges are set, so later objects get nothing until a migration grants it.
-- Supabase's anon, authenticated and service_role get nothing on cf.

REVOKE ALL ON SCHEMA cf FROM PUBLIC;
REVOKE ALL ON ALL TABLES IN SCHEMA cf FROM PUBLIC;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA cf FROM PUBLIC;
GRANT USAGE ON SCHEMA cf TO cf_n8n_runtime;

GRANT SELECT ON ALL TABLES IN SCHEMA cf TO cf_n8n_runtime;
GRANT INSERT, UPDATE ON
  cf.agent_runs, cf.anime_franchises, cf.anime_titles, cf.research_candidates
  TO cf_n8n_runtime;
""")
parts.append(lines(996, 1000))  # seed kill switches OFF

parts.append("""
-- =============================================================================
-- END — 0001_cf_sprint01
-- =============================================================================
""")

text = '\n'.join(parts)
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(text)
print(OUT, len(text.splitlines()), 'lines')
