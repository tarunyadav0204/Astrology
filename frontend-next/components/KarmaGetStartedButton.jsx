'use client';

import { karmaAppHref } from '@/lib/navigation';

export default function KarmaGetStartedButton({ children = 'Get your personalised karma report' }) {
  const handleClick = () => {
    document.getElementById('karma-tool')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
    const birth = typeof window !== 'undefined' ? localStorage.getItem('astrology_birth_data') : null;
    if (!token) {
      window.location.href = karmaAppHref({ login: true, hash: 'karma-tool' });
      return;
    }
    if (!birth) {
      window.location.href = karmaAppHref({ hash: 'karma-tool' });
      return;
    }
  };

  return (
    <button type="button" className="karma-landing-cta" onClick={handleClick}>
      {children}
    </button>
  );
}
