/**
 * Replace entire root stack with Login so swipe-back cannot return to Home (or any
 * authenticated screen) after logout or forced re-auth.
 */
export function replaceWithLogin(navigation) {
  navigation.reset({ index: 0, routes: [{ name: 'Login' }] });
}
