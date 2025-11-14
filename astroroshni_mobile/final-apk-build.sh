#!/bin/bash

echo "🚀 Final APK Build Attempt for AstroRoshni..."

export PATH="/usr/local/bin:$PATH"

# Try using Expo's turtle-cli (legacy but works)
echo "📱 Installing turtle-cli for APK generation..."
npm install -g turtle-cli

# Login to Expo (if needed)
echo "🔐 Logging into Expo..."
turtle setup:android

# Build APK using turtle
echo "🐢 Building APK with turtle-cli..."
turtle build:android --type apk --release-channel production

echo "✅ APK build completed!"