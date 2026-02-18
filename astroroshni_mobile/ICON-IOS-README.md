# iOS app icon showing white

On iOS, if your app icon appears **white** or invisible on the home screen, it is usually because the icon image has a **transparent background** with light-colored content. iOS does not add a background to app icons (unlike Android).

## Fix

Use an icon that has a **solid background** (e.g. orange `#f97316`) so it is visible on both light and dark home screens.

### Option A: Add a dedicated iOS icon (recommended)

1. Create a 1024×1024 PNG with your logo on a **solid orange** (`#f97316`) background (e.g. in Figma, Preview, or any editor).
2. Save it as **`assets/icon-ios.png`** in this project.
3. After the next `npx expo prebuild` or EAS build, the iOS app will need to use this file. To do that automatically, add this plugin to `app.json` (see Option B for plugin), or **manually** copy the file:
   - Copy `assets/icon-ios.png` to  
     **`ios/AstroRoshni/Images.xcassets/AppIcon.appiconset/App-Icon-1024x1024@1x.png`**
4. Rebuild the iOS app (`npx expo run:ios` or archive in Xcode).

### Option B: Replace the main icon

If you prefer a single icon for all platforms:

1. Edit **`assets/icon.png`** so it has a solid background (e.g. orange #f97316), not transparency.
2. Run **`npx expo prebuild --clean`** to regenerate the native `ios` folder and app icons.
3. Rebuild the iOS app.

After either option, the icon on your iPhone should show with a visible background instead of white.
