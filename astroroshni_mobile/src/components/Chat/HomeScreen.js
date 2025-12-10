import React, { useEffect, useRef, useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  Animated,
  Dimensions,
  Alert,
  FlatList,
  AppState,
} from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import { LinearGradient } from 'expo-linear-gradient';
import Icon from '@expo/vector-icons/Ionicons';
import Svg, { Circle, Text as SvgText, G, Defs, RadialGradient, Stop, Path, Line } from 'react-native-svg';
import { COLORS } from '../../utils/constants';
import { chartAPI, panchangAPI, pricingAPI } from '../../services/api';

const { width } = Dimensions.get('window');

export default function HomeScreen({ birthData, onOptionSelect }) {
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(50)).current;
  const scaleAnim = useRef(new Animated.Value(0.9)).current;
  const pulseAnim = useRef(new Animated.Value(1)).current;
  const starAnims = useRef([...Array(20)].map(() => new Animated.Value(0))).current;
  
  const [dashData, setDashData] = useState(null);
  const [chartData, setChartData] = useState(null);
  const [transitData, setTransitData] = useState(null);
  const [panchangData, setPanchangData] = useState(null);
  const [pricing, setPricing] = useState({});
  const [loading, setLoading] = useState(true);
  
  useFocusEffect(
    React.useCallback(() => {
      loadHomeData();
    }, [birthData])
  );
  
  useEffect(() => {
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 1000,
        useNativeDriver: true,
      }),
      Animated.spring(slideAnim, {
        toValue: 0,
        tension: 50,
        friction: 8,
        useNativeDriver: true,
      }),
      Animated.spring(scaleAnim, {
        toValue: 1,
        tension: 50,
        friction: 7,
        useNativeDriver: true,
      }),
    ]).start();
    
    Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, {
          toValue: 1.05,
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
    
    starAnims.forEach((anim, index) => {
      Animated.loop(
        Animated.sequence([
          Animated.delay(index * 100),
          Animated.timing(anim, {
            toValue: 1,
            duration: 2000,
            useNativeDriver: true,
          }),
          Animated.timing(anim, {
            toValue: 0,
            duration: 2000,
            useNativeDriver: true,
          }),
        ])
      ).start();
    });
    
    loadHomeData();
    
    // Update Panchang daily at midnight
    const now = new Date();
    const tomorrow = new Date(now);
    tomorrow.setDate(tomorrow.getDate() + 1);
    tomorrow.setHours(0, 0, 0, 0);
    const msUntilMidnight = tomorrow.getTime() - now.getTime();
    
    const midnightTimer = setTimeout(() => {
      loadHomeData();
      // Set up daily interval after first midnight update
      const dailyInterval = setInterval(loadHomeData, 24 * 60 * 60 * 1000);
      return () => clearInterval(dailyInterval);
    }, msUntilMidnight);
    
    // Update when app becomes active (user returns from background)
    const handleAppStateChange = (nextAppState) => {
      if (nextAppState === 'active') {
        loadHomeData();
      }
    };
    
    const subscription = AppState.addEventListener('change', handleAppStateChange);
    
    return () => {
      clearTimeout(midnightTimer);
      subscription?.remove();
    };
  }, [birthData]);
  
