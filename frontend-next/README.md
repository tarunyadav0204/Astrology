# SEO pages (Next.js static export)

Pre-rendered SEO pages for `/karma-analysis`, `/kundli-matching`, and `/chat`, merged into the CRA production build.

`/reports` is **not** Next — it uses CRA + Puppeteer prerender like `/wealth-analysis`.

## Local dev

**Option A — CRA (recommended, same as rest of the site):**

```bash
cd frontend
npm start
# http://localhost:3001/karma-analysis
```

CRA serves the interactive app routes during local development.

**Option B — Next only:**

```bash
cd frontend-next
npm install
npm run dev   # http://localhost:3002/karma-analysis, /kundli-matching, /chat
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

Serve from `frontend/build` with **`npm run serve:build`** (custom `scripts/serve-build.mjs` — `/` is the CRA app; `/karma-analysis`, `/kundli-matching`, and `/chat` serve Next SEO HTML unless `?app=1`, then CRA).

For local login/API testing, keep the backend running on `http://127.0.0.1:8001`. To use a different backend:

```bash
cd frontend
API_TARGET=http://127.0.0.1:8001 npm run serve:build
```

For SEO HTML check: open `/karma-analysis`, `/kundli-matching`, or `/chat` in incognito — Network should show `/_next/static/...`. In-app links use React Router (CRA route).

## Homepage (`/`)

**Users** always get the **CRA** marketing homepage at `/` (your `NavigationHeader`, sections, widgets, and layout). SEO for that URL comes from CRA’s existing `react-helmet-async` + JSON-LD in `AstroRoshniHomepage`.

The Next export still builds **`home.html`** in `frontend/build` as an **optional** crawlable snapshot (e.g. audits, `href` from sitemap, or future nginx rules). It is **not** the default document for `/` in `serve-build.mjs` or `serve.json` so the live site matches the app you designed.

## CRA integration

- The public `/karma-analysis`, `/kundli-matching`, and `/chat` URLs are SEO static pages in production.
- CRA still registers the same paths as interactive fallback/app views; production app links use `?app=1`.
- Public SEO links use the clean URL so crawlers and users get the static page.
- Auth/chart data uses the same `localStorage` keys as the main app (`token`, `user`, `astrology_birth_data`, `astrology_chart_data`).
