import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  StatusBar,
  Alert,
  Modal,
  ActivityIndicator,
  AppState,
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
    subtitle: 'Coming soon',
    description: 'A future report for income flow, saving patterns, and wealth growth.',
    icon: '💰',
    gradient: ['#0EA5E9', '#38BDF8'],
    enabled: false,
  },
  {
    key: 'health',
    title: 'Health Report',
    subtitle: 'Coming soon',
    description: 'A future report for body constitution, care points, and wellness habits.',
    icon: '🏥',
    gradient: ['#22c55e', '#15803d'],
    enabled: false,
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

const REPORT_SESSION_KEY = 'reportsStudioActiveSession';

const NativePreviewCard = ({ title, subtitle, chart, onPress, isEmpty, theme, colors, icon, accent }) => (
  <TouchableOpacity
    activeOpacity={0.9}
    onPress={onPress}
    style={[
      styles.nativeCard,
      {
        backgroundColor: theme === 'dark' ? 'rgba(255,255,255,0.06)' : colors.surface,
        borderColor: theme === 'dark' ? 'rgba(255,255,255,0.12)' : colors.cardBorder,
      },
      isEmpty && styles.nativeCardEmpty,
    ]}
  >
    <View style={[styles.nativeCardIcon, { backgroundColor: `${accent}18` }]}>
      <Text style={styles.nativeCardEmoji}>{icon}</Text>
    </View>
    <View style={styles.nativeCardBody}>
      <Text style={[styles.nativeCardTitle, { color: colors.text }]}>{title}</Text>
      <Text style={[styles.nativeCardSubtitle, { color: colors.textSecondary }]} numberOfLines={2}>
        {isEmpty ? subtitle : formatBirthLine(chart)}
      </Text>
      {!isEmpty && chart?.name ? (
        <Text style={[styles.nativeCardMeta, { color: colors.textTertiary }]} numberOfLines={1}>
          {chart.name}
        </Text>
      ) : null}
    </View>
    <Ionicons name="chevron-forward" size={22} color={colors.textTertiary} />
  </TouchableOpacity>
);

export default function ReportsStudioScreen({ navigation, route }) {
  const { t, i18n } = useTranslation();
  useAnalytics('ReportsStudioScreen');
  const { theme, colors } = useTheme();
  const isDark = theme === 'dark';
  const { pricing, pricingOriginal, credits } = useCredits();

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
  const pollTimerRef = useRef(null);
  const reportSessionRef = useRef(null);
  const mountedRef = useRef(true);

  const reportTypeMap = useMemo(() => {
    const map = new Map();
    [...REPORT_TYPE_FALLBACKS, ...reportTypes].forEach((item) => {
      if (!item?.key) return;
      map.set(item.key, { ...map.get(item.key), ...item });
    });
    return map;
  }, [reportTypes]);

  const reportCost = useMemo(() => {
    const key = `${selectedReportType}_report`;
    return Number(pricing?.[key] ?? pricing?.partnership_report ?? pricing?.partnership ?? 9) || 0;
  }, [pricing, selectedReportType]);

  const reportOriginalCost = useMemo(() => {
    const key = `${selectedReportType}_report`;
    return pricingOriginal?.[key] ?? null;
  }, [pricingOriginal, selectedReportType]);

  const selectedTypeMeta = reportTypeMap.get(selectedReportType) || REPORT_TYPE_FALLBACKS[0];
  const selectedTypeEnabled = selectedTypeMeta?.enabled !== false;
  const step1Ready = !!selectedReportType && selectedTypeEnabled;
  const step2Ready = selectedReportType !== 'partnership' || (!!selectedPersonA && !!selectedPersonB);
  const readyToGenerate = selectedReportType === 'partnership' && !!selectedPersonA && !!selectedPersonB && !loadingReport;

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

  const restoreReportSession = useCallback(async () => {
    if (!mountedRef.current) return;

    const session = await loadStoredReportSession();
    if (!session?.reportId) return;

    reportSessionRef.current = session;
    setReportSession(session);
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
    setReportJobId(session.reportId);
    setActiveStep(3);
    setReportError('');
    setLoadingReport(true);
    setProcessingStatus(session.status === 'completed' ? 'processing' : (session.status || 'pending'));
    await pollReportStatus(session.reportId, { fromRestore: true });
  }, [loadStoredReportSession]);

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

  useFocusEffect(
    useCallback(() => {
      restoreReportSession();
    }, [restoreReportSession])
  );

  useEffect(() => {
    const subscription = AppState.addEventListener('change', (nextState) => {
      if (nextState === 'active') {
        restoreReportSession();
      }
    });
    return () => subscription.remove();
  }, [restoreReportSession]);

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
      if (pdfGenerationState === 'building') {
        Alert.alert(
          t('reports.pdfBuildingTitle', 'PDF is still loading'),
          t('reports.pdfBuildingBody', 'The report is ready, but the PDF is still being prepared. Please try again in a moment.')
        );
        return;
      }

      const reportId = reportJobId || reportDocument?.report_id;
      const pdfUrl = reportDocument?.pdf_url || (reportId ? await resolveReportPdfUrl(reportId) : '');
      const pdfUri = generatedPdfUri || (pdfUrl && reportId ? await ensureLocalPdf(reportId, pdfUrl) : '');
      if (!pdfUri) {
        throw new Error(t('reports.pdfOpenUnavailable', 'We could not open the PDF right now.'));
      }
      navigation.navigate('ReportViewer', {
        pdfUri,
        pdfUrl,
        title: reportDocument?.premium_report?.headline || t('reports.viewerTitle', 'Your report'),
        subtitle: currentLanguageLabel,
      });
    } catch (error) {
      Alert.alert(
        t('reports.pdfErrorTitle', 'PDF error'),
        t('reports.pdfErrorBody', {
          defaultValue: `We could not load the PDF right now. ${error?.message || 'Unknown error'}`,
          message: error?.message || 'Unknown error',
        })
      );
    }
  };

  const pollReportStatus = async (reportId, options = {}) => {
    clearPollTimer();
    try {
      const response = await reportAPI.getPartnershipReportStatus(reportId);
      const statusPayload = response?.data || {};
      const status = String(statusPayload.status || '').toLowerCase();
      setProcessingStatus(status || 'pending');

      await persistReportSession({
        ...(reportSessionRef.current || {}),
        reportId,
        reportType: selectedReportType,
        language: reportLanguage,
        status: status || 'pending',
        selectedPersonA,
        selectedPersonB,
        updatedAt: Date.now(),
      });

      if (status === 'completed') {
        const data = statusPayload.data || {};
        setReportDocument(data);
        setLoadingReport(false);
        setReportError('');
        setPdfGenerationState('building');
        try {
          const pdfUrl = data.pdf_url || await resolveReportPdfUrl(reportId, data.pdf_url || '');
          if (!pdfUrl) {
            throw new Error('PDF URL not available yet');
          }
          await ensureLocalPdf(reportId, pdfUrl);
        } catch (error) {
          console.error('PDF download failed:', error);
          const friendlyMessage = error?.response?.data?.detail || error?.message || t('reports.pdfErrorBody', {
            defaultValue: 'We could not load the PDF right now. Please try again in a moment.',
            message: 'Unknown error',
          });
          if (mountedRef.current) {
            setPdfGenerationState('failed');
            setReportError(friendlyMessage);
          }
          Alert.alert(
            t('reports.pdfErrorTitle', 'PDF error'),
            friendlyMessage
          );
        }
        await persistReportSession({
          ...(reportSessionRef.current || {}),
          reportId,
          reportType: selectedReportType,
          language: reportLanguage,
          status: 'completed',
          selectedPersonA,
          selectedPersonB,
          updatedAt: Date.now(),
        });
        return;
      }

      if (status === 'failed') {
        const errorMessage = statusPayload.error || t('reports.reportFailed', 'We could not generate the report right now. Please try again.');
        setReportError(errorMessage);
        setLoadingReport(false);
        await persistReportSession({
          ...(reportSessionRef.current || {}),
          reportId,
          reportType: selectedReportType,
          language: reportLanguage,
          status: 'failed',
          selectedPersonA,
          selectedPersonB,
          errorMessage,
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
      setReportError(error?.response?.data?.detail || error?.message || t('reports.reportFailed', 'We could not generate the report right now. Please try again.'));
      setLoadingReport(false);
      if (error?.response?.status === 404) {
        await persistReportSession(null);
      }
    }
  };

  const handleGenerate = async () => {
    if (!selectedTypeMeta?.enabled && selectedReportType !== 'partnership') {
      Alert.alert(
        t('reports.comingSoonTitle', 'Coming soon'),
        t('reports.comingSoonBody', 'This report type is not available yet. We are building it next.')
      );
      return;
    }

    if (selectedReportType !== 'partnership') {
      Alert.alert(
        t('reports.unavailableTitle', 'Not ready yet'),
        t('reports.unavailableBody', 'Only partnership reports are available in this release.')
      );
      return;
    }

    if (!selectedPersonA || !selectedPersonB) {
      Alert.alert(
        t('reports.missingPairTitle', 'Choose both people'),
        t('reports.missingPairBody', 'Please select both chart slots before generating your report.')
      );
      return;
    }

    if (credits < reportCost) {
      navigation.navigate('Credits');
      return;
    }

    try {
      setLoadingReport(true);
      setReportError('');
      setReportDocument(null);
      setGeneratedPdfUri('');
      setProcessingStatus('pending');
      const response = await reportAPI.startPartnershipReport(
        selectedPersonA,
        selectedPersonB,
        reportLanguage,
        { includeImages: true, forceRegenerate: false, chartStyle: 'both' }
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
        selectedPersonB,
        createdAt: Date.now(),
        updatedAt: Date.now(),
      });
      setActiveStep(3);
      pollReportStatus(reportId);
    } catch (error) {
      console.error('Failed to start report generation:', error);
      setLoadingReport(false);
      setReportError(error?.response?.data?.detail || error?.message || t('reports.startFailed', 'Could not start the report.'));
      Alert.alert(
        t('reports.errorTitle', 'Unable to generate report'),
        error?.response?.data?.detail || error?.message || t('reports.startFailed', 'Could not start the report.')
      );
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
      ? t('reports.processing', 'We are reading both charts and assembling the report now.')
      : t('reports.pending', 'Your report job is queued and will start shortly.'))
    : reportDocument
      ? (generatedPdfUri
        ? t('reports.ready', 'Your premium report PDF is ready.')
        : pdfGenerationState === 'failed'
          ? t('reports.pdfPendingRetry', 'The report is ready, but the PDF needs another try.')
          : t('reports.pdfBuilding', 'The report analysis is complete. We are loading the PDF now.'))
      : t('reports.helper', 'Choose a report type, select the charts, and confirm the language before generating.');

  const showProgressCard = loadingReport || reportError || !reportDocument || !isPdfReady || pdfGenerationState === 'failed';
  const showSuccessCard = Boolean(reportDocument && isPdfReady);

  const hasResumeSession = Boolean(reportSession?.reportId);
  const isPdfReady = Boolean(generatedPdfUri);
  const resumeLabel = reportSession?.status === 'completed'
    ? (isPdfReady
      ? t('reports.resumeReadyTitle', 'Your report is ready to open')
      : t('reports.resumeBuildTitle', 'Your report analysis is complete')
    )
    : t('reports.resumeRunningTitle', 'Your report is still being prepared');
  const resumeBody = reportSession?.status === 'completed'
    ? (isPdfReady
      ? t('reports.resumeReadyBody', 'You can open the latest PDF now, share it again, or review it later in history.')
      : t('reports.resumeBuildBody', 'The report analysis finished successfully, and we are still building the PDF file. You can come back in a moment and open it from here or history.')
    )
    : t('reports.resumeRunningBody', 'We saved your progress. When you come back, we continue checking the same report automatically.');

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
                onPress={() => navigation.goBack()}
              >
                <Ionicons name="arrow-back" size={22} color={colors.text} />
              </TouchableOpacity>
              <View style={styles.headerActionsRow}>
                <View style={[styles.creditPill, { backgroundColor: isDark ? 'rgba(255,255,255,0.08)' : colors.surface }]}>
                  <Ionicons name="sparkles" size={14} color={colors.primary} />
                  <Text style={[styles.creditText, { color: colors.text }]}>
                    {credits}
                  </Text>
                </View>
                <TouchableOpacity
                  onPress={() => navigation.navigate('ReportHistory')}
                  style={[styles.historyButton, { backgroundColor: isDark ? 'rgba(255,255,255,0.08)' : colors.surface }]}
                >
                  <Ionicons name="time-outline" size={16} color={colors.text} />
                  <Text style={[styles.historyButtonText, { color: colors.text }]}>
                    {t('reports.historyTitle', 'Report History')}
                  </Text>
                </TouchableOpacity>
              </View>
            </View>
            <View style={styles.headerTextWrap}>
              <Text style={[styles.headerTitle, { color: colors.text }]} numberOfLines={1} ellipsizeMode="tail">
                {t('reports.title', 'Reports Studio')}
              </Text>
              <Text style={[styles.headerSubtitle, { color: colors.textSecondary }]} numberOfLines={2} ellipsizeMode="tail">
                {t('reports.subtitle', 'Create a premium report with clear structure, deep insights, and a polished PDF viewer.')}
              </Text>
            </View>
          </View>

          {hasResumeSession ? (
            <View style={[styles.resumeCard, { backgroundColor: isDark ? 'rgba(255,255,255,0.07)' : colors.surface, borderColor: colors.cardBorder }]}>
              <View style={styles.resumeIconWrap}>
                <Ionicons
                  name={reportSession?.status === 'completed' ? 'checkmark-circle' : 'hourglass-outline'}
                  size={18}
                  color={reportSession?.status === 'completed' ? '#22c55e' : colors.primary}
                />
              </View>
              <View style={styles.resumeBody}>
                <Text style={[styles.resumeTitle, { color: colors.text }]}>{resumeLabel}</Text>
                <Text style={[styles.resumeText, { color: colors.textSecondary }]}>{resumeBody}</Text>
              </View>
              <TouchableOpacity
                onPress={() => {
                  if (reportSession?.status === 'completed' && isPdfReady) {
                    openGeneratedReport();
                    return;
                  }
                  restoreReportSession();
                }}
                style={[styles.resumeAction, { backgroundColor: colors.primary }]}
              >
                <Text style={styles.resumeActionText}>
                  {reportSession?.status === 'completed'
                    ? (isPdfReady
                      ? t('reports.openPdf', 'Open PDF')
                      : t('reports.buildPdf', 'Load PDF'))
                    : t('reports.resumeAction', 'Resume')}
                </Text>
              </TouchableOpacity>
            </View>
          ) : null}

          <ScrollView
            style={styles.scroll}
            contentContainerStyle={styles.scrollContent}
            showsVerticalScrollIndicator={false}
          >
            <LinearGradient colors={['#fb7185', '#f97316']} style={styles.heroCard}>
              <View style={styles.heroTopRow}>
                <View style={styles.heroIconWrap}>
                  <Text style={styles.heroEmoji}>📄</Text>
                </View>
                <View style={styles.heroTextWrap}>
                  <Text style={styles.heroTitle} numberOfLines={1} ellipsizeMode="tail">
                    {t('reports.heroTitle', 'Authentic Deep Vedic Analysis')}
                  </Text>
                  <Text style={styles.heroBody} numberOfLines={2} ellipsizeMode="tail">
                    {t('reports.heroBody', 'Choose two charts, confirm the language, and we will generate a polished 20-page report with chart overlays, timing, remedies, and clear takeaways.')}
                  </Text>
                </View>
              </View>
              <View style={styles.heroFooterRow}>
                <View style={styles.heroBadge}>
                  <Text style={styles.heroBadgeText}>
                    {t('reports.pageCount', { defaultValue: '20 pages' })}
                  </Text>
                </View>
                <View style={styles.heroBadge}>
                  <Text style={styles.heroBadgeText}>
                    {t('reports.languageBadge', { defaultValue: currentLanguageLabel })}
                  </Text>
                </View>
              </View>
            </LinearGradient>

            <View style={styles.stepperRow}>
              {[1, 2, 3].map((step) => (
                <View key={step} style={styles.stepperItem}>
                  <View
                    style={[
                      styles.stepperDot,
                      { backgroundColor: step <= stepIndex ? colors.primary : (isDark ? 'rgba(255,255,255,0.15)' : colors.cardBorder) },
                    ]}
                  >
                    <Text style={styles.stepperDotText}>{step}</Text>
                  </View>
                  {step < 3 ? <View style={[styles.stepperLine, { backgroundColor: isDark ? 'rgba(255,255,255,0.12)' : colors.cardBorder }]} /> : null}
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
                    ? t('reports.step2Subtitle', 'Choose the two charts for this report.')
                    : t('reports.step3Subtitle', 'Choose the language and then generate the report.')}
              </Text>

              {activeStep === 1 ? (
                <>
                  <View style={styles.reportTypeList}>
                    {reportTypes.map((item) => {
                      const costKey = `${item.key}_report`;
                      const itemCost = Number(pricing?.[costKey] ?? pricing?.partnership_report ?? pricing?.partnership ?? 0) || 0;
                      const itemOriginal = pricingOriginal?.[costKey] ?? null;
                      const selected = selectedReportType === item.key;
                      const enabled = item.enabled !== false;
                      return (
                        <TouchableOpacity
                          key={item.key}
                          activeOpacity={enabled ? 0.9 : 1}
                          onPress={() => enabled && setSelectedReportType(item.key)}
                          style={[
                            styles.reportTypeCard,
                            {
                              backgroundColor: selected
                                ? `${item.gradient?.[0] || colors.primary}18`
                                : (isDark ? 'rgba(255,255,255,0.06)' : colors.surface),
                              borderColor: selected ? item.gradient?.[0] || colors.primary : (isDark ? 'rgba(255,255,255,0.12)' : colors.cardBorder),
                              opacity: enabled ? 1 : 0.78,
                            },
                          ]}
                        >
                          <LinearGradient colors={item.gradient || [colors.primary, colors.secondary]} style={styles.reportTypeIcon}>
                            <Text style={styles.reportTypeEmoji}>{item.icon}</Text>
                          </LinearGradient>
                          <View style={styles.reportTypeBody}>
                            <View style={styles.reportTypeTopRow}>
                              <Text style={[styles.reportTypeTitle, { color: colors.text }]}>{item.title}</Text>
                              <View style={[styles.reportTypeBadge, { backgroundColor: enabled ? 'rgba(34,197,94,0.14)' : 'rgba(148,163,184,0.18)' }]}>
                                <Text style={[styles.reportTypeBadgeText, { color: enabled ? '#22c55e' : colors.textSecondary }]}>
                                  {enabled ? t('reports.available', 'Available') : t('reports.comingSoon', 'Coming soon')}
                                </Text>
                              </View>
                            </View>
                            <Text style={[styles.reportTypeSubtitle, { color: colors.textSecondary }]}>{item.subtitle}</Text>
                            <Text style={[styles.reportTypeDescription, { color: colors.textSecondary }]} numberOfLines={3}>
                              {item.description}
                            </Text>
                          </View>
                          <View style={styles.reportTypeCostWrap}>
                            <Text style={[styles.reportTypeCost, { color: colors.text }]}>{formatCost(itemCost, itemOriginal)}</Text>
                          </View>
                        </TouchableOpacity>
                      );
                    })}
                  </View>
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
                      <View style={styles.nativeSlotsRow}>
                        <View style={styles.nativeSlotColumn}>
                          <Text style={[styles.nativeSlotLabel, { color: colors.textSecondary }]}>
                            {t('reports.personA', 'You')}
                          </Text>
                          <NativePreviewCard
                            title={selectedPersonA?.name || t('reports.selectPersonA', 'Select your chart')}
                            subtitle={t('reports.selectPersonADesc', 'Choose the first chart for this report')}
                            chart={selectedPersonA}
                            isEmpty={!selectedPersonA}
                            onPress={() => openNativeSelector('personA')}
                            theme={theme}
                            colors={colors}
                            icon="👤"
                            accent={colors.primary}
                          />
                        </View>
                        <View style={styles.nativeSlotColumn}>
                          <Text style={[styles.nativeSlotLabel, { color: colors.textSecondary }]}>
                            {t('reports.personB', 'Other person')}
                          </Text>
                          <NativePreviewCard
                            title={selectedPersonB?.name || t('reports.selectPersonB', 'Select the other chart')}
                            subtitle={t('reports.selectPersonBDesc', 'Choose the second chart for comparison')}
                            chart={selectedPersonB}
                            isEmpty={!selectedPersonB}
                            onPress={() => openNativeSelector('personB')}
                            theme={theme}
                            colors={colors}
                            icon="💞"
                            accent="#fb7185"
                          />
                        </View>
                      </View>
                      <TouchableOpacity
                        activeOpacity={0.8}
                        onPress={swapCharts}
                        disabled={!selectedPersonA || !selectedPersonB}
                        style={[
                          styles.swapButton,
                          {
                            backgroundColor: isDark ? 'rgba(255,255,255,0.06)' : colors.surface,
                            borderColor: isDark ? 'rgba(255,255,255,0.12)' : colors.cardBorder,
                            opacity: selectedPersonA && selectedPersonB ? 1 : 0.45,
                          },
                        ]}
                      >
                        <Ionicons name="swap-horizontal" size={16} color={colors.textSecondary} />
                        <Text style={[styles.swapButtonText, { color: colors.textSecondary }]}>
                          {t('reports.swapCharts', 'Swap charts')}
                        </Text>
                      </TouchableOpacity>
                    </>
                  ) : (
                    <View style={[styles.comingSoonPanel, { backgroundColor: isDark ? 'rgba(255,255,255,0.05)' : colors.surface, borderColor: colors.cardBorder }]}>
                      <Ionicons name="time-outline" size={20} color={colors.textSecondary} />
                      <Text style={[styles.comingSoonText, { color: colors.textSecondary }]}>
                        {t('reports.comingSoonPairing', 'This report type will get its own chart flow soon. Partnership is the first live report.')}
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
                      <View>
                        <Text style={[styles.languageTitle, { color: colors.text }]}>
                          {currentLanguageLabel}
                        </Text>
                        <Text style={[styles.languageSubtitle, { color: colors.textSecondary }]}>
                          {t('reports.languageHelp', 'This language will be used for the AI text inside the report.')}
                        </Text>
                      </View>
                    </View>
                    <Ionicons name="chevron-forward" size={20} color={colors.textSecondary} />
                  </TouchableOpacity>
                  <View style={styles.stepActions}>
                    <TouchableOpacity
                      onPress={goToPreviousStep}
                      style={[styles.stepSecondaryButton, { borderColor: colors.cardBorder, backgroundColor: isDark ? 'rgba(255,255,255,0.06)' : colors.surface }]}
                    >
                      <Text style={[styles.stepSecondaryText, { color: colors.text }]}>{t('reports.back', 'Back')}</Text>
                    </TouchableOpacity>
                    <TouchableOpacity
                      activeOpacity={0.9}
                      disabled={!readyToGenerate}
                      onPress={handleGenerate}
                      style={[styles.stepPrimaryButton, !readyToGenerate && styles.stepPrimaryButtonDisabled]}
                    >
                      <LinearGradient
                        colors={readyToGenerate ? ['#fb7185', '#f97316'] : ['#94a3b8', '#64748b']}
                        style={styles.stepPrimaryGradient}
                      >
                        {loadingReport ? <ActivityIndicator size="small" color="#fff" /> : <Ionicons name="sparkles" size={18} color="#fff" />}
                        <Text style={styles.stepPrimaryText}>
                          {loadingReport ? t('reports.generating', 'Generating your report...') : t('reports.generate', 'Generate report')}
                        </Text>
                      </LinearGradient>
                    </TouchableOpacity>
                  </View>
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
                <View style={[styles.successCard, { backgroundColor: isDark ? 'rgba(255,255,255,0.06)' : colors.surface, borderColor: isDark ? 'rgba(255,255,255,0.12)' : colors.cardBorder }]}>
                  <View style={styles.successSummary}>
                    <Text style={[styles.successTitle, { color: colors.text }]}>
                      {reportDocument?.premium_report?.headline || t('reports.successTitle', 'Your report is ready to open')}
                    </Text>
                    <Text style={[styles.successMeta, { color: colors.textSecondary }]}>
                      {t('reports.successMeta', 'Report ID')}: {reportJobId || reportDocument?.report_id || '--'}
                    </Text>
                    <Text style={[styles.successBody, { color: colors.textSecondary }]}>
                      {t('reports.successBody', 'Open the PDF now, share it with someone, or come back to it later from history.')}
                    </Text>
                  </View>
                  <View style={styles.actionRow}>
                  <TouchableOpacity onPress={openGeneratedReport} style={styles.actionButton}>
                    <Text style={styles.actionButtonText}>{t('reports.openPdf', 'Open PDF')}</Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    onPress={async () => {
                      try {
                        await sharePDFOnWhatsApp(generatedPdfUri);
                      } catch (error) {
                        Alert.alert(
                          t('reports.pdfErrorTitle', 'PDF error'),
                          t('reports.pdfErrorBody', {
                            defaultValue: `We could not build the PDF right now. ${error?.message || 'Unknown error'}`,
                            message: error?.message || 'Unknown error',
                          })
                        );
                      }
                    }}
                    style={styles.actionButton}
                  >
                    <Text style={styles.actionButtonText}>{t('reports.sharePdf', 'Share PDF')}</Text>
                  </TouchableOpacity>
                </View>
                <TouchableOpacity
                  disabled={pdfGenerationState === 'building'}
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
                      Alert.alert(
                        t('reports.pdfReadyTitle', 'PDF ready'),
                        t('reports.pdfReadyBody', 'Your PDF has been loaded and is ready to open.')
                      );
                    } catch (error) {
                      const friendlyMessage = error?.message || t('reports.pdfErrorBody', {
                        defaultValue: 'We could not load the PDF right now. Please try again in a moment.',
                        message: 'Unknown error',
                      });
                      if (mountedRef.current) {
                        setPdfGenerationState('failed');
                        setReportError(friendlyMessage);
                      }
                      Alert.alert(
                        t('reports.pdfErrorTitle', 'PDF error'),
                        friendlyMessage
                      );
                    }
                  }}
                  style={[
                    styles.actionButton,
                    styles.actionButtonSecondary,
                    {
                      borderColor: colors.cardBorder,
                      marginTop: 10,
                      opacity: pdfGenerationState === 'building' ? 0.7 : 1,
                    },
                  ]}
                >
                  <Text style={[styles.actionButtonText, { color: colors.text }]}>
                    {generatedPdfUri ? t('reports.buildAgain', 'Load PDF again') : t('reports.buildPdf', 'Load PDF now')}
                  </Text>
                </TouchableOpacity>
              </View>
            ) : null}

          </ScrollView>

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
    gap: 10,
    paddingHorizontal: 16,
    paddingTop: 8,
    paddingBottom: 12,
  },
  headerTopRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 12,
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
    flexShrink: 1,
  },
  headerTextWrap: {
    flex: 1,
    minWidth: 0,
    paddingRight: 4,
  },
  headerTitle: { fontSize: 20, fontWeight: '800' },
  headerSubtitle: { fontSize: 12, marginTop: 2, lineHeight: 16 },
  creditPill: {
    paddingHorizontal: 10,
    paddingVertical: 8,
    borderRadius: 16,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  creditText: { fontSize: 12, fontWeight: '800' },
  historyButton: {
    minHeight: 40,
    paddingHorizontal: 12,
    borderRadius: 18,
    alignItems: 'center',
    justifyContent: 'center',
    flexDirection: 'row',
    gap: 6,
  },
  historyButtonText: { fontSize: 10, fontWeight: '900' },
  resumeCard: {
    marginHorizontal: 16,
    marginBottom: 10,
    borderWidth: 1,
    borderRadius: 22,
    padding: 14,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  resumeIconWrap: {
    width: 40,
    height: 40,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'rgba(255,255,255,0.08)',
  },
  resumeBody: { flex: 1 },
  resumeTitle: { fontSize: 14, fontWeight: '900' },
  resumeText: { marginTop: 3, fontSize: 11, lineHeight: 16, fontWeight: '700' },
  resumeAction: {
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderRadius: 14,
  },
  resumeActionText: { color: '#fff', fontWeight: '900', fontSize: 11 },
  scroll: { flex: 1 },
  scrollContent: {
    paddingHorizontal: 16,
    paddingBottom: 30,
  },
  heroCard: {
    borderRadius: 22,
    padding: 12,
    marginTop: 4,
    shadowColor: '#000',
    shadowOpacity: 0.12,
    shadowRadius: 12,
    shadowOffset: { width: 0, height: 6 },
    elevation: 4,
  },
  heroTopRow: { flexDirection: 'row', alignItems: 'flex-start', gap: 12 },
  heroIconWrap: {
    width: 44,
    height: 44,
    borderRadius: 14,
    backgroundColor: 'rgba(255,255,255,0.16)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  heroEmoji: { fontSize: 22 },
  heroTextWrap: { flex: 1 },
  heroTitle: { color: '#fff', fontSize: 17, fontWeight: '900', lineHeight: 21 },
  heroBody: { color: 'rgba(255,255,255,0.92)', marginTop: 4, lineHeight: 17, fontSize: 12 },
  heroFooterRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 6, marginTop: 10 },
  heroBadge: {
    backgroundColor: 'rgba(255,255,255,0.16)',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 999,
  },
  heroBadgeText: { color: '#fff', fontWeight: '800', fontSize: 11 },
  stepperRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginVertical: 18,
  },
  stepperItem: { flexDirection: 'row', alignItems: 'center', flex: 1 },
  stepperDot: {
    width: 28,
    height: 28,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
  },
  stepperDotText: { color: '#fff', fontWeight: '900', fontSize: 12 },
  stepperLine: { flex: 1, height: 2, marginHorizontal: 8, borderRadius: 2 },
  section: {
    marginBottom: 18,
  },
  sectionTitle: { fontSize: 18, fontWeight: '800' },
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
    flex: 1,
    borderRadius: 18,
    overflow: 'hidden',
  },
  stepPrimaryButtonDisabled: {
    opacity: 0.7,
  },
  stepPrimaryGradient: {
    minHeight: 52,
    borderRadius: 18,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
  },
  stepPrimaryText: {
    color: '#fff',
    fontWeight: '900',
    fontSize: 14,
  },
  stepSecondaryButton: {
    flex: 1,
    borderWidth: 1,
    borderRadius: 18,
    minHeight: 52,
    alignItems: 'center',
    justifyContent: 'center',
  },
  stepSecondaryText: {
    fontWeight: '900',
    fontSize: 14,
  },
  reportTypeList: { gap: 12 },
  reportTypeCard: {
    borderWidth: 1,
    borderRadius: 22,
    padding: 14,
    flexDirection: 'row',
    gap: 12,
    alignItems: 'center',
  },
  reportTypeIcon: {
    width: 52,
    height: 52,
    borderRadius: 18,
    alignItems: 'center',
    justifyContent: 'center',
  },
  reportTypeEmoji: { fontSize: 24 },
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
  reportTypeSubtitle: { fontSize: 12, marginTop: 4, fontWeight: '700' },
  reportTypeDescription: { fontSize: 12, marginTop: 4, lineHeight: 18 },
  reportTypeCostWrap: { alignItems: 'flex-end', minWidth: 52 },
  reportTypeCost: { fontSize: 14, fontWeight: '900' },
  nativeSlotsRow: {
    flexDirection: 'row',
    gap: 12,
  },
  nativeSlotColumn: { flex: 1 },
  nativeSlotLabel: { fontSize: 12, fontWeight: '800', marginBottom: 8, textTransform: 'uppercase', letterSpacing: 0.5 },
  nativeCard: {
    minHeight: 100,
    borderWidth: 1,
    borderRadius: 20,
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
  nativeCardMeta: { fontSize: 11, marginTop: 6 },
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
  languageCard: {
    borderWidth: 1,
    borderRadius: 20,
    padding: 16,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
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
  statusCard: {
    borderWidth: 1,
    borderRadius: 22,
    padding: 16,
    marginBottom: 18,
  },
  successCard: {
    borderWidth: 1,
    borderRadius: 22,
    padding: 16,
    marginBottom: 18,
  },
  statusTopRow: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  statusText: { flex: 1, fontSize: 13, lineHeight: 19, fontWeight: '700' },
  errorText: { marginTop: 10, fontSize: 12, lineHeight: 18, fontWeight: '700' },
  successSummary: { marginTop: 12 },
  successTitle: { fontSize: 15, fontWeight: '900' },
  successMeta: { fontSize: 12, marginTop: 4 },
  successBody: { fontSize: 12, marginTop: 6, lineHeight: 17 },
  actionRow: { flexDirection: 'row', gap: 10, marginTop: 14 },
  actionButton: {
    flex: 1,
    borderRadius: 14,
    paddingVertical: 13,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#fb7185',
  },
  actionButtonSecondary: {
    backgroundColor: 'transparent',
    borderWidth: 1,
  },
  actionButtonText: { color: '#fff', fontWeight: '900', fontSize: 13 },
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
