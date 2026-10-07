#!/usr/bin/env bash
# Local-only test harness for Engine 2 migration 0003_cf_freeze_generated_columns_and_search_path (never touches Supabase).
# Same cluster shape as evidence/cf-0002-tools/run_0002_tests.sh: throwaway PostgreSQL clusters run as the unprivileged
# user pgtest on unix sockets only, trust auth, a non-superuser `postgres` with CREATEROLE that applies the migrations,
# anon / authenticated / service_role, and cf_n8n_runtime created with the exact live statement.
# VERIFY files read pg_authid, so locally they run as the superuser pgtest (on Supabase postgres can read it).
# Usage: run_0003_tests.sh <output-file> [pg16-bindir] [pg17-bindir pg17-libdir]
set -uo pipefail

REPO=/home/claude/va-industries-engineering
PKG=projects/anime-clip-farming/architecture/data-contracts/migrations
WORK=/home/pgtest/work3
OUT=${1:-/tmp/0003_output.txt}
PG16BIN=${2:-/usr/lib/postgresql/16/bin}
PG17BIN=${3:-}
PG17LIB=${4:-}

FILES="0001_cf_sprint01.sql 0001_cf_sprint01.TESTS.sql 0001_cf_sprint01.VERIFY.sql 0001_cf_sprint01.ROLLBACK.sql \
0002_cf_runtime_human_admin_guard.sql 0002_cf_runtime_human_admin_guard.ROLLBACK.sql 0002_cf_runtime_human_admin_guard.TESTS.sql 0002_cf_runtime_human_admin_guard.VERIFY.sql \
0003_cf_freeze_generated_columns_and_search_path.sql 0003_cf_freeze_generated_columns_and_search_path.ROLLBACK.sql \
0003_cf_freeze_generated_columns_and_search_path.TESTS.sql 0003_cf_freeze_generated_columns_and_search_path.VERIFY.sql"
rm -rf "$WORK"; mkdir -p "$WORK"
for f in $FILES; do cp "$REPO/$PKG/$f" "$WORK/$f"; done
M1=$WORK/0001_cf_sprint01.sql;  T1=$WORK/0001_cf_sprint01.TESTS.sql;  V1=$WORK/0001_cf_sprint01.VERIFY.sql;  R1=$WORK/0001_cf_sprint01.ROLLBACK.sql
M2=$WORK/0002_cf_runtime_human_admin_guard.sql;  T2=$WORK/0002_cf_runtime_human_admin_guard.TESTS.sql;  V2=$WORK/0002_cf_runtime_human_admin_guard.VERIFY.sql;  R2=$WORK/0002_cf_runtime_human_admin_guard.ROLLBACK.sql
M3=$WORK/0003_cf_freeze_generated_columns_and_search_path.sql;  R3=$WORK/0003_cf_freeze_generated_columns_and_search_path.ROLLBACK.sql
T3=$WORK/0003_cf_freeze_generated_columns_and_search_path.TESTS.sql;  V3=$WORK/0003_cf_freeze_generated_columns_and_search_path.VERIFY.sql
# 0002 tests re-run on the 0003 state: two assertions (H2-51 freeze md5, H2-52 proconfig) describe 0002's state and are
# updated to 0003's intended deltas, nothing else is edited. The 0002 files themselves are untouched.
T2X=$WORK/T2_on_0003.sql
FREEZE0=e4b4d9c63cc9870d5f59ab09e5dfe2c1; FREEZE1=f957a25df6e08a74a21b6a64e5181a47
GUARD=0dac745af135d4772111d92fd2b168c9; GUARD0=eb7450cc84bc9e3d8c4ae4cd7d9187e3
sed -e "s/$FREEZE0/$FREEZE1/" -e "s/AND proowner = 'postgres'::regrole AND proconfig IS NULL/AND proowner = 'postgres'::regrole AND proconfig = ARRAY['search_path=pg_catalog, cf']/" "$T2" >"$T2X"
chown -R pgtest:pgtest "$WORK"

