/** Web routes that work without sign-in (no redirect on expired session). */
export const PUBLIC_APP_PATH_PREFIXES = [
  '/panchang',
  '/monthly-panchang',
  '/muhurat-finder',
  '/festivals',
  '/nakshatras',
  '/nakshatra',
  '/horoscope',
  '/karma-analysis',
  '/blog',
  '/contact',
  '/about',
  '/policy',
  '/terms',
  '/calendar-2026',
  '/beginners-guide',
  '/advanced-courses',
  '/myths-vs-reality',
  '/lesson',
  '/kundli-matching',
  '/chat',
  '/tools/ashtakavarga',
];

export const isPublicAppPath = (pathname) => {
  if (!pathname || pathname === '/') return true;
  return PUBLIC_APP_PATH_PREFIXES.some(
    (prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`)
  );
};

export const APP_CONFIG = {
  api: {
    dev: 'http://localhost:8001',
    test: 'https://test.astroroshni.com',
    // Fallback when hostname is not the public site (e.g. raw LB IP). AstroRoshni web app uses window origin in config.js.
    prod: 'https://astroroshni.com',
    timeout: 30000,
    retries: 3
  },
  form: {
    dateFormat: 'YYYY-MM-DD',
    timeFormat: '12h',
    dateRange: {
      min: '1900-01-01',
      max: '2100-12-31'
    },
    validation: {
      nameMinLength: 2,
      nameMaxLength: 50,
      placeMinLength: 2
    }
  },
  ui: {
    breakpoints: {
      mobile: '768px',
      tablet: '1024px',
      desktop: '1200px'
    },
    toast: {
      duration: 4000,
      position: 'top-right'
    }
  },
  location: {
    geocodingService: 'nominatim',
    debounceMs: 300,
    minSearchLength: 3
  },
  /**
   * Homepage WhatsApp promo (9:16 banner modal).
   * Uses compressed WebP + JPEG (see `public/images/README-WHATSAPP-BANNER.md`); do not ship multi‑MB PNGs as the primary URL.
   * Optional click-through: set REACT_APP_WHATSAPP_CHAT_URL (e.g. https://wa.me/15551234567) in `.env`.
   */
  whatsappHomeBanner: {
    imageWebpSrcSet:
      '/images/whatsapp-home-banner-480.webp 480w, /images/whatsapp-home-banner-720.webp 720w',
    imageFallback: '/images/whatsapp-home-banner-720.jpg',
    /** Matches modal frame: ~92vw on phones, ~380–420px on larger screens */
    imageSizes: '(min-width: 769px) 380px, min(420px, 92vw)',
    ctaHref: (typeof process !== 'undefined' && process.env.REACT_APP_WHATSAPP_CHAT_URL) || '',
    storageDismissKey: 'ar_home_whatsapp_banner_dismissed_v1',
  },
};