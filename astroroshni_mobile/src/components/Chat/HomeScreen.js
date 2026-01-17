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
import Svg, { Circle, Text as SvgText, G, Defs, RadialGradient, Stop, Path, Line, Rect, Polygon } from 'react-native-svg';
import { COLORS } from '../../utils/constants';
import { useTheme } from '../../context/ThemeContext';
import { chartAPI, panchangAPI, pricingAPI } from '../../services/api';
import { BiometricTeaserCard } from '../BiometricTeaserCard';
import { PhysicalTraitsModal } from '../PhysicalTraitsModal';
import NativeSelectorChip from '../Common/NativeSelectorChip';

const { width } = Dimensions.get('window');

export default function HomeScreen({ birthData, onOptionSelect, navigation, setShowDashaBrowser }) {
  const { theme, colors } = useTheme();
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
  const [scanLoading, setScanLoading] = useState(false);
  const [physicalTraits, setPhysicalTraits] = useState(null);
  const [currentNativeData, setCurrentNativeData] = useState(null);
  const [showTraitsModal, setShowTraitsModal] = useState(false);
  const [hasFeedback, setHasFeedback] = useState(false);
  
  useFocusEffect(
    React.useCallback(() => {
      const loadData = async () => {
        const nativeData = await loadCurrentNative();
        await loadHomeData(nativeData);
      };
      loadData();
    }, [])
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
    
    // Removed duplicate loadHomeData call - handled by useFocusEffect
    
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
  }, []);
  
const loadCurrentNative = async () => {
    try {
      const { storage } = require('../../services/storage');
      
      // First try to get single birth details
      let selectedNative = await storage.getBirthDetails();
      
      // If no single birth details, get from profiles
      if (!selectedNative) {
        const profiles = await storage.getBirthProfiles();
        
        if (profiles && profiles.length > 0) {
          // Use the first profile or find 'self' relation
          selectedNative = profiles.find(p => p.relation === 'self') || profiles[0];
        }
      }
      
      setCurrentNativeData(selectedNative);
      return selectedNative;
    } catch (error) {
      return null;
    }
  };

