#!/bin/bash

# Automated deployment script for Astrology App
#
# Order: (1) backend venv/pip + encryption → (2) restart backend + /api/health if needed —
# then (3) frontend npm build → (4) restart static server only if build ran or 3001
# is down. Frontend-only deploys skip (2) when /api/health is already OK so mobile
# keeps the same API process during long npm build.
set -e

APP_ROOT="${APP_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
BACKEND_MONITOR_SCRIPT="${APP_ROOT}/scripts/run_backend_with_monitor.sh"
cd "${APP_ROOT}"

# Timestamps: wall clock, seconds since deploy start, seconds since previous timing line.
DEPLOY_T0=$(date +%s)
LAST_T=$DEPLOY_T0
deploy_timing() {
  local now wall total step
  now=$(date +%s)
  wall=$(date '+%Y-%m-%d %H:%M:%S')
  total=$((now - DEPLOY_T0))
  step=$((now - LAST_T))
  echo "⏱️  ${wall}  | +${total}s total  | +${step}s last step  — ${1}"
  LAST_T=$now
}

echo "🚀 Starting deployment..."
deploy_timing "deploy script started"

# Deploy branch on the server (default: main).
# Can be overridden by setting DEPLOY_BRANCH in the SSH script, e.g.:
#   DEPLOY_BRANCH=test bash deploy.sh
DEPLOY_BRANCH="${DEPLOY_BRANCH:-main}"
echo "📌 Deploying branch: ${DEPLOY_BRANCH}"
FORCE_FULL_DEPLOY="${FORCE_FULL_DEPLOY:-false}"
FORCE_FRONTEND_DEPLOY="${FORCE_FRONTEND_DEPLOY:-false}"
DEFER_FRONTEND_BUILD="${DEFER_FRONTEND_BUILD:-false}"
SERVE_FRONTEND_LOCALLY="${SERVE_FRONTEND_LOCALLY:-true}"
FRONTEND_PREBUILT_ARCHIVE="${FRONTEND_PREBUILT_ARCHIVE:-}"
case "$(printf '%s' "${FORCE_FULL_DEPLOY}" | tr '[:upper:]' '[:lower:]')" in
  true|1|yes) FORCE_FULL_DEPLOY=true ;;
  *) FORCE_FULL_DEPLOY=false ;;
esac
case "$(printf '%s' "${FORCE_FRONTEND_DEPLOY}" | tr '[:upper:]' '[:lower:]')" in
  true|1|yes) FORCE_FRONTEND_DEPLOY=true ;;
  *) FORCE_FRONTEND_DEPLOY=false ;;
esac
case "$(printf '%s' "${DEFER_FRONTEND_BUILD}" | tr '[:upper:]' '[:lower:]')" in
  true|1|yes) DEFER_FRONTEND_BUILD=true ;;
  *) DEFER_FRONTEND_BUILD=false ;;
esac
case "$(printf '%s' "${SERVE_FRONTEND_LOCALLY}" | tr '[:upper:]' '[:lower:]')" in
  true|1|yes) SERVE_FRONTEND_LOCALLY=true ;;
  *) SERVE_FRONTEND_LOCALLY=false ;;
esac

has_frontend_prebuilt=false
if [ -n "${FRONTEND_PREBUILT_ARCHIVE}" ]; then
  if [ ! -f "${FRONTEND_PREBUILT_ARCHIVE}" ]; then
    echo "❌ FRONTEND_PREBUILT_ARCHIVE not found: ${FRONTEND_PREBUILT_ARCHIVE}"
    exit 1
  fi
  has_frontend_prebuilt=true
fi

# Pull latest changes
echo "📥 Pulling latest changes from Git..."
PREV_HEAD="$(git rev-parse --short HEAD 2>/dev/null || echo '')"
git fetch origin "${DEPLOY_BRANCH}"
git reset --hard "origin/${DEPLOY_BRANCH}"
NEW_HEAD="$(git rev-parse --short HEAD)"
echo "🔎 Deploying commit: ${PREV_HEAD} -> ${NEW_HEAD}"

CHANGED_FILES=""
if [ -n "${PREV_HEAD}" ]; then
  CHANGED_FILES="$(git diff --name-only "${PREV_HEAD}" "${NEW_HEAD}" || true)"
