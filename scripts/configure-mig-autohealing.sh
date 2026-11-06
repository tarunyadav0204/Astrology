#!/usr/bin/env bash
# Run once with infrastructure permissions. Keep LB health checks unchanged.
set -euo pipefail
PROJECT_ID="${GCP_PROJECT_ID:?Set GCP_PROJECT_ID}"
CHECK_NAME=astroroshni-autohealing
if gcloud compute health-checks describe "$CHECK_NAME" --project "$PROJECT_ID" --global >/dev/null 2>&1; then
  action=update
else
  action=create
fi
gcloud compute health-checks "$action" http "$CHECK_NAME" --project "$PROJECT_ID" --global \
  --port 8001 --request-path /api/keepalive --check-interval 30s --timeout 15s \
  --healthy-threshold 2 --unhealthy-threshold 6 --enable-logging \
  --description 'Conservative VM repair check; load balancer uses its separate fast check'
for mig in astroroshni-mig-s2b astroroshni-chat-worker-mig; do
  gcloud compute instance-groups managed update "$mig" --project "$PROJECT_ID" --zone asia-south2-b \
    --health-check "$CHECK_NAME" --initial-delay 600 \
    --update-policy-type opportunistic --update-policy-max-unavailable 0 \
    --update-policy-max-surge 1 --update-policy-replacement-method substitute
done
