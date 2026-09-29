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
  # gcloud storage avoids gsutil's macOS multiprocessing deadlock and works in CI.
  gcloud storage rsync "$DIST/_expo" "${TARGET}/_expo" --recursive \
    --cache-control="public, max-age=31536000, immutable"
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
    gcloud storage cp "$f" "${TARGET}/${base}" --cache-control="public, max-age=3600"
  elif [[ -d "$f" ]]; then
    gcloud storage rsync "$f" "${TARGET}/${base}" --recursive \
      --cache-control="public, max-age=3600"
  fi
done

# PWA supporting files under /mobile/ (phones on / keep CRA).
if [[ -f "$DIST/mobile/manifest.webmanifest" ]]; then
  gcloud storage cp "$DIST/mobile/manifest.webmanifest" "${TARGET}/mobile/manifest.webmanifest" \
    --cache-control="no-cache" --content-type="application/manifest+json"
fi
# PWA icons must resolve under /mobile/ (manifest prefers these paths)
for icon in pwa-icon-192.png pwa-icon-512.png apple-touch-icon.png; do
  if [[ -f "$DIST/mobile/$icon" ]]; then
    gcloud storage cp "$DIST/mobile/$icon" "${TARGET}/mobile/$icon" \
      --cache-control="public, max-age=86400" --content-type="image/png"
  elif [[ -f "$DIST/$icon" ]]; then
    gcloud storage cp "$DIST/$icon" "${TARGET}/mobile/$icon" \
      --cache-control="public, max-age=86400" --content-type="image/png"
  fi
done

# Keep root copy for debugging / health checks
gcloud storage cp "$DIST/expo-index.html" "${TARGET}/expo-index.html" \
  --cache-control="no-store, max-age=0, must-revalidate" --content-type="text/html; charset=utf-8"

# Commit the release only after every dependency is available. The service
# worker and version marker come after the HTML; either can prompt old clients
# to update, so they must never advertise a half-published release.
gcloud storage cp "$DIST/expo-index.html" "${TARGET}/mobile/index.html" \
  --cache-control="no-store, max-age=0, must-revalidate" --content-type="text/html; charset=utf-8"
if [[ -f "$DIST/mobile/sw.js" ]]; then
  gcloud storage cp "$DIST/mobile/sw.js" "${TARGET}/mobile/sw.js" \
    --cache-control="no-store, max-age=0, must-revalidate" \
    --content-type="application/javascript; charset=utf-8" \
    --custom-metadata="Service-Worker-Allowed=/mobile/"
fi
if [[ -f "$DIST/mobile/version.json" ]]; then
  gcloud storage cp "$DIST/mobile/version.json" "${TARGET}/mobile/version.json" \
    --cache-control="no-cache, no-store, must-revalidate" \
    --content-type="application/json; charset=utf-8"
fi

echo "Done publishing Expo Web to ${TARGET}"
echo "  Entry: ${TARGET}/mobile/index.html  →  https://astroroshni.com/mobile/"
