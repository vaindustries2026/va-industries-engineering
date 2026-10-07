-- =============================================================================
-- Read-only post-apply verification for 0001_cf_sprint01
-- =============================================================================
-- Safe to run on mkeldytatorxxszjdngt right after the apply: one SELECT, no
-- writes. Every column must be true. The checks are the catalog checks of
-- 0001_cf_sprint01.TESTS.sql (S1-ISO-*, S1-PRIV-*, S1-GATE-00, T-RIGHTS-01,
-- T-PUB-01), which cannot be run as-is on Supabase because that file writes
-- fixture rows.
-- =============================================================================
SELECT
  (SELECT array_agg(relname::text ORDER BY relname) FROM pg_class
    WHERE relnamespace = 'cf'::regnamespace AND relkind IN ('r','p','v','m','f','S'))
    = ARRAY['agent_runs','allowed_transitions','anime_franchises','anime_titles','research_candidates','reviewers','system_flags']
    AS tables_exact,
  (SELECT array_agg(typname::text ORDER BY typname) FROM pg_type
    WHERE typnamespace = 'cf'::regnamespace AND typtype = 'e')
    = ARRAY['gate_code','gate_decision_value','lifecycle_status','run_state']
    AS enum_types_exact,
  (SELECT array_agg(proname::text ORDER BY proname) FROM pg_proc WHERE pronamespace = 'cf'::regnamespace)
    = ARRAY['forbid_delete','freeze_after_first_status','guard_status_transition','touch_updated_at']
    AS functions_exact,
  (SELECT count(*) FROM pg_trigger t JOIN pg_class c ON c.oid = t.tgrelid
    WHERE c.relnamespace = 'cf'::regnamespace AND NOT t.tgisinternal) = 12
    AS triggers_12,
  (SELECT count(*) FROM cf.allowed_transitions) = 14
    AND NOT EXISTS (SELECT 1 FROM cf.allowed_transitions WHERE required_gate IS NOT NULL OR mode = 'HUMAN_GATE')
    AND to_regclass('cf.gate_decisions') IS NULL
    AND NOT EXISTS (SELECT 1 FROM pg_proc WHERE proname = 'record_gate_decision')
    AS transitions_14_no_gates,
  (SELECT count(*) FROM cf.system_flags) = 3 AND NOT EXISTS (SELECT 1 FROM cf.system_flags WHERE enabled)
    AS kill_switches_off,
  NOT EXISTS (SELECT 1 FROM pg_constraint k JOIN pg_class r ON r.oid = k.confrelid
              WHERE k.connamespace = 'cf'::regnamespace AND k.contype = 'f' AND r.relnamespace <> 'cf'::regnamespace)
  AND NOT EXISTS (SELECT 1 FROM pg_proc WHERE pronamespace = 'cf'::regnamespace
                  AND (prosecdef OR prosrc ~* '\m(public|auth|storage|vault|extensions|net|cron|graphql|graphql_public|realtime|pgbouncer|supabase_[a-z_]+)\.'))
    AS no_cross_schema_refs,
  NOT EXISTS (SELECT 1 FROM information_schema.columns
              WHERE table_schema = 'cf' AND column_name ~* '(fair_?use|copyright_?safe|legal_?safe|is_legal|rights_?cleared)')
    AS no_legal_determination_columns,
  (SELECT rolcanlogin AND NOT rolinherit AND NOT rolbypassrls AND NOT rolsuper AND NOT rolcreatedb
          AND NOT rolcreaterole AND NOT rolreplication FROM pg_roles WHERE rolname = 'cf_n8n_runtime')
  AND NOT EXISTS (SELECT 1 FROM pg_auth_members WHERE member = 'cf_n8n_runtime'::regrole)
  AND NOT EXISTS (SELECT 1 FROM pg_class WHERE relowner = 'cf_n8n_runtime'::regrole)
    AS runtime_role_unchanged,
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
    AS no_access_for_supabase_api_roles_or_public;
