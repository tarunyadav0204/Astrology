#!/bin/bash

set -euo pipefail

APP_ROOT="${APP_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
BACKEND_DIR="${BACKEND_DIR:-${APP_ROOT}/backend}"
BACKEND_PORT="${BACKEND_PORT:-8001}"
CPU_SNAPSHOT_SCRIPT="${CPU_SNAPSHOT_SCRIPT:-${APP_ROOT}/scripts/capture_cpu_snapshot.sh}"
BACKEND_LOG_TAG="${BACKEND_LOG_TAG:-astroroshni-backend}"
MONITOR_LOG_TAG="${MONITOR_LOG_TAG:-astroroshni-backend-monitor}"
EXIT_SNAPSHOT_TAIL_LINES="${EXIT_SNAPSHOT_TAIL_LINES:-120}"

timestamp_utc() {
  date -u '+%Y-%m-%dT%H:%M:%SZ'
}

log_monitor() {
  local message="$1"
  logger -t "${MONITOR_LOG_TAG}" -- "$(timestamp_utc) ${message}"
}

emit_block_to_logger() {
  local tag="$1"
  while IFS= read -r line; do
    logger -t "${tag}" -- "${line}"
  done
}

capture_exit_snapshot() {
  local exit_code="$1"
  local signal_name="$2"

  {
    echo ""
    echo "========== BACKEND EXIT SNAPSHOT $(timestamp_utc) =========="
    echo "exit_code=${exit_code}"
    echo "signal=${signal_name}"
    echo "hostname=$(hostname)"
    echo "uptime=$(uptime)"
    echo "--- process tree ---"
    ps -eo pid,ppid,cmd,%cpu,%mem --sort=-%cpu | head -n 25
    echo "--- backend listeners ---"
    ss -ltnp | grep ":${BACKEND_PORT}" || true
    echo "--- backend journal tail ---"
    journalctl -t "${BACKEND_LOG_TAG}" -n "${EXIT_SNAPSHOT_TAIL_LINES}" --no-pager 2>/dev/null || true
    echo "--- systemd oom / kill hints ---"
    journalctl -k -n 120 --no-pager 2>/dev/null | rg -i "killed process|out of memory|oom|segfault|memory cgroup" || true
    echo "--- service log tail ---"
    journalctl -u google-startup-scripts.service -n 80 --no-pager 2>/dev/null || true
    echo "========== END BACKEND EXIT SNAPSHOT $(timestamp_utc) =========="
  } | emit_block_to_logger "${MONITOR_LOG_TAG}"

  if [ -f "${CPU_SNAPSHOT_SCRIPT}" ]; then
    APP_ROOT="${APP_ROOT}" BACKEND_PORT="${BACKEND_PORT}" ONLY_IF_HIGH="false" OUTPUT_FILE="/dev/stdout" \
      bash "${CPU_SNAPSHOT_SCRIPT}" 2>&1 | emit_block_to_logger "${MONITOR_LOG_TAG}" || true
  fi
}

cd "${BACKEND_DIR}"

log_monitor "backend_monitor_start cwd=${BACKEND_DIR}"
set +e
set -o pipefail
python main.py 2>&1 | emit_block_to_logger "${BACKEND_LOG_TAG}"
EXIT_CODE=${PIPESTATUS[0]}
set +o pipefail
set -e

SIGNAL_NAME=""
if [ "${EXIT_CODE}" -ge 128 ] && [ "${EXIT_CODE}" -le 192 ]; then
  SIGNAL_NUM=$((EXIT_CODE - 128))
  SIGNAL_NAME="$(kill -l "${SIGNAL_NUM}" 2>/dev/null || echo "SIG${SIGNAL_NUM}")"
fi

log_monitor "backend_child_exit exit_code=${EXIT_CODE} signal=${SIGNAL_NAME:-none}"
capture_exit_snapshot "${EXIT_CODE}" "${SIGNAL_NAME:-none}"

exit "${EXIT_CODE}"
