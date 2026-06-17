#!/bin/bash

set -euo pipefail

APP_ROOT="${APP_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
LOG_DIR="${LOG_DIR:-${APP_ROOT}/logs}"
OUTPUT_FILE="${OUTPUT_FILE:-${LOG_DIR}/cpu-snapshots.log}"
BACKEND_LOG_FILE="${BACKEND_LOG_FILE:-${LOG_DIR}/backend.log}"
BACKEND_PORT="${BACKEND_PORT:-8001}"
BACKEND_LOG_TAG="${BACKEND_LOG_TAG:-astroroshni-backend}"
CPU_THRESHOLD_PERCENT="${CPU_THRESHOLD_PERCENT:-120}"
THREAD_LINES="${THREAD_LINES:-25}"
PROCESS_LINES="${PROCESS_LINES:-20}"
SLOW_REQUEST_LINES="${SLOW_REQUEST_LINES:-40}"
ONLY_IF_HIGH="${ONLY_IF_HIGH:-false}"

case "$(printf '%s' "${ONLY_IF_HIGH}" | tr '[:upper:]' '[:lower:]')" in
  true|1|yes) ONLY_IF_HIGH=true ;;
  *) ONLY_IF_HIGH=false ;;
esac

mkdir -p "${LOG_DIR}"

timestamp_utc() {
  date -u '+%Y-%m-%dT%H:%M:%SZ'
}

cpu_total_percent() {
  if [ -r /proc/stat ] && command -v python3 >/dev/null 2>&1; then
    python3 - <<'PY'
import os
import time

def read():
    with open("/proc/stat", "r", encoding="utf-8") as fh:
        parts = fh.readline().split()[1:]
    values = list(map(int, parts[:8]))
    idle = values[3] + values[4]
    total = sum(values)
    return idle, total

i1, t1 = read()
time.sleep(0.25)
i2, t2 = read()
idle = i2 - i1
total = t2 - t1
if total <= 0:
    print("0")
else:
    cpu_count = os.cpu_count() or 1
    busy = max(total - idle, 0)
    print(round((busy / total) * cpu_count * 100, 1))
PY
    return 0
  fi

  if command -v python3 >/dev/null 2>&1; then
    python3 - <<'PY'
try:
    import psutil
except Exception:
    print("0")
else:
    print(round(psutil.cpu_percent(interval=0.25), 1))
PY
  else
    echo "0"
  fi
}

CURRENT_CPU="$(cpu_total_percent)"

if [ "${ONLY_IF_HIGH}" = "true" ]; then
  CURRENT_CPU_INT="${CURRENT_CPU%.*}"
  if [ "${CURRENT_CPU_INT:-0}" -lt "${CPU_THRESHOLD_PERCENT}" ]; then
    echo "Skipping snapshot: cpu ${CURRENT_CPU}% below threshold ${CPU_THRESHOLD_PERCENT}%"
    exit 0
  fi
fi

{
  echo ""
  echo "========== CPU SNAPSHOT $(timestamp_utc) =========="
  echo "cpu_total_percent=${CURRENT_CPU}"
  echo "hostname=$(hostname)"
  echo "uptime=$(uptime)"
  echo "--- local keepalive ---"
  curl -fsS --max-time 5 "http://127.0.0.1:${BACKEND_PORT}/api/keepalive" || true
  echo
  echo "--- local health ---"
  curl -fsS --max-time 10 "http://127.0.0.1:${BACKEND_PORT}/api/health" || true
  echo
  echo "--- local system-status ---"
  curl -fsS --max-time 10 "http://127.0.0.1:${BACKEND_PORT}/api/system-status" || true
  echo
  echo "--- top processes ---"
  ps -eo pid,ppid,cmd,%cpu,%mem --sort=-%cpu | head -n "${PROCESS_LINES}"
  echo "--- top threads ---"
  ps -eLo pid,tid,ppid,pcpu,pmem,comm,args --sort=-pcpu | head -n "${THREAD_LINES}"
  echo "--- socket summary ---"
  ss -s || true
  echo "--- backend listeners ---"
  ss -ltnp | grep ":${BACKEND_PORT}" || true
  echo "--- recent slow_request/chat timing logs ---"
  journalctl -t "${BACKEND_LOG_TAG}" -n 400 --no-pager 2>/dev/null | rg "slow_request|chat_processing_phase|chat_processing_complete|request_exception" | tail -n "${SLOW_REQUEST_LINES}" || true
  echo "========== END CPU SNAPSHOT $(timestamp_utc) =========="
} >> "${OUTPUT_FILE}" 2>&1

echo "Wrote CPU snapshot to ${OUTPUT_FILE}"
