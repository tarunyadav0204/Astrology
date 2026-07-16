# Expo Web on astroroshni.com (mobile UA)

## Goal

Phone browsers hitting `https://astroroshni.com` get the **Expo Web** shell (same UI as `astroroshni_mobile`). Desktop browsers and crawlers keep the CRA site.

## Build locally

```bash
cd astroroshni_mobile
npm ci
npm run web:export          # → dist-web/
bash scripts/postexport-web.sh dist-web
npx serve dist-web -l 8081
```

Dev (hot reload):

```bash
npm run web                 # expo start --web
```

Route smoke (Chrome required):

```bash
SMOKE_URL=http://127.0.0.1:8081 node scripts/smoke-expo-web-routes.mjs
```

## Dual SPA layout in the site bucket

| Object | Audience |
|--------|----------|
| `index.html` | CRA desktop + bots |
| `expo-index.html` | Expo Web mobile shell |
| `/static/**`, `/_next/**` | CRA assets |
| `/_expo/**` | Expo Web assets |

Publish Expo without wiping CRA:

```bash
bash astroroshni_mobile/scripts/publish-web-to-gcs.sh "$GCP_FRONTEND_SITE_BUCKET" astroroshni_mobile/dist-web
```

## UA edge router

Service: [`infra/ua-edge-router`](../infra/ua-edge-router)

Rules:

1. Bot UA → CRA `index.html`
2. Mobile UA → Expo `expo-index.html`
3. Desktop → CRA `index.html`
4. `?force_web=1` / cookie `force_web=1` → CRA
5. `?force_app=1` / cookie `force_app=1` → Expo

`/api/*` must continue to hit the backend MIG (LB URL map), not this router.

Deploy example (Cloud Run):

```bash
gcloud run deploy astroroshni-ua-edge \
  --source infra/ua-edge-router \
  --region asia-south2 \
  --allow-unauthenticated \
  --set-env-vars "SITE_BUCKET_BASE_URL=https://storage.googleapis.com/${GCP_FRONTEND_SITE_BUCKET}"
```

Then point the HTTPS load balancer’s default frontend path at this Cloud Run service (keep `/api/*` on the API backend).

## CI

[`.github/workflows/deploy.yml`](../.github/workflows/deploy.yml) detects `astroroshni_mobile/**` and `infra/ua-edge-router/**` as `mobile_web_required`, builds `expo export`, publishes `mobile-web-build-*.tgz`, and rsyncs Expo assets into `GCP_FRONTEND_SITE_BUCKET`.

## Platform shims

Native-only modules are stubbed on web via Metro (`astroroshni_mobile/metro.config.js`) and `.web.js` files:

- IAP / Razorpay native → Razorpay Checkout.js (`src/platform/payments.web.js`)
- Push / store review → no-op
- WebView → iframe
- Speech → Web Speech API
- Sentry RN → soft mobile-web bootstrap

## Escape hatches (production)

- Desktop on phone UA: `https://astroroshni.com/?force_web=1`
- Expo on desktop: `https://astroroshni.com/?force_app=1`
