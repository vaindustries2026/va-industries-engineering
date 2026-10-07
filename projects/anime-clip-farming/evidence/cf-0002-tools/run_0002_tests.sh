#!/usr/bin/env bash
# Local-only test harness for Engine 2 migration 0002_cf_runtime_human_admin_guard (never touches Supabase).
# Runs as root, starts throwaway PostgreSQL clusters as the unprivileged user pgtest, on unix sockets only
# (listen_addresses=''), with trust authentication so the tests can log in as cf_n8n_runtime without a password.
# Clusters mirror the Supabase shape that matters: a non-superuser `postgres` with CREATEROLE owns the
# databases and applies the migrations; anon / authenticated / service_role exist; cf_n8n_runtime is created
# by `postgres` with the exact statement used live.
# 0002 VERIFY reads pg_authid, which the local non-superuser postgres cannot; locally it is run as the superuser pgtest
# (on Supabase the postgres role can read it).
# Usage: run_0002_tests.sh <output-file> [pg16-bindir] [pg17-bindir pg17-libdir]
set -uo pipefail

REPO=/home/claude/va-industries-engineering
PKG=projects/anime-clip-farming/architecture/data-contracts/migrations
WORK=/home/pgtest/work2
OUT=${1:-/tmp/0002_output.txt}
PG16BIN=${2:-/usr/lib/postgresql/16/bin}
PG17BIN=${3:-}
PG17LIB=${4:-}

rm -rf "$WORK"; mkdir -p "$WORK"
for f in 0001_cf_sprint01.sql 0001_cf_sprint01.TESTS.sql 0001_cf_sprint01.VERIFY.sql 0001_cf_sprint01.ROLLBACK.sql \
         0002_cf_runtime_human_admin_guard.sql 0002_cf_runtime_human_admin_guard.ROLLBACK.sql \
         0002_cf_runtime_human_admin_guard.TESTS.sql 0002_cf_runtime_human_admin_guard.VERIFY.sql; do
  cp "$REPO/$PKG/$f" "$WORK/$f"
done
chown -R pgtest:pgtest "$WORK"
M1=$WORK/0001_cf_sprint01.sql;                    T1=$WORK/0001_cf_sprint01.TESTS.sql;  V1=$WORK/0001_cf_sprint01.VERIFY.sql
M2=$WORK/0002_cf_runtime_human_admin_guard.sql;   R2=$WORK/0002_cf_runtime_human_admin_guard.ROLLBACK.sql
T2=$WORK/0002_cf_runtime_human_admin_guard.TESTS.sql; V2=$WORK/0002_cf_runtime_human_admin_guard.VERIFY.sql
MD5_0001=eb7450cc84bc9e3d8c4ae4cd7d9187e3
MD5_0002=0dac745af135d4772111d92fd2b168c9

PSQL=$PG16BIN/psql
PASS=0; FAIL=0
log() { echo "$*" | tee -a "$OUT"; }
check() { if [ "$3" -eq 0 ]; then PASS=$((PASS+1)); log "PASS $1 $2"; else FAIL=$((FAIL+1)); log "FAIL $1 $2"; fi; }

start_cluster() { local tag=$1 bin=$2 port=$3 ld=${4:-}
  local data=/home/pgtest/pg2$tag sock=/home/pgtest/sk2$tag
  runuser -u pgtest -- bash -c "rm -rf $data $sock; mkdir -p $sock"
  runuser -u pgtest -- env LD_LIBRARY_PATH="$ld" "$bin/initdb" -D "$data" -U pgtest --auth=trust -E UTF8 --locale=C.UTF-8 >/dev/null
  runuser -u pgtest -- env LD_LIBRARY_PATH="$ld" "$bin/pg_ctl" -D "$data" -l "$data/server.log" -w \
     -o "-k $sock -p $port -c listen_addresses=''" start >/dev/null; }
