#!/usr/bin/env bash
# Local-only: migration 0004 tests 1-20 plus the CF-002 workflow SQL flow, on throwaway PostgreSQL clusters that carry
# migrations 0001-0003 exactly as applied live. The restricted login cf_n8n_runtime does every behaviour test. Never touches Supabase.
# Usage: run_cf002_tests.sh <output-file> [pg16-bindir] [pg17-bindir pg17-libdir]
set -uo pipefail
REPO=/home/claude/va-industries-engineering
PKG=$REPO/projects/anime-clip-farming/architecture/data-contracts/migrations
TOOLS=$REPO/projects/anime-clip-farming/evidence/cf-002-tools
WORK=/home/pgtest/work_cf2
OUT=${1:-/tmp/cf002_sql_output.txt}
PG16BIN=${2:-/usr/lib/postgresql/16/bin}
PG17BIN=${3:-}; PG17LIB=${4:-}
rm -rf "$WORK"; mkdir -p "$WORK"
cp "$PKG"/0001_cf_sprint01.sql "$PKG"/0002_cf_runtime_human_admin_guard.sql "$PKG"/0003_cf_freeze_generated_columns_and_search_path.sql "$PKG"/0004_cf002_scene_intelligence*.sql "$WORK"/
cp "$TOOLS"/test/validation_live.sql "$TOOLS"/test/negative_live.sql "$TOOLS"/test/cf_test_helpers.sql "$TOOLS"/test/seed_upstream.sql "$WORK"/
node "$TOOLS/test/gen_sql_tests.js" "$WORK" >"$WORK/gen.txt" || exit 2
chown -R pgtest:pgtest "$WORK"
: >"$OUT"
log() { echo "$*" | tee -a "$OUT"; }
q() { local tag=$1 port=$2 user=$3 db=$4; shift 4
  runuser -u pgtest -- env LD_LIBRARY_PATH="${LDP:-}" "$PSQL" -X -q -h /home/pgtest/skc$tag -p "$port" -U "$user" -d "$db" -v ON_ERROR_STOP=1 "$@"; }
