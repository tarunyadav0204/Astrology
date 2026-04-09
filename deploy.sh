#!/bin/bash

# Automated deployment script for Astrology App
#
# Order: (1) backend venv/pip + encryption → (2) restart backend + /api/health —
# then (3) frontend npm build → (4) restart static server only if build ran or 3001
# is down. Mobile clients keep talking to a live API while the web bundle rebuilds.
set -e

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
if [ ! -d "frontend/node_modules" ] || [ "${FORCE_FULL_DEPLOY}" = "true" ]; then
  needs_frontend_install=true
fi
if [ "${FORCE_FULL_DEPLOY}" = "true" ] || [ ! -d "frontend/build" ]; then
  needs_frontend_build=true
elif echo "${CHANGED_FILES}" | grep -E -q '^frontend/'; then
  needs_frontend_build=true
  if echo "${CHANGED_FILES}" | grep -E -q '^frontend/package(-lock)?\.json$'; then
    needs_frontend_install=true
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
if [ -z "${PREV_HEAD}" ] || [ "${FORCE_FULL_DEPLOY}" = "true" ]; then
  needs_backend_pip=true
elif echo "${CHANGED_FILES}" | grep -qE '^backend/requirements\.txt$'; then
  needs_backend_pip=true
fi

if [ "${FORCE_BACKEND_PIP}" = "true" ]; then
  needs_backend_pip=true
fi

if [ "${SKIP_BACKEND_PIP}" = "true" ] && [ "${FORCE_BACKEND_PIP}" != "true" ]; then
  if [ -z "${PREV_HEAD}" ] || [ "${FORCE_FULL_DEPLOY}" = "true" ]; then
    echo "⚠️ SKIP_BACKEND_PIP ignored (first deploy or FORCE_FULL_DEPLOY)"
  elif echo "${CHANGED_FILES}" | grep -qE '^backend/requirements\.txt$'; then
    echo "⚠️ SKIP_BACKEND_PIP ignored (backend/requirements.txt changed)"
  else
    needs_backend_pip=false
  fi
fi

echo "📋 needs_backend_pip=${needs_backend_pip} FORCE_BACKEND_PIP=${FORCE_BACKEND_PIP} SKIP_BACKEND_PIP=${SKIP_BACKEND_PIP} needs_frontend_install=${needs_frontend_install} needs_frontend_build=${needs_frontend_build}"

# Repo root (deploy.sh is always run from here)
APP_ROOT="$(pwd)"

# --- Phase 1: backend dependencies (venv, pip, encryption) ---
echo "🐍 Setting up backend..."
cd "${APP_ROOT}/backend"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
  python3 -m venv venv
fi

# Activate virtual environment and install dependencies
source venv/bin/activate
if [ "${needs_backend_pip}" = "true" ]; then
  echo "📦 Installing backend dependencies..."
  PIP_DISABLE_PIP_VERSION_CHECK=1 pip3 install -q -r requirements.txt
  echo "✅ Backend dependencies installed"
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

# --- Phase 2: restart backend first (API live before frontend work — least impact on mobile) ---
echo "🔄 Restarting backend (frontend left running until new build is ready)..."
cd "${APP_ROOT}"

echo "Stopping restart monitor..."
pkill -f restart_server.sh 2>/dev/null || true
sleep 1

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

export GOOGLE_PLAY_SERVICE_ACCOUNT_JSON="${GOOGLE_PLAY_SERVICE_ACCOUNT_JSON:-/home/tarun_yadav/play-billing-key.json}"

echo "Starting backend..."
nohup python main.py > "${APP_ROOT}/logs/backend.log" 2>&1 &
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
        echo "❌ Backend process exited before health check passed"
        tail -80 "${APP_ROOT}/logs/backend.log"
        exit 1
      fi
      sleep 2
    done

    if [ "$backend_ready" != "true" ]; then
      echo "❌ Health check did not pass in time"
      tail -80 "${APP_ROOT}/logs/backend.log"
      exit 1
    fi
    deploy_timing "backend up and /api/health OK"
else
    echo "❌ Backend failed to start. Check logs:"
    tail -20 "${APP_ROOT}/logs/backend.log"
    exit 1
fi

# --- Phase 3: frontend install/build (API already serving new code) ---
echo "⚛️ Building frontend..."
cd "${APP_ROOT}/frontend"
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
  npm run build
  deploy_timing "npm run build finished"
else
  echo "⏭️ Frontend unchanged; skipping build"
  deploy_timing "npm build skipped"
fi
echo "✅ Frontend phase complete"

# --- Phase 4: restart static server only when needed (new build or not listening) ---
cd "${APP_ROOT}"
restart_frontend=false
if [ "${needs_frontend_build}" = "true" ]; then
  restart_frontend=true
fi
if ! ss -ltn 2>/dev/null | grep -qE ':3001\s'; then
  echo "ℹ️ Nothing on 3001; will start frontend static server"
  restart_frontend=true
fi

if [ "${restart_frontend}" = "true" ]; then
  echo "Stopping existing frontend on 3001..."
  fuser -k 3001/tcp 2>/dev/null || true
  pkill -f "serve -s build -l 3001" 2>/dev/null || true
  for i in 1 2 3 4 5 6 7 8 9 10; do
    if ! ss -ltn 2>/dev/null | grep -qE ':3001\s'; then
      break
    fi
    sleep 1
  done
  deploy_timing "frontend port cleared"

  cd "${APP_ROOT}/frontend"
  nohup npx serve -s build -l 3001 > "${APP_ROOT}/logs/frontend.log" 2>&1 &
  echo "✅ Frontend started on port 3001"
  deploy_timing "npx serve (frontend static) started"
else
  echo "⏭️ Leaving existing frontend server on 3001 running (no new build)"
  deploy_timing "frontend serve unchanged"
fi

# --- Phase 5: auto-restart monitor (backend watchdog) ---
echo "🔄 Starting auto-restart monitor..."
cd "${APP_ROOT}"
nohup ./restart_server.sh > logs/monitor.log 2>&1 &
MONITOR_PID=$!
echo "✅ Auto-restart monitor started with PID: $MONITOR_PID"
deploy_timing "restart monitor started"

TOTAL=$(( $(date +%s) - DEPLOY_T0 ))
echo "🎉 Deployment completed successfully! (total wall time: ${TOTAL}s)"
echo "📊 Backend: http://localhost:8001"
echo "🌐 Frontend: http://localhost:3001"
echo "🔄 Monitor: PID $MONITOR_PID (logs/monitor.log)"