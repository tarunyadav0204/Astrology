/** Full-page links into the main CRA app (not Next client routing). */

export function craHref(path) {
  const p = path.startsWith('/') ? path : `/${path}`;
  return p;
}

/** Interactive karma tool: CRA shell + NavigationHeader + login modal */
export function karmaAppHref({ login = false, hash = '' } = {}) {
  const params = new URLSearchParams({ app: '1' });
  if (login) params.set('login', '1');
  const h = hash ? (hash.startsWith('#') ? hash : `#${hash}`) : '';
  return `/karma-analysis?${params.toString()}${h}`;
}

/** Interactive Kundli matching tool: CRA shell + login modal + saved charts */
export function kundliAppHref({ login = false, hash = '' } = {}) {
  const params = new URLSearchParams({ app: '1' });
  if (login) params.set('login', '1');
  const h = hash ? (hash.startsWith('#') ? hash : `#${hash}`) : '';
  return `/kundli-matching?${params.toString()}${h}`;
}

/** Interactive AI astrologer chat: CRA shell + login modal + saved charts */
export function chatAppHref({ login = false, hash = '' } = {}) {
  const params = new URLSearchParams({ app: '1' });
  if (login) params.set('login', '1');
  const h = hash ? (hash.startsWith('#') ? hash : `#${hash}`) : '';
  return `/chat?${params.toString()}${h}`;
}
