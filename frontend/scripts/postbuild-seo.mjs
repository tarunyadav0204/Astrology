/**
 * Post-build SEO: static sitemap in build/ + optional HTML prerender for crawlers.
 *
 * Env:
 *   SITEMAP_URL — fetch sitemap XML (default http://127.0.0.1:8001/sitemap.xml)
 *   PRERENDER — set to "false" to skip prerender
 *   BLOG_API_URL — optional blog list for extra prerender paths
 */
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import http from 'http';
import https from 'https';
import { spawn } from 'child_process';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const BUILD_DIR = path.resolve(__dirname, '../build');
const SITE_ORIGIN = process.env.SITE_ORIGIN || 'https://astroroshni.com';

const NAKSHATRA_SLUGS = [
  'ashwini', 'bharani', 'krittika', 'rohini', 'mrigashira', 'ardra', 'punarvasu', 'pushya',
  'ashlesha', 'magha', 'purva-phalguni', 'uttara-phalguni', 'hasta', 'chitra', 'swati',
  'vishakha', 'anuradha', 'jyeshtha', 'mula', 'purva-ashadha', 'uttara-ashadha', 'shravana',
  'dhanishta', 'shatabhisha', 'purva-bhadrapada', 'uttara-bhadrapada', 'revati',
];

const STATIC_PRERENDER_PATHS = [
  '/',
  '/panchang',
  '/muhurat-finder',
  '/monthly-panchang',
  '/festivals',
  '/festivals/monthly',
  '/nakshatras',
  // /kundli-matching is pre-rendered by frontend-next (do not puppeteer the CRA route)
  // /karma-analysis is pre-rendered by frontend-next (do not puppeteer the CRA route)
  // /chat is pre-rendered by frontend-next (do not puppeteer the CRA route)
  '/blog',
  '/about',
  '/contact',
  '/policy',
  '/calendar-2026',
  '/beginners-guide',
  '/advanced-courses',
  '/myths-vs-reality',
  '/horoscope',
  '/horoscope/daily',
  '/horoscope/weekly',
  '/horoscope/monthly',
  '/tools/ashtakavarga',
  '/astrovastu',
  '/marriage-analysis',
  '/career-guidance',
  '/health-analysis',
  '/wealth-analysis',
];

function fetchUrl(url) {
  return new Promise((resolve, reject) => {
    const lib = url.startsWith('https') ? https : http;
    lib
      .get(url, (res) => {
        if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
          fetchUrl(res.headers.location).then(resolve).catch(reject);
          return;
        }
        const chunks = [];
        res.on('data', (c) => chunks.push(c));
        res.on('end', () => {
          const body = Buffer.concat(chunks).toString('utf8');
          if (res.statusCode >= 400) {
            reject(new Error(`HTTP ${res.statusCode} for ${url}`));
            return;
          }
          resolve(body);
        });
      })
      .on('error', reject);
  });
}

function buildFallbackSitemap() {
  const today = new Date().toISOString().slice(0, 10);
  const year = new Date().getFullYear();
  const urls = [
    ...STATIC_PRERENDER_PATHS,
    ...NAKSHATRA_SLUGS.map((n) => `/nakshatra/${n}/${year}`),
  ];
  const unique = [...new Set(urls)];
  const entries = unique
    .map(
      (p) => `  <url>
    <loc>${SITE_ORIGIN}${p === '/' ? '/' : p}</loc>
    <lastmod>${today}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>${p === '/' ? '1.0' : '0.7'}</priority>
  </url>`
    )
    .join('\n');
  return `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${entries}
</urlset>`;
}

async function writeSitemap() {
  const outPath = path.join(BUILD_DIR, 'sitemap.xml');
  const sitemapUrl = process.env.SITEMAP_URL || 'http://127.0.0.1:8001/sitemap.xml';
  let xml;
  try {
    xml = await fetchUrl(sitemapUrl);
    console.log(`[seo] Wrote sitemap from ${sitemapUrl}`);
  } catch (err) {
    console.warn(`[seo] Could not fetch sitemap (${err.message}); using fallback`);
    xml = buildFallbackSitemap();
  }
  fs.writeFileSync(outPath, xml, 'utf8');
}

