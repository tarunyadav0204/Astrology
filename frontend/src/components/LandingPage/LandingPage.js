import React, { useState, useEffect } from 'react';
import LoginForm from '../Auth/LoginForm';
import RegisterForm from '../Auth/RegisterForm';
import { getCurrentDomainConfig } from '../../config/domains.config';
import './LandingPage.css';

const LandingPage = ({ onLogin, onRegister }) => {
  const [authView, setAuthView] = useState('login');
  const [showAuth, setShowAuth] = useState(false);
  const [domainConfig, setDomainConfig] = useState(null);
  
  useEffect(() => {
    setDomainConfig(getCurrentDomainConfig());
  }, []);

  return (
    <div className="landing-page">
      <div className="landing-hero">
        <div className="stars"></div>
        <div className="hero-content">
          <div className="hero-text">
            <h1 className="hero-title">
              ✨ Welcome to {domainConfig?.title || 'AstroClick'} 🌟
            </h1>
            <p className="hero-subtitle">
              {domainConfig?.userType === 'software' 
                ? 'Professional Vedic astrology software for accurate calculations and predictions'
                : domainConfig?.userType === 'general'
                ? 'Get personalized astrology readings and spiritual guidance from expert astrologers'
                : 'Unlock the secrets of your birth chart with authentic Vedic astrology'
              }
            </p>
            <div className="features-grid">
              <div className="feature">
                <span className="feature-icon">🌙</span>
                <span>Precise Calculations</span>
              </div>
              <div className="feature">
                <span className="feature-icon">⭐</span>
                <span>Vedic Traditions</span>
              </div>
              <div className="feature">
                <span className="feature-icon">🔮</span>
                <span>Life Predictions</span>
              </div>
              <div className="feature">
                <span className="feature-icon">🌟</span>
                <span>Dasha Analysis</span>
              </div>
            </div>
            <button 
              className="cta-button"
              onClick={() => {
                console.log('Button clicked, setting showAuth to true');
                setShowAuth(true);
              }}
            >
              {domainConfig?.userType === 'software' ? 'Access Software' : 'Begin Your Reading'}
            </button>
          </div>
          <div className="hero-visual">
            <div className="zodiac-wheel">
              <div className="wheel-center">
                <span className="center-symbol">☉</span>
              </div>
              <div className="zodiac-signs">
                {['♈', '♉', '♊', '♋', '♌', '♍', '♎', '♏', '♐', '♑', '♒', '♓'].map((sign, i) => (
                  <div key={i} className={`zodiac-sign sign-${i}`}>
                    {sign}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {showAuth && (
        <div className="auth-modal">
          <div className="auth-container">
            <button 
              className="close-button"
              onClick={() => setShowAuth(false)}
            >
              ×
            </button>
            <div className="auth-header">
              <h2>Access Your Account</h2>
              <div className="auth-tabs">
                <button 
                  className={`tab ${authView === 'login' ? 'active' : ''}`}
                  onClick={() => setAuthView('login')}
                >
                  Sign In
                </button>
                <button 
                  className={`tab ${authView === 'register' ? 'active' : ''}`}
                  onClick={() => setAuthView('register')}
                >
                  Create Account
                </button>
              </div>
            </div>
            {authView === 'login' ? (
              <LoginForm 
                onLogin={onLogin} 
                onSwitchToRegister={() => setAuthView('register')} 
              />
            ) : (
              <RegisterForm 
                onRegister={onRegister} 
                onSwitchToLogin={() => setAuthView('login')} 
              />
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default LandingPage;