#!/bin/bash
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive

APP_USER="${APP_USER:-tarun_yadav}"
APP_DIR="${APP_DIR:-/home/${APP_USER}/AstrologyApp}"
LOG_FILE="${LOG_FILE:-/var/log/astroroshni-startup.log}"
BOOTSTRAP_SCRIPT="${BOOTSTRAP_SCRIPT:-${APP_DIR}/scripts/bootstrap-runtime.sh}"
WATCHDOG_INSTALLER="${WATCHDOG_INSTALLER:-${APP_DIR}/scripts/install_runtime_watchdog.sh}"

exec > >(tee -a "${LOG_FILE}") 2>&1

echo "========== AstroRoshni startup $(date -u) =========="

exec 9>/var/lock/astroroshni-startup.lock
flock -n 9 || exit 0

id "${APP_USER}" >/dev/null 2>&1 || useradd -m -s /bin/bash "${APP_USER}"

if [ ! -d "${APP_DIR}" ]; then
  echo "❌ App directory missing: ${APP_DIR}"
  exit 1
fi

if [ ! -x "${BOOTSTRAP_SCRIPT}" ]; then
  echo "❌ Bootstrap script missing or not executable: ${BOOTSTRAP_SCRIPT}"
  exit 1
fi

if [ -f "${WATCHDOG_INSTALLER}" ]; then
  APP_USER="${APP_USER}" APP_DIR="${APP_DIR}" bash "${WATCHDOG_INSTALLER}"
else
  echo "⚠️ Watchdog installer missing: ${WATCHDOG_INSTALLER}"
fi

PROJECT_ID="$(curl -fsH 'Metadata-Flavor: Google' http://metadata.google.internal/computeMetadata/v1/project/project-id)"
gcloud config set project "${PROJECT_ID}"

sudo -u "${APP_USER}" bash -lc "
  cd '${APP_DIR}'
  export APP_ROOT='${APP_DIR}'
  export SYNC_GCP_SECRETS='true'
  export INSTALL_GCP_OPS_AGENT='false'
  export SERVE_FRONTEND_LOCALLY='false'
  '${BOOTSTRAP_SCRIPT}'
"

echo "========== AstroRoshni startup complete $(date -u) =========="