stop_cluster() { local tag=$1 bin=$2 ld=${3:-}
  runuser -u pgtest -- env LD_LIBRARY_PATH="$ld" "$bin/pg_ctl" -D /home/pgtest/pg2$tag -m fast stop >/dev/null
  runuser -u pgtest -- rm -rf /home/pgtest/pg2$tag /home/pgtest/sk2$tag; }
q() { local tag=$1 port=$2 user=$3 db=$4; shift 4
  runuser -u pgtest -- "$PSQL" -X -q -h /home/pgtest/sk2$tag -p "$port" -U "$user" -d "$db" -v ON_ERROR_STOP=1 "$@"; }
newdb() { q "$1" "$2" pgtest postgres -c "CREATE DATABASE $3 OWNER postgres"; }
apply() { local tag=$1 port=$2 db=$3 file=$4 out=$5   # as non-superuser postgres, one transaction
  q "$tag" "$port" postgres "$db" --single-transaction -f "$file" >"$out" 2>&1; }
count_pass() { grep -c '^NOTICE:  PASS' "$1"; }
count_fail() { grep -c 'FAIL' "$1"; }
fnmd5() { q "$1" "$2" pgtest "$3" -At -c "select md5(prosrc) from pg_proc where oid = to_regprocedure('cf.guard_status_transition()')"; }
fresh() { local tag=$1 port=$2 db=$3; newdb "$tag" "$port" "$db"; apply "$tag" "$port" "$db" "$M1" "$WORK/apply1_$db.txt"; }

