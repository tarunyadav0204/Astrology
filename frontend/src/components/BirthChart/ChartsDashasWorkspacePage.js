import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import BirthFormModal from '../BirthForm/BirthFormModal';
import SEOHead from '../SEO/SEOHead';
import ChartWidget from '../Charts/ChartWidget';
import TransitControls from '../TransitControls/TransitControls';
import DeskDashaPanel from './DeskDashaPanel';
import DeskSpecialPoints from './DeskSpecialPoints';
import DeskBirthPanchang from './DeskBirthPanchang';
import DeskConditionStrip from './DeskConditionStrip';
import DeskSpecialLagnas from './DeskSpecialLagnas';
import DeskPositionsTable from './DeskPositionsTable';
import DeskYogasPanel from './DeskYogasPanel';
import DeskFriendshipPanel from './DeskFriendshipPanel';
import DeskHouseLordsPanel from './DeskHouseLordsPanel';
import DeskAspectsPanel from './DeskAspectsPanel';
import DeskHouseInsight from './DeskHouseInsight';
import DeskStrengthStrip from './DeskStrengthStrip';
import DeskActivationsPanel from './DeskActivationsPanel';
import DeskToolModals from './DeskToolModals';
import ParashariDeskMobile from './ParashariDeskMobile';
import { useAstrology } from '../../context/AstrologyContext';
import { generatePageSEO } from '../../config/seo.config';
import { apiService } from '../../services/apiService';
import './ChartsDashasWorkspacePage.css';

const MOBILE_DESK_MQ = '(max-width: 900px)';

function useMobileDesk() {
  const [isMobile, setIsMobile] = useState(() => (
    typeof window !== 'undefined' ? window.matchMedia(MOBILE_DESK_MQ).matches : false
  ));
  useEffect(() => {
    if (typeof window === 'undefined') return undefined;
    const mq = window.matchMedia(MOBILE_DESK_MQ);
    const onChange = () => setIsMobile(mq.matches);
    onChange();
    if (mq.addEventListener) mq.addEventListener('change', onChange);
    else mq.addListener(onChange);
    return () => {
      if (mq.removeEventListener) mq.removeEventListener('change', onChange);
      else mq.removeListener(onChange);
    };
  }, []);
  return isMobile;
}

const DIVISIONAL_CHART_OPTIONS = [
  { value: 2, shortLabel: 'D2', label: 'Hora' },
  { value: 3, shortLabel: 'D3', label: 'Drekkana' },
  { value: 4, shortLabel: 'D4', label: 'Chaturthamsa' },
  { value: 7, shortLabel: 'D7', label: 'Saptamsa' },
  { value: 9, shortLabel: 'D9', label: 'Navamsa' },
  { value: 10, shortLabel: 'D10', label: 'Dasamsa' },
  { value: 12, shortLabel: 'D12', label: 'Dwadasamsa' },
  { value: 16, shortLabel: 'D16', label: 'Shodasamsa' },
  { value: 20, shortLabel: 'D20', label: 'Vimshamsa' },
  { value: 24, shortLabel: 'D24', label: 'Chaturvimshamsa' },
  { value: 27, shortLabel: 'D27', label: 'Saptavimshamsa' },
  { value: 30, shortLabel: 'D30', label: 'Trimshamsa' },
  { value: 40, shortLabel: 'D40', label: 'Khavedamsa' },
  { value: 45, shortLabel: 'D45', label: 'Akshavedamsa' },
  { value: 60, shortLabel: 'D60', label: 'Shashtyamsa' },
];

const JAIMINI_CHART_OPTIONS = [
  { value: 'karkamsa', shortLabel: 'Ka', label: 'Kārkāṁśa' },
  { value: 'swamsa', shortLabel: 'Sw', label: 'Swāṁśa' },
];

