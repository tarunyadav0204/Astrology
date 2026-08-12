import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import i18n from '../../locales/i18n';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  ActivityIndicator,
  TouchableOpacity,
  Animated,
  Alert,
  Platform,
  StatusBar,
} from 'react-native';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { userFacingPdfExportError } from '../../utils/pdfExportMessages';
import { API_BASE_URL, getEndpoint } from '../../utils/constants';
import { useTheme } from '../../context/ThemeContext';
import { useFocusEffect } from '@react-navigation/native';
import { storage } from '../../services/storage';
import { useCredits } from '../../credits/CreditContext';
import { pricingAPI } from '../../services/api';
import { useAnalytics } from '../../hooks/useAnalytics';
import { trackAstrologyEvent, trackEvent } from '../../utils/analytics';
import { useAuthGate } from '../../auth/AuthGateContext';
import AnalysisCreditModal from '../Analysis/AnalysisCreditModal';
import NativeSelectorChip from '../Common/NativeSelectorChip';
import { typographyTokens } from '../../theme/tokens';

/** Map AI/backend section heading to karmaAnalysis.sectionTitles.<slug> */
function karmaSectionTitleSlug(title) {
  if (title == null || title === '') return 'unknown';
  const s = String(title).trim();
  if (/^introduction$/i.test(s)) return 'introduction';
  const core = s.replace(/^\d+\.\s*/, '').trim();
  const slug = core
    .toLowerCase()
    .replace(/'/g, '')
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_|_$/g, '');
  return slug || 'unknown';
}

