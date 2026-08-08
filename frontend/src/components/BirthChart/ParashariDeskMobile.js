import React, { useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import ChartWidget from '../Charts/ChartWidget';
import DeskDateNavigator from './DeskDateNavigator';
import DeskDashaPanel from './DeskDashaPanel';
import DeskActivationsPanel from './DeskActivationsPanel';
import DeskHouseInsight from './DeskHouseInsight';
import DeskPositionsTable from './DeskPositionsTable';
import DeskYogasPanel from './DeskYogasPanel';
import DeskFriendshipPanel from './DeskFriendshipPanel';
import DeskHouseLordsPanel from './DeskHouseLordsPanel';
import DeskAspectsPanel from './DeskAspectsPanel';
import DeskStrengthStrip from './DeskStrengthStrip';
import DeskBirthPanchang from './DeskBirthPanchang';
import DeskSpecialPoints from './DeskSpecialPoints';
import DeskConditionStrip from './DeskConditionStrip';
import DeskSpecialLagnas from './DeskSpecialLagnas';
import './ParashariDeskMobile.css';

const HUB_TABS = [
  { id: 'chart', label: 'Chart' },
  { id: 'dasha', label: 'Dasha' },
  { id: 'act', label: 'Act' },
  { id: 'more', label: 'More' },
];

const MORE_TABS = [
  { id: 'house', label: 'House', icon: '⌂' },
  { id: 'positions', label: 'Pos', icon: '☷' },
  { id: 'yogas', label: 'Yogas', icon: '✦' },
  { id: 'friends', label: 'Friends', icon: '↔' },
  { id: 'lords', label: 'Lords', icon: '♔' },
  { id: 'aspects', label: 'Aspects', icon: '◎' },
  { id: 'meta', label: 'Meta', icon: '⋯' },
];

const SIGN_NAMES = [
  'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
  'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces',
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

function buildHouseSelection(chartData, houseNumber, chartId = 'lagna') {
  const lagnaSign = chartData?.houses?.[0]?.sign
    ?? (typeof chartData?.ascendant === 'number'
      ? Math.floor((((chartData.ascendant % 360) + 360) % 360) / 30)
      : 0);
  const rashiIndex = chartData?.houses?.[houseNumber - 1]?.sign
    ?? ((Number(lagnaSign) + houseNumber - 1) % 12);
  return {
    houseNumber,
    rashiIndex,
    signName: SIGN_NAMES[rashiIndex] || '',
    chartId,
  };
}

/**
 * Phone Parashari desk — ChartsHub-style tabs (Chart / Dasha / Act / More).
 */
export default function ParashariDeskMobile({
  birthData,
  chartData,
  asOfDate,
  onAsOfChange,
  selectedDx,
  onSelectedDxChange,
  divisionalOptions,
  jaiminiOptions,
  selectedDivisionalChart,
  dxChartType,
  dashaSystem,
  onDashaSystemChange,
  activationLedger,
  activationLoading,
  activationError,
  activationNowCount,
  analysisTab,
  onAnalysisTabChange,
  houseSelection,
  onHouseSelect,
  onOpenTool,
  onChangeNative,
  initialHubTab,
}) {
  const navigate = useNavigate();
  const requestedHubTab = HUB_TABS.some((tab) => tab.id === initialHubTab)
    ? initialHubTab
    : 'chart';
  const [hubTab, setHubTab] = useState(requestedHubTab);
  const [chartPill, setChartPill] = useState('lagna');
  const [metaOpen, setMetaOpen] = useState(true);
  const [sheetOpen, setSheetOpen] = useState(false);
  const chartNavRef = useRef(null);
  const moreNavRef = useRef(null);

  useEffect(() => {
    setHubTab(requestedHubTab);
  }, [requestedHubTab]);

  const showAsOf = (hubTab === 'chart' && chartPill === 'transit')
    || hubTab === 'dasha'
    || hubTab === 'act';

  const mobileChartOptions = useMemo(() => {
    const divisionals = (divisionalOptions || []).map((option) => ({
      ...option,
      id: `division-${option.value}`,
      mode: option.value === 9 ? 'navamsa' : 'divisional',
      icon: {
        2: '💰', 3: '👫', 4: '🏡', 7: '👶', 9: '💎', 10: '💼',
        12: '👪', 16: '🚗', 20: '🙏', 24: '📚', 27: '⭐', 30: '⚠️',
        40: '🍀', 45: '🎭', 60: '⏳',
      }[option.value] || '◇',
    }));
    const jaimini = (jaiminiOptions || []).map((option) => ({
      ...option,
      id: `division-${option.value}`,
      mode: 'divisional',
      icon: option.value === 'karkamsa' ? '🎯' : '🕉️',
    }));
    const navamsa = divisionals.find((option) => option.value === 9);
    const otherDivisionals = divisionals.filter((option) => option.value !== 9);
    return [
      { id: 'lagna', shortLabel: 'D1', label: 'Lagna', mode: 'lagna', icon: '🏠' },
      ...(navamsa ? [navamsa] : []),
      { id: 'transit', shortLabel: 'Tr', label: 'Transit', mode: 'transit', icon: '🪐' },
      ...jaimini,
      ...otherDivisionals,
    ];
  }, [divisionalOptions, jaiminiOptions]);

  useEffect(() => {
    if (hubTab !== 'chart') return;
    const nav = chartNavRef.current;
    const active = nav?.querySelector('.is-active');
    if (!nav || !active) return;
    const left = active.offsetLeft - ((nav.clientWidth - active.clientWidth) / 2);
    nav.scrollTo({ left: Math.max(0, left), behavior: 'smooth' });
  }, [hubTab, chartPill, selectedDx]);

  useEffect(() => {
    if (hubTab !== 'more') return;
    const nav = moreNavRef.current;
    const active = nav?.querySelector('.is-active');
    if (!nav || !active) return;
    const left = active.offsetLeft - ((nav.clientWidth - active.clientWidth) / 2);
    nav.scrollTo({ left: Math.max(0, left), behavior: 'smooth' });
  }, [hubTab, analysisTab]);

  const activeChart = useMemo(() => {
    if (chartPill === 'lagna') {
      return { chartType: 'lagna', title: 'D1', division: undefined };
    }
    if (chartPill === 'navamsa') {
      return { chartType: 'navamsa', title: 'D9', division: undefined };
    }
    if (chartPill === 'transit') {
      return { chartType: 'transit', title: 'Transit', division: undefined };
    }
    return {
      chartType: dxChartType,
      title: selectedDivisionalChart?.shortLabel || 'Dx',
      division: typeof selectedDx === 'number' ? selectedDx : undefined,
    };
  }, [chartPill, dxChartType, selectedDivisionalChart, selectedDx]);

  const handleHouseSelect = (sel) => {
    onHouseSelect?.(sel);
    setSheetOpen(true);
    onAnalysisTabChange?.('house');
  };

  const pickHouse = (houseNumber, { openSheet = false } = {}) => {
    const sel = buildHouseSelection(chartData, houseNumber, 'lagna');
    onHouseSelect?.(sel);
    onAnalysisTabChange?.('house');
    if (openSheet) setSheetOpen(true);
  };

  const openAct = () => setHubTab('act');

  const housePicker = (
    <div className="pdm__house-pick" role="group" aria-label="Select house">
      {Array.from({ length: 12 }, (_, i) => i + 1).map((n) => (
        <button
          key={n}
          type="button"
          className={houseSelection?.houseNumber === n ? 'is-active' : ''}
          onClick={() => pickHouse(n, { openSheet: hubTab === 'chart' })}
        >
          H{n}
        </button>
      ))}
    </div>
  );

  return (
    <div className="pdm">
      <header className="pdm__chrome">
        <div className="pdm__bar">
          <button type="button" className="pdm__back" onClick={() => navigate('/')}>←</button>
          <div className="pdm__brand-wrap">
            <strong className="pdm__brand">Parashari</strong>
            <span className="pdm__native">{birthData?.name || 'Native'}</span>
          </div>
          <button type="button" className="pdm__change-native" onClick={onChangeNative}>
            Change native
          </button>
          <button type="button" className="pdm__link" onClick={() => navigate('/charts-dashas/kp')}>KP</button>
          <button type="button" className="pdm__link" onClick={() => navigate('/charts-dashas/nadi')}>Nadi</button>
        </div>

        <nav className="pdm__hub" aria-label="Desk sections">
          {HUB_TABS.map((tab) => (
            <button
              key={tab.id}
              type="button"
              className={hubTab === tab.id ? 'is-active' : ''}
              onClick={() => setHubTab(tab.id)}
            >
              {tab.label}
              {tab.id === 'act' && activationNowCount ? <em>{activationNowCount}</em> : null}
            </button>
          ))}
        </nav>

        {showAsOf ? (
          <div className="pdm__asof">
            <DeskDateNavigator
              date={asOfDate}
              onChange={onAsOfChange}
              onResetToToday={() => onAsOfChange?.(new Date())}
              showTime
            />
          </div>
        ) : null}
      </header>

      <div className="pdm__body">
        {hubTab === 'chart' ? (
          <section className="pdm__pane pdm__pane--chart">
            <div className="pdm__chart">
              <ChartWidget
                title={activeChart.title}
                chartType={activeChart.chartType}
                chartData={chartData}
                birthData={birthData}
                transitDate={chartPill === 'transit' ? asOfDate : undefined}
                division={activeChart.division}
                defaultStyle="north"
                showFooterHint={false}
                embedInDashboard
                deskMode
                onHouseSelect={handleHouseSelect}
                selectedHouseNumber={houseSelection?.houseNumber}
              />
            </div>

            {(chartPill === 'lagna' || chartPill === 'navamsa') ? (
              <button type="button" className="pdm__act-cta" onClick={openAct}>
                <span>
                  <strong>What is activated now?</strong>
                  <em>Active houses, reasons, timing</em>
                </span>
                <i aria-hidden>→</i>
              </button>
            ) : null}

            <button
              type="button"
              className="pdm__meta-toggle"
              onClick={() => setMetaOpen((open) => !open)}
              aria-expanded={metaOpen}
            >
              Chart meta {metaOpen ? '▴' : '▾'}
            </button>
            {metaOpen ? (
              <div className="pdm__meta">
                <DeskBirthPanchang birthData={birthData} />
                <DeskSpecialPoints birthData={birthData} chartData={chartData} variant="strip" />
                <DeskConditionStrip birthData={birthData} chartData={chartData} />
                <DeskSpecialLagnas birthData={birthData} chartData={chartData} />
              </div>
            ) : null}

            <nav className="pdm__chart-nav" aria-label="Chart browser">
              <div
                ref={chartNavRef}
                className="pdm__pills pdm__pills--charts"
                role="tablist"
                aria-label="Chart type"
              >
                {mobileChartOptions.map((pill) => {
                  const isActive = pill.mode === 'divisional'
                    ? chartPill === 'divisional' && selectedDx === pill.value
                    : chartPill === pill.mode;
                  return (
                    <button
                      key={pill.id}
                      type="button"
                      role="tab"
                      title={pill.label}
                      aria-selected={isActive}
                      className={isActive ? 'is-active' : ''}
                      onClick={() => {
                        if (pill.value != null) onSelectedDxChange?.(pill.value);
                        setChartPill(pill.mode);
                      }}
                    >
                      <span className="pdm__chart-tab-icon" aria-hidden>{pill.icon}</span>
                      <span className="pdm__chart-tab-label">{pill.shortLabel}</span>
                    </button>
                  );
                })}
              </div>
            </nav>
          </section>
        ) : null}

        {hubTab === 'dasha' ? (
          <section className="pdm__pane pdm__pane--dasha">
            <DeskDashaPanel
              birthData={birthData}
              chartData={chartData}
              asOfDate={asOfDate}
              onJumpToDate={onAsOfChange}
              system={dashaSystem}
              onSystemChange={onDashaSystemChange}
              layout="mobile"
            />
          </section>
        ) : null}

        {hubTab === 'act' ? (
          <section className="pdm__pane pdm__pane--act">
            <DeskActivationsPanel
              result={activationLedger}
              loading={activationLoading}
              error={activationError}
              asOfDate={asOfDate}
              onJumpToDate={onAsOfChange}
              layout="mobile"
              onOpenFull={() => navigate(`/charts-dashas/activations?asOf=${formatAsOfIso(asOfDate)}`)}
            />
          </section>
        ) : null}

        {hubTab === 'more' ? (
          <section className="pdm__pane pdm__pane--more">
            <DeskStrengthStrip
              birthData={birthData}
              chartData={chartData}
              onOpenTool={(toolId) => {
                if (toolId === 'ashtakavarga') {
                  navigate('/tools/ashtakavarga');
                  return;
                }
                onOpenTool?.(toolId);
              }}
              layout="mobile"
            />
            <div className={`pdm__more-body${analysisTab === 'meta' ? ' pdm__more-body--meta' : ''}`}>
              {analysisTab === 'house' ? (
                <>
                  {housePicker}
                  <DeskHouseInsight
                    birthData={birthData}
                    chartData={chartData}
                    selection={houseSelection}
                    asOfDate={asOfDate}
                    chartId={houseSelection?.chartId || 'lagna'}
                    emptyTitle="Pick a house below"
                    emptyHint="Or open Chart and tap a bhāva on D1 / D9 / Dx / Transit"
                    emptyAction={(
                      <button
                        type="button"
                        className="pdm__goto-chart"
                        onClick={() => setHubTab('chart')}
                      >
                        Open Chart tab
                      </button>
                    )}
                  />
                </>
              ) : analysisTab === 'positions' ? (
                <DeskPositionsTable chartData={chartData} />
              ) : analysisTab === 'yogas' ? (
                <DeskYogasPanel birthData={birthData} />
              ) : analysisTab === 'friends' ? (
                <DeskFriendshipPanel chartData={chartData} />
              ) : analysisTab === 'lords' ? (
                <DeskHouseLordsPanel chartData={chartData} />
              ) : analysisTab === 'aspects' ? (
                <DeskAspectsPanel chartData={chartData} />
              ) : (
                <div className="pdm__meta pdm__meta--overview">
                  <DeskBirthPanchang birthData={birthData} />
                  <DeskSpecialPoints birthData={birthData} chartData={chartData} variant="strip" />
                  <DeskConditionStrip
                    birthData={birthData}
                    chartData={chartData}
                    label="Planetary conditions"
                  />
                  <DeskSpecialLagnas birthData={birthData} chartData={chartData} />
                </div>
              )}
            </div>

            <nav className="pdm__more-nav" aria-label="Analysis browser">
              <div ref={moreNavRef} className="pdm__more-tabs" role="tablist" aria-label="Analysis">
                {MORE_TABS.map((tab) => {
                  const isActive = analysisTab === tab.id;
                  return (
                    <button
                      key={tab.id}
                      type="button"
                      role="tab"
                      aria-selected={isActive}
                      className={isActive ? 'is-active' : ''}
                      onClick={() => onAnalysisTabChange?.(tab.id)}
                    >
                      <span className="pdm__more-tab-icon" aria-hidden>{tab.icon}</span>
                      <span className="pdm__more-tab-label">
                        {tab.id === 'house' && houseSelection?.houseNumber
                          ? `H${houseSelection.houseNumber}`
                          : tab.label}
                      </span>
                    </button>
                  );
                })}
              </div>
            </nav>
          </section>
        ) : null}
      </div>

      {sheetOpen && houseSelection ? (
        <div className="pdm__sheet" role="dialog" aria-label="House insight">
          <button
            type="button"
            className="pdm__sheet-backdrop"
            aria-label="Close"
            onClick={() => setSheetOpen(false)}
          />
          <div className="pdm__sheet-card">
            <header>
              <strong>
                House {houseSelection.houseNumber}
                {houseSelection.signName ? ` · ${houseSelection.signName}` : ''}
              </strong>
              <button type="button" onClick={() => setSheetOpen(false)}>Close</button>
            </header>
            <div className="pdm__sheet-body">
              <DeskHouseInsight
                birthData={birthData}
                chartData={chartData}
                selection={houseSelection}
                asOfDate={asOfDate}
                chartId={houseSelection?.chartId || 'lagna'}
              />
            </div>
            <button
              type="button"
              className="pdm__sheet-more"
              onClick={() => {
                setSheetOpen(false);
                setHubTab('more');
                onAnalysisTabChange?.('house');
              }}
            >
              Open in More
            </button>
          </div>
        </div>
      ) : null}
    </div>
  );
}
