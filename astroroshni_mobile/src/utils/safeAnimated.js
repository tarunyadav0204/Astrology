import { Animated } from 'react-native';

/** Stop a running animation loop / timing without throwing. */
export function stopAnimationLoop(loop) {
  try {
    loop?.stop?.();
  } catch (_) {
    /* ignore */
  }
}

/** Stop an Animated.Value and optional reset. */
export function stopAnimatedValue(value, resetTo = null) {
  if (!value) return;
  try {
    value.stopAnimation?.();
    if (resetTo !== null && typeof value.setValue === 'function') {
      value.setValue(resetTo);
    }
  } catch (_) {
    /* ignore */
  }
}

/** Stop several Animated.Values at once. */
export function stopAnimatedValues(values, resetTo = null) {
  (values || []).forEach((v) => stopAnimatedValue(v, resetTo));
}

/**
 * Run Animated.timing only while mounted; returns a cancellable handle.
 */
export function runTiming(value, config, onEnd) {
  let cancelled = false;
  const anim = Animated.timing(value, config);
  anim.start(({ finished }) => {
    if (!cancelled && finished && onEnd) onEnd();
  });
  return {
    cancel() {
      cancelled = true;
      stopAnimatedValue(value);
    },
  };
}
