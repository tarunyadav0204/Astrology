import React, { useEffect, useMemo, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import ModernNavigationHeader from '../Shared/ModernNavigationHeader';
import BirthFormModal from '../BirthForm/BirthFormModal';
import SEOHead from '../SEO/SEOHead';
import { useAstrology } from '../../context/AstrologyContext';
import { generatePageSEO } from '../../config/seo.config';
import './BirthChartCreationPage.css';

const FAQ_ITEMS = [
  {
    question: 'What is a Janam Kundli or birth chart?',
    answer: 'A Janam Kundli is a Vedic map of the sky for your exact birth date, time, and place. It establishes the Lagna, houses, planetary positions, rashis, nakshatras, divisional charts, and timing framework used for personalized interpretation.',
  },
  {
    question: 'Which details do I need to create my Kundli?',
    answer: 'You need your name, birth date, accurate birth time, and birth place. Select the place from search so the chart can use the correct coordinates and timezone.',
  },
  {
    question: 'Why does an accurate birth time matter?',
    answer: 'Birth time determines the Ascendant and house framework. Even a small difference can affect house positions, divisional charts, and timing layers, so use the most reliable recorded time available.',
  },
  {
    question: 'Is Kundli creation free?',
    answer: 'Creating and saving a birth chart is free. Some deeper reports and AI conversations may use credits, but your saved Kundli remains available across supported AstroRoshni tools.',
  },
  {
    question: 'Where is AI used?',
    answer: 'The birth chart itself is calculated from astronomical and Vedic astrology rules. AI is used later to help synthesize the calculated chart into readable, chart-aware guidance; it does not invent the planetary positions.',
  },
  {
    question: 'Can I save more than one Kundli?',
    answer: 'Yes. You can keep multiple saved charts and switch between your own Kundli and charts created for family members or other people when using supported features.',
  },
  {
    question: 'How does AstroRoshni protect my birth data?',
    answer: 'Your birth details are stored in your account for private reuse across AstroRoshni features. They are not displayed publicly on this landing page.',
  },
];

const CHART_OUTPUTS = [
  ['01', 'Lagna and 12 houses', 'The Ascendant and house framework that anchors every life-area reading.'],
  ['02', 'Grahas by sign and degree', 'Planetary placements with rashi, house, degree, and motion.'],
  ['03', 'Nakshatra and pada', 'The lunar-mansion detail used for temperament and timing.'],
  ['04', 'Divisional charts', 'Including Navamsa and the specialist vargas used by deeper analysis.'],
  ['05', 'Dasha timeline', 'Planetary periods that place natal promise into time.'],
  ['06', 'Reusable chart context', 'One saved Kundli for reports, matching, tools, and Tara.'],
];

const RELATED_TOOLS = [
  ['/charts-dashas', 'Charts & dashas', 'Inspect the main chart, divisional charts, strengths, and planetary periods.'],
  ['/kundli-matching', 'Kundli matching', 'Compare two complete birth charts for relationship compatibility.'],
  ['/career-guidance', 'Career analysis', 'Read vocation, professional strengths, timing, and development themes.'],
  ['/life-events', 'Life events', 'Explore year and month-level themes through chart-aware timing.'],
  ['/ashtakavarga', 'Ashtakavarga', 'Study house and transit support through classical point analysis.'],
  ['/chat?app=1', 'Ask Tara', 'Discuss your questions using the selected Kundli as context.'],
];

const BirthChartCreationPage = ({ user, onLogout, onAdminClick, onLogin, onOpenRegister }) => {
  const { birthData } = useAstrology();
  const resultsRef = useRef(null);
  const [showBirthModal, setShowBirthModal] = useState(false);
  const [birthModalTab, setBirthModalTab] = useState('new');
  const [pendingBirthDraft, setPendingBirthDraft] = useState(null);
  const [resumeAfterAuth, setResumeAfterAuth] = useState(false);
  const [chartCreated, setChartCreated] = useState(false);
  const seoData = generatePageSEO('birthChartCreation', { path: '/ai-kundli-generator/' });

  useEffect(() => {
    if (!user || !resumeAfterAuth || !pendingBirthDraft) return;
    setBirthModalTab('new');
    setShowBirthModal(true);
    setResumeAfterAuth(false);
  }, [pendingBirthDraft, resumeAfterAuth, user]);

  const structuredData = useMemo(() => ({
    '@context': 'https://schema.org',
    '@graph': [
      {
        '@type': 'Service',
        name: 'Free Janam Kundli Generator',
        description: seoData.description,
        provider: { '@type': 'Organization', name: 'AstroRoshni', url: 'https://astroroshni.com/' },
        areaServed: 'Worldwide',
        isRelatedTo: { '@type': 'SoftwareApplication', name: 'AstroRoshni' },
      },
      {
        '@type': 'BreadcrumbList',
        itemListElement: [
          { '@type': 'ListItem', position: 1, name: 'Home', item: 'https://astroroshni.com/' },
          { '@type': 'ListItem', position: 2, name: 'Free Kundli Generator', item: seoData.canonical },
        ],
      },
      {
        '@type': 'FAQPage',
        mainEntity: FAQ_ITEMS.map((item) => ({
          '@type': 'Question',
          name: item.question,
          acceptedAnswer: { '@type': 'Answer', text: item.answer },
        })),
      },
    ],
  }), [seoData.canonical, seoData.description]);

  const openBirthModal = (tab = 'new') => {
    if (tab === 'saved' && !user) {
      (onLogin || onOpenRegister)?.();
      return;
    }
    setBirthModalTab(tab);
    setShowBirthModal(true);
  };

  const requireAccountToSave = (draft) => {
    setPendingBirthDraft(draft);
    setResumeAfterAuth(true);
    setShowBirthModal(false);
    (onOpenRegister || onLogin)?.();
  };

  const completeBirthChart = () => {
    setPendingBirthDraft(null);
    setResumeAfterAuth(false);
    setShowBirthModal(false);
    setChartCreated(true);
  };

  return (
    <div className="kundli-generator-page">
      <SEOHead
        title={seoData.title}
        description={seoData.description}
        keywords={seoData.keywords}
        canonical={seoData.canonical}
        structuredData={structuredData}
      />

      <ModernNavigationHeader
        user={user}
        onLogin={onLogin}
        onLogout={onLogout}
        onAdminClick={onAdminClick}
      />

      <main className="kundli-generator-main">
        <header className="kundli-generator-hero">
          <div className="kundli-generator-hero__copy">
            <p className="kundli-generator-eyebrow">Free Kundli generator · Vedic birth chart</p>
            <h1>Create your <em>Janam Kundli.</em></h1>
            <p className="kundli-generator-hero__lead">
              Calculate a precise Vedic birth chart from your birth date, time, and place. Save it once, then use the
              same Kundli across AstroRoshni’s reports, matching, timing tools, and chart-aware conversations.
            </p>
            <div className="kundli-generator-actions">
              <button type="button" className="kundli-generator-primary" onClick={() => openBirthModal('new')}>
                Create free Kundli <span aria-hidden>↗</span>
              </button>
              {user ? (
                <button type="button" className="kundli-generator-secondary" onClick={() => openBirthModal('saved')}>
                  Select saved Kundli
                </button>
              ) : (
                <button type="button" className="kundli-generator-secondary" onClick={() => resultsRef.current?.scrollIntoView({ behavior: 'smooth' })}>
                  See what you receive
                </button>
              )}
            </div>
            <p className="kundli-generator-privacy"><span aria-hidden>●</span> Free chart creation · Private account storage · No credits required</p>
          </div>

          <div className="kundli-generator-visual" aria-label="Illustration of a calculated Vedic Kundli">
            <div className="kundli-generator-orbit kundli-generator-orbit--outer"></div>
            <div className="kundli-generator-orbit kundli-generator-orbit--inner"></div>
            <div className="kundli-generator-chart" aria-hidden>
              <span className="kundli-generator-chart__axis kundli-generator-chart__axis--one"></span>
              <span className="kundli-generator-chart__axis kundli-generator-chart__axis--two"></span>
              <b className="kundli-generator-chart__lagna">Lagna<small>17° 46′</small></b>
              <i className="kundli-generator-chart__sun">SU</i>
              <i className="kundli-generator-chart__moon">MO</i>
              <i className="kundli-generator-chart__jupiter">JU</i>
              <i className="kundli-generator-chart__saturn">SA</i>
            </div>
            <div className="kundli-generator-visual__caption"><span>Calculated chart</span><strong>Sidereal Vedic foundation</strong></div>
          </div>

          <dl className="kundli-generator-hero__facts">
            <div><dt>Input</dt><dd>Date · time · place</dd></div>
            <div><dt>Foundation</dt><dd>Lagna · grahas · rashis</dd></div>
            <div><dt>Reuse</dt><dd>One chart · every reading</dd></div>
          </dl>
        </header>

        {chartCreated && (
          <section className="kundli-generator-success" aria-live="polite">
            <div><span>Chart ready</span><strong>{birthData?.name || 'Your Kundli'} is now selected across AstroRoshni.</strong></div>
            <Link to="/charts-dashas">Open charts & dashas <span aria-hidden>↗</span></Link>
          </section>
        )}

        <section className="kundli-generator-results" ref={resultsRef} aria-labelledby="kundli-results-title">
          <div className="kundli-generator-heading">
            <p className="kundli-generator-section-label">Inside your chart</p>
            <h2 id="kundli-results-title">More than a <em>Sun-sign summary.</em></h2>
            <p>Your Kundli becomes the calculation foundation for personalized astrology throughout AstroRoshni.</p>
          </div>
          <div className="kundli-generator-output-grid">
            {CHART_OUTPUTS.map(([number, title, body]) => (
              <article key={number}><span>{number}</span><h3>{title}</h3><p>{body}</p></article>
            ))}
          </div>
        </section>

        <section className="kundli-generator-process" aria-labelledby="kundli-process-title">
          <div>
            <p className="kundli-generator-section-label">Three simple steps</p>
            <h2 id="kundli-process-title">From birth details to a <em>reusable chart.</em></h2>
          </div>
          <ol>
            <li><span>01</span><div><h3>Enter accurate details</h3><p>Add the recorded birth date and time, then select the birth place from search.</p></div></li>
            <li><span>02</span><div><h3>Calculate and save</h3><p>AstroRoshni calculates the Vedic chart and securely associates it with your account.</p></div></li>
            <li><span>03</span><div><h3>Use it everywhere</h3><p>Select the saved Kundli in analyses, compatibility, reports, timing tools, and Tara.</p></div></li>
          </ol>
          <button type="button" className="kundli-generator-primary" onClick={() => openBirthModal('new')}>
            Start your Kundli <span aria-hidden>↗</span>
          </button>
        </section>

        <section className="kundli-generator-ai" aria-labelledby="kundli-ai-title">
          <div className="kundli-generator-ai__mark" aria-hidden><span>AR</span><small>Chart intelligence</small></div>
          <div>
            <p className="kundli-generator-section-label">Calculation first · interpretation second</p>
            <h2 id="kundli-ai-title">Astronomy establishes the positions. <em>AI helps explain them.</em></h2>
            <p>
              AstroRoshni does not ask an AI model to invent your planets. The chart engine calculates the astronomical
              positions and Vedic layers first. AI-assisted interpretation can then synthesize those established
              calculations into clearer language and practical guidance.
            </p>
          </div>
        </section>

        <section className="kundli-generator-tools" aria-labelledby="kundli-tools-title">
          <div className="kundli-generator-heading">
            <p className="kundli-generator-section-label">One Kundli · many paths</p>
            <h2 id="kundli-tools-title">Create once, then <em>go deeper.</em></h2>
            <p>These destinations use or extend the chart foundation you create here.</p>
          </div>
          <div className="kundli-generator-tool-grid">
            {RELATED_TOOLS.map(([to, title, body], index) => (
              <Link to={to} key={to}><span>{String(index + 1).padStart(2, '0')}</span><h3>{title}</h3><p>{body}</p><i aria-hidden>↗</i></Link>
            ))}
          </div>
        </section>

        <section className="kundli-generator-trust" aria-labelledby="kundli-trust-title">
          <div>
            <p className="kundli-generator-section-label">Your data stays personal</p>
            <h2 id="kundli-trust-title">Birth details are private chart context—not public profile information.</h2>
          </div>
          <p>Your saved birth data is used so you can return to the same chart across AstroRoshni. Review how information is handled in our <Link to="/policy">Privacy Policy</Link>, or remove your account and associated data from <Link to="/account/delete">Delete account</Link>.</p>
        </section>

        <section className="kundli-generator-faq" aria-labelledby="kundli-faq-title">
          <div className="kundli-generator-heading">
            <p className="kundli-generator-section-label">Kundli questions</p>
            <h2 id="kundli-faq-title">Before you <em>begin.</em></h2>
            <p>The practical details behind creating, saving, and using your chart.</p>
          </div>
          <div className="kundli-generator-faq__list">
            {FAQ_ITEMS.map((item, index) => (
              <details key={item.question} open={index === 0}>
                <summary><span>{String(index + 1).padStart(2, '0')}</span>{item.question}<i aria-hidden>+</i></summary>
                <p>{item.answer}</p>
              </details>
            ))}
          </div>
        </section>

        <section className="kundli-generator-final" aria-labelledby="kundli-final-title">
          <p className="kundli-generator-section-label">Your chart begins here</p>
          <h2 id="kundli-final-title">One precise Kundli.<br /><em>A lifetime of context.</em></h2>
          <button type="button" className="kundli-generator-primary" onClick={() => openBirthModal('new')}>
            Create free Kundli <span aria-hidden>↗</span>
          </button>
        </section>
      </main>

      <footer className="kundli-generator-footer">
        <Link to="/">AstroRoshni</Link>
        <p>Vedic chart calculation and chart-aware guidance.</p>
        <nav aria-label="Kundli page footer"><Link to="/about">About</Link><Link to="/contact">Contact</Link><Link to="/policy">Privacy</Link><Link to="/terms">Terms</Link></nav>
      </footer>

      <BirthFormModal
        isOpen={showBirthModal}
        onClose={() => setShowBirthModal(false)}
        onSubmit={completeBirthChart}
        onRequireAuth={!user ? requireAccountToSave : undefined}
        title="Choose your Kundli"
        description="Create a new Vedic birth chart or select one you saved earlier"
        prefilledData={pendingBirthDraft ? { person1: pendingBirthDraft } : undefined}
        defaultActiveTab={birthModalTab}
      />
    </div>
  );
};

export default BirthChartCreationPage;
