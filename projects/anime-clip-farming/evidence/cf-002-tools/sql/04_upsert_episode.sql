-- Resolve / Upsert Source Episode. $1 episode json, $2 anime_title_id, $3 agent_run_id.
-- Natural key (title, season, episode, variant) decides identity; an existing row is returned unchanged (never overwritten).
WITH x AS (
  SELECT * FROM jsonb_to_record($1::jsonb) AS e(season_number int, episode_number numeric, episode_variant text, episode_title_display text, duration_seconds int)
), ins AS (
  INSERT INTO cf.anime_source_episodes (anime_title_id, season_number, episode_number, episode_variant, episode_title_display, duration_seconds, status, agent_run_id)
  SELECT $2::uuid, x.season_number, x.episode_number, x.episode_variant, x.episode_title_display, x.duration_seconds, 'DRAFT', $3::uuid FROM x
  ON CONFLICT ON CONSTRAINT source_episode_natural_key DO NOTHING
  RETURNING source_episode_id, status::text AS status
)
SELECT source_episode_id, status, true AS created FROM ins
UNION ALL
SELECT e.source_episode_id, e.status::text, false
  FROM cf.anime_source_episodes e, x
 WHERE e.anime_title_id = $2::uuid AND e.season_number = x.season_number AND e.episode_number = x.episode_number
   AND e.episode_variant = x.episode_variant AND NOT EXISTS (SELECT 1 FROM ins);
