import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  View,
  Text,
  TextInput,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  StatusBar,
  Alert,
  Modal,
  ActivityIndicator,
  AppState,
  Platform,
  Linking,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useFocusEffect } from '@react-navigation/native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LANGUAGES } from '../../utils/constants';
import { useTheme } from '../../context/ThemeContext';
import { useCredits } from '../../credits/CreditContext';
import { storage } from '../../services/storage';
import { reportAPI } from '../../services/api';
import { downloadPdfToLocalUri, sharePDFOnWhatsApp } from '../../utils/pdfGenerator';
import { useAnalytics } from '../../hooks/useAnalytics';
import { useTranslation } from 'react-i18next';
import ConfirmCreditsModal from '../ConfirmCreditsModal';
import NotificationEnableBanner from '../Notifications/NotificationEnableBanner';
import { useAuthGate } from '../../auth/AuthGateContext';
import { goBackOrHome } from '../../navigation/navHelpers';

const REPORT_TYPE_FALLBACKS = [
  {
    key: 'partnership',
    title: 'Partnership Report',
    subtitle: 'Best for marriage, business, parent-child, or any two-person relationship study',
    description: 'A premium 20-page PDF with chart overlays, timing, strengths, friction points, remedies, and next steps.',
    icon: '💞',
    gradient: ['#fb7185', '#f97316'],
    enabled: true,
  },
  {
    key: 'career',
    title: 'Career Report',
    subtitle: 'Coming soon',
    description: 'A future report for work style, timing, and career direction.',
    icon: '💼',
    gradient: ['#6366F1', '#8B5CF6'],
    enabled: false,
  },
  {
    key: 'wealth',
    title: 'Wealth Report',
    subtitle: 'Best for income, savings, assets, and the next 12 months of money timing',
    description: 'A premium 27-page PDF with D1/D2/D10 layers, yogas, spouse money themes, and dasha-based monthly wealth timing.',
    icon: '💰',
    gradient: ['#0EA5E9', '#38BDF8'],
    enabled: true,
  },
  {
    key: 'health',
    title: 'Health Report',
    subtitle: 'Best for constitution, care points, and the next 12 months of wellness timing',
    description: 'A premium 27-page PDF with D1/D9/D30 layers, vitality themes, lifestyle triggers, and dasha-based monthly health timing.',
    icon: '🏥',
    gradient: ['#22c55e', '#15803d'],
    enabled: true,
  },
  {
    key: 'janam_kundli',
    title: 'Janam Kundli Report',
    subtitle: 'Full birth chart PDF — charts, dashas, yogas, life guidance',
    description: 'A 24-page personalized Janam Kundli with D1/Moon/D9/D10 charts, Ashtakavarga, Vimshottari dashas, yogas, and age-aware guidance (English/Hindi).',
    icon: '🕉️',
    gradient: ['#ea580c', '#f97316'],
    enabled: true,
  },
  {
    key: 'progeny',
    title: 'Progeny Report',
    subtitle: 'Coming soon',
    description: 'A future report for family timing, children, and parenting themes.',
    icon: '👶',
    gradient: ['#ec4899', '#a855f7'],
    enabled: false,
  },
];

const buildReportPdfFileName = (reportId) => `report-${String(reportId || 'latest').replace(/[^a-zA-Z0-9_-]+/g, '_')}`;

const EMPTY_REPORT_BRANDING = {
  business_name: '',
  tagline: '',
  phone: '',
  email: '',
  website: '',
  address: '',
  show_powered_by: true,
};

const HISTORY_STATUS_META = {
  completed: { icon: 'checkmark-circle', tint: '#22c55e' },
  processing: { icon: 'hourglass-outline', tint: '#f59e0b' },
  pending: { icon: 'time-outline', tint: '#f59e0b' },
  failed: { icon: 'close-circle', tint: '#f43f5e' },
};

const normalizeHistoryStatus = (value) => String(value || '').trim().toLowerCase();

const formatHistoryDate = (value, locale = 'en-IN') => {
  if (!value) return '';
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return String(value);
  return new Intl.DateTimeFormat(locale, { dateStyle: 'medium', timeStyle: 'short' }).format(parsed);
};

const normalizeLanguageCode = (value) => {
  const normalized = String(value || '').trim().toLowerCase();
  if (!normalized) return 'english';
  const exact = LANGUAGES.find((item) => item.code === normalized);
  if (exact) return exact.code;
  if (normalized.startsWith('en')) return 'english';
  if (normalized.startsWith('hi')) return 'hindi';
  if (normalized.startsWith('ta')) return 'tamil';
  if (normalized.startsWith('te')) return 'telugu';
  if (normalized.startsWith('gu')) return 'gujarati';
  if (normalized.startsWith('mr')) return 'marathi';
  if (normalized.startsWith('de')) return 'german';
  if (normalized.startsWith('fr')) return 'french';
  if (normalized.startsWith('ru')) return 'russian';
  if (normalized.startsWith('zh') || normalized.startsWith('cn')) return 'chinese';
  return 'english';
};

const formatBirthLine = (chart) => {
  if (!chart) return '';
  const parts = [chart.date, chart.time, chart.place].filter(Boolean);
  return parts.join(' • ');
};

const formatCost = (cost, originalCost) => {
  if (cost == null) return '--';
  if (originalCost != null && originalCost > cost) {
    return `${originalCost} → ${cost}`;
  }
  return `${cost}`;
};

const formatCreditsLabel = (cost, originalCost, creditsWord = 'credits') => {
  const value = formatCost(cost, originalCost);
  if (value === '--') return value;
  return `${value} ${creditsWord}`;
};

const REPORT_SESSION_KEY = 'reportsStudioActiveSession';

const chartIdentityKey = (person) => {
  if (!person || typeof person !== 'object') return '';
  return [
    person.id ?? person.chart_id ?? '',
    person.date ?? '',
    person.time ?? '',
    person.latitude ?? '',
    person.longitude ?? '',
    person.name ?? '',
  ]
    .map((value) => String(value).trim().toLowerCase())
    .join('|');
};

const isSameReportPair = (personA, personB, otherA, otherB) => {
  if (!personA || !personB || !otherA || !otherB) return false;
  return (
    chartIdentityKey(personA) === chartIdentityKey(otherA)
    && chartIdentityKey(personB) === chartIdentityKey(otherB)
  );
};

const isSingleChartReport = (reportType) => (
  reportType === 'wealth' || reportType === 'health' || reportType === 'janam_kundli'
);

const isSameReportSelection = (reportType, personA, personB, otherA, otherB) => {
  if (!personA || !otherA) return false;
  if (chartIdentityKey(personA) !== chartIdentityKey(otherA)) return false;
  if (isSingleChartReport(reportType)) return true;
  return isSameReportPair(personA, personB, otherA, otherB);
};

const NativePreviewCard = ({
  title,
  subtitle,
  chart,
  onPress,
  isEmpty,
  theme,
  colors,
  icon,
  accent,
  slotLabel = '',
  emptyHint = 'Tap to choose',
}) => (
  <TouchableOpacity
    activeOpacity={0.9}
    onPress={onPress}
    style={[
      styles.nativeCard,
      {
        backgroundColor: theme === 'dark' ? 'rgba(255,255,255,0.06)' : colors.surface,
        borderColor: isEmpty
          ? (theme === 'dark' ? 'rgba(251,113,133,0.35)' : 'rgba(249,115,22,0.28)')
          : (theme === 'dark' ? 'rgba(255,255,255,0.12)' : colors.cardBorder),
        borderStyle: isEmpty ? 'dashed' : 'solid',
      },
    ]}
  >
    <View style={[styles.nativeCardIcon, { backgroundColor: `${accent}18` }]}>
      <Text style={styles.nativeCardEmoji}>{icon}</Text>
    </View>
    <View style={styles.nativeCardBody}>
      <Text style={[styles.nativeCardTitle, { color: colors.text }]} numberOfLines={1}>
        {isEmpty ? title : (chart?.name || title)}
      </Text>
      <Text style={[styles.nativeCardSubtitle, { color: colors.textSecondary }]} numberOfLines={2}>
        {isEmpty ? subtitle : (formatBirthLine(chart) || subtitle)}
      </Text>
      <Text style={[styles.nativeCardMeta, { color: isEmpty ? accent : (colors.textTertiary || colors.textSecondary) }]}>
        {isEmpty ? emptyHint : slotLabel}
      </Text>
    </View>
    <Ionicons name={isEmpty ? 'add-circle-outline' : 'checkmark-circle'} size={22} color={isEmpty ? accent : '#22c55e'} />
  </TouchableOpacity>
);

