#!/bin/bash

echo "🚀 Building AstroRoshni APK..."

# Navigate to android directory
cd android

# Clean previous builds
echo "🧹 Cleaning previous builds..."
./gradlew clean

# Build release APK
echo "📱 Building release APK..."
./gradlew assembleRelease

# Check result
if [ -f "app/build/outputs/apk/release/app-release.apk" ]; then
    echo ""
    echo "✅ APK built successfully!"
    echo "📍 Location: android/app/build/outputs/apk/release/app-release.apk"
    echo ""
    ls -lh app/build/outputs/apk/release/app-release.apk
else
    echo "❌ Build failed"
    exit 1
fi
