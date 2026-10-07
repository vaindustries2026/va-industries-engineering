#!/usr/bin/env bash
# Local-only preflight test harness for Engine 2 Sprint 1 (never touches Supabase).
# Runs as root, starts throwaway PostgreSQL clusters as the unprivileged user pgtest.
# Environment used on 2026-10-07: Ubuntu 24.04 container; PostgreSQL 16.15 from the Ubuntu package;
# PostgreSQL 17.10 binaries from npm @embedded-postgres/linux-x64@17.10.0-beta.17 (tarball sha256
# 5bad48012c3a7415c06310f632ce9a0f9da20dadb70e774e4985c2f416a4445b) extracted to /home/pgtest/pg17dist,
# because the PostgreSQL apt repository is blocked by the container's network policy.
# Clusters listen on unix sockets only (listen_addresses='') and are deleted at the end of each run.
set -uo pipefail

REPO=/home/claude/va-industries-engineering
PKG=projects/anime-clip-farming/architecture/data-contracts
WORK=/home/pgtest/work
OUT=${1:-/tmp/preflight_output.txt}

rm -rf "$WORK"; mkdir -p "$WORK"
git -C "$REPO" show 5190db5:$PKG/migrations-draft/0001_cf_backbone.DESIGN_ONLY.sql  > "$WORK/orig_design.sql"
git -C "$REPO" show 5190db5:$PKG/migrations-draft/0001_cf_backbone.STATIC_TESTS.sql > "$WORK/orig_tests.sql"
cp "$REPO/$PKG/migrations-draft/0001_cf_backbone.DESIGN_ONLY.sql"  "$WORK/rev_design.sql"
cp "$REPO/$PKG/migrations-draft/0001_cf_backbone.STATIC_TESTS.sql" "$WORK/rev_tests.sql"
cp "$REPO/$PKG/migrations/0001_cf_sprint01.sql"          "$WORK/s1.sql"
cp "$REPO/$PKG/migrations/0001_cf_sprint01.TESTS.sql"    "$WORK/s1_tests.sql"
cp "$REPO/$PKG/migrations/0001_cf_sprint01.ROLLBACK.sql" "$WORK/s1_rollback.sql"
cp "$REPO/$PKG/migrations/0001_cf_sprint01.VERIFY.sql"   "$WORK/s1_verify.sql"
chown -R pgtest:pgtest "$WORK"

PSQL=/usr/lib/postgresql/16/bin/psql
PASS=0; FAIL=0
log() { echo "$*" | tee -a "$OUT"; }
check() { # check <id> <description> <condition-exit-code>
  if [ "$3" -eq 0 ]; then PASS=$((PASS+1)); log "PASS $1 $2"; else FAIL=$((FAIL+1)); log "FAIL $1 $2"; fi
}

start_cluster() { # start_cluster <tag> <bindir> <port> [ld_library_path]
  local tag=$1 bin=$2 port=$3 ld=${4:-}
  local data=/home/pgtest/pf$tag sock=/home/pgtest/sock$tag
  runuser -u pgtest -- bash -c "rm -rf $data $sock; mkdir -p $sock"
  runuser -u pgtest -- env LD_LIBRARY_PATH="$ld" "$bin/initdb" -D "$data" -U pgtest --auth=trust -E UTF8 --locale=C.UTF-8 >/dev/null
  runuser -u pgtest -- env LD_LIBRARY_PATH="$ld" "$bin/pg_ctl" -D "$data" -l "$data/server.log" -w \
     -o "-k $sock -p $port -c listen_addresses=''" start >/dev/null
}
stop_cluster() { # stop_cluster <tag> <bindir> [ld]
  local tag=$1 bin=$2 ld=${3:-}
  runuser -u pgtest -- env LD_LIBRARY_PATH="$ld" "$bin/pg_ctl" -D /home/pgtest/pf$tag -m fast stop >/dev/null
  runuser -u pgtest -- rm -rf /home/pgtest/pf$tag /home/pgtest/sock$tag
}

# q <tag> <port> <user> <db> [psql args...]  -> runs psql as pgtest OS user
q() { local tag=$1 port=$2 user=$3 db=$4; shift 4
  runuser -u pgtest -- "$PSQL" -X -q -h /home/pgtest/sock$tag -p "$port" -U "$user" -d "$db" -v ON_ERROR_STOP=1 "$@"; }

