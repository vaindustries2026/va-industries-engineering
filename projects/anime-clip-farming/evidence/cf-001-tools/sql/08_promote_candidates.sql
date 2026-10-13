-- Promote candidates IDEA -> READY (complete evidence) or IDEA -> REJECTED (reason recorded). $1 candidates json, $2 window. Only IDEA rows move.
WITH x AS (
  SELECT t.anime_title_id, c.topic_key, c.content_lane, c.ready, c.rejection_reason,
         encode(sha256(convert_to(t.anime_title_id::text || '|' || c.topic_key || '|' || c.content_lane || '|' || $2::text, 'UTF8')), 'hex') AS dedupe_key
    FROM jsonb_to_recordset($1::jsonb) AS c(anilist_id bigint, topic_key text, content_lane text, ready boolean, rejection_reason text)
    JOIN cf.anime_titles t ON t.anilist_id = c.anilist_id
)
UPDATE cf.research_candidates rc
   SET status = CASE WHEN x.ready THEN 'READY' ELSE 'REJECTED' END::cf.lifecycle_status,
       rejection_reason = CASE WHEN x.ready THEN NULL ELSE x.rejection_reason END
  FROM x
 WHERE rc.dedupe_key = x.dedupe_key AND rc.status = 'IDEA'
RETURNING rc.research_candidate_id, rc.status::text AS status;