fi
deploy_timing "git fetch/reset and diff complete"

# Optional: trigger / override pip from commit message (after pull, HEAD is the deployed commit).
#   [pip]  [deps]  [full-pip]  → run pip even if only backend .py changed
#   [skip-pip] → skip pip when safe (not when requirements.txt changed or first deploy)
COMMIT_MSG="$(git log -1 --format=%B 2>/dev/null || true)"
if echo "${COMMIT_MSG}" | grep -qiE '\[(pip|deps|full-pip)\]'; then
  echo "📌 Commit message tag: forcing backend pip ([pip] / [deps] / [full-pip])"
  FORCE_BACKEND_PIP=true
fi
if echo "${COMMIT_MSG}" | grep -qiE '\[skip-pip\]'; then
  echo "📌 Commit message tag: skip pip if safe ([skip-pip])"
  SKIP_BACKEND_PIP=true
fi

needs_frontend_install=false
needs_frontend_build=false
if [ "${SERVE_FRONTEND_LOCALLY}" = "true" ]; then
  if [ ! -d "frontend/node_modules" ] || [ "${FORCE_FULL_DEPLOY}" = "true" ]; then
    needs_frontend_install=true
  fi
  if [ "${FORCE_FULL_DEPLOY}" = "true" ] || [ "${FORCE_FRONTEND_DEPLOY}" = "true" ] || [ ! -d "frontend/build" ]; then
    needs_frontend_build=true
  elif echo "${CHANGED_FILES}" | grep -E -q '^frontend/|^frontend-next/'; then
    needs_frontend_build=true
    if echo "${CHANGED_FILES}" | grep -E -q '^frontend/package(-lock)?\.json$'; then
      needs_frontend_install=true
    fi
  fi
fi

frontend_build_deferred=false
if [ "${SERVE_FRONTEND_LOCALLY}" = "true" ] && [ "${DEFER_FRONTEND_BUILD}" = "true" ] && [ "${FORCE_FRONTEND_DEPLOY}" != "true" ] && [ "${has_frontend_prebuilt}" != "true" ]; then
  if [ "${needs_frontend_install}" = "true" ] || [ "${needs_frontend_build}" = "true" ]; then
    echo "⏭️ Deferring frontend install/build for this run (DEFER_FRONTEND_BUILD=true)"
    frontend_build_deferred=true
    needs_frontend_install=false
    needs_frontend_build=false
  fi
fi

# Backend pip (default: rare — only when requirements change or first deploy).
# Override: FORCE_BACKEND_PIP=true (env, e.g. GitHub "Run workflow" checkbox) or [pip] in commit message.
# Skip:    SKIP_BACKEND_PIP=true or [skip-pip] in message — ignored if requirements.txt changed or first deploy.
FORCE_BACKEND_PIP="${FORCE_BACKEND_PIP:-false}"
SKIP_BACKEND_PIP="${SKIP_BACKEND_PIP:-false}"
# Normalize env from CI (GitHub may pass boolean-ish strings)
case "$(printf '%s' "${FORCE_BACKEND_PIP}" | tr '[:upper:]' '[:lower:]')" in
  true|1|yes) FORCE_BACKEND_PIP=true ;;
  *) FORCE_BACKEND_PIP=false ;;
esac
case "$(printf '%s' "${SKIP_BACKEND_PIP}" | tr '[:upper:]' '[:lower:]')" in
  true|1|yes) SKIP_BACKEND_PIP=true ;;
  *) SKIP_BACKEND_PIP=false ;;
esac

needs_backend_pip=false
if [ ! -d "backend/venv" ] || [ -z "${PREV_HEAD}" ] || [ "${FORCE_FULL_DEPLOY}" = "true" ]; then
  needs_backend_pip=true
elif echo "${CHANGED_FILES}" | grep -qE '^backend/requirements\.txt$'; then
  needs_backend_pip=true
fi

if [ "${FORCE_BACKEND_PIP}" = "true" ]; then
  needs_backend_pip=true
fi

