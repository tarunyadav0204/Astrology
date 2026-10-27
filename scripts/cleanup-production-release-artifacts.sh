#!/usr/bin/env bash

# Removes only release artifacts that are no longer usable for a safe rollback.
# Default mode is report-only. Pass --apply to perform deletions.

set -euo pipefail

PROJECT_ID="${PROJECT_ID:-tradebest-465307}"
KEEP_VM_IMAGES="${KEEP_VM_IMAGES:-20}"
KEEP_CONTAINER_IMAGES="${KEEP_CONTAINER_IMAGES:-15}"
CONTAINER_MAX_AGE_DAYS="${CONTAINER_MAX_AGE_DAYS:-30}"
DELETE_PARALLELISM="${DELETE_PARALLELISM:-8}"
APPLY=false

usage() {
  cat <<'EOF'
Usage: cleanup-production-release-artifacts.sh [--apply] [--project PROJECT_ID]
       [--keep-vm-images COUNT] [--keep-container-images COUNT]
       [--container-max-age-days DAYS] [--delete-parallelism COUNT]

Without --apply, prints the exact templates and images that would be deleted.
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --apply) APPLY=true ;;
    --project) PROJECT_ID="$2"; shift ;;
    --keep-vm-images) KEEP_VM_IMAGES="$2"; shift ;;
    --keep-container-images) KEEP_CONTAINER_IMAGES="$2"; shift ;;
    --container-max-age-days) CONTAINER_MAX_AGE_DAYS="$2"; shift ;;
    --delete-parallelism) DELETE_PARALLELISM="$2"; shift ;;
    --help|-h) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
  shift
done

case "${KEEP_VM_IMAGES}:${KEEP_CONTAINER_IMAGES}:${CONTAINER_MAX_AGE_DAYS}:${DELETE_PARALLELISM}" in
  *[!0-9:]*|:*|*::*) echo "Retention values must be positive integers." >&2; exit 2 ;;
esac

if [ "${KEEP_VM_IMAGES}" -lt 1 ] || [ "${KEEP_CONTAINER_IMAGES}" -lt 1 ] || [ "${CONTAINER_MAX_AGE_DAYS}" -lt 1 ] || [ "${DELETE_PARALLELISM}" -lt 1 ]; then
  echo "Retention values must be at least one." >&2
  exit 2
fi

for command in gcloud jq date; do
  command -v "${command}" >/dev/null || { echo "Missing required command: ${command}" >&2; exit 1; }
done

WORK_DIR="$(mktemp -d)"
trap 'rm -rf "${WORK_DIR}"' EXIT

contains_line() {
  local file="$1"
  local value="$2"
  grep -Fqx -- "${value}" "${file}"
}

run_delete() {
  if [ "${APPLY}" = true ]; then
    "$@"
  else
    printf 'DRY RUN: '
    printf '%q ' "$@"
    printf '\n'
  fi
}

delete_compute_templates() {
  [ -s "${WORK_DIR}/templates-to-delete.txt" ] || return 0
  if [ "${APPLY}" = true ]; then
    xargs -P "${DELETE_PARALLELISM}" -n 1 \
      gcloud compute instance-templates delete --project="${PROJECT_ID}" --quiet \
      < "${WORK_DIR}/templates-to-delete.txt"
  else
    while IFS= read -r template_name; do
      [ -n "${template_name}" ] || continue
      run_delete gcloud compute instance-templates delete "${template_name}" --project="${PROJECT_ID}" --quiet
    done < "${WORK_DIR}/templates-to-delete.txt"
  fi
}

delete_compute_images() {
  [ -s "${WORK_DIR}/images-to-delete.txt" ] || return 0
  if [ "${APPLY}" = true ]; then
    xargs -P "${DELETE_PARALLELISM}" -n 1 \
      gcloud compute images delete --project="${PROJECT_ID}" --quiet \
      < "${WORK_DIR}/images-to-delete.txt"
  else
    while IFS= read -r image_name; do
      [ -n "${image_name}" ] || continue
      run_delete gcloud compute images delete "${image_name}" --project="${PROJECT_ID}" --quiet
    done < "${WORK_DIR}/images-to-delete.txt"
  fi
}

