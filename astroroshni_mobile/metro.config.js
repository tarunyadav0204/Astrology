const path = require('path');
const { getDefaultConfig } = require('@expo/metro-config');
const { getSentryExpoConfig } = require('@sentry/react-native/metro');

/**
 * Expo + Sentry: use getSentryExpoConfig so Debug ID is applied via before-serialization plugins.
 * withSentryConfig() wraps customSerializer and breaks when Expo's serializer ignores
 * options.sentryBundleCallback → "Debug ID was not found in the bundle".
 *
 * On web, native-only packages are redirected to lightweight stubs so `expo export -p web` can boot.
 */
function getSvgAwareExpoConfig(projectRoot, options) {
  const config = getDefaultConfig(projectRoot, options);

  config.transformer = {
    ...config.transformer,
    babelTransformerPath: require.resolve('react-native-svg-transformer'),
    minifierConfig: {
      keep_classnames: true,
      keep_fnames: true,
      mangle: {
        keep_classnames: true,
        keep_fnames: true,
      },
    },
  };

  config.resolver = {
    ...config.resolver,
    assetExts: config.resolver.assetExts.filter((ext) => ext !== 'svg'),
    sourceExts: [...config.resolver.sourceExts, 'svg'],
  };

  return config;
}

const metroConfig = getSentryExpoConfig(__dirname, {
  getDefaultConfig: getSvgAwareExpoConfig,
});

const WEB_NATIVE_STUBS = {
  'react-native-iap': path.resolve(__dirname, 'src/platform/stubs/react-native-iap.js'),
  'react-native-razorpay': path.resolve(__dirname, 'src/platform/stubs/react-native-razorpay.js'),
  'react-native-fbsdk-next': path.resolve(
    __dirname,
    'src/platform/stubs/react-native-fbsdk-next.js'
  ),
  'react-native-view-shot': path.resolve(
    __dirname,
    'src/platform/stubs/react-native-view-shot.js'
  ),
  'react-native-webview': path.resolve(
    __dirname,
    'src/platform/stubs/react-native-webview.js'
  ),
  'expo-store-review': path.resolve(__dirname, 'src/platform/stubs/expo-store-review.js'),
  'expo-notifications': path.resolve(__dirname, 'src/platform/stubs/expo-notifications.js'),
  '@sentry/react-native': path.resolve(__dirname, 'src/platform/stubs/sentry-react-native.js'),
};

const previousResolveRequest = metroConfig.resolver.resolveRequest;

metroConfig.resolver.resolveRequest = (context, moduleName, platform) => {
  if (platform === 'web' && WEB_NATIVE_STUBS[moduleName]) {
    return {
      filePath: WEB_NATIVE_STUBS[moduleName],
      type: 'sourceFile',
    };
  }
  if (typeof previousResolveRequest === 'function') {
    return previousResolveRequest(context, moduleName, platform);
  }
  return context.resolveRequest(context, moduleName, platform);
};

module.exports = metroConfig;
