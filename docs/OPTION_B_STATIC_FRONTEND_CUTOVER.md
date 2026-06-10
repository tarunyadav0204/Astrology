# Option B Cutover Runbook

This runbook moves AstroRoshni production to:

- **Frontend:** Cloud Storage + Cloud CDN + HTTPS Load Balancer
- **Backend:** existing Managed Instance Group

That keeps backend risk low while removing frontend serving/build work from the VM fleet.

## 1. Provision frontend static hosting resources

Run:

```bash
./infra/gcp/provision-option-b-frontend.sh \
  tradebest-465307 \
  tradebest-465307-frontend-site \
  astroroshni-frontend-site \
  asia-south2
```

This creates:

- `gs://tradebest-465307-frontend-site`
- backend bucket `astroroshni-frontend-site`

Then set the GitHub Actions repository variable:

```text
GCP_FRONTEND_SITE_BUCKET=tradebest-465307-frontend-site
```

Keep:

```text
SERVE_FRONTEND_LOCALLY=true
```

for the first deploys. That gives us a safe overlap period while the load balancer still points at the VM frontend.

## 2. Publish the site to the bucket

Push to `main` or run the deploy workflow manually.

The deploy workflow now does two frontend publishes when frontend changes:

1. uploads the versioned build tarball to the artifact bucket
2. uploads `frontend/build` to `gs://$GCP_FRONTEND_SITE_BUCKET`

It also sets cache headers:

- `*.html` → `Cache-Control: no-cache`
- hashed static assets under `/static/` and `/_next/static/` → `Cache-Control: public, max-age=31536000, immutable`
- `manifest.json`, `robots.txt`, `sitemap.xml` → `Cache-Control: public, max-age=3600`

## 3. Export the current URL map

List the URL map:

```bash
gcloud compute url-maps list
```

Export the active map:

```bash
gcloud compute url-maps export YOUR_URL_MAP --destination /tmp/astroroshni-url-map.yaml
```

## 4. Update the URL map for backend-bucket frontend routing

Keep the existing `/api/*` path routing to the MIG backend service.

Change the **default frontend route** so non-API traffic goes to:

```text
https://www.googleapis.com/compute/v1/projects/tradebest-465307/global/backendBuckets/astroroshni-frontend-site
```

In practice, that means the path matcher that currently sends `/` to the VM frontend should instead use the backend bucket as its `defaultService`, while any `/api/*` rule keeps the backend service.

Typical shape:

```yaml
pathMatchers:
  - name: astroroshni-paths
    defaultService: https://www.googleapis.com/compute/v1/projects/tradebest-465307/global/backendBuckets/astroroshni-frontend-site
    pathRules:
      - paths:
          - /api/*
        service: https://www.googleapis.com/compute/v1/projects/tradebest-465307/global/backendServices/YOUR_BACKEND_SERVICE
```

If your URL map already has host rules for multiple domains, keep those intact and change only the frontend default for the AstroRoshni host/path matcher.

Import the edited map:

```bash
gcloud compute url-maps import YOUR_URL_MAP --source /tmp/astroroshni-url-map.yaml
```

## 5. Verify before disabling local frontend serving

Check both:

```bash
curl -I https://astroroshni.com/
curl -I https://astroroshni.com/api/health
```

Then verify a few public pages in a browser:

- `/`
- `/karma-analysis`
- `/kundli-matching`
- `/chat`

The key thing we want is:

- HTML comes from the bucket/CDN
- API calls still reach the MIG backend

## 6. Flip VMs to backend-only

Once the public site is healthy via the backend bucket, set:

```text
SERVE_FRONTEND_LOCALLY=false
```

in GitHub Actions repository variables.

From then on:

- production deploys still publish frontend artifacts/site builds
- VMs skip local frontend build/serve work
- deploy verification on VMs only checks backend health

## 7. Optional cleanup after stable cutover

After several clean deploys and at least one healthy MIG replacement:

- remove frontend-specific process management from the VM startup path
- eventually stop exposing VM frontend port `3001`
- keep frontend artifacts in GCS/CDN as the only production frontend source

## Why this is the right intermediate state

Option B removes the biggest frontend operational risks without forcing a backend runtime migration yet:

- no frontend chunk mismatch across VMs
- no frontend build pressure during MIG replacement
- no frontend outage coupled to backend VM lifecycle
- clean path to later move the backend from MIG to Cloud Run or containers
