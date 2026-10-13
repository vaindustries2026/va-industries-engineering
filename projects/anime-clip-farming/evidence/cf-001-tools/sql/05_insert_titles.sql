-- Insert Titles at DRAFT. $1 titles json array, $2 agent_run_id. Existing anilist_id -> untouched (expected dedupe).
-- Any other unique violation (title identity fallback, mal_id) is a real failure and aborts the statement.
INSERT INTO cf.anime_titles (franchise_id, normalised_title_key, display_title, alt_titles, anilist_id, mal_id, media_type, start_year, status, agent_run_id)
SELECT f.franchise_id, x.normalised_title_key, x.display_title,
       coalesce(ARRAY(SELECT jsonb_array_elements_text(x.alt_titles)), ARRAY[]::text[]),
       x.anilist_id, x.mal_id, x.media_type, x.start_year, 'DRAFT', $2::uuid
  FROM jsonb_to_recordset($1::jsonb) AS x(franchise_key text, normalised_title_key text, display_title text, alt_titles jsonb, anilist_id bigint, mal_id bigint, media_type text, start_year int)
  JOIN cf.anime_franchises f ON f.normalised_key = x.franchise_key
ON CONFLICT (anilist_id) DO NOTHING
RETURNING anime_title_id, anilist_id;
