const fs = require('fs');
const path = require('path');
const sharp = require('sharp');

const VISeme_DIR = path.join(__dirname, '..', 'src', 'assets', 'tara');
const WHITE_THRESHOLD = 246;

const isNearWhite = (r, g, b) =>
  r >= WHITE_THRESHOLD && g >= WHITE_THRESHOLD && b >= WHITE_THRESHOLD;

async function processFile(filename) {
  const filePath = path.join(VISeme_DIR, filename);
  const { data, info } = await sharp(filePath)
    .ensureAlpha()
    .raw()
    .toBuffer({ resolveWithObject: true });

  for (let index = 0; index < data.length; index += info.channels) {
    const r = data[index];
    const g = data[index + 1];
    const b = data[index + 2];

    if (isNearWhite(r, g, b)) {
      data[index + 3] = 0;
    }
  }

  await sharp(data, {
    raw: {
      width: info.width,
      height: info.height,
      channels: info.channels,
    },
  })
    .png()
    .toFile(filePath);
}

async function main() {
  const files = fs
    .readdirSync(VISeme_DIR)
    .filter((name) => /^viseme_.*\.png$/i.test(name));

  for (const file of files) {
    // Keep this batch step simple so the generated visemes can be previewed quickly in-app.
    await processFile(file);
    process.stdout.write(`Updated ${file}\n`);
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
