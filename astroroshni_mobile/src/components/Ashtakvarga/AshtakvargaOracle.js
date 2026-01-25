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
import DateNavigator from '../Common/DateNavigator';
import { useTheme } from '../../context/ThemeContext';

const { width, height } = Dimensions.get('window');

const HOUSE_SIGNIFICATIONS = {
  0: { // House 1
    name: "Self & Personality",
    significations: "Physical body, appearance, personality, self-expression, vitality, overall health, life path, and how you present yourself to the world."
  },
  1: { // House 2
    name: "Wealth & Family",
    significations: "Accumulated wealth, family values, speech, food habits, early childhood, face, eyes, right eye, financial security, and material possessions."
  },
  2: { // House 3
    name: "Courage & Siblings",
    significations: "Siblings, courage, short travels, communication skills, hobbies, neighbors, hands, arms, shoulders, and self-efforts."
  },
  3: { // House 4
    name: "Home & Mother",
    significations: "Mother, home, property, vehicles, emotional peace, education, chest, heart, domestic happiness, and inner contentment."
  },
  4: { // House 5
    name: "Children & Creativity",
    significations: "Children, creativity, intelligence, romance, speculation, past life merits, stomach, education, and spiritual practices."
  },
  5: { // House 6
    name: "Health & Enemies",
    significations: "Diseases, enemies, debts, obstacles, service, daily work, pets, maternal relatives, digestive system, and competitive abilities."
  },
  6: { // House 7
    name: "Marriage & Partnership",
    significations: "Spouse, marriage, business partnerships, public relations, sexual organs, lower abdomen, and long-term relationships."
  },
  7: { // House 8
    name: "Transformation & Longevity",
    significations: "Longevity, sudden events, inheritance, occult knowledge, research, chronic diseases, reproductive organs, and transformative experiences."
  },
  8: { // House 9
    name: "Fortune & Dharma",
    significations: "Father, luck, higher education, long journeys, spirituality, religion, philosophy, thighs, and life purpose."
  },
  9: { // House 10
    name: "Career & Status",
    significations: "Career, profession, reputation, authority, government, knees, public image, and social standing."
  },
  10: { // House 11
    name: "Gains & Aspirations",
    significations: "Income, gains, elder siblings, friends, social networks, left ear, fulfillment of desires, and large organizations."
  },
  11: { // House 12
    name: "Liberation & Expenses",
    significations: "Expenses, losses, foreign lands, spirituality, isolation, sleep, feet, bed pleasures, and final liberation (moksha)."
  }
};

