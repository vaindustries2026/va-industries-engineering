-- =============================================================================
-- Read-only post-apply verification for 0004_cf002_scene_intelligence
-- =============================================================================
-- Safe to run on mkeldytatorxxszjdngt right after the apply: one SELECT, no
-- writes. Every column must be true, except runtime_role_has_password, which
-- is informational (the human has set the role password; it must not be
-- inspected). Also re-checks what the 0003 VERIFY checked for the old objects
-- (function bodies F-2/F-6/F-7, original 14 transition rows by hash).
-- =============================================================================
SELECT
  (SELECT md5(prosrc) = 'f957a25df6e08a74a21b6a64e5181a47' FROM pg_proc WHERE oid = to_regprocedure('cf.freeze_after_first_status()'))
    AS f6_freeze_function_exact,
  (SELECT md5(prosrc) = '0dac745af135d4772111d92fd2b168c9' AND position('CF_GOVERNANCE_DENIED' IN prosrc) > 0
   FROM pg_proc WHERE oid = to_regprocedure('cf.guard_status_transition()'))
    AS f2_guard_body_exact_with_human_admin_block,
  (SELECT md5(prosrc) = '4097ad56aa56e6835ce9d375769fc6ba' FROM pg_proc WHERE oid = to_regprocedure('cf.forbid_delete()'))
  AND (SELECT md5(prosrc) = 'c28bbd99ced3dfcd7ff6c2a1298a90e1' FROM pg_proc WHERE oid = to_regprocedure('cf.touch_updated_at()'))
    AS forbid_and_touch_exact,
  (SELECT count(*) = 4 AND bool_and(proconfig = ARRAY['search_path=pg_catalog, cf'] AND NOT prosecdef AND proowner = 'postgres'::regrole)
   FROM pg_proc WHERE pronamespace = 'cf'::regnamespace)
    AS f7_four_functions_pinned_invoker_postgres_owned,
  NOT EXISTS (SELECT 1 FROM pg_proc p, aclexplode(coalesce(p.proacl, acldefault('f', p.proowner))) a
               WHERE p.pronamespace = 'cf'::regnamespace AND a.grantee <> p.proowner)
    AS no_function_execute_grants,
  (SELECT count(*) FROM pg_trigger t JOIN pg_class c ON c.oid = t.tgrelid
    WHERE c.relnamespace = 'cf'::regnamespace AND NOT t.tgisinternal AND t.tgenabled = 'O') = 20
    AS twenty_triggers_enabled,
  (SELECT array_agg(relname::text ORDER BY relname) FROM pg_class
    WHERE relnamespace = 'cf'::regnamespace AND relkind IN ('r','p','v','m','f','S'))
    = ARRAY['agent_runs','allowed_transitions','anime_franchises','anime_scene_intelligence','anime_source_episodes','anime_titles',
            'research_candidates','reviewers','system_flags','v_scene_publication_status']
    AS inventory_exact_10_objects,
  (SELECT count(*) = 25 FROM cf.allowed_transitions) AS transitions_25,
  (SELECT md5(string_agg(concat_ws('|', object_type, from_status, to_status, coalesce(required_gate::text, ''),
                coalesce(required_decision::text, ''), mode), ';' ORDER BY object_type, from_status, to_status)) = '6ea6f7a4fafee461dc64345d400b648c'
   FROM cf.allowed_transitions WHERE object_type IN ('anime_franchise', 'anime_title', 'research_candidate'))
    AS original_14_transition_rows_unchanged,
  (SELECT count(*) = 11 AND count(*) FILTER (WHERE mode = 'DETERMINISTIC') = 6 AND count(*) FILTER (WHERE mode = 'HUMAN_ADMIN') = 5
   FROM cf.allowed_transitions WHERE object_type IN ('anime_source_episode', 'scene'))
    AS new_11_rows_6_deterministic_5_human_admin,
  NOT EXISTS (SELECT 1 FROM cf.allowed_transitions WHERE mode = 'HUMAN_GATE')
    AS no_human_gate_edges,
  NOT EXISTS (SELECT 1 FROM cf.allowed_transitions WHERE to_status IN ('APPROVED', 'PUBLISHED'))
    AS no_edge_to_approved_or_published,
  NOT EXISTS (SELECT 1 FROM pg_attribute a WHERE a.attrelid = 'cf.anime_scene_intelligence'::regclass AND a.attnum > 0 AND NOT a.attisdropped
                AND a.attname ~* '(publication|rights|licen|fair_use|monetis|approv|cleared)')
    AS scene_has_no_publication_or_rights_column,
  (SELECT bool_and(publication_source_status = 'UNKNOWN') IS NOT FALSE FROM cf.v_scene_publication_status)
    AS every_scene_publication_status_unknown,
  has_table_privilege('cf_n8n_runtime', 'cf.anime_scene_intelligence', 'SELECT')
  AND has_table_privilege('cf_n8n_runtime', 'cf.anime_scene_intelligence', 'INSERT')
  AND has_table_privilege('cf_n8n_runtime', 'cf.anime_source_episodes', 'SELECT')
  AND has_table_privilege('cf_n8n_runtime', 'cf.anime_source_episodes', 'INSERT')
  AND has_table_privilege('cf_n8n_runtime', 'cf.v_scene_publication_status', 'SELECT')
    AS runtime_select_insert_ok,
  NOT (SELECT bool_or(has_table_privilege('cf_n8n_runtime', t, p))
         FROM unnest(ARRAY['cf.anime_scene_intelligence', 'cf.anime_source_episodes', 'cf.agent_runs', 'cf.anime_franchises',
                           'cf.anime_titles', 'cf.research_candidates', 'cf.reviewers', 'cf.system_flags', 'cf.allowed_transitions']) t,
              unnest(ARRAY['DELETE', 'TRUNCATE', 'REFERENCES', 'TRIGGER']) p)
    AS runtime_no_delete_truncate_references_trigger_anywhere,
  NOT has_table_privilege('cf_n8n_runtime', 'cf.anime_scene_intelligence', 'UPDATE')
  AND has_column_privilege('cf_n8n_runtime', 'cf.anime_scene_intelligence', 'status', 'UPDATE')
  AND has_column_privilege('cf_n8n_runtime', 'cf.anime_scene_intelligence', 'timestamps_human_verified', 'UPDATE')
  AND NOT has_column_privilege('cf_n8n_runtime', 'cf.anime_scene_intelligence', 'scene_summary', 'UPDATE')
  AND NOT has_column_privilege('cf_n8n_runtime', 'cf.anime_scene_intelligence', 'research_access_basis', 'UPDATE')
  AND NOT has_table_privilege('cf_n8n_runtime', 'cf.anime_source_episodes', 'UPDATE')
  AND has_column_privilege('cf_n8n_runtime', 'cf.anime_source_episodes', 'status', 'UPDATE')
    AS runtime_update_is_column_level_only,
  NOT has_table_privilege('cf_n8n_runtime', 'cf.reviewers', 'INSERT') AND NOT has_table_privilege('cf_n8n_runtime', 'cf.reviewers', 'UPDATE')
  AND NOT has_table_privilege('cf_n8n_runtime', 'cf.system_flags', 'UPDATE') AND NOT has_table_privilege('cf_n8n_runtime', 'cf.system_flags', 'INSERT')
  AND NOT has_table_privilege('cf_n8n_runtime', 'cf.allowed_transitions', 'INSERT') AND NOT has_table_privilege('cf_n8n_runtime', 'cf.allowed_transitions', 'UPDATE')
    AS runtime_no_governance_writes,
  NOT has_schema_privilege('cf_n8n_runtime', 'cf', 'CREATE') AND NOT has_schema_privilege('cf_n8n_runtime', 'public', 'CREATE')
    AS runtime_no_schema_create,
  NOT (SELECT bool_or(has_table_privilege(r, t, 'SELECT') OR has_table_privilege(r, t, 'INSERT') OR has_table_privilege(r, t, 'UPDATE'))
         FROM unnest(ARRAY['anon', 'authenticated', 'service_role']) r,
              unnest(ARRAY['cf.anime_scene_intelligence', 'cf.anime_source_episodes', 'cf.v_scene_publication_status']) t)
    AS supabase_api_roles_have_no_access,
  (SELECT rolcanlogin AND NOT rolinherit AND NOT rolbypassrls AND NOT rolsuper AND NOT rolcreatedb AND NOT rolcreaterole AND NOT rolreplication
   FROM pg_roles WHERE rolname = 'cf_n8n_runtime')
  AND NOT EXISTS (SELECT 1 FROM pg_auth_members WHERE member = 'cf_n8n_runtime'::regrole)
  AND NOT EXISTS (SELECT 1 FROM pg_class WHERE relowner = 'cf_n8n_runtime'::regrole)
    AS runtime_role_attributes_exact,
  NOT EXISTS (SELECT 1 FROM cf.system_flags WHERE enabled IS TRUE) AND (SELECT count(*) = 3 FROM cf.system_flags)
    AS kill_switches_all_false,
  to_regprocedure('cf.__set_runtime_password_once()') IS NULL
    AS password_helper_absent,
  (SELECT count(*) FROM pg_constraint WHERE conrelid = 'cf.anime_scene_intelligence'::regclass AND contype = 'f') = 5
    AS scene_five_foreign_keys,
  to_regclass('public.episode_scripts') IS NULL AND to_regclass('public.asset_registry') IS NULL
  AND to_regclass('public.production_plans') IS NULL AND to_regclass('public.videos') IS NULL
    AS no_youtube_kids_objects;
