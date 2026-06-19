import React, { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import NavigationHeader from '../Shared/NavigationHeader';
import BirthFormModal from '../BirthForm/BirthFormModal';
import CreditsModal from '../Credits/CreditsModal';
import SEOHead from '../SEO/SEOHead';
import { useAstrology } from '../../context/AstrologyContext';
import { generatePageSEO } from '../../config/seo.config';
import '../Analysis/AnalysisDetailPage.css';
import './AshtakavargaSeoPage.css';

const FAQ_ITEMS = [
  {
    question: 'What is Ashtakavarga in Vedic astrology?',
    answer:
      'Ashtakavarga is a bindu-based scoring system used in Vedic astrology to measure support or strength across signs and houses. It helps astrologers judge where results are easier, slower, stronger, or more effort-heavy.',
  },
  {
    question: 'What is the difference between Sarvashtakavarga and Bhinna Ashtakavarga?',
    answer:
      'Sarvashtakavarga combines the bindu totals from multiple planets to show overall house strength. Bhinna Ashtakavarga shows the contribution of each individual planet so you can see which graha supports which sign or house.',
  },
  {
    question: 'Why is Ashtakavarga useful?',
    answer:
      'It adds a practical strength layer to the chart. You can compare houses, judge transit support, identify stronger life areas, and understand why some periods produce better results than others.',
  },
  {
    question: 'Do I need accurate birth details for Ashtakavarga?',
    answer:
      'Yes. Accurate birth date, time, and place are important because planetary positions and house layout affect the bindu calculations and transit comparisons.',
  },
  {
    question: 'Can Ashtakavarga alone predict everything?',
    answer:
      'No. It is one important layer, but it works best with the Lagna chart, divisional charts, dashas, yogas, and transits. AstroRoshni treats it as part of a bigger Vedic analysis system.',
  },
  {
    question: 'What does this AstroRoshni page let me do?',
    answer:
      'You can open your saved chart, view Sarvashtakavarga and planetary BAV strength, compare natal support with transit timing, and use the same chart context across the rest of AstroRoshni.',
  },
  {
    question: 'What are bindus in Ashtakavarga?',
    answer:
      'Bindus are the point-values given by planets to different signs in the Ashtakavarga system. More bindus generally indicate greater support, smoother outcomes, or better capacity for a sign or house to deliver results, while lower bindus can indicate weaker support or more effort.',
  },
  {
    question: 'How should Sarvashtakavarga totals be interpreted?',
    answer:
      'Sarvashtakavarga totals are usually read comparatively, not in isolation. A house or sign with higher total bindus tends to show stronger support in that area of life, while lower totals suggest weaker backing. The real interpretation comes from comparing stronger and weaker houses across the chart and then checking dashas and transits.',
  },
  {
    question: 'Why do astrologers compare Ashtakavarga with houses from the Ascendant?',
    answer:
      'Because the same zodiac sign also represents a house from the Lagna. When a sign has low or high bindus, that strength gets experienced through the life area ruled by the corresponding house from the Ascendant. This is one reason Ashtakavarga is useful for practical life interpretation.',
  },
  {
    question: 'How does Bhinna Ashtakavarga differ in use from Sarvashtakavarga?',
    answer:
      'Bhinna Ashtakavarga is used when you want to know which specific planet is contributing strength to a sign or house. Sarvashtakavarga gives the cumulative picture. Astrologically, BAV helps with graha-specific judgment, while SAV helps with overall area-of-life strength.',
  },
  {
    question: 'Is Ashtakavarga useful for transit analysis?',
    answer:
      'Yes. This is one of its strongest uses. When planets transit signs with higher or lower bindu support, astrologers can judge whether the transit is likely to give smoother or more strained outcomes. It does not replace standard transit reading, but it makes transit timing more nuanced.',
  },
  {
    question: 'Can Ashtakavarga help in predicting career, marriage, or finance?',
    answer:
      'Yes, but indirectly and structurally. It helps assess the strength of the relevant houses and signs connected to career, marriage, wealth, gains, or family. It becomes most useful when combined with house lords, yogas, divisional charts, and dasha timing rather than being read alone.',
  },
  {
    question: 'What is considered a strong or weak Ashtakavarga score?',
    answer:
      'There is no single magical cutoff that works in every chart, because interpretation is relative. In practice, astrologers look for houses that stand out as stronger or weaker compared with the rest of the chart. The distribution pattern matters more than one isolated number.',
  },
  {
    question: 'Does Ashtakavarga replace Shadbala or other strength systems?',
    answer:
      'No. Ashtakavarga and Shadbala measure different things. Shadbala looks at planetary strength through multiple classical factors, while Ashtakavarga measures supportive point distribution across signs and houses. Together they can complement each other rather than compete.',
  },
  {
    question: 'Why can a strong-looking house still give mixed results?',
    answer:
      'Because Ashtakavarga is only one layer. A house may have good bindu support but still be affected by difficult house lords, afflictions, weak divisional support, or an unfavorable dasha. Conversely, a weaker Ashtakavarga area may still activate meaningfully during a strong dasha or yoga period.',
  },
  {
    question: 'How is Ashtakavarga used with dashas?',
    answer:
      'Dashas show when karma matures, while Ashtakavarga helps judge how strongly certain signs or houses are supported when those periods unfold. Used together, they can refine prediction by showing both timing and the structural strength behind the results.',
  },
  {
    question: 'Can Ashtakavarga be read for remedies?',
    answer:
      'It can guide attention toward weaker areas of support, but remedies should not be prescribed from Ashtakavarga alone. A serious remedy decision should also consider the natal chart, house lords, divisional charts, dasha, and the condition of the relevant planets.',
  },
];

const FEATURE_CARDS = [
  ['Sarvashtakavarga totals', 'Review cumulative house strength so you can quickly see which areas of life carry more support in the chart.'],
  ['Planet-wise BAV', 'Break support down by each graha to understand which planet is strengthening which sign or house.'],
  ['Transit comparison', 'Read current sky movement against the birth chart to judge whether timing is gaining or losing support.'],
  ['Chart-linked workflow', 'Use the same saved birth chart instead of entering data again every time you want to inspect bindus.'],
  ['Prediction support', 'Use Ashtakavarga as a practical layer while reading career, marriage, health, wealth, and timing flows.'],
  ['Clean full-page tool', 'Open the working calculator view after sign-in with a layout designed for mobile and desktop study.'],
];

const USE_CASES = [
  'Compare house strength before reading a life area deeply',
  'Check whether a transit period is broadly supportive or weaker',
  'See where different planets contribute more bindus',
  'Use bindu logic alongside dasha and divisional chart reading',
  'Keep one saved chart for repeated timing and strength checks',
  'Move from SEO explainer page into the live calculator without changing tools',
];

const LIFE_PREDICTION_ITEMS = [
  'A detailed multi-section life reading, not just a bindu table',
  'Domain-wise interpretation for personality, wealth, home, career, marriage, gains, and more',
  'Transit-linked prediction context layered onto Ashtakavarga strength',
  'Saved reading workflow so users can reopen the prediction later',
  'A stronger narrative report for people who want meaning, not only numbers',
  'Useful bridge between raw Ashtakavarga analysis and practical life guidance',
];

const AshtakavargaSeoPage = ({
  user,
  onLogout,
  onAdminClick,
  onLogin,
  onOpenRegister,
}) => {
  const navigate = useNavigate();
  const { birthData } = useAstrology();
  const [showBirthModal, setShowBirthModal] = useState(false);
  const [showCreditsModal, setShowCreditsModal] = useState(false);
  const seoData = generatePageSEO('ashtakavarga', { path: '/ashtakavarga' });

  const structuredData = useMemo(
    () => ({
      '@context': 'https://schema.org',
      '@graph': [
        {
          '@type': 'Service',
          name: 'Ashtakavarga Calculator',
          description: seoData.description,
          provider: { '@type': 'Organization', name: 'AstroRoshni' },
          areaServed: 'Worldwide',
        },
        {
          '@type': 'BreadcrumbList',
          itemListElement: [
            { '@type': 'ListItem', position: 1, name: 'Home', item: 'https://astroroshni.com/' },
            { '@type': 'ListItem', position: 2, name: 'Ashtakavarga', item: seoData.canonical },
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

  const openTool = () => {
    if (!user) {
      onLogin?.();
      return;
    }
    if (!birthData) {
      setShowBirthModal(true);
      return;
    }
    navigate('/tools/ashtakavarga');
  };

  const openPredictionsReport = () => {
    if (!user) {
      onLogin?.();
      return;
    }
    if (!birthData) {
      setShowBirthModal(true);
      return;
    }
    navigate('/tools/ashtakavarga', { state: { initialActiveTab: 'analysis' } });
  };

  return (
    <div
      className="analysis-detail-page analysis-detail-page--career ashtakavarga-seo-page"
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
        onCreditsClick={() => setShowCreditsModal(true)}
        birthData={birthData}
        onCreateBirthChart={() => navigate('/ai-kundli-generator')}
        onSelectBirthChart={user ? () => setShowBirthModal(true) : () => onLogin?.()}
      />

      <main className="analysis-detail-main">
        <header className="analysis-detail-hero">
          <div className="analysis-detail-hero__inner ashtakavarga-seo-hero">
            <div className="ashtakavarga-seo-hero__copy">
              <button type="button" className="analysis-detail-back" onClick={() => navigate('/')}>
                ← Home
              </button>
              <p className="analysis-detail-kicker">Vedic chart strength analysis</p>
              <h1 className="analysis-detail-title">
                <span className="analysis-detail-title__icon" aria-hidden>⊞</span>
                Ashtakavarga Calculator
              </h1>
              <p className="analysis-detail-blurb">
                Explore Sarvashtakavarga and planet-wise bindus to understand chart strength, house support, and how
                transits interact with your birth chart in a more measurable Vedic framework.
              </p>
              <div className="career-detail-hero-actions">
                <button type="button" className="career-detail-primary" onClick={openTool}>
                  {user ? (birthData ? 'Open Ashtakavarga tool' : 'Add birth details') : 'Sign in to use tool'}
                </button>
                <button
                  type="button"
                  className="career-detail-secondary"
                  onClick={() => navigate('/ai-kundli-generator')}
                >
                  Create birth chart first
                </button>
              </div>
              <div className="career-detail-proof" aria-label="Ashtakavarga coverage">
                <span>Sarvashtakavarga totals</span>
                <span>Planet-wise BAV support</span>
                <span>Transit vs natal timing context</span>
              </div>
            </div>

            <div className="ashtakavarga-seo-hero__visual" aria-hidden="true">
              <div className="ashtakavarga-preview">
                <div className="ashtakavarga-preview__topbar" />
                <div className="ashtakavarga-preview__body">
                  <div className="ashtakavarga-preview__badge">Sample preview, not your chart</div>
                  <div className="ashtakavarga-preview__header">
                    <h3>Birth Sarvashtakavarga</h3>
                    <p>337 total bindus</p>
                  </div>

                  <div className="ashtakavarga-preview__grid">
                    {[
                      ['Aries', 'H9', 28, 'warm'],
                      ['Taurus', 'H10', 25, 'soft-red'],
                      ['Gemini', 'H11', 34, 'green'],
                      ['Cancer', 'H12', 36, 'green'],
                      ['Leo', 'H1', 22, 'soft-red'],
                      ['Virgo', 'H2', 22, 'soft-red'],
                      ['Libra', 'H3', 28, 'warm'],
                      ['Scorpio', 'H4', 31, 'green'],
                      ['Sagittarius', 'H5', 31, 'green'],
                      ['Capricorn', 'H6', 38, 'green'],
                      ['Aquarius', 'H7', 23, 'soft-red'],
                      ['Pisces', 'H8', 19, 'soft-red'],
                    ].map(([sign, house, value, tone]) => (
                      <div key={sign} className={`ashtakavarga-preview__tile ashtakavarga-preview__tile--${tone}`}>
                        <strong>{sign}</strong>
                        <span>{house}</span>
                        <em>{value}</em>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </header>

        <div className="analysis-detail-body">
          <section className="career-detail-intro" aria-label="Ashtakavarga features">
            <div className="career-detail-section-heading">
              <p>Strength framework</p>
              <h2>What this Ashtakavarga page helps you study</h2>
            </div>
            <div className="career-detail-method-grid">
              {FEATURE_CARDS.map(([title, body]) => (
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
                <h2>Sign in to open your chart-linked calculator</h2>
                <p>
                  This public page explains Ashtakavarga for search and discovery. The live calculator works inside
                  your account so it can use your saved birth chart accurately.
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
            <section className="ashtakavarga-seo-callout" aria-label="Tool entry">
              <div className="ashtakavarga-seo-callout__content">
                <p className="career-detail-eyebrow">Live tool access</p>
                <h2>{birthData ? 'Your chart is ready for Ashtakavarga' : 'Add a chart to start calculating bindus'}</h2>
                <p>
                  {birthData
                    ? 'You already have a selected birth chart. Open the full Ashtakavarga tool now to inspect Sarvashtakavarga totals, BAV support, and transit context.'
                    : 'Ashtakavarga depends on your exact birth chart. Add your birth details once, then you can open the live calculator and reuse that chart later across AstroRoshni.'}
                </p>
              </div>
              <div className="analysis-detail-empty__actions">
                <button type="button" className="analysis-detail-empty__cta" onClick={openTool}>
                  {birthData ? 'Open full calculator' : 'Enter birth details'}
                </button>
                <button
                  type="button"
                  className="analysis-detail-empty__cta analysis-detail-empty__cta--secondary"
                  onClick={() => navigate('/charts-dashas')}
                >
                  Open charts & dashas
                </button>
              </div>
            </section>
          )}

          <section className="career-detail-report-scope" aria-label="Ashtakavarga use cases">
            <div>
              <p className="career-detail-eyebrow">Practical uses</p>
              <h2>Where Ashtakavarga becomes genuinely useful</h2>
              <p>
                Ashtakavarga is most valuable when you need a practical strength layer instead of a vague reading. It
                helps you compare houses, understand which grahas are contributing support, and add a measurable lens
                while reading dasha and transit outcomes.
              </p>
            </div>
            <ul>
              {USE_CASES.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </section>

          <section className="ashtakavarga-report-highlight" aria-label="Ashtakavarga life predictions report">
            <div className="ashtakavarga-report-highlight__intro">
              <p className="career-detail-eyebrow">Detailed report</p>
              <h2>There is also a full Ashtakavarga life predictions report inside the tool</h2>
              <p>
                The Ashtakavarga page is not limited to colored bindu boxes. Inside the tool there is a much deeper
                life predictions section that turns the strength analysis into an actual written reading across major
                areas of life.
              </p>
              <div className="analysis-detail-empty__actions">
                <button type="button" className="analysis-detail-empty__cta" onClick={openPredictionsReport}>
                  {user ? (birthData ? 'Open Ashtakavarga report' : 'Add birth details first') : 'Sign in to view report'}
                </button>
              </div>
            </div>
            <ul className="ashtakavarga-report-highlight__list">
              {LIFE_PREDICTION_ITEMS.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </section>

          <section className="career-detail-seo-copy" aria-label="Ashtakavarga explanation">
            <article>
              <h2>How AstroRoshni fits Ashtakavarga into the bigger chart workflow</h2>
              <p>
                AstroRoshni does not treat Ashtakavarga as an isolated novelty tool. It works best when used together
                with the birth chart, divisional charts, and timing systems. That is why the calculator lives inside
                the same saved-chart workflow as Kundli creation, charts and dashas, life-area reports, and AI chat.
              </p>
              <p>
                In plain English, Ashtakavarga helps answer a very useful question: where is the chart getting more
                support, and where is it getting less? Once that is visible, readings become more grounded. A house
                with stronger support can behave very differently from one with low bindus, especially when current
                transits are also factored in.
              </p>
            </article>
          </section>

          <section className="career-detail-faq" aria-label="Ashtakavarga FAQs">
            <div className="career-detail-section-heading">
              <p>FAQ</p>
              <h2>Questions people ask before using Ashtakavarga</h2>
            </div>
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

      <BirthFormModal
        isOpen={showBirthModal}
        onClose={() => setShowBirthModal(false)}
        onSubmit={() => setShowBirthModal(false)}
        title="Birth details for Ashtakavarga"
        description="Accurate sidereal birth details are needed for Sarvashtakavarga and planetary bindu analysis."
      />
      <CreditsModal isOpen={showCreditsModal} onClose={() => setShowCreditsModal(false)} onLogin={onLogin} />
    </div>
  );
};

export default AshtakavargaSeoPage;
