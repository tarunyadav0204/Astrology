#!/bin/bash

# Auto-restart script for Astrology API (started by deploy.sh)
APP_DIR="$(cd "$(dirname "$0")" && pwd)"
PROBE_URL="http://localhost:8001/api/keepalive"
LOG_FILE="$APP_DIR/logs/restart.log"
SNAPSHOT_FILE="$APP_DIR/logs/crash-snapshots.log"
FAILURE_COUNT=0
FAILURE_THRESHOLD=3
PROBE_TIMEOUT=15
CHECK_INTERVAL=30
STARTUP_WAIT=20

mkdir -p "$APP_DIR/logs"

snapshot_before_restart() {
  local stamp
  stamp="$(date -u '+%Y-%m-%d %H:%M:%S UTC')"
  {
    echo ""
    echo "========== Crash snapshot $stamp =========="
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

  fuser -k 8001/tcp 2>/dev/null || true
  pkill -f "python main.py" 2>/dev/null || true
  sleep 3

  cd "$APP_DIR/backend" || exit 1
  # shellcheck source=/dev/null
  source venv/bin/activate
  export PYTHONUNBUFFERED=1
  echo "$(date -u): Starting backend (append to logs/backend.log)" >> "$LOG_FILE"
  nohup python main.py >> "$APP_DIR/logs/backend.log" 2>&1 &
  BACKEND_PID=$!
  echo "$(date -u): Server restarted with PID: $BACKEND_PID" >> "$LOG_FILE"

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
