import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  Animated,
  Platform,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'react-native';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useTheme } from '../../context/ThemeContext';
import { useCredits } from '../../credits/CreditContext';
import { pricingAPI } from '../../services/api';
import { storage } from '../../services/storage';
import NativeSelectorChip from '../Common/NativeSelectorChip';
import { useAnalytics } from '../../hooks/useAnalytics';
import { useTranslation } from 'react-i18next';

export default function AnalysisHubScreen({ navigation }) {
  useAnalytics('AnalysisHubScreen');
  const { t } = useTranslation();
  const { colors } = useTheme();
  const { credits } = useCredits();
  const [fadeAnim] = useState(new Animated.Value(0));
  const [slideAnim] = useState(new Animated.Value(50));
  const [pricing, setPricing] = useState({});
  const [pricingOriginal, setPricingOriginal] = useState({});
  const [loadingPricing, setLoadingPricing] = useState(true);
  const [birthData, setBirthData] = useState(null);

  useEffect(() => {
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 800,
        useNativeDriver: true,
      }),
      Animated.timing(slideAnim, {
        toValue: 0,
        duration: 600,
        useNativeDriver: true,
      }),
    ]).start();

    fetchPricing();
    loadBirthData();
  }, []);
  
  const loadBirthData = async () => {
    try {
      const data = await storage.getBirthDetails();
      if (!data || !data.name) {
        navigation.replace('BirthProfileIntro', { returnTo: 'AnalysisHub' });
        return;
      }
      setBirthData(data);
    } catch (error) {
      console.error('Error loading birth data:', error);
    }
  };
  
  const fetchPricing = async () => {
    try {
      const response = await pricingAPI.getPricing();
      if (response.data && response.data.pricing) {
        setPricing(response.data.pricing);
        setPricingOriginal(response.data.pricing_original || {});
      }
    } catch (error) {
      console.error('Failed to fetch pricing:', error);
      // Use default pricing if API fails
      setPricing({
        career: 10,
        wealth: 5,
        health: 5,
        marriage: 5,
        education: 5,
        progeny: 15
      });
    } finally {
      setLoadingPricing(false);
    }
  };

  const getAnalysisTypes = () => {
    const baseTypes = [
      {
        id: 'reports',
        title: t('lifeAnalysisFlow.premiumReports'),
        subtitle: t('lifeAnalysisFlow.premiumReportsSubtitle'),
        icon: '📄',
        gradient: ['#fb7185', '#f97316'],
        description: t('lifeAnalysisFlow.premiumReportsDescription'),
        isFree: false,
      },
      {
        id: 'career',
        title: t('home.analysis.career.title'),
        subtitle: t('home.analysis.career.description'),
        icon: '💼',
        gradient: ['#6366F1', '#8B5CF6'],
        description: t('lifeAnalysisFlow.cardDescriptions.career')
      },
      {
        id: 'wealth',
        title: t('home.analysis.wealth.title'),
        subtitle: t('home.analysis.wealth.description'),
        icon: '💰',
        gradient: ['#FFD700', '#FF8C00'],
        description: t('lifeAnalysisFlow.cardDescriptions.wealth')
      },
      {
        id: 'health',
        title: t('home.analysis.health.title'),
        subtitle: t('home.analysis.health.description'),
        icon: '🏥',
        gradient: ['#32CD32', '#228B22'],
        description: t('lifeAnalysisFlow.cardDescriptions.health')
      },
      {
        id: 'relationshipMatch',
        title: t('lifeAnalysisFlow.kundliMatching'),
        subtitle: t('lifeAnalysisFlow.kundliMatchingSubtitle'),
        icon: '💞',
        gradient: ['#fb7185', '#f97316'],
        description: t('lifeAnalysisFlow.kundliMatchingDescription'),
        isFree: true,
      },
      {
        id: 'marriage',
        title: t('home.analysis.marriage.title'),
        subtitle: t('home.analysis.marriage.description'),
        icon: '💕',
        gradient: ['#FF69B4', '#DC143C'],
        description: t('lifeAnalysisFlow.cardDescriptions.marriage')
      },
      {
        id: 'education',
        title: t('home.analysis.education.title'),
        subtitle: t('home.analysis.education.description'),
        icon: '🎓',
        gradient: ['#4169E1', '#1E90FF'],
        description: t('lifeAnalysisFlow.cardDescriptions.education')
      },
      {
        id: 'progeny',
        title: t('home.analysis.progeny.title'),
        subtitle: t('home.analysis.progeny.description'),
        icon: '👶',
        gradient: ['#FF69B4', '#FFB6C1'],
        description: t('lifeAnalysisFlow.cardDescriptions.progeny')
      }
    ];
    
    return baseTypes.map(type => ({
      ...type,
      cost: type.id === 'reports'
        ? (pricing.partnership_report ?? pricing.partnership ?? 9)
        : (pricing[type.id] || 0),
      originalCost: type.id === 'reports'
        ? (pricingOriginal.partnership_report ?? pricingOriginal.partnership ?? null)
        : pricingOriginal[type.id],
    }));
  };

  const handleAnalysisSelect = (analysisType) => {
    if (analysisType.id === 'reports') {
      navigation.navigate('ReportsStudio');
      return;
    }
    if (analysisType.id === 'relationshipMatch') {
      navigation.navigate('RelationshipMatch');
      return;
    }

    navigation.navigate('AnalysisDetail', { 
      analysisType: analysisType.id,
      title: analysisType.title,
      cost: analysisType.cost,
      originalCost: analysisType.originalCost,
    });
  };

  const screenGradientColors = [colors.background, colors.backgroundSecondary, colors.background];

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor={colors.headerSurface} />
      <LinearGradient colors={screenGradientColors} style={styles.gradientBg}>
        <SafeAreaView style={styles.safeArea}>
          <View style={[styles.header, { backgroundColor: colors.headerSurface, borderBottomColor: colors.cardBorder }]}>
            <TouchableOpacity 
              style={[styles.backButton, { backgroundColor: 'rgba(255,255,255,0.09)', borderColor: colors.cardBorder }]}
              onPress={() => navigation.navigate('Home', { resetToGreeting: true })}
            >
              <Ionicons name="arrow-back" size={22} color={colors.textInverse} />
            </TouchableOpacity>
            <View style={styles.headerCenter}>
              <Text style={[styles.headerTitle, { color: colors.textInverse }]}>
                {t('lifeAnalysisFlow.lifeAnalysis')}
              </Text>
              {birthData && (
                <NativeSelectorChip 
                  birthData={birthData}
                  onPress={() => navigation.navigate('SelectNative')}
                  maxLength={15}
                  style={[styles.nativeChip, { backgroundColor: 'rgba(255,255,255,0.08)', borderColor: colors.cardBorder }]}
                  textStyle={[styles.nativeChipText, { color: colors.textInverseMuted }]}
                  showIcon={false}
                />
              )}
            </View>
            <TouchableOpacity style={styles.creditButton} onPress={() => navigation.navigate('Credits')}>
              <View style={[styles.creditGradient, { backgroundColor: colors.accentSoft }]}>
                <Text style={[styles.creditText, { color: colors.onAccent }]}>💳 {credits}</Text>
              </View>
            </TouchableOpacity>
          </View>

          {/* Content */}
          <Animated.View 
            style={[
              styles.content,
              {
                opacity: fadeAnim,
                transform: [{ translateY: slideAnim }]
              }
            ]}
          >
            <ScrollView 
              style={styles.scrollView}
              contentContainerStyle={styles.scrollContent}
              showsVerticalScrollIndicator={false}
            >
              {/* Hero Section */}
              <View style={[styles.heroSection, { backgroundColor: colors.surfaceInverse, borderColor: colors.cardBorder }]}>
                <View pointerEvents="none" style={styles.heroLinework}>
                  <View style={[styles.heroOrbitOuter, { borderColor: colors.accent }]} />
                  <View style={[styles.heroOrbitInner, { borderColor: colors.accent }]} />
                  <View style={[styles.heroDiagonal, { backgroundColor: colors.accent }]} />
                  <View style={[styles.heroAxis, { backgroundColor: colors.accent }]} />
                  <View style={[styles.heroPoint, { backgroundColor: colors.accent }]} />
                </View>
              <Text
                style={[
                  styles.heroTitle,
                  { color: colors.onSurfaceInverse || colors.textInverse },
                ]}
              >
                {t('lifeAnalysisFlow.heroTitle')}
              </Text>
              <Text style={[styles.heroSubtitle, { color: colors.onSurfaceInverseMuted || colors.textInverseMuted }]}>
                  {t('lifeAnalysisFlow.heroBody')}
              </Text>
              </View>

              {/* Analysis Cards */}
              <View style={styles.analysisGrid}>
                {getAnalysisTypes().map((analysis, index) => (
                  <Animated.View
                    key={analysis.id}
                    style={[
                      styles.analysisCard,
                      {
                        opacity: fadeAnim,
                        transform: [{
                          translateY: slideAnim.interpolate({
                            inputRange: [0, 50],
                            outputRange: [0, 50 + (index * 20)],
                          })
                        }]
                      }
                    ]}
                  >
                    <TouchableOpacity
                      onPress={() => handleAnalysisSelect(analysis)}
                      style={styles.cardTouchable}
                    >
                      <View style={[styles.cardGradient, { backgroundColor: colors.surfaceRaised, borderColor: colors.cardBorder }]}>
                        <View style={styles.cardHeader}>
                          <View style={styles.iconContainer}>
                            <View style={[styles.iconGradient, { backgroundColor: colors.accentSoft, borderColor: colors.cardBorder }]}>
                              <Text style={styles.cardIcon}>{analysis.icon}</Text>
                            </View>
                          </View>
                          <View style={[styles.costBadge, { backgroundColor: colors.primary }]}>
                            {analysis.isFree ? (
                              <Text style={[styles.costText, { color: colors.onPrimary }]}>{t('relationshipMatch.freeCompare')}</Text>
                            ) : analysis.originalCost != null && analysis.originalCost > analysis.cost ? (
                              <View style={styles.costWithDiscount}>
                                <Text style={[styles.costText, styles.costOriginal, { color: colors.onPrimary }]}>{analysis.originalCost}</Text>
                                <Text style={[styles.costText, { color: colors.onPrimary }]}>{t('lifeAnalysisFlow.credits', { count: analysis.cost })}</Text>
                              </View>
                            ) : (
                              <Text style={[styles.costText, { color: colors.onPrimary }]}>{t('lifeAnalysisFlow.credits', { count: analysis.cost })}</Text>
                            )}
                          </View>
                        </View>
                        <Text style={[styles.cardTitle, { color: colors.text }]}>{analysis.title}</Text>
                        <Text style={[styles.cardSubtitle, { color: colors.textSecondary }]}>{analysis.subtitle}</Text>
                        <Text style={[styles.cardDescription, { color: colors.textSecondary }]}>{analysis.description}</Text>
                        <View style={styles.cardFooter}>
                          <Text style={[styles.exploreText, { color: colors.primary }]}>{t('lifeAnalysisFlow.exploreNow')}</Text>
                          <Ionicons name="arrow-forward" size={16} color={colors.textSecondary} />
                        </View>
                      </View>
                    </TouchableOpacity>
                  </Animated.View>
                ))}
              </View>

              <View style={styles.infoSection}>
                <View style={[styles.infoCard, { backgroundColor: colors.surfaceRaised, borderColor: colors.cardBorder }]}>
                  <Text style={[styles.infoTitle, { color: colors.text }]}>✨ {t('lifeAnalysisFlow.premiumFeatures')}</Text>
                  <Text style={[styles.infoText, { color: colors.textSecondary }]}>
                    {t('lifeAnalysisFlow.premiumFeaturesBody')}
                  </Text>
                </View>
              </View>
            </ScrollView>
          </Animated.View>
        </SafeAreaView>
      </LinearGradient>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  gradientBg: {
    flex: 1,
  },
  safeArea: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
  },
  backButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#ffffff',
    textAlign: 'center',
  },
  headerCenter: {
    flex: 1,
    alignItems: 'center',
  },
  nativeChip: {
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    marginTop: 4,
    paddingHorizontal: 8,
    paddingVertical: 2,
  },
  nativeChipText: {
    fontSize: 11,
    color: 'rgba(255, 255, 255, 0.8)',
  },
  creditButton: {
    borderRadius: 18,
    overflow: 'hidden',
  },
  creditGradient: {
    paddingHorizontal: 14,
    paddingVertical: 8,
  },
  creditText: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: '700',
  },
  content: {
    flex: 1,
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    paddingBottom: 30,
  },
  heroSection: {
    alignItems: 'flex-start',
    margin: 16,
    paddingVertical: 28,
    paddingHorizontal: 24,
    borderRadius: 28,
    borderWidth: 1,
    overflow: 'hidden',
  },
  heroLinework: {
    ...StyleSheet.absoluteFillObject,
    opacity: 0.58,
  },
  heroOrbitOuter: {
    position: 'absolute',
    width: 218,
    height: 218,
    borderRadius: 109,
    borderWidth: 1,
    top: -112,
    right: -62,
  },
  heroOrbitInner: {
    position: 'absolute',
    width: 148,
    height: 148,
    borderRadius: 74,
    borderWidth: 1,
    top: -77,
    right: -27,
  },
  heroDiagonal: {
    position: 'absolute',
    width: 1,
    height: 210,
    top: -24,
    right: 72,
    opacity: 0.34,
    transform: [{ rotate: '38deg' }],
  },
  heroAxis: {
    position: 'absolute',
    width: 92,
    height: 1,
    top: 47,
    right: 24,
    opacity: 0.72,
  },
  heroPoint: {
    position: 'absolute',
    width: 7,
    height: 7,
    borderRadius: 4,
    top: 44,
    right: 68,
  },
  heroTitle: {
    fontSize: 38,
    fontWeight: '500',
    fontFamily: Platform.select({ web: 'Georgia', ios: 'Georgia', android: 'serif' }),
    color: '#ffffff',
    textAlign: 'left',
    marginBottom: 12,
    maxWidth: '84%',
    zIndex: 1,
  },
  heroSubtitle: {
    fontSize: 16,
    color: 'rgba(255, 255, 255, 0.8)',
    textAlign: 'left',
    lineHeight: 24,
    maxWidth: '88%',
    zIndex: 1,
  },
  analysisGrid: {
    paddingHorizontal: 16,
    gap: 12,
  },
  analysisCard: {
    borderRadius: 18,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.08,
    shadowRadius: 12,
    elevation: 2,
  },
  cardTouchable: {
    width: '100%',
  },
  cardGradient: {
    padding: 18,
    borderWidth: 1,
    borderRadius: 18,
    borderColor: 'rgba(255, 255, 255, 0.2)',
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  iconContainer: {
    width: 52,
    height: 52,
    borderRadius: 26,
    overflow: 'hidden',
  },
  iconGradient: {
    width: '100%',
    height: '100%',
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 2,
    borderColor: 'rgba(255, 255, 255, 0.3)',
  },
  cardIcon: {
    fontSize: 28,
  },
  costBadge: {
    backgroundColor: 'rgba(255, 107, 53, 0.8)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
  },
  costText: {
    color: '#ffffff',
    fontSize: 12,
    fontWeight: '600',
  },
  costWithDiscount: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  costOriginal: {
    textDecorationLine: 'line-through',
    opacity: 0.9,
  },
  cardTitle: {
    fontSize: 24,
    fontWeight: '500',
    fontFamily: Platform.select({ web: 'Georgia', ios: 'Georgia', android: 'serif' }),
    color: '#ffffff',
    marginBottom: 8,
  },
  cardSubtitle: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.8)',
    marginBottom: 12,
    fontWeight: '500',
  },
  cardDescription: {
    fontSize: 13,
    color: 'rgba(255, 255, 255, 0.7)',
    lineHeight: 18,
    marginBottom: 16,
  },
  cardFooter: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  exploreText: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.9)',
    fontWeight: '600',
  },
  infoSection: {
    paddingHorizontal: 20,
    paddingTop: 30,
  },
  infoCard: {
    padding: 20,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.2)',
  },
  infoTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#ffffff',
    marginBottom: 12,
  },
  infoText: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.8)',
    lineHeight: 20,
  },
});
