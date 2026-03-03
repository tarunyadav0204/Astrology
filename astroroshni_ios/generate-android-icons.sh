#!/bin/bash

# Generate Android icons from source icon
# Run: chmod +x generate-android-icons.sh && ./generate-android-icons.sh

SOURCE_ICON="assets/icon.png"
ANDROID_RES="android/app/src/main/res"
BACKGROUND_COLOR="#f97316"

echo "🎨 Generating Android icons from: $SOURCE_ICON"

if [ ! -f "$SOURCE_ICON" ]; then
    echo "❌ Source icon not found: $SOURCE_ICON"
    exit 1
fi

# Check if ImageMagick is installed
if ! command -v convert &> /dev/null; then
    echo "❌ ImageMagick not found. Installing via Homebrew..."
    brew install imagemagick
fi

# Function to generate icon
generate_icon() {
    local folder=$1
    local size=$2
    local foreground_size=$3
    
    local folder_path="$ANDROID_RES/$folder"
    mkdir -p "$folder_path"
    
    echo ""
    echo "📁 Generating $folder icons..."
    
    # Generate ic_launcher.png (legacy with background)
    convert "$SOURCE_ICON" -resize ${size}x${size} -background "$BACKGROUND_COLOR" -gravity center -extent ${size}x${size} "$folder_path/ic_launcher.png"
    echo "  ✅ ic_launcher.png (${size}x${size})"
    
    # Generate ic_launcher_round.png (legacy round with background)
    convert "$SOURCE_ICON" -resize ${size}x${size} -background "$BACKGROUND_COLOR" -gravity center -extent ${size}x${size} "$folder_path/ic_launcher_round.png"
    echo "  ✅ ic_launcher_round.png (${size}x${size})"
    
    # Generate ic_launcher_foreground.png (adaptive icon foreground - transparent background)
    convert "$SOURCE_ICON" -resize ${foreground_size}x${foreground_size} -background none -gravity center -extent ${foreground_size}x${foreground_size} "$folder_path/ic_launcher_foreground.png"
    echo "  ✅ ic_launcher_foreground.png (${foreground_size}x${foreground_size})"
    
    # Delete old .webp files
    rm -f "$folder_path/ic_launcher.webp" "$folder_path/ic_launcher_round.webp" "$folder_path/ic_launcher_foreground.webp"
    echo "  🗑️  Deleted old .webp files"
}

# Generate icons for all densities
generate_icon "mipmap-mdpi" 48 108
generate_icon "mipmap-hdpi" 72 162
generate_icon "mipmap-xhdpi" 96 216
generate_icon "mipmap-xxhdpi" 144 324
generate_icon "mipmap-xxxhdpi" 192 432

echo ""
echo "✨ All Android icons generated successfully!"
echo ""
echo "📝 Next steps:"
echo "   1. cd android"
echo "   2. ./gradlew clean"
echo "   3. cd .."
echo "   4. npx react-native run-android"
echo ""
