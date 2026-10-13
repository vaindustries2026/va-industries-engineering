'use strict';
// Generates test/validation_live.sql: ONE DO block, run as the restricted runtime credential (live via "TEST — CF-002 validation-mode DB test", locally by run_cf002_tests.sh).
// It EXECUTEs the exact workflow SQL files (v0.1.1 validation mode) against synthetic ZZ rows, checks them, and ends with RAISE EXCEPTION so everything rolls back.
const fs = require('fs');
const path = require('path');
const sql = (f) => fs.readFileSync(path.join(__dirname, '..', 'sql', f), 'utf8').split('\n').filter((l) => !/^\s*--/.test(l)).join('\n').trim().replace(/;$/, '');
const Q = (tag, f) => `$${tag}$${sql(f)}$${tag}$`;
const scene = { ordinal: 1, start_ms: 0, end_ms: 90000, characters_present: ['ZZ A', 'ZZ B'], scene_summary: 'ZZ rollback fixture scene.', scene_function: 'ZZ', why_scene_matters: 'ZZ fixture.', possible_editorial_angles: ['ZZ'], context_requirement: null,
  spoiler_level: 'HIGH', visual_strength: 0.5, nostalgia_signal: 0.5, editorial_strength: 'UNASSESSED', research_source_platform: 'OFFICIAL_ZZ_FIXTURE', research_source_reference: 'https://example.org/zz-fixture',
  research_access_basis: 'PUBLIC_OFFICIAL_UPLOAD', research_access_notes: 'CF002_VALIDATION_SOURCE_OUTSIDE_CF001_BATCH', research_observed_at: '2026-10-13T05:00:00Z', research_observer: 'VA_HUMAN_RESEARCHER_01', timestamps_human_verified: true };
