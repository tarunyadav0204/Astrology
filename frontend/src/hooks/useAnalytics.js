import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { initMetaPixel, trackMetaPixelEvent, trackMetaPixelPageView } from '../services/metaPixel';

export const useAnalytics = () => {
  const location = useLocation();

  useEffect(() => {
    initMetaPixel();
  }, []);

  useEffect(() => {
    const path = location.pathname + location.search;
    if (typeof window !== 'undefined' && window.gtag) {
      const measurementId = process.env.REACT_APP_GA_MEASUREMENT_ID;
      if (measurementId && measurementId !== 'G-XXXXXXXXXX') {
        window.gtag('config', measurementId, {
          page_path: path,
          page_title: document.title,
        });
      }
    }
    trackMetaPixelPageView(path, document.title);
  }, [location]);

  const trackEvent = (action, category, label, value) => {
    if (typeof window !== 'undefined' && window.gtag) {
      const measurementId = process.env.REACT_APP_GA_MEASUREMENT_ID;
      if (measurementId && measurementId !== 'G-XXXXXXXXXX') {
        window.gtag('event', action, {
          event_category: category,
          event_label: label,
          value: value,
        });
      }
    }

    // Mirror key engagement into Meta Pixel (tagged ar_surface=website).
    if (action === 'login' || action === 'user_logged_in' || label === 'user_login') {
      trackMetaPixelEvent('Login', { method: label || 'website', category });
    } else if (action === 'sign_up' || label === 'user_registration') {
      trackMetaPixelEvent('CompleteRegistration', { method: label || 'website', status: true });
    } else if (action === 'horoscope_viewed' || action === 'analysis_requested' || action === 'panchang_viewed') {
      trackMetaPixelEvent('ViewContent', {
        content_name: action,
        content_category: category || 'astrology',
        content_ids: [String(label || action)],
      });
    } else if (action === 'muhurat_searched' || action === 'horoscope_period_changed') {
      trackMetaPixelEvent('Search', {
        search_string: String(label || action),
        content_category: category || 'astrology',
      });
    }
  };

  return { trackEvent };
};
