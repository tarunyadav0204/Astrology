const path = require('path');
const fs = require('fs');
const SRC = path.join(__dirname, '..', 'assets', 'icon.png');
const OUT = path.join(__dirname, '..', 'ios', 'AstroRoshni', 'Images.xcassets', 'AppIcon.appiconset', 'App-Icon-1024x1024@1x.png');

async function main() {
  const sharp = require('sharp');
  if (!fs.existsSync(SRC)) throw new Error('Missing: ' + SRC);
  if (!fs.existsSync(path.dirname(OUT))) throw new Error('Missing ios folder. Run: npx expo prebuild');
  const size = 1024;
  const bg = await sharp({ create: { width: size, height: size, channels: 3, background: '#f97316' } }).png().toBuffer();
  const icon = await sharp(SRC).resize(size, size).toBuffer();
  await sharp(bg).composite([{ input: icon, top: 0, left: 0 }]).png().toFile(OUT);
  console.log('Done. Rebuild iOS app.');
}
main().catch(e => { console.error(e); process.exit(1); });