const cat = { franchise: { normalised_key: 'zz cf002 rollback fixture', display_name: 'ZZ CF002 Rollback Fixture' }, title: { normalised_title_key: 'zz cf002 rollback title', display_title: 'ZZ CF002 Rollback Title', media_type: 'TV' } };
const ep = { season_number: 19, episode_number: 1, episode_variant: 'TV', episode_title_display: 'ZZ fixture', duration_seconds: null };
const s = `DO $val$
DECLARE rep text := ''; st text; m text; run uuid; title1 uuid; title2 uuid; fr1 uuid; frc boolean; tc boolean; frs text; ts text; ep1 uuid; ep2 uuid; epc boolean; sc1 uuid; v jsonb; n int; cand0 int;
  cat text := $c$${JSON.stringify(cat)}$c$; scs text := $c$${JSON.stringify([scene])}$c$; bnd text := '[{"start_ms":0,"end_ms":90000}]'; epj text := $c$${JSON.stringify(ep)}$c$;
  q_boot text := ${Q('qb', '03b_bootstrap_catalog.sql')};
  q_upep text := ${Q('qe', '04_upsert_episode.sql')};
  q_proep text := ${Q('qp', '05_promote_episode.sql')};
  q_insc text := ${Q('qi', '06_insert_scenes.sql')};
  q_prosc text := ${Q('qs', '07_promote_scenes.sql')};
  q_ver text := ${Q('qv', '08_verify_persisted.sql')};
BEGIN
  rep := 'who=' || current_user || '/' || session_user || E'\\n';
  SELECT count(*) INTO cand0 FROM cf.research_candidates;
  INSERT INTO cf.agent_runs(agent_code,agent_version,idempotency_key,input_ids,input_state_hash,run_state,attempt_count,provider_call_count,paid_call_count,estimated_cost_usd,started_at)
    VALUES ('CF-002','v0.1.1',repeat('7',64),'{}'::jsonb,repeat('8',64),'RUNNING',1,0,0,0,now()) RETURNING agent_run_id INTO run;
  EXECUTE q_boot INTO title1, fr1, frc, tc, frs, ts USING cat, ''::text, run::text;
  rep := rep || CASE WHEN title1 IS NOT NULL AND frc AND tc AND frs='DRAFT' AND ts='DRAFT' THEN E'PASS V01 bootstrap created franchise and title, both DRAFT\\n' ELSE E'FAIL V01\\n' END;
  EXECUTE q_upep INTO ep1, st, epc USING epj, title1::text, run::text;
  EXECUTE q_proep USING ep1::text;
  EXECUTE q_insc INTO sc1 USING scs, ep1::text, title1::text, ''::text, run::text, 'v0.1.1'::text;
  EXECUTE q_prosc USING ep1::text, bnd;
  SELECT count(*) INTO n FROM cf.anime_scene_intelligence s JOIN cf.v_scene_publication_status v USING (scene_id)
   WHERE s.scene_id = sc1 AND s.research_candidate_id IS NULL AND s.status = 'READY' AND s.research_access_notes LIKE 'CF002_VALIDATION_SOURCE_OUTSIDE_CF001_BATCH%' AND v.publication_source_status = 'UNKNOWN' AND s.agent_version = 'v0.1.1';
  rep := rep || CASE WHEN n=1 THEN E'PASS V02 scene persisted with NULL candidate, lineage marker, READY, publication UNKNOWN\\n' ELSE E'FAIL V02\\n' END;
  EXECUTE q_ver INTO v USING ep1::text, bnd, title1::text;
  rep := rep || CASE WHEN (v->>'found_scenes')::int=1 AND (v->>'scenes_with_null_candidate')::int=1 AND v->'title'->>'status'='DRAFT' AND v->'title'->>'franchise_status'='DRAFT' AND (v->>'all_publication_unknown')::boolean THEN E'PASS V03 verification: 1 scene, null candidate, DRAFT catalog, all UNKNOWN\\n' ELSE E'FAIL V03 ' || v::text || E'\\n' END;
  EXECUTE q_boot INTO title2, fr1, frc, tc, frs, ts USING cat, ''::text, run::text;
  rep := rep || CASE WHEN title2 = title1 AND NOT frc AND NOT tc AND frs='DRAFT' AND ts='DRAFT' THEN E'PASS V04 replay: same franchise and title, nothing created, still DRAFT\\n' ELSE E'FAIL V04\\n' END;
  EXECUTE q_upep INTO ep2, st, epc USING epj, title2::text, run::text;
  sc1 := NULL;
  EXECUTE q_insc INTO sc1 USING scs, ep2::text, title2::text, ''::text, run::text, 'v0.1.1'::text;
  SELECT count(*) INTO n FROM cf.anime_scene_intelligence WHERE source_episode_id = ep1;
  rep := rep || CASE WHEN ep2 = ep1 AND NOT epc AND sc1 IS NULL AND n=1 THEN E'PASS V05 replay: same episode, no scene inserted, 1 scene row\\n' ELSE E'FAIL V05\\n' END;
  SELECT count(*) INTO n FROM cf.anime_franchises WHERE normalised_key = 'zz cf002 rollback fixture';
  rep := rep || CASE WHEN n=1 AND (SELECT count(*) FROM cf.anime_titles WHERE normalised_title_key='zz cf002 rollback title')=1 AND (SELECT count(*) FROM cf.research_candidates)=cand0 THEN E'PASS V06 no duplicate catalog rows; research candidates unchanged\\n' ELSE E'FAIL V06\\n' END;
  FOR n IN 1..4 LOOP
    BEGIN
      IF n=1 THEN EXECUTE 'DELETE FROM cf.anime_titles WHERE anime_title_id = $1' USING title1;
      ELSIF n=2 THEN EXECUTE 'TRUNCATE cf.anime_franchises CASCADE';
      ELSIF n=3 THEN EXECUTE 'INSERT INTO cf.research_candidates(anime_title_id) VALUES ($1)' USING title1;
      ELSE EXECUTE 'INSERT INTO cf.anime_scene_intelligence(publication_source_status) VALUES (''APPROVED'')';
      END IF;
      rep := rep || 'FAIL V1' || n || E' (succeeded)\\n';
    EXCEPTION WHEN OTHERS THEN GET STACKED DIAGNOSTICS st = RETURNED_SQLSTATE;
      rep := rep || 'PASS V1' || n || ' denied (' || st || E')\\n';
    END;
  END LOOP;
  RAISE EXCEPTION 'CF002_VAL_REPORT fails=% %', (length(rep) - length(replace(rep,'FAIL ','')))/5, E'\\n' || rep;
END
$val$;`;
fs.writeFileSync(path.join(__dirname, 'validation_live.sql'), s);
console.log('bytes', s.length);
