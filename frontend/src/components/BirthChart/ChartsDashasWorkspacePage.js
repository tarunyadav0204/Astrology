import React, { useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import BirthFormModal from '../BirthForm/BirthFormModal';
import SEOHead from '../SEO/SEOHead';
import ChartWidget from '../Charts/ChartWidget';
import TransitControls from '../TransitControls/TransitControls';
import DeskDashaPanel from './DeskDashaPanel';
import DeskSpecialPoints from './DeskSpecialPoints';
import DeskBirthPanchang from './DeskBirthPanchang';
import DeskConditionStrip from './DeskConditionStrip';
import DeskSpecialLagnas from './DeskSpecialLagnas';
import DeskKarakasPanel from './DeskKarakasPanel';
import DeskPositionsTable from './DeskPositionsTable';
import ClassicalLifeReading from './ClassicalLifeReading';
import DeskYogasPanel from './DeskYogasPanel';
import DeskFriendshipPanel from './DeskFriendshipPanel';
import DeskHouseLordsPanel from './DeskHouseLordsPanel';
import DeskAspectsPanel from './DeskAspectsPanel';
import DeskHouseInsight from './DeskHouseInsight';
import DeskStrengthStrip from './DeskStrengthStrip';
import DeskActivationsPanel from './DeskActivationsPanel';
import DeskTopicSelector from './DeskTopicSelector';
import DeskTopicLens from './DeskTopicLens';
import DeskToolModals from './DeskToolModals';
import DeskDrawingBoard from './DeskDrawingBoard';
import ParashariDeskMobile from './ParashariDeskMobile';
import ChartActivationKey from './ChartActivationKey';
import ChartOverviewPopup from '../Charts/ChartOverviewPopup';
import HouseInsightPopup from '../Charts/HouseInsightPopup';
import { useAstrology } from '../../context/AstrologyContext';
import { useCredits } from '../../context/CreditContext';
import { generatePageSEO } from '../../config/seo.config';
import { apiService } from '../../services/apiService';
import './ChartsDashasWorkspacePage.css';

// The four-chart workstation needs genuine desktop width. Tablet portrait and
// compact landscape use the focused hub instead of shrinking the workstation.
const MOBILE_DESK_MQ = '(max-width: 1180px)';
const PARASHARI_PROFILE_KEY = 'astroroshni_parashari_view_profile_v1';
const PARASHARI_SPLIT_KEY = 'astroroshni_parashari_desk_split_v1';
const PARASHARI_COMPARE_CHART_KEY = 'astroroshni_parashari_compare_chart_v1';
const PARASHARI_TOPIC_KEY = 'astroroshni_parashari_topic_v1';
const DEFAULT_CHART_ROW_PERCENT = 54;
const MIN_CHART_ROW_PERCENT = 30;
const MAX_CHART_ROW_PERCENT = 76;
const DEFAULT_PARASHARI_PROFILE = { ayanamsha: 'lahiri', node_type: 'mean' };
const AYANAMSHA_OPTIONS = [
  ['lahiri', 'Lahiri'],
  ['raman', 'Raman'],
  ['krishnamurti', 'Krishnamurti ayanamsha'],
  ['yukteshwar', 'Yukteshwar'],
  ['true_chitra', 'True Chitra'],
  ['true_revati', 'True Revati'],
  ['true_pushya', 'Pushya Paksha (True Pushya)'],
  ['jn_bhasin', 'J. N. Bhasin'],
  ['kp_291', 'KP 291 ayanamsha'],
  ['lahiri_1940', 'Lahiri 1940'],
  ['lahiri_icrc', 'Lahiri ICRC'],
];
const SUPPORTED_AYANAMSHAS = new Set(AYANAMSHA_OPTIONS.map(([value]) => value));

function clampChartRowPercent(value) {
  return Math.min(MAX_CHART_ROW_PERCENT, Math.max(MIN_CHART_ROW_PERCENT, value));
}

function loadChartRowPercent() {
  if (typeof window === 'undefined') return DEFAULT_CHART_ROW_PERCENT;
  const savedValue = window.localStorage.getItem(PARASHARI_SPLIT_KEY);
  if (savedValue === null) return DEFAULT_CHART_ROW_PERCENT;
  const saved = Number(savedValue);
  return Number.isFinite(saved)
    ? clampChartRowPercent(saved)
    : DEFAULT_CHART_ROW_PERCENT;
}

function loadParashariProfile() {
  if (typeof window === 'undefined') return DEFAULT_PARASHARI_PROFILE;
  try {
    const saved = JSON.parse(window.localStorage.getItem(PARASHARI_PROFILE_KEY) || '{}');
    return {
      ayanamsha: SUPPORTED_AYANAMSHAS.has(saved.ayanamsha)
        ? saved.ayanamsha
        : 'lahiri',
      node_type: saved.node_type === 'true' ? 'true' : 'mean',
    };
  } catch {
    return DEFAULT_PARASHARI_PROFILE;
  }
}

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
  { value: 2, shortLabel: 'D2', label: 'Hora', purpose: 'Wealth and resources' },
  { value: 3, shortLabel: 'D3', label: 'Drekkana', purpose: 'Siblings, courage and vitality' },
  { value: 4, shortLabel: 'D4', label: 'Chaturthamsa', purpose: 'Home, property and fortune' },
  { value: 7, shortLabel: 'D7', label: 'Saptamsa', purpose: 'Children and lineage' },
  { value: 9, shortLabel: 'D9', label: 'Navamsa', purpose: 'Marriage and dharma' },
  { value: 10, shortLabel: 'D10', label: 'Dasamsa', purpose: 'Career, status and professional work' },
  { value: 12, shortLabel: 'D12', label: 'Dwadasamsa', purpose: 'Parents and ancestry' },
  { value: 16, shortLabel: 'D16', label: 'Shodasamsa', purpose: 'Vehicles, comforts and happiness' },
  { value: 20, shortLabel: 'D20', label: 'Vimshamsa', purpose: 'Spiritual practice and worship' },
  { value: 24, shortLabel: 'D24', label: 'Chaturvimshamsa', purpose: 'Education and learning' },
  { value: 27, shortLabel: 'D27', label: 'Saptavimshamsa', purpose: 'Strengths and weaknesses' },
  { value: 30, shortLabel: 'D30', label: 'Trimshamsa', purpose: 'Misfortune and vulnerabilities' },
  { value: 40, shortLabel: 'D40', label: 'Khavedamsa', purpose: 'Maternal legacy and auspiciousness' },
  { value: 45, shortLabel: 'D45', label: 'Akshavedamsa', purpose: 'Paternal legacy and character' },
  { value: 60, shortLabel: 'D60', label: 'Shashtyamsa', purpose: 'Deep karmic pattern' },
];

