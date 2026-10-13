-- Bootstrap Catalog (v0.1.1). $1 catalog json or the text 'null', $2 anime_title_id (uuid text, '' in validation mode), $3 agent_run_id.
-- Production mode ($1 = 'null'): no write; returns $2 unchanged. Validation mode: resolve-or-create exactly one franchise and one title, both DRAFT, never promoted;
-- existing rows are returned untouched (never overwritten).
WITH c AS (SELECT CASE WHEN $1::text = 'null' THEN NULL ELSE $1::jsonb END AS j),
f_ins AS (
  INSERT INTO cf.anime_franchises (normalised_key, display_name, status, agent_run_id)
  SELECT c.j->'franchise'->>'normalised_key', c.j->'franchise'->>'display_name', 'DRAFT', $3::uuid FROM c WHERE c.j IS NOT NULL
  ON CONFLICT (normalised_key) DO NOTHING
  RETURNING franchise_id, status
), f AS (
  SELECT franchise_id, status::text AS status, true AS created FROM f_ins
  UNION ALL
  SELECT a.franchise_id, a.status::text, false FROM cf.anime_franchises a, c
   WHERE c.j IS NOT NULL AND a.normalised_key = c.j->'franchise'->>'normalised_key' AND NOT EXISTS (SELECT 1 FROM f_ins)
), t_ins AS (
  INSERT INTO cf.anime_titles (franchise_id, normalised_title_key, display_title, media_type, start_year, status, agent_run_id)
  SELECT f.franchise_id, c.j->'title'->>'normalised_title_key', c.j->'title'->>'display_title', coalesce(c.j->'title'->>'media_type', 'TV'),
         (c.j->'title'->>'start_year')::smallint, 'DRAFT', $3::uuid
    FROM f, c
  ON CONFLICT ON CONSTRAINT anime_titles_fallback_key DO NOTHING
  RETURNING anime_title_id, franchise_id, status
), t AS (
  SELECT anime_title_id, franchise_id, status::text AS status, true AS created FROM t_ins
  UNION ALL
  SELECT a.anime_title_id, a.franchise_id, a.status::text, false FROM cf.anime_titles a, f, c
   WHERE c.j IS NOT NULL AND a.franchise_id = f.franchise_id AND a.normalised_title_key = c.j->'title'->>'normalised_title_key'
     AND a.start_year IS NOT DISTINCT FROM (c.j->'title'->>'start_year')::smallint AND NOT EXISTS (SELECT 1 FROM t_ins)
)
SELECT CASE WHEN c.j IS NULL THEN NULLIF($2::text, '')::uuid ELSE (SELECT t.anime_title_id FROM t) END AS anime_title_id,
       (SELECT t.franchise_id FROM t) AS franchise_id,
       (SELECT f.created FROM f) AS franchise_created, (SELECT t.created FROM t) AS title_created,
       (SELECT f.status FROM f) AS franchise_status, (SELECT t.status FROM t) AS title_status
  FROM c;
