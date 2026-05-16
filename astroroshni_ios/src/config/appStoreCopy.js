/**
 * App Store / in-app positioning for the educational iOS build.
 * Used in About, Welcome, and review-facing strings.
 */
export const APP_DISPLAY_NAME = 'AstroRoshni Study';
export const APP_TAGLINE = 'Learn Vedic chart mathematics';
export const APP_SHORT_DESCRIPTION =
  'Swiss Ephemeris–based birth charts, dashas, and structured lessons. For study and chart literacy—not fortune telling.';

/** Paste into App Store Connect → App Review Information → Notes */
export const APP_STORE_REVIEW_NOTES = [
  'AstroRoshni Study is an educational Vedic astrology reference app.',
  'Users explore Swiss Ephemeris birth charts, divisional charts, dashas, Ashtakavarga tables, and yogas.',
  'The Learn tab opens a teaching-focused chat (backend lab mode) that explains chart mechanics using the user chart as a worked example—it does not provide fortune telling, gambling advice, or medical/legal/financial predictions.',
  'Life-event timelines, trading forecasts, muhurat planners, and premium “prediction” flows are removed from this build.',
  'Advanced reference calculators (charts, dashas, KP, Kota Chakra, yogas, Ashtakavarga, etc.) are labeled Premium on the home screen and require an active credit balance or subscription; free tier includes Study chat and educational blog content.',
].join('\n');
