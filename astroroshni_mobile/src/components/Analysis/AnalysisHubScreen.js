import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  Animated,
  Dimensions,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'react-native';
import Ionicons from '@expo/vector-icons/Ionicons';
import { COLORS } from '../../utils/constants';
import { useCredits } from '../../credits/CreditContext';
import { pricingAPI } from '../../services/api';
import { storage } from '../../services/storage';
import NativeSelectorChip from '../Common/NativeSelectorChip';

const { width } = Dimensions.get('window');

export default function AnalysisHubScreen({ navigation }) {
  const { credits } = useCredits();
  const [fadeAnim] = useState(new Animated.Value(0));
  const [slideAnim] = useState(new Animated.Value(50));
  const [pricing, setPricing] = useState({});
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
      setBirthData(data);
    } catch (error) {
      console.error('Error loading birth data:', error);
    }
  };
  
  const fetchPricing = async () => {
    try {
      const response = await pricingAPI.getAnalysisPricing();
      if (response.data && response.data.pricing) {
        setPricing(response.data.pricing);
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
        id: 'career',
        title: 'Career Analysis',
        subtitle: 'Professional success & opportunities',
        icon: '💼',
        gradient: ['#6366F1', '#8B5CF6'],
        description: 'Discover your career potential, ideal industries, and professional timing with AI-powered insights'
      },
      {
        id: 'wealth',
        title: 'Wealth Analysis',
        subtitle: 'Financial prospects & opportunities',
        icon: '💰',
        gradient: ['#FFD700', '#FF8C00'],
        description: 'Discover your financial potential, investment timing, and wealth accumulation patterns'
      },
      {
        id: 'health',
        title: 'Health Analysis',
        subtitle: 'Wellness insights & precautions',
        icon: '🏥',
        gradient: ['#32CD32', '#228B22'],
        description: 'Understand health vulnerabilities, body constitution, and preventive measures'
      },
      {
        id: 'marriage',
        title: 'Marriage Analysis',
        subtitle: 'Relationship compatibility & timing',
        icon: '💕',
        gradient: ['#FF69B4', '#DC143C'],
        description: 'Explore relationship patterns, marriage timing, and partner compatibility'
      },
      {
        id: 'education',
        title: 'Education Analysis',
        subtitle: 'Learning path & career guidance',
        icon: '🎓',
        gradient: ['#4169E1', '#1E90FF'],
        description: 'Identify educational strengths, career paths, and learning opportunities'
      },
      {
        id: 'progeny',
        title: 'Progeny Analysis',
        subtitle: 'Children & family expansion',
        icon: '👶',
        gradient: ['#FF69B4', '#FFB6C1'],
        description: 'Explore fertility potential, timing for children, and family expansion insights'
      }
    ];
    
    return baseTypes.map(type => ({
      ...type,
      cost: pricing[type.id] || 5
    }));
  };

  const handleAnalysisSelect = (analysisType) => {
    if (credits < analysisType.cost) {
      navigation.navigate('Credits');
      return;
    }
    
    navigation.navigate('AnalysisDetail', { 
      analysisType: analysisType.id,
      title: analysisType.title,
      cost: analysisType.cost
    });
  };

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#1a0033" />
      <LinearGradient colors={['#1a0033', '#2d1b4e', '#4a2c6d', '#ff6b35']} style={styles.gradientBg}>
        <SafeAreaView style={styles.safeArea}>
          {/* Header */}
          <View style={styles.header}>
            <TouchableOpacity 
              style={styles.backButton}
              onPress={() => navigation.navigate('Home', { resetToGreeting: true })}
            >
              <Ionicons name="arrow-back" size={24} color={COLORS.white} />
            </TouchableOpacity>
            <View style={styles.headerCenter}>
              <Text style={styles.headerTitle}>Life Analysis</Text>
              {birthData && (
                <NativeSelectorChip 
                  birthData={birthData}
                  onPress={() => navigation.navigate('SelectNative')}
                  maxLength={15}
                  style={styles.nativeChip}
                  textStyle={styles.nativeChipText}
                  showIcon={false}
                />
              )}
            </View>
            <TouchableOpacity 
              style={styles.creditButton}
              onPress={() => navigation.navigate('Credits')}
            >
              <LinearGradient
                colors={['#ff6b35', '#ff8c5a']}
                style={styles.creditGradient}
              >
                <Text style={styles.creditText}>💳 {credits}</Text>
              </LinearGradient>
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
              <View style={styles.heroSection}>
                <View style={styles.cosmicOrb}>
                  <LinearGradient
                    colors={['#ff6b35', '#ffd700', '#ff6b35']}
                    style={styles.orbGradient}
                  >
                    <Text style={styles.orbIcon}>🔮</Text>
                  </LinearGradient>
                </View>
                <Text style={styles.heroTitle}>Unlock Your Life's Mysteries</Text>
                <Text style={styles.heroSubtitle}>
                  Deep astrological insights into the four pillars of life
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
                      <LinearGradient
                        colors={['rgba(255, 255, 255, 0.15)', 'rgba(255, 255, 255, 0.05)']}
                        style={styles.cardGradient}
                      >
                        <View style={styles.cardHeader}>
                          <View style={styles.iconContainer}>
                            <LinearGradient
                              colors={analysis.gradient}
                              style={styles.iconGradient}
                            >
                              <Text style={styles.cardIcon}>{analysis.icon}</Text>
                            </LinearGradient>
                          </View>
                          <View style={styles.costBadge}>
                            <Text style={styles.costText}>{analysis.cost} credits</Text>
                          </View>
                        </View>
                        
                        <Text style={styles.cardTitle}>{analysis.title}</Text>
                        <Text style={styles.cardSubtitle}>{analysis.subtitle}</Text>
                        <Text style={styles.cardDescription}>{analysis.description}</Text>
                        
                        <View style={styles.cardFooter}>
                          <Text style={styles.exploreText}>Explore Now</Text>
                          <Ionicons name="arrow-forward" size={16} color="rgba(255, 255, 255, 0.8)" />
                        </View>
                      </LinearGradient>
                    </TouchableOpacity>
                  </Animated.View>
                ))}
              </View>

              {/* Info Section */}
              <View style={styles.infoSection}>
                <LinearGradient
                  colors={['rgba(255, 255, 255, 0.1)', 'rgba(255, 255, 255, 0.05)']}
                  style={styles.infoCard}
                >
                  <Text style={styles.infoTitle}>✨ Premium Analysis Features</Text>
                  <Text style={styles.infoText}>
                    • Detailed astrological calculations{'\n'}
                    • Personalized remedies & suggestions{'\n'}
                    • Timing predictions & favorable periods{'\n'}
                    • Interactive Q&A format{'\n'}
                    • Follow-up questions for deeper insights
                  </Text>
                </LinearGradient>
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
    paddingHorizontal: 20,
    paddingVertical: 16,
  },
  backButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: COLORS.white,
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
    color: COLORS.white,
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
    alignItems: 'center',
    paddingVertical: 30,
    paddingHorizontal: 20,
  },
  cosmicOrb: {
    width: 80,
    height: 80,
    borderRadius: 40,
    marginBottom: 20,
    shadowColor: '#ff6b35',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.6,
    shadowRadius: 16,
    elevation: 10,
  },
  orbGradient: {
    width: '100%',
    height: '100%',
    borderRadius: 40,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 3,
    borderColor: 'rgba(255, 255, 255, 0.3)',
  },
  orbIcon: {
    fontSize: 40,
  },
  heroTitle: {
    fontSize: 28,
    fontWeight: '800',
    color: COLORS.white,
    textAlign: 'center',
    marginBottom: 12,
    textShadowColor: 'rgba(0, 0, 0, 0.3)',
    textShadowOffset: { width: 0, height: 2 },
    textShadowRadius: 4,
  },
  heroSubtitle: {
    fontSize: 16,
    color: 'rgba(255, 255, 255, 0.8)',
    textAlign: 'center',
    lineHeight: 24,
  },
  analysisGrid: {
    paddingHorizontal: 20,
    gap: 16,
  },
  analysisCard: {
    borderRadius: 20,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.3,
    shadowRadius: 16,
    elevation: 8,
  },
  cardTouchable: {
    width: '100%',
  },
  cardGradient: {
    padding: 20,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.2)',
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  iconContainer: {
    width: 60,
    height: 60,
    borderRadius: 30,
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
    color: COLORS.white,
    fontSize: 12,
    fontWeight: '600',
  },
  cardTitle: {
    fontSize: 22,
    fontWeight: '700',
    color: COLORS.white,
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
    color: COLORS.white,
    marginBottom: 12,
  },
  infoText: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.8)',
    lineHeight: 20,
  },
});