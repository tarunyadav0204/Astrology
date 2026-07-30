/**
 * Meta Pixel (fbq) for the marketing / CRA website (astroroshni.com, not /mobile/).
 * PWA uses astroroshni_mobile/src/services/metaPixel.js with ar_surface=pwa.
 * Native apps use the Facebook App Events SDK (separate "App" integration in Events Manager).
 */
export const META_PIXEL_ID =
  (typeof process !== 'undefined' && process.env?.REACT_APP_META_PIXEL_ID
    ? String(process.env.REACT_APP_META_PIXEL_ID).trim()
    : '') || '1900398174159684';

/** Distinguishes website vs /mobile PWA in Pixel payloads (filter in Events Manager / Ads). */
export const META_SURFACE = 'website';

let initStarted = false;

function canRun() {
  return typeof window !== 'undefined' && typeof document !== 'undefined' && !!META_PIXEL_ID;
}

function getFbq() {
  if (!canRun()) return null;
  return typeof window.fbq === 'function' ? window.fbq : null;
}

function withSurface(params = {}) {
  return {
    ar_surface: META_SURFACE,
    ...params,
  };
}

function sanitizePixelParams(params = {}) {
  const out = {};
  Object.entries(params || {}).forEach(([key, value]) => {
    if (value == null) return;
    if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') {
      out[key] = value;
    } else {
      out[key] = String(value);
    }
  });
  return out;
}

const STANDARD_EVENTS = new Set([
  'PageView',
  'ViewContent',
  'Search',
  'AddToCart',
  'AddToWishlist',
  'InitiateCheckout',
  'AddPaymentInfo',
  'Purchase',
  'Lead',
  'CompleteRegistration',
  'Contact',
  'CustomizeProduct',
  'Donate',
  'FindLocation',
  'Schedule',
  'StartTrial',
  'SubmitApplication',
  'Subscribe',
]);

/** Events Manager has no URL filter — these custom names show as separate rows. */
function surfaceEventName(eventName) {
  const prefix = META_SURFACE === 'website' ? 'Website' : 'PWA';
  return `${prefix}_${eventName}`;
}

/**
 * Inject Meta Pixel once and fire PageView tagged as website.
 */
export function initMetaPixel() {
  if (!canRun()) return;
  if (initStarted || window.__AR_META_PIXEL_WEBSITE_INIT__) {
    initStarted = true;
    return;
  }
  initStarted = true;

  try {
    if (!window.fbq) {
      // eslint-disable-next-line no-unused-expressions
      !(function (f, b, e, v, n, t, s) {
        if (f.fbq) return;
        n = f.fbq = function () {
          n.callMethod ? n.callMethod.apply(n, arguments) : n.queue.push(arguments);
        };
        if (!f._fbq) f._fbq = n;
        n.push = n;
        n.loaded = true;
        n.version = '2.0';
        n.queue = [];
        t = b.createElement(e);
        t.async = true;
        t.src = v;
        s = b.getElementsByTagName(e)[0];
        s.parentNode.insertBefore(t, s);
      })(window, document, 'script', 'https://connect.facebook.net/en_US/fbevents.js');
    }

    window.fbq('init', META_PIXEL_ID);
    // Standard PageView (ads) + surface-named custom event (Events Manager filter).
    window.fbq('track', 'PageView', withSurface({ content_name: 'website_shell' }));
    window.fbq('trackCustom', surfaceEventName('PageView'), withSurface({ content_name: 'website_shell' }));
    window.__AR_META_PIXEL_WEBSITE_INIT__ = true;
  } catch (e) {
    if (process.env.NODE_ENV === 'development') {
      // eslint-disable-next-line no-console
      console.warn('[MetaPixel:website] init failed', e?.message || e);
    }
  }
}

export function trackMetaPixelEvent(eventName, params = {}, options = {}) {
  if (!canRun() || !eventName) return;
  initMetaPixel();
  const fbq = getFbq();
  if (!fbq) return;

  const payload = sanitizePixelParams(withSurface(params));
  const labeled = surfaceEventName(eventName);
  try {
    if (options.eventID) {
      fbq('trackCustom', eventName, payload, { eventID: options.eventID });
      fbq('trackCustom', labeled, payload, { eventID: `${options.eventID}_${META_SURFACE}` });
    } else if (STANDARD_EVENTS.has(eventName)) {
      fbq('track', eventName, payload);
      fbq('trackCustom', labeled, payload);
    } else {
      fbq('trackCustom', eventName, payload);
      // Already custom — still emit surface-prefixed twin for the Events list.
      if (eventName !== labeled) {
        fbq('trackCustom', labeled, payload);
      }
    }
  } catch (e) {
    if (process.env.NODE_ENV === 'development') {
      // eslint-disable-next-line no-console
      console.warn('[MetaPixel:website] track failed', eventName, e?.message || e);
    }
  }
}

export function trackMetaPixelPageView(path, title) {
  trackMetaPixelEvent('PageView', {
    content_name: title || document.title || 'page',
    content_ids: [String(path || window.location?.pathname || '/')],
  });
}
