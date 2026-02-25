/**
 * Ensures android-notification-icon.png exists for expo-notifications.
 * Converts from android-notification-icon.jpeg and adds transparency so Android
 * shows the icon correctly (white shape on transparent background).
 */
const path = require('path');
const fs = require('fs');

const ASSETS = path.join(__dirname, '..', 'assets');
const JPEG_PATH = path.join(ASSETS, 'android-notification-icon.jpeg');
const PNG_PATH = path.join(ASSETS, 'android-notification-icon.png');

async function main() {
  const sharp = require('sharp');
  if (!fs.existsSync(JPEG_PATH)) {
    console.warn('Missing:', JPEG_PATH, '- notification icon will not be custom.');
    return;
  }
  const { data, info } = await sharp(JPEG_PATH)
    .raw()
    .toBuffer({ resolveWithObject: true });
  const { width, height, channels } = info;
  const out = Buffer.alloc(width * height * 4);
  const threshold = 252; // treat near-white as background
  for (let i = 0, j = 0; i < data.length; i += channels, j += 4) {
    const r = data[i];
    const g = data[i + 1];
    const b = data[i + 2];
    const isBackground = r >= threshold && g >= threshold && b >= threshold;
    if (isBackground) {
      out[j] = 0;
      out[j + 1] = 0;
      out[j + 2] = 0;
      out[j + 3] = 0;
    } else {
      out[j] = 255;
      out[j + 1] = 255;
      out[j + 2] = 255;
      out[j + 3] = 255;
    }
  }
  await sharp(out, {
    raw: { width, height, channels: 4 },
  })
    .png()
    .toFile(PNG_PATH);
  console.log('Written:', PNG_PATH);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