const SPECIAL_CHART_OPTIONS = [
  { value: 'bhav_chalit', shortLabel: 'BC', label: 'Bhava Chalit', purpose: 'House-cusp adjusted placements' },
  { value: 'karkamsa', shortLabel: 'Ka', label: 'Kārkāṁśa', purpose: 'Atmakaraka in Navamsa' },
  { value: 'swamsa', shortLabel: 'Sw', label: 'Swāṁśa', purpose: 'Navamsa Lagna as the first house' },
];

const COMPARE_CHART_OPTIONS = DIVISIONAL_CHART_OPTIONS.filter((option) => option.value !== 9);
const FREQUENT_COMPARE_VALUES = new Set([2, 3, 4, 7, 10, 12]);
const COMPARE_CHART_VALUES = new Set([
  ...COMPARE_CHART_OPTIONS.map((option) => option.value),
  ...SPECIAL_CHART_OPTIONS.map((option) => option.value),
]);

function loadCompareChart() {
  if (typeof window === 'undefined') return 10;
  const saved = window.localStorage.getItem(PARASHARI_COMPARE_CHART_KEY);
  const normalized = saved && /^\d+$/.test(saved) ? Number(saved) : saved;
  return COMPARE_CHART_VALUES.has(normalized) ? normalized : 10;
}

function loadTopicLens() {
  if (typeof window === 'undefined') return 'whole_chart';
  return window.localStorage.getItem(PARASHARI_TOPIC_KEY) || 'whole_chart';
}

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

function formatWorkspaceDate(date, options = {}) {
  if (!(date instanceof Date) || Number.isNaN(date.getTime())) return '—';
  return date.toLocaleDateString('en-IN', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    ...options,
  });
}

const SIGN_NAMES = [
  'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
  'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces',
];

const HOUSE_AREAS = [
  'Self', 'Wealth', 'Skills', 'Home', 'Children', 'Health',
  'Partner', 'Change', 'Fortune', 'Career', 'Gains', 'Release',
];

function buildHouseSelection(renderedChartData, houseNumber, chartId = 'lagna') {
  const lagnaSign = renderedChartData?.houses?.[0]?.sign
    ?? (typeof renderedChartData?.ascendant === 'number'
      ? Math.floor((((renderedChartData.ascendant % 360) + 360) % 360) / 30)
      : 0);
  const rashiIndex = renderedChartData?.houses?.[houseNumber - 1]?.sign
    ?? ((Number(lagnaSign) + houseNumber - 1) % 12);
  return {
    houseNumber,
    rashiIndex,
    signName: SIGN_NAMES[rashiIndex] || '',
    chartId,
  };
}

function occupantsForHouse(chartData, houseNumber) {
  if (!chartData?.planets || !houseNumber) return [];
  const lagnaSign = chartData.houses?.[0]?.sign
    ?? (typeof chartData.ascendant === 'number'
      ? Math.floor((((chartData.ascendant % 360) + 360) % 360) / 30)
      : 0);
  return Object.entries(chartData.planets)
    .filter(([name, data]) => {
      if (!data || name === 'InduLagna') return false;
      if (typeof data.house === 'number') return data.house === houseNumber;
      if (typeof data.sign !== 'number' || typeof lagnaSign !== 'number') return false;
      return ((data.sign - lagnaSign + 12) % 12) + 1 === houseNumber;
    })
    .map(([name, data]) => ({ name, ...data }));
}

