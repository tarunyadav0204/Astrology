import { gtag } from 'gtag';

// Replace with your actual Google Analytics 4 Measurement ID
const GA_MEASUREMENT_ID = process.env.REACT_APP_GA_MEASUREMENT_ID || 'G-XXXXXXXXXX';

// Initialize Google Analytics
export const initGA = () => {
  if (typeof window !== 'undefined' && GA_MEASUREMENT_ID !== 'G-XXXXXXXXXX') {
    gtag('config', GA_MEASUREMENT_ID, {
      page_title: document.title,
      page_location: window.location.href,
    });
  }
};

// Track page views
export const trackPageView = (path, title) => {
  if (typeof window !== 'undefined' && GA_MEASUREMENT_ID !== 'G-XXXXXXXXXX') {
    gtag('config', GA_MEASUREMENT_ID, {
      page_path: path,
      page_title: title,
    });
  }
};

// Track custom events
export const trackEvent = (action, category, label, value) => {
  if (typeof window !== 'undefined' && GA_MEASUREMENT_ID !== 'G-XXXXXXXXXX') {
    gtag('event', action, {
      event_category: category,
      event_label: label,
      value: value,
    });
  }
};

// Astrology-specific event tracking
export const trackAstrologyEvent = {
  chartGenerated: (chartType) => trackEvent('chart_generated', 'astrology', chartType),
  horoscopeViewed: (zodiacSign, period) => trackEvent('horoscope_viewed', 'astrology', `${zodiacSign}_${period}`),
  muhuratSearched: (muhuratType) => trackEvent('muhurat_searched', 'astrology', muhuratType),
  panchangViewed: (date) => trackEvent('panchang_viewed', 'astrology', date),
  analysisRequested: (analysisType) => trackEvent('analysis_requested', 'astrology', analysisType),
  userRegistered: () => trackEvent('sign_up', 'engagement', 'user_registration'),
  userLoggedIn: () => trackEvent('login', 'engagement', 'user_login'),
  consultationRequested: () => trackEvent('consultation_requested', 'conversion', 'astrologer_consultation'),
};