#!/usr/bin/env node
/**
 * Smoke-test Expo Web routes after export/dev server is up.
 * Usage: SMOKE_URL=http://127.0.0.1:8082 node scripts/smoke-expo-web-routes.mjs
 */
import { createRequire } from 'module';
import { pathToFileURL } from 'url';

const require = createRequire(import.meta.url);
let chromium;
try {
  ({ chromium } = require('playwright-core'));
} catch (_) {
  ({ chromium } = require('/tmp/node_modules/playwright-core'));
}

const BASE = process.env.SMOKE_URL || 'http://127.0.0.1:8082';
const ROUTES = [
  '/',
  '/about',
  '/contact',
  '/credits',
  '/profile',
  '/blog',
  '/karma-analysis',
  '/kundli-matching',
  '/reports',
  '/charts',
  '/muhurat-finder',
  '/nakshatras',
  '/analysis',
];

async function main() {
  const browser = await chromium.launch({
    executablePath: process.env.CHROME_PATH || '/usr/local/bin/google-chrome',
    headless: true,
    args: ['--no-sandbox', '--disable-dev-shm-usage'],
  });
  const page = await browser.newPage();
  const results = [];

  for (const route of ROUTES) {
    const pageErrors = [];
    const onError = (err) => pageErrors.push(String(err?.message || err));
    page.on('pageerror', onError);
    try {
      await page.goto(`${BASE}${route}`, { waitUntil: 'domcontentloaded', timeout: 45000 });
      // Splash has a minimum display time (~3s); wait past it for deep links.
      await page.waitForTimeout(4500);
      const info = await page.evaluate(() => ({
        text: (document.getElementById('root')?.innerText || '').slice(0, 120),
        children: document.getElementById('root')?.childElementCount || 0,
      }));
      const failed =
        pageErrors.length > 0 ||
        info.children < 1 ||
        /Something went wrong/i.test(info.text);
      results.push({
        route,
        ok: !failed,
        children: info.children,
        preview: info.text.replace(/\s+/g, ' ').trim(),
        pageErrors: pageErrors.slice(0, 3),
      });
    } catch (e) {
      results.push({ route, ok: false, error: String(e?.message || e) });
    } finally {
      page.off('pageerror', onError);
    }
  }

  await browser.close();
  const failed = results.filter((r) => !r.ok);
  console.log(
    JSON.stringify(
      { base: BASE, passed: results.length - failed.length, failed: failed.length, results },
      null,
      2
    )
  );
  process.exit(failed.length ? 1 : 0);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
