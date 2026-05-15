const { getDefaultConfig } = require('@expo/metro-config');
const { getSentryExpoConfig } = require('@sentry/react-native/metro');

/**
 * Expo + Sentry: use getSentryExpoConfig so Debug ID is applied via before-serialization plugins.
 * withSentryConfig() wraps customSerializer and breaks when Expo's serializer ignores
 * options.sentryBundleCallback → "Debug ID was not found in the bundle".
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

module.exports = getSentryExpoConfig(__dirname, {
  getDefaultConfig: getSvgAwareExpoConfig,
});
