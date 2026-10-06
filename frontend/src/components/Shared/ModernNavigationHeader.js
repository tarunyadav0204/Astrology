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

const CALENDAR_LINKS = [
  ['/panchang', 'Today’s Panchang', 'Tithi, nakshatra, yoga and the day’s rhythm'],
  ['/festivals', 'Festivals', 'Hindu observances with lunar timing'],
  ['/festivals/monthly', 'Monthly calendar', 'Plan festivals and vrats across the month'],
  ['/monthly-panchang', 'Monthly Panchang', 'Wider month view of tithi and nakshatra'],
  ['/muhurat-finder', 'Muhurat', 'Find a considered window for beginnings'],
  ['/nakshatras', 'Nakshatras', 'The 27 lunar constellations'],
];

// Paid / account readings — linked directly so they are not buried mid-page
const READING_LINKS = [
  ['/career-guidance', 'Career', 'Strengths, turning points and timing'],
  ['/marriage-analysis', 'Marriage', 'Compatibility and relationship periods'],
  ['/wealth-analysis', 'Wealth', 'Earning patterns and financial cycles'],
  ['/health-analysis', 'Health', 'Constitution and supportive periods'],
  ['/life-events', 'Life timing', 'Dashas, transits and activation windows'],
  ['/karma-analysis', 'Past-life karma', 'Inherited patterns made practical'],
  ['/progeny-analysis', 'Progeny', 'Children and family-growth themes'],
  ['/education', 'Education', 'Learning patterns and examination periods'],
];

