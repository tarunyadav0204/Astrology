#!/usr/bin/env node
/**
 * Applies two fixes to astroroshni_mobile AshtakavargaOracle.js:
 * 1) Show "Generate Life Predictions" on iOS (remove Platform.OS !== 'ios' gate).
 * 2) Re-fetch ashtakavarga when birthData loads (add birthData to useEffect deps).
 *
 * Run from repo root:
 *   node scripts/apply-ashtakvarga-oracle-mobile-fix.cjs
 */

const fs = require('fs');
const path = require('path');

const file = path.join(
  __dirname,
  '..',
  'astroroshni_mobile',
  'src',
  'components',
  'Ashtakavarga',
  'AshtakavargaOracle.js'
);

if (!fs.existsSync(file)) {
  console.error('File not found:', file);
  console.error('Open the AstroRoshni mobile app folder in Cursor or run this from the monorepo root.');
  process.exit(1);
}

let s = fs.readFileSync(file, 'utf8');
const orig = s;

// --- Fix 1: iOS button visibility ---
const iosGateOpen = `        {/* Generate Life Predictions hidden on iOS for App Store compliance */}
        {Platform.OS !== 'ios' && (
          <View style={styles.lifePredictionsContainer}>`;

if (s.includes(iosGateOpen)) {
  s = s.replace(
    iosGateOpen,
    `        <View style={styles.lifePredictionsContainer}>`
  );
  // Remove the closing `)}` for that conditional — match the life predictions block end.
  const closePattern = /(\s*<\/LinearGradient>\s*<\/TouchableOpacity>\s*<\/View>\s*)\)\}\s*/m;
  if (!closePattern.test(s)) {
    console.error(
      'Could not find closing )} for iOS gate after editing. Revert file from git and report this script.'
    );
    process.exit(1);
  }
  s = s.replace(closePattern, '$1');
} else if (s.includes("Platform.OS !== 'ios'") && s.includes('lifePredictionsContainer')) {
  console.error('iOS gate text differs from expected; apply the fix manually (see script comments).');
  process.exit(1);
} else {
  console.log('Skip fix 1: iOS gate already removed or not present.');
}

// --- Fix 2: useEffect deps ---
const badEffect = `  useEffect(() => {
    if (birthData) {
      fetchAshtakvargaData(birthData, selectedDate);
    }
  }, [selectedDate]);`;

const goodEffect = `  useEffect(() => {
    if (birthData) {
      fetchAshtakvargaData(birthData, selectedDate);
    }
  }, [birthData, selectedDate]);`;

if (s.includes(badEffect)) {
  s = s.replace(badEffect, goodEffect);
} else if (s.includes('[birthData, selectedDate]')) {
  console.log('Skip fix 2: useEffect already includes birthData.');
} else {
  console.warn(
    'Fix 2: could not find exact useEffect block; search for fetchAshtakavargaData(birthData, selectedDate) and set deps to [birthData, selectedDate].'
  );
}

if (s === orig) {
  console.log('No changes written (already applied or patterns differ).');
  process.exit(0);
}

fs.writeFileSync(file, s, 'utf8');
console.log('Updated:', file);
console.log('Review with git diff, then rebuild the iOS app.');