delete_container_images() {
  [ -s "${WORK_DIR}/docker-images-to-delete.tsv" ] || return 0
  if [ "${APPLY}" = true ]; then
    awk -F '\t' '{print $1 "@" $2}' "${WORK_DIR}/docker-images-to-delete.tsv" \
      | xargs -P "${DELETE_PARALLELISM}" -n 1 sh -c 'gcloud artifacts docker images delete "$0" --delete-tags --quiet'
  else
    while IFS=$'\t' read -r package version; do
      [ -n "${package}" ] || continue
      run_delete gcloud artifacts docker images delete "${package}@${version}" --delete-tags --quiet
    done < "${WORK_DIR}/docker-images-to-delete.tsv"
  fi
}

echo "Release artifact cleanup for ${PROJECT_ID} ($([ "${APPLY}" = true ] && echo APPLY || echo DRY-RUN))"

# ---- Compute Engine release images and templates --------------------------------
gcloud compute images list --project="${PROJECT_ID}" --no-standard-images --format=json > "${WORK_DIR}/images.json"
gcloud compute instance-templates list --project="${PROJECT_ID}" --format=json > "${WORK_DIR}/templates.json"
gcloud compute instance-groups managed list --project="${PROJECT_ID}" --format='value(instanceTemplate)' \
  | sed '/^$/d;s#.*/##' | sort -u > "${WORK_DIR}/active-templates.txt"

jq -r --argjson keep "${KEEP_VM_IMAGES}" '
  map(select(.name | startswith("astroroshni-release-backend-")))
  | sort_by(.creationTimestamp) | reverse | .[0:$keep][] | .name
' "${WORK_DIR}/images.json" | sort -u > "${WORK_DIR}/protected-images.txt"

# Never remove an image referenced by a live MIG template, or by a template outside
# the two release-template families managed below.
while IFS= read -r template_name; do
  jq -r --arg name "${template_name}" '
    .[] | select(.name == $name)
    | .properties.disks[]?.initializeParams.sourceImage? // empty
    | split("/")[-1]
  ' "${WORK_DIR}/templates.json" >> "${WORK_DIR}/protected-images.txt"
done < "${WORK_DIR}/active-templates.txt"

jq -r '
  .[]
  | select(.name | test("^(astro-baked|astro-chat-worker)-") | not)
  | .properties.disks[]?.initializeParams.sourceImage? // empty
  | split("/")[-1]
' "${WORK_DIR}/templates.json" >> "${WORK_DIR}/protected-images.txt"

sort -u -o "${WORK_DIR}/protected-images.txt" "${WORK_DIR}/protected-images.txt"