const ModernNavigationHeader = ({
  user,
  onLogin,
  onLogout,
  onAdminClick,
  onHomeClick,
  onOpenCurrentChart,
  sticky = true,
  showNativeBar = true,
}) => {
  const navigate = useNavigate();
  const { pathname } = useLocation();
  const { birthData } = useAstrology();
  const { credits, loading: creditsLoading, features } = useCredits();
  // Show the menu entry whenever the UI flag is on so guests can discover it.
  const partnerPortraitEnabled = Boolean(features?.partner_portrait_enabled);
  const { theme, themes, setTheme } = useTheme();
  const accountMenuRef = useRef(null);
  const themeMenuRef = useRef(null);
  const discoverMenuRef = useRef(null);
  const calendarMenuRef = useRef(null);
  const learnMenuRef = useRef(null);
  const mobileMenuRef = useRef(null);
  const [showCreditsModal, setShowCreditsModal] = useState(false);
  const [showBirthFormModal, setShowBirthFormModal] = useState(false);
  const [showSiteSearch, setShowSiteSearch] = useState(false);
  const [birthFormDefaultTab, setBirthFormDefaultTab] = useState('saved');

  const accountName = user?.name || user?.email || user?.phone || 'Your account';
  const sectionHref = (id) => `${pathname === '/' ? '' : '/'}#${id}`;

  const leaveShell = () => {
    onHomeClick?.();
  };

  const goHome = (event) => {
    closeMenus();
    if (!onHomeClick) return;
    event.preventDefault();
    onHomeClick();
    if (pathname !== '/') navigate('/');
  };

  const goSection = (id) => (event) => {
    closeMenus();
    if (!onHomeClick) return;
    event.preventDefault();
    onHomeClick();
    const applyHash = () => {
      const el = document.getElementById(id);
      if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
      window.history.replaceState(null, '', `/#${id}`);
    };
    if (pathname !== '/') navigate('/');
    window.setTimeout(applyHash, pathname === '/' ? 50 : 120);
  };

  useEffect(() => {
    const closeMenus = (event) => {
      const isEscape = event.type === 'keydown' && event.key === 'Escape';
      [accountMenuRef, themeMenuRef, discoverMenuRef, calendarMenuRef, learnMenuRef, mobileMenuRef].forEach((menuRef) => {
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
    calendarMenuRef.current?.removeAttribute('open');
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
    leaveShell();
    navigate('/charts-dashas');
  };

  const askTara = () => {
    closeMenus();
    if (!user) return onLogin?.();
    leaveShell();
    navigate('/chat?app=1');
  };

  const goSiteRoute = (to) => (event) => {
    if (!onHomeClick) return;
    event.preventDefault();
    closeMenus();
    leaveShell();
    navigate(to);
  };

  return (
    <>
      <div
        className={`ar-modern-nav-shell${sticky ? ' ar-modern-nav-shell--pin' : ''}${user && showNativeBar ? ' ar-modern-nav-shell--with-native' : ''}`}
      >
      <header className={`mh-nav ar-modern-nav ${sticky ? 'ar-modern-nav--sticky' : ''} ${user && showNativeBar ? 'ar-modern-nav--with-native' : ''}`} aria-label="Primary navigation">
        <div className="mh-nav__inner">
          <Link className="mh-brand" to="/" aria-label="AstroRoshni home" onClick={onHomeClick ? goHome : undefined}>
            <span className="mh-brand__mark" aria-hidden="true">
              <img src={SEO_CONFIG.images.logo} alt="" width="44" height="44" />
            </span>
            <span>AstroRoshni</span>
          </Link>

          <nav className="mh-nav__links" aria-label="Site sections">
            <Link className="mh-nav__workspace-link" to="/charts-dashas" onClick={goSiteRoute('/charts-dashas')}>
              Charts &amp; Dashas
            </Link>
            <details className="mh-nav-menu" ref={discoverMenuRef}>
              <summary>Readings</summary>
              <div className="mh-nav-menu__panel mh-nav-menu__panel--readings" onClick={closeMenus}>
                <a href={sectionHref('clarity')} onClick={onHomeClick ? goSection('clarity') : undefined}>
                  <span>All life themes</span>
                  <small>Browse career, wealth, marriage and more</small>
                </a>
                {READING_LINKS.map(([to, label, blurb]) => (
                  <Link key={to} to={to} onClick={goSiteRoute(to)}>
                    <span>{label}</span>
                    <small>{blurb}</small>
                  </Link>
                ))}
                <Link to="/kundli-matching" onClick={goSiteRoute('/kundli-matching')}>
                  <span>Kundli matching</span>
                  <small>Compare two charts for partnership</small>
                </Link>
                {partnerPortraitEnabled && (
                  <Link to="/partner-portrait" onClick={goSiteRoute('/partner-portrait')}>
                    <span>Partner Portrait</span>
                    <small>Meet the person your Kundli describes</small>
                  </Link>
                )}
                <Link to="/ai-kundli-generator" onClick={goSiteRoute('/ai-kundli-generator')}>
                  <span>Create Kundli</span>
                  <small>Calculate and save your Vedic chart</small>
                </Link>
                <Link to="/horoscope/daily" onClick={goSiteRoute('/horoscope/daily')}>
                  <span>Horoscope</span>
                  <small>Daily to yearly Sun-sign forecasts</small>
                </Link>
              </div>
            </details>
            <details className="mh-nav-menu" ref={calendarMenuRef}>
              <summary>Calendar</summary>
              <div className="mh-nav-menu__panel" onClick={closeMenus}>
                {CALENDAR_LINKS.map(([to, label, blurb]) => (
                  <Link key={to} to={to} onClick={goSiteRoute(to)}>
                    <span>{label}</span>
                    <small>{blurb}</small>
                  </Link>
                ))}
              </div>
            </details>
            <details className="mh-nav-menu" ref={learnMenuRef}>
              <summary>Learn</summary>
              <div className="mh-nav-menu__panel mh-nav-menu__panel--learn" onClick={closeMenus}>
                <a href={sectionHref('journal')} onClick={onHomeClick ? goSection('journal') : undefined}><span>Learning overview</span><small>Start with the essentials</small></a>
                <Link to="/beginners-guide" onClick={goSiteRoute('/beginners-guide')}><span>Beginner’s guide</span><small>Eight foundational lessons</small></Link>
                <Link to="/advanced-courses" onClick={goSiteRoute('/advanced-courses')}><span>Advanced courses</span><small>Go deeper into interpretation</small></Link>
                <Link to="/myths-vs-reality" onClick={goSiteRoute('/myths-vs-reality')}><span>Myths vs reality</span><small>Separate tradition from misconception</small></Link>
                <Link to="/lesson/1" onClick={goSiteRoute('/lesson/1')}><span>Start lesson one</span><small>What is astrology?</small></Link>
              </div>
            </details>
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
                  <button type="button" onClick={() => { leaveShell(); navigate('/profile'); }}>Profile <i aria-hidden>↗</i></button>
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
              <Link className="mh-mobile-menu__workspace" to="/charts-dashas" onClick={goSiteRoute('/charts-dashas')}>Charts &amp; Dashas</Link>
              <span className="mh-mobile-menu__label">Readings</span>
              <a href={sectionHref('clarity')} onClick={onHomeClick ? goSection('clarity') : undefined}>All life themes</a>
              {READING_LINKS.map(([to, label]) => (
                <Link key={to} to={to} onClick={goSiteRoute(to)}>{label}</Link>
              ))}
              <Link to="/kundli-matching" onClick={goSiteRoute('/kundli-matching')}>Kundli matching</Link>
              {partnerPortraitEnabled && <Link to="/partner-portrait" onClick={goSiteRoute('/partner-portrait')}>Partner Portrait</Link>}
              <Link to="/ai-kundli-generator" onClick={goSiteRoute('/ai-kundli-generator')}>Create Kundli</Link>
              <Link to="/horoscope/daily" onClick={goSiteRoute('/horoscope/daily')}>Horoscope</Link>
              <span className="mh-mobile-menu__label">Calendar</span>
              {CALENDAR_LINKS.map(([to, label]) => (
                <Link key={to} to={to} onClick={goSiteRoute(to)}>{label}</Link>
              ))}
              <span className="mh-mobile-menu__label">Learn</span>
              <a href={sectionHref('journal')} onClick={onHomeClick ? goSection('journal') : undefined}>Learning overview</a>
              <Link to="/beginners-guide" onClick={goSiteRoute('/beginners-guide')}>Beginner’s guide</Link>
              <Link to="/advanced-courses" onClick={goSiteRoute('/advanced-courses')}>Advanced courses</Link>
              <Link to="/myths-vs-reality" onClick={goSiteRoute('/myths-vs-reality')}>Myths vs reality</Link>
              <Link to="/lesson/1" onClick={goSiteRoute('/lesson/1')}>Start lesson one</Link>
              <button type="button" onClick={askTara}>Ask Tara</button>
              <button type="button" onClick={() => openBirthForm('new')}>Create Kundli</button>
              {user && <button type="button" onClick={() => openBirthForm('saved')}>Saved Kundlis</button>}
              {user && <button type="button" onClick={() => { leaveShell(); navigate('/profile'); }}>Profile</button>}
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
            <span className="mh-native-bar__label">Selected chart</span>
            <div className="mh-native-bar__subject">
              <i aria-hidden>{birthData?.name?.charAt(0)?.toUpperCase() || '+'}</i>
              <span><strong>{birthData?.name || 'Choose a birth chart'}</strong><small>{birthData?.place || 'Select a saved native to personalize every reading'}</small></span>
            </div>
            <div className="mh-native-bar__actions">
              {birthData && (
                <button type="button" className="mh-native-bar__open" onClick={openCurrentChart}>
                  Open chart <span aria-hidden>↗</span>
                </button>
              )}
              <button type="button" className="mh-native-bar__change" onClick={() => openBirthForm('saved')}>
                {birthData ? 'Change native' : 'Select Kundli'}
              </button>
            </div>
          </div>
        )}
      </header>
      </div>

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