# Self-heal: MIG replacements / skipped pip can leave a venv with old reportlab
# (no TTFont shapable=) or missing uharfbuzz — force install when the PDF stack is broken.
if [ "${needs_backend_pip}" = "false" ] && [ -d "backend/venv" ]; then
  if ! "backend/venv/bin/python" - <<'PY' >/dev/null 2>&1
import inspect
import reportlab
from reportlab.pdfbase.ttfonts import TTFont
import uharfbuzz  # noqa: F401
assert "shapable" in inspect.signature(TTFont.__init__).parameters, reportlab.Version
PY
  then
    echo "⚠️ Forcing backend pip: reportlab/uharfbuzz shapable stack missing or too old in venv"
    needs_backend_pip=true
  fi
fi

if [ "${SKIP_BACKEND_PIP}" = "true" ] && [ "${FORCE_BACKEND_PIP}" != "true" ]; then
  if [ -z "${PREV_HEAD}" ] || [ "${FORCE_FULL_DEPLOY}" = "true" ]; then
    echo "⚠️ SKIP_BACKEND_PIP ignored (first deploy or FORCE_FULL_DEPLOY)"
  elif echo "${CHANGED_FILES}" | grep -qE '^backend/requirements\.txt$'; then
    echo "⚠️ SKIP_BACKEND_PIP ignored (backend/requirements.txt changed)"
  elif [ "${needs_backend_pip}" = "true" ]; then
    echo "⚠️ SKIP_BACKEND_PIP ignored (PDF dependency self-heal required)"
  else
    needs_backend_pip=false
  fi
fi

echo "📋 needs_backend_pip=${needs_backend_pip} FORCE_BACKEND_PIP=${FORCE_BACKEND_PIP} SKIP_BACKEND_PIP=${SKIP_BACKEND_PIP} FORCE_FRONTEND_DEPLOY=${FORCE_FRONTEND_DEPLOY} FORCE_FULL_DEPLOY=${FORCE_FULL_DEPLOY} DEFER_FRONTEND_BUILD=${DEFER_FRONTEND_BUILD} SERVE_FRONTEND_LOCALLY=${SERVE_FRONTEND_LOCALLY} needs_frontend_install=${needs_frontend_install} needs_frontend_build=${needs_frontend_build} frontend_build_deferred=${frontend_build_deferred} has_frontend_prebuilt=${has_frontend_prebuilt}"

# Repo root
APP_ROOT="$(pwd)"
APP_USER="${APP_USER:-$(id -un)}"
WATCHDOG_INSTALLER="${APP_ROOT}/scripts/install_runtime_watchdog.sh"

# --- Secret Manager sync: materialize runtime-only secrets before backend imports .env ---
# Keep secret names configurable so staging/prod can use different Secret Manager entries.
SYNC_GCP_SECRETS="${SYNC_GCP_SECRETS:-true}"
APP_ENV_SECRET_NAME="${APP_ENV_SECRET_NAME:-APP_ENV_FILE}"
WHATSAPP_FLOW_PRIVATE_KEY_SECRET_NAME="${WHATSAPP_FLOW_PRIVATE_KEY_SECRET_NAME:-WHATSAPP_FLOW_PRIVATE_KEY_FILE}"
WHATSAPP_FLOW_PRIVATE_KEY_PATH="${WHATSAPP_FLOW_PRIVATE_KEY_PATH:-/home/tarun_yadav/AstrologyApp/backend/flow_endpoint_private.pem}"
PLAY_PAYMENT_SERVICE_SHARED_SECRET_NAME="${PLAY_PAYMENT_SERVICE_SHARED_SECRET_NAME:-PLAY_PAYMENT_SERVICE_SHARED_SECRET}"
PLAY_PAYMENT_SERVICE_SHARED_SECRET_PATH="${PLAY_PAYMENT_SERVICE_SHARED_SECRET_PATH:-/home/tarun_yadav/AstrologyApp/secrets/play_payment_service_shared_secret}"
INSTALL_GCP_OPS_AGENT="${INSTALL_GCP_OPS_AGENT:-true}"

case "$(printf '%s' "${SYNC_GCP_SECRETS}" | tr '[:upper:]' '[:lower:]')" in
  true|1|yes) SYNC_GCP_SECRETS=true ;;
  *) SYNC_GCP_SECRETS=false ;;
