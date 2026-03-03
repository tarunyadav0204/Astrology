import { useEffect } from 'react';
import { trackScreenView, trackEvent } from '../utils/analytics';

export const useAnalytics = (screenName) => {
  useEffect(() => {
    if (screenName) {
      trackScreenView(screenName);
    }
  }, [screenName]);

  return { trackEvent };
};
