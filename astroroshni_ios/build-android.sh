#!/bin/bash

# Android Build Script for AstroRoshni Mobile App
# This script creates a production APK build

set -e  # Exit on any error

echo "🚀 Starting Android Build Process..."

# Set environment variables
export PATH="/usr/local/bin:$PATH"
export JAVA_HOME="/opt/homebrew/Cellar/openjdk@17/17.0.17/libexec/openjdk.jdk/Contents/Home"
export ANDROID_HOME="/Users/tarunydv/Library/Android/sdk"

# Get the project directory
PROJECT_DIR="/Users/tarunydv/Desktop/Code/AstrologyApp/astroroshni_mobile"
cd "$PROJECT_DIR"

echo "📁 Current directory: $(pwd)"

# Step 1: Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf android/app/src/main/assets/index.android.bundle
rm -rf android/app/build/outputs/apk/

# Step 2: Create assets directory
echo "📂 Creating assets directory..."
mkdir -p android/app/src/main/assets

# Step 3: Create JavaScript bundle
echo "📦 Creating JavaScript bundle..."
npx react-native bundle \
  --platform android \
  --dev false \
  --entry-file index.js \
  --bundle-output android/app/src/main/assets/index.android.bundle \
  --assets-dest android/app/src/main/res/

echo "✅ JavaScript bundle created successfully"

# Step 4: Build release APK
echo "🔨 Building release APK..."
cd android

# Clean gradle cache
echo "🧹 Cleaning gradle cache..."
./gradlew clean

# Build the APK
echo "📱 Assembling release APK..."
./gradlew assembleRelease

# Check if APK was created successfully
APK_PATH="app/build/outputs/apk/release/app-release.apk"
if [ -f "$APK_PATH" ]; then
    echo "✅ APK built successfully!"
    echo "📍 APK Location: $PROJECT_DIR/android/$APK_PATH"
    
    # Get APK size
    APK_SIZE=$(du -h "$APK_PATH" | cut -f1)
    echo "📏 APK Size: $APK_SIZE"
    
    # Copy APK to project root for easy access
    cp "$APK_PATH" "$PROJECT_DIR/AstroRoshni-release.apk"
    echo "📋 APK copied to: $PROJECT_DIR/AstroRoshni-release.apk"
    
else
    echo "❌ APK build failed!"
    exit 1
fi

echo "🎉 Android build completed successfully!"
echo ""
echo "📱 Install APK with: adb install AstroRoshni-release.apk"
echo "🔗 Or transfer the APK file to your Android device"