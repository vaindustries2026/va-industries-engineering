-- =============================================================================
-- Read-only post-apply verification for 0003_cf_freeze_generated_columns_and_search_path
-- =============================================================================
-- Safe to run on mkeldytatorxxszjdngt right after the apply: one SELECT, no
-- writes. Every column must be true. Compares the live function bodies with the
-- bodies that passed the local tests. runtime_role_passwordless is expected to
-- turn false after the human sets the role password; every other column must
-- stay true. Needs to read pg_authid (the postgres role can on Supabase).
-- =============================================================================
SELECT
  (SELECT md5(prosrc) = 'f957a25df6e08a74a21b6a64e5181a47' AND position('attgenerated' IN prosrc) > 0
   FROM pg_proc WHERE oid = to_regprocedure('cf.freeze_after_first_status()'))
    AS freeze_function_is_0003_exact,
  (SELECT md5(prosrc) = '0dac745af135d4772111d92fd2b168c9'
     AND position('CF_GOVERNANCE_DENIED' IN prosrc) > 0
     AND position('session_user = ''cf_n8n_runtime'' OR current_user = ''cf_n8n_runtime''' IN prosrc) > 0
   FROM pg_proc WHERE oid = to_regprocedure('cf.guard_status_transition()'))
    AS guard_body_is_0002_exact_with_human_admin_block,
  (SELECT md5(prosrc) = '4097ad56aa56e6835ce9d375769fc6ba' FROM pg_proc WHERE oid = to_regprocedure('cf.forbid_delete()'))
  AND (SELECT md5(prosrc) = 'c28bbd99ced3dfcd7ff6c2a1298a90e1' FROM pg_proc WHERE oid = to_regprocedure('cf.touch_updated_at()'))
    AS forbid_and_touch_bodies_unchanged,
  (SELECT count(*) = 4 AND bool_and(coalesce(proconfig = ARRAY['search_path=pg_catalog, cf'], false))
   FROM pg_proc WHERE pronamespace = 'cf'::regnamespace)
    AS all_four_search_paths_pinned_to_pg_catalog_cf,
  (SELECT bool_and(NOT prosecdef AND proowner = 'postgres'::regrole
                   AND NOT EXISTS (SELECT 1 FROM aclexplode(coalesce(proacl, acldefault('f', proowner))) a
                                   WHERE a.grantee <> proowner))
   FROM pg_proc WHERE pronamespace = 'cf'::regnamespace)
    AS all_four_invoker_owned_by_postgres_no_execute_grants,
  (SELECT count(*) FROM pg_trigger t JOIN pg_class c ON c.oid = t.tgrelid
    WHERE c.relnamespace = 'cf'::regnamespace AND NOT t.tgisinternal AND t.tgenabled = 'O') = 12
  AND (SELECT count(*) FROM pg_trigger t
        WHERE t.tgfoid = to_regprocedure('cf.guard_status_transition()') AND NOT t.tgisinternal) = 3
  AND (SELECT count(*) FROM pg_trigger t
        WHERE t.tgfoid = to_regprocedure('cf.freeze_after_first_status()') AND NOT t.tgisinternal) = 3
    AS triggers_bound_and_enabled,
  (SELECT array_agg(proname::text ORDER BY proname) FROM pg_proc WHERE pronamespace = 'cf'::regnamespace)
    = ARRAY['forbid_delete','freeze_after_first_status','guard_status_transition','touch_updated_at']
  AND (SELECT array_agg(relname::text ORDER BY relname) FROM pg_class
        WHERE relnamespace = 'cf'::regnamespace AND relkind IN ('r','p','v','m','f','S'))
    = ARRAY['agent_runs','allowed_transitions','anime_franchises','anime_titles','research_candidates','reviewers','system_flags']
    AS inventory_unchanged,
  (SELECT count(*) = 14
          AND md5(string_agg(concat_ws('|', object_type, from_status, to_status,
                coalesce(required_gate::text, ''), coalesce(required_decision::text, ''), mode), ';'
                ORDER BY object_type, from_status, to_status)) = '6ea6f7a4fafee461dc64345d400b648c'
   FROM cf.allowed_transitions)
    AS transition_rows_unchanged,
  (SELECT array_agg(a.attname::text ORDER BY a.attname) FROM pg_attribute a
    WHERE a.attrelid = 'cf.anime_titles'::regclass AND a.attnum > 0 AND NOT a.attisdropped AND a.attgenerated <> '')
    = ARRAY['era_decade']
    AS only_generated_column_is_era_decade,
  (SELECT rolcanlogin AND NOT rolinherit AND NOT rolbypassrls AND NOT rolsuper AND NOT rolcreatedb
          AND NOT rolcreaterole AND NOT rolreplication FROM pg_roles WHERE rolname = 'cf_n8n_runtime')
  AND NOT EXISTS (SELECT 1 FROM pg_auth_members WHERE member = 'cf_n8n_runtime'::regrole)
  AND NOT EXISTS (SELECT 1 FROM pg_class WHERE relowner = 'cf_n8n_runtime'::regrole)
    AS runtime_role_attributes_exact,
  (SELECT rolpassword IS NULL FROM pg_authid WHERE rolname = 'cf_n8n_runtime')
    AS runtime_role_passwordless,
  has_schema_privilege('cf_n8n_runtime', 'cf', 'USAGE')
  AND NOT has_schema_privilege('cf_n8n_runtime', 'cf', 'CREATE')
  AND NOT EXISTS (
        SELECT 1
        FROM pg_class c
        CROSS JOIN unnest(ARRAY['SELECT','INSERT','UPDATE','DELETE','TRUNCATE','REFERENCES','TRIGGER']) AS p(priv)
        WHERE c.relnamespace = 'cf'::regnamespace AND c.relkind = 'r'
          AND has_table_privilege('cf_n8n_runtime', c.oid, p.priv)
              <> (p.priv = 'SELECT'
                  OR (p.priv IN ('INSERT','UPDATE')
                      AND c.relname IN ('agent_runs','anime_franchises','anime_titles','research_candidates'))))
  AND NOT EXISTS (SELECT 1 FROM pg_proc WHERE pronamespace = 'cf'::regnamespace
                  AND has_function_privilege('cf_n8n_runtime', oid, 'EXECUTE'))
    AS runtime_privileges_exact,
  NOT EXISTS (
    SELECT 1 FROM pg_roles r
    WHERE r.rolname IN ('anon','authenticated','service_role')
      AND (has_schema_privilege(r.oid, 'cf', 'USAGE')
           OR EXISTS (SELECT 1 FROM pg_class c
                      CROSS JOIN unnest(ARRAY['SELECT','INSERT','UPDATE','DELETE','TRUNCATE']) AS p(priv)
                      WHERE c.relnamespace = 'cf'::regnamespace AND c.relkind = 'r'
                        AND has_table_privilege(r.oid, c.oid, p.priv))))
  AND NOT EXISTS (SELECT 1 FROM pg_class c, aclexplode(coalesce(c.relacl, acldefault('r', c.relowner))) a
                  WHERE c.relnamespace = 'cf'::regnamespace AND a.grantee = 0)
  AND NOT EXISTS (SELECT 1 FROM pg_proc f, aclexplode(coalesce(f.proacl, acldefault('f', f.proowner))) a
                  WHERE f.pronamespace = 'cf'::regnamespace AND a.grantee = 0)
    AS no_access_for_supabase_api_roles_or_public,
  NOT EXISTS (SELECT 1 FROM pg_constraint k JOIN pg_class r ON r.oid = k.confrelid
              WHERE k.connamespace = 'cf'::regnamespace AND k.contype = 'f' AND r.relnamespace <> 'cf'::regnamespace)
  AND NOT EXISTS (SELECT 1 FROM pg_proc WHERE pronamespace = 'cf'::regnamespace
                  AND (prosecdef OR prosrc ~* '\m(public|auth|storage|vault|extensions|net|cron|graphql|graphql_public|realtime|pgbouncer|supabase_[a-z_]+)\.'))
    AS no_cross_schema_refs,
  (SELECT count(*) FROM cf.agent_runs) + (SELECT count(*) FROM cf.anime_franchises) + (SELECT count(*) FROM cf.anime_titles)
  + (SELECT count(*) FROM cf.research_candidates) + (SELECT count(*) FROM cf.reviewers) = 0
    AS no_data_rows_left_behind;
