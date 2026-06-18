#!/bin/bash

set -euo pipefail

BOOTSTRAP_T0=$(date +%s)
LAST_T=$BOOTSTRAP_T0

bootstrap_timing() {
  local now wall total step
  now=$(date +%s)
  wall=$(date '+%Y-%m-%d %H:%M:%S')
  total=$((now - BOOTSTRAP_T0))
  step=$((now - LAST_T))
  echo "⏱️  ${wall}  | +${total}s total  | +${step}s last step  — ${1}"
  LAST_T=$now
}

echo "🚀 Starting runtime bootstrap..."
bootstrap_timing "bootstrap script started"

APP_ROOT="${APP_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
BACKEND_DIR="${BACKEND_DIR:-${APP_ROOT}/backend}"
LOG_DIR="${LOG_DIR:-${APP_ROOT}/logs}"
BACKEND_LOG_FILE="${BACKEND_LOG_FILE:-${LOG_DIR}/backend.log}"
BACKEND_MONITOR_SCRIPT="${BACKEND_MONITOR_SCRIPT:-${APP_ROOT}/scripts/run_backend_with_monitor.sh}"
BACKEND_PORT="${BACKEND_PORT:-8001}"
FRONTEND_PORT="${FRONTEND_PORT:-3001}"
SERVE_FRONTEND_LOCALLY="${SERVE_FRONTEND_LOCALLY:-true}"
FRONTEND_LOG_FILE="${FRONTEND_LOG_FILE:-${LOG_DIR}/frontend.log}"
SYNC_GCP_SECRETS="${SYNC_GCP_SECRETS:-true}"
APP_ENV_SECRET_NAME="${APP_ENV_SECRET_NAME:-APP_ENV_FILE}"
WHATSAPP_FLOW_PRIVATE_KEY_SECRET_NAME="${WHATSAPP_FLOW_PRIVATE_KEY_SECRET_NAME:-WHATSAPP_FLOW_PRIVATE_KEY_FILE}"
WHATSAPP_FLOW_PRIVATE_KEY_PATH="${WHATSAPP_FLOW_PRIVATE_KEY_PATH:-/home/tarun_yadav/AstrologyApp/backend/flow_endpoint_private.pem}"
PLAY_PAYMENT_SERVICE_SHARED_SECRET_NAME="${PLAY_PAYMENT_SERVICE_SHARED_SECRET_NAME:-PLAY_PAYMENT_SERVICE_SHARED_SECRET}"
PLAY_PAYMENT_SERVICE_SHARED_SECRET_PATH="${PLAY_PAYMENT_SERVICE_SHARED_SECRET_PATH:-/home/tarun_yadav/AstrologyApp/secrets/play_payment_service_shared_secret}"
INSTALL_GCP_OPS_AGENT="${INSTALL_GCP_OPS_AGENT:-false}"
SKIP_BACKEND_RESTART="${SKIP_BACKEND_RESTART:-false}"
SKIP_FRONTEND_RESTART="${SKIP_FRONTEND_RESTART:-false}"
BACKEND_HEALTH_URL="${BACKEND_HEALTH_URL:-http://127.0.0.1:${BACKEND_PORT}/api/health}"
BACKEND_HEALTH_ATTEMPTS="${BACKEND_HEALTH_ATTEMPTS:-20}"
BACKEND_HEALTH_SLEEP_SECONDS="${BACKEND_HEALTH_SLEEP_SECONDS:-2}"
FRONTEND_HEALTH_URL="${FRONTEND_HEALTH_URL:-http://127.0.0.1:${FRONTEND_PORT}/}"
FRONTEND_HEALTH_ATTEMPTS="${FRONTEND_HEALTH_ATTEMPTS:-20}"
FRONTEND_HEALTH_SLEEP_SECONDS="${FRONTEND_HEALTH_SLEEP_SECONDS:-1}"
APP_COMMIT_SHA="${APP_COMMIT_SHA:-unknown-version}"
UVICORN_WORKERS="${UVICORN_WORKERS:-1}"

case "$(printf '%s' "${SYNC_GCP_SECRETS}" | tr '[:upper:]' '[:lower:]')" in
  true|1|yes) SYNC_GCP_SECRETS=true ;;
  *) SYNC_GCP_SECRETS=false ;;
