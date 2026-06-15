#!/bin/bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/home/tarun_yadav/AstrologyApp}"
CONFIG_SOURCE="${CONFIG_SOURCE:-${APP_ROOT}/ops-agent/config.yaml}"
CONFIG_TARGET="/etc/google-cloud-ops-agent/config.yaml"

echo "==> Installing Google Cloud Ops Agent"
if ! systemctl list-unit-files | grep -q '^google-cloud-ops-agent'; then
  curl -sSO https://dl.google.com/cloudagents/add-google-cloud-ops-agent-repo.sh
  sudo bash add-google-cloud-ops-agent-repo.sh --also-install
  rm -f add-google-cloud-ops-agent-repo.sh
else
  echo "==> Google Cloud Ops Agent already installed; skipping package install"
fi

echo "==> Applying AstroRoshni Ops Agent config"
if [ ! -f "${CONFIG_SOURCE}" ]; then
  echo "Missing config source: ${CONFIG_SOURCE}" >&2
  exit 1
fi

sudo mkdir -p "$(dirname "${CONFIG_TARGET}")"
sudo cp "${CONFIG_SOURCE}" "${CONFIG_TARGET}"
sudo chown root:root "${CONFIG_TARGET}"
sudo chmod 0644 "${CONFIG_TARGET}"

echo "==> Restarting Ops Agent"
sudo systemctl enable google-cloud-ops-agent
sudo systemctl restart google-cloud-ops-agent
sudo systemctl --no-pager --full status google-cloud-ops-agent || true

echo "==> Ops Agent install/apply complete"