PSQL=$PG16BIN/psql
PASS=0; FAIL=0
log() { echo "$*" | tee -a "$OUT"; }
check() { if [ "$3" -eq 0 ]; then PASS=$((PASS+1)); log "PASS $1 $2"; else FAIL=$((FAIL+1)); log "FAIL $1 $2"; fi; }

start_cluster() { local tag=$1 bin=$2 port=$3 ld=${4:-}
  local data=/home/pgtest/pg3$tag sock=/home/pgtest/sk3$tag
  runuser -u pgtest -- bash -c "rm -rf $data $sock; mkdir -p $sock"
  runuser -u pgtest -- env LD_LIBRARY_PATH="$ld" "$bin/initdb" -D "$data" -U pgtest --auth=trust -E UTF8 --locale=C.UTF-8 >/dev/null
  runuser -u pgtest -- env LD_LIBRARY_PATH="$ld" "$bin/pg_ctl" -D "$data" -l "$data/server.log" -w \
     -o "-k $sock -p $port -c listen_addresses=''" start >/dev/null; }
stop_cluster() { local tag=$1 bin=$2 ld=${3:-}
  runuser -u pgtest -- env LD_LIBRARY_PATH="$ld" "$bin/pg_ctl" -D /home/pgtest/pg3$tag -m fast stop >/dev/null
  runuser -u pgtest -- rm -rf /home/pgtest/pg3$tag /home/pgtest/sk3$tag; }
q() { local tag=$1 port=$2 user=$3 db=$4; shift 4
  runuser -u pgtest -- "$PSQL" -X -q -h /home/pgtest/sk3$tag -p "$port" -U "$user" -d "$db" -v ON_ERROR_STOP=1 "$@"; }
newdb() { q "$1" "$2" pgtest postgres -c "CREATE DATABASE $3 OWNER postgres"; }
apply() { local tag=$1 port=$2 db=$3 file=$4 out=$5
  q "$tag" "$port" postgres "$db" --single-transaction -f "$file" >"$out" 2>&1; }
count_pass() { grep -c '^NOTICE:  PASS' "$1"; }
count_fail() { grep -c 'FAIL' "$1"; }
fnmd5() { q "$1" "$2" pgtest "$3" -At -c "select md5(prosrc) from pg_proc where oid = to_regprocedure('cf.$4()')"; }
pinned() { q "$1" "$2" pgtest "$3" -At -c "select count(*) from pg_proc where pronamespace='cf'::regnamespace and proconfig = array['search_path=pg_catalog, cf']"; }
unpinned() { q "$1" "$2" pgtest "$3" -At -c "select count(*) from pg_proc where pronamespace='cf'::regnamespace and proconfig is null"; }
fresh2() { local tag=$1 port=$2 db=$3; newdb "$tag" "$port" "$db"; apply "$tag" "$port" "$db" "$M1" "$WORK/a1_$db.txt"; apply "$tag" "$port" "$db" "$M2" "$WORK/a2_$db.txt"; }
fresh3() { local tag=$1 port=$2 db=$3; fresh2 "$tag" "$port" "$db"; apply "$tag" "$port" "$db" "$M3" "$WORK/a3_$db.txt"; }
runtests() { # tag port db file expected-regex-of-grep-pattern -> sets RT_PASS RT_EXP RT_FAIL RT_RC, appends output
  local tag=$1 port=$2 db=$3 file=$4 out=$5
  q "$tag" "$port" pgtest "$db" -At <"$file" >"$out" 2>&1; RT_RC=$?
  RT_EXP=$(grep -cE "cf_test\.expect_(true|error|denied|ok)\('" "$file"); RT_PASS=$(count_pass "$out"); RT_FAIL=$(count_fail "$out")
  grep -v '^$' "$out" | sed 's/^/    /' >>"$OUT"; }

