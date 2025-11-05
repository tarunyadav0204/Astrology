import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';

export const useAnalytics = () => {
  const location = useLocation();

  useEffect(() => {
    if (typeof window !== 'undefined' && window.gtag) {
      const measurementId = process.env.REACT_APP_GA_MEASUREMENT_ID;
      if (measurementId && measurementId !== 'G-XXXXXXXXXX') {
        window.gtag('config', measurementId, {
          page_path: location.pathname + location.search,
          page_title: document.title,
        });
      }
    }
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
  };

  return { trackEvent };
};