# AstroRoshni SEO Strategy

## Current state (CRA SPA)

The frontend is a **Create React App** single-page application. You already have:

- `react-helmet-async` + `SEOHead` on many marketing pages
- `SEO_CONFIG` / `generatePageSEO` in `frontend/src/config/seo.config.js`
- Dynamic sitemap at **`GET /sitemap.xml`** (FastAPI, `backend/sitemap_routes.py`)
- `robots.txt` pointing to the sitemap

**Why Google still sees “no SEO”:** crawlers receive `index.html` with an empty `<div id="root"></div>` until JavaScript runs. Meta tags set in React are invisible to crawlers that do not execute JS (and even Google may index the shell first).

## What we implemented (Phase 1 — no Next.js yet)

| Piece | Purpose |
|--------|---------|
| **Default meta in `public/index.html`** | Baseline title/description/OG for the homepage shell |
| **`RouteSEO`** | Per-route title, description, canonical, robots for all public URLs |
| **`publicRoutes.seo.js`** | Central route → SEO mapping + prerender path list |
| **`scripts/postbuild-seo.mjs`** | After `npm run build`: writes `build/sitemap.xml`, optionally **prerenders** HTML per route with Puppeteer |
| **Expanded backend sitemap** | All key tools, festivals, kundli matching, current-year nakshatras |
| **Deploy** | Build runs postbuild SEO; uses live API for sitemap + blog slugs when backend is up |

### Prerender

`serve -s build` serves `build/panchang/index.html` for `/panchang` when that file exists. Prerender fills each public route with full HTML including `<title>` and meta from Helmet.

- Install: `npm install` in `frontend/` (adds `puppeteer` devDependency)
- Skip on CI/server without Chrome: `PRERENDER=false npm run build`
- Sitemap-only: `npm run build:app && npm run build:seo`

### Nginx / production

Ensure **`/sitemap.xml`** is served as XML, not the SPA fallback:

```nginx
# Prefer static file from build/ (postbuild copies sitemap)
location = /sitemap.xml {
    root /path/to/repo/frontend/build;
    default_type application/xml;
}

# Or proxy to API (always up to date with new blog posts)
# location = /sitemap.xml {
#     proxy_pass http://127.0.0.1:8001/sitemap.xml;
# }
```

Submit in [Google Search Console](https://search.google.com/search-console): `https://astroroshni.com/sitemap.xml`

## Phase 2 — recommended next steps (1–2 weeks)

1. **Unique copy on every public page** — 300–600 words visible without login (Panchang, festivals, tools).
2. **Blog** — 2–4 posts/month; `BlogPost` already supports SEO fields.
3. **Core Web Vitals** — lazy-load homepage solar animation; code-split heavy routes.
4. **`hreflang`** if you add Hindi UI.
5. **Google Search Console** — monitor coverage, fix “Crawled – currently not indexed”.
6. **Structured data** — `FAQPage`, `BreadcrumbList`, `Article` on blogs (extend `SEOHead`).

## Phase 3 — Next.js (optional, 4–8 weeks)

Migrate **public/marketing routes only** to **Next.js App Router**:

| Route group | Rendering |
|-------------|-----------|
| `/`, `/panchang`, `/blog/*`, `/nakshatras`, tools | **SSG/ISR** — best SEO |
| `/chat`, `/dashboard`, profile | Stay CRA or **client-only** in Next |

**Why consider Next.js**

- True SSR/SSG without Puppeteer at build time
- Built-in metadata API, sitemap, robots
- Better performance scores → ranking signal

**Why not rush**

- Large app with auth, credits, chat, multi-domain routing
- Prerender + RouteSEO gets ~80% of SEO value faster

**Hybrid pattern (common):**

- `www.astroroshni.com` → Next.js marketing site
- `app.astroroshni.com` → existing CRA app for logged-in users

## Phase 4 — ongoing

- Track rankings for: `panchang today`, `kundli matching`, `guna milan`, `muhurat for marriage`
- Internal linking from homepage → tool pages (already partially done)
- Backlinks / guest posts on astrology sites

## Karma Analysis (`/karma-analysis`) — flagship SEO page

Served by **Next.js static export** (`frontend-next/`), merged into `frontend/build/karma-analysis/` on deploy. View source shows full H1, FAQ, and JSON-LD without waiting for React.

1. **Public landing (SSR HTML)** — `frontend-next/components/KarmaAnalysisLanding.jsx` + `lib/karmaSeoContent.js`
2. **Tool (`#karma-tool`)** — client component; uses same `localStorage` keys as CRA (`token`, `user`, `astrology_birth_data`, `astrology_chart_data`)

The public `/karma-analysis` URL is owned by the Next static export for SEO. CRA still has a `/karma-analysis` route as the interactive app fallback, and the production static server routes `/karma-analysis?app=1` to CRA `index.html`. Internal SEO links use `<a href="/karma-analysis">`; app/tool links use `/karma-analysis?app=1`.

Technical: Next `metadata` + `@graph` schema (WebPage, BreadcrumbList, WebApplication, FAQPage), sitemap priority **0.9**. Build: `frontend-next/README.md`.

After deploy: URL Inspection → Request indexing for `https://astroroshni.com/karma-analysis` → Rich Results Test (FAQ).

---

## Checklist after deploy

- [ ] `curl -I https://astroroshni.com/sitemap.xml` → `200` + `Content-Type: application/xml`
- [ ] View source on `/panchang` → see title + description in HTML (not only in JS)
- [ ] Search Console: submit sitemap, request indexing for `/panchang`, `/kundli-matching`
- [ ] Rich Results Test on homepage and one blog post