function waitForServer(port, maxAttempts = 40) {
  return new Promise((resolve, reject) => {
    let attempts = 0;
    const tick = () => {
      http
        .get(`http://127.0.0.1:${port}/`, (res) => {
          res.resume();
          resolve();
        })
        .on('error', () => {
          attempts += 1;
          if (attempts >= maxAttempts) {
            reject(new Error(`Static server not ready on port ${port}`));
            return;
          }
          setTimeout(tick, 250);
        });
    };
    tick();
  });
}

function startStaticServer(port) {
  return new Promise((resolve, reject) => {
    const child = spawn('npx', ['serve', '-s', 'build', '-l', String(port)], {
      cwd: path.resolve(__dirname, '..'),
      stdio: 'ignore',
      shell: true,
    });
    child.on('error', reject);
    resolve(child);
  });
}

async function fetchBlogSlugs() {
  const apiBase = process.env.BLOG_API_URL || 'http://127.0.0.1:8001';
  try {
    const json = await fetchUrl(`${apiBase}/api/blog/posts?status=published&limit=200`);
    const posts = JSON.parse(json);
    if (!Array.isArray(posts)) return [];
    return posts.map((p) => p.slug).filter(Boolean);
  } catch {
    return [];
  }
}

function outputPathForRoute(routePath) {
  if (routePath === '/') {
    return path.join(BUILD_DIR, 'index.html');
  }
  const clean = routePath.replace(/^\//, '').replace(/\/$/, '');
  return path.join(BUILD_DIR, clean, 'index.html');
}

async function prerenderRoutes() {
  // Deploy sets CI=true and PRERENDER=false; skip unless explicitly PRERENDER=true.
  if (process.env.PRERENDER === 'false') {
    console.log('[seo] Prerender skipped (PRERENDER=false)');
    return;
  }
  if (process.env.CI === 'true' && process.env.PRERENDER !== 'true') {
    console.log('[seo] Prerender skipped (CI=true; set PRERENDER=true to enable on deploy)');
    return;
  }

  let puppeteer;
  try {
    puppeteer = await import('puppeteer');
  } catch {
    console.warn('[seo] puppeteer not installed — run npm install && rebuild for prerendered HTML');
    return;
  }

  const port = Number(process.env.PRERENDER_PORT || 4567);
  const blogSlugs = await fetchBlogSlugs();
  const year = new Date().getFullYear();
  const paths = [
    ...STATIC_PRERENDER_PATHS,
    ...NAKSHATRA_SLUGS.map((n) => `/nakshatra/${n}/${year}`),
    ...blogSlugs.map((s) => `/blog/${s}`),
  ];
  const uniquePaths = [...new Set(paths)];

  const server = await startStaticServer(port);
  try {
    await waitForServer(port);
    const browser = await puppeteer.default.launch({
      headless: true,
      args: ['--no-sandbox', '--disable-setuid-sandbox'],
    });
    const page = await browser.newPage();
    await page.setViewport({ width: 1280, height: 800 });

    for (const routePath of uniquePaths) {
      const url = `http://127.0.0.1:${port}${routePath}`;
      process.stdout.write(`[seo] Prerender ${routePath} ... `);
      try {
        await page.goto(url, { waitUntil: 'networkidle2', timeout: 60000 });
        await page.waitForSelector('#root', { timeout: 15000 });
        await new Promise((r) => setTimeout(r, 500));
        const html = await page.content();
        const out = outputPathForRoute(routePath);
        fs.mkdirSync(path.dirname(out), { recursive: true });
        fs.writeFileSync(out, html, 'utf8');
        console.log('ok');
      } catch (err) {
        console.log(`failed (${err.message})`);
      }
    }

    await browser.close();
    console.log(`[seo] Prerendered ${uniquePaths.length} routes`);
  } finally {
    server.kill('SIGTERM');
  }
}

async function main() {
  if (!fs.existsSync(BUILD_DIR)) {
    console.error('[seo] build/ not found — run react-scripts build first');
    process.exit(1);
  }

  await writeSitemap();
  await prerenderRoutes();
  console.log('[seo] Post-build SEO complete');
}

main().catch((err) => {
  console.error('[seo] Fatal:', err);
  process.exit(1);
});
