#!/bin/bash

set -euo pipefail

APP_ROOT="${APP_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
PROJECT_ID="${PROJECT_ID:-tradebest-465307}"
ZONE="${ZONE:-asia-south2-b}"
MACHINE_TYPE="${MACHINE_TYPE:-e2-standard-2}"
BASE_IMAGE="${BASE_IMAGE:-astroroshni-release-backend-cad234c4eae9-855}"
BASE_IMAGE_PROJECT="${BASE_IMAGE_PROJECT:-${PROJECT_ID}}"
SERVICE_ACCOUNT="${SERVICE_ACCOUNT:-800681558445-compute@developer.gserviceaccount.com}"
SCOPES="${SCOPES:-https://www.googleapis.com/auth/cloud-platform}"
INSTANCE_NAME="${INSTANCE_NAME:-astroroshni-image-builder-$(date +%Y%m%d-%H%M%S)}"
IMAGE_NAME="${IMAGE_NAME:-astroroshni-release-$(date +%Y%m%d-%H%M%S)}"
IMAGE_FAMILY="${IMAGE_FAMILY:-astroroshni-release}"
STORAGE_LOCATION="${STORAGE_LOCATION:-asia-south2}"
REMOTE_APP_DIR="${REMOTE_APP_DIR:-/home/tarun_yadav/AstrologyApp}"
TMP_ROOT="${TMPDIR:-/tmp}"
WORK_BUNDLE="$(mktemp "${TMP_ROOT%/}/astroroshni-release-image-bundle-${IMAGE_NAME}.XXXXXX.tgz")"
GCLOUD_BIN="${GCLOUD_BIN:-gcloud}"
GCLOUD_CONFIG="${GCLOUD_CONFIG:-${CLOUDSDK_CONFIG:-}}"
KEEP_BUILDER_VM="${KEEP_BUILDER_VM:-false}"

run_gcloud() {
  if [ -n "${GCLOUD_CONFIG}" ]; then
    CLOUDSDK_CONFIG="${GCLOUD_CONFIG}" "${GCLOUD_BIN}" "$@"
  else
    "${GCLOUD_BIN}" "$@"
  fi
}

retry_gcloud() {
  local attempts="$1"
  local sleep_seconds="$2"
  shift 2

  local attempt=1
  while true; do
    if run_gcloud "$@"; then
      return 0
    fi
    if [ "${attempt}" -ge "${attempts}" ]; then
      echo "❌ Command failed after ${attempts} attempt(s): ${GCLOUD_BIN} $*"
      return 1
    fi
    echo "⚠️ Command failed on attempt ${attempt}/${attempts}. Retrying in ${sleep_seconds}s..."
    sleep "${sleep_seconds}"
    attempt=$((attempt + 1))
  done
}

cleanup() {
  rm -f "${WORK_BUNDLE}" 2>/dev/null || true
}
trap cleanup EXIT

wait_for_ssh() {
  local attempt
  for attempt in $(seq 1 30); do
    if run_gcloud compute ssh tarun_yadav@"${INSTANCE_NAME}" \
      --zone="${ZONE}" \
      --project="${PROJECT_ID}" \
      --command='echo ssh-ready' >/dev/null 2>&1; then
      return 0
    fi
    sleep 5
  done
  echo "❌ Builder VM SSH did not become ready in time: ${INSTANCE_NAME}"
  return 1
}

echo "📦 Creating source bundle for image build..."
tar \
  -czf "${WORK_BUNDLE}" \
  -C "${APP_ROOT}" \
  --exclude='backend/venv' \
  --exclude='backend/logs' \
  --exclude='frontend/node_modules' \
  --exclude='frontend/build' \
  --exclude='frontend/.build-deploy-stage' \
  --exclude='frontend-next/.next' \
  --exclude='frontend-next/node_modules' \
  --exclude='scripts/.DS_Store' \
  --exclude='ops-agent/.DS_Store' \
  backend \
  frontend \
  frontend-next \
  scripts \
  systemd \
  ops-agent \
  deploy.sh \
  restart_server.sh

