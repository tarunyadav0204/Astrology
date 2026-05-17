'use client';

import { kundliAppHref } from '../lib/navigation';

export default function KundliGetStartedButton({ children = 'Get your AI Kundli matching report' }) {
  const handleClick = () => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
    if (!token) {
      window.location.href = kundliAppHref({ login: true });
      return;
    }
    window.location.href = kundliAppHref();
  };

  return (
    <button type="button" className="karma-landing-cta kundli-landing-cta" onClick={handleClick}>
      {children}
    </button>
  );
}
