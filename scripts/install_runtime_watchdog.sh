#!/bin/bash

set -euo pipefail

APP_USER="${APP_USER:-tarun_yadav}"
APP_DIR="${APP_DIR:-/home/${APP_USER}/AstrologyApp}"
UNIT_TEMPLATE="${UNIT_TEMPLATE:-${APP_DIR}/systemd/astroroshni-watchdog.service}"
UNIT_DEST="/etc/systemd/system/astroroshni-watchdog.service"

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
systemctl enable astroroshni-watchdog.service
systemctl restart astroroshni-watchdog.service

echo "✅ Installed and restarted astroroshni-watchdog.service"
