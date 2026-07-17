import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
  Dimensions,
  Alert,
  Modal,
  Platform,
} from 'react-native';
import { ScrollView as GHScrollView } from 'react-native-gesture-handler';
import { SafeAreaView } from 'react-native-safe-area-context';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useNavigation } from '@react-navigation/native';
import { LinearGradient } from 'expo-linear-gradient';
import AsyncStorage from '@react-native-async-storage/async-storage';

import { chatAPI, pricingAPI } from '../services/api';
import { storage } from '../services/storage';
import { useCredits } from '../credits/CreditContext';
import MonthlyAccordion from './MonthlyAccordion';
import NativeSelectorChip from './Common/NativeSelectorChip';
import { API_BASE_URL } from '../utils/constants';
import { useTheme } from '../context/ThemeContext';
import ConfirmCreditsModal from './ConfirmCreditsModal';
import { useTranslation } from 'react-i18next';
import { generateEventTimelinePDF, sharePDFOnWhatsApp, getLogoDataUriForModule } from '../utils/pdfGenerator';
import { trackEvent } from '../utils/analytics';
import { useAnalytics } from '../hooks/useAnalytics';
import { userFacingTimelineError } from '../utils/timelineUserErrors';
import { useAuthGate } from '../auth/AuthGateContext';

const { width } = Dimensions.get('window');

// Layout constants for FlatList
const START_YEAR_FALLBACK = 1950;
const END_YEAR = 2100;
const ITEM_WIDTH = 80;
const ITEM_GAP = 12;
const TOTAL_ITEM_SIZE = ITEM_WIDTH + ITEM_GAP;
const SIDE_PADDING = (width - ITEM_WIDTH) / 2;

const extractBirthYear = (data) => {
  if (!data || typeof data !== 'object') return null;
  const candidates = [
    data.date,
    data.birth_date,
    data.dob,
    data.birthDate,
    data.birth_date_iso,
    data.birth_details?.date,
    data.birthDetails?.date,
  ];
  for (const raw of candidates) {
    if (!raw) continue;
    const s = String(raw).trim();
    // Prefer leading YYYY forms: 1980-04-02 / 1980/04/02 / 1980.04.02
    let m = s.match(/^(\d{4})[-/.]/);
    if (!m) {
      // Fallback: any 4-digit year in sensible range
      m = s.match(/\b(19\d{2}|20\d{2})\b/);
    }
    if (!m) continue;
    const y = Number(m[1]);
    if (Number.isFinite(y) && y >= 1900 && y <= END_YEAR) return y;
  }
  return null;
};

const resolveBirthChartId = (data) => {
  const raw = data?.id ?? data?.chart_id ?? data?.birth_chart_id ?? null;
  const parsed = Number(raw);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : null;
};

const YEARLY_TIMELINE_PENDING_KEY = 'eventScreenYearlyPendingJob';
const CACHED_YEARS_STORAGE_PREFIX = 'eventScreenCachedYears:';

const mergeCachedYearList = (...lists) => {
  const merged = new Set();
  lists.flat().forEach((value) => {
    const year = Number(value);
    if (Number.isFinite(year)) merged.add(year);
  });
  return [...merged].sort((a, b) => a - b);
};

const CHIP_CACHED = {
  dark: { bg: '#166534', border: '#22c55e', text: '#ecfdf5' },
  light: { bg: '#dcfce7', border: '#16a34a', text: '#14532d' },
};

