import React, { useEffect, useRef, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { SEO_CONFIG } from '../../config/seo.config';
import { useAstrology } from '../../context/AstrologyContext';
import { useCredits } from '../../context/CreditContext';
import { useTheme } from '../../theme';
import BirthFormModal from '../BirthForm/BirthFormModal';
import CreditsModal from '../Credits/CreditsModal';
import ModernSiteSearch from '../Search/ModernSiteSearch';
import './ModernNavigationHeader.css';

const SECTION_LINKS = [
  ['your-day', 'Your day'],
  ['method', 'How it works'],
  ['clarity', 'Explore'],
  ['tools', 'Vedic tools'],
];

const ModernNavigationHeader = ({
  user,
  onLogin,
  onLogout,
  onAdminClick,
  onOpenCurrentChart,
  sticky = true,
  showNativeBar = true,
}) => {
  const navigate = useNavigate();
  const { pathname } = useLocation();
  const { birthData } = useAstrology();
  const { credits, loading: creditsLoading } = useCredits();
  const { theme, themes, setTheme } = useTheme();
  const accountMenuRef = useRef(null);
  const themeMenuRef = useRef(null);
  const discoverMenuRef = useRef(null);
  const learnMenuRef = useRef(null);
  const mobileMenuRef = useRef(null);
  const [showCreditsModal, setShowCreditsModal] = useState(false);
  const [showBirthFormModal, setShowBirthFormModal] = useState(false);
  const [showSiteSearch, setShowSiteSearch] = useState(false);
  const [birthFormDefaultTab, setBirthFormDefaultTab] = useState('saved');

  const accountName = user?.name || user?.email || user?.phone || 'Your account';
  const sectionHref = (id) => `${pathname === '/' ? '' : '/'}#${id}`;

  useEffect(() => {
    const closeMenus = (event) => {
      const isEscape = event.type === 'keydown' && event.key === 'Escape';
      [accountMenuRef, themeMenuRef, discoverMenuRef, learnMenuRef, mobileMenuRef].forEach((menuRef) => {
        const menu = menuRef.current;
        if (!menu?.open) return;
        if (isEscape || (event.type === 'pointerdown' && !menu.contains(event.target))) {
          menu.removeAttribute('open');
          if (isEscape) menu.querySelector('summary')?.focus();
        }
      });
    };

    document.addEventListener('pointerdown', closeMenus);
    document.addEventListener('keydown', closeMenus);
    return () => {
      document.removeEventListener('pointerdown', closeMenus);
      document.removeEventListener('keydown', closeMenus);
    };
  }, []);

  const closeMenus = () => {
    accountMenuRef.current?.removeAttribute('open');
    themeMenuRef.current?.removeAttribute('open');
    discoverMenuRef.current?.removeAttribute('open');
    learnMenuRef.current?.removeAttribute('open');
    mobileMenuRef.current?.removeAttribute('open');
  };

  const selectTheme = (themeId) => {
    setTheme(themeId);
    closeMenus();
  };

  const openBirthForm = (tab) => {
    if (!user) return onLogin?.();
    closeMenus();
    setBirthFormDefaultTab(tab);
    setShowBirthFormModal(true);
  };

  const openCurrentChart = () => {
    if (!birthData) return openBirthForm('saved');
    if (onOpenCurrentChart) return onOpenCurrentChart();
    navigate('/charts-dashas');
  };

  const askTara = () => {
    closeMenus();
    if (!user) return onLogin?.();
    navigate('/chat?app=1');
  };

  return (
    <>
      <header className={`mh-nav ar-modern-nav ${sticky ? 'ar-modern-nav--sticky' : ''} ${user && showNativeBar ? 'ar-modern-nav--with-native' : ''}`} aria-label="Primary navigation">
        <div className="mh-nav__inner">
          <Link className="mh-brand" to="/" aria-label="AstroRoshni home">
            <span className="mh-brand__mark" aria-hidden="true">
              <img src={SEO_CONFIG.images.logo} alt="" width="44" height="44" />
            </span>
            <span>AstroRoshni</span>
          </Link>

          <nav className="mh-nav__links" aria-label="Site sections">
            {SECTION_LINKS.map(([id, label]) => <a key={id} href={sectionHref(id)}>{label}</a>)}
            <details className="mh-nav-menu" ref={discoverMenuRef}>
              <summary>Discover</summary>
              <div className="mh-nav-menu__panel" onClick={closeMenus}>
                <a href={sectionHref('discover')}><span>Discover overview</span><small>Explore AstroRoshni</small></a>
                <Link to="/ai-kundli-generator"><span>Create Kundli</span><small>Calculate and save your Vedic chart</small></Link>
                <Link to="/horoscope/daily"><span>Horoscope</span><small>Daily to yearly Sun-sign forecasts</small></Link>
              </div>
            </details>
            <details className="mh-nav-menu" ref={learnMenuRef}>
              <summary>Learn</summary>
              <div className="mh-nav-menu__panel mh-nav-menu__panel--learn" onClick={closeMenus}>
                <a href={sectionHref('journal')}><span>Learning overview</span><small>Start with the essentials</small></a>
                <Link to="/beginners-guide"><span>Beginner’s guide</span><small>Eight foundational lessons</small></Link>
                <Link to="/advanced-courses"><span>Advanced courses</span><small>Go deeper into interpretation</small></Link>
                <Link to="/myths-vs-reality"><span>Myths vs reality</span><small>Separate tradition from misconception</small></Link>
                <Link to="/lesson/1"><span>Start lesson one</span><small>What is astrology?</small></Link>
              </div>
            </details>
            <Link to="/panchang">Panchang</Link>
          </nav>

          <div className="mh-nav__actions">
            {user?.role === 'admin' && (
              <button className="mh-text-button" type="button" onClick={onAdminClick}>Admin</button>
            )}
            <button className="mh-search-button" type="button" onClick={() => { closeMenus(); setShowSiteSearch(true); }} aria-label="Search AstroRoshni" title="Search">
              <svg aria-hidden="true" viewBox="0 0 24 24"><circle cx="10.8" cy="10.8" r="6.7"></circle><path d="m16 16 4.2 4.2"></path></svg>
            </button>
            <details className="mh-theme-menu" ref={themeMenuRef}>
              <summary aria-label={`Appearance: ${themes.find((item) => item.id === theme)?.label || 'Theme'}`} title="Change appearance">
                <svg aria-hidden="true" viewBox="0 0 24 24">
                  <path d="M12 3.25a8.75 8.75 0 1 0 0 17.5h1.4a1.85 1.85 0 0 0 .6-3.6l-.45-.15a1.35 1.35 0 0 1 .44-2.63h1.76A5 5 0 0 0 20.75 9.4C20.75 5.65 16.83 3.25 12 3.25Z" />
                  <circle cx="7.8" cy="10.1" r="1" />
                  <circle cx="10.1" cy="6.9" r="1" />
                  <circle cx="14.2" cy="6.9" r="1" />
                  <circle cx="17" cy="9.5" r="1" />
                </svg>
                <span className="mh-visually-hidden">Change theme</span>
              </summary>
              <div className="mh-theme-menu__panel" role="radiogroup" aria-label="Choose appearance">
                <div className="mh-theme-menu__heading">
                  <span>Appearance</span>
                  <small>Choose your AstroRoshni theme</small>
                </div>
                {themes.map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    role="radio"
                    aria-checked={theme === item.id}
                    className={theme === item.id ? 'is-active' : ''}
                    onClick={() => selectTheme(item.id)}
                  >
                    <i
                      className="mh-theme-menu__preview"
                      style={{
                        '--preview-canvas': item.preview.canvas,
                        '--preview-surface': item.preview.surface,
                        '--preview-accent': item.preview.accent,
                        '--preview-border': item.preview.border,
                      }}
                      aria-hidden
                    >
                      <span></span><span></span>
                    </i>
                    <span>{item.label}</span>
                    <b aria-hidden>{theme === item.id ? '✓' : ''}</b>
                  </button>
                ))}
              </div>
            </details>
            {user ? (
              <details className="mh-account-menu" ref={accountMenuRef}>
                <summary aria-label="Open account menu">
                  <span>{accountName.charAt(0).toUpperCase()}</span>
                  <strong>Account</strong>
                </summary>
                <div className="mh-account-menu__panel" onClick={closeMenus}>
                  <div className="mh-account-menu__identity"><span>Signed in as</span><strong>{accountName}</strong></div>
                  <button type="button" onClick={() => navigate('/profile')}>Profile <i aria-hidden>↗</i></button>
                  <button type="button" onClick={() => openBirthForm('saved')}>Saved Kundlis <i aria-hidden>↗</i></button>
                  <button type="button" onClick={() => setShowCreditsModal(true)}>Credits <b>{creditsLoading ? '—' : credits}</b></button>
                  <button type="button" onClick={onLogout}>Sign out</button>
                </div>
              </details>
            ) : (
              <button className="mh-text-button" type="button" onClick={onLogin}>Sign in</button>
            )}
            <button className="mh-primary-button mh-primary-button--nav" type="button" onClick={askTara}>
              Ask Tara <span aria-hidden>↗</span>
            </button>
          </div>

          <details className="mh-mobile-menu" ref={mobileMenuRef}>
            <summary aria-label="Open menu"><span></span><span></span></summary>
            <div className="mh-mobile-menu__panel" onClick={closeMenus}>
              {SECTION_LINKS.map(([id, label]) => <a key={id} href={sectionHref(id)}>{label}</a>)}
              <span className="mh-mobile-menu__label">Discover</span>
              <a href={sectionHref('discover')}>Discover overview</a>
              <Link to="/ai-kundli-generator">Create Kundli</Link>
              <Link to="/horoscope/daily">Horoscope</Link>
              <span className="mh-mobile-menu__label">Learn</span>
              <a href={sectionHref('journal')}>Learning overview</a>
              <Link to="/beginners-guide">Beginner’s guide</Link>
              <Link to="/advanced-courses">Advanced courses</Link>
              <Link to="/myths-vs-reality">Myths vs reality</Link>
              <Link to="/lesson/1">Start lesson one</Link>
              <Link to="/panchang">Panchang</Link>
              <button type="button" onClick={askTara}>Ask Tara</button>
              <button type="button" onClick={() => openBirthForm('new')}>Create Kundli</button>
              {user && <button type="button" onClick={() => openBirthForm('saved')}>Saved Kundlis</button>}
              {user && <button type="button" onClick={() => navigate('/profile')}>Profile</button>}
              {user && <button type="button" onClick={() => setShowCreditsModal(true)}>Credits · {creditsLoading ? '—' : credits}</button>}
              <div className="mh-mobile-theme" role="radiogroup" aria-label="Choose appearance" onClick={(event) => event.stopPropagation()}>
                <span>Appearance</span>
                <div>
                  {themes.map((item) => (
                    <button
                      key={item.id}
                      type="button"
                      role="radio"
                      aria-checked={theme === item.id}
                      className={theme === item.id ? 'is-active' : ''}
                      onClick={() => selectTheme(item.id)}
                    >
                      {item.label}
                    </button>
                  ))}
                </div>
              </div>
              {user?.role === 'admin' && <button type="button" onClick={onAdminClick}>Admin</button>}
              <button type="button" onClick={user ? onLogout : onLogin}>{user ? 'Sign out' : 'Sign in'}</button>
            </div>
          </details>
        </div>

        {user && showNativeBar && (
          <div className="mh-native-bar" aria-label="Current Kundli">
            <span className="mh-native-bar__label">Current Kundli</span>
            <button type="button" className="mh-native-bar__subject" onClick={openCurrentChart}>
              <i aria-hidden>{birthData?.name?.charAt(0)?.toUpperCase() || '+'}</i>
              <span><strong>{birthData?.name || 'Choose a birth chart'}</strong><small>{birthData?.place || 'Select a saved native to personalize every reading'}</small></span>
            </button>
            <button type="button" className="mh-native-bar__change" onClick={() => openBirthForm('saved')}>
              {birthData ? 'Change native' : 'Select Kundli'} <span aria-hidden>↗</span>
            </button>
          </div>
        )}
      </header>

      <BirthFormModal
        isOpen={showBirthFormModal}
        onClose={() => setShowBirthFormModal(false)}
        onSubmit={() => setShowBirthFormModal(false)}
        title="Choose your Kundli"
        description="Select a saved native or create a new Vedic birth chart"
        defaultActiveTab={birthFormDefaultTab}
      />
      <CreditsModal isOpen={showCreditsModal} onClose={() => setShowCreditsModal(false)} onLogin={onLogin} />
      <ModernSiteSearch isOpen={showSiteSearch} onClose={() => setShowSiteSearch(false)} user={user} onLogin={onLogin} />
    </>
  );
};

export default ModernNavigationHeader;
