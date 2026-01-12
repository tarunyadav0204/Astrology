#!/usr/bin/env node

/**
 * Generate Android icons from source icon
 * Run: node generate-android-icons.js
 */

const sharp = require('sharp');
const fs = require('fs');
const path = require('path');

const SOURCE_ICON = path.join(__dirname, 'assets', 'icon.png');
const ANDROID_RES = path.join(__dirname, 'android', 'app', 'src', 'main', 'res');

// Android icon sizes
const ICON_SIZES = {
  'mipmap-mdpi': { size: 48, foreground: 108 },
  'mipmap-hdpi': { size: 72, foreground: 162 },
  'mipmap-xhdpi': { size: 96, foreground: 216 },
  'mipmap-xxhdpi': { size: 144, foreground: 324 },
  'mipmap-xxxhdpi': { size: 192, foreground: 432 }
};

async function generateIcons() {
  console.log('🎨 Generating Android icons from:', SOURCE_ICON);
  
  if (!fs.existsSync(SOURCE_ICON)) {
    console.error('❌ Source icon not found:', SOURCE_ICON);
    process.exit(1);
  }

  for (const [folder, sizes] of Object.entries(ICON_SIZES)) {
    const folderPath = path.join(ANDROID_RES, folder);
    
    if (!fs.existsSync(folderPath)) {
      fs.mkdirSync(folderPath, { recursive: true });
    }

    console.log(`\n📁 Generating ${folder} icons...`);

    // Generate ic_launcher.png (legacy)
    await sharp(SOURCE_ICON)
      .resize(sizes.size, sizes.size, { fit: 'contain', background: { r: 249, g: 115, b: 22, alpha: 1 } })
      .png()
      .toFile(path.join(folderPath, 'ic_launcher.png'));
    console.log(`  ✅ ic_launcher.png (${sizes.size}x${sizes.size})`);

    // Generate ic_launcher_round.png (legacy round)
    await sharp(SOURCE_ICON)
      .resize(sizes.size, sizes.size, { fit: 'contain', background: { r: 249, g: 115, b: 22, alpha: 1 } })
      .png()
      .toFile(path.join(folderPath, 'ic_launcher_round.png'));
    console.log(`  ✅ ic_launcher_round.png (${sizes.size}x${sizes.size})`);

    // Generate ic_launcher_foreground.png (adaptive icon foreground)
    await sharp(SOURCE_ICON)
      .resize(sizes.foreground, sizes.foreground, { fit: 'contain', background: { r: 0, g: 0, b: 0, alpha: 0 } })
      .png()
      .toFile(path.join(folderPath, 'ic_launcher_foreground.png'));
    console.log(`  ✅ ic_launcher_foreground.png (${sizes.foreground}x${sizes.foreground})`);

    // Delete old .webp files if they exist
    ['ic_launcher.webp', 'ic_launcher_round.webp', 'ic_launcher_foreground.webp'].forEach(file => {
      const webpPath = path.join(folderPath, file);
      if (fs.existsSync(webpPath)) {
        fs.unlinkSync(webpPath);
        console.log(`  🗑️  Deleted old ${file}`);
      }
    });
  }

  console.log('\n✨ All Android icons generated successfully!');
  console.log('\n📝 Next steps:');
  console.log('   1. cd android');
  console.log('   2. ./gradlew clean');
  console.log('   3. cd ..');
  console.log('   4. npx react-native run-android');
}

generateIcons().catch(err => {
  console.error('❌ Error generating icons:', err);
  process.exit(1);
});
