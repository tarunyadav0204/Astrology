#!/bin/bash

# Automated deployment script for Astrology App
set -e

echo "🚀 Starting deployment..."

# Pull latest changes
echo "📥 Pulling latest changes from Git..."
git pull origin main

# Backend deployment
echo "🐍 Setting up backend..."
cd backend
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

# Kill existing processes
pkill -f "python main.py" || true
pkill -f "serve -s build" || true

# Start backend
cd backend
nohup python main.py > ../logs/backend.log 2>&1 &
echo "✅ Backend started on port 8000"

# Start frontend
cd ../frontend
nohup npx serve -s build -l 3000 > ../logs/frontend.log 2>&1 &
echo "✅ Frontend started on port 3000"

echo "🎉 Deployment completed successfully!"
echo "📊 Backend: http://localhost:8000"
echo "🌐 Frontend: http://localhost:3000"