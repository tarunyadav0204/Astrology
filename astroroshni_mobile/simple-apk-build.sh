#!/bin/bash

echo "🚀 Creating Simple APK Build..."

export PATH="/usr/local/bin:$PATH"

# Create a simple React Native bundle
echo "📦 Creating React Native bundle..."
npx react-native bundle --platform android --dev false --entry-file index.js --bundle-output android/app/src/main/assets/index.android.bundle --assets-dest android/app/src/main/res/

# Copy assets
echo "📁 Copying assets..."
mkdir -p android/app/src/main/assets
cp -r assets/* android/app/src/main/res/drawable/ 2>/dev/null || true

# Build APK directly
echo "🔨 Building APK..."
cd android
export JAVA_HOME="/opt/homebrew/Cellar/openjdk@17/17.0.17/libexec/openjdk.jdk/Contents/Home"
./gradlew clean
./gradlew assembleDebug

echo "✅ APK created at: android/app/build/outputs/apk/debug/app-debug.apk"