esac
case "$(printf '%s' "${INSTALL_GCP_OPS_AGENT}" | tr '[:upper:]' '[:lower:]')" in
  true|1|yes) INSTALL_GCP_OPS_AGENT=true ;;
  *) INSTALL_GCP_OPS_AGENT=false ;;
esac
case "$(printf '%s' "${SKIP_BACKEND_RESTART}" | tr '[:upper:]' '[:lower:]')" in
  true|1|yes) SKIP_BACKEND_RESTART=true ;;
  *) SKIP_BACKEND_RESTART=false ;;
esac
case "$(printf '%s' "${SKIP_FRONTEND_RESTART}" | tr '[:upper:]' '[:lower:]')" in
  true|1|yes) SKIP_FRONTEND_RESTART=true ;;
  *) SKIP_FRONTEND_RESTART=false ;;
esac
case "$(printf '%s' "${SERVE_FRONTEND_LOCALLY}" | tr '[:upper:]' '[:lower:]')" in
  true|1|yes) SERVE_FRONTEND_LOCALLY=true ;;
  *) SERVE_FRONTEND_LOCALLY=false ;;
esac

if [ ! -d "${APP_ROOT}" ]; then
  echo "❌ APP_ROOT does not exist: ${APP_ROOT}"
  exit 1
fi
if [ ! -d "${BACKEND_DIR}" ]; then
  echo "❌ BACKEND_DIR does not exist: ${BACKEND_DIR}"
  exit 1
fi
if [ ! -f "${BACKEND_DIR}/main.py" ]; then
  echo "❌ backend entrypoint missing: ${BACKEND_DIR}/main.py"
  exit 1
fi
if [ ! -d "${BACKEND_DIR}/venv" ]; then
  echo "❌ baked backend virtualenv missing: ${BACKEND_DIR}/venv"
  exit 1
fi

mkdir -p "${LOG_DIR}"

sync_gcp_secret_to_file() {
  local secret_name="$1"
  local target_path="$2"
  local mode="$3"
  local temp_path

  if [ -z "${secret_name}" ] || [ -z "${target_path}" ]; then
    echo "❌ Secret sync misconfigured: secret name and target path are required"
    exit 1
  fi
  if ! command -v gcloud >/dev/null 2>&1; then
    echo "❌ gcloud CLI not found. Install/configure Google Cloud SDK or set SYNC_GCP_SECRETS=false."
    exit 1
  fi

  mkdir -p "$(dirname "${target_path}")"
  temp_path="$(mktemp "${target_path}.tmp.XXXXXX")"
  chmod 600 "${temp_path}" 2>/dev/null || true
  if ! gcloud secrets versions access latest --secret="${secret_name}" > "${temp_path}"; then
    rm -f "${temp_path}"
    echo "❌ Failed to read Secret Manager secret: ${secret_name}"
    exit 1
  fi
  if [ ! -s "${temp_path}" ]; then
    rm -f "${temp_path}"
    echo "❌ Secret Manager secret is empty: ${secret_name}"
    exit 1
  fi
  chmod "${mode}" "${temp_path}"
  mv "${temp_path}" "${target_path}"
}

if [ "${SYNC_GCP_SECRETS}" = "true" ]; then
  echo "🔑 Pulling runtime secrets from Google Secret Manager..."
  sync_gcp_secret_to_file "${APP_ENV_SECRET_NAME}" "${BACKEND_DIR}/.env" 600
  sync_gcp_secret_to_file "${WHATSAPP_FLOW_PRIVATE_KEY_SECRET_NAME}" "${WHATSAPP_FLOW_PRIVATE_KEY_PATH}" 600
  sync_gcp_secret_to_file "${PLAY_PAYMENT_SERVICE_SHARED_SECRET_NAME}" "${PLAY_PAYMENT_SERVICE_SHARED_SECRET_PATH}" 600
  if ! grep -q "BEGIN .*PRIVATE KEY" "${WHATSAPP_FLOW_PRIVATE_KEY_PATH}"; then
    echo "❌ WhatsApp Flow private key file does not look like a PEM private key: ${WHATSAPP_FLOW_PRIVATE_KEY_PATH}"
    exit 1
  fi
  echo "✅ Runtime secrets synced"
  bootstrap_timing "gcp secret sync finished"
else
  echo "⏭️ Skipping Google Secret Manager sync (SYNC_GCP_SECRETS=false)"
fi

