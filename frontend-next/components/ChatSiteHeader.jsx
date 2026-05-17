'use client';

import { useEffect, useState } from 'react';
import { chatAppHref, craHref } from '../lib/navigation';
import { loadStoredUser } from '../lib/api';

export default function ChatSiteHeader() {
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
          <a href={craHref('/kundli-matching')}>Kundli matching</a>
          <a href={chatAppHref()}>Open chat</a>
          {user ? (
            <a href={craHref('/')}>My account</a>
          ) : (
            <a href={chatAppHref({ login: true })}>Sign in</a>
          )}
        </nav>
      </div>
    </header>
  );
}
