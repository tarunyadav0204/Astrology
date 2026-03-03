#!/bin/bash

# AstroRoshni APK Build Script
echo "🚀 Building AstroRoshni Android APK..."

# Set environment variables
export PATH="/usr/local/bin:$PATH"
export JAVA_HOME="/opt/homebrew/Cellar/openjdk@17/17.0.17/libexec/openjdk.jdk/Contents/Home"

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf android/app/build/outputs/apk/

# Build APK using EAS Build (recommended)
echo "📱 Building APK with EAS Build..."
eas build --platform android --profile production --local

echo "✅ Build complete! Check the output above for APK location."