# Karma analysis (Next.js static export)

Pre-rendered SEO page for `/karma-analysis`, merged into the CRA production build.

## Local dev

**Option A — CRA (recommended, same as rest of the site):**

```bash
cd frontend
npm start
# http://localhost:3001/karma-analysis
```

CRA serves the interactive app route during local development.

**Option B — Next only:**

```bash
cd frontend-next
npm install
npm run dev   # http://localhost:3002/karma-analysis
```

Optional API in dev (if not proxying `/api`):

```bash
echo 'NEXT_PUBLIC_API_BASE=http://localhost:8001' > .env.local
```

## Production build (with CRA)

```bash
cd frontend
npm run build
cd ../frontend-next
npm install
npm run build
node scripts/copy-to-cra-build.mjs
```

`deploy.sh` runs this automatically after the CRA build when `frontend-next/` exists.

Serve from `frontend/build` with **`npm run serve:build`** (custom `scripts/serve-build.mjs` — serves `karma-analysis.html` for `/karma-analysis`, and CRA `index.html` for `/karma-analysis?app=1`).

For local login/API testing, keep the backend running on `http://127.0.0.1:8001`. To use a different backend:

```bash
cd frontend
API_TARGET=http://127.0.0.1:8001 npm run serve:build
```

For SEO HTML check: open `/karma-analysis` in incognito — Network should show `/_next/static/...`. In-app links use React Router (CRA route).

## CRA integration

- The public `/karma-analysis` URL is the SEO static page in production.
- CRA still registers `/karma-analysis` as the interactive fallback/app view; production app links use `/karma-analysis?app=1`.
- Public links to karma use `<a href="/karma-analysis">` so crawlers and users get the static page.
- Auth/chart data uses the same `localStorage` keys as the main app (`token`, `user`, `astrology_birth_data`, `astrology_chart_data`).
