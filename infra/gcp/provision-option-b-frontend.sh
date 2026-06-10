#!/bin/bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  provision-option-b-frontend.sh PROJECT_ID SITE_BUCKET BACKEND_BUCKET_NAME [REGION]

Creates or updates the GCS bucket and HTTPS load-balancer backend bucket used
for Option B frontend hosting:
  - frontend static site in Cloud Storage
  - Cloud CDN via a backend bucket

Example:
  ./infra/gcp/provision-option-b-frontend.sh \
    tradebest-465307 \
    tradebest-465307-frontend-site \
    astroroshni-frontend-site \
    asia-south2
EOF
}

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
  usage
  exit 0
fi

if [ "$#" -lt 3 ] || [ "$#" -gt 4 ]; then
  usage >&2
  exit 1
fi

PROJECT_ID="$1"
SITE_BUCKET="$2"
BACKEND_BUCKET_NAME="$3"
REGION="${4:-asia-south2}"

echo "🔧 Provisioning Option B frontend resources"
echo "   project:        ${PROJECT_ID}"
echo "   site bucket:    gs://${SITE_BUCKET}"
echo "   backend bucket: ${BACKEND_BUCKET_NAME}"
echo "   region:         ${REGION}"

gcloud config set project "${PROJECT_ID}" >/dev/null

if gcloud storage buckets describe "gs://${SITE_BUCKET}" >/dev/null 2>&1; then
  echo "ℹ️ GCS site bucket already exists: gs://${SITE_BUCKET}"
else
  echo "➕ Creating GCS site bucket..."
  gcloud storage buckets create "gs://${SITE_BUCKET}" \
    --project="${PROJECT_ID}" \
    --location="${REGION}" \
    --uniform-bucket-level-access
fi

echo "🔒 Enforcing uniform bucket-level access..."
gcloud storage buckets update "gs://${SITE_BUCKET}" \
  --project="${PROJECT_ID}" \
  --uniform-bucket-level-access

if gcloud compute backend-buckets describe "${BACKEND_BUCKET_NAME}" --project="${PROJECT_ID}" >/dev/null 2>&1; then
  echo "ℹ️ Backend bucket already exists; updating CDN settings..."
  gcloud compute backend-buckets update "${BACKEND_BUCKET_NAME}" \
    --project="${PROJECT_ID}" \
    --gcs-bucket-name="${SITE_BUCKET}" \
    --enable-cdn
else
  echo "➕ Creating backend bucket..."
  gcloud compute backend-buckets create "${BACKEND_BUCKET_NAME}" \
    --project="${PROJECT_ID}" \
    --gcs-bucket-name="${SITE_BUCKET}" \
    --enable-cdn
fi

cat <<EOF

✅ Option B frontend resources are ready.

Next:
1. Set GitHub Actions variable:
   GCP_FRONTEND_SITE_BUCKET=${SITE_BUCKET}

2. Run the deploy workflow once so CI uploads frontend/build into:
   gs://${SITE_BUCKET}

3. Update your HTTPS load balancer URL map so:
   - /api/* keeps pointing at the backend MIG service
   - all non-API traffic uses backend bucket:
     https://www.googleapis.com/compute/v1/projects/${PROJECT_ID}/global/backendBuckets/${BACKEND_BUCKET_NAME}

4. After public verification, set:
   SERVE_FRONTEND_LOCALLY=false
EOF
