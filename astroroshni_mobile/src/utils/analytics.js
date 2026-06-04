import { Platform } from 'react-native';
import axios from 'axios';
import { trackMobileJourneyEvent } from '../services/journeyTracker';
import {
  logFacebookEvent,
  logMetaAppEvent,
  MetaStandardEvent,
  setFacebookUserId,
  clearFacebookUserId,
} from '../services/facebookAnalytics';

export { MetaStandardEvent, logMetaAppEvent };

const GA_MEASUREMENT_ID = 'G-M0C9B8LGMR';
const API_SECRET = 'TY4n2VL_R6qWdmqGc5rGZg'; // Get from GA4 Admin > Data Streams > Measurement Protocol API secrets
const GA4_CLIENT_ID_KEY = 'astro_ga4_client_id_v1';
const ACQUISITION_INSTALLATION_ID_KEY = 'astro_installation_id_v1';

if (Platform.OS === 'web') {
  const script1 = document.createElement('script');
  script1.async = true;
  script1.src = `https://www.googletagmanager.com/gtag/js?id=${GA_MEASUREMENT_ID}`;
  document.head.appendChild(script1);

  const script2 = document.createElement('script');
  script2.innerHTML = `
    window.dataLayer = window.dataLayer || [];
    function gtag(){dataLayer.push(arguments);}
    gtag('js', new Date());
    gtag('config', '${GA_MEASUREMENT_ID}');
  `;
  document.head.appendChild(script2);
}

const gtag = (...args) => {
  if (Platform.OS === 'web' && window.gtag) {
    window.gtag(...args);
  }
};

function generateAnalyticsClientId() {
  if (typeof globalThis.crypto !== 'undefined' && typeof globalThis.crypto.randomUUID === 'function') {
    return `mobile_${Platform.OS}_${globalThis.crypto.randomUUID()}`;
  }
  return `mobile_${Platform.OS}_${Date.now()}_${Math.random().toString(16).slice(2)}`;
}

async function getStableGA4ClientId(AsyncStorage) {
  const installId = await AsyncStorage.getItem(ACQUISITION_INSTALLATION_ID_KEY);
  if (installId && String(installId).trim()) {
    return `mobile_${Platform.OS}_${String(installId).trim()}`;
  }

  const existing = await AsyncStorage.getItem(GA4_CLIENT_ID_KEY);
  if (existing && String(existing).trim()) return String(existing).trim();

  const id = generateAnalyticsClientId();
  await AsyncStorage.setItem(GA4_CLIENT_ID_KEY, id);
  return id;
}

const sendToGA4 = async (eventName, params = {}) => {
  if (Platform.OS === 'web') return;
  
  try {
    // Get stable client/user identity from AsyncStorage if available.
    const AsyncStorage = require('@react-native-async-storage/async-storage').default;
    const clientId = await getStableGA4ClientId(AsyncStorage);
    let userName = null;
    let userId = null;
    try {
      const userDataStr = await AsyncStorage.getItem('userData');
      if (userDataStr) {
        const userData = JSON.parse(userDataStr);
        userName = userData.name || userData.username || null;
        userId = userData.userid ?? userData.user_id ?? userData.id ?? null;
      }
    } catch (e) {
      console.log('Could not retrieve analytics user data from storage');
    }
    
    const payload = {
      client_id: clientId,
      ...(userId != null ? { user_id: String(userId) } : {}),
      user_properties: userName ? {
        user_name: { value: userName }
      } : undefined,
      events: [{
        name: eventName,
        params: {
          ...params,
          platform: Platform.OS,
          os_version: `${Platform.OS} ${Platform.Version || 'unknown'}`,
          engagement_time_msec: 100
        }
      }]
    };
    
    await axios.post(
      `https://www.google-analytics.com/mp/collect?measurement_id=${GA_MEASUREMENT_ID}&api_secret=${API_SECRET}`,
      payload,
      {
        headers: {
          'Content-Type': 'application/json'
        }
      }
    );
  } catch (error) {
    console.error('❌ GA4 tracking error:', error.response?.data || error.message);
  }
};

export const trackGA4EventOnly = (eventName, params = {}) => {
  console.log('📊 GA4 Event:', eventName, params);
  if (Platform.OS === 'web') {
    gtag('event', eventName, params);
  } else {
    return sendToGA4(eventName, params);
  }
  return Promise.resolve();
};

export const trackScreenView = (screenName, meta = {}) => {
  const contentId = meta.content_id || screenName;
  const contentType = meta.content_type || 'screen';
  console.log('📊 Screen:', screenName, { content_id: contentId, content_type: contentType });
  if (Platform.OS === 'web') {
    gtag('event', 'screen_view', {
      screen_name: screenName,
      content_id: contentId,
      content_type: contentType,
    });
  } else {
    sendToGA4('screen_view', {
      screen_name: screenName,
      content_id: contentId,
      content_type: contentType,
    });
    logMetaAppEvent(MetaStandardEvent.VIEW_CONTENT, {
      content_id: contentId,
      content_type: contentType,
    });
    trackMobileJourneyEvent('mobile_screen_view', {
      screen_name: screenName,
      resource_type: 'screen',
      resource_id: contentId,
      metadata: { content_type: contentType },
    });
  }
};

export const trackEvent = (eventName, params = {}) => {
  console.log('📊 Event:', eventName, params);
  if (Platform.OS === 'web') {
    gtag('event', eventName, params);
  } else {
    sendToGA4(eventName, params);
    // Meta standard events are dispatched via trackMetaStandard / logMetaAppEvent; avoid duplicate custom logs.
    if (!Object.values(MetaStandardEvent).includes(eventName)) {
      logFacebookEvent(eventName, params);
    }
    // Mirror every analytics event to mobile journey events.
    trackMobileJourneyEvent('mobile_action', {
      resource_type: 'event',
      resource_id: eventName,
      metadata: params || {},
    });
  }
};