EVIL_BASE=$(cat <<'SQL'
CREATE SCHEMA cf_evil;
CREATE FUNCTION cf_evil.now() RETURNS timestamptz LANGUAGE sql AS $$ SELECT '1999-01-01'::timestamptz $$;
CREATE FUNCTION cf_evil.to_jsonb(anyelement) RETURNS jsonb LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'EVIL to_jsonb was resolved'; END $$;
INSERT INTO cf.anime_franchises (franchise_id, normalised_key, display_name) VALUES ('00000000-0000-4000-8000-0000000000e1','ev one','Ev One');
SET search_path = cf_evil, pg_catalog;
DO $$ BEGIN
  BEGIN UPDATE cf.anime_franchises SET status = 'READY' WHERE franchise_id = '00000000-0000-4000-8000-0000000000e1'; RAISE NOTICE 'EVIL_RESULT=ok';
  EXCEPTION WHEN others THEN RAISE NOTICE 'EVIL_RESULT=%', left(SQLERRM, 40); END;
END $$;
RESET search_path;
SELECT 'UPDATED_AT_1999=' || (updated_at < '2000-01-01'::timestamptz) FROM cf.anime_franchises WHERE franchise_id = '00000000-0000-4000-8000-0000000000e1';
SQL
)

# Baseline F-6 / F-7 reproduction on 0001 + 0002 (and the same fixtures after 0003)
F6_SQL=$(cat <<'SQL'
INSERT INTO cf.anime_franchises (franchise_id, normalised_key, display_name) VALUES ('00000000-0000-4000-8000-0000000000e1','k one','K One');
INSERT INTO cf.anime_titles (anime_title_id, franchise_id, normalised_title_key, display_title, start_year) VALUES
  ('00000000-0000-4000-8000-0000000000e2','00000000-0000-4000-8000-0000000000e1','dated ready','Dated Ready',2001),
  ('00000000-0000-4000-8000-0000000000e3','00000000-0000-4000-8000-0000000000e1','dated blocked','Dated Blocked',2002);
UPDATE cf.anime_titles SET status = 'READY'   WHERE anime_title_id = '00000000-0000-4000-8000-0000000000e2';  -- NEW -> DRAFT -> READY
UPDATE cf.anime_titles SET status = 'BLOCKED' WHERE anime_title_id = '00000000-0000-4000-8000-0000000000e3';  -- NEW -> DRAFT -> BLOCKED
DO $$
DECLARE r text;
BEGIN
  SET LOCAL ROLE postgres;
  BEGIN UPDATE cf.anime_titles SET status = 'RETIRED' WHERE anime_title_id = '00000000-0000-4000-8000-0000000000e2'; r := 'succeeded';
  EXCEPTION WHEN others THEN r := left(SQLERRM, 16); END;
  RAISE NOTICE 'ADMIN_READY_TO_RETIRED=%', r;
  BEGIN UPDATE cf.anime_titles SET status = 'READY' WHERE anime_title_id = '00000000-0000-4000-8000-0000000000e3'; r := 'succeeded';
  EXCEPTION WHEN others THEN r := left(SQLERRM, 16); END;
  RAISE NOTICE 'ADMIN_BLOCKED_TO_READY=%', r;
  RESET ROLE;
  SET LOCAL ROLE cf_n8n_runtime;
  BEGIN UPDATE cf.anime_titles SET status = 'RETIRED' WHERE anime_title_id = '00000000-0000-4000-8000-0000000000e2'; r := 'succeeded';
  EXCEPTION WHEN others THEN r := left(SQLERRM, 20); END;
  RAISE NOTICE 'RUNTIME_READY_TO_RETIRED=%', r;
  BEGIN UPDATE cf.anime_titles SET status = 'READY' WHERE anime_title_id = '00000000-0000-4000-8000-0000000000e3'; r := 'succeeded';
  EXCEPTION WHEN others THEN r := left(SQLERRM, 20); END;
  RAISE NOTICE 'RUNTIME_BLOCKED_TO_READY=%', r;
  RESET ROLE;
END $$;
SQL
)
GEN_SQL=$(cat <<'SQL'
CREATE SCHEMA cf_test;
CREATE TABLE cf_test.gen_fixture (gid integer PRIMARY KEY, status cf.lifecycle_status NOT NULL DEFAULT 'READY',
  src_a integer NOT NULL, src_b text NOT NULL, mut text,
  doubled integer GENERATED ALWAYS AS (src_a * 2) STORED, shout text GENERATED ALWAYS AS (upper(src_b)) STORED,
  updated_at timestamptz NOT NULL DEFAULT now());
CREATE TRIGGER gen_freeze BEFORE UPDATE ON cf_test.gen_fixture FOR EACH ROW EXECUTE FUNCTION cf.freeze_after_first_status('mut');
INSERT INTO cf_test.gen_fixture (gid, src_a, src_b, mut) VALUES (1, 5, 'abc', 'm');
DO $$ BEGIN
  BEGIN UPDATE cf_test.gen_fixture SET status = 'BLOCKED' WHERE gid = 1; RAISE NOTICE 'GEN_RESULT=succeeded';
  EXCEPTION WHEN others THEN RAISE NOTICE 'GEN_RESULT=%', left(SQLERRM, 16); END;
END $$;
SQL
)

