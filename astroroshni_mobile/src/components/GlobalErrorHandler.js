import React, { useEffect, useRef } from 'react';
import { useNavigation } from '@react-navigation/native';
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
          showError(error);
          break;

        case 'auth':
          // Auth errors navigate immediately, no overlay
          navigation.navigate('Login');
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