const loadHomeData = async () => {
    try {
      setLoading(true);
      
      // Load pricing first
      try {
        const pricingResponse = await pricingAPI.getAnalysisPricing();
        if (pricingResponse?.data) {
          setPricing(pricingResponse.data);
        }
      } catch (pricingError) {
        console.log('Failed to load pricing:', pricingError);
      }
      
      const targetDate = new Date().toISOString().split('T')[0];
      
      // Load transits (no birth data needed) - wrapped in try-catch to not block other loading
      try {
        const transitResponse = await chartAPI.calculateTransits({}, targetDate);
        if (transitResponse?.data) {
          setTransitData(transitResponse.data);
        }
      } catch (transitError) {
      }
      
      // Load panchang for Delhi (default location) - wrapped in try-catch to not block birth chart loading
      try {
        const defaultLat = 28.6139;
        const defaultLon = 77.2090;
        
        const [panchangResponse, rahuKaalResponse, inauspiciousResponse, dailyPanchangResponse] = await Promise.allSettled([
          panchangAPI.calculateSunriseSunset(targetDate, defaultLat, defaultLon),
          panchangAPI.calculateRahuKaal(targetDate, defaultLat, defaultLon),
          panchangAPI.calculateInauspiciousTimes(targetDate, defaultLat, defaultLon),
          panchangAPI.calculateDailyPanchang(targetDate, defaultLat, defaultLon)
        ]);
        
        if (panchangResponse.status === 'fulfilled' && panchangResponse.value?.data) {
          let combinedPanchangData = panchangResponse.value.data;
          
          if (rahuKaalResponse.status === 'fulfilled' && rahuKaalResponse.value?.data) {
            combinedPanchangData.rahu_kaal = rahuKaalResponse.value.data;
          }
          
          if (inauspiciousResponse.status === 'fulfilled' && inauspiciousResponse.value?.data) {
            combinedPanchangData.inauspicious_times = inauspiciousResponse.value.data;
          }
          
          if (dailyPanchangResponse.status === 'fulfilled' && dailyPanchangResponse.value?.data) {
            const basicPanchang = dailyPanchangResponse.value.data.basic_panchang;
            if (basicPanchang) {
              combinedPanchangData.daily_panchang = {
                ...dailyPanchangResponse.value.data,
                nakshatra: basicPanchang.nakshatra,
                tithi: basicPanchang.tithi,
                yoga: basicPanchang.yoga,
                karana: basicPanchang.karana
              };
            }
          }
          
          setPanchangData(combinedPanchangData);
        }
      } catch (panchangError) {
      }
      
      
      // Load birth-dependent data if available
      let currentBirthData = birthData;
      
      if (!currentBirthData) {
        try {
          const { storage } = require('../../services/storage');
          let savedBirthData = await storage.getBirthData();
          
          // If not in storage, try to load from API
          if (!savedBirthData || !savedBirthData.name) {
            const { authAPI } = require('../../services/api');
            const response = await authAPI.getSelfBirthChart();
            if (response.data.has_self_chart) {
              savedBirthData = response.data;
              // Save to storage for future use
              await storage.setBirthData(savedBirthData);
            }
          }
          
          if (savedBirthData && savedBirthData.name) {
            currentBirthData = savedBirthData;
          }
        } catch (error) {
        }
      }
      
      
      if (currentBirthData) {
        const formattedBirthData = {
          name: currentBirthData.name,
          date: currentBirthData.date.includes('T') ? currentBirthData.date.split('T')[0] : currentBirthData.date,
          time: currentBirthData.time.includes('T') ? new Date(currentBirthData.time).toTimeString().slice(0, 5) : currentBirthData.time,
          latitude: parseFloat(currentBirthData.latitude),
          longitude: parseFloat(currentBirthData.longitude),
          timezone: currentBirthData.timezone || 'Asia/Kolkata',
          location: currentBirthData.place || 'Unknown'
        };
        
        const [dashResponse, chartResponse] = await Promise.allSettled([
          chartAPI.calculateCascadingDashas(formattedBirthData, targetDate),
          chartAPI.calculateChartOnly(formattedBirthData)
        ]);
        
        if (dashResponse.status === 'fulfilled' && dashResponse.value?.data && !dashResponse.value.data.error) {
          setDashData(dashResponse.value.data);
        }
        
        if (chartResponse.status === 'fulfilled' && chartResponse.value?.data) {
          setChartData(chartResponse.value.data);
        } else {
        }
      }
    } catch (error) {
    } finally {
      setLoading(false);
    }
  };
  
  const getPlanetColor = (planetName) => {
    const colors = {
      'Sun': '#ff6b35',
      'Moon': '#e0e0e0',
      'Mars': '#d32f2f',
      'Mercury': '#4caf50',
      'Jupiter': '#ffd700',
      'Venus': '#e91e63',
      'Saturn': '#2196f3',
      'Rahu': '#9e9e9e',
      'Ketu': '#795548',
    };
    return colors[planetName] || '#ffffff';
  };
  
  const getSignName = (signNumber) => {
    const signs = {
      0: 'Aries', 1: 'Taurus', 2: 'Gemini', 3: 'Cancer',
      4: 'Leo', 5: 'Virgo', 6: 'Libra', 7: 'Scorpio',
      8: 'Sagittarius', 9: 'Capricorn', 10: 'Aquarius', 11: 'Pisces'
    };
    return signs[signNumber] || signNumber;
  };
  
  const getSignIcon = (signNumber) => {
    const icons = {
      0: '♈', 1: '♉', 2: '♊', 3: '♋',
      4: '♌', 5: '♍', 6: '♎', 7: '♏',
      8: '♐', 9: '♑', 10: '♒', 11: '♓'
    };
    return icons[signNumber] || '⭐';
  };
  
  const getSignColor = (signNumber) => {
    const colors = {
      0: '#FF5733', 1: '#4CAF50', 2: '#FFC300', 3: '#2196F3',
      4: '#FF8C00', 5: '#8BC34A', 6: '#00BCD4', 7: '#673AB7',
      8: '#E91E63', 9: '#009688', 10: '#3F51B5', 11: '#9C27B0'
    };
    return colors[signNumber] || '#ffffff';
  };
  
  const place = birthData?.place || `${birthData?.latitude}, ${birthData?.longitude}`;
  const time = birthData?.time || 'Unknown time';

  const options = [
    {
      id: 'question',
      icon: '💬',
      title: 'Ask Any Question',
      description: 'Get insights about your personality, relationships, career, or any astrological topic',
      action: 'question'
    },
    {
      id: 'periods',
      icon: '🎯',
      title: 'Find Event Periods',
      description: 'Discover high-probability periods when specific events might happen',
      action: 'periods'
    }
  ];

  const analysisOptions = [
    { 
      id: 'career', 
      title: 'Career Analysis', 
      icon: '💼', 
      description: 'Professional success & opportunities',
      gradient: ['#6366F1', '#8B5CF6'],
      cost: pricing.career_analysis || 10
    },
    { 
      id: 'wealth', 
      title: 'Wealth Analysis', 
      icon: '💰', 
      description: 'Financial prospects & opportunities',
      gradient: ['#FFD700', '#FF8C00'],
      cost: pricing.wealth_analysis || 5
    },
    { 
      id: 'health', 
      title: 'Health Analysis', 
      icon: '🏥', 
      description: 'Wellness insights & precautions',
      gradient: ['#32CD32', '#228B22'],
      cost: pricing.health_analysis || 5
    },
    { 
      id: 'marriage', 
      title: 'Marriage Analysis', 
      icon: '💕', 
      description: 'Relationship compatibility & timing',
      gradient: ['#FF69B4', '#DC143C'],
      cost: pricing.marriage_analysis || 5
    },
    { 
      id: 'education', 
      title: 'Education Analysis', 
      icon: '🎓', 
      description: 'Learning path & career guidance',
      gradient: ['#4169E1', '#1E90FF'],
      cost: pricing.education_analysis || 5
    },
    { 
      id: 'progeny', 
      title: 'Progeny Analysis', 
      icon: '👨‍👩‍👧‍👦', 
      description: 'Fertility potential & family expansion',
      gradient: ['#FF69B4', '#FF1493'],
      cost: pricing.progeny_analysis || 15
    },
    { 
      id: 'trading', 
      title: 'Trading Forecast', 
      icon: '📈', 
      description: 'Stock market predictions & timing',
      gradient: ['#FFD700', '#FF8C00'],
      cost: 5
    },
    { 
      id: 'childbirth', 
      title: 'Childbirth Planner', 
      icon: '🤱', 
      description: 'Auspicious dates for delivery',
      gradient: ['#FF69B4', '#FF1493'],
      cost: pricing.childbirth_planner || 8
    },
    { 
      id: 'muhurat', 
      title: 'Muhurat Planner', 
      icon: '🕉️', 
      description: 'Auspicious timing for all events',
      gradient: ['#9C27B0', '#7B1FA2'],
      cost: 0
    }
  ];

  return (
    <View style={styles.container}>
      <LinearGradient
        colors={['#1a0033', '#2d1b4e', '#4a2c6d', '#ff6b35']}
        style={styles.gradient}
      >
        {starAnims.map((anim, index) => {
          const top = Math.random() * 100;
          const left = Math.random() * 100;
          return (
            <Animated.View
              key={index}
              style={[
                styles.star,
                {
                  top: `${top}%`,
                  left: `${left}%`,
                  opacity: anim,
                  zIndex: -1,
                },
              ]}
            >
              <Text style={styles.starText}>✨</Text>
            </Animated.View>
          );
        })}
        
      <ScrollView style={[styles.scrollView, { zIndex: 1 }]} contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <Animated.View style={[styles.greetingContainer, { opacity: fadeAnim, transform: [{ translateY: slideAnim }, { scale: scaleAnim }] }]}>
          <View style={styles.avatarContainer}>
            <Animated.View style={[styles.zodiacRing, { transform: [{ rotate: pulseAnim.interpolate({ inputRange: [1, 1.05], outputRange: ['0deg', '360deg'] }) }] }]}>
              <LinearGradient
                colors={['#ff6b35', '#ffd700', '#ff6b35']}
                style={styles.ringGradient}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 1 }}
              />
            </Animated.View>
            <Animated.View style={[styles.avatar, { transform: [{ scale: pulseAnim }] }]}>
              <Text key={chartData ? 'chart-loaded' : 'chart-loading'} style={styles.avatarText}>
                {chartData ? (() => {
                  const signIndex = chartData?.houses?.[0]?.sign || 0;
                  return getSignIcon(signIndex);
                })() : '♈'}
              </Text>
            </Animated.View>
          </View>
          
          <Text style={styles.greetingTitle}>
            Welcome, {birthData?.name}!
          </Text>
          <View style={styles.birthInfoCard}>
            <Text style={styles.birthInfoText}>
              📅 {new Date(birthData?.date).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}
            </Text>
            <Text style={styles.birthInfoText}>
              🕐 {time}
            </Text>
            <Text style={styles.birthInfoText}>
              📍 {place}
            </Text>
          </View>
          <Text style={styles.greetingSubtext}>
            Your cosmic blueprint awaits. Choose your path to enlightenment.
          </Text>
        </Animated.View>

        <Animated.View style={[styles.optionsContainer, { opacity: fadeAnim }]}>
          <Text style={styles.optionsTitle}>Choose Your Path</Text>
          {options.map((option, index) => (
            <OptionCard
              key={option.id}
              option={option}
              index={index}
              onOptionSelect={onOptionSelect}
            />
          ))}
        </Animated.View>

        {/* Life Analysis Options */}
        <Animated.View style={[styles.analysisContainer, { opacity: fadeAnim }]}>
          <Text style={styles.analysisTitle}>🧘 Life Analysis</Text>
          <View style={styles.lifeAnalysisGrid}>
            {analysisOptions.slice(0, 6).map((option, index) => (
              <LifeAnalysisCard
                key={option.id}
                option={option}
                index={index}
                onOptionSelect={onOptionSelect}
              />
            ))}
          </View>
        </Animated.View>

        {/* Timing Planners */}
        <Animated.View style={[styles.analysisContainer, { opacity: fadeAnim }]}>
          <Text style={styles.analysisTitle}>⏰ Timing Planners</Text>
          {analysisOptions.slice(6).map((option, index) => (
            <AnalysisCard
              key={option.id}
              option={option}
              index={index + 6}
              onOptionSelect={onOptionSelect}
            />
          ))}
        </Animated.View>



        {/* Magical Dashboard Cards - Moved to Bottom */}
        <Animated.View style={[styles.dashboardContainer, { opacity: fadeAnim }]}>
          <Text style={styles.dashboardTitle}>✨ Your Cosmic Dashboard</Text>
          


          {/* Big 3 Signs Row */}
          <View style={styles.bigThreeRow}>
            <View style={styles.signCard}>
              <LinearGradient colors={['#1E3A8A', '#3B82F6']} style={styles.signGradient}>
                <Text style={styles.signEmoji}>⬆️</Text>
                <Text style={styles.signLabel}>Ascendant</Text>
                <Text style={styles.signValue}>{chartData?.houses?.[0]?.sign !== undefined ? (() => {
                  const signIndex = chartData.houses[0].sign;
                  return `${getSignIcon(signIndex)} ${getSignName(signIndex).slice(0, 3)}`;
                })() : loading ? '...' : 'N/A'}</Text>
              </LinearGradient>
            </View>
            
            <View style={styles.signCard}>
              <LinearGradient colors={['#7C2D12', '#DC2626']} style={styles.signGradient}>
                <Text style={styles.signEmoji}>🌙</Text>
                <Text style={styles.signLabel}>Moon</Text>
                <Text style={styles.signValue}>{chartData?.planets?.Moon?.sign !== undefined ? `${getSignIcon(chartData.planets.Moon.sign)} ${getSignName(chartData.planets.Moon.sign).slice(0, 3)}` : loading ? '...' : 'N/A'}</Text>
              </LinearGradient>
            </View>
            
            <View style={styles.signCard}>
              <LinearGradient colors={['#B45309', '#F59E0B']} style={styles.signGradient}>
                <Text style={styles.signEmoji}>☀️</Text>
                <Text style={styles.signLabel}>Sun</Text>
                <Text style={styles.signValue}>{chartData?.planets?.Sun?.sign !== undefined ? `${getSignIcon(chartData.planets.Sun.sign)} ${getSignName(chartData.planets.Sun.sign).slice(0, 3)}` : loading ? '...' : 'N/A'}</Text>
              </LinearGradient>
            </View>
          </View>

          {/* Current Dasha Chips - Under Birth Chart */}
          {dashData && (
            <Animated.View style={[styles.dashaSection, { opacity: fadeAnim }]}>
              <Text style={styles.dashaSectionTitle}>⏰ Current Dasha Periods</Text>
              <FlatList
                horizontal
                showsHorizontalScrollIndicator={false}
                data={[
                  dashData.maha_dashas?.find(d => d.current),
                  dashData.antar_dashas?.find(d => d.current),
                  dashData.pratyantar_dashas?.find(d => d.current),
                  dashData.sookshma_dashas?.find(d => d.current),
                  dashData.prana_dashas?.find(d => d.current)
                ].filter(Boolean)}
                keyExtractor={(item, index) => index.toString()}
                renderItem={({ item: dasha }) => {
                  const planetColor = getPlanetColor(dasha.planet);
                  const startDate = new Date(dasha.start).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: '2-digit' });
                  const endDate = new Date(dasha.end).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: '2-digit' });
                  return (
                    <View 
                      style={[styles.dashaChip, { backgroundColor: planetColor + '20', borderColor: planetColor }]}
                    >
                      <Text style={[styles.dashaChipPlanet, { color: planetColor }]}>{dasha.planet}</Text>
                      <Text style={styles.dashaChipDates}>{startDate}</Text>
                      <Text style={styles.dashaChipDates}>{endDate}</Text>
                    </View>
                  );
                }}
                contentContainerStyle={styles.dashaFlatListContent}
                snapToInterval={118}
                decelerationRate="fast"
                pagingEnabled={false}
              />
            </Animated.View>
          )}

          {/* Zodiac Wheel - Vibrant Design */}
          <View style={styles.planetarySection}>
            <Text style={styles.planetarySectionTitle}>🪐 Current Planetary Transits</Text>
            <View style={styles.planetGrid}>
              {transitData?.planets && Object.entries(transitData.planets).map(([planet, data]) => (
                <View key={planet} style={[
                  styles.planetCard,
                  { backgroundColor: getSignColor(data.sign) + '20', borderColor: getSignColor(data.sign) }
                ]}>
                  <Text style={styles.planetName}>{planet}</Text>
                  <Text style={styles.planetSign}>{getSignIcon(data.sign)} {getSignName(data.sign)}</Text>
                  <Text style={styles.planetDegree}>{data.degree.toFixed(2)}°</Text>
                </View>
              ))}
            </View>
          </View>

          {/* Panchang Timeline */}
          {panchangData && (
            <View style={styles.panchangCard}>
              <Text style={[styles.panchangTitle, { textAlign: 'center', marginBottom: 20 }]}>🌅 Today's Panchang</Text>
              <View style={styles.sunTimesRow}>
                <View style={styles.sunTimeItem}>
                  <Text style={styles.sunTimeEmoji}>🌅</Text>
                  <Text style={styles.sunTimeLabel}>Sunrise</Text>
                  <Text style={styles.sunTimeValue}>{panchangData.sunrise ? new Date(panchangData.sunrise).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true }) : '6:30 AM'}</Text>
                </View>
                <View style={styles.sunTimeItem}>
                  <Text style={styles.sunTimeEmoji}>🌇</Text>
                  <Text style={styles.sunTimeLabel}>Sunset</Text>
                  <Text style={styles.sunTimeValue}>{panchangData.sunset ? new Date(panchangData.sunset).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true }) : '6:45 PM'}</Text>
                </View>
              </View>
              
              <View style={styles.sunTimesRow}>
                <View style={styles.sunTimeItem}>
                  <Text style={styles.sunTimeEmoji}>🌙</Text>
                  <Text style={styles.sunTimeLabel}>Moonrise</Text>
                  <Text style={styles.sunTimeValue}>{panchangData.daily_panchang?.sunrise_sunset?.moonrise || panchangData.sunrise_sunset?.moonrise || '7:53 AM'}</Text>
                </View>
                <View style={styles.sunTimeItem}>
                  <Text style={styles.sunTimeEmoji}>🌚</Text>
                  <Text style={styles.sunTimeLabel}>Moonset</Text>
                  <Text style={styles.sunTimeValue}>{panchangData.daily_panchang?.sunrise_sunset?.moonset || panchangData.sunrise_sunset?.moonset || '6:06 PM'}</Text>
                </View>
              </View>
              
              {/* Panchang Elements Section */}
              {panchangData.daily_panchang && (
                <View style={styles.panchangElementsSection}>
                  <Text style={styles.panchangElementsTitle}>🕉️ Panchang Elements</Text>
                  
                  {/* Nakshatra */}
                  {panchangData.daily_panchang.nakshatra && (
                    <View style={styles.panchangElement}>
                      <Text style={styles.elementLabel}>⭐ Nakshatra:</Text>
                      <Text style={styles.elementValue}>{panchangData.daily_panchang.nakshatra.name}</Text>
                    </View>
                  )}
                  
                  {/* Tithi */}
                  {panchangData.daily_panchang.tithi && (
                    <View style={styles.panchangElement}>
                      <Text style={styles.elementLabel}>🌙 Tithi:</Text>
                      <Text style={styles.elementValue}>{panchangData.daily_panchang.tithi.name}</Text>
                    </View>
                  )}
                  
                  {/* Yoga */}
                  {panchangData.daily_panchang.yoga && (
                    <View style={styles.panchangElement}>
                      <Text style={styles.elementLabel}>🧘 Yoga:</Text>
                      <Text style={styles.elementValue}>{panchangData.daily_panchang.yoga.name}</Text>
                    </View>
                  )}
                  
                  {/* Karana */}
                  {panchangData.daily_panchang.karana && (
                    <View style={styles.panchangElement}>
                      <Text style={styles.elementLabel}>⚡ Karana:</Text>
                      <Text style={styles.elementValue}>{panchangData.daily_panchang.karana.name}</Text>
                    </View>
                  )}
                </View>
              )}
              

              
              {/* Row 1: Moon Phase Text and Illumination */}
              <View style={styles.moonPhaseTextRow}>
                <Text style={styles.moonPhaseText}>{panchangData.moon_phase || 'Full Moon'}</Text>
                <Text style={styles.moonIllumination}>{panchangData.moon_illumination ? `${panchangData.moon_illumination.toFixed(1)}%` : '98.5%'}</Text>
              </View>
              
              {/* Row 2: Big Moon SVG Only */}
              <View style={styles.moonSvgRow}>
                <Svg width="80" height="80" viewBox="0 0 80 80">
                  {/* Dark Background Circle */}
                  <Circle cx="40" cy="40" r="35" fill="#1a1a1a" stroke="rgba(255,255,255,0.1)" strokeWidth="1" />
                  
                  {(() => {
                    const illumination = panchangData.moon_illumination || 98.5;
                    const phase = panchangData.moon_phase || 'Full Moon';
                    const r = 33;
                    const cx = 40;
                    const cy = 40;
                    
                    const isWaxing = phase.includes('Waxing') || (!phase.includes('Waning') && !phase.includes('Full') && !phase.includes('New'));

                    if (illumination >= 99) {
                      return <Circle cx="40" cy="40" r="33" fill="#f0f0f0" />;
                    } else if (illumination <= 1) {
                      return null;
                    } 
                    
                    const ellipseRadiusX = r * Math.abs(1 - (2 * illumination / 100));
                    
                    let pathData = "";

                    if (isWaxing) {
                      pathData = `M ${cx} ${cy - r} A ${r} ${r} 0 0 1 ${cx} ${cy + r}`;
                      
                      if (illumination > 50) {
                        pathData += ` A ${ellipseRadiusX} ${r} 0 0 1 ${cx} ${cy - r}`;
                      } else {
                        pathData += ` A ${ellipseRadiusX} ${r} 0 0 0 ${cx} ${cy - r}`;
                      }
                    } else {
                      pathData = `M ${cx} ${cy + r} A ${r} ${r} 0 0 1 ${cx} ${cy - r}`;
                      
                      if (illumination > 50) {
                        pathData += ` A ${ellipseRadiusX} ${r} 0 0 1 ${cx} ${cy + r}`;
                      } else {
                        pathData += ` A ${ellipseRadiusX} ${r} 0 0 0 ${cx} ${cy + r}`;
                      }
                    }

                    return (
                      <Path 
                        d={pathData} 
                        fill="#f0f0f0"
                        stroke="none"
                      />
                    );
                  })()}
                </Svg>
              </View>
              
              {/* Row 3: Day Progress */}
              <View style={styles.dayProgressBar}>
                <View style={styles.progressTrack}>
                  {(() => {
                    const now = new Date();
                    const sunrise = new Date(panchangData.sunrise);
                    const sunset = new Date(panchangData.sunset);
                    const totalDayTime = sunset.getTime() - sunrise.getTime();
                    const elapsedTime = now.getTime() - sunrise.getTime();
                    const progress = Math.max(0, Math.min(100, (elapsedTime / totalDayTime) * 100));
                    return (
                      <>
                        <View style={[styles.progressFill, { width: `${progress}%` }]} />
                        <View style={[styles.currentTimeDot, { left: `${progress}%` }]} />
                      </>
                    );
                  })()}
                </View>
                <Text style={styles.progressLabel}>Day Progress</Text>
              </View>
              
              <View style={styles.muhurtaSection}>
                <Text style={styles.muhurtaTitle}>🕉️ Auspicious Times</Text>
                <View style={styles.muhurtaRow}>
                  <Text style={styles.muhurtaLabel}>Brahma Muhurta:</Text>
                  <Text style={styles.muhurtaTime}>
                    {panchangData.brahma_muhurta_start && panchangData.brahma_muhurta_end ? 
                      `${new Date(panchangData.brahma_muhurta_start).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true })} - ${new Date(panchangData.brahma_muhurta_end).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true })}` : 
                      '4:29 AM - 6:05 AM'
                    }
                  </Text>
                </View>
                <View style={styles.muhurtaRow}>
                  <Text style={styles.muhurtaLabel}>Abhijit Muhurta:</Text>
                  <Text style={styles.muhurtaTime}>
                    {panchangData.abhijit_muhurta_start && panchangData.abhijit_muhurta_end ? 
                      `${new Date(panchangData.abhijit_muhurta_start).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true })} - ${new Date(panchangData.abhijit_muhurta_end).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true })}` : 
                      '11:36 AM - 12:24 PM'
                    }
                  </Text>
                </View>
              </View>
              
              {(panchangData.rahu_kaal || panchangData.inauspicious_times) && (
                <View style={styles.inauspiciousSection}>
                  <Text style={styles.inauspiciousTitle}>⚠️ Inauspicious Times</Text>
                  
                  {panchangData.rahu_kaal && (
                    <View style={styles.muhurtaRow}>
                      <Text style={styles.muhurtaLabel}>Rahu Kaal:</Text>
                      <Text style={styles.inauspiciousTime}>
                        {panchangData.rahu_kaal.rahu_kaal_start && panchangData.rahu_kaal.rahu_kaal_end ? 
                          `${new Date(panchangData.rahu_kaal.rahu_kaal_start).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true })} - ${new Date(panchangData.rahu_kaal.rahu_kaal_end).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true })}` : 
                          'Not available'
                        }
                      </Text>
                    </View>
                  )}
                  
                  {panchangData.inauspicious_times?.dur_muhurta?.map((period, index) => (
                    <View key={`dur-${index}`} style={styles.muhurtaRow}>
                      <Text style={styles.muhurtaLabel}>Dur Muhurta:</Text>
                      <Text style={styles.inauspiciousTime}>
                        {period.start_time && period.end_time ? 
                          `${new Date(period.start_time).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true })} - ${new Date(period.end_time).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true })}` : 
                          'Not available'
                        }
                      </Text>
                    </View>
                  ))}
                  
                  {panchangData.inauspicious_times?.varjyam?.map((period, index) => (
                    <View key={`varjyam-${index}`} style={styles.muhurtaRow}>
                      <Text style={styles.muhurtaLabel}>Varjyam:</Text>
                      <Text style={styles.inauspiciousTime}>
                        {period.start_time && period.end_time ? 
                          `${new Date(period.start_time).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true })} - ${new Date(period.end_time).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true })}` : 
                          'Not available'
                        }
                      </Text>
                    </View>
                  ))}
                </View>
              )}
            </View>
          )}

        </Animated.View>
      </ScrollView>
      </LinearGradient>
    </View>
  );
}

