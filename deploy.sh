#!/bin/bash

# Automated deployment script for Astrology App
set -e

echo "🚀 Starting deployment..."

# Pull latest changes
echo "📥 Pulling latest changes from Git..."
git fetch origin main
git reset --hard origin/main

# Backend deployment
echo "🐍 Setting up backend..."
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
  python3 -m venv venv
fi

# Activate virtual environment and install dependencies
source venv/bin/activate
pip install -r requirements.txt
echo "✅ Backend dependencies installed"

# Frontend deployment
echo "⚛️ Building frontend..."
cd ../frontend
npm install
npm run build
echo "✅ Frontend built successfully"

# Start services
echo "🔄 Restarting services..."
cd ..

# Kill existing processes on ports 8001 and 3001
echo "Stopping existing services..."
fuser -k 8001/tcp 2>/dev/null || true
fuser -k 3001/tcp 2>/dev/null || true
sleep 3

# Start backend
cd backend
source venv/bin/activate

# Create logs directory if it doesn't exist
mkdir -p ../logs

# Start backend with better error handling
echo "Starting backend..."
nohup python main.py > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"
sleep 3

# Check if backend is running
if ps -p $BACKEND_PID > /dev/null; then
    echo "✅ Backend started successfully on port 8001"
    # Test health endpoint
    curl -f http://localhost:8001/api/health || echo "⚠️ Health check failed"
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

# Kill existing restart monitor if running
pkill -f restart_server.sh 2>/dev/null || true
sleep 2

# Start the restart monitor in background
nohup ./restart_server.sh > logs/monitor.log 2>&1 &
MONITOR_PID=$!
echo "✅ Auto-restart monitor started with PID: $MONITOR_PID"

echo "🎉 Deployment completed successfully!"
echo "📊 Backend: http://localhost:8001"
echo "🌐 Frontend: http://localhost:3001"
echo "🔄 Monitor: PID $MONITOR_PID (logs/monitor.log)"