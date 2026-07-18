import React, { useEffect, useRef } from 'react';
import { useNavigation } from '@react-navigation/native';
import * as Sentry from '@sentry/react-native';
import { setGlobalErrorHandler } from '../services/api';
import { useError } from '../context/ErrorContext';

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
          // Expired/invalid session → clear account + chart leftovers, explore as guest on Home.
          // Do not hard-reset to Login (that fights guest-mode product policy).
          (async () => {
            try {
              const { storage } = require('../services/storage');
              await storage.clearAccountSession();
            } catch (_) {
              /* ignore */
            }
            try {
              const state = navigation.getState?.();
              const current = state?.routes?.[state.index || 0]?.name;
              if (current === 'Home' || current === 'Welcome' || current === 'Login') {
                return;
              }
              navigation.reset({ index: 0, routes: [{ name: 'Home' }] });
            } catch (_) {
              /* ignore */
            }
          })();
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