const META_GA_EVENT_ALIAS = {
  [MetaStandardEvent.CONTACT]: 'contact',
  [MetaStandardEvent.SEARCH]: 'search',
  [MetaStandardEvent.COMPLETE_REGISTRATION]: 'sign_up',
  [MetaStandardEvent.VIEW_CONTENT]: 'view_content',
  [MetaStandardEvent.SUBSCRIBE]: 'subscribe',
  [MetaStandardEvent.INITIATE_CHECKOUT]: 'initiate_checkout',
  [MetaStandardEvent.START_TRIAL]: 'start_trial',
  [MetaStandardEvent.PURCHASE]: 'purchase',
  [MetaStandardEvent.ADD_PAYMENT_INFO]: 'add_payment_info',
};

/** Fire a Meta standard app event (+ GA4 + journey). Prefer for Events Manager checklist. */
export const trackMetaStandard = (eventKey, params = {}) => {
  const gaEventName = META_GA_EVENT_ALIAS[eventKey] || eventKey;
  console.log('📊 Meta standard:', eventKey, params);
  if (Platform.OS === 'web') {
    gtag('event', gaEventName, params);
  } else {
    sendToGA4(gaEventName, params);
    trackMobileJourneyEvent('mobile_action', {
      resource_type: 'meta_event',
      resource_id: gaEventName,
      metadata: params || {},
    });
    logMetaAppEvent(eventKey, params);
  }
};

export const trackAstrologyEvent = {
  chartGenerated: (chartType) => trackEvent('chart_generated', { chart_type: chartType }),
  horoscopeViewed: (zodiacSign, period) => trackEvent('horoscope_viewed', { zodiac_sign: zodiacSign, period }),
  dashaViewed: (dashaType) => trackEvent('dasha_viewed', { dasha_type: dashaType }),
  transitViewed: (date) => trackEvent('transit_viewed', { date }),
  analysisRequested: (analysisType) => trackEvent('analysis_requested', { analysis_type: analysisType }),
  chatMessageSent: (messageType) => trackEvent('chat_message_sent', { message_type: messageType }),
  creditPurchased: (amount, opts = {}) =>
    trackMetaStandard(MetaStandardEvent.PURCHASE, {
      amount,
      currency: opts.currency || 'INR',
      content_id: opts.content_id || opts.productId,
      content_type: opts.content_type || 'credits',
      ...opts,
    }),
  userRegistered: (method = 'mobile') =>
    trackMetaStandard(MetaStandardEvent.COMPLETE_REGISTRATION, {
      method,
      registration_method: method,
    }),
  userLoggedIn: () => trackEvent('login', { method: 'mobile' }),
  pdfGenerated: (reportType) => trackEvent('pdf_generated', { report_type: reportType }),
  panchangViewed: (date) => trackEvent('panchang_viewed', { date }),
  languageChanged: (language) => trackEvent('language_changed', { language }),
  contact: () => trackMetaStandard(MetaStandardEvent.CONTACT),
  search: (query, contentType = 'app') =>
    trackMetaStandard(MetaStandardEvent.SEARCH, {
      search_string: query,
      content_id: query,
      content_type: contentType,
    }),
  viewContent: (contentId, contentType) =>
    trackMetaStandard(MetaStandardEvent.VIEW_CONTENT, {
      content_id: contentId,
      content_type: contentType,
    }),
  initiateCheckout: (opts = {}) =>
    trackMetaStandard(MetaStandardEvent.INITIATE_CHECKOUT, {
      content_id: opts.content_id || opts.productId,
      content_type: opts.content_type || 'credits',
      currency: opts.currency || 'INR',
      value: opts.value ?? opts.amount,
      ...opts,
    }),
  subscribe: (opts = {}) =>
    trackMetaStandard(MetaStandardEvent.SUBSCRIBE, {
      content_id: opts.content_id || opts.productId,
      content_type: opts.content_type || 'subscription',
      currency: opts.currency || 'INR',
      value: opts.value ?? opts.amount,
      ...opts,
    }),
  startTrial: (opts = {}) =>
    trackMetaStandard(MetaStandardEvent.START_TRIAL, {
      content_id: opts.content_id || opts.productId,
      content_type: opts.content_type || 'subscription_trial',
      ...opts,
    }),
  addPaymentInfo: (success = true, opts = {}) =>
    trackMetaStandard(MetaStandardEvent.ADD_PAYMENT_INFO, { success, ...opts }),
};

export const setUserProperties = async (properties) => {
  console.log('User properties:', properties);
};

export const setUserName = async (userName) => {
  console.log('📊 Setting User Name:', userName);
  
  // Store userName in AsyncStorage for future events
  try {
    const AsyncStorage = require('@react-native-async-storage/async-storage').default;
    await AsyncStorage.setItem('userName', String(userName));
  } catch (e) {
    console.error('Failed to store userName:', e);
  }
  
  // Set user property in GA4 for web
  if (Platform.OS === 'web' && window.gtag) {
    gtag('set', 'user_properties', {
      user_name: userName
    });
  }
};

/** Link Meta App Events to your backend user id after login/register. */
export const setAnalyticsUserId = async (userId) => {
  if (userId != null && String(userId).trim()) {
    await setFacebookUserId(userId);
  } else {
    await clearFacebookUserId();
  }
};
