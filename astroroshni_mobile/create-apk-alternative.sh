#!/bin/bash

echo "🚀 Creating AstroRoshni APK using alternative method..."

# Set environment
export PATH="/usr/local/bin:$PATH"

# Method 1: Try Expo export + manual APK creation
echo "📦 Exporting Expo bundle..."
npx expo export --platform android

# Method 2: Use React Native CLI directly
echo "🔧 Trying React Native CLI approach..."
npx react-native bundle --platform android --dev false --entry-file index.js --bundle-output android/app/src/main/assets/index.android.bundle --assets-dest android/app/src/main/res

# Create assets directory if it doesn't exist
mkdir -p android/app/src/main/assets

# Method 3: Build with bypassing problematic modules
echo "🛠️ Building APK with module bypass..."
cd android
export JAVA_HOME="/opt/homebrew/Cellar/openjdk@17/17.0.17/libexec/openjdk.jdk/Contents/Home"

# Try building with specific flags
./gradlew assembleRelease -x :expo-module-gradle-plugin:compileKotlin --continue

echo "✅ Check android/app/build/outputs/apk/release/ for APK file"