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
const sentryDsn =
  (typeof process !== 'undefined' && process.env.EXPO_PUBLIC_SENTRY_DSN) ||
  localEnv.EXPO_PUBLIC_SENTRY_DSN ||
  '';

module.exports = {
  expo: {
    ...appJson.expo,
    extra: {
      ...(appJson.expo.extra || {}),
      sentryDsn,
    },
  },
};
