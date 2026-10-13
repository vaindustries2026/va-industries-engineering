-- Local test helpers (created by the runner as the cluster owner; never part of any migration, never applied live).
CREATE SCHEMA IF NOT EXISTS cf_test; GRANT USAGE ON SCHEMA cf_test TO PUBLIC;
CREATE OR REPLACE FUNCTION cf_test.expect_true(p_name text, p_cond boolean) RETURNS void LANGUAGE plpgsql AS $$ BEGIN
  IF p_cond IS TRUE THEN RAISE NOTICE 'PASS %', p_name; ELSE RAISE NOTICE 'FAIL %', p_name; END IF; END $$;
-- Runs one statement in a sub-transaction as the CALLER (SECURITY INVOKER) and passes only when it fails with a SQLSTATE matching p_state (regex) and, optionally, a message matching p_msg.
CREATE OR REPLACE FUNCTION cf_test.expect_err(p_name text, p_stmt text, p_state text, p_msg text DEFAULT '') RETURNS void LANGUAGE plpgsql AS $$
DECLARE st text; m text;
BEGIN
  BEGIN EXECUTE p_stmt; RAISE NOTICE 'FAIL % (statement succeeded)', p_name; RETURN;
  EXCEPTION WHEN OTHERS THEN GET STACKED DIAGNOSTICS st = RETURNED_SQLSTATE, m = MESSAGE_TEXT; END;
  IF st ~ p_state AND m ~ p_msg THEN RAISE NOTICE 'PASS %', p_name; ELSE RAISE NOTICE 'FAIL % (got % : %)', p_name, st, left(m, 120); END IF;
END $$;
GRANT EXECUTE ON FUNCTION cf_test.expect_true(text, boolean), cf_test.expect_err(text, text, text, text) TO PUBLIC;
