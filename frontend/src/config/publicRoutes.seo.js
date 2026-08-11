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

const LESSON_SEO = {
  1: ['What is Astrology?', 'Understand astrology as an interpretive tradition and distinguish Vedic chart interpretation from astronomy.'],
  2: ['The Zodiac Signs', 'Learn the twelve zodiac signs through element, modality, and planetary rulership.'],
  3: ['Understanding Your Birth Chart', 'Learn how ascendant, houses, signs, planets, and house lords combine in a Vedic birth chart.'],
  4: ['The Planets and Their Meanings', 'Meet the nine Vedic grahas and learn how planetary roles change through lordship, dignity, and placement.'],
  5: ['The 12 Houses Explained', 'Understand the twelve Vedic astrology houses and the areas of life each bhava represents.'],
  6: ['Aspects and Conjunctions', 'Learn how conjunctions and Parashari planetary aspects connect planets and houses.'],
  7: ['Nakshatras — Lunar Mansions', 'Understand the twenty-seven nakshatras, their lords, padas, symbols, and role in Vedic astrology.'],
  8: ['Dasha Systems', 'Learn how Vimshottari dasha periods organise astrological timing and activate natal chart promise.'],
};

const HOROSCOPE_PERIODS = ['daily', 'weekly', 'monthly', 'yearly'];
// Static GCS directory pages serve the trailing-slash URL as the canonical 200.
const DIRECTORY_CANONICAL_PATHS = new Set([
  '/about',
  '/blog',
  '/beginners-guide',
  '/contact',
  '/panchang',
  '/policy',
]);