const loadHomeData = async (nativeData = null) => {
    try {
      setLoading(true);
      
      // Clear existing chart data first
      setChartData(null);
      setDashData(null);
      
      // Load pricing first
      try {
        const pricingResponse = await pricingAPI.getAnalysisPricing();
        if (pricingResponse?.data) {
          setPricing(pricingResponse.data);
        }
      } catch (pricingError) {
      }
      
      const targetDate = new Date().toISOString().split('T')[0];
      
      // Use provided native data or get fresh from storage
      let currentBirthData = nativeData;
      if (!currentBirthData) {
        const { storage } = require('../../services/storage');
        
        // First try single birth details
        currentBirthData = await storage.getBirthDetails();
        
        // If no single birth details, get from profiles
        if (!currentBirthData) {
          const profiles = await storage.getBirthProfiles();
          if (profiles && profiles.length > 0) {
            currentBirthData = profiles.find(p => p.relation === 'self') || profiles[0];
          }
        }
      }
      
      // Fallback to props if no native data
      if (!currentBirthData) {
        currentBirthData = birthData;
      }
      
      // Load transits with birth data
      if (currentBirthData) {
        try {
          const formattedBirthData = {
            name: currentBirthData.name,
            date: currentBirthData.date.includes('T') ? currentBirthData.date.split('T')[0] : currentBirthData.date,
            time: currentBirthData.time.includes('T') ? new Date(currentBirthData.time).toTimeString().slice(0, 5) : currentBirthData.time,
            latitude: parseFloat(currentBirthData.latitude),
            longitude: parseFloat(currentBirthData.longitude),
            location: currentBirthData.place || 'Unknown'
          };
          const transitResponse = await chartAPI.calculateTransits(formattedBirthData, targetDate);
          if (transitResponse?.data) {
            setTransitData(transitResponse.data);
          }
        } catch (transitError) {
        }
      }
      
      // Load panchang for user's location or fallback to Delhi
      try {
        let panchangLat = 28.6139; // Delhi fallback
        let panchangLon = 77.2090; // Delhi fallback
        
        // Use current birth data location if available
        if (currentBirthData && currentBirthData.latitude && currentBirthData.longitude) {
          panchangLat = parseFloat(currentBirthData.latitude);
          panchangLon = parseFloat(currentBirthData.longitude);
        }
        
        const [panchangResponse, rahuKaalResponse, inauspiciousResponse, dailyPanchangResponse] = await Promise.allSettled([
          panchangAPI.calculateSunriseSunset(targetDate, panchangLat, panchangLon),
          panchangAPI.calculateRahuKaal(targetDate, panchangLat, panchangLon),
          panchangAPI.calculateInauspiciousTimes(targetDate, panchangLat, panchangLon),
          panchangAPI.calculateDailyPanchang(targetDate, panchangLat, panchangLon)
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
      
      
      if (currentBirthData) {
        
        const formattedBirthData = {
          name: currentBirthData.name,
          date: currentBirthData.date.includes('T') ? currentBirthData.date.split('T')[0] : currentBirthData.date,
          time: currentBirthData.time.includes('T') ? new Date(currentBirthData.time).toTimeString().slice(0, 5) : currentBirthData.time,
          latitude: parseFloat(currentBirthData.latitude),
          longitude: parseFloat(currentBirthData.longitude),
          location: currentBirthData.place || 'Unknown'
        };
        
        // console.log('🏠 HomeScreen - Sending birth data to backend:', JSON.stringify(formattedBirthData, null, 2));
        
        const [dashResponse, chartResponse] = await Promise.allSettled([
          chartAPI.calculateCascadingDashas(formattedBirthData, targetDate),
          chartAPI.calculateChartOnly(formattedBirthData)
        ]);
        
        if (dashResponse.status === 'fulfilled' && dashResponse.value?.data && !dashResponse.value.data.error) {
          setDashData(dashResponse.value.data);
        }
        
        if (chartResponse.status === 'fulfilled' && chartResponse.value?.data) {
          // console.log('🏠 HomeScreen - Received chart data from backend:', JSON.stringify(chartResponse.value.data, null, 2));
          // console.log('🏠 HomeScreen - Ascendant sign from chart:', chartResponse.value.data?.houses?.[0]?.sign);
          setChartData(chartResponse.value.data);
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
  
  // Use current native data for display
  const displayData = currentNativeData || birthData;
  
  // Don't render if no birth data available
  if (!displayData) {
    return null;
  }
  
  const place = displayData?.place || `${displayData?.latitude}, ${displayData?.longitude}`;
  const time = displayData?.time || 'Unknown time';

  const handlePhysicalScan = async () => {
    
    // Use current native data for scan
    const scanBirthData = currentNativeData || birthData;
    if (!scanBirthData) {
      Alert.alert('Error', 'Birth data not available for physical scan.');
      return;
    }

    setScanLoading(true);
    try {
      const scanData = {
        name: scanBirthData.name,
        date: scanBirthData.date,
        time: scanBirthData.time,
        latitude: scanBirthData.latitude,
        longitude: scanBirthData.longitude,
        place: scanBirthData.place || ''
      };
      
      const result = await chartAPI.scanPhysicalTraits(scanData, scanBirthData.id);
      
      if (result.data?.success && result.data?.traits?.length > 0) {
        setPhysicalTraits(result.data.traits);
        setHasFeedback(result.data.has_feedback || false);
        setShowTraitsModal(true);
      } else {
        Alert.alert('Physical Scan', 'No distinctive physical traits found in your chart.');
      }
    } catch (error) {
      Alert.alert('Error', `Failed to perform physical scan: ${error.response?.data?.detail || error.message}`);
    } finally {
      setScanLoading(false);
    }
  };

  const handleTraitsFeedback = async (feedbackType) => {
    // Store feedback in database
    try {
      const scanBirthData = currentNativeData || birthData;
      if (scanBirthData && chartData) {
        const feedbackData = {
          chart_data: chartData,
          birth_data: {
            name: scanBirthData.name,
            date: scanBirthData.date,
            time: scanBirthData.time,
            latitude: scanBirthData.latitude,
            longitude: scanBirthData.longitude,
            place: scanBirthData.place || '',
            gender: scanBirthData.gender || ''
          },
          feedback: feedbackType,
          birth_chart_id: scanBirthData.id
        };
        
        await chartAPI.submitPhysicalFeedback(feedbackData);
        setHasFeedback(true); // Update state to hide buttons
      }
    } catch (error) {
    }
    
    setShowTraitsModal(false);
    
    if (feedbackType === 'accurate') {
      setTimeout(() => {
        Alert.alert('Amazing!', 'Vedic astrology reveals so much about us! ✨');
      }, 300);
    } else {
      setTimeout(() => {
        Alert.alert('Feedback', 'Thank you for the feedback. We will improve our accuracy.');
      }, 300);
    }
  };

  const options = [
    {
      id: 'question',
      icon: '💬',
      title: 'Ask Any Question',
      description: 'Get insights about your personality, relationships, career, or any astrological topic',
      action: 'question'
    },
    {
      id: 'mundane',
      icon: '🌍',
      title: 'Global Markets & Events',
      description: 'Analyze world events, stock markets, politics, and economic trends',
      action: 'mundane'
    },
    {
      id: 'periods',
      icon: '🎯',
      title: 'Find Event Periods',
      description: 'Discover high-probability periods when specific events might happen',
      action: 'periods'
    },
    {
      id: 'events',
      icon: '🌟',
      title: 'Event Timeline',
      description: 'AI-powered yearly predictions with monthly breakdowns and major milestones',
      action: 'events'
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
      id: 'financial', 
      title: 'Market Astrology', 
      icon: '💹', 
      description: 'Sector forecasts & investment timing',
      gradient: ['#10b981', '#059669'],
      cost: 0
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
        colors={theme === 'dark' ? [colors.gradientStart, colors.gradientMid, colors.gradientEnd, colors.primary] : [colors.gradientStart, colors.gradientStart, colors.gradientStart, colors.gradientStart]}
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
              <Text style={[styles.starText, { color: theme === 'dark' ? '#FFD700' : '#c2410c' }]}>✦</Text>
            </Animated.View>
          );
        })}
        
        {/* Header with Native Selector */}
        <View style={styles.header}>
        </View>
        
      <ScrollView style={[styles.scrollView, { zIndex: 1 }]} contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <Animated.View style={[styles.greetingContainer, { opacity: fadeAnim, transform: [{ translateY: slideAnim }, { scale: scaleAnim }] }]}>
          <View style={styles.avatarContainer}>
            <Animated.View style={[styles.zodiacRing, { transform: [{ rotate: pulseAnim.interpolate({ inputRange: [1, 1.05], outputRange: ['0deg', '360deg'] }) }] }]}>
              <LinearGradient
                colors={[colors.primary, colors.accent, colors.primary]}
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
                })() : '⏳'}
              </Text>
            </Animated.View>
          </View>
          
          <Text style={[styles.greetingTitle, { color: colors.text }]}>
            Welcome, {displayData?.name}!
          </Text>
          <View style={[
            styles.birthInfoCard,
            {
              backgroundColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.1)' : 'rgba(249, 115, 22, 0.1)',
              borderColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.2)' : 'rgba(249, 115, 22, 0.2)'
            }
          ]}>
            <Text style={[styles.birthInfoText, { color: colors.textSecondary }]}>
              📅 {displayData?.date ? new Date(displayData.date).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' }) : 'Unknown date'}
            </Text>
            <Text style={[styles.birthInfoText, { color: colors.textSecondary }]}>
              🕐 {time}
            </Text>
            <Text style={[styles.birthInfoText, { color: colors.textSecondary }]}>
              📍 {place}
            </Text>
          </View>
          <Text style={[styles.greetingSubtext, { color: colors.textSecondary }]}>
            Your cosmic blueprint awaits. Choose your path to enlightenment.
          </Text>
        </Animated.View>

        {/* Biometric Teaser Card - COMMENTED OUT */}
        {/* <BiometricTeaserCard 
          onPressReveal={() => {
            console.log('🔄 BiometricTeaserCard pressed');
            handlePhysicalScan();
          }}
          isLoading={scanLoading}
        /> */}

        <Animated.View style={[styles.optionsContainer, { opacity: fadeAnim }]}>
          <Text style={[styles.optionsTitle, { color: colors.text }]}>Choose Your Path</Text>
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
          <Text style={[styles.analysisTitle, { color: colors.text }]}>🧘 Life Analysis</Text>
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
          <Text style={[styles.analysisTitle, { color: colors.text }]}>⏰ Timing Planners</Text>
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
          <Text style={[styles.dashboardTitle, { color: colors.text }]}>✨ Your Cosmic Dashboard</Text>
          


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
              <Text style={[styles.dashaSectionTitle, { color: colors.text }]}>⏰ Current Dasha Periods</Text>
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
                      <Text style={[styles.dashaChipDates, { color: colors.textSecondary }]}>{startDate}</Text>
                      <Text style={[styles.dashaChipDates, { color: colors.textSecondary }]}>{endDate}</Text>
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

          {/* Astrology Tools Section */}
          <View style={styles.toolsSection}>
            <Text style={[styles.toolsSectionTitle, { color: colors.text }]}>🔧 Astrology Tools</Text>
            <View style={styles.toolsGrid}>
              <TouchableOpacity 
                style={styles.toolCard}
                onPress={() => navigation.navigate('Chart', { birthData })}
                activeOpacity={0.8}
              >
                <View style={[
                  styles.toolGlassmorphism,
                  {
                    backgroundColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.1)' : 'rgba(249, 115, 22, 0.1)',
                    borderColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.2)' : 'rgba(249, 115, 22, 0.2)'
                  }
                ]}>
                  <Svg width="28" height="28" viewBox="0 0 48 48" style={{ marginBottom: 8 }}>
                    <Rect x="2" y="2" width="44" height="44" fill="none" stroke="#ffffff" strokeWidth="2" />
                    <Polygon points="24,2 46,24 24,46 2,24" fill="none" stroke="#ffd700" strokeWidth="1.5" />
                    <Line x1="2" y1="2" x2="46" y2="46" stroke="#ff8a65" strokeWidth="1" />
                    <Line x1="46" y1="2" x2="2" y2="46" stroke="#ff8a65" strokeWidth="1" />
                  </Svg>
                  <Text style={[styles.toolTitle, { color: colors.text }]}>Charts</Text>
                </View>
              </TouchableOpacity>
              
              <TouchableOpacity 
                style={styles.toolCard}
                onPress={() => setShowDashaBrowser(true)}
                activeOpacity={0.8}
              >
                <View style={[
                  styles.toolGlassmorphism,
                  {
                    backgroundColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.1)' : 'rgba(249, 115, 22, 0.1)',
                    borderColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.2)' : 'rgba(249, 115, 22, 0.2)'
                  }
                ]}>
                  <Text style={styles.toolEmoji}>⏰</Text>
                  <Text style={[styles.toolTitle, { color: colors.text }]}>Dashas</Text>
                </View>
              </TouchableOpacity>
              
              <TouchableOpacity 
                style={styles.toolCard}
                onPress={() => navigation.navigate('AshtakvargaOracle')}
                activeOpacity={0.8}
              >
                <View style={[
                  styles.toolGlassmorphism,
                  {
                    backgroundColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.1)' : 'rgba(249, 115, 22, 0.1)',
                    borderColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.2)' : 'rgba(249, 115, 22, 0.2)'
                  }
                ]}>
                  <Text style={styles.toolEmoji}>⊞</Text>
                  <Text style={[styles.toolTitle, { color: colors.text }]}>Ashtak-{"\n"}varga</Text>
                </View>
              </TouchableOpacity>
              
              <TouchableOpacity 
                style={styles.toolCard}
                onPress={() => chartData && navigation.navigate('PlanetaryPositions', { chartData })}
                activeOpacity={0.8}
              >
                <View style={[
                  styles.toolGlassmorphism,
                  {
                    backgroundColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.1)' : 'rgba(249, 115, 22, 0.1)',
                    borderColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.2)' : 'rgba(249, 115, 22, 0.2)'
                  }
                ]}>
                  <Text style={styles.toolEmoji}>🌌</Text>
                  <Text style={[styles.toolTitle, { color: colors.text }]}>Positions</Text>
                </View>
              </TouchableOpacity>
            </View>
          </View>

          {/* Zodiac Wheel - Vibrant Design */}
          <View style={styles.planetarySection}>
            <Text style={[styles.planetarySectionTitle, { color: colors.text }]}>🪐 Current Planetary Transits</Text>
            {!transitData ? (
              <Text style={styles.loadingText}>Loading transits...</Text>
            ) : !transitData.planets ? (
              <Text style={styles.loadingText}>No transit data available</Text>
            ) : (
              <View style={styles.planetGrid}>
                {Object.entries(transitData.planets).map(([planet, data]) => (
                  <View key={planet} style={[
                    styles.planetCard,
                    { backgroundColor: getSignColor(data.sign) + '20', borderColor: getSignColor(data.sign) }
                  ]}>
                    <Text style={[styles.planetName, { color: colors.text }]}>{planet}</Text>
                    <Text style={[styles.planetSign, { color: colors.textSecondary }]}>{getSignIcon(data.sign)} {getSignName(data.sign)}</Text>
                    <Text style={[styles.planetDegree, { color: colors.textSecondary }]}>{data.degree.toFixed(1)}°</Text>
                  </View>
                ))}
              </View>
            )}
          </View>

          {/* Panchang Timeline */}
          {panchangData && (
            <View style={[
              styles.panchangCard,
              {
                backgroundColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.1)' : 'rgba(249, 115, 22, 0.1)',
                borderColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.2)' : 'rgba(249, 115, 22, 0.2)'
              }
            ]}>
              <Text style={[styles.panchangTitle, { textAlign: 'center', marginBottom: 20, color: colors.text }]}>🌅 Today's Panchang</Text>
              <View style={styles.sunTimesRow}>
                <View style={styles.sunTimeItem}>
                  <Text style={styles.sunTimeEmoji}>🌅</Text>
                  <Text style={[styles.sunTimeLabel, { color: colors.textSecondary }]}>Sunrise</Text>
                  <Text style={[styles.sunTimeValue, { color: colors.text }]}>{panchangData.sunrise ? new Date(panchangData.sunrise).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true }) : '6:30 AM'}</Text>
                </View>
                <View style={styles.sunTimeItem}>
                  <Text style={styles.sunTimeEmoji}>🌇</Text>
                  <Text style={[styles.sunTimeLabel, { color: colors.textSecondary }]}>Sunset</Text>
                  <Text style={[styles.sunTimeValue, { color: colors.text }]}>{panchangData.sunset ? new Date(panchangData.sunset).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true }) : '6:45 PM'}</Text>
                </View>
              </View>
              
              <View style={styles.sunTimesRow}>
                <View style={styles.sunTimeItem}>
                  <Text style={styles.sunTimeEmoji}>🌙</Text>
                  <Text style={[styles.sunTimeLabel, { color: colors.textSecondary }]}>Moonrise</Text>
                  <Text style={[styles.sunTimeValue, { color: colors.text }]}>{panchangData.daily_panchang?.sunrise_sunset?.moonrise || panchangData.sunrise_sunset?.moonrise || '7:53 AM'}</Text>
                </View>
                <View style={styles.sunTimeItem}>
                  <Text style={styles.sunTimeEmoji}>🌚</Text>
                  <Text style={[styles.sunTimeLabel, { color: colors.textSecondary }]}>Moonset</Text>
                  <Text style={[styles.sunTimeValue, { color: colors.text }]}>{panchangData.daily_panchang?.sunrise_sunset?.moonset || panchangData.sunrise_sunset?.moonset || '6:06 PM'}</Text>
                </View>
              </View>
              
              {/* Panchang Elements Section */}
              {panchangData.daily_panchang && (
                <View style={styles.panchangElementsSection}>
                  <Text style={[styles.panchangElementsTitle, { color: colors.primary }]}>🕉️ Panchang Elements</Text>
                  
                  {/* Nakshatra */}
                  {panchangData.daily_panchang.nakshatra && (
                    <View style={styles.panchangElement}>
                      <Text style={[styles.elementLabel, { color: colors.textSecondary }]}>⭐ Nakshatra:</Text>
                      <Text style={[styles.elementValue, { color: colors.textPrimary }]}>{panchangData.daily_panchang.nakshatra.name}</Text>
                    </View>
                  )}
                  
                  {/* Tithi */}
                  {panchangData.daily_panchang.tithi && (
                    <View style={styles.panchangElement}>
                      <Text style={[styles.elementLabel, { color: colors.textSecondary }]}>🌙 Tithi:</Text>
                      <Text style={[styles.elementValue, { color: colors.textPrimary }]}>{panchangData.daily_panchang.tithi.name}</Text>
                    </View>
                  )}
                  
                  {/* Yoga */}
                  {panchangData.daily_panchang.yoga && (
                    <View style={styles.panchangElement}>
                      <Text style={[styles.elementLabel, { color: colors.textSecondary }]}>🧘 Yoga:</Text>
                      <Text style={[styles.elementValue, { color: colors.textPrimary }]}>{panchangData.daily_panchang.yoga.name}</Text>
                    </View>
                  )}
                  
                  {/* Karana */}
                  {panchangData.daily_panchang.karana && (
                    <View style={styles.panchangElement}>
                      <Text style={[styles.elementLabel, { color: colors.textSecondary }]}>⚡ Karana:</Text>
                      <Text style={[styles.elementValue, { color: colors.textPrimary }]}>{panchangData.daily_panchang.karana.name}</Text>
                    </View>
                  )}
                </View>
              )}
              

              
              {/* Row 1: Moon Phase Text and Illumination */}
              <View style={styles.moonPhaseTextRow}>
                <Text style={[styles.moonPhaseText, { color: colors.text }]}>{panchangData.moon_phase || 'Full Moon'}</Text>
                <Text style={[styles.moonIllumination, { color: colors.textSecondary }]}>{panchangData.moon_illumination ? `${panchangData.moon_illumination.toFixed(1)}%` : '98.5%'}</Text>
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
                <Text style={[styles.progressLabel, { color: colors.textTertiary }]}>Day Progress</Text>
              </View>
              
              <View style={styles.muhurtaSection}>
                <Text style={styles.muhurtaTitle}>🕉️ Auspicious Times</Text>
                <View style={styles.muhurtaRow}>
                  <Text style={[styles.muhurtaLabel, { color: colors.textSecondary }]}>Brahma Muhurta:</Text>
                  <Text style={styles.muhurtaTime}>
                    {panchangData.brahma_muhurta_start && panchangData.brahma_muhurta_end ? 
                      `${new Date(panchangData.brahma_muhurta_start).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true })} - ${new Date(panchangData.brahma_muhurta_end).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true })}` : 
                      '4:29 AM - 6:05 AM'
                    }
                  </Text>
                </View>
                <View style={styles.muhurtaRow}>
                  <Text style={[styles.muhurtaLabel, { color: colors.textSecondary }]}>Abhijit Muhurta:</Text>
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
                      <Text style={[styles.muhurtaLabel, { color: colors.textSecondary }]}>Rahu Kaal:</Text>
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
                      <Text style={[styles.muhurtaLabel, { color: colors.textSecondary }]}>Dur Muhurta:</Text>
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
                      <Text style={[styles.muhurtaLabel, { color: colors.textSecondary }]}>Varjyam:</Text>
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
      
      {/* Physical Traits Modal */}
      <PhysicalTraitsModal
        visible={showTraitsModal}
        traits={physicalTraits || []}
        onClose={() => setShowTraitsModal(false)}
        onFeedback={handleTraitsFeedback}
        hasFeedback={hasFeedback}
      />
      
      </LinearGradient>
    </View>
  );
}

