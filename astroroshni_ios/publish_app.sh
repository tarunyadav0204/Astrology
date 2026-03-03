#!/bin/bash

echo "🚀 Publishing AstroRoshni Mobile App to Expo"
echo "============================================"

# Navigate to mobile app directory
cd "$(dirname "$0")"

# Check if EAS CLI is installed
if ! command -v eas &> /dev/null; then
    echo "📦 Installing EAS CLI..."
    npm install -g @expo/eas-cli
fi

# Login to Expo (will prompt for credentials)
echo "🔐 Logging into Expo..."
eas login

# Configure EAS Updates if not already configured
if [ ! -f "eas.json" ]; then
    echo "⚙️  Configuring EAS Updates..."
    eas update:configure
fi

# Publish the update
echo "📤 Publishing update..."
eas update --branch preview --message "Release for friends - $(date)"

echo ""
echo "✅ App published successfully!"
echo ""
echo "📱 Share with friends:"
echo "1. Friends install 'Expo Go' from App Store"
echo "2. Share the QR code or URL from above"
echo "3. Friends scan QR code or enter URL in Expo Go"
echo ""
echo "🔄 To publish updates later, just run this script again!"