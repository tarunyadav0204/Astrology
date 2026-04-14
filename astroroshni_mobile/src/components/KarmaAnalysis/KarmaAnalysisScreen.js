import React, { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import i18n from '../../locales/i18n';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  ActivityIndicator,
  Dimensions,
  TouchableOpacity,
  Animated,
  Alert,
  Modal,
  Platform,
} from 'react-native';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as Print from 'expo-print';
import * as Sharing from 'expo-sharing';
import { API_BASE_URL, getEndpoint } from '../../utils/constants';
import { useTheme } from '../../context/ThemeContext';
import { useFocusEffect } from '@react-navigation/native';
import { storage } from '../../services/storage';
import { useCredits } from '../../credits/CreditContext';
import { pricingAPI } from '../../services/api';
import { useAnalytics } from '../../hooks/useAnalytics';
import { trackAstrologyEvent } from '../../utils/analytics';

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

const { width, height } = Dimensions.get('window');

const KarmaAnalysisScreen = ({ route, navigation }) => {
  useAnalytics('KarmaAnalysisScreen');
  const { t } = useTranslation();
  const { theme, colors } = useTheme();
  const insets = useSafeAreaInsets();
  const isDark = theme === 'dark';
  const { chartId } = route.params || {};
  const { credits, fetchBalance } = useCredits();

  const screenGradient = isDark
    ? [colors.gradientStart, colors.gradientMid, colors.gradientEnd]
    : [colors.background, colors.backgroundSecondary, colors.backgroundTertiary];
  const screenGradientWithAccent = isDark
    ? [...screenGradient, colors.primary]
    : [...screenGradient, colors.primary];
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
  }, [selectedChartId]);

  useEffect(() => {
    if (selectedChartId && !loading && !isChangingChart) {
      checkExistingAnalysis();
    }
    Animated.timing(fadeAnim, {
      toValue: 1,
      duration: 1000,
      useNativeDriver: true,
    }).start();
    return () => {
      if (pollingInterval) clearInterval(pollingInterval);
    };
  }, [selectedChartId, isChangingChart]);

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

  const handleStartAnalysis = () => {
    if (credits < karmaCost) {
      Alert.alert(
        t('karmaAnalysis.insufficientCreditsTitle'),
        t('karmaAnalysis.insufficientCreditsBody', { cost: karmaCost }),
        [
          { text: t('karmaAnalysis.getCredits'), onPress: () => navigation.navigate('Credits') },
          { text: t('karmaAnalysis.cancel'), style: 'cancel' },
        ]
      );
      return;
    }
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
    if (credits < karmaCost) {
      Alert.alert(
        t('karmaAnalysis.insufficientCreditsTitle'),
        t('karmaAnalysis.insufficientCreditsBody', { cost: karmaCost }),
        [
          { text: t('karmaAnalysis.getCredits'), onPress: () => navigation.navigate('Credits') },
          { text: t('karmaAnalysis.cancel'), style: 'cancel' },
        ]
      );
      return;
    }
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
                <div class="title">${t('karmaAnalysis.pdfDocTitle')}</div>
                <div class="subtitle">${t('karmaAnalysis.pdfDocSubtitle')}</div>
                <div class="native-name">${nativeName}</div>
                <div class="timestamp">${new Date().toLocaleString()}</div>
              </div>
              ${contentHTML}
              <div class="footer">
                ${t('karmaAnalysis.pdfFooterLine1')}<br>
                ${t('karmaAnalysis.pdfFooterLine2')}
              </div>
            </div>
          </body>
        </html>
      `;
      
      console.log('[PDF] HTML generated, calling printToFileAsync...');
      const { uri } = await Promise.race([
        Print.printToFileAsync({ html }),
        new Promise((_, reject) => 
          setTimeout(() => reject(new Error(i18n.t('karmaAnalysis.pdfTimeoutError'))), 30000)
        )
      ]);
      
      console.log('[PDF] Generated successfully:', uri);
      console.log('[PDF] Sharing...');
      
      await Sharing.shareAsync(uri, {
        mimeType: 'application/pdf',
        dialogTitle: t('karmaAnalysis.pdfShareTitle'),
        UTI: 'com.adobe.pdf',
      });
      
      console.log('[PDF] Share completed');
      setGeneratingPDF(false);
    } catch (error) {
      console.error('[PDF] Error:', error);
      setGeneratingPDF(false);
      Alert.alert(
        t('karmaAnalysis.pdfErrorTitle'),
        t('karmaAnalysis.pdfErrorBody', { message: error.message })
      );
    }
  };

  const headerBorder = isDark ? 'rgba(255,215,0,0.14)' : colors.cardBorder;
  const headerIconBg = isDark ? 'rgba(255,255,255,0.08)' : colors.surface;
  const headerIconBorder = isDark ? 'rgba(255,215,0,0.3)' : colors.cardBorder;

  const renderKarmaTopBar = ({ nativeInteractive = false, rightSlot }) => (
    <View
      style={[
        styles.karmaTopBar,
        {
          paddingTop: Math.max(insets.top, 12) + 6,
          borderBottomColor: headerBorder,
        },
      ]}
    >
      <View style={styles.karmaTopBarSide}>
        <TouchableOpacity
          onPress={() => navigation.goBack()}
          style={[styles.headerIconBtn, { backgroundColor: headerIconBg, borderColor: headerIconBorder }]}
          activeOpacity={0.75}
          accessibilityRole="button"
          accessibilityLabel={t('karmaAnalysis.a11yGoBack')}
        >
          <Ionicons name="arrow-back" size={22} color={colors.accent} />
        </TouchableOpacity>
      </View>
      <View style={styles.karmaTopBarCenter} pointerEvents="box-none">
        {nativeInteractive ? (
          <TouchableOpacity
            onPress={() => navigation.navigate('SelectNative', { returnTo: 'KarmaAnalysis' })}
            style={[
              styles.nameChip,
              {
                backgroundColor: isDark ? 'rgba(255,215,0,0.14)' : colors.surface,
                borderColor: isDark ? 'rgba(255,215,0,0.38)' : colors.cardBorder,
              },
            ]}
            activeOpacity={0.8}
            accessibilityRole="button"
            accessibilityLabel={t('karmaAnalysis.a11yChangeNative')}
          >
            <Text style={[styles.nameChipText, { color: colors.accent }]} numberOfLines={1}>
              {nativeName}
            </Text>
            <Ionicons name="chevron-down" size={17} color={colors.accent} style={styles.nameChipChevron} />
          </TouchableOpacity>
        ) : (
          <View
            style={[
              styles.nameChip,
              styles.nameChipStatic,
              {
                backgroundColor: isDark ? 'rgba(255,215,0,0.14)' : colors.surface,
                borderColor: isDark ? 'rgba(255,215,0,0.38)' : colors.cardBorder,
              },
            ]}
          >
            <Text style={[styles.nameChipText, { color: colors.accent }]} numberOfLines={1}>
              {nativeName}
            </Text>
          </View>
        )}
      </View>
      <View style={[styles.karmaTopBarSide, styles.karmaTopBarSideRight]}>{rightSlot}</View>
    </View>
  );

  if (loading) {
    return (
      <View style={[styles.container, { backgroundColor: colors.background }]}>
        <LinearGradient colors={screenGradient} style={StyleSheet.absoluteFill} />
        {renderKarmaTopBar({ rightSlot: <View style={styles.headerRightSpacer} /> })}
        <Animated.View style={[styles.loadingContainer, { opacity: fadeAnim }]}>
          <View style={[styles.cosmicLoader, { backgroundColor: isDark ? 'rgba(255,215,0,0.1)' : colors.surface, borderColor: isDark ? 'rgba(255,215,0,0.3)' : colors.cardBorder }]}>
            <Text style={styles.omSymbol}>🕉️</Text>
          </View>
          <ActivityIndicator size="large" color={colors.primary} style={styles.spinner} />
          <Text style={[styles.loadingTitle, { color: colors.accent }]}>{t('karmaAnalysis.loadingTitle')}</Text>
          <Text style={[styles.loadingSubtitle, { color: colors.textSecondary }]}>
            {showProgress ? t('karmaAnalysis.loadingSubtitleProgress') : t('karmaAnalysis.loadingSubtitleSlow')}
          </Text>
          {showProgress && (
            <View style={styles.progressBarContainer}>
              <View style={[styles.progressBarBackground, { backgroundColor: isDark ? 'rgba(255,255,255,0.2)' : colors.surface }]}>
                <View style={[styles.progressBarFill, { width: `${progress}%`, backgroundColor: colors.primary }]} />
              </View>
              <Text style={[styles.progressText, { color: colors.accent }]}>{Math.round(progress)}%</Text>
            </View>
          )}
          <View style={styles.dotsContainer}>
            <View style={[styles.dot, styles.dot1, { backgroundColor: colors.accent }]} />
            <View style={[styles.dot, styles.dot2, { backgroundColor: colors.accent }]} />
            <View style={[styles.dot, styles.dot3, { backgroundColor: colors.accent }]} />
          </View>
        </Animated.View>
      </View>
    );
  }

  if (error) {
    return (
      <View style={[styles.container, { backgroundColor: colors.background }]}>
        <LinearGradient colors={screenGradient} style={StyleSheet.absoluteFill} />
        {renderKarmaTopBar({ rightSlot: <View style={styles.headerRightSpacer} /> })}
        <View style={styles.errorContainer}>
          <Text style={styles.errorIcon}>⚠️</Text>
          <Text style={[styles.errorTitle, { color: colors.accent }]}>{t('karmaAnalysis.errorTitle')}</Text>
          <Text style={[styles.errorText, { color: colors.textSecondary }]}>{error}</Text>
          <TouchableOpacity style={styles.retryButton} onPress={() => initiateAnalysis(false)}>
            <LinearGradient colors={[colors.primary, colors.secondary]} style={styles.retryGradient}>
              <Text style={[styles.retryText, { color: '#fff' }]}>{t('karmaAnalysis.tryAgain')}</Text>
            </LinearGradient>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.errorBackRow, { borderColor: headerIconBorder, backgroundColor: headerIconBg }]}
            onPress={() => navigation.goBack()}
            activeOpacity={0.75}
            accessibilityRole="button"
            accessibilityLabel={t('karmaAnalysis.a11yGoBack')}
          >
            <Ionicons name="arrow-back" size={20} color={colors.accent} />
            <Text style={[styles.errorBackRowText, { color: colors.textSecondary }]}>{t('karmaAnalysis.goBack')}</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  if (!analysis && !loading && !error) {
    return (
      <View style={[styles.container, { backgroundColor: colors.background }]}>
        <LinearGradient colors={screenGradient} style={StyleSheet.absoluteFill} />
        {renderKarmaTopBar({
          nativeInteractive: true,
          rightSlot: <View style={styles.headerRightSpacer} />,
        })}
        <View style={styles.startContainer}>
          <Text style={styles.omSymbol}>🕉️</Text>
          <Text style={[styles.startTitle, { color: colors.accent }]}>{t('karmaAnalysis.startTitle')}</Text>
          <Text style={[styles.startSubtitle, { color: colors.textSecondary }]}>{t('karmaAnalysis.startSubtitle')}</Text>
          <TouchableOpacity style={styles.startButton} onPress={handleStartAnalysis}>
            <LinearGradient colors={[colors.primary, colors.secondary]} style={styles.startGradient}>
              <Text style={[styles.startButtonText, { color: '#fff' }]}>{t('karmaAnalysis.startButton')}</Text>
            </LinearGradient>
          </TouchableOpacity>
        </View>
        <CreditModal
          visible={showStartModal}
          onClose={() => setShowStartModal(false)}
          onConfirm={confirmStartAnalysis}
          credits={credits}
          cost={karmaCost}
          title={t('karmaAnalysis.confirmStartTitle')}
          colors={colors}
          isDark={isDark}
        />
      </View>
    );
  }

  const sections = analysis?.sections || {};
  const sectionKeys = Object.keys(sections);

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      <LinearGradient colors={screenGradientWithAccent} style={styles.backgroundGradient}>
        {renderKarmaTopBar({
          nativeInteractive: true,
          rightSlot: (
            <>
              <TouchableOpacity
                onPress={generateKarmaPDF}
                style={[
                  styles.headerIconBtn,
                  { backgroundColor: headerIconBg, borderColor: headerIconBorder },
                  generatingPDF && styles.headerIconBtnDisabled,
                ]}
                disabled={generatingPDF}
                activeOpacity={0.75}
                accessibilityRole="button"
                accessibilityLabel={t('karmaAnalysis.a11ySharePdf')}
              >
                {generatingPDF ? (
                  <ActivityIndicator size="small" color={colors.accent} />
                ) : (
                  <Ionicons name="share-outline" size={21} color={colors.accent} />
                )}
              </TouchableOpacity>
              <TouchableOpacity
                onPress={handleRegenerate}
                style={[styles.headerIconBtn, { backgroundColor: headerIconBg, borderColor: headerIconBorder }]}
                activeOpacity={0.75}
                accessibilityRole="button"
                accessibilityLabel={t('karmaAnalysis.a11yRegenerate')}
              >
                <Ionicons name="refresh" size={22} color={colors.accent} />
              </TouchableOpacity>
            </>
          ),
        })}
        <CreditModal
          visible={showRegenerateModal}
          onClose={() => setShowRegenerateModal(false)}
          onConfirm={confirmRegenerate}
          credits={credits}
          cost={karmaCost}
          title={t('karmaAnalysis.confirmRegenerateTitle')}
          colors={colors}
          isDark={isDark}
        />
        <ScrollView 
          showsVerticalScrollIndicator={false} 
          contentContainerStyle={styles.scrollContent}
          bounces={true}
        >
          <Animated.View style={{ opacity: fadeAnim }}>
            <View style={[styles.headerContainer, { backgroundColor: isDark ? 'rgba(255,215,0,0.08)' : colors.surface }]}>
              <View style={[styles.headerGlow, { backgroundColor: isDark ? 'rgba(255,215,0,0.15)' : colors.surface, borderColor: isDark ? 'rgba(255,215,0,0.3)' : colors.cardBorder }]}>
                <Text style={styles.omHeader}>🕉️</Text>
                <Text style={[styles.title, { color: colors.accent }]}>{t('karmaAnalysis.resultTitle')}</Text>
                <Text style={[styles.subtitle, { color: colors.textSecondary }]}>{t('karmaAnalysis.resultSubtitle')}</Text>
                <View style={[styles.divider, { backgroundColor: isDark ? 'rgba(255,215,0,0.3)' : colors.cardBorder }]} />
              </View>
            </View>

            {sectionKeys.map((key, index) => (
              <KarmaCard
                key={index}
                title={key}
                content={sections[key]}
                index={index}
                colors={colors}
                isDark={isDark}
                resolveSectionTitle={resolveSectionTitle}
              />
            ))}

            <View style={styles.footerContainer}>
              <View style={[styles.footerGradient, { backgroundColor: isDark ? 'rgba(0,0,0,0.2)' : colors.surface, borderColor: isDark ? 'rgba(255,215,0,0.15)' : colors.cardBorder }]}>
                <Text style={styles.footerIcon}>✨</Text>
                <Text style={[styles.footerText, { color: colors.textSecondary }]}>{t('karmaAnalysis.footerAnalyzedBy')}</Text>
                <Text style={[styles.footerSubtext, { color: colors.textSecondary }]}>{t('karmaAnalysis.footerAI')}</Text>
              </View>
            </View>
          </Animated.View>
        </ScrollView>
      </LinearGradient>
    </View>
  );
};

const CreditModal = ({ visible, onClose, onConfirm, credits, cost, title, colors = {}, isDark = true }) => {
  const { t } = useTranslation();
  return (
    <Modal visible={visible} transparent animationType="fade">
      <View style={[styles.modalOverlay, { backgroundColor: '#000000' }]}>
        <View style={[styles.modalContent, { backgroundColor: colors.surface || '#2d1b4e', borderColor: colors.cardBorder || 'rgba(255,215,0,0.3)' }]}>
          <Text style={[styles.modalTitle, { color: colors.accent || '#FFD700' }]}>{title}</Text>
          <Text style={[styles.modalText, { color: colors.text || '#fff' }]}>
            {t('karmaAnalysis.creditsModalWillUse', { cost })}
          </Text>
          <Text style={[styles.modalBalance, { color: colors.textSecondary || '#ccc' }]}>
            {t('karmaAnalysis.creditsModalBalance', { credits })}
          </Text>
          <View style={styles.modalButtons}>
            <TouchableOpacity style={[styles.modalButton, { backgroundColor: isDark ? 'rgba(255,255,255,0.1)' : colors.backgroundSecondary, borderColor: colors.cardBorder }]} onPress={onClose}>
              <Text style={[styles.modalButtonText, { color: colors.text }]}>{t('karmaAnalysis.creditsModalCancel')}</Text>
            </TouchableOpacity>
            <TouchableOpacity style={[styles.modalButton, styles.modalButtonPrimary, { backgroundColor: colors.primary }]} onPress={onConfirm}>
              <Text style={[styles.modalButtonText, styles.modalButtonTextPrimary, { color: '#fff' }]}>{t('karmaAnalysis.creditsModalConfirm')}</Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </Modal>
  );
};

const KarmaCard = ({ title, content, index, colors = {}, isDark = true, resolveSectionTitle }) => {
  const [expanded, setExpanded] = useState(true);
  const icons = ['🕉️', '🌟', '🎯', '⚖️', '💎', '🔱', '👪', '🦋', '🙏', '⏳', '🕉️'];
  
  const displayTitle = resolveSectionTitle ? resolveSectionTitle(title) : title;
  const isIntroduction = title === 'Introduction';
  const cardStyle = isIntroduction 
    ? { backgroundColor: isDark ? 'rgba(218, 165, 32, 0.9)' : (colors.cardBackground || colors.surface), borderColor: isDark ? 'rgba(218, 165, 32, 1)' : (colors.cardBorder || colors.primary) }
    : { backgroundColor: isDark ? 'rgba(255, 255, 255, 0.15)' : (colors.cardBackground || colors.surface), borderColor: isDark ? 'rgba(255, 255, 255, 0.3)' : (colors.cardBorder || colors.primary) };

  const formatContent = (text) => {
    // Clean up text first
    const cleanText = text.trim();
    
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

  const contentColor = colors.text || 'rgba(255,255,255,0.95)';
  const accentColor = colors.accent || '#FFD700';
  const introHighlightColor = isDark ? '#4a0080' : (colors.primary || colors.text);

  const renderFormattedText = (text) => {
    // Split by single or double newlines to get paragraphs
    const paragraphs = text.split(/\n+/).filter(p => p.trim().length > 0);
    
    return (
      <View>
        {paragraphs.map((para, paraIndex) => {
          const parts = formatContent(para);
          return (
            <Text key={paraIndex} style={[styles.cardContent, { color: contentColor }, paraIndex > 0 && styles.paragraphSpacing]}>
              {parts.map((part, index) => (
                <Text
                  key={index}
                  style={[
                    styles.cardContent,
                    { color: contentColor },
                    part.style === 'bold' && (isIntroduction ? { fontWeight: '700', color: introHighlightColor } : { fontWeight: '700', color: accentColor }),
                    part.style === 'italic' && (isIntroduction ? { fontStyle: 'italic', color: introHighlightColor } : { fontStyle: 'italic', color: accentColor }),
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

  const iconCircleStyle = isIntroduction
    ? (isDark ? { backgroundColor: 'rgba(139, 69, 19, 0.3)', borderColor: 'rgba(139, 69, 19, 0.6)' } : { backgroundColor: colors.surface, borderColor: colors.cardBorder })
    : (isDark ? { backgroundColor: 'rgba(255, 215, 0, 0.2)', borderColor: 'rgba(255, 215, 0, 0.4)' } : { backgroundColor: colors.surface, borderColor: colors.cardBorder });

  return (
    <View style={styles.cardWrapper}>
      <View style={[styles.glassCard, cardStyle]}>
        <TouchableOpacity 
          style={styles.cardHeader}
          onPress={() => setExpanded(!expanded)}
          activeOpacity={0.8}
        >
          <View style={[styles.iconCircle, isIntroduction && styles.introIconCircle, iconCircleStyle]}>
            <Text style={styles.cardIcon}>{icons[index % icons.length]}</Text>
          </View>
          <Text style={[styles.cardTitle, { color: colors.text || '#fff' }]}>{displayTitle}</Text>
          <Text style={[styles.expandIcon, { color: colors.textSecondary || 'rgba(255,255,255,0.8)' }]}>{expanded ? '▼' : '▶'}</Text>
        </TouchableOpacity>
        {expanded && (
          <View style={styles.cardContentContainer}>
            <View style={[styles.contentDivider, { backgroundColor: colors.cardBorder || 'rgba(255,255,255,0.2)' }]} />
            {renderFormattedText(content)}
          </View>
        )}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
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
    width: width * 0.7,
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
  modalOverlay: {
    flex: 1,
    backgroundColor: '#000000',
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalContent: {
    backgroundColor: '#2d1b4e',
    borderRadius: 20,
    padding: 30,
    width: '85%',
    borderWidth: 1,
    borderColor: 'rgba(255, 215, 0, 0.3)',
  },
  modalTitle: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#FFD700',
    marginBottom: 15,
    textAlign: 'center',
  },
  modalText: {
    fontSize: 16,
    color: '#fff',
    marginBottom: 10,
    textAlign: 'center',
  },
  modalBalance: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.7)',
    marginBottom: 25,
    textAlign: 'center',
  },
  modalButtons: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 15,
  },
  modalButton: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 10,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.3)',
  },
  modalButtonPrimary: {
    backgroundColor: '#FFD700',
    borderColor: '#FFD700',
  },
  modalButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
    textAlign: 'center',
  },
  modalButtonTextPrimary: {
    color: '#1a0033',
  },
});

export default KarmaAnalysisScreen;
