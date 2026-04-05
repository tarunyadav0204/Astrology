#!/bin/bash

# Automated deployment script for Astrology App
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

# Backend: always `pip install -r requirements.txt` on every deploy.
# Relying only on git-diff for requirements.txt misses cases (e.g. merge order,
# manual pulls) and caused prod to skip new packages like psycopg2-binary.

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

# Backend pip: skip when this deploy only touches paths outside backend/ (saves minutes of resolver I/O).
# Still run when requirements or any backend file changed, first deploy (no PREV_HEAD), or FORCE_FULL_DEPLOY.
needs_backend_pip=true
if [ "${FORCE_FULL_DEPLOY}" = "true" ] || [ -z "${PREV_HEAD}" ]; then
  needs_backend_pip=true
elif echo "${CHANGED_FILES}" | grep -q . && ! echo "${CHANGED_FILES}" | grep -qE '^backend/'; then
  needs_backend_pip=false
fi

echo "📋 needs_backend_pip=${needs_backend_pip} needs_frontend_install=${needs_frontend_install} needs_frontend_build=${needs_frontend_build}"

# Backend deployment
echo "🐍 Setting up backend..."
cd backend

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
  echo "⏭️ No backend/ changes; skipping pip install (venv unchanged)"
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

# Frontend deployment
echo "⚛️ Building frontend..."
cd ../frontend
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
  # Faster production build: no browser sourcemaps, CI mode trims checks slightly in CRA
  export CI=true
  export GENERATE_SOURCEMAP=false
  export INLINE_RUNTIME_CHUNK=true
  npm run build
  deploy_timing "npm run build finished"
else
  echo "⏭️ Frontend unchanged; skipping build"
  deploy_timing "npm build skipped"
fi
echo "✅ Frontend built successfully"

# Start services
echo "🔄 Restarting services..."
cd ..

# Stop restart monitor first to avoid it racing deploy and re-spawning services
echo "Stopping restart monitor..."
pkill -f restart_server.sh 2>/dev/null || true
sleep 1

# Kill existing processes on ports 8001 and 3001
echo "Stopping existing services..."
fuser -k 8001/tcp 2>/dev/null || true
fuser -k 3001/tcp 2>/dev/null || true
pkill -f "python main.py" 2>/dev/null || true
pkill -f "uvicorn.*8001" 2>/dev/null || true
pkill -f "serve -s build -l 3001" 2>/dev/null || true

# Wait until both ports are fully free before starting
for i in 1 2 3 4 5 6 7 8 9 10; do
  if ! ss -ltn 2>/dev/null | grep -qE ':(8001|3001)\s'; then
    break
  fi
  sleep 1
done
deploy_timing "old processes stopped, ports free"

# Start backend
cd backend
source venv/bin/activate

# Create logs directory if it doesn't exist
mkdir -p ../logs

# Google Play billing verification (service account JSON path on server)
export GOOGLE_PLAY_SERVICE_ACCOUNT_JSON="${GOOGLE_PLAY_SERVICE_ACCOUNT_JSON:-/home/tarun_yadav/play-billing-key.json}"

# Start backend with better error handling
echo "Starting backend..."
nohup python main.py > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"
sleep 2

# Check if backend is running
if ps -p $BACKEND_PID > /dev/null; then
    echo "✅ Backend started successfully on port 8001"
    # Retry health check with longer warm-up window.
    backend_ready=false
    for i in $(seq 1 20); do
      if curl -fsS http://localhost:8001/api/health >/dev/null; then
        echo "✅ Backend health check passed"
        backend_ready=true
        break
      fi

      # If process exited, fail fast and print logs.
      if ! ps -p $BACKEND_PID > /dev/null; then
        echo "❌ Backend process exited before health check passed"
        tail -80 ../logs/backend.log
        exit 1
      fi

      sleep 2
    done

    if [ "$backend_ready" != "true" ]; then
      echo "❌ Health check did not pass in time"
      tail -80 ../logs/backend.log
      exit 1
    fi
    deploy_timing "backend up and /api/health OK"
else
    echo "❌ Backend failed to start. Check logs:"
    tail -20 ../logs/backend.log
    exit 1
fi

# Start frontend
cd ../frontend
nohup npx serve -s build -l 3001 > ../logs/frontend.log 2>&1 &
echo "✅ Frontend started on port 3001"
deploy_timing "npx serve (frontend static) started"

# Start auto-restart monitor
echo "🔄 Starting auto-restart monitor..."
cd ..

# Start the restart monitor in background
nohup ./restart_server.sh > logs/monitor.log 2>&1 &
MONITOR_PID=$!
echo "✅ Auto-restart monitor started with PID: $MONITOR_PID"
deploy_timing "restart monitor started"

TOTAL=$(( $(date +%s) - DEPLOY_T0 ))
echo "🎉 Deployment completed successfully! (total wall time: ${TOTAL}s)"
echo "📊 Backend: http://localhost:8001"
echo "🌐 Frontend: http://localhost:3001"
echo "🔄 Monitor: PID $MONITOR_PID (logs/monitor.log)"