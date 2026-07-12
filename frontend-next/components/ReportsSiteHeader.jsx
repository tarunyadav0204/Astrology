'use client';

import { useEffect, useState } from 'react';
import { appHomeHref, craHref, reportsAppHref } from '../lib/navigation';
import { loadStoredUser } from '../lib/api';

export default function ReportsSiteHeader() {
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
          <a href={reportsAppHref()}>Open Reports Studio</a>
          {user ? (
            <a href={appHomeHref()}>My account</a>
          ) : (
            <a href={reportsAppHref({ login: true })}>Sign in</a>
          )}
        </nav>
      </div>
    </header>
  );
}
