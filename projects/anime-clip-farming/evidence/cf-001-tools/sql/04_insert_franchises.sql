-- Insert Franchises at DRAFT. $1 franchises json array, $2 agent_run_id. Existing normalised_key -> untouched (expected dedupe).
INSERT INTO cf.anime_franchises (normalised_key, display_name, status, agent_run_id)
SELECT x.normalised_key, x.display_name, 'DRAFT', $2::uuid
  FROM jsonb_to_recordset($1::jsonb) AS x(normalised_key text, display_name text)
ON CONFLICT (normalised_key) DO NOTHING
RETURNING franchise_id, normalised_key;
