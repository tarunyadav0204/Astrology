import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';

/**
 * After a dev-server restart or new build, an open tab can still run an old main bundle
 * that references chunk files that no longer exist. The browser then fetches a missing
 * .js URL, gets HTML (SPA fallback), and throws "Unexpected token '<'" + ChunkLoadError.
 * One soft reload usually fixes it (sessionStorage prevents reload loops).
 */
function installStaleChunkReloadRecovery() {
  if (typeof window === 'undefined') return;
  const KEY = '__astro_chunk_reload_ts';
  const COOLDOWN_MS = 8000;
  const chunkFail = (msg) =>
    /ChunkLoadError|Loading chunk \d+ failed|Importing a module script failed/i.test(String(msg || ''));

  const tryReload = () => {
    try {
      const prev = Number(sessionStorage.getItem(KEY) || '0');
      const now = Date.now();
      if (now - prev < COOLDOWN_MS) return;
      sessionStorage.setItem(KEY, String(now));
    } catch {
      return;
    }
    window.location.reload();
  };

  window.addEventListener('unhandledrejection', (event) => {
    const r = event.reason;
    const msg = (r && r.message) || r || '';
    if (chunkFail(msg)) {
      event.preventDefault();
      tryReload();
    }
  });
  window.addEventListener('error', (event) => {
    if (chunkFail(event.message)) tryReload();
  });
}

installStaleChunkReloadRecovery();

function hasAuthToken() {
  try {
    return typeof localStorage !== 'undefined' && !!localStorage.getItem('token');
  } catch {
    return false;
  }
}

const rootElement = document.getElementById('root');
const prerendered = rootElement?.hasChildNodes();
const tokenPresent = hasAuthToken();

if (prerendered && !tokenPresent) {
  // Crawlers / logged-out: static HTML matches first paint when App starts with loading=false (see App.js).
  ReactDOM.hydrateRoot(rootElement, <App />, {
    onRecoverableError: () => {},
  });
} else if (prerendered && tokenPresent) {
  // Logged-in HTML cannot match prerender (always logged-out homepage). Hydrating would mis-bind handlers / user.
  rootElement.textContent = '';
  ReactDOM.createRoot(rootElement).render(<App />);
} else {
  ReactDOM.createRoot(rootElement).render(<App />);
}