'use strict';
// Generates test/negative_live.sql: ONE DO block run as the restricted runtime credential (live, via the TEST workflow, and locally by run_cf002_tests.sh).
// It reads a real READY candidate, creates its own episode/scenes, runs positive and negative checks, and ends with RAISE EXCEPTION so everything rolls back.
const fs = require('fs');
const path = require('path');
const SC = (o) => {
  const d = Object.assign({ s: 1000, e: 2000, ref: "'human-observation:neg'", basis: "'SECONDARY_REFERENCE'", key: "repeat('1',64)", cand: "'{C}'" }, o);
  return `INSERT INTO cf.anime_scene_intelligence (source_episode_id,anime_title_id,research_candidate_id,start_ms,end_ms,scene_summary,why_scene_matters,spoiler_level,research_source_platform,research_source_reference,research_access_basis,research_observed_at,dedupe_key,status,agent_run_id,agent_version) VALUES ('{EP}','{T}',${d.cand},${d.s},${d.e},'t','y','LOW','HUMAN_RESEARCH_OBSERVATION',${d.ref},${d.basis}::cf.research_access_basis,now(),${d.key},'DRAFT','{RUN}','v0.1')`;
};
const tests = [
  ['N01 DELETE scene', 'DELETE FROM cf.anime_scene_intelligence', '42501'],
  ['N02 DELETE episode', 'DELETE FROM cf.anime_source_episodes', '42501'],
  ['N03 TRUNCATE', 'TRUNCATE cf.anime_scene_intelligence', '42501'],
  ['N04 update scene text', "UPDATE cf.anime_scene_intelligence SET scene_summary='x'", '42501'],
  ['N05 update research_access_basis', "UPDATE cf.anime_scene_intelligence SET research_access_basis='PUBLIC_OFFICIAL_UPLOAD'", '42501'],
  ['N06 write reviewers', 'INSERT INTO cf.reviewers DEFAULT VALUES', '42501'],
  ['N07 enable kill switch', 'UPDATE cf.system_flags SET enabled=true', '42501'],
  ['N08 add transition', "INSERT INTO cf.allowed_transitions(object_type,from_status,to_status,mode) VALUES ('scene','READY','PUBLISHED','DETERMINISTIC')", '42501'],
  ['N09 disable trigger', 'ALTER TABLE cf.anime_scene_intelligence DISABLE TRIGGER USER', '42501'],
  ['N10 session_replication_role', 'SET session_replication_role=replica', '42501'],
  ['N11 call cf function', 'SELECT cf.forbid_delete()', '42501'],
  ['N12 SET ROLE postgres', 'SET ROLE postgres', '42501'],
  ['N13 CREATE TABLE cf (no CF-003 data)', 'CREATE TABLE cf.cf003_probe(i int)', '42501'],
  ['N14 CREATE TABLE public', 'CREATE TABLE public.cf003_probe(i int)', '42501'],
  ['N15 ALTER TABLE add publication column', 'ALTER TABLE cf.anime_scene_intelligence ADD COLUMN publication_source_status text', '42501'],
  ['N16 write publication view', "UPDATE cf.v_scene_publication_status SET publication_source_status='APPROVED'", '42501|0A000'],
  ['N17 publication column absent', "INSERT INTO cf.anime_scene_intelligence(publication_source_status) VALUES ('APPROVED')", '42703'],
  ['N18 scene status APPROVED', "UPDATE cf.anime_scene_intelligence SET status='APPROVED'", '23514|P0001|42501|22P02'],
  ['N19 end = start', SC({ s: 5000, e: 5000, key: "repeat('2',64)" }), '23514'],
  ['N20 negative start', SC({ s: -1, e: 5000, key: "repeat('3',64)" }), '23514'],
  ['N21 empty source reference', SC({ ref: "''", key: "repeat('4',64)" }), '23514'],
  ['N22 token in source reference', SC({ ref: "'https://example.org/w?token=abc'", key: "repeat('5',64)" }), '23514'],
  ['N23 NULL source reference', SC({ ref: 'NULL', key: "repeat('6',64)" }), '23502'],
  ['N24 access basis outside enum', SC({ basis: "'LICENSED'", key: "repeat('7',64)" }), '22P02'],
  ['N25 candidate of another title', SC({ cand: "'{C2}'", key: "repeat('8',64)" }), '23503'],
  ['N26 HUMAN_ADMIN scene DRAFT->REJECTED (F-2)', "UPDATE cf.anime_scene_intelligence SET status='REJECTED' WHERE start_ms=5000", '42501'],
  ['N27 HUMAN_ADMIN episode READY->RETIRED (F-2)', 'UPDATE cf.anime_source_episodes SET status=\'RETIRED\' WHERE season_number=99', '42501'],
  ['N28 episode identity frozen', 'UPDATE cf.anime_source_episodes SET episode_number=98', '42501'],
  ['N29 duplicate natural-key episode', "INSERT INTO cf.anime_source_episodes(anime_title_id,season_number,episode_number,status) VALUES ('{T}',99,1,'DRAFT')", '23505'],
  ['N30 duplicate scene dedupe_key', SC({ key: "(SELECT dedupe_key FROM cf.anime_scene_intelligence WHERE start_ms=1000)" }), '23505'],
];
const vals = tests.map(([n, st, ex]) => `('${n}',$t$${st}$t$,'${ex}')`).join(',\n  ');
const s = `DO $neg$
DECLARE r record; rep text := ''; st text; m text; pass int := 0; fail int := 0; n int; c uuid; c2 uuid; t uuid; ep uuid; run uuid; q text;
BEGIN
  rep := 'who=' || current_user || '/' || session_user || E'\\n';
  SELECT research_candidate_id, anime_title_id INTO c, t FROM cf.research_candidates ORDER BY dedupe_key LIMIT 1;
  SELECT research_candidate_id INTO c2 FROM cf.research_candidates WHERE anime_title_id <> t ORDER BY dedupe_key LIMIT 1;
  INSERT INTO cf.agent_runs(agent_code,agent_version,idempotency_key,input_ids,input_state_hash,run_state,attempt_count,provider_call_count,paid_call_count,estimated_cost_usd,started_at)
    VALUES ('CF-002','v0.1',repeat('9',64),'{}'::jsonb,repeat('a',64),'RUNNING',1,0,0,0,now()) RETURNING agent_run_id INTO run;
  INSERT INTO cf.anime_source_episodes(anime_title_id,season_number,episode_number,episode_variant,status,agent_run_id) VALUES (t,99,1,'TV','DRAFT',run) RETURNING source_episode_id INTO ep;
  UPDATE cf.anime_source_episodes SET status='READY' WHERE source_episode_id=ep;
  EXECUTE replace(replace(replace(replace(replace($s$${SC({ s: 1000, e: 2000, key: "repeat('0',64)" })}$s$,'{EP}',ep::text),'{T}',t::text),'{C}',c::text),'{RUN}',run::text),'{C2}',coalesce(c2,c)::text);
  EXECUTE replace(replace(replace(replace(replace($s$${SC({ s: 5000, e: 9000, key: "repeat('f',64)", ref: "'human-observation:neg-2'" })}$s$,'{EP}',ep::text),'{T}',t::text),'{C}',c::text),'{RUN}',run::text),'{C2}',coalesce(c2,c)::text);
  SELECT count(*) INTO n FROM cf.anime_scene_intelligence WHERE source_episode_id=ep;
  rep := rep || CASE WHEN n=2 THEN E'PASS P01 two scenes in one episode persisted\\n' ELSE E'FAIL P01\\n' END;
  UPDATE cf.anime_scene_intelligence SET status='READY' WHERE start_ms=1000 AND source_episode_id=ep;
  UPDATE cf.anime_scene_intelligence SET timestamps_human_verified=true WHERE start_ms=1000 AND source_episode_id=ep;
  SELECT count(*) INTO n FROM cf.anime_scene_intelligence s JOIN cf.v_scene_publication_status v USING(scene_id) WHERE s.status='READY' AND s.timestamps_human_verified AND v.publication_source_status='UNKNOWN' AND s.source_episode_id=ep;
  rep := rep || CASE WHEN n=1 THEN E'PASS P02 DRAFT->READY and human-verified flag work; status UNKNOWN\\n' ELSE E'FAIL P02\\n' END;
  WITH i AS (INSERT INTO cf.anime_source_episodes(anime_title_id,season_number,episode_number,status) VALUES (t,99,1,'DRAFT') ON CONFLICT ON CONSTRAINT source_episode_natural_key DO NOTHING RETURNING 1) SELECT count(*) INTO n FROM i;
  rep := rep || CASE WHEN n=0 THEN E'PASS P03 episode replay inserts nothing\\n' ELSE E'FAIL P03\\n' END;
  FOR r IN SELECT * FROM (VALUES
  ${vals}) v(name,stmt,expect) LOOP
    q := replace(replace(replace(replace(replace(r.stmt,'{EP}',ep::text),'{T}',t::text),'{C}',c::text),'{RUN}',run::text),'{C2}',coalesce(c2,c)::text);
    BEGIN EXECUTE q; rep := rep || 'FAIL ' || r.name || E' (succeeded)\\n';
    EXCEPTION WHEN OTHERS THEN GET STACKED DIAGNOSTICS st = RETURNED_SQLSTATE, m = MESSAGE_TEXT;
      rep := rep || CASE WHEN st ~ r.expect THEN 'PASS ' || r.name || ' (' || st || E')\\n' ELSE 'FAIL ' || r.name || ' got ' || st || ' ' || left(m,60) || E'\\n' END;
    END;
  END LOOP;
  RAISE EXCEPTION 'CF002_NEG_REPORT fails=% %', (length(rep) - length(replace(rep,'FAIL ','')))/5, E'\\n' || rep;
END
$neg$;`;
fs.writeFileSync(path.join(__dirname, 'negative_live.sql'), s);
console.log('bytes', s.length);
