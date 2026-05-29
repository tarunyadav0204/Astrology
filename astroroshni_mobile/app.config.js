/**
 * Dynamic Expo config so Sentry DSN is available at runtime via Constants.expoConfig.extra.sentryDsn.
 * Plain app.json alone does not load .env; Gradle/Metro may bundle with an empty EXPO_PUBLIC_SENTRY_DSN.
 */
const fs = require('fs');
const path = require('path');

function readEnvFile() {
  const envPath = path.join(__dirname, '.env');
  if (!fs.existsSync(envPath)) return {};
  const env = {};
  const lines = fs.readFileSync(envPath, 'utf8').split(/\r?\n/);
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) continue;
    const eq = trimmed.indexOf('=');
    if (eq === -1) continue;
    const key = trimmed.slice(0, eq).trim();
    let val = trimmed.slice(eq + 1).trim();
    if (
      (val.startsWith('"') && val.endsWith('"')) ||
      (val.startsWith("'") && val.endsWith("'"))
    ) {
      val = val.slice(1, -1);
    }
    env[key] = val;
  }
  return env;
}

const appJson = require('./app.json');
const localEnv = readEnvFile();

const env = (key) =>
  (typeof process !== 'undefined' && process.env[key]) || localEnv[key] || '';

const sentryDsn = env('EXPO_PUBLIC_SENTRY_DSN') || '';
const facebookAppId = env('EXPO_PUBLIC_FACEBOOK_APP_ID') || '';
const facebookClientToken = env('EXPO_PUBLIC_FACEBOOK_CLIENT_TOKEN') || '';
const facebookDisplayName = env('EXPO_PUBLIC_FACEBOOK_DISPLAY_NAME') || 'AstroRoshni';
const facebookDebugLog = ['1', 'true', 'yes'].includes(
  String(env('EXPO_PUBLIC_FACEBOOK_DEBUG_LOG') || '').toLowerCase()
);

const plugins = [...(appJson.expo.plugins || [])];

if (facebookAppId && facebookClientToken) {
  plugins.push([
    'react-native-fbsdk-next',
    {
      appID: facebookAppId,
      clientToken: facebookClientToken,
      displayName: facebookDisplayName,
      scheme: `fb${facebookAppId}`,
      isAutoInitEnabled: true,
      autoLogAppEventsEnabled: true,
      advertiserIDCollectionEnabled: false,
      iosUserTrackingPermission:
        'This identifier helps us measure app installs and improve AstroRoshni. You can change this anytime in Settings.',
    },
  ]);
}

module.exports = {
  expo: {
    ...appJson.expo,
    plugins,
    extra: {
      ...(appJson.expo.extra || {}),
      sentryDsn,
      facebookAppId,
      facebookClientToken,
      facebookDisplayName,
      facebookDebugLog,
    },
  },
};
