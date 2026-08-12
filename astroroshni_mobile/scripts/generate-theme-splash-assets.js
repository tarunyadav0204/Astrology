const fs = require('fs');
const path = require('path');
const sharp = require('sharp');

const root = path.resolve(__dirname, '..');
const logoPath = path.join(root, 'assets', 'logo.png');

async function renderCanvas(outputPath, width, height, logoSize) {
  const logo = await sharp(logoPath)
    .resize(logoSize, logoSize, { fit: 'contain' })
    .png()
    .toBuffer();

  await sharp({
    create: {
      width,
      height,
      channels: 4,
      background: { r: 0, g: 0, b: 0, alpha: 0 },
    },
  })
    .composite([{ input: logo, gravity: 'center' }])
    .png()
    .toFile(outputPath);
}

async function main() {
  await renderCanvas(path.join(root, 'assets', 'splash.png'), 1284, 2778, 300);

  const androidSizes = [
    ['drawable-mdpi', 288, 92],
    ['drawable-hdpi', 432, 138],
    ['drawable-xhdpi', 576, 184],
    ['drawable-xxhdpi', 864, 276],
    ['drawable-xxxhdpi', 1152, 368],
  ];
  for (const [density, canvas, logo] of androidSizes) {
    await renderCanvas(
      path.join(root, 'android', 'app', 'src', 'main', 'res', density, 'splashscreen_logo.png'),
      canvas,
      canvas,
      logo
    );
  }

  const iosDir = path.join(
    root,
    'ios',
    'AstroRoshni',
    'Images.xcassets',
    'SplashScreenLegacy.imageset'
  );
  await renderCanvas(path.join(iosDir, 'image.png'), 414, 736, 104);
  await renderCanvas(path.join(iosDir, 'image@2x.png'), 828, 1472, 208);
  await renderCanvas(path.join(iosDir, 'image@3x.png'), 1242, 2208, 312);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
