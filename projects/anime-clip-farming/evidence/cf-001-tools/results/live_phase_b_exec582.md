# Phase B live: n8n execution 582 (workflow lNeYt1t1KmMxn5mn, credential e08pNFP1Th42jXyO, role cf_n8n_runtime)
Probe: current_user=session_user=cf_n8n_runtime; queryReplacement params containing commas, quotes and JSON arrived as single values; counts runs/franchises/titles/candidates=0; flags all false.
Negative suite (DO block, ended by RAISE EXCEPTION so everything rolled back): CF001_NEG_REPORT pass=53 fail=0
Covers: DELETE/TRUNCATE denied, reviewers/system_flags/allowed_transitions writes denied, CREATE/ALTER/trigger-disable/SET ROLE/session_replication_role denied (42501),
EXECUTE on 4 cf functions denied, HUMAN_ADMIN transitions denied (CF_GOVERNANCE_DENIED), freeze (CF_IMMUTABLE_ROW 23514), unique 23505, CHECK 23514, FK 23503,
positive controls P01/P02 (ON CONFLICT DO NOTHING = 0 rows; DRAFT/IDEA->READY as runtime), GRANT grants nothing, kill switches false.
Post-run check as postgres (read-only): runs=0 franchises=0 titles=0 candidates=0, transitions=14, flags false, runtime DELETE privilege false.
