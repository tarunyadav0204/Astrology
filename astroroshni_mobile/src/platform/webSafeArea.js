/**
 * iOS PWA home-indicator + viewport helpers.
 *
 * Safari tab vs Add-to-Home-Screen (standalone) behave differently:
 * - Safari: usually fine with 100dvh / innerHeight
 * - Standalone: visualViewport.height is often *shorter* than the full window,
 *   so locking html/body/#root to it leaves a dead purple strip under bottom tabs.
 *   RN safe-area insets still pad the tab bar → fat orange padding.
 *
 * Fix: never size the shell from visualViewport; prefer innerHeight/clientHeight
 * (or inset:0 fill on standalone). Cap bottom inset for home indicator.
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
 * Visible layout height for the app shell.
 * Never use visualViewport.height — on iOS standalone it under-reports and
 * leaves a dead strip under #root when height/max-height are locked to it.
 */
function resolveShellHeight() {
  const inner = Math.round(window.innerHeight || 0);
  const client = Math.round(document.documentElement?.clientHeight || 0);
  return Math.max(inner, client);
}

/**
 * Lock html/body/#root to the real window height (critical for iOS standalone PWA).
 * Call once at web startup.
 */
export function installWebViewportHeightLock() {
  if (Platform.OS !== 'web' || typeof window === 'undefined' || typeof document === 'undefined') {
    return () => {};
  }

  const root = document.documentElement;

  const apply = () => {
    const height = resolveShellHeight();
    if (height <= 0) return;

    // Standalone: rely on CSS position:fixed + inset:0. Clearing a short
    // --ar-app-height / inline height is what removes the purple strip.
    if (isIosStandalonePwa()) {
      root.style.removeProperty('--ar-app-height');
      if (document.body) {
        document.body.style.height = '';
        document.body.style.minHeight = '';
        document.body.style.maxHeight = '';
      }
      const appRoot = document.getElementById('root');
      if (appRoot) {
        appRoot.style.height = '';
        appRoot.style.minHeight = '';
        appRoot.style.maxHeight = '';
      }
      return;
    }

    root.style.setProperty('--ar-app-height', `${height}px`);
    if (document.body) {
      document.body.style.height = `${height}px`;
      document.body.style.minHeight = `${height}px`;
      document.body.style.maxHeight = '';
    }
    const appRoot = document.getElementById('root');
    if (appRoot) {
      appRoot.style.height = `${height}px`;
      appRoot.style.minHeight = `${height}px`;
      appRoot.style.maxHeight = '';
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
  // Keep listening to visualViewport for keyboard / URL-bar changes, but apply()
  // never sizes the shell from visualViewport.height.
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
