/**
 * Central SEO metadata for public routes. Used by RouteSEO (fallback) and build-time prerender list.
 * Pages with their own SEOHead still override these via react-helmet-async (child wins).
 */
import { matchPath } from 'react-router-dom';
import { SEO_CONFIG, generatePageSEO } from './seo.config';

const { url: SITE_URL } = SEO_CONFIG.site;

/** 27 nakshatra slugs (must match backend/sitemap_routes.py). */
export const NAKSHATRA_SLUGS = [
  'ashwini', 'bharani', 'krittika', 'rohini', 'mrigashira', 'ardra', 'punarvasu', 'pushya',
  'ashlesha', 'magha', 'purva-phalguni', 'uttara-phalguni', 'hasta', 'chitra', 'swati',
  'vishakha', 'anuradha', 'jyeshtha', 'mula', 'purva-ashadha', 'uttara-ashadha', 'shravana',
  'dhanishta', 'shatabhisha', 'purva-bhadrapada', 'uttara-bhadrapada', 'revati',
];

const HOROSCOPE_PERIODS = ['daily', 'weekly', 'monthly'];

/** Static public paths to prerender at build time (no auth). */
export function getPrerenderPaths({ year = new Date().getFullYear(), blogSlugs = [] } = {}) {
  const paths = [
    '/',
    '/panchang',
    '/muhurat-finder',
    '/monthly-panchang',
    '/festivals',
    '/festivals/monthly',
    '/nakshatras',
    '/kundli-matching',
    '/karma-analysis',
    '/chat',
    '/blog',
    '/about',
    '/contact',
    '/policy',
    '/calendar-2026',
    '/beginners-guide',
    '/advanced-courses',
    '/myths-vs-reality',
    '/horoscope',
    '/tools/ashtakavarga',
    '/astrovastu',
    '/marriage-analysis',
    '/career-guidance',
    '/health-analysis',
    '/wealth-analysis',
  ];

  HOROSCOPE_PERIODS.forEach((p) => paths.push(`/horoscope/${p}`));
  NAKSHATRA_SLUGS.forEach((n) => paths.push(`/nakshatra/${n}/${year}`));
  blogSlugs.forEach((slug) => paths.push(`/blog/${slug}`));

  return [...new Set(paths)];
}

/**
 * Route patterns for react-router matchPath. First match wins.
 * @type {Array<{ path: string, pageKey?: string, noIndex?: boolean, resolve?: (params: object) => object }>}
 */
export const PUBLIC_ROUTE_SEO_RULES = [
  { path: '/', pageKey: 'home' },
  { path: '/panchang', pageKey: 'panchang' },
  { path: '/muhurat-finder', pageKey: 'muhuratFinder' },
  { path: '/monthly-panchang', pageKey: 'monthlyPanchang' },
  { path: '/festivals/monthly', pageKey: 'festivalsMonthly' },
  { path: '/festivals', pageKey: 'festivals' },
  { path: '/nakshatras', pageKey: 'nakshatrasList' },
  {
    path: '/nakshatra/:nakshatraName/:year',
    resolve: ({ nakshatraName, year }) => {
      const name = String(nakshatraName || '').replace(/-/g, ' ');
      const titleName = name.replace(/\b\w/g, (c) => c.toUpperCase());
      const yearNum = parseInt(year, 10);
      const currentYear = new Date().getFullYear();
      // Past-year URLs stay reachable but canonical points to current year (avoids duplicate clusters).
      const canonicalYear =
        Number.isFinite(yearNum) && yearNum < currentYear ? currentYear : yearNum || currentYear;
      return generatePageSEO('nakshatraDetail', {
        path: `/nakshatra/${nakshatraName}/${canonicalYear}`,
        title: `${titleName} Nakshatra ${canonicalYear} — Calendar & Predictions | AstroRoshni`,
        description: `${titleName} nakshatra yearly calendar, auspicious dates, and Vedic insights for ${canonicalYear}.`,
        keywords: `${nakshatraName} nakshatra, nakshatra calendar, vedic astrology, ${canonicalYear}`,
      });
    },
  },
  { path: '/kundli-matching', pageKey: 'kundliMatching' },
  { path: '/karma-analysis', pageKey: 'karmaAnalysis' },
  { path: '/chat', pageKey: 'chatAstrologer' },
  { path: '/blog', pageKey: 'blogList' },
  {
    path: '/blog/:slug',
    resolve: () =>
      generatePageSEO('blogPost', {
        path: '/blog',
        title: 'Blog | AstroRoshni',
        description: 'Vedic astrology articles, guides, and insights from AstroRoshni.',
      }),
  },
  { path: '/about', pageKey: 'about' },
  { path: '/contact', pageKey: 'contact' },
  { path: '/policy', pageKey: 'policy' },
  { path: '/calendar-2026', pageKey: 'calendar2026' },
  { path: '/beginners-guide', pageKey: 'beginnersGuide' },
  { path: '/advanced-courses', pageKey: 'advancedCourses' },
  { path: '/myths-vs-reality', pageKey: 'mythsVsReality' },
  { path: '/horoscope/:period', pageKey: 'dailyHoroscope' },
  { path: '/horoscope', pageKey: 'dailyHoroscope' },
  { path: '/tools/ashtakavarga', pageKey: 'ashtakavarga' },
  { path: '/astrovastu', pageKey: 'astroVastu' },
  { path: '/marriage-analysis', pageKey: 'marriageAnalysis' },
  { path: '/career-guidance', pageKey: 'careerGuidance' },
  { path: '/health-analysis', pageKey: 'healthAnalysis' },
  { path: '/wealth-analysis', pageKey: 'wealthAnalysis' },
  { path: '/life-events', pageKey: 'lifeEvents', noIndex: true },
  { path: '/education', pageKey: 'educationAnalysis', noIndex: true },
  { path: '/progeny-analysis', pageKey: 'progenyAnalysis', noIndex: true },
  { path: '/speech-chat', noIndex: true },
  { path: '/profile', noIndex: true },
  { path: '/admin/blog', noIndex: true },
];

/** Resolve SEO props for a pathname (used by RouteSEO). */
export function resolveSeoForPathname(pathname) {
  const path = pathname.split('?')[0] || '/';

  for (const rule of PUBLIC_ROUTE_SEO_RULES) {
    const match = matchPath({ path: rule.path, end: true }, path);
    if (!match) continue;

    if (rule.resolve) {
      const data = rule.resolve(match.params);
      return { ...data, noIndex: rule.noIndex };
    }
    if (rule.pageKey) {
      const data = generatePageSEO(rule.pageKey, { path });
      return { ...data, noIndex: rule.noIndex };
    }
    return { noIndex: rule.noIndex };
  }

  return null;
}

export { SITE_URL };
