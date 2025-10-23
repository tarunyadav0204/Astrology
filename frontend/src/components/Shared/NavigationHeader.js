import React from 'react';
import { useNavigate } from 'react-router-dom';
import './NavigationHeader.css';

const NavigationHeader = ({ onPeriodChange, showZodiacSelector, zodiacSigns, selectedZodiac, onZodiacChange }) => {
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
          </div>
          <div className="auth-section">
            <button className="auth-btn">Sign In / Sign Up</button>
          </div>
        </div>
      </div>

      <div className="main-nav">
        <div className="container">
          <div className="logo-section">
            <button className="logo-text" onClick={() => navigate('/')}>
              🔮 AstroVedic
            </button>
          </div>
          <div className="language-section">
            <button className="lang-btn">हिन्दी</button>
            <button className="lang-btn">தமிழ்</button>
            <button className="lang-btn">తెలుగు</button>
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
                  if (onPeriodChange) onPeriodChange('daily');
                  navigate('/horoscope/daily');
                }}>📅 Daily Horoscope</button>
                <button onClick={() => {
                  if (onPeriodChange) onPeriodChange('weekly');
                  navigate('/horoscope/weekly');
                }}>📊 Weekly Horoscope</button>
                <button onClick={() => {
                  if (onPeriodChange) onPeriodChange('monthly');
                  navigate('/horoscope/monthly');
                }}>🗓️ Monthly Horoscope</button>
                <button onClick={() => {
                  if (onPeriodChange) onPeriodChange('yearly');
                  navigate('/horoscope/yearly');
                }}>📆 Yearly Horoscope</button>
              </div>
            </li>
            <li><a href="/#astrology">Astrology</a></li>
            <li><a href="/#reports">Free Reports</a></li>
            <li><a href="/#panchang">Panchang</a></li>
            <li><a href="/#lalkitab">Lal Kitab</a></li>
            <li><a href="/#compatibility">Compatibility</a></li>
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