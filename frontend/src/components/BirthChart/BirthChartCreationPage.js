import React, { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import NavigationHeader from '../Shared/NavigationHeader';
import BirthFormModal from '../BirthForm/BirthFormModal';
import SEOHead from '../SEO/SEOHead';
import ChartWidget from '../Charts/ChartWidget';
import { useAstrology } from '../../context/AstrologyContext';
import { generatePageSEO } from '../../config/seo.config';
import '../Analysis/AnalysisDetailPage.css';
import './ChartsDashasWorkspacePage.css';

const FAQ_ITEMS = [
  {
    question: 'What is a birth chart or Kundli?',
    answer:
      'A birth chart, also called a Kundli or Janam Kundli, is a map of the sky at your exact birth time and place. In Vedic astrology it shows the Lagna, planets, houses, rashis, nakshatras, yogas, and the timing framework used for deeper prediction.',
  },
  {
    question: 'Which details are needed to create a birth chart?',
    answer:
      'You need your birth date, accurate birth time, and birth place. These are used to calculate the Ascendant, Moon nakshatra, planetary degrees, house cusps, divisional charts, and dasha timing.',
  },
  {
    question: 'Why is exact birth time important?',
    answer:
      'Even a small time difference can change the Ascendant, house positions, navamsa placement, and timing layers. That is why accurate birth time improves the quality of a Vedic birth chart reading.',
  },
  {
    question: 'What do I get after creating my birth chart on AstroRoshni?',
    answer:
      'Once your chart is created, you can reuse it across life-event predictions, chat, marriage analysis, career analysis, health analysis, wealth analysis, progeny analysis, education analysis, Panchang-linked guidance, and other chart-based tools.',
  },
  {
    question: 'Does AstroRoshni create only a basic chart?',
    answer:
      'No. AstroRoshni uses the main birth chart together with divisional charts, dasha timing, transits, yogas, and strength measures so your chart can support much richer analysis than a simple one-page Kundli summary.',
  },
  {
    question: 'Can I save multiple birth charts?',
    answer:
      'Yes. Your account can keep saved birth charts so you can switch between your own chart and charts for family or other people when using supported tools.',
  },
  {
    question: 'Can I create a chart first and analyze later?',
    answer:
      'Yes. That is exactly the point of this page. You can create and save the chart first, then use it later for reports, matching, timing, and AI chat without re-entering the same birth details each time.',
  },
  {
    question: 'Is creating a birth chart free?',
    answer:
      'Creating and saving the birth chart itself is part of your account workflow. Some deeper personalized reports or chat flows may use credits later, but the chart-creation step is the foundation for everything else.',
  },
  {
    question: 'Is my birth data private?',
    answer:
      'Your birth details are stored on your account so you can reuse them in chart-based tools. They are not shown publicly on this page, and they are used only for your astrology features inside AstroRoshni.',
  },
];

const METHOD_CARDS = [
  ['Birth details', 'Your date, time, and place of birth are used to calculate the exact chart rather than giving a generic zodiac-only reading.'],
  ['Lagna and houses', 'The engine calculates Ascendant and all 12 houses so each life area can be read through a proper Vedic framework.'],
  ['Planetary positions', 'Planets are placed by sign, degree, nakshatra, and house to build the full reading foundation.'],
  ['Divisional charts', 'Higher-order charts like D9, D10, D24, D30, and D7 help AstroRoshni go beyond surface-level interpretation.'],
  ['Dashas and timing', 'Your chart becomes usable for prediction because dasha sequences and current transits can be read against it.'],
  ['Reusable workspace', 'Once saved, the same chart can be selected again across reports, matching, and AI astrology chat.'],
];

const REPORT_ITEMS = [
  'Create and save your Janam Kundli / birth chart',
  'Use one saved chart across multiple astrology tools',
  'Switch between saved charts later',
  'Enable chart-aware AI astrology chat',
  'Unlock life-area reports like career, marriage, health, and wealth',
  'Support timing analysis with dasha and transits',
  'Build a reusable account-level astrology workspace',
  'Avoid re-entering birth details every time',
];

const buildChartPanelTitle = (eyebrow, heading) => (
  <div className="charts-dashas-widget-title">
    <span>{eyebrow}</span>
    <strong>{heading}</strong>
  </div>
);

const BirthChartCreationPage = ({
  user,
  onLogout,
  onAdminClick,
  onLogin,
  onOpenRegister,
}) => {
  const navigate = useNavigate();
  const { birthData, chartData } = useAstrology();
  const [showBirthModal, setShowBirthModal] = useState(false);
  const [birthModalTab, setBirthModalTab] = useState('new');
  const seoData = generatePageSEO('birthChartCreation', { path: '/ai-kundli-generator/' });

  const structuredData = useMemo(
    () => ({
      '@context': 'https://schema.org',
      '@graph': [
        {
          '@type': 'Service',
          name: 'Birth Chart Creation',
          description: seoData.description,
          provider: { '@type': 'Organization', name: 'AstroRoshni' },
          areaServed: 'Worldwide',
        },
        {
          '@type': 'BreadcrumbList',
          itemListElement: [
            { '@type': 'ListItem', position: 1, name: 'Home', item: 'https://astroroshni.com/' },
            { '@type': 'ListItem', position: 2, name: 'AI Kundli Generator', item: seoData.canonical },
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
    }),
    [seoData.canonical, seoData.description]
  );

  const openBirthModal = (tab = 'new') => {
    setBirthModalTab(tab);
    setShowBirthModal(true);
  };

  return (
    <div
      className="analysis-detail-page analysis-detail-page--career"
      style={{ '--analysis-hero-image': `url(${process.env.PUBLIC_URL || ''}/images/software/birth-chart.png)` }}
    >
      <SEOHead
        title={seoData.title}
        description={seoData.description}
        keywords={seoData.keywords}
        canonical={seoData.canonical}
        structuredData={structuredData}
      />

      <NavigationHeader
        compact
        showZodiacSelector={false}
        user={user}
        onAdminClick={onAdminClick}
        onLogout={onLogout}
        onLogin={!user ? onLogin : undefined}
        showLoginButton={!user}
        birthData={birthData}
        onCreateBirthChart={() => navigate('/ai-kundli-generator')}
        onSelectBirthChart={
          user
            ? () => openBirthModal('saved')
            : () => onLogin?.()
        }
      />

      <main className="analysis-detail-main">
        <header className="analysis-detail-hero">
          <div className="analysis-detail-hero__inner">
            <button type="button" className="analysis-detail-back" onClick={() => navigate('/')}>
              ← Home
            </button>
            <p className="analysis-detail-kicker">Vedic birth chart setup</p>
            <h1 className="analysis-detail-title">
              <span className="analysis-detail-title__icon" aria-hidden>✨</span>
              Create Birth Chart
            </h1>
            <p className="analysis-detail-blurb">
              Create your Janam Kundli with date, time, and place of birth so AstroRoshni can use the same saved chart
              across predictions, reports, matching, and AI astrology chat.
            </p>
            <div className="career-detail-hero-actions">
              <button
                type="button"
                className="career-detail-primary"
                onClick={() => (user ? openBirthModal('new') : onLogin?.())}
              >
                {user ? 'Create birth chart now' : 'Sign in to create chart'}
              </button>
              <button
                type="button"
                className="career-detail-secondary"
                onClick={() => (user ? openBirthModal('saved') : (onOpenRegister || onLogin)?.())}
              >
                {user ? 'Select saved chart' : 'Create free account'}
              </button>
            </div>
            <div className="career-detail-proof" aria-label="Birth chart workflow coverage">
              <span>Birth date, time, and place</span>
              <span>Lagna, grahas, houses, rashis</span>
              <span>Saved chart reuse across tools</span>
            </div>
          </div>
        </header>

        <div className="analysis-detail-body">
          <section className="career-detail-intro" aria-label="Birth chart creation workflow">
            <div className="career-detail-section-heading">
              <p>Birth chart engine</p>
              <h2>What AstroRoshni prepares when you create a birth chart</h2>
            </div>
            <div className="career-detail-method-grid">
              {METHOD_CARDS.map(([title, body]) => (
                <article key={title}>
                  <h3>{title}</h3>
                  <p>{body}</p>
                </article>
              ))}
            </div>
          </section>

          {!user ? (
            <div className="analysis-detail-empty">
              <div className="analysis-detail-empty__card">
                <span className="analysis-detail-empty__icon" aria-hidden>🪐</span>
                <h2>Sign in to save your chart</h2>
                <p>
                  This page explains the workflow publicly for search and sharing, but saving the actual birth chart
                  happens inside your account so you can reuse it later across AstroRoshni tools.
                </p>
                <div className="analysis-detail-empty__actions">
                  <button type="button" className="analysis-detail-empty__cta" onClick={() => onLogin?.()}>
                    Sign in
                  </button>
                  <button
                    type="button"
                    className="analysis-detail-empty__cta analysis-detail-empty__cta--secondary"
                    onClick={() => (onOpenRegister || onLogin)?.()}
                  >
                    Create account
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <div className="analysis-detail-empty">
              <div className="analysis-detail-empty__card">
                <span className="analysis-detail-empty__icon" aria-hidden>📊</span>
                <h2>Create or select your chart</h2>
                <p>
                  You are signed in. Create a new birth chart now or pick a saved one to start using it in reports,
                  matching, chat, and timing tools.
                </p>
                <div className="analysis-detail-empty__actions">
                  <button type="button" className="analysis-detail-empty__cta" onClick={() => openBirthModal('new')}>
                    Create new chart
                  </button>
                  <button
                    type="button"
                    className="analysis-detail-empty__cta analysis-detail-empty__cta--secondary"
                    onClick={() => openBirthModal('saved')}
                  >
                    Select saved chart
                  </button>
                </div>
              </div>
            </div>
          )}

          <section className="career-detail-report-scope" aria-label="Birth chart benefits">
            <div>
              <p className="career-detail-eyebrow">Saved chart workspace</p>
              <h2>Why create the birth chart first</h2>
              <p>
                A saved birth chart turns AstroRoshni into a reusable astrology workspace. Instead of entering your
                birth details repeatedly, you create the chart once and then use it in multiple analysis flows, timing
                tools, compatibility checks, and AI conversations.
              </p>
            </div>
            <ul>
              {REPORT_ITEMS.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </section>

          {user && birthData && chartData ? (
            <section className="charts-dashas-section" aria-label="Chart previews">
              <div className="career-detail-section-heading">
                <p>Live preview</p>
                <h2>Your saved chart can already power charts and dasha tools</h2>
              </div>
              <div className="charts-dashas-grid charts-dashas-grid--top">
                <article className="charts-dashas-card charts-dashas-card--widget-only">
                  <ChartWidget
                    title={buildChartPanelTitle('Lagna / D1', 'Main birth chart')}
                    chartType="lagna"
                    chartData={chartData}
                    birthData={birthData}
                    defaultStyle="north"
                    showFooterHint={false}
                  />
                </article>

                <article className="charts-dashas-card charts-dashas-card--widget-only">
                  <ChartWidget
                    title={buildChartPanelTitle('D9', 'Navamsa preview')}
                    chartType="navamsa"
                    chartData={chartData}
                    birthData={birthData}
                    defaultStyle="north"
                    showFooterHint={false}
                  />
                </article>
              </div>
              <div className="form-buttons" style={{ marginTop: '14px', justifyContent: 'center' }}>
                <button
                  type="button"
                  className="analysis-detail-empty__cta"
                  onClick={() => navigate('/charts-dashas')}
                >
                  Open charts & dashas workspace
                </button>
              </div>
            </section>
          ) : null}

          <section className="career-detail-seo-copy" aria-label="Birth chart explanation">
            <article>
              <h2>Birth chart creation is the foundation of personalized astrology</h2>
              <p>
                A Vedic birth chart is more than a sun-sign summary. It gives AstroRoshni the exact reference point
                needed to read houses, planetary strengths, yogas, nakshatras, divisional charts, dasha sequences, and
                transits in a way that is actually specific to you.
              </p>
            </article>
            <article>
              <h2>Create once, then reuse across reports, chat, and matching</h2>
              <p>
                Once the chart is saved, it becomes the chart context for later tools. That is why creating the birth
                chart first is useful even if your real goal is career, marriage, wealth, health, education, progeny,
                or AI astrology chat.
              </p>
            </article>
          </section>

          <section className="career-detail-faq" aria-label="Birth chart FAQ">
            <h2>Birth Chart FAQ</h2>
            <div className="career-detail-faq-grid">
              {FAQ_ITEMS.map((item) => (
                <article key={item.question}>
                  <h3>{item.question}</h3>
                  <p>{item.answer}</p>
                </article>
              ))}
            </div>
          </section>
        </div>
      </main>

      {user ? (
        <BirthFormModal
          isOpen={showBirthModal}
          onClose={() => setShowBirthModal(false)}
          onSubmit={() => setShowBirthModal(false)}
          defaultActiveTab={birthModalTab}
          title="Birth Chart — Enter details"
          description="Please provide your birth information to create and save your Vedic birth chart."
        />
      ) : null}
    </div>
  );
};

export default BirthChartCreationPage;
