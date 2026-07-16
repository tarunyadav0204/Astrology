/**
 * App entry (replaces default expo/AppEntry.js import of ../../App) so Metro always
 * resolves the root component from this package. Run `npx expo start` from this folder.
 */
import './src/services/instrumentSentry';
import { Platform } from 'react-native';

if (Platform.OS === 'web') {
  // Phone-shell CSS for Expo Web (mobile browsers on astroroshni.com).
  // eslint-disable-next-line global-require
  require('./src/platform/webShell.css');
  if (typeof document !== 'undefined') {
    const ensureViewport = () => {
      let meta = document.querySelector('meta[name="viewport"]');
      if (!meta) {
        meta = document.createElement('meta');
        meta.setAttribute('name', 'viewport');
        document.head.appendChild(meta);
      }
      meta.setAttribute(
        'content',
        'width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no, viewport-fit=cover'
      );
    };
    ensureViewport();
  }
}

import registerRootComponent from 'expo/src/launch/registerRootComponent';
import App from './App';

registerRootComponent(App);
