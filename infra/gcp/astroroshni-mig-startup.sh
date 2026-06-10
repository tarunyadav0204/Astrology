#!/bin/bash
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive

APP_USER="tarun_yadav"
APP_DIR="/home/${APP_USER}/AstrologyApp"
DEPLOY_BRANCH="main"
GITHUB_KEY_SECRET="GITHUB_STARTUP_DEPLOY_KEY"
LOG_FILE="/var/log/astroroshni-startup.log"

exec > >(tee -a "${LOG_FILE}") 2>&1

echo "========== AstroRoshni startup $(date -u) =========="

exec 9>/var/lock/astroroshni-startup.lock
flock -n 9 || exit 0

id "${APP_USER}" >/dev/null 2>&1 || useradd -m -s /bin/bash "${APP_USER}"

echo "Waiting for apt locks..."
while fuser /var/lib/dpkg/lock-frontend >/dev/null 2>&1 \
   || fuser /var/lib/dpkg/lock >/dev/null 2>&1 \
   || fuser /var/lib/apt/lists/lock >/dev/null 2>&1; do
  sleep 5
done

apt-get update -y
echo "Waiting for apt locks after update..."
while fuser /var/lib/dpkg/lock-frontend >/dev/null 2>&1 \
   || fuser /var/lib/dpkg/lock >/dev/null 2>&1 \
   || fuser /var/lib/apt/lists/lock >/dev/null 2>&1; do
  sleep 5
done

apt-get install -y -o Dpkg::Options::="--force-confold" \
  git curl ca-certificates gnupg python3 python3-venv python3-pip psmisc iproute2 openssh-client \
  libnspr4 libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
  libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 \
  libxrandr2 libgbm1 libasound2 libpango-1.0-0 libcairo2 \
  libgtk-3-0

if ! command -v node >/dev/null 2>&1; then
  curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
  apt-get install -y -o Dpkg::Options::="--force-confold" nodejs
fi

if ! command -v gcloud >/dev/null 2>&1; then
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg \
    | gpg --dearmor -o /etc/apt/keyrings/cloud.google.gpg
  echo "deb [signed-by=/etc/apt/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" \
    > /etc/apt/sources.list.d/google-cloud-sdk.list
  apt-get update -y
  apt-get install -y -o Dpkg::Options::="--force-confold" google-cloud-cli
fi

PROJECT_ID="$(curl -fsH 'Metadata-Flavor: Google' http://metadata.google.internal/computeMetadata/v1/project/project-id)"
gcloud config set project "${PROJECT_ID}"

install -d -m 700 -o "${APP_USER}" -g "${APP_USER}" "/home/${APP_USER}/.ssh"
gcloud secrets versions access latest --secret="${GITHUB_KEY_SECRET}" > "/home/${APP_USER}/.ssh/astroroshni_startup_deploy_key"
chown "${APP_USER}:${APP_USER}" "/home/${APP_USER}/.ssh/astroroshni_startup_deploy_key"
chmod 600 "/home/${APP_USER}/.ssh/astroroshni_startup_deploy_key"

sudo -u "${APP_USER}" ssh-keyscan github.com >> "/home/${APP_USER}/.ssh/known_hosts"
chown "${APP_USER}:${APP_USER}" "/home/${APP_USER}/.ssh/known_hosts"
chmod 644 "/home/${APP_USER}/.ssh/known_hosts"

if [ ! -d "${APP_DIR}/.git" ]; then
  sudo -u "${APP_USER}" GIT_SSH_COMMAND="ssh -i /home/${APP_USER}/.ssh/astroroshni_startup_deploy_key -o IdentitiesOnly=yes" \
    git clone --branch "${DEPLOY_BRANCH}" git@github.com:tarunyadav0204/Astrology.git "${APP_DIR}"
fi

sudo -u "${APP_USER}" bash -lc "
  cd '${APP_DIR}'
  git remote set-url origin git@github.com:tarunyadav0204/Astrology.git
  export GIT_SSH_COMMAND='ssh -i /home/${APP_USER}/.ssh/astroroshni_startup_deploy_key -o IdentitiesOnly=yes'
  export DEPLOY_BRANCH='${DEPLOY_BRANCH}'
  export SERVE_FRONTEND_LOCALLY=false
  export SYNC_GCP_SECRETS=true
  export DEFER_FRONTEND_BUILD=true
  bash deploy.sh
"

echo "========== AstroRoshni startup complete $(date -u) =========="
