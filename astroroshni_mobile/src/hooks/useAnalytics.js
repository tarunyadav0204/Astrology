import { useCallback, useRef } from 'react';
import { useFocusEffect } from '@react-navigation/native';
import { trackScreenView, trackEvent } from '../utils/analytics';
import { trackMobileJourneyEvent } from '../services/journeyTracker';

export const useAnalytics = (screenName) => {
  const startMsRef = useRef(null);
  const screenRef = useRef(screenName);
  screenRef.current = screenName;

  useFocusEffect(
    useCallback(() => {
      if (!screenRef.current) return () => {};
      const screen = screenRef.current;
      const startedAt = Date.now();
      startMsRef.current = startedAt;

      // Existing GA tracking
      trackScreenView(screen);

      return () => {
        const endMs = Date.now();
        const durationMs = Math.max(0, endMs - (startMsRef.current || endMs));
        trackMobileJourneyEvent('mobile_screen_exit', {
          screen_name: screen,
          duration_ms: durationMs,
          resource_type: 'screen',
          resource_id: screen,
          metadata: { duration_bucket: durationMs < 5000 ? 'lt_5s' : durationMs < 30000 ? '5s_30s' : durationMs < 120000 ? '30s_2m' : 'gt_2m' },
        });
      };
    }, [screenName])
  );

  return { trackEvent };
};
