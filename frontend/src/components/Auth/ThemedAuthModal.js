import React from 'react';
import LoginForm from './LoginForm';
import RegisterForm from './RegisterForm';
import AuthModalShell from './AuthModalShell';

const DEFAULT_EYEBROW = 'Your chart, remembered';
const DEFAULT_TITLE = 'Welcome to AstroRoshni';
const DEFAULT_LEAD =
  'Sign in to continue with your saved Kundlis, personal timing and Tara conversations.';

/**
 * The same themed Sign in / Sign up sheet used by the homepage header.
 * Tool pages should open this modal — not a separate pink/legacy auth popup.
 */
export default function ThemedAuthModal({
  isOpen,
  onClose,
  authView,
  setAuthView,
  onAuthenticated,
  eyebrow = DEFAULT_EYEBROW,
  title = DEFAULT_TITLE,
  description = DEFAULT_LEAD,
}) {
  return (
    <AuthModalShell themed isOpen={isOpen} onClose={onClose}>
      <div className="auth-experience">
        <p className="auth-experience__eyebrow">{eyebrow}</p>
        <h2 className="auth-experience__title">{title}</h2>
        <p className="auth-experience__lead">{description}</p>
        <div className="auth-experience__tabs" style={{ display: 'flex', justifyContent: 'center' }}>
          <button
            type="button"
            className={authView === 'login' ? 'is-active' : ''}
            onClick={() => setAuthView('login')}
          >
            Sign In
          </button>
          <button
            type="button"
            className={authView === 'register' ? 'is-active' : ''}
            onClick={() => setAuthView('register')}
          >
            Sign Up
          </button>
        </div>
      </div>
      {authView === 'login' ? (
        <LoginForm
          onLogin={(userData) => {
            onAuthenticated(userData);
            onClose();
          }}
          onSwitchToRegister={() => setAuthView('register')}
        />
      ) : (
        <RegisterForm
          onRegister={(userData) => {
            onAuthenticated(userData);
            onClose();
          }}
          onSwitchToLogin={() => setAuthView('login')}
        />
      )}
    </AuthModalShell>
  );
}
