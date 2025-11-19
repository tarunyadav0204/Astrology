#!/bin/bash

echo "🔄 Upgrading Expo SDK to 54.0.0"
echo "================================"

# Navigate to mobile app directory
cd "$(dirname "$0")"

# Upgrade Expo SDK
echo "📦 Upgrading Expo SDK..."
npx expo install --fix

# Install dependencies
echo "📦 Installing dependencies..."
npm install

# Clear cache
echo "🧹 Clearing cache..."
npx expo r -c

echo ""
echo "✅ Expo SDK upgraded to 54.0.0!"
echo ""
echo "🚀 Now run: ./publish_app.sh"