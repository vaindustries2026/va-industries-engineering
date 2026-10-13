DO $neg$
DECLARE r record; rep text := ''; st text; m text; pass int := 0; fail int := 0; n int; c uuid; c2 uuid; t uuid; ep uuid; run uuid; q text;
BEGIN
  rep := 'who=' || current_user || '/' || session_user || E'\n';
  SELECT research_candidate_id, anime_title_id INTO c, t FROM cf.research_candidates ORDER BY dedupe_key LIMIT 1;
  SELECT research_candidate_id INTO c2 FROM cf.research_candidates WHERE anime_title_id <> t ORDER BY dedupe_key LIMIT 1;
  INSERT INTO cf.agent_runs(agent_code,agent_version,idempotency_key,input_ids,input_state_hash,run_state,attempt_count,provider_call_count,paid_call_count,estimated_cost_usd,started_at)
    VALUES ('CF-002','v0.1',repeat('9',64),'{}'::jsonb,repeat('a',64),'RUNNING',1,0,0,0,now()) RETURNING agent_run_id INTO run;
  INSERT INTO cf.anime_source_episodes(anime_title_id,season_number,episode_number,episode_variant,status,agent_run_id) VALUES (t,99,1,'TV','DRAFT',run) RETURNING source_episode_id INTO ep;
  UPDATE cf.anime_source_episodes SET status='READY' WHERE source_episode_id=ep;
  EXECUTE replace(replace(replace(replace(replace($s$INSERT INTO cf.anime_scene_intelligence (source_episode_id,anime_title_id,research_candidate_id,start_ms,end_ms,scene_summary,why_scene_matters,spoiler_level,research_source_platform,research_source_reference,research_access_basis,research_observed_at,dedupe_key,status,agent_run_id,agent_version) VALUES ('{EP}','{T}','{C}',1000,2000,'t','y','LOW','HUMAN_RESEARCH_OBSERVATION','human-observation:neg','SECONDARY_REFERENCE'::cf.research_access_basis,now(),repeat('0',64),'DRAFT','{RUN}','v0.1')$s$,'{EP}',ep::text),'{T}',t::text),'{C}',c::text),'{RUN}',run::text),'{C2}',coalesce(c2,c)::text);
  EXECUTE replace(replace(replace(replace(replace($s$INSERT INTO cf.anime_scene_intelligence (source_episode_id,anime_title_id,research_candidate_id,start_ms,end_ms,scene_summary,why_scene_matters,spoiler_level,research_source_platform,research_source_reference,research_access_basis,research_observed_at,dedupe_key,status,agent_run_id,agent_version) VALUES ('{EP}','{T}','{C}',5000,9000,'t','y','LOW','HUMAN_RESEARCH_OBSERVATION','human-observation:neg-2','SECONDARY_REFERENCE'::cf.research_access_basis,now(),repeat('f',64),'DRAFT','{RUN}','v0.1')$s$,'{EP}',ep::text),'{T}',t::text),'{C}',c::text),'{RUN}',run::text),'{C2}',coalesce(c2,c)::text);
  SELECT count(*) INTO n FROM cf.anime_scene_intelligence WHERE source_episode_id=ep;
  rep := rep || CASE WHEN n=2 THEN E'PASS P01 two scenes in one episode persisted\n' ELSE E'FAIL P01\n' END;
  UPDATE cf.anime_scene_intelligence SET status='READY' WHERE start_ms=1000 AND source_episode_id=ep;
  UPDATE cf.anime_scene_intelligence SET timestamps_human_verified=true WHERE start_ms=1000 AND source_episode_id=ep;
  SELECT count(*) INTO n FROM cf.anime_scene_intelligence s JOIN cf.v_scene_publication_status v USING(scene_id) WHERE s.status='READY' AND s.timestamps_human_verified AND v.publication_source_status='UNKNOWN' AND s.source_episode_id=ep;
  rep := rep || CASE WHEN n=1 THEN E'PASS P02 DRAFT->READY and human-verified flag work; status UNKNOWN\n' ELSE E'FAIL P02\n' END;
  WITH i AS (INSERT INTO cf.anime_source_episodes(anime_title_id,season_number,episode_number,status) VALUES (t,99,1,'DRAFT') ON CONFLICT ON CONSTRAINT source_episode_natural_key DO NOTHING RETURNING 1) SELECT count(*) INTO n FROM i;
  rep := rep || CASE WHEN n=0 THEN E'PASS P03 episode replay inserts nothing\n' ELSE E'FAIL P03\n' END;
  FOR r IN SELECT * FROM (VALUES
  ('N01 DELETE scene',$t$DELETE FROM cf.anime_scene_intelligence$t$,'42501'),
  ('N02 DELETE episode',$t$DELETE FROM cf.anime_source_episodes$t$,'42501'),
  ('N03 TRUNCATE',$t$TRUNCATE cf.anime_scene_intelligence$t$,'42501'),
  ('N04 update scene text',$t$UPDATE cf.anime_scene_intelligence SET scene_summary='x'$t$,'42501'),
  ('N05 update research_access_basis',$t$UPDATE cf.anime_scene_intelligence SET research_access_basis='PUBLIC_OFFICIAL_UPLOAD'$t$,'42501'),
  ('N06 write reviewers',$t$INSERT INTO cf.reviewers DEFAULT VALUES$t$,'42501'),
  ('N07 enable kill switch',$t$UPDATE cf.system_flags SET enabled=true$t$,'42501'),
  ('N08 add transition',$t$INSERT INTO cf.allowed_transitions(object_type,from_status,to_status,mode) VALUES ('scene','READY','PUBLISHED','DETERMINISTIC')$t$,'42501'),
  ('N09 disable trigger',$t$ALTER TABLE cf.anime_scene_intelligence DISABLE TRIGGER USER$t$,'42501'),
  ('N10 session_replication_role',$t$SET session_replication_role=replica$t$,'42501'),
  ('N11 call cf function',$t$SELECT cf.forbid_delete()$t$,'42501'),
  ('N12 SET ROLE postgres',$t$SET ROLE postgres$t$,'42501'),
  ('N13 CREATE TABLE cf (no CF-003 data)',$t$CREATE TABLE cf.cf003_probe(i int)$t$,'42501'),
  ('N14 CREATE TABLE public',$t$CREATE TABLE public.cf003_probe(i int)$t$,'42501'),
  ('N15 ALTER TABLE add publication column',$t$ALTER TABLE cf.anime_scene_intelligence ADD COLUMN publication_source_status text$t$,'42501'),
  ('N16 write publication view',$t$UPDATE cf.v_scene_publication_status SET publication_source_status='APPROVED'$t$,'42501|0A000'),
  ('N17 publication column absent',$t$INSERT INTO cf.anime_scene_intelligence(publication_source_status) VALUES ('APPROVED')$t$,'42703'),
  ('N18 scene status APPROVED',$t$UPDATE cf.anime_scene_intelligence SET status='APPROVED'$t$,'23514|P0001|42501|22P02'),
  ('N19 end = start',$t$INSERT INTO cf.anime_scene_intelligence (source_episode_id,anime_title_id,research_candidate_id,start_ms,end_ms,scene_summary,why_scene_matters,spoiler_level,research_source_platform,research_source_reference,research_access_basis,research_observed_at,dedupe_key,status,agent_run_id,agent_version) VALUES ('{EP}','{T}','{C}',5000,5000,'t','y','LOW','HUMAN_RESEARCH_OBSERVATION','human-observation:neg','SECONDARY_REFERENCE'::cf.research_access_basis,now(),repeat('2',64),'DRAFT','{RUN}','v0.1')$t$,'23514'),
  ('N20 negative start',$t$INSERT INTO cf.anime_scene_intelligence (source_episode_id,anime_title_id,research_candidate_id,start_ms,end_ms,scene_summary,why_scene_matters,spoiler_level,research_source_platform,research_source_reference,research_access_basis,research_observed_at,dedupe_key,status,agent_run_id,agent_version) VALUES ('{EP}','{T}','{C}',-1,5000,'t','y','LOW','HUMAN_RESEARCH_OBSERVATION','human-observation:neg','SECONDARY_REFERENCE'::cf.research_access_basis,now(),repeat('3',64),'DRAFT','{RUN}','v0.1')$t$,'23514'),
  ('N21 empty source reference',$t$INSERT INTO cf.anime_scene_intelligence (source_episode_id,anime_title_id,research_candidate_id,start_ms,end_ms,scene_summary,why_scene_matters,spoiler_level,research_source_platform,research_source_reference,research_access_basis,research_observed_at,dedupe_key,status,agent_run_id,agent_version) VALUES ('{EP}','{T}','{C}',1000,2000,'t','y','LOW','HUMAN_RESEARCH_OBSERVATION','','SECONDARY_REFERENCE'::cf.research_access_basis,now(),repeat('4',64),'DRAFT','{RUN}','v0.1')$t$,'23514'),
  ('N22 token in source reference',$t$INSERT INTO cf.anime_scene_intelligence (source_episode_id,anime_title_id,research_candidate_id,start_ms,end_ms,scene_summary,why_scene_matters,spoiler_level,research_source_platform,research_source_reference,research_access_basis,research_observed_at,dedupe_key,status,agent_run_id,agent_version) VALUES ('{EP}','{T}','{C}',1000,2000,'t','y','LOW','HUMAN_RESEARCH_OBSERVATION','https://example.org/w?token=abc','SECONDARY_REFERENCE'::cf.research_access_basis,now(),repeat('5',64),'DRAFT','{RUN}','v0.1')$t$,'23514'),
  ('N23 NULL source reference',$t$INSERT INTO cf.anime_scene_intelligence (source_episode_id,anime_title_id,research_candidate_id,start_ms,end_ms,scene_summary,why_scene_matters,spoiler_level,research_source_platform,research_source_reference,research_access_basis,research_observed_at,dedupe_key,status,agent_run_id,agent_version) VALUES ('{EP}','{T}','{C}',1000,2000,'t','y','LOW','HUMAN_RESEARCH_OBSERVATION',NULL,'SECONDARY_REFERENCE'::cf.research_access_basis,now(),repeat('6',64),'DRAFT','{RUN}','v0.1')$t$,'23502'),
  ('N24 access basis outside enum',$t$INSERT INTO cf.anime_scene_intelligence (source_episode_id,anime_title_id,research_candidate_id,start_ms,end_ms,scene_summary,why_scene_matters,spoiler_level,research_source_platform,research_source_reference,research_access_basis,research_observed_at,dedupe_key,status,agent_run_id,agent_version) VALUES ('{EP}','{T}','{C}',1000,2000,'t','y','LOW','HUMAN_RESEARCH_OBSERVATION','human-observation:neg','LICENSED'::cf.research_access_basis,now(),repeat('7',64),'DRAFT','{RUN}','v0.1')$t$,'22P02'),
  ('N25 candidate of another title',$t$INSERT INTO cf.anime_scene_intelligence (source_episode_id,anime_title_id,research_candidate_id,start_ms,end_ms,scene_summary,why_scene_matters,spoiler_level,research_source_platform,research_source_reference,research_access_basis,research_observed_at,dedupe_key,status,agent_run_id,agent_version) VALUES ('{EP}','{T}','{C2}',1000,2000,'t','y','LOW','HUMAN_RESEARCH_OBSERVATION','human-observation:neg','SECONDARY_REFERENCE'::cf.research_access_basis,now(),repeat('8',64),'DRAFT','{RUN}','v0.1')$t$,'23503'),
  ('N26 HUMAN_ADMIN scene DRAFT->REJECTED (F-2)',$t$UPDATE cf.anime_scene_intelligence SET status='REJECTED' WHERE start_ms=5000$t$,'42501'),
  ('N27 HUMAN_ADMIN episode READY->RETIRED (F-2)',$t$UPDATE cf.anime_source_episodes SET status='RETIRED' WHERE season_number=99$t$,'42501'),
  ('N28 episode identity frozen',$t$UPDATE cf.anime_source_episodes SET episode_number=98$t$,'42501'),
  ('N29 duplicate natural-key episode',$t$INSERT INTO cf.anime_source_episodes(anime_title_id,season_number,episode_number,status) VALUES ('{T}',99,1,'DRAFT')$t$,'23505'),
  ('N30 duplicate scene dedupe_key',$t$INSERT INTO cf.anime_scene_intelligence (source_episode_id,anime_title_id,research_candidate_id,start_ms,end_ms,scene_summary,why_scene_matters,spoiler_level,research_source_platform,research_source_reference,research_access_basis,research_observed_at,dedupe_key,status,agent_run_id,agent_version) VALUES ('{EP}','{T}','{C}',1000,2000,'t','y','LOW','HUMAN_RESEARCH_OBSERVATION','human-observation:neg','SECONDARY_REFERENCE'::cf.research_access_basis,now(),(SELECT dedupe_key FROM cf.anime_scene_intelligence WHERE start_ms=1000),'DRAFT','{RUN}','v0.1')$t$,'23505')) v(name,stmt,expect) LOOP
    q := replace(replace(replace(replace(replace(r.stmt,'{EP}',ep::text),'{T}',t::text),'{C}',c::text),'{RUN}',run::text),'{C2}',coalesce(c2,c)::text);
    BEGIN EXECUTE q; rep := rep || 'FAIL ' || r.name || E' (succeeded)\n';
    EXCEPTION WHEN OTHERS THEN GET STACKED DIAGNOSTICS st = RETURNED_SQLSTATE, m = MESSAGE_TEXT;
      rep := rep || CASE WHEN st ~ r.expect THEN 'PASS ' || r.name || ' (' || st || E')\n' ELSE 'FAIL ' || r.name || ' got ' || st || ' ' || left(m,60) || E'\n' END;
    END;
  END LOOP;
  RAISE EXCEPTION 'CF002_NEG_REPORT fails=% %', (length(rep) - length(replace(rep,'FAIL ','')))/5, E'\n' || rep;
END
$neg$;