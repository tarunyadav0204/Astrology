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

copy_path() {
  local src_rel="$1"
  local src="${APP_ROOT}/${src_rel}"
  local dest="${OUT_DIR}/${src_rel}"
  mkdir -p "$(dirname "${dest}")"
  if [ -d "${src}" ]; then
    mkdir -p "${dest}"
    rsync -a \
      --exclude '__pycache__' \
      --exclude '*.pyc' \
      --exclude '*.pyo' \
      --exclude '.DS_Store' \
      "${src}/" "${dest}/"
  else
    cp "${src}" "${dest}"
  fi
}

# Payment service runtime
copy_path "play_payment_service"

# Python deps list used by Docker build
copy_path "backend/requirements.txt"

# Only backend modules needed by the Play payment flow
copy_path "backend/auth.py"
copy_path "backend/db.py"
copy_path "backend/utils"
copy_path "backend/activity"
copy_path "backend/credits"

echo "Prepared play payment build context at ${OUT_DIR}"
