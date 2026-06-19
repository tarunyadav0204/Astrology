import React, { useEffect, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useCredits } from '../../context/CreditContext';
import SearchBar from '../Search/SearchBar';
import './NavigationHeader.css';

/** Logo mark: WebP + small PNG fallback (Lighthouse: avoid 1024² icon for 22–44px display). */
function BrandLogoIcon({ alt }) {
  return (
    <picture>
      <source type="image/webp" srcSet="/images/astroroshni-icon-96.webp" />
      <img
        src="/images/astroroshni-icon-96.png"
        alt={alt}
        className="logo-icon-img"
        width={96}
        height={96}
        decoding="async"
      />
    </picture>
  );
}

/** Full hamburger list: nav destinations + account (compact chat/webview + main header). */
function FullHamburgerMenuItems({
  navigate,
  onHomeClick,
  onAstrologyClick,
  onCreditsClick,
  onChangeNative,
  birthData,
  user,
  onLogin,
  onAdminClick,
  onLogout,
  showLoginButton,
  creditsLoading,
  credits,
  onClose,
  onBirthChartAction,
}) {
  return (
    <div className="mobile-menu-items">
      <button
        type="button"
        className="mobile-menu-item"
        onClick={() => {
          (onHomeClick || (() => navigate('/')))();
          onClose();
        }}
      >
        🏠 Home
      </button>

    <div className="mobile-menu-section-label">Birth Chart</div>
    <button type="button" className="mobile-menu-item mobile-menu-item--sub" onClick={() => { onBirthChartAction('create'); onClose(); }}>✨ Create birth chart</button>
    <button type="button" className="mobile-menu-item mobile-menu-item--sub" onClick={() => { onBirthChartAction('select'); onClose(); }}>👤 Select birth chart</button>

    <div className="mobile-menu-section-label">Your Life</div>
    <button type="button" className="mobile-menu-item mobile-menu-item--sub" onClick={() => { navigate('/career-guidance'); onClose(); }}>💼 Your Career</button>
    <button type="button" className="mobile-menu-item mobile-menu-item--sub" onClick={() => { navigate('/marriage-analysis'); onClose(); }}>💍 Your Marriage</button>
    <button type="button" className="mobile-menu-item mobile-menu-item--sub" onClick={() => { navigate('/progeny-analysis'); onClose(); }}>👶 Your Progeny</button>
    <button type="button" className="mobile-menu-item mobile-menu-item--sub" onClick={() => { navigate('/education'); onClose(); }}>🎓 Your Education</button>
    <button type="button" className="mobile-menu-item mobile-menu-item--sub" onClick={() => { navigate('/health-analysis'); onClose(); }}>🏥 Your Health</button>
    <button type="button" className="mobile-menu-item mobile-menu-item--sub" onClick={() => { navigate('/wealth-analysis'); onClose(); }}>💰 Your Wealth</button>
    <button type="button" className="mobile-menu-item mobile-menu-item--sub" onClick={() => { (user ? navigate('/life-events') : onLogin && onLogin()); onClose(); }}>📅 Life events</button>
    <button type="button" className="mobile-menu-item mobile-menu-item--sub" onClick={() => { navigate('/karma-analysis'); onClose(); }}>🕉️ Past life analysis</button>
    <button
      type="button"
      className="mobile-menu-item mobile-menu-item--sub"
      onClick={() => {
        if (onAstrologyClick) onAstrologyClick();
        else navigate('/#astrology');
        onClose();
      }}
    >
      ✨ Astrology
    </button>
    <button type="button" className="mobile-menu-item mobile-menu-item--sub" onClick={() => { navigate('/tools/ashtakavarga'); onClose(); }}>⊞ Ashtakavarga</button>
    <button type="button" className="mobile-menu-item mobile-menu-item--sub" onClick={() => { navigate('/kundli-matching', user ? undefined : { state: { openLogin: true } }); onClose(); }}>💕 Kundli matching</button>
    <button type="button" className="mobile-menu-item mobile-menu-item--sub" onClick={() => { navigate('/#numerology'); onClose(); }}>🔢 Numerology</button>

    <div className="mobile-menu-section-label">Explore</div>
    <Link to="/panchang" className="mobile-menu-item mobile-menu-item--sub" onClick={() => onClose()}>🌅 Panchang</Link>
    <button type="button" className="mobile-menu-item mobile-menu-item--sub" onClick={() => { navigate('/muhurat-finder'); onClose(); }}>⏳ Muhurat Finder</button>
    <button type="button" className="mobile-menu-item mobile-menu-item--sub" onClick={() => { navigate('/festivals'); onClose(); }}>🎉 Festivals</button>
    <button type="button" className="mobile-menu-item mobile-menu-item--sub" onClick={() => { navigate('/nakshatras'); onClose(); }}>⭐ Nakshatras</button>
    <button type="button" className="mobile-menu-item mobile-menu-item--sub" onClick={() => { navigate('/blog'); onClose(); }}>📝 Blogs</button>

    <div className="mobile-menu-section-label">Account</div>
    <button type="button" className="mobile-menu-item" onClick={() => { navigate('/subscription'); onClose(); }}>⭐ VIP membership</button>
    <button type="button" className="mobile-menu-item" onClick={() => { navigate('/order-management'); onClose(); }}>🧾 Orders & billing</button>
    <button type="button" className="mobile-menu-item" onClick={() => { navigate('/contact'); onClose(); }}>📧 Contact us</button>
    {user ? (
      <>
        {!creditsLoading && onCreditsClick && (
          <button type="button" className="mobile-menu-item" onClick={() => { onCreditsClick(); onClose(); }}>💳 Credits: {credits}</button>
        )}
        {birthData && birthData.name && onChangeNative && (
          <button type="button" className="mobile-menu-item" onClick={() => { onChangeNative(); onClose(); }}>👤 Change Native: {birthData.name}</button>
        )}
        <button type="button" className="mobile-menu-item" onClick={() => { navigate('/profile'); onClose(); }}>👤 Profile</button>
        {user.role === 'admin' && onAdminClick && (
          <button type="button" className="mobile-menu-item" onClick={() => { onAdminClick(); onClose(); }}>⚙️ Admin Panel</button>
        )}
        <button type="button" className="mobile-menu-item logout" onClick={() => { onClose(); onLogout && onLogout(); }}>🚪 Logout</button>
      </>
    ) : showLoginButton ? (
      <button type="button" className="mobile-menu-item" onClick={() => { onLogin(); onClose(); }}>🔑 Sign In / Sign Up</button>
    ) : null}
    </div>
  );
}

