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
LOG_FILE="${LOG_FILE:-$APP_DIR/logs/restart.log}"
SNAPSHOT_FILE="${SNAPSHOT_FILE:-$APP_DIR/logs/crash-snapshots.log}"
FAILURE_COUNT=0
FAILURE_THRESHOLD="${FAILURE_THRESHOLD:-3}"
PROBE_TIMEOUT="${PROBE_TIMEOUT:-5}"
CHECK_INTERVAL="${CHECK_INTERVAL:-10}"
STARTUP_WAIT="${STARTUP_WAIT:-10}"

mkdir -p "$APP_DIR/logs"

snapshot_before_restart() {
  local stamp
  stamp="$(date -u '+%Y-%m-%d %H:%M:%S UTC')"
  {
    echo ""
    echo "========== Crash snapshot $stamp =========="
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
    if [ -f "$APP_DIR/logs/backend.log" ]; then
      echo "--- backend.log (last 500 lines) ---"
      tail -500 "$APP_DIR/logs/backend.log"
    else
      echo "(no logs/backend.log)"
    fi
  } >> "$SNAPSHOT_FILE"
}

cd "$APP_DIR" || exit 1

while true; do
  if curl -fsS --max-time "$PROBE_TIMEOUT" "$PROBE_URL" > /dev/null 2>&1; then
    if [ "$FAILURE_COUNT" -gt 0 ]; then
      echo "$(date -u): Probe recovered after $FAILURE_COUNT failure(s)" >> "$LOG_FILE"
    fi
    FAILURE_COUNT=0
    sleep "$CHECK_INTERVAL"
    continue
  fi

  FAILURE_COUNT=$((FAILURE_COUNT + 1))
  echo "$(date -u): Probe failed ($FAILURE_COUNT/$FAILURE_THRESHOLD) for $PROBE_URL" >> "$LOG_FILE"

  if [ "$FAILURE_COUNT" -lt "$FAILURE_THRESHOLD" ]; then
    sleep "$CHECK_INTERVAL"
    continue
  fi

  echo "$(date -u): Server down after $FAILURE_COUNT consecutive failures, restarting..." >> "$LOG_FILE"
  snapshot_before_restart

  fuser -k "${BACKEND_PORT}"/tcp 2>/dev/null || true
  pkill -f "python main.py" 2>/dev/null || true
  sleep 3

  echo "$(date -u): Running bootstrap runtime script" >> "$LOG_FILE"
  sudo -u "$APP_USER" bash -lc "
    cd '$APP_DIR'
    export APP_ROOT='$APP_DIR'
    export SYNC_GCP_SECRETS='true'
    export INSTALL_GCP_OPS_AGENT='false'
    export SERVE_FRONTEND_LOCALLY='false'
    export SKIP_FRONTEND_RESTART='true'
    '$BOOTSTRAP_SCRIPT'
  " >> "$LOG_FILE" 2>&1 || true

  sleep "$STARTUP_WAIT"

  if curl -fsS --max-time "$PROBE_TIMEOUT" "$PROBE_URL" > /dev/null 2>&1; then
    echo "$(date -u): Server restart successful" >> "$LOG_FILE"
    FAILURE_COUNT=0
  else
    echo "$(date -u): Server restart failed (probe still failing)" >> "$LOG_FILE"
  fi

  cd "$APP_DIR" || exit 1
  sleep "$CHECK_INTERVAL"
done
