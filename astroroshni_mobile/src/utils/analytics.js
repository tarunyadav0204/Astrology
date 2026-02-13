import { Platform } from 'react-native';
import axios from 'axios';

const GA_MEASUREMENT_ID = 'G-M0C9B8LGMR';
const API_SECRET = 'TY4n2VL_R6qWdmqGc5rGZg'; // Get from GA4 Admin > Data Streams > Measurement Protocol API secrets

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

const sendToGA4 = async (eventName, params = {}) => {
  if (Platform.OS === 'web') return;
  
  try {
    // Get userName from AsyncStorage if available
    let userName = null;
    try {
      const AsyncStorage = require('@react-native-async-storage/async-storage').default;
      const userDataStr = await AsyncStorage.getItem('userData');
      if (userDataStr) {
        const userData = JSON.parse(userDataStr);
        userName = userData.name || userData.username || null;
      }
    } catch (e) {
      console.log('Could not retrieve userName from storage');
    }
    
    const payload = {
      client_id: `mobile_${Platform.OS}_${Date.now()}`,
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

export const trackScreenView = (screenName) => {
  console.log('📊 Screen:', screenName);
  if (Platform.OS === 'web') {
    gtag('event', 'screen_view', { screen_name: screenName });
  } else {
    sendToGA4('screen_view', { screen_name: screenName });
  }
};

export const trackEvent = (eventName, params = {}) => {
  console.log('📊 Event:', eventName, params);
  if (Platform.OS === 'web') {
    gtag('event', eventName, params);
  } else {
    sendToGA4(eventName, params);
  }
};

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
  languageChanged: (language) => trackEvent('language_changed', { language }),
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