if [ "${INSTALL_GCP_OPS_AGENT}" = "true" ]; then
  echo "🛰️ Ensuring Google Cloud Ops Agent is installed and configured..."
  APP_ROOT="${APP_ROOT}" "${APP_ROOT}/scripts/install_ops_agent.sh"
  bootstrap_timing "ops agent install/apply finished"
else
  echo "⏭️ Skipping Ops Agent install/apply (INSTALL_GCP_OPS_AGENT=false)"
fi

cd "${BACKEND_DIR}"
source venv/bin/activate

if [ ! -f "${BACKEND_DIR}/.env" ]; then
  echo "❌ backend/.env missing after bootstrap"
  exit 1
fi

DEFAULT_PLAY_BILLING_KEY="/home/tarun_yadav/play-billing-key.json"
if [ -z "${GOOGLE_PLAY_SERVICE_ACCOUNT_JSON:-}" ] && [ -f "${DEFAULT_PLAY_BILLING_KEY}" ]; then
  export GOOGLE_PLAY_SERVICE_ACCOUNT_JSON="${DEFAULT_PLAY_BILLING_KEY}"
fi
if [ -z "${PLAY_PAYMENT_SERVICE_SHARED_SECRET:-}" ] && [ -f "${PLAY_PAYMENT_SERVICE_SHARED_SECRET_PATH}" ]; then
  export PLAY_PAYMENT_SERVICE_SHARED_SECRET="$(tr -d '\r\n' < "${PLAY_PAYMENT_SERVICE_SHARED_SECRET_PATH}")"
fi
export APP_COMMIT_SHA
export UVICORN_WORKERS
export PYTHONUNBUFFERED=1

if [ "${SKIP_BACKEND_RESTART}" = "true" ]; then
  echo "⏭️ Skipping backend restart/start (SKIP_BACKEND_RESTART=true)"
  exit 0
fi

echo "🧹 Clearing backend port ${BACKEND_PORT} before start..."
echo "Backend listeners before cleanup:"
ss -ltnp 2>/dev/null | grep ":${BACKEND_PORT}\\b" || true
echo "Backend processes before cleanup:"
ps -ef | grep -E "python main.py|uvicorn" | grep -v grep || true
fuser -k "${BACKEND_PORT}"/tcp 2>/dev/null || true
pkill -TERM -f "python main.py" 2>/dev/null || true
pkill -TERM -f "uvicorn.*${BACKEND_PORT}" 2>/dev/null || true

for i in 1 2 3 4 5 6 7 8 9 10; do
  if ! ss -ltn 2>/dev/null | grep -qE ":${BACKEND_PORT}\\s"; then
    break
  fi
  sleep 1
done

if ss -ltn 2>/dev/null | grep -qE ":${BACKEND_PORT}\\s"; then
  echo "⚠️ Backend port still busy after TERM cleanup, forcing kill..."
  fuser -k -9 "${BACKEND_PORT}"/tcp 2>/dev/null || true
  pkill -KILL -f "python main.py" 2>/dev/null || true
  pkill -KILL -f "uvicorn.*${BACKEND_PORT}" 2>/dev/null || true
  sleep 2
fi

echo "Backend listeners after cleanup:"
ss -ltnp 2>/dev/null | grep ":${BACKEND_PORT}\\b" || true
echo "Backend processes after cleanup:"
ps -ef | grep -E "python main.py|uvicorn" | grep -v grep || true
bootstrap_timing "backend port cleared"

echo "Starting backend (logs go to journald / Cloud Logging)..."
if [ ! -f "${BACKEND_MONITOR_SCRIPT}" ]; then
  echo "❌ Backend monitor script missing: ${BACKEND_MONITOR_SCRIPT}"
  exit 1
fi
logger -t astroroshni-backend-monitor -- "bootstrap_backend_start commit=${APP_COMMIT_SHA}"
logger -t astroroshni-backend-monitor -- "bootstrap_backend_env uvicorn_workers=${UVICORN_WORKERS} backend_port=${BACKEND_PORT}"
nohup bash "${BACKEND_MONITOR_SCRIPT}" >/dev/null 2>&1 &
BACKEND_PID=$!
echo "Backend PID: ${BACKEND_PID}"
sleep 2

if ! ps -p "${BACKEND_PID}" > /dev/null; then
  echo "❌ Backend failed to start. Check Cloud Logging / journalctl tag astroroshni-backend"
  exit 1
fi

