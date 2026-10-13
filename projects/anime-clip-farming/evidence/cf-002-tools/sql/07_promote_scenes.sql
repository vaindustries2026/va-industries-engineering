-- Promote Scenes. $1 source_episode_id, $2 boundaries json [{start_ms,end_ms}].
-- DRAFT -> READY (DETERMINISTIC) only when the episode is READY, the span is valid, provenance is complete and no >= 80% overlap flag exists.
WITH b AS (
  SELECT encode(sha256(convert_to($1::text || '|' || (j.start_ms / 1000)::text || '|' || ((j.end_ms + 999) / 1000)::text, 'UTF8')), 'hex') AS dk
    FROM jsonb_to_recordset($2::jsonb) AS j(start_ms int, end_ms int)
)
UPDATE cf.anime_scene_intelligence s SET status = 'READY'
  FROM b, cf.anime_source_episodes e
 WHERE s.dedupe_key = b.dk AND s.status = 'DRAFT' AND s.possible_duplicate_of_scene_id IS NULL
   AND e.source_episode_id = s.source_episode_id AND e.status = 'READY'
   AND s.end_ms > s.start_ms AND s.research_source_platform <> '' AND s.research_source_reference <> ''
RETURNING s.scene_id, s.status::text AS status;