chk() { # name, condition-result ("t"/"f")
  if [ "$2" = "t" ]; then log "PASS $1"; else log "FAIL $1"; fi; }
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
  base() { local db=$1; q $tag $port pgtest postgres -c "CREATE DATABASE $db OWNER postgres"
    for m in 0001_cf_sprint01 0002_cf_runtime_human_admin_guard 0003_cf_freeze_generated_columns_and_search_path; do
      q $tag $port postgres $db --single-transaction -f $WORK/$m.sql >>$WORK/apply_$tag.txt 2>&1 || log "FAIL base migration $m on $db"; done
    q $tag $port pgtest $db -f $WORK/cf_test_helpers.sql; }
  m4() { q $tag $port postgres $1 --single-transaction -f $WORK/0004_cf002_scene_intelligence.sql; }

  # ---- T1 correct path, T3 second-apply guard, VERIFY, T16-18 behaviour ----
  base t1; q $tag $port postgres t1 -f $WORK/seed_upstream.sql || log "FAIL seed"
  local before; before=$(q $tag $port postgres t1 -At -c "select md5(string_agg(md5(prosrc), '' order by proname)) from pg_proc where pronamespace='cf'::regnamespace")
  m4 t1 >$WORK/a1_$tag.txt 2>&1 && log "PASS T1 0004 applies on top of 0001-0003 (single transaction)" || { log "FAIL T1 0004 apply"; head -5 $WORK/a1_$tag.txt | tee -a "$OUT"; }
  q $tag $port postgres t1 -At -f $WORK/0004_cf002_scene_intelligence.VERIFY.sql >$WORK/v1_$tag.txt 2>&1
  # VERIFY as a table: wrap the file's single SELECT as a subquery
  local vq; vq=$(grep -vE '^\s*--' $WORK/0004_cf002_scene_intelligence.VERIFY.sql | sed 's/;\s*$//')
  local nf; nf=$(q $tag $port postgres t1 -At -c "select count(*) filter (where value <> 'true') || '/' || count(*) from jsonb_each_text((select to_jsonb(v) from ($vq) v))")
  [ "${nf%%/*}" = "0" ] && log "PASS T1b VERIFY: all ${nf#*/} columns true" || { log "FAIL T1b VERIFY not all true ($nf)"; q $tag $port postgres t1 -At -c "select key from jsonb_each_text((select to_jsonb(v) from ($vq) v)) where value <> 'true'" | tee -a "$OUT"; }
  local after; after=$(q $tag $port postgres t1 -At -c "select md5(string_agg(md5(prosrc), '' order by proname)) from pg_proc where pronamespace='cf'::regnamespace")
  chk "T16-18 F-2/F-6/F-7: the four cf function bodies are byte-identical after 0004" $([ "$before" = "$after" ] && echo t || echo f)
  m4 t1 >$WORK/a2_$tag.txt 2>&1; grep -q CF_ALREADY_APPLIED $WORK/a2_$tag.txt && log "PASS T3 second apply refused (CF_ALREADY_APPLIED)" || { log "FAIL T3 second apply"; head -3 $WORK/a2_$tag.txt | tee -a "$OUT"; }
  chk "T3b refused second apply changed nothing (25 transitions, 20 triggers)" $(q $tag $port postgres t1 -At -c "select ((select count(*) from cf.allowed_transitions)=25 and (select count(*) from pg_trigger t join pg_class c on c.oid=t.tgrelid where c.relnamespace='cf'::regnamespace and not t.tgisinternal)=20)::text" | cut -c1)
  q $tag $port cf_n8n_runtime t1 -f $WORK/0004_cf002_scene_intelligence.TESTS.sql >$WORK/ot_$tag.txt 2>&1; local rct=$?
  grep -hE 'NOTICE:  (PASS|FAIL)' $WORK/ot_$tag.txt | sed 's/^.*NOTICE:  //' >>"$OUT"
  [ $rct -ne 0 ] && { log "FAIL TESTS.sql exit $rct"; grep -E 'ERROR|psql:' $WORK/ot_$tag.txt | head -5 | tee -a "$OUT"; }
  # postgres-side behaviour on the new tables (freeze F-6, forbid_delete, guard on direct READY insert)
  local pr; pr=$(q $tag $port postgres t1 -At <<'SQL' 2>&1
DO $$ DECLARE st text; m text; r text := '';
BEGIN
  BEGIN UPDATE cf.anime_scene_intelligence SET scene_summary = 'tamper' WHERE status = 'READY'; r := r || 'freeze:no_error;';
  EXCEPTION WHEN OTHERS THEN GET STACKED DIAGNOSTICS st = RETURNED_SQLSTATE, m = MESSAGE_TEXT; r := r || 'freeze:' || st || ':' || left(m, 20) || ';'; END;
  BEGIN DELETE FROM cf.anime_scene_intelligence; r := r || 'delete:no_error;';
  EXCEPTION WHEN OTHERS THEN GET STACKED DIAGNOSTICS st = RETURNED_SQLSTATE, m = MESSAGE_TEXT; r := r || 'delete:' || st || ';'; END;
  BEGIN UPDATE cf.anime_source_episodes SET season_number = 7 WHERE status = 'READY'; r := r || 'epfreeze:no_error;';
  EXCEPTION WHEN OTHERS THEN GET STACKED DIAGNOSTICS st = RETURNED_SQLSTATE, m = MESSAGE_TEXT; r := r || 'epfreeze:' || st || ';'; END;
  BEGIN UPDATE cf.anime_scene_intelligence SET start_ms = 1 WHERE status = 'READY'; r := r || 'start_freeze:no_error;';
  EXCEPTION WHEN OTHERS THEN GET STACKED DIAGNOSTICS st = RETURNED_SQLSTATE, m = MESSAGE_TEXT; r := r || 'start_freeze:' || st || ';'; END;
  RAISE NOTICE 'RESULT %', r;
END $$;
SQL
)
  echo "$pr" | grep -q 'freeze:23514:CF_IMMUTABLE_ROW' && log "PASS T17 F-6 freeze: content of a READY scene is immutable even for postgres (CF_IMMUTABLE_ROW)" || log "FAIL T17 freeze ($pr)"
  echo "$pr" | grep -q 'delete:' && ! echo "$pr" | grep -q 'delete:no_error' && log "PASS T7d forbid_delete trigger blocks DELETE even for postgres" || log "FAIL T7d delete ($pr)"
  echo "$pr" | grep -q 'epfreeze:23514' && echo "$pr" | grep -q 'start_freeze:23514' && log "PASS T17b episode identity columns and scene boundaries are frozen after DRAFT" || log "FAIL T17b ($pr)"

  # ---- workflow SQL flow as the real restricted login ----
  base t2; q $tag $port postgres t2 -f $WORK/seed_upstream.sql; m4 t2 >/dev/null 2>&1
  q $tag $port cf_n8n_runtime t2 -f $WORK/s_flow.sql >$WORK/of_$tag.txt 2>&1; local rcf=$?
  grep -hE 'NOTICE:  (PASS|FAIL)' $WORK/of_$tag.txt | sed 's/^.*NOTICE:  //' >>"$OUT"
  [ $rcf -ne 0 ] && { log "FAIL s_flow exit $rcf"; grep -E 'ERROR|psql:' $WORK/of_$tag.txt | head -6 | tee -a "$OUT"; }

  # ---- live negative block (the exact SQL the TEST workflow runs), here as the real restricted login ----
  base t11; q $tag $port postgres t11 -f $WORK/seed_upstream.sql; m4 t11 >/dev/null 2>&1
  q $tag $port cf_n8n_runtime t11 -f $WORK/negative_live.sql >$WORK/on_$tag.txt 2>&1
  true
  grep -E '^(PASS|FAIL) ' $WORK/on_$tag.txt >>"$OUT"
  q $tag $port cf_n8n_runtime t11 -f $WORK/validation_live.sql >$WORK/ov_$tag.txt 2>&1
  grep -E '^(PASS|FAIL) V' $WORK/ov_$tag.txt | sed 's/^/VALIDATION-LIVE /' >>"$OUT"
  grep -q 'CF002_VAL_REPORT fails=0' $WORK/ov_$tag.txt && log "PASS VAL live validation-mode block: fails=0" || { log "FAIL VAL live validation-mode block"; head -12 $WORK/ov_$tag.txt | tee -a "$OUT"; }
  chk "NEG live block left nothing behind (rolled back)" $(q $tag $port postgres t11 -At -c "select ((select count(*) from cf.anime_source_episodes)=0 and (select count(*) from cf.anime_scene_intelligence)=0)::text" | cut -c1)

  # ---- T2 wrong-project guard ----
  base t3; q $tag $port postgres t3 -c "create table public.videos (id int)"
  m4 t3 >$WORK/a3_$tag.txt 2>&1; grep -q CF_WRONG_TARGET $WORK/a3_$tag.txt && log "PASS T2 wrong-project guard refuses (YouTube Kids table present)" || { log "FAIL T2"; head -3 $WORK/a3_$tag.txt | tee -a "$OUT"; }
  chk "T2b refused apply left no 0004 object" $(q $tag $port postgres t3 -At -c "select (to_regclass('cf.anime_scene_intelligence') is null and to_regtype('cf.research_access_basis') is null)::text" | cut -c1)
  # ---- T4 drift guards ----
  base t4; q $tag $port postgres t4 -c "alter function cf.forbid_delete() reset search_path"
  m4 t4 >$WORK/a4_$tag.txt 2>&1; grep -q CF_DRIFT $WORK/a4_$tag.txt && log "PASS T4a unpinned search_path (F-7 drift) refused" || { log "FAIL T4a"; head -3 $WORK/a4_$tag.txt | tee -a "$OUT"; }
  base t5; q $tag $port postgres t5 -c "create or replace function cf.touch_updated_at() returns trigger language plpgsql set search_path = pg_catalog, cf as \$f\$ begin new.updated_at := now(); return new; end \$f\$"
  m4 t5 >$WORK/a5_$tag.txt 2>&1; grep -q CF_DRIFT $WORK/a5_$tag.txt && log "PASS T4b drifted function body refused (touch_updated_at)" || { log "FAIL T4b"; head -3 $WORK/a5_$tag.txt | tee -a "$OUT"; }
  base t6; q $tag $port postgres t6 -c "create or replace function cf.guard_status_transition() returns trigger language plpgsql set search_path = pg_catalog, cf as \$f\$ begin return new; end \$f\$"
  m4 t6 >$WORK/a6_$tag.txt 2>&1; grep -q CF_DRIFT $WORK/a6_$tag.txt && log "PASS T4c F-2 guard replaced by a permissive body refused" || { log "FAIL T4c"; head -3 $WORK/a6_$tag.txt | tee -a "$OUT"; }
  base t7; q $tag $port postgres t7 -c "alter role cf_n8n_runtime createdb"
  m4 t7 >$WORK/a7_$tag.txt 2>&1; grep -q CF_WRONG_TARGET $WORK/a7_$tag.txt && log "PASS T4d runtime role with CREATEDB refused" || { log "FAIL T4d"; head -3 $WORK/a7_$tag.txt | tee -a "$OUT"; }
  q $tag $port postgres postgres -c "alter role cf_n8n_runtime nocreatedb"
  base t8; q $tag $port postgres t8 -c "update cf.system_flags set enabled = true where flag_key = 'PUBLISH_ENABLED'"
  m4 t8 >$WORK/a8_$tag.txt 2>&1; grep -q 'kill switch' $WORK/a8_$tag.txt && log "PASS T4e apply refused while a kill switch is on" || { log "FAIL T4e"; head -3 $WORK/a8_$tag.txt | tee -a "$OUT"; }
  base t9; m4 t9 >$WORK/a9_$tag.txt 2>&1 || { log "FAIL setup t9 apply"; head -3 $WORK/a9_$tag.txt | tee -a "$OUT"; }
  q $tag $port postgres t9 -f $WORK/seed_upstream.sql >>$WORK/a9_$tag.txt 2>&1
  q $tag $port postgres t9 -c "insert into cf.agent_runs (agent_code, agent_version, idempotency_key, input_ids, input_state_hash, run_state, attempt_count, provider_call_count, paid_call_count, estimated_cost_usd, started_at) values ('CF-002','v0.1',repeat('b',64),'{}',repeat('c',64),'RUNNING',1,0,0,0,now())" >>$WORK/a9_$tag.txt 2>&1
  q $tag $port postgres t9 -c "insert into cf.anime_source_episodes (anime_title_id, season_number, episode_number, status, agent_run_id) select '22222222-2222-4222-8222-222222222222', 1, 1, 'DRAFT', agent_run_id from cf.agent_runs where agent_code='CF-002'" >>$WORK/a9_$tag.txt 2>&1
  q $tag $port postgres t9 --single-transaction -f $WORK/0004_cf002_scene_intelligence.ROLLBACK.sql >$WORK/r0_$tag.txt 2>&1
  grep -qi 'rollback_destroys_data\|rows' $WORK/r0_$tag.txt && log "PASS T19a rollback refused while the tables hold rows" || { log "FAIL T19a"; head -3 $WORK/r0_$tag.txt | tee -a "$OUT"; }
  chk "T19b refused rollback left everything in place" $(q $tag $port postgres t9 -At -c "select (to_regclass('cf.anime_source_episodes') is not null and (select count(*) from cf.anime_source_episodes)=1)::text" | cut -c1)
  base t10; q $tag $port postgres t10 -f $WORK/seed_upstream.sql; m4 t10 >/dev/null 2>&1
  q $tag $port postgres t10 --single-transaction -f $WORK/0004_cf002_scene_intelligence.ROLLBACK.sql >$WORK/r1_$tag.txt 2>&1 && log "PASS T19 rollback of empty 0004 succeeds" || { log "FAIL T19 rollback"; head -5 $WORK/r1_$tag.txt | tee -a "$OUT"; }
  chk "T19c after rollback: 0004 objects gone, 14 transitions, 12 triggers, 4 functions, md5 of original 14 rows unchanged" $(q $tag $port postgres t10 -At -c "select (to_regclass('cf.anime_scene_intelligence') is null and to_regclass('cf.anime_source_episodes') is null and to_regclass('cf.v_scene_publication_status') is null and to_regtype('cf.research_access_basis') is null and (select count(*) from cf.allowed_transitions)=14 and (select count(*) from pg_trigger t join pg_class c on c.oid=t.tgrelid where c.relnamespace='cf'::regnamespace and not t.tgisinternal)=12 and (select count(*) from pg_proc where pronamespace='cf'::regnamespace)=4 and (select md5(string_agg(concat_ws('|', object_type, from_status, to_status, coalesce(required_gate::text,''), coalesce(required_decision::text,''), mode), ';' order by object_type, from_status, to_status)) from cf.allowed_transitions)='6ea6f7a4fafee461dc64345d400b648c' and not exists (select 1 from pg_indexes where indexname='research_candidates_id_title_uq'))::text" | cut -c1)
  chk "T19d CF-001 data untouched by rollback (2 candidates)" $(q $tag $port postgres t10 -At -c "select ((select count(*) from cf.research_candidates)=2)::text" | cut -c1)
  m4 t10 >$WORK/r2_$tag.txt 2>&1 && log "PASS T20 reapply after rollback succeeds" || { log "FAIL T20"; head -5 $WORK/r2_$tag.txt | tee -a "$OUT"; }
  nf=$(q $tag $port postgres t10 -At -c "select count(*) filter (where value <> 'true') || '/' || count(*) from jsonb_each_text((select to_jsonb(v) from ($vq) v))")
  [ "${nf%%/*}" = "0" ] && log "PASS T20b VERIFY all ${nf#*/} true after rollback and reapply" || log "FAIL T20b ($nf)"
  q $tag $port cf_n8n_runtime t10 -c "select 1" >/dev/null 2>&1
  runuser -u pgtest -- env LD_LIBRARY_PATH="$ld" "$bin/pg_ctl" -D "$data" -m fast stop >/dev/null
  runuser -u pgtest -- rm -rf $data $sock; }
run_version 16 "$PG16BIN" 55470 ""
[ -n "$PG17BIN" ] && run_version 17 "$PG17BIN" 55471 "$PG17LIB"
P=$(grep -c "^PASS" "$OUT"); F=$(grep -c "^FAIL" "$OUT")
log "TOTAL pass=$P fail=$F"
[ "$F" -eq 0 ]
