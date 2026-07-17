#!/usr/bin/env bash
# Post-process Expo Web export for dual-SPA hosting next to CRA.
# - Renames index.html → expo-index.html (CRA keeps index.html)
# - Writes PWA manifest + icons + minimal service worker (Android Chrome install)
# - Apple meta tags for Safari Add to Home Screen
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DIST="${1:-$ROOT/dist-web}"
ASSETS="$ROOT/assets"

if [[ ! -f "$DIST/index.html" ]]; then
  echo "Missing $DIST/index.html — run expo export first" >&2
  exit 1
fi

cp "$DIST/index.html" "$DIST/expo-index.html"

# PWA icons (Chrome wants real 192 + 512 PNGs; Safari uses apple-touch-icon)
# Prefer checked-in assets (CI has no macOS sips).
mkdir -p "$DIST/mobile"
cp "$ASSETS/icon-512.png" "$DIST/pwa-icon-512.png"
cp "$ASSETS/pwa-icon-192.png" "$DIST/pwa-icon-192.png"
cp "$ASSETS/apple-touch-icon.png" "$DIST/apple-touch-icon.png"
cp "$DIST/pwa-icon-512.png" "$DIST/mobile/pwa-icon-512.png"
cp "$DIST/pwa-icon-192.png" "$DIST/mobile/pwa-icon-192.png"
cp "$DIST/apple-touch-icon.png" "$DIST/mobile/apple-touch-icon.png"

# Minimal service worker — required for Chrome Android "Install app" / beforeinstallprompt.
# Scoped to /mobile/ so it does not intercept the CRA site on /.
cat > "$DIST/mobile/sw.js" <<'EOF'
/* AstroRoshni Expo Web — installability SW (network-first, no offline cache). */
self.addEventListener('install', (event) => {
  self.skipWaiting();
});
self.addEventListener('activate', (event) => {
  event.waitUntil(self.clients.claim());
});
self.addEventListener('fetch', (event) => {
  event.respondWith(fetch(event.request));
});
EOF

# Ensure viewport-fit=cover for notched phones (index.js also sets this at runtime).
python3 - <<'PY' "$DIST/expo-index.html"
import pathlib, sys, re
path = pathlib.Path(sys.argv[1])
html = path.read_text(encoding='utf-8')
html = re.sub(
    r'<meta name="viewport"[^>]*>',
    '<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no, viewport-fit=cover" />',
    html,
    count=1,
)
# Mark shell for debugging / edge verification
if 'data-ar-shell=' not in html:
    html = html.replace('<html lang="en">', '<html lang="en" data-ar-shell="expo-web">', 1)
# Soft analytics hook — production can inject real gtag via GTM on the edge if desired
if 'gtag(' not in html and 'googletagmanager' not in html:
    snippet = '''
<script>
window.dataLayer = window.dataLayer || [];
function gtag(){dataLayer.push(arguments);}
window.gtag = window.gtag || gtag;
window.__ASTROROSHNI_SENTRY_ENV__ = window.__ASTROROSHNI_SENTRY_ENV__ || 'mobile-web';
</script>
'''
    html = html.replace('</head>', snippet + '</head>', 1)
path.write_text(html, encoding='utf-8')
print(f'Wrote {path}')
PY

cat > "$DIST/expo-manifest.webmanifest" <<'EOF'
{
  "name": "AstroRoshni",
  "short_name": "AstroRoshni",
  "description": "Vedic astrology chat, charts, and timing tools",
  "id": "/mobile/",
  "start_url": "/mobile/",
  "scope": "/mobile/",
  "display": "standalone",
  "orientation": "portrait",
  "background_color": "#1a0033",
  "theme_color": "#f97316",
  "icons": [
    {
      "src": "/mobile/pwa-icon-192.png",
      "sizes": "192x192",
      "type": "image/png",
      "purpose": "any"
    },
    {
      "src": "/mobile/pwa-icon-512.png",
      "sizes": "512x512",
      "type": "image/png",
      "purpose": "any"
    },
    {
      "src": "/mobile/pwa-icon-512.png",
      "sizes": "512x512",
      "type": "image/png",
      "purpose": "maskable"
    },
    {
      "src": "/pwa-icon-192.png",
      "sizes": "192x192",
      "type": "image/png",
      "purpose": "any"
    },
    {
      "src": "/pwa-icon-512.png",
      "sizes": "512x512",
      "type": "image/png",
      "purpose": "any"
    }
  ]
}
EOF
cp "$DIST/expo-manifest.webmanifest" "$DIST/mobile/manifest.webmanifest"

# Link manifest + Apple tags + SW registration on expo-index (also copied to mobile/index.html at publish)
python3 - <<'PY' "$DIST/expo-index.html"
import pathlib, sys
path = pathlib.Path(sys.argv[1])
html = path.read_text(encoding='utf-8')
head_bits = '''
<link rel="manifest" href="/mobile/manifest.webmanifest" />
<meta name="mobile-web-app-capable" content="yes" />
<meta name="apple-mobile-web-app-capable" content="yes" />
<meta name="apple-mobile-web-app-title" content="AstroRoshni" />
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
<link rel="apple-touch-icon" href="/mobile/apple-touch-icon.png" />
'''
# Prefer /mobile/manifest; replace any older root manifest link from a prior export.
html = html.replace('<link rel="manifest" href="/expo-manifest.webmanifest" />', '')
if '/mobile/manifest.webmanifest' not in html:
    html = html.replace('</head>', head_bits + '</head>', 1)
elif 'apple-mobile-web-app-title' not in html:
    html = html.replace('</head>', head_bits + '</head>', 1)
sw_bits = '''
<script>
if ('serviceWorker' in navigator) {
  window.addEventListener('load', function () {
    navigator.serviceWorker.register('/mobile/sw.js', { scope: '/mobile/' }).catch(function (err) {
      console.warn('[PWA] SW registration failed', err);
    });
  });
}
</script>
'''
if '/mobile/sw.js' not in html:
    html = html.replace('</body>', sw_bits + '</body>', 1)
    if '/mobile/sw.js' not in html:
        html = html.replace('</head>', sw_bits + '</head>', 1)
path.write_text(html, encoding='utf-8')
print('Manifest + Apple tags + SW registration linked')
PY

# Keep a ready-to-publish mobile entry (publish script also copies expo-index → mobile/index.html)
cp "$DIST/expo-index.html" "$DIST/mobile/index.html"

echo "Post-export complete: $DIST/expo-index.html + $DIST/mobile/ (PWA)"
