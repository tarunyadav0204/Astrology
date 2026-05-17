'use client';

import { chatAppHref } from '@/lib/navigation';

export default function ChatGetStartedButton({ children = 'Start chatting with your chart' }) {
  const handleClick = () => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
    if (!token) {
      window.location.href = chatAppHref({ login: true });
      return;
    }
    window.location.href = chatAppHref();
  };

  return (
    <button type="button" className="karma-landing-cta chat-landing-cta" onClick={handleClick}>
      {children}
    </button>
  );
}
