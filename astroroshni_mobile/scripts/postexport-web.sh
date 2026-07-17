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
# BUILD_ID is injected after HTML is finalized (see python block below).
mkdir -p "$DIST/mobile"
cat > "$DIST/mobile/sw.js" <<'EOF'
/* AstroRoshni Expo Web — network-first installability SW (no offline asset cache). */
const BUILD_ID = '__AR_WEB_BUILD__';
self.addEventListener('install', (event) => {
  self.skipWaiting();
});
self.addEventListener('activate', (event) => {
  event.waitUntil((async () => {
    try {
      const keys = await caches.keys();
      await Promise.all(keys.map((k) => caches.delete(k)));
    } catch (_) {}
    await self.clients.claim();
  })());
});
self.addEventListener('fetch', (event) => {
  // Always hit network so deploys show up without deleting the home-screen icon (iOS/Android).
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
# Default PWA chrome = dark shell purple (runtime ThemeContext updates for light/dark).
if 'name="theme-color"' in html:
    html = re.sub(
        r'(<meta\s+name="theme-color"[^>]*content=")[^"]*(")',
        r'\1#1a0033\2',
        html,
        flags=re.I,
    )
else:
    html = html.replace('</head>', '<meta name="theme-color" content="#1a0033" />\n</head>', 1)
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
  "theme_color": "#1a0033",
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

# Link manifest + Apple tags + SW registration + auto-update (iOS home screen included)
python3 - <<'PY' "$DIST/expo-index.html" "$DIST/mobile"
import pathlib, sys, re, json, time
html_path = pathlib.Path(sys.argv[1])
mobile_dir = pathlib.Path(sys.argv[2])
html = html_path.read_text(encoding='utf-8')

# Build id from hashed Expo bundle (changes every deploy) — fallback to timestamp.
m = re.search(r'/index-([a-f0-9]+)\.js', html)
build_id = m.group(1) if m else str(int(time.time()))

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

# Stamp build id for client update checks (works on iOS A2HS without deleting the icon).
if 'window.__AR_WEB_BUILD__' not in html:
    html = html.replace(
        '</head>',
        f'<script>window.__AR_WEB_BUILD__={json.dumps(build_id)};</script>\n</head>',
        1,
    )
else:
    html = re.sub(
        r'window\.__AR_WEB_BUILD__\s*=\s*[^;<]+',
        f'window.__AR_WEB_BUILD__={json.dumps(build_id)}',
        html,
        count=1,
    )

# SW with matching BUILD_ID (byte change forces browsers to fetch a new worker).
sw_path = mobile_dir / 'sw.js'
sw = sw_path.read_text(encoding='utf-8').replace('__AR_WEB_BUILD__', build_id)
sw_path.write_text(sw, encoding='utf-8')

version = {
    'build': build_id,
    'ts': int(time.time()),
    'note': 'Fetched with cache:no-store on launch/focus so home-screen PWAs pick up deploys.',
}
(mobile_dir / 'version.json').write_text(json.dumps(version) + '\n', encoding='utf-8')

sw_bits = f'''
<script>
(function () {{
  var BUILD = {json.dumps(build_id)};
  window.__AR_WEB_BUILD__ = window.__AR_WEB_BUILD__ || BUILD;

  function reloadOnce() {{
    try {{
      if (sessionStorage.getItem('ar_web_reloading') === BUILD) return;
      sessionStorage.setItem('ar_web_reloading', BUILD);
    }} catch (_) {{}}
    window.location.reload();
  }}

  function clearReloadGuard() {{
    try {{
      if (sessionStorage.getItem('ar_web_reloading') === BUILD) {{
        sessionStorage.removeItem('ar_web_reloading');
      }}
    }} catch (_) {{}}
  }}

  async function checkDeployedBuild() {{
    try {{
      var res = await fetch('/mobile/version.json?_=' + Date.now(), {{ cache: 'no-store', credentials: 'same-origin' }});
      if (!res.ok) return;
      var data = await res.json();
      if (data && data.build && data.build !== BUILD) {{
        console.info('[PWA] New build available', data.build, 'current', BUILD);
        reloadOnce();
      }} else {{
        clearReloadGuard();
      }}
    }} catch (err) {{
      console.warn('[PWA] version check failed', err);
    }}
  }}

  if ('serviceWorker' in navigator) {{
    window.addEventListener('load', function () {{
      navigator.serviceWorker.register('/mobile/sw.js?v=' + encodeURIComponent(BUILD), {{ scope: '/mobile/' }})
        .then(function (reg) {{
          try {{ reg.update(); }} catch (_) {{}}
          setInterval(function () {{ try {{ reg.update(); }} catch (_) {{}} }}, 5 * 60 * 1000);
        }})
        .catch(function (err) {{ console.warn('[PWA] SW registration failed', err); }});
      navigator.serviceWorker.addEventListener('controllerchange', function () {{
        reloadOnce();
      }});
    }});
  }}

  // iOS home-screen apps often skip SW update races — version.json is the source of truth.
  document.addEventListener('visibilitychange', function () {{
    if (!document.hidden) checkDeployedBuild();
  }});
  window.addEventListener('pageshow', function (ev) {{
    if (ev.persisted) checkDeployedBuild();
  }});
  window.addEventListener('focus', checkDeployedBuild);
  setTimeout(checkDeployedBuild, 1500);
}})();
</script>
'''

# Replace any prior SW registration snippet so we do not double-register.
html = re.sub(
    r'<script>\s*if\s*\(\s*\'serviceWorker\'\s+in\s+navigator\s*\).*?</script>',
    '',
    html,
    flags=re.S,
)
html = re.sub(
    r'<script>\s*\(function\s*\(\s*\)\s*\{\s*var BUILD = .*?</script>',
    '',
    html,
    flags=re.S,
)
if 'checkDeployedBuild' not in html:
    if '</body>' in html:
        html = html.replace('</body>', sw_bits + '</body>', 1)
    else:
        html = html.replace('</head>', sw_bits + '</head>', 1)

html_path.write_text(html, encoding='utf-8')
print(f'Manifest + Apple tags + auto-update linked (build={build_id})')
PY

# Keep a ready-to-publish mobile entry (publish script also copies expo-index → mobile/index.html)
cp "$DIST/expo-index.html" "$DIST/mobile/index.html"

echo "Post-export complete: $DIST/expo-index.html + $DIST/mobile/ (PWA)"
