/**
 * iOS PWA home-indicator helpers.
 *
 * Mac Safari "responsive design" often reports insets.bottom ≈ 0 and a full
 * mock viewport, so padding looks fine there. On a real iPhone (especially
 * Add-to-Home-Screen), react-native-safe-area-context can over-report the
 * bottom inset while CSS -webkit-fill-available shrinks #root above the
 * home-indicator — producing orange tab padding + a purple dead strip below.
 */
import { Platform } from 'react-native';

/** Typical iPhone home-indicator inset; never pad more than this on web. */
export const WEB_MAX_BOTTOM_INSET = 34;

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
 * Bottom inset for pinning tab / chart bars on Expo Web.
 * Prefers the smaller of RN insets and CSS env(), capped for home indicator.
 */
export function getWebBottomInset(rnInsetsBottom = 0) {
  if (Platform.OS !== 'web') {
    return Math.max(0, Number(rnInsetsBottom) || 0);
  }
  const fromRn = Math.max(0, Number(rnInsetsBottom) || 0);
  const fromCss = readCssSafeAreaBottom();
  const raw = fromCss > 0 ? Math.min(fromRn || fromCss, fromCss) : fromRn;
  // If RN reports a huge value (layout bug) and CSS is 0, still cap.
  return Math.min(Math.max(raw, 0), WEB_MAX_BOTTOM_INSET);
}
