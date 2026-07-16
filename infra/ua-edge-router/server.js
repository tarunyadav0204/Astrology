/**
 * UA edge router for astroroshni.com
 *
 * Serves CRA (desktop + crawlers) or Expo Web (mobile browsers) HTML entry
 * from the same GCS site bucket, while proxying static assets from that bucket.
 *
 * Escape hatches:
 *   ?force_web=1 / Cookie force_web=1  → CRA
 *   ?force_app=1 / Cookie force_app=1  → Expo Web
 *
 * Env:
 *   SITE_BUCKET_BASE_URL  e.g. https://storage.googleapis.com/tradebest-465307-frontend-site
 *     or the public CDN origin that already fronts the bucket
 *   PORT                  default 8080
 *   CACHE_HTML_SECONDS    default 0
 */
const http = require('http');
const https = require('https');
const { URL } = require('url');

const PORT = Number(process.env.PORT || 8080);
const SITE_BASE = String(
  process.env.SITE_BUCKET_BASE_URL || 'https://storage.googleapis.com/tradebest-465307-frontend-site'
).replace(/\/+$/, '');

const BOT_RE =
  /googlebot|bingbot|slurp|duckduckbot|baiduspider|yandexbot|sogou|exabot|facebot|ia_archiver|semrushbot|ahrefsbot|dotbot|petalbot|applebot|twitterbot|linkedinbot|embedly|quora link preview|showyoubot|outbrain|pinterest|slackbot|vkshare|w3c_validator|whatsapp|telegrambot|discordbot|preview/i;

const MOBILE_RE =
  /Android|webOS|iPhone|iPod|BlackBerry|IEMobile|Opera Mini|Mobile|mobile|CriOS|FxiOS/i;

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
    // Explicit asset extensions are never HTML SPA fallbacks
    if (/\.(js|css|map|png|jpe?g|gif|webp|svg|ico|woff2?|ttf|json|txt|xml|webmanifest)$/i.test(pathname)) {
      return false;
    }
  }
  if (accept.includes('text/html')) return true;
  if (!accept || accept === '*/*') return true;
  return false;
}

function resolveShell(req, url) {
  const cookies = parseCookies(req.headers.cookie);
  const forceWeb =
    url.searchParams.get('force_web') === '1' || cookies.force_web === '1';
  const forceApp =
    url.searchParams.get('force_app') === '1' || cookies.force_app === '1';
  const ua = String(req.headers['user-agent'] || '');

  if (forceWeb) return 'cra';
  if (forceApp) return 'expo';
  if (BOT_RE.test(ua)) return 'cra';
  if (MOBILE_RE.test(ua)) return 'expo';
  return 'cra';
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

    // Never proxy API through this edge — LB should route /api to backend.
    if (pathname === '/api' || pathname.startsWith('/api/')) {
      res.writeHead(404, { 'content-type': 'text/plain' });
      res.end('Not found');
      return;
    }

    const html = wantsHtml(req, pathname);
    let upstreamPath = pathname;
    let isHtmlShell = false;
    const setCookies = [];

    if (html) {
      const shell = resolveShell(req, url);
      isHtmlShell = true;
      upstreamPath = shell === 'expo' ? '/expo-index.html' : '/index.html';

      if (url.searchParams.get('force_web') === '1') {
        setCookies.push('force_web=1; Path=/; Max-Age=86400; SameSite=Lax');
        setCookies.push('force_app=; Path=/; Max-Age=0; SameSite=Lax');
      }
      if (url.searchParams.get('force_app') === '1') {
        setCookies.push('force_app=1; Path=/; Max-Age=86400; SameSite=Lax');
        setCookies.push('force_web=; Path=/; Max-Age=0; SameSite=Lax');
      }
    }

    const upstream = await fetchUpstream(upstreamPath);
    // SPA fallback: missing deep-link asset → appropriate index
    if (html && upstream.statusCode === 404) {
      const shell = resolveShell(req, url);
      const fallback = await fetchUpstream(shell === 'expo' ? '/expo-index.html' : '/index.html');
      const headers = {
        'content-type': 'text/html; charset=utf-8',
        'cache-control': 'no-cache',
        'x-ar-shell': shell,
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
      headers['x-ar-shell'] = resolveShell(req, url);
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
