/**
 * Production static server for frontend/build.
 * - /karma-analysis (+ trailing slash) → karma-analysis.html (Next SEO export)
 * - Everything else → static file, or index.html for SPA routes
 */
import http from 'http';
import https from 'https';
import fs from 'fs';
import path from 'path';
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

function send(res, status, body, contentType) {
  res.writeHead(status, { 'Content-Type': contentType });
  res.end(body);
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
      send(res, 502, JSON.stringify({ detail: 'API unavailable' }), 'application/json');
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

    // SEO HTML by default; ?app=1 → CRA (full nav, login modal, tool)
    if (pathname === '/karma-analysis' || pathname === '/karma-analysis/') {
      const useCraApp = url.searchParams.get('app') === '1';
      if (useCraApp) {
        const indexPath = path.join(BUILD, 'index.html');
        if (await exists(indexPath)) {
          const html = await readFile(indexPath);
          return send(res, 200, html, MIME['.html']);
        }
      }
      if (!useCraApp) {
        const karmaFile = path.join(BUILD, 'karma-analysis.html');
        if (await exists(karmaFile)) {
          const html = await readFile(karmaFile);
          return send(res, 200, html, MIME['.html']);
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
        return send(res, 200, body, MIME[ext] || 'application/octet-stream');
      }
    }

    // SPA fallback (CRA)
    const indexPath = path.join(BUILD, 'index.html');
    if (await exists(indexPath)) {
      const html = await readFile(indexPath);
      return send(res, 200, html, MIME['.html']);
    }

    send(res, 404, 'Not found', 'text/plain');
  } catch (err) {
    console.error(err);
    send(res, 500, 'Server error', 'text/plain');
  }
});

server.listen(PORT, () => {
  console.log(`Serving ${BUILD} at http://localhost:${PORT}`);
  console.log('Karma SEO:  http://localhost:' + PORT + '/karma-analysis');
  console.log('Karma app:  http://localhost:' + PORT + '/karma-analysis?app=1');
});
