#!/usr/bin/env bash
# Publish Expo Web assets into the CRA site bucket without wiping CRA files.
# Expects dist-web already built + post-processed (expo-index.html present).
#
# Public entry: https://astroroshni.com/mobile/  (CRA stays on / for all devices)
set -euo pipefail

BUCKET="${1:-${GCP_FRONTEND_SITE_BUCKET:-}}"
DIST="${2:-dist-web}"

if [[ -z "$BUCKET" ]]; then
  echo "Usage: $0 <GCS_BUCKET> [dist-web]" >&2
  exit 1
fi
if [[ ! -f "$DIST/expo-index.html" ]]; then
  echo "Missing $DIST/expo-index.html — run scripts/postexport-web.sh first" >&2
  exit 1
fi

TARGET="gs://${BUCKET}"

echo "Publishing Expo Web assets to ${TARGET} (non-destructive)"

# Canonical Expo entry + PWA bits under /mobile/ (phones on / keep CRA)
gsutil -h "Cache-Control:no-cache" -h "Content-Type:text/html; charset=utf-8" \
  cp "$DIST/expo-index.html" "${TARGET}/mobile/index.html"
if [[ -f "$DIST/mobile/sw.js" ]]; then
  gsutil -h "Cache-Control:no-cache" -h "Content-Type:application/javascript; charset=utf-8" \
    cp "$DIST/mobile/sw.js" "${TARGET}/mobile/sw.js"
fi
if [[ -f "$DIST/mobile/manifest.webmanifest" ]]; then
  gsutil -h "Cache-Control:no-cache" -h "Content-Type:application/manifest+json" \
    cp "$DIST/mobile/manifest.webmanifest" "${TARGET}/mobile/manifest.webmanifest"
fi

# Keep root copy for debugging / health checks
gsutil -h "Cache-Control:no-cache" -h "Content-Type:text/html; charset=utf-8" \
  cp "$DIST/expo-index.html" "${TARGET}/expo-index.html"

# Hashed Expo bundles (absolute /_expo/... URLs in the HTML)
if [[ -d "$DIST/_expo" ]]; then
  gsutil -m rsync -r "$DIST/_expo" "${TARGET}/_expo"
  gsutil -m setmeta -h "Cache-Control:public, max-age=31536000, immutable" "${TARGET}/_expo/**" || true
fi

# Other root assets from the export (favicon, fonts, manifest)
# Do NOT use rsync -d here — that would delete CRA files.
shopt -s nullglob
for f in "$DIST"/*; do
  base="$(basename "$f")"
  case "$base" in
    index.html|expo-index.html|_expo|metadata.json|mobile) continue ;;
  esac
  if [[ -f "$f" ]]; then
    gsutil -h "Cache-Control:public, max-age=3600" cp "$f" "${TARGET}/${base}"
  elif [[ -d "$f" ]]; then
    gsutil -m rsync -r "$f" "${TARGET}/${base}"
  fi
done

echo "Done publishing Expo Web to ${TARGET}"
echo "  Entry: ${TARGET}/mobile/index.html  →  https://astroroshni.com/mobile/"
