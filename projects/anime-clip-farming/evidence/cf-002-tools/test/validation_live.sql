DO $val$
DECLARE rep text := ''; st text; m text; run uuid; title1 uuid; title2 uuid; fr1 uuid; frc boolean; tc boolean; frs text; ts text; ep1 uuid; ep2 uuid; epc boolean; sc1 uuid; v jsonb; n int; cand0 int;
  cat text := $c${"franchise":{"normalised_key":"zz cf002 rollback fixture","display_name":"ZZ CF002 Rollback Fixture"},"title":{"normalised_title_key":"zz cf002 rollback title","display_title":"ZZ CF002 Rollback Title","media_type":"TV"}}$c$; scs text := $c$[{"ordinal":1,"start_ms":0,"end_ms":90000,"characters_present":["ZZ A","ZZ B"],"scene_summary":"ZZ rollback fixture scene.","scene_function":"ZZ","why_scene_matters":"ZZ fixture.","possible_editorial_angles":["ZZ"],"context_requirement":null,"spoiler_level":"HIGH","visual_strength":0.5,"nostalgia_signal":0.5,"editorial_strength":"UNASSESSED","research_source_platform":"OFFICIAL_ZZ_FIXTURE","research_source_reference":"https://example.org/zz-fixture","research_access_basis":"PUBLIC_OFFICIAL_UPLOAD","research_access_notes":"CF002_VALIDATION_SOURCE_OUTSIDE_CF001_BATCH","research_observed_at":"2026-10-13T05:00:00Z","research_observer":"VA_HUMAN_RESEARCHER_01","timestamps_human_verified":true}]$c$; bnd text := '[{"start_ms":0,"end_ms":90000}]'; epj text := $c${"season_number":19,"episode_number":1,"episode_variant":"TV","episode_title_display":"ZZ fixture","duration_seconds":null}$c$;
  q_boot text := $qb$WITH c AS (SELECT CASE WHEN $1::text = 'null' THEN NULL ELSE $1::jsonb END AS j),
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
  FROM c$qb$;
  q_upep text := $qe$WITH x AS (
  SELECT * FROM jsonb_to_record($1::jsonb) AS e(season_number int, episode_number numeric, episode_variant text, episode_title_display text, duration_seconds int)
), ins AS (
  INSERT INTO cf.anime_source_episodes (anime_title_id, season_number, episode_number, episode_variant, episode_title_display, duration_seconds, status, agent_run_id)
  SELECT $2::uuid, x.season_number, x.episode_number, x.episode_variant, x.episode_title_display, x.duration_seconds, 'DRAFT', $3::uuid FROM x
  ON CONFLICT ON CONSTRAINT source_episode_natural_key DO NOTHING
  RETURNING source_episode_id, status::text AS status
)
SELECT source_episode_id, status, true AS created FROM ins
UNION ALL
SELECT e.source_episode_id, e.status::text, false
  FROM cf.anime_source_episodes e, x
 WHERE e.anime_title_id = $2::uuid AND e.season_number = x.season_number AND e.episode_number = x.episode_number
   AND e.episode_variant = x.episode_variant AND NOT EXISTS (SELECT 1 FROM ins)$qe$;
  q_proep text := $qp$WITH up AS (
  UPDATE cf.anime_source_episodes SET status = 'READY'
   WHERE source_episode_id = $1::uuid AND status = 'DRAFT'
  RETURNING source_episode_id, status::text AS status
)
SELECT source_episode_id, status FROM up
UNION ALL
SELECT source_episode_id, status::text FROM cf.anime_source_episodes WHERE source_episode_id = $1::uuid AND NOT EXISTS (SELECT 1 FROM up)$qp$;
  q_insc text := $qi$WITH x AS (
  SELECT s.*, encode(sha256(convert_to($2::text || '|' || (s.start_ms / 1000)::text || '|' || ((s.end_ms + 999) / 1000)::text, 'UTF8')), 'hex') AS dk
    FROM jsonb_to_recordset($1::jsonb) AS s(ordinal int, start_ms int, end_ms int, characters_present jsonb, scene_summary text, scene_function text, why_scene_matters text,
         possible_editorial_angles jsonb, context_requirement text, spoiler_level text, visual_strength numeric, nostalgia_signal numeric, editorial_strength text,
         research_source_platform text, research_source_reference text, research_access_basis text, research_access_notes text,
         research_observed_at timestamptz, research_observer text, timestamps_human_verified boolean)
)
INSERT INTO cf.anime_scene_intelligence (source_episode_id, anime_title_id, research_candidate_id, start_ms, end_ms, characters_present, scene_summary, scene_function,
       why_scene_matters, possible_editorial_angles, context_requirement, spoiler_level, visual_strength, nostalgia_signal, editorial_strength,
       research_source_platform, research_source_reference, research_access_basis, research_access_notes, research_observed_at, research_observer,
       timestamps_human_verified, possible_duplicate_of_scene_id, dedupe_key, status, agent_run_id, agent_version)