const ChartsDashasWorkspacePage = ({
  user,
  onLogin,
  onOpenRegister,
}) => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const isMobileDesk = useMobileDesk();
  const { birthData, chartData, setBirthData } = useAstrology();
  const { features } = useCredits();
  const lifeTabEnabled = Boolean(features?.classical_life_tab_enabled);
  const [showBirthModal, setShowBirthModal] = useState(false);
  const [birthModalTab, setBirthModalTab] = useState('saved');
  /** One shared as-of clock for transit + dashas + activations */
  const [asOfDate, setAsOfDate] = useState(new Date());
  /** number (D2–D60) or 'karkamsa' | 'swamsa' */
  const [selectedDx, setSelectedDx] = useState(loadCompareChart);
  const [topicId, setTopicId] = useState(loadTopicLens);
  const [comparePickerOpen, setComparePickerOpen] = useState(false);
  const [dashaSystem, setDashaSystem] = useState('vimshottari');
  const [activationLedger, setActivationLedger] = useState(null);
  const [activationLoading, setActivationLoading] = useState(false);
  const [activationError, setActivationError] = useState(null);
  const [showChartActivations, setShowChartActivations] = useState(true);
  const [analysisTab, setAnalysisTab] = useState(() => topicId === 'whole_chart' ? 'positions' : 'judgment');
  const [analysisExpanded, setAnalysisExpanded] = useState(() => topicId !== 'whole_chart');
  const [activationsFocus, setActivationsFocus] = useState(false);
  const [activeTool, setActiveTool] = useState(null);
  const [houseSelection, setHouseSelection] = useState(null);
  const [overviewOpen, setOverviewOpen] = useState(false);
  const [houseSheetOpen, setHouseSheetOpen] = useState(false);
  const [drawingActive, setDrawingActive] = useState(false);
  const [viewProfile, setViewProfile] = useState(loadParashariProfile);
  const [appliedViewProfile, setAppliedViewProfile] = useState(DEFAULT_PARASHARI_PROFILE);
  const [viewChartData, setViewChartData] = useState(null);
  const [viewChartBirthKey, setViewChartBirthKey] = useState('');
  const [viewProfileLoading, setViewProfileLoading] = useState(false);
  const [chartRowPercent, setChartRowPercent] = useState(loadChartRowPercent);
  const workspaceGridRef = useRef(null);
  const comparePickerRef = useRef(null);
  const seoData = generatePageSEO('chartsDashasWorkspace', { path: '/charts-dashas' });
  const hasChart = Boolean(birthData && chartData);
  const isViewingNow = Math.abs(asOfDate.getTime() - Date.now()) < 5 * 60 * 1000;
  const workspaceDateLabel = formatWorkspaceDate(asOfDate);
  const currentBirthKey = [
    birthData?.chart_id || birthData?.birth_chart_id || birthData?.id || '',
    birthData?.date || '', birthData?.time || '', birthData?.latitude ?? '', birthData?.longitude ?? '',
  ].join('|');
  const drawingKey = [
    currentBirthKey,
    viewProfile.ayanamsha,
    viewProfile.node_type,
    formatAsOfIso(asOfDate),
    String(selectedDx),
    dashaSystem,
    Number(chartRowPercent).toFixed(1),
    activationsFocus ? 'activations' : 'workspace',
    analysisExpanded ? 'analysis-expanded' : `analysis-${analysisTab}`,
    isMobileDesk ? 'compact' : 'desktop',
  ].join('|');

  const openDrawingBoard = () => {
    setComparePickerOpen(false);
    setOverviewOpen(false);
    setHouseSheetOpen(false);
    setActiveTool(null);
    setDrawingActive(true);
  };

  useEffect(() => {
    window.localStorage.setItem(PARASHARI_PROFILE_KEY, JSON.stringify(viewProfile));
  }, [viewProfile]);

  useEffect(() => {
    window.localStorage.setItem(PARASHARI_SPLIT_KEY, String(chartRowPercent));
  }, [chartRowPercent]);

  useEffect(() => {
    if (COMPARE_CHART_VALUES.has(selectedDx)) {
      window.localStorage.setItem(PARASHARI_COMPARE_CHART_KEY, String(selectedDx));
    }
  }, [selectedDx]);

  useEffect(() => {
    window.localStorage.setItem(PARASHARI_TOPIC_KEY, topicId);
  }, [topicId]);

  const changeTopic = (nextTopic, definition = null) => {
    setTopicId(nextTopic);
    setActivationsFocus(false);
    if (nextTopic !== 'whole_chart') {
      const comparisonChart = (definition?.primary_charts || [])
        .find((chart) => /^D\d+$/.test(chart) && chart !== 'D1');
      if (comparisonChart) setSelectedDx(Number(comparisonChart.slice(1)));
      setAnalysisTab('judgment');
      setAnalysisExpanded(true);
    } else if (analysisTab === 'judgment') {
      setAnalysisTab('positions');
      setAnalysisExpanded(false);
    }
  };

  useEffect(() => {
    if (!comparePickerOpen) return undefined;
    const closeWhenOutside = (event) => {
      if (!comparePickerRef.current?.contains(event.target)) setComparePickerOpen(false);
    };
    const closeOnEscape = (event) => {
      if (event.key === 'Escape') setComparePickerOpen(false);
    };
    document.addEventListener('pointerdown', closeWhenOutside);
    document.addEventListener('keydown', closeOnEscape);
    return () => {
      document.removeEventListener('pointerdown', closeWhenOutside);
      document.removeEventListener('keydown', closeOnEscape);
    };
  }, [comparePickerOpen]);

  useEffect(() => () => {
    document.body.classList.remove('is-resizing-parashari-workspace');
  }, []);

  const resizeWorkspaceFromPointer = (clientY) => {
    const rect = workspaceGridRef.current?.getBoundingClientRect();
    if (!rect?.height) return;
    setChartRowPercent(clampChartRowPercent(((clientY - rect.top) / rect.height) * 100));
  };

  const handleWorkspaceResizeStart = (event) => {
    event.preventDefault();
    event.currentTarget.setPointerCapture?.(event.pointerId);
    document.body.classList.add('is-resizing-parashari-workspace');
    resizeWorkspaceFromPointer(event.clientY);
  };

  const handleWorkspaceResizeMove = (event) => {
    if (!event.currentTarget.hasPointerCapture?.(event.pointerId)) return;
    resizeWorkspaceFromPointer(event.clientY);
  };

  const handleWorkspaceResizeEnd = (event) => {
    if (event.currentTarget.hasPointerCapture?.(event.pointerId)) {
      event.currentTarget.releasePointerCapture(event.pointerId);
    }
    document.body.classList.remove('is-resizing-parashari-workspace');
  };

  const handleWorkspaceResizeKey = (event) => {
    if (!['ArrowUp', 'ArrowDown', 'Home', 'End'].includes(event.key)) return;
    event.preventDefault();
    if (event.key === 'Home') setChartRowPercent(MIN_CHART_ROW_PERCENT);
    else if (event.key === 'End') setChartRowPercent(MAX_CHART_ROW_PERCENT);
    else setChartRowPercent((current) => clampChartRowPercent(
      current + (event.key === 'ArrowDown' ? 3 : -3),
    ));
  };

  useEffect(() => {
    if (!lifeTabEnabled && analysisTab === 'life') setAnalysisTab('positions');
  }, [analysisTab, lifeTabEnabled]);

  useEffect(() => {
    let cancelled = false;
    if (!birthData || !chartData) {
      setViewChartData(null);
      setViewChartBirthKey('');
      setAppliedViewProfile(DEFAULT_PARASHARI_PROFILE);
      return () => { cancelled = true; };
    }
    setViewProfileLoading(true);
    apiService.calculateChartOnly(birthData, viewProfile.node_type, viewProfile)
      .then((data) => {
        if (!cancelled) {
          setViewChartData(data);
          setViewChartBirthKey(currentBirthKey);
          setAppliedViewProfile(viewProfile);
        }
      })
      .catch((error) => {
        console.error('Failed to load Parashari viewing profile:', error);
      })
      .finally(() => {
        if (!cancelled) setViewProfileLoading(false);
      });
    return () => { cancelled = true; };
  }, [birthData, chartData, currentBirthKey, viewProfile]);

  const hasAppliedChart = Boolean(viewChartData && viewChartBirthKey === currentBirthKey);
  const renderedChartData = hasAppliedChart ? viewChartData : chartData;
  const effectiveViewProfile = hasAppliedChart ? appliedViewProfile : DEFAULT_PARASHARI_PROFILE;

  const updateViewProfile = (field, value) => {
    setViewProfile((current) => ({ ...current, [field]: value }));
  };

  useEffect(() => {
    if (isMobileDesk) {
      setActivationsFocus(false);
      setAnalysisExpanded(false);
    } else if (selectedDx === 9) {
      // D9 already has a fixed desktop panel; keep the third panel useful for comparison.
      setSelectedDx(10);
    }
  }, [isMobileDesk, selectedDx]);

  useEffect(() => {
    if (!analysisExpanded || drawingActive) return undefined;
    const handleKeyDown = (event) => {
      if (event.key === 'Escape') setAnalysisExpanded(false);
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [analysisExpanded, drawingActive]);

  useEffect(() => {
    setDrawingActive(false);
  }, [currentBirthKey]);

  const selectedDivisionalChart = useMemo(() => {
    if (typeof selectedDx === 'string') {
      return SPECIAL_CHART_OPTIONS.find((o) => o.value === selectedDx);
    }
    return DIVISIONAL_CHART_OPTIONS.find((option) => option.value === selectedDx) || DIVISIONAL_CHART_OPTIONS[5];
  }, [selectedDx]);

  const dxChartType = typeof selectedDx === 'string'
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
      calculationProfile: effectiveViewProfile,
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
  }, [birthData, chartData, user, asOfDate, effectiveViewProfile]);

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

  const activationHouseStates = useMemo(() => {
    if (activationLoading) return {};
    const rows = activationLedger?.house_activations || [];
    const asOf = formatAsOfIso(asOfDate);
    const stateRank = {
      dasha_connected: 1,
      dasha_transit_activated: 2,
      fully_reinforced: 3,
    };
    return rows.reduce((states, row) => {
      if (row.window?.start_date > asOf || row.window?.end_date < asOf) return states;
      if (!stateRank[row.state]) return states;
      const house = Number(row.house);
      if (!house || stateRank[row.state] <= (stateRank[states[house]] || 0)) return states;
      return { ...states, [house]: row.state };
    }, {});
  }, [activationLedger, activationLoading, asOfDate]);

  const visibleActivationHouseStates = showChartActivations ? activationHouseStates : {};

  useEffect(() => {
    setHouseSelection(null);
  }, [birthData?.date, birthData?.time, birthData?.name]);

  const handleHouseSelect = (sel) => {
    setHouseSelection(sel);
    setActivationsFocus(false);
    setAnalysisTab('house');
  };

  const openOverview = () => {
    setOverviewOpen(true);
    setHouseSheetOpen(false);
  };

  const openHouseFromOverview = (houseNumber) => {
    const sel = buildHouseSelection(renderedChartData || chartData, houseNumber, 'lagna');
    setHouseSelection(sel);
    setAnalysisTab('house');
    setActivationsFocus(false);
    setOverviewOpen(false);
    setHouseSheetOpen(true);
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
            title={activationsFocus ? 'Close activations focus (Esc)' : 'Open activations with D1, D9, Transit and dashas'}
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
          <button type="button" className="parashari-desk-chip" onClick={() => navigate('/charts-dashas/rectification')}>
            Rectify time
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
          {hasChart ? (
            <button
              type="button"
              className={`parashari-desk-chip parashari-desk-chip--draw${drawingActive ? ' is-active' : ''}`}
              onClick={openDrawingBoard}
              aria-pressed={drawingActive}
              title="Draw across charts, dashas and analysis"
            >
              <span aria-hidden="true">✎</span> Draw
            </button>
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
          chartData={renderedChartData}
          viewChartData={renderedChartData}
          calculationProfile={effectiveViewProfile}
          onCalculationProfileChange={updateViewProfile}
          calculationProfileLoading={viewProfileLoading}
          asOfDate={asOfDate}
          onAsOfChange={setAsOfDate}
          selectedDx={selectedDx}
          onSelectedDxChange={setSelectedDx}
          divisionalOptions={DIVISIONAL_CHART_OPTIONS}
          specialChartOptions={SPECIAL_CHART_OPTIONS}
          selectedDivisionalChart={selectedDivisionalChart}
          dxChartType={dxChartType}
          dashaSystem={dashaSystem}
          onDashaSystemChange={setDashaSystem}
          activationLedger={activationLedger}
          activationLoading={activationLoading}
          activationError={activationError}
          activationNowCount={activationNowCount}
          activationHouseStates={activationHouseStates}
          showChartActivations={showChartActivations}
          onShowChartActivationsChange={setShowChartActivations}
          analysisTab={analysisTab}
          onAnalysisTabChange={setAnalysisTab}
          houseSelection={houseSelection}
          onHouseSelect={handleHouseSelect}
          onOpenTool={setActiveTool}
          onChangeNative={() => openBirthModal('saved')}
          initialHubTab={searchParams.get('tab')}
          lifeTabEnabled={lifeTabEnabled}
          topicId={topicId}
          onTopicChange={changeTopic}
        />
      ) : (
        <div className="parashari-desk-body">
          {/* Shared tools — keeps all four chart cells equal */}
          <div className={`parashari-desk-tools${activationsFocus ? ' is-act-focus' : ''}`}>
            <div className="parashari-desk-tools__settings">
              <span className="parashari-desk-tools__category">Viewing</span>
              <DeskTopicSelector value={topicId} onChange={changeTopic} />
              <div className="parashari-view-profile" aria-label="Chart viewing standard">
                <span>Calculation standard</span>
                <select
                  value={viewProfile.ayanamsha}
                  onChange={(event) => updateViewProfile('ayanamsha', event.target.value)}
                  aria-label="Ayanamsha"
                >
                  {AYANAMSHA_OPTIONS.map(([value, label]) => (
                    <option value={value} key={value}>{label}</option>
                  ))}
                </select>
                <select
                  value={viewProfile.node_type}
                  onChange={(event) => updateViewProfile('node_type', event.target.value)}
                  aria-label="Rahu and Ketu calculation"
                >
                  <option value="mean">Mean nodes</option>
                  <option value="true">True nodes</option>
                </select>
                {viewProfileLoading ? <i aria-label="Updating chart">Updating…</i> : null}
              </div>
              <ChartActivationKey
                enabled={showChartActivations}
                onToggle={setShowChartActivations}
                loading={activationLoading}
              />
            </div>
            <div className="parashari-desk-tools__foundations">
              <span className="parashari-desk-tools__category">Birth &amp; reference</span>
              <div className="parashari-desk-tools__foundation-content">
                <DeskBirthPanchang birthData={birthData} calculationProfile={effectiveViewProfile} />
                <DeskSpecialPoints birthData={birthData} chartData={renderedChartData} variant="strip" calculationProfile={effectiveViewProfile} />
              </div>
            </div>
            <div className="parashari-desk-tools__meta">
              <span className="parashari-desk-tools__category">Chart roles</span>
              <DeskConditionStrip birthData={birthData} chartData={renderedChartData} calculationProfile={effectiveViewProfile} />
              <DeskSpecialLagnas birthData={birthData} chartData={renderedChartData} />
              <DeskKarakasPanel
                birthData={birthData}
                chartData={renderedChartData}
                onOpenTool={setActiveTool}
              />
            </div>
          </div>

          <section
            className={`parashari-time-nav${isViewingNow ? '' : ' is-away-from-now'}`}
            aria-label="Time navigator for transit, dashas and activations"
          >
            <div className="parashari-time-nav__identity">
              <span className="parashari-time-nav__icon" aria-hidden="true">◷</span>
              <div>
                <strong>Time navigator</strong>
                <small>Controls Transit, Dashas and Activations</small>
              </div>
            </div>
            <div className="parashari-time-nav__controls">
              <TransitControls
                date={asOfDate}
                onChange={setAsOfDate}
                onResetToToday={() => setAsOfDate(new Date())}
                variant="light"
                textColor="var(--color-text)"
                primaryColor="var(--color-brand)"
                showTime
                descriptiveNavigation
              />
            </div>
            <div className="parashari-time-nav__state" aria-live="polite">
              {isViewingNow ? (
                <span className="is-current">Viewing now</span>
              ) : (
                <>
                  <span>Viewing {workspaceDateLabel}</span>
                  <button type="button" onClick={() => setAsOfDate(new Date())}>Return to today</button>
                </>
              )}
            </div>
          </section>

          <div
            ref={workspaceGridRef}
            className={`parashari-desk-grid${activationsFocus ? ' parashari-desk-grid--act-focus' : ''}`}
            style={{
              '--pd-chart-row': `${chartRowPercent}fr`,
              '--pd-lower-row': `${100 - chartRowPercent}fr`,
            }}
          >
            <section className="parashari-desk-panel parashari-desk-panel--d1">
              <header className="parashari-desk-panel__head">
                <div className="parashari-desk-panel__titles">
                  <h2>D1</h2>
                  <span>Lagna</span>
                </div>
                <div className="parashari-desk-panel__actions">
                  <button type="button" className="parashari-desk-panel__cta" onClick={openOverview}>
                    Read this chart
                  </button>
                  <div id="parashari-d1-chart-controls" className="parashari-desk-panel__chart-controls" />
                </div>
              </header>
              <div className="parashari-desk-chart">
                <ChartWidget
                  title="D1"
                  chartType="lagna"
                  chartData={renderedChartData}
                  birthData={birthData}
                  defaultStyle="north"
                  showFooterHint={false}
                  embedInDashboard
                  deskMode
                  inlinePlanetDetails
                  deskControlsHostId="parashari-d1-chart-controls"
                  onHouseSelect={handleHouseSelect}
                  selectedHouseNumber={houseSelection?.houseNumber}
                  activationHouseStates={visibleActivationHouseStates}
                  calculationProfile={effectiveViewProfile}
                />
              </div>
            </section>

            <section className="parashari-desk-panel parashari-desk-panel--d9">
              <header className="parashari-desk-panel__head">
                <div className="parashari-desk-panel__titles">
                  <h2>D9</h2>
                  <span>Navamsa</span>
                </div>
                <div className="parashari-desk-panel__actions">
                  <em className="parashari-desk-panel__hint">Click a house for insight dock</em>
                  <div id="parashari-d9-chart-controls" className="parashari-desk-panel__chart-controls" />
                </div>
              </header>
              <div className="parashari-desk-chart">
                <ChartWidget
                  title="D9"
                  chartType="navamsa"
                  chartData={renderedChartData}
                  birthData={birthData}
                  defaultStyle="north"
                  showFooterHint={false}
                  embedInDashboard
                  deskMode
                  inlinePlanetDetails
                  deskControlsHostId="parashari-d9-chart-controls"
                  onHouseSelect={handleHouseSelect}
                  selectedHouseNumber={houseSelection?.houseNumber}
                  calculationProfile={effectiveViewProfile}
                />
              </div>
            </section>

            {!activationsFocus ? (
              <section className="parashari-desk-panel parashari-desk-panel--div">
                <header className="parashari-desk-panel__head">
                  <div className="parashari-compare-picker" ref={comparePickerRef}>
                    <span className="parashari-compare-picker__label">Compare chart</span>
                    <button
                      type="button"
                      className="parashari-compare-picker__trigger"
                      aria-haspopup="dialog"
                      aria-expanded={comparePickerOpen}
                      onClick={() => setComparePickerOpen((open) => !open)}
                    >
                      <strong>{selectedDivisionalChart.shortLabel}</strong>
                      <span>{selectedDivisionalChart.label}</span>
                      <b aria-hidden="true">⌄</b>
                    </button>
                    {comparePickerOpen ? (
                      <div className="parashari-compare-picker__menu" role="dialog" aria-label="Choose comparison chart">
                        <header>
                          <div>
                            <strong>Choose comparison chart</strong>
                            <span>D1, D9 and Transit remain fixed</span>
                          </div>
                          <button type="button" onClick={() => setComparePickerOpen(false)} aria-label="Close chart selector">×</button>
                        </header>
                        <section>
                          <h3>Frequently used</h3>
                          <div className="parashari-compare-picker__options">
                            {COMPARE_CHART_OPTIONS.filter((option) => FREQUENT_COMPARE_VALUES.has(option.value)).map((option) => (
                              <button
                                type="button"
                                key={option.value}
                                className={selectedDx === option.value ? 'is-active' : ''}
                                onClick={() => {
                                  setSelectedDx(option.value);
                                  setComparePickerOpen(false);
                                }}
                              >
                                <strong>{option.shortLabel}</strong>
                                <span>{option.label}</span>
                                <small>{option.purpose}</small>
                              </button>
                            ))}
                          </div>
                        </section>
                        <section>
                          <h3>Other Vargas</h3>
                          <div className="parashari-compare-picker__options">
                            {COMPARE_CHART_OPTIONS.filter((option) => !FREQUENT_COMPARE_VALUES.has(option.value)).map((option) => (
                              <button
                                type="button"
                                key={option.value}
                                className={selectedDx === option.value ? 'is-active' : ''}
                                onClick={() => {
                                  setSelectedDx(option.value);
                                  setComparePickerOpen(false);
                                }}
                              >
                                <strong>{option.shortLabel}</strong>
                                <span>{option.label}</span>
                                <small>{option.purpose}</small>
                              </button>
                            ))}
                          </div>
                        </section>
                        <section>
                          <h3>Special charts</h3>
                          <div className="parashari-compare-picker__options parashari-compare-picker__options--special">
                            {SPECIAL_CHART_OPTIONS.map((option) => (
                              <button
                                type="button"
                                key={option.value}
                                className={selectedDx === option.value ? 'is-active' : ''}
                                onClick={() => {
                                  setSelectedDx(option.value);
                                  setComparePickerOpen(false);
                                }}
                              >
                                <strong>{option.shortLabel}</strong>
                                <span>{option.label}</span>
                                <small>{option.purpose}</small>
                              </button>
                            ))}
                          </div>
                        </section>
                      </div>
                    ) : null}
                  </div>
                  <div className="parashari-desk-panel__actions">
                    <em className="parashari-desk-panel__hint">Click a house for insight dock</em>
                    <div id="parashari-dx-chart-controls" className="parashari-desk-panel__chart-controls" />
                  </div>
                </header>
                <div className="parashari-desk-chart">
                  <ChartWidget
                    title={selectedDivisionalChart.shortLabel}
                    chartType={dxChartType}
                    chartData={renderedChartData}
                    birthData={birthData}
                    division={typeof selectedDx === 'number' ? selectedDx : undefined}
                    defaultStyle="north"
                    showFooterHint={false}
                    embedInDashboard
                    deskMode
                    inlinePlanetDetails
                    deskControlsHostId="parashari-dx-chart-controls"
                    onHouseSelect={handleHouseSelect}
                    selectedHouseNumber={houseSelection?.houseNumber}
                    calculationProfile={effectiveViewProfile}
                  />
                </div>
              </section>
            ) : null}

            <section className="parashari-desk-panel parashari-desk-panel--transit">
              <header className="parashari-desk-panel__head">
                <div className="parashari-desk-panel__titles">
                  <h2>Transit</h2>
                  <span>As-of sky · {workspaceDateLabel}</span>
                </div>
                <div className="parashari-desk-panel__actions">
                  <em className="parashari-desk-panel__hint">Click a house for insight dock</em>
                  <div id="parashari-transit-chart-controls" className="parashari-desk-panel__chart-controls" />
                </div>
              </header>
              <div className="parashari-desk-chart">
                <ChartWidget
                  title="Transit"
                  chartType="transit"
                  chartData={renderedChartData}
                  birthData={birthData}
                  transitDate={asOfDate}
                  defaultStyle="north"
                  showFooterHint={false}
                  embedInDashboard
                  deskMode
                  inlinePlanetDetails
                  deskControlsHostId="parashari-transit-chart-controls"
                  onHouseSelect={handleHouseSelect}
                  selectedHouseNumber={houseSelection?.houseNumber}
                  activationHouseStates={visibleActivationHouseStates}
                  calculationProfile={effectiveViewProfile}
                />
              </div>
            </section>

            <div
              className="parashari-desk-splitter"
              role="separator"
              aria-label="Resize charts and lower workbench"
              aria-orientation="horizontal"
              aria-valuemin={MIN_CHART_ROW_PERCENT}
              aria-valuemax={MAX_CHART_ROW_PERCENT}
              aria-valuenow={Math.round(chartRowPercent)}
              tabIndex={0}
              onPointerDown={handleWorkspaceResizeStart}
              onPointerMove={handleWorkspaceResizeMove}
              onPointerUp={handleWorkspaceResizeEnd}
              onPointerCancel={handleWorkspaceResizeEnd}
              onLostPointerCapture={handleWorkspaceResizeEnd}
              onKeyDown={handleWorkspaceResizeKey}
              onDoubleClick={() => setChartRowPercent(DEFAULT_CHART_ROW_PERCENT)}
              title="Drag to resize charts and workbench. Double-click to reset."
            >
              <span aria-hidden="true" />
              <em>Drag to resize</em>
            </div>

            <section className="parashari-desk-panel parashari-desk-panel--dasha">
              <DeskDashaPanel
                birthData={birthData}
                chartData={renderedChartData}
                calculationProfile={effectiveViewProfile}
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
                  birthData={birthData}
                  chartData={renderedChartData}
                  calculationProfile={effectiveViewProfile}
                  asOfDate={asOfDate}
                  onJumpToDate={setAsOfDate}
                  layout="focus"
                  onOpenFull={() => navigate(`/charts-dashas/activations?asOf=${formatAsOfIso(asOfDate)}`)}
                />
              </section>
            ) : (
              <>
              {analysisExpanded ? (
                <button
                  type="button"
                  className="parashari-desk-analysis__backdrop"
                  onClick={() => setAnalysisExpanded(false)}
                  aria-label="Close expanded analysis"
                />
              ) : null}
              <section
                className={`parashari-desk-panel parashari-desk-panel--analysis${analysisExpanded ? ' is-expanded' : ''}`}
                aria-label="Analysis dock"
                role={analysisExpanded ? 'dialog' : undefined}
                aria-modal={analysisExpanded ? 'true' : undefined}
              >
                <div className="parashari-desk-analysis__chrome">
                  <DeskStrengthStrip
                    birthData={birthData}
                    chartData={renderedChartData}
                    onOpenTool={setActiveTool}
                  />
                  <header className="parashari-desk-analysis__head">
                    <div className="parashari-desk-analysis__tabs" role="tablist" aria-label="Analysis">
                      {topicId !== 'whole_chart' ? (
                        <button
                          type="button"
                          role="tab"
                          aria-selected={analysisTab === 'judgment'}
                          className={analysisTab === 'judgment' ? 'is-active' : ''}
                          onClick={() => setAnalysisTab('judgment')}
                          title="Topic judgment — natal promise, timing and classical basis"
                        >
                          Judgment
                        </button>
                      ) : null}
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
                      {lifeTabEnabled ? (
                        <button
                          type="button"
                          role="tab"
                          aria-selected={analysisTab === 'life'}
                          className={analysisTab === 'life' ? 'is-active' : ''}
                          onClick={() => setAnalysisTab('life')}
                        >
                          Life
                        </button>
                      ) : null}
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
                    <button
                      type="button"
                      className="parashari-desk-analysis__expand"
                      onClick={() => setAnalysisExpanded((current) => !current)}
                      aria-label={analysisExpanded ? 'Restore compact analysis panel' : 'Expand analysis panel'}
                      title={analysisExpanded ? 'Restore compact panel' : 'Open in a larger view'}
                    >
                      {analysisExpanded ? (
                        <svg viewBox="0 0 24 24" aria-hidden="true">
                          <path d="M9 3v6H3M15 21v-6h6M9 9 3 3M15 15l6 6" />
                        </svg>
                      ) : (
                        <svg viewBox="0 0 24 24" aria-hidden="true">
                          <path d="M8 3H3v5M16 21h5v-5M3 8l6-6M21 16l-6 6" />
                        </svg>
                      )}
                    </button>
                  </header>
                </div>
                <div className="parashari-desk-analysis__body" role="tabpanel">
                  {analysisTab === 'judgment' && topicId !== 'whole_chart' ? (
                    <DeskTopicLens
                      topicId={topicId}
                      birthData={birthData}
                      chartData={renderedChartData}
                      asOfDate={asOfDate}
                      calculationProfile={effectiveViewProfile}
                      onInspectDate={setAsOfDate}
                      compact={!analysisExpanded}
                    />
                  ) : analysisTab === 'house' ? (
                    <>
                      {analysisExpanded ? (
                        <div className="parashari-desk-analysis__house-picker" role="group" aria-label="Select a D1 house">
                          <span className="parashari-desk-analysis__house-picker-label">D1 house</span>
                          <div className="parashari-desk-analysis__house-chips">
                            {Array.from({ length: 12 }, (_, index) => {
                              const houseNumber = index + 1;
                              const selection = buildHouseSelection(renderedChartData, houseNumber, 'lagna');
                              const selected = houseSelection?.chartId === 'lagna' && houseSelection?.houseNumber === houseNumber;
                              return (
                                <button
                                  type="button"
                                  key={houseNumber}
                                  className={selected ? 'is-active' : ''}
                                  aria-pressed={selected}
                                  onClick={() => handleHouseSelect(selection)}
                                  title={`House ${houseNumber} · ${selection.signName} · ${HOUSE_AREAS[index]}`}
                                >
                                  <strong>H{houseNumber}</strong>
                                  <span>{HOUSE_AREAS[index]}</span>
                                </button>
                              );
                            })}
                          </div>
                        </div>
                      ) : null}
                      <DeskHouseInsight
                        birthData={birthData}
                        chartData={renderedChartData}
                        selection={houseSelection}
                        asOfDate={asOfDate}
                        chartId={houseSelection?.chartId || 'lagna'}
                        expanded={analysisExpanded}
                        calculationProfile={effectiveViewProfile}
                      />
                    </>
                  ) : analysisTab === 'positions' ? (
                    <DeskPositionsTable chartData={renderedChartData} birthData={birthData} />
                  ) : analysisTab === 'life' && lifeTabEnabled ? (
                    <ClassicalLifeReading
                      birthData={birthData}
                      chartData={renderedChartData}
                      variant={analysisExpanded ? 'expanded' : 'compact'}
                    />
                  ) : analysisTab === 'yogas' ? (
                    <DeskYogasPanel birthData={birthData} chartData={renderedChartData} calculationProfile={effectiveViewProfile} />
                  ) : analysisTab === 'friends' ? (
                    <DeskFriendshipPanel chartData={renderedChartData} />
                  ) : analysisTab === 'lords' ? (
                    <DeskHouseLordsPanel chartData={renderedChartData} />
                  ) : (
                    <DeskAspectsPanel chartData={renderedChartData} />
                  )}
                </div>
              </section>
              </>
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
        <>
          <ChartOverviewPopup
            isOpen={overviewOpen}
            onClose={() => setOverviewOpen(false)}
            birthData={birthData}
            transitDate={formatAsOfIso(asOfDate)}
            calculationProfile={effectiveViewProfile}
            chartData={renderedChartData}
            onOpenHouse={openHouseFromOverview}
            onOpenYogas={() => {
              setOverviewOpen(false);
              setAnalysisTab('yogas');
            }}
          />
          <HouseInsightPopup
            isOpen={houseSheetOpen && !!houseSelection?.houseNumber}
            onClose={() => setHouseSheetOpen(false)}
            houseNumber={houseSelection?.houseNumber}
            signName={houseSelection?.signName}
            rashiIndex={houseSelection?.rashiIndex}
            chartData={renderedChartData}
            birthData={birthData}
            chartId="lagna"
            transitDate={formatAsOfIso(asOfDate)}
            calculationProfile={effectiveViewProfile}
            planetsInHouse={occupantsForHouse(renderedChartData, houseSelection?.houseNumber)}
          />
        </>
      ) : null}

      {hasChart ? (
        <DeskToolModals
          birthData={birthData}
          chartData={renderedChartData}
          activeTool={activeTool}
          onClose={() => setActiveTool(null)}
        />
      ) : null}

      {user && hasChart ? (
        <DeskDrawingBoard
          active={drawingActive}
          onActiveChange={setDrawingActive}
          drawingKey={drawingKey}
          showLauncher={isMobileDesk}
        />
      ) : null}
    </div>
  );
};

export default ChartsDashasWorkspacePage;
