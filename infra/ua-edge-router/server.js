/**
 * Path-based shell router for astroroshni.com
 *
 * - `/` and normal site paths → CRA (`index.html`) for everyone (desktop + phones)
 * - `/mobile` and `/mobile/*` → Expo Web (`/mobile/index.html`)
 * - `/api/*` is not served here (LB should send API to backend)
 *
 * Escape hatches:
 *   ?force_web=1  → CRA (even under /mobile)
 *   ?force_app=1  → redirect to /mobile/ (Expo entry)
 *
 * Env:
 *   SITE_BUCKET_BASE_URL  e.g. https://storage.googleapis.com/tradebest-465307-frontend-site
 *   PORT                  default 8080
 */
const http = require('http');
const https = require('https');
const { URL } = require('url');

const PORT = Number(process.env.PORT || 8080);
const SITE_BASE = String(
  process.env.SITE_BUCKET_BASE_URL || 'https://storage.googleapis.com/tradebest-465307-frontend-site'
).replace(/\/+$/, '');

function parseCookies(header) {
  const out = {};
  String(header || '')
    .split(';')
    .forEach((part) => {
      const idx = part.indexOf('=');
      if (idx === -1) return;
      const k = part.slice(0, idx).trim();
      const v = part.slice(idx + 1).trim();
      if (k) out[k] = decodeURIComponent(v);
    });
  return out;
}

function wantsHtml(req, pathname) {
  const accept = String(req.headers.accept || '');
  if (pathname.includes('.')) {
    if (/\.(js|css|map|png|jpe?g|gif|webp|svg|ico|woff2?|ttf|json|txt|xml|webmanifest)$/i.test(pathname)) {
      return false;
    }
  }
  if (accept.includes('text/html')) return true;
  if (!accept || accept === '*/*') return true;
  return false;
}

function isExpoMobilePath(pathname) {
  return pathname === '/mobile' || pathname.startsWith('/mobile/');
}

function fetchUpstream(pathname, redirectsLeft = 3) {
  const target = `${SITE_BASE}${pathname.startsWith('/') ? pathname : `/${pathname}`}`;
  return new Promise((resolve, reject) => {
    const lib = target.startsWith('https') ? https : http;
    const req = lib.get(target, { timeout: 15000 }, (res) => {
      const status = res.statusCode || 502;
      if (
        redirectsLeft > 0 &&
        [301, 302, 307, 308].includes(status) &&
        res.headers.location
      ) {
        res.resume();
        try {
          const next = new URL(res.headers.location, target);
          const nextPath = `${next.pathname}${next.search || ''}`;
          resolve(fetchUpstream(nextPath, redirectsLeft - 1));
        } catch (err) {
          reject(err);
        }
        return;
      }
      const chunks = [];
      res.on('data', (c) => chunks.push(c));
      res.on('end', () => {
        resolve({
          statusCode: status,
          headers: res.headers,
          body: Buffer.concat(chunks),
        });
      });
    });
    req.on('error', reject);
    req.on('timeout', () => {
      req.destroy();
      reject(new Error('upstream timeout'));
    });
  });
}

function pickContentType(pathname, upstreamType, isHtmlShell) {
  if (isHtmlShell) return 'text/html; charset=utf-8';
  if (upstreamType) return upstreamType;
  if (pathname.endsWith('.js')) return 'application/javascript; charset=utf-8';
  if (pathname.endsWith('.css')) return 'text/css; charset=utf-8';
  if (pathname.endsWith('.json')) return 'application/json; charset=utf-8';
  if (pathname.endsWith('.webmanifest')) return 'application/manifest+json';
  return 'application/octet-stream';
}

