#!/usr/bin/env bash
# Post-process Expo Web export for dual-SPA hosting next to CRA.
# - Renames index.html → expo-index.html (CRA keeps index.html)
# - Writes a small PWA manifest
# - Injects GA4 stub hook if gtag is already on the page (optional)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DIST="${1:-$ROOT/dist-web}"

if [[ ! -f "$DIST/index.html" ]]; then
  echo "Missing $DIST/index.html — run expo export first" >&2
  exit 1
fi

cp "$DIST/index.html" "$DIST/expo-index.html"

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
  "start_url": "/mobile/",
  "display": "standalone",
  "orientation": "portrait",
  "background_color": "#1a0033",
  "theme_color": "#f97316",
  "icons": [
    {
      "src": "/favicon.ico",
      "sizes": "48x48",
      "type": "image/x-icon"
    }
  ]
}
EOF

# Link manifest from expo-index.html
python3 - <<'PY' "$DIST/expo-index.html"
import pathlib, sys
path = pathlib.Path(sys.argv[1])
html = path.read_text(encoding='utf-8')
if 'expo-manifest.webmanifest' not in html:
    html = html.replace(
        '</head>',
        '<link rel="manifest" href="/expo-manifest.webmanifest" />\n<meta name="apple-mobile-web-app-capable" content="yes" />\n<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />\n</head>',
        1,
    )
    path.write_text(html, encoding='utf-8')
print('Manifest linked')
PY

echo "Post-export complete: $DIST/expo-index.html"
