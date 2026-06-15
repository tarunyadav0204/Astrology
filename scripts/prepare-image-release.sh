#!/bin/bash

set -euo pipefail

PREP_T0=$(date +%s)
LAST_T=$PREP_T0
prep_timing() {
  local now wall total step
  now=$(date +%s)
  wall=$(date '+%Y-%m-%d %H:%M:%S')
  total=$((now - PREP_T0))
  step=$((now - LAST_T))
  echo "⏱️  ${wall}  | +${total}s total  | +${step}s last step  — ${1}"
  LAST_T=$now
}

echo "🏗️ Preparing baked release image contents..."
prep_timing "image prep started"

APP_ROOT="${APP_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
BACKEND_DIR="${BACKEND_DIR:-${APP_ROOT}/backend}"
FRONTEND_DIR="${FRONTEND_DIR:-${APP_ROOT}/frontend}"
LOG_DIR="${LOG_DIR:-${APP_ROOT}/logs}"
BACKEND_PORT="${BACKEND_PORT:-8001}"
SYNC_GCP_SECRETS="${SYNC_GCP_SECRETS:-true}"
APP_ENV_SECRET_NAME="${APP_ENV_SECRET_NAME:-APP_ENV_FILE}"
WHATSAPP_FLOW_PRIVATE_KEY_SECRET_NAME="${WHATSAPP_FLOW_PRIVATE_KEY_SECRET_NAME:-WHATSAPP_FLOW_PRIVATE_KEY_FILE}"
WHATSAPP_FLOW_PRIVATE_KEY_PATH="${WHATSAPP_FLOW_PRIVATE_KEY_PATH:-/home/tarun_yadav/AstrologyApp/backend/flow_endpoint_private.pem}"
SERVE_FRONTEND_LOCALLY="${SERVE_FRONTEND_LOCALLY:-false}"
INSTALL_GCP_OPS_AGENT="${INSTALL_GCP_OPS_AGENT:-true}"
FORCE_BACKEND_PIP="${FORCE_BACKEND_PIP:-true}"
FORCE_FRONTEND_INSTALL="${FORCE_FRONTEND_INSTALL:-true}"
FORCE_FRONTEND_BUILD="${FORCE_FRONTEND_BUILD:-true}"
PRERENDER="${PRERENDER:-true}"
APP_COMMIT_SHA="${APP_COMMIT_SHA:-image-build}"
BUILD_METADATA_FILE="${BUILD_METADATA_FILE:-${APP_ROOT}/.image-build-metadata.json}"

case "$(printf '%s' "${SYNC_GCP_SECRETS}" | tr '[:upper:]' '[:lower:]')" in
  true|1|yes) SYNC_GCP_SECRETS=true ;;
  *) SYNC_GCP_SECRETS=false ;;
esac
case "$(printf '%s' "${SERVE_FRONTEND_LOCALLY}" | tr '[:upper:]' '[:lower:]')" in
  true|1|yes) SERVE_FRONTEND_LOCALLY=true ;;
  *) SERVE_FRONTEND_LOCALLY=false ;;
esac
case "$(printf '%s' "${INSTALL_GCP_OPS_AGENT}" | tr '[:upper:]' '[:lower:]')" in
  true|1|yes) INSTALL_GCP_OPS_AGENT=true ;;
  *) INSTALL_GCP_OPS_AGENT=false ;;
esac
case "$(printf '%s' "${FORCE_BACKEND_PIP}" | tr '[:upper:]' '[:lower:]')" in
  true|1|yes) FORCE_BACKEND_PIP=true ;;
  *) FORCE_BACKEND_PIP=false ;;
esac
case "$(printf '%s' "${FORCE_FRONTEND_INSTALL}" | tr '[:upper:]' '[:lower:]')" in
  true|1|yes) FORCE_FRONTEND_INSTALL=true ;;
  *) FORCE_FRONTEND_INSTALL=false ;;
esac
case "$(printf '%s' "${FORCE_FRONTEND_BUILD}" | tr '[:upper:]' '[:lower:]')" in
  true|1|yes) FORCE_FRONTEND_BUILD=true ;;
  *) FORCE_FRONTEND_BUILD=false ;;
esac
case "$(printf '%s' "${PRERENDER}" | tr '[:upper:]' '[:lower:]')" in
  true|1|yes) PRERENDER=true ;;
  *) PRERENDER=false ;;
esac

if [ ! -d "${APP_ROOT}" ] || [ ! -f "${BACKEND_DIR}/main.py" ]; then
  echo "❌ App checkout is incomplete under ${APP_ROOT}"
  exit 1
fi

