'use client';

import { reportsAppHref } from '../lib/navigation';

export default function ReportsGetStartedButton({ children = 'Open Reports Studio' }) {
  const handleClick = () => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
    if (!token) {
      window.location.href = reportsAppHref({ login: true });
      return;
    }
    window.location.href = reportsAppHref();
  };

  return (
    <button type="button" className="karma-landing-cta reports-landing-cta" onClick={handleClick}>
      {children}
    </button>
  );
}
