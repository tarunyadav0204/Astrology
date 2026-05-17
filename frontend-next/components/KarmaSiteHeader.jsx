'use client';

import { useEffect, useState } from 'react';
import { craHref, karmaAppHref } from '@/lib/navigation';
import { loadStoredUser } from '@/lib/api';

export default function KarmaSiteHeader() {
  const [user, setUser] = useState(null);

  useEffect(() => {
    setUser(loadStoredUser());
  }, []);

  return (
    <header className="karma-site-header">
      <div className="karma-site-header-inner">
        <a href={craHref('/')} className="karma-site-logo">
          AstroRoshni
        </a>
        <nav className="karma-site-nav" aria-label="Main">
          <a href={craHref('/panchang')}>Panchang</a>
          <a href={craHref('/kundli-matching')}>Kundli matching</a>
          <a href={craHref('/chat')}>AI chat</a>
          <a href={craHref('/nakshatras')}>Nakshatras</a>
          <a href={karmaAppHref()}>Open full app view</a>
          {user ? (
            <a href={craHref('/')}>My account</a>
          ) : (
            <a href={karmaAppHref({ login: true })}>Sign in</a>
          )}
        </nav>
      </div>
    </header>
  );
}