const NavigationHeader = ({ compact = false, variant, onPeriodChange, showZodiacSelector, zodiacSigns, selectedZodiac, onZodiacChange, user, onAdminClick, onLogout, onLogin, showLoginButton, onCreditsClick, onHomeClick, onChangeNative, birthData, onAstrologyClick, onCreateBirthChart, onSelectBirthChart }) => {
  const navigate = useNavigate();
  const { credits, loading: creditsLoading } = useCredits();
  const [showMobileSearch, setShowMobileSearch] = useState(false);
  const [activeDropdown, setActiveDropdown] = useState(null);
  const [dropdownPosition, setDropdownPosition] = useState({ top: 0, left: 0 });
  const [showMobileMenu, setShowMobileMenu] = useState(false);

  const applyBirthChartIntent = (mode) => {
    if (mode === 'create') {
      navigate('/ai-kundli-generator');
      return;
    }

    const cb = mode === 'create' ? onCreateBirthChart : onSelectBirthChart;
    if (cb) {
      cb();
      return;
    }

    // When already authenticated on a page that supports birth modal, stay on page.
    if (user && onChangeNative) {
      onChangeNative(mode);
      return;
    }

    if (!user) {
      try {
        sessionStorage.setItem('pendingBirthChart', mode);
      } catch (_) { /* ignore */ }
      if (onLogin) onLogin();
      else navigate(`/?birthChart=${mode}`);
      return;
    }

    // Fallback for legacy pages that don't expose modal callbacks.
    navigate(`/?birthChart=${mode}`);
  };

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



  if (compact) {
    return (
      <header className={`main-header compact${variant === 'chat' ? ' compact--chat' : ''}`}>
        <div className="compact-nav">
          <div className="container">
            <div className="compact-nav__brand-row">
              <button
                type="button"
                className="mobile-menu-btn compact-nav__menu-toggle compact-nav__menu-toggle--desktop"
                onClick={() => setShowMobileMenu(true)}
                aria-label="Open menu"
                aria-expanded={showMobileMenu}
              >
                ☰
              </button>
              <button className="logo-text" onClick={onHomeClick || (() => navigate('/'))}>
                <span className="logo-full">
                  <BrandLogoIcon alt="AstroRoshni" />
                  AstroRoshni
                </span>
                <span className="logo-short">
                  <BrandLogoIcon alt="AR" />
                  AR
                </span>
              </button>
              <button
                type="button"
                className="mobile-menu-btn compact-nav__menu-toggle compact-nav__menu-toggle--mobile"
                onClick={() => setShowMobileMenu(true)}
                aria-label="Open menu"
                aria-expanded={showMobileMenu}
              >
                ☰
              </button>
            </div>

            <nav className="compact-menu">
              <button onClick={onHomeClick || (() => navigate('/'))}>Home</button>
              <div className={`dropdown ${activeDropdown === 'birthchart' ? 'active' : ''}`}>
                <a href="#birthchart" className="dropdown-toggle" onClick={(e) => { e.preventDefault(); toggleDropdown('birthchart', e); }}>Birth Chart</a>
              </div>
              <div className={`dropdown ${activeDropdown === 'yourlife' ? 'active' : ''}`}>
                <a href="#yourlife" className="dropdown-toggle" onClick={(e) => { e.preventDefault(); toggleDropdown('yourlife', e); }}>Your Life</a>
              </div>
              <Link to="/panchang">Panchang</Link>
              <button onClick={() => navigate('/muhurat-finder')}>Muhurat</button>
              <button onClick={() => navigate('/festivals')}>Festivals</button>
              <button onClick={() => navigate('/nakshatras')}>Nakshatras</button>
              <button type="button" className="compact-menu__item compact-menu__item--wide" onClick={() => navigate('/kundli-matching', user ? undefined : { state: { openLogin: true } })}>Kundli matching</button>
              {onAstrologyClick ? (
                <button type="button" className="compact-menu__item compact-menu__item--optional" onClick={() => onAstrologyClick()}>Astrology</button>
              ) : (
                <a href="/#astrology" className="compact-menu__item compact-menu__item--optional">Astrology</a>
              )}
              <button type="button" className="compact-menu__item compact-menu__item--optional" onClick={() => navigate('/tools/ashtakavarga')}>Ashtakavarga</button>
              <button type="button" className="compact-menu__item compact-menu__item--optional compact-menu__item--low" onClick={() => navigate('/#numerology')}>Numerology</button>
              <button className="compact-menu__item compact-menu__item--optional compact-menu__item--low" onClick={() => navigate('/blog')}>Blogs</button>
            </nav>
            
            <div className="compact-actions">
              {user ? (
                <>
                  {!creditsLoading && onCreditsClick && (
                    <button type="button" className="credits-btn credits-btn--compact" onClick={onCreditsClick}>
                      <span className="credits-btn__icon" aria-hidden>💳</span>
                      <span className="credits-btn__value">{credits}</span>
                    </button>
                  )}
                  <button type="button" className="credits-btn nav-vip-btn credits-btn--compact" onClick={() => navigate('/subscription')}>
                    <span aria-hidden>⭐</span>
                    <span>VIP</span>
                  </button>
                  {birthData && birthData.name && onChangeNative && (
                    <button
                      type="button"
                      className="native-selector-chip"
                      onClick={onChangeNative}
                      title="Change native / chart"
                    >
                      <span className="native-selector-chip__icon" aria-hidden>👤</span>
                      <span className="native-selector-chip__name">{birthData.name}</span>
                      <span className="native-selector-chip__chevron" aria-hidden>▾</span>
                    </button>
                  )}
                </>
              ) : showLoginButton ? (
                <button className="auth-btn" onClick={onLogin}>Sign In</button>
              ) : null}
            </div>
          </div>
        </div>
        
        {activeDropdown === 'birthchart' && (
          <div className="dropdown-content" style={{ top: `${dropdownPosition.top}px`, left: `${dropdownPosition.left}px` }}>
            <button type="button" onClick={() => { applyBirthChartIntent('create'); setActiveDropdown(null); }}>✨ Create birth chart</button>
            <button type="button" onClick={() => { applyBirthChartIntent('select'); setActiveDropdown(null); }}>👤 Select birth chart</button>
          </div>
        )}

        {activeDropdown === 'yourlife' && (
          <div className="dropdown-content" style={{ top: `${dropdownPosition.top}px`, left: `${dropdownPosition.left}px` }}>
            <button onClick={() => { navigate('/career-guidance'); setActiveDropdown(null); }}>💼 Your Career</button>
            <button onClick={() => { navigate('/marriage-analysis'); setActiveDropdown(null); }}>💍 Your Marriage</button>
            <button onClick={() => { navigate('/progeny-analysis'); setActiveDropdown(null); }}>👶 Your Progeny</button>
            <button onClick={() => { navigate('/education'); setActiveDropdown(null); }}>🎓 Your Education</button>
            <button onClick={() => { navigate('/health-analysis'); setActiveDropdown(null); }}>🏥 Your Health</button>
            <button onClick={() => { navigate('/wealth-analysis'); setActiveDropdown(null); }}>💰 Your Wealth</button>
            <button onClick={() => { user ? navigate('/life-events') : onLogin(); setActiveDropdown(null); }}>📅 Life events</button>
            <button type="button" onClick={() => { navigate('/karma-analysis'); setActiveDropdown(null); }}>🕉️ Past life analysis</button>
          </div>
        )}
        
        {showMobileMenu && (
          <div className="mobile-menu-modal" role="presentation">
            <button
              type="button"
              className="mobile-menu-backdrop"
              onClick={() => setShowMobileMenu(false)}
              aria-label="Close menu"
            />
            <aside
              className="mobile-menu-drawer"
              role="dialog"
              aria-modal="true"
              aria-label="Site menu"
            >
              <div className="mobile-menu-header">
                <h3>Menu</h3>
                <button type="button" className="close-menu-btn" onClick={() => setShowMobileMenu(false)} aria-label="Close menu">
                  ×
                </button>
              </div>
              <div className="mobile-menu-drawer-body">
                <FullHamburgerMenuItems
                  navigate={navigate}
                  onHomeClick={onHomeClick}
                  onAstrologyClick={onAstrologyClick}
                  onCreditsClick={onCreditsClick}
                  onChangeNative={onChangeNative}
                  birthData={birthData}
                  user={user}
                  onLogin={onLogin}
                  onAdminClick={onAdminClick}
                  onLogout={onLogout}
                  showLoginButton={showLoginButton}
                  creditsLoading={creditsLoading}
                  credits={credits}
                  onClose={() => setShowMobileMenu(false)}
                  onBirthChartAction={applyBirthChartIntent}
                />
              </div>
            </aside>
          </div>
        )}
      </header>
    );
  }
  
  return (
    <header className="main-header">
      <div className="top-bar">
        <div className="container">
          <button
            type="button"
            className="mobile-menu-btn main-header__hamburger-desktop"
            onClick={() => setShowMobileMenu(true)}
            aria-label="Open menu"
            aria-expanded={showMobileMenu}
          >
            ☰
          </button>
          <div className="top-links">
            <a href="/calendar-2026" className="top-link">Calendar 2026</a>
            <a href="/contact" className="top-link">Contact us</a>
            {!user && <a href="/subscription" className="top-link">VIP membership</a>}
            {/* <a href="/astroroshni" target="_blank" className="astroroshni-link">
              ⭐ AstroVishnu Pro
            </a> */}
          </div>
          <div className="auth-section">
            {user ? (
              <div className="user-menu">
                {!creditsLoading && onCreditsClick && (
                  <button type="button" className="credits-btn" onClick={onCreditsClick}>
                    <span className="credits-btn__icon" aria-hidden>💳</span>
                    <span className="credits-btn__value">{credits}</span>
                  </button>
                )}
                <button type="button" className="credits-btn nav-vip-btn" onClick={() => navigate('/subscription')}>
                  <span aria-hidden>⭐</span>
                  <span>VIP</span>
                </button>
                <button type="button" className="credits-btn nav-orders-btn" onClick={() => navigate('/order-management')}>
                  <span aria-hidden>🧾</span>
                  <span>Orders</span>
                </button>
                <button
                  type="button"
                  className="profile-btn"
                  onClick={() => navigate('/profile')}
                  title={user.name || user.phone || 'Profile'}
                >
                  <span className="profile-btn__icon" aria-hidden>👤</span>
                  <span className="profile-btn__name">{user.name || user.phone}</span>
                </button>
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
              <span className="logo-full">
                <BrandLogoIcon alt="AstroRoshni" />
                AstroRoshni
              </span>
              <span className="logo-short">
                <BrandLogoIcon alt="AR" />
                AR
              </span>
            </button>
          </div>
          <SearchBar user={user} onLogin={onLogin} />
          <div className="mobile-actions-group">
            <button className="mobile-search-btn" onClick={() => setShowMobileSearch(true)}>
              🔍
            </button>
            {user && (
              <div className="mobile-actions-group__account">
                {!creditsLoading && onCreditsClick && (
                  <button type="button" className="credits-btn credits-btn--compact" onClick={onCreditsClick}>
                    <span className="credits-btn__icon" aria-hidden>💳</span>
                    <span className="credits-btn__value">{credits}</span>
                  </button>
                )}
                <button
                  type="button"
                  className="credits-btn nav-vip-btn credits-btn--compact"
                  onClick={() => navigate('/subscription')}
                >
                  <span aria-hidden>⭐</span>
                  <span>VIP</span>
                </button>
              </div>
            )}
            {user && birthData && birthData.name && onChangeNative && (
              <button
                type="button"
                className="native-selector-chip native-selector-chip--nav-mobile"
                onClick={onChangeNative}
                title={`Native: ${birthData.name} — tap to change`}
              >
                <span className="native-selector-chip__icon" aria-hidden>👤</span>
                <span className="native-selector-chip__name">{birthData.name}</span>
                <span className="native-selector-chip__chevron" aria-hidden>▾</span>
              </button>
            )}
            <button
              type="button"
              className="mobile-menu-btn main-header__hamburger-mobile"
              onClick={() => setShowMobileMenu(true)}
              aria-label="Open menu"
              aria-expanded={showMobileMenu}
            >
              ☰
            </button>
          </div>
        </div>
      </div>

      <nav className="navigation">
        <div className="container">
          <ul className="nav-menu">
            <li><button onClick={onHomeClick || (() => navigate('/'))}>Home</button></li>
            <li className={`dropdown ${activeDropdown === 'birthchart' ? 'active' : ''}`}>
              <a href="#birthchart" className="dropdown-toggle" onClick={(e) => { e.preventDefault(); toggleDropdown('birthchart', e); }}>Birth Chart</a>
            </li>
            <li className={`dropdown ${activeDropdown === 'yourlife' ? 'active' : ''}`}>
              <a href="#yourlife" className="dropdown-toggle" onClick={(e) => { e.preventDefault(); toggleDropdown('yourlife', e); }}>Your Life</a>
            </li>
            <li><Link to="/panchang">Panchang</Link></li>
            <li><button onClick={() => navigate('/muhurat-finder')}>Muhurat Finder</button></li>
            <li><button onClick={() => navigate('/festivals')}>Festivals</button></li>
            <li><button onClick={() => navigate('/nakshatras')}>Nakshatras</button></li>
            <li><button type="button" onClick={() => navigate('/kundli-matching', user ? undefined : { state: { openLogin: true } })}>Kundli matching</button></li>
            <li>
              {onAstrologyClick ? (
                <button type="button" onClick={() => onAstrologyClick()}>Astrology</button>
              ) : (
                <a href="/#astrology">Astrology</a>
              )}
            </li>
            <li><button type="button" onClick={() => navigate('/tools/ashtakavarga')}>Ashtakavarga</button></li>
            <li><button type="button" onClick={() => navigate('/#numerology')}>Numerology</button></li>
            <li><button onClick={() => navigate('/blog')}>Blogs</button></li>
            <li><button onClick={() => navigate('/contact')}>Contact us</button></li>
          </ul>
        </div>
      </nav>

      {/* Dropdown menus rendered outside navigation */}
      {activeDropdown === 'birthchart' && (
        <div className="dropdown-content" style={{ top: `${dropdownPosition.top}px`, left: `${dropdownPosition.left}px` }}>
          <button type="button" onClick={() => { applyBirthChartIntent('create'); setActiveDropdown(null); }}>✨ Create birth chart</button>
          <button type="button" onClick={() => { applyBirthChartIntent('select'); setActiveDropdown(null); }}>👤 Select birth chart</button>
        </div>
      )}

      {activeDropdown === 'yourlife' && (
        <div className="dropdown-content" style={{ top: `${dropdownPosition.top}px`, left: `${dropdownPosition.left}px` }}>
          <button onClick={() => { navigate('/career-guidance'); setActiveDropdown(null); }}>💼 Your Career</button>
          <button onClick={() => { navigate('/marriage-analysis'); setActiveDropdown(null); }}>💍 Your Marriage</button>
          <button onClick={() => { navigate('/progeny-analysis'); setActiveDropdown(null); }}>👶 Your Progeny</button>
          <button onClick={() => { navigate('/education'); setActiveDropdown(null); }}>🎓 Your Education</button>
          <button onClick={() => { navigate('/health-analysis'); setActiveDropdown(null); }}>🏥 Your Health</button>
          <button onClick={() => { navigate('/wealth-analysis'); setActiveDropdown(null); }}>💰 Your Wealth</button>
          <button onClick={() => { user ? navigate('/life-events') : onLogin(); setActiveDropdown(null); }}>📅 Life events</button>
          <button type="button" onClick={() => { navigate('/karma-analysis'); setActiveDropdown(null); }}>🕉️ Past life analysis</button>
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
      
      {showMobileMenu && (
        <div className="mobile-menu-modal" role="presentation">
          <button
            type="button"
            className="mobile-menu-backdrop"
            onClick={() => setShowMobileMenu(false)}
            aria-label="Close menu"
          />
          <aside
            className="mobile-menu-drawer"
            role="dialog"
            aria-modal="true"
            aria-label="Site menu"
          >
            <div className="mobile-menu-header">
              <h3>Menu</h3>
              <button type="button" className="close-menu-btn" onClick={() => setShowMobileMenu(false)} aria-label="Close menu">
                ×
              </button>
            </div>
            <div className="mobile-menu-drawer-body">
              <FullHamburgerMenuItems
                navigate={navigate}
                onHomeClick={onHomeClick}
                onAstrologyClick={onAstrologyClick}
                onCreditsClick={onCreditsClick}
                onChangeNative={onChangeNative}
                birthData={birthData}
                user={user}
                onLogin={onLogin}
                onAdminClick={onAdminClick}
                onLogout={onLogout}
                showLoginButton={showLoginButton}
                creditsLoading={creditsLoading}
                credits={credits}
                onClose={() => setShowMobileMenu(false)}
                onBirthChartAction={applyBirthChartIntent}
              />
            </div>
          </aside>
        </div>
      )}
    </header>
  );
};

export default NavigationHeader;