const STRENGTH_TOOLS = [
  { id: 'shadbala', label: 'SB', title: 'Shadbala' },
  { id: 'ashtakavarga', label: 'AV', title: 'Ashtakavarga' },
  { id: 'karakas', label: 'CK', title: 'Chara Karakas' },
  { id: 'dignities', label: 'Dig', title: 'Planetary dignities' },
];

function formatAsOfIso(date) {
  if (!(date instanceof Date) || Number.isNaN(date.getTime())) {
    return new Date().toISOString().slice(0, 10);
  }
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, '0');
  const d = String(date.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
}

const ChartsDashasWorkspacePage = ({
  user,
  onLogin,
  onOpenRegister,
}) => {
  const navigate = useNavigate();
  const isMobileDesk = useMobileDesk();
  const { birthData, chartData, setBirthData } = useAstrology();
  const [showBirthModal, setShowBirthModal] = useState(false);
  const [birthModalTab, setBirthModalTab] = useState('saved');
  /** One shared as-of clock for transit + dashas + activations */
  const [asOfDate, setAsOfDate] = useState(new Date());
  /** number (D2–D60) or 'karkamsa' | 'swamsa' */
  const [selectedDx, setSelectedDx] = useState(10);
  const [dashaSystem, setDashaSystem] = useState('vimshottari');
  const [activationLedger, setActivationLedger] = useState(null);
  const [activationLoading, setActivationLoading] = useState(false);
  const [activationError, setActivationError] = useState(null);
  const [analysisTab, setAnalysisTab] = useState('positions');
  const [activationsFocus, setActivationsFocus] = useState(false);
  const [activeTool, setActiveTool] = useState(null);
  const [houseSelection, setHouseSelection] = useState(null);
  const seoData = generatePageSEO('chartsDashasWorkspace', { path: '/charts-dashas' });
  const hasChart = Boolean(birthData && chartData);

  useEffect(() => {
    if (isMobileDesk) setActivationsFocus(false);
  }, [isMobileDesk]);

  const selectedDivisionalChart = useMemo(() => {
    if (selectedDx === 'karkamsa' || selectedDx === 'swamsa') {
      return JAIMINI_CHART_OPTIONS.find((o) => o.value === selectedDx);
    }
    return DIVISIONAL_CHART_OPTIONS.find((option) => option.value === selectedDx) || DIVISIONAL_CHART_OPTIONS[5];
  }, [selectedDx]);

  const dxChartType = selectedDx === 'karkamsa' || selectedDx === 'swamsa'
    ? selectedDx
    : 'divisional';

  useEffect(() => {
    let cancelled = false;
    if (!user || !birthData || !chartData) {
      setActivationLedger(null);
      setActivationError(null);
      setActivationLoading(false);
      return () => { cancelled = true; };
    }
    const asOf = formatAsOfIso(asOfDate);
    setActivationLoading(true);
    setActivationError(null);
    apiService.getActivationExplorer({
      birthChartId: birthData.chart_id || birthData.birth_chart_id || birthData.id || null,
      birthData,
      asOf,
      horizonDays: 180,
      trace: false,
    }).then((data) => {
      if (!cancelled) {
        setActivationLedger(data);
        setActivationLoading(false);
      }
    }).catch((err) => {
      if (!cancelled) {
        setActivationLedger(null);
        setActivationLoading(false);
        const detail = err?.response?.data?.detail;
        setActivationError(
          typeof detail === 'string'
            ? detail
            : err?.message || 'Could not load house activation ledger'
        );
      }
    });
    return () => { cancelled = true; };
  }, [birthData, chartData, user, asOfDate]);

  const activationNowCount = useMemo(() => {
    const rows = activationLedger?.house_activations || [];
    if (!rows.length) return 0;
    const asOf = formatAsOfIso(asOfDate);
    const containing = rows.filter(
      (row) => row.window?.start_date <= asOf && row.window?.end_date >= asOf
    );
    const pool = containing.length
      ? containing
      : rows.filter((row) => row.window?.start_date === rows[0]?.window?.start_date);
    return pool.filter((row) => !['transit_only', 'dormant'].includes(row.state)).length;
  }, [activationLedger, asOfDate]);

  useEffect(() => {
    setHouseSelection(null);
  }, [birthData?.date, birthData?.time, birthData?.name]);

  const handleHouseSelect = (sel) => {
    setHouseSelection(sel);
    setActivationsFocus(false);
    setAnalysisTab('house');
  };

  useEffect(() => {
    if (!activationsFocus) return undefined;
    const onKey = (event) => {
      if (event.key === 'Escape') setActivationsFocus(false);
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [activationsFocus]);

  const structuredData = useMemo(
    () => ({
      '@context': 'https://schema.org',
      '@graph': [
        {
          '@type': 'Service',
          name: 'Parashari Desk — Charts and Dashas',
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
    <div className={`parashari-desk${isMobileDesk ? ' parashari-desk--mobile' : ''}`}>
      <SEOHead
        title={seoData.title}
        description={seoData.description}
        keywords={seoData.keywords}
        canonical={seoData.canonical}
        structuredData={structuredData}
      />

      {!isMobileDesk || !user || !hasChart ? (
      <header className="parashari-desk-bar">
        <div className="parashari-desk-bar__left">
          <button type="button" className="parashari-desk-bar__back" onClick={() => navigate('/')}>← Home</button>
          <strong className="parashari-desk-bar__brand">Parashari Desk</strong>
          <span className="parashari-desk-bar__native">
            {birthData?.name || 'No native'}
            {birthData?.date ? ` · ${String(birthData.date).split('T')[0]}` : ''}
          </span>
        </div>
        <div className="parashari-desk-bar__center">
          <button
            type="button"
            className={`parashari-desk-chip parashari-desk-chip--activations${activationsFocus ? ' is-active' : ''}`}
            onClick={() => setActivationsFocus((open) => !open)}
            title={activationsFocus ? 'Close activations focus (Esc)' : 'Open activations with D1, Transit and dashas'}
            aria-pressed={activationsFocus}
          >
            {activationsFocus ? 'Close activations' : 'Activations'}
            {!activationsFocus && activationNowCount ? <em>{activationNowCount}</em> : null}
          </button>
          <button type="button" className="parashari-desk-chip" onClick={() => navigate('/charts-dashas/kp')}>
            KP Desk
          </button>
          <button type="button" className="parashari-desk-chip" onClick={() => navigate('/charts-dashas/nadi')}>
            Nadi Desk
          </button>
          {hasChart ? (
            <div className="parashari-desk-bar__tools" role="group" aria-label="Strength tools">
              {STRENGTH_TOOLS.map((tool) => (
                <button
                  key={tool.id}
                  type="button"
                  className={`parashari-desk-chip${activeTool === tool.id ? ' is-active' : ''}`}
                  title={tool.title}
                  onClick={() => setActiveTool(tool.id)}
                >
                  {tool.label}
                </button>
              ))}
            </div>
          ) : null}
        </div>
        <div className="parashari-desk-bar__right">
          <button
            type="button"
            onClick={() => (user ? openBirthModal(hasChart ? 'saved' : 'new') : onLogin?.())}
          >
            {user ? (hasChart ? 'Change native' : 'Select chart') : 'Sign in'}
          </button>
          {!user ? (
            <button type="button" className="parashari-desk-bar__primary" onClick={onLogin}>Sign in</button>
          ) : null}
        </div>
      </header>
      ) : null}

      {!user ? (
        <div className="parashari-desk-empty">
          <h2>Sign in for the Parashari desk</h2>
          <p>D1, D9, divisionals, transit and dashas in one astrologer workspace.</p>
          <button type="button" className="parashari-desk-bar__primary" onClick={onLogin}>Sign in</button>
          {onOpenRegister ? (
            <button type="button" onClick={onOpenRegister}>Create account</button>
          ) : null}
        </div>
      ) : !hasChart ? (
        <div className="parashari-desk-empty">
          <h2>Select a birth chart</h2>
          <p>Load a native to open Lagna, Navamsa, divisionals, transit and dasha systems.</p>
          <button type="button" className="parashari-desk-bar__primary" onClick={() => openBirthModal('new')}>
            Create / select chart
          </button>
        </div>
      ) : isMobileDesk ? (
        <ParashariDeskMobile
          birthData={birthData}
          chartData={chartData}
          asOfDate={asOfDate}
          onAsOfChange={setAsOfDate}
          selectedDx={selectedDx}
          onSelectedDxChange={setSelectedDx}
          divisionalOptions={DIVISIONAL_CHART_OPTIONS}
          jaiminiOptions={JAIMINI_CHART_OPTIONS}
          selectedDivisionalChart={selectedDivisionalChart}
          dxChartType={dxChartType}
          dashaSystem={dashaSystem}
          onDashaSystemChange={setDashaSystem}
          activationLedger={activationLedger}
          activationLoading={activationLoading}
          activationError={activationError}
          activationNowCount={activationNowCount}
          analysisTab={analysisTab}
          onAnalysisTabChange={setAnalysisTab}
          houseSelection={houseSelection}
          onHouseSelect={handleHouseSelect}
          onOpenTool={setActiveTool}
          onChangeNative={() => openBirthModal('saved')}
        />
      ) : (
        <div className="parashari-desk-body">
          {/* Shared tools — keeps all four chart cells equal */}
          <div className={`parashari-desk-tools${activationsFocus ? ' is-act-focus' : ''}`}>
            <div className="parashari-desk-tools__clock" aria-label="As-of date for transit and dashas">
              <span className="parashari-desk-tools__label">As-of</span>
              <TransitControls
                date={asOfDate}
                onChange={setAsOfDate}
                onResetToToday={() => setAsOfDate(new Date())}
                variant="light"
                showTime
              />
            </div>
            {!activationsFocus ? (
              <div className="parashari-desk-tools__divs" aria-label="Divisional chart">
                <span className="parashari-desk-tools__label">
                  {selectedDivisionalChart.shortLabel}
                </span>
                <div className="parashari-desk-pills">
                  {DIVISIONAL_CHART_OPTIONS.map((option) => (
                    <button
                      key={option.value}
                      type="button"
                      className={selectedDx === option.value ? 'is-active' : ''}
                      onClick={() => setSelectedDx(option.value)}
                      title={option.label}
                    >
                      {option.shortLabel}
                    </button>
                  ))}
                  <span className="parashari-desk-pills__sep" aria-hidden="true" />
                  {JAIMINI_CHART_OPTIONS.map((option) => (
                    <button
                      key={option.value}
                      type="button"
                      className={`parashari-desk-pills__jaimini${selectedDx === option.value ? ' is-active' : ''}`}
                      onClick={() => setSelectedDx(option.value)}
                      title={option.label}
                    >
                      {option.shortLabel}
                    </button>
                  ))}
                </div>
              </div>
            ) : null}
            <DeskBirthPanchang birthData={birthData} />
            <DeskSpecialPoints birthData={birthData} chartData={chartData} variant="strip" />
            <div className="parashari-desk-tools__meta">
              <DeskConditionStrip birthData={birthData} chartData={chartData} />
              <DeskSpecialLagnas birthData={birthData} chartData={chartData} />
            </div>
          </div>

          <div className={`parashari-desk-grid${activationsFocus ? ' parashari-desk-grid--act-focus' : ''}`}>
            <section className="parashari-desk-panel parashari-desk-panel--d1">
              <header className="parashari-desk-panel__head">
                <div className="parashari-desk-panel__titles">
                  <h2>D1</h2>
                  <span>Lagna</span>
                </div>
                <em className="parashari-desk-panel__hint">Click a house for insight dock</em>
              </header>
              <div className="parashari-desk-chart">
                <ChartWidget
                  title="D1"
                  chartType="lagna"
                  chartData={chartData}
                  birthData={birthData}
                  defaultStyle="north"
                  showFooterHint={false}
                  embedInDashboard
                  deskMode
                  onHouseSelect={handleHouseSelect}
                  selectedHouseNumber={houseSelection?.houseNumber}
                />
              </div>
            </section>

            {!activationsFocus ? (
              <section className="parashari-desk-panel parashari-desk-panel--d9">
                <header className="parashari-desk-panel__head">
                  <div className="parashari-desk-panel__titles">
                    <h2>D9</h2>
                    <span>Navamsa</span>
                  </div>
                  <em className="parashari-desk-panel__hint">Click a house for insight dock</em>
                </header>
                <div className="parashari-desk-chart">
                  <ChartWidget
                    title="D9"
                    chartType="navamsa"
                    chartData={chartData}
                    birthData={birthData}
                    defaultStyle="north"
                    showFooterHint={false}
                    embedInDashboard
                    deskMode
                    onHouseSelect={handleHouseSelect}
                    selectedHouseNumber={houseSelection?.houseNumber}
                  />
                </div>
              </section>
            ) : null}

            {!activationsFocus ? (
              <section className="parashari-desk-panel parashari-desk-panel--div">
                <header className="parashari-desk-panel__head">
                  <div className="parashari-desk-panel__titles">
                    <h2>{selectedDivisionalChart.shortLabel}</h2>
                    <span>{selectedDivisionalChart.label}</span>
                  </div>
                  <em className="parashari-desk-panel__hint">Click a house for insight dock</em>
                </header>
                <div className="parashari-desk-chart">
                  <ChartWidget
                    title={selectedDivisionalChart.shortLabel}
                    chartType={dxChartType}
                    chartData={chartData}
                    birthData={birthData}
                    division={typeof selectedDx === 'number' ? selectedDx : undefined}
                    defaultStyle="north"
                    showFooterHint={false}
                    embedInDashboard
                    deskMode
                    onHouseSelect={handleHouseSelect}
                    selectedHouseNumber={houseSelection?.houseNumber}
                  />
                </div>
              </section>
            ) : null}

            <section className="parashari-desk-panel parashari-desk-panel--transit">
              <header className="parashari-desk-panel__head">
                <div className="parashari-desk-panel__titles">
                  <h2>Transit</h2>
                  <span>As-of sky</span>
                </div>
                <em className="parashari-desk-panel__hint">Click a house for insight dock</em>
              </header>
              <div className="parashari-desk-chart">
                <ChartWidget
                  title="Transit"
                  chartType="transit"
                  chartData={chartData}
                  birthData={birthData}
                  transitDate={asOfDate}
                  defaultStyle="north"
                  showFooterHint={false}
                  embedInDashboard
                  deskMode
                  onHouseSelect={handleHouseSelect}
                  selectedHouseNumber={houseSelection?.houseNumber}
                />
              </div>
            </section>

            <section className="parashari-desk-panel parashari-desk-panel--dasha">
              <DeskDashaPanel
                birthData={birthData}
                chartData={chartData}
                asOfDate={asOfDate}
                onJumpToDate={setAsOfDate}
                system={dashaSystem}
                onSystemChange={setDashaSystem}
              />
            </section>

            {activationsFocus ? (
              <section
                className="parashari-desk-panel parashari-desk-panel--activations"
                aria-label="House activations"
              >
                <DeskActivationsPanel
                  result={activationLedger}
                  loading={activationLoading}
                  error={activationError}
                  asOfDate={asOfDate}
                  onJumpToDate={setAsOfDate}
                  layout="focus"
                  onOpenFull={() => navigate(`/charts-dashas/activations?asOf=${formatAsOfIso(asOfDate)}`)}
                />
              </section>
            ) : (
              <section className="parashari-desk-panel parashari-desk-panel--analysis" aria-label="Analysis dock">
                <div className="parashari-desk-analysis__chrome">
                  <DeskStrengthStrip
                    birthData={birthData}
                    chartData={chartData}
                    onOpenTool={setActiveTool}
                  />
                  <header className="parashari-desk-analysis__head">
                    <div className="parashari-desk-analysis__tabs" role="tablist" aria-label="Analysis">
                      <button
                        type="button"
                        role="tab"
                        aria-selected={analysisTab === 'house'}
                        className={analysisTab === 'house' ? 'is-active' : ''}
                        onClick={() => setAnalysisTab('house')}
                        title="House insight — click a house on any chart"
                      >
                        House{houseSelection?.houseNumber ? ` ${houseSelection.houseNumber}` : ''}
                      </button>
                      <button
                        type="button"
                        role="tab"
                        aria-selected={analysisTab === 'positions'}
                        className={analysisTab === 'positions' ? 'is-active' : ''}
                        onClick={() => setAnalysisTab('positions')}
                      >
                        Positions
                      </button>
                      <button
                        type="button"
                        role="tab"
                        aria-selected={analysisTab === 'yogas'}
                        className={analysisTab === 'yogas' ? 'is-active' : ''}
                        onClick={() => setAnalysisTab('yogas')}
                      >
                        Yogas
                      </button>
                      <button
                        type="button"
                        role="tab"
                        aria-selected={analysisTab === 'friends'}
                        className={analysisTab === 'friends' ? 'is-active' : ''}
                        onClick={() => setAnalysisTab('friends')}
                        title="Panchadha Maitri — five-fold friendship"
                      >
                        Friends
                      </button>
                      <button
                        type="button"
                        role="tab"
                        aria-selected={analysisTab === 'lords'}
                        className={analysisTab === 'lords' ? 'is-active' : ''}
                        onClick={() => setAnalysisTab('lords')}
                        title="House lord map — lord, seat, dignity, tenants"
                      >
                        Lords
                      </button>
                      <button
                        type="button"
                        role="tab"
                        aria-selected={analysisTab === 'aspects'}
                        className={analysisTab === 'aspects' ? 'is-active' : ''}
                        onClick={() => setAnalysisTab('aspects')}
                        title="Parashari graha drishti — special aspects"
                      >
                        Aspects
                      </button>
                    </div>
                  </header>
                </div>
                <div className="parashari-desk-analysis__body" role="tabpanel">
                  {analysisTab === 'house' ? (
                    <DeskHouseInsight
                      birthData={birthData}
                      chartData={chartData}
                      selection={houseSelection}
                      asOfDate={asOfDate}
                      chartId={houseSelection?.chartId || 'lagna'}
                    />
                  ) : analysisTab === 'positions' ? (
                    <DeskPositionsTable chartData={chartData} />
                  ) : analysisTab === 'yogas' ? (
                    <DeskYogasPanel birthData={birthData} />
                  ) : analysisTab === 'friends' ? (
                    <DeskFriendshipPanel chartData={chartData} />
                  ) : analysisTab === 'lords' ? (
                    <DeskHouseLordsPanel chartData={chartData} />
                  ) : (
                    <DeskAspectsPanel chartData={chartData} />
                  )}
                </div>
              </section>
            )}
          </div>
        </div>
      )}

      {user ? (
        <BirthFormModal
          isOpen={showBirthModal}
          onClose={() => setShowBirthModal(false)}
          onSubmit={(data) => {
            if (data) setBirthData?.(data);
            setShowBirthModal(false);
          }}
          defaultActiveTab={birthModalTab}
          title="Parashari Desk — Birth details"
          description="Create a new chart or choose a saved one for the desk."
          prefilledData={birthData}
        />
      ) : null}

      {hasChart ? (
        <DeskToolModals
          birthData={birthData}
          chartData={chartData}
          activeTool={activeTool}
          onClose={() => setActiveTool(null)}
        />
      ) : null}
    </div>
  );
};

export default ChartsDashasWorkspacePage;
