#!/bin/bash

echo "🚀 Building AstroRoshni Android APK..."

# Set environment variables
export PATH="/usr/local/bin:$PATH"
export JAVA_HOME="/opt/homebrew/Cellar/openjdk@17/17.0.17/libexec/openjdk.jdk/Contents/Home"

# Navigate to android directory
cd android

# Build APK
./gradlew assembleRelease --no-daemon

# Check if APK was created
if [ -f "app/build/outputs/apk/release/app-release.apk" ]; then
    echo "✅ APK created successfully!"
    echo "📍 Location: android/app/build/outputs/apk/release/app-release.apk"
    echo "📊 Size: $(ls -lh app/build/outputs/apk/release/app-release.apk | awk '{print $5}')"
else
    echo "❌ APK build failed"
fi