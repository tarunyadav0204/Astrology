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

# Kill existing astrology app processes only
pkill -f "AstrologyApp.*python.*main.py" || true
pkill -f "AstrologyApp.*serve -s build" || true

# Start backend
cd backend
source venv/bin/activate
nohup python3 main.py > ../logs/backend.log 2>&1 &
echo "✅ Backend started on port 8001"

# Start frontend
cd ../frontend
nohup npx serve -s build -l 3001 > ../logs/frontend.log 2>&1 &
echo "✅ Frontend started on port 3001"

echo "🎉 Deployment completed successfully!"
echo "📊 Backend: http://localhost:8001"
echo "🌐 Frontend: http://localhost:3001"