echo "✅ Backend started successfully on port ${BACKEND_PORT}"
backend_ready=false
for i in $(seq 1 "${BACKEND_HEALTH_ATTEMPTS}"); do
  if curl -fsS --max-time 5 "${BACKEND_HEALTH_URL}" >/dev/null; then
    echo "✅ Backend health check passed"
    backend_ready=true
    break
  fi
  if ! ps -p "${BACKEND_PID}" > /dev/null; then
    echo "❌ Backend process exited before health check passed. Check Cloud Logging / journalctl tags astroroshni-backend and astroroshni-backend-monitor"
    exit 1
  fi
  sleep "${BACKEND_HEALTH_SLEEP_SECONDS}"
done

if [ "${backend_ready}" != "true" ]; then
  echo "❌ Health check did not pass in time. Check Cloud Logging / journalctl tag astroroshni-backend"
  exit 1
fi

bootstrap_timing "backend up and /api/health OK"

if [ "${SERVE_FRONTEND_LOCALLY}" = "true" ] && [ "${SKIP_FRONTEND_RESTART}" != "true" ]; then
  FRONTEND_DIR="${APP_ROOT}/frontend"
  if [ ! -d "${FRONTEND_DIR}" ]; then
    echo "❌ frontend directory missing: ${FRONTEND_DIR}"
    exit 1
  fi
  if [ ! -f "${FRONTEND_DIR}/build/index.html" ]; then
    echo "❌ baked frontend build missing: ${FRONTEND_DIR}/build/index.html"
    exit 1
  fi
  if [ ! -d "${FRONTEND_DIR}/node_modules" ]; then
    echo "❌ baked frontend node_modules missing: ${FRONTEND_DIR}/node_modules"
    exit 1
  fi

  echo "🧹 Clearing frontend port ${FRONTEND_PORT} before start..."
  fuser -k "${FRONTEND_PORT}"/tcp 2>/dev/null || true
  pkill -f "serve-build.mjs" 2>/dev/null || true
  pkill -f "serve build -l ${FRONTEND_PORT}" 2>/dev/null || true
  pkill -f "serve -s build -l ${FRONTEND_PORT}" 2>/dev/null || true
  for i in 1 2 3 4 5 6 7 8 9 10; do
    if ! ss -ltn 2>/dev/null | grep -qE ":${FRONTEND_PORT}\\s"; then
      break
    fi
    sleep 1
  done
  bootstrap_timing "frontend port cleared"

  cd "${FRONTEND_DIR}"
  echo "Starting frontend (appending to ${FRONTEND_LOG_FILE})..."
  {
    echo ""
    echo "========== Bootstrap frontend start $(date -u '+%Y-%m-%d %H:%M:%S UTC') commit=${APP_COMMIT_SHA} =========="
  } >> "${FRONTEND_LOG_FILE}"
  nohup node scripts/serve-build.mjs >> "${FRONTEND_LOG_FILE}" 2>&1 &
  FRONTEND_PID=$!
  echo "Frontend PID: ${FRONTEND_PID}"
  sleep 2

  if ! ps -p "${FRONTEND_PID}" >/dev/null; then
    echo "❌ Frontend failed to start. Check logs:"
    tail -40 "${FRONTEND_LOG_FILE}"
    exit 1
  fi

  frontend_ready=false
  for i in $(seq 1 "${FRONTEND_HEALTH_ATTEMPTS}"); do
    if curl -fsS --max-time 5 "${FRONTEND_HEALTH_URL}" >/dev/null; then
      echo "✅ Frontend health check passed"
      frontend_ready=true
      break
    fi
    if ! ps -p "${FRONTEND_PID}" >/dev/null; then
      echo "❌ Frontend process exited before health check passed"
      tail -80 "${FRONTEND_LOG_FILE}"
      exit 1
    fi
    sleep "${FRONTEND_HEALTH_SLEEP_SECONDS}"
  done

  if [ "${frontend_ready}" != "true" ]; then
    echo "❌ Frontend health check did not pass in time"
    tail -80 "${FRONTEND_LOG_FILE}"
    exit 1
  fi

  bootstrap_timing "frontend up and / ready"
elif [ "${SERVE_FRONTEND_LOCALLY}" = "true" ]; then
  echo "⏭️ Skipping frontend restart/start (SKIP_FRONTEND_RESTART=true)"
else
  echo "⏭️ Local frontend serving disabled (SERVE_FRONTEND_LOCALLY=false)"
fi

echo "✅ Runtime bootstrap complete"
