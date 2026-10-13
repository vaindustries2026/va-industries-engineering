-- Validate Upstream Research Candidate. $1 research_candidate_id (text), $2 anime_title_id (text). Read-only; always returns one row.
-- Text comparison on purpose: a malformed id must produce an "unknown" row, not a cast error.
SELECT c.research_candidate_id, c.status::text AS candidate_status, c.anime_title_id AS candidate_title_id,
       t.anime_title_id AS title_id, t.status::text AS title_status, t.display_title, t.start_year,
       f.status::text AS franchise_status
  FROM (SELECT $1::text AS cid, $2::text AS tid) p
  LEFT JOIN cf.research_candidates c ON c.research_candidate_id::text = p.cid
  LEFT JOIN cf.anime_titles t ON t.anime_title_id::text = p.tid
  LEFT JOIN cf.anime_franchises f ON f.franchise_id = t.franchise_id;