// Separate component to avoid hooks order violation
function OptionCard({ option, index, onOptionSelect }) {
  const cardDelay = (index + 1) * 200;
  const cardAnim = useRef(new Animated.Value(0)).current;
  
  useEffect(() => {
    Animated.sequence([
      Animated.delay(cardDelay),
      Animated.spring(cardAnim, {
        toValue: 1,
        tension: 50,
        friction: 7,
        useNativeDriver: true,
      }),
    ]).start();
  }, []);
  
  return (
    <Animated.View
      style={[
        styles.optionCard,
        {
          opacity: cardAnim,
          transform: [
            {
              translateY: cardAnim.interpolate({
                inputRange: [0, 1],
                outputRange: [50, 0],
              }),
            },
            {
              scale: cardAnim.interpolate({
                inputRange: [0, 1],
                outputRange: [0.9, 1],
              }),
            },
          ],
        },
      ]}
    >
      <TouchableOpacity
        onPress={() => onOptionSelect(option)}
        activeOpacity={0.9}
      >
        <LinearGradient
          colors={['rgba(255, 255, 255, 0.15)', 'rgba(255, 255, 255, 0.05)']}
          style={styles.optionGradient}
        >
          <View style={styles.optionIconContainer}>
            <LinearGradient
              colors={['#ff6b35', '#ff8c5a']}
              style={styles.optionIconGradient}
            >
              <Text style={styles.optionEmoji}>{option.icon}</Text>
            </LinearGradient>
          </View>
          <View style={styles.optionContent}>
            <Text style={styles.optionTitle}>{option.title}</Text>
            <Text style={styles.optionDescription}>{option.description}</Text>
          </View>
          <Icon name="chevron-forward" size={24} color="rgba(255, 255, 255, 0.6)" />
        </LinearGradient>
      </TouchableOpacity>
    </Animated.View>
  );
}