run_version() { local tag=$1 bin=$2 port=$3 ld=$4 rc ver v n
  start_cluster "$tag" "$bin" "$port" "$ld"
  ver=$(q "$tag" "$port" pgtest postgres -At -c "select version()")
  log ""; log "=== Cluster $tag: $ver ==="
  q "$tag" "$port" pgtest postgres <<'SQL'
CREATE ROLE postgres LOGIN NOSUPERUSER INHERIT CREATEROLE CREATEDB REPLICATION BYPASSRLS;
CREATE ROLE anon NOLOGIN NOINHERIT;
CREATE ROLE authenticated NOLOGIN NOINHERIT;
CREATE ROLE service_role NOLOGIN NOINHERIT BYPASSRLS;
SQL
  q "$tag" "$port" postgres postgres -c "create role cf_n8n_runtime with login noinherit nobypassrls nosuperuser nocreatedb nocreaterole noreplication password null;"

  # --- F-0: the defect on 0001 alone (proves the denial tests are not vacuous) ---
  fresh "$tag" "$port" before
  q "$tag" "$port" pgtest before -At >"$WORK/before_$tag.txt" 2>&1 <<'SQL'
SET ROLE cf_n8n_runtime;
INSERT INTO cf.anime_franchises (franchise_id, normalised_key, display_name) VALUES ('00000000-0000-4000-8000-0000000000e1','before one','Before One');
UPDATE cf.anime_franchises SET status = 'BLOCKED' WHERE franchise_id = '00000000-0000-4000-8000-0000000000e1';
UPDATE cf.anime_franchises SET status = 'READY'   WHERE franchise_id = '00000000-0000-4000-8000-0000000000e1';
UPDATE cf.anime_franchises SET status = 'RETIRED' WHERE franchise_id = '00000000-0000-4000-8000-0000000000e1';
SELECT 'STATUS=' || status FROM cf.anime_franchises WHERE franchise_id = '00000000-0000-4000-8000-0000000000e1';
SQL
  rc=$?; grep -q 'STATUS=RETIRED' "$WORK/before_$tag.txt" && [ $rc -eq 0 ]
  check "F0-$tag" "on 0001 alone the runtime role CAN do BLOCKED -> READY and READY -> RETIRED (finding F-2 reproduced)" $?

  # --- B: apply 0002 on top of 0001 and run its tests ---
  fresh "$tag" "$port" c1
  apply "$tag" "$port" c1 "$M2" "$WORK/apply2_c1_$tag.txt"; rc=$?
  [ $rc -eq 0 ] && [ "$(fnmd5 "$tag" "$port" c1)" = "$MD5_0002" ]
  check "B1-$tag" "0002 applies as non-superuser postgres in one transaction; guard body md5 = $MD5_0002" $?
  local out=$WORK/T2_$tag.txt expected
  q "$tag" "$port" pgtest c1 -At <"$T2" >"$out" 2>&1; rc=$?
  expected=$(grep -cE "cf_test\.expect_(true|error|denied|ok)\('" "$T2")
  log "--- 0002 tests ($tag): exit=$rc pass=$(count_pass "$out")/$expected fail=$(count_fail "$out")"
  grep -v '^$' "$out" | sed 's/^/    /' >>"$OUT"
  [ $rc -eq 0 ] && [ "$(count_pass "$out")" -eq "$expected" ] && [ "$(count_fail "$out")" -eq 0 ]
  check "B2-$tag" "all $expected 0002 tests pass (denials, deterministic path, admin path, real login, HUMAN_GATE compatibility)" $?

  # --- B3: the 33 Sprint 1 tests rerun on a database that has 0001 + 0002 ---
  fresh "$tag" "$port" c2
  apply "$tag" "$port" c2 "$M2" "$WORK/apply2_c2_$tag.txt"
  out=$WORK/T1_$tag.txt
  q "$tag" "$port" pgtest c2 -At <"$T1" >"$out" 2>&1; rc=$?
  expected=$(grep -cE "cf_test\.expect_(true|error)\('" "$T1")
  log "--- 0001 tests after 0002 ($tag): exit=$rc pass=$(count_pass "$out")/$expected fail=$(count_fail "$out")"
  grep -v '^$' "$out" | sed 's/^/    /' >>"$OUT"
  [ $rc -eq 0 ] && [ "$(count_pass "$out")" -eq "$expected" ] && [ "$expected" -eq 33 ] && [ "$(count_fail "$out")" -eq 0 ]
  check "B3-$tag" "all 33 Sprint 1 fail-closed tests still pass after 0002 (identity, dedupe, no-delete, freeze, paid, publication, privileges, isolation, CREATE)" $?

  # --- B4: both verification queries on a clean 0001 + 0002 database ---
  fresh "$tag" "$port" c3
  apply "$tag" "$port" c3 "$M2" "$WORK/apply2_c3_$tag.txt"
  v=$(q "$tag" "$port" postgres c3 -At -F, -f "$V1" 2>&1)
  [ "$v" = "t,t,t,t,t,t,t,t,t,t,t" ]; check "B4a-$tag" "0001 VERIFY returns all true after 0002 ($v)" $?
  v=$(q "$tag" "$port" pgtest c3 -At -F, -f "$V2" 2>&1)
  [ "$v" = "t,t,t,t,t,t,t,t,t,t,t" ]; check "B4b-$tag" "0002 VERIFY returns all true ($v)" $?
  q "$tag" "$port" postgres c3 -c "grant delete on cf.reviewers to cf_n8n_runtime"
  v=$(q "$tag" "$port" pgtest c3 -At -F, -f "$V2" 2>&1)
  q "$tag" "$port" postgres c3 -c "revoke delete on cf.reviewers from cf_n8n_runtime"
  [ "$v" = "t,t,t,t,t,t,t,t,f,t,t" ]; check "B4c-$tag" "0002 VERIFY catches an extra privilege (runtime_privileges_exact=false: $v)" $?
  q "$tag" "$port" postgres c3 -c "alter role cf_n8n_runtime password '$(head -c 12 /dev/urandom | od -An -tx1 | tr -d ' \n')'" >/dev/null 2>&1
  v=$(q "$tag" "$port" pgtest c3 -At -F, -f "$V2" 2>&1 | head -1)
  [ "$v" = "t,t,t,t,t,t,t,f,t,t,t" ]; check "B4d-$tag" "0002 VERIFY shows runtime_role_passwordless=false once a password exists ($v)" $?
  q "$tag" "$port" postgres c3 -c "alter role cf_n8n_runtime password null" >/dev/null 2>&1

  # --- K: finding F-6, an existing defect outside 0002 (documented, not fixed here) ---
  # cf.freeze_after_first_status compares to_jsonb(OLD) with to_jsonb(NEW); the stored generated column
  # era_decade is not yet computed in NEW during a BEFORE trigger, so any status change on a DATED title
  # that has left DRAFT raises CF_IMMUTABLE_ROW, for every role including the owner. This check pins the
  # current behaviour; if a later migration fixes the freeze function it will (rightly) start failing.
  fresh "$tag" "$port" k1
  q "$tag" "$port" pgtest k1 -At >"$WORK/k1_$tag.txt" 2>&1 <<'SQL'
INSERT INTO cf.anime_franchises (franchise_id, normalised_key, display_name) VALUES ('00000000-0000-4000-8000-0000000000e1','k one','K One');
INSERT INTO cf.anime_titles (anime_title_id, franchise_id, normalised_title_key, display_title, start_year)
  VALUES ('00000000-0000-4000-8000-0000000000e2','00000000-0000-4000-8000-0000000000e1','dated','Dated',2001);
UPDATE cf.anime_titles SET status = 'READY' WHERE anime_title_id = '00000000-0000-4000-8000-0000000000e2';
DO $$
BEGIN
  SET LOCAL ROLE postgres;
  BEGIN
    UPDATE cf.anime_titles SET status = 'RETIRED' WHERE anime_title_id = '00000000-0000-4000-8000-0000000000e2';
    RAISE NOTICE 'ADMIN_RESULT=succeeded';
  EXCEPTION WHEN others THEN RAISE NOTICE 'ADMIN_RESULT=%', left(SQLERRM, 20);
  END;
  RESET ROLE;
  SET LOCAL ROLE cf_n8n_runtime;
  BEGIN
    UPDATE cf.anime_titles SET status = 'RETIRED' WHERE anime_title_id = '00000000-0000-4000-8000-0000000000e2';
    RAISE NOTICE 'RUNTIME_RESULT=succeeded';
  EXCEPTION WHEN others THEN RAISE NOTICE 'RUNTIME_RESULT=%', left(SQLERRM, 20);
  END;
  RESET ROLE;
END $$;
SQL
  grep -q 'ADMIN_RESULT=CF_IMMUTABLE_ROW' "$WORK/k1_$tag.txt" && grep -q 'RUNTIME_RESULT=CF_IMMUTABLE_ROW' "$WORK/k1_$tag.txt"
  check "K1-$tag" "F-6 pinned: a dated READY title cannot change status for ANY role (CF_IMMUTABLE_ROW from the freeze trigger, before the status guard)" $?
  sed 's/^/    /' "$WORK/k1_$tag.txt" >>"$OUT"

  # --- G: guard branches of 0002 ---
  newdb "$tag" "$port" g1
  apply "$tag" "$port" g1 "$M2" "$WORK/g1.txt"; rc=$?
  grep -q 'CF_PRECONDITION: migration 0001_cf_sprint01 is not applied' "$WORK/g1.txt" && [ $rc -ne 0 ]
  check "G2-01-$tag" "0002 refuses a database where 0001 is not applied" $?

  fresh "$tag" "$port" g2
  q "$tag" "$port" postgres postgres -c "alter role cf_n8n_runtime inherit"
  apply "$tag" "$port" g2 "$M2" "$WORK/g2.txt"; rc=$?
  q "$tag" "$port" postgres postgres -c "alter role cf_n8n_runtime noinherit"
  grep -q 'CF_WRONG_TARGET: cf_n8n_runtime must be LOGIN NOINHERIT' "$WORK/g2.txt" && [ $rc -ne 0 ] && [ "$(fnmd5 "$tag" "$port" g2)" = "$MD5_0001" ]
  check "G2-02-$tag" "0002 refuses when the runtime role has the wrong attributes and leaves the function unchanged" $?

  fresh "$tag" "$port" g3
  q "$tag" "$port" postgres g3 -c "create table public.episode_scripts (id int)"
  apply "$tag" "$port" g3 "$M2" "$WORK/g3.txt"; rc=$?
  grep -q 'CF_WRONG_TARGET: YouTube Kids tables found' "$WORK/g3.txt" && [ $rc -ne 0 ] && [ "$(fnmd5 "$tag" "$port" g3)" = "$MD5_0001" ]
  check "G2-03-$tag" "0002 refuses a database that has the YouTube Kids tables" $?

  apply "$tag" "$port" c3 "$M2" "$WORK/g4.txt"; rc=$?
  grep -q 'CF_ALREADY_APPLIED' "$WORK/g4.txt" && [ $rc -ne 0 ]
  check "G2-04-$tag" "a second apply of 0002 is refused" $?

  fresh "$tag" "$port" g5
  q "$tag" "$port" postgres g5 -At -c "select prosrc from pg_proc where oid = to_regprocedure('cf.guard_status_transition()')" >/dev/null
  q "$tag" "$port" postgres g5 <<'SQL'
CREATE OR REPLACE FUNCTION cf.guard_status_transition() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  RETURN NEW; -- drifted function
END $$;
SQL
  apply "$tag" "$port" g5 "$M2" "$WORK/g5.txt"; rc=$?
  grep -q 'CF_PRECONDITION: cf.guard_status_transition() differs from the approved 0001 version' "$WORK/g5.txt" && [ $rc -ne 0 ]
  check "G2-05-$tag" "0002 refuses to replace a guard function that is not the approved 0001 version" $?

  fresh "$tag" "$port" g6
  q "$tag" "$port" pgtest postgres -c "grant authenticated to cf_n8n_runtime"
  apply "$tag" "$port" g6 "$M2" "$WORK/g6.txt"; rc=$?
  q "$tag" "$port" pgtest postgres -c "revoke authenticated from cf_n8n_runtime"
  grep -q 'CF_WRONG_TARGET: cf_n8n_runtime must not be a member of any role' "$WORK/g6.txt" && [ $rc -ne 0 ]
  check "G2-06-$tag" "0002 refuses when the runtime role belongs to another role" $?

  # --- R: rollback of 0002 ---
  fresh "$tag" "$port" r1
  apply "$tag" "$port" r1 "$R2" "$WORK/r1.txt"; rc=$?
  grep -q 'already the 0001 version' "$WORK/r1.txt" && [ $rc -ne 0 ]
  check "R2-01-$tag" "rollback refuses when 0002 is not applied" $?

  q "$tag" "$port" postgres r1 <<'SQL'
CREATE OR REPLACE FUNCTION cf.guard_status_transition() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  RETURN NEW; -- unknown function
END $$;
SQL
  apply "$tag" "$port" r1 "$R2" "$WORK/r2.txt"; rc=$?
  grep -q 'neither the 0001 nor the 0002 version' "$WORK/r2.txt" && [ $rc -ne 0 ]
  check "R2-02-$tag" "rollback refuses to overwrite an unknown function" $?

  fresh "$tag" "$port" r3
  apply "$tag" "$port" r3 "$M2" "$WORK/r3a.txt"
  q "$tag" "$port" postgres r3 -c "create schema supabase_migrations" -c "create table supabase_migrations.schema_migrations (version text, name text)" \
     -c "insert into supabase_migrations.schema_migrations values ('1','cf_sprint01'),('2','cf_runtime_human_admin_guard')"
  apply "$tag" "$port" r3 "$R2" "$WORK/r3b.txt"; rc=$?
  [ $rc -eq 0 ] && [ "$(fnmd5 "$tag" "$port" r3)" = "$MD5_0001" ] \
    && [ "$(q "$tag" "$port" pgtest r3 -At -c "select string_agg(name, ',') from supabase_migrations.schema_migrations")" = "cf_sprint01" ]
  check "R2-03-$tag" "rollback restores the exact 0001 body (md5 $MD5_0001) and removes only its own history row" $?
  v=$(q "$tag" "$port" pgtest r3 -At -F, -f "$V2" 2>&1 | head -1)
  [ "${v%%,*}" = "f" ]; check "R2-04-$tag" "0002 VERIFY reports guard_function_is_0002_exact=false after the rollback ($v)" $?
  apply "$tag" "$port" r3 "$M2" "$WORK/r3c.txt"; rc=$?
  out=$WORK/T2b_$tag.txt
  q "$tag" "$port" pgtest r3 -At <"$T2" >"$out" 2>&1; rc2=$?
  expected=$(grep -cE "cf_test\.expect_(true|error|denied|ok)\('" "$T2")
  [ $rc -eq 0 ] && [ $rc2 -eq 0 ] && [ "$(count_pass "$out")" -eq "$expected" ] && [ "$(count_fail "$out")" -eq 0 ]
  check "R2-05-$tag" "re-apply after rollback succeeds and all $expected 0002 tests pass again" $?

  fresh "$tag" "$port" r6
  apply "$tag" "$port" r6 "$M2" "$WORK/r6a.txt"
  q "$tag" "$port" postgres r6 -c "create table public.videos (id int)"
  apply "$tag" "$port" r6 "$R2" "$WORK/r6b.txt"; rc=$?
  grep -q 'CF_WRONG_TARGET: YouTube Kids tables found' "$WORK/r6b.txt" && [ $rc -ne 0 ] && [ "$(fnmd5 "$tag" "$port" r6)" = "$MD5_0002" ]
  check "R2-06-$tag" "rollback refuses a database that has the YouTube Kids tables" $?

  # --- R7: rolling back 0002 and then 0001 leaves the database as before 0001 ---
  fresh "$tag" "$port" r7
  apply "$tag" "$port" r7 "$M2" "$WORK/r7a.txt"
  apply "$tag" "$port" r7 "$R2" "$WORK/r7b.txt"
  q "$tag" "$port" postgres r7 --single-transaction -f "$WORK/0001_cf_sprint01.ROLLBACK.sql" >"$WORK/r7c.txt" 2>&1; rc=$?
  [ $rc -eq 0 ] && [ "$(q "$tag" "$port" pgtest r7 -At -c "select count(*) from pg_namespace where nspname='cf'")" = 0 ]
  check "R2-07-$tag" "rolling back 0002 and then 0001 leaves no cf schema" $?

  stop_cluster "$tag" "$bin" "$ld"
}

: >"$OUT"
log "# Engine 2 migration 0002 local test run (throwaway clusters inside the engineering container; never Supabase)"
log "# Run: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
for f in 0001_cf_sprint01.sql 0001_cf_sprint01.TESTS.sql 0001_cf_sprint01.VERIFY.sql 0001_cf_sprint01.ROLLBACK.sql \
         0002_cf_runtime_human_admin_guard.sql 0002_cf_runtime_human_admin_guard.ROLLBACK.sql \
         0002_cf_runtime_human_admin_guard.TESTS.sql 0002_cf_runtime_human_admin_guard.VERIFY.sql; do
  log "# sha256 $(sha256sum "$WORK/$f" | cut -c1-64)  $f"
done

run_version 16 "$PG16BIN" 54339 ""
if [ -n "$PG17BIN" ]; then run_version 17 "$PG17BIN" 54341 "$PG17LIB"; fi

log ""
log "SUMMARY: $PASS harness checks passed, $FAIL failed"
[ "$FAIL" -eq 0 ] && rm -rf "$WORK"
[ "$FAIL" -eq 0 ]
