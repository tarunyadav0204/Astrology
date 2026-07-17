/**
 * Safe back for React Navigation — on web/PWA, screens opened via linking
 * or auth `reset` often have an empty stack so goBack() is a no-op.
 */
export function goBackOrHome(navigation, homeParams) {
  try {
    if (navigation?.canGoBack?.()) {
      navigation.goBack();
      return;
    }
  } catch (_) {
    /* fall through */
  }
  if (typeof navigation?.navigate === 'function') {
    navigation.navigate('Home', homeParams);
  }
}

/**
 * Reset after login/register. Keep Home under non-Home destinations so Back works.
 */
export function resetToRoute(navigation, routeName, params) {
  if (!navigation?.reset) return;
  if (!routeName || routeName === 'Home') {
    navigation.reset({
      index: 0,
      routes: [{ name: 'Home', params }],
    });
    return;
  }
  navigation.reset({
    index: 1,
    routes: [
      { name: 'Home' },
      { name: routeName, params },
    ],
  });
}
