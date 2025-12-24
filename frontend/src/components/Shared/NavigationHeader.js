import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCredits } from '../../context/CreditContext';
import SearchBar from '../Search/SearchBar';
import './NavigationHeader.css';

const NavigationHeader = ({ onPeriodChange, showZodiacSelector, zodiacSigns, selectedZodiac, onZodiacChange, user, onAdminClick, onLogout, onLogin, showLoginButton, onCreditsClick, onHomeClick }) => {
  const navigate = useNavigate();
  const { credits, loading: creditsLoading } = useCredits();
  const [showMobileSearch, setShowMobileSearch] = useState(false);
  const [activeDropdown, setActiveDropdown] = useState(null);
  const [dropdownPosition, setDropdownPosition] = useState({ top: 0, left: 0 });

  const toggleDropdown = (dropdownName, event) => {
    if (activeDropdown === dropdownName) {
      setActiveDropdown(null);
    } else {
      const rect = event.currentTarget.getBoundingClientRect();
      
      setDropdownPosition({
        top: rect.bottom + window.scrollY,
        left: rect.left
      });
      setActiveDropdown(dropdownName);
    }
  };

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (activeDropdown && !event.target.closest('.dropdown') && !event.target.closest('.dropdown-content')) {
        setActiveDropdown(null);
      }
    };

    document.addEventListener('click', handleClickOutside);
    return () => document.removeEventListener('click', handleClickOutside);
  }, [activeDropdown]);



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
                {!creditsLoading && onCreditsClick && (
                  <button className="credits-btn" onClick={onCreditsClick}>
                    💳 {credits}
                  </button>
                )}
                <button className="profile-btn" onClick={() => navigate('/profile')}>
                  👤 {user.name || user.phone}
                </button>
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
            <button className="logo-text" onClick={onHomeClick || (() => navigate('/'))}>
              <span className="logo-full">🔮 AstroRoshni</span>
              <span className="logo-short">🔮 AR</span>
            </button>
          </div>
          <SearchBar user={user} onLogin={onLogin} />
          <button className="mobile-search-btn" onClick={() => setShowMobileSearch(true)}>
            🔍
          </button>
          <div className="mobile-auth">
            {user ? (
              <div className="user-menu">
                {!creditsLoading && onCreditsClick && (
                  <button className="credits-btn mobile" onClick={onCreditsClick}>
                    💳 {credits}
                  </button>
                )}
                <button className="profile-btn" onClick={() => navigate('/profile')}>
                  👤 {user.name || user.phone}
                </button>
                {user.role === 'admin' && (
                  <button className="admin-btn mobile-admin" onClick={onAdminClick}></button>
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
            <li><button onClick={onHomeClick || (() => navigate('/'))}>Home</button></li>
            <li className={`dropdown ${activeDropdown === 'horoscope' ? 'active' : ''}`}>
              <a href="#horoscope" className="dropdown-toggle" onClick={(e) => { e.preventDefault(); toggleDropdown('horoscope', e); }}>Horoscope</a>
            </li>
            <li><a href="/#astrology">Astrology</a></li>
            <li className={`dropdown ${activeDropdown === 'yourlife' ? 'active' : ''}`}>
              <a href="#yourlife" className="dropdown-toggle" onClick={(e) => { e.preventDefault(); toggleDropdown('yourlife', e); }}>Your Life</a>
            </li>
            <li><button onClick={() => navigate('/panchang')}>Panchang</button></li>
            <li><button onClick={() => navigate('/muhurat-finder')}>Muhurat Finder</button></li>
            <li><button onClick={() => navigate('/festivals')}>Festivals</button></li>
            <li><button onClick={() => navigate('/nakshatras')}>Nakshatras</button></li>
            <li><a href="/#calculators">Calculators</a></li>
          </ul>
        </div>
      </nav>

      {/* Dropdown menus rendered outside navigation */}
      {activeDropdown === 'horoscope' && (
        <div className="dropdown-content" style={{ top: `${dropdownPosition.top}px`, left: `${dropdownPosition.left}px` }}>
          <button onClick={() => {
            navigate('/horoscope?period=daily');
            setActiveDropdown(null);
          }}>📅 Daily Horoscope</button>
          <button onClick={() => {
            navigate('/horoscope?period=weekly');
            setActiveDropdown(null);
          }}>📊 Weekly Horoscope</button>
          <button onClick={() => {
            navigate('/horoscope?period=monthly');
            setActiveDropdown(null);
          }}>🗓️ Monthly Horoscope</button>
          <button onClick={() => {
            navigate('/horoscope?period=yearly');
            setActiveDropdown(null);
          }}>📆 Yearly Horoscope</button>
        </div>
      )}

      {activeDropdown === 'yourlife' && (
        <div className="dropdown-content" style={{ top: `${dropdownPosition.top}px`, left: `${dropdownPosition.left}px` }}>
          <button onClick={() => { user ? navigate('/career-guidance') : onLogin(); setActiveDropdown(null); }}>💼 Your Career</button>
          <button onClick={() => { user ? navigate('/marriage-analysis') : onLogin(); setActiveDropdown(null); }}>💍 Your Marriage</button>
          <button onClick={() => { user ? navigate('/education') : (onLogin && onLogin()); setActiveDropdown(null); }}>🎓 Your Education</button>
          <button onClick={() => { user ? navigate('/health-analysis') : onLogin(); setActiveDropdown(null); }}>🏥 Your Health</button>
          <button onClick={() => { user ? navigate('/wealth-analysis') : onLogin(); setActiveDropdown(null); }}>💰 Your Wealth</button>
        </div>
      )}

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
      
      {showMobileSearch && (
        <div className="mobile-search-modal" onClick={() => setShowMobileSearch(false)}>
          <div className="mobile-search-content" onClick={(e) => e.stopPropagation()}>
            <div className="mobile-search-header">
              <h3>Search</h3>
              <button className="close-search-btn" onClick={() => setShowMobileSearch(false)}>×</button>
            </div>
            <SearchBar user={user} onLogin={onLogin} />
          </div>
        </div>
      )}
    </header>
  );
};

export default NavigationHeader;