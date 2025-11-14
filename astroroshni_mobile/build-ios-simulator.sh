#!/bin/bash

echo "🚀 Building iOS Simulator Build..."

cd ios

# Build for iOS Simulator
xcodebuild -workspace AstroRoshni.xcworkspace \
           -scheme AstroRoshni \
           -configuration Release \
           -destination 'platform=iOS Simulator,name=iPhone 15,OS=latest' \
           build

echo "✅ Simulator build completed!"
echo "📱 You can now run this in iOS Simulator"