# Production Status - 2026-06-10

This document records what was completed during the Option B production migration work, what is currently stable, and what still needs follow-up.

## Goal

Move production toward **Option B**:

- **Frontend** served from **Cloud Storage + HTTPS Load Balancer / CDN path**
- **Backend** continues on the **Managed Instance Group (MIG)**

The main intent was to remove frontend serving/build responsibility from production VMs while keeping backend infrastructure stable.

## What Was Completed

### 1. Frontend cutover to static hosting

Completed:

- created frontend site bucket:
  - `gs://tradebest-465307-frontend-site`
- created backend bucket:
  - `astroroshni-frontend-site`
- made the site bucket publicly readable
- configured bucket website behavior:
  - main page: `index.html`
  - error page: `maintenance.html`
- updated the HTTPS load balancer URL map so:
  - `/api/*` continues to route to backend MIG service
  - non-API traffic routes to the frontend backend bucket

Verified:

- `https://astroroshni.com/` returned `200`
- `https://astroroshni.com/api/health` returned healthy backend JSON

### 2. CI/CD changes for Option B

Completed in repo:

- workflow publishes frontend artifact tarballs to:
  - `gs://tradebest-465307-frontend-artifacts/prod/frontend-build-$GITHUB_SHA.tgz`
  - `gs://tradebest-465307-frontend-artifacts/prod/frontend-build-latest.tgz`
- workflow publishes extracted frontend site files to:
  - `gs://tradebest-465307-frontend-site`
- cache headers are set for HTML vs immutable hashed assets
- `SERVE_FRONTEND_LOCALLY=false` is now supported end to end

GitHub Actions variables in use:

- `GCP_FRONTEND_ARTIFACT_BUCKET=tradebest-465307-frontend-artifacts`
- `GCP_FRONTEND_SITE_BUCKET=tradebest-465307-frontend-site`
- `SERVE_FRONTEND_LOCALLY=false`

### 3. Backend-only production deploy behavior

Completed in repo:

- `deploy.sh` supports backend-only VM deploys via:
  - `SERVE_FRONTEND_LOCALLY=false`
- when frontend is externalized:
  - skip local frontend build
  - skip local frontend restart
  - skip local frontend verification
  - keep backend deploy/health behavior only

### 4. MIG/health-check stabilization work

Completed:

- health check path moved to lightweight backend endpoint:
  - `/api/keepalive`
- MIG autohealing initial delay increased to:
  - `600s`
- duplicate local watchdog approach was moved out of the critical recovery path
- 2-worker backend change had already helped steady-state stability

## Current Stable State

As of this document:

- frontend traffic is served from the static bucket path through the load balancer
- backend traffic is served from the MIG
- production deploys are using the backend-only model
- the previously broken MIG-wide `startup-script` override has been removed
- the bad replacement instance caused by that override experiment was being deleted
- two serving instances remained healthy on the known-good path

## What Went Wrong

### 1. MIG-wide startup-script override experiment broke

We attempted to use:

- `gcloud compute instance-groups managed all-instances-config update ... --metadata=startup-script=...`

to force the new backend-only startup path across the MIG.

That approach proved brittle because:

- shell quoting/escaping during inline metadata injection is easy to corrupt
- a broken injected script produced startup-script failures like:
  - `exit status 127`

This caused a replacement VM (`astroroshni-mig-4k0w`) to remain stuck in:

- `HEALTH_STATE=TIMEOUT`
- `ACTION=VERIFYING`

We removed that broken override.

### 2. Regional template creation did not replace copied startup-script metadata cleanly

We attempted to create newer templates (`v5`, `v6`) from `--source-instance` while overriding the startup script using:

- `--metadata-from-file=startup-script=...`

Observed behavior:

- the newly created regional templates still carried forward the older inline startup script metadata copied from the source instance/template lineage
- the expected replacement of `startup-script` did not happen cleanly

This means:

- the template naming (`v5`, `v6`) changed
- but the effective startup script inside the template did **not** become the clean backend-only script we expected

## Current Known-Good Runtime Path

The known-good production path is still effectively the older `v3` startup behavior plus:

- frontend externalized at the load balancer
- backend-only deploy behavior from CI (`SERVE_FRONTEND_LOCALLY=false`)
- longer autohealing delay

In other words:

- the **serving architecture** is improved and working
- the **template-authoring cleanup** is the part still unfinished

## What Is Pending

### Priority 1 - finish clean backend-only instance template authoring

Still needed:

- create a truly clean backend-only instance template whose `startup-script` is authored fresh, not copied forward from the old template chain

Recommended approach:

1. do **not** use the current `--source-instance` flow if it keeps inheriting the old script
2. use a template creation path that explicitly defines metadata from scratch
3. verify the created template immediately with:
   - `gcloud compute instance-templates list --filter="name=..." --format="yaml(name,selfLink,properties.metadata)"`
4. only after verifying the template metadata, point the MIG to it

### Priority 2 - remove stale frontend assumptions from GCP config

Still worth doing later:

- remove named port `frontend:3001` from the MIG if no longer used
- review any backend service or health-check assumptions that still reference the old VM-served frontend path

### Priority 3 - reduce boot-time VM work

Still pending:

- bake runtime dependencies into image/template instead of doing so much `apt-get` at boot

This remains the next major reliability improvement for backend VM recovery.

## Recommended Next Session Plan

1. Verify the MIG is back to 2 healthy instances.
2. Freeze production changes unless there is an incident.
3. Create a **fresh backend-only template authoring plan**:
   - avoid brittle inline all-instances metadata injection
   - avoid template creation paths that silently keep the old startup script
4. Test that template in a controlled replacement before broader rollout.

## Commands That Were Important

Useful operational checks:

```bash
gcloud compute instance-groups managed list-instances astroroshni-mig \
  --zone=asia-south2-a

gcloud compute instance-groups managed describe astroroshni-mig \
  --zone=asia-south2-a

gcloud compute instance-templates list --filter="name~astroroshni"
```

Useful metadata inspection:

```bash
gcloud compute ssh INSTANCE_NAME \
  --zone=asia-south2-a \
  --command='curl -s -H "Metadata-Flavor: Google" "http://metadata.google.internal/computeMetadata/v1/instance/attributes/?recursive=true"'
```

Useful startup-script journal inspection:

```bash
gcloud compute ssh INSTANCE_NAME \
  --zone=asia-south2-a \
  --command='sudo journalctl -u google-startup-scripts.service -n 200 --no-pager'
```

## Bottom Line

### Working now

- frontend static hosting cutover
- backend MIG serving
- backend-only deploy path
- production health is much better than where the day started

### Not finished yet

- clean, template-native backend-only startup script in the MIG template chain

That remaining work is important, but it is **cleanup/hardening**, not the same level of emergency as the original production instability.