export default function AshtakvargaOracle({ navigation }) {
  const { theme, colors } = useTheme();
  const [activeTab, setActiveTab] = useState(0);
  const [birthData, setBirthData] = useState(null);
  const [oracleData, setOracleData] = useState(null);
  const [birthOracleData, setBirthOracleData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedPillar, setSelectedPillar] = useState(null);
  const [showSecretScroll, setShowSecretScroll] = useState(false);
  const [completeOracleData, setCompleteOracleData] = useState(null);
  const [loadingInsight, setLoadingInsight] = useState(false);
  const [selectedDate, setSelectedDate] = useState(new Date());
  
  // Animations
  const pulseAnim = useRef(new Animated.Value(1)).current;
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const loadingRotateAnim = useRef(new Animated.Value(0)).current;



  useEffect(() => {
    loadBirthData();
    startAnimations();
  }, []);
  
  useEffect(() => {
    if (birthData) {
      fetchAshtakvargaData(birthData, selectedDate);
    }
  }, [selectedDate]);

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
        // Set selected date to birth date initially
        setSelectedDate(new Date(data.date));
        await fetchAshtakvargaData(data, new Date(data.date));
      } else {
        console.log('No birth data found in storage');
      }
    } catch (error) {
      console.error('Error loading birth data:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchAshtakvargaData = async (birth, date = null) => {
    try {
      const token = await AsyncStorage.getItem('authToken');
      
      if (!token || !birth) {
        throw new Error('Missing authentication token or birth data');
      }
      
      // Compare dates properly - check if selected date matches birth date
      const birthDate = new Date(birth.date);
      const selectedDate = date || birthDate;
      
      // Compare only date parts (ignore time)
      const isSameDate = birthDate.getFullYear() === selectedDate.getFullYear() &&
                        birthDate.getMonth() === selectedDate.getMonth() &&
                        birthDate.getDate() === selectedDate.getDate();
      
      const requestBody = {
        birth_data: {
          name: birth.name,
          date: birth.date,
          time: birth.time,
          latitude: birth.latitude,
          longitude: birth.longitude
        },
        chart_type: isSameDate ? 'lagna' : 'transit'
      };
      
      if (!isSameDate) {
        requestBody.transit_date = selectedDate.toISOString().split('T')[0];
      }
      
      const response = await fetch(`${API_BASE_URL}${getEndpoint('/calculate-ashtakavarga')}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestBody)
      });

      if (response.ok) {
        const data = await response.json();
        setOracleData(data);
        
        // Store birth chart data for comparison if this is birth chart
        if (isSameDate) {
          setBirthOracleData(data);
        }
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
              <Text style={[styles.cosmicTheme, { color: colors.text }]}>{weather.theme}</Text>
              <Text style={[styles.cosmicSubtext, { color: colors.textSecondary }]}>Today's Cosmic Pulse</Text>
              <View style={styles.strengthIndicator}>
                <Text style={styles.strengthValue}>{Math.round((oracleData.ashtakavarga.total_bindus / 337) * 100)}%</Text>
                <Text style={styles.strengthLabel}>Cosmic Alignment</Text>
              </View>
            </Animated.View>
          </LinearGradient>
        </View>

        <Animated.View style={[styles.narrativeCard, { opacity: fadeAnim }]}>
          <LinearGradient
            colors={theme === 'dark' ? ['rgba(255, 255, 255, 0.15)', 'rgba(255, 255, 255, 0.05)'] : ['rgba(249, 115, 22, 0.15)', 'rgba(249, 115, 22, 0.08)']}
            style={styles.narrativeGradient}
          >
            <Text style={[styles.narrativeTitle, { color: colors.text }]}>Today's Oracle</Text>
            {completeOracleData ? (
              <Text style={[styles.narrativeText, { color: colors.textSecondary }]}>
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
          <Text style={[styles.powerActionsTitle, { color: colors.text }]}>Power Actions</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.pillsContainer}>
            {(completeOracleData?.power_actions || []).map((action, index) => (
              <TouchableOpacity key={index} style={[styles.actionPill, action.type === 'avoid' ? styles.avoidPill : styles.doPill]}>
                <Text style={styles.pillIcon}>{action.type === 'avoid' ? '🔴' : '🟢'}</Text>
                <Text style={[styles.pillText, { color: colors.text }]}>{action.text}</Text>
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
      <ScrollView style={styles.tabContent} contentContainerStyle={{ paddingBottom: 20 }} showsVerticalScrollIndicator={false}>
        <View style={styles.titleContainer}>
          <Text style={[styles.mapTitle, { color: colors.text }]}>Sarvashtakvarga Chart</Text>
          <Text style={[styles.mapSubtitle, { color: colors.textSecondary }]}>Tap any house to see its cosmic strength</Text>
        </View>
        
        <DateNavigator 
          date={selectedDate}
          onDateChange={setSelectedDate}
          cosmicTheme={true}
          resetDate={birthData ? new Date(birthData.date) : new Date()}
        />
        
        <View style={[styles.chartContainer, { backgroundColor: theme === 'dark' ? 'rgba(255,255,255,0.05)' : 'rgba(249,115,22,0.08)', borderWidth: 1, borderColor: theme === 'dark' ? 'rgba(255,255,255,0.1)' : 'rgba(249,115,22,0.2)', borderRadius: 16 }]}>
          <AshtakvargaChart 
            chartData={oracleData.chart_data}
            ashtakvargaData={oracleData.chart_ashtakavarga}
            birthAshtakvargaData={birthOracleData?.chart_ashtakavarga}
            onHousePress={(houseNum, bindus, signName) => {
              openSecretScroll(signName, bindus, houseNum - 1);
            }}
            cosmicTheme={true}
          />
        </View>

        <View style={styles.planetaryToggle}>
          <Text style={[styles.toggleTitle, { color: colors.text }]}>Bhinnashtakvarga Charts</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false}>
            {['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'].map(planet => {
              const planetChart = oracleData?.ashtakavarga?.individual_charts?.[planet];
              const totalBindus = planetChart?.total || 0;
              const iconColor = theme === 'dark' ? '#ffd700' : '#c2410c';
              return (
                <TouchableOpacity 
                  key={planet} 
                  style={[styles.planetButton, { backgroundColor: theme === 'dark' ? 'rgba(255,255,255,0.1)' : 'rgba(249,115,22,0.15)', borderWidth: 1, borderColor: theme === 'dark' ? 'rgba(255,255,255,0.2)' : 'rgba(249,115,22,0.3)' }]}
                  onPress={() => openPlanetChart(planet, planetChart)}
                >
                  <Text style={[styles.planetIcon, { color: iconColor }]}>{getPlanetIcon(planet)}</Text>
                  <Text style={[styles.planetName, { color: colors.text }]}>{planet}</Text>
                  <Text style={[styles.planetBindus, { color: colors.primary }]}>{totalBindus}</Text>
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
  const [yearlyStrength, setYearlyStrength] = useState(null);
  const [loadingYearly, setLoadingYearly] = useState(false);
  const [yearlyProgress, setYearlyProgress] = useState(0);

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
      
      const response = await fetch(`${API_BASE_URL}${getEndpoint('/ashtakavarga/life-predictions')}`, {
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
            place: birthData.place || '',
            gender: birthData.gender || ''
          }
        })
      });

      if (response.ok) {
        const predictions = await response.json();
        // console.log('Life predictions received:', predictions);
        setLoadingProgress(100);
        setLifePredictions(predictions);
        setShowLifePredictions(true);
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

  const fetchYearlyStrength = async (houseNumber) => {
    setLoadingYearly(true);
    setYearlyProgress(0);
    
    try {
      const token = await AsyncStorage.getItem('authToken');
      
      // Simulate progress (actual calculation happens on backend)
      const progressInterval = setInterval(() => {
        setYearlyProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + 2;
        });
      }, 500);
      
      const response = await fetch(`${API_BASE_URL}${getEndpoint('/ashtakavarga/yearly-house-strength')}`, {
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
            longitude: birthData.longitude
          },
          house_number: houseNumber,
          year: new Date().getFullYear()
        })
      });
      
      clearInterval(progressInterval);
      
      if (response.ok) {
        const data = await response.json();
        setYearlyProgress(100);
        setYearlyStrength(data);
      } else {
        console.error('Failed to fetch yearly strength:', response.status);
      }
    } catch (error) {
      console.error('Error fetching yearly strength:', error);
    } finally {
      setTimeout(() => {
        setLoadingYearly(false);
        setYearlyProgress(0);
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
        <LinearGradient colors={theme === 'dark' ? [colors.gradientStart, colors.gradientMid, colors.gradientEnd] : [colors.gradientStart, colors.gradientStart, colors.gradientStart]} style={styles.loadingGradient}>
          <Animated.View style={{ transform: [{ scale: pulseAnim }] }}>
            <Text style={styles.loadingText}>🔮</Text>
          </Animated.View>
          <Text style={[styles.loadingSubtext, { color: colors.text }]}>Consulting the Oracle...</Text>
        </LinearGradient>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <StatusBar barStyle={colors.statusBarStyle} backgroundColor={colors.background} translucent={false} />
      <LinearGradient colors={theme === 'dark' ? [colors.gradientStart, colors.gradientMid, colors.gradientEnd, colors.primary] : [colors.gradientStart, colors.gradientStart, colors.gradientStart, colors.gradientStart]} style={styles.gradient}>
        <SafeAreaView style={styles.safeArea}>
          <View style={styles.header}>
            <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backButton}>
              <Ionicons name="arrow-back" size={24} color={colors.text} />
            </TouchableOpacity>
            <Text style={[styles.headerTitle, { color: colors.text }]}>Ashtakvarga</Text>
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
                    <Ionicons name="close" size={24} color={colors.text} />
                  </TouchableOpacity>
                  
                  <ScrollView showsVerticalScrollIndicator={false}>
                    <Text style={[styles.predictionsTitle, { color: colors.text }]}>Life Predictions</Text>
                    <Text style={[styles.predictionsSubtitle, { color: colors.primary }]}>{lifePredictions?.methodology || "Vinay Aditya's Dots of Destiny"}</Text>
                    
                    <View style={styles.predictionsContent}>
                      {lifePredictions?.predictions?.current_life_phase && (
                        <>
                          <Text style={[styles.sectionTitle, { color: colors.primary }]}>Current Life Phase</Text>
                          <Text style={[styles.sectionText, { color: colors.textSecondary }]}>{lifePredictions.predictions.current_life_phase}</Text>
                        </>
                      )}
                      
                      {lifePredictions?.predictions?.sav_strength_analysis?.strong_areas && (
                        <>
                          <Text style={[styles.sectionTitle, { color: colors.primary }]}>Strong Areas</Text>
                          {lifePredictions.predictions.sav_strength_analysis.strong_areas.map((area, index) => (
                            <Text key={index} style={[styles.bulletPoint, { color: colors.textSecondary }]}>• {area}</Text>
                          ))}
                        </>
                      )}
                      
                      {lifePredictions?.predictions?.sav_strength_analysis?.challenging_areas && (
                        <>
                          <Text style={[styles.sectionTitle, { color: colors.primary }]}>Challenging Areas</Text>
                          {lifePredictions.predictions.sav_strength_analysis.challenging_areas.map((area, index) => (
                            <Text key={index} style={[styles.bulletPoint, { color: colors.textSecondary }]}>• {area}</Text>
                          ))}
                        </>
                      )}
                      
                      {lifePredictions?.predictions?.life_predictions?.next_6_months && (
                        <>
                          <Text style={[styles.sectionTitle, { color: colors.primary }]}>Next 6 Months</Text>
                          <Text style={[styles.sectionText, { color: colors.textSecondary }]}>{lifePredictions.predictions.life_predictions.next_6_months}</Text>
                        </>
                      )}
                      
                      {lifePredictions?.predictions?.life_predictions?.next_year && (
                        <>
                          <Text style={[styles.sectionTitle, { color: colors.primary }]}>Next Year</Text>
                          <Text style={[styles.sectionText, { color: colors.textSecondary }]}>{lifePredictions.predictions.life_predictions.next_year}</Text>
                        </>
                      )}
                      
                      {lifePredictions?.predictions?.remedial_measures && (
                        <>
                          <Text style={[styles.sectionTitle, { color: colors.primary }]}>Remedial Measures</Text>
                          {lifePredictions.predictions.remedial_measures.map((remedy, index) => (
                            <Text key={index} style={[styles.bulletPoint, { color: colors.textSecondary }]}>• {remedy}</Text>
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
            onRequestClose={() => {
              setShowSecretScroll(false);
              setYearlyStrength(null);
            }}
          >
            <View style={styles.modalOverlay}>
              <TouchableOpacity 
                style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0 }}
                activeOpacity={1}
                onPress={() => {
                  setShowSecretScroll(false);
                  setYearlyStrength(null);
                }}
              />
              <View style={styles.secretScroll}>
                <LinearGradient
                  colors={theme === 'dark' ? ['rgba(26, 0, 51, 0.95)', 'rgba(45, 27, 78, 0.9)'] : ['rgba(254, 252, 251, 0.98)', 'rgba(254, 252, 251, 0.95)']}
                  style={styles.scrollGradient}
                >
                  <TouchableOpacity 
                    style={styles.closeButton}
                    onPress={() => {
                      setShowSecretScroll(false);
                      setYearlyStrength(null);
                    }}
                  >
                    <Ionicons name="close" size={24} color={colors.text} />
                  </TouchableOpacity>
                  
                  {selectedPillar?.type === 'planet' ? (
                    <>
                      <Text style={[styles.scrollTitle, { color: colors.text }]}>
                        {selectedPillar.planet} Bhinnashtakvarga
                      </Text>
                      <Text style={[styles.scrollBindus, { color: colors.primary }]}>
                        {selectedPillar.planetChart.total} Total Points
                      </Text>
                      <View style={styles.planetChartGrid}>
                        {Object.entries(selectedPillar.planetChart.bindus).map(([sign, bindus]) => {
                          const signs = ['Ari', 'Tau', 'Gem', 'Can', 'Leo', 'Vir', 'Lib', 'Sco', 'Sag', 'Cap', 'Aqu', 'Pis'];
                          return (
                            <View key={sign} style={[styles.miniPillar, { backgroundColor: theme === 'dark' ? 'rgba(255,255,255,0.1)' : 'rgba(249,115,22,0.15)', borderRadius: 8, padding: 8, borderWidth: 1, borderColor: theme === 'dark' ? 'rgba(255,255,255,0.2)' : 'rgba(249,115,22,0.3)' }]}>
                              <Text style={[styles.miniBindus, { color: colors.primary }]}>{bindus}</Text>
                              <Text style={[styles.miniSign, { color: colors.textSecondary }]}>{signs[parseInt(sign)]}</Text>
                            </View>
                          );
                        })}
                      </View>
                      <Text style={[styles.scrollDescription, { color: colors.textSecondary }]}>
                        This shows where {selectedPillar.planet} receives support from other planets. Higher numbers indicate stronger beneficial influences in those zodiac signs.
                      </Text>
                    </>
                  ) : (
                    <ScrollView showsVerticalScrollIndicator={false}>
                      <Text style={[styles.scrollTitle, { color: colors.text }]}>
                        House {(selectedPillar?.index || 0) + 1}: {HOUSE_SIGNIFICATIONS[selectedPillar?.index || 0]?.name}
                      </Text>
                      <Text style={[styles.scrollBindus, { color: colors.primary }]}>
                        {selectedPillar?.bindus || 0} Cosmic Points
                      </Text>
                      
                      <View style={[styles.significationBox, { backgroundColor: theme === 'dark' ? 'rgba(255,255,255,0.05)' : 'rgba(249,115,22,0.08)', borderWidth: 1, borderColor: theme === 'dark' ? 'rgba(255,255,255,0.1)' : 'rgba(249,115,22,0.2)', borderRadius: 12, padding: 16, marginBottom: 20 }]}>
                        <Text style={[styles.significationTitle, { color: colors.primary }]}>House Significations:</Text>
                        <Text style={[styles.significationText, { color: colors.textSecondary }]}>
                          {HOUSE_SIGNIFICATIONS[selectedPillar?.index || 0]?.significations}
                        </Text>
                      </View>
                      
                      <Text style={[styles.scrollDescription, { color: colors.textSecondary }]}>
                        {completeOracleData?.pillar_insights?.[selectedPillar?.index] || 
                         (selectedPillar && selectedPillar.bindus >= 30 
                          ? `With ${selectedPillar.bindus} points, this house is strongly supported. Matters related to ${HOUSE_SIGNIFICATIONS[selectedPillar?.index || 0]?.name.toLowerCase()} will flourish with ease and bring positive results.`
                          : selectedPillar && selectedPillar.bindus <= 25
                          ? `With ${selectedPillar.bindus} points, this house needs attention. Matters of ${HOUSE_SIGNIFICATIONS[selectedPillar?.index || 0]?.name.toLowerCase()} may require extra effort and patience.`
                          : selectedPillar
                          ? `With ${selectedPillar.bindus} points, this house offers moderate support. Steady progress in ${HOUSE_SIGNIFICATIONS[selectedPillar?.index || 0]?.name.toLowerCase()} is possible through consistent effort.`
                          : 'Loading cosmic insights...'
                         )}
                      </Text>
                      
                      {!yearlyStrength && !loadingYearly && (
                        <TouchableOpacity 
                          style={styles.yearlyButton}
                          onPress={() => fetchYearlyStrength(selectedPillar?.index + 1)}
                        >
                          <LinearGradient
                            colors={['#ff6b35', '#ffd700']}
                            style={styles.yearlyButtonGradient}
                          >
                            <Text style={styles.yearlyButtonText}>📊 View Yearly Strength</Text>
                          </LinearGradient>
                        </TouchableOpacity>
                      )}
                      
                      {loadingYearly && (
                        <View style={styles.loadingYearlyContainer}>
                          <Text style={[styles.loadingYearlyText, { color: colors.text }]}>Calculating 365 days...</Text>
                          <View style={styles.progressBar}>
                            <View style={[styles.progressFill, { width: `${yearlyProgress}%` }]} />
                          </View>
                          <Text style={styles.progressText}>{Math.round(yearlyProgress)}%</Text>
                        </View>
                      )}
                      
                      {yearlyStrength && (
                        <View style={[styles.yearlyStrengthContainer, { backgroundColor: theme === 'dark' ? 'rgba(255,255,255,0.05)' : 'rgba(249,115,22,0.08)', borderWidth: 1, borderColor: theme === 'dark' ? 'rgba(255,255,255,0.1)' : 'rgba(249,115,22,0.2)' }]}>
                          <Text style={[styles.yearlyTitle, { color: colors.text }]}>House {yearlyStrength.house} - {yearlyStrength.year} Strength</Text>
                          <Text style={[styles.yearlySubtitle, { color: colors.primary }]}>Birth Chart: {yearlyStrength.birth_bindus} bindus</Text>
                          
                          <ScrollView style={styles.yearlyDataScroll} showsVerticalScrollIndicator={true}>
                            {yearlyStrength.daily_data && yearlyStrength.daily_data.map((day, index) => (
                              <View key={index} style={[
                                styles.dayRow,
                                { backgroundColor: theme === 'dark' ? 'rgba(255,255,255,0.05)' : 'rgba(249,115,22,0.08)' },
                                day.category === 'strong' && styles.strongDay,
                                day.category === 'weak' && styles.weakDay
                              ]}>
                                <Text style={[styles.dayDate, { color: colors.text }]}>{day.date}</Text>
                                <Text style={[styles.dayBindus, { color: colors.primary }]}>{day.bindus} bindus</Text>
                                <Text style={[
                                  styles.dayDiff,
                                  day.difference > 0 ? styles.positiveDiff : styles.negativeDiff
                                ]}>
                                  {day.difference > 0 ? '+' : ''}{day.difference}
                                </Text>
                                <Text style={[styles.dayCategory, { color: colors.textSecondary }]}>{day.category}</Text>
                              </View>
                            ))}
                          </ScrollView>
                        </View>
                      )}
                    </ScrollView>
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
  
  tabContent: { 
    flex: 1, 
    paddingHorizontal: 20,
  },
  
  titleContainer: {
    alignItems: 'center',
    paddingVertical: 5,
  },
  
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
    marginBottom: 10,
    marginTop: 5,
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
    paddingVertical: 8,
    paddingHorizontal: 12,
    alignItems: 'center',
  },
  lifePredictionsIcon: {
    fontSize: 18,
    marginBottom: 3,
  },
  lifePredictionsText: {
    fontSize: 12,
    fontWeight: '700',
    color: COLORS.white,
    textAlign: 'center',
    marginBottom: 1,
  },
  lifePredictionsSubtext: {
    fontSize: 10,
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
    fontSize: 20,
    fontWeight: '700',
    color: COLORS.white,
    textAlign: 'center',
    marginBottom: 4,
  },
  mapSubtitle: {
    fontSize: 12,
    color: 'rgba(255,255,255,0.7)',
    textAlign: 'center',
    marginBottom: 10,
  },
  chartContainer: {
    marginBottom: 2,
    paddingHorizontal: 5,
    paddingTop: 8,
    paddingBottom: 0,
    justifyContent: 'center',
    alignItems: 'center',
  },
  
  planetaryToggle: { 
    marginTop: 16,
    marginBottom: 8,
    paddingVertical: 5
  },
  toggleTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: COLORS.white,
    marginBottom: 8,
  },
  planetButton: {
    alignItems: 'center',
    paddingHorizontal: 8,
    paddingVertical: 6,
    marginRight: 8,
    borderRadius: 8,
    backgroundColor: 'rgba(255,255,255,0.1)',
  },
  planetIcon: { fontSize: 20, marginBottom: 4 },
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
    marginHorizontal: 4,
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
  yearlyButton: {
    borderRadius: 12,
    overflow: 'hidden',
    marginTop: 20,
  },
  yearlyButtonGradient: {
    paddingVertical: 14,
    paddingHorizontal: 20,
    alignItems: 'center',
  },
  yearlyButtonText: {
    fontSize: 15,
    fontWeight: '700',
    color: COLORS.white,
  },
  loadingYearlyContainer: {
    marginTop: 20,
    alignItems: 'center',
  },
  loadingYearlyText: {
    fontSize: 14,
    color: COLORS.white,
    marginBottom: 12,
  },
  yearlyStrengthContainer: {
    marginTop: 20,
    padding: 16,
    borderRadius: 12,
    maxHeight: 400,
  },
  yearlyTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: COLORS.white,
    marginBottom: 4,
  },
  yearlySubtitle: {
    fontSize: 13,
    color: '#ffd700',
    marginBottom: 16,
  },
  yearlyDataScroll: {
    maxHeight: 300,
  },
  dayRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
    paddingHorizontal: 12,
    marginBottom: 4,
    borderRadius: 8,
  },
  strongDay: {
    backgroundColor: 'rgba(0,255,0,0.1)',
    borderLeftWidth: 3,
    borderLeftColor: '#00ff00',
  },
  weakDay: {
    backgroundColor: 'rgba(255,0,0,0.1)',
    borderLeftWidth: 3,
    borderLeftColor: '#ff6b6b',
  },
  dayDate: {
    fontSize: 11,
    color: COLORS.white,
    flex: 2,
  },
  dayBindus: {
    fontSize: 12,
    fontWeight: '600',
    color: '#ffd700',
    flex: 1,
    textAlign: 'center',
  },
  dayDiff: {
    fontSize: 11,
    fontWeight: '600',
    flex: 1,
    textAlign: 'center',
  },
  positiveDiff: {
    color: '#00ff00',
  },
  negativeDiff: {
    color: '#ff6b6b',
  },
  dayCategory: {
    fontSize: 10,
    color: 'rgba(255,255,255,0.7)',
    flex: 1,
    textAlign: 'right',
    textTransform: 'capitalize',
  },
  significationBox: {
    marginVertical: 16,
  },
  significationTitle: {
    fontSize: 16,
    fontWeight: '700',
    marginBottom: 8,
  },
  significationText: {
    fontSize: 14,
    lineHeight: 22,
  },
  yearlyNote: {
    fontSize: 12,
    color: 'rgba(255,255,255,0.6)',
    fontStyle: 'italic',
    textAlign: 'center',
    marginTop: 20,
  },
};