-- Promote reference rows DRAFT -> READY, or DRAFT -> BLOCKED. $1 franchises json, $2 titles json. Only DRAFT rows move.
WITH pf AS (
  UPDATE cf.anime_franchises f
     SET status = CASE WHEN x.blocked THEN 'BLOCKED' ELSE 'READY' END::cf.lifecycle_status
    FROM jsonb_to_recordset($1::jsonb) AS x(normalised_key text, blocked boolean)
   WHERE f.normalised_key = x.normalised_key AND f.status = 'DRAFT'
  RETURNING f.franchise_id, f.status
), pt AS (
  UPDATE cf.anime_titles t
     SET status = CASE WHEN x.blocked OR fr.status IN ('BLOCKED', 'RETIRED') THEN 'BLOCKED' ELSE 'READY' END::cf.lifecycle_status
    FROM jsonb_to_recordset($2::jsonb) AS x(anilist_id bigint, blocked boolean), cf.anime_franchises fr
   WHERE t.anilist_id = x.anilist_id AND t.status = 'DRAFT' AND fr.franchise_id = t.franchise_id
  RETURNING t.anime_title_id, t.status
)
SELECT (SELECT count(*) FROM pf WHERE status = 'READY') AS franchises_ready, (SELECT count(*) FROM pf WHERE status = 'BLOCKED') AS franchises_blocked,
       (SELECT count(*) FROM pt WHERE status = 'READY') AS titles_ready, (SELECT count(*) FROM pt WHERE status = 'BLOCKED') AS titles_blocked;
