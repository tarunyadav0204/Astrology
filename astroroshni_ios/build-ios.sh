#!/bin/bash

echo "🚀 Building iOS Archive for AstroRoshni..."

# Set paths
PROJECT_DIR="/Users/tarunydv/Desktop/Code/AstrologyApp/astroroshni_mobile"
IOS_DIR="$PROJECT_DIR/ios"
ARCHIVE_PATH="$IOS_DIR/AstroRoshni.xcarchive"
IPA_PATH="$IOS_DIR/AstroRoshni.ipa"

cd "$IOS_DIR"

# Step 1: Build Archive (you need to configure signing in Xcode first)
echo "📦 Creating archive..."
xcodebuild -workspace AstroRoshni.xcworkspace \
           -scheme AstroRoshni \
           -configuration Release \
           -destination generic/platform=iOS \
           -archivePath "$ARCHIVE_PATH" \
           archive

if [ $? -eq 0 ]; then
    echo "✅ Archive created successfully!"
    
    # Step 2: Export IPA
    echo "📱 Exporting IPA..."
    xcodebuild -exportArchive \
               -archivePath "$ARCHIVE_PATH" \
               -exportPath "$IOS_DIR" \
               -exportOptionsPlist ExportOptions.plist
    
    if [ $? -eq 0 ]; then
        echo "✅ IPA exported successfully!"
        echo "📍 Location: $IPA_PATH"
        ls -la "$IOS_DIR"/*.ipa 2>/dev/null || echo "IPA files:"
        find "$IOS_DIR" -name "*.ipa" -exec ls -la {} \;
    else
        echo "❌ IPA export failed"
    fi
else
    echo "❌ Archive creation failed"
    echo "👉 Please configure signing in Xcode first:"
    echo "   1. Open AstroRoshni.xcworkspace in Xcode"
    echo "   2. Select AstroRoshni target"
    echo "   3. Go to Signing & Capabilities"
    echo "   4. Set your Team and Bundle Identifier"
fi