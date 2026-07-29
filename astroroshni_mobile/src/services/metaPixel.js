/**
 * Meta Pixel (fbq) for the Expo Web / PWA shell served at /mobile/.
 * Native iOS/Android keep using react-native-fbsdk-next App Events.
 */
import { Platform } from 'react-native';
import Constants from 'expo-constants';

export const META_PIXEL_ID =
  (Constants.expoConfig?.extra?.metaPixelId && String(Constants.expoConfig.extra.metaPixelId).trim()) ||
  (typeof process !== 'undefined' && process.env?.EXPO_PUBLIC_META_PIXEL_ID
    ? String(process.env.EXPO_PUBLIC_META_PIXEL_ID).trim()
    : '') ||
  '1900398174159684';

let initStarted = false;

function isWebPwa() {
  return Platform.OS === 'web' && typeof window !== 'undefined' && typeof document !== 'undefined';
}

/** Prefer production /mobile shell; allow local Expo web (/) for testing. */
export function shouldTrackMetaPixel() {
  if (!isWebPwa() || !META_PIXEL_ID) return false;
  const path = String(window.location?.pathname || '');
  if (__DEV__) return true;
  return path === '/mobile' || path.startsWith('/mobile/') || path === '/';
}

function getFbq() {
  if (!isWebPwa()) return null;
  return typeof window.fbq === 'function' ? window.fbq : null;
}

/**
 * Inject Meta Pixel base code once and fire PageView (Opening the URL).
 */
export function initMetaPixel() {
  if (!shouldTrackMetaPixel()) return;
  // Static HTML from postexport-web.sh may have already booted fbq + PageView.
  if (initStarted || (typeof window !== 'undefined' && window.__AR_META_PIXEL_INIT__)) {
    initStarted = true;
    return;
  }
  initStarted = true;

  try {
    if (!window.fbq) {
      // Standard Meta Pixel snippet (queue stub before fbevents.js loads).
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
    window.fbq('track', 'PageView');
    if (typeof window !== 'undefined') {
      window.__AR_META_PIXEL_INIT__ = true;
    }
    if (__DEV__) {
      console.log('[MetaPixel] init + PageView', META_PIXEL_ID);
    }
  } catch (e) {
    if (__DEV__) console.warn('[MetaPixel] init failed', e?.message || e);
  }
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

/**
 * Fire a standard or custom Pixel event.
 * @param {string} eventName Meta event name (Purchase, CompleteRegistration, Login, ChatMessage, …)
 * @param {object} [params]
 * @param {{ eventID?: string }} [options]
 */
export function trackMetaPixelEvent(eventName, params = {}, options = {}) {
  if (!shouldTrackMetaPixel()) return;
  initMetaPixel();
  const fbq = getFbq();
  if (!fbq || !eventName) return;

  const payload = sanitizePixelParams(params);
  try {
    if (options.eventID) {
      fbq('trackCustom', eventName, payload, { eventID: options.eventID });
    } else if (
      [
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
      ].includes(eventName)
    ) {
      fbq('track', eventName, payload);
    } else {
      fbq('trackCustom', eventName, payload);
    }
    if (__DEV__) console.log('[MetaPixel]', eventName, payload);
  } catch (e) {
    if (__DEV__) console.warn('[MetaPixel] track failed', eventName, e?.message || e);
  }
}

export function trackMetaPixelPurchase({ value, currency = 'INR', content_ids, content_type, contents, num_items } = {}) {
  const params = {
    value: Number(value) || 0,
    currency: currency || 'INR',
  };
  if (content_ids) params.content_ids = Array.isArray(content_ids) ? content_ids : [String(content_ids)];
  if (content_type) params.content_type = content_type;
  if (contents) params.contents = contents;
  if (num_items != null) params.num_items = num_items;
  trackMetaPixelEvent('Purchase', params);
}

/** Map internal MetaStandardEvent keys → Pixel standard/custom names. */
export const META_PIXEL_STANDARD_MAP = {
  meta_contact: 'Contact',
  meta_search: 'Search',
  sign_up: 'CompleteRegistration',
  meta_view_content: 'ViewContent',
  meta_subscribe: 'Subscribe',
  meta_initiate_checkout: 'InitiateCheckout',
  meta_start_trial: 'StartTrial',
  purchase: 'Purchase',
  meta_add_payment_info: 'AddPaymentInfo',
};

export function trackMetaPixelFromStandardKey(eventKey, params = {}) {
  const pixelName = META_PIXEL_STANDARD_MAP[eventKey] || eventKey;
  if (pixelName === 'Purchase') {
    trackMetaPixelPurchase({
      value: params.value ?? params.amount ?? params.valueToSum,
      currency: params.currency || 'INR',
      content_ids: params.content_id || params.contentId || params.productId,
      content_type: params.content_type || params.contentType || 'product',
    });
    return;
  }
  const payload = { ...params };
  if (pixelName === 'CompleteRegistration') {
    payload.status = true;
    payload.method = params.registration_method || params.method || 'mobile';
  }
  if (pixelName === 'InitiateCheckout' || pixelName === 'Subscribe' || pixelName === 'StartTrial') {
    if (params.value == null && params.amount != null) payload.value = params.amount;
    if (!payload.currency) payload.currency = 'INR';
  }
  trackMetaPixelEvent(pixelName, payload);
}