SELECT $2::uuid, $3::uuid, NULLIF($4::text, '')::uuid, x.start_ms, x.end_ms,
       coalesce(ARRAY(SELECT jsonb_array_elements_text(x.characters_present)), ARRAY[]::text[]), x.scene_summary, x.scene_function,
       x.why_scene_matters, coalesce(ARRAY(SELECT jsonb_array_elements_text(x.possible_editorial_angles)), ARRAY[]::text[]), x.context_requirement,
       x.spoiler_level, x.visual_strength, x.nostalgia_signal, x.editorial_strength,
       x.research_source_platform, x.research_source_reference, x.research_access_basis::cf.research_access_basis, x.research_access_notes, x.research_observed_at, x.research_observer,
       coalesce(x.timestamps_human_verified, false),
       (SELECT o.scene_id FROM cf.anime_scene_intelligence o
         WHERE o.source_episode_id = $2::uuid AND o.dedupe_key <> x.dk
           AND LEAST(o.end_ms, x.end_ms) - GREATEST(o.start_ms, x.start_ms) > 0
           AND (LEAST(o.end_ms, x.end_ms) - GREATEST(o.start_ms, x.start_ms))::numeric >= 0.8 * LEAST(o.end_ms - o.start_ms, x.end_ms - x.start_ms)
         ORDER BY (LEAST(o.end_ms, x.end_ms) - GREATEST(o.start_ms, x.start_ms)) DESC, o.scene_id LIMIT 1),
       x.dk, 'DRAFT', $5::uuid, $6::text
  FROM x ORDER BY x.ordinal
ON CONFLICT (dedupe_key) DO NOTHING
RETURNING scene_id, dedupe_key, start_ms, end_ms, possible_duplicate_of_scene_id$qi$;
  q_prosc text := $qs$WITH b AS (
  SELECT encode(sha256(convert_to($1::text || '|' || (j.start_ms / 1000)::text || '|' || ((j.end_ms + 999) / 1000)::text, 'UTF8')), 'hex') AS dk
    FROM jsonb_to_recordset($2::jsonb) AS j(start_ms int, end_ms int)
)
UPDATE cf.anime_scene_intelligence s SET status = 'READY'
  FROM b, cf.anime_source_episodes e
 WHERE s.dedupe_key = b.dk AND s.status = 'DRAFT' AND s.possible_duplicate_of_scene_id IS NULL
   AND e.source_episode_id = s.source_episode_id AND e.status = 'READY'
   AND s.end_ms > s.start_ms AND s.research_source_platform <> '' AND s.research_source_reference <> ''
