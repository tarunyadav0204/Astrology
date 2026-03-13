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
import { SafeAreaView } from 'react-native-safe-area-context';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useNavigation, useRoute } from '@react-navigation/native';

import { chatAPI, creditAPI, pricingAPI } from '../services/api';
import { storage } from '../services/storage';
import { useCredits } from '../credits/CreditContext';
import MonthlyAccordion from './MonthlyAccordion';
import ConfirmCreditsModal from './ConfirmCreditsModal';
import { generateEventTimelinePDF, sharePDFOnWhatsApp, getLogoDataUriForModule } from '../utils/pdfGenerator';
import { useTheme } from '../context/ThemeContext';
import { useTranslation } from 'react-i18next';

const MONTH_NAMES = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

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

  const [birthData, setBirthData] = useState(null);
  const [monthlyData, setMonthlyData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [creditCost, setCreditCost] = useState(100);
  const [loadingMessageIndex, setLoadingMessageIndex] = useState(0);
  const loadingIntervalRef = useRef(null);
  const [showMonthlyCreditsModal, setShowMonthlyCreditsModal] = useState(false);
  const [isExportingPdf, setIsExportingPdf] = useState(false);

  useEffect(() => {
    pricingAPI.getPricing().then((res) => {
      const cost = res?.data?.pricing?.events;
      if (cost != null) setCreditCost(Number(cost));
    }).catch(() => {});
  }, []);

  const loadingMessages = [
    { icon: '🌟', text: t('monthlyDeepScreen.loadingAnalyzing', 'Analyzing this month in depth...') },
    { icon: '🔮', text: t('monthlyDeepScreen.loadingMapping', 'Mapping every trigger and manifestation...') },
    { icon: '✨', text: t('monthlyDeepScreen.loadingExamining', 'Examining all house activations...') },
  ];

  const getBirthDetails = useCallback(async () => {
    try {
      return await storage.getBirthDetails();
    } catch (e) {
      console.error(e);
      return null;
    }
  }, []);

  const fetchDeepMonth = useCallback(async () => {
    if (!birthData?.id || year == null || month == null) return;
    setGenerating(true);
    loadingIntervalRef.current = setInterval(() => {
      setLoadingMessageIndex(prev => (prev + 1) % loadingMessages.length);
    }, 3000);
    try {
      const startResponse = await chatAPI.getMonthlyEvents({
        ...birthData,
        selectedYear: year,
        selectedMonth: month,
        birth_chart_id: birthData.id,
      });
      if (startResponse.data?.data && !startResponse.data?.job_id) {
        setMonthlyData(startResponse.data.data);
        fetchBalance();
        setGenerating(false);
        if (loadingIntervalRef.current) {
          clearInterval(loadingIntervalRef.current);
          loadingIntervalRef.current = null;
        }
        return;
      }
      const jobId = startResponse.data?.job_id;
      if (!jobId) throw new Error('No job_id received.');
      const pollInterval = setInterval(async () => {
        try {
          const statusResponse = await chatAPI.getMonthlyEventsStatus(jobId);
          const status = statusResponse.data.status;
          if (status === 'completed') {
            clearInterval(pollInterval);
            setMonthlyData(statusResponse.data.data);
            fetchBalance();
            setGenerating(false);
            if (loadingIntervalRef.current) {
              clearInterval(loadingIntervalRef.current);
              loadingIntervalRef.current = null;
            }
          } else if (status === 'failed') {
            clearInterval(pollInterval);
            throw new Error(statusResponse.data.error || 'Analysis failed');
          }
        } catch (e) {
          clearInterval(pollInterval);
          setGenerating(false);
          if (loadingIntervalRef.current) {
            clearInterval(loadingIntervalRef.current);
            loadingIntervalRef.current = null;
          }
          Alert.alert('Error', e.message || 'Something went wrong.');
        }
      }, 3000);
    } catch (e) {
      setGenerating(false);
      if (loadingIntervalRef.current) {
        clearInterval(loadingIntervalRef.current);
        loadingIntervalRef.current = null;
      }
      if (e.response?.status === 402) {
        Alert.alert('Insufficient Credits', e.response?.data?.detail || 'You need more credits.', [
          { text: 'Get Credits', onPress: () => navigation.navigate('Credits') },
          { text: 'Cancel', style: 'cancel' },
        ]);
      } else {
        Alert.alert('Error', e.message || 'Failed to generate.');
      }
    }
  }, [birthData, year, month, fetchBalance, navigation]);

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
      try {
        const cacheRes = await chatAPI.getCachedMonthlyEvents({
          ...bd,
          selectedYear: year,
          selectedMonth: month,
          birth_chart_id: bd.id,
        });
        if (mounted && cacheRes.data?.cached && cacheRes.data?.data) {
          setMonthlyData(cacheRes.data.data);
        }
      } catch (e) {
        console.error('Cache check failed:', e);
      }
      setLoading(false);
    })();
    return () => { mounted = false; };
  }, [year, month, getBirthDetails, navigation, route.params]);

  const handleGenerate = async () => {
    await fetchBalance();
    const balanceRes = await creditAPI.getBalance();
    const actualCredits = balanceRes.data.balance;
    if (actualCredits < creditCost) {
      Alert.alert('Insufficient Credits', `You need ${creditCost} credits. You have ${actualCredits}.`, [
        { text: 'Get Credits', onPress: () => navigation.navigate('Credits') },
        { text: 'Cancel', style: 'cancel' },
      ]);
      return;
    }
    setShowMonthlyCreditsModal(true);
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
      <SafeAreaView style={[styles.container, { backgroundColor: colors.background }]}>
        <View style={styles.centerContainer}>
          <ActivityIndicator size="large" color={colors.accent} />
          <Text style={[styles.loadingText, { color: colors.textSecondary }]}>{t('monthlyDeepScreen.loading', 'Loading...')}</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: colors.background }]}>
      <View style={[styles.header, { backgroundColor: colors.backgroundSecondary, borderBottomColor: colors.cardBorder }]}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={[styles.backButton, { backgroundColor: colors.surface }]}>
          <Ionicons name="arrow-back" size={24} color={colors.accent} />
        </TouchableOpacity>
        <Text style={[styles.headerTitle, { color: colors.accent }]} numberOfLines={1}>
          {monthLabel ? t('monthlyDeepScreen.headerDeepDive', { monthYear: monthLabel }) : t('monthlyDeepScreen.headerMonthlyDeepDive', 'Monthly deep dive')}
        </Text>
        <View style={styles.headerRight}>
          {singleMonth && !generating && (
            <>
              <TouchableOpacity
                onPress={handleGenerate}
                style={[styles.regenerateButton, { backgroundColor: colors.surface, borderColor: colors.cardBorder }]}
              >
                <Ionicons name="refresh" size={20} color={colors.accent} />
              </TouchableOpacity>
              <TouchableOpacity
                onPress={handleExportPdf}
                disabled={isExportingPdf}
                style={[styles.settingsButton, { backgroundColor: colors.surface }]}
              >
                {isExportingPdf ? (
                  <ActivityIndicator size="small" color={colors.accent} />
                ) : (
                  <Ionicons name="document-text-outline" size={20} color={colors.accent} />
                )}
              </TouchableOpacity>
            </>
          )}
        </View>
      </View>

      {generating ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={colors.accent} />
          <Text style={styles.loadingIcon}>{loadingMessages[loadingMessageIndex].icon}</Text>
          <Text style={[styles.loadingText, { color: colors.text }]}>{loadingMessages[loadingMessageIndex].text}</Text>
        </View>
      ) : singleMonth ? (
        <ScrollView
          style={styles.scroll}
          contentContainerStyle={[styles.scrollContent, { backgroundColor: colors.background }]}
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
        <View style={[styles.emptyContainer, { backgroundColor: colors.background }]}>
          <Ionicons name="calendar-outline" size={64} color={colors.textTertiary} />
          <Text style={[styles.emptyTitle, { color: colors.text }]}>{t('monthlyDeepScreen.emptyTitle', { monthYear: monthLabel })}</Text>
          <Text style={[styles.emptyDesc, { color: colors.textSecondary }]}>
            {t('monthlyDeepScreen.emptyDesc', { cost: creditCost })}
          </Text>
          <TouchableOpacity style={[styles.generateButton, { backgroundColor: colors.accent }]} onPress={handleGenerate}>
            <Text style={[styles.generateButtonText, { color: theme === 'dark' ? colors.background : '#1a1a1a' }]}>
              {t('monthlyDeepScreen.generateDeepDive', 'Generate deep dive')}
            </Text>
          </TouchableOpacity>
        </View>
      )}
      <ConfirmCreditsModal
        visible={showMonthlyCreditsModal}
        onClose={() => setShowMonthlyCreditsModal(false)}
        onConfirm={() => {
          setShowMonthlyCreditsModal(false);
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
  scroll: { flex: 1 },
  scrollContent: { padding: 16, paddingBottom: 32 },
  emptyContainer: { flex: 1, padding: 24, justifyContent: 'center', alignItems: 'center' },
  emptyTitle: { fontSize: 20, fontWeight: '700', marginTop: 16, textAlign: 'center' },
  emptyDesc: { fontSize: 14, textAlign: 'center', marginTop: 8, paddingHorizontal: 16 },
  generateButton: { marginTop: 24, paddingVertical: 14, paddingHorizontal: 24, borderRadius: 12 },
  generateButtonText: { fontSize: 16, fontWeight: '700' },
});