// Separate component to avoid hooks order violation
function OptionCard({ option, index, onOptionSelect }) {
  const { theme, colors } = useTheme();
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
  
  // Special gradients for different options
  const gradientColors = option.id === 'events' 
    ? ['#FFD700', '#FF8C00'] 
    : option.id === 'ashtakvarga'
    ? ['#9C27B0', '#E91E63']
    : ['#ff6b35', '#ff8c5a'];
  
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
          colors={theme === 'dark' 
            ? ['rgba(255, 255, 255, 0.15)', 'rgba(255, 255, 255, 0.05)']
            : ['rgba(249, 115, 22, 0.15)', 'rgba(249, 115, 22, 0.05)']}
          style={styles.optionGradient}
        >
          <View style={styles.optionIconContainer}>
            <LinearGradient
              colors={gradientColors}
              style={styles.optionIconGradient}
            >
              <Text style={styles.optionEmoji}>{option.icon}</Text>
            </LinearGradient>
          </View>
          <View style={styles.optionContent}>
            <Text style={[styles.optionTitle, { color: colors.text }]}>{option.title}</Text>
            <Text style={[styles.optionDescription, { color: colors.textSecondary }]}>{option.description}</Text>
          </View>
          <Icon name="chevron-forward" size={24} color={colors.textTertiary} />
        </LinearGradient>
      </TouchableOpacity>
    </Animated.View>
  );
}

