import React, { useEffect, useRef } from 'react';
import { useNavigation } from '@react-navigation/native';
import * as Sentry from '@sentry/react-native';
import { setGlobalErrorHandler } from '../services/api';
import { useError } from '../context/ErrorContext';
import { replaceWithLogin } from '../navigation/replaceWithLogin';

export default function GlobalErrorHandler() {
  const navigation = useNavigation();
  const { showError } = useError();
  const lastErrorTime = useRef(0);
  const DEBOUNCE_TIME = 2000; // 2 seconds

  useEffect(() => {
    setGlobalErrorHandler((error) => {
      const now = Date.now();
      
      // Debounce: ignore if same error type within 2 seconds
      if (now - lastErrorTime.current < DEBOUNCE_TIME) {
        return;
      }
      lastErrorTime.current = now;

      switch (error.type) {
        case 'network':
        case 'timeout':
        case 'server':
          try {
            Sentry.addBreadcrumb({
              category: 'ui',
              type: 'default',
              level: 'error',
              message: `global_error_overlay:${error.type}`,
              data: { type: error.type, detail: error.message },
            });
            if (error.type === 'network' || error.type === 'timeout') {
              Sentry.captureMessage(`global_overlay_${error.type}`, {
                level: 'info',
                tags: { overlay: error.type },
              });
            }
          } catch (_) {
            /* never let Sentry block the overlay */
          }
          showError(error);
          break;

        case 'auth':
          // Auth errors: clear stack so user cannot swipe back into Home.
          replaceWithLogin(navigation);
          break;

        default:
          break;
      }
    });

    return () => {
      setGlobalErrorHandler(null);
    };
  }, [navigation, showError]);

  return null;
}