export default function EventScreen({ route }) {
  useAnalytics('EventScreen');
  const navigation = useNavigation();
  const { t } = useTranslation();
  const { credits, fetchBalance } = useCredits();
  const { requireAuthForPaid } = useAuthGate();
  const { theme, colors } = useTheme();
  const isIOS = Platform.OS === 'ios';
  const onPrimaryText = '#ffffff';
  const cachedChip = CHIP_CACHED[theme] || CHIP_CACHED.dark;
  const bgGradient = theme === 'dark'
    ? [colors.gradientStart, colors.gradientMid, colors.gradientEnd]
    : [colors.gradientStart, colors.gradientMid, colors.gradientEnd];
  const continueGradient = [colors.primary, theme === 'dark' ? '#ea580c' : '#c2410c'];
  const quickSelectButtonStyle = {
    backgroundColor: colors.surface,
    borderColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.24)' : colors.cardBorder,
    borderWidth: 1.5,
  };
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());
  const deviceNow = React.useMemo(() => new Date(), []);
  const deviceYear = deviceNow.getFullYear();
  const deviceMonth = deviceNow.getMonth() + 1;
  const deviceDay = deviceNow.getDate();
  const recommendedMonth = deviceDay <= 15 ? deviceMonth : Math.min(deviceMonth + 1, 12);
  const deviceMonths = React.useMemo(() => Array.from({ length: 12 }, (_, i) => i + 1), []);
  const [readingMode, setReadingMode] = useState('yearly'); // 'yearly' | 'monthly'
  const [selectedMonth, setSelectedMonth] = useState(recommendedMonth);
  const [monthlyData, setMonthlyData] = useState(null);
  
  // Loading states
  const [loadingMonthly, setLoadingMonthly] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [analysisStarted, setAnalysisStarted] = useState(false);
  const [creditCost, setCreditCost] = useState(100);
  const [creditCostOriginal, setCreditCostOriginal] = useState(null);
  const [loadingMessageIndex, setLoadingMessageIndex] = useState(0);
  const [loadingProgress, setLoadingProgress] = useState(0);
  const [timelineProgress, setTimelineProgress] = useState({ monthsReady: 0, totalMonths: 12, completedQuarters: 0 });
  const progressIntervalRef = useRef(null);
  const [nativeName, setNativeName] = useState('');
  const [birthData, setBirthData] = useState(null);
  const [showRegenerateModal, setShowRegenerateModal] = useState(false);
  const [isExportingPdf, setIsExportingPdf] = useState(false);
  const [cachedYears, setCachedYears] = useState([]);
  const [cachedMonths, setCachedMonths] = useState([]);
  const cachedYearsForChartRef = useRef(null);
  const cachedYearsLoadPromiseRef = useRef(null);

  const persistCachedYearsLocal = useCallback(async (chartId, years) => {
    if (!chartId || !Array.isArray(years)) return;
    try {
      await AsyncStorage.setItem(
        `${CACHED_YEARS_STORAGE_PREFIX}${chartId}`,
        JSON.stringify(mergeCachedYearList(years))
      );
    } catch (error) {
      if (__DEV__) {
        console.warn('[EventScreen] persist cached years', error?.message || error);
      }
    }
  }, []);

  const hydrateCachedYearsFromStorage = useCallback(async (chartId) => {
    if (!chartId) return null;
    try {
      const raw = await AsyncStorage.getItem(`${CACHED_YEARS_STORAGE_PREFIX}${chartId}`);
      if (!raw) return null;
      const parsed = JSON.parse(raw);
      return Array.isArray(parsed) ? mergeCachedYearList(parsed) : null;
    } catch {
      return null;
    }
  }, []);

  const markYearCached = useCallback((year) => {
    const y = Number(year);
    if (!Number.isFinite(y)) return;
    setCachedYears((prev) => {
      const next = mergeCachedYearList(prev, [y]);
      const chartId = cachedYearsForChartRef.current;
      if (chartId) persistCachedYearsLocal(chartId, next);
      return next;
    });
  }, [persistCachedYearsLocal]);
  const yearSliderRef = useRef(null);
  const monthSliderRef = useRef(null);
  const loadingIntervalRef = useRef(null);
  /** Yearly timeline async job: must use refs so timeout/poll always clear (no stale React state). */
  const timelinePollRef = useRef(null);
  const timelineTimeoutRef = useRef(null);
  const TIMELINE_POLL_MS = 3000;
  const TIMELINE_MAX_WAIT_MS = 15 * 60 * 1000;
  const [showEventCreditsModal, setShowEventCreditsModal] = useState(false);
  const [pendingAction, setPendingAction] = useState(null); // 'generate' | 'regenerate' | null
  const [continueChecking, setContinueChecking] = useState(false);

  const loadingMessages = [
    { icon: '🌟', text: 'Analyzing planetary positions...' },
    { icon: '🔮', text: `Calculating dasha periods for ${selectedYear}...` },
    { icon: '✨', text: 'Examining transit patterns...' },
    { icon: '🌙', text: isIOS ? 'Reviewing the timing calendar...' : 'Consulting the cosmic calendar...' },
    { icon: '⭐', text: 'Mapping celestial influences...' },
    { icon: '🪐', text: 'Decoding planetary alignments...' },
    { icon: '💫', text: 'Synthesizing astrological insights...' },
    { icon: '🌠', text: 'Studying nakshatra transits...' },
    { icon: '☀️', text: 'Analyzing solar influences...' },
    { icon: '🌕', text: 'Examining lunar cycles...' },
    { icon: '♃', text: 'Calculating Jupiter transits...' },
    { icon: '♄', text: 'Tracking Saturn movements...' },
    { icon: '♂️', text: 'Assessing Mars energy...' },
    { icon: '♀️', text: 'Evaluating Venus positions...' },
    { icon: '☿', text: 'Analyzing Mercury patterns...' },
    { icon: '🔱', text: 'Computing Rahu-Ketu axis...' },
    { icon: '📊', text: 'Calculating house strengths...' },
    { icon: '🎯', text: isIOS ? 'Identifying key timing windows...' : 'Identifying key life events...' },
    { icon: '🌈', text: 'Mapping yogas and combinations...' },
    { icon: '⚡', text: 'Detecting planetary aspects...' },
    { icon: '🧭', text: 'Determining auspicious periods...' },
    { icon: '📅', text: isIOS ? 'Preparing a chart study...' : 'Analyzing monthly forecasts...' },
    { icon: '🔬', text: 'Examining divisional charts...' },
    { icon: '🎨', text: 'Building your chart summary...' },
    { icon: '🌊', text: 'Flowing through time cycles...' },
    { icon: '🔥', text: isIOS ? 'Refining the chart study...' : 'Igniting predictive insights...' },
    { icon: '🌸', text: 'Blooming astrological wisdom...' },
    { icon: '🎭', text: 'Revealing karmic patterns...' },
    { icon: '🗝️', text: isIOS ? 'Opening chart details...' : 'Unlocking celestial secrets...' },
    { icon: '💎', text: isIOS ? 'Polishing the final study...' : 'Polishing the timeline insights...' },
    { icon: '🌺', text: 'Cultivating cosmic clarity...' },
    { icon: '🦋', text: 'Transforming raw data...' },
    { icon: '🌻', text: 'Growing your timeline...' },
    { icon: '🎪', text: 'Orchestrating planetary dance...' },
    { icon: '🏔️', text: 'Scaling astrological peaks...' },
    { icon: '🌅', text: 'Dawning new insights...' },
    { icon: '🎼', text: 'Composing cosmic symphony...' },
    { icon: '🔭', text: isIOS ? 'Reviewing your chart context...' : 'Reviewing the timing context...' },
    { icon: '🌌', text: 'Navigating the cosmos...' },
    { icon: '✅', text: isIOS ? 'Finalizing your chart study...' : 'Finalizing the timing study...' }
  ];

  const getYearlyPendingPayload = useCallback((jobId, year, birthChartId, startedAt = new Date().toISOString()) => ({
    jobId,
    year: Number(year),
    birthChartId: Number(birthChartId),
    startedAt,
  }), []);

  const saveYearlyPendingJob = useCallback(async (payload) => {
    try {
      await AsyncStorage.setItem(YEARLY_TIMELINE_PENDING_KEY, JSON.stringify(payload));
    } catch (error) {
      console.warn('[EventScreen] save pending yearly job', error?.message || error);
    }
  }, []);

  const loadYearlyPendingJob = useCallback(async () => {
    try {
      const raw = await AsyncStorage.getItem(YEARLY_TIMELINE_PENDING_KEY);
      if (!raw) return null;
      return JSON.parse(raw);
    } catch (error) {
      console.warn('[EventScreen] load pending yearly job', error?.message || error);
      return null;
    }
  }, []);

  const clearYearlyPendingJob = useCallback(async () => {
    try {
      await AsyncStorage.removeItem(YEARLY_TIMELINE_PENDING_KEY);
    } catch (error) {
      console.warn('[EventScreen] clear pending yearly job', error?.message || error);
    }
  }, []);

  const startYearlyLoadingUi = useCallback((startedAtInput = new Date().toISOString()) => {
    const startedAtMs = new Date(startedAtInput || Date.now()).getTime();
    const safeStartedAt = Number.isFinite(startedAtMs) ? startedAtMs : Date.now();
    const elapsedMs = Math.max(0, Date.now() - safeStartedAt);
    const initialMessageIndex = Math.floor(elapsedMs / 3000) % loadingMessages.length;
    setAnalysisStarted(true);
    setLoadingMonthly(true);
    setLoadingMessageIndex(initialMessageIndex);
    setLoadingProgress(elapsedMs <= 100000 ? (elapsedMs / 100000) * 90 : -1);

    loadingIntervalRef.current = setInterval(() => {
      setLoadingMessageIndex((prev) => (prev + 1) % loadingMessages.length);
    }, 3000);

    let elapsed = elapsedMs;
    progressIntervalRef.current = setInterval(() => {
      elapsed += 100;
      if (elapsed <= 100000) {
        setLoadingProgress((elapsed / 100000) * 90);
      } else {
        setLoadingProgress(-1);
      }
    }, 100);
  }, [loadingMessages.length]);

  // Get birth data from storage
  const getBirthDetails = async () => {
    try {
      return await storage.getBirthDetails();
    } catch (error) {
      console.error('Error getting birth details:', error);
      return null;
    }
  };

  // Load native name and birth data on mount
  useEffect(() => {
    const loadBirthData = async () => {
      const birthData = await getBirthDetails();
      if (__DEV__) {
        console.log('[EventScreen] birthData from storage:', {
          keys: birthData ? Object.keys(birthData) : null,
          id: birthData?.id,
          name: birthData?.name,
          date: birthData?.date,
          birth_date: birthData?.birth_date,
          dob: birthData?.dob,
          birth_details_date: birthData?.birth_details?.date,
        });
      }
      if (!birthData?.name) {
        navigation.replace('BirthProfileIntro', { returnTo: 'EventScreen' });
        return;
      }
      setNativeName(birthData.name.substring(0, 7));
      setBirthData(birthData);
      const chartId = resolveBirthChartId(birthData);
      if (chartId) {
        cachedYearsForChartRef.current = chartId;
        const hydrated = await hydrateCachedYearsFromStorage(chartId);
        if (hydrated?.length) {
          setCachedYears(hydrated);
        }
      }
    };
    loadBirthData();
  }, [hydrateCachedYearsFromStorage, navigation]);

  // Fetch credit cost (user-discounted via my-pricing when logged in)
  useEffect(() => {
    const fetchCreditCost = async () => {
      try {
        const response = await pricingAPI.getPricing();
        const data = response?.data || response;
        const cost = data?.pricing?.events;
        const original = data?.pricing_original?.events;
        if (cost != null) {
          setCreditCost(Number(cost));
          setCreditCostOriginal(original != null ? Number(original) : null);
        }
      } catch (error) {
        console.error('❌ Error fetching credit cost:', {
          message: error.message,
          status: error.response?.status,
          data: error.response?.data,
          url: error.config?.url
        });
      }
    };
    fetchCreditCost();
  }, []);

  const stopEventTimelineJob = useCallback((opts = {}) => {
    if (timelinePollRef.current) {
      clearInterval(timelinePollRef.current);
      timelinePollRef.current = null;
    }
    if (timelineTimeoutRef.current) {
      clearTimeout(timelineTimeoutRef.current);
      timelineTimeoutRef.current = null;
    }
    if (loadingIntervalRef.current) {
      clearInterval(loadingIntervalRef.current);
      loadingIntervalRef.current = null;
    }
    if (progressIntervalRef.current) {
      clearInterval(progressIntervalRef.current);
      progressIntervalRef.current = null;
    }
    setLoadingMonthly(false);
    if (opts.resetAnalysisStarted) setAnalysisStarted(false);
  }, []);

  const tryLoadCachedYearlyTimeline = useCallback(
    async (y) => {
      try {
        const bd = await getBirthDetails();
        if (!bd?.id) return false;
        const res = await chatAPI.getCachedMonthlyEvents({
          ...bd,
          selectedYear: y,
          birth_chart_id: bd.id,
        });
        if (res.data?.cached && res.data?.data) {
          setMonthlyData(res.data.data);
          markYearCached(y);
          await clearYearlyPendingJob();
          trackEvent('yearly_timeline_delivered', {
            year: Number(y),
            source: 'event_screen',
            mode: 'cached',
          });
          await fetchBalance();
          return true;
        }
      } catch (e) {
        console.warn('[EventScreen] cache recovery', e?.message || e);
      }
      return false;
    },
    [clearYearlyPendingJob, fetchBalance, markYearCached]
  );

  const attachYearlyTimelinePolling = useCallback((jobId, year, startedAt = new Date().toISOString()) => {
    let outcomeHandled = false;
    const takeOutcome = () => {
      if (outcomeHandled) return false;
      outcomeHandled = true;
      return true;
    };

    const finishSuccess = async (data, mode = 'poll_completed') => {
      if (!takeOutcome()) return;
      stopEventTimelineJob();
      setMonthlyData(data);
      markYearCached(year);
      await clearYearlyPendingJob();
      trackEvent('yearly_timeline_delivered', {
        year: Number(year),
        source: 'event_screen',
        mode,
      });
      fetchBalance();
    };

    const onPollFailure = async (message) => {
      if (!takeOutcome()) return;
      stopEventTimelineJob({ resetAnalysisStarted: false });
      await clearYearlyPendingJob();
      const recovered = await tryLoadCachedYearlyTimeline(year);
      if (recovered) {
        Alert.alert(
          t('eventScreen.timelineRecoveredTitle', 'Timeline ready'),
          t(
            'eventScreen.timelineRecoveredBody',
            'Loaded your saved timeline from the server.'
          )
        );
        return;
      }
      const raw = message != null ? String(message).trim() : '';
      const safeBody = raw
        ? userFacingTimelineError(raw)
        : t(
            'eventScreen.timelineStoppedBody',
            'The analysis may still be running. Wait a minute, then tap your year again, or open this screen again to load saved results without spending credits again.'
          );
      Alert.alert(
        t('eventScreen.timelineStoppedTitle', 'Could not finish loading'),
        safeBody,
        [
          {
            text: t('eventScreen.tryLoadSaved', 'Load saved'),
            onPress: async () => {
              const ok = await tryLoadCachedYearlyTimeline(year);
              if (!ok) {
                Alert.alert(
                  t('eventScreen.noSavedYetTitle', 'No saved result yet'),
                  t(
                    'eventScreen.noSavedYetBody',
                    'Try again in a little while if the study is still running.'
                  )
                );
              }
            },
          },
          { text: t('common.ok', 'OK'), style: 'cancel' },
        ]
      );
      setAnalysisStarted(false);
    };

    timelinePollRef.current = setInterval(async () => {
      try {
        const statusResponse = await chatAPI.getMonthlyEventsStatus(jobId);
        const status = statusResponse.data.status;
        const partialData = statusResponse.data?.partial_data;

        if (partialData && Array.isArray(partialData.monthly_predictions)) {
          setMonthlyData((prev) => ({
            ...(prev || {}),
            macro_trends: partialData.macro_trends || prev?.macro_trends || [],
            monthly_predictions: partialData.monthly_predictions || [],
          }));
          setTimelineProgress({
            monthsReady: Number(statusResponse.data?.months_ready || partialData.monthly_predictions.length || 0),
            totalMonths: 12,
            completedQuarters: Number(
              statusResponse.data?.completed_quarters || partialData.completed_quarters || 0
            ),
          });
        }

        if (status === 'completed' && statusResponse.data.data) {
          await finishSuccess(statusResponse.data.data);
        } else if (status === 'failed') {
          await onPollFailure(statusResponse.data.error || 'Analysis failed');
        }
      } catch (pollError) {
        await onPollFailure(
          pollError?.response?.data?.detail ||
            pollError?.message ||
            'Connection error while checking status.'
        );
      }
    }, TIMELINE_POLL_MS);

    const elapsedMs = Math.max(0, Date.now() - new Date(startedAt || Date.now()).getTime());
    const remainingMs = Math.max(5000, TIMELINE_MAX_WAIT_MS - elapsedMs);
    timelineTimeoutRef.current = setTimeout(async () => {
      if (timelinePollRef.current) {
        clearInterval(timelinePollRef.current);
        timelinePollRef.current = null;
      }
      timelineTimeoutRef.current = null;
      if (outcomeHandled) return;
      try {
        const last = await chatAPI.getMonthlyEventsStatus(jobId);
        if (last.data?.status === 'completed' && last.data?.data) {
          await finishSuccess(last.data.data);
          return;
        }
      } catch (e) {
        console.warn('[EventScreen] final status check', e?.message || e);
      }
      const recovered = await tryLoadCachedYearlyTimeline(year);
      if (recovered) {
        if (!takeOutcome()) return;
        stopEventTimelineJob();
        await clearYearlyPendingJob();
        Alert.alert(
          t('eventScreen.timelineRecoveredTitle', 'Timeline ready'),
          t(
            'eventScreen.timelineLongRunBody',
          'Your study finished — loaded from saved results.'
          )
        );
        return;
      }
      if (!takeOutcome()) return;
      stopEventTimelineJob();
      await clearYearlyPendingJob();
      setAnalysisStarted(false);
      Alert.alert(
        t('eventScreen.timelineTimeoutTitle', 'Still working or interrupted'),
        t(
          'eventScreen.timelineTimeoutBody',
          'We stopped waiting after 15 minutes. If you were charged, your result is usually saved—tap “Load saved”. Otherwise try generating again.'
        ),
        [
          {
            text: t('eventScreen.tryLoadSaved', 'Load saved'),
            onPress: async () => {
              const ok = await tryLoadCachedYearlyTimeline(year);
              if (!ok) {
                Alert.alert(
                  t('eventScreen.noSavedYetTitle', 'No saved result yet'),
                  t(
                    'eventScreen.noSavedYetBody',
                    'Try again in a little while if the study is still running.'
                  )
                );
              }
            },
          },
          { text: t('common.ok', 'OK'), style: 'cancel' },
        ]
      );
    }, remainingMs);
  }, [
    TIMELINE_MAX_WAIT_MS,
    TIMELINE_POLL_MS,
    clearYearlyPendingJob,
    fetchBalance,
    markYearCached,
    stopEventTimelineJob,
    t,
    tryLoadCachedYearlyTimeline,
  ]);

  const resumePendingYearlyJob = useCallback(async (pending, options = {}) => {
    const { preservePartialData = true } = options;
    const birthChartId = resolveBirthChartId(birthData);
    if (
      !pending ||
      !pending.jobId ||
      !birthChartId ||
      Number(pending.birthChartId) !== Number(birthChartId)
    ) {
      return false;
    }
    stopEventTimelineJob();
    if (!preservePartialData) {
      setMonthlyData(null);
      setTimelineProgress({ monthsReady: 0, totalMonths: 12, completedQuarters: 0 });
    }
    setSelectedYear(Number(pending.year) || selectedYear);
    startYearlyLoadingUi(pending.startedAt);
    attachYearlyTimelinePolling(
      pending.jobId,
      Number(pending.year) || selectedYear,
      pending.startedAt
    );
    return true;
  }, [
    attachYearlyTimelinePolling,
    birthData,
    selectedYear,
    startYearlyLoadingUi,
    stopEventTimelineJob,
  ]);

  // Fetch Monthly Guide (AI Powered) with Polling
  const fetchMonthlyGuide = useCallback(async (year) => {
    trackEvent('yearly_timeline_requested', {
      year: Number(year),
      source: 'event_screen',
    });
    stopEventTimelineJob();
    setMonthlyData(null);
    setTimelineProgress({ monthsReady: 0, totalMonths: 12, completedQuarters: 0 });
    const startedAt = new Date().toISOString();
    startYearlyLoadingUi(startedAt);

    try {
      const birthData = await getBirthDetails();
      if (!birthData) {
        await clearYearlyPendingJob();
        stopEventTimelineJob({ resetAnalysisStarted: true });
        return;
      }

      if (!birthData.id) {
        Alert.alert(
          'Error',
          'Birth chart ID not found. Please re-select your birth chart from Select Native screen.'
        );
        await clearYearlyPendingJob();
        stopEventTimelineJob({ resetAnalysisStarted: true });
        return;
      }

      const startResponse = await chatAPI.getMonthlyEvents({
        ...birthData,
        selectedYear: year,
        birth_chart_id: birthData.id,
      });

      if (startResponse.data?.data && !startResponse.data?.job_id) {
        setMonthlyData(startResponse.data.data);
        await clearYearlyPendingJob();
        trackEvent('yearly_timeline_delivered', {
          year: Number(year),
          source: 'event_screen',
          mode: 'direct',
        });
        fetchBalance();
        stopEventTimelineJob();
        return;
      }

      const jobId = startResponse.data?.job_id;
      if (!jobId) {
        throw new Error('No job_id received from server.');
      }
      await saveYearlyPendingJob(getYearlyPendingPayload(jobId, year, birthData.id, startedAt));
      attachYearlyTimelinePolling(jobId, year, startedAt);
    } catch (error) {
      console.error('❌ EventScreen Error Details:', {
        message: error.message,
        status: error.response?.status,
        statusText: error.response?.statusText,
        data: error.response?.data,
        url: error.config?.url,
        headers: error.config?.headers
      });
      
      let errorMessage = 'Failed to load timeline. Please try again.';
      
      if (error.response?.status === 401) {
        errorMessage = 'Session expired. Please login again.';
        Alert.alert('Authentication Error', errorMessage, [
          {
            text: 'Login',
            onPress: () => {
              const { replaceWithLogin } = require('../navigation/replaceWithLogin');
              replaceWithLogin(navigation);
            },
          },
          { text: 'Cancel' }
        ]);
      } else if (error.response?.status === 402) {
        errorMessage = 'You need more credits for this analysis.';
        Alert.alert('Insufficient Credits', errorMessage, [
          { text: 'Get Credits', onPress: () => navigation.navigate('Credits') },
          { text: 'OK' }
        ]);
      } else if (error.response?.status === 500) {
        errorMessage = 'Server error. Please contact support or try again later.';
        Alert.alert('Server Error', errorMessage);
      } else if (error.message === 'Network Error' || !error.response) {
        errorMessage = 'Cannot connect to server. Check your internet connection.';
        Alert.alert('Network Error', errorMessage);
      } else {
        Alert.alert('Error', errorMessage + '\n\nDetails: ' + (error.response?.data?.detail || error.message));
      }
      
      await clearYearlyPendingJob();
      stopEventTimelineJob({ resetAnalysisStarted: true });
    }
  }, [
    attachYearlyTimelinePolling,
    clearYearlyPendingJob,
    fetchBalance,
    getYearlyPendingPayload,
    navigation,
    startYearlyLoadingUi,
    stopEventTimelineJob,
    t,
    saveYearlyPendingJob,
  ]);

  // Check for cached data when analysis starts or year changes
  useEffect(() => {
    const loadCachedData = async () => {
      if (!analysisStarted) return;
      if (loadingMonthly) return;
      
      if (monthlyData) return;
      
      try {
        const birthData = await getBirthDetails();
        if (!birthData) return;

        const pending = await loadYearlyPendingJob();
        const resumedPending = await resumePendingYearlyJob(pending, { preservePartialData: true });
        if (resumedPending) {
          return;
        }
        
        // console.log('🔍 Checking cache with:', { 
        //   birth_chart_id: birthData.id, 
        //   selectedYear: selectedYear,
        //   name: birthData.name 
        // });
        
        const cacheResponse = await chatAPI.getCachedMonthlyEvents({
          ...birthData,
          selectedYear: selectedYear,
          birth_chart_id: birthData.id
        });
        
        // console.log('📦 Cache response:', cacheResponse.data);
        
        if (cacheResponse.data?.cached && cacheResponse.data?.data) {
          setMonthlyData(cacheResponse.data.data);
          markYearCached(selectedYear);
        } else {
          // No cached data - check credits before generating
          const refreshedCredits = await fetchBalance();
          const actualCredits = refreshedCredits ?? credits;

          if (actualCredits < creditCost) {
            Alert.alert('Insufficient Credits', `You need ${creditCost} credits for this analysis. You have ${actualCredits} credits.`, [
              { text: 'Get Credits', onPress: () => navigation.navigate('Credits') },
              { text: 'Cancel', onPress: () => setAnalysisStarted(false) }
            ]);
            return;
          }
          
          fetchMonthlyGuide(selectedYear);
        }
      } catch (error) {
        // Do not auto-start paid generation on cache failure — user may have 0 credits but a saved result.
        const recovered = await tryLoadCachedYearlyTimeline(selectedYear);
        if (!recovered) {
          console.warn('[EventScreen] loadCachedData failed', error?.message || error);
          const startPaidGenerationIfAllowed = async () => {
            try {
              const refreshedCredits = await fetchBalance();
              const actualCredits = refreshedCredits ?? credits;
              if (actualCredits < creditCost) {
                Alert.alert(
                  'Insufficient Credits',
                  `You need ${creditCost} credits for this analysis. You have ${actualCredits} credits.`,
                  [
                    { text: 'Get Credits', onPress: () => navigation.navigate('Credits') },
                    { text: 'OK' },
                  ]
                );
                return;
              }
              fetchMonthlyGuide(selectedYear);
            } catch (e) {
              Alert.alert('Error', e?.message || 'Could not verify credits. Please try again.');
            }
          };
          Alert.alert(
            'Could not load',
            'We could not reach the server to check for a saved timeline. Go back and try again (no credits) if you already paid, or start a new analysis if you have credits.',
            [
              { text: 'Go back', style: 'cancel', onPress: () => setAnalysisStarted(false) },
              { text: 'Generate new report', onPress: () => { startPaidGenerationIfAllowed(); } },
            ]
          );
        }
      }
    };
    
    if (analysisStarted) {
      loadCachedData();
    }
  }, [
    selectedYear,
    analysisStarted,
    loadingMonthly,
    loadYearlyPendingJob,
    resumePendingYearlyJob,
    tryLoadCachedYearlyTimeline,
    creditCost,
    credits,
    fetchMonthlyGuide,
    fetchBalance,
    markYearCached,
    navigation,
  ]);

  useEffect(() => {
    return () => {
      if (loadingIntervalRef.current) {
        clearInterval(loadingIntervalRef.current);
        loadingIntervalRef.current = null;
      }
      if (progressIntervalRef.current) {
        clearInterval(progressIntervalRef.current);
        progressIntervalRef.current = null;
      }
      if (timelinePollRef.current) {
        clearInterval(timelinePollRef.current);
        timelinePollRef.current = null;
      }
      if (timelineTimeoutRef.current) {
        clearTimeout(timelineTimeoutRef.current);
        timelineTimeoutRef.current = null;
      }
    };
  }, []);

  const onRefresh = useCallback(() => {
    // Prevent accidental regeneration - do nothing on pull-to-refresh
    setRefreshing(false);
  }, []);

  const startYear = React.useMemo(() => {
    const parsed = extractBirthYear(birthData);
    if (__DEV__) {
      console.log('[EventScreen] startYear resolution:', {
        parsed,
        fallback: START_YEAR_FALLBACK,
        date: birthData?.date,
        birth_date: birthData?.birth_date,
        dob: birthData?.dob,
        birth_details_date: birthData?.birth_details?.date,
      });
    }
    if (parsed != null) return parsed;
    return START_YEAR_FALLBACK;
  }, [birthData]);

  const years = React.useMemo(
    () => Array.from({ length: Math.max(1, END_YEAR - startYear + 1) }, (_, i) => startYear + i),
    [startYear]
  );
  const cachedYearSet = React.useMemo(() => new Set((cachedYears || []).map((y) => Number(y))), [cachedYears]);
  const cachedMonthSet = React.useMemo(() => new Set((cachedMonths || []).map((m) => Number(m))), [cachedMonths]);

  const getYearChipStyles = useCallback(
    (item) => {
      const isCached = cachedYearSet.has(Number(item));
      const isSelected = selectedYear === item;
      return [
        styles.yearChip,
        { backgroundColor: colors.cardBackground, borderColor: colors.cardBorder, width: ITEM_WIDTH },
        isCached && !isSelected && {
          backgroundColor: cachedChip.bg,
          borderColor: cachedChip.border,
        },
        isSelected && { backgroundColor: colors.primary, borderColor: colors.primary },
      ];
    },
    [cachedYearSet, cachedChip.bg, cachedChip.border, colors.cardBackground, colors.cardBorder, colors.primary, selectedYear]
  );

  const getYearChipTextColor = useCallback(
    (item) => {
      const isCached = cachedYearSet.has(Number(item));
      const isSelected = selectedYear === item;
      if (isSelected) return onPrimaryText;
      if (isCached) return cachedChip.text;
      return colors.text;
    },
    [cachedYearSet, cachedChip.text, colors.text, onPrimaryText, selectedYear]
  );

  const getMonthChipStyles = useCallback(
    (item) => {
      const isCached = cachedMonthSet.has(Number(item));
      const isSelected = selectedMonth === item;
      return [
        styles.monthChip,
        { backgroundColor: colors.cardBackground, borderColor: colors.cardBorder, width: ITEM_WIDTH },
        isCached && !isSelected && {
          backgroundColor: cachedChip.bg,
          borderColor: cachedChip.border,
        },
        isSelected && { backgroundColor: colors.primary, borderColor: colors.primary },
      ];
    },
    [
      cachedMonthSet,
      cachedChip.bg,
      cachedChip.border,
      colors.cardBackground,
      colors.cardBorder,
      colors.primary,
      selectedMonth,
    ]
  );

  const getMonthChipTextColor = useCallback(
    (item) => {
      const isCached = cachedMonthSet.has(Number(item));
      const isSelected = selectedMonth === item;
      if (isSelected) return onPrimaryText;
      if (isCached) return cachedChip.text;
      return colors.text;
    },
    [cachedMonthSet, cachedChip.text, colors.text, onPrimaryText, selectedMonth]
  );

  const loadCachedYears = useCallback(async () => {
    if (cachedYearsLoadPromiseRef.current) {
      return cachedYearsLoadPromiseRef.current;
    }

    const run = async () => {
      const bd = resolveBirthChartId(birthData) ? birthData : await getBirthDetails();
      const birthChartId = resolveBirthChartId(bd);
      if (!birthChartId) return;

      if (cachedYearsForChartRef.current !== birthChartId) {
        cachedYearsForChartRef.current = birthChartId;
        const hydrated = await hydrateCachedYearsFromStorage(birthChartId);
        if (hydrated?.length) {
          setCachedYears(hydrated);
        }
      }

      let apiYears = [];
      try {
        const res = await chatAPI.getCachedMonthlyEventYears(birthChartId);
        const yearsFromApi = Array.isArray(res?.data?.years)
          ? res.data.years
          : Array.isArray(res?.years)
            ? res.years
            : [];
        apiYears = mergeCachedYearList(yearsFromApi);
        if (apiYears.length > 0) {
          setCachedYears(apiYears);
          await persistCachedYearsLocal(birthChartId, apiYears);
          if (__DEV__) {
            console.log('[EventScreen] cached years from API:', apiYears);
          }
          return;
        }
      } catch (e) {
        if (__DEV__) {
          console.warn('[EventScreen] cached-years API failed, probing:', e?.message || e);
        }
      }

      // Fallback: probe /cached for nearby years (batched to avoid flooding the server).
      const probeStart = Math.max(startYear, deviceYear - 15);
      const probeEnd = Math.min(END_YEAR, deviceYear + 15);
      const probeYears = Array.from(
        { length: Math.max(0, probeEnd - probeStart + 1) },
        (_, i) => probeStart + i
      );
      if (probeYears.length === 0) return;

      const probed = [];
      const PROBE_BATCH = 6;
      for (let i = 0; i < probeYears.length; i += PROBE_BATCH) {
        const batch = probeYears.slice(i, i + PROBE_BATCH);
        const checks = await Promise.all(
          batch.map(async (y) => {
            try {
              const r = await chatAPI.getCachedMonthlyEvents({
                ...bd,
                selectedYear: y,
                birth_chart_id: birthChartId,
              });
              return r?.data?.cached ? y : null;
            } catch {
              return null;
            }
          })
        );
        probed.push(...checks.filter((y) => Number.isFinite(y)));
      }

      if (probed.length > 0) {
        let mergedForStorage = [];
        setCachedYears((prev) => {
          mergedForStorage = mergeCachedYearList(prev, probed, apiYears);
          return mergedForStorage;
        });
        await persistCachedYearsLocal(birthChartId, mergedForStorage);
        if (__DEV__) {
          console.log('[EventScreen] cached years from probe:', probed);
        }
      } else if (__DEV__) {
        console.log('[EventScreen] probe found no cached years in window', {
          probeStart,
          probeEnd,
          birthChartId,
        });
      }
    };

    cachedYearsLoadPromiseRef.current = run().finally(() => {
      cachedYearsLoadPromiseRef.current = null;
    });
    return cachedYearsLoadPromiseRef.current;
  }, [birthData, deviceYear, hydrateCachedYearsFromStorage, persistCachedYearsLocal, startYear]);

  useEffect(() => {
    loadCachedYears();
  }, [loadCachedYears]);

  useEffect(() => {
    const unsubscribe = navigation.addListener('focus', () => {
      loadCachedYears();
      (async () => {
        const pending = await loadYearlyPendingJob();
        if (monthlyData?.monthly_predictions?.length || loadingMonthly) {
          return;
        }
        const resumed = await resumePendingYearlyJob(pending, { preservePartialData: true });
        if (resumed) {
          setReadingMode('yearly');
        }
      })();
    });
    return unsubscribe;
  }, [
    loadCachedYears,
    loadYearlyPendingJob,
    loadingMonthly,
    monthlyData,
    navigation,
    resumePendingYearlyJob,
  ]);

  useEffect(() => {
    let cancelled = false;
    const loadCachedMonths = async () => {
      const birthChartId = resolveBirthChartId(birthData);
      if (!birthChartId || !selectedYear) {
        if (!cancelled) setCachedMonths([]);
        return;
      }
      try {
        const checks = await Promise.all(
          Array.from({ length: 12 }, (_, i) => i + 1).map(async (m) => {
            try {
              const res = await chatAPI.getCachedMonthlyEvents({
                ...birthData,
                selectedYear,
                selectedMonth: m,
                birth_chart_id: birthChartId,
              });
              return res?.data?.cached ? m : null;
            } catch {
              return null;
            }
          })
        );
        if (!cancelled) {
          setCachedMonths(checks.filter((m) => Number.isFinite(m)));
        }
      } catch {
        if (!cancelled) setCachedMonths([]);
      }
    };
    loadCachedMonths();
    return () => {
      cancelled = true;
    };
  }, [birthData, selectedYear]);

  const scrollYearStripToIndex = useCallback((index, animated) => {
    const ref = yearSliderRef.current;
    if (!ref) return;
    const padding = SIDE_PADDING;
    const itemOffset = padding + index * TOTAL_ITEM_SIZE;
    const desired = itemOffset - (width - ITEM_WIDTH) / 2;
    const contentW = padding * 2 + years.length * TOTAL_ITEM_SIZE;
    const maxScroll = Math.max(0, contentW - width);
    const x = Math.max(0, Math.min(maxScroll, desired));
    ref.scrollTo({ x, animated });
  }, [years.length]);

  const scrollMonthStripToIndex = useCallback((index, animated) => {
    const ref = monthSliderRef.current;
    if (!ref) return;
    const padding = SIDE_PADDING;
    const itemOffset = padding + index * TOTAL_ITEM_SIZE;
    const desired = itemOffset - (width - ITEM_WIDTH) / 2;
    const contentW = padding * 2 + deviceMonths.length * TOTAL_ITEM_SIZE;
    const maxScroll = Math.max(0, contentW - width);
    const x = Math.max(0, Math.min(maxScroll, desired));
    ref.scrollTo({ x, animated });
  }, [deviceMonths.length]);

  useEffect(() => {
    if (analysisStarted) return;
    const index = selectedYear - startYear;
    const t = setTimeout(() => scrollYearStripToIndex(index, false), 100);
    return () => clearTimeout(t);
  }, [analysisStarted, readingMode, selectedYear, scrollYearStripToIndex, startYear]);

  useEffect(() => {
    if (analysisStarted || readingMode !== 'monthly') return;
    const index = Math.max(0, Math.min(deviceMonths.length - 1, selectedMonth - 1));
    const t = setTimeout(() => scrollMonthStripToIndex(index, false), 100);
    return () => clearTimeout(t);
  }, [analysisStarted, readingMode, selectedMonth, deviceMonths.length, scrollMonthStripToIndex]);

  const handleYearChange = (year) => {
    setSelectedYear(year);
    setMonthlyData(null); // Clear data when year changes
    const index = year - startYear;
    scrollYearStripToIndex(index, true);
  };

  const handleMonthChange = (month) => {
    setSelectedMonth(month);
    const index = Math.max(0, Math.min(deviceMonths.length - 1, month - 1));
    scrollMonthStripToIndex(index, true);
  };

  const handleMonthlyContinue = () => {
    trackEvent('monthly_timeline_requested', {
      year: Number(selectedYear),
      month: Number(selectedMonth),
      source: 'event_screen',
    });
    navigation.navigate('MonthlyDeepScreen', { year: selectedYear, month: selectedMonth });
  };

  const navigateToChat = (context, type) => {
    // Build detailed prediction text from context
    console.log('📋 Context data:', JSON.stringify(context, null, 2));
    console.log('📋 Events count:', context.events?.length);
    
    let predictionText = `${context.month} Study:\n\n`;
    
    if (context.events && context.events.length > 0) {
      context.events.forEach((event, idx) => {
        predictionText += `Item ${idx + 1}: ${event.type}\n`;
        predictionText += `${event.prediction}\n`;
        if (event.start_date && event.end_date) {
          predictionText += `Period: ${event.start_date} to ${event.end_date}\n`;
        }
        
        // Include manifestations if available
        if (event.possible_manifestations && event.possible_manifestations.length > 0) {
          predictionText += `\nPossible scenarios (${event.possible_manifestations.length}):\n`;
          event.possible_manifestations.forEach((manifest, mIdx) => {
            const scenario = typeof manifest === 'string' ? manifest : manifest.scenario;
            predictionText += `${mIdx + 1}. ${scenario}\n`;
          });
        }
        predictionText += `\n`;
      });
    }
    
    predictionText += `Please explain these results in more detail.`;
    
    console.log('📋 Final study text:', predictionText);
    
    navigation.navigate('Home', {
      startChat: true,
      initialMessage: predictionText
    });
  };

  const handleExportPdf = async () => {
    if (!monthlyData) return;
    try {
      setIsExportingPdf(true);
      const logoDataUri = await getLogoDataUriForModule(require('../../assets/logo.png'));
      const pdfUri = await generateEventTimelinePDF({
        year: selectedYear,
        nativeName: nativeName || '',
        monthlyData,
        logoDataUri,
      });
      await sharePDFOnWhatsApp(pdfUri);
    } catch (error) {
      console.error('Export PDF error:', error);
      Alert.alert('Export failed', error?.message || 'Could not generate or share PDF.');
    } finally {
      setIsExportingPdf(false);
    }
  };

  const handleContinue = async () => {
    if (continueChecking) return;
    const authOk = await requireAuthForPaid({
      feature: 'life events timeline',
      message: 'Sign in to generate your yearly timeline. Cached timelines reopen free after purchase.',
      resume: { resumeRoute: 'EventScreen', resumeParams: {} },
    });
    if (!authOk) return;
    setContinueChecking(true);
    try {
      const birthData = await getBirthDetails();
      if (!birthData || !birthData.id) {
        Alert.alert('Error', 'Birth chart not found. Please select a birth chart.');
        return;
      }

      const pending = await loadYearlyPendingJob();
      const resumedPending = await resumePendingYearlyJob(pending, { preservePartialData: false });
      if (resumedPending) {
        setReadingMode('yearly');
        return;
      }

      // Green chip = known cached year — skip network cache probe
      if (cachedYearSet.has(Number(selectedYear))) {
        setAnalysisStarted(true);
        return;
      }

      const [cacheResponse, refreshedCredits] = await Promise.all([
        chatAPI.getCachedMonthlyEvents({
          ...birthData,
          selectedYear: selectedYear,
          birth_chart_id: birthData.id,
        }),
        fetchBalance(),
      ]);

      if (cacheResponse.data?.cached) {
        markYearCached(selectedYear);
        setAnalysisStarted(true);
        return;
      }

      const actualCredits = refreshedCredits ?? credits;
      if (actualCredits < creditCost) {
        Alert.alert('Insufficient Credits', `You need ${creditCost} credits for this analysis. You have ${actualCredits} credits.`, [
          { text: 'Get Credits', onPress: () => navigation.navigate('Credits') },
          { text: 'Cancel', style: 'cancel' },
        ]);
        return;
      }
      setPendingAction('generate');
      setShowEventCreditsModal(true);
    } catch (error) {
      console.error('❌ Cache Check Error Details:', {
        message: error.message,
        status: error.response?.status,
        statusText: error.response?.statusText,
        data: error.response?.data,
        url: error.config?.url
      });
      
      if (error.response?.status === 401) {
        Alert.alert('Authentication Error', 'Session expired. Please login again.', [
          {
            text: 'Login',
            onPress: () => {
              const { replaceWithLogin } = require('../navigation/replaceWithLogin');
              replaceWithLogin(navigation);
            },
          },
          { text: 'Cancel' }
        ]);
      } else {
        Alert.alert('Error', 'Failed to check for existing predictions. Please try again.');
      }
    } finally {
      setContinueChecking(false);
    }
  };

  const getMonthName = (monthId) => {
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    return months[monthId - 1] || `Month ${monthId}`;
  };
  const isDescriptiveTrend = (trend) => {
    const t = String(trend || '').replace(/\s+/g, ' ').trim();
    if (!t) return false;
    const wc = t.split(' ').filter(Boolean).length;
    if (wc <= 3 || t.length < 28) return false;
    return true;
  };
  const displayMacroTrends = (monthlyData?.macro_trends || []).filter(isDescriptiveTrend);

  const renderCachedYearsLegend = () => (
    <View style={styles.cachedYearsHintRow}>
      <View style={[styles.cachedYearsLegendDot, { backgroundColor: cachedChip.border }]} />
      <Text style={[styles.cachedYearsHintText, { color: colors.textTertiary }]}>
        {t(
          'eventScreen.cachedHint',
          'Already saved — select and open, no extra credits.'
        )}
      </Text>
    </View>
  );

  const handleRegenerateConfirm = async () => {
    setShowRegenerateModal(false);
    const refreshedCredits = await fetchBalance();
    const actualCredits = refreshedCredits ?? credits;

    if (actualCredits < creditCost) {
      Alert.alert('Insufficient Credits', `You need ${creditCost} credits to regenerate. You have ${actualCredits} credits.`, [
        { text: 'Get Credits', onPress: () => navigation.navigate('Credits') },
        { text: 'Cancel', style: 'cancel' }
      ]);
      return;
    }
    
    setPendingAction('regenerate');
    setShowEventCreditsModal(true);
  };

  const handleEventCreditsConfirm = () => {
    setShowEventCreditsModal(false);
    if (pendingAction === 'generate') {
      setAnalysisStarted(true);
    } else if (pendingAction === 'regenerate') {
      setMonthlyData(null);
      fetchMonthlyGuide(selectedYear);
    }
    setPendingAction(null);
  };

  return (
    <LinearGradient colors={bgGradient} style={{ flex: 1 }}>
      <SafeAreaView style={[styles.container, { backgroundColor: 'transparent' }]}>
      {/* Regenerate Confirmation Modal */}
      <Modal
        visible={showRegenerateModal}
        transparent
        animationType="fade"
        onRequestClose={() => setShowRegenerateModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={[styles.modalContent, { backgroundColor: colors.backgroundSecondary, borderColor: colors.cardBorder }]}>
            <Ionicons name="refresh-circle" size={48} color={colors.primary} style={styles.modalIcon} />
            <Text style={[styles.modalTitle, { color: colors.primary }]}>{t('eventScreen.regenerateTitle', 'Refresh Study?')}</Text>
            <Text style={[styles.modalText, { color: colors.textSecondary }]}>
              {t('eventScreen.regenerateMessage', { cost: creditCost, year: selectedYear })}
            </Text>
            <View style={styles.modalButtons}>
              <TouchableOpacity 
                style={[styles.modalButton, styles.modalButtonCancel, { backgroundColor: colors.cardBackground, borderColor: colors.cardBorder }]} 
                onPress={() => setShowRegenerateModal(false)}
              >
                <Text style={[styles.modalButtonTextCancel, { color: colors.text }]}>{t('eventScreen.cancel', 'Cancel')}</Text>
              </TouchableOpacity>
              <TouchableOpacity 
                style={[styles.modalButton, styles.modalButtonConfirm, { backgroundColor: colors.primary }]} 
                onPress={handleRegenerateConfirm}
              >
                <Text style={[styles.modalButtonTextConfirm, { color: onPrimaryText }]}>{t('eventScreen.confirm', 'Confirm')}</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => analysisStarted ? setAnalysisStarted(false) : navigation.goBack()} style={[styles.backButton, { backgroundColor: colors.surface }]}>
          <Ionicons name="arrow-back" size={24} color={colors.primary} />
        </TouchableOpacity>
        <View style={styles.headerCenter}>
          <Text style={[styles.headerTitle, { color: colors.text }]}>
            {analysisStarted ? t('eventScreen.headerPredictions', { year: selectedYear }) : t('eventScreen.headerTitle', 'Annual Chart Review')}
          </Text>
          {birthData && (
            <NativeSelectorChip 
              birthData={birthData}
              onPress={() => navigation.navigate('SelectNative')}
              maxLength={12}
            />
          )}
        </View>
        <View style={styles.headerRight}>
          {analysisStarted && monthlyData && (
            <TouchableOpacity onPress={() => setShowRegenerateModal(true)} style={[styles.regenerateButton, { backgroundColor: colors.surface, borderColor: colors.cardBorder }]}>
              <Ionicons name="refresh" size={22} color={colors.primary} />
            </TouchableOpacity>
          )}
          {analysisStarted && (
            <TouchableOpacity
              onPress={handleExportPdf}
              disabled={isExportingPdf || !monthlyData}
              style={[styles.settingsButton, { backgroundColor: colors.surface }]}
            >
              {isExportingPdf ? (
                <ActivityIndicator size="small" color={colors.primary} />
              ) : (
                <Ionicons name="document-text-outline" size={24} color={colors.primary} />
              )}
            </TouchableOpacity>
          )}
        </View>
        {!analysisStarted && <View style={styles.headerSpacer} />}
      </View>

      {!analysisStarted ? (
        <ScrollView
          nestedScrollEnabled
          showsVerticalScrollIndicator={false}
          contentContainerStyle={[
            styles.selectionContainer,
            { backgroundColor: 'transparent' },
          ]}
        >
          <Text style={[styles.selectionTitle, { color: colors.text }]}>🌟 {t('eventScreen.chooseReading', 'Choose your chart review')}</Text>
          <Text style={[styles.selectionSubtitle, { color: colors.textSecondary }]}>
            {readingMode === 'yearly'
              ? t('eventScreen.yearlySubtitle', 'You’ll get a year-level chart review with 12 monthly notes. Tap any month to go deeper.')
              : t('eventScreen.monthlySubtitle', 'Pick your month—then we’ll generate a one-month chart review with dasha activation and multiple scenarios.')}
          </Text>

          <View style={styles.modeToggleContainer}>
            <TouchableOpacity
              style={[
                styles.modeToggleButton,
                { backgroundColor: readingMode === 'yearly' ? colors.primary : colors.cardBackground, borderColor: readingMode === 'yearly' ? colors.primary : colors.cardBorder }
              ]}
              onPress={() => setReadingMode('yearly')}
            >
              <Text style={[styles.modeToggleText, { color: readingMode === 'yearly' ? onPrimaryText : colors.text }]}>
                {t('eventScreen.yearlyOverview', 'Whole Year')}
              </Text>
              <Text
                style={[
                  styles.modeToggleSubtext,
                  {
                    color: readingMode === 'yearly' ? 'rgba(255,255,255,0.88)' : colors.textSecondary,
                  },
                ]}
              >
                {t('eventScreen.yearlyOverviewDesc', '12 monthly notes')}
              </Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[
                styles.modeToggleButton,
                { backgroundColor: readingMode === 'monthly' ? colors.primary : colors.cardBackground, borderColor: readingMode === 'monthly' ? colors.primary : colors.cardBorder }
              ]}
              onPress={() => setReadingMode('monthly')}
            >
              <Text style={[styles.modeToggleText, { color: readingMode === 'monthly' ? onPrimaryText : colors.text }]}>
                {t('eventScreen.monthlyDeepDive', 'One Month')}
              </Text>
              <Text
                style={[
                  styles.modeToggleSubtext,
                  {
                    color: readingMode === 'monthly' ? 'rgba(255,255,255,0.88)' : colors.textSecondary,
                  },
                ]}
              >
                {t('eventScreen.monthlyDeepDiveDesc', 'Deep detail for your month')}
              </Text>
            </TouchableOpacity>
          </View>
          
          {/* Year Picker - Horizontal Chips */}
          {readingMode === 'yearly' ? (
            <>
              {/* Year Picker - Horizontal Chips */}
              <View style={styles.yearChipsContainer}>
                <GHScrollView
                  ref={yearSliderRef}
                  horizontal
                  nestedScrollEnabled
                  showsHorizontalScrollIndicator={false}
                  decelerationRate="fast"
                  contentContainerStyle={styles.yearChipsContent}
                >
                  {years.map((item) => (
                    <View key={item} style={{ width: TOTAL_ITEM_SIZE }}>
                      <TouchableOpacity
                        style={getYearChipStyles(item)}
                        onPress={() => handleYearChange(item)}
                      >
                        <Text style={[styles.yearChipText, { color: getYearChipTextColor(item) }]}>
                          {item}
                        </Text>
                      </TouchableOpacity>
                    </View>
                  ))}
                </GHScrollView>
              </View>

              {/* Quick Select */}
              <View style={styles.quickSelectContainer}>
                <TouchableOpacity
                  style={[styles.quickSelectButton, quickSelectButtonStyle]}
                  onPress={() => handleYearChange(deviceYear)}
                >
                  <Text style={[styles.quickSelectText, { color: colors.text }]}>{t('eventScreen.thisYear', 'This Year')}</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={[styles.quickSelectButton, quickSelectButtonStyle]}
                  onPress={() => handleYearChange(deviceYear + 1)}
                >
                  <Text style={[styles.quickSelectText, { color: colors.text }]}>{t('eventScreen.nextYear', 'Next Year')}</Text>
                </TouchableOpacity>
              </View>
              {renderCachedYearsLegend()}
            </>
          ) : (
            <>
              <Text style={[styles.sectionSubtitle, { color: colors.textSecondary, marginTop: 8, marginBottom: 12 }]}>
                {t('eventScreen.pickMonth', `Pick a month in ${selectedYear}`)}
              </Text>
              <View style={styles.yearChipsContainer}>
                <GHScrollView
                  ref={yearSliderRef}
                  horizontal
                  nestedScrollEnabled
                  showsHorizontalScrollIndicator={false}
                  decelerationRate="fast"
                  contentContainerStyle={styles.yearChipsContent}
                >
                  {years.map((item) => (
                    <View key={item} style={{ width: TOTAL_ITEM_SIZE }}>
                      <TouchableOpacity
                        style={getYearChipStyles(item)}
                        onPress={() => handleYearChange(item)}
                      >
                        <Text style={[styles.yearChipText, { color: getYearChipTextColor(item) }]}>
                          {item}
                        </Text>
                      </TouchableOpacity>
                    </View>
                  ))}
                </GHScrollView>
              </View>
              {renderCachedYearsLegend()}
              <View style={styles.monthChipsContainer}>
                <GHScrollView
                  ref={monthSliderRef}
                  horizontal
                  nestedScrollEnabled
                  showsHorizontalScrollIndicator={false}
                  decelerationRate="fast"
                  contentContainerStyle={styles.monthChipsContent}
                >
                  {deviceMonths.map((item) => (
                    <View key={item} style={{ width: ITEM_WIDTH + ITEM_GAP }}>
                      <TouchableOpacity
                        style={getMonthChipStyles(item)}
                        onPress={() => handleMonthChange(item)}
                      >
                        <Text style={[styles.monthChipText, { color: getMonthChipTextColor(item) }]}>
                          {getMonthName(item)}
                        </Text>
                      </TouchableOpacity>
                    </View>
                  ))}
                </GHScrollView>
              </View>
            </>
          )}

          {/* What's Included */}
          <View style={[styles.featuresContainer, { backgroundColor: colors.cardBackground, borderColor: colors.cardBorder }]}>
            <Text style={[styles.featuresTitle, { color: colors.text }]}>{t('eventScreen.whatsIncluded', "What you'll see:")}</Text>
            <View style={styles.featureItem}>
              <Ionicons name="checkmark-circle" size={20} color={colors.primary} />
              <Text style={[styles.featureText, { color: colors.text }]}>
                {readingMode === 'yearly'
                  ? t('eventScreen.monthlyForecasts', '12 Monthly Chart Notes')
                  : t('eventScreen.oneMonthDeep', 'One Month Chart Review')}
              </Text>
            </View>
            <View style={styles.featureItem}>
              <Ionicons name="checkmark-circle" size={20} color={colors.primary} />
              <Text style={[styles.featureText, { color: colors.text }]}>{t('eventScreen.majorLifeEvents', 'Key timing themes')}</Text>
            </View>
            <View style={styles.featureItem}>
              <Ionicons name="checkmark-circle" size={20} color={colors.primary} />
              <Text style={[styles.featureText, { color: colors.text }]}>{t('eventScreen.timingGuidance', 'Chart notes')}</Text>
            </View>
            <View style={styles.featureItem}>
              <Ionicons name="checkmark-circle" size={20} color={colors.primary} />
              <Text style={[styles.featureText, { color: colors.text }]}>
                {t(
                  'eventScreen.aiInsights',
                  'Using classic vedic methods including Parashari, Nadi and Jaimini'
                )}
              </Text>
            </View>
          </View>

          {/* Continue Button */}
          <View
            style={[
              styles.unlockButtonContainer,
              readingMode === 'monthly' && styles.unlockButtonContainerMonthly,
            ]}
          >
            <TouchableOpacity
              style={[styles.unlockButton, continueChecking && styles.unlockButtonDisabled]}
              onPress={readingMode === 'yearly' ? handleContinue : handleMonthlyContinue}
              disabled={continueChecking}
              activeOpacity={continueChecking ? 1 : 0.7}
            >
              <LinearGradient
                colors={continueGradient}
                style={styles.unlockGradient}
              >
                {continueChecking && readingMode === 'yearly' ? (
                  <>
                    <ActivityIndicator size="small" color={onPrimaryText} />
                    <Text style={[styles.unlockButtonText, { color: onPrimaryText }]}>
                      {t('eventScreen.checking', 'Checking…')}
                    </Text>
                  </>
                ) : (
                  <>
                    <Text style={[styles.unlockButtonText, { color: onPrimaryText }]}>
                      {readingMode === 'yearly'
                        ? t('eventScreen.continue', 'Continue')
                        : t('eventScreen.generateMonth', 'Generate my month study')}
                    </Text>
                    <Ionicons name="arrow-forward" size={22} color={onPrimaryText} />
                  </>
                )}
              </LinearGradient>
            </TouchableOpacity>
          </View>
        </ScrollView>
      ) : (
        <ScrollView
        nestedScrollEnabled
        contentContainerStyle={[styles.scrollContent, { backgroundColor: 'transparent' }]}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.primary} />}
      >
        {/* Macro Trends (The "Vibe") */}
        {displayMacroTrends.length > 0 && (
          <View
            style={[
              styles.macroCard,
              {
                backgroundColor: theme === 'dark' ? 'rgba(44, 30, 78, 0.85)' : colors.cardBackground,
                borderColor: colors.cardBorder,
              },
            ]}
          >
            <View style={styles.macroHeader}>
              <Ionicons name="planet" size={18} color={colors.primary} />
              <Text style={[styles.macroTitle, { color: colors.text }]}>The Vibe of {selectedYear}</Text>
            </View>
            {displayMacroTrends.map((trend, index) => (
              <View key={index} style={styles.trendRow}>
                <Text style={[styles.bullet, { color: colors.primary }]}>•</Text>
                <Text style={[styles.trendText, { color: colors.text }]}>{trend}</Text>
              </View>
            ))}
          </View>
        )}

        {/* SECTION 3: Monthly Guide (The "Details") */}
        {loadingMonthly ? (
          <View style={styles.section}>
            <View style={styles.loadingContainer}>
              <ActivityIndicator size="large" color={colors.primary} />
              <Text style={styles.loadingIcon}>{loadingMessages[loadingMessageIndex].icon}</Text>
              <Text style={[styles.loadingText, { color: colors.text }]}>{loadingMessages[loadingMessageIndex].text}</Text>
              {timelineProgress.monthsReady > 0 ? (
                <Text style={[styles.takingLongerText, { color: colors.textSecondary }]}>
                  {timelineProgress.monthsReady}/{timelineProgress.totalMonths} months ready
                  {timelineProgress.completedQuarters > 0 ? ` • Q${timelineProgress.completedQuarters} done` : ''}
                </Text>
              ) : null}
              
              {loadingProgress >= 0 ? (
                <View style={styles.progressBarContainer}>
                  <View style={[styles.progressBarTrack, { backgroundColor: colors.backgroundSecondary, borderColor: colors.cardBorder }]}>
                    <View style={[styles.progressBarFill, { width: `${loadingProgress}%`, backgroundColor: colors.primary }]} />
                  </View>
                  <Text style={[styles.progressPercentText, { color: colors.primary }]}>
                    {loadingProgress < 90 ? `${Math.round(loadingProgress)}%` : t('eventScreen.almostThere', 'Almost there...')}
                  </Text>
                </View>
              ) : (
                <Text style={[styles.takingLongerText, { color: colors.textSecondary }]}>Taking longer than usual...</Text>
              )}
            </View>
            {monthlyData?.monthly_predictions && monthlyData.monthly_predictions.length > 0 ? (
              <View style={styles.accordionContainer}>
                {monthlyData.monthly_predictions.map((month, index) => (
                  <MonthlyAccordion
                    key={`stream-${index}`}
                    data={{ ...month, month: getMonthName(month.month_id) }}
                    hideDiveDeep
                  />
                ))}
              </View>
            ) : null}
          </View>
        ) : monthlyData?.monthly_predictions && monthlyData.monthly_predictions.length > 0 ? (
          <View style={styles.section}>
            <Text style={[styles.sectionTitle, { color: colors.text }]}>📅 {t('eventScreen.monthlyGuide', 'Monthly Chart Notes')}</Text>
            <View style={styles.accordionContainer}>
              {monthlyData?.monthly_predictions?.map((month, index) => (
                <MonthlyAccordion
                  key={index}
                  data={{ ...month, month: getMonthName(month.month_id) }}
                  onChatPress={() => navigateToChat({ ...month, month: getMonthName(month.month_id) }, 'monthly')}
                  onDiveDeepPress={(data) => navigation.navigate('MonthlyDeepScreen', { year: selectedYear, month: data.month_id })}
                />
              ))}
            </View>
          </View>
        ) : monthlyData ? (
          <View style={styles.section}>
            <View style={styles.loadingContainer}>
              <Text style={[styles.loadingText, { color: colors.text }]}>⚠️ {t('eventScreen.noPredictions', 'No timeline insights generated. Please try again.')}</Text>
            </View>
          </View>
        ) : null}

      </ScrollView>
      )}
      <ConfirmCreditsModal
        visible={showEventCreditsModal}
        onClose={() => { setShowEventCreditsModal(false); setPendingAction(null); }}
        onConfirm={handleEventCreditsConfirm}
        title={t('home.options.events.title', 'What Will Manifest')}
        description={t(
          'credits.eventTimeline.description',
          'We will deeply analyze all your divisional charts using Parashari, Nadi, and Jaimini methods, and map all high‑probability events that may manifest over this period.'
        )}
        cost={creditCost}
        credits={credits}
        confirmLabel={t('eventScreen.continue', 'Continue')}
      />
      </SafeAreaView>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  header: {
    paddingHorizontal: 20,
    paddingTop: 10,
    paddingBottom: 14,
    backgroundColor: 'transparent',
    borderBottomWidth: 0,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    elevation: 0,
    shadowOpacity: 0,
  },
  backButton: {
    padding: 8,
    borderRadius: 8,
    backgroundColor: 'rgba(255, 215, 0, 0.1)'
  },
  headerCenter: {
    flex: 1,
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: '700',
    textAlign: 'center',
    marginBottom: 10,
    letterSpacing: 0.5,
  },
  headerSpacer: { width: 32 },
  headerRight: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  regenerateButton: { 
    width: 40, 
    height: 40, 
    borderRadius: 20, 
    backgroundColor: 'rgba(255, 215, 0, 0.15)', 
    justifyContent: 'center', 
    alignItems: 'center',
    borderWidth: 1,
    borderColor: 'rgba(255, 215, 0, 0.3)'
  },
  settingsButton: { 
    padding: 8,
    borderRadius: 8,
    backgroundColor: 'rgba(255, 215, 0, 0.1)'
  },
  
  scrollContent: { paddingBottom: 40 },
  
  section: { marginTop: 24, marginBottom: 24 },
  sectionHeader: { paddingHorizontal: 20, marginBottom: 16 },
  sectionTitle: { fontSize: 20, fontWeight: '700', marginBottom: 6, letterSpacing: 0.3 },
  sectionSubtitle: { fontSize: 14, lineHeight: 20 },
  
  macroCard: {
    margin: 20,
    padding: 20,
    borderRadius: 18,
    borderWidth: 1,
    elevation: 1,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.16,
    shadowRadius: 6,
  },
  macroHeader: { flexDirection: 'row', alignItems: 'center', marginBottom: 16, gap: 10 },
  macroTitle: { fontSize: 18, fontWeight: '700', letterSpacing: 0.3 },
  trendRow: { flexDirection: 'row', marginBottom: 10, alignItems: 'flex-start' },
  bullet: { marginRight: 10, fontSize: 18, marginTop: 2 },
  trendText: { fontSize: 15, lineHeight: 22, flex: 1 },
  
  loadingContainer: { alignItems: 'center', marginTop: 60, paddingHorizontal: 40 },
  loadingIcon: { fontSize: 56, marginTop: 20, marginBottom: 12 },
  loadingText: { marginTop: 16, fontSize: 17, fontWeight: '600', textAlign: 'center', lineHeight: 26 },
  progressBarContainer: { width: '100%', marginTop: 28, alignItems: 'center' },
  progressBarTrack: { width: '100%', height: 8, borderRadius: 4, overflow: 'hidden', borderWidth: 1 },
  progressBarFill: { height: '100%', borderRadius: 4 },
  progressPercentText: { fontSize: 15, fontWeight: '700', marginTop: 10 },
  takingLongerText: { fontSize: 14, marginTop: 28, fontStyle: 'italic' },
  
  waitingContainer: { 
    flex: 1, 
    justifyContent: 'center', 
    alignItems: 'center' 
  },
  waitingText: { 
    color: 'white', 
    marginTop: 16, 
    fontSize: 16, 
    fontWeight: '600' 
  },
  
  accordionContainer: { paddingHorizontal: 20 },
  
  selectionContainer: {
    padding: 16,
    paddingBottom: 22,
  },
  selectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    textAlign: 'center',
    marginTop: 16,
    marginBottom: 8,
    letterSpacing: 0.5,
  },
  selectionSubtitle: {
    fontSize: 14,
    textAlign: 'center',
    marginBottom: 18,
    lineHeight: 22,
  },
  modeToggleContainer: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 12,
  },
  modeToggleButton: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 12,
    borderWidth: 2,
    alignItems: 'center',
    justifyContent: 'center',
  },
  modeToggleText: {
    fontSize: 15,
    fontWeight: '800',
    letterSpacing: 0.3,
    marginBottom: 4,
  },
  modeToggleSubtext: {
    fontSize: 12,
    fontWeight: '600',
    letterSpacing: 0.2,
  },
  monthChipsContainer: {
    marginBottom: 16,
    height: 56,
    justifyContent: 'center',
    width: '100%',
  },
  monthChipsContent: {
    paddingHorizontal: (width - ITEM_WIDTH) / 2,
    flexDirection: 'row',
    alignItems: 'center',
  },
  monthChip: {
    paddingVertical: 12,
    borderRadius: 12,
    borderWidth: 2,
    alignItems: 'center',
    justifyContent: 'center',
    minWidth: ITEM_WIDTH - 6,
  },
  monthChipText: {
    fontSize: 14,
    fontWeight: '700',
  },
  yearChipsContainer: {
    marginBottom: 16,
    height: 56,
    width: '100%',
  },
  yearChipsContent: {
    paddingHorizontal: (width - 80) / 2,
    flexDirection: 'row',
    alignItems: 'center',
  },
  yearChip: {
    paddingVertical: 12,
    borderRadius: 12,
    borderWidth: 2,
    alignItems: 'center',
    justifyContent: 'center',
  },
  yearChipText: {
    fontSize: 15,
    fontWeight: '600',
  },
  quickSelectContainer: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 18
  },
  cachedYearsHintRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    marginBottom: 16,
    paddingHorizontal: 8,
  },
  cachedYearsLegendDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
    flexShrink: 0,
  },
  cachedYearsHintText: {
    fontSize: 12.5,
    lineHeight: 18,
    textAlign: 'left',
    flexShrink: 1,
  },
  quickSelectButton: {
    flex: 1,
    paddingVertical: 10,
    borderRadius: 12,
  },
  quickSelectText: {
    fontSize: 14,
    fontWeight: '600',
    textAlign: 'center',
    letterSpacing: 0.3,
  },
  featuresContainer: {
    padding: 16,
    paddingRight: 22,
    borderRadius: 14,
    marginBottom: 18,
    borderWidth: 1,
  },
  featuresTitle: {
    fontSize: 16,
    fontWeight: '700',
    marginBottom: 12,
    letterSpacing: 0.3,
  },
  featureItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 10,
    gap: 12
  },
  featureText: {
    fontSize: 14,
    lineHeight: 20,
    flex: 1,
    flexShrink: 1,
    flexWrap: 'wrap',
  },
  unlockButtonContainer: {
    marginTop: 10,
    paddingTop: 12,
    paddingBottom: 10,
  },
  unlockButtonContainerMonthly: {
    paddingBottom: 16,
  },
  unlockButton: {
    borderRadius: 14,
    overflow: 'hidden',
    borderWidth: 0,
    borderColor: 'transparent',
    shadowColor: '#140f2b',
    shadowOffset: { width: 0, height: 5 },
    shadowOpacity: 0.22,
    shadowRadius: 10,
    elevation: 4,
  },
  unlockButtonDisabled: {
    opacity: 0.85,
  },
  unlockGradient: {
    paddingVertical: 14,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 10
  },
  unlockButtonText: {
    fontSize: 16,
    fontWeight: '700',
    letterSpacing: 0.5
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.85)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20
  },
  modalContent: {
    borderRadius: 20,
    padding: 28,
    width: '100%',
    maxWidth: 340,
    alignItems: 'center',
    borderWidth: 1,
    elevation: 10
  },
  modalIcon: {
    marginBottom: 20
  },
  modalTitle: {
    fontSize: 22,
    fontWeight: '700',
    marginBottom: 14,
    textAlign: 'center',
    letterSpacing: 0.3
  },
  modalText: {
    fontSize: 15,
    textAlign: 'center',
    lineHeight: 22,
    marginBottom: 28
  },
  modalCostStrikethrough: {
    textDecorationLine: 'line-through',
    marginRight: 4
  },
  modalButtons: {
    flexDirection: 'row',
    gap: 12,
    width: '100%'
  },
  modalButton: {
    flex: 1,
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: 'center'
  },
  modalButtonCancel: {
    borderWidth: 1.5
  },
  modalButtonConfirm: {
    elevation: 4
  },
  modalButtonTextCancel: {
    fontSize: 16,
    fontWeight: '600',
    letterSpacing: 0.3
  },
  modalButtonTextConfirm: {
    fontSize: 16,
    fontWeight: '700',
    letterSpacing: 0.3
  }
});
