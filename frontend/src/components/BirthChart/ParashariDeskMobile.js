import React, { useMemo, useState } from 'react';
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

const CHART_PILLS = [
  { id: 'lagna', label: 'D1', title: 'Lagna' },
  { id: 'navamsa', label: 'D9', title: 'Navamsa' },
  { id: 'divisional', label: 'Dx', title: 'Divisional' },
  { id: 'transit', label: 'Tr', title: 'Transit' },
];

const MORE_TABS = [
  { id: 'house', label: 'House' },
  { id: 'positions', label: 'Pos' },
  { id: 'yogas', label: 'Yogas' },
  { id: 'friends', label: 'Friends' },
  { id: 'lords', label: 'Lords' },
  { id: 'aspects', label: 'Aspects' },
  { id: 'meta', label: 'Meta' },
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
}) {
  const navigate = useNavigate();
  const [hubTab, setHubTab] = useState('chart');
  const [chartPill, setChartPill] = useState('lagna');
  const [metaOpen, setMetaOpen] = useState(false);
  const [sheetOpen, setSheetOpen] = useState(false);

  const showAsOf = hubTab === 'chart' || hubTab === 'dasha' || hubTab === 'act';

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
            <button type="button" className="pdm__native" onClick={onChangeNative}>
              {birthData?.name || 'Native'}
            </button>
          </div>
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
            <div className="pdm__pills" role="tablist" aria-label="Chart type">
              {CHART_PILLS.map((pill) => (
                <button
                  key={pill.id}
                  type="button"
                  role="tab"
                  title={pill.title}
                  aria-selected={chartPill === pill.id}
                  className={chartPill === pill.id ? 'is-active' : ''}
                  onClick={() => setChartPill(pill.id)}
                >
                  {pill.id === 'divisional'
                    ? (selectedDivisionalChart?.shortLabel || 'Dx')
                    : pill.label}
                </button>
              ))}
            </div>

            {chartPill === 'divisional' ? (
              <div className="pdm__dx-scroll" aria-label="Divisional charts">
                {(divisionalOptions || []).map((option) => (
                  <button
                    key={option.value}
                    type="button"
                    className={selectedDx === option.value ? 'is-active' : ''}
                    onClick={() => onSelectedDxChange?.(option.value)}
                    title={option.label}
                  >
                    {option.shortLabel}
                  </button>
                ))}
                <span className="pdm__dx-sep" aria-hidden />
                {(jaiminiOptions || []).map((option) => (
                  <button
                    key={option.value}
                    type="button"
                    className={selectedDx === option.value ? 'is-active' : ''}
                    onClick={() => onSelectedDxChange?.(option.value)}
                    title={option.label}
                  >
                    {option.shortLabel}
                  </button>
                ))}
              </div>
            ) : null}

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
              layout="focus"
              onOpenFull={() => navigate(`/charts-dashas/activations?asOf=${formatAsOfIso(asOfDate)}`)}
            />
          </section>
        ) : null}

        {hubTab === 'more' ? (
          <section className="pdm__pane pdm__pane--more">
            <DeskStrengthStrip
              birthData={birthData}
              chartData={chartData}
              onOpenTool={onOpenTool}
            />
            <div className="pdm__more-tabs" role="tablist" aria-label="Analysis">
              {MORE_TABS.map((tab) => (
                <button
                  key={tab.id}
                  type="button"
                  role="tab"
                  aria-selected={analysisTab === tab.id || (tab.id === 'meta' && analysisTab === 'meta')}
                  className={(tab.id === 'meta' ? analysisTab === 'meta' : analysisTab === tab.id) ? 'is-active' : ''}
                  onClick={() => onAnalysisTabChange?.(tab.id)}
                >
                  {tab.id === 'house' && houseSelection?.houseNumber
                    ? `H${houseSelection.houseNumber}`
                    : tab.label}
                </button>
              ))}
            </div>
            <div className="pdm__more-body">
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
                <div className="pdm__meta">
                  <DeskBirthPanchang birthData={birthData} />
                  <DeskSpecialPoints birthData={birthData} chartData={chartData} variant="strip" />
                  <DeskConditionStrip birthData={birthData} chartData={chartData} />
                  <DeskSpecialLagnas birthData={birthData} chartData={chartData} />
                </div>
              )}
            </div>
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
