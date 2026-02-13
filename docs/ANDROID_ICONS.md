# Android Icon Generation

## What Was Done

Generated fresh Android app icons from the source `assets/icon.png` file to replace old cached `.webp` icons.

## Files Generated

For each density (mdpi, hdpi, xhdpi, xxhdpi, xxxhdpi):
- `ic_launcher.png` - Legacy launcher icon with orange background
- `ic_launcher_round.png` - Legacy round launcher icon with orange background  
- `ic_launcher_foreground.png` - Adaptive icon foreground (transparent background)

## Icon Sizes

- **mipmap-mdpi**: 48x48 (foreground: 108x108)
- **mipmap-hdpi**: 72x72 (foreground: 162x162)
- **mipmap-xhdpi**: 96x96 (foreground: 216x216)
- **mipmap-xxhdpi**: 144x144 (foreground: 324x324)
- **mipmap-xxxhdpi**: 192x192 (foreground: 432x432)

## Background Color

The icon background uses the app's primary color: `#f97316` (orange)

## How to Regenerate Icons

If you need to regenerate icons in the future:

```bash
# Run the generation script
./generate-android-icons.sh

# Clean the Android build
cd android
./gradlew clean
cd ..

# Build the app
npx react-native run-android
# or
./build-apk.sh
```

## Next Steps

1. Build a new APK/AAB
2. Test on a device to verify the new icons appear
3. Upload to Play Store if needed

## Notes

- Old `.webp` files have been deleted
- The script uses ImageMagick (installed via Homebrew)
- Icons are generated as PNG format for better compatibility
- Adaptive icons use transparent foreground with colored background layer
