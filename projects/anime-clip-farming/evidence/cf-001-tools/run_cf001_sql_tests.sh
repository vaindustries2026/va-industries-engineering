#!/usr/bin/env bash
# Local-only: replays the CF-001 SQL (sql/*.sql) as the real cf_n8n_runtime login on throwaway PostgreSQL clusters
# that carry migrations 0001-0003 exactly as applied live. Never touches Supabase.
# Usage: run_cf001_sql_tests.sh <output-file> [pg16-bindir] [pg17-bindir pg17-libdir]
set -uo pipefail
REPO=/home/claude/va-industries-engineering
PKG=$REPO/projects/anime-clip-farming/architecture/data-contracts/migrations
TOOLS=$REPO/projects/anime-clip-farming/evidence/cf-001-tools
WORK=/home/pgtest/work_cf1
OUT=${1:-/tmp/cf001_sql_output.txt}
PG16BIN=${2:-/usr/lib/postgresql/16/bin}
PG17BIN=${3:-}; PG17LIB=${4:-}
rm -rf "$WORK"; mkdir -p "$WORK"
cp "$PKG"/0001_cf_sprint01.sql "$PKG"/0002_cf_runtime_human_admin_guard.sql "$PKG"/0003_cf_freeze_generated_columns_and_search_path.sql "$WORK"/
node "$TOOLS/test/gen_sql_tests.js" "$WORK" >"$WORK/gen.txt" || exit 2
cp "$TOOLS"/test/negative_phase_b.sql "$WORK"/ 2>/dev/null
chown -R pgtest:pgtest "$WORK"
: >"$OUT"
PASS=0; FAIL=0
log() { echo "$*" | tee -a "$OUT"; }
q() { local tag=$1 port=$2 user=$3 db=$4; shift 4
  runuser -u pgtest -- env LD_LIBRARY_PATH="${LDP:-}" "$PSQL" -X -q -h /home/pgtest/skc$tag -p "$port" -U "$user" -d "$db" -v ON_ERROR_STOP=1 "$@"; }
run_version() { local tag=$1 bin=$2 port=$3 ld=$4
  export LDP=""; PSQL=$PG16BIN/psql
  local data=/home/pgtest/pgc$tag sock=/home/pgtest/skc$tag
  runuser -u pgtest -- bash -c "rm -rf $data $sock; mkdir -p $sock"
  runuser -u pgtest -- env LD_LIBRARY_PATH="$ld" "$bin/initdb" -D "$data" -U pgtest --auth=trust -E UTF8 --locale=C.UTF-8 >/dev/null
  runuser -u pgtest -- env LD_LIBRARY_PATH="$ld" "$bin/pg_ctl" -D "$data" -l "$data/server.log" -w -o "-k $sock -p $port -c listen_addresses=''" start >/dev/null
  log "=== Cluster $tag: $(q $tag $port pgtest postgres -At -c 'select version()') ==="
  q $tag $port pgtest postgres <<'SQL'
CREATE ROLE postgres LOGIN NOSUPERUSER INHERIT CREATEROLE CREATEDB REPLICATION BYPASSRLS;
CREATE ROLE anon NOLOGIN NOINHERIT; CREATE ROLE authenticated NOLOGIN NOINHERIT; CREATE ROLE service_role NOLOGIN NOINHERIT BYPASSRLS;
SQL
  q $tag $port postgres postgres -c "create role cf_n8n_runtime with login noinherit nobypassrls nosuperuser nocreatedb nocreaterole noreplication password null;"
  fresh() { local db=$1; q $tag $port pgtest postgres -c "CREATE DATABASE $db OWNER postgres"
    for m in 0001_cf_sprint01 0002_cf_runtime_human_admin_guard 0003_cf_freeze_generated_columns_and_search_path; do
      q $tag $port postgres $db --single-transaction -f $WORK/$m.sql >>$WORK/apply_$tag.txt 2>&1 || { log "FAIL migration $m on $db"; FAIL=$((FAIL+1)); }; done
    q $tag $port pgtest $db <<'SQL'
CREATE SCHEMA cf_test; GRANT USAGE ON SCHEMA cf_test TO PUBLIC;
CREATE FUNCTION cf_test.expect_true(p_name text, p_cond boolean) RETURNS void LANGUAGE plpgsql AS $$ BEGIN
  IF p_cond IS TRUE THEN RAISE NOTICE 'PASS %', p_name; ELSE RAISE NOTICE 'FAIL %', p_name; END IF; END $$;
GRANT EXECUTE ON FUNCTION cf_test.expect_true(text, boolean) TO PUBLIC;
SQL
  }
  fresh t1
  q $tag $port cf_n8n_runtime t1 -f $WORK/s1_flow.sql >$WORK/o1_$tag.txt 2>&1; local rc1=$?
  q $tag $port cf_n8n_runtime t1 -f $WORK/s6_more.sql >$WORK/o6_$tag.txt 2>&1; local rc6=$?
  grep -hE 'NOTICE:  (PASS|FAIL)|ERROR' $WORK/o1_$tag.txt $WORK/o6_$tag.txt | sed 's/^.*NOTICE:  //' >>"$OUT"
  [ $rc1 -ne 0 ] && { log "FAIL s1_flow exit $rc1"; head -20 $WORK/o1_$tag.txt | tee -a "$OUT"; FAIL=$((FAIL+1)); }
  [ $rc6 -ne 0 ] && { log "FAIL s6_more exit $rc6"; head -20 $WORK/o6_$tag.txt | tee -a "$OUT"; FAIL=$((FAIL+1)); }
  if [ -f "$WORK/negative_phase_b.sql" ]; then
    q $tag $port cf_n8n_runtime t1 -At -f $WORK/negative_phase_b.sql >$WORK/ob_$tag.txt 2>&1
    grep -hE '^(PASS|FAIL)|CF001_NEG_REPORT' $WORK/ob_$tag.txt >>"$OUT"
  fi
  runuser -u pgtest -- env LD_LIBRARY_PATH="$ld" "$bin/pg_ctl" -D "$data" -m fast stop >/dev/null
  runuser -u pgtest -- rm -rf $data $sock; }
run_version 16 "$PG16BIN" 55460 ""
[ -n "$PG17BIN" ] && run_version 17 "$PG17BIN" 55461 "$PG17LIB"
P=$(grep -c '^PASS' "$OUT"); F=$(grep -c '^FAIL' "$OUT")
log "TOTAL pass=$P fail=$F"
[ "$F" -eq 0 ]
