/** Cosmic/dark UI used text shadows; on light/pandit they smudge type (esp. Devanagari). */
export const NO_TEXT_SHADOW = {
  textShadowColor: 'transparent',
  textShadowOffset: { width: 0, height: 0 },
  textShadowRadius: 0,
};

export function isDarkTheme(theme) {
  return theme === 'dark';
}

/** Apply a shadow only in dark theme; clear it for light/pandit. */
export function themeTextShadow(theme, darkShadow = null) {
  if (!isDarkTheme(theme)) return NO_TEXT_SHADOW;
  return (
    darkShadow || {
      textShadowColor: 'rgba(0, 0, 0, 0.3)',
      textShadowOffset: { width: 0, height: 2 },
      textShadowRadius: 4,
    }
  );
}