esac
case "$(printf '%s' "${INSTALL_GCP_OPS_AGENT}" | tr '[:upper:]' '[:lower:]')" in
  true|1|yes) INSTALL_GCP_OPS_AGENT=true ;;
  *) INSTALL_GCP_OPS_AGENT=false ;;
esac

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
  sync_gcp_secret_to_file "${APP_ENV_SECRET_NAME}" "${APP_ROOT}/backend/.env" 600
  sync_gcp_secret_to_file "${WHATSAPP_FLOW_PRIVATE_KEY_SECRET_NAME}" "${WHATSAPP_FLOW_PRIVATE_KEY_PATH}" 600
  sync_gcp_secret_to_file "${PLAY_PAYMENT_SERVICE_SHARED_SECRET_NAME}" "${PLAY_PAYMENT_SERVICE_SHARED_SECRET_PATH}" 600
  if ! grep -q "BEGIN .*PRIVATE KEY" "${WHATSAPP_FLOW_PRIVATE_KEY_PATH}"; then
    echo "❌ WhatsApp Flow private key file does not look like a PEM private key: ${WHATSAPP_FLOW_PRIVATE_KEY_PATH}"
    exit 1
  fi
  echo "✅ Runtime secrets synced"
  deploy_timing "gcp secret sync finished"
else
  echo "⏭️ Skipping Google Secret Manager sync (SYNC_GCP_SECRETS=false)"
fi

if [ "${INSTALL_GCP_OPS_AGENT}" = "true" ]; then
  echo "🛰️ Ensuring Google Cloud Ops Agent is installed and configured..."
  APP_ROOT="${APP_ROOT}" "${APP_ROOT}/scripts/install_ops_agent.sh"
  deploy_timing "ops agent install/apply finished"
else
  echo "⏭️ Skipping Ops Agent install/apply (INSTALL_GCP_OPS_AGENT=false)"
fi

if [ -f "${WATCHDOG_INSTALLER}" ]; then
  echo "🛟 Ensuring runtime watchdog service is installed..."
  sudo APP_USER="${APP_USER}" APP_DIR="${APP_ROOT}" bash "${WATCHDOG_INSTALLER}"
  deploy_timing "runtime watchdog install/apply finished"
else
  echo "⚠️ Runtime watchdog installer missing: ${WATCHDOG_INSTALLER}"
fi

# --- Phase 1: backend dependencies (venv, pip, encryption) ---
echo "🐍 Setting up backend..."
cd "${APP_ROOT}/backend"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
  python3 -m venv venv
fi

# Activate virtual environment and install dependencies
source venv/bin/activate
# Prefer venv interpreter's pip — bare `pip3` can install into system Python.
VENV_PYTHON="${APP_ROOT}/backend/venv/bin/python"
if [ ! -x "${VENV_PYTHON}" ]; then
  VENV_PYTHON="$(command -v python3)"
fi
if [ "${needs_backend_pip}" = "true" ]; then
  echo "📦 Installing backend dependencies into ${VENV_PYTHON}..."
  PIP_DISABLE_PIP_VERSION_CHECK=1 "${VENV_PYTHON}" -m pip install -r requirements.txt
  echo "🔎 Verifying reportlab shapable + uharfbuzz in venv..."
  if ! "${VENV_PYTHON}" - <<'PY'
import inspect
import reportlab
from reportlab.pdfbase.ttfonts import TTFont
import uharfbuzz  # noqa: F401
print(f"reportlab={reportlab.Version}")
print(f"uharfbuzz_ok=True")
assert "shapable" in inspect.signature(TTFont.__init__).parameters, (
    f"TTFont still lacks shapable= (reportlab={reportlab.Version}). "
    "Upgrade reportlab>=4.1 in the venv."
)
# Smoke-register path without needing a font file for kwarg acceptance.
print("shapable_kwarg_ok=True")
PY
  then
    echo "❌ Backend venv is missing a working reportlab/uharfbuzz shapable stack after pip"
    "${VENV_PYTHON}" -m pip show reportlab uharfbuzz || true
    exit 1
  fi
  echo "✅ Backend dependencies installed and verified"
