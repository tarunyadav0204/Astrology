/**
 * iOS PWA home-indicator + viewport helpers.
 *
 * Safari tab vs Add-to-Home-Screen (standalone) behave differently:
 * - Safari: 100dvh ≈ visible area, insets.bottom often ~0 → looks fine
 * - Standalone: 100dvh can be shorter than the real app chrome → purple strip
 *   under bottom tabs, while RN safe-area insets still pad the tab bar.
 *
 * Fix: pin shell height to visualViewport/innerHeight, and cap bottom inset.
 */
import { Platform } from 'react-native';

/** Typical iPhone home-indicator inset; never pad more than this on web. */
export const WEB_MAX_BOTTOM_INSET = 34;

export function isIosStandalonePwa() {
  if (typeof window === 'undefined') return false;
  try {
    const standaloneMq =
      window.matchMedia && window.matchMedia('(display-mode: standalone)').matches;
    const iosStandalone = window.navigator?.standalone === true;
    return Boolean(standaloneMq || iosStandalone);
  } catch (_) {
    return false;
  }
}

function readCssSafeAreaBottom() {
  if (typeof document === 'undefined' || typeof window === 'undefined') return 0;
  try {
    const probe = document.createElement('div');
    probe.style.cssText =
      'position:fixed;left:0;bottom:0;width:0;height:0;padding-bottom:env(safe-area-inset-bottom,0px);visibility:hidden;pointer-events:none;';
    document.documentElement.appendChild(probe);
    const px = parseFloat(window.getComputedStyle(probe).paddingBottom) || 0;
    probe.remove();
    return Number.isFinite(px) ? px : 0;
  } catch (_) {
    return 0;
  }
}

/**
 * Bottom inset for pinning tab / chart / chat bars on Expo Web.
 * Prefers CSS env() when available; always capped for home indicator.
 */
export function getWebBottomInset(rnInsetsBottom = 0) {
  if (Platform.OS !== 'web') {
    return Math.max(0, Number(rnInsetsBottom) || 0);
  }
  const fromRn = Math.max(0, Number(rnInsetsBottom) || 0);
  const fromCss = readCssSafeAreaBottom();
  // Prefer CSS env — more reliable than RN insets on iOS standalone WebKit.
  const raw = fromCss > 0 ? fromCss : fromRn;
  return Math.min(Math.max(raw, 0), WEB_MAX_BOTTOM_INSET);
}

/**
 * Lock html/body/#root to the real visible height (critical for iOS standalone PWA).
 * Call once at web startup.
 */
export function installWebViewportHeightLock() {
  if (Platform.OS !== 'web' || typeof window === 'undefined' || typeof document === 'undefined') {
    return () => {};
  }

  const root = document.documentElement;

  const apply = () => {
    const vv = window.visualViewport;
    // Prefer visualViewport when it matches the visible frame; fall back to innerHeight.
    const height = Math.round(
      (vv && vv.height > 0 ? vv.height + (vv.offsetTop || 0) : 0) ||
        window.innerHeight ||
        root.clientHeight ||
        0
    );
    if (height > 0) {
      root.style.setProperty('--ar-app-height', `${height}px`);
      // Also set on body/#root directly for stubborn iOS standalone WebKit.
      if (document.body) {
        document.body.style.height = `${height}px`;
        document.body.style.minHeight = `${height}px`;
      }
      const appRoot = document.getElementById('root');
      if (appRoot) {
        appRoot.style.height = `${height}px`;
        appRoot.style.minHeight = `${height}px`;
      }
    }
  };

  apply();
  // Re-apply after first paint — iOS often reports a wrong height before chrome settles.
  requestAnimationFrame(apply);
  setTimeout(apply, 50);
  setTimeout(apply, 300);
  setTimeout(apply, 1000);

  window.addEventListener('resize', apply);
  window.addEventListener('orientationchange', apply);
  window.addEventListener('pageshow', apply);
  document.addEventListener('visibilitychange', apply);
  if (window.visualViewport) {
    window.visualViewport.addEventListener('resize', apply);
    window.visualViewport.addEventListener('scroll', apply);
  }

  return () => {
    window.removeEventListener('resize', apply);
    window.removeEventListener('orientationchange', apply);
    window.removeEventListener('pageshow', apply);
    document.removeEventListener('visibilitychange', apply);
    if (window.visualViewport) {
      window.visualViewport.removeEventListener('resize', apply);
      window.visualViewport.removeEventListener('scroll', apply);
    }
  };
}