export default function ReportsStudioScreen({ navigation, route }) {
  const { t, i18n } = useTranslation();
  useAnalytics('ReportsStudioScreen');
  const { theme, colors } = useTheme();
  const isDark = theme === 'dark';
  const { pricing, pricingOriginal, credits, fetchBalance } = useCredits();
  const { requireAuthForPaid } = useAuthGate();

  const [birthData, setBirthData] = useState(null);
  const [selectedReportType, setSelectedReportType] = useState('partnership');
  const [selectedPersonA, setSelectedPersonA] = useState(null);
  const [selectedPersonB, setSelectedPersonB] = useState(null);
  const [reportLanguage, setReportLanguage] = useState(normalizeLanguageCode(i18n.language));
  const [showLanguageModal, setShowLanguageModal] = useState(false);
  const [activeStep, setActiveStep] = useState(1);
  const [reportTypes, setReportTypes] = useState(REPORT_TYPE_FALLBACKS);
  const [loadingTypes, setLoadingTypes] = useState(false);
  const [loadingReport, setLoadingReport] = useState(false);
  const [processingStatus, setProcessingStatus] = useState('idle');
  const [reportJobId, setReportJobId] = useState(null);
  const [reportDocument, setReportDocument] = useState(null);
  const [reportError, setReportError] = useState('');
  const [generatedPdfUri, setGeneratedPdfUri] = useState('');
  const [pdfGenerationState, setPdfGenerationState] = useState('idle');
  const [reportSession, setReportSession] = useState(null);
  const [showCreditsModal, setShowCreditsModal] = useState(false);
  const [pendingForceRegenerate, setPendingForceRegenerate] = useState(false);
  const [checkingExistingReport, setCheckingExistingReport] = useState(false);
  const [pastReports, setPastReports] = useState([]);
  const [loadingPastReports, setLoadingPastReports] = useState(true);
  const [openingPastReportId, setOpeningPastReportId] = useState(null);
  const [reportBranding, setReportBranding] = useState(EMPTY_REPORT_BRANDING);
  const [brandingLoaded, setBrandingLoaded] = useState(false);
  const pollTimerRef = useRef(null);
  const reportSessionRef = useRef(null);
  const mountedRef = useRef(true);
  const existingLookupKeyRef = useRef('');

  const reportTypeMap = useMemo(() => {
    const map = new Map();
    [...REPORT_TYPE_FALLBACKS, ...reportTypes].forEach((item) => {
      if (!item?.key) return;
      map.set(item.key, { ...map.get(item.key), ...item });
    });
    return map;
  }, [reportTypes]);

  const displayReportTypes = useMemo(() => {
    const fallbackByKey = new Map(REPORT_TYPE_FALLBACKS.map((item) => [item.key, item]));
    const orderedKeys = [
      ...REPORT_TYPE_FALLBACKS.map((item) => item.key),
      ...reportTypes.map((item) => item?.key).filter(Boolean),
    ];
    const seen = new Set();
    return orderedKeys.reduce((list, key) => {
      if (!key || seen.has(key)) return list;
      seen.add(key);
      const fallback = fallbackByKey.get(key) || {};
      const merged = reportTypeMap.get(key) || fallback;
      const englishTitle = merged.title || fallback.title || key;
      const englishSubtitle = merged.subtitle || fallback.subtitle || '';
      const englishDescription = merged.description || merged.summary || fallback.description || '';
      const englishShort = String(englishTitle).replace(/\s+Report$/i, '');
      list.push({
        ...fallback,
        ...merged,
        key,
        icon: merged.icon || fallback.icon || '📄',
        gradient: merged.gradient || fallback.gradient || ['#fb7185', '#f97316'],
        // Prefer locale strings over API/fallback English copy.
        title: t(`reports.types.${key}.title`, englishTitle),
        shortTitle: t(`reports.types.${key}.shortTitle`, englishShort),
        subtitle: t(`reports.types.${key}.subtitle`, englishSubtitle),
        description: t(`reports.types.${key}.description`, englishDescription),
        enabled: merged.enabled !== undefined ? merged.enabled : fallback.enabled !== false,
      });
      return list;
    }, []);
  }, [reportTypeMap, reportTypes, t, i18n.language]);

  const reportCost = useMemo(() => {
    const key = `${selectedReportType}_report`;
    const fallbackKey = selectedReportType === 'health' ? 'health_report_cost' : null;
    return Number(
      pricing?.[key]
      ?? (fallbackKey ? pricing?.[fallbackKey] : null)
      ?? pricing?.partnership_report
      ?? pricing?.partnership
      ?? 9
    ) || 0;
  }, [pricing, selectedReportType]);

  const reportOriginalCost = useMemo(() => {
    const key = `${selectedReportType}_report`;
    const fallbackKey = selectedReportType === 'health' ? 'health_report_cost' : null;
    return pricingOriginal?.[key] ?? (fallbackKey ? pricingOriginal?.[fallbackKey] : null) ?? null;
  }, [pricingOriginal, selectedReportType]);

  const selectedTypeMeta = reportTypeMap.get(selectedReportType) || REPORT_TYPE_FALLBACKS[0];
  const selectedTypeDisplay = displayReportTypes.find((item) => item.key === selectedReportType) || selectedTypeMeta;
  const selectedTypeEnabled = selectedTypeMeta?.enabled !== false;
  const creditsWord = t('reports.creditsWord', 'credits');
  const step1Ready = !!selectedReportType && selectedTypeEnabled;
  const step2Ready = selectedReportType === 'partnership'
    ? (!!selectedPersonA && !!selectedPersonB)
    : isSingleChartReport(selectedReportType)
      ? !!selectedPersonA
      : false;
  const readyToGenerate = (
    (selectedReportType === 'partnership' && !!selectedPersonA && !!selectedPersonB)
    || (isSingleChartReport(selectedReportType) && !!selectedPersonA)
  ) && !loadingReport;

  const genericReportError = t('reports.genericError', 'Something went wrong while preparing your report. Please try again in a moment.');
  const genericPdfError = t('reports.genericPdfError', 'The report is ready, but we could not open the PDF right now. Please try again in a moment.');

  const clearPollTimer = () => {
    if (pollTimerRef.current) {
      clearTimeout(pollTimerRef.current);
      pollTimerRef.current = null;
    }
  };

  const persistReportSession = useCallback(async (nextSession) => {
    if (!mountedRef.current) return;
    reportSessionRef.current = nextSession;
    setReportSession(nextSession);
    if (nextSession) {
      await storage.setItem(REPORT_SESSION_KEY, JSON.stringify(nextSession));
    } else {
      await storage.removeItem(REPORT_SESSION_KEY);
    }
  }, []);

  const loadStoredReportSession = useCallback(async () => {
    try {
      const raw = await storage.getItem(REPORT_SESSION_KEY);
      if (!raw) return null;
      const parsed = JSON.parse(raw);
      if (!parsed || !parsed.reportId) return null;
      return parsed;
    } catch (error) {
      return null;
    }
  }, []);

  const isActiveReportStatus = (status) => {
    const normalized = String(status || '').toLowerCase();
    return normalized === 'pending' || normalized === 'processing' || !normalized;
  };

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
      clearPollTimer();
    };
  }, []);

  useEffect(() => {
    const loadBirthData = async () => {
      try {
        const data = await storage.getBirthDetails();
        if (mountedRef.current) {
          setBirthData(data || null);
          if (!selectedPersonA && data) {
            setSelectedPersonA(data);
          }
        }
      } catch (error) {
        console.error('Failed to load birth data for reports:', error);
      }
    };
    loadBirthData();
    fetchReportTypes();
    return () => clearPollTimer();
    // Intentionally run once on mount; navigation params handle returning from selector.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const params = route?.params || {};
    if (params.selectorTarget && params.birthData) {
      if (params.selectorTarget === 'personA') {
        setSelectedPersonA(params.birthData);
      } else if (params.selectorTarget === 'personB') {
        setSelectedPersonB(params.birthData);
      }
      navigation.setParams({
        ...params,
        selectorTarget: undefined,
        birthData: undefined,
        birthDetails: undefined,
        birthChartId: undefined,
      });
    }
  }, [route?.params, navigation]);

  useEffect(() => {
    const lang = normalizeLanguageCode(i18n.language);
    setReportLanguage((current) => current || lang);
  }, [i18n.language]);

  useEffect(() => {
    let cancelled = false;
    const loadBranding = async () => {
      try {
        const response = await reportAPI.getReportBranding();
        // Axios: response.data === { success, branding }
        const branding = response?.data?.branding || response?.data?.data?.branding;
        if (!cancelled && branding && typeof branding === 'object') {
          setReportBranding({ ...EMPTY_REPORT_BRANDING, ...branding });
        }
      } catch (error) {
        // Unauthenticated or first-time users simply start with empty branding.
        console.warn('Report branding load skipped:', error?.message || error);
      } finally {
        if (!cancelled) setBrandingLoaded(true);
      }
    };
    loadBranding();
    return () => { cancelled = true; };
  }, []);

  const updateBrandingField = useCallback((key, value) => {
    setReportBranding((prev) => ({ ...prev, [key]: value }));
  }, []);

  const fetchReportTypes = async () => {
    try {
      setLoadingTypes(true);
      const response = await reportAPI.listTypes();
      const remoteTypes = response?.data?.data || response?.data || [];
      if (Array.isArray(remoteTypes) && remoteTypes.length > 0) {
        setReportTypes(remoteTypes);
      }
    } catch (error) {
      console.error('Failed to load report types:', error);
    } finally {
      setLoadingTypes(false);
    }
  };

  const openNativeSelector = (selectorTarget) => {
    navigation.navigate('SelectNative', {
      returnTo: 'ReportsStudio',
      selectorTarget,
      returnParams: {
        reportType: selectedReportType,
        reportLanguage,
        fromReportsStudio: true,
      },
    });
  };

  const swapCharts = () => {
    if (!selectedPersonA || !selectedPersonB) return;
    setSelectedPersonA(selectedPersonB);
    setSelectedPersonB(selectedPersonA);
  };

  const goToNextStep = () => {
    setActiveStep((current) => Math.min(3, current + 1));
  };

  const goToPreviousStep = () => {
    setActiveStep((current) => Math.max(1, current - 1));
  };

  const normalizeReportPayload = (payload) => {
    const report = payload || {};
    const scoreSummary = report.score_summary || {};
    const percent = Number(scoreSummary.percentage ?? scoreSummary.score ?? scoreSummary.overall ?? 0) || 0;
    return {
      overall_score: {
        percentage: percent,
      },
      recommendation: {
        recommendation: report?.premium_report?.compatibility_verdict
          || report?.premium_report?.headline
          || 'Relationship report generated.',
      },
      guna_milan: scoreSummary.guna_milan || scoreSummary.ashtakoota || report.guna_milan || {},
      manglik_analysis: report.premium_report?.manglik_analysis || report.manglik_analysis || {},
      timing_overlay: report.premium_report?.timing_overlay || report.timing_overlay || scoreSummary.timing_overlay || {},
    };
  };

  const resolveReportPdfUrl = async (reportId, fallbackUrl = null) => {
    if (fallbackUrl) return fallbackUrl;
    const response = await reportAPI.getReportPdfUrl(reportId);
    return response?.data?.pdf_url || '';
  };

  const ensureLocalPdf = async (reportId, pdfUrl) => {
    const localUri = await downloadPdfToLocalUri(pdfUrl, buildReportPdfFileName(reportId));
    if (mountedRef.current) {
      setGeneratedPdfUri(localUri);
      setPdfGenerationState('ready');
    }
    return localUri;
  };

  const openGeneratedReport = async () => {
    try {
      const reportId = reportJobId || reportDocument?.report_id;
      const pdfUrl = reportDocument?.pdf_url || (reportId ? await resolveReportPdfUrl(reportId) : '');

      if (pdfGenerationState === 'building' && !generatedPdfUri && !pdfUrl) {
        Alert.alert(
          t('reports.pdfBuildingTitle', 'PDF is still loading'),
          t('reports.pdfBuildingBody', 'The report is ready, but the PDF is still being prepared. Please try again in a moment.')
        );
        return;
      }

      let pdfUri = generatedPdfUri || '';
      if (!pdfUri && pdfUrl) {
        try {
          pdfUri = reportId ? await ensureLocalPdf(reportId, pdfUrl) : await downloadPdfToLocalUri(pdfUrl, 'report');
        } catch (downloadError) {
          // Native needs a local file; on web the signed URL is enough to open.
          if (Platform.OS !== 'web') throw downloadError;
          console.warn('Open report: local PDF prepare failed, using remote URL', downloadError?.message);
          pdfUri = pdfUrl;
        }
      }
      if (!pdfUri && !pdfUrl) {
        throw new Error(t('reports.pdfOpenUnavailable', 'We could not open the PDF right now.'));
      }

      navigation.navigate('ReportViewer', {
        pdfUri: pdfUri || pdfUrl,
        pdfUrl: pdfUrl || pdfUri,
        title: reportDocument?.premium_report?.headline || t('reports.viewerTitle', 'Your report'),
        subtitle: currentLanguageLabel,
      });
    } catch (error) {
      console.error('Open report PDF failed:', error);
      if (Platform.OS === 'web') {
        const reportId = reportJobId || reportDocument?.report_id;
        const fallbackUrl = reportDocument?.pdf_url || (reportId ? await resolveReportPdfUrl(reportId).catch(() => '') : '');
        if (fallbackUrl) {
          try {
            await Linking.openURL(fallbackUrl);
            return;
          } catch (_) {
            /* fall through to alert */
          }
        }
      }
      Alert.alert(
        t('reports.pdfErrorTitle', 'PDF error'),
        genericPdfError
      );
    }
  };

  const loadPastReports = useCallback(async () => {
    try {
      const token = await storage.getAuthToken();
      if (!token) {
        if (mountedRef.current) {
          setPastReports([]);
          setLoadingPastReports(false);
        }
        return;
      }
      const res = await reportAPI.getHistory({ limit: 20, offset: 0 });
      const items = res?.data?.data || [];
      if (mountedRef.current) {
        setPastReports(Array.isArray(items) ? items : []);
      }
    } catch (error) {
      if (error?.response?.status !== 404) {
        console.error('[ReportsStudio] past reports load failed', error);
      }
      if (mountedRef.current) setPastReports([]);
    } finally {
      if (mountedRef.current) setLoadingPastReports(false);
    }
  }, []);

  const hydrateCompletedReport = async (reportId, { silent = false } = {}) => {
    if (!reportId) return false;
    try {
      const response = await reportAPI.getPartnershipReportStatus(reportId);
      const statusPayload = response?.data || {};
      const status = String(statusPayload.status || '').toLowerCase();
      if (status !== 'completed') {
        return false;
      }
      const data = statusPayload.data || {};
      if (mountedRef.current) {
        setReportDocument(data);
        setReportJobId(reportId);
        setReportError('');
      }
      const pdfUrl = data.pdf_url || await resolveReportPdfUrl(reportId);
      if (!pdfUrl) {
        if (mountedRef.current) setPdfGenerationState('failed');
        return false;
      }
      if (mountedRef.current) setPdfGenerationState('building');
      await ensureLocalPdf(reportId, pdfUrl);
      return true;
    } catch (error) {
      console.error('Failed to hydrate completed report:', error);
      if (!silent && mountedRef.current) {
        setPdfGenerationState('failed');
        Alert.alert(t('reports.pdfErrorTitle', 'PDF error'), genericPdfError);
      }
      return false;
    }
  };

  const pollReportStatus = async (reportId, options = {}) => {
    clearPollTimer();
    const reportType = options.reportType || selectedReportType;
    try {
      const statusResponse = reportType === 'health'
        ? await reportAPI.getHealthReportStatus(reportId)
        : reportType === 'janam_kundli'
          ? await reportAPI.getJanamKundliReportStatus(reportId)
          : reportType === 'wealth'
            ? await reportAPI.getWealthReportStatus(reportId)
            : await reportAPI.getPartnershipReportStatus(reportId);
      const statusPayload = statusResponse?.data || {};
      const status = String(statusPayload.status || '').toLowerCase();
      setProcessingStatus(status || 'pending');

      await persistReportSession({
        ...(reportSessionRef.current || {}),
        reportId,
        reportType,
        language: reportLanguage,
        status: status || 'pending',
        selectedPersonA,
        selectedPersonB: reportType === 'partnership' ? selectedPersonB : null,
        updatedAt: Date.now(),
      });

      if (status === 'completed') {
        const data = statusPayload.data || {};
        setReportDocument(data);
        setLoadingReport(false);
        setReportError('');
        setPdfGenerationState('building');
        // Refresh balance after job completion (fresh generate deducts; cache reopen is a no-op).
        fetchBalance?.().catch(() => {});
        loadPastReports();
        try {
          const pdfUrl = data.pdf_url || await resolveReportPdfUrl(reportId, data.pdf_url || '');
          if (!pdfUrl) {
            throw new Error('PDF URL not available yet');
          }
          await ensureLocalPdf(reportId, pdfUrl);
        } catch (error) {
          console.error('PDF download failed:', error);
          if (mountedRef.current) {
            setPdfGenerationState('failed');
            setReportError(genericPdfError);
          }
          Alert.alert(
            t('reports.pdfErrorTitle', 'PDF error'),
            genericPdfError
          );
        }
        await persistReportSession({
          ...(reportSessionRef.current || {}),
          reportId,
          reportType,
          language: reportLanguage,
          status: 'completed',
          selectedPersonA,
          selectedPersonB: reportType === 'partnership' ? selectedPersonB : null,
          updatedAt: Date.now(),
        });
        return;
      }

      if (status === 'failed') {
        console.error('Report generation failed:', statusPayload.error || statusPayload);
        setReportError(genericReportError);
        setLoadingReport(false);
        await persistReportSession({
          ...(reportSessionRef.current || {}),
          reportId,
          reportType,
          language: reportLanguage,
          status: 'failed',
          selectedPersonA,
          selectedPersonB: reportType === 'partnership' ? selectedPersonB : null,
          errorMessage: genericReportError,
          updatedAt: Date.now(),
        });
        return;
      }

      if (!options.fromRestore) {
        setActiveStep(3);
      }
      pollTimerRef.current = setTimeout(() => {
        if (mountedRef.current) {
          pollReportStatus(reportId, options);
        }
      }, 3500);
    } catch (error) {
      console.error('Report status polling failed:', error);
      setReportError(genericReportError);
      setLoadingReport(false);
      if (error?.response?.status === 404) {
        await persistReportSession(null);
      }
    }
  };

  const restoreReportSession = useCallback(async ({ forceResume = false } = {}) => {
    if (!mountedRef.current) return;

    const session = await loadStoredReportSession();
    if (!session?.reportId) return;

    reportSessionRef.current = session;
    setReportSession(session);
    setReportJobId(session.reportId);

    const status = String(session.status || '').toLowerCase();
    const shouldResumeWizard = forceResume || isActiveReportStatus(status);

    if (!shouldResumeWizard) {
      // Completed / failed: keep the wizard where it is; the top banner opens the PDF.
      setLoadingReport(false);
      return;
    }

    if (session.reportType) {
      setSelectedReportType(session.reportType);
    }
    if (session.language) {
      setReportLanguage(normalizeLanguageCode(session.language));
    }
    if (session.selectedPersonA) {
      setSelectedPersonA(session.selectedPersonA);
    }
    if (session.selectedPersonB) {
      setSelectedPersonB(session.selectedPersonB);
    }
    setActiveStep(3);
    setReportError('');
    setLoadingReport(true);
    setProcessingStatus(status === 'completed' ? 'processing' : (status || 'pending'));
    await pollReportStatus(session.reportId, { fromRestore: true, reportType: session.reportType });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loadStoredReportSession]);

  useFocusEffect(
    useCallback(() => {
      restoreReportSession();
      setLoadingPastReports(true);
      loadPastReports();
    }, [restoreReportSession, loadPastReports])
  );

  useEffect(() => {
    const subscription = AppState.addEventListener('change', (nextState) => {
      if (nextState === 'active') {
        restoreReportSession();
      }
    });
    return () => subscription.remove();
  }, [restoreReportSession]);

  // Server is source of truth for "already generated" — local session alone is not enough.
  useEffect(() => {
    let cancelled = false;
    const isPartnership = selectedReportType === 'partnership';
    const isSoloChart = isSingleChartReport(selectedReportType);
    if (
      (!isPartnership && !isSoloChart)
      || !selectedPersonA
      || (isPartnership && !selectedPersonB)
      || !reportLanguage
    ) {
      setCheckingExistingReport(false);
      return undefined;
    }
    if (loadingReport) {
      return undefined;
    }

    const lookupKey = [
      chartIdentityKey(selectedPersonA),
      isPartnership ? chartIdentityKey(selectedPersonB) : 'solo',
      String(reportLanguage || '').toLowerCase(),
      selectedReportType,
    ].join('::');

    const timer = setTimeout(async () => {
      const currentSession = reportSessionRef.current;
      const currentStatus = String(currentSession?.status || '').toLowerCase();
      const sameRunning = isActiveReportStatus(currentStatus)
        && String(currentSession?.reportType || '') === selectedReportType
        && isSameReportSelection(
          selectedReportType,
          selectedPersonA,
          selectedPersonB,
          currentSession?.selectedPersonA,
          currentSession?.selectedPersonB
        )
        && String(currentSession?.language || '').toLowerCase() === String(reportLanguage || '').toLowerCase();
      if (sameRunning) {
        return;
      }

      existingLookupKeyRef.current = lookupKey;
      if (mountedRef.current) setCheckingExistingReport(true);
      try {
        const response = selectedReportType === 'health'
          ? await reportAPI.lookupExistingHealthReport(selectedPersonA, reportLanguage, { chartStyle: 'both' })
          : selectedReportType === 'janam_kundli'
            ? await reportAPI.lookupExistingJanamKundliReport(selectedPersonA, reportLanguage, { chartStyle: 'both' })
            : selectedReportType === 'wealth'
              ? await reportAPI.lookupExistingWealthReport(selectedPersonA, reportLanguage, { chartStyle: 'both' })
              : await reportAPI.lookupExistingPartnershipReport(
                selectedPersonA,
                selectedPersonB,
                reportLanguage,
                { chartStyle: 'both' }
              );
        if (cancelled || !mountedRef.current || existingLookupKeyRef.current !== lookupKey) {
          return;
        }
        const data = response?.data || {};
        if (data.exists && data.report_id) {
          const status = String(data.status || '').toLowerCase();
          const inProgress = Boolean(data.in_progress) || status === 'pending' || status === 'processing';
          const previousId = reportSessionRef.current?.reportId;
          if (previousId && previousId !== data.report_id) {
            setGeneratedPdfUri('');
            setReportDocument(null);
            setPdfGenerationState('idle');
          }
          setReportJobId(data.report_id);
          if (inProgress) {
            await persistReportSession({
              reportId: data.report_id,
              reportType: selectedReportType,
              language: reportLanguage,
              status: status === 'processing' ? 'processing' : 'pending',
              selectedPersonA,
              selectedPersonB: isPartnership ? selectedPersonB : null,
              createdAt: currentSession?.createdAt || Date.now(),
              updatedAt: Date.now(),
              fromServerCache: false,
            });
            setActiveStep(3);
            setReportError('');
            setLoadingReport(true);
            setProcessingStatus(status === 'processing' ? 'processing' : 'pending');
            pollReportStatus(data.report_id, { fromRestore: true, reportType: selectedReportType });
          } else {
            await persistReportSession({
              reportId: data.report_id,
              reportType: selectedReportType,
              language: reportLanguage,
              status: 'completed',
              selectedPersonA,
              selectedPersonB: isPartnership ? selectedPersonB : null,
              createdAt: currentSession?.createdAt || Date.now(),
              updatedAt: Date.now(),
              fromServerCache: true,
            });
          }
        } else if (
          currentSession?.reportId
          && String(currentSession.status || '').toLowerCase() === 'completed'
          && String(currentSession.reportType || '') === selectedReportType
          && isSameReportSelection(
            selectedReportType,
            selectedPersonA,
            selectedPersonB,
            currentSession.selectedPersonA,
            currentSession.selectedPersonB
          )
          && String(currentSession.language || '').toLowerCase() === String(reportLanguage || '').toLowerCase()
        ) {
          await persistReportSession(null);
          setReportJobId(null);
          setReportDocument(null);
          setGeneratedPdfUri('');
          setPdfGenerationState('idle');
        }
      } catch (error) {
        console.warn('Existing report lookup failed:', error);
      } finally {
        if (!cancelled && mountedRef.current && existingLookupKeyRef.current === lookupKey) {
          setCheckingExistingReport(false);
        }
      }
    }, 250);

    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [
    selectedPersonA,
    selectedPersonB,
    reportLanguage,
    selectedReportType,
    loadingReport,
    persistReportSession,
  ]);

  const startReportGeneration = async ({ forceRegenerate = false } = {}) => {
    if (
      !selectedTypeMeta?.enabled
      && selectedReportType !== 'partnership'
      && selectedReportType !== 'wealth'
      && selectedReportType !== 'health'
      && selectedReportType !== 'janam_kundli'
    ) {
      Alert.alert(
        t('reports.comingSoonTitle', 'Coming soon'),
        t('reports.comingSoonBody', 'This report type is not available yet. We are building it next.')
      );
      return;
    }

    if (
      selectedReportType !== 'partnership'
      && selectedReportType !== 'wealth'
      && selectedReportType !== 'health'
      && selectedReportType !== 'janam_kundli'
    ) {
      Alert.alert(
        t('reports.unavailableTitle', 'Not ready yet'),
        t('reports.unavailableBody', 'Only partnership, wealth, health, and Janam Kundli reports are available in this release.')
      );
      return;
    }

    if (selectedReportType === 'partnership' && (!selectedPersonA || !selectedPersonB)) {
      Alert.alert(
        t('reports.missingPairTitle', 'Choose both people'),
        t('reports.missingPairBody', 'Please select both chart slots before generating your report.')
      );
      return;
    }

    if (isSingleChartReport(selectedReportType) && !selectedPersonA) {
      Alert.alert(
        t('reports.missingChartTitle', 'Choose a chart'),
        selectedReportType === 'health'
          ? t('reports.missingChartBodyHealth', 'Please select a birth chart before generating your health report.')
          : selectedReportType === 'janam_kundli'
            ? t('reports.missingChartBodyJanam', 'Please select a birth chart before generating your Janam Kundli.')
            : t('reports.missingChartBody', 'Please select a birth chart before generating your wealth report.')
      );
      return;
    }

    if (credits < reportCost) {
      Alert.alert(
        t('credits.insufficient', 'Insufficient Credits'),
        t('reports.insufficientCreditsBody', {
          defaultValue: `You need ${reportCost} credits for this report. You have ${credits} credits.`,
          count: reportCost,
          balance: credits,
        }),
        [
          { text: t('common.cancel', 'Cancel'), style: 'cancel' },
          { text: t('credits.buyCredits', 'Buy Credits'), onPress: () => navigation.navigate('Credits') },
        ]
      );
      return;
    }

    try {
      setLoadingReport(true);
      setReportError('');
      setReportDocument(null);
      setGeneratedPdfUri('');
      setProcessingStatus('pending');
      const response = selectedReportType === 'health'
        ? await reportAPI.startHealthReport(selectedPersonA, reportLanguage, {
          includeImages: true,
          forceRegenerate,
          chartStyle: 'both',
        })
        : selectedReportType === 'janam_kundli'
          ? await reportAPI.startJanamKundliReport(selectedPersonA, reportLanguage, {
            includeImages: true,
            forceRegenerate,
            chartStyle: 'both',
            branding: reportBranding,
          })
          : selectedReportType === 'wealth'
            ? await reportAPI.startWealthReport(selectedPersonA, reportLanguage, {
              includeImages: true,
              forceRegenerate,
              chartStyle: 'both',
            })
            : await reportAPI.startPartnershipReport(
              selectedPersonA,
              selectedPersonB,
              reportLanguage,
              { includeImages: true, forceRegenerate, chartStyle: 'both' }
            );
      const reportId = response?.data?.report_id;
      if (!reportId) {
        throw new Error(t('reports.startFailed', 'Could not start the report.'));
      }
      setReportJobId(reportId);
      await persistReportSession({
        reportId,
        reportType: selectedReportType,
        language: reportLanguage,
        status: 'pending',
        selectedPersonA,
        selectedPersonB: selectedReportType === 'partnership' ? selectedPersonB : null,
        createdAt: Date.now(),
        updatedAt: Date.now(),
      });
      setActiveStep(3);
      pollReportStatus(reportId, { reportType: selectedReportType });
    } catch (error) {
      console.error('Failed to start report generation:', error);
      setLoadingReport(false);
      setReportError(genericReportError);
      Alert.alert(
        t('reports.errorTitle', 'Unable to generate report'),
        genericReportError
      );
    }
  };

  const openCreditsConfirmModal = async ({ forceRegenerate = false } = {}) => {
    const authOk = await requireAuthForPaid({
      feature: 'PDF report',
      message: 'Sign in to generate a premium PDF report. Reopening a saved report stays free.',
      resume: { resumeRoute: 'ReportsStudio', resumeParams: {} },
    });
    if (!authOk) return;
    setPendingForceRegenerate(Boolean(forceRegenerate));
    setShowCreditsModal(true);
  };

  const handleCreditsModalConfirm = () => {
    const forceRegenerate = pendingForceRegenerate;
    setShowCreditsModal(false);
    startReportGeneration({ forceRegenerate });
  };

  const handleGenerate = () => openCreditsConfirmModal({ forceRegenerate: false });

  const handleRegenerate = () => openCreditsConfirmModal({ forceRegenerate: true });

  const handleOpenExistingReport = async () => {
    if (!isPdfReady) {
      const ready = await hydrateCompletedReport(reportSession?.reportId || reportJobId);
      if (!ready) return;
    }
    await openGeneratedReport();
  };

  const openPastReport = async (item) => {
    if (normalizeHistoryStatus(item?.status) !== 'completed') {
      Alert.alert(
        t('reports.historyNotReadyTitle', 'Report not ready'),
        t('reports.historyNotReadyBody', 'This report is still being prepared.')
      );
      return;
    }
    try {
      setOpeningPastReportId(item.report_id);
      const pdfUrl = await resolveReportPdfUrl(item.report_id);
      if (!pdfUrl) throw new Error(t('reports.pdfOpenUnavailable', 'We could not open the PDF right now.'));
      let pdfUri = pdfUrl;
      try {
        pdfUri = await downloadPdfToLocalUri(pdfUrl, buildReportPdfFileName(item.report_id));
      } catch (downloadError) {
        if (Platform.OS !== 'web') throw downloadError;
        pdfUri = pdfUrl;
      }
      navigation.navigate('ReportViewer', {
        pdfUri,
        pdfUrl,
        title: item.title || t('reports.viewerTitle', 'Your report'),
        subtitle: item.person_a_name && item.person_b_name
          ? `${item.person_a_name} vs ${item.person_b_name}`
          : t('reports.viewerSubtitle', 'Open the generated PDF inside the app.'),
      });
    } catch (error) {
      console.error('[ReportsStudio] open past report failed', error);
      if (Platform.OS === 'web') {
        try {
          const fallbackUrl = await resolveReportPdfUrl(item.report_id).catch(() => '');
          if (fallbackUrl) {
            await Linking.openURL(fallbackUrl);
            return;
          }
        } catch (_) {
          /* fall through */
        }
      }
      Alert.alert(t('reports.pdfErrorTitle', 'PDF error'), genericPdfError);
    } finally {
      setOpeningPastReportId(null);
    }
  };

  const sharePastReport = async (item) => {
    if (normalizeHistoryStatus(item?.status) !== 'completed') {
      Alert.alert(
        t('reports.historyNotReadyTitle', 'Report not ready'),
        t('reports.historyNotReadyBody', 'This report is still being prepared.')
      );
      return;
    }
    try {
      setOpeningPastReportId(item.report_id);
      const pdfUrl = await resolveReportPdfUrl(item.report_id);
      if (!pdfUrl) throw new Error(t('reports.pdfOpenUnavailable', 'We could not open the PDF right now.'));
      const pdfUri = await downloadPdfToLocalUri(pdfUrl, buildReportPdfFileName(item.report_id));
      await sharePDFOnWhatsApp(pdfUri);
    } catch (error) {
      console.error('[ReportsStudio] share past report failed', error);
      Alert.alert(t('reports.pdfErrorTitle', 'PDF error'), genericPdfError);
    } finally {
      setOpeningPastReportId(null);
    }
  };

  const currentLanguageLabel = useMemo(() => {
    const match = LANGUAGES.find((item) => item.code === reportLanguage);
    return match ? `${match.flag} ${match.name}` : reportLanguage;
  }, [reportLanguage]);

  const stepIndex = reportDocument ? 3 : activeStep;
  const stepTitle = activeStep === 1
    ? t('reports.step1Title', 'Step 1 of 3')
    : activeStep === 2
      ? t('reports.step2Title', 'Step 2 of 3')
      : t('reports.step3Title', 'Step 3 of 3');

  const statusMessage = loadingReport
    ? (processingStatus === 'processing'
      ? (isSingleChartReport(selectedReportType)
        ? (selectedReportType === 'health'
          ? t('reports.processingHealth', 'We are reading your chart and assembling the health report now.')
          : t('reports.processingWealth', 'We are reading your chart and assembling the wealth report now.'))
        : t('reports.processing', 'We are reading both charts and assembling the report now.'))
      : t('reports.pending', "We're getting started on your report. This usually takes just a moment."))
    : reportDocument
      ? (generatedPdfUri
        ? t('reports.ready', 'Your premium report PDF is ready.')
        : pdfGenerationState === 'failed'
          ? t('reports.pdfPendingRetry', 'The report is ready, but the PDF needs another try.')
          : t('reports.pdfBuilding', 'The report analysis is complete. We are loading the PDF now.'))
      : t('reports.helper', 'Choose a report type, select the charts, and confirm the language before generating.');

  const sessionMatchesCurrentPair = useMemo(
    () => (
      String(reportSession?.reportType || selectedReportType) === selectedReportType
      && isSameReportSelection(
        selectedReportType,
        selectedPersonA,
        selectedPersonB,
        reportSession?.selectedPersonA,
        reportSession?.selectedPersonB
      )
    ),
    [selectedPersonA, selectedPersonB, reportSession, selectedReportType]
  );
  const sessionMatchesCurrentLanguage = useMemo(
    () => String(reportSession?.language || '').toLowerCase() === String(reportLanguage || '').toLowerCase(),
    [reportSession?.language, reportLanguage]
  );
  const sessionStatus = String(reportSession?.status || '').toLowerCase();
  const isSessionCompleted = sessionStatus === 'completed';
  const isSessionFailed = sessionStatus === 'failed';
  const isSessionRunning = isActiveReportStatus(sessionStatus);
  // Running jobs stay visible even if the user changes natives.
  // Completed/failed banners only apply to the currently selected pair.
  const hasResumeSession = Boolean(reportSession?.reportId) && (isSessionRunning || (sessionMatchesCurrentPair && sessionMatchesCurrentLanguage));
  const canRegenerateCurrentPair = Boolean(
    selectedPersonA
    && (selectedReportType !== 'partnership' || selectedPersonB)
    && sessionMatchesCurrentPair
    && sessionMatchesCurrentLanguage
    && isSessionCompleted
    && !loadingReport
  );
  const isPdfReady = Boolean(generatedPdfUri);
  // Keep result cards on the generate step only; completed returns use the top banner.
  const showProgressCard = activeStep === 3 && (loadingReport || reportError || !reportDocument || !isPdfReady || pdfGenerationState === 'failed');
  const showSuccessCard = activeStep === 3 && sessionMatchesCurrentPair && Boolean(reportDocument && isPdfReady);
  const resumeLabel = isSessionCompleted
    ? (isPdfReady
      ? t('reports.resumeReadyTitle', 'Your report is ready to open')
      : t('reports.resumeBuildTitle', 'Your report analysis is complete'))
    : isSessionFailed
      ? t('reports.resumeFailedTitle', 'Last report could not finish')
      : t('reports.resumeRunningTitle', 'Your report is still being prepared');
  const resumeActionLabel = isSessionCompleted
    ? (isPdfReady
      ? t('reports.openPdf', 'Open PDF')
      : t('reports.buildPdf', 'Load PDF'))
    : isSessionFailed
      ? t('reports.historyTitle', 'Report History')
      : t('reports.resumeAction', 'Resume');

  const handleResumeBannerPress = async () => {
    if (isSessionCompleted) {
      if (!isPdfReady) {
        const ready = await hydrateCompletedReport(reportSession?.reportId);
        if (!ready) return;
      }
      await openGeneratedReport();
      return;
    }
    if (isSessionFailed) {
      navigation.navigate('ReportHistory');
      return;
    }
    restoreReportSession({ forceResume: true });
  };

  const stepLabels = [
    t('reports.stepLabelType', 'Type'),
    t('reports.stepLabelCharts', 'Charts'),
    t('reports.stepLabelLanguage', 'Language'),
  ];
  const availableReportTypes = displayReportTypes.filter((item) => item.enabled !== false);
  const upcomingReportTypes = displayReportTypes.filter((item) => item.enabled === false);
  const headerSubtitleText = canRegenerateCurrentPair
    ? (isSingleChartReport(selectedReportType)
      ? (selectedReportType === 'health'
        ? t('reports.subtitleReadyHealth', 'Your health report for this chart is ready. Open it anytime, or regenerate for a fresh reading.')
        : t('reports.subtitleReadyWealth', 'Your wealth report for this chart is ready. Open it anytime, or regenerate for a fresh reading.'))
      : t('reports.subtitleReady', 'Your report for this pair is ready. Open it anytime, or regenerate for a fresh reading.'))
    : activeStep === 2
      ? (isSingleChartReport(selectedReportType)
        ? (selectedReportType === 'health'
          ? t('reports.subtitleStep2Health', 'Pick the birth chart this health report should study.')
          : t('reports.subtitleStep2Wealth', 'Pick the birth chart this wealth report should study.'))
        : t('reports.subtitleStep2', 'Pick the two charts this report should study.'))
      : activeStep === 3
        ? t('reports.subtitleStep3', 'Confirm language, then open or generate the PDF.')
        : t('reports.subtitle', 'Premium Vedic reports with clear structure and a shareable PDF.');

  return (
    <View style={styles.container}>
      <StatusBar barStyle={isDark ? 'light-content' : 'dark-content'} backgroundColor={colors.background} />
      <LinearGradient
        colors={isDark ? [colors.gradientStart, colors.gradientMid, colors.gradientEnd] : [colors.background, colors.backgroundSecondary, colors.backgroundTertiary]}
        style={styles.gradient}
      >
        <SafeAreaView style={styles.safeArea}>
          <View style={styles.header}>
            <View style={styles.headerTopRow}>
              <TouchableOpacity
                style={[styles.backButton, { backgroundColor: isDark ? 'rgba(255,255,255,0.1)' : colors.surface }]}
                onPress={() => goBackOrHome(navigation)}
                accessibilityRole="button"
                accessibilityLabel={t('common.back', 'Back')}
              >
                <Ionicons name="arrow-back" size={22} color={colors.text} />
              </TouchableOpacity>
              <View style={styles.headerTextWrap}>
                <Text style={[styles.headerTitle, { color: colors.text }]} numberOfLines={1} ellipsizeMode="tail">
                  {t('reports.title', 'Reports Studio')}
                </Text>
                <Text style={[styles.headerSubtitle, { color: colors.textSecondary }]} numberOfLines={2} ellipsizeMode="tail">
                  {headerSubtitleText}
                </Text>
              </View>
              <View style={styles.headerActionsRow}>
                <TouchableOpacity
                  style={[
                    styles.creditButton,
                    {
                      backgroundColor: isDark ? 'rgba(255, 107, 53, 0.2)' : 'rgba(249, 115, 22, 0.12)',
                      borderColor: isDark ? 'rgba(255, 107, 53, 0.4)' : 'rgba(249, 115, 22, 0.35)',
                    },
                  ]}
                  onPress={() => navigation.navigate('Credits')}
                  accessibilityRole="button"
                  accessibilityLabel={t('credits.label', 'Credits')}
                >
                  <Text style={[styles.creditText, { color: colors.text }]}>💳 {credits}</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  onPress={() => navigation.navigate('ReportHistory')}
                  style={[styles.historyButton, { backgroundColor: isDark ? 'rgba(255,255,255,0.08)' : colors.surface }]}
                  accessibilityRole="button"
                  accessibilityLabel={t('reports.historyTitle', 'Report History')}
                >
                  <Ionicons name="time-outline" size={18} color={colors.text} />
                </TouchableOpacity>
              </View>
            </View>
          </View>

          <ScrollView
            style={styles.scroll}
            contentContainerStyle={styles.scrollContent}
            showsVerticalScrollIndicator={false}
          >
            {hasResumeSession ? (
              <TouchableOpacity
                activeOpacity={0.9}
                onPress={handleResumeBannerPress}
                style={styles.resumeBanner}
                accessibilityRole="button"
                accessibilityLabel={resumeLabel}
              >
                <View style={[
                  styles.heroStatusIcon,
                  {
                    backgroundColor: isSessionCompleted
                      ? 'rgba(34,197,94,0.2)'
                      : isSessionFailed
                        ? 'rgba(244,63,94,0.2)'
                        : 'rgba(255,255,255,0.18)',
                  },
                ]}>
                  <Ionicons
                    name={isSessionCompleted ? 'checkmark-circle' : isSessionFailed ? 'alert-circle' : 'hourglass-outline'}
                    size={14}
                    color={isSessionCompleted ? '#86efac' : isSessionFailed ? '#fda4af' : '#fff'}
                  />
                </View>
                <View style={styles.heroStatusTextWrap}>
                  <Text style={styles.heroStatusTitle} numberOfLines={1}>
                    {isSessionCompleted
                      ? t('reports.heroStatusReady', 'Report ready')
                      : isSessionFailed
                        ? t('reports.heroStatusFailed', 'Last report failed')
                        : t('reports.heroStatusPreparing', 'Preparing report')}
                  </Text>
                  <Text style={styles.heroStatusSubtitle} numberOfLines={1}>
                    {isSessionRunning && !sessionMatchesCurrentPair
                      ? `${reportSession?.selectedPersonA?.name || 'Person A'} · ${reportSession?.selectedPersonB?.name || 'Person B'}`
                      : resumeActionLabel}
                  </Text>
                </View>
                <View style={styles.heroStatusAction}>
                  <Text style={styles.heroStatusActionText}>{resumeActionLabel}</Text>
                  <Ionicons name="chevron-forward" size={12} color="#fff" />
                </View>
              </TouchableOpacity>
            ) : null}

            <View style={styles.stepperRow}>
              {[1, 2, 3].map((step) => (
                <View key={step} style={styles.stepperItem}>
                  {step > 1 ? (
                    <View
                      style={[
                        styles.stepperLine,
                        styles.stepperLineLeft,
                        {
                          backgroundColor: step - 1 < stepIndex
                            ? colors.primary
                            : (isDark ? 'rgba(255,255,255,0.12)' : colors.cardBorder),
                        },
                      ]}
                    />
                  ) : null}
                  <View style={styles.stepperColumn}>
                    <View
                      style={[
                        styles.stepperDot,
                        {
                          backgroundColor: step <= stepIndex
                            ? colors.primary
                            : (isDark ? 'rgba(255,255,255,0.15)' : colors.cardBorder),
                        },
                      ]}
                    >
                      {step < stepIndex ? (
                        <Ionicons name="checkmark" size={14} color="#fff" />
                      ) : (
                        <Text style={styles.stepperDotText}>{step}</Text>
                      )}
                    </View>
                    <Text
                      style={[
                        styles.stepperLabel,
                        {
                          color: step <= stepIndex ? colors.text : colors.textSecondary,
                          fontWeight: step === Math.min(activeStep, 3) ? '800' : '600',
                        },
                      ]}
                      numberOfLines={1}
                    >
                      {stepLabels[step - 1]}
                    </Text>
                  </View>
                  {step < 3 ? (
                    <View
                      style={[
                        styles.stepperLine,
                        styles.stepperLineRight,
                        {
                          backgroundColor: step < stepIndex
                            ? colors.primary
                            : (isDark ? 'rgba(255,255,255,0.12)' : colors.cardBorder),
                        },
                      ]}
                    />
                  ) : null}
                </View>
              ))}
            </View>
            <View style={styles.section}>
              <Text style={[styles.sectionTitle, { color: colors.text }]}>
                {stepTitle}
              </Text>
              <Text style={[styles.sectionSubtitle, { color: colors.textSecondary }]}>
                {activeStep === 1
                  ? t('reports.step1Subtitle', 'Choose the report that feels most relevant right now.')
                  : activeStep === 2
                    ? (isSingleChartReport(selectedReportType)
                      ? (selectedReportType === 'health'
                        ? t('reports.step2SubtitleHealth', 'Choose the birth chart for this health report.')
                        : t('reports.step2SubtitleWealth', 'Choose the birth chart for this wealth report.'))
                      : t('reports.step2Subtitle', 'Choose the two charts for this report.'))
                    : t('reports.step3Subtitle', 'Choose the language and then generate the report.')}
              </Text>

              {activeStep === 1 ? (
                <>
                  <View style={styles.reportTypeList}>
                    {availableReportTypes.map((item) => {
                      const costKey = `${item.key}_report`;
                      const itemCost = Number(
                        pricing?.[costKey]
                        ?? (item.key === 'health' ? pricing?.health_report_cost : null)
                        ?? pricing?.partnership_report
                        ?? pricing?.partnership
                        ?? 0
                      ) || 0;
                      const itemOriginal = pricingOriginal?.[costKey]
                        ?? (item.key === 'health' ? pricingOriginal?.health_report_cost : null)
                        ?? null;
                      const selected = selectedReportType === item.key;
                      return (
                        <TouchableOpacity
                          key={item.key}
                          activeOpacity={0.9}
                          onPress={() => {
                            setSelectedReportType(item.key);
                            if (isSingleChartReport(item.key)) setSelectedPersonB(null);
                          }}
                          style={[
                            styles.reportTypeCard,
                            {
                              backgroundColor: selected
                                ? `${item.gradient?.[0] || colors.primary}18`
                                : (isDark ? 'rgba(255,255,255,0.06)' : colors.surface),
                              borderColor: selected ? item.gradient?.[0] || colors.primary : (isDark ? 'rgba(255,255,255,0.12)' : colors.cardBorder),
                            },
                          ]}
                        >
                          <LinearGradient colors={item.gradient || [colors.primary, colors.secondary]} style={styles.reportTypeIcon}>
                            <Text style={styles.reportTypeEmoji}>{item.icon || '📄'}</Text>
                          </LinearGradient>
                          <View style={styles.reportTypeBody}>
                            <View style={styles.reportTypeTopRow}>
                              <Text style={[styles.reportTypeTitle, { color: colors.text }]}>{item.title}</Text>
                              {selected ? (
                                <Ionicons name="checkmark-circle" size={18} color={item.gradient?.[0] || colors.primary} />
                              ) : null}
                            </View>
                            <Text style={[styles.reportTypeSubtitle, { color: colors.textSecondary }]}>{item.subtitle}</Text>
                            <Text style={[styles.reportTypeDescription, { color: colors.textSecondary }]} numberOfLines={2}>
                              {item.description}
                            </Text>
                            <Text style={[styles.reportTypeCostInline, { color: colors.text }]}>
                              {formatCreditsLabel(itemCost, itemOriginal, creditsWord)}
                            </Text>
                          </View>
                        </TouchableOpacity>
                      );
                    })}
                  </View>
                  {upcomingReportTypes.length ? (
                    <View style={styles.upcomingWrap}>
                      <Text style={[styles.upcomingLabel, { color: colors.textSecondary }]}>
                        {t('reports.comingSoonSection', 'Coming soon')}
                      </Text>
                      <View style={styles.upcomingRow}>
                        {upcomingReportTypes.map((item) => (
                          <View
                            key={item.key}
                            style={[
                              styles.upcomingChip,
                              {
                                backgroundColor: isDark ? 'rgba(255,255,255,0.05)' : colors.surface,
                                borderColor: isDark ? 'rgba(255,255,255,0.1)' : colors.cardBorder,
                              },
                            ]}
                          >
                            <Text style={styles.upcomingChipEmoji}>{item.icon || '📄'}</Text>
                            <Text style={[styles.upcomingChipText, { color: colors.textSecondary }]} numberOfLines={1}>
                              {item.shortTitle || item.title}
                            </Text>
                          </View>
                        ))}
                      </View>
                    </View>
                  ) : null}
                  <View style={styles.stepActions}>
                    <View style={styles.stepActionsSpacer} />
                    <TouchableOpacity
                      onPress={goToNextStep}
                      disabled={!step1Ready}
                      style={[styles.stepPrimaryButton, !step1Ready && styles.stepPrimaryButtonDisabled]}
                    >
                      <LinearGradient
                        colors={step1Ready ? ['#fb7185', '#f97316'] : ['#94a3b8', '#64748b']}
                        style={styles.stepPrimaryGradient}
                      >
                        <Text style={styles.stepPrimaryText}>{t('reports.continue', 'Continue')}</Text>
                        <Ionicons name="arrow-forward" size={16} color="#fff" />
                      </LinearGradient>
                    </TouchableOpacity>
                  </View>
                </>
              ) : null}

              {activeStep === 2 ? (
                <>
                  {selectedReportType === 'partnership' ? (
                    <>
                      <View style={styles.nativeSlotsStack}>
                        <NativePreviewCard
                          title={t('reports.selectPersonA', 'Select your chart')}
                          subtitle={t('reports.selectPersonADesc', 'First person in this report')}
                          chart={selectedPersonA}
                          isEmpty={!selectedPersonA}
                          onPress={() => openNativeSelector('personA')}
                          theme={theme}
                          colors={colors}
                          icon="👤"
                          accent={colors.primary}
                          slotLabel={t('reports.personA', 'You')}
                          emptyHint={t('reports.tapToChoose', 'Tap to choose')}
                        />
                        <View style={styles.swapInlineRow}>
                          <View style={[styles.swapDivider, { backgroundColor: isDark ? 'rgba(255,255,255,0.1)' : colors.cardBorder }]} />
                          <TouchableOpacity
                            activeOpacity={0.8}
                            onPress={swapCharts}
                            disabled={!selectedPersonA || !selectedPersonB}
                            style={[
                              styles.swapFab,
                              {
                                backgroundColor: isDark ? 'rgba(255,255,255,0.08)' : colors.surface,
                                borderColor: isDark ? 'rgba(255,255,255,0.12)' : colors.cardBorder,
                                opacity: selectedPersonA && selectedPersonB ? 1 : 0.45,
                              },
                            ]}
                            accessibilityRole="button"
                            accessibilityLabel={t('reports.swapCharts', 'Swap charts')}
                          >
                            <Ionicons name="swap-vertical" size={16} color={colors.textSecondary} />
                          </TouchableOpacity>
                          <View style={[styles.swapDivider, { backgroundColor: isDark ? 'rgba(255,255,255,0.1)' : colors.cardBorder }]} />
                        </View>
                        <NativePreviewCard
                          title={t('reports.selectPersonB', 'Select the other chart')}
                          subtitle={t('reports.selectPersonBDesc', 'Second person in this report')}
                          chart={selectedPersonB}
                          isEmpty={!selectedPersonB}
                          onPress={() => openNativeSelector('personB')}
                          theme={theme}
                          colors={colors}
                          icon="💞"
                          accent="#fb7185"
                          slotLabel={t('reports.personB', 'Other person')}
                          emptyHint={t('reports.tapToChoose', 'Tap to choose')}
                        />
                      </View>
                    </>
                  ) : isSingleChartReport(selectedReportType) ? (
                    <View style={styles.nativeSlotsStack}>
                      <NativePreviewCard
                        title={
                          selectedReportType === 'health'
                            ? t('reports.selectHealthChart', 'Select your chart')
                            : t('reports.selectWealthChart', 'Select your chart')
                        }
                        subtitle={
                          selectedReportType === 'health'
                            ? t('reports.selectHealthChartDesc', 'Single birth chart for this health report')
                            : t('reports.selectWealthChartDesc', 'Single birth chart for this wealth report')
                        }
                        chart={selectedPersonA}
                        isEmpty={!selectedPersonA}
                        onPress={() => openNativeSelector('personA')}
                        theme={theme}
                        colors={colors}
                        icon={selectedReportType === 'health' ? '🏥' : '💰'}
                        accent={selectedReportType === 'health' ? '#22c55e' : '#0EA5E9'}
                        slotLabel={t('reports.personA', 'You')}
                        emptyHint={t('reports.tapToChoose', 'Tap to choose')}
                      />
                    </View>
                  ) : (
                    <View style={[styles.comingSoonPanel, { backgroundColor: isDark ? 'rgba(255,255,255,0.05)' : colors.surface, borderColor: colors.cardBorder }]}>
                      <Ionicons name="time-outline" size={20} color={colors.textSecondary} />
                      <Text style={[styles.comingSoonText, { color: colors.textSecondary }]}>
                        {t('reports.comingSoonPairing', 'This report type will get its own chart flow soon. Partnership, Wealth, and Health are live now.')}
                      </Text>
                    </View>
                  )}
                  <View style={styles.stepActions}>
                    <TouchableOpacity
                      onPress={goToPreviousStep}
                      style={[styles.stepSecondaryButton, { borderColor: colors.cardBorder, backgroundColor: isDark ? 'rgba(255,255,255,0.06)' : colors.surface }]}
                    >
                      <Text style={[styles.stepSecondaryText, { color: colors.text }]}>{t('reports.back', 'Back')}</Text>
                    </TouchableOpacity>
                    <TouchableOpacity
                      onPress={goToNextStep}
                      disabled={!step2Ready}
                      style={[styles.stepPrimaryButton, !step2Ready && styles.stepPrimaryButtonDisabled]}
                    >
                      <LinearGradient
                        colors={step2Ready ? ['#fb7185', '#f97316'] : ['#94a3b8', '#64748b']}
                        style={styles.stepPrimaryGradient}
                      >
                        <Text style={styles.stepPrimaryText}>{t('reports.continue', 'Continue')}</Text>
                        <Ionicons name="arrow-forward" size={16} color="#fff" />
                      </LinearGradient>
                    </TouchableOpacity>
                  </View>
                </>
              ) : null}

              {activeStep === 3 ? (
                <>
                  <View
                    style={[
                      styles.reviewCard,
                      {
                        backgroundColor: isDark ? 'rgba(255,255,255,0.06)' : colors.surface,
                        borderColor: isDark ? 'rgba(255,255,255,0.12)' : colors.cardBorder,
                      },
                    ]}
                  >
                    <Text style={[styles.reviewTitle, { color: colors.text }]}>
                      {t('reports.reviewTitle', 'Report summary')}
                    </Text>
                    <View style={styles.reviewRow}>
                      <Text style={[styles.reviewLabel, { color: colors.textSecondary }]}>
                        {isSingleChartReport(selectedReportType)
                          ? t('reports.reviewChart', 'Chart')
                          : t('reports.reviewPair', 'Pair')}
                      </Text>
                      <Text style={[styles.reviewValue, { color: colors.text }]} numberOfLines={1}>
                        {isSingleChartReport(selectedReportType)
                          ? (selectedPersonA?.name || '—')
                          : `${selectedPersonA?.name || '—'} · ${selectedPersonB?.name || '—'}`}
                      </Text>
                    </View>
                    <View style={styles.reviewRow}>
                      <Text style={[styles.reviewLabel, { color: colors.textSecondary }]}>
                        {t('reports.reviewType', 'Type')}
                      </Text>
                      <Text style={[styles.reviewValue, { color: colors.text }]} numberOfLines={1}>
                        {selectedTypeDisplay?.title || t('reports.types.partnership.title', 'Partnership Report')}
                      </Text>
                    </View>
                    <View style={styles.reviewRow}>
                      <Text style={[styles.reviewLabel, { color: colors.textSecondary }]}>
                        {t('reports.reviewCost', 'Credits')}
                      </Text>
                      <Text style={[styles.reviewValue, { color: colors.text }]}>
                        {canRegenerateCurrentPair
                          ? t('reports.reviewAlreadyPaid', 'Already generated')
                          : formatCreditsLabel(reportCost, reportOriginalCost, creditsWord)}
                      </Text>
                    </View>
                  </View>
                  <TouchableOpacity
                    activeOpacity={0.9}
                    onPress={() => setShowLanguageModal(true)}
                    style={[
                      styles.languageCard,
                      {
                        backgroundColor: isDark ? 'rgba(255,255,255,0.06)' : colors.surface,
                        borderColor: isDark ? 'rgba(255,255,255,0.12)' : colors.cardBorder,
                      },
                    ]}
                  >
                    <View style={styles.languageLeft}>
                      <View style={[styles.languageIcon, { backgroundColor: `${colors.primary}18` }]}>
                        <Ionicons name="language-outline" size={18} color={colors.primary} />
                      </View>
                      <View style={{ flex: 1 }}>
                        <Text style={[styles.languageTitle, { color: colors.text }]}>
                          {currentLanguageLabel}
                        </Text>
                        <Text style={[styles.languageSubtitle, { color: colors.textSecondary }]}>
                          {t('reports.languageHelp', 'Used for the AI narrative inside the PDF.')}
                        </Text>
                      </View>
                    </View>
                    <Text style={[styles.languageChange, { color: colors.primary }]}>
                      {t('reports.change', 'Change')}
                    </Text>
                  </TouchableOpacity>
                  {selectedReportType === 'janam_kundli' ? (
                    <View
                      style={[
                        styles.brandingCard,
                        {
                          backgroundColor: isDark ? 'rgba(255,255,255,0.06)' : colors.surface,
                          borderColor: isDark ? 'rgba(255,255,255,0.12)' : colors.cardBorder,
                        },
                      ]}
                    >
                      <Text style={[styles.reviewTitle, { color: colors.text }]}>
                        {t('reports.brandingTitle', 'Your branding on the PDF')}
                      </Text>
                      <Text style={[styles.languageSubtitle, { color: colors.textSecondary, marginBottom: 8 }]}>
                        {t(
                          'reports.brandingHelp',
                          'Saved to your account — used on cover and footer. Leave blank for AstroRoshni branding.'
                        )}
                      </Text>
                      {[
                        ['business_name', t('reports.brandingBusiness', 'Practice / business name'), 'Pandit Sharma Jyotish'],
                        ['tagline', t('reports.brandingTagline', 'Tagline (optional)'), 'Vedic guidance you can trust'],
                        ['phone', t('reports.brandingPhone', 'Phone'), '+91 …'],
                        ['email', t('reports.brandingEmail', 'Email'), 'you@example.com'],
                        ['website', t('reports.brandingWebsite', 'Website'), 'https://…'],
                        ['address', t('reports.brandingAddress', 'Address (optional)'), 'City, State'],
                      ].map(([key, label, placeholder]) => (
                        <View key={key} style={styles.brandingField}>
                          <Text style={[styles.brandingLabel, { color: colors.textSecondary }]}>{label}</Text>
                          <TextInput
                            value={String(reportBranding[key] || '')}
                            onChangeText={(text) => updateBrandingField(key, text)}
                            placeholder={placeholder}
                            placeholderTextColor={isDark ? 'rgba(255,255,255,0.35)' : '#94a3b8'}
                            autoCapitalize={key === 'email' || key === 'website' ? 'none' : 'words'}
                            keyboardType={key === 'phone' ? 'phone-pad' : (key === 'email' ? 'email-address' : 'default')}
                            style={[
                              styles.brandingInput,
                              {
                                color: colors.text,
                                borderColor: isDark ? 'rgba(255,255,255,0.14)' : colors.cardBorder,
                                backgroundColor: isDark ? 'rgba(0,0,0,0.2)' : '#fff',
                              },
                            ]}
                          />
                        </View>
                      ))}
                      {!brandingLoaded ? (
                        <Text style={[styles.languageSubtitle, { color: colors.textSecondary }]}>
                          {t('reports.brandingLoading', 'Loading saved branding…')}
                        </Text>
                      ) : null}
                    </View>
                  ) : null}
                  <View style={styles.stepActions}>
                    <TouchableOpacity
                      onPress={goToPreviousStep}
                      style={[styles.stepSecondaryButton, { borderColor: colors.cardBorder, backgroundColor: isDark ? 'rgba(255,255,255,0.06)' : colors.surface }]}
                    >
                      <Text style={[styles.stepSecondaryText, { color: colors.text }]}>{t('reports.back', 'Back')}</Text>
                    </TouchableOpacity>
                    {canRegenerateCurrentPair ? (
                      <TouchableOpacity
                        activeOpacity={0.9}
                        disabled={loadingReport}
                        onPress={handleOpenExistingReport}
                        style={[styles.stepPrimaryButton, loadingReport && styles.stepPrimaryButtonDisabled]}
                      >
                        <LinearGradient
                          colors={loadingReport ? ['#94a3b8', '#64748b'] : ['#22c55e', '#16a34a']}
                          style={styles.stepPrimaryGradient}
                        >
                          {loadingReport ? <ActivityIndicator size="small" color="#fff" /> : <Ionicons name="document-text-outline" size={18} color="#fff" />}
                          <Text style={styles.stepPrimaryText}>
                            {t('reports.openExisting', 'Open report')}
                          </Text>
                        </LinearGradient>
                      </TouchableOpacity>
                    ) : (
                      <TouchableOpacity
                        activeOpacity={0.9}
                        disabled={!readyToGenerate || checkingExistingReport}
                        onPress={handleGenerate}
                        style={[styles.stepPrimaryButton, (!readyToGenerate || checkingExistingReport) && styles.stepPrimaryButtonDisabled]}
                      >
                        <LinearGradient
                          colors={(readyToGenerate && !checkingExistingReport) ? ['#fb7185', '#f97316'] : ['#94a3b8', '#64748b']}
                          style={styles.stepPrimaryGradient}
                        >
                          {(loadingReport || checkingExistingReport) ? <ActivityIndicator size="small" color="#fff" /> : <Ionicons name="sparkles" size={18} color="#fff" />}
                          <Text style={styles.stepPrimaryText}>
                            {loadingReport
                              ? t('reports.generating', 'Generating your report...')
                              : checkingExistingReport
                                ? t('reports.checkingExisting', 'Checking for existing report...')
                              : t('reports.generateWithCredits', {
                                  defaultValue: `Generate · ${reportCost} credits`,
                                  count: reportCost,
                                })}
                          </Text>
                        </LinearGradient>
                      </TouchableOpacity>
                    )}
                  </View>
                  {canRegenerateCurrentPair ? (
                    <TouchableOpacity
                      disabled={loadingReport}
                      onPress={handleRegenerate}
                      style={[
                        styles.regenerateButton,
                        {
                          borderColor: colors.cardBorder,
                          backgroundColor: isDark ? 'rgba(255,255,255,0.06)' : colors.surface,
                          opacity: loadingReport ? 0.6 : 1,
                        },
                      ]}
                    >
                      <Ionicons name="refresh" size={16} color={colors.text} />
                      <Text style={[styles.regenerateButtonText, { color: colors.text }]}>
                        {t('reports.regenerateWithCredits', {
                          defaultValue: `Regenerate · ${reportCost} credits`,
                          count: reportCost,
                        })}
                      </Text>
                    </TouchableOpacity>
                  ) : null}
                </>
              ) : null}
            </View>

            {showProgressCard ? (
              <View style={[styles.statusCard, { backgroundColor: isDark ? 'rgba(255,255,255,0.06)' : colors.surface, borderColor: isDark ? 'rgba(255,255,255,0.12)' : colors.cardBorder }]}>
                <View style={styles.statusTopRow}>
                  <Ionicons
                    name={loadingReport ? 'hourglass-outline' : reportDocument ? 'sparkles-outline' : 'sparkles-outline'}
                    size={18}
                    color={reportError ? '#f43f5e' : colors.primary}
                  />
                  <Text style={[styles.statusText, { color: colors.text }]}>{statusMessage}</Text>
                </View>
                {reportError ? (
                  <Text style={[styles.errorText, { color: '#f43f5e' }]}>{reportError}</Text>
                ) : null}
              </View>
            ) : null}

              {showSuccessCard ? (
                <View style={[styles.successCard, { backgroundColor: isDark ? 'rgba(34,197,94,0.08)' : 'rgba(34,197,94,0.08)', borderColor: isDark ? 'rgba(34,197,94,0.28)' : 'rgba(34,197,94,0.22)' }]}>
                  <View style={styles.successHeaderRow}>
                    <View style={styles.successIconWrap}>
                      <Ionicons name="checkmark-circle" size={22} color="#16a34a" />
                    </View>
                    <View style={{ flex: 1 }}>
                      <Text style={[styles.successTitle, { color: colors.text }]}>
                        {t('reports.successTitle', 'Your report is ready')}
                      </Text>
                      <Text style={[styles.successBody, { color: colors.textSecondary }]} numberOfLines={2}>
                        {reportDocument?.premium_report?.headline
                          || t('reports.successBody', 'Open the PDF now, or share it with someone.')}
                      </Text>
                    </View>
                  </View>
                  <NotificationEnableBanner reason="report_ready" active={showSuccessCard} style={{ marginTop: 10, marginBottom: 4 }} />
                  <View style={styles.actionRow}>
                    <TouchableOpacity onPress={openGeneratedReport} style={styles.actionButton}>
                      <Ionicons name="document-text-outline" size={16} color="#fff" />
                      <Text style={styles.actionButtonText}>{t('reports.openPdf', 'Open PDF')}</Text>
                    </TouchableOpacity>
                    <TouchableOpacity
                      onPress={async () => {
                        try {
                          await sharePDFOnWhatsApp(generatedPdfUri);
                        } catch (error) {
                          console.error('Share report PDF failed:', error);
                          Alert.alert(
                            t('reports.pdfErrorTitle', 'PDF error'),
                            genericPdfError
                          );
                        }
                      }}
                      style={[styles.actionButton, styles.actionButtonSecondary, { borderColor: colors.cardBorder, backgroundColor: isDark ? 'rgba(255,255,255,0.06)' : colors.surface }]}
                    >
                      <Ionicons name="share-outline" size={16} color={colors.text} />
                      <Text style={[styles.actionButtonText, { color: colors.text }]}>{t('reports.sharePdf', 'Share')}</Text>
                    </TouchableOpacity>
                  </View>
                  {pdfGenerationState === 'failed' ? (
                    <TouchableOpacity
                      onPress={async () => {
                        try {
                          setReportError('');
                          setPdfGenerationState('building');
                          const reportId = reportJobId || reportDocument?.report_id;
                          const pdfUrl = reportDocument?.pdf_url || (reportId ? await resolveReportPdfUrl(reportId) : '');
                          if (!pdfUrl) {
                            throw new Error(t('reports.pdfOpenUnavailable', 'We could not open the PDF right now.'));
                          }
                          await ensureLocalPdf(reportId, pdfUrl);
                        } catch (error) {
                          console.error('Load report PDF failed:', error);
                          if (mountedRef.current) {
                            setPdfGenerationState('failed');
                            setReportError(genericPdfError);
                          }
                          Alert.alert(
                            t('reports.pdfErrorTitle', 'PDF error'),
                            genericPdfError
                          );
                        }
                      }}
                      style={styles.retryLink}
                    >
                      <Text style={[styles.retryLinkText, { color: colors.primary }]}>
                        {t('reports.buildPdf', 'Load PDF now')}
                      </Text>
                    </TouchableOpacity>
                  ) : null}
                </View>
              ) : null}

            <View style={styles.pastReportsSection}>
              <View style={styles.pastReportsHeader}>
                <View style={{ flex: 1 }}>
                  <Text style={[styles.pastReportsTitle, { color: colors.text }]}>
                    {t('reports.pastReportsTitle', 'Your past reports')}
                  </Text>
                  <Text style={[styles.pastReportsSubtitle, { color: colors.textSecondary }]}>
                    {t('reports.pastReportsSubtitle', 'Reports you have already generated stay here so you can open them again.')}
                  </Text>
                </View>
                <TouchableOpacity
                  onPress={() => navigation.navigate('ReportHistory')}
                  hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
                  accessibilityRole="button"
                  accessibilityLabel={t('reports.historyTitle', 'Report History')}
                >
                  <Text style={[styles.pastReportsSeeAll, { color: colors.primary }]}>
                    {t('reports.seeAllHistory', 'See all')}
                  </Text>
                </TouchableOpacity>
              </View>

              {loadingPastReports ? (
                <View style={[styles.pastReportsEmpty, { borderColor: colors.cardBorder, backgroundColor: isDark ? 'rgba(255,255,255,0.04)' : colors.surface }]}>
                  <ActivityIndicator color={colors.primary} />
                </View>
              ) : pastReports.length === 0 ? (
                <View style={[styles.pastReportsEmpty, { borderColor: colors.cardBorder, backgroundColor: isDark ? 'rgba(255,255,255,0.04)' : colors.surface }]}>
                  <Ionicons name="documents-outline" size={22} color={colors.textSecondary} />
                  <Text style={[styles.pastReportsEmptyTitle, { color: colors.text }]}>
                    {t('reports.historyEmptyTitle', 'No reports yet')}
                  </Text>
                  <Text style={[styles.pastReportsEmptyBody, { color: colors.textSecondary }]}>
                    {t('reports.historyEmptyBody', 'When you generate a report, it will appear here so you can open it again later.')}
                  </Text>
                </View>
              ) : (
                pastReports.map((item) => {
                  const typeMeta = reportTypeMap.get(item.report_type) || REPORT_TYPE_FALLBACKS[0];
                  const statusMeta = HISTORY_STATUS_META[normalizeHistoryStatus(item.status)] || HISTORY_STATUS_META.pending;
                  const isOpening = openingPastReportId === item.report_id;
                  const isCompleted = normalizeHistoryStatus(item.status) === 'completed';
                  const dateLabel = formatHistoryDate(
                    item.completed_at || item.created_at,
                    i18n.language === 'en' ? 'en-IN' : undefined
                  );
                  return (
                    <View
                      key={item.report_id || `${item.report_type}-${item.created_at}`}
                      style={[
                        styles.pastReportCard,
                        {
                          backgroundColor: isDark ? 'rgba(255,255,255,0.06)' : colors.surface,
                          borderColor: isDark ? 'rgba(255,255,255,0.12)' : colors.cardBorder,
                        },
                      ]}
                    >
                      <View style={styles.pastReportTopRow}>
                        <View style={[styles.pastReportIconWrap, { backgroundColor: `${(typeMeta.gradient || ['#f97316'])[0]}18` }]}>
                          <Text style={styles.pastReportIconText}>{typeMeta.icon || '📄'}</Text>
                        </View>
                        <View style={{ flex: 1, minWidth: 0 }}>
                          <Text style={[styles.pastReportTitle, { color: colors.text }]} numberOfLines={1}>
                            {item.title || typeMeta.title || t('reports.viewerTitle', 'Your report')}
                          </Text>
                          <Text style={[styles.pastReportSubtitle, { color: colors.textSecondary }]} numberOfLines={2}>
                            {item.person_a_name && item.person_b_name
                              ? `${item.person_a_name} vs ${item.person_b_name}`
                              : item.person_a_name || item.subtitle || t('reports.historySubtitleFallback', 'Generated report')}
                          </Text>
                          <View style={styles.pastReportMetaRow}>
                            <View style={[styles.pastReportStatusPill, { backgroundColor: `${statusMeta.tint}18` }]}>
                              <Ionicons name={statusMeta.icon} size={12} color={statusMeta.tint} />
                              <Text style={[styles.pastReportStatusText, { color: statusMeta.tint }]}>
                                {t(`reports.status.${normalizeHistoryStatus(item.status)}`, item.status || 'pending')}
                              </Text>
                            </View>
                            {item.language ? (
                              <Text style={[styles.pastReportLang, { color: colors.textTertiary || colors.textSecondary }]}>
                                {String(item.language).toUpperCase()}
                              </Text>
                            ) : null}
                          </View>
                          {dateLabel ? (
                            <Text style={[styles.pastReportDate, { color: colors.textTertiary || colors.textSecondary }]}>
                              {dateLabel}
                            </Text>
                          ) : null}
                        </View>
                      </View>
                      <View style={styles.pastReportActions}>
                        <TouchableOpacity
                          onPress={() => openPastReport(item)}
                          disabled={isOpening || !isCompleted}
                          style={[
                            styles.pastReportPrimaryBtn,
                            { backgroundColor: colors.primary },
                            (isOpening || !isCompleted) && styles.pastReportBtnDisabled,
                          ]}
                        >
                          {isOpening ? (
                            <ActivityIndicator color="#fff" size="small" />
                          ) : (
                            <Text style={styles.pastReportPrimaryBtnText}>{t('reports.openPdf', 'Open PDF')}</Text>
                          )}
                        </TouchableOpacity>
                        <TouchableOpacity
                          onPress={() => sharePastReport(item)}
                          disabled={isOpening || !isCompleted}
                          style={[
                            styles.pastReportSecondaryBtn,
                            {
                              borderColor: colors.cardBorder,
                              backgroundColor: isDark ? 'rgba(255,255,255,0.04)' : colors.surface,
                            },
                            (isOpening || !isCompleted) && styles.pastReportBtnDisabled,
                          ]}
                        >
                          <Text style={[styles.pastReportSecondaryBtnText, { color: colors.text }]}>
                            {t('reports.sharePdf', 'Share')}
                          </Text>
                        </TouchableOpacity>
                      </View>
                    </View>
                  );
                })
              )}
            </View>

          </ScrollView>

          <ConfirmCreditsModal
            visible={showCreditsModal}
            onClose={() => setShowCreditsModal(false)}
            onConfirm={handleCreditsModalConfirm}
            title={pendingForceRegenerate
              ? t('reports.regenerateTitle', 'Regenerate report?')
              : t('reports.creditConfirmTitle', 'Generate report?')}
            description={t('reports.creditConfirmBody', {
              defaultValue: 'Credits are deducted only after the report is generated successfully. You will get a premium PDF with chart overlays, timing, and remedies.',
              count: reportCost,
            })}
            cost={reportCost}
            credits={credits}
            confirmLabel={pendingForceRegenerate
              ? t('reports.regenerateAction', 'Regenerate')
              : t('reports.generate', 'Generate report')}
          />

          <Modal visible={showLanguageModal} transparent animationType="fade" onRequestClose={() => setShowLanguageModal(false)}>
            <View style={styles.modalOverlay}>
              <View style={[styles.modalCard, { backgroundColor: colors.background }]}>
                <View style={styles.modalHeader}>
                  <Text style={[styles.modalTitle, { color: colors.text }]}>
                    {t('reports.languageModalTitle', 'Choose report language')}
                  </Text>
                  <TouchableOpacity onPress={() => setShowLanguageModal(false)}>
                    <Ionicons name="close" size={22} color={colors.textSecondary} />
                  </TouchableOpacity>
                </View>
                <ScrollView style={{ maxHeight: 420 }}>
                  {LANGUAGES.map((lang) => {
                    const selected = lang.code === reportLanguage;
                    return (
                      <TouchableOpacity
                        key={lang.code}
                        onPress={() => {
                          setReportLanguage(lang.code);
                          setShowLanguageModal(false);
                        }}
                        style={[
                          styles.languageOption,
                          {
                            borderColor: selected ? colors.primary : colors.cardBorder,
                            backgroundColor: selected ? `${colors.primary}12` : colors.surface,
                          },
                        ]}
                      >
                        <Text style={styles.languageOptionFlag}>{lang.flag}</Text>
                        <Text style={[styles.languageOptionText, { color: colors.text }]}>{lang.name}</Text>
                        {selected ? <Ionicons name="checkmark-circle" size={18} color={colors.primary} /> : null}
                      </TouchableOpacity>
                    );
                  })}
                </ScrollView>
              </View>
            </View>
          </Modal>
        </SafeAreaView>
      </LinearGradient>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  gradient: { flex: 1 },
  safeArea: { flex: 1 },
  header: {
    gap: 0,
    paddingHorizontal: 16,
    paddingTop: 8,
    paddingBottom: 10,
  },
  headerTopRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 10,
  },
  backButton: {
    width: 42,
    height: 42,
    borderRadius: 21,
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerActionsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    flexShrink: 0,
  },
  headerTextWrap: {
    flex: 1,
    minWidth: 0,
    paddingHorizontal: 2,
  },
  headerTitle: { fontSize: 18, fontWeight: '800' },
  headerSubtitle: { fontSize: 12, marginTop: 2, lineHeight: 16 },
  creditButton: {
    borderWidth: 1,
    paddingHorizontal: 10,
    paddingVertical: 7,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
  },
  creditText: { fontSize: 12, fontWeight: '700' },
  historyButton: {
    width: 40,
    height: 40,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
  },
  historyButtonText: { fontSize: 10, fontWeight: '900' },
  scroll: { flex: 1 },
  scrollContent: {
    paddingHorizontal: 16,
    paddingBottom: 36,
  },
  pastReportsSection: {
    marginTop: 22,
    gap: 12,
  },
  pastReportsHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 12,
  },
  pastReportsTitle: {
    fontSize: 17,
    fontWeight: '800',
  },
  pastReportsSubtitle: {
    fontSize: 12,
    lineHeight: 17,
    marginTop: 3,
  },
  pastReportsSeeAll: {
    fontSize: 13,
    fontWeight: '800',
    marginTop: 2,
  },
  pastReportsEmpty: {
    borderWidth: 1,
    borderRadius: 18,
    paddingVertical: 22,
    paddingHorizontal: 16,
    alignItems: 'center',
    gap: 8,
  },
  pastReportsEmptyTitle: {
    fontSize: 15,
    fontWeight: '800',
  },
  pastReportsEmptyBody: {
    fontSize: 12,
    lineHeight: 17,
    textAlign: 'center',
  },
  pastReportCard: {
    borderWidth: 1,
    borderRadius: 18,
    padding: 14,
    gap: 12,
  },
  pastReportTopRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 12,
  },
  pastReportIconWrap: {
    width: 42,
    height: 42,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
  },
  pastReportIconText: {
    fontSize: 20,
  },
  pastReportTitle: {
    fontSize: 15,
    fontWeight: '800',
  },
  pastReportSubtitle: {
    fontSize: 12,
    lineHeight: 17,
    marginTop: 2,
  },
  pastReportMetaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginTop: 8,
    flexWrap: 'wrap',
  },
  pastReportStatusPill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    borderRadius: 999,
    paddingHorizontal: 8,
    paddingVertical: 3,
  },
  pastReportStatusText: {
    fontSize: 11,
    fontWeight: '700',
    textTransform: 'capitalize',
  },
  pastReportLang: {
    fontSize: 11,
    fontWeight: '700',
  },
  pastReportDate: {
    fontSize: 11,
    marginTop: 6,
  },
  pastReportActions: {
    flexDirection: 'row',
    gap: 10,
  },
  pastReportPrimaryBtn: {
    flex: 1,
    borderRadius: 14,
    minHeight: 42,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 12,
  },
  pastReportPrimaryBtnText: {
    color: '#fff',
    fontSize: 13,
    fontWeight: '800',
  },
  pastReportSecondaryBtn: {
    flex: 1,
    borderRadius: 14,
    minHeight: 42,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    paddingHorizontal: 12,
  },
  pastReportSecondaryBtnText: {
    fontSize: 13,
    fontWeight: '800',
  },
  pastReportBtnDisabled: {
    opacity: 0.55,
  },
  resumeBanner: {
    marginTop: 2,
    marginBottom: 8,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    paddingVertical: 10,
    paddingHorizontal: 12,
    borderRadius: 16,
    backgroundColor: 'rgba(15, 23, 42, 0.92)',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.14)',
  },
  heroStatusChip: {
    marginTop: -12,
    marginHorizontal: 10,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    paddingVertical: 8,
    paddingHorizontal: 10,
    borderRadius: 16,
    backgroundColor: 'rgba(15, 23, 42, 0.88)',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.14)',
  },
  heroStatusIcon: {
    width: 28,
    height: 28,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
  },
  heroStatusTextWrap: {
    flex: 1,
    minWidth: 0,
  },
  heroStatusTitle: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '800',
  },
  heroStatusSubtitle: {
    color: 'rgba(255,255,255,0.72)',
    fontSize: 10,
    fontWeight: '600',
    marginTop: 1,
  },
  heroStatusAction: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 2,
    paddingHorizontal: 8,
    paddingVertical: 6,
    borderRadius: 999,
    backgroundColor: 'rgba(255,255,255,0.14)',
  },
  heroStatusActionText: {
    color: '#fff',
    fontSize: 10,
    fontWeight: '800',
  },
  stepperRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    width: '100%',
    marginTop: 8,
    marginBottom: 16,
  },
  stepperItem: {
    flex: 1,
    alignItems: 'center',
    position: 'relative',
  },
  stepperColumn: {
    alignItems: 'center',
    zIndex: 1,
  },
  stepperDot: {
    width: 28,
    height: 28,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
  },
  stepperDotText: { color: '#fff', fontWeight: '800', fontSize: 12 },
  stepperLabel: { fontSize: 11, marginTop: 6, textAlign: 'center' },
  stepperLine: {
    position: 'absolute',
    top: 13,
    height: 2,
    borderRadius: 2,
  },
  stepperLineLeft: {
    left: 0,
    right: '50%',
    marginRight: 18,
  },
  stepperLineRight: {
    left: '50%',
    right: 0,
    marginLeft: 18,
  },
  section: {
    marginBottom: 18,
  },
  sectionTitle: { fontSize: 17, fontWeight: '800' },
  sectionSubtitle: { fontSize: 13, lineHeight: 19, marginTop: 4, marginBottom: 14 },
  stepActions: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    marginTop: 16,
  },
  stepActionsSpacer: {
    flex: 1,
  },
  stepPrimaryButton: {
    flex: 1.35,
    borderRadius: 16,
    overflow: 'hidden',
  },
  stepPrimaryButtonDisabled: {
    opacity: 0.7,
  },
  stepPrimaryGradient: {
    minHeight: 50,
    borderRadius: 16,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingHorizontal: 12,
  },
  stepPrimaryText: {
    color: '#fff',
    fontWeight: '800',
    fontSize: 13,
  },
  stepSecondaryButton: {
    flex: 0.75,
    borderWidth: 1,
    borderRadius: 16,
    minHeight: 50,
    alignItems: 'center',
    justifyContent: 'center',
  },
  stepSecondaryText: {
    fontWeight: '800',
    fontSize: 13,
  },
  reportTypeList: { gap: 12 },
  reportTypeCard: {
    borderWidth: 1,
    borderRadius: 20,
    padding: 14,
    flexDirection: 'row',
    gap: 12,
    alignItems: 'flex-start',
  },
  reportTypeIcon: {
    width: 48,
    height: 48,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
  },
  reportTypeEmoji: { fontSize: 22 },
  reportTypeBody: { flex: 1 },
  reportTypeTopRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 10,
  },
  reportTypeTitle: { fontSize: 15, fontWeight: '800', flex: 1 },
  reportTypeBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 999,
  },
  reportTypeBadgeText: { fontSize: 10, fontWeight: '800' },
  reportTypeSubtitle: { fontSize: 12, marginTop: 4, fontWeight: '600' },
  reportTypeDescription: { fontSize: 12, marginTop: 4, lineHeight: 17 },
  reportTypeCostInline: { fontSize: 12, fontWeight: '800', marginTop: 8 },
  reportTypeCostWrap: { alignItems: 'flex-end', minWidth: 52 },
  reportTypeCost: { fontSize: 14, fontWeight: '900' },
  upcomingWrap: { marginTop: 14, gap: 8 },
  upcomingLabel: { fontSize: 12, fontWeight: '700' },
  upcomingRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  upcomingChip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    borderWidth: 1,
    borderRadius: 999,
    paddingHorizontal: 10,
    paddingVertical: 7,
  },
  upcomingChipEmoji: { fontSize: 13 },
  upcomingChipText: { fontSize: 11, fontWeight: '700' },
  nativeSlotsStack: {
    gap: 0,
  },
  nativeSlotsRow: {
    flexDirection: 'row',
    gap: 12,
  },
  nativeSlotColumn: { flex: 1 },
  nativeSlotLabel: { fontSize: 12, fontWeight: '800', marginBottom: 8, textTransform: 'uppercase', letterSpacing: 0.5 },
  nativeCard: {
    minHeight: 88,
    borderWidth: 1,
    borderRadius: 18,
    padding: 14,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  nativeCardEmpty: { opacity: 1 },
  nativeCardIcon: {
    width: 44,
    height: 44,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
  },
  nativeCardEmoji: { fontSize: 20 },
  nativeCardBody: { flex: 1 },
  nativeCardTitle: { fontSize: 15, fontWeight: '800' },
  nativeCardSubtitle: { fontSize: 12, marginTop: 4, lineHeight: 17 },
  nativeCardMeta: { fontSize: 11, marginTop: 6, fontWeight: '700' },
  swapInlineRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginVertical: 8,
    gap: 10,
  },
  swapDivider: {
    flex: 1,
    height: StyleSheet.hairlineWidth,
  },
  swapFab: {
    width: 36,
    height: 36,
    borderRadius: 18,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  swapButton: {
    marginTop: 12,
    borderWidth: 1,
    borderRadius: 999,
    paddingVertical: 12,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
  },
  swapButtonText: { fontSize: 12, fontWeight: '800' },
  comingSoonPanel: {
    borderWidth: 1,
    borderRadius: 20,
    padding: 16,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  comingSoonText: { flex: 1, fontSize: 13, lineHeight: 18 },
  reviewCard: {
    borderWidth: 1,
    borderRadius: 18,
    padding: 14,
    marginBottom: 12,
    gap: 10,
  },
  reviewTitle: { fontSize: 14, fontWeight: '800', marginBottom: 2 },
  reviewRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 12,
  },
  reviewLabel: { fontSize: 12, fontWeight: '600' },
  reviewValue: { flex: 1, textAlign: 'right', fontSize: 13, fontWeight: '700' },
  languageCard: {
    borderWidth: 1,
    borderRadius: 18,
    padding: 14,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 10,
  },
  languageLeft: { flexDirection: 'row', alignItems: 'center', gap: 12, flex: 1 },
  languageIcon: {
    width: 42,
    height: 42,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
  },
  languageTitle: { fontSize: 15, fontWeight: '800' },
  languageSubtitle: { fontSize: 12, marginTop: 4, lineHeight: 17 },
  languageChange: { fontSize: 12, fontWeight: '800' },
  brandingCard: {
    borderWidth: 1,
    borderRadius: 18,
    padding: 14,
    marginTop: 12,
    gap: 8,
  },
  brandingField: { gap: 4 },
  brandingLabel: { fontSize: 12, fontWeight: '600' },
  brandingInput: {
    borderWidth: 1,
    borderRadius: 12,
    paddingHorizontal: 12,
    paddingVertical: Platform.OS === 'ios' ? 12 : 8,
    fontSize: 14,
    fontWeight: '600',
  },
  statusCard: {
    borderWidth: 1,
    borderRadius: 18,
    padding: 16,
    marginBottom: 18,
  },
  successCard: {
    borderWidth: 1,
    borderRadius: 18,
    padding: 16,
    marginBottom: 18,
  },
  successHeaderRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 10,
  },
  successIconWrap: {
    marginTop: 1,
  },
  statusTopRow: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  statusText: { flex: 1, fontSize: 13, lineHeight: 19, fontWeight: '700' },
  errorText: { marginTop: 10, fontSize: 12, lineHeight: 18, fontWeight: '700' },
  successSummary: { marginTop: 12 },
  successTitle: { fontSize: 15, fontWeight: '800' },
  successMeta: { fontSize: 12, marginTop: 4 },
  successBody: { fontSize: 12, marginTop: 4, lineHeight: 17 },
  actionRow: { flexDirection: 'row', gap: 10, marginTop: 14 },
  actionButton: {
    flex: 1,
    borderRadius: 14,
    paddingVertical: 12,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#fb7185',
    flexDirection: 'row',
    gap: 6,
  },
  actionButtonSecondary: {
    backgroundColor: 'transparent',
    borderWidth: 1,
  },
  actionButtonContent: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
  },
  actionButtonText: { color: '#fff', fontWeight: '800', fontSize: 13 },
  retryLink: {
    marginTop: 12,
    alignItems: 'center',
  },
  retryLinkText: {
    fontSize: 12,
    fontWeight: '700',
  },
  regenerateButton: {
    marginTop: 10,
    borderWidth: 1,
    borderRadius: 14,
    paddingVertical: 12,
    paddingHorizontal: 14,
    alignItems: 'center',
    justifyContent: 'center',
    flexDirection: 'row',
    gap: 8,
  },
  regenerateButtonText: {
    fontSize: 13,
    fontWeight: '800',
  },
  generateButton: {
    borderRadius: 24,
    overflow: 'hidden',
  },
  generateButtonDisabled: { opacity: 0.7 },
  generateGradient: {
    minHeight: 58,
    borderRadius: 24,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 10,
  },
  generateButtonText: { color: '#fff', fontWeight: '900', fontSize: 16 },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.55)',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 18,
  },
  modalCard: {
    width: '100%',
    borderRadius: 24,
    padding: 16,
  },
  modalHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  modalTitle: { fontSize: 16, fontWeight: '900' },
  languageOption: {
    borderWidth: 1,
    borderRadius: 16,
    paddingHorizontal: 14,
    paddingVertical: 13,
    marginBottom: 10,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  languageOptionFlag: { fontSize: 18 },
  languageOptionText: { flex: 1, fontSize: 14, fontWeight: '800' },
});
