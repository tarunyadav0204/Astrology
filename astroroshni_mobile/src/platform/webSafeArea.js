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
 *
 * Keyboard: do NOT refresh shell height from visualViewport resize/scroll — that
 * fights Safari's keyboard scroll and flickers the chat thread. Measure keyboard
 * overlap separately via getWebKeyboardOverlap / subscribeWebKeyboardOverlap.
 */
import { Platform } from 'react-native';

/** Typical iPhone home-indicator inset reported by CSS env(). */
export const WEB_MAX_BOTTOM_INSET = 34;

/**
 * Modest pad under labels when a bar should NOT extend into the home-indicator.
 * Home/Chart tab bars use getWebBottomInset so their background paints that zone.
 */
export const WEB_TAB_BOTTOM_PAD = 10;

/** Ignore tiny URL-bar / chrome changes; real keyboards are much taller. */
const WEB_KEYBOARD_OPEN_THRESHOLD = 80;

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
 * iOS standalone often reports 0 from env() — fall back to a typical
 * home-indicator height so the tab chrome can cover the purple strip.
 */
export function getWebBottomInset(rnInsetsBottom = 0) {
  if (Platform.OS !== 'web') {
    return Math.max(0, Number(rnInsetsBottom) || 0);
  }
  const fromRn = Math.max(0, Number(rnInsetsBottom) || 0);
  const fromCss = readCssSafeAreaBottom();
  // Prefer CSS env — more reliable than RN insets on iOS standalone WebKit.
  const raw = fromCss > 0 ? fromCss : fromRn;
  const capped = Math.min(Math.max(raw, 0), WEB_MAX_BOTTOM_INSET);
  if (capped > 0) return capped;
  // env() / RN often return 0 in Add-to-Home-Screen even though the home
  // indicator zone still shows the shell purple under fixed footers.
  if (isIosStandalonePwa()) return WEB_MAX_BOTTOM_INSET;
  return 0;
}

/** Modest pad under tab / chart / chat chrome labels (not full home-indicator). */
export function getWebTabBottomPad(rnInsetsBottom = 0) {
  if (Platform.OS !== 'web') {
    return Math.max(0, Number(rnInsetsBottom) || 0);
  }
  const inset = getWebBottomInset(rnInsetsBottom);
  if (inset <= 0) return 8;
  return Math.min(inset, WEB_TAB_BOTTOM_PAD);
}

/**
 * How many CSS pixels the software keyboard (or Safari chrome) covers at the
 * bottom of the layout viewport. Used to lift chat composer on iOS PWA web.
 */
export function getWebKeyboardOverlap() {
  if (Platform.OS !== 'web' || typeof window === 'undefined') return 0;
  try {
    const vv = window.visualViewport;
    if (!vv) return 0;
    const layoutH = Math.round(window.innerHeight || document.documentElement?.clientHeight || 0);
    if (layoutH <= 0) return 0;
    const overlap = Math.round(layoutH - vv.height - (vv.offsetTop || 0));
    return Math.max(0, overlap);
  } catch (_) {
    return 0;
  }
}

/**
 * Subscribe to keyboard / visual-viewport overlap changes (web only).
 * Debounced to one rAF so chat layout does not thrash while Safari animates.
 */
export function subscribeWebKeyboardOverlap(callback) {
  if (Platform.OS !== 'web' || typeof window === 'undefined') {
    return () => {};
  }
  if (typeof callback !== 'function') return () => {};

  let raf = 0;
  const notify = () => {
    if (raf) cancelAnimationFrame(raf);
    raf = requestAnimationFrame(() => {
      raf = 0;
      try {
        callback(getWebKeyboardOverlap());
      } catch (_) {}
    });
  };

  const vv = window.visualViewport;
  vv?.addEventListener('resize', notify);
  vv?.addEventListener('scroll', notify);
  window.addEventListener('resize', notify);
  notify();

  return () => {
    if (raf) cancelAnimationFrame(raf);
    vv?.removeEventListener('resize', notify);
    vv?.removeEventListener('scroll', notify);
    window.removeEventListener('resize', notify);
  };
}

/**
 * Re-apply shell sizing after keyboard / stack navigation.
 * iOS PWA often leaves a short layout (purple gap under tabs) after BirthForm.
 */