const KarmaAnalysisScreen = ({ route, navigation }) => {
  useAnalytics('KarmaAnalysisScreen');
  const { t } = useTranslation();
  const { colors } = useTheme();
  const insets = useSafeAreaInsets();
  const { chartId } = route.params || {};
  const { credits, fetchBalance } = useCredits();
  const { requireAuthForPaid } = useAuthGate();

  const isIosKarmaStudy = Platform.OS === 'ios';
  const [karmaCost, setKarmaCost] = useState(25);
  const [loading, setLoading] = useState(false);
  const [analysis, setAnalysis] = useState(null);
  const [error, setError] = useState(null);
  const [pollingInterval, setPollingInterval] = useState(null);
  const [currentJobId, setCurrentJobId] = useState(null);
  const [fadeAnim] = useState(new Animated.Value(0));
  const [nativeName, setNativeName] = useState(() =>
    i18n.t('karmaAnalysis.defaultNativeName', 'Native')
  );
  const uiText = {
    pdfShareTitle: isIosKarmaStudy ? 'Share Chart Study' : t('karmaAnalysis.pdfShareTitle'),
    pdfDocTitle: isIosKarmaStudy ? 'Chart Pattern Study' : t('karmaAnalysis.pdfDocTitle'),
    pdfDocSubtitle: isIosKarmaStudy ? 'A study of repeating chart themes' : t('karmaAnalysis.pdfDocSubtitle'),
    pdfFooterLine1: isIosKarmaStudy ? 'Analyzed by AstroRoshni' : t('karmaAnalysis.pdfFooterLine1'),
    pdfFooterLine2: isIosKarmaStudy ? 'Chart Study • Vedic Astrology' : t('karmaAnalysis.pdfFooterLine2'),
    loadingTitle: isIosKarmaStudy ? 'Studying Chart Patterns' : t('karmaAnalysis.loadingTitle'),
    loadingSubtitleProgress: isIosKarmaStudy
      ? 'Reviewing repeating themes and timing markers...'
      : t('karmaAnalysis.loadingSubtitleProgress'),
    loadingSubtitleSlow: isIosKarmaStudy
      ? 'This is taking longer than usual...'
      : t('karmaAnalysis.loadingSubtitleSlow'),
    errorTitle: isIosKarmaStudy ? 'Unable to Load Study' : t('karmaAnalysis.errorTitle'),
    startTitle: isIosKarmaStudy ? 'Chart Pattern Study' : t('karmaAnalysis.startTitle'),
    startSubtitle: isIosKarmaStudy
      ? 'Review repeating themes and chart patterns'
      : t('karmaAnalysis.startSubtitle'),
    confirmStartTitle: isIosKarmaStudy ? 'Start Chart Study' : t('karmaAnalysis.confirmStartTitle'),
    confirmRegenerateTitle: isIosKarmaStudy
      ? 'Regenerate Chart Study'
      : t('karmaAnalysis.confirmRegenerateTitle'),
    resultTitle: isIosKarmaStudy ? 'Chart Patterns' : t('karmaAnalysis.resultTitle'),
    resultSubtitle: isIosKarmaStudy
      ? 'A study of repeating chart themes'
      : t('karmaAnalysis.resultSubtitle'),
    footerAnalyzedBy: isIosKarmaStudy ? 'Study prepared by AstroRoshni' : t('karmaAnalysis.footerAnalyzedBy'),
    footerAI: isIosKarmaStudy ? 'Chart Study • Vedic Astrology' : t('karmaAnalysis.footerAI'),
  };

  const resolveSectionTitle = useCallback(
    (sectionTitle) => {
      const slug = karmaSectionTitleSlug(sectionTitle);
      return t(`karmaAnalysis.sectionTitles.${slug}`, sectionTitle);
    },
    [t]
  );
  const [selectedChartId, setSelectedChartId] = useState(chartId);
  const [showStartModal, setShowStartModal] = useState(false);
  const [showRegenerateModal, setShowRegenerateModal] = useState(false);
  const [generatingPDF, setGeneratingPDF] = useState(false);
  const [progress, setProgress] = useState(0);
  const [showProgress, setShowProgress] = useState(false);
  const [progressTimer, setProgressTimer] = useState(null);
  const [isChangingChart, setIsChangingChart] = useState(false);
  const lastTrackedAnalysisRef = useRef(null);

  // Declared before useFocusEffect — that hook reads loadBirthData in its dep array.
  const loadBirthData = useCallback(async () => {
    try {
      console.log('[KarmaAnalysis] Loading birth data...');
      let birthDetails = await storage.getBirthDetails();
      if (!birthDetails) {
        const profiles = await storage.getBirthProfiles();
        if (profiles?.length) birthDetails = profiles.find((p) => p.relation === 'self') || profiles[0];
      }
      if (!birthDetails?.name) {
        navigation.replace('BirthProfileIntro', { returnTo: 'KarmaAnalysis' });
        return;
      }
      console.log('[KarmaAnalysis] Birth details:', birthDetails);
      
      if (birthDetails?.name) {
        setNativeName(birthDetails.name);
      }
      if (birthDetails?.id) {
        console.log('[KarmaAnalysis] Setting selectedChartId to:', birthDetails.id);
        // Reset analysis if chart changed
        if (birthDetails.id !== selectedChartId && selectedChartId) {
          console.log('[KarmaAnalysis] Chart changed, clearing analysis');
          setIsChangingChart(true);
          // Clear immediately
          setAnalysis(null);
          setError(null);
          setLoading(false);
        }
        setSelectedChartId(birthDetails.id);
        // Reset flag after state updates
        if (birthDetails.id !== selectedChartId && selectedChartId) {
          setTimeout(() => setIsChangingChart(false), 50);
        }
      }
    } catch (err) {
      console.error('[KarmaAnalysis] Error loading birth data:', err);
    }
  }, [selectedChartId, navigation]);

  const fetchKarmaCost = async () => {
    try {
      const response = await pricingAPI.getPricing();
      const data = response?.data || response;
      const cost = data?.pricing?.karma != null ? Number(data.pricing.karma) : 25;
      setKarmaCost(cost);
    } catch (err) {
      console.error('Error fetching karma cost:', err);
    }
  };

  useFocusEffect(
    useCallback(() => {
      loadBirthData();
      fetchKarmaCost();
      // Don't restart if already loading/polling
      if (!loading && !pollingInterval) {
        if (selectedChartId) {
          checkExistingAnalysis();
        }
      }
    }, [loadBirthData])
  );

  useEffect(() => {
    if (selectedChartId && !loading && !isChangingChart) {
      checkExistingAnalysis();
    }
  }, [selectedChartId, isChangingChart]);

  useEffect(() => {
    if (loading) return;
    if (Platform.OS === 'web') {
      fadeAnim.setValue(1);
      return;
    }
    fadeAnim.setValue(0);
    Animated.timing(fadeAnim, {
      toValue: 1,
      duration: 500,
      useNativeDriver: true,
    }).start();
  }, [loading, analysis, error]);

  useEffect(() => {
    return () => {
      if (pollingInterval) clearInterval(pollingInterval);
    };
  }, [pollingInterval]);

  useEffect(() => {
    if (!analysis) return;
    const signature = JSON.stringify({
      chartId: selectedChartId,
      keysCount: Object.keys(analysis || {}).length,
      hasSections: !!analysis?.sections,
    });
    if (lastTrackedAnalysisRef.current === signature) return;
    lastTrackedAnalysisRef.current = signature;
    trackEvent('karma_analysis_received', {
      chart_id: selectedChartId ? String(selectedChartId) : null,
      source: 'karma_analysis_screen',
    });
  }, [analysis, selectedChartId]);

  const checkExistingAnalysis = async () => {
    try {
      if (!selectedChartId) {
        setError(t('karmaAnalysis.chartNotFound'));
        return;
      };
      
      setLoading(true);
      const token = await AsyncStorage.getItem('authToken');
      const response = await fetch(`${API_BASE_URL}${getEndpoint(`/karma-analysis/status?chart_id=${selectedChartId}`)}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        if ((data.status === 'complete' || data.status === 'completed') && data.data) {
          setAnalysis(data.data);
          await saveAnalysis(data.data);
        } else {
          // No analysis exists - keep analysis as null
          setAnalysis(null);
        }
      } else {
        // No analysis exists - keep analysis as null
        setAnalysis(null);
      }
      setLoading(false);
    } catch (err) {
      console.error('Error checking existing analysis:', err);
      setAnalysis(null);
      setLoading(false);
    }
  };

  const saveAnalysis = async (data) => {
    try {
      if (!selectedChartId) return;
      await AsyncStorage.setItem(`karma_analysis_${selectedChartId}`, JSON.stringify(data));
    } catch (error) {
      console.error('Error saving analysis:', error);
    }
  };

  const handleStartAnalysis = async () => {
    const authOk = await requireAuthForPaid({
      feature: 'karma analysis',
      message: 'Sign in to run karma analysis. Credits are charged only after you confirm.',
      resume: { resumeRoute: 'KarmaAnalysis', resumeParams: { chartId: selectedChartId } },
    });
    if (!authOk) return;
    setShowStartModal(true);
  };

  const confirmStartAnalysis = async () => {
    setShowStartModal(false);
    setLoading(true);
    fadeAnim.setValue(0);
    Animated.timing(fadeAnim, {
      toValue: 1,
      duration: 500,
      useNativeDriver: true,
    }).start();
    startProgressBar();
    await initiateAnalysis(false);
  };

  const handleRegenerate = () => {
    setShowRegenerateModal(true);
  };

  const confirmRegenerate = async () => {
    setShowRegenerateModal(false);
    try {
      if (selectedChartId) {
        await AsyncStorage.removeItem(`karma_analysis_${selectedChartId}`);
      }
    } catch (error) {
      console.error('Failed to clear cache:', error);
    }
    setAnalysis(null);
    setLoading(true);
    fadeAnim.setValue(0);
    Animated.timing(fadeAnim, {
      toValue: 1,
      duration: 500,
      useNativeDriver: true,
    }).start();
    startProgressBar();
    setTimeout(() => initiateAnalysis(true), 100);
  };

  const initiateAnalysis = async (forceRegenerate = false) => {
    if (!selectedChartId) {
      setError(t('karmaAnalysis.chartNotFound'));
      setLoading(false);
      return;
    }
    try {
      setLoading(true);
      
      // Track karma analysis request
      trackAstrologyEvent.analysisRequested(forceRegenerate ? 'karma_regenerate' : 'karma');
      trackEvent('karma_analysis_sent', {
        chart_id: selectedChartId ? String(selectedChartId) : null,
        source: 'karma_analysis_screen',
        force_regenerate: !!forceRegenerate,
      });
      
      const token = await AsyncStorage.getItem('authToken');
      const response = await fetch(`${API_BASE_URL}${getEndpoint('/karma-analysis/start')}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ chart_id: String(selectedChartId), force_regenerate: !!forceRegenerate })
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || i18n.t('karmaAnalysis.initiateFailed'));
      }
      
      const data = await response.json();
      
      if ((data.status === 'complete' || data.status === 'completed') && data.data) {
        stopProgressBar();
        setAnalysis(data.data);
        await saveAnalysis(data.data);
        await fetchBalance();
        setLoading(false);
      } else if (data.job_id) {
        setCurrentJobId(data.job_id);
        startPolling(data.job_id);
      } else {
        throw new Error(i18n.t('karmaAnalysis.unexpectedResponse'));
      }
    } catch (err) {
      stopProgressBar();
      setError(err.message);
      setLoading(false);
    }
  };

  const startProgressBar = () => {
    setProgress(0);
    setShowProgress(true);
    const duration = 60000; // 60 seconds
    const steps = 600; // Update every 100ms
    let currentStep = 0;
    
    const timer = setInterval(() => {
      currentStep++;
      setProgress((currentStep / steps) * 100);
      
      if (currentStep >= steps) {
        clearInterval(timer);
        setShowProgress(false);
      }
    }, duration / steps);
    
    setProgressTimer(timer);
  };

  const stopProgressBar = () => {
    if (progressTimer) {
      clearInterval(progressTimer);
      setProgressTimer(null);
    }
    setShowProgress(false);
    setProgress(0);
  };

  const startPolling = (jobId) => {
    const interval = setInterval(async () => {
      try {
        const token = await AsyncStorage.getItem('authToken');
        const response = await fetch(`${API_BASE_URL}${getEndpoint(`/karma-analysis/status/${jobId}`)}`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        const data = await response.json();
        
        if ((data.status === 'complete' || data.status === 'completed') && data.data) {
          stopProgressBar();
          setAnalysis(data.data);
          await saveAnalysis(data.data);
          await fetchBalance();
          setLoading(false);
          clearInterval(interval);
          setPollingInterval(null);
          setCurrentJobId(null);
        } else if (data.status === 'failed' || data.status === 'error') {
          stopProgressBar();
          setError(data.error);
          setLoading(false);
          clearInterval(interval);
          setPollingInterval(null);
          setCurrentJobId(null);
        }
      } catch (err) {
        console.error('[KarmaAnalysis] Polling error:', err);
        stopProgressBar();
        setError(err.message);
        setLoading(false);
        clearInterval(interval);
        setPollingInterval(null);
      }
    }, 2000);
    
    setPollingInterval(interval);
  };

  const generateKarmaPDF = async () => {
    if (!analysis) return;
    
    try {
      setGeneratingPDF(true);
      
      // Track PDF generation
      trackAstrologyEvent.pdfGenerated('karma');
      
      console.log('[PDF] Starting generation...');
      
      const sections = analysis.sections || {};
      let contentHTML = '';
      
      Object.entries(sections).forEach(([title, content]) => {
        // Format content with bold and italic
        let formattedContent = content
          .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')  // Bold
          .replace(/\*(.*?)\*/g, '<em>$1</em>')              // Italic
          .replace(/\n/g, '<br>');

        const sectionHeading = resolveSectionTitle(title);

        contentHTML += `
          <div class="karma-section">
            <h2 class="section-title">🕉️ ${sectionHeading}</h2>
            <div class="section-content">${formattedContent}</div>
          </div>
        `;
      });
      
      const html = `
        <!DOCTYPE html>
        <html>
          <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
              * { margin: 0; padding: 0; box-sizing: border-box; }
              body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: white;
                padding: 20px;
                color: #1a1a1a;
                line-height: 1.6;
              }
              .container {
                max-width: 800px;
                margin: 0 auto;
                background: white;
                border-radius: 20px;
                padding: 30px;
                box-shadow: 0 8px 24px rgba(0,0,0,0.1);
                border: 2px solid #FFD700;
              }
              .header {
                text-align: center;
                margin-bottom: 30px;
                padding-bottom: 20px;
                border-bottom: 3px solid #FFD700;
              }
              .logo { font-size: 48px; margin-bottom: 10px; }
              .title {
                font-size: 32px;
                font-weight: 700;
                color: #1a0033;
                margin-bottom: 5px;
                letter-spacing: 1px;
              }
              .subtitle {
                font-size: 16px;
                color: #4a0080;
                font-style: italic;
              }
              .native-name {
                font-size: 18px;
                color: #1a0033;
                margin-top: 10px;
                font-weight: 600;
              }
              .timestamp {
                font-size: 12px;
                color: #666;
                margin-top: 5px;
              }
              .karma-section {
                background: #fef7f0;
                border-radius: 16px;
                padding: 20px;
                margin: 20px 0;
                border: 2px solid #FFD700;
              }
              .section-title {
                font-size: 20px;
                font-weight: 700;
                color: #1a0033;
                margin-bottom: 15px;
                display: flex;
                align-items: center;
              }
              .section-content {
                font-size: 15px;
                line-height: 1.8;
                color: #1a1a1a;
                text-align: justify;
              }
              strong {
                font-weight: 700;
                color: #1a0033;
              }
              em {
                font-style: italic;
                color: #4a0080;
              }
              .footer {
                margin-top: 40px;
                padding-top: 20px;
                border-top: 2px solid #FFD700;
                text-align: center;
                color: #666;
                font-size: 12px;
              }
            </style>
          </head>
          <body>
            <div class="container">
              <div class="header">
                <div class="logo">🕉️</div>
                <div class="title">${uiText.pdfDocTitle}</div>
                <div class="subtitle">${uiText.pdfDocSubtitle}</div>
                <div class="native-name">${nativeName}</div>
                <div class="timestamp">${new Date().toLocaleString()}</div>
              </div>
              ${contentHTML}
              <div class="footer">
                ${uiText.pdfFooterLine1}<br>
                ${uiText.pdfFooterLine2}
              </div>
            </div>
          </body>
        </html>
      `;

      console.log('[PDF] HTML generated, exporting...');
      const { exportHtmlAsPdf, sharePDFOnWhatsApp, PDF_PRINT_STYLES } = await import('../../utils/pdfGenerator');
      const htmlWithPrintStyles = html.replace('</style>', `${PDF_PRINT_STYLES}\n            </style>`);
      const pdfUri = await exportHtmlAsPdf(htmlWithPrintStyles, { timeoutMs: 30000 });

      console.log('[PDF] Generated successfully:', pdfUri || '(web print dialog)');
      await sharePDFOnWhatsApp(pdfUri, { dialogTitle: uiText.pdfShareTitle });
    } catch (error) {
      console.error('[PDF] Error:', error);
      Alert.alert(
        t('karmaAnalysis.pdfErrorTitle'),
        userFacingPdfExportError(error)
      );
    } finally {
      setGeneratingPDF(false);
    }
  };

  const renderKarmaTopBar = ({ showActions = false } = {}) => (
    <View style={[styles.karmaTopBar, { paddingTop: Math.max(insets.top, 10) + 5, backgroundColor: colors.headerSurface, borderBottomColor: colors.cosmicLine }]}>
      <TouchableOpacity
        onPress={() => navigation.goBack()}
        style={[styles.headerIconBtn, { backgroundColor: colors.cosmicRaised, borderColor: colors.cosmicLine }]}
        activeOpacity={0.75}
        accessibilityRole="button"
        accessibilityLabel={t('karmaAnalysis.a11yGoBack')}
      >
        <Ionicons name="arrow-back" size={21} color={colors.textInverse} />
      </TouchableOpacity>
      <View style={styles.karmaTopBarCopy}>
        <Text style={[styles.karmaTopBarEyebrow, { color: colors.accent }]}>{t('premiumUi.karma.soulPatterns')}</Text>
        <Text style={[styles.karmaTopBarTitle, { color: colors.textInverse }]}>{t('premiumUi.karma.title')}</Text>
      </View>
      {showActions ? (
        <View style={styles.headerActions}>
          <TouchableOpacity onPress={generateKarmaPDF} style={[styles.headerIconBtn, { backgroundColor: colors.cosmicRaised, borderColor: colors.cosmicLine }]} disabled={generatingPDF} accessibilityLabel={t('karmaAnalysis.a11ySharePdf')}>
            {generatingPDF ? <ActivityIndicator size="small" color={colors.accent} /> : <Ionicons name="share-outline" size={20} color={colors.textInverse} />}
          </TouchableOpacity>
          <TouchableOpacity onPress={handleRegenerate} style={[styles.headerIconBtn, { backgroundColor: colors.cosmicRaised, borderColor: colors.cosmicLine }]} accessibilityLabel={t('karmaAnalysis.a11yRegenerate')}>
            <Ionicons name="refresh" size={20} color={colors.textInverse} />
          </TouchableOpacity>
        </View>
      ) : (
        <NativeSelectorChip
          birthData={{ name: nativeName }}
          onPress={() => navigation.navigate('SelectNative', { returnTo: 'KarmaAnalysis' })}
          maxLength={8}
          showIcon={false}
          style={{ backgroundColor: colors.cosmicRaised, borderColor: colors.cosmicLine }}
          textStyle={{ color: colors.textInverseMuted }}
          iconColor={colors.accent}
        />
      )}
    </View>
  );

  if (loading) {
    return (
      <View style={[styles.container, { backgroundColor: colors.background }]}>
        <StatusBar barStyle="light-content" backgroundColor={colors.headerSurface} />
        {renderKarmaTopBar()}
        <Animated.View style={[styles.loadingContainer, { opacity: Platform.OS === 'web' ? 1 : fadeAnim }]}>
          <View style={[styles.cosmicLoader, { backgroundColor: colors.cosmicSurface, borderColor: colors.cosmicLine }]}>
            <Ionicons name="infinite-outline" size={34} color={colors.accent} />
          </View>
          <ActivityIndicator size="small" color={colors.primary} style={styles.spinner} />
          <Text style={[styles.loadingTitle, { color: colors.text }]}>{uiText.loadingTitle}</Text>
          <Text style={[styles.loadingSubtitle, { color: colors.textSecondary }]}>
            {showProgress ? uiText.loadingSubtitleProgress : uiText.loadingSubtitleSlow}
          </Text>
          {showProgress && (
            <View style={styles.progressBarContainer}>
              <View style={[styles.progressBarBackground, { backgroundColor: colors.surfaceMuted }]}>
                <View style={[styles.progressBarFill, { width: `${progress}%`, backgroundColor: colors.primary }]} />
              </View>
              <Text style={[styles.progressText, { color: colors.primaryStrong }]}>{Math.round(progress)}%</Text>
            </View>
          )}
        </Animated.View>
      </View>
    );
  }

  if (error) {
    return (
      <View style={[styles.container, { backgroundColor: colors.background }]}>
        <StatusBar barStyle="light-content" backgroundColor={colors.headerSurface} />
        {renderKarmaTopBar()}
        <View style={styles.errorContainer}>
          <View style={[styles.errorIcon, { backgroundColor: colors.errorSoft || colors.surfaceMuted }]}><Ionicons name="alert-circle-outline" size={28} color={colors.error} /></View>
          <Text style={[styles.errorTitle, { color: colors.text }]}>{uiText.errorTitle}</Text>
          <Text style={[styles.errorText, { color: colors.textSecondary }]}>{error}</Text>
          <TouchableOpacity style={[styles.retryButton, { backgroundColor: colors.primary }]} onPress={() => initiateAnalysis(false)}>
            <Text style={[styles.retryText, { color: colors.onPrimary }]}>{t('karmaAnalysis.tryAgain')}</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.errorBackRow, { borderColor: colors.cardBorder, backgroundColor: colors.cardBackground }]}
            onPress={() => navigation.goBack()}
            activeOpacity={0.75}
            accessibilityRole="button"
            accessibilityLabel={t('karmaAnalysis.a11yGoBack')}
          >
            <Ionicons name="arrow-back" size={20} color={colors.primaryStrong} />
            <Text style={[styles.errorBackRowText, { color: colors.textSecondary }]}>{t('karmaAnalysis.goBack')}</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  if (!analysis && !loading && !error) {
    return (
      <View style={[styles.container, { backgroundColor: colors.background }]}>
        <StatusBar barStyle="light-content" backgroundColor={colors.headerSurface} />
        {renderKarmaTopBar()}
        <ScrollView contentContainerStyle={styles.startScrollContent} showsVerticalScrollIndicator={false}>
          <View style={[styles.startHero, { backgroundColor: colors.cosmicSurface, borderColor: colors.cosmicLine }]}>
            <View style={[styles.orbitLarge, { borderColor: colors.cosmicLine }]} />
            <View style={[styles.orbitSmall, { borderColor: colors.cosmicLine }]} />
            <Text style={[styles.heroEyebrow, { color: colors.accent }]}>{t('premiumUi.karma.pastPresent')}</Text>
            <Text style={[styles.startTitle, { color: colors.textInverse }]}>{uiText.startTitle}</Text>
            <Text style={[styles.startSubtitle, { color: colors.textInverseMuted }]}>{uiText.startSubtitle}</Text>
            <View style={[styles.readingForRow, { borderTopColor: colors.cosmicLine }]}>
              <View style={[styles.readingAvatar, { backgroundColor: colors.cosmicRaised, borderColor: colors.cosmicLine }]}><Text style={[styles.readingAvatarText, { color: colors.accent }]}>{nativeName?.charAt(0)?.toUpperCase()}</Text></View>
              <View style={styles.readingForCopy}><Text style={[styles.readingForLabel, { color: colors.textInverseMuted }]}>{t('premiumUi.karma.readingFor')}</Text><Text style={[styles.readingForName, { color: colors.textInverse }]}>{nativeName}</Text></View>
              <TouchableOpacity onPress={() => navigation.navigate('SelectNative', { returnTo: 'KarmaAnalysis' })}><Text style={[styles.changeChartText, { color: colors.accent }]}>{t('premiumUi.common.change')}</Text></TouchableOpacity>
            </View>
          </View>
          <View style={styles.includedSection}>
            <Text style={[styles.sectionEyebrow, { color: colors.primaryStrong }]}>{t('premiumUi.karma.whatTaraExplores')}</Text>
            <Text style={[styles.sectionTitle, { color: colors.text }]}>{t('premiumUi.karma.deeperSynthesis')}</Text>
            {[
              ['repeat-outline', t('premiumUi.karma.repeatingThemes'), t('premiumUi.karma.repeatingBody')],
              ['git-branch-outline', t('premiumUi.karma.karmicSignatures'), t('premiumUi.karma.signaturesBody')],
              ['compass-outline', t('premiumUi.karma.pathForward'), t('premiumUi.karma.pathBody')],
            ].map(([icon, title, body], index) => (
              <View key={title} style={[styles.includedRow, index < 2 && { borderBottomColor: colors.cardBorder, borderBottomWidth: StyleSheet.hairlineWidth }]}>
                <View style={[styles.includedIcon, { backgroundColor: colors.accentSoft }]}><Ionicons name={icon} size={20} color={colors.primaryStrong} /></View>
                <View style={styles.includedCopy}><Text style={[styles.includedTitle, { color: colors.text }]}>{title}</Text><Text style={[styles.includedBody, { color: colors.textSecondary }]}>{body}</Text></View>
              </View>
            ))}
          </View>
          <TouchableOpacity style={[styles.startButton, { backgroundColor: colors.primary }]} onPress={handleStartAnalysis}>
            <Ionicons name="sparkles-outline" size={18} color={colors.onPrimary} />
            <Text style={[styles.startButtonText, { color: colors.onPrimary }]}>{isIosKarmaStudy ? 'Start Study' : t('karmaAnalysis.startButton')}</Text>
            <View style={[styles.creditPill, { backgroundColor: colors.primaryStrong }]}><Text style={[styles.creditPillText, { color: colors.onPrimary }]}>{t('premiumUi.karma.credits', { count: karmaCost })}</Text></View>
          </TouchableOpacity>
        </ScrollView>
        <AnalysisCreditModal
          visible={showStartModal}
          onClose={() => setShowStartModal(false)}
          onConfirm={confirmStartAnalysis}
          onGetCredits={() => {
            setShowStartModal(false);
            navigation.navigate('Credits');
          }}
          credits={credits}
          cost={karmaCost}
          title={uiText.confirmStartTitle}
          canAfford={credits >= karmaCost}
          description={credits >= karmaCost
            ? t('karmaAnalysis.creditsModalWillUse', { cost: karmaCost })
            : t('karmaAnalysis.insufficientCreditsBody', { cost: karmaCost })}
          confirmLabel={t('karmaAnalysis.creditsModalConfirm')}
          getCreditsLabel={t('karmaAnalysis.getCredits')}
          cancelLabel={t('karmaAnalysis.creditsModalCancel')}
          confirmGradientColors={[colors.primary, colors.secondary]}
        />
      </View>
    );
  }

  const sections = analysis?.sections || {};
  const sectionKeys = Object.keys(sections);

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      <StatusBar barStyle="light-content" backgroundColor={colors.headerSurface} />
        {renderKarmaTopBar({ showActions: true })}
        <AnalysisCreditModal
          visible={showRegenerateModal}
          onClose={() => setShowRegenerateModal(false)}
          onConfirm={confirmRegenerate}
          onGetCredits={() => {
            setShowRegenerateModal(false);
            navigation.navigate('Credits');
          }}
          credits={credits}
          cost={karmaCost}
          title={uiText.confirmRegenerateTitle}
          canAfford={credits >= karmaCost}
          description={credits >= karmaCost
            ? t('karmaAnalysis.creditsModalWillUse', { cost: karmaCost })
            : t('karmaAnalysis.insufficientCreditsBody', { cost: karmaCost })}
          confirmLabel={t('karmaAnalysis.creditsModalConfirm')}
          getCreditsLabel={t('karmaAnalysis.getCredits')}
          cancelLabel={t('karmaAnalysis.creditsModalCancel')}
          confirmGradientColors={[colors.primary, colors.secondary]}
        />
        <ScrollView 
          showsVerticalScrollIndicator={false} 
          contentContainerStyle={styles.scrollContent}
          bounces={true}
        >
          <Animated.View style={{ opacity: Platform.OS === 'web' ? 1 : fadeAnim }}>
            <View style={[styles.resultHero, { backgroundColor: colors.cosmicSurface, borderColor: colors.cosmicLine }]}>
              <View style={[styles.orbitLarge, { borderColor: colors.cosmicLine }]} />
              <Text style={[styles.heroEyebrow, { color: colors.accent }]}>{t('premiumUi.karma.karmicMap')}</Text>
              <Text style={[styles.resultTitle, { color: colors.textInverse }]}>{uiText.resultTitle}</Text>
              <Text style={[styles.resultSubtitle, { color: colors.textInverseMuted }]}>{uiText.resultSubtitle}</Text>
              <View style={[styles.resultMeta, { borderTopColor: colors.cosmicLine }]}>
                <TouchableOpacity onPress={() => navigation.navigate('SelectNative', { returnTo: 'KarmaAnalysis' })}><Text style={[styles.resultMetaLabel, { color: colors.textInverseMuted }]}>{t('premiumUi.karma.readingForChange')}</Text><Text style={[styles.resultMetaValue, { color: colors.textInverse }]}>{nativeName}</Text></TouchableOpacity>
                <View style={styles.resultMetaRight}><Text style={[styles.resultMetaLabel, { color: colors.textInverseMuted }]}>{t('premiumUi.karma.chapters')}</Text><Text style={[styles.resultMetaValue, { color: colors.accent }]}>{sectionKeys.length}</Text></View>
              </View>
            </View>

            <View style={styles.readingHeading}><Text style={[styles.sectionEyebrow, { color: colors.primaryStrong }]}>{t('premiumUi.karma.interpretation')}</Text><Text style={[styles.sectionTitle, { color: colors.text }]}>{t('premiumUi.karma.karmicChapters')}</Text></View>

            {sectionKeys.map((key, index) => (
              <KarmaCard
                key={index}
                title={key}
                content={sections[key]}
                index={index}
                colors={colors}
                resolveSectionTitle={resolveSectionTitle}
              />
            ))}

            <View style={styles.footerContainer}>
              <View style={[styles.footerGradient, { backgroundColor: colors.cardBackground, borderColor: colors.cardBorder }]}>
                <View style={[styles.footerIcon, { backgroundColor: colors.accentSoft }]}><Ionicons name="sparkles-outline" size={20} color={colors.primaryStrong} /></View>
                <Text style={[styles.footerText, { color: colors.text }]}>{uiText.footerAnalyzedBy}</Text>
                <Text style={[styles.footerSubtext, { color: colors.textSecondary }]}>{uiText.footerAI}</Text>
              </View>
            </View>
          </Animated.View>
        </ScrollView>
    </View>
  );
};

