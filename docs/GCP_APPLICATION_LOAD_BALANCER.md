# GCP Application Load Balancer: maintenance & error pages

For a **global external Application Load Balancer** (HTTPS), use Google’s **custom error response** feature so users see your maintenance HTML instead of a generic error when backends return **5xx** (or chosen **4xx**).

Official guides:

- [Custom error response overview](https://cloud.google.com/load-balancing/docs/https/custom-error-response)
- [Configure custom error responses](https://cloud.google.com/load-balancing/docs/https/configure-custom-error-responses)

## Recommended pattern

1. **Build** the same page you ship with the app: after `npm run build`, use `frontend/build/maintenance.html` (from `frontend/public/maintenance.html`).

2. **Upload** it to a dedicated Cloud Storage bucket (or a prefix in a bucket used only for error assets), for example:

   ```bash
   gcloud storage cp frontend/build/maintenance.html gs://YOUR_ERROR_PAGES_BUCKET/maintenance.html
   ```

   If the HTML references `/favicon.png` or other assets, either use **inline-only** styling (current template) or upload those objects to the **same** bucket and add **URL map path rules** so normal requests for `/favicon.png` can be served from that bucket (see Google’s “linked assets” example in the configure doc).

3. **Create a backend bucket** that points at that GCS bucket and attach it to the same load balancer (in addition to your normal backend service).

4. **Edit the URL map** and add `defaultCustomErrorResponsePolicy` so **502**, **503**, and **504** (and optionally all **5xx**) pull content from the backend bucket:

   ```yaml
   defaultCustomErrorResponsePolicy:
     errorResponseRules:
       - matchResponseCodes:
           - 502
           - 503
           - 504
         path: "/maintenance.html"
         # Optional: show maintenance body but return 200 to clients
         # overrideResponseCode: 200
     errorService: https://www.googleapis.com/compute/v1/projects/PROJECT_ID/global/backendBuckets/YOUR_ERROR_BACKEND_BUCKET
   ```

   Export → edit → import:

   ```bash
   gcloud compute url-maps export YOUR_URL_MAP --destination url-map.yaml
   # edit url-map.yaml
   gcloud compute url-maps import YOUR_URL_MAP --source url-map.yaml
   ```

5. **Wait** for the URL map update to propagate (Google notes this can take a short time).

## When this triggers

Custom error responses apply when the **load balancer** surfaces matching HTTP error codes from your **backend service** (e.g. all backends unhealthy, connection failures, or returned 502/503). It does **not** replace your app’s own JSON error bodies for successful HTTP 200 responses.

## “Index of build/” style listings

That usually means the **origin** is exposing a directory index (wrong web root, or listing enabled), not the load balancer itself. Fix the **origin** (document root = `frontend/build`, disable autoindex) as in `DOMAIN_SETUP.md`. If the origin is **Cloud Storage**, avoid listing public objects as a “site”; use a **backend bucket** with appropriate object layout and URL map paths instead of browsing the bucket URL directly.

## Scope

Custom error responses for this mechanism are supported for **global external Application Load Balancers** as described in Google’s docs; regional or other products may differ—confirm against the linked documentation for your exact resource types.
