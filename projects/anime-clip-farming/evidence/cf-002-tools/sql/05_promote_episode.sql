-- Promote Episode. $1 source_episode_id. DRAFT -> READY only (DETERMINISTIC edge); anything else is returned as is.
WITH up AS (
  UPDATE cf.anime_source_episodes SET status = 'READY'
   WHERE source_episode_id = $1::uuid AND status = 'DRAFT'
  RETURNING source_episode_id, status::text AS status
)
SELECT source_episode_id, status FROM up
UNION ALL
SELECT source_episode_id, status::text FROM cf.anime_source_episodes WHERE source_episode_id = $1::uuid AND NOT EXISTS (SELECT 1 FROM up);
