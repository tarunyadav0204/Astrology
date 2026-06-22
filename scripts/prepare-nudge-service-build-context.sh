#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
SERVICE_NAME="${1:-}"
OUT_DIR="${2:-}"

if [ -z "${SERVICE_NAME}" ] || [ -z "${OUT_DIR}" ]; then
  echo "usage: $0 SERVICE_NAME OUT_DIR"
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
      --exclude '*.swp' \
      --exclude '*.swo' \
      --exclude '.DS_Store' \
      "${src}/" "${dest}/"
  else
    cp "${src}" "${dest}"
  fi
}

copy_path "${SERVICE_NAME}"
copy_path "backend"

echo "Prepared ${SERVICE_NAME} build context at ${OUT_DIR}"