supabase_like_roles() { # mirrors the Supabase shape that matters here
  local tag=$1 port=$2
  q "$tag" "$port" pgtest postgres <<'SQL'
CREATE ROLE postgres LOGIN NOSUPERUSER INHERIT CREATEROLE CREATEDB REPLICATION BYPASSRLS;
CREATE ROLE anon NOLOGIN NOINHERIT;
CREATE ROLE authenticated NOLOGIN NOINHERIT;
CREATE ROLE service_role NOLOGIN NOINHERIT BYPASSRLS;
SQL
}
newdb() { local tag=$1 port=$2 db=$3; q "$tag" "$port" pgtest postgres -c "CREATE DATABASE $db OWNER postgres"; }
provision_runtime_role() { # exact statement used on the live project, run as the non-superuser postgres
  q "$1" "$2" postgres postgres -c "create role cf_n8n_runtime with login noinherit nobypassrls nosuperuser nocreatedb nocreaterole noreplication password null;"
}
count_pass() { grep -c '^NOTICE:  PASS' "$1"; }
count_fail() { grep -c 'FAIL' "$1"; }

run_version() { # run_version <tag> <bindir> <port> <ld>
  local tag=$1 bin=$2 port=$3 ld=$4 tmp
  start_cluster "$tag" "$bin" "$port" "$ld"
  local ver; ver=$(q "$tag" "$port" pgtest postgres -At -c "select version()")
  log ""; log "=== Cluster $tag: $ver ==="

  # --- Run A: original Sprint 0 files (commit 5190db5), exactly as Sprint 0 ran them (superuser) ---
  q "$tag" "$port" pgtest postgres -c "CREATE DATABASE a_orig"
  tmp=$WORK/A_$tag.txt
  { q "$tag" "$port" pgtest a_orig -f "$WORK/orig_design.sql" && q "$tag" "$port" pgtest a_orig -At <"$WORK/orig_tests.sql"; } >"$tmp" 2>&1
  local rc=$?; chown pgtest "$tmp" 2>/dev/null
  log "--- A ($tag) original Sprint 0 design + 33 static tests: exit=$rc pass=$(count_pass "$tmp") fail=$(count_fail "$tmp")"
  grep -v '^$' "$tmp" | sed 's/^/    /' >>"$OUT"
  [ "$rc" -eq 0 ] && [ "$(count_pass "$tmp")" -eq 33 ] && [ "$(count_fail "$tmp")" -eq 0 ]; check "A-$tag" "original 33 static tests pass on the Sprint 0 design" $?
  q "$tag" "$port" pgtest postgres -c "DROP DATABASE a_orig" -c "DROP ROLE cf_agent" -c "DROP ROLE cf_governance"

  # --- Supabase-like roles for every later run ---
  supabase_like_roles "$tag" "$port"

  # --- Guard G-01: runtime role missing (before provisioning) ---
  newdb "$tag" "$port" g01
  q "$tag" "$port" postgres g01 --single-transaction -f "$WORK/s1.sql" >"$WORK/g01.txt" 2>&1; rc=$?
  grep -q 'CF_WRONG_TARGET: role cf_n8n_runtime does not exist' "$WORK/g01.txt" && [ $rc -ne 0 ] \
    && [ "$(q "$tag" "$port" pgtest g01 -At -c "select count(*) from pg_namespace where nspname='cf'")" = 0 ]
  check "G-01-$tag" "migration aborts and creates nothing when cf_n8n_runtime is missing" $?

  # --- Provisioning step (same statement as live) ---
  provision_runtime_role "$tag" "$port"

  # --- Guard G-02: wrong role attributes ---
  newdb "$tag" "$port" g02
  q "$tag" "$port" postgres postgres -c "alter role cf_n8n_runtime inherit"
  q "$tag" "$port" postgres g02 --single-transaction -f "$WORK/s1.sql" >"$WORK/g02.txt" 2>&1; rc=$?
  q "$tag" "$port" postgres postgres -c "alter role cf_n8n_runtime noinherit"
  grep -q 'CF_WRONG_TARGET: cf_n8n_runtime must be LOGIN NOINHERIT' "$WORK/g02.txt" && [ $rc -ne 0 ] \
    && [ "$(q "$tag" "$port" pgtest g02 -At -c "select count(*) from pg_namespace where nspname='cf'")" = 0 ]
  check "G-02-$tag" "migration aborts and creates nothing when the role is INHERIT" $?

  # --- Guard G-03: role is a member of another role ---
  newdb "$tag" "$port" g03
  q "$tag" "$port" pgtest postgres -c "grant authenticated to cf_n8n_runtime"
  q "$tag" "$port" postgres g03 --single-transaction -f "$WORK/s1.sql" >"$WORK/g03.txt" 2>&1; rc=$?
  q "$tag" "$port" pgtest postgres -c "revoke authenticated from cf_n8n_runtime"
  grep -q 'CF_WRONG_TARGET: cf_n8n_runtime must not be a member of any role' "$WORK/g03.txt" && [ $rc -ne 0 ]
  check "G-03-$tag" "migration aborts when the role belongs to another role" $?

  # --- Guard G-04: a database shaped like the shared VA-Company-Brain project ---
  newdb "$tag" "$port" g04
  q "$tag" "$port" postgres g04 -c "create table public.episode_scripts (id int); create table public.asset_registry (id int)"
  q "$tag" "$port" postgres g04 --single-transaction -f "$WORK/s1.sql" >"$WORK/g04.txt" 2>&1; rc=$?
  grep -q 'CF_WRONG_TARGET: YouTube Kids tables found' "$WORK/g04.txt" && [ $rc -ne 0 ] \
    && [ "$(q "$tag" "$port" pgtest g04 -At -c "select count(*) from pg_namespace where nspname='cf'")" = 0 ]
  check "G-04-$tag" "migration aborts on a database that has the YouTube Kids tables" $?
  q "$tag" "$port" postgres g04 --single-transaction -f "$WORK/s1_rollback.sql" >"$WORK/r01.txt" 2>&1; rc=$?
  grep -q 'CF_WRONG_TARGET: YouTube Kids tables found' "$WORK/r01.txt" && [ $rc -ne 0 ] \
    && [ "$(q "$tag" "$port" pgtest g04 -At -c "select count(*) from pg_class where relname in ('episode_scripts','asset_registry')")" = 2 ]
  check "R-01-$tag" "rollback refuses to run on a database that has the YouTube Kids tables" $?

  # --- Run B: revised design (role change only) + the 33 static tests, DDL as non-superuser postgres ---
  newdb "$tag" "$port" b_rev
  tmp=$WORK/B_$tag.txt
  { q "$tag" "$port" postgres b_rev -f "$WORK/rev_design.sql" && q "$tag" "$port" pgtest b_rev -At <"$WORK/rev_tests.sql"; } >"$tmp" 2>&1; rc=$?
  log "--- B ($tag) revised design (ADR-001 roles) + 33 static tests: exit=$rc pass=$(count_pass "$tmp") fail=$(count_fail "$tmp")"
  grep -v '^$' "$tmp" | sed 's/^/    /' >>"$OUT"
  [ "$rc" -eq 0 ] && [ "$(count_pass "$tmp")" -eq 33 ] && [ "$(count_fail "$tmp")" -eq 0 ]; check "B-$tag" "33 static tests pass on the revised design, DDL applied by non-superuser postgres" $?
  q "$tag" "$port" pgtest postgres -c "DROP DATABASE b_rev" -c "DROP ROLE cf_governance"

  # --- Run C: Sprint 1 migration as non-superuser postgres in one transaction, then its tests ---
  newdb "$tag" "$port" c_s1
  tmp=$WORK/C_$tag.txt
  { q "$tag" "$port" postgres c_s1 --single-transaction -f "$WORK/s1.sql" && q "$tag" "$port" pgtest c_s1 -At <"$WORK/s1_tests.sql"; } >"$tmp" 2>&1; rc=$?
  local expected_c; expected_c=$(grep -cE "cf_test\.expect_(true|error)\('" "$WORK/s1_tests.sql")
  log "--- C ($tag) Sprint 1 migration + its tests: exit=$rc pass=$(count_pass "$tmp")/$expected_c fail=$(count_fail "$tmp")"
  grep -v '^$' "$tmp" | sed 's/^/    /' >>"$OUT"
  [ "$rc" -eq 0 ] && [ "$(count_pass "$tmp")" -eq "$expected_c" ] && [ "$(count_fail "$tmp")" -eq 0 ]; check "C-$tag" "Sprint 1 migration applies as non-superuser and all its tests pass" $?

  # --- Read-only verification query (the one to run on Supabase after the apply) ---
  local v; v=$(q "$tag" "$port" postgres c_s1 -At -F, -f "$WORK/s1_verify.sql" 2>&1)
  [ "$v" = "t,t,t,t,t,t,t,t,t,t,t" ]; check "V-01-$tag" "read-only verification query returns all true, run as postgres ($v)" $?
  q "$tag" "$port" postgres c_s1 -c "grant delete on cf.reviewers to cf_n8n_runtime"
  v=$(q "$tag" "$port" postgres c_s1 -At -F, -f "$WORK/s1_verify.sql" 2>&1)
  q "$tag" "$port" postgres c_s1 -c "revoke delete on cf.reviewers from cf_n8n_runtime"
  [ "$v" = "t,t,t,t,t,t,t,t,t,f,t" ]; check "V-02-$tag" "verification catches an extra privilege (runtime_privileges_exact=false: $v)" $?

  # --- Guard G-05: second apply is refused ---
  q "$tag" "$port" postgres c_s1 --single-transaction -f "$WORK/s1.sql" >"$WORK/g05.txt" 2>&1; rc=$?
  grep -q 'CF_ALREADY_APPLIED' "$WORK/g05.txt" && [ $rc -ne 0 ]
  check "G-05-$tag" "a second apply is refused" $?

  # --- Rollback R-02: fails closed when something else lives in cf ---
  q "$tag" "$port" postgres c_s1 -c "create table cf.not_from_0001 (x int)"
  q "$tag" "$port" postgres c_s1 --single-transaction -f "$WORK/s1_rollback.sql" >"$WORK/r02.txt" 2>&1; rc=$?
  grep -q 'cannot drop schema cf because other objects depend on it' "$WORK/r02.txt" && [ $rc -ne 0 ] \
    && [ "$(q "$tag" "$port" pgtest c_s1 -At -c "select count(*) from pg_class where relnamespace = 'cf'::regnamespace and relkind = 'r'")" = 8 ]
  check "R-02-$tag" "rollback stops and changes nothing when an object it did not create is in cf" $?
  q "$tag" "$port" postgres c_s1 -c "drop table cf.not_from_0001"

  # --- Rollback R-03: fails closed when an object outside cf depends on a cf table ---
  q "$tag" "$port" postgres c_s1 -c "create view public.depends_on_cf as select research_candidate_id from cf.research_candidates"
  q "$tag" "$port" postgres c_s1 --single-transaction -f "$WORK/s1_rollback.sql" >"$WORK/r03.txt" 2>&1; rc=$?
  grep -q 'because other objects depend on them' "$WORK/r03.txt" && [ $rc -ne 0 ] \
    && [ "$(q "$tag" "$port" pgtest c_s1 -At -c "select count(*) from pg_namespace where nspname='cf'")" = 1 ]
  check "R-03-$tag" "rollback stops when an object outside cf depends on cf" $?
  sed 's/^/    /' "$WORK/r03.txt" >>"$OUT"
  q "$tag" "$port" postgres c_s1 -c "drop view public.depends_on_cf"

  # --- Rollback R-04: clean rollback (with CF-001 fixture rows present), then re-apply and re-test ---
  q "$tag" "$port" postgres c_s1 --single-transaction -f "$WORK/s1_rollback.sql" >"$WORK/r04.txt" 2>&1; rc=$?
  local left; left=$(q "$tag" "$port" pgtest c_s1 -At -c "select (select count(*) from pg_namespace where nspname='cf') || ',' || (select count(*) from pg_roles where rolname='cf_n8n_runtime') || ',' || (select count(*) from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname not in ('pg_catalog','information_schema','pg_toast','cf_test') and has_table_privilege('cf_n8n_runtime', c.oid, 'SELECT'))")
  [ $rc -eq 0 ] && [ "$left" = "0,1,0" ]
  check "R-04-$tag" "clean rollback removes schema cf and its rows, keeps cf_n8n_runtime with no table access (cf,role,tables=$left)" $?
  q "$tag" "$port" pgtest c_s1 -c "drop schema cf_test cascade"
  tmp=$WORK/C2_$tag.txt
  { q "$tag" "$port" postgres c_s1 --single-transaction -f "$WORK/s1.sql" && q "$tag" "$port" pgtest c_s1 -At <"$WORK/s1_tests.sql"; } >"$tmp" 2>&1; rc=$?
  [ "$rc" -eq 0 ] && [ "$(count_pass "$tmp")" -eq "$expected_c" ] && [ "$(count_fail "$tmp")" -eq 0 ]
  check "R-05-$tag" "re-apply after rollback succeeds and all Sprint 1 tests pass again" $?

  stop_cluster "$tag" "$bin" "$ld"
}

: >"$OUT"
log "# Engine 2 pre-Sprint 1 local preflight test run (throwaway clusters inside the engineering container; never Supabase)"
log "# Run: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
for f in orig_design.sql orig_tests.sql rev_design.sql rev_tests.sql s1.sql s1_tests.sql s1_rollback.sql s1_verify.sql; do
  log "# sha256 $(sha256sum "$WORK/$f" | cut -c1-64)  $f"
done

run_version 16 /usr/lib/postgresql/16/bin 54329 ""
P17=/home/pgtest/pg17dist/package/native
run_version 17 "$P17/bin" 54331 "$P17/lib"

log ""
log "SUMMARY: $PASS harness checks passed, $FAIL failed"
[ "$FAIL" -eq 0 ] && rm -rf "$WORK"
[ "$FAIL" -eq 0 ]
