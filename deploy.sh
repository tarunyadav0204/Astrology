#!/bin/bash

# Automated deployment script for Astrology App
set -e

echo "🚀 Starting deployment..."

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

# Backend deployment
echo "🐍 Setting up backend..."
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
  python3 -m venv venv
fi

# Activate virtual environment and install dependencies
source venv/bin/activate
echo "📦 Installing backend dependencies (always; idempotent)..."
pip3 install -r requirements.txt
echo "✅ Backend dependencies installed"

# Setup encryption (idempotent - safe to run multiple times)
echo "🔐 Setting up encryption..."
python3 setup_encryption.py
if [ $? -eq 0 ]; then
    echo "✅ Encryption setup complete"
else
    echo "⚠️ Encryption setup failed, continuing without encryption"
fi

# Frontend deployment
echo "⚛️ Building frontend..."
cd ../frontend
if [ "${needs_frontend_install}" = "true" ]; then
  echo "📦 Installing frontend dependencies..."
  npm install
else
  echo "⏭️ Frontend dependencies unchanged; skipping npm install"
fi

if [ "${needs_frontend_build}" = "true" ]; then
  echo "🏗️ Frontend changed; building..."
  npm run build
else
  echo "⏭️ Frontend unchanged; skipping build"
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
else
    echo "❌ Backend failed to start. Check logs:"
    tail -20 ../logs/backend.log
    exit 1
fi

# Start frontend
cd ../frontend
nohup npx serve -s build -l 3001 > ../logs/frontend.log 2>&1 &
echo "✅ Frontend started on port 3001"

# Start auto-restart monitor
echo "🔄 Starting auto-restart monitor..."
cd ..

# Start the restart monitor in background
nohup ./restart_server.sh > logs/monitor.log 2>&1 &
MONITOR_PID=$!
echo "✅ Auto-restart monitor started with PID: $MONITOR_PID"

echo "🎉 Deployment completed successfully!"
echo "📊 Backend: http://localhost:8001"
echo "🌐 Frontend: http://localhost:3001"
echo "🔄 Monitor: PID $MONITOR_PID (logs/monitor.log)"