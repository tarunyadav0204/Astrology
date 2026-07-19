#!/bin/bash

set -euo pipefail

# Local watchdog for the API process. This complements, but does not replace,
# the load balancer and MIG health checks.
APP_DIR="${APP_DIR:-$(cd "$(dirname "$0")" && pwd)}"
APP_USER="${APP_USER:-tarun_yadav}"
BACKEND_PORT="${BACKEND_PORT:-8001}"
PROBE_URL="${PROBE_URL:-http://127.0.0.1:${BACKEND_PORT}/api/keepalive}"
HEALTH_URL="${HEALTH_URL:-http://127.0.0.1:${BACKEND_PORT}/api/health}"
BOOTSTRAP_SCRIPT="${BOOTSTRAP_SCRIPT:-$APP_DIR/scripts/bootstrap-runtime.sh}"
WATCHDOG_LOG_TAG="${WATCHDOG_LOG_TAG:-astroroshni-watchdog}"
BACKEND_LOG_TAG="${BACKEND_LOG_TAG:-astroroshni-backend}"
FAILURE_COUNT=0
FAILURE_THRESHOLD="${FAILURE_THRESHOLD:-3}"
PROBE_TIMEOUT="${PROBE_TIMEOUT:-5}"
CHECK_INTERVAL="${CHECK_INTERVAL:-10}"
# Cold start with 2 uvicorn workers + DB schema ensure often exceeds 10s.
STARTUP_WAIT="${STARTUP_WAIT:-120}"
PORT_CLEAR_WAIT_SECONDS="${PORT_CLEAR_WAIT_SECONDS:-10}"

timestamp_utc() {
  date -u '+%Y-%m-%dT%H:%M:%SZ'
}

log_watchdog() {
  local event="$1"
  shift || true
  logger -t "${WATCHDOG_LOG_TAG}" -- "$(timestamp_utc) event=${event} $*"
}

clear_backend_processes() {
  log_watchdog "port_cleanup_begin" "backend_port=${BACKEND_PORT}"

  fuser -k "${BACKEND_PORT}"/tcp 2>/dev/null || true
  pkill -TERM -f "python main.py" 2>/dev/null || true
  pkill -TERM -f "uvicorn.*${BACKEND_PORT}" 2>/dev/null || true
  pkill -TERM -f "uvicorn.*main:app" 2>/dev/null || true

  for _ in $(seq 1 "${PORT_CLEAR_WAIT_SECONDS}"); do
    if ! ss -ltn 2>/dev/null | grep -qE ":${BACKEND_PORT}\\s"; then
      break
    fi
    sleep 1
  done

  if ss -ltn 2>/dev/null | grep -qE ":${BACKEND_PORT}\\s"; then
    log_watchdog "port_cleanup_force_kill" "backend_port=${BACKEND_PORT}"
    fuser -k -9 "${BACKEND_PORT}"/tcp 2>/dev/null || true
    pkill -KILL -f "python main.py" 2>/dev/null || true
    pkill -KILL -f "uvicorn.*${BACKEND_PORT}" 2>/dev/null || true
    pkill -KILL -f "uvicorn.*main:app" 2>/dev/null || true
    sleep 2
  fi

  log_watchdog "port_cleanup_done" "backend_port=${BACKEND_PORT}"
}

emit_snapshot_block() {
  while IFS= read -r line; do
    logger -t "${WATCHDOG_LOG_TAG}" -- "${line}"
  done
}

snapshot_before_restart() {
  local stamp
  stamp="$(date -u '+%Y-%m-%d %H:%M:%S UTC')"
  {
    echo ""
    echo "========== WATCHDOG SNAPSHOT $stamp =========="
    echo "--- uptime ---"
    uptime || true
    echo "--- port ${BACKEND_PORT} ---"
    ss -ltnp 2>/dev/null | grep "${BACKEND_PORT}" || true
    echo "--- top processes ---"
    ps -eo pid,ppid,cmd,%cpu,%mem --sort=-%cpu | head -20 || true
    echo "--- local keepalive ---"
    curl -si --max-time "$PROBE_TIMEOUT" "$PROBE_URL" || true
    echo "--- local health ---"
    curl -si --max-time "$PROBE_TIMEOUT" "$HEALTH_URL" || true
    echo "--- backend journal tail ---"
    journalctl -t "${BACKEND_LOG_TAG}" -n 200 --no-pager 2>/dev/null || true
    echo "--- watchdog journal tail ---"
    journalctl -t "${WATCHDOG_LOG_TAG}" -n 80 --no-pager 2>/dev/null || true
    echo "--- kernel oom / segfault hints ---"
    journalctl -k -n 120 --no-pager 2>/dev/null | rg -i "killed process|out of memory|oom|segfault|memory cgroup" || true
    echo "========== END WATCHDOG SNAPSHOT $stamp =========="
  } | emit_snapshot_block
}

cd "$APP_DIR" || exit 1

while true; do
  if curl -fsS --max-time "$PROBE_TIMEOUT" "$PROBE_URL" > /dev/null 2>&1; then
    if [ "$FAILURE_COUNT" -gt 0 ]; then
      log_watchdog "probe_recovered" "failures=${FAILURE_COUNT} probe_url=${PROBE_URL}"
    fi
    FAILURE_COUNT=0
    sleep "$CHECK_INTERVAL"
    continue
  fi

  FAILURE_COUNT=$((FAILURE_COUNT + 1))
  log_watchdog "probe_failed" "failure_count=${FAILURE_COUNT} threshold=${FAILURE_THRESHOLD} probe_url=${PROBE_URL}"

  if [ "$FAILURE_COUNT" -lt "$FAILURE_THRESHOLD" ]; then
    sleep "$CHECK_INTERVAL"
    continue
  fi

  log_watchdog "restart_begin" "failure_count=${FAILURE_COUNT} probe_url=${PROBE_URL}"
  snapshot_before_restart

  clear_backend_processes

  log_watchdog "bootstrap_runtime_begin" "script=${BOOTSTRAP_SCRIPT}"
  sudo -u "$APP_USER" bash -lc "
    cd '$APP_DIR'
    export APP_ROOT='$APP_DIR'
    export SYNC_GCP_SECRETS='true'
    export INSTALL_GCP_OPS_AGENT='false'
    export SERVE_FRONTEND_LOCALLY='false'
    export SKIP_FRONTEND_RESTART='true'
    '$BOOTSTRAP_SCRIPT'
  " >/dev/null 2>&1 || true

  # Poll until healthy instead of a single check after a blind sleep.
  startup_ok=0
  for _ in $(seq 1 "${STARTUP_WAIT}"); do
    if curl -fsS --max-time "$PROBE_TIMEOUT" "$PROBE_URL" > /dev/null 2>&1; then
      startup_ok=1
      break
    fi
    sleep 1
  done

  if [ "$startup_ok" -eq 1 ]; then
    log_watchdog "restart_success" "failure_count=${FAILURE_COUNT} startup_wait=${STARTUP_WAIT} probe_url=${PROBE_URL}"
    FAILURE_COUNT=0
  else
    log_watchdog "restart_failed" "failure_count=${FAILURE_COUNT} startup_wait=${STARTUP_WAIT} probe_url=${PROBE_URL}"
  fi

  cd "$APP_DIR" || exit 1
  sleep "$CHECK_INTERVAL"
done