// Life Analysis Card - 3 per row
function LifeAnalysisCard({ option, index, onOptionSelect }) {
  const cardDelay = (index + 3) * 200;
  const cardAnim = useRef(new Animated.Value(0)).current;
  
  useEffect(() => {
    Animated.sequence([
      Animated.delay(cardDelay),
      Animated.spring(cardAnim, {
        toValue: 1,
        tension: 50,
        friction: 7,
        useNativeDriver: true,
      }),
    ]).start();
  }, []);
  
  return (
    <Animated.View
      style={[
        styles.lifeAnalysisCard,
        {
          opacity: cardAnim,
          transform: [
            {
              translateY: cardAnim.interpolate({
                inputRange: [0, 1],
                outputRange: [50, 0],
              }),
            },
            {
              scale: cardAnim.interpolate({
                inputRange: [0, 1],
                outputRange: [0.9, 1],
              }),
            },
          ],
        },
      ]}
    >
      <TouchableOpacity
        onPress={() => onOptionSelect({ action: 'analysis', type: option.id })}
        activeOpacity={0.9}
      >
        <LinearGradient
          colors={option.gradient}
          style={styles.lifeAnalysisGradient}
        >
          <Text style={styles.lifeAnalysisEmoji}>{option.icon}</Text>
          <Text style={styles.lifeAnalysisTitle}>{option.title}</Text>
          <Text style={styles.lifeAnalysisDescription}>{option.description}</Text>
        </LinearGradient>
      </TouchableOpacity>
    </Animated.View>
  );
}

