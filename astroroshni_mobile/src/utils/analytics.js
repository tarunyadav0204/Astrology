import { Platform } from 'react-native';

const GA_MEASUREMENT_ID = 'G-M0C9B8LGMR';

// Inject gtag script (web-like approach)
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

export const trackScreenView = (screenName) => {
  console.log('📊 Screen:', screenName);
  gtag('event', 'screen_view', { screen_name: screenName });
};

export const trackEvent = (eventName, params = {}) => {
  console.log('📊 Event:', eventName, params);
  gtag('event', eventName, params);
};

// Astrology-specific event tracking
export const trackAstrologyEvent = {
  chartGenerated: (chartType) => trackEvent('chart_generated', { chart_type: chartType }),
  horoscopeViewed: (zodiacSign, period) => trackEvent('horoscope_viewed', { zodiac_sign: zodiacSign, period }),
  dashaViewed: (dashaType) => trackEvent('dasha_viewed', { dasha_type: dashaType }),
  transitViewed: (date) => trackEvent('transit_viewed', { date }),
  analysisRequested: (analysisType) => trackEvent('analysis_requested', { analysis_type: analysisType }),
  chatMessageSent: (messageType) => trackEvent('chat_message_sent', { message_type: messageType }),
  creditPurchased: (amount) => trackEvent('credit_purchased', { amount, currency: 'INR' }),
  userRegistered: () => trackEvent('sign_up', { method: 'mobile' }),
  userLoggedIn: () => trackEvent('login', { method: 'mobile' }),
  pdfGenerated: (reportType) => trackEvent('pdf_generated', { report_type: reportType }),
  panchangViewed: (date) => trackEvent('panchang_viewed', { date }),
};

export const setUserProperties = async (properties) => {
  console.log('User properties:', properties);
};

export const setUserId = async (userId) => {
  console.log('User ID:', userId);
};
