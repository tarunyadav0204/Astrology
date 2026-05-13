import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { SafeAreaView } from 'react-native-safe-area-context';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useNavigation, useRoute } from '@react-navigation/native';
import AsyncStorage from '@react-native-async-storage/async-storage';

import { chatAPI, creditAPI, pricingAPI } from '../services/api';
import { storage } from '../services/storage';
import { useCredits } from '../credits/CreditContext';
import MonthlyAccordion from './MonthlyAccordion';
import ConfirmCreditsModal from './ConfirmCreditsModal';
import { generateEventTimelinePDF, sharePDFOnWhatsApp, getLogoDataUriForModule } from '../utils/pdfGenerator';
import { useTheme } from '../context/ThemeContext';
import { useTranslation } from 'react-i18next';
import { trackEvent } from '../utils/analytics';
import { userFacingTimelineError } from '../utils/timelineUserErrors';

const MONTH_NAMES = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
const MONTHLY_DEEP_PENDING_KEY = 'monthlyDeepScreenPendingJob';

function getMonthName(monthId) {
  return MONTH_NAMES[monthId - 1] || `Month ${monthId}`;
}

export default function MonthlyDeepScreen() {
  const navigation = useNavigation();
  const route = useRoute();
  const { year, month } = route.params || {};
  const { credits, fetchBalance } = useCredits();
  const { t } = useTranslation();
  const { theme, colors } = useTheme();
  const bgGradient = theme === 'dark'
    ? ['#1a0033', '#2d1b4e', '#4a2c6d', colors.primary]
    : ['#fefcfb', '#fef7f0', '#fed7d7', '#fefcfb'];

  const [birthData, setBirthData] = useState(null);
  const [monthlyData, setMonthlyData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [creditCost, setCreditCost] = useState(100);
  const [loadingMessageIndex, setLoadingMessageIndex] = useState(0);
  const [loadingProgress, setLoadingProgress] = useState(0);
  const loadingIntervalRef = useRef(null);
  const progressIntervalRef = useRef(null);
  const deepPollRef = useRef(null);
  const deepTimeoutRef = useRef(null);
  const TIMELINE_POLL_MS = 3000;
  const TIMELINE_MAX_WAIT_MS = 15 * 60 * 1000;
  const [showMonthlyCreditsModal, setShowMonthlyCreditsModal] = useState(false);
  const [showGenerateButton, setShowGenerateButton] = useState(false);
  const [isExportingPdf, setIsExportingPdf] = useState(false);
  const isMountedRef = useRef(true);
  const initLoadKeyRef = useRef(null);
  const creditsModalInFlightRef = useRef(false);

  const loadingMessages = [
    { icon: '🌟', text: t('monthlyDeepScreen.loadingAnalyzing', 'Analyzing this month in depth...') },
    { icon: '🔮', text: t('monthlyDeepScreen.loadingMapping', 'Mapping every trigger and manifestation...') },
    { icon: '✨', text: t('monthlyDeepScreen.loadingExamining', 'Examining all house activations...') },
  ];

  const savePendingDeepMonthJob = useCallback(async (payload) => {
    try {
      await AsyncStorage.setItem(MONTHLY_DEEP_PENDING_KEY, JSON.stringify(payload));
    } catch (error) {
      console.warn('[MonthlyDeepScreen] save pending job', error?.message || error);
    }
  }, []);

  const loadPendingDeepMonthJob = useCallback(async () => {
    try {
      const raw = await AsyncStorage.getItem(MONTHLY_DEEP_PENDING_KEY);
      if (!raw) return null;
      return JSON.parse(raw);
    } catch (error) {
      console.warn('[MonthlyDeepScreen] load pending job', error?.message || error);
      return null;
    }
  }, []);

  const clearPendingDeepMonthJob = useCallback(async () => {
    try {
      await AsyncStorage.removeItem(MONTHLY_DEEP_PENDING_KEY);
    } catch (error) {
      console.warn('[MonthlyDeepScreen] clear pending job', error?.message || error);
    }
  }, []);

  const startMonthlyLoadingUi = useCallback((startedAtInput = new Date().toISOString()) => {
    const startedAtMs = new Date(startedAtInput || Date.now()).getTime();
    const safeStartedAt = Number.isFinite(startedAtMs) ? startedAtMs : Date.now();
    const elapsedMs = Math.max(0, Date.now() - safeStartedAt);
    const initialMessageIndex = Math.floor(elapsedMs / 3000) % loadingMessages.length;
    setGenerating(true);
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

  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  useEffect(() => {
    return () => {
      if (deepPollRef.current) {
        clearInterval(deepPollRef.current);
        deepPollRef.current = null;
      }
      if (deepTimeoutRef.current) {
        clearTimeout(deepTimeoutRef.current);
        deepTimeoutRef.current = null;
      }
      if (loadingIntervalRef.current) {
        clearInterval(loadingIntervalRef.current);
        loadingIntervalRef.current = null;
      }
      if (progressIntervalRef.current) {
        clearInterval(progressIntervalRef.current);
        progressIntervalRef.current = null;
      }
    };
  }, []);

  const getBirthDetails = useCallback(async () => {
    try {
      return await storage.getBirthDetails();
    } catch (e) {
      console.error(e);
      return null;
    }
  }, []);

  const stopDeepMonthJob = useCallback(() => {
    if (deepPollRef.current) {
      clearInterval(deepPollRef.current);
      deepPollRef.current = null;
    }
    if (deepTimeoutRef.current) {
      clearTimeout(deepTimeoutRef.current);
      deepTimeoutRef.current = null;
    }
    if (loadingIntervalRef.current) {
      clearInterval(loadingIntervalRef.current);
      loadingIntervalRef.current = null;
    }
    if (progressIntervalRef.current) {
      clearInterval(progressIntervalRef.current);
      progressIntervalRef.current = null;
    }
    setGenerating(false);
  }, []);

  /** After a failed or timed-out run, `showGenerateButton` was left false (set when user confirmed credits). */
  const revealEmptyStateActions = useCallback(() => {
    if (!isMountedRef.current) return;
    setShowMonthlyCreditsModal(false);
    setShowGenerateButton(true);
  }, []);

  const tryLoadCachedDeepMonth = useCallback(async () => {
    try {
      const bd = await getBirthDetails();
      if (!bd?.id || year == null || month == null) return false;
      const res = await chatAPI.getCachedMonthlyEvents({
        ...bd,
        selectedYear: year,
        selectedMonth: month,
        birth_chart_id: bd.id,
      });
      if (res.data?.cached && res.data?.data) {
        if (isMountedRef.current) {
          setMonthlyData(res.data.data);
          setShowMonthlyCreditsModal(false);
          setShowGenerateButton(false);
          await clearPendingDeepMonthJob();
          trackEvent('monthly_timeline_delivered', {
            year: Number(year),
            month: Number(month),
            source: 'monthly_deep_screen',
            mode: 'cached',
          });
          await fetchBalance();
        }
        return true;
      }
    } catch (e) {
      console.warn('[MonthlyDeepScreen] cache recovery', e?.message || e);
    }
    return false;
  }, [clearPendingDeepMonthJob, year, month, fetchBalance, getBirthDetails]);

  const attachDeepMonthPolling = useCallback((jobId, startedAt = new Date().toISOString()) => {
    let outcomeHandled = false;
    const takeOutcome = () => {
      if (outcomeHandled) return false;
      outcomeHandled = true;
      return true;
    };

    const finishSuccess = async (data, mode = 'poll_completed') => {
      if (!takeOutcome()) return;
      stopDeepMonthJob();
      setMonthlyData(data);
      await clearPendingDeepMonthJob();
      trackEvent('monthly_timeline_delivered', {
        year: Number(year),
        month: Number(month),
        source: 'monthly_deep_screen',
        mode,
      });
      fetchBalance();
    };

    const onPollFailure = async (message) => {
      if (!takeOutcome()) return;
      stopDeepMonthJob();
      await clearPendingDeepMonthJob();
      const recovered = await tryLoadCachedDeepMonth();
      if (recovered) {
        Alert.alert(
          t('monthlyDeepScreen.recoveredTitle', 'Deep dive ready'),
          t(
            'monthlyDeepScreen.recoveredBody',
            'Loaded your saved analysis from the server.'
          )
        );
        return;
      }
      revealEmptyStateActions();
      const raw = message != null ? String(message).trim() : '';
      const safeBody = raw
        ? userFacingTimelineError(raw)
        : t(
            'monthlyDeepScreen.stoppedBody',
            'The analysis may still be running. Use “Load saved”, or wait and open this screen again.'
          );
      Alert.alert(
        t('monthlyDeepScreen.stoppedTitle', 'Could not finish loading'),
        safeBody,
        [
          {
            text: t('eventScreen.tryLoadSaved', 'Load saved'),
            onPress: async () => {
              const ok = await tryLoadCachedDeepMonth();
              if (!ok) {
                Alert.alert(
                  t('eventScreen.noSavedYetTitle', 'No saved result yet'),
                  t(
                    'eventScreen.noSavedYetBody',
                    'Try again in a little while if the analysis is still running.'
                  )
                );
              }
            },
          },
          {
            text: t('common.tryAgain', 'Try again'),
            onPress: () => {
              revealEmptyStateActions();
            },
          },
          { text: t('common.ok', 'OK'), style: 'cancel' },
        ]
      );
    };

    deepPollRef.current = setInterval(async () => {
      try {
        const statusResponse = await chatAPI.getMonthlyEventsStatus(jobId);
        const status = statusResponse.data.status;
        if (status === 'completed' && statusResponse.data.data) {
          await finishSuccess(statusResponse.data.data);
        } else if (status === 'failed') {
          await onPollFailure(statusResponse.data.error || 'Analysis failed');
        }
      } catch (e) {
        await onPollFailure(
          e?.response?.data?.detail ||
            e?.message ||
            'Connection error while checking status.'
        );
      }
    }, TIMELINE_POLL_MS);

    const elapsedMs = Math.max(0, Date.now() - new Date(startedAt || Date.now()).getTime());
    const remainingMs = Math.max(5000, TIMELINE_MAX_WAIT_MS - elapsedMs);
    deepTimeoutRef.current = setTimeout(async () => {
      if (deepPollRef.current) {
        clearInterval(deepPollRef.current);
        deepPollRef.current = null;
      }
      deepTimeoutRef.current = null;
      if (outcomeHandled) return;
      try {
        const last = await chatAPI.getMonthlyEventsStatus(jobId);
        if (last.data?.status === 'completed' && last.data?.data) {
          await finishSuccess(last.data.data);
          return;
        }
      } catch (e) {
        console.warn('[MonthlyDeepScreen] final status check', e?.message || e);
      }
      const recovered = await tryLoadCachedDeepMonth();
      if (recovered) {
        if (!takeOutcome()) return;
        stopDeepMonthJob();
        await clearPendingDeepMonthJob();
        Alert.alert(
          t('monthlyDeepScreen.recoveredTitle', 'Deep dive ready'),
          t(
            'monthlyDeepScreen.longRunBody',
            'Your analysis finished — loaded from saved results.'
          )
        );
        return;
      }
      if (!takeOutcome()) return;
      stopDeepMonthJob();
      await clearPendingDeepMonthJob();
      revealEmptyStateActions();
      Alert.alert(
        t('monthlyDeepScreen.timeoutTitle', 'Still working or interrupted'),
        t(
          'monthlyDeepScreen.timeoutBody',
          'We stopped waiting after 15 minutes. If you were charged, your result is usually saved — tap “Load saved”. Otherwise tap “Try again” to run the credit step and generate again.'
        ),
        [
          {
            text: t('eventScreen.tryLoadSaved', 'Load saved'),
            onPress: async () => {
              const ok = await tryLoadCachedDeepMonth();
              if (!ok) {
                Alert.alert(
                  t('eventScreen.noSavedYetTitle', 'No saved result yet'),
                  t(
                    'eventScreen.noSavedYetBody',
                    'Try again in a little while if the analysis is still running.'
                  )
                );
              }
            },
          },
          {
            text: t('common.tryAgain', 'Try again'),
            onPress: () => {
              revealEmptyStateActions();
            },
          },
          { text: t('common.ok', 'OK'), style: 'cancel' },
        ]
      );
    }, remainingMs);
  }, [
    TIMELINE_MAX_WAIT_MS,
    TIMELINE_POLL_MS,
    clearPendingDeepMonthJob,
    fetchBalance,
    month,
    revealEmptyStateActions,
    stopDeepMonthJob,
    t,
    tryLoadCachedDeepMonth,
    year,
  ]);

  const resumePendingDeepMonthJob = useCallback(async (pending, birthDataOverride = null) => {
    const activeBirthData = birthDataOverride || birthData;
    if (
      !pending ||
      !pending.jobId ||
      !activeBirthData?.id ||
      Number(pending.birthChartId) !== Number(activeBirthData.id) ||
      Number(pending.year) !== Number(year) ||
      Number(pending.month) !== Number(month)
    ) {
      return false;
    }
    stopDeepMonthJob();
    setShowMonthlyCreditsModal(false);
    setShowGenerateButton(false);
    startMonthlyLoadingUi(pending.startedAt);
    attachDeepMonthPolling(pending.jobId, pending.startedAt);
    return true;
  }, [
    attachDeepMonthPolling,
    birthData,
    month,
    startMonthlyLoadingUi,
    stopDeepMonthJob,
    year,
  ]);

  const openCreditsModal = useCallback(async () => {
    if (creditsModalInFlightRef.current || showMonthlyCreditsModal) {
      return true;
    }
    creditsModalInFlightRef.current = true;
    try {
      await fetchBalance();
      const balanceRes = await creditAPI.getBalance();
      const actualCredits = balanceRes.data.balance;

      if (actualCredits < creditCost) {
        Alert.alert('Insufficient Credits', `You need ${creditCost} credits. You have ${actualCredits}.`, [
          { text: 'Get Credits', onPress: () => navigation.navigate('Credits') },
          { text: 'Cancel', style: 'cancel' },
        ]);
        if (isMountedRef.current) {
          setShowMonthlyCreditsModal(false);
          setShowGenerateButton(true);
        }
        return false;
      }

      if (isMountedRef.current) {
        setShowMonthlyCreditsModal(true);
        setShowGenerateButton(false);
      }
      return true;
    } catch (e) {
      if (isMountedRef.current) {
        setShowMonthlyCreditsModal(false);
        setShowGenerateButton(true);
      }
      return false;
    } finally {
      creditsModalInFlightRef.current = false;
    }
  }, [fetchBalance, creditCost, navigation, showMonthlyCreditsModal]);

  useEffect(() => {
    pricingAPI.getPricing().then((res) => {
      const cost = res?.data?.pricing?.events;
      if (cost != null) setCreditCost(Number(cost));
    }).catch(() => {});
  }, []);

  const fetchDeepMonth = useCallback(async () => {
    if (!birthData?.id || year == null || month == null) return;
    trackEvent('monthly_timeline_requested', {
      year: Number(year),
      month: Number(month),
      source: 'monthly_deep_screen',
    });
    stopDeepMonthJob();
    const startedAt = new Date().toISOString();
    startMonthlyLoadingUi(startedAt);
    try {
      const startResponse = await chatAPI.getMonthlyEvents({
        ...birthData,
        selectedYear: year,
        selectedMonth: month,
        birth_chart_id: birthData.id,
      });
      if (startResponse.data?.data && !startResponse.data?.job_id) {
        setMonthlyData(startResponse.data.data);
        await clearPendingDeepMonthJob();
        trackEvent('monthly_timeline_delivered', {
          year: Number(year),
          month: Number(month),
          source: 'monthly_deep_screen',
          mode: 'direct',
        });
        fetchBalance();
        stopDeepMonthJob();
        return;
      }
      const jobId = startResponse.data?.job_id;
      if (!jobId) throw new Error('No job_id received.');
      await savePendingDeepMonthJob({
        jobId,
        birthChartId: Number(birthData.id),
        year: Number(year),
        month: Number(month),
        startedAt,
      });
      attachDeepMonthPolling(jobId, startedAt);
    } catch (e) {
      await clearPendingDeepMonthJob();
      stopDeepMonthJob();
      revealEmptyStateActions();
      if (e.response?.status === 402) {
        Alert.alert('Insufficient Credits', e.response?.data?.detail || 'You need more credits.', [
          { text: 'Get Credits', onPress: () => navigation.navigate('Credits') },
          { text: 'Cancel', style: 'cancel' },
        ]);
      } else {
        Alert.alert('Error', e.message || 'Failed to generate.');
      }
    }
  }, [
    birthData,
    clearPendingDeepMonthJob,
    year,
    month,
    attachDeepMonthPolling,
    openCreditsModal,
    revealEmptyStateActions,
    savePendingDeepMonthJob,
    startMonthlyLoadingUi,
    stopDeepMonthJob,
  ]);

  useEffect(() => {
    let mounted = true;
    (async () => {
      const bd = await getBirthDetails();
      if (!mounted) return;
      if (!bd?.name) {
        navigation.replace('BirthProfileIntro', { returnTo: 'MonthlyDeepScreen', returnParams: route.params });
        return;
      }
      setBirthData(bd);
      if (year == null || month == null) {
        setLoading(false);
        return;
      }
      const initKey = `${bd.id || 'nochart'}:${year}:${month}`;
      if (initLoadKeyRef.current === initKey) {
        setLoading(false);
        return;
      }
      initLoadKeyRef.current = initKey;
      try {
        const pending = await loadPendingDeepMonthJob();
        const resumedPending = await resumePendingDeepMonthJob(
          pending && pending.birthChartId
            ? { ...pending, birthChartId: pending.birthChartId }
            : pending,
          bd,
        );
        if (resumedPending) {
          setLoading(false);
          return;
        }

        const recovered = await tryLoadCachedDeepMonth();
        if (recovered) {
          if (mounted) {
            setLoading(false);
          }
          return;
        } else {
          // Not cached: open credits modal immediately (user decides before generation).
          setMonthlyData(null);
          setShowGenerateButton(false);
          await openCreditsModal();
        }
      } catch (e) {
        console.error('Cache check failed:', e);
        initLoadKeyRef.current = null;
      }
      setLoading(false);
    })();
    return () => { mounted = false; };
  }, [year, month, getBirthDetails, loadPendingDeepMonthJob, navigation, resumePendingDeepMonthJob, route.params, tryLoadCachedDeepMonth]);

  useEffect(() => {
    const unsubscribe = navigation.addListener('focus', () => {
      (async () => {
        const pending = await loadPendingDeepMonthJob();
        if (monthlyData?.monthly_predictions?.length || generating) {
          return;
        }
        await resumePendingDeepMonthJob(pending);
      })();
    });
    return unsubscribe;
  }, [
    birthData,
    generating,
    loadPendingDeepMonthJob,
    month,
    monthlyData,
    navigation,
    resumePendingDeepMonthJob,
    year,
  ]);

  const handleGenerate = async () => {
    await openCreditsModal();
  };

  const singleMonth = monthlyData?.monthly_predictions?.[0];
  const monthLabel = year != null && month != null ? `${getMonthName(month)} ${year}` : '';

  const navigateToChatWithMonth = (context) => {
    if (!context) return;
    let predictionText = `${context.month} ${year || ''} Predictions:\n\n`;
    if (context.events?.length > 0) {
      context.events.forEach((event, idx) => {
        predictionText += `Event ${idx + 1}: ${event.type}\n`;
        predictionText += `${event.prediction}\n`;
        if (event.start_date && event.end_date) {
          predictionText += `Period: ${event.start_date} to ${event.end_date}\n`;
        }
        if (event.possible_manifestations?.length > 0) {
          predictionText += `\nPossible Scenarios (${event.possible_manifestations.length}):\n`;
          event.possible_manifestations.forEach((manifest, mIdx) => {
            const scenario = typeof manifest === 'string' ? manifest : manifest?.scenario;
            predictionText += `${mIdx + 1}. ${scenario}\n`;
          });
        }
        predictionText += '\n';
      });
    }
    predictionText += 'Please explain these predictions or ask your questions.';
    navigation.navigate('Home', { startChat: true, initialMessage: predictionText });
  };

  const handleExportPdf = async () => {
    if (!singleMonth) return;
    try {
      setIsExportingPdf(true);
      const logoDataUri = await getLogoDataUriForModule(require('../../assets/logo.png'));
      // Build a minimal monthlyData object containing only this month for the PDF generator
      const monthlyDataForPdf = monthlyData && monthlyData.monthly_predictions
        ? { ...monthlyData, monthly_predictions: monthlyData.monthly_predictions.filter(m => m.month_id === singleMonth.month_id) }
        : { monthly_predictions: [singleMonth] };

      const pdfUri = await generateEventTimelinePDF({
        year: year || new Date().getFullYear(),
        nativeName: birthData?.name?.substring(0, 7) || '',
        monthlyData: monthlyDataForPdf,
        logoDataUri,
      });
      await sharePDFOnWhatsApp(pdfUri);
    } catch (error) {
      console.error('Monthly deep export PDF error:', error);
      Alert.alert('Export failed', error?.message || 'Could not generate or share PDF.');
    } finally {
      setIsExportingPdf(false);
    }
  };

  if (loading) {
    return (
      <LinearGradient colors={bgGradient} style={{ flex: 1 }}>
        <SafeAreaView style={[styles.container, { backgroundColor: 'transparent' }]}>
          <View style={styles.centerContainer}>
            <ActivityIndicator size="large" color={colors.primary} />
            <Text style={[styles.loadingText, { color: colors.textSecondary }]}>{t('monthlyDeepScreen.loading', 'Loading...')}</Text>
          </View>
        </SafeAreaView>
      </LinearGradient>
    );
  }

  return (
    <LinearGradient colors={bgGradient} style={{ flex: 1 }}>
      <SafeAreaView style={[styles.container, { backgroundColor: 'transparent' }]}>
        <View style={[styles.header, { backgroundColor: 'transparent', borderBottomColor: colors.cardBorder }]}>
          <TouchableOpacity onPress={() => navigation.goBack()} style={[styles.backButton, { backgroundColor: colors.surface }]}>
            <Ionicons name="arrow-back" size={24} color={colors.primary} />
        </TouchableOpacity>
          <Text style={[styles.headerTitle, { color: colors.primary }]} numberOfLines={1}>
            {monthLabel ? t('monthlyDeepScreen.headerDeepDive', { monthYear: monthLabel }) : t('monthlyDeepScreen.headerMonthlyDeepDive', 'Monthly deep dive')}
          </Text>
          <View style={styles.headerRight}>
            {singleMonth && !generating && (
              <>
                <TouchableOpacity
                  onPress={handleGenerate}
                  style={[styles.regenerateButton, { backgroundColor: colors.surface, borderColor: colors.cardBorder }]}
                >
                  <Ionicons name="refresh" size={20} color={colors.primary} />
                </TouchableOpacity>
                <TouchableOpacity
                  onPress={handleExportPdf}
                  disabled={isExportingPdf}
                  style={[styles.settingsButton, { backgroundColor: colors.surface }]}
                >
                  {isExportingPdf ? (
                    <ActivityIndicator size="small" color={colors.primary} />
                  ) : (
                    <Ionicons name="document-text-outline" size={20} color={colors.primary} />
                  )}
                </TouchableOpacity>
              </>
            )}
          </View>
        </View>

        {generating ? (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color={colors.primary} />
            <Text style={styles.loadingIcon}>{loadingMessages[loadingMessageIndex].icon}</Text>
            <Text style={[styles.loadingText, { color: colors.text }]}>{loadingMessages[loadingMessageIndex].text}</Text>
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
              <Text style={[styles.takingLongerText, { color: colors.textSecondary }]}>
                {t('eventScreen.takingLonger', 'Taking longer than usual...')}
              </Text>
            )}
          </View>
        ) : singleMonth ? (
          <ScrollView
            style={styles.scroll}
            contentContainerStyle={[styles.scrollContent, { backgroundColor: 'transparent' }]}
            showsVerticalScrollIndicator={false}
          >
            <MonthlyAccordion
              data={{ ...singleMonth, month: getMonthName(singleMonth.month_id) }}
              onChatPress={() => navigateToChatWithMonth({ ...singleMonth, month: getMonthName(singleMonth.month_id) })}
              defaultExpanded
              hideDiveDeep
            />
          </ScrollView>
        ) : (
          <View style={[styles.emptyContainer, { backgroundColor: 'transparent' }]}>
            <Ionicons name="calendar-outline" size={64} color={colors.textTertiary} />
            <Text style={[styles.emptyTitle, { color: colors.text }]}>{t('monthlyDeepScreen.emptyTitle', { monthYear: monthLabel })}</Text>
            <Text style={[styles.emptyDesc, { color: colors.textSecondary }]}>
              {t('monthlyDeepScreen.emptyDesc', { cost: creditCost })}
            </Text>
            {showGenerateButton && !showMonthlyCreditsModal && (
              <TouchableOpacity style={[styles.generateButton, { backgroundColor: colors.primary }]} onPress={handleGenerate}>
                <Text style={[styles.generateButtonText, { color: theme === 'dark' ? colors.background : '#1a1a1a' }]}>
                  {t('monthlyDeepScreen.generateDeepDive', 'Generate deep dive')}
                </Text>
              </TouchableOpacity>
            )}
          </View>
        )}
        <ConfirmCreditsModal
          visible={showMonthlyCreditsModal}
          onClose={() => {
            setShowMonthlyCreditsModal(false);
            setShowGenerateButton(true);
          }}
          onConfirm={() => {
            setShowMonthlyCreditsModal(false);
            setShowGenerateButton(false);
            fetchDeepMonth();
          }}
          title={t('monthlyDeepScreen.generateConfirmTitle', 'Generate deep dive')}
          description={t(
            'credits.eventTimeline.description',
            'We will deeply analyze all your divisional charts using Parashari, Nadi, and Jaimini methods, and map all high‑probability events that may manifest over this period.'
          )}
          cost={creditCost}
          credits={credits}
          confirmLabel={t('monthlyDeepScreen.continue', 'Continue')}
        />
      </SafeAreaView>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
  },
  backButton: { padding: 8, borderRadius: 8, marginRight: 8 },
  headerTitle: { flex: 1, fontSize: 18, fontWeight: '700' },
  headerRight: { flexDirection: 'row', alignItems: 'center', justifyContent: 'flex-end', gap: 8 },
  regenerateButton: {
    width: 32,
    height: 32,
    borderRadius: 16,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  settingsButton: {
    width: 32,
    height: 32,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
  },
  centerContainer: { flex: 1, justifyContent: 'center', alignItems: 'center', gap: 12 },
  loadingContainer: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 24, gap: 12 },
  loadingIcon: { fontSize: 32 },
  loadingText: { fontSize: 16 },
  progressBarContainer: { width: '100%', marginTop: 20, alignItems: 'center' },
  progressBarTrack: {
    width: '100%',
    height: 8,
    borderRadius: 4,
    overflow: 'hidden',
    borderWidth: 1,
  },
  progressBarFill: { height: '100%', borderRadius: 4 },
  progressPercentText: { marginTop: 10, fontSize: 13, fontWeight: '700' },
  takingLongerText: { marginTop: 12, fontSize: 13, textAlign: 'center' },
  scroll: { flex: 1 },
  scrollContent: { padding: 16, paddingBottom: 32 },
  emptyContainer: { flex: 1, padding: 24, justifyContent: 'center', alignItems: 'center' },
  emptyTitle: { fontSize: 20, fontWeight: '700', marginTop: 16, textAlign: 'center' },
  emptyDesc: { fontSize: 14, textAlign: 'center', marginTop: 8, paddingHorizontal: 16 },
  generateButton: { marginTop: 24, paddingVertical: 14, paddingHorizontal: 24, borderRadius: 12 },
  generateButtonText: { fontSize: 16, fontWeight: '700' },
});
