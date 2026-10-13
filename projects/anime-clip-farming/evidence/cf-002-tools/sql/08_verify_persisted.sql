-- Verify Persisted Output. $1 source_episode_id, $2 boundaries json [{start_ms,end_ms}], $3 anime_title_id. Read-only; always returns one row.
WITH b AS (
  SELECT encode(sha256(convert_to($1::text || '|' || (j.start_ms / 1000)::text || '|' || ((j.end_ms + 999) / 1000)::text, 'UTF8')), 'hex') AS dk
    FROM jsonb_to_recordset($2::jsonb) AS j(start_ms int, end_ms int)
), sc AS (
  SELECT s.*, v.publication_source_status FROM cf.anime_scene_intelligence s
    JOIN cf.v_scene_publication_status v ON v.scene_id = s.scene_id
   WHERE s.dedupe_key IN (SELECT dk FROM b) AND s.source_episode_id = $1::uuid AND s.anime_title_id = $3::uuid
)
SELECT jsonb_build_object(
  'expected_scenes', (SELECT count(*) FROM b),
  'found_scenes', (SELECT count(*) FROM sc),
  'ready', (SELECT count(*) FROM sc WHERE status = 'READY'),
  'draft_held', (SELECT count(*) FROM sc WHERE status = 'DRAFT'),
  'blocked', (SELECT count(*) FROM sc WHERE status = 'BLOCKED'),
  'flagged_possible_duplicates', (SELECT count(*) FROM sc WHERE possible_duplicate_of_scene_id IS NOT NULL),
  'scenes_with_null_candidate', (SELECT count(*) FROM sc WHERE research_candidate_id IS NULL),
  'title', (SELECT jsonb_build_object('anime_title_id', t.anime_title_id, 'status', t.status::text, 'franchise_id', t.franchise_id, 'franchise_status', f.status::text)
              FROM cf.anime_titles t JOIN cf.anime_franchises f ON f.franchise_id = t.franchise_id WHERE t.anime_title_id = $3::uuid),
  'all_publication_unknown', (SELECT coalesce(bool_and(publication_source_status = 'UNKNOWN'), true) FROM sc),
  'episode', (SELECT jsonb_build_object('source_episode_id', e.source_episode_id, 'status', e.status::text, 'season_number', e.season_number, 'episode_number', e.episode_number, 'episode_variant', e.episode_variant)
                FROM cf.anime_source_episodes e WHERE e.source_episode_id = $1::uuid),
  'scenes', (SELECT coalesce(jsonb_agg(jsonb_build_object('scene_id', sc.scene_id, 'dedupe_key', sc.dedupe_key, 'status', sc.status::text, 'start_ms', sc.start_ms, 'end_ms', sc.end_ms,
                    'possible_duplicate_of_scene_id', sc.possible_duplicate_of_scene_id, 'research_source_platform', sc.research_source_platform,
                    'research_source_reference', sc.research_source_reference, 'research_access_basis', sc.research_access_basis::text,
                    'publication_source_status', sc.publication_source_status, 'agent_run_id', sc.agent_run_id) ORDER BY sc.start_ms, sc.end_ms), '[]'::jsonb) FROM sc)
) AS verification;