// Life Analysis Card - 3 per row
function LifeAnalysisCard({ option, index, onOptionSelect }) {
  const { colors } = useTheme();
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
  const { theme, colors } = useTheme();
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
        <View style={[
          styles.analysisGlassmorphism,
          {
            backgroundColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.1)' : 'rgba(249, 115, 22, 0.1)',
            borderColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.2)' : 'rgba(249, 115, 22, 0.2)'
          }
        ]}>
          <View style={styles.analysisIconContainer}>
            <Text style={styles.analysisEmoji}>{option.icon}</Text>
          </View>
          <View style={styles.analysisContent}>
            <Text style={[styles.analysisCardTitle, { color: colors.text }]}>{option.title}</Text>
            <Text style={[styles.analysisDescription, { color: colors.textSecondary }]}>{option.description}</Text>
          </View>
          <Icon name="chevron-forward" size={24} color={colors.textTertiary} />
        </View>
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
    textAlign: 'center',
    marginVertical: 2,
  },
  greetingSubtext: {
    fontSize: 16,
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
    marginBottom: 6,
  },
  optionDescription: {
    fontSize: 14,
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
    textAlign: 'center',
    marginBottom: 8,
  },
  quickQuestionsSubtext: {
    fontSize: 14,
    textAlign: 'center',
    lineHeight: 20,
  },
  analysisContainer: {
    marginBottom: 30,
  },
  analysisTitle: {
    fontSize: 24,
    fontWeight: '700',
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
  },
  analysisGlassmorphism: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 20,
    borderRadius: 20,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
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
    marginBottom: 6,
  },
  analysisDescription: {
    fontSize: 14,
    lineHeight: 20,
    marginBottom: 6,
  },
  analysisCost: {
    fontSize: 12,
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
    minHeight: width * 0.32,
  },
  lifeAnalysisEmoji: {
    fontSize: 18,
    marginBottom: 6,
  },
  lifeAnalysisTitle: {
    fontSize: 10,
    fontWeight: '700',
    marginBottom: 6,
    textAlign: 'center',
    lineHeight: 12,
    color: '#ffffff',
  },
  lifeAnalysisDescription: {
    fontSize: 8,
    textAlign: 'center',
    lineHeight: 10,
    paddingHorizontal: 2,
    color: 'rgba(255, 255, 255, 0.9)',
  },
  lifeAnalysisCost: {
    fontSize: 10,
    fontWeight: '600',
  },
  // Dashboard Cards Styles
  dashboardContainer: {
    marginBottom: 30,
  },
  dashboardTitle: {
    fontSize: 24,
    fontWeight: '700',
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
  
  // Astrology Tools Section
  toolsSection: {
    marginBottom: 24,
  },
  toolsSectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 12,
    paddingHorizontal: 4,
    textAlign: 'center',
  },
  toolsGrid: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 8,
  },
  toolCard: {
    flex: 1,
    borderRadius: 16,
    overflow: 'hidden',
    minWidth: 0,
  },
  toolGlassmorphism: {
    padding: 16,
    alignItems: 'center',
    minHeight: 100,
    maxHeight: 100,
    justifyContent: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.2)',
  },
  toolEmoji: {
    fontSize: 28,
    marginBottom: 8,
  },
  toolTitle: {
    fontSize: 11,
    fontWeight: '700',
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
    marginBottom: 4,
  },
  planetSign: {
    fontSize: 11,
    marginBottom: 2,
  },
  planetDegree: {
    fontSize: 10,
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
    borderRadius: 16,
    padding: 20,
    borderWidth: 1,
  },
  panchangTitle: {
    fontSize: 18,
    fontWeight: '600',
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
    marginBottom: 4,
  },
  sunTimeValue: {
    fontSize: 14,
    fontWeight: '600',
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
    fontWeight: '500',
  },
  elementValue: {
    fontSize: 13,
    fontWeight: '600',
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
    marginBottom: 4,
  },
  moonIllumination: {
    fontSize: 12,
  },
  
  // Header Styles
  header: {
    position: 'absolute',
    top: 50,
    left: 20,
    right: 20,
    zIndex: 10,
    alignItems: 'flex-end',
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