const KarmaCard = ({ title, content, index, colors, resolveSectionTitle }) => {
  const [expanded, setExpanded] = useState(index === 0);
  const icons = ['book-outline', 'repeat-outline', 'git-branch-outline', 'scale-outline', 'diamond-outline', 'flame-outline', 'people-outline', 'leaf-outline', 'hand-left-outline', 'hourglass-outline'];
  const displayTitle = resolveSectionTitle ? resolveSectionTitle(title) : title;

  const formatContent = (text) => {
    // Clean up text first
    const cleanText = String(text || '').trim();
    
    // Split by markdown patterns while preserving them
    const parts = [];
    let lastIndex = 0;
    
    // Match **bold** and *italic* patterns (non-greedy, must have closing tag)
    const regex = /\*\*(.+?)\*\*|\*([^*]+?)\*/g;
    let match;
    
    while ((match = regex.exec(cleanText)) !== null) {
      // Add text before match
      if (match.index > lastIndex) {
        parts.push({ text: cleanText.slice(lastIndex, match.index), style: 'normal' });
      }
      
      // Add matched text with style
      if (match[1]) {
        // Bold (**text**)
        parts.push({ text: match[1], style: 'bold' });
      } else if (match[2]) {
        // Italic (*text*)
        parts.push({ text: match[2], style: 'italic' });
      }
      
      lastIndex = regex.lastIndex;
    }
    
    // Add remaining text
    if (lastIndex < cleanText.length) {
      parts.push({ text: cleanText.slice(lastIndex), style: 'normal' });
    }
    
    // Clean up standalone asterisks in normal text parts only
    return parts.map(part => {
      if (part.style === 'normal') {
        // Replace asterisks with space, then clean up multiple spaces
        return { ...part, text: part.text.replace(/\*/g, ' ').replace(/\s+/g, ' ') };
      }
      return part;
    });
  };

  const renderFormattedText = (text) => {
    // Split by single or double newlines to get paragraphs
    const paragraphs = text.split(/\n+/).filter(p => p.trim().length > 0);
    
    return (
      <View>
        {paragraphs.map((para, paraIndex) => {
          const parts = formatContent(para);
          return (
            <Text key={paraIndex} style={[styles.cardContent, { color: colors.textSecondary }, paraIndex > 0 && styles.paragraphSpacing]}>
              {parts.map((part, index) => (
                <Text
                  key={index}
                  style={[
                    styles.cardContent,
                    { color: colors.textSecondary },
                    part.style === 'bold' && { fontWeight: '800', color: colors.text },
                    part.style === 'italic' && { fontStyle: 'italic', color: colors.primaryStrong },
                  ]}
                >
                  {index === 0 ? part.text.trimStart() : part.text}
                </Text>
              ))}
            </Text>
          );
        })}
      </View>
    );
  };

  return (
    <View style={styles.cardWrapper}>
      <View style={[styles.glassCard, { backgroundColor: colors.cardBackground, borderColor: colors.cardBorder }]}>
        <TouchableOpacity 
          style={styles.cardHeader}
          onPress={() => setExpanded(!expanded)}
          activeOpacity={0.8}
        >
          <View style={[styles.iconCircle, { backgroundColor: expanded ? colors.selectionSurface : colors.accentSoft, borderColor: expanded ? colors.selectionBorder : colors.cardBorder }]}>
            <Ionicons name={icons[index % icons.length]} size={20} color={expanded ? colors.selectionText : colors.primaryStrong} />
          </View>
          <View style={styles.cardTitleWrap}><Text style={[styles.cardNumber, { color: colors.primaryStrong }]}>{String(index + 1).padStart(2, '0')}</Text><Text style={[styles.cardTitle, { color: colors.text }]}>{displayTitle}</Text></View>
          <View style={[styles.expandIcon, { backgroundColor: expanded ? colors.primary : colors.surfaceMuted }]}><Ionicons name={expanded ? 'remove' : 'add'} size={18} color={expanded ? colors.onPrimary : colors.textSecondary} /></View>
        </TouchableOpacity>
        {expanded && (
          <View style={styles.cardContentContainer}>
            <View style={[styles.contentDivider, { backgroundColor: colors.cardBorder }]} />
            {renderFormattedText(content)}
          </View>
        )}
      </View>
    </View>
  );
};