mkdir -p "${LOG_DIR}"

sync_gcp_secret_to_file() {
  local secret_name="$1"
  local target_path="$2"
  local mode="$3"
  local temp_path

  if ! command -v gcloud >/dev/null 2>&1; then
    echo "❌ gcloud CLI not found"
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
  prep_timing "gcp secret sync finished"
fi

if [ "${INSTALL_GCP_OPS_AGENT}" = "true" ]; then
  echo "🛰️ Ensuring Google Cloud Ops Agent is installed and configured..."
  APP_ROOT="${APP_ROOT}" "${APP_ROOT}/scripts/install_ops_agent.sh"
  prep_timing "ops agent install/apply finished"
fi

cd "${BACKEND_DIR}"
if [ ! -d "venv" ]; then
  python3 -m venv venv
fi
source venv/bin/activate

if [ "${FORCE_BACKEND_PIP}" = "true" ]; then
  echo "📦 Installing backend dependencies for baked image..."
  PIP_DISABLE_PIP_VERSION_CHECK=1 pip3 install -q -r requirements.txt
  prep_timing "backend pip finished"
fi

echo "🔐 Setting up encryption..."
python3 setup_encryption.py || true
prep_timing "encryption setup finished"

echo "🧹 Clearing backend port ${BACKEND_PORT} before temporary build-time start..."
fuser -k "${BACKEND_PORT}"/tcp 2>/dev/null || true
pkill -f "python main.py" 2>/dev/null || true
pkill -f "uvicorn.*${BACKEND_PORT}" 2>/dev/null || true

DEFAULT_PLAY_BILLING_KEY="/home/tarun_yadav/play-billing-key.json"
if [ -z "${GOOGLE_PLAY_SERVICE_ACCOUNT_JSON:-}" ] && [ -f "${DEFAULT_PLAY_BILLING_KEY}" ]; then
  export GOOGLE_PLAY_SERVICE_ACCOUNT_JSON="${DEFAULT_PLAY_BILLING_KEY}"
fi
export APP_COMMIT_SHA
export PYTHONUNBUFFERED=1

echo "🚀 Starting temporary backend for frontend build dependencies..."
nohup python main.py >> "${LOG_DIR}/backend.log" 2>&1 &
TEMP_BACKEND_PID=$!
backend_ready=false
for i in $(seq 1 20); do
  if curl -fsS --max-time 5 "http://127.0.0.1:${BACKEND_PORT}/api/health" >/dev/null; then
    backend_ready=true
    break
  fi
  if ! ps -p "${TEMP_BACKEND_PID}" >/dev/null; then
    echo "❌ Temporary backend exited before health check passed"
    tail -80 "${LOG_DIR}/backend.log"
    exit 1
  fi
  sleep 2
done
if [ "${backend_ready}" != "true" ]; then
  echo "❌ Temporary backend health check did not pass"
  tail -80 "${LOG_DIR}/backend.log"
  exit 1
fi
prep_timing "temporary backend up for frontend build"

if [ "${SERVE_FRONTEND_LOCALLY}" = "true" ]; then
  cd "${FRONTEND_DIR}"
  if [ "${FORCE_FRONTEND_INSTALL}" = "true" ]; then
    echo "📦 Installing frontend dependencies for baked image..."
    npm install
    prep_timing "frontend npm install finished"
  fi
  if [ "${FORCE_FRONTEND_BUILD}" = "true" ]; then
    echo "🏗️ Building frontend for baked image..."
    export CI=true
    export GENERATE_SOURCEMAP=false
    export INLINE_RUNTIME_CHUNK=true
    export PRERENDER
    unset PRERENDER_ROUTES
    SITEMAP_URL="${SITEMAP_URL:-http://127.0.0.1:${BACKEND_PORT}/sitemap.xml}" \
    BLOG_API_URL="${BLOG_API_URL:-http://127.0.0.1:${BACKEND_PORT}}" \
    npm run build
    prep_timing "frontend build finished"
  fi
fi

if ps -p "${TEMP_BACKEND_PID}" >/dev/null; then
  kill "${TEMP_BACKEND_PID}" 2>/dev/null || true
  sleep 2
fi

python3 - <<'PY' > "${BUILD_METADATA_FILE}"
import json, os, time
print(json.dumps({
    "baked_at_epoch": int(time.time()),
    "app_commit_sha": os.environ.get("APP_COMMIT_SHA", "image-build"),
    "serve_frontend_locally": os.environ.get("SERVE_FRONTEND_LOCALLY", "true"),
}, indent=2))
PY
prep_timing "image metadata written"

echo "✅ Baked release image contents are ready"
