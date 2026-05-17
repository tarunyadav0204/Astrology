/**
 * Merge Next static export into CRA build/ for SEO (crawlers + direct URL when serve.json applies).
 */
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const OUT = path.resolve(__dirname, '../out');
const CRA_BUILD = path.resolve(__dirname, '../../frontend/build');

function copyRecursive(src, dest) {
  if (!fs.existsSync(src)) {
    console.error(`[next-karma] Missing ${src}`);
    process.exit(1);
  }
  const stat = fs.statSync(src);
  if (stat.isDirectory()) {
    fs.mkdirSync(dest, { recursive: true });
    for (const name of fs.readdirSync(src)) {
      copyRecursive(path.join(src, name), path.join(dest, name));
    }
  } else {
    fs.mkdirSync(path.dirname(dest), { recursive: true });
    fs.copyFileSync(src, dest);
  }
}

function readKarmaHtml() {
  const flat = path.join(OUT, 'karma-analysis.html');
  const nested = path.join(OUT, 'karma-analysis', 'index.html');
  if (fs.existsSync(flat)) return fs.readFileSync(flat, 'utf8');
  if (fs.existsSync(nested)) return fs.readFileSync(nested, 'utf8');
  return null;
}

if (!fs.existsSync(CRA_BUILD)) {
  console.error('[next-karma] Run CRA build first: frontend/build not found');
  process.exit(1);
}

if (fs.existsSync(path.join(OUT, '_next'))) {
  copyRecursive(path.join(OUT, '_next'), path.join(CRA_BUILD, '_next'));
  console.log('[next-karma] Copied _next assets to frontend/build/_next');
}

const html = readKarmaHtml();
if (!html) {
  console.error('[next-karma] No karma HTML in out/ — run npm run build in frontend-next');
  process.exit(1);
}

fs.writeFileSync(path.join(CRA_BUILD, 'karma-analysis.html'), html, 'utf8');
const karmaDir = path.join(CRA_BUILD, 'karma-analysis');
fs.mkdirSync(karmaDir, { recursive: true });
fs.writeFileSync(path.join(karmaDir, 'index.html'), html, 'utf8');
console.log('[next-karma] Wrote karma-analysis.html and karma-analysis/index.html');

// Compatibility only for simple static hosting. Query-aware routing such as
// /karma-analysis?app=1 requires frontend/scripts/serve-build.mjs.
const serveJson = {
  rewrites: [
    { source: '/karma-analysis', destination: '/karma-analysis.html' },
    { source: '/karma-analysis/', destination: '/karma-analysis.html' },
    { source: '**', destination: '/index.html' },
  ],
};
fs.writeFileSync(path.join(CRA_BUILD, 'serve.json'), `${JSON.stringify(serveJson, null, 2)}\n`, 'utf8');
console.log('[next-karma] Wrote build/serve.json for basic static fallback');
console.log('[next-karma] Use `cd frontend && npm run serve:build` for /karma-analysis?app=1 support');

console.log('[next-karma] Merge complete');