else
  echo "⏭️ Skipping pip install (requirements.txt unchanged — use [pip] in commit message, FORCE_BACKEND_PIP=true, or workflow checkbox to force)"
fi
deploy_timing "backend pip (or skip) finished"

# Setup encryption (idempotent - safe to run multiple times)
echo "🔐 Setting up encryption..."
python3 setup_encryption.py
if [ $? -eq 0 ]; then
    echo "✅ Encryption setup complete"
else
    echo "⚠️ Encryption setup failed, continuing without encryption"
fi
deploy_timing "encryption setup finished"

# --- Phase 2: restart backend when backend/ changed or API unhealthy (skip for frontend-only) ---
restart_backend=true
if [ "${needs_backend_pip}" = "true" ]; then
  # Dependency changes must pick up the new venv packages.
  restart_backend=true
  echo "🔄 Backend restart required after pip install"
elif [ "${FORCE_FULL_DEPLOY}" != "true" ]; then
  backend_changed=false
  if [ -n "${CHANGED_FILES}" ] && echo "${CHANGED_FILES}" | grep -qE '^backend/'; then
    backend_changed=true
  fi

  if [ "${FORCE_FRONTEND_DEPLOY}" = "true" ] || { [ -n "${PREV_HEAD}" ] && [ "${backend_changed}" != "true" ]; }; then
    if curl -fsS --max-time 5 http://localhost:8001/api/health >/dev/null 2>&1; then
      restart_backend=false
      echo "⏭️ Frontend-only deploy and /api/health OK — skipping backend restart (keeps mobile API traffic up)"
    else
      echo "⚠️ Frontend-only deploy requested but /api/health failed — restarting backend"
    fi
  fi
fi

cd "${APP_ROOT}"

if [ "${restart_backend}" = "true" ]; then
  echo "Stopping restart monitor..."
  pkill -f restart_server.sh 2>/dev/null || true
  sleep 1

  echo "🔄 Restarting backend (frontend left running until new build is ready)..."
  echo "Stopping existing backend on 8001..."
  fuser -k 8001/tcp 2>/dev/null || true
  pkill -f "python main.py" 2>/dev/null || true
  pkill -f "uvicorn.*8001" 2>/dev/null || true

  for i in 1 2 3 4 5 6 7 8 9 10; do
    if ! ss -ltn 2>/dev/null | grep -qE ':8001\s'; then
      break
    fi
    sleep 1
  done
  deploy_timing "backend port cleared"

  cd "${APP_ROOT}/backend"
  source venv/bin/activate

  mkdir -p "${APP_ROOT}/logs"

  DEFAULT_PLAY_BILLING_KEY="/home/tarun_yadav/play-billing-key.json"
  if [ -z "${GOOGLE_PLAY_SERVICE_ACCOUNT_JSON:-}" ] && [ -f "${DEFAULT_PLAY_BILLING_KEY}" ]; then
    export GOOGLE_PLAY_SERVICE_ACCOUNT_JSON="${DEFAULT_PLAY_BILLING_KEY}"
  fi
  if [ -z "${PLAY_PAYMENT_SERVICE_SHARED_SECRET:-}" ] && [ -f "${PLAY_PAYMENT_SERVICE_SHARED_SECRET_PATH}" ]; then
    export PLAY_PAYMENT_SERVICE_SHARED_SECRET="$(tr -d '\r\n' < "${PLAY_PAYMENT_SERVICE_SHARED_SECRET_PATH}")"
  fi
  export APP_COMMIT_SHA="${NEW_HEAD}"
  export PYTHONUNBUFFERED=1

  echo "Starting backend (logs go to journald / Cloud Logging)..."
  if [ ! -f "${BACKEND_MONITOR_SCRIPT}" ]; then
      echo "❌ Backend monitor script missing: ${BACKEND_MONITOR_SCRIPT}"
      exit 1
  fi
  logger -t astroroshni-backend-monitor -- "deploy_backend_start commit=${NEW_HEAD}"
  nohup bash "${BACKEND_MONITOR_SCRIPT}" >/dev/null 2>&1 &
  BACKEND_PID=$!
  echo "Backend PID: $BACKEND_PID"
  sleep 2

  if ps -p $BACKEND_PID > /dev/null; then
      echo "✅ Backend started successfully on port 8001"
      backend_ready=false
      for i in $(seq 1 20); do
        if curl -fsS http://localhost:8001/api/health >/dev/null; then
          echo "✅ Backend health check passed"
          backend_ready=true
          break
        fi
        if ! ps -p $BACKEND_PID > /dev/null; then
          echo "❌ Backend process exited before health check passed. Check Cloud Logging / journalctl tags astroroshni-backend and astroroshni-backend-monitor"
          exit 1
        fi
        sleep 2
      done

      if [ "$backend_ready" != "true" ]; then
        echo "❌ Health check did not pass in time. Check Cloud Logging / journalctl tag astroroshni-backend"
        exit 1
      fi
      deploy_timing "backend up and /api/health OK"
  else
      echo "❌ Backend failed to start. Check Cloud Logging / journalctl tag astroroshni-backend"
      exit 1
  fi