const legacyStyles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#1a0033',
  },
  backgroundGradient: {
    flex: 1,
  },
  scrollContent: {
    paddingHorizontal: 16,
    paddingTop: 10,
    paddingBottom: 40,
  },
  karmaTopBar: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 14,
    paddingBottom: 12,
    borderBottomWidth: StyleSheet.hairlineWidth,
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 1 },
        shadowOpacity: 0.06,
        shadowRadius: 3,
      },
      android: {
        elevation: 1,
      },
    }),
  },
  karmaTopBarSide: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'flex-start',
    minWidth: 44,
  },
  karmaTopBarSideRight: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'flex-end',
    gap: 8,
    minWidth: 44,
  },
  karmaTopBarCenter: {
    flexShrink: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 6,
    maxWidth: '52%',
  },
  headerIconBtn: {
    width: 44,
    height: 44,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: StyleSheet.hairlineWidth * 2,
  },
  headerIconBtnDisabled: {
    opacity: 0.55,
  },
  headerRightSpacer: {
    width: 44,
    height: 44,
  },
  nameChip: {
    flexDirection: 'row',
    alignItems: 'center',
    maxWidth: '100%',
    paddingHorizontal: 14,
    paddingVertical: 9,
    borderRadius: 20,
    borderWidth: 1,
  },
  nameChipStatic: {
    paddingRight: 14,
  },
  nameChipText: {
    fontSize: 14,
    fontWeight: '700',
    flexShrink: 1,
  },
  nameChipChevron: {
    marginLeft: 4,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
  },
  cosmicLoader: {
    width: 120,
    height: 120,
    borderRadius: 60,
    backgroundColor: 'rgba(255, 215, 0, 0.1)',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 30,
    borderWidth: 2,
    borderColor: 'rgba(255, 215, 0, 0.3)',
  },
  omSymbol: {
    fontSize: 60,
  },
  spinner: {
    marginVertical: 20,
  },
  loadingTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#FFD700',
    marginTop: 20,
    textAlign: 'center',
  },
  loadingSubtitle: {
    fontSize: 16,
    color: 'rgba(255, 255, 255, 0.7)',
    marginTop: 10,
    textAlign: 'center',
    fontStyle: 'italic',
  },
  progressBarContainer: {
    width: '70%',
    marginTop: 20,
    alignItems: 'center',
  },
  progressBarBackground: {
    width: '100%',
    height: 8,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    borderRadius: 4,
    overflow: 'hidden',
  },
  progressBarFill: {
    height: '100%',
    backgroundColor: '#FFD700',
    borderRadius: 4,
  },
  progressText: {
    color: '#FFD700',
    fontSize: 14,
    marginTop: 8,
    fontWeight: '600',
  },
  dotsContainer: {
    flexDirection: 'row',
    marginTop: 30,
  },
  dot: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: '#FFD700',
    marginHorizontal: 5,
  },
  headerContainer: {
    marginBottom: 30,
  },
  headerGlow: {
    borderRadius: 16,
    padding: 30,
    alignItems: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.15)',
    borderWidth: 0.5,
    borderColor: 'rgba(255, 255, 255, 0.3)',
  },
  omHeader: {
    fontSize: 50,
    marginBottom: 15,
  },
  title: {
    fontSize: 36,
    fontWeight: 'bold',
    color: '#FFD700',
    marginBottom: 8,
    textAlign: 'center',
    letterSpacing: 1,
  },
  subtitle: {
    fontSize: 16,
    color: 'rgba(255, 255, 255, 0.8)',
    fontStyle: 'italic',
    textAlign: 'center',
  },
  divider: {
    width: 100,
    height: 2,
    backgroundColor: 'rgba(255, 215, 0, 0.5)',
    marginTop: 15,
    borderRadius: 1,
  },
  cardWrapper: {
    marginBottom: 20,
  },
  glassCard: {
    backgroundColor: 'rgba(255, 255, 255, 0.15)',
    borderRadius: 16,
    borderWidth: 0.5,
    borderColor: 'rgba(255, 255, 255, 0.3)',
    overflow: 'hidden',
    shadowColor: 'rgba(0, 0, 0, 0.3)',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 12,
    elevation: 5,
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 18,
  },
  iconCircle: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: 'rgba(255, 215, 0, 0.2)',
    borderWidth: 0.5,
    borderColor: 'rgba(255, 215, 0, 0.4)',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  introIconCircle: {
    backgroundColor: 'rgba(139, 69, 19, 0.3)',
    borderColor: 'rgba(139, 69, 19, 0.6)',
  },
  cardIcon: {
    fontSize: 26,
  },
  cardTitle: {
    flex: 1,
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
    letterSpacing: 0.5,
  },
  expandIcon: {
    fontSize: 16,
    color: 'rgba(255, 255, 255, 0.8)',
    marginLeft: 10,
  },
  cardContentContainer: {
    paddingHorizontal: 20,
    paddingBottom: 20,
  },
  contentDivider: {
    height: 0.5,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    marginBottom: 16,
  },
  cardContent: {
    fontSize: 15,
    lineHeight: 24,
    color: 'rgba(255, 255, 255, 0.95)',
    textAlign: 'justify',
  },
  boldText: {
    fontWeight: '700',
    color: '#FFD700',
  },
  italicText: {
    fontStyle: 'italic',
    color: 'rgba(255, 215, 0, 0.9)',
  },
  introBoldText: {
    fontWeight: '700',
    color: '#4a0080',
  },
  introItalicText: {
    fontStyle: 'italic',
    color: '#4a0080',
  },
  paragraphSpacing: {
    marginTop: 12,
  },
  footerContainer: {
    marginTop: 30,
    marginBottom: 20,
  },
  footerGradient: {
    borderRadius: 16,
    padding: 25,
    alignItems: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.15)',
    borderWidth: 0.5,
    borderColor: 'rgba(255, 255, 255, 0.3)',
  },
  footerIcon: {
    fontSize: 30,
    marginBottom: 10,
  },
  footerText: {
    fontSize: 16,
    color: '#FFD700',
    fontWeight: 'bold',
    marginBottom: 5,
  },
  footerSubtext: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.6)',
    fontStyle: 'italic',
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
  },
  errorIcon: {
    fontSize: 60,
    marginBottom: 20,
  },
  errorTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#FFD700',
    marginBottom: 15,
    textAlign: 'center',
  },
  errorText: {
    fontSize: 16,
    color: 'rgba(255, 255, 255, 0.8)',
    textAlign: 'center',
    marginBottom: 30,
    lineHeight: 24,
  },
  retryButton: {
    borderRadius: 30,
    overflow: 'hidden',
    marginBottom: 15,
  },
  retryGradient: {
    paddingHorizontal: 40,
    paddingVertical: 15,
  },
  retryText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1a0033',
  },
  errorBackRow: {
    marginTop: 10,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    paddingVertical: 12,
    paddingHorizontal: 18,
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth * 2,
  },
  errorBackRowText: {
    fontSize: 16,
    fontWeight: '600',
  },
  startContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
  },
  startTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#FFD700',
    marginTop: 20,
    textAlign: 'center',
  },
  startSubtitle: {
    fontSize: 16,
    color: 'rgba(255, 255, 255, 0.7)',
    marginTop: 10,
    marginBottom: 40,
    textAlign: 'center',
  },
  startButton: {
    borderRadius: 30,
    overflow: 'hidden',
  },
  startGradient: {
    paddingHorizontal: 50,
    paddingVertical: 16,
  },
  startButtonText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1a0033',
  },
});

