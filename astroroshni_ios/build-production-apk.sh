#!/bin/bash

echo "🚀 Building Production APK for AstroRoshni..."

# Set environment variables
export PATH="/usr/local/bin:$PATH"
export JAVA_HOME="/opt/homebrew/Cellar/openjdk@17/17.0.17/libexec/openjdk.jdk/Contents/Home"

# Clean previous builds
echo "🧹 Cleaning previous builds..."
cd android
./gradlew clean

# Build production APK
echo "📱 Building production APK..."
./gradlew assembleRelease

# Check if APK was created
if [ -f "app/build/outputs/apk/release/app-release.apk" ]; then
    echo "✅ Production APK created successfully!"
    echo "📍 Location: android/app/build/outputs/apk/release/app-release.apk"
    ls -la app/build/outputs/apk/release/
else
    echo "❌ APK build failed"
fi