-- =============================================================================
-- V&A Anime Clip Farming / Engine 2 — rollback for 0004_cf002_scene_intelligence
-- =============================================================================
-- Target:  the dedicated project mkeldytatorxxszjdngt only.
-- Effect:  removes the CF-002 objects (view, scene and episode tables, their 11
--          transition rows, the research_candidates (id, title) unique index,
--          the research_access_basis type). 0001-0003 state is left exactly as
--          it was. It does not remove the migration-history row; the operator
--          removes it (supabase_migrations.schema_migrations, name
--          cf002_scene_intelligence) with the rollback.
-- Fails closed: stops unless 0004 is applied, stops on a wrong target, and
--          stops when either table holds rows (research data), because DROP
--          would destroy it. To roll back a populated database a human sets
--          `SET cf.rollback_destroys_data = 'yes'` in the same session first.
-- =============================================================================
DO $$
BEGIN
  IF to_regclass('public.episode_scripts') IS NOT NULL
     OR to_regclass('public.asset_registry') IS NOT NULL
     OR to_regclass('public.production_plans') IS NOT NULL
     OR to_regclass('public.videos') IS NOT NULL THEN
    RAISE EXCEPTION 'CF_WRONG_TARGET: YouTube Kids tables found; this is not the dedicated Engine 2 project';
  END IF;
  IF to_regrole('cf_n8n_runtime') IS NULL THEN
    RAISE EXCEPTION 'CF_WRONG_TARGET: role cf_n8n_runtime does not exist';
  END IF;
  IF to_regclass('cf.anime_scene_intelligence') IS NULL OR to_regclass('cf.anime_source_episodes') IS NULL THEN
    RAISE EXCEPTION 'CF_PRECONDITION: 0004 is not applied; nothing to roll back';
  END IF;
  IF (SELECT count(*) FROM cf.anime_scene_intelligence) + (SELECT count(*) FROM cf.anime_source_episodes) > 0
     AND coalesce(current_setting('cf.rollback_destroys_data', true), '') <> 'yes' THEN
    RAISE EXCEPTION 'CF_ROLLBACK_REFUSED: the CF-002 tables hold rows; set cf.rollback_destroys_data = yes only with explicit human approval';
  END IF;
END $$;

DROP VIEW cf.v_scene_publication_status;
DROP TABLE cf.anime_scene_intelligence;
DROP TABLE cf.anime_source_episodes;
DROP INDEX cf.research_candidates_id_title_uq;
DELETE FROM cf.allowed_transitions WHERE object_type IN ('anime_source_episode', 'scene');
DROP TYPE cf.research_access_basis;

DO $$
BEGIN
  IF (SELECT count(*) FROM cf.allowed_transitions) <> 14 THEN RAISE EXCEPTION 'CF_ROLLBACK_POSTCHECK: transitions are not back to 14'; END IF;
  IF (SELECT count(*) FROM pg_trigger t JOIN pg_class c ON c.oid = t.tgrelid
       WHERE c.relnamespace = 'cf'::regnamespace AND NOT t.tgisinternal AND t.tgenabled = 'O') <> 12 THEN
    RAISE EXCEPTION 'CF_ROLLBACK_POSTCHECK: triggers are not back to 12';
  END IF;
END $$;
