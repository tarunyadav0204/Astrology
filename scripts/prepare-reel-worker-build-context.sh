#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
OUT_DIR="${1:-}"

if [ -z "${OUT_DIR}" ]; then
  echo "usage: $0 OUT_DIR"
  exit 1
fi

rm -rf "${OUT_DIR}"
mkdir -p "${OUT_DIR}"

for path in backend reel_worker_service; do
  mkdir -p "${OUT_DIR}/${path}"
  rsync -a \
    --exclude '__pycache__' --exclude '*.pyc' --exclude '*.pyo' --exclude '.DS_Store' \
    "${APP_ROOT}/${path}/" "${OUT_DIR}/${path}/"
done

echo "Prepared Reel worker build context at ${OUT_DIR}"
