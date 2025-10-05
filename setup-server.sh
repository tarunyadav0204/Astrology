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

# Install webhook dependencies
npm install

# Setup systemd services
sudo cp systemd/astrology-app.service /etc/systemd/system/
sudo cp systemd/astrology-webhook.service /etc/systemd/system/

# Enable and start services
sudo systemctl daemon-reload
sudo systemctl enable astrology-app
sudo systemctl enable astrology-webhook

# Initial deployment
bash deploy.sh

# Start webhook server
sudo systemctl start astrology-webhook

echo "✅ Server setup completed!"
echo "🎣 Webhook server: http://your-server:9000/webhook"
echo "📊 Backend API: http://your-server:8000"
echo "🌐 Frontend: http://your-server:3000"