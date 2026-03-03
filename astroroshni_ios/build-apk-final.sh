#!/bin/bash

echo "🚀 Building AstroRoshni Production APK..."

# Set Java 17 globally
export JAVA_HOME="/opt/homebrew/Cellar/openjdk@17/17.0.17/libexec/openjdk.jdk/Contents/Home"
export PATH="/usr/local/bin:$JAVA_HOME/bin:$PATH"

# Build using EAS local with Java 17
eas build --platform android --profile local --local

echo "✅ APK build completed!"
echo "📍 Check the output above for APK download link"