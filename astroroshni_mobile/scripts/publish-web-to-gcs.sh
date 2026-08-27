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

# Upload immutable bundles before making the new shell discoverable. Publishing
# index.html first creates a window where it references a bundle that is not in
# GCS yet; clients refreshing in that window are sent to the maintenance page.
if [[ -d "$DIST/_expo" ]]; then
  gsutil -m rsync -r "$DIST/_expo" "${TARGET}/_expo"
  gsutil -m setmeta -h "Cache-Control:public, max-age=31536000, immutable" "${TARGET}/_expo/**" || true
fi

# Other root assets from the export (favicon, fonts, manifest). Do not use
# rsync -d: old hashed bundles must remain available to already-open clients.
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

# PWA supporting files under /mobile/ (phones on / keep CRA).
if [[ -f "$DIST/mobile/manifest.webmanifest" ]]; then
  gsutil -h "Cache-Control:no-cache" -h "Content-Type:application/manifest+json" \
    cp "$DIST/mobile/manifest.webmanifest" "${TARGET}/mobile/manifest.webmanifest"
fi
# PWA icons must resolve under /mobile/ (manifest prefers these paths)
for icon in pwa-icon-192.png pwa-icon-512.png apple-touch-icon.png; do
  if [[ -f "$DIST/mobile/$icon" ]]; then
    gsutil -h "Cache-Control:public, max-age=86400" -h "Content-Type:image/png" \
      cp "$DIST/mobile/$icon" "${TARGET}/mobile/$icon"
  elif [[ -f "$DIST/$icon" ]]; then
    gsutil -h "Cache-Control:public, max-age=86400" -h "Content-Type:image/png" \
      cp "$DIST/$icon" "${TARGET}/mobile/$icon"
  fi
done

# Keep root copy for debugging / health checks
gsutil -h "Cache-Control:no-cache" -h "Content-Type:text/html; charset=utf-8" \
  cp "$DIST/expo-index.html" "${TARGET}/expo-index.html"

# Commit the release only after every dependency is available. The service
# worker and version marker come after the HTML; either can prompt old clients
# to update, so they must never advertise a half-published release.
gsutil -h "Cache-Control:no-cache" -h "Content-Type:text/html; charset=utf-8" \
  cp "$DIST/expo-index.html" "${TARGET}/mobile/index.html"
if [[ -f "$DIST/mobile/sw.js" ]]; then
  gsutil -h "Cache-Control:no-cache" \
    -h "Content-Type:application/javascript; charset=utf-8" \
    -h "Service-Worker-Allowed:/mobile/" \
    cp "$DIST/mobile/sw.js" "${TARGET}/mobile/sw.js"
fi
if [[ -f "$DIST/mobile/version.json" ]]; then
  gsutil -h "Cache-Control:no-cache, no-store, must-revalidate" \
    -h "Content-Type:application/json; charset=utf-8" \
    cp "$DIST/mobile/version.json" "${TARGET}/mobile/version.json"
fi

echo "Done publishing Expo Web to ${TARGET}"
echo "  Entry: ${TARGET}/mobile/index.html  →  https://astroroshni.com/mobile/"
