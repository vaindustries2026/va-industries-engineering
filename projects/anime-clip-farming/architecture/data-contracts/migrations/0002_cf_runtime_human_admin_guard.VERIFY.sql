-- =============================================================================
-- Read-only post-apply verification for 0002_cf_runtime_human_admin_guard
-- =============================================================================
-- Safe to run on mkeldytatorxxszjdngt right after the apply: one SELECT, no
-- writes. Every column must be true. Run 0001_cf_sprint01.VERIFY.sql as well.
-- guard_function_is_0002_exact compares the live function body with the body
-- that passed the local tests (md5 0dac745af135d4772111d92fd2b168c9).
-- runtime_role_passwordless is expected to turn false after the human sets the
-- role password; every other column must stay true.
-- =============================================================================
SELECT
  (SELECT md5(prosrc) = '0dac745af135d4772111d92fd2b168c9'
     AND position('CF_GOVERNANCE_DENIED' IN prosrc) > 0
     AND position('session_user = ''cf_n8n_runtime'' OR current_user = ''cf_n8n_runtime''' IN prosrc) > 0
   FROM pg_proc WHERE oid = to_regprocedure('cf.guard_status_transition()'))
    AS guard_function_is_0002_exact,
  (SELECT NOT prosecdef AND proowner = 'postgres'::regrole AND proconfig IS NULL
     AND NOT EXISTS (SELECT 1 FROM aclexplode(coalesce(proacl, acldefault('f', proowner))) a
                     WHERE a.grantee <> proowner)
   FROM pg_proc WHERE oid = to_regprocedure('cf.guard_status_transition()'))
    AS guard_function_invoker_owned_by_postgres_no_execute_grants,
  (SELECT count(*) FROM pg_trigger t
    WHERE t.tgfoid = to_regprocedure('cf.guard_status_transition()') AND NOT t.tgisinternal AND t.tgenabled = 'O') = 3
  AND (SELECT count(*) FROM pg_trigger t JOIN pg_class c ON c.oid = t.tgrelid
        WHERE c.relnamespace = 'cf'::regnamespace AND NOT t.tgisinternal AND t.tgenabled = 'O') = 12
    AS guard_triggers_bound_and_enabled,
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
  (SELECT array_agg(object_type || ':' || from_status || '>' || to_status ORDER BY object_type, from_status, to_status)
   FROM cf.allowed_transitions WHERE mode = 'HUMAN_ADMIN')
    = ARRAY['anime_franchise:BLOCKED>READY','anime_franchise:READY>RETIRED','anime_title:BLOCKED>READY','anime_title:READY>RETIRED']
    AS human_admin_edges_are_the_four_accepted,
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
    AS no_cross_schema_refs;