/** Static public paths to prerender at build time (no auth). */
export function getPrerenderPaths({ year = new Date().getFullYear(), blogSlugs = [] } = {}) {
  const paths = [
    '/',
    '/ai-kundli-generator',
    '/charts-dashas',
    '/charts-dashas/activations',
    '/panchang',
    '/muhurat-finder',
    '/monthly-panchang',
    '/festivals',
    '/festivals/monthly',
    '/nakshatras',
    '/kundli-matching',
    '/karma-analysis',
    '/chat',
    '/reports',
    '/blog',
    '/about',
    '/contact',
    '/order-management',
    '/policy',
    '/terms',
    '/calendar-2026',
    '/beginners-guide',
    '/advanced-courses',
    '/myths-vs-reality',
    '/horoscope',
    '/ashtakavarga',
    '/astrovastu',
    '/life-events',
    '/marriage-analysis',
    '/career-guidance',
    '/subscription',
    '/health-analysis',
    '/wealth-analysis',
    '/education',
    '/progeny-analysis',
  ];

  Object.keys(LESSON_SEO).forEach((lessonId) => paths.push(`/lesson/${lessonId}`));

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
  { path: '/ai-kundli-generator', pageKey: 'birthChartCreation' },
  { path: '/birth-chart', pageKey: 'birthChartCreation' },
  { path: '/charts-dashas/activations', noIndex: true },
  { path: '/charts-dashas', pageKey: 'chartsDashasWorkspace' },
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
        path: `/nakshatra/${nakshatraName}/${canonicalYear}/`,
        title: `${titleName} Nakshatra ${canonicalYear} — Calendar & Predictions | AstroRoshni`,
        description: `${titleName} nakshatra yearly calendar, auspicious dates, and Vedic insights for ${canonicalYear}.`,
        keywords: `${nakshatraName} nakshatra, nakshatra calendar, vedic astrology, ${canonicalYear}`,
      });
    },
  },
  /** Short URL /nakshatra/ashwini → canonical year URL (matches sitemap). */
  {
    path: '/nakshatra/:nakshatraName',
    resolve: ({ nakshatraName }) => {
      const year = new Date().getFullYear();
      const name = String(nakshatraName || '').replace(/-/g, ' ');
      const titleName = name.replace(/\b\w/g, (c) => c.toUpperCase());
      return generatePageSEO('nakshatraDetail', {
        path: `/nakshatra/${nakshatraName}/${year}/`,
        title: `${titleName} Nakshatra ${year} — Calendar & Predictions | AstroRoshni`,
        description: `${titleName} nakshatra yearly calendar, auspicious dates, and Vedic insights for ${year}.`,
        keywords: `${nakshatraName} nakshatra, nakshatra calendar, vedic astrology, ${year}`,
      });
    },
  },
  { path: '/kundli-matching', pageKey: 'kundliMatching' },
  { path: '/reports', pageKey: 'reportsStudio' },
  { path: '/karma-analysis', pageKey: 'karmaAnalysis' },
  { path: '/chat', pageKey: 'chatAstrologer' },
  { path: '/blog', pageKey: 'blogList' },
  {
    path: '/blog/:slug',
    resolve: ({ slug }) =>
      generatePageSEO('blogPost', {
        path: `/blog/${slug}/`,
        title: 'Blog | AstroRoshni',
        description: 'Vedic astrology articles, guides, and insights from AstroRoshni.',
      }),
  },
  { path: '/about', pageKey: 'about' },
  { path: '/contact', pageKey: 'contact' },
  {
    path: '/order-management',
    noIndex: true,
    resolve: () => ({
      canonical: `${SITE_URL}/order-management/`,
    }),
  },
  { path: '/policy', pageKey: 'policy' },
  { path: '/terms', pageKey: 'terms' },
  {
    path: '/account/delete',
    noIndex: true,
    resolve: () => ({
      title: 'Delete Your AstroRoshni Account',
      description:
        'Permanently delete your AstroRoshni account and associated personal data, or learn how to remove individual conversations.',
      canonical: `${SITE_URL}/account/delete/`,
    }),
  },
  { path: '/calendar-2026', pageKey: 'calendar2026' },
  { path: '/beginners-guide', pageKey: 'beginnersGuide' },
  {
    path: '/lesson/:lessonId',
    resolve: ({ lessonId }) => {
      const lesson = LESSON_SEO[lessonId];
      if (!lesson) return { noIndex: true };
      return generatePageSEO('beginnersGuide', {
        path: `/lesson/${lessonId}/`,
        title: `${lesson[0]} — Vedic Astrology Lesson ${lessonId} | AstroRoshni`,
        description: lesson[1],
        keywords: `${lesson[0]}, learn vedic astrology, jyotish lesson, astrology for beginners`,
      });
    },
  },
  { path: '/advanced-courses', pageKey: 'advancedCourses' },
  { path: '/myths-vs-reality', pageKey: 'mythsVsReality' },
  { path: '/horoscope/:period', pageKey: 'dailyHoroscope' },
  { path: '/horoscope', pageKey: 'dailyHoroscope' },
  { path: '/ashtakavarga', pageKey: 'ashtakavarga' },
  { path: '/tools/ashtakavarga', noIndex: true },
  { path: '/astrovastu', pageKey: 'astroVastu' },
  { path: '/marriage-analysis', pageKey: 'marriageAnalysis' },
  { path: '/career-guidance', pageKey: 'careerGuidance' },
  { path: '/subscription', pageKey: 'subscription' },
  { path: '/health-analysis', pageKey: 'healthAnalysis' },
  { path: '/wealth-analysis', pageKey: 'wealthAnalysis' },
  { path: '/life-events', pageKey: 'lifeEvents' },
  { path: '/education', pageKey: 'educationAnalysis' },
  { path: '/progeny-analysis', pageKey: 'progenyAnalysis' },
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
      const canonicalPath = DIRECTORY_CANONICAL_PATHS.has(path) ? `${path}/` : path;
      const data = generatePageSEO(rule.pageKey, { path: canonicalPath });
      return { ...data, noIndex: rule.noIndex };
    }
    return { noIndex: rule.noIndex };
  }

  return null;
}

export { SITE_URL };
