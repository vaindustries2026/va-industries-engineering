-- Insert Candidates at IDEA. $1 candidates json, $2 observation window, $3 agent_run_id.
-- dedupe_key = sha256(anime_title_id|topic_key|content_lane|observation_window) (DATA_MODEL 4.7). Existing key -> untouched (expected dedupe).
INSERT INTO cf.research_candidates (anime_title_id, franchise_id, topic_key, topic_display, content_lane, trend_state,
       demand_signal, nostalgia_signal, editorial_potential, timeliness, signal_evidence, observation_window, dedupe_key, status, agent_run_id, agent_version)
SELECT t.anime_title_id, t.franchise_id, x.topic_key, x.topic_display, x.content_lane, x.trend_state,
       x.demand_signal, x.nostalgia_signal, x.editorial_potential, x.timeliness, x.signal_evidence, $2::text,
       encode(sha256(convert_to(t.anime_title_id::text || '|' || x.topic_key || '|' || x.content_lane || '|' || $2::text, 'UTF8')), 'hex'),
       'IDEA', $3::uuid, 'v0.1'
  FROM jsonb_to_recordset($1::jsonb) AS x(anilist_id bigint, topic_key text, topic_display text, content_lane text, trend_state text,
       demand_signal numeric, nostalgia_signal numeric, editorial_potential numeric, timeliness numeric, signal_evidence jsonb)
  JOIN cf.anime_titles t ON t.anilist_id = x.anilist_id AND t.status = 'READY'
  JOIN cf.anime_franchises f ON f.franchise_id = t.franchise_id AND f.status = 'READY'
ON CONFLICT (dedupe_key) DO NOTHING
RETURNING research_candidate_id, anime_title_id, dedupe_key;
