import React, { useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react';
import { Helmet } from 'react-helmet-async';
import { Link, useNavigate } from 'react-router-dom';
import { SEO_CONFIG, buildHomeAccuracyProofStructuredData } from '../../config/seo.config';
import { useAstrology } from '../../context/AstrologyContext';
import { useCredits } from '../../context/CreditContext';
import partnerPortraitSample from '../../assets/partner-portrait/sample-woman-pair.jpg';
import partnerPortraitMaleSample from '../../assets/partner-portrait/sample-example.jpg';
import KpTodayHome from '../Home/KpTodayHome';
import ModernNavigationHeader from '../Shared/ModernNavigationHeader';
import LiveTransitRing from './LiveTransitRing';
import './ModernAstroRoshniHomepage.css';

const FOCUS_AREAS = [
  {
    key: 'career',
    number: '01',
    title: 'Your Career',
    text: 'See professional strengths, turning points and the timing behind your next move.',
    path: '/career-guidance',
    signal: 'D10 · Dashas · Transits',
  },
  {
    key: 'relationships',
    number: '02',
    title: 'Your Marriage',
    text: 'Understand compatibility, emotional patterns and meaningful relationship periods.',
    path: '/marriage-analysis',
    signal: 'D9 · 7th house · Venus',
  },
  {
    key: 'progeny',
    number: '03',
    title: 'Your Progeny',
    text: 'Explore children, parenthood potential, family growth and the timing surrounding these chapters.',
    path: '/progeny-analysis',
    signal: 'D7 · 5th house · Jupiter',
  },
  {
    key: 'education',
    number: '04',
    title: 'Your Education',
    text: 'Understand learning patterns, suitable fields, examination periods and the strengths behind growth.',
    path: '/education',
    signal: 'D24 · Mercury · 4th & 5th houses',
  },
  {
    key: 'wealth',
    number: '05',
    title: 'Your Wealth',
    text: 'Explore earning patterns, financial cycles and the periods that reward measured action.',
    path: '/wealth-analysis',
    signal: 'D2 · Yogas · Timing',
  },
  {
    key: 'health',
    number: '06',
    title: 'Your Health',
    text: 'Read constitutional tendencies and supportive periods through a whole-chart view.',
    path: '/health-analysis',
    signal: 'D1 · D6 · Planetary strength',
  },
  {
    key: 'timing',
    number: '07',
    title: 'Your Life Timing',
    text: 'Move beyond vague forecasts with layered dashas, transits and activation windows.',
    path: '/life-events',
    signal: 'Dashas · Transits · Activations',
  },
  {
    key: 'karma',
    number: '08',
    title: 'Past-life Karma',
    text: 'Explore inherited patterns, karmic strengths and the themes your chart asks you to understand more deeply.',
    path: '/karma-analysis',
    signal: 'D9 · D60 · Rahu–Ketu · 12th house',
  },
];

const HOME_FAQS = [
  {
    question: 'Is Tara AI astrology accurate?',
    answer: 'Tara is designed for personalized Vedic chart analysis. It reads dashas, transits, yogas, divisional charts, Ashtakavarga and nakshatra context together. Astrology remains guidance rather than a guarantee, but a complete chart is far more specific than generic horoscope text.',
  },
  {
    question: 'How is Tara different from a generic horoscope?',
    answer: 'A generic horoscope usually starts with one zodiac sign. Tara calculates your Kundli from your birth date, exact time and place, then answers against your own houses, Lagna, Moon, dashas, transits and chart strengths.',
  },
  {
    question: 'Can AstroRoshni match two Kundlis?',
    answer: 'Yes. Kundli Matching compares both birth charts for compatibility, relationship dynamics and classical matching factors. Both people’s date, time and place of birth produce the most useful result.',
  },
  {
    question: 'What does the progeny analysis cover?',
    answer: 'The progeny analysis studies children and parenthood themes using relevant houses, planetary strengths, timing periods and divisional-chart context. It is astrological guidance and does not replace medical advice.',
  },
  {
    question: 'What is included in past-life karma analysis?',
    answer: 'It examines karmic patterns through classical indicators including Rahu and Ketu, the 12th house, Navamsa and deeper divisional-chart themes, translating them into practical patterns to reflect on now.',
  },
  {
    question: 'What information do I need to create a Kundli?',
    answer: 'You need your date of birth, time of birth and place of birth. Accurate birth time improves the reliability of the Lagna, houses, nakshatra pada, dashas and divisional-chart interpretation.',
  },
];

const METHOD_LAYERS = [
  {
    label: 'Chart',
    title: 'Your sky, calculated precisely',
    copy: 'Birth time and place become an astronomical map using Swiss Ephemeris precision—not a generic Sun-sign profile.',
    stat: 'Planetary positions',
    value: 'Swiss Ephemeris',
  },
  {
    label: 'Synthesis',
    title: 'Four traditions, one coherent answer',
    copy: 'Every answer combines Parashari, Nadi, Jaimini and KP astrology, connecting houses, strength, yogas, divisionals and significators instead of reading any signal alone.',
    stat: 'Analysis layers & calculators',
    value: '90+',
  },
  {
    label: 'Timing',
    title: 'Patterns placed on a timeline',
    copy: 'Vimshottari, Yogini, Chara and transit activations turn potential into useful windows for reflection and action.',
    stat: 'Timing systems',
    value: 'Multi-dasha',
  },
];

const TOOLS = [
  { code: 'PA', title: 'Parashari Desk', text: 'Charts, divisionals, dashas and activation layers.', path: '/charts-dashas' },
  { code: 'KP', title: 'KP Desk', text: 'Cusps, significators and event-level timing.', path: '/charts-dashas/kp' },
  { code: 'NA', title: 'Nadi Desk', text: 'Karakas, planetary links and age activation.', path: '/charts-dashas/nadi' },
  { code: 'AV', title: 'Ashtakavarga', text: 'Bindus, strength and transit comparison.', path: '/ashtakavarga' },
  { code: 'DA', title: 'Dasha Browser', text: 'Navigate major and nested planetary periods.', path: '/charts-dashas' },
  { code: 'RS', title: 'Reports Studio', text: 'Focused readings built around your saved chart.', path: '/reports' },
];

const DISCOVERY_PATHS = [
  { number: '01', title: 'Nakshatra Guide', text: 'Meet the 27 lunar constellations and the temperament, purpose and timing held in each.', path: '/nakshatras' },
  { number: '02', title: 'Festival Calendar', text: 'Follow observances through their tithi, lunar context and traditional significance.', path: '/festivals' },
  { number: '03', title: 'Monthly Panchang', text: 'Plan ahead with a wider view of tithi, nakshatra and the rhythm of the month.', path: '/monthly-panchang' },
];

const LEARNING_FALLBACK = [
  { title: 'Beginner’s Guide to Vedic Astrology', category: 'Start here', excerpt: 'Build a clear foundation in planets, signs, houses, nakshatras and timing systems.', path: '/beginners-guide' },
  { title: 'What Your Moon Nakshatra Reveals', category: 'Nakshatra', excerpt: 'Understand why your birth star matters for temperament, compatibility and dasha timing.', path: '/nakshatras' },
  { title: 'How to Read Your Daily Panchang', category: 'Panchang', excerpt: 'Learn how tithi, nakshatra, yoga and karana describe the texture of a day.', path: '/panchang' },
];

const FOOTER_GROUPS = [
  {
    title: 'Readings',
    links: [
      ['Career guidance', '/career-guidance'],
      ['Marriage analysis', '/marriage-analysis'],
      ['Wealth analysis', '/wealth-analysis'],
      ['Health analysis', '/health-analysis'],
      ['Life timing', '/life-events'],
      ['Past-life karma', '/karma-analysis'],
      ['Progeny analysis', '/progeny-analysis'],
      ['Education', '/education'],
    ],
  },
  {
    title: 'Vedic tools',
    links: [
      ['Panchang', '/panchang'],
      ['Festivals', '/festivals'],
      ['Monthly calendar', '/festivals/monthly'],
      ['Muhurat', '/muhurat-finder'],
      ['Nakshatras', '/nakshatras'],
      ['Ashtakavarga', '/ashtakavarga'],
    ],
  },
  {
    title: 'AstroRoshni',
    links: [
      ['About Us', '/about'],
      ['Journal', '/blog'],
      ['Contact Us', '/contact'],
      ['Privacy Policy', '/policy'],
      ['Terms & Conditions', '/terms'],
      ['Android app', SEO_CONFIG.mobileApp.playStoreUrl, true],
    ],
  },
];

const FOOTER_SOCIALS = [
  { label: 'Instagram', href: 'https://instagram.com/astroroshniai', icon: 'instagram' },
  { label: 'Facebook', href: 'https://www.facebook.com/AstroRoshni/', icon: 'facebook' },
  { label: 'X', href: 'https://x.com/astroroshni', icon: 'x' },
  { label: 'LinkedIn', href: 'https://www.linkedin.com/company/astroroshni', icon: 'linkedin' },
];

const FooterSocialIcon = ({ name }) => {
  if (name === 'instagram') {
    return <svg aria-hidden="true" viewBox="0 0 24 24"><rect x="3.5" y="3.5" width="17" height="17" rx="5" /><circle cx="12" cy="12" r="4" /><circle cx="17.5" cy="6.7" r="1" /></svg>;
  }
  if (name === 'facebook') {
    return <svg aria-hidden="true" viewBox="0 0 24 24"><path d="M14.2 21v-8h2.7l.4-3h-3.1V8.1c0-.9.3-1.5 1.6-1.5h1.7V3.9c-.3 0-1.3-.1-2.5-.1-2.5 0-4.2 1.5-4.2 4.3V10H8v3h2.8v8h3.4Z" /></svg>;
  }
  if (name === 'linkedin') {
    return <svg aria-hidden="true" viewBox="0 0 24 24"><path d="M6.3 8.3H3.2V21h3.1V8.3ZM4.8 3A1.8 1.8 0 1 0 4.8 6.6 1.8 1.8 0 0 0 4.8 3ZM21 13.7c0-3.8-2-5.6-4.7-5.6-2.2 0-3.2 1.2-3.7 2V8.3H9.5V21h3.1v-6.3c0-1.7.3-3.3 2.4-3.3 2 0 2 1.9 2 3.4V21H21v-7.3Z" /></svg>;
  }
  return <svg aria-hidden="true" viewBox="0 0 24 24"><path d="M4 4h4.6l4.2 5.8L17.7 4H20l-6.1 7.5L20.7 21h-4.6l-4.7-6.5L6.1 21H3.8l6.5-8.2L4 4Zm3.4 1.8 9.7 13.4h1.7L9.1 5.8H7.4Z" /></svg>;
};

const ModernAstroRoshniHomepage = ({
  user,
  onLogin,
  onLogout,
  onAdminClick,
}) => {
  const navigate = useNavigate();
  const { birthData, chartData } = useAstrology();
  const { features, partnerPortraitCost } = useCredits();
  // Discovery card should excite visitors before login; the portrait page
  // itself prompts sign-in when they try to generate.
  const showPartnerPortrait = Boolean(features?.partner_portrait_enabled);
  const partnerSample = ['female', 'woman', 'f', 'girl'].includes(String(birthData?.gender || '').trim().toLowerCase())
    ? partnerPortraitMaleSample
    : partnerPortraitSample;
  const [focusKey, setFocusKey] = useState('career');
  const [methodIndex, setMethodIndex] = useState(0);
  const [latestArticles, setLatestArticles] = useState([]);
  const [verifiedTestimonials, setVerifiedTestimonials] = useState([]);
  const [showIosInstallGuide, setShowIosInstallGuide] = useState(false);
  const focusDetailRef = useRef(null);
  const focusTouchedRef = useRef(false);
  const selectedFocus = useMemo(
    () => FOCUS_AREAS.find((area) => area.key === focusKey) || FOCUS_AREAS[0],
    [focusKey]
  );
  const activeMethod = METHOD_LAYERS[methodIndex];

  const selectFocus = (key) => {
    focusTouchedRef.current = true;
    setFocusKey(key);
  };

  useEffect(() => {
    if (!focusTouchedRef.current || !focusDetailRef.current) return undefined;
    if (typeof window === 'undefined' || !window.matchMedia('(max-width: 900px)').matches) {
      return undefined;
    }
    const frame = window.requestAnimationFrame(() => {
      focusDetailRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    });
    return () => window.cancelAnimationFrame(frame);
  }, [focusKey]);

  useEffect(() => {
    document.body.classList.add('modern-homepage-active');
    return () => document.body.classList.remove('modern-homepage-active');
  }, []);

  useLayoutEffect(() => {
    if (!['#mobile-app', '#begin'].includes(window.location.hash)) return undefined;
    let secondFrame;
    const firstFrame = window.requestAnimationFrame(() => {
      secondFrame = window.requestAnimationFrame(() => {
        document.getElementById('mobile-app')?.scrollIntoView({ block: 'start', behavior: 'auto' });
      });
    });
    return () => {
      window.cancelAnimationFrame(firstFrame);
      if (secondFrame) window.cancelAnimationFrame(secondFrame);
    };
  }, []);

  useEffect(() => {
    if (!showIosInstallGuide) return undefined;
    const previousOverflow = document.body.style.overflow;
    const closeOnEscape = (event) => {
      if (event.key === 'Escape') setShowIosInstallGuide(false);
    };
    document.body.style.overflow = 'hidden';
    document.addEventListener('keydown', closeOnEscape);
    return () => {
      document.body.style.overflow = previousOverflow;
      document.removeEventListener('keydown', closeOnEscape);
    };
  }, [showIosInstallGuide]);

  useLayoutEffect(() => {
    const page = document.querySelector('.mh-page');
    const scrollRoot = page?.querySelector('.mh-scroll');
    if (!page || !scrollRoot) return undefined;

    const targets = Array.from(page.querySelectorAll([
      '.mh-scroll > .mh-chapter > :not(.mh-ambient):not(.mh-scroll-cue)',
      '.mh-scroll > .mh-faq > *',
      '.mh-scroll > .mh-footer > *',
    ].join(',')));
    const parentCounts = new Map();

    targets.forEach((target) => {
      const order = parentCounts.get(target.parentElement) || 0;
      parentCounts.set(target.parentElement, order + 1);
      target.classList.add('mh-reveal');
      target.style.setProperty('--mh-reveal-delay', `${Math.min(order, 3) * 110}ms`);
    });
    page.classList.add('mh-motion-ready');

    const reducedMotion = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
    if (reducedMotion || !('IntersectionObserver' in window)) {
      targets.forEach((target) => target.classList.add('is-visible'));
      return () => {
        page.classList.remove('mh-motion-ready');
        targets.forEach((target) => {
          target.classList.remove('mh-reveal', 'is-visible');
          target.style.removeProperty('--mh-reveal-delay');
        });
      };
    }

    // Always observe against the homepage scrollport so footer/chapter reveals
    // still fire on tablet after layout switches away from window scrolling.
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add('is-visible');
        observer.unobserve(entry.target);
      });
    }, {
      root: scrollRoot,
      rootMargin: '0px 0px -6% 0px',
      threshold: 0.08,
    });

    targets.forEach((target) => observer.observe(target));

    // Footer is below the fold and easy to miss if an early layout pass
    // reports zero intersection — keep it readable either way.
    page.querySelectorAll('.mh-footer .mh-reveal').forEach((target) => {
      target.classList.add('is-visible');
      observer.unobserve(target);
    });

    return () => {
      observer.disconnect();
      page.classList.remove('mh-motion-ready');
      targets.forEach((target) => {
        target.classList.remove('mh-reveal', 'is-visible');
        target.style.removeProperty('--mh-reveal-delay');
      });
    };
  }, []);

  useEffect(() => {
    let cancelled = false;

    fetch('/api/blog/posts?status=published')
      .then((response) => (response.ok ? response.json() : Promise.reject(new Error('Articles unavailable'))))
      .then((data) => {
        if (!cancelled && Array.isArray(data)) setLatestArticles(data.slice(0, 3));
      })
      .catch(() => {
        if (!cancelled) setLatestArticles([]);
      });

    fetch('/api/testimonials?limit=6')
      .then((response) => (response.ok ? response.json() : Promise.reject(new Error('Reviews unavailable'))))
      .then((data) => {
        if (!cancelled && Array.isArray(data.testimonials)) {
          setVerifiedTestimonials(data.testimonials.filter((item) => item?.name && item?.text).slice(0, 3));
        }
      })
      .catch(() => {
        if (!cancelled) setVerifiedTestimonials([]);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const requireAccount = (path) => {
    if (!user) {
      onLogin?.();
      return;
    }
    navigate(path);
  };

  const askTara = () => requireAccount('/chat?app=1');
  const learningCards = latestArticles.length > 0
    ? latestArticles.map((article) => ({
        ...article,
        category: article.category || 'Journal',
        excerpt: article.excerpt || String(article.content || '').replace(/[#*[\]()]/g, '').slice(0, 150),
        path: article.slug ? `/blog/${article.slug}` : '/blog',
      }))
    : LEARNING_FALLBACK;

  return (
    <div className={user ? 'mh-page mh-page--with-native' : 'mh-page'}>
      <Helmet>
        <title>{SEO_CONFIG.pages.home.title}</title>
        <meta name="description" content={SEO_CONFIG.pages.home.description} />
        <meta name="keywords" content={SEO_CONFIG.pages.home.keywords} />
        <meta name="theme-color" content="#210b17" />
        <meta property="og:title" content={SEO_CONFIG.pages.home.title} />
        <meta property="og:description" content={SEO_CONFIG.pages.home.description} />
        <meta property="og:image" content={`${SEO_CONFIG.site.url}/images/astroroshni-modern-og.png`} />
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:image" content={`${SEO_CONFIG.site.url}/images/astroroshni-modern-og.png`} />
        <link rel="canonical" href={SEO_CONFIG.site.url} />
        <script type="application/ld+json">
          {JSON.stringify(buildHomeAccuracyProofStructuredData())}
        </script>
      </Helmet>

      <ModernNavigationHeader
        user={user}
        onLogin={onLogin}
        onLogout={onLogout}
        onAdminClick={onAdminClick}
      />

      <main className="mh-scroll" data-seo-page="home">
        <section className="mh-chapter mh-hero" id="top">
          <div className="mh-ambient mh-ambient--one" aria-hidden></div>
          <div className="mh-ambient mh-ambient--two" aria-hidden></div>
          <div className="mh-hero__copy">
            <p className="mh-eyebrow"><span></span> Vedic intelligence, made personal</p>
            <h1>Your chart is not a horoscope. <em>It&rsquo;s a map.</em></h1>
            <p className="mh-hero__lead">
              Tara interprets your complete Vedic chart to reveal patterns, timing and possibilities unique to you.
            </p>
            <div className="mh-hero__actions">
              {user && birthData ? (
                <>
                  <button className="mh-primary-button" type="button" onClick={askTara}>
                    Ask Tara <span aria-hidden>↗</span>
                  </button>
                  <button className="mh-secondary-button" type="button" onClick={() => navigate('/charts-dashas')}>
                    Open Charts &amp; Dashas
                  </button>
                </>
              ) : (
                <>
                  <button className="mh-primary-button" type="button" onClick={askTara}>Ask Tara <span aria-hidden>↗</span></button>
                  <Link className="mh-secondary-button" to="/ai-kundli-generator">
                    Create free Kundli
                  </Link>
                </>
              )}
            </div>
            <div className="mh-proof-line" aria-label="Calculation credentials">
              <span>Swiss Ephemeris</span><i></i><span>90+ analysis layers</span><i></i><span>Four-system synthesis</span>
            </div>
          </div>

          <div className="mh-hero__visual" aria-label="Live sidereal transit visualization">
            <LiveTransitRing birthData={birthData} chartData={chartData} />
          </div>
          <a className="mh-scroll-cue" href="#your-day"><span>See your day</span><i aria-hidden></i></a>
        </section>

        <section className="mh-chapter mh-day" id="your-day">
          <div className="mh-section-heading">
            <p className="mh-eyebrow"><span></span> Personal timing</p>
            <h2>Your day,<br /><em>in context.</em></h2>
            <p>Begin with your own chart-aware themes, then move into today&rsquo;s Panchang, Muhurat and broader horoscope.</p>
          </div>
          <div className="mh-day__content">
            <div className="mh-day__personal">
              <KpTodayHome
                user={user}
                birthData={birthData}
                onLogin={onLogin}
                onNeedBirth={() => navigate('/ai-kundli-generator')}
                displayMode="inline"
              />
            </div>
            <div className="mh-day__links">
              <button type="button" onClick={() => navigate('/panchang')}>
                <span>01</span><strong>Today&rsquo;s Panchang</strong><p>Tithi, nakshatra, yoga and the rhythm of the day.</p><i aria-hidden>↗</i>
              </button>
              <button type="button" onClick={() => navigate('/muhurat-finder')}>
                <span>02</span><strong>Muhurat Finder</strong><p>Find a considered window for important beginnings.</p><i aria-hidden>↗</i>
              </button>
              <button type="button" onClick={() => navigate('/horoscope/daily')}>
                <span>03</span><strong>Daily Horoscope</strong><p>A quick Sun-sign view before your deeper chart reading.</p><i aria-hidden>↗</i>
              </button>
            </div>
          </div>
        </section>

        <section className="mh-chapter mh-method" id="method">
          <div className="mh-section-heading">
            <p className="mh-eyebrow"><span></span> How Tara thinks</p>
            <h2>Ancient knowledge.<br /><em>Modern synthesis.</em></h2>
            <p>Every answer synthesizes Parashari, Nadi, Jaimini and KP astrology across 90+ analysis layers and calculators—so the prediction comes from the complete chart, not one placement.</p>
          </div>
          <div className="mh-method__stage">
            <div className="mh-method__rail" role="tablist" aria-label="Tara calculation layers">
              {METHOD_LAYERS.map((layer, index) => (
                <button
                  key={layer.label}
                  className={index === methodIndex ? 'is-active' : ''}
                  type="button"
                  role="tab"
                  aria-selected={index === methodIndex}
                  onClick={() => setMethodIndex(index)}
                >
                  <span>0{index + 1}</span>{layer.label}
                </button>
              ))}
            </div>
            <div className="mh-method__panel" key={activeMethod.label}>
              <div className="mh-method__glyph" aria-hidden><span>{methodIndex + 1}</span><i></i><b></b></div>
              <div className="mh-method__content">
                <p className="mh-panel-label">Layer 0{methodIndex + 1}</p>
                <h3>{activeMethod.title}</h3>
                <p>{activeMethod.copy}</p>
                <div className="mh-method__stat"><span>{activeMethod.stat}</span><strong>{activeMethod.value}</strong></div>
                <button className="mh-primary-button mh-method__cta" type="button" onClick={askTara}>
                  Ask Tara using your chart <span aria-hidden>↗</span>
                </button>
              </div>
            </div>
          </div>
        </section>

        <section className="mh-chapter mh-clarity" id="clarity">
          <div className="mh-section-heading mh-section-heading--light">
            <p className="mh-eyebrow"><span></span> Begin with a question</p>
            <h2>What would you like<br /><em>clarity on?</em></h2>
          </div>
          <div className="mh-focus-layout">
            <div className="mh-focus-list" role="list">
              {FOCUS_AREAS.map((area) => {
                const isActive = area.key === focusKey;
                return (
                  <div
                    key={area.key}
                    className={isActive ? 'mh-focus-item is-active' : 'mh-focus-item'}
                    role="listitem"
                  >
                    <button
                      className={isActive ? 'mh-focus-row is-active' : 'mh-focus-row'}
                      type="button"
                      aria-expanded={isActive}
                      onClick={() => selectFocus(area.key)}
                    >
                      <span>{area.number}</span><strong>{area.title}</strong><i aria-hidden>{isActive ? '▾' : '↗'}</i>
                    </button>
                    {isActive && (
                      <div
                        className="mh-focus-detail mh-focus-detail--inline"
                        ref={focusDetailRef}
                        aria-live="polite"
                      >
                        <p className="mh-panel-label">Selected theme · {area.number}</p>
                        <h3>{area.title}</h3>
                        <p>{area.text}</p>
                        <div className="mh-focus-signal"><span>Chart signals</span><strong>{area.signal}</strong></div>
                        <button className="mh-primary-button" type="button" onClick={() => requireAccount(area.path)}>
                          Explore {area.title.toLowerCase()} <span aria-hidden>↗</span>
                        </button>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
            <div className="mh-focus-detail mh-focus-detail--aside" key={selectedFocus.key} aria-live="polite">
              <p className="mh-panel-label">Selected theme · {selectedFocus.number}</p>
              <h3>{selectedFocus.title}</h3>
              <p>{selectedFocus.text}</p>
              <div className="mh-focus-signal"><span>Chart signals</span><strong>{selectedFocus.signal}</strong></div>
              <button className="mh-primary-button" type="button" onClick={() => requireAccount(selectedFocus.path)}>
                Explore {selectedFocus.title.toLowerCase()} <span aria-hidden>↗</span>
              </button>
            </div>
          </div>
        </section>

        <section className="mh-chapter mh-tools" id="tools">
          <div className="mh-section-heading">
            <p className="mh-eyebrow"><span></span> Professional workspaces</p>
            <h2>Go deeper than<br /><em>a single reading.</em></h2>
            <p>Dedicated Vedic desks for people who want to inspect the calculation, not only receive the conclusion.</p>
          </div>
          <div className="mh-tools-grid">
            {TOOLS.map((tool, index) => (
              <button type="button" className="mh-tool-card" key={tool.title} onClick={() => tool.public ? navigate(tool.path) : requireAccount(tool.path)}>
                <span className="mh-tool-card__index">0{index + 1}</span>
                <span className="mh-tool-card__code">{tool.code}</span>
                <strong>{tool.title}</strong>
                <p>{tool.text}</p>
                <i aria-hidden>↗</i>
              </button>
            ))}
          </div>
        </section>

        <section className="mh-chapter mh-discover" id="discover">
          {showPartnerPortrait ? <div className="mh-discover__feature mh-discover__portrait">
            <img src={partnerSample} alt="" aria-hidden="true" />
            <div>
              <p className="mh-eyebrow"><span></span> New · Created from your Kundli</p>
              <h2>Meet the person<br /><em>your chart describes.</em></h2>
              <p>Create face and full-body portraits, then discover the appearance, personality and classical chart logic that shaped them.</p>
              <ul><li>Two original portraits</li><li>Appearance and personality synthesis</li><li>Classical factors and references</li></ul>
              <button className="mh-primary-button" type="button" onClick={() => navigate('/partner-portrait')}>Create my partner&rsquo;s portrait · {partnerPortraitCost} credits <span aria-hidden>↗</span></button>
            </div>
          </div> : <div className="mh-discover__feature mh-discover__karma">
            <div className="mh-karma-mark" aria-hidden><span>R</span><b>K</b><i></i></div>
            <p className="mh-eyebrow"><span></span> Patterns beneath the present</p>
            <h2>Past-life karma,<br /><em>made practical.</em></h2>
            <p>Explore inherited patterns through Rahu–Ketu, the 12th house and deeper divisional-chart themes—then connect them to choices you can make now.</p>
            <ul><li>Karmic strengths and inherited patterns</li><li>Lessons repeating in the present</li><li>Practical reflection and remedies</li></ul>
            <button className="mh-primary-button" type="button" onClick={() => requireAccount('/karma-analysis')}>Explore past-life karma <span aria-hidden>↗</span></button>
          </div>}
          <div className="mh-discover__calendar">
            <div className="mh-section-heading">
              <p className="mh-eyebrow"><span></span> Lunar knowledge</p>
              <h2>Follow the sky&rsquo;s<br /><em>living calendar.</em></h2>
              <p>Move from personal chart interpretation into the lunar markers that structure traditional time.</p>
            </div>
            <div className="mh-discovery-list">
              {DISCOVERY_PATHS.map((item) => (
                <button type="button" key={item.title} onClick={() => navigate(item.path)}>
                  <span>{item.number}</span><div><strong>{item.title}</strong><p>{item.text}</p></div><i aria-hidden>↗</i>
                </button>
              ))}
            </div>
          </div>
        </section>

        <section className="mh-chapter mh-match" id="matching">
          <div className="mh-match__copy">
            <p className="mh-eyebrow"><span></span> Two charts, one relationship</p>
            <h2>Kundli matching,<br /><em>beyond a score.</em></h2>
            <p>
              Compare two complete birth charts for emotional rhythm, shared strengths, classical compatibility and the timing surrounding partnership.
            </p>
            <div className="mh-match__points">
              <span>Guna Milan</span><span>Manglik analysis</span><span>Chart-to-chart synthesis</span>
            </div>
            <button className="mh-primary-button" type="button" onClick={() => navigate('/kundli-matching')}>
              Match two Kundlis <span aria-hidden>↗</span>
            </button>
          </div>
          <div className="mh-match__visual" aria-label="Two birth charts connected for compatibility analysis">
            <div className="mh-match-chart mh-match-chart--one" aria-hidden><span>A</span><i></i><b></b></div>
            <div className="mh-match-bridge" aria-hidden><span>36</span><small>CLASSICAL FACTORS</small></div>
            <div className="mh-match-chart mh-match-chart--two" aria-hidden><span>B</span><i></i><b></b></div>
            <div className="mh-match__result">
              <span>Compatibility synthesis</span>
              <strong>Patterns, strengths and timing—read together.</strong>
            </div>
          </div>
        </section>

        <section className="mh-chapter mh-journal" id="journal">
          <div className="mh-journal__heading">
            <p className="mh-eyebrow"><span></span> Learn with AstroRoshni</p>
            <h2>Ideas worth<br /><em>returning to.</em></h2>
            <p>Clear guides for understanding your chart—not content written merely to predict the next thing.</p>
            <Link className="mh-inline-link" to="/blog">Explore the journal <span aria-hidden>↗</span></Link>
          </div>
          <div className="mh-journal__body">
            <div className="mh-article-grid">
              {learningCards.map((article, index) => (
                <Link className="mh-article-card" to={article.path} key={article.id || article.slug || article.title}>
                  <span><small>0{index + 1}</small>{article.category}</span>
                  <h3>{article.title}</h3>
                  <p>{article.excerpt}</p>
                  <i aria-hidden>Read ↗</i>
                </Link>
              ))}
            </div>
            <div className="mh-voices" aria-labelledby="mh-voices-title">
              <div className="mh-voices__heading">
                <div><span>Verified voices</span><h3 id="mh-voices-title">From the AstroRoshni community</h3></div>
                <a href={SEO_CONFIG.mobileApp.playStoreUrl} target="_blank" rel="noopener noreferrer">Google Play <span aria-hidden>↗</span></a>
              </div>
              {verifiedTestimonials.length > 0 ? (
                <div className="mh-voices__grid">
                  {verifiedTestimonials.map((testimonial, index) => (
                    <blockquote key={testimonial.id || `${testimonial.name}-${index}`}>
                      <div><span aria-label={`${Math.max(1, Math.min(5, Number(testimonial.rating) || 5))} out of 5 stars`}>{'★'.repeat(Math.max(1, Math.min(5, Number(testimonial.rating) || 5)))}</span><small>Google Play</small></div>
                      <p>&ldquo;{testimonial.text}&rdquo;</p>
                      <footer><strong>{testimonial.name}</strong>{testimonial.location && <span>{testimonial.location}</span>}</footer>
                    </blockquote>
                  ))}
                </div>
              ) : (
                <div className="mh-voices__empty">
                  <span>Reviews are shown only when they can be loaded from our verified Google Play collection.</span>
                  <a href={SEO_CONFIG.mobileApp.playStoreUrl} target="_blank" rel="noopener noreferrer">Read reviews on Google Play <span aria-hidden>↗</span></a>
                </div>
              )}
            </div>
          </div>
        </section>

        <section className="mh-chapter mh-trust" id="trust">
          <div className="mh-trust__statement">
            <p className="mh-eyebrow"><span></span> Built for confidence</p>
            <blockquote>&ldquo;Astrology becomes useful when wonder is supported by a method you can inspect.&rdquo;</blockquote>
            <p className="mh-trust__body">Every answer begins with astronomical calculation, synthesizes Parashari, Nadi, Jaimini and KP frameworks, and ends in clear, human language.</p>
            <Link className="mh-inline-link" to="/about">Read about our methodology <span aria-hidden>↗</span></Link>
          </div>
          <div className="mh-trust__metrics">
            <div><strong>90+</strong><span>analysis layers and calculators</span></div>
            <div><strong>16</strong><span>divisional-chart layers available</span></div>
            <div><strong>24/7</strong><span>private access to Tara&rsquo;s guidance</span></div>
            <div><strong>1</strong><span>saved chart across every workspace</span></div>
          </div>
        </section>

        <section className="mh-chapter mh-app" id="mobile-app">
          <header className="mh-app__heading">
            <p className="mh-eyebrow"><span></span> AstroRoshni on your phone</p>
            <h2>Your sky,<br /><em>always with you.</em></h2>
            <p>Choose your device below. Android installs from Google Play. On iPhone and iPad, AstroRoshni is added directly from Safari.</p>
          </header>

          <article className="mh-platform-card mh-platform-card--android">
            <div className="mh-platform-card__body">
              <p className="mh-platform-card__label"><span aria-hidden>▶</span> Android</p>
              <h3>Install from Google Play</h3>
              <p>Download the Android app and sign in to keep your charts, readings and Tara conversations with you.</p>
              <ul>
                <li><span>01</span> Download from Google Play</li>
                <li><span>02</span> Sign in with your AstroRoshni account</li>
                <li><span>03</span> Access saved charts and notifications</li>
              </ul>
              <a className="mh-store-button" href={SEO_CONFIG.mobileApp.playStoreUrl} target="_blank" rel="noopener noreferrer" aria-label="Get AstroRoshni on Google Play">
                <span className="mh-store-button__icon" aria-hidden>▶</span>
                <span className="mh-store-button__copy"><span>GET IT ON</span><strong>Google Play</strong></span>
              </a>
            </div>
            <div className="mh-platform-card__device" aria-hidden="true">
              <span className="mh-app-device__speaker" aria-hidden></span>
              <picture>
                <source srcSet="/images/AstroRoshni_Home.webp" type="image/webp" />
                <img src="/images/AstroRoshni_Home.png" alt="" width="1280" height="2856" loading="lazy" />
              </picture>
            </div>
          </article>

          <article className="mh-platform-card mh-platform-card--ios">
            <div className="mh-platform-card__body">
              <p className="mh-platform-card__label"><span className="mh-platform-card__apple" aria-hidden></span> iPhone &amp; iPad</p>
              <h3>Add from Safari</h3>
              <p>There is no App Store download. Add AstroRoshni to your Home Screen once, then open it like any other app.</p>
              <ol className="mh-platform-install-steps">
                <li><b>1</b><span>Open <a className="mh-mobile-site-link" href="/mobile/">astroroshni.com/mobile/</a> in Safari</span></li>
                <li><b>2</b><span>Tap the <strong>Share</strong> button</span></li>
                <li><b>3</b><span>Choose <strong>Add to Home Screen</strong>, then tap Add</span></li>
              </ol>
              <div className="mh-platform-card__actions">
                <button className="mh-store-button mh-store-button--ios" type="button" onClick={() => setShowIosInstallGuide(true)} aria-haspopup="dialog">
                  <span className="mh-store-button__icon" aria-hidden>▶</span>
                  <span className="mh-store-button__copy"><span>IPHONE &amp; IPAD</span><strong>Watch install guide</strong></span>
                </button>
                <a className="mh-ios-open-link" href="/mobile/">Open mobile site <span aria-hidden>↗</span></a>
              </div>
              <small>Use Apple Safari so the “Add to Home Screen” option is available.</small>
            </div>
            <button className="mh-platform-card__video" type="button" onClick={() => setShowIosInstallGuide(true)} aria-label="Watch the iPhone and iPad installation guide">
              <img src="/mobile/astroroshni-ios-app-thumbnail.png" alt="Preview of the AstroRoshni mobile app" loading="lazy" />
              <span aria-hidden>▶</span>
              <strong>Watch guide</strong>
            </button>
          </article>
        </section>

        {showIosInstallGuide && (
          <div className="mh-ios-modal" role="presentation" onMouseDown={(event) => {
            if (event.target === event.currentTarget) setShowIosInstallGuide(false);
          }}>
            <section className="mh-ios-dialog" role="dialog" aria-modal="true" aria-labelledby="mh-ios-title">
              <button className="mh-ios-dialog__close" type="button" onClick={() => setShowIosInstallGuide(false)} aria-label="Close iPhone installation guide">×</button>
              <div className="mh-ios-dialog__media">
                <video controls playsInline muted preload="metadata" poster="/mobile/astroroshni-ios-app-thumbnail.png">
                  <source src="/mobile/astroroshni-ios-install-guide.mp4" type="video/mp4" />
                  Your browser does not support this video.
                </video>
                <span>Quick installation guide</span>
              </div>
              <div className="mh-ios-dialog__content">
                <p className="mh-eyebrow"><span></span> iPhone &amp; iPad</p>
                <h2 id="mh-ios-title">Add AstroRoshni to your Home Screen</h2>
                <p className="mh-ios-dialog__lead">AstroRoshni opens like an app on iPhone and iPad. No App Store download is needed.</p>
                <ol className="mh-ios-steps">
                  <li><b>1</b><div><strong>Open AstroRoshni in Safari</strong><small>Visit <a className="mh-mobile-site-link" href="/mobile/">astroroshni.com/mobile/</a> in Apple Safari.</small></div></li>
                  <li><b>2</b><div><strong>Tap the Share button</strong><small>Look for the square with the upward arrow.</small></div></li>
                  <li><b>3</b><div><strong>Choose “Add to Home Screen”</strong><small>Scroll down in the Share menu if it is not immediately visible.</small></div></li>
                  <li><b>4</b><div><strong>Tap Add</strong><small>If shown, keep “Open as Web App” enabled.</small></div></li>
                </ol>
                <a className="mh-ios-dialog__open" href="/mobile/">Open AstroRoshni Mobile <span aria-hidden>→</span></a>
                <small className="mh-ios-dialog__note">Use Safari for the Add to Home Screen option.</small>
              </div>
            </section>
          </div>
        )}

        <section className="mh-faq" id="faq" aria-labelledby="mh-faq-title">
          <div className="mh-faq__heading">
            <p className="mh-eyebrow"><span></span> Questions, answered clearly</p>
            <h2 id="mh-faq-title">Before you<br /><em>begin.</em></h2>
            <p>Useful answers about Tara, Kundli analysis and the different readings available across AstroRoshni.</p>
          </div>
          <div className="mh-faq__list">
            {HOME_FAQS.map((item, index) => (
              <details key={item.question} className="mh-faq__item">
                <summary><span>0{index + 1}</span><strong>{item.question}</strong><i aria-hidden>+</i></summary>
                <p>{item.answer}</p>
              </details>
            ))}
          </div>
        </section>

        <footer className="mh-footer" aria-labelledby="mh-footer-title">
          <div className="mh-footer__main">
            <div className="mh-footer__brand">
              <Link className="mh-footer__logo" to="/" aria-label="AstroRoshni home">
                <img src={SEO_CONFIG.images.logo} alt="" width="42" height="42" />
                <span>AstroRoshni</span>
              </Link>
              <h2 id="mh-footer-title">Ancient insight.<br /><em>Clearer decisions.</em></h2>
              <p>Personal Vedic astrology synthesized across Parashari, Nadi, Jaimini and KP—built around your complete chart, not a generic zodiac sign.</p>
              <div className="mh-footer__proof" aria-label="AstroRoshni analysis approach">
                <span><strong>90+</strong> analysis layers</span>
                <span><strong>4</strong> Vedic traditions</span>
              </div>
            </div>

            <nav className="mh-footer__nav" aria-label="Footer navigation">
              {FOOTER_GROUPS.map((group) => (
                <section key={group.title}>
                  <h3>{group.title}</h3>
                  {group.links.map(([label, href, external]) => external ? (
                    <a key={label} href={href} target="_blank" rel="noopener noreferrer">{label}<span aria-hidden>↗</span></a>
                  ) : (
                    <Link key={label} to={href}>{label}</Link>
                  ))}
                </section>
              ))}
            </nav>
          </div>

          <div className="mh-footer__connect">
            <div>
              <span className="mh-footer__eyebrow">Follow the conversation</span>
              <div className="mh-footer__socials">
                {FOOTER_SOCIALS.map((social) => (
                  <a key={social.label} href={social.href} target="_blank" rel="noopener noreferrer" aria-label={`AstroRoshni on ${social.label}`}>
                    <FooterSocialIcon name={social.icon} /><span>{social.label}</span>
                  </a>
                ))}
              </div>
            </div>
            <a className="mh-footer__email" href="mailto:help@astroroshni.com"><span>Need help?</span><strong>help@astroroshni.com</strong><i aria-hidden>↗</i></a>
          </div>

          <div className="mh-footer__bottom">
            <small>© {new Date().getFullYear()} AstroRoshni.com. All rights reserved.</small>
            <p>AstroRoshni is a brand of Apeiron Logic LLP, which develops this site and the AstroRoshni apps. LLPIN ACU-9370. <Link to="/about">About the company</Link></p>
            <div><Link to="/policy">Privacy Policy</Link><Link to="/terms">Terms &amp; Conditions</Link></div>
          </div>
          <p className="mh-footer__disclaimer">Astrological guidance is interpretive and does not replace medical, legal or financial advice.</p>
        </footer>
      </main>
    </div>
  );
};

export default ModernAstroRoshniHomepage;
