#!/bin/bash

# Server setup script for GCP deployment
set -e

echo "🔧 Setting up server for Astrology App..."

# Update system
sudo apt update && sudo apt upgrade -y

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install Python and pip
sudo apt install -y python3 python3-pip

# Install serve globally for frontend
sudo npm install -g serve

# Clone repository
git clone https://github.com/tarunyadav0204/Astrology.git AstrologyApp
cd AstrologyApp

# Setup systemd service
sudo cp systemd/astrology-app.service /etc/systemd/system/

# Enable service
sudo systemctl daemon-reload
sudo systemctl enable astrology-app

# Initial deployment
bash deploy.sh

echo "✅ Server setup completed!"
echo "📊 Backend API: http://your-server:8001"
echo "🌐 Frontend: http://your-server:3001"