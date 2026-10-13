-- Seeds one READY franchise/title/candidate with fixed ids (SYNTHETIC test data, local databases only). Run as postgres; uses the normal guarded path (DRAFT/IDEA -> READY).
INSERT INTO cf.agent_runs (agent_run_id, agent_code, agent_version, idempotency_key, input_ids, input_state_hash, run_state, attempt_count, provider_call_count, paid_call_count, estimated_cost_usd, started_at, finished_at)
  VALUES ('55555555-5555-4555-8555-555555555555', 'CF-001', 'v0.1', repeat('e', 64), '{}'::jsonb, repeat('f', 64), 'SUCCEEDED', 1, 0, 0, 0, now(), now());
INSERT INTO cf.anime_franchises (franchise_id, normalised_key, display_name, status) VALUES ('44444444-4444-4444-8444-444444444444', 'synthetic test title', 'SYNTHETIC TEST TITLE', 'DRAFT');
INSERT INTO cf.anime_titles (anime_title_id, franchise_id, normalised_title_key, display_title, alt_titles, anilist_id, media_type, start_year, status)
  VALUES ('22222222-2222-4222-8222-222222222222', '44444444-4444-4444-8444-444444444444', 'synthetic test title', 'SYNTHETIC TEST TITLE', ARRAY[]::text[], 900001, 'TV', 2000, 'DRAFT');
INSERT INTO cf.anime_titles (anime_title_id, franchise_id, normalised_title_key, display_title, alt_titles, anilist_id, media_type, start_year, status)
  VALUES ('33333333-3333-4333-8333-333333333333', '44444444-4444-4444-8444-444444444444', 'synthetic other title', 'SYNTHETIC OTHER TITLE', ARRAY[]::text[], 900002, 'TV', 2001, 'DRAFT');
UPDATE cf.anime_franchises SET status = 'READY';
UPDATE cf.anime_titles SET status = 'READY';
INSERT INTO cf.research_candidates (research_candidate_id, anime_title_id, franchise_id, topic_key, topic_display, content_lane, trend_state, demand_signal, nostalgia_signal, editorial_potential, timeliness, signal_evidence, observation_window, dedupe_key, status, agent_run_id, agent_version)
  VALUES ('11111111-1111-4111-8111-111111111111', '22222222-2222-4222-8222-222222222222', '44444444-4444-4444-8444-444444444444', 'synthetic', 'Synthetic', 'EVERGREEN_DEMAND', 'EVERGREEN', 0.5, 0.5, 0.5, 0.5, '[1,2,3]'::jsonb, '2026-W42', repeat('a', 64), 'IDEA', '55555555-5555-4555-8555-555555555555', 'v0.1');
UPDATE cf.research_candidates SET status = 'READY';
INSERT INTO cf.research_candidates (research_candidate_id, anime_title_id, franchise_id, topic_key, topic_display, content_lane, trend_state, demand_signal, nostalgia_signal, editorial_potential, timeliness, signal_evidence, observation_window, dedupe_key, status, agent_run_id, agent_version)
  VALUES ('66666666-6666-4666-8666-666666666666', '33333333-3333-4333-8333-333333333333', '44444444-4444-4444-8444-444444444444', 'synthetic2', 'Synthetic 2', 'EVERGREEN_DEMAND', 'EVERGREEN', 0.5, 0.5, 0.5, 0.5, '[1,2,3]'::jsonb, '2026-W42', repeat('c', 64), 'IDEA', '55555555-5555-4555-8555-555555555555', 'v0.1');
UPDATE cf.research_candidates SET status = 'READY';