const server = http.createServer(async (req, res) => {
  try {
    if (req.method === 'GET' && req.url === '/healthz') {
      res.writeHead(200, { 'content-type': 'text/plain' });
      res.end('ok');
      return;
    }

    const url = new URL(req.url || '/', `http://${req.headers.host || 'localhost'}`);
    let pathname = url.pathname || '/';
    if (pathname.length > 1 && pathname.endsWith('/')) {
      pathname = pathname.slice(0, -1);
    }

    if (pathname === '/api' || pathname.startsWith('/api/')) {
      res.writeHead(404, { 'content-type': 'text/plain' });
      res.end('Not found');
      return;
    }

    const cookies = parseCookies(req.headers.cookie);
    const forceWeb =
      url.searchParams.get('force_web') === '1' || cookies.force_web === '1';
    const forceApp =
      url.searchParams.get('force_app') === '1' || cookies.force_app === '1';

    // Canonicalize /mobile → /mobile/ so the document URL stays inside PWA scope `/mobile/`.
    // (Scope prefix matching does NOT treat `/mobile` as inside `/mobile/`.)
    if (pathname === '/mobile') {
      const qs = url.search ? url.search : '';
      res.writeHead(301, {
        location: `/mobile/${qs}`,
        'cache-control': 'no-cache',
      });
      res.end();
      return;
    }

    // Bookmark / old escape hatch → canonical Expo entry
    if (forceApp && !isExpoMobilePath(pathname) && !forceWeb) {
      res.writeHead(302, {
        location: '/mobile/',
        'set-cookie': [
          'force_app=; Path=/; Max-Age=0; SameSite=Lax',
          'force_web=; Path=/; Max-Age=0; SameSite=Lax',
        ],
        'cache-control': 'no-cache',
      });
      res.end();
      return;
    }

    const html = wantsHtml(req, pathname);
    let upstreamPath = pathname;
    let isHtmlShell = false;
    let shell = 'cra';
    const setCookies = [];

    if (html) {
      isHtmlShell = true;
      const wantExpo = isExpoMobilePath(pathname) && !forceWeb;
      shell = wantExpo ? 'expo' : 'cra';
      upstreamPath = wantExpo ? '/mobile/index.html' : '/index.html';

      if (url.searchParams.get('force_web') === '1') {
        setCookies.push('force_web=1; Path=/; Max-Age=86400; SameSite=Lax');
        setCookies.push('force_app=; Path=/; Max-Age=0; SameSite=Lax');
      }
    }

    const upstream = await fetchUpstream(upstreamPath);
    // SPA fallback for Expo deep links: /mobile/credits → mobile/index.html
    if (html && upstream.statusCode === 404 && shell === 'expo') {
      const fallback = await fetchUpstream('/mobile/index.html');
      const headers = {
        'content-type': 'text/html; charset=utf-8',
        'cache-control': 'no-cache',
        'x-ar-shell': 'expo',
      };
      if (setCookies.length) headers['set-cookie'] = setCookies;
      res.writeHead(fallback.statusCode === 200 ? 200 : fallback.statusCode, headers);
      res.end(fallback.body);
      return;
    }

    // CRA SPA fallback for unknown HTML paths (not under /mobile)
    if (html && upstream.statusCode === 404 && shell === 'cra') {
      const fallback = await fetchUpstream('/index.html');
      const headers = {
        'content-type': 'text/html; charset=utf-8',
        'cache-control': 'no-cache',
        'x-ar-shell': 'cra',
      };
      if (setCookies.length) headers['set-cookie'] = setCookies;
      res.writeHead(fallback.statusCode === 200 ? 200 : fallback.statusCode, headers);
      res.end(fallback.body);
      return;
    }

    const headers = {
      'content-type': pickContentType(upstreamPath, upstream.headers['content-type'], isHtmlShell),
      'cache-control': isHtmlShell
        ? 'no-cache'
        : upstream.headers['cache-control'] || 'public, max-age=31536000, immutable',
    };
    if (isHtmlShell) {
      headers['x-ar-shell'] = shell;
    }
    if (setCookies.length) headers['set-cookie'] = setCookies;

    res.writeHead(upstream.statusCode, headers);
    res.end(upstream.body);
  } catch (err) {
    res.writeHead(502, { 'content-type': 'text/plain' });
    res.end(`Bad gateway: ${err?.message || err}`);
  }
});

server.listen(PORT, () => {
  console.log(`[ua-edge-router] listening on ${PORT}, site=${SITE_BASE}`);
});
