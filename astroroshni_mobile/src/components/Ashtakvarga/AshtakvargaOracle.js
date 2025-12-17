import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  Animated,
  Dimensions,
  Modal,
  StatusBar,
  Clipboard,
  Alert,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { SafeAreaView } from 'react-native-safe-area-context';
import Ionicons from '@expo/vector-icons/Ionicons';
import { storage } from '../../services/storage';
import { COLORS, API_BASE_URL, getEndpoint } from '../../utils/constants';
import AsyncStorage from '@react-native-async-storage/async-storage';
import AshtakvargaChart from './AshtakvargaChart';

const { width, height } = Dimensions.get('window');

export default function AshtakvargaOracle({ navigation }) {
  const [activeTab, setActiveTab] = useState(0);
  const [birthData, setBirthData] = useState(null);
  const [oracleData, setOracleData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedPillar, setSelectedPillar] = useState(null);
  const [showSecretScroll, setShowSecretScroll] = useState(false);
  const [completeOracleData, setCompleteOracleData] = useState(null);
  const [loadingInsight, setLoadingInsight] = useState(false);
  
  // Animations
  const pulseAnim = useRef(new Animated.Value(1)).current;
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const loadingRotateAnim = useRef(new Animated.Value(0)).current;



  useEffect(() => {
    loadBirthData();
    startAnimations();
  }, []);

  const startAnimations = () => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, {
          toValue: 1.1,
          duration: 2000,
          useNativeDriver: true,
        }),
        Animated.timing(pulseAnim, {
          toValue: 1,
          duration: 2000,
          useNativeDriver: true,
        }),
      ])
    ).start();

    Animated.timing(fadeAnim, {
      toValue: 1,
      duration: 1000,
      useNativeDriver: true,
    }).start();
  };

  const loadBirthData = async () => {
    try {
      // First try to get single birth details
      let data = await storage.getBirthDetails();
      
      // If no single birth details, get from profiles
      if (!data) {
        const profiles = await storage.getBirthProfiles();
        if (profiles && profiles.length > 0) {
          // Use the first profile or find 'self' relation
          data = profiles.find(p => p.relation === 'self') || profiles[0];
        }
      }
      
      if (data) {
        setBirthData(data);
        await fetchAshtakvargaData(data);
      } else {
        console.log('No birth data found in storage');
      }
    } catch (error) {
      console.error('Error loading birth data:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchAshtakvargaData = async (birth) => {
    try {
      const token = await AsyncStorage.getItem('authToken');
      
      if (!token || !birth) {
        throw new Error('Missing authentication token or birth data');
      }
      
      const response = await fetch(`${API_BASE_URL}${getEndpoint('/calculate-ashtakavarga')}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          birth_data: {
            name: birth.name,
            date: birth.date,
            time: birth.time,
            latitude: birth.latitude,
            longitude: birth.longitude,
            timezone: birth.timezone || 'Asia/Kolkata'
          },
          chart_type: 'lagna'
        })
      });

      if (response.ok) {
        const data = await response.json();
        console.log('Ashtakvarga data received:', data);
        setOracleData(data);
      } else {
        throw new Error(`Failed to fetch ashtakvarga data: ${response.status}`);
      }
    } catch (error) {
      console.error('Error fetching ashtakvarga data:', error);
      throw error;
    }
  };

  const fetchDailyInsight = async () => {
    if (!oracleData || !birthData) {
      console.error('Missing ashtakvarga or birth data');
      return;
    }

    setLoadingInsight(true);
    try {
      const token = await AsyncStorage.getItem('authToken');
      
      const dailyResponse = await fetch(`${API_BASE_URL}/api/ashtakavarga/oracle-insight`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          birth_data: birthData,
          ashtakvarga_data: oracleData,
          date: new Date().toISOString().split('T')[0]
        })
      });

      if (dailyResponse.ok) {
        const completeData = await dailyResponse.json();
        console.log('Complete oracle data received:', completeData);
        setCompleteOracleData(completeData);
      } else {
        console.error('Failed to fetch oracle insight:', dailyResponse.status, dailyResponse.statusText);
      }
    } catch (error) {
      console.error('Error fetching oracle insight:', error);
    } finally {
      setLoadingInsight(false);
    }
  };

  const getCosmicWeatherTheme = () => {
    if (!oracleData?.ashtakavarga?.total_bindus) {
      throw new Error('Ashtakvarga total bindus data is required but not available');
    }
    
    const totalBindus = oracleData.ashtakavarga.total_bindus;
    const strength = Math.round((totalBindus / 337) * 100); // 337 is theoretical max
    
    if (strength >= 80) {
      return {
        theme: 'Breakthrough',
        sentiment: 'positive',
        colors: ['#ff6b35', '#ffd700', '#ff8c5a']
      };
    } else if (strength >= 50) {
      return {
        theme: 'Stability',
        sentiment: 'neutral',
        colors: ['#1a0033', '#2d1b4e', '#4a2c6d']
      };
    } else {
      return {
        theme: 'Reflection',
        sentiment: 'caution',
        colors: ['#2c3e50', '#34495e', '#5d6d7e']
      };
    }
  };

  const renderOraclesPulse = () => {
    const weather = getCosmicWeatherTheme();
    
    return (
      <ScrollView style={styles.tabContent} showsVerticalScrollIndicator={false}>
        <View style={[styles.cosmicWeatherHeader, { height: height * 0.35 }]}>
          <LinearGradient
            colors={weather.colors}
            style={styles.weatherGradient}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 1 }}
          >
            <Animated.View style={[styles.weatherContent, { transform: [{ scale: pulseAnim }] }]}>
              <Text style={styles.cosmicTheme}>{weather.theme}</Text>
              <Text style={styles.cosmicSubtext}>Today's Cosmic Pulse</Text>
              <View style={styles.strengthIndicator}>
                <Text style={styles.strengthValue}>{Math.round((oracleData.ashtakavarga.total_bindus / 337) * 100)}%</Text>
                <Text style={styles.strengthLabel}>Cosmic Alignment</Text>
              </View>
            </Animated.View>
          </LinearGradient>
        </View>

        <Animated.View style={[styles.narrativeCard, { opacity: fadeAnim }]}>
          <LinearGradient
            colors={['rgba(255, 255, 255, 0.15)', 'rgba(255, 255, 255, 0.05)']}
            style={styles.narrativeGradient}
          >
            <Text style={styles.narrativeTitle}>Today's Oracle</Text>
            {completeOracleData ? (
              <Text style={styles.narrativeText}>
                {completeOracleData.oracle_message}
              </Text>
            ) : (
              <TouchableOpacity 
                style={styles.generateInsightButton}
                onPress={fetchDailyInsight}
                disabled={loadingInsight}
              >
                <LinearGradient
                  colors={['#ff6b35', '#ffd700']}
                  style={styles.buttonGradient}
                >
                  <Text style={styles.buttonText}>
                    {loadingInsight ? '🔮 Consulting Oracle...' : '🔮 Generate Daily Insight'}
                  </Text>
                </LinearGradient>
              </TouchableOpacity>
            )}
          </LinearGradient>
        </Animated.View>

        <View style={styles.powerActionsContainer}>
          <Text style={styles.powerActionsTitle}>Power Actions</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.pillsContainer}>
            {(completeOracleData?.power_actions || []).map((action, index) => (
              <TouchableOpacity key={index} style={[styles.actionPill, action.type === 'avoid' ? styles.avoidPill : styles.doPill]}>
                <Text style={styles.pillIcon}>{action.type === 'avoid' ? '🔴' : '🟢'}</Text>
                <Text style={styles.pillText}>{action.text}</Text>
              </TouchableOpacity>
            ))}
          </ScrollView>
        </View>
      </ScrollView>
    );
  };

  const renderDestinyMap = () => {
    if (!oracleData || !oracleData.ashtakavarga || !oracleData.ashtakavarga.sarvashtakavarga) {
      throw new Error('Ashtakvarga data is required but not available');
    }

    return (
      <ScrollView style={styles.tabContent} showsVerticalScrollIndicator={false}>
        <Text style={styles.mapTitle}>Sarvashtakvarga Chart</Text>
        <Text style={styles.mapSubtitle}>Tap any house to see its cosmic strength</Text>
        
        <View style={styles.chartContainer}>
          <AshtakvargaChart 
            chartData={oracleData.chart_data}
            ashtakvargaData={oracleData.chart_ashtakavarga}
            onHousePress={(houseNum, bindus, signName) => {
              openSecretScroll(signName, bindus, houseNum - 1);
            }}
            cosmicTheme={true}
          />
        </View>

        <View style={styles.planetaryToggle}>
          <Text style={styles.toggleTitle}>Bhinnashtakvarga Charts</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false}>
            {['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'].map(planet => {
              const planetChart = oracleData?.ashtakavarga?.individual_charts?.[planet];
              const totalBindus = planetChart?.total || 0;
              return (
                <TouchableOpacity 
                  key={planet} 
                  style={styles.planetButton}
                  onPress={() => openPlanetChart(planet, planetChart)}
                >
                  <Text style={styles.planetIcon}>{getPlanetIcon(planet)}</Text>
                  <Text style={styles.planetName}>{planet}</Text>
                  <Text style={styles.planetBindus}>{totalBindus}</Text>
                </TouchableOpacity>
              );
            })}
          </ScrollView>
        </View>

        <View style={styles.lifePredictionsContainer}>
          <TouchableOpacity 
            style={[styles.lifePredictionsButton, loadingLifePredictions && styles.loadingButton]}
            onPress={generateLifePredictions}
            disabled={loadingLifePredictions}
          >
            <LinearGradient
              colors={loadingLifePredictions ? ['#2c3e50', '#34495e', '#5d6d7e'] : ['#8e44ad', '#9b59b6', '#af7ac5']}
              style={styles.lifePredictionsGradient}
            >
              {loadingLifePredictions ? (
                <View style={styles.loadingContent}>
                  <Animated.View 
                    style={[
                      styles.loadingIconContainer,
                      {
                        transform: [{
                          rotate: loadingRotateAnim.interpolate({
                            inputRange: [0, 1],
                            outputRange: ['0deg', '360deg']
                          })
                        }]
                      }
                    ]}
                  >
                    <Text style={styles.lifePredictionsIcon}>✨</Text>
                  </Animated.View>
                  <Text style={styles.lifePredictionsText}>
                    Consulting Dots of Destiny...
                  </Text>
                  <View style={styles.progressContainer}>
                    <View style={styles.progressBar}>
                      <View style={[styles.progressFill, { width: `${loadingProgress}%` }]} />
                    </View>
                    <Text style={styles.progressText}>{Math.round(loadingProgress)}%</Text>
                  </View>
                </View>
              ) : (
                <>
                  <Text style={styles.lifePredictionsIcon}>🌟</Text>
                  <Text style={styles.lifePredictionsText}>
                    Generate Life Predictions
                  </Text>
                  <Text style={styles.lifePredictionsSubtext}>Vinay Aditya's Methodology</Text>
                </>
              )}
            </LinearGradient>
          </TouchableOpacity>
        </View>
      </ScrollView>
    );
  };



  const openSecretScroll = (sign, bindus, index) => {
    setSelectedPillar({ sign, bindus, index });
    setShowSecretScroll(true);
  };

  const openPlanetChart = (planet, planetChart) => {
    if (!planetChart) return;
    setSelectedPillar({ 
      planet, 
      planetChart, 
      type: 'planet'
    });
    setShowSecretScroll(true);
  };

  const [lifePredictions, setLifePredictions] = useState(null);
  const [loadingLifePredictions, setLoadingLifePredictions] = useState(false);
  const [showLifePredictions, setShowLifePredictions] = useState(false);
  const [loadingProgress, setLoadingProgress] = useState(0);

  const startLoadingAnimation = () => {
    setLoadingProgress(0);
    Animated.loop(
      Animated.timing(loadingRotateAnim, {
        toValue: 1,
        duration: 2000,
        useNativeDriver: true,
      })
    ).start();
    
    // Slow progress over 35 seconds
    const progressInterval = setInterval(() => {
      setLoadingProgress(prev => {
        if (prev >= 85) {
          clearInterval(progressInterval);
          return 85;
        }
        return prev + Math.random() * 3 + 1; // 1-4% increment
      });
    }, 1000); // Update every second
    
    return progressInterval;
  };

  const generateLifePredictions = async () => {
    if (!birthData) {
      console.error('No birth data available for life predictions');
      return;
    }

    setLoadingLifePredictions(true);
    const progressInterval = startLoadingAnimation();
    
    try {
      const token = await AsyncStorage.getItem('authToken');
      
      const response = await fetch(`${API_BASE_URL}/api/ashtakavarga/life-predictions`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          birth_data: {
            name: birthData.name,
            date: birthData.date,
            time: birthData.time,
            latitude: birthData.latitude,
            longitude: birthData.longitude,
            timezone: birthData.timezone || 'Asia/Kolkata',
            place: birthData.place || '',
            gender: birthData.gender || ''
          }
        })
      });

      if (response.ok) {
        const predictions = await response.json();
        console.log('Life predictions received:', predictions);
        setLoadingProgress(100);
        setTimeout(() => {
          setLifePredictions(predictions);
          setShowLifePredictions(true);
        }, 500);
      } else {
        console.error('Failed to generate life predictions:', response.status);
      }
    } catch (error) {
      console.error('Error generating life predictions:', error);
    } finally {
      clearInterval(progressInterval);
      loadingRotateAnim.stopAnimation();
      loadingRotateAnim.setValue(0);
      setTimeout(() => {
        setLoadingLifePredictions(false);
        setLoadingProgress(0);
      }, 500);
    }
  };



  const getPlanetIcon = (planet) => {
    const icons = {
      'Sun': '☉', 'Moon': '☽', 'Mars': '♂', 'Mercury': '☿',
      'Jupiter': '♃', 'Venus': '♀', 'Saturn': '♄'
    };
    return icons[planet] || '⭐';
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <LinearGradient colors={['#1a0033', '#2d1b4e', '#4a2c6d']} style={styles.loadingGradient}>
          <Animated.View style={{ transform: [{ scale: pulseAnim }] }}>
            <Text style={styles.loadingText}>🔮</Text>
          </Animated.View>
          <Text style={styles.loadingSubtext}>Consulting the Oracle...</Text>
        </LinearGradient>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#1a0033" />
      <LinearGradient colors={['#1a0033', '#2d1b4e', '#4a2c6d']} style={styles.gradient}>
        <SafeAreaView style={styles.safeArea}>
          <View style={styles.header}>
            <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backButton}>
              <Ionicons name="arrow-back" size={24} color={COLORS.white} />
            </TouchableOpacity>
            <Text style={styles.headerTitle}>Ashtakvarga Oracle</Text>
            <View style={styles.headerRight} />
          </View>

          {renderDestinyMap()}

          <Modal
            visible={showLifePredictions}
            transparent
            animationType="slide"
            onRequestClose={() => setShowLifePredictions(false)}
          >
            <View style={styles.modalOverlay}>
              <View style={styles.predictionsModal}>
                <LinearGradient
                  colors={['rgba(26, 0, 51, 0.95)', 'rgba(45, 27, 78, 0.9)']}
                  style={styles.predictionsGradient}
                >
                  <TouchableOpacity 
                    style={styles.closeButton}
                    onPress={() => setShowLifePredictions(false)}
                  >
                    <Ionicons name="close" size={24} color={COLORS.white} />
                  </TouchableOpacity>
                  
                  <ScrollView showsVerticalScrollIndicator={false}>
                    <Text style={styles.predictionsTitle}>Life Predictions</Text>
                    <Text style={styles.predictionsSubtitle}>{lifePredictions?.methodology || "Vinay Aditya's Dots of Destiny"}</Text>
                    
                    <View style={styles.predictionsContent}>
                      {lifePredictions?.predictions?.current_life_phase && (
                        <>
                          <Text style={styles.sectionTitle}>Current Life Phase</Text>
                          <Text style={styles.sectionText}>{lifePredictions.predictions.current_life_phase}</Text>
                        </>
                      )}
                      
                      {lifePredictions?.predictions?.sav_strength_analysis?.strong_areas && (
                        <>
                          <Text style={styles.sectionTitle}>Strong Areas</Text>
                          {lifePredictions.predictions.sav_strength_analysis.strong_areas.map((area, index) => (
                            <Text key={index} style={styles.bulletPoint}>• {area}</Text>
                          ))}
                        </>
                      )}
                      
                      {lifePredictions?.predictions?.sav_strength_analysis?.challenging_areas && (
                        <>
                          <Text style={styles.sectionTitle}>Challenging Areas</Text>
                          {lifePredictions.predictions.sav_strength_analysis.challenging_areas.map((area, index) => (
                            <Text key={index} style={styles.bulletPoint}>• {area}</Text>
                          ))}
                        </>
                      )}
                      
                      {lifePredictions?.predictions?.life_predictions?.next_6_months && (
                        <>
                          <Text style={styles.sectionTitle}>Next 6 Months</Text>
                          <Text style={styles.sectionText}>{lifePredictions.predictions.life_predictions.next_6_months}</Text>
                        </>
                      )}
                      
                      {lifePredictions?.predictions?.life_predictions?.next_year && (
                        <>
                          <Text style={styles.sectionTitle}>Next Year</Text>
                          <Text style={styles.sectionText}>{lifePredictions.predictions.life_predictions.next_year}</Text>
                        </>
                      )}
                      
                      {lifePredictions?.predictions?.remedial_measures && (
                        <>
                          <Text style={styles.sectionTitle}>Remedial Measures</Text>
                          {lifePredictions.predictions.remedial_measures.map((remedy, index) => (
                            <Text key={index} style={styles.bulletPoint}>• {remedy}</Text>
                          ))}
                        </>
                      )}
                    </View>
                  </ScrollView>
                </LinearGradient>
              </View>
            </View>
          </Modal>

          <Modal
            visible={showSecretScroll && selectedPillar !== null}
            transparent
            animationType="slide"
            onRequestClose={() => setShowSecretScroll(false)}
          >
            <View style={styles.modalOverlay}>
              <View style={styles.secretScroll}>
                <LinearGradient
                  colors={['rgba(26, 0, 51, 0.95)', 'rgba(45, 27, 78, 0.9)']}
                  style={styles.scrollGradient}
                >
                  <TouchableOpacity 
                    style={styles.closeButton}
                    onPress={() => setShowSecretScroll(false)}
                  >
                    <Ionicons name="close" size={24} color={COLORS.white} />
                  </TouchableOpacity>
                  
                  {selectedPillar?.type === 'planet' ? (
                    <>
                      <Text style={styles.scrollTitle}>
                        {selectedPillar.planet} Bhinnashtakvarga
                      </Text>
                      <Text style={styles.scrollBindus}>
                        {selectedPillar.planetChart.total} Total Points
                      </Text>
                      <View style={styles.planetChartGrid}>
                        {Object.entries(selectedPillar.planetChart.bindus).map(([sign, bindus]) => {
                          const signs = ['Ari', 'Tau', 'Gem', 'Can', 'Leo', 'Vir', 'Lib', 'Sco', 'Sag', 'Cap', 'Aqu', 'Pis'];
                          return (
                            <View key={sign} style={styles.miniPillar}>
                              <Text style={styles.miniBindus}>{bindus}</Text>
                              <Text style={styles.miniSign}>{signs[parseInt(sign)]}</Text>
                            </View>
                          );
                        })}
                      </View>
                      <Text style={styles.scrollDescription}>
                        This shows where {selectedPillar.planet} receives support from other planets. Higher numbers indicate stronger beneficial influences in those zodiac signs.
                      </Text>
                    </>
                  ) : (
                    <>
                      <Text style={styles.scrollTitle}>
                        {selectedPillar?.sign || 'Unknown'} Sector
                      </Text>
                      <Text style={styles.scrollBindus}>
                        {selectedPillar?.bindus || 0} Cosmic Points
                      </Text>
                      <Text style={styles.scrollDescription}>
                        {completeOracleData?.pillar_insights?.[selectedPillar?.index] || 
                         (selectedPillar && selectedPillar.bindus >= 30 
                          ? `${selectedPillar.sign} is your fortress of power. With ${selectedPillar.bindus} points, this sector provides strong karmic protection and opportunities for growth.`
                          : selectedPillar && selectedPillar.bindus <= 25
                          ? `${selectedPillar.sign} requires careful attention. With only ${selectedPillar.bindus} points, this area may present challenges that require patience and wisdom.`
                          : selectedPillar
                          ? `${selectedPillar.sign} offers moderate support. With ${selectedPillar.bindus} points, steady progress is possible through consistent effort.`
                          : 'Loading cosmic insights...'
                         )}
                      </Text>
                    </>
                  )}
                </LinearGradient>
              </View>
            </View>
          </Modal>
        </SafeAreaView>
      </LinearGradient>
    </View>
  );
}

const styles = {
  container: { flex: 1 },
  gradient: { flex: 1 },
  safeArea: { flex: 1 },
  loadingContainer: { flex: 1 },
  loadingGradient: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  loadingText: { fontSize: 60, marginBottom: 20 },
  loadingSubtext: { color: COLORS.white, fontSize: 16 },
  
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 15,
  },
  backButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(255,255,255,0.1)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  headerTitle: {
    flex: 1,
    textAlign: 'center',
    fontSize: 20,
    fontWeight: '700',
    color: COLORS.white,
  },
  headerRight: { width: 40 },
  
  tabNavigation: {
    flexDirection: 'row',
    paddingHorizontal: 20,
    marginBottom: 20,
  },
  tab: {
    flex: 1,
    alignItems: 'center',
    paddingVertical: 12,
    borderRadius: 20,
    marginHorizontal: 4,
  },
  activeTab: {
    backgroundColor: 'rgba(255, 215, 0, 0.2)',
  },
  tabText: {
    fontSize: 12,
    color: 'rgba(255,255,255,0.6)',
    marginTop: 4,
  },
  activeTabText: {
    color: '#ffd700',
    fontWeight: '600',
  },
  
  tabContent: { flex: 1, paddingHorizontal: 20 },
  
  cosmicWeatherHeader: {
    borderRadius: 20,
    overflow: 'hidden',
    marginBottom: 20,
  },
  weatherGradient: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  weatherContent: { alignItems: 'center' },
  cosmicTheme: {
    fontSize: 36,
    fontWeight: '800',
    color: COLORS.white,
    textAlign: 'center',
    marginBottom: 10,
  },
  cosmicSubtext: {
    fontSize: 16,
    color: 'rgba(255,255,255,0.8)',
    marginBottom: 20,
  },
  strengthIndicator: { alignItems: 'center' },
  strengthValue: {
    fontSize: 48,
    fontWeight: '700',
    color: '#ffd700',
  },
  strengthLabel: {
    fontSize: 14,
    color: 'rgba(255,255,255,0.7)',
  },
  
  narrativeCard: {
    borderRadius: 16,
    overflow: 'hidden',
    marginBottom: 20,
  },
  narrativeGradient: { padding: 20 },
  narrativeTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: COLORS.white,
    marginBottom: 12,
  },
  narrativeText: {
    fontSize: 16,
    color: 'rgba(255,255,255,0.9)',
    lineHeight: 24,
  },
  generateInsightButton: {
    borderRadius: 12,
    overflow: 'hidden',
  },
  buttonGradient: {
    paddingVertical: 16,
    paddingHorizontal: 24,
    alignItems: 'center',
  },
  buttonText: {
    fontSize: 16,
    fontWeight: '700',
    color: COLORS.white,
  },
  
  powerActionsContainer: { marginBottom: 10 },
  
  lifePredictionsContainer: { 
    marginBottom: 20,
    marginTop: 10,
  },
  lifePredictionsButton: {
    borderRadius: 16,
    overflow: 'hidden',
    elevation: 8,
    shadowColor: '#8e44ad',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
  },
  loadingButton: {
    shadowColor: '#2c3e50',
  },
  lifePredictionsGradient: {
    paddingVertical: 12,
    paddingHorizontal: 16,
    alignItems: 'center',
  },
  lifePredictionsIcon: {
    fontSize: 24,
    marginBottom: 6,
  },
  lifePredictionsText: {
    fontSize: 14,
    fontWeight: '700',
    color: COLORS.white,
    textAlign: 'center',
    marginBottom: 2,
  },
  lifePredictionsSubtext: {
    fontSize: 12,
    color: 'rgba(255,255,255,0.8)',
    textAlign: 'center',
    fontStyle: 'italic',
  },
  loadingContent: {
    alignItems: 'center',
  },
  loadingIconContainer: {
    marginBottom: 8,
  },
  progressContainer: {
    alignItems: 'center',
    marginTop: 12,
    width: '100%',
  },
  progressBar: {
    width: '80%',
    height: 4,
    backgroundColor: 'rgba(255,255,255,0.2)',
    borderRadius: 2,
    overflow: 'hidden',
    marginBottom: 8,
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#ffd700',
    borderRadius: 2,
  },
  progressText: {
    fontSize: 12,
    color: '#ffd700',
    fontWeight: '600',
  },
  warningText: {
    color: '#ff6b6b',
  },
  copyButton: {
    backgroundColor: '#ffd700',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
    alignSelf: 'flex-end',
    marginBottom: 10,
  },
  copyButtonText: {
    color: '#000',
    fontWeight: '600',
  },
  powerActionsTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: COLORS.white,
    marginBottom: 12,
  },
  pillsContainer: { flexDirection: 'row' },
  actionPill: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 20,
    marginRight: 12,
  },
  doPill: { backgroundColor: 'rgba(76, 175, 80, 0.2)' },
  avoidPill: { backgroundColor: 'rgba(244, 67, 54, 0.2)' },
  pillIcon: { fontSize: 16, marginRight: 8 },
  pillText: {
    color: COLORS.white,
    fontSize: 14,
    fontWeight: '600',
  },
  
  mapTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: COLORS.white,
    textAlign: 'center',
    marginBottom: 8,
  },
  mapSubtitle: {
    fontSize: 14,
    color: 'rgba(255,255,255,0.7)',
    textAlign: 'center',
    marginBottom: 20,
  },
  chartContainer: {
    height: 350,
    marginBottom: 30,
    paddingHorizontal: 10,
    justifyContent: 'center',
    alignItems: 'center',
  },
  
  planetaryToggle: { marginBottom: 20 },
  toggleTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: COLORS.white,
    marginBottom: 12,
  },
  planetButton: {
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 8,
    marginRight: 12,
    borderRadius: 12,
    backgroundColor: 'rgba(255,255,255,0.1)',
  },
  planetIcon: { fontSize: 20, marginBottom: 4, color: '#ffd700' },
  planetName: {
    fontSize: 12,
    color: COLORS.white,
  },
  planetBindus: {
    fontSize: 10,
    color: '#ffd700',
    fontWeight: '600',
  },
  planetChartGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'center',
    marginVertical: 20,
  },
  miniPillar: {
    width: '15%',
    alignItems: 'center',
    marginBottom: 8,
  },
  miniBindus: {
    fontSize: 14,
    fontWeight: '700',
    color: '#ffd700',
  },
  miniSign: {
    fontSize: 10,
    color: 'rgba(255,255,255,0.8)',
  },
  
  timeTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: COLORS.white,
    textAlign: 'center',
    marginBottom: 20,
  },
  querySelector: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    marginBottom: 30,
  },
  queryOption: {
    width: '48%',
    alignItems: 'center',
    paddingVertical: 20,
    borderRadius: 16,
    borderWidth: 2,
    backgroundColor: 'rgba(255,255,255,0.05)',
    marginBottom: 12,
  },
  queryIcon: { fontSize: 32, marginBottom: 8 },
  queryTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.white,
    textAlign: 'center',
  },
  
  timelineContainer: { flex: 1 },
  timelineTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: COLORS.white,
    marginBottom: 20,
  },
  timelineEvent: {
    flexDirection: 'row',
    marginBottom: 20,
  },
  eventNode: {
    width: 20,
    height: 20,
    borderRadius: 10,
    marginRight: 15,
    marginTop: 10,
  },
  goldNode: { backgroundColor: '#ffd700' },
  greyNode: { backgroundColor: '#666' },
  eventCard: {
    flex: 1,
    padding: 16,
    borderRadius: 12,
    backgroundColor: 'rgba(255,255,255,0.1)',
  },
  eventTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: COLORS.white,
    marginBottom: 4,
  },
  eventDate: {
    fontSize: 12,
    color: '#ffd700',
    marginBottom: 8,
  },
  eventDescription: {
    fontSize: 14,
    color: 'rgba(255,255,255,0.8)',
    lineHeight: 20,
    marginBottom: 8,
  },
  eventScore: {
    fontSize: 14,
    fontWeight: '700',
    color: '#ffd700',
  },
  timelineSubtext: {
    fontSize: 16,
    color: 'rgba(255,255,255,0.6)',
    textAlign: 'center',
    fontStyle: 'italic',
    marginTop: 20,
  },
  
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.8)',
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 20,
  },
  secretScroll: {
    width: '100%',
    maxHeight: '70%',
    borderRadius: 20,
    overflow: 'hidden',
  },
  scrollGradient: { padding: 30 },
  closeButton: {
    position: 'absolute',
    top: 15,
    right: 15,
    zIndex: 1,
  },
  scrollTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: COLORS.white,
    textAlign: 'center',
    marginBottom: 8,
  },
  scrollBindus: {
    fontSize: 18,
    color: '#ffd700',
    textAlign: 'center',
    marginBottom: 20,
  },
  scrollDescription: {
    fontSize: 16,
    color: 'rgba(255,255,255,0.9)',
    lineHeight: 24,
    textAlign: 'center',
  },
  
  predictionsModal: {
    width: '95%',
    maxHeight: '85%',
    borderRadius: 20,
    overflow: 'hidden',
  },
  predictionsGradient: {
    padding: 20,
    paddingTop: 50,
  },
  predictionsTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: COLORS.white,
    textAlign: 'center',
    marginBottom: 8,
  },
  predictionsSubtitle: {
    fontSize: 14,
    color: '#ffd700',
    textAlign: 'center',
    marginBottom: 20,
    fontStyle: 'italic',
  },
  predictionsContent: {
    paddingBottom: 20,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#ffd700',
    marginTop: 20,
    marginBottom: 10,
  },
  sectionText: {
    fontSize: 14,
    color: 'rgba(255,255,255,0.9)',
    lineHeight: 20,
    marginBottom: 10,
  },
  bulletPoint: {
    fontSize: 14,
    color: 'rgba(255,255,255,0.8)',
    lineHeight: 18,
    marginBottom: 6,
    paddingLeft: 10,
  },
};