else
  deploy_timing "backend restart skipped (frontend-only deploy)"
fi

staged_frontend_build=false
if [ "${SERVE_FRONTEND_LOCALLY}" = "true" ]; then
  # --- Phase 3: frontend install/build (API already serving new code) ---
  echo "⚛️ Building frontend..."
  cd "${APP_ROOT}/frontend"
  frontend_stage_dir="${APP_ROOT}/frontend/.build-deploy-stage"
  if [ "${needs_frontend_build}" = "true" ] && [ "${has_frontend_prebuilt}" = "true" ]; then
    echo "📦 Using prebuilt frontend artifact: ${FRONTEND_PREBUILT_ARCHIVE}"
    rm -rf "${frontend_stage_dir}"
    mkdir -p "${frontend_stage_dir}"
    tar -xzf "${FRONTEND_PREBUILT_ARCHIVE}" -C "${frontend_stage_dir}"
    if [ ! -f "${frontend_stage_dir}/build/index.html" ]; then
      echo "❌ Prebuilt frontend artifact is missing build/index.html"
      exit 1
    fi
    staged_frontend_build=true
    deploy_timing "frontend artifact unpacked"
  else
    if [ "${needs_frontend_install}" = "true" ]; then
      echo "📦 Installing frontend dependencies..."
      npm install
      deploy_timing "npm install finished"
    else
      echo "⏭️ Frontend dependencies unchanged; skipping npm install"
      deploy_timing "npm install skipped"
    fi

    if [ "${needs_frontend_build}" = "true" ]; then
      echo "🏗️ Frontend changed; building..."
      export CI=true
      export GENERATE_SOURCEMAP=false
      export INLINE_RUNTIME_CHUNK=true
      # SEO: prerender CRA routes (homepage + key public URLs) so crawlers get correct <link rel="canonical"> in first HTML.
      # Omit PRERENDER_ROUTES to use the full list in frontend/scripts/postbuild-seo.mjs (STATIC + nakshatras + blog).
      export PRERENDER=true
      unset PRERENDER_ROUTES
      SITEMAP_URL="${SITEMAP_URL:-http://127.0.0.1:8001/sitemap.xml}" \
      BLOG_API_URL="${BLOG_API_URL:-http://127.0.0.1:8001}" \
      npm run build
      deploy_timing "npm run build finished (includes frontend-next karma export)"
    else
      echo "⏭️ Frontend unchanged; skipping build"
      deploy_timing "npm build skipped"
    fi
  fi
  echo "✅ Frontend phase complete"
else
  echo "⏭️ Local frontend serving disabled; skipping frontend build/deploy on this VM"
  deploy_timing "frontend build skipped (external static hosting)"
fi

# --- Phase 4: restart static server only when needed (new build or not listening) ---
cd "${APP_ROOT}"
frontend_build_available=false
if [ "${SERVE_FRONTEND_LOCALLY}" = "true" ] && [ -f "${APP_ROOT}/frontend/build/index.html" ]; then
  frontend_build_available=true
fi
restart_frontend=false
if [ "${SERVE_FRONTEND_LOCALLY}" = "true" ] && [ "${needs_frontend_build}" = "true" ]; then
  restart_frontend=true
fi
if [ "${SERVE_FRONTEND_LOCALLY}" != "true" ]; then
  echo "⏭️ Local frontend serving disabled; skipping frontend static server changes"
elif [ "${frontend_build_deferred}" = "true" ]; then
  echo "⏭️ Frontend startup deferred for this deploy; skipping frontend static server changes"
elif ! ss -ltn 2>/dev/null | grep -qE ':3001\s'; then
  if [ "${frontend_build_available}" = "true" ]; then
    echo "ℹ️ Nothing on 3001; will start frontend static server"
    restart_frontend=true
  else
    echo "❌ Nothing is listening on 3001 and frontend/build/index.html is missing"
    exit 1
  fi
fi

if [ "${restart_frontend}" = "true" ]; then
  echo "Stopping existing frontend on 3001..."
  fuser -k 3001/tcp 2>/dev/null || true
  pkill -f "serve-build.mjs" 2>/dev/null || true
  pkill -f "serve build -l 3001" 2>/dev/null || true
  pkill -f "serve -s build -l 3001" 2>/dev/null || true
  for i in 1 2 3 4 5 6 7 8 9 10; do
    if ! ss -ltn 2>/dev/null | grep -qE ':3001\s'; then
      break
    fi
    sleep 1
  done
  deploy_timing "frontend port cleared"

  cd "${APP_ROOT}/frontend"
  frontend_build_dir="${APP_ROOT}/frontend/build"
  frontend_backup_dir="${APP_ROOT}/frontend/build.previous"
  if [ "${staged_frontend_build}" = "true" ]; then
    echo "🔁 Swapping in staged frontend build..."
    rm -rf "${frontend_backup_dir}"
    if [ -d "${frontend_build_dir}" ]; then
      mv "${frontend_build_dir}" "${frontend_backup_dir}"
    fi
    mv "${frontend_stage_dir}/build" "${frontend_build_dir}"
    rm -rf "${frontend_stage_dir}"
    if [ -d "${frontend_backup_dir}/static" ] && [ -d "${frontend_build_dir}/static" ]; then
      echo "🧷 Preserving previous hashed /static assets for compatibility during rollout..."
      cp -Rn "${frontend_backup_dir}/static/." "${frontend_build_dir}/static/" 2>/dev/null || true
    fi
    deploy_timing "frontend build swapped"
  fi

  nohup node scripts/serve-build.mjs > "${APP_ROOT}/logs/frontend.log" 2>&1 &
  FRONTEND_PID=$!
  echo "Frontend PID: ${FRONTEND_PID}"

  frontend_ready=false
  for i in $(seq 1 20); do
    if curl -fsS --max-time 3 http://127.0.0.1:3001/ >/dev/null 2>&1; then
      frontend_ready=true
      break
    fi
    if ! ps -p "${FRONTEND_PID}" >/dev/null; then
      echo "❌ Frontend static server exited before it was ready. Check logs:"
      tail -80 "${APP_ROOT}/logs/frontend.log"
      exit 1
    fi
    sleep 1
  done

  if [ "${frontend_ready}" != "true" ]; then
    if [ "${staged_frontend_build}" = "true" ] && [ -d "${frontend_backup_dir}" ]; then
      echo "↩️ Restoring previous frontend build after failed startup..."
      rm -rf "${frontend_build_dir}"
      mv "${frontend_backup_dir}" "${frontend_build_dir}"
      nohup node scripts/serve-build.mjs > "${APP_ROOT}/logs/frontend.log" 2>&1 &
      sleep 2
    fi
    echo "❌ Frontend static server did not become ready on port 3001"
    tail -80 "${APP_ROOT}/logs/frontend.log"
    exit 1
  fi

  rm -rf "${frontend_backup_dir}" 2>/dev/null || true
  echo "✅ Frontend started on port 3001"
  deploy_timing "frontend static server started"
else
  echo "⏭️ Leaving existing frontend server on 3001 running (no new build)"
  deploy_timing "frontend serve unchanged"
fi