const styles = StyleSheet.create({
  container: { flex: 1 },
  karmaTopBar: { minHeight: 77, paddingHorizontal: 18, paddingBottom: 10, borderBottomWidth: StyleSheet.hairlineWidth, flexDirection: 'row', alignItems: 'center', gap: 12 },
  karmaTopBarCopy: { flex: 1 },
  karmaTopBarEyebrow: { ...typographyTokens.eyebrow, fontSize: 8, marginBottom: 3 },
  karmaTopBarTitle: { ...typographyTokens.sectionTitle, fontSize: 22 },
  headerActions: { flexDirection: 'row', gap: 8 },
  headerIconBtn: { width: 42, height: 42, borderRadius: 21, borderWidth: 1, alignItems: 'center', justifyContent: 'center' },
  loadingContainer: { flex: 1, justifyContent: 'center', alignItems: 'center', paddingHorizontal: 34 },
  cosmicLoader: { width: 66, height: 66, borderRadius: 33, borderWidth: 1, justifyContent: 'center', alignItems: 'center', marginBottom: 16 },
  spinner: { marginBottom: 15 },
  loadingTitle: { ...typographyTokens.sectionTitle, fontSize: 23, textAlign: 'center' },
  loadingSubtitle: { fontSize: 14, lineHeight: 21, textAlign: 'center', marginTop: 8 },
  progressBarContainer: { width: '78%', marginTop: 22, alignItems: 'center' },
  progressBarBackground: { width: '100%', height: 6, borderRadius: 3, overflow: 'hidden' },
  progressBarFill: { height: '100%', borderRadius: 3 },
  progressText: { fontSize: 11, fontWeight: '800', marginTop: 8 },
  errorContainer: { flex: 1, justifyContent: 'center', alignItems: 'center', paddingHorizontal: 34 },
  errorIcon: { width: 60, height: 60, borderRadius: 30, alignItems: 'center', justifyContent: 'center', marginBottom: 17 },
  errorTitle: { ...typographyTokens.sectionTitle, fontSize: 23, textAlign: 'center', marginBottom: 8 },
  errorText: { fontSize: 14, lineHeight: 21, textAlign: 'center', marginBottom: 22 },
  retryButton: { minHeight: 46, borderRadius: 23, paddingHorizontal: 26, alignItems: 'center', justifyContent: 'center' },
  retryText: { fontSize: 13, fontWeight: '800' },
  errorBackRow: { marginTop: 10, flexDirection: 'row', alignItems: 'center', gap: 8, paddingVertical: 11, paddingHorizontal: 18, borderRadius: 22, borderWidth: 1 },
  errorBackRowText: { fontSize: 13, fontWeight: '700' },
  startScrollContent: { paddingHorizontal: 18, paddingTop: 18, paddingBottom: 44 },
  startHero: { borderRadius: 28, borderWidth: 1, padding: 24, overflow: 'hidden' },
  orbitLarge: { position: 'absolute', width: 184, height: 184, borderRadius: 92, borderWidth: 1, right: -78, top: -88 },
  orbitSmall: { position: 'absolute', width: 120, height: 120, borderRadius: 60, borderWidth: 1, right: -12, top: -62 },
  heroEyebrow: { ...typographyTokens.eyebrow, fontSize: 9, marginBottom: 14 },
  startTitle: { ...typographyTokens.display, fontSize: 38, lineHeight: 42, maxWidth: 290 },
  startSubtitle: { fontSize: 15, lineHeight: 23, marginTop: 12, maxWidth: 300 },
  readingForRow: { borderTopWidth: StyleSheet.hairlineWidth, marginTop: 24, paddingTop: 17, flexDirection: 'row', alignItems: 'center', gap: 11 },
  readingAvatar: { width: 40, height: 40, borderRadius: 20, borderWidth: 1, alignItems: 'center', justifyContent: 'center' },
  readingAvatarText: { ...typographyTokens.sectionTitle, fontSize: 18 },
  readingForCopy: { flex: 1 },
  readingForLabel: { ...typographyTokens.eyebrow, fontSize: 8, marginBottom: 2 },
  readingForName: { ...typographyTokens.sectionTitle, fontSize: 17 },
  changeChartText: { fontSize: 12, fontWeight: '800' },
  includedSection: { paddingVertical: 27 },
  sectionEyebrow: { ...typographyTokens.eyebrow, fontSize: 9, marginBottom: 5 },
  sectionTitle: { ...typographyTokens.sectionTitle, fontSize: 25 },
  includedRow: { minHeight: 80, flexDirection: 'row', alignItems: 'center', gap: 13, paddingVertical: 13 },
  includedIcon: { width: 44, height: 44, borderRadius: 15, alignItems: 'center', justifyContent: 'center' },
  includedCopy: { flex: 1 },
  includedTitle: { ...typographyTokens.sectionTitle, fontSize: 17, marginBottom: 3 },
  includedBody: { fontSize: 12, lineHeight: 18 },
  startButton: { minHeight: 56, borderRadius: 28, paddingHorizontal: 17, flexDirection: 'row', alignItems: 'center', gap: 9 },
  startButtonText: { flex: 1, fontSize: 14, fontWeight: '800' },
  creditPill: { borderRadius: 999, paddingHorizontal: 10, paddingVertical: 6 },
  creditPillText: { fontSize: 9, fontWeight: '800', textTransform: 'uppercase', letterSpacing: 0.4 },
  scrollContent: { paddingHorizontal: 18, paddingTop: 18, paddingBottom: 46 },
  resultHero: { borderRadius: 28, borderWidth: 1, padding: 24, overflow: 'hidden', marginBottom: 28 },
  resultTitle: { ...typographyTokens.display, fontSize: 38, lineHeight: 42, maxWidth: 290 },
  resultSubtitle: { fontSize: 15, lineHeight: 22, marginTop: 10 },
  resultMeta: { borderTopWidth: StyleSheet.hairlineWidth, marginTop: 22, paddingTop: 17, flexDirection: 'row', justifyContent: 'space-between' },
  resultMetaRight: { alignItems: 'flex-end' },
  resultMetaLabel: { ...typographyTokens.eyebrow, fontSize: 8, marginBottom: 4 },
  resultMetaValue: { ...typographyTokens.sectionTitle, fontSize: 17 },
  readingHeading: { marginBottom: 14 },
  cardWrapper: { marginBottom: 11 },
  glassCard: { borderRadius: 21, borderWidth: 1, overflow: 'hidden' },
  cardHeader: { minHeight: 76, flexDirection: 'row', alignItems: 'center', paddingHorizontal: 14, paddingVertical: 12, gap: 12 },
  iconCircle: { width: 44, height: 44, borderRadius: 15, borderWidth: 1, justifyContent: 'center', alignItems: 'center' },
  cardTitleWrap: { flex: 1 },
  cardNumber: { ...typographyTokens.eyebrow, fontSize: 8, marginBottom: 3 },
  cardTitle: { ...typographyTokens.sectionTitle, fontSize: 17, lineHeight: 21 },
  expandIcon: { width: 30, height: 30, borderRadius: 15, alignItems: 'center', justifyContent: 'center' },
  cardContentContainer: { paddingHorizontal: 17, paddingBottom: 20 },
  contentDivider: { height: StyleSheet.hairlineWidth, marginBottom: 16 },
  cardContent: { fontSize: 14, lineHeight: 23 },
  paragraphSpacing: { marginTop: 13 },
  footerContainer: { marginTop: 22, marginBottom: 10 },
  footerGradient: { borderRadius: 20, padding: 22, alignItems: 'center', borderWidth: 1 },
  footerIcon: { width: 44, height: 44, borderRadius: 22, alignItems: 'center', justifyContent: 'center', marginBottom: 11 },
  footerText: { ...typographyTokens.sectionTitle, fontSize: 16, marginBottom: 4, textAlign: 'center' },
  footerSubtext: { fontSize: 11, textAlign: 'center' },
});

export default KarmaAnalysisScreen;
