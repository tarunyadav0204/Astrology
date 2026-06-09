/**
 * Production static server for frontend/build.
 * - / (+ trailing slash) → CRA index.html, prerendered after build for homepage SEO
 * - /karma-analysis, /kundli-matching, /chat → Next SEO HTML by default; ?app=1 → CRA for those paths
 * - Everything else → static file, or index.html for SPA routes
 */
import http from 'http';
import https from 'https';
import fs from 'fs';
import path from 'path';
import zlib from 'zlib';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const BUILD = path.resolve(__dirname, '../build');
const PORT = Number(process.env.PORT) || 3001;
const API_TARGET = process.env.API_TARGET || 'http://127.0.0.1:8001';

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.gif': 'image/gif',
  '.svg': 'image/svg+xml',
  '.webp': 'image/webp',
  '.ico': 'image/x-icon',
  '.woff': 'font/woff',
  '.woff2': 'font/woff2',
  '.txt': 'text/plain; charset=utf-8',
  '.xml': 'application/xml',
  '.map': 'application/json',
};

/** CRA hashes filenames under /static → safe to cache “forever” at browser + CDN. */
const CACHE_IMMUTABLE = 'public, max-age=31536000, immutable';
/** Images use stable names; bump cache after asset changes or use deploy purge. */
const CACHE_IMAGES = 'public, max-age=2592000'; // 30d
/** HTML must revalidate so new JS/CSS chunk names are picked up after deploy. */
const CACHE_HTML = 'no-cache';

function shouldGzip(req, contentType, byteLength) {
  if (byteLength < 900) return false;
  const enc = String(req.headers['accept-encoding'] || '');
  if (!enc.includes('gzip')) return false;
  return /charset=utf-8|text\/|javascript|json|xml|svg\+xml|\/css/i.test(contentType);
}

function send(req, res, status, body, contentType, extraHeaders = {}) {
  const buf = Buffer.isBuffer(body) ? body : Buffer.from(String(body), 'utf8');
  if (req && shouldGzip(req, contentType, buf.length)) {
    const gz = zlib.gzipSync(buf, { level: 6 });
    res.writeHead(status, {
      'Content-Type': contentType,
      ...extraHeaders,
      'Content-Encoding': 'gzip',
      Vary: 'Accept-Encoding',
    });
    res.end(gz);
    return;
  }
  res.writeHead(status, { 'Content-Type': contentType, ...extraHeaders });
  res.end(buf);
}

function cacheControlForPath(pathname, ext) {
  if (ext === '.html') return CACHE_HTML;
  if (pathname.startsWith('/static/')) return CACHE_IMMUTABLE;
  if (pathname.startsWith('/images/')) return CACHE_IMAGES;
  if (ext === '.woff' || ext === '.woff2') return CACHE_IMMUTABLE;
  if (ext === '.ico') return CACHE_IMAGES;
  if (pathname === '/manifest.json' || pathname.endsWith('/manifest.json')) return 'public, max-age=86400';
  if (pathname.startsWith('/.well-known/')) return 'public, max-age=86400';
  if (ext === '.txt' || ext === '.xml') return 'public, max-age=3600';
  return 'public, max-age=86400';
}

function safePath(urlPath) {
  const decoded = decodeURIComponent(urlPath.split('?')[0]);
  const normalized = path.normalize(decoded).replace(/^(\.\.(\/|\\|$))+/, '');
  const full = path.join(BUILD, normalized);
  if (!full.startsWith(BUILD)) return null;
  return full;
}

function readFile(filePath) {
  return fs.promises.readFile(filePath);
}

function exists(filePath) {
  return fs.promises.access(filePath, fs.constants.R_OK).then(() => true).catch(() => false);
}

function proxyApi(req, res) {
  const target = new URL(req.url || '/', API_TARGET);
  const client = target.protocol === 'https:' ? https : http;
  const headers = { ...req.headers, host: target.host };

  const proxyReq = client.request(
    target,
    {
      method: req.method,
      headers,
    },
    (proxyRes) => {
      res.writeHead(proxyRes.statusCode || 502, proxyRes.headers);
      proxyRes.pipe(res);
    }
  );

  proxyReq.on('error', (err) => {
    console.error('[api proxy]', err.message);
    if (!res.headersSent) {
      send(req, res, 502, JSON.stringify({ detail: 'API unavailable' }), 'application/json');
    } else {
      res.end();
    }
  });

  req.pipe(proxyReq);
}

