import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './NavigationHeader.css';

const NavigationHeader = ({ onPeriodChange, showZodiacSelector, zodiacSigns, selectedZodiac, onZodiacChange, user, onAdminClick, onLogout, onLogin, showLoginButton }) => {
  const navigate = useNavigate();



  return (
    <header className="main-header">
      <div className="top-bar">
        <div className="container">
          <div className="top-links">
            <a href="#rashifal">Rashifal</a>
            <a href="#kundli">Kundli</a>
            <a href="#horoscope">Horoscope 2025</a>
            <a href="#calendar">Calendar 2025</a>
            <a href="#chat" className="chat-btn">
              💬 Chat with Astrologer <span className="online-dot"></span>
            </a>
            <a href="/astroroshni" target="_blank" className="astroroshni-link">
              ⭐ AstroVishnu Pro
            </a>
          </div>
          <div className="auth-section">
            {user ? (
              <div className="user-menu">
                <span className="user-name">👤 {user.name || user.phone}</span>
                {user.role === 'admin' && (
                  <button className="admin-btn" onClick={onAdminClick}>
                    ⚙️ Admin
                  </button>
                )}
                <button className="auth-btn" onClick={onLogout}>Logout</button>
              </div>
            ) : (
              <button className="auth-btn" onClick={onLogin}>Sign In / Sign Up</button>
            )}
          </div>
        </div>
      </div>

      <div className="main-nav">
        <div className="container">
          <div className="logo-section">
            <button className="logo-text" onClick={() => navigate('/')}>
              🔮 AstroRoshni
            </button>
          </div>
          <div className="language-section">
            <button className="lang-btn">हिन्दी</button>
            <button className="lang-btn">தமிழ்</button>
            <button className="lang-btn">తెలుగు</button>
          </div>
          <div className="mobile-auth">
            {user ? (
              <div className="user-menu">
                <span className="user-name">👤 {user.name || user.phone}</span>
                {user.role === 'admin' && (
                  <button className="admin-btn" onClick={onAdminClick}>
                    ⚙️ Admin
                  </button>
                )}
                <button className="auth-btn" onClick={onLogout}>Logout</button>
              </div>
            ) : (
              showLoginButton && <button className="auth-btn" onClick={onLogin}>Sign In</button>
            )}
          </div>
        </div>
      </div>

      <nav className="navigation">
        <div className="container">
          <ul className="nav-menu">
            <li><a href="/#home">Home</a></li>
            <li className="dropdown">
              <a href="#horoscope" className="dropdown-toggle">Horoscope</a>
              <div className="dropdown-content">
                <button onClick={() => {
                  navigate('/horoscope/daily');
                }}>📅 Daily Horoscope</button>
                <button onClick={() => {
                  navigate('/horoscope/weekly');
                }}>📊 Weekly Horoscope</button>
                <button onClick={() => {
                  navigate('/horoscope/monthly');
                }}>🗓️ Monthly Horoscope</button>
                <button onClick={() => {
                  navigate('/horoscope/yearly');
                }}>📆 Yearly Horoscope</button>
              </div>
            </li>
            <li><a href="/#astrology">Astrology</a></li>
            <li className="dropdown">
              <a href="#yourlife" className="dropdown-toggle">Your Life</a>
              <div className="dropdown-content">
                <a href="/#career">💼 Your Career</a>
                <a href="/#marriage">💍 Your Marriage</a>
                <a href="/#education">🎓 Your Education</a>
                <a href="/#health">🏥 Your Health</a>
                <a href="/#wealth">💰 Your Wealth</a>
              </div>
            </li>
            <li><button onClick={() => navigate('/panchang')}>Panchang</button></li>
            <li><a href="/#calculators">Calculators</a></li>
          </ul>
        </div>
      </nav>

      {showZodiacSelector && zodiacSigns && (
        <div className="zodiac-selector">
          <div className="zodiac-nav">
            {zodiacSigns.map(sign => (
              <button 
                key={sign.name}
                className={`zodiac-btn ${selectedZodiac === sign.name ? 'active' : ''}`}
                onClick={() => onZodiacChange && onZodiacChange(sign.name)}
              >
                <div className="zodiac-symbol">{sign.symbol}</div>
                <div className="zodiac-name">{sign.displayName}</div>
              </button>
            ))}
          </div>
        </div>
      )}
    </header>
  );
};

export default NavigationHeader;