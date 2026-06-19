import React, { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import NavigationHeader from '../Shared/NavigationHeader';
import BirthFormModal from '../BirthForm/BirthFormModal';
import SEOHead from '../SEO/SEOHead';
import ChartWidget from '../Charts/ChartWidget';
import DashaBrowser from '../DashaBrowser/DashaBrowser';
import TransitControls from '../TransitControls/TransitControls';
import { useAstrology } from '../../context/AstrologyContext';
import { generatePageSEO } from '../../config/seo.config';
import '../Analysis/AnalysisDetailPage.css';
import './ChartsDashasWorkspacePage.css';

const DIVISIONAL_CHART_OPTIONS = [
  { value: 2, shortLabel: 'D2', label: 'Hora', description: 'Money, resources, and value flow.' },
  { value: 3, shortLabel: 'D3', label: 'Drekkana', description: 'Effort, courage, and co-born themes.' },
  { value: 4, shortLabel: 'D4', label: 'Chaturthamsa', description: 'Home, property, and stability.' },
  { value: 7, shortLabel: 'D7', label: 'Saptamsa', description: 'Children, lineage, and family expansion.' },
  { value: 9, shortLabel: 'D9', label: 'Navamsa', description: 'Marriage, dharma, and maturity of promise.' },
  { value: 10, shortLabel: 'D10', label: 'Dasamsa', description: 'Career, karma in action, and status.' },
  { value: 12, shortLabel: 'D12', label: 'Dwadasamsa', description: 'Parents and ancestral line.' },
  { value: 16, shortLabel: 'D16', label: 'Shodasamsa', description: 'Comforts, vehicles, and inner ease.' },
  { value: 20, shortLabel: 'D20', label: 'Vimshamsa', description: 'Spiritual practice and devotion.' },
  { value: 24, shortLabel: 'D24', label: 'Chaturvimshamsa', description: 'Education, learning, and mastery.' },
  { value: 27, shortLabel: 'D27', label: 'Saptavimshamsa', description: 'Strength, weakness, and resilience.' },
  { value: 30, shortLabel: 'D30', label: 'Trimshamsa', description: 'Difficulties, vulnerabilities, and hidden stress.' },
  { value: 40, shortLabel: 'D40', label: 'Khavedamsa', description: 'Maternal karmic line and subtle fortune.' },
  { value: 45, shortLabel: 'D45', label: 'Akshavedamsa', description: 'Paternal karmic line and subtle fortune.' },
  { value: 60, shortLabel: 'D60', label: 'Shashtyamsa', description: 'Deep karmic residue and subtle causes.' },
];

const buildChartPanelTitle = (eyebrow, heading) => (
  <div className="charts-dashas-widget-title">
    <span>{eyebrow}</span>
    <strong>{heading}</strong>
  </div>
);

const ChartsDashasWorkspacePage = ({
  user,
  onLogout,
  onAdminClick,
  onLogin,
  onOpenRegister,
}) => {
  const navigate = useNavigate();
  const { birthData, chartData } = useAstrology();
  const [showBirthModal, setShowBirthModal] = useState(false);
  const [birthModalTab, setBirthModalTab] = useState('saved');
  const [transitDate, setTransitDate] = useState(new Date());
  const [selectedDivision, setSelectedDivision] = useState(10);
  const seoData = generatePageSEO('chartsDashasWorkspace', { path: '/charts-dashas' });
  const hasChart = Boolean(birthData && chartData);
  const selectedDivisionalChart =
    DIVISIONAL_CHART_OPTIONS.find((option) => option.value === selectedDivision) || DIVISIONAL_CHART_OPTIONS[5];

  const structuredData = useMemo(
    () => ({
      '@context': 'https://schema.org',
      '@graph': [
        {
          '@type': 'Service',
          name: 'Charts and Dashas Workspace',
          description: seoData.description,
          provider: { '@type': 'Organization', name: 'AstroRoshni' },
        },
        {
          '@type': 'BreadcrumbList',
          itemListElement: [
            { '@type': 'ListItem', position: 1, name: 'Home', item: 'https://astroroshni.com/' },
            { '@type': 'ListItem', position: 2, name: 'Charts & Dashas', item: seoData.canonical },
          ],
        },
      ],
    }),
    [seoData.canonical, seoData.description]
  );

  const openBirthModal = (tab = 'saved') => {
    setBirthModalTab(tab);
    setShowBirthModal(true);
  };

  return (
    <div
      className="analysis-detail-page charts-dashas-page"
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
        onSelectBirthChart={user ? () => openBirthModal('saved') : () => onLogin?.()}
      />

      <main className="analysis-detail-main">
        <header className="analysis-detail-hero">
          <div className="analysis-detail-hero__inner">
            <button type="button" className="analysis-detail-back" onClick={() => navigate('/ai-kundli-generator')}>
              ← Birth Chart
            </button>
            <p className="analysis-detail-kicker">AstroRoshni chart workspace</p>
            <h1 className="analysis-detail-title">
              <span className="analysis-detail-title__icon" aria-hidden>📊</span>
              Charts & Dashas
            </h1>
            <p className="analysis-detail-blurb">
              Explore your Lagna chart, divisional charts, transit view, and dasha systems in one focused workspace
              built around your saved birth chart.
            </p>
            <div className="career-detail-hero-actions">
              <button
                type="button"
                className="career-detail-primary"
                onClick={() => (user ? openBirthModal(hasChart ? 'saved' : 'new') : onLogin?.())}
              >
                {user ? (hasChart ? 'Change chart' : 'Create birth chart') : 'Sign in to start'}
              </button>
              <button
                type="button"
                className="career-detail-secondary"
                onClick={() => navigate('/ai-kundli-generator')}
              >
                Learn about birth charts
              </button>
            </div>
            <div className="career-detail-proof" aria-label="Workspace features">
              <span>Lagna and divisional charts</span>
              <span>Transit-date controls</span>
              <span>Vimshottari, Yogini, Kalachakra, Chara</span>
            </div>
          </div>
        </header>

        <div className="analysis-detail-body">
          {!user ? (
            <div className="analysis-detail-empty">
              <div className="analysis-detail-empty__card">
                <span className="analysis-detail-empty__icon" aria-hidden>🪐</span>
                <h2>Sign in to open your chart workspace</h2>
                <p>
                  Charts and dasha timelines depend on your saved birth details. Sign in to create or select a chart,
                  then this workspace becomes fully interactive.
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
          ) : !hasChart ? (
            <div className="analysis-detail-empty">
              <div className="analysis-detail-empty__card">
                <span className="analysis-detail-empty__icon" aria-hidden>✨</span>
                <h2>Add your birth chart first</h2>
                <p>
                  We need your saved birth chart to render Lagna, divisional, and transit charts correctly and to
                  calculate your dasha timelines.
                </p>
                <div className="analysis-detail-empty__actions">
                  <button type="button" className="analysis-detail-empty__cta" onClick={() => openBirthModal('new')}>
                    Create birth chart
                  </button>
                  <button
                    type="button"
                    className="analysis-detail-empty__cta analysis-detail-empty__cta--secondary"
                    onClick={() => navigate('/ai-kundli-generator')}
                  >
                    Back to guide
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <>
              <section className="charts-dashas-section" aria-label="Core charts">
                <div className="career-detail-section-heading">
                  <p>Core charts</p>
                  <h2>Read the main chart first, then compare deeper layers</h2>
                </div>
                <div className="charts-dashas-grid charts-dashas-grid--top">
                  <article className="charts-dashas-card charts-dashas-card--widget-only">
                    <div className="charts-dashas-chart-shell">
                      <ChartWidget
                        title={buildChartPanelTitle('Lagna / D1', 'Main birth chart')}
                        chartType="lagna"
                        chartData={chartData}
                        birthData={birthData}
                        defaultStyle="north"
                        showFooterHint={false}
                      />
                    </div>
                  </article>

                  <article className="charts-dashas-card charts-dashas-card--widget-only">
                    <div className="charts-dashas-chart-shell">
                      <ChartWidget
                        title={buildChartPanelTitle('D9', 'Navamsa chart')}
                        chartType="navamsa"
                        chartData={chartData}
                        birthData={birthData}
                        defaultStyle="north"
                        showFooterHint={false}
                      />
                    </div>
                  </article>
                </div>
              </section>

              <section className="charts-dashas-section" aria-label="Divisional and transit charts">
                <div className="career-detail-section-heading">
                  <p>Deeper layers</p>
                  <h2>Use divisional and transit views for context and timing</h2>
                </div>
                <div className="charts-dashas-grid charts-dashas-grid--bottom">
                  <article className="charts-dashas-card charts-dashas-card--layered">
                    <div className="charts-dashas-card__intro">
                      <div>
                        <p>Divisionals</p>
                        <h3>{selectedDivisionalChart.label} ({selectedDivisionalChart.shortLabel})</h3>
                        <span className="charts-dashas-card__subcopy">{selectedDivisionalChart.description}</span>
                      </div>
                    </div>
                    <div className="charts-dashas-pill-row" aria-label="Divisional chart selector">
                      {DIVISIONAL_CHART_OPTIONS.map((option) => (
                        <button
                          key={option.value}
                          type="button"
                          className={`charts-dashas-pill${selectedDivision === option.value ? ' charts-dashas-pill--active' : ''}`}
                          onClick={() => setSelectedDivision(option.value)}
                        >
                          {option.shortLabel}
                        </button>
                      ))}
                    </div>
                    <div className="charts-dashas-chart-shell charts-dashas-chart-shell--attached">
                      <ChartWidget
                        title={`${selectedDivisionalChart.label} (${selectedDivisionalChart.shortLabel})`}
                        chartType="divisional"
                        chartData={chartData}
                        birthData={birthData}
                        division={selectedDivision}
                        defaultStyle="north"
                        showFooterHint={false}
                      />
                    </div>
                  </article>

                  <article className="charts-dashas-card charts-dashas-card--layered">
                    <div className="charts-dashas-card__intro">
                      <div>
                        <p>Transit date</p>
                        <h3>Transit chart</h3>
                        <span className="charts-dashas-card__subcopy">Shift the date to compare current sky movement against the natal chart.</span>
                      </div>
                    </div>
                    <div className="charts-dashas-card__controls-row">
                      <TransitControls
                        date={transitDate}
                        onChange={setTransitDate}
                        onResetToToday={() => setTransitDate(new Date())}
                        variant="light"
                      />
                    </div>
                    <div className="charts-dashas-chart-shell charts-dashas-chart-shell--attached">
                      <ChartWidget
                        title="Transit Chart"
                        chartType="transit"
                        chartData={chartData}
                        birthData={birthData}
                        transitDate={transitDate}
                        defaultStyle="north"
                        showFooterHint={false}
                      />
                    </div>
                  </article>
                </div>
              </section>

              <section className="charts-dashas-section charts-dashas-section--dashas" aria-label="Dasha systems">
                <div className="career-detail-section-heading">
                  <p>Timing systems</p>
                  <h2>Move across the major dasha frameworks in one place</h2>
                </div>
                <div className="charts-dashas-dasha-shell">
                  <DashaBrowser birthData={birthData} chartData={chartData} />
                </div>
              </section>
            </>
          )}
        </div>
      </main>

      {user ? (
        <BirthFormModal
          isOpen={showBirthModal}
          onClose={() => setShowBirthModal(false)}
          onSubmit={() => setShowBirthModal(false)}
          defaultActiveTab={birthModalTab}
          title="Charts & Dashas — Birth details"
          description="Create a new chart or choose a saved one to explore charts and dasha timelines."
        />
      ) : null}
    </div>
  );
};

export default ChartsDashasWorkspacePage;