export function refreshWebShellHeight() {
  if (Platform.OS !== 'web' || typeof window === 'undefined' || typeof document === 'undefined') {
    return;
  }

  // While the keyboard is open, forcing scrollTop=0 fights Safari and flickers chat.
  const keyboardOpen = getWebKeyboardOverlap() >= WEB_KEYBOARD_OPEN_THRESHOLD;

  if (!keyboardOpen) {
    try {
      window.scrollTo(0, 0);
      if (document.documentElement) document.documentElement.scrollTop = 0;
      if (document.body) document.body.scrollTop = 0;
    } catch (_) {}
  }

  const root = document.documentElement;
  const appRoot = document.getElementById('root');

  // Always prefer filling the real window — never leave a short box with purple under tabs.
  root.style.removeProperty('--ar-app-height');
  root.style.height = '';
  root.style.minHeight = '';
  if (document.body) {
    document.body.style.top = '0';
    document.body.style.left = '0';
    document.body.style.right = '0';
    document.body.style.bottom = '0';
    document.body.style.height = '';
    document.body.style.minHeight = '';
    document.body.style.maxHeight = '';
  }
  if (appRoot) {
    appRoot.style.top = '0';
    appRoot.style.bottom = '0';
    appRoot.style.height = '';
    appRoot.style.minHeight = '';
    appRoot.style.maxHeight = '';
    // Do not defeat the centred desktop shell with inline left/right values.
    if (window.innerWidth >= 768) {
      appRoot.style.left = '50%';
      appRoot.style.right = 'auto';
    } else {
      appRoot.style.left = '0';
      appRoot.style.right = '0';
    }
  }

  // Re-measure / refresh orange cover if Home has it active.
  try {
    const fill = document.getElementById('ar-home-safe-fill-dom');
    const color = root.style.getPropertyValue('--ar-bottom-safe-color')?.trim();
    if (fill && color) {
      setWebBottomSafeColor(color);
    }
  } catch (_) {}
}

/**
 * Lock html/body/#root to the real window height (critical for iOS standalone PWA).
 * Call once at web startup.
 *
 * Important: do NOT subscribe to visualViewport here. Keyboard open/close fires
 * vv resize/scroll continuously; re-applying shell + scrollTo(0) causes the
 * chat screen flicker and can hide the focused input.
 */
export function installWebViewportHeightLock() {
  if (Platform.OS !== 'web' || typeof window === 'undefined' || typeof document === 'undefined') {
    return () => {};
  }

  const apply = () => refreshWebShellHeight();

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

  return () => {
    window.removeEventListener('resize', apply);
    window.removeEventListener('orientationchange', apply);
    window.removeEventListener('pageshow', apply);
    document.removeEventListener('visibilitychange', apply);
  };
}

/**
 * Paint the iPhone home-indicator zone orange while Home tabs are visible.
 * Uses a <style> tag (body::after) so it is not clipped by RN Views and does
 * not change tab bar height/padding. iOS bottom:0 is the safe edge — we
 * translate the paint into the unsafe strip below the tab bar.
 */
export function setWebBottomSafeColor(color) {
  if (Platform.OS !== 'web' || typeof document === 'undefined') return;
  const STYLE_ID = 'ar-home-indicator-style';
  const existingFill = document.getElementById('ar-home-safe-fill-dom');
  if (existingFill) existingFill.remove();

  let styleEl = document.getElementById(STYLE_ID);

  if (!color) {
    if (styleEl) styleEl.remove();
    document.documentElement.style.removeProperty('--ar-bottom-safe-color');
    const meta = document.querySelector('meta[name="theme-color"]:not([media])');
    if (meta && meta.dataset.arPrevThemeColor != null) {
      meta.setAttribute('content', meta.dataset.arPrevThemeColor);
      delete meta.dataset.arPrevThemeColor;
    }
    document.querySelectorAll('meta[name="theme-color"][media]').forEach((m) => {
      if (m.dataset.arPrevThemeColor != null) {
        m.setAttribute('content', m.dataset.arPrevThemeColor);
        delete m.dataset.arPrevThemeColor;
      }
    });
    return;
  }

  document.documentElement.style.setProperty('--ar-bottom-safe-color', color);

  if (!styleEl) {
    styleEl = document.createElement('style');
    styleEl.id = STYLE_ID;
    document.head.appendChild(styleEl);
  }

  styleEl.textContent = `
    html {
      background-color: var(--ar-shell-bg, #1a0033) !important;
      background-image: linear-gradient(
        to bottom,
        var(--ar-shell-bg, #1a0033) 0%,
        var(--ar-shell-bg, #1a0033) calc(100% - 34px),
        ${color} calc(100% - 34px),
        ${color} 100%
      ) !important;
    }
    /* Let html's orange bottom show; opaque body/#root were covering it. */
    body {
      background-color: transparent !important;
      background-image: none !important;
      overflow: visible !important;
    }
    /* Strip below safe bottom:0 (= under the tab bar on iOS). */
    body::after {
      content: '';
      position: fixed;
      left: 0;
      right: 0;
      bottom: 0;
      width: 100%;
      height: 34px;
      height: constant(safe-area-inset-bottom);
      height: env(safe-area-inset-bottom, 34px);
      min-height: 34px;
      background: ${color};
      transform: translateY(100%);
      z-index: 9999;
      pointer-events: none;
    }
    @media (min-width: 768px) {
      html {
        background-image: none !important;
      }
      body::after {
        display: none;
      }
    }
  `;

  const meta = document.querySelector('meta[name="theme-color"]:not([media])');
  if (meta) {
    if (meta.dataset.arPrevThemeColor == null) {
      meta.dataset.arPrevThemeColor = meta.getAttribute('content') || '#1a0033';
    }
    meta.setAttribute('content', color);
  }
  document.querySelectorAll('meta[name="theme-color"][media]').forEach((m) => {
    if (m.dataset.arPrevThemeColor == null) {
      m.dataset.arPrevThemeColor = m.getAttribute('content') || '#1a0033';
    }
    m.setAttribute('content', color);
  });
}
