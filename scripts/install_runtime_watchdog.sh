#!/bin/bash

set -euo pipefail

APP_USER="${APP_USER:-tarun_yadav}"
APP_DIR="${APP_DIR:-/home/${APP_USER}/AstrologyApp}"
UNIT_TEMPLATE="${UNIT_TEMPLATE:-${APP_DIR}/systemd/astroroshni-watchdog.service}"
UNIT_DEST="/etc/systemd/system/astroroshni-watchdog.service"
START_RUNTIME_WATCHDOG="${START_RUNTIME_WATCHDOG:-true}"

if [ "$(id -u)" -ne 0 ]; then
  echo "❌ install_runtime_watchdog.sh must run as root"
  exit 1
fi

if [ ! -f "${UNIT_TEMPLATE}" ]; then
  echo "❌ Watchdog unit template missing: ${UNIT_TEMPLATE}"
  exit 1
fi

tmp_unit="$(mktemp)"
trap 'rm -f "${tmp_unit}"' EXIT

sed \
  -e "s|__APP_USER__|${APP_USER}|g" \
  -e "s|__APP_DIR__|${APP_DIR}|g" \
  "${UNIT_TEMPLATE}" > "${tmp_unit}"

install -m 644 "${tmp_unit}" "${UNIT_DEST}"
systemctl daemon-reload
if [ "${START_RUNTIME_WATCHDOG}" = "true" ]; then
  systemctl enable astroroshni-watchdog.service
  systemctl restart astroroshni-watchdog.service
  echo "✅ Installed and restarted astroroshni-watchdog.service"
else
  # App deploys manage the backend directly and rely on MIG autohealing after
  # completion. Leaving this Restart=always unit active creates a race: killing
  # restart_server.sh makes systemd respawn it while deploy-release.sh is
  # starting its own backend monitor, and the watchdog then kills that backend.
  systemctl disable --now astroroshni-watchdog.service 2>/dev/null || true
  echo "✅ Installed astroroshni-watchdog.service (left disabled for MIG autohealing)"
fi