verify_frontend_routes=true
if [ "${SERVE_FRONTEND_LOCALLY}" != "true" ] || [ "${frontend_build_deferred}" = "true" ] || ! ss -ltn 2>/dev/null | grep -qE ':3001\s'; then
  verify_frontend_routes=false
fi

if [ "${verify_frontend_routes}" = "true" ]; then
echo "🔎 Verifying public SEO routes..."
cd "${APP_ROOT}"
# Next static export: clean URLs for tool landing pages.
# Root "/" is CRA index.html (Puppeteer prerender in postbuild-seo.mjs), not Next — never expect Next-only copy on /.
verify_route_marker() {
  local route="$1"
  local marker="$2"
  local desc="$3"
  local url="http://127.0.0.1:3001${route}"
  if curl -fsS --max-time 20 "${url}" | grep -Fq "${marker}"; then
    echo "✅ ${route} — ${desc}"
  else
    echo "❌ ${route} — missing expected marker for: ${desc}"
    echo "   curl -fsS --max-time 20 ${url} | head -c 4000"
    echo "   Check frontend/build, scripts/serve-build.mjs on 3001, and route content."
    exit 1
  fi
}

# Match postbuild-seo.mjs: both strings must appear in prerendered HTML (fixed-string grep; retries for slow bind).
verify_homepage_prerender() {
  local url="http://127.0.0.1:3001/"
  local attempt html
  for attempt in 1 2 3 4 5 6; do
    html="$(curl -fsS --max-time 25 "${url}" 2>/dev/null || true)"
    if printf '%s' "${html}" | grep -Fq "Ask Tara your questions" \
      && printf '%s' "${html}" | grep -Fq "Frequently asked questions"; then
      echo "✅ / — CRA homepage HTML (prerender; markers OK)"
      return 0
    fi
    sleep 2
  done
  echo "❌ / — CRA homepage prerender markers missing after retries"
  echo "   Expected literal substrings: Ask Tara your questions  AND  Frequently asked questions"
  echo "   (Root is CRA + postbuild-seo, not Next karma/kundli/chat HTML.)"
  if [ -f "${APP_ROOT}/frontend/build/index.html" ]; then
    if grep -Fq "Ask Tara your questions" "${APP_ROOT}/frontend/build/index.html" 2>/dev/null; then
      echo "   ℹ️  frontend/build/index.html on disk contains Ask Tara — check serve-build.mjs / port 3001."
    else
      echo "   ℹ️  frontend/build/index.html on disk also lacks Ask Tara — rerun PRERENDER=true npm run build in frontend/."
    fi
  fi
  exit 1
}

verify_route_marker "/karma-analysis" "Past Life Karma Analysis" "Next SEO HTML (karma)"
verify_route_marker "/kundli-matching" "Kundli Matching" "Next SEO HTML (kundli)"
verify_route_marker "/chat" "AI Vedic Astrologer Chat" "Next SEO HTML (chat)"
verify_route_marker "/reports" "Why Reports Studio?" "CRA prerendered Reports Studio (Partnership + Wealth)"
verify_homepage_prerender
deploy_timing "frontend SEO route verification complete"
else
  echo "⏭️ Skipping frontend SEO route verification because frontend is externalized, deferred, or not running in this deploy"
  deploy_timing "frontend verification skipped"
fi

# --- Phase 5: keep local watchdog disabled; MIG autohealing is the single recovery owner ---
echo "⏭️ Leaving local backend watchdog disabled (MIG autohealing owns recovery)"
cd "${APP_ROOT}"
deploy_timing "watchdog disabled"

TOTAL=$(( $(date +%s) - DEPLOY_T0 ))
echo "🎉 Deployment completed successfully! (total wall time: ${TOTAL}s)"
echo "📊 Backend: http://localhost:8001"
if [ "${frontend_build_deferred}" = "true" ]; then
  echo "🌐 Frontend: deferred during this deploy"
elif [ "${SERVE_FRONTEND_LOCALLY}" != "true" ]; then
  echo "🌐 Frontend: external static hosting (not served from this VM)"
else
  echo "🌐 Frontend: http://localhost:3001"
fi
echo "🔄 Watchdog: disabled (MIG health checks should use a lightweight endpoint)"
echo "📋 Logs: logs/backend.log (append), logs/frontend.log"