// Full width Analysis Card for Timing Planners
function AnalysisCard({ option, index, onOptionSelect }) {
  const cardDelay = (index + 9) * 200;
  const cardAnim = useRef(new Animated.Value(0)).current;
  
  useEffect(() => {
    Animated.sequence([
      Animated.delay(cardDelay),
      Animated.spring(cardAnim, {
        toValue: 1,
        tension: 50,
        friction: 7,
        useNativeDriver: true,
      }),
    ]).start();
  }, []);
  
  return (
    <Animated.View
      style={[
        styles.analysisCard,
        {
          opacity: cardAnim,
          transform: [
            {
              translateY: cardAnim.interpolate({
                inputRange: [0, 1],
                outputRange: [50, 0],
              }),
            },
            {
              scale: cardAnim.interpolate({
                inputRange: [0, 1],
                outputRange: [0.9, 1],
              }),
            },
          ],
        },
      ]}
    >
      <TouchableOpacity
        onPress={() => {
          if (option.id === 'muhurat') {
            onOptionSelect({ action: 'muhurat' });
          } else {
            onOptionSelect({ action: 'analysis', type: option.id });
          }
        }}
        activeOpacity={0.9}
      >
        <LinearGradient
          colors={option.gradient}
          style={styles.analysisGradient}
        >
          <View style={styles.analysisIconContainer}>
            <Text style={styles.analysisEmoji}>{option.icon}</Text>
          </View>
          <View style={styles.analysisContent}>
            <Text style={styles.analysisCardTitle}>{option.title}</Text>
            <Text style={styles.analysisDescription}>{option.description}</Text>
          </View>
          <Icon name="chevron-forward" size={24} color="rgba(255, 255, 255, 0.9)" />
        </LinearGradient>
      </TouchableOpacity>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  gradient: {
    flex: 1,
  },
  scrollView: {
    flex: 1,
  },
  content: {
    padding: 20,
    paddingBottom: 40,
  },
  star: {
    position: 'absolute',
  },
  starText: {
    fontSize: 12,
  },
  greetingContainer: {
    alignItems: 'center',
    marginBottom: 40,
    paddingVertical: 30,
  },
  avatarContainer: {
    position: 'relative',
    marginBottom: 24,
  },
  zodiacRing: {
    position: 'absolute',
    width: 120,
    height: 120,
    borderRadius: 60,
    top: -10,
    left: -10,
  },
  ringGradient: {
    width: '100%',
    height: '100%',
    borderRadius: 60,
    opacity: 0.3,
  },
  avatar: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: 'rgba(255, 255, 255, 0.15)',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 3,
    borderColor: 'rgba(255, 255, 255, 0.3)',
    shadowColor: '#ff6b35',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.6,
    shadowRadius: 20,
    elevation: 10,
  },
  avatarText: {
    fontSize: 48,
  },
  greetingTitle: {
    fontSize: 32,
    fontWeight: '700',
    color: COLORS.white,
    textAlign: 'center',
    marginBottom: 16,
    textShadowColor: 'rgba(0, 0, 0, 0.3)',
    textShadowOffset: { width: 0, height: 2 },
    textShadowRadius: 4,
  },
  birthInfoCard: {
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 12,
    padding: 12,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.2)',
  },
  birthInfoText: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.9)',
    textAlign: 'center',
    marginVertical: 2,
  },
  greetingSubtext: {
    fontSize: 16,
    color: 'rgba(255, 255, 255, 0.8)',
    textAlign: 'center',
    lineHeight: 24,
    paddingHorizontal: 20,
  },
  optionsContainer: {
    marginBottom: 30,
  },
  optionsTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: COLORS.white,
    textAlign: 'center',
    marginBottom: 24,
    textShadowColor: 'rgba(0, 0, 0, 0.3)',
    textShadowOffset: { width: 0, height: 2 },
    textShadowRadius: 4,
  },
  optionCard: {
    marginBottom: 16,
    borderRadius: 20,
    overflow: 'hidden',
  },
  optionGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 20,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.2)',
  },
  optionIconContainer: {
    marginRight: 16,
  },
  optionIconGradient: {
    width: 60,
    height: 60,
    borderRadius: 30,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 2,
    borderColor: 'rgba(255, 255, 255, 0.3)',
  },
  optionEmoji: {
    fontSize: 28,
  },
  optionContent: {
    flex: 1,
  },
  optionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: COLORS.white,
    marginBottom: 6,
  },
  optionDescription: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.7)',
    lineHeight: 20,
  },
  quickQuestionsContainer: {
    alignItems: 'center',
    paddingVertical: 20,
    paddingHorizontal: 20,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 16,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.2)',
  },
  quickQuestionsTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1a1a1a',
    textAlign: 'center',
    marginBottom: 8,
    textShadowColor: 'rgba(255, 255, 255, 0.8)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 2,
  },
  quickQuestionsSubtext: {
    fontSize: 14,
    color: '#2d2d2d',
    textAlign: 'center',
    lineHeight: 20,
    textShadowColor: 'rgba(255, 255, 255, 0.6)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 1,
  },
  analysisContainer: {
    marginBottom: 30,
  },
  analysisTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: COLORS.white,
    textAlign: 'center',
    marginBottom: 24,
    textShadowColor: 'rgba(0, 0, 0, 0.3)',
    textShadowOffset: { width: 0, height: 2 },
    textShadowRadius: 4,
  },
  analysisCard: {
    marginBottom: 16,
    borderRadius: 20,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 6,
  },
  glassmorphismContainer: {
    position: 'relative',
    borderRadius: 20,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.2)',
  },
  glassmorphismOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    zIndex: 1,
  },
  analysisGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 20,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.2)',
  },
  analysisIconContainer: {
    marginRight: 16,
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 2,
    borderColor: 'rgba(255, 255, 255, 0.4)',
  },
  analysisEmoji: {
    fontSize: 28,
  },
  analysisContent: {
    flex: 1,
  },
  analysisCardTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: COLORS.white,
    marginBottom: 6,
  },
  analysisDescription: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.9)',
    lineHeight: 20,
    marginBottom: 6,
  },
  analysisCost: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.8)',
    fontWeight: '600',
  },
  // Life Analysis Grid Styles
  lifeAnalysisGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    gap: 6,
  },
  lifeAnalysisCard: {
    width: '30%',
    marginBottom: 10,
    borderRadius: 12,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 6,
  },
  lifeAnalysisGradient: {
    padding: 8,
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 10,
    minHeight: 120,
  },
  lifeAnalysisEmoji: {
    fontSize: 18,
    marginBottom: 6,
  },
  lifeAnalysisTitle: {
    fontSize: 10,
    fontWeight: '700',
    color: COLORS.white,
    marginBottom: 6,
    textAlign: 'center',
    lineHeight: 12,
  },
  lifeAnalysisDescription: {
    fontSize: 8,
    color: 'rgba(255, 255, 255, 0.9)',
    textAlign: 'center',
    lineHeight: 10,
    paddingHorizontal: 2,
  },
  lifeAnalysisCost: {
    fontSize: 10,
    color: 'rgba(255, 255, 255, 0.8)',
    fontWeight: '600',
  },
  // Dashboard Cards Styles
  dashboardContainer: {
    marginBottom: 30,
  },
  dashboardTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: COLORS.white,
    textAlign: 'center',
    marginBottom: 20,
    textShadowColor: 'rgba(0, 0, 0, 0.3)',
    textShadowOffset: { width: 0, height: 2 },
    textShadowRadius: 4,
  },
  dashboardCard: {
    marginBottom: 16,
    borderRadius: 20,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.3,
    shadowRadius: 12,
    elevation: 8,
  },