RETURNING s.scene_id, s.status::text AS status$qs$;
  q_ver text := $qv$WITH b AS (
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
) AS verification$qv$;
BEGIN
  rep := 'who=' || current_user || '/' || session_user || E'\n';
  SELECT count(*) INTO cand0 FROM cf.research_candidates;
  INSERT INTO cf.agent_runs(agent_code,agent_version,idempotency_key,input_ids,input_state_hash,run_state,attempt_count,provider_call_count,paid_call_count,estimated_cost_usd,started_at)
    VALUES ('CF-002','v0.1.1',repeat('7',64),'{}'::jsonb,repeat('8',64),'RUNNING',1,0,0,0,now()) RETURNING agent_run_id INTO run;
  EXECUTE q_boot INTO title1, fr1, frc, tc, frs, ts USING cat, ''::text, run::text;
  rep := rep || CASE WHEN title1 IS NOT NULL AND frc AND tc AND frs='DRAFT' AND ts='DRAFT' THEN E'PASS V01 bootstrap created franchise and title, both DRAFT\n' ELSE E'FAIL V01\n' END;
  EXECUTE q_upep INTO ep1, st, epc USING epj, title1::text, run::text;
  EXECUTE q_proep USING ep1::text;
  EXECUTE q_insc INTO sc1 USING scs, ep1::text, title1::text, ''::text, run::text, 'v0.1.1'::text;
  EXECUTE q_prosc USING ep1::text, bnd;
  SELECT count(*) INTO n FROM cf.anime_scene_intelligence s JOIN cf.v_scene_publication_status v USING (scene_id)
   WHERE s.scene_id = sc1 AND s.research_candidate_id IS NULL AND s.status = 'READY' AND s.research_access_notes LIKE 'CF002_VALIDATION_SOURCE_OUTSIDE_CF001_BATCH%' AND v.publication_source_status = 'UNKNOWN' AND s.agent_version = 'v0.1.1';
  rep := rep || CASE WHEN n=1 THEN E'PASS V02 scene persisted with NULL candidate, lineage marker, READY, publication UNKNOWN\n' ELSE E'FAIL V02\n' END;
  EXECUTE q_ver INTO v USING ep1::text, bnd, title1::text;
  rep := rep || CASE WHEN (v->>'found_scenes')::int=1 AND (v->>'scenes_with_null_candidate')::int=1 AND v->'title'->>'status'='DRAFT' AND v->'title'->>'franchise_status'='DRAFT' AND (v->>'all_publication_unknown')::boolean THEN E'PASS V03 verification: 1 scene, null candidate, DRAFT catalog, all UNKNOWN\n' ELSE E'FAIL V03 ' || v::text || E'\n' END;
  EXECUTE q_boot INTO title2, fr1, frc, tc, frs, ts USING cat, ''::text, run::text;
  rep := rep || CASE WHEN title2 = title1 AND NOT frc AND NOT tc AND frs='DRAFT' AND ts='DRAFT' THEN E'PASS V04 replay: same franchise and title, nothing created, still DRAFT\n' ELSE E'FAIL V04\n' END;
  EXECUTE q_upep INTO ep2, st, epc USING epj, title2::text, run::text;
  sc1 := NULL;
  EXECUTE q_insc INTO sc1 USING scs, ep2::text, title2::text, ''::text, run::text, 'v0.1.1'::text;
  SELECT count(*) INTO n FROM cf.anime_scene_intelligence WHERE source_episode_id = ep1;
  rep := rep || CASE WHEN ep2 = ep1 AND NOT epc AND sc1 IS NULL AND n=1 THEN E'PASS V05 replay: same episode, no scene inserted, 1 scene row\n' ELSE E'FAIL V05\n' END;
  SELECT count(*) INTO n FROM cf.anime_franchises WHERE normalised_key = 'zz cf002 rollback fixture';
  rep := rep || CASE WHEN n=1 AND (SELECT count(*) FROM cf.anime_titles WHERE normalised_title_key='zz cf002 rollback title')=1 AND (SELECT count(*) FROM cf.research_candidates)=cand0 THEN E'PASS V06 no duplicate catalog rows; research candidates unchanged\n' ELSE E'FAIL V06\n' END;
  FOR n IN 1..4 LOOP
    BEGIN
      IF n=1 THEN EXECUTE 'DELETE FROM cf.anime_titles WHERE anime_title_id = $1' USING title1;
      ELSIF n=2 THEN EXECUTE 'TRUNCATE cf.anime_franchises CASCADE';
      ELSIF n=3 THEN EXECUTE 'INSERT INTO cf.research_candidates(anime_title_id) VALUES ($1)' USING title1;
      ELSE EXECUTE 'INSERT INTO cf.anime_scene_intelligence(publication_source_status) VALUES (''APPROVED'')';
      END IF;
      rep := rep || 'FAIL V1' || n || E' (succeeded)\n';
    EXCEPTION WHEN OTHERS THEN GET STACKED DIAGNOSTICS st = RETURNED_SQLSTATE;
      rep := rep || 'PASS V1' || n || ' denied (' || st || E')\n';
    END;
  END LOOP;
  RAISE EXCEPTION 'CF002_VAL_REPORT fails=% %', (length(rep) - length(replace(rep,'FAIL ','')))/5, E'\n' || rep;
END
$val$;