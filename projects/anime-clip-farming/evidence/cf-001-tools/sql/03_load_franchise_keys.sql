-- Load Franchise Keys. Read-only; used for the near-match (edit distance <= 2) check.
SELECT franchise_id, normalised_key, status::text AS status FROM cf.anime_franchises ORDER BY normalised_key;
