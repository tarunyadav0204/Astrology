'use client';

import { useEffect, useState } from 'react';
import { craHref, kundliAppHref } from '../lib/navigation';
import { loadStoredUser } from '../lib/api';

export default function KundliSiteHeader() {
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
          <a href={craHref('/karma-analysis')}>Karma analysis</a>
          <a href={craHref('/chat')}>AI chat</a>
          <a href={craHref('/nakshatras')}>Nakshatras</a>
          <a href={kundliAppHref()}>Open matching tool</a>
          {user ? (
            <a href={craHref('/')}>My account</a>
          ) : (
            <a href={kundliAppHref({ login: true })}>Sign in</a>
          )}
        </nav>
      </div>
    </header>
  );
}
