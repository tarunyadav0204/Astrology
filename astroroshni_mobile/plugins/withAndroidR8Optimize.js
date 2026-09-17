const { withAppBuildGradle } = require('expo/config-plugins');

/**
 * Play Console requires R8 optimisation (not just minify). The Expo Android
 * template still points at proguard-android.txt, which includes -dontoptimize.
 */
function withAndroidR8Optimize(config) {
  return withAppBuildGradle(config, (modConfig) => {
    modConfig.modResults.contents = modConfig.modResults.contents.replace(
      /getDefaultProguardFile\(["']proguard-android\.txt["']\)/g,
      'getDefaultProguardFile("proguard-android-optimize.txt")'
    );
    return modConfig;
  });
}

module.exports = withAndroidR8Optimize;