run_version() { local tag=$1 bin=$2 port=$3 ld=$4 rc v ver out
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

  # --- A: baseline reproduction on 0001 + 0002 (the live state before 0003) ---
  fresh2 "$tag" "$port" base
  [ "$(fnmd5 "$tag" "$port" base guard_status_transition)" = "$GUARD" ] && [ "$(fnmd5 "$tag" "$port" base freeze_after_first_status)" = "$FREEZE0" ] && [ "$(unpinned "$tag" "$port" base)" = 4 ]
  check "A0-$tag" "baseline = live state: guard md5 $GUARD (0002), freeze md5 $FREEZE0 (0001), four functions with no search_path" $?
  q "$tag" "$port" pgtest base -At >"$WORK/f6_base_$tag.txt" 2>&1 <<<"$F6_SQL"
  log "--- F-6 baseline on 0002 ($tag) ---"; sed 's/^/    /' "$WORK/f6_base_$tag.txt" >>"$OUT"
  grep -q 'ADMIN_READY_TO_RETIRED=CF_IMMUTABLE_ROW' "$WORK/f6_base_$tag.txt" && grep -q 'ADMIN_BLOCKED_TO_READY=CF_IMMUTABLE_ROW' "$WORK/f6_base_$tag.txt" \
    && grep -q 'RUNTIME_READY_TO_RETIRED=CF_IMMUTABLE_ROW' "$WORK/f6_base_$tag.txt" && grep -q 'RUNTIME_BLOCKED_TO_READY=CF_IMMUTABLE_ROW' "$WORK/f6_base_$tag.txt"
  check "A1-$tag" "F-6 REPRODUCED on the 0002 baseline: a dated title's post-DRAFT status changes fail with CF_IMMUTABLE_ROW for admin and runtime (not CF_GOVERNANCE_DENIED)" $?
  newdb "$tag" "$port" basegen; apply "$tag" "$port" basegen "$M1" /dev/null; apply "$tag" "$port" basegen "$M2" /dev/null
  q "$tag" "$port" pgtest basegen -At >"$WORK/gen_base_$tag.txt" 2>&1 <<<"$GEN_SQL"
  grep -q 'GEN_RESULT=CF_IMMUTABLE_ROW' "$WORK/gen_base_$tag.txt"
  check "A2-$tag" "the generic fixture (generated columns other than era_decade) is also frozen wrongly on the 0002 baseline, so the fixture test is not vacuous" $?
  newdb "$tag" "$port" baseevil; apply "$tag" "$port" baseevil "$M1" /dev/null; apply "$tag" "$port" baseevil "$M2" /dev/null
  q "$tag" "$port" pgtest baseevil -At >"$WORK/evil_base_$tag.txt" 2>&1 <<<"$EVIL_BASE"
  grep -q 'EVIL_RESULT=EVIL to_jsonb was resolved' "$WORK/evil_base_$tag.txt"
  check "A3-$tag" "F-7 shown on the baseline: with a hostile schema first in the session search_path an unpinned cf function resolves cf_evil.to_jsonb" $?

  # --- B: apply 0003 ---
  fresh2 "$tag" "$port" c1
  apply "$tag" "$port" c1 "$M3" "$WORK/apply3_c1_$tag.txt"; rc=$?
  [ $rc -eq 0 ] && [ "$(fnmd5 "$tag" "$port" c1 freeze_after_first_status)" = "$FREEZE1" ] && [ "$(fnmd5 "$tag" "$port" c1 guard_status_transition)" = "$GUARD" ] && [ "$(pinned "$tag" "$port" c1)" = 4 ]
  check "B1-$tag" "0003 applies as non-superuser postgres in one transaction; freeze md5 $FREEZE1, guard md5 unchanged $GUARD, 4 of 4 functions pinned" $?
  runtests "$tag" "$port" c1 "$T3" "$WORK/T3_$tag.txt"
  log "--- 0003 tests ($tag): exit=$RT_RC pass=$RT_PASS/$RT_EXP fail=$RT_FAIL"
  [ $RT_RC -eq 0 ] && [ "$RT_PASS" -eq "$RT_EXP" ] && [ "$RT_FAIL" -eq 0 ]
  check "B2-$tag" "all $RT_EXP 0003 tests pass (F-6 dated titles, immutability, generic fixtures, F-7 function security, real login, hostile search_path)" $?

  # --- C: regression: the 0002 tests (43) and the 0001 tests (33) on a 0001+0002+0003 database ---
  fresh3 "$tag" "$port" c2
  runtests "$tag" "$port" c2 "$T2X" "$WORK/T2X_$tag.txt"
  log "--- 0002 tests on the 0003 state ($tag): exit=$RT_RC pass=$RT_PASS/$RT_EXP fail=$RT_FAIL"
  [ $RT_RC -eq 0 ] && [ "$RT_PASS" -eq "$RT_EXP" ] && [ "$RT_EXP" -eq 43 ] && [ "$RT_FAIL" -eq 0 ]
  check "C1-$tag" "all 43 0002 tests pass on the 0003 state (F-2 closed, deterministic path, admin path, real login, HUMAN_GATE stand-ins; only H2-51/H2-52 updated to 0003's deltas)" $?
  fresh3 "$tag" "$port" c4
  runtests "$tag" "$port" c4 "$T1" "$WORK/T1_$tag.txt"
  log "--- 0001 tests on the 0003 state ($tag): exit=$RT_RC pass=$RT_PASS/$RT_EXP fail=$RT_FAIL"
  [ $RT_RC -eq 0 ] && [ "$RT_PASS" -eq "$RT_EXP" ] && [ "$RT_EXP" -eq 33 ] && [ "$RT_FAIL" -eq 0 ]
  check "C2-$tag" "all 33 Sprint 1 fail-closed tests pass on the 0003 state (identity, dedupe, no-delete, freeze, paid, publication, privileges, isolation)" $?

  # --- D: the three verification queries on a clean 0001+0002+0003 database ---
  fresh3 "$tag" "$port" c3
  v=$(q "$tag" "$port" pgtest c3 -At -F, -f "$V3" 2>&1)
  [ "$v" = "t,t,t,t,t,t,t,t,t,t,t,t,t,t,t" ]; check "D1-$tag" "0003 VERIFY returns all 15 columns true ($v)" $?
  v=$(q "$tag" "$port" postgres c3 -At -F, -f "$V1" 2>&1)
  [ "$v" = "t,t,t,t,t,t,t,t,t,t,t" ]; check "D2-$tag" "0001 VERIFY re-run returns all true after 0003 ($v)" $?
  v=$(q "$tag" "$port" pgtest c3 -At -F, -f "$V2" 2>&1)
  log "    0002 VERIFY on the 0003 state: $v"
  [ "$v" = "t,f,t,t,t,t,t,t,t,t,t" ]; check "D3-$tag" "0002 VERIFY on 0003: only column 2 (guard function proconfig IS NULL) differs, intentionally; guard md5 and HUMAN_ADMIN block still exact" $?
  q "$tag" "$port" postgres c3 -c "alter function cf.touch_updated_at() reset search_path"
  v=$(q "$tag" "$port" pgtest c3 -At -F, -f "$V3" 2>&1)
  [ "$(echo "$v" | cut -d, -f4)" = f ]; check "D4-$tag" "0003 VERIFY catches an unpinned search_path ($v)" $?
  q "$tag" "$port" postgres c3 -c "alter function cf.touch_updated_at() set search_path = pg_catalog, cf"
  q "$tag" "$port" postgres c3 -c "grant execute on function cf.forbid_delete() to cf_n8n_runtime"
  v=$(q "$tag" "$port" pgtest c3 -At -F, -f "$V3" 2>&1); [ "$(echo "$v" | cut -d, -f5)" = f ] && [ "$(echo "$v" | cut -d, -f12)" = f ]; check "D5-$tag" "0003 VERIFY catches an EXECUTE grant to the runtime role ($v)" $?
  q "$tag" "$port" postgres c3 -c "revoke execute on function cf.forbid_delete() from cf_n8n_runtime"
  q "$tag" "$port" postgres c3 -c "alter role cf_n8n_runtime password '$(head -c 12 /dev/urandom | od -An -tx1 | tr -d ' \n')'" >/dev/null 2>&1
  v=$(q "$tag" "$port" pgtest c3 -At -F, -f "$V3" 2>&1); [ "$(echo "$v" | cut -d, -f11)" = f ]; check "D6-$tag" "0003 VERIFY shows runtime_role_passwordless=false once a password exists" $?
  q "$tag" "$port" postgres c3 -c "alter role cf_n8n_runtime password null" >/dev/null 2>&1

  # --- E: 0003 guard branches ---
  newdb "$tag" "$port" g1; apply "$tag" "$port" g1 "$M3" "$WORK/g1.txt"; rc=$?
  grep -q 'CF_PRECONDITION: migration 0001_cf_sprint01 is not applied' "$WORK/g1.txt" && [ $rc -ne 0 ]
  check "G3-01-$tag" "0003 refuses a database where 0001 is not applied" $?
  fresh2 "$tag" "$port" g2; q "$tag" "$port" postgres postgres -c "alter role cf_n8n_runtime inherit"
  apply "$tag" "$port" g2 "$M3" "$WORK/g2.txt"; rc=$?; q "$tag" "$port" postgres postgres -c "alter role cf_n8n_runtime noinherit"
  grep -q 'CF_WRONG_TARGET: cf_n8n_runtime must be LOGIN NOINHERIT' "$WORK/g2.txt" && [ $rc -ne 0 ] && [ "$(pinned "$tag" "$port" g2)" = 0 ]
  check "G3-02-$tag" "0003 refuses when the runtime role has the wrong attributes and changes nothing" $?
  fresh2 "$tag" "$port" g3; q "$tag" "$port" postgres g3 -c "create table public.videos (id int)"
  apply "$tag" "$port" g3 "$M3" "$WORK/g3.txt"; rc=$?
  grep -q 'CF_WRONG_TARGET: YouTube Kids tables found' "$WORK/g3.txt" && [ $rc -ne 0 ] && [ "$(pinned "$tag" "$port" g3)" = 0 ]
  check "G3-03-$tag" "0003 refuses a database that has the YouTube Kids tables" $?
  apply "$tag" "$port" c3 "$M3" "$WORK/g4.txt"; rc=$?
  grep -q 'CF_ALREADY_APPLIED' "$WORK/g4.txt" && [ $rc -ne 0 ]
  check "G3-04-$tag" "a second apply of 0003 is refused" $?
  fresh2 "$tag" "$port" g5
  q "$tag" "$port" postgres g5 <<'SQL'
CREATE OR REPLACE FUNCTION cf.freeze_after_first_status() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RETURN NEW; END $$;
SQL
  apply "$tag" "$port" g5 "$M3" "$WORK/g5.txt"; rc=$?
  grep -q 'CF_PRECONDITION: cf.freeze_after_first_status() differs' "$WORK/g5.txt" && [ $rc -ne 0 ] && [ "$(pinned "$tag" "$port" g5)" = 0 ]
  check "G3-05-$tag" "0003 refuses to replace a drifted freeze function" $?
  q "$tag" "$port" postgres g5 -c "alter function cf.freeze_after_first_status() reset search_path" >/dev/null 2>&1
  fresh "$tag" "$port" g6 2>/dev/null || { newdb "$tag" "$port" g6; apply "$tag" "$port" g6 "$M1" /dev/null; }
  apply "$tag" "$port" g6 "$M3" "$WORK/g6.txt"; rc=$?   # 0001 only: guard body is the 0001 body, not 0002
  grep -q 'CF_PRECONDITION: cf.guard_status_transition() differs' "$WORK/g6.txt" && [ $rc -ne 0 ]
  check "G3-06-$tag" "0003 refuses a database that is on 0001 only (guard function is not the 0002 version, so the HUMAN_ADMIN block would be lost)" $?
  fresh2 "$tag" "$port" g7; q "$tag" "$port" postgres g7 -c "alter function cf.forbid_delete() set search_path = public"
  apply "$tag" "$port" g7 "$M3" "$WORK/g7.txt"; rc=$?
  grep -q 'CF_ALREADY_APPLIED: cf.forbid_delete() already' "$WORK/g7.txt" && [ $rc -ne 0 ]
  check "G3-07-$tag" "0003 refuses when a function already carries a search_path setting" $?
  fresh2 "$tag" "$port" g8; q "$tag" "$port" pgtest postgres -c "grant authenticated to cf_n8n_runtime"
  apply "$tag" "$port" g8 "$M3" "$WORK/g8.txt"; rc=$?; q "$tag" "$port" pgtest postgres -c "revoke authenticated from cf_n8n_runtime"
  grep -q 'CF_WRONG_TARGET: cf_n8n_runtime must not be a member of any role' "$WORK/g8.txt" && [ $rc -ne 0 ]
  check "G3-08-$tag" "0003 refuses when the runtime role belongs to another role" $?

  # --- F: rollback of 0003 ---
  fresh2 "$tag" "$port" r1; apply "$tag" "$port" r1 "$R3" "$WORK/r1.txt"; rc=$?
  grep -q 'is not the 0003 version' "$WORK/r1.txt" && [ $rc -ne 0 ]
  check "R3-01-$tag" "rollback refuses when 0003 is not applied" $?
  fresh3 "$tag" "$port" r2
  q "$tag" "$port" postgres r2 -c "create or replace function cf.forbid_delete() returns trigger language plpgsql set search_path = pg_catalog, cf as \$\$ begin return old; end \$\$"
  apply "$tag" "$port" r2 "$R3" "$WORK/r2.txt"; rc=$?
  grep -q 'cf.forbid_delete() or cf.touch_updated_at() is not the approved version' "$WORK/r2.txt" && [ $rc -ne 0 ] && [ "$(fnmd5 "$tag" "$port" r2 freeze_after_first_status)" = "$FREEZE1" ]
  check "R3-02-$tag" "rollback refuses to touch anything when another function is not the approved body" $?
  fresh3 "$tag" "$port" r3
  q "$tag" "$port" postgres r3 -c "create schema supabase_migrations" -c "create table supabase_migrations.schema_migrations (version text, name text)" \
     -c "insert into supabase_migrations.schema_migrations values ('1','cf_sprint01'),('2','cf_runtime_human_admin_guard'),('3','cf_freeze_generated_columns_and_search_path')"
  apply "$tag" "$port" r3 "$R3" "$WORK/r3.txt"; rc=$?
  [ $rc -eq 0 ] && [ "$(fnmd5 "$tag" "$port" r3 freeze_after_first_status)" = "$FREEZE0" ] && [ "$(fnmd5 "$tag" "$port" r3 guard_status_transition)" = "$GUARD" ] && [ "$(unpinned "$tag" "$port" r3)" = 4 ]
  check "R3-03-$tag" "rollback restores the 0001 freeze body ($FREEZE0), keeps the 0002 guard ($GUARD) and clears all four proconfig settings" $?
  v=$(q "$tag" "$port" pgtest r3 -At -F, -f "$V2" 2>&1)
  [ "$v" = "t,t,t,t,t,t,t,t,t,t,t" ]; check "R3-04-$tag" "after the rollback the 0002 VERIFY is all true again, i.e. exactly the pre-0003 state ($v)" $?
  v=$(q "$tag" "$port" pgtest r3 -At -F, -f "$V3" 2>&1); [ "$(echo "$v" | cut -d, -f1)" = f ] && [ "$(echo "$v" | cut -d, -f4)" = f ]
  check "R3-05-$tag" "0003 VERIFY reports the freeze function and pinned search_paths as false after the rollback ($v)" $?
  q "$tag" "$port" pgtest r3 -At >"$WORK/f6_after_rb_$tag.txt" 2>&1 <<<"$F6_SQL"
  grep -q 'ADMIN_READY_TO_RETIRED=CF_IMMUTABLE_ROW' "$WORK/f6_after_rb_$tag.txt"
  check "R3-06-$tag" "after the rollback F-6 is back (dated READY -> RETIRED fails again): the rollback really restores the old behaviour" $?
  # the rollback leaves history rows alone (documented); remove 0003's row, then re-apply and re-test
  q "$tag" "$port" postgres r3 -c "delete from supabase_migrations.schema_migrations where name = 'cf_freeze_generated_columns_and_search_path'"
  newdb "$tag" "$port" r4; apply "$tag" "$port" r4 "$M1" /dev/null; apply "$tag" "$port" r4 "$M2" /dev/null; apply "$tag" "$port" r4 "$M3" /dev/null
  apply "$tag" "$port" r4 "$R3" "$WORK/r4a.txt"; apply "$tag" "$port" r4 "$M3" "$WORK/r4b.txt"; rc=$?
  runtests "$tag" "$port" r4 "$T3" "$WORK/T3b_$tag.txt"
  [ $rc -eq 0 ] && [ $RT_RC -eq 0 ] && [ "$RT_PASS" -eq "$RT_EXP" ] && [ "$RT_FAIL" -eq 0 ] && [ "$(fnmd5 "$tag" "$port" r4 freeze_after_first_status)" = "$FREEZE1" ]
  check "R3-07-$tag" "apply, rollback, re-apply works and all $RT_EXP 0003 tests pass again" $?
  fresh3 "$tag" "$port" r5; apply "$tag" "$port" r5 "$R3" "$WORK/r5a.txt"
  apply "$tag" "$port" r5 "$R2" "$WORK/r5b.txt"; apply "$tag" "$port" r5 "$R1" "$WORK/r5c.txt"; rc=$?
  [ $rc -eq 0 ] && [ "$(q "$tag" "$port" pgtest r5 -At -c "select count(*) from pg_namespace where nspname='cf'")" = 0 ]
  check "R3-08-$tag" "rolling back 0003, then 0002, then 0001 leaves no cf schema" $?
  fresh3 "$tag" "$port" r6; q "$tag" "$port" postgres r6 -c "create table public.videos (id int)"
  apply "$tag" "$port" r6 "$R3" "$WORK/r6.txt"; rc=$?
  grep -q 'CF_WRONG_TARGET: YouTube Kids tables found' "$WORK/r6.txt" && [ $rc -ne 0 ] && [ "$(pinned "$tag" "$port" r6)" = 4 ]
  check "R3-09-$tag" "rollback refuses a database that has the YouTube Kids tables" $?

  stop_cluster "$tag" "$bin" "$ld"
}

: >"$OUT"
log "# Engine 2 migration 0003 local test run (throwaway clusters inside the engineering container; never Supabase)"
log "# Run: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
for f in $FILES; do log "# sha256 $(sha256sum "$WORK/$f" | cut -c1-64)  $f"; done
run_version 16 "$PG16BIN" 54349 ""
if [ -n "$PG17BIN" ]; then run_version 17 "$PG17BIN" 54351 "$PG17LIB"; fi
log ""
log "SUMMARY: $PASS harness checks passed, $FAIL failed"
[ "$FAIL" -eq 0 ] && rm -rf "$WORK"
[ "$FAIL" -eq 0 ]