jq -r '
  .[]
  | select(.name | test("^(astro-baked|astro-chat-worker)-"))
  | [.name, (.properties.disks[]?.initializeParams.sourceImage? // "" | split("/")[-1])]
  | @tsv
' "${WORK_DIR}/templates.json" > "${WORK_DIR}/release-templates.tsv"

: > "${WORK_DIR}/templates-to-delete.txt"
while IFS=$'\t' read -r template_name image_name; do
  [ -n "${image_name}" ] || continue
  if ! contains_line "${WORK_DIR}/protected-images.txt" "${image_name}"; then
    printf '%s\n' "${template_name}" >> "${WORK_DIR}/templates-to-delete.txt"
  fi
done < "${WORK_DIR}/release-templates.tsv"

echo "Compute templates retained: $(( $(wc -l < "${WORK_DIR}/release-templates.tsv") - $(wc -l < "${WORK_DIR}/templates-to-delete.txt") ))"
echo "Compute templates to delete: $(wc -l < "${WORK_DIR}/templates-to-delete.txt")"
delete_compute_templates

jq -r '
  .[] | select(.name | startswith("astroroshni-release-backend-")) | .name
' "${WORK_DIR}/images.json" > "${WORK_DIR}/release-images.txt"

: > "${WORK_DIR}/images-to-delete.txt"
while IFS= read -r image_name; do
  [ -n "${image_name}" ] || continue
  if ! contains_line "${WORK_DIR}/protected-images.txt" "${image_name}"; then
    printf '%s\n' "${image_name}" >> "${WORK_DIR}/images-to-delete.txt"
  fi
done < "${WORK_DIR}/release-images.txt"

echo "VM images retained: $(( $(wc -l < "${WORK_DIR}/release-images.txt") - $(wc -l < "${WORK_DIR}/images-to-delete.txt") ))"
echo "VM images to delete: $(wc -l < "${WORK_DIR}/images-to-delete.txt")"
delete_compute_images

# ---- Artifact Registry container images ------------------------------------------
# Active Cloud Run image references are protected even if they are older than the
# normal retention window. Retention is also kept per package for rollback safety.
ARTIFACT_REPOSITORY="asia-south2-docker.pkg.dev/${PROJECT_ID}/cloud-run"
gcloud artifacts docker images list "${ARTIFACT_REPOSITORY}" --include-tags --format=json > "${WORK_DIR}/docker-images.json"
: > "${WORK_DIR}/protected-docker-images.tsv"

jq -r --argjson keep "${KEEP_CONTAINER_IMAGES}" '
  group_by(.package)[] | sort_by(.createTime) | reverse | .[0:$keep][]
  | [.package, .version] | @tsv
' "${WORK_DIR}/docker-images.json" >> "${WORK_DIR}/protected-docker-images.tsv"

for region in us-central1 asia-south1 asia-south2; do
  gcloud run services list --project="${PROJECT_ID}" --region="${region}" --format=json \
    | jq -r '.[] | .spec.template.spec.containers[]?.image // empty'
done | sort -u > "${WORK_DIR}/active-cloud-run-images.txt"

while IFS= read -r image_ref; do
  [ -n "${image_ref}" ] || continue
  if [[ "${image_ref}" == *"@"* ]]; then
    package="${image_ref%@*}"
    version="${image_ref#*@}"
    jq -r --arg package "${package}" --arg version "${version}" \
      '.[] | select(.package == $package and .version == $version) | [.package, .version] | @tsv' \
      "${WORK_DIR}/docker-images.json" >> "${WORK_DIR}/protected-docker-images.tsv"
  else
    package="${image_ref%:*}"
    tag="${image_ref##*:}"
    jq -r --arg package "${package}" --arg tag "${tag}" \
      '.[] | select(.package == $package and (.tags // [] | index($tag))) | [.package, .version] | @tsv' \
      "${WORK_DIR}/docker-images.json" >> "${WORK_DIR}/protected-docker-images.tsv"
  fi
done < "${WORK_DIR}/active-cloud-run-images.txt"

sort -u -o "${WORK_DIR}/protected-docker-images.tsv" "${WORK_DIR}/protected-docker-images.tsv"
cutoff_epoch="$(date -u -d "${CONTAINER_MAX_AGE_DAYS} days ago" +%s 2>/dev/null || date -u -v-"${CONTAINER_MAX_AGE_DAYS}"d +%s)"

: > "${WORK_DIR}/docker-images-to-delete.tsv"
while IFS=$'\t' read -r package version created_at; do
  [ -n "${package}" ] || continue
  created_at_seconds="${created_at%%.*}Z"
  created_epoch="$(date -u -d "${created_at}" +%s 2>/dev/null || date -u -j -f '%Y-%m-%dT%H:%M:%SZ' "${created_at_seconds}" +%s)"
  if [ "${created_epoch}" -lt "${cutoff_epoch}" ] && ! contains_line "${WORK_DIR}/protected-docker-images.tsv" "${package}"$'\t'"${version}"; then
    printf '%s\t%s\n' "${package}" "${version}" >> "${WORK_DIR}/docker-images-to-delete.tsv"
  fi
done < <(jq -r '.[] | [.package, .version, .createTime] | @tsv' "${WORK_DIR}/docker-images.json")

echo "Container images retained/protected: $(wc -l < "${WORK_DIR}/protected-docker-images.tsv")"
echo "Container images to delete: $(wc -l < "${WORK_DIR}/docker-images-to-delete.tsv")"
delete_container_images

echo "Cleanup complete."
