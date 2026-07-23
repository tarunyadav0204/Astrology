# Expo Web at `/mobile` (CRA stays on `/`)

## Goal

| URL | Audience |
|-----|----------|
| `https://astroroshni.com/` | **CRA frontend** for everyone (desktop **and** phone browsers) |
| `https://astroroshni.com/mobile/` | **Expo Web** shell (same UI as `astroroshni_mobile`) |

There is **no** mobile-UA auto-switch on `/`. Phones keep the website unless they open `/mobile`.

## Build locally

```bash
cd astroroshni_mobile
npm ci
npm run web:export          # → dist-web/
bash scripts/postexport-web.sh dist-web
npx serve dist-web -l 8081  # local entry is still / (not /mobile)
```

Dev (hot reload):

```bash
npm run web                 # expo start --web → http://localhost:8081/
```

## Dual SPA layout in the site bucket

| Object | Audience |
|--------|----------|
| `index.html` | CRA (all devices on `/`) |
| `mobile/index.html` | Expo Web entry for `/mobile/` |
| `expo-index.html` | Same Expo HTML (debug / health check) |
| `/static/**`, `/_next/**` | CRA assets |
| `/_expo/**` | Expo Web assets (absolute paths from site root) |

Publish Expo without wiping CRA:

```bash
bash astroroshni_mobile/scripts/publish-web-to-gcs.sh "$GCP_FRONTEND_SITE_BUCKET" astroroshni_mobile/dist-web
```

After publish, these work from the GCS/CDN backend bucket:

- `https://astroroshni.com/mobile/` → Expo
- `https://astroroshni.com/mobile/index.html` → Expo
- `https://astroroshni.com/` → CRA (phones included)

## Path edge router (deep links under `/mobile/*`)

Service: [`infra/ua-edge-router`](../infra/ua-edge-router)

Rules:

1. `/mobile` and `/mobile/*` HTML → `mobile/index.html` (Expo SPA fallback)
2. All other HTML → `index.html` (CRA) — **including mobile phone UAs**
3. `?force_app=1` → redirect to `/mobile/`
4. `?force_web=1` under `/mobile` → CRA (escape hatch)

`/api/*` must continue to hit the backend MIG (LB URL map), not this router.

Deploy example (Cloud Run):

```bash
gcloud run deploy astroroshni-ua-edge \
  --source infra/ua-edge-router \
  --region asia-south2 \
  --allow-unauthenticated \
  --set-env-vars "SITE_BUCKET_BASE_URL=https://storage.googleapis.com/${GCP_FRONTEND_SITE_BUCKET}"
```

Then point the HTTPS load balancer’s **non-API** frontend path at this Cloud Run service (keep `/api/*` on the API backend).

Without the edge router, `/mobile/` and `/mobile/index.html` still work from the backend bucket; client deep links like `/mobile/credits` need the edge (or another SPA rewrite) for refresh.

## CI

[`.github/workflows/deploy.yml`](../.github/workflows/deploy.yml) detects `astroroshni_mobile/**` and `infra/ua-edge-router/**` as `mobile_web_required`, builds `expo export`, publishes `mobile-web-build-*.tgz`, and uploads `mobile/index.html` + `/_expo/**` into `GCP_FRONTEND_SITE_BUCKET`.

## Deploy checklist

1. Commit + push to `main` (or workflow_dispatch with `force_frontend_deploy`).
2. Confirm Actions job **`mobile_web`** ran.
3. Smoke:
   - Phone or desktop: `https://astroroshni.com/` → CRA
   - `https://astroroshni.com/mobile/` → Expo shell (`data-ar-shell="expo-web"` in HTML)
4. (Optional) Deploy / re-point UA edge router so `/mobile/credits` etc. SPA-fallback correctly.

## Add to Home Screen / PWA

**Only `/mobile/` is the installable app.** The CRA marketing site at `/` ships `display: "browser"` and `apple-mobile-web-app-capable=no` so browsers do not create a competing home-screen icon that launches `https://astroroshni.com/` (website) instead of `/mobile/`.

| Platform | How users save it | What we ship |
|----------|-------------------|--------------|
| **iOS Safari** | Share → **Add to Home Screen** from **`/mobile/` only** | Expo shell: `apple-mobile-web-app-*` meta, `apple-touch-icon`, in-app guide modal |
| **Android Chrome** | Chrome **⋮ → Install app** or **Add to Home screen** on **`/mobile/`** | Web manifest (`id`/`start_url`/`scope`: `/mobile/`) + `/mobile/sw.js` (we do **not** hijack `beforeinstallprompt`) |

Both open full-screen from the home icon when installed from `/mobile/`. If an old icon still opens the website, delete it and re-add from `https://astroroshni.com/mobile/`.

**Updates after deploy (no reinstall)**  
Each export writes `/mobile/version.json` + stamps `window.__AR_WEB_BUILD__`. On open/focus, the home-screen app fetches `version.json` with `cache: no-store` and **reloads itself** when the build id changes. Users should **not** need to delete the iOS home-screen icon for normal deploys—just reopen the app (or switch back to it).

**Android tips if Install is missing**
1. Open exactly `https://astroroshni.com/mobile/` (trailing slash) in **Chrome**, not an in-app browser.
2. If the Play Store app is already installed, Chrome often hides **Install app** — use **Add to Home screen** instead.
3. Wait a few seconds after load so the service worker can register, then check **⋮** again.

**Test after deploy:** open `https://astroroshni.com/mobile/` on a real phone (HTTPS required for Chrome install). Confirm `/mobile/version.json` shows the new build id.

## Platform shims

Native-only modules are stubbed on web via Metro (`astroroshni_mobile/metro.config.js`) and `.web.js` files:

- IAP / Razorpay native → Razorpay Checkout.js (`src/platform/payments.web.js`)
- Push / store review → no-op
- WebView → iframe
- Speech → Web Speech API
- Sentry RN → soft mobile-web bootstrap