echo "🖥️ Creating builder VM ${INSTANCE_NAME} from ${BASE_IMAGE}..."
run_gcloud compute instances create "${INSTANCE_NAME}" \
  --project="${PROJECT_ID}" \
  --zone="${ZONE}" \
  --machine-type="${MACHINE_TYPE}" \
  --image="${BASE_IMAGE}" \
  --image-project="${BASE_IMAGE_PROJECT}" \
  --subnet=default \
  --service-account="${SERVICE_ACCOUNT}" \
  --scopes="${SCOPES}" \
  --labels=purpose=image-build,owner=codex

echo "⏳ Waiting for SSH readiness on ${INSTANCE_NAME}..."
wait_for_ssh

echo "📤 Copying release bundle and scripts to builder VM..."
run_gcloud compute scp \
  "${WORK_BUNDLE}" \
  "${APP_ROOT}/scripts/prepare-image-release.sh" \
  "${APP_ROOT}/scripts/bootstrap-runtime.sh" \
  "${APP_ROOT}/scripts/gce-startup-bootstrap.sh" \
  tarun_yadav@"${INSTANCE_NAME}":/tmp/ \
  --zone="${ZONE}" \
  --project="${PROJECT_ID}"

echo "🔧 Expanding current repo state onto the builder VM and preparing baked contents..."
run_gcloud compute ssh tarun_yadav@"${INSTANCE_NAME}" \
  --zone="${ZONE}" \
  --project="${PROJECT_ID}" \
  --command="set -euo pipefail
mkdir -p '${REMOTE_APP_DIR}'
tar -xzf '/tmp/$(basename "${WORK_BUNDLE}")' -C '${REMOTE_APP_DIR}'
mkdir -p '${REMOTE_APP_DIR}/scripts'
cp /tmp/prepare-image-release.sh '${REMOTE_APP_DIR}/scripts/prepare-image-release.sh'
cp /tmp/bootstrap-runtime.sh '${REMOTE_APP_DIR}/scripts/bootstrap-runtime.sh'
cp /tmp/gce-startup-bootstrap.sh '${REMOTE_APP_DIR}/scripts/gce-startup-bootstrap.sh'
chmod +x '${REMOTE_APP_DIR}/scripts/prepare-image-release.sh' '${REMOTE_APP_DIR}/scripts/bootstrap-runtime.sh' '${REMOTE_APP_DIR}/scripts/gce-startup-bootstrap.sh' '${REMOTE_APP_DIR}/scripts/install_runtime_watchdog.sh'
APP_ROOT='${REMOTE_APP_DIR}' APP_COMMIT_SHA='${IMAGE_NAME}' SERVE_FRONTEND_LOCALLY='false' INSTALL_GCP_OPS_AGENT='false' '${REMOTE_APP_DIR}/scripts/prepare-image-release.sh'"

echo "⏹️ Stopping builder VM before imaging..."
run_gcloud compute instances stop "${INSTANCE_NAME}" \
  --zone="${ZONE}" \
  --project="${PROJECT_ID}"

echo "🧊 Creating release image ${IMAGE_NAME}..."
retry_gcloud 3 20 compute images create "${IMAGE_NAME}" \
  --project="${PROJECT_ID}" \
  --source-disk="${INSTANCE_NAME}" \
  --source-disk-zone="${ZONE}" \
  --family="${IMAGE_FAMILY}" \
  --storage-location="${STORAGE_LOCATION}" \
  --guest-os-features=UEFI_COMPATIBLE

echo "✅ Release image ready: ${IMAGE_NAME}"

case "$(printf '%s' "${KEEP_BUILDER_VM}" | tr '[:upper:]' '[:lower:]')" in
  true|1|yes)
    echo "ℹ️ Builder VM retained for inspection: ${INSTANCE_NAME}"
    ;;
  *)
    echo "🧹 Deleting builder VM ${INSTANCE_NAME}..."
    run_gcloud compute instances delete "${INSTANCE_NAME}" \
      --project="${PROJECT_ID}" \
      --zone="${ZONE}" \
      --quiet
    echo "✅ Builder VM deleted"
    ;;
esac