loadingText: {
    color: 'rgba(255, 255, 255, 0.7)',
    fontSize: 14,
    fontStyle: 'italic',
    textAlign: 'center',
    marginTop: 20,
  },
  debugText: {
    color: 'rgba(255, 255, 255, 0.5)',
    fontSize: 10,
    marginBottom: 8,
  },
  
  // Dasha Timeline Card
  dashaTimelineCard: {
    height: 140,
  },
  dashaCardGradient: {
    padding: 20,
    height: '100%',
    borderWidth: 1,
    borderColor: 'rgba(255, 107, 53, 0.3)',
  },
  dashaHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  dashaEmoji: {
    fontSize: 20,
    marginRight: 10,
  },
  dashaTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.white,
  },
  dashaContent: {
    flex: 1,
  },
  dashaChipsContainer: {
    marginBottom: 12,
  },
dashaSection: {
    marginTop: 16,
    marginBottom: 24,
  },
  dashaSectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: COLORS.white,
    marginBottom: 12,
    paddingHorizontal: 4,
    textAlign: 'center',
  },
dashaChip: {
    borderWidth: 1.5,
    borderRadius: 16,
    paddingHorizontal: 10,
    paddingVertical: 10,
    alignItems: 'center',
    marginRight: 8,
    width: 110,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 4,
    elevation: 3,
  },
  dashaFlatListContent: {
    paddingHorizontal: 4,
  },
  dashaChipPlanet: {
    fontSize: 14,
    fontWeight: '700',
    marginBottom: 2,
  },
  dashaChipDates: {
    fontSize: 10,
    color: 'rgba(255, 255, 255, 0.8)',
    fontWeight: '500',
  },

  
  // Big Three Signs Row
  bigThreeRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 16,
    gap: 8,
  },
  signCard: {
    flex: 1,
    borderRadius: 16,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 6,
  },
  signGradient: {
    padding: 16,
    alignItems: 'center',
    minHeight: 100,
    justifyContent: 'center',
  },
  signEmoji: {
    fontSize: 24,
    marginBottom: 8,
  },
  signLabel: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.8)',
    fontWeight: '600',
    marginBottom: 4,
  },
  signValue: {
    fontSize: 13,
    fontWeight: '700',
    color: COLORS.white,
    textAlign: 'center',
  },
  
  // Zodiac Wheel - Vibrant Design
  planetarySection: {
    marginBottom: 24,
    alignItems: 'center',
  },
  planetarySectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: COLORS.white,
    marginBottom: 12,
    paddingHorizontal: 4,
    textAlign: 'center',
  },
  planetGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    gap: 8,
  },
  planetCard: {
    width: '30%',
    borderRadius: 12,
    borderWidth: 1.5,
    padding: 12,
    alignItems: 'center',
    marginBottom: 8,
  },
  planetName: {
    fontSize: 12,
    fontWeight: '700',
    color: COLORS.white,
    marginBottom: 4,
  },
  planetSign: {
    fontSize: 11,
    color: 'rgba(255, 255, 255, 0.9)',
    marginBottom: 2,
  },
  planetDegree: {
    fontSize: 10,
    color: 'rgba(255, 255, 255, 0.7)',
    fontWeight: '500',
  },

  loadingOverlay: {
    position: 'absolute',
    top: '50%',
    left: '50%',
    transform: [{ translateX: -30 }, { translateY: -10 }],
    color: 'rgba(255, 255, 255, 0.8)',
    fontSize: 14,
    fontWeight: '600',
  },
  
  // Panchang Card Styles
  panchangCard: {
    marginBottom: 40,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 16,
    padding: 20,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.2)',
  },
  panchangTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: COLORS.white,
    textAlign: 'center',
    marginBottom: 12,
    paddingHorizontal: 4,
  },
  sunTimesRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 20,
  },
  sunTimeItem: {
    alignItems: 'center',
    flex: 1,
  },
  sunTimeEmoji: {
    fontSize: 24,
    marginBottom: 8,
  },
  sunTimeLabel: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.7)',
    marginBottom: 4,
  },
  sunTimeValue: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.white,
  },
  dayProgressBar: {
    alignItems: 'center',
  },
  progressTrack: {
    width: '100%',
    height: 6,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    borderRadius: 3,
    position: 'relative',
    marginBottom: 8,
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#ff6b35',
    borderRadius: 3,
  },
  currentTimeDot: {
    position: 'absolute',
    right: '55%',
    top: -3,
    width: 12,
    height: 12,
    borderRadius: 6,
    backgroundColor: '#ffd700',
    borderWidth: 2,
    borderColor: COLORS.white,
  },
  progressLabel: {
    fontSize: 11,
    color: 'rgba(255, 255, 255, 0.6)',
  },
  muhurtaSection: {
    marginTop: 20,
    marginBottom: 16,
    backgroundColor: 'rgba(16, 185, 129, 0.1)',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: 'rgba(16, 185, 129, 0.3)',
  },
  muhurtaTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#10B981',
    textAlign: 'center',
    marginBottom: 12,
  },
  muhurtaRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
    paddingHorizontal: 12,
    marginBottom: 6,
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    borderRadius: 8,
  },
  muhurtaLabel: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.8)',
    fontWeight: '500',
  },
  muhurtaTime: {
    fontSize: 12,
    fontWeight: '600',
    color: '#10B981',
  },
  inauspiciousSection: {
    marginTop: 16,
    marginBottom: 16,
    backgroundColor: 'rgba(239, 68, 68, 0.1)',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: 'rgba(239, 68, 68, 0.3)',
  },
  inauspiciousTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#EF4444',
    textAlign: 'center',
    marginBottom: 12,
  },
  inauspiciousTime: {
    fontSize: 12,
    fontWeight: '600',
    color: '#EF4444',
  },
  panchangElementsSection: {
    marginBottom: 16,
  },
  panchangElementsTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#ffd700',
    textAlign: 'center',
    marginBottom: 12,
  },
  panchangElement: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
    paddingHorizontal: 12,
    marginBottom: 6,
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
  },
  elementLabel: {
    fontSize: 13,
    color: 'rgba(255, 255, 255, 0.8)',
    fontWeight: '500',
  },
  elementValue: {
    fontSize: 13,
    fontWeight: '600',
    color: '#ffd700',
  },
  moonPhaseTextRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  moonSvgRow: {
    alignItems: 'center',
    marginBottom: 20,
  },
  moonPhaseText: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.white,
    marginBottom: 4,
  },
  moonIllumination: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.8)',
  },
  
  // Panchang Weather Card
  panchangWeatherCard: {
    height: 200,
  },
  panchangCardGradient: {
    padding: 20,
    height: '100%',
  },
  panchangHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  panchangEmoji: {
    fontSize: 20,
    marginRight: 10,
  },
  panchangTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.white,
  },
  panchangContent: {
    flex: 1,
  },
  skyContainer: {
    height: 60,
    borderRadius: 12,
    overflow: 'hidden',
    marginBottom: 16,
  },
  skyGradient: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  sunIcon: {
    fontSize: 24,
  },
  timeSlider: {
    marginBottom: 16,
  },
  timeTrack: {
    height: 6,
    backgroundColor: 'rgba(255,255,255,0.2)',
    borderRadius: 3,
    position: 'relative',
    marginBottom: 8,
  },
  auspiciousBlock: {
    position: 'absolute',
    height: '100%',
    backgroundColor: '#10B981',
    borderRadius: 3,
  },
  currentTimeIndicator: {
    position: 'absolute',
    width: 12,
    height: 12,
    borderRadius: 6,
    backgroundColor: '#FF6B35',
    top: -3,
  },
  timeLabels: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  timeLabel: {
    fontSize: 10,
    color: 'rgba(255,255,255,0.6)',
  },
  panchangInfo: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  panchangDetail: {
    fontSize: 11,
    color: 'rgba(255,255,255,0.9)',
  },
  panchangTithi: {
    fontSize: 11,
    color: COLORS.white,
    fontWeight: '600',
  },
});