const server = http.createServer(async (req, res) => {
  try {
    const url = new URL(req.url || '/', `http://localhost:${PORT}`);
    let pathname = url.pathname;

    // Local/prod fallback API proxy. In production nginx normally handles /api first,
    // but this keeps `npm run serve:build` faithful during localhost testing.
    if (pathname === '/api' || pathname.startsWith('/api/')) {
      return proxyApi(req, res);
    }

    const sendCraApp = async (headers = {}) => {
      const indexPath = path.join(BUILD, 'index.html');
      if (await exists(indexPath)) {
        const html = await readFile(indexPath);
        return send(req, res, 200, html, MIME['.html'], {
          'Cache-Control': CACHE_HTML,
          ...headers,
        });
      }
      return false;
    };

    if (pathname === '/app' || pathname === '/app/' || (pathname === '/' && url.searchParams.get('app') === '1')) {
      return sendCraApp({ 'X-Robots-Tag': 'noindex, follow' });
    }

    // SEO HTML by default for tool landing URLs; ?app=1 → CRA (full nav, login modal, tool).
    // Root `/` is the real CRA homepage; build-time prerender makes its index.html crawlable.
    const nextSeoRoutes = {
      '/karma-analysis': 'karma-analysis.html',
      '/kundli-matching': 'kundli-matching.html',
      '/chat': 'chat.html',
    };
    const seoRouteKey = pathname === '/' ? '/' : pathname.replace(/\/$/, '');
    const seoFileName = nextSeoRoutes[seoRouteKey];
    if (seoFileName) {
      const useCraApp = url.searchParams.get('app') === '1';
      if (useCraApp) {
        return sendCraApp({ 'X-Robots-Tag': 'noindex, follow' });
      }
      if (!useCraApp) {
        const seoFile = path.join(BUILD, seoFileName);
        if (await exists(seoFile)) {
          const html = await readFile(seoFile);
          return send(req, res, 200, html, MIME['.html'], { 'Cache-Control': CACHE_HTML });
        }
      }
    }

    // Static file
    let filePath = safePath(pathname);
    if (filePath && (await exists(filePath))) {
      const stat = await fs.promises.stat(filePath);
      if (stat.isDirectory()) {
        filePath = path.join(filePath, 'index.html');
      }
      if (await exists(filePath)) {
        const ext = path.extname(filePath).toLowerCase();
        const body = await readFile(filePath);
        const rel = '/' + path.relative(BUILD, filePath).split(path.sep).join('/');
        const cc = cacheControlForPath(rel, ext);
        return send(req, res, 200, body, MIME[ext] || 'application/octet-stream', {
          'Cache-Control': cc,
        });
      }
    }

    // Hashed build assets must never fall through to the SPA HTML fallback.
    // If a browser asks for a missing chunk, returning index.html makes it parse
    // "<!doctype html>" as JavaScript and report the confusing
    // "Unexpected token '<'" error instead of a clear missing asset.
    if (pathname.startsWith('/static/')) {
      const ext = path.extname(pathname).toLowerCase();
      return send(req, res, 404, 'Not found', MIME[ext] || 'text/plain; charset=utf-8', {
        'Cache-Control': 'no-store',
      });
    }

    // SPA fallback (CRA)
    return sendCraApp();

    send(req, res, 404, 'Not found', 'text/plain');
  } catch (err) {
    console.error(err);
    send(req, res, 500, 'Server error', 'text/plain');
  }
});

server.listen(PORT, () => {
  console.log(`Serving ${BUILD} at http://localhost:${PORT}`);
  console.log('Home:       http://localhost:' + PORT + '/  (CRA, prerendered)');
  console.log('Karma SEO:  http://localhost:' + PORT + '/karma-analysis');
  console.log('Karma app:  http://localhost:' + PORT + '/karma-analysis?app=1');
  console.log('Kundli SEO: http://localhost:' + PORT + '/kundli-matching');
  console.log('Kundli app: http://localhost:' + PORT + '/kundli-matching?app=1');
  console.log('Chat SEO:   http://localhost:' + PORT + '/chat');
  console.log('Chat app:   http://localhost:' + PORT + '/chat?app=1');
});
