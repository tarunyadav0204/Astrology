import React, { useCallback, useEffect, useRef, useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  Dimensions,
  Alert,
  FlatList,
  AppState,
  Platform,
  Modal,
  Animated,
} from 'react-native';
import { BlurView } from 'expo-blur';
import { useFocusEffect } from '@react-navigation/native';
import { LinearGradient } from 'expo-linear-gradient';
const AnimatedLinearGradient = Animated.createAnimatedComponent(LinearGradient);
import Icon from '@expo/vector-icons/Ionicons';
import Svg, { Circle, Text as SvgText, Path, Line, Rect, Polygon } from 'react-native-svg';
import { COLORS } from '../../utils/constants';
import { useTheme } from '../../context/ThemeContext';
import { chartAPI, panchangAPI, pricingAPI } from '../../services/api';
import { BiometricTeaserCard } from '../BiometricTeaserCard';
import { PhysicalTraitsModal } from '../PhysicalTraitsModal';
import NativeSelectorChip from '../Common/NativeSelectorChip';
import { useAnalytics } from '../../hooks/useAnalytics';
import { useTranslation } from 'react-i18next';

const { width, height: windowHeight } = Dimensions.get('window');
const MONTH_NAMES = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
const ordinalSuffix = (n) => {
  if (n >= 11 && n <= 13) return 'th';
  switch (n % 10) { case 1: return 'st'; case 2: return 'nd'; case 3: return 'rd'; default: return 'th'; }
};
/** Format ISO date "YYYY-MM-DD" as "2nd April 1980" */
const formatDateOrdinal = (isoDate) => {
  if (!isoDate || typeof isoDate !== 'string') return isoDate || '';
  const [y, m, d] = isoDate.split('T')[0].split('-').map(Number);
  if (!y || !m || !d) return isoDate;
  const dayStr = d + ordinalSuffix(d);
  const month = MONTH_NAMES[m - 1] || m;
  return `${dayStr} ${month} ${y}`;
};

// Scale animation for cards on scroll
const getCardScale = (index) => 1;

/** Sign keys for ascendant description i18n (home.ascendantDescriptions.Aries etc.). */
const ASCENDANT_SIGN_KEYS = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'];

export default function HomeScreen({ birthData, onOptionSelect, navigation, setShowDashaBrowser }) {
  const { t, i18n } = useTranslation();
  console.log('🌐 HomeScreen current language:', i18n.language);
  useAnalytics('HomeScreen');
  const { theme, colors, androidLightCardFixStyle } = useTheme();
  
  if (!colors) {
    return null;
  }
  const [dashData, setDashData] = useState(null);
  const [chartData, setChartData] = useState(null);
  const [activeTab, setActiveTab] = useState('ask');
  const [transitData, setTransitData] = useState(null);
  const [panchangData, setPanchangData] = useState(null);
  const [pricing, setPricing] = useState({});
  const [loading, setLoading] = useState(true);
  const [scanLoading, setScanLoading] = useState(false);
  const [physicalTraits, setPhysicalTraits] = useState([]);

  const [currentNativeData, setCurrentNativeData] = useState(null);
  const [showTraitsModal, setShowTraitsModal] = useState(false);
  const [hasFeedback, setHasFeedback] = useState(false);
  const [activeInsight, setActiveInsight] = useState(null);
  const [tickerData, setTickerData] = useState({
    sadeSati: null,
    mahadasha: null,
    nakshatra: null,
    loading: true
  });
  const [isFABCollapsed, setIsFABCollapsed] = useState(false);
  const lastScrollY = useRef(0);
  const fabWidth = useRef(new Animated.Value(1)).current; // 1 for full, 0 for collapsed

  const handleScroll = (event) => {
    const currentScrollY = event.nativeEvent.contentOffset.y;
    
    // Determine scroll direction
    const isScrollingDown = currentScrollY > lastScrollY.current;
    const scrollThreshold = 20;

    if (currentScrollY <= scrollThreshold) {
      // Always expand at the top
      if (isFABCollapsed) {
        setIsFABCollapsed(false);
        Animated.timing(fabWidth, {
          toValue: 1,
          duration: 200,
          useNativeDriver: false,
        }).start();
      }
    } else {
      // Toggle based on direction when not at the top
      if (isScrollingDown && !isFABCollapsed) {
        setIsFABCollapsed(true);
        Animated.timing(fabWidth, {
          toValue: 0,
          duration: 200,
          useNativeDriver: false,
        }).start();
      } else if (!isScrollingDown && isFABCollapsed) {
        setIsFABCollapsed(false);
        Animated.timing(fabWidth, {
          toValue: 1,
          duration: 200,
          useNativeDriver: false,
        }).start();
      }
    }
    
    lastScrollY.current = currentScrollY;
  };



  const getSignInsight = (type, signIndex) => {
    if (signIndex === undefined || signIndex === null) return null;
    const signName = getSignName(signIndex);
    const signKey = ASCENDANT_SIGN_KEYS[signIndex];
    const ascendantDescription = signKey ? t(`home.ascendantDescriptions.${signKey}`) : null;
    const moonDescription = signKey ? t(`home.moonDescriptions.${signKey}`) : null;
    const sunDescription = signKey ? t(`home.sunDescriptions.${signKey}`) : null;
    const insights = {
      ascendant: {
        title: `${signName} Ascendant`,
        description: ascendantDescription || `Your ${signName} Ascendant (Lagna) represents your physical self, personality, and how the world perceives you.`,
        icon: '⬆️'
      },
      moon: {
        title: `${signName} Moon`,
        description: moonDescription || `Your Moon in ${signName} governs your emotions, subconscious mind, and inner well-being. It reveals how you nurture yourself and respond to the world emotionally.`,
        icon: '🌙'
      },
      sun: {
        title: `${signName} Sun`,
        description: sunDescription || `Your Sun in ${signName} represents your core ego, soul's purpose, and vitality. It is the source of your creative power and self-expression.`,
        icon: '☀️'
      }
    };
    return insights[type];
  };
  
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
    // Update Panchang daily at midnight
    const now = new Date();
    const tomorrow = new Date(now);
    tomorrow.setDate(tomorrow.getDate() + 1);
    tomorrow.setHours(0, 0, 0, 0);
    const msUntilMidnight = tomorrow.getTime() - now.getTime();
    
    let dailyInterval;
    const midnightTimer = setTimeout(() => {
      loadHomeData();
      // Set up daily interval after first midnight update
      dailyInterval = setInterval(loadHomeData, 24 * 60 * 60 * 1000);
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
      if (dailyInterval) clearInterval(dailyInterval);
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
            name: currentBirthData.name || 'Unknown',
            date: (currentBirthData.date && typeof currentBirthData.date === 'string' && currentBirthData.date.includes('T')) ? currentBirthData.date.split('T')[0] : (currentBirthData.date || ''),
            time: (currentBirthData.time && typeof currentBirthData.time === 'string' && currentBirthData.time.includes('T')) ? new Date(currentBirthData.time).toTimeString().slice(0, 5) : (currentBirthData.time || ''),
            latitude: parseFloat(currentBirthData.latitude) || 0,
            longitude: parseFloat(currentBirthData.longitude) || 0,
            location: currentBirthData.place || 'Unknown'
          };
          
          // Fetch Ticker Data (Dasha & Sade Sati)
          Promise.allSettled([
            chartAPI.calculateCascadingDashas(formattedBirthData, targetDate),
            // Sade Sati is usually part of a larger analysis, but we can check transit Saturn vs Moon
            chartAPI.calculateTransits(formattedBirthData, targetDate)
          ]).then(([dashaRes, transitRes]) => {
            let tickerUpdate = { loading: false };
            
            if (dashaRes && dashaRes.status === 'fulfilled' && dashaRes.value?.data) {
              const currentMaha = dashaRes.value.data.maha_dashas?.find(d => d.current);
              if (currentMaha) {
                tickerUpdate.mahadasha = currentMaha.planet;
              }
            }
            
            if (transitRes && transitRes.status === 'fulfilled' && transitRes.value?.data) {
              const transits = transitRes.value.data.transits;
              const birthMoonSign = transitRes.value.data.birth_chart?.planets?.Moon?.sign;
              const transitSaturnSign = transits?.Saturn?.sign;
              
              if (birthMoonSign !== undefined && transitSaturnSign !== undefined) {
                // Simple Sade Sati logic: Saturn in 12th, 1st, or 2nd from Moon
                const diff = (transitSaturnSign - birthMoonSign + 12) % 12;
                if (diff === 11 || diff === 0 || diff === 1) {
                  tickerUpdate.sadeSati = true;
                } else {
                  tickerUpdate.sadeSati = false;
                }
              }
            }
            
            setTickerData(prev => ({ ...prev, ...tickerUpdate }));
          }).catch(err => {
            setTickerData(prev => ({ ...prev, loading: false }));
          });

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
        
        if (panchangResponse && panchangResponse.status === 'fulfilled' && panchangResponse.value?.data) {
          let combinedPanchangData = panchangResponse.value.data;
          
          if (rahuKaalResponse && rahuKaalResponse.status === 'fulfilled' && rahuKaalResponse.value?.data) {
            combinedPanchangData.rahu_kaal = rahuKaalResponse.value.data;
          }
          
          if (inauspiciousResponse && inauspiciousResponse.status === 'fulfilled' && inauspiciousResponse.value?.data) {
            combinedPanchangData.inauspicious_times = inauspiciousResponse.value.data;
          }
          
          if (dailyPanchangResponse && dailyPanchangResponse.status === 'fulfilled' && dailyPanchangResponse.value?.data) {
            const basicPanchang = dailyPanchangResponse.value.data.basic_panchang;
            if (basicPanchang) {
              combinedPanchangData.daily_panchang = {
                ...dailyPanchangResponse.value.data,
                nakshatra: basicPanchang.nakshatra,
                tithi: basicPanchang.tithi,
                yoga: basicPanchang.yoga,
                karana: basicPanchang.karana
              };
              const nakshatraName = basicPanchang.nakshatra?.name || basicPanchang.nakshatra;
              if (nakshatraName) {
                setTickerData(prev => ({ ...prev, nakshatra: nakshatraName }));
              }
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
        
        if (dashResponse && dashResponse.status === 'fulfilled' && dashResponse.value?.data && !dashResponse.value.data.error) {
          setDashData(dashResponse.value.data);
        }
        
        if (chartResponse && chartResponse.status === 'fulfilled' && chartResponse.value?.data) {
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
    if (signNumber === undefined || signNumber === null) return t('common.unknown', 'Unknown');
    const signs = {
      0: 'Aries', 1: 'Taurus', 2: 'Gemini', 3: 'Cancer',
      4: 'Leo', 5: 'Virgo', 6: 'Libra', 7: 'Scorpio',
      8: 'Sagittarius', 9: 'Capricorn', 10: 'Aquarius', 11: 'Pisces'
    };
    const signName = signs[signNumber] || signNumber;
    return t(`signs.${signName}`, signName);
  };
  
  const getSignIcon = (signNumber) => {
    if (signNumber === undefined || signNumber === null) return '⭐';
    const icons = {
      0: '♈', 1: '♉', 2: '♊', 3: '♋',
      4: '♌', 5: '♍', 6: '♎', 7: '♏',
      8: '♐', 9: '♑', 10: '♒', 11: '♓'
    };
    return icons[signNumber] || '⭐';
  };
  
  const getSignColor = (signNumber) => {
    if (signNumber === undefined || signNumber === null) return '#ffffff';
    const colors = {
      0: '#FF5733', 1: '#4CAF50', 2: '#FFC300', 3: '#2196F3',
      4: '#FF8C00', 5: '#8BC34A', 6: '#00BCD4', 7: '#673AB7',
      8: '#E91E63', 9: '#009688', 10: '#3F51B5', 11: '#9C27B0'
    };
    return colors[signNumber] || '#ffffff';
  };

  const getPlanetVibe = (planet) => {
    if (!planet) return { tag: 'Energy', icon: '✨' };
    const vibes = {
      'Sun': { tag: 'Core', icon: '☀️' },
      'Moon': { tag: 'Mind', icon: '🌙' },
      'Mars': { tag: 'Action', icon: '⚔️' },
      'Mercury': { tag: 'Logic', icon: '🧠' },
      'Jupiter': { tag: 'Growth', icon: '⚖️' },
      'Venus': { tag: 'Love', icon: '💖' },
      'Saturn': { tag: 'Karma', icon: '⏳' },
      'Rahu': { tag: 'Desire', icon: '🌀' },
      'Ketu': { tag: 'Spirit', icon: '🧘' },
    };
    return vibes[planet] || { tag: 'Energy', icon: '✨' };
  };

  const getPlanetStatus = (planet, sign, isRetrograde) => {
    if (sign === undefined || sign === null) return [];
    const status = [];
    if (isRetrograde) status.push({ label: 'Rx', color: '#EF4444' });
    
    // Simple Exaltation/Debilitation logic (Vedic)
    const exaltation = { 'Sun': 0, 'Moon': 1, 'Mars': 9, 'Mercury': 5, 'Jupiter': 3, 'Venus': 11, 'Saturn': 6 };
    const debilitation = { 'Sun': 6, 'Moon': 7, 'Mars': 3, 'Mercury': 11, 'Jupiter': 9, 'Venus': 5, 'Saturn': 0 };
    
    if (exaltation[planet] === sign) status.push({ label: 'Exalted', color: '#10B981' });
    if (debilitation[planet] === sign) status.push({ label: 'Debilitated', color: '#F59E0B' });
    
    return status;
  };
  
  // Use current native data for display
  const displayData = currentNativeData || birthData;

  // Don't render if no birth data available
  if (!displayData || !colors) {
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
      title: t('home.options.question.title', 'Ask Any Question'),
      description: t('home.options.question.description', 'Get insights about your personality, relationships, career, or any astrological topic'),
      action: 'question'
    },
    {
      id: 'partnership',
      icon: '👥',
      title: t('home.options.partnership.title', 'Partnership Analysis'),
      description: t('home.options.partnership.description', 'Analyze compatibility and relationship dynamics between two people'),
      action: 'partnership'
    },
    {
      id: 'mundane',
      icon: '🌍',
      title: t('home.options.mundane.title', 'Global Markets & Events'),
      description: t('home.options.mundane.description', 'Analyze world events, stock markets, politics, and economic trends'),
      action: 'mundane'
    },
    // Commented out in favor of Event Timeline tile for now
    // {
    //   id: 'periods',
    //   icon: '🎯',
    //   title: 'Find Event Periods',
    //   description: 'Discover high-probability periods when specific events might happen',
    //   action: 'periods'
    // },
    {
      id: 'events',
      icon: '📅',
      title: t('home.options.events.title', 'Event Timeline'),
      description: t('home.options.events.description', 'AI-powered yearly predictions with monthly breakdowns and major milestones'),
      action: 'events'
    }
  ];

  const analysisOptions = [
    { 
      id: 'career', 
      title: t('home.analysis.career.title', 'Career Analysis'), 
      icon: '💼', 
      description: t('home.analysis.career.description', 'Professional success & opportunities'),
      gradient: ['#6366F1', '#8B5CF6'],
      cost: pricing.career_analysis || 10
    },
    { 
      id: 'wealth', 
      title: t('home.analysis.wealth.title', 'Wealth Analysis'), 
      icon: '💰', 
      description: t('home.analysis.wealth.description', 'Financial prospects & opportunities'),
      gradient: ['#0EA5E9', '#38BDF8'],
      cost: pricing.wealth_analysis || 5
    },
    { 
      id: 'marriage', 
      title: t('home.analysis.marriage.title', 'Marriage Analysis'), 
      icon: '💕', 
      description: t('home.analysis.marriage.description', 'Relationship compatibility & timing'),
      gradient: ['#FF69B4', '#DC143C'],
      cost: pricing.marriage_analysis || 5
    },
    { 
      id: 'health', 
      title: t('home.analysis.health.title', 'Health Analysis'), 
      icon: '🏥', 
      description: t('home.analysis.health.description', 'Wellness insights & precautions'),
      gradient: ['#32CD32', '#228B22'],
      cost: pricing.health_analysis || 5
    },
    { 
      id: 'education', 
      title: t('home.analysis.education.title', 'Education Analysis'), 
      icon: '🎓', 
      description: t('home.analysis.education.description', 'Learning path & career guidance'),
      gradient: ['#4169E1', '#1E90FF'],
      cost: pricing.education_analysis || 5
    },
    { 
      id: 'progeny', 
      title: t('home.analysis.progeny.title', 'Progeny Analysis'), 
      icon: '👨‍👩‍👧‍👦', 
      description: t('home.analysis.progeny.description', 'Fertility potential & family expansion'),
      gradient: ['#FF69B4', '#FF1493'],
      cost: pricing.progeny_analysis || 15
    },
    { 
      id: 'trading', 
      title: t('home.analysis.trading.title', 'Trading Forecast'), 
      icon: '📈', 
      description: t('home.analysis.trading.description', 'Stock market predictions & timing'),
      gradient: ['#FFD700', '#FF8C00'],
      cost: 5
    },
    { 
      id: 'financial', 
      title: t('home.analysis.financial.title', 'Market Astrology'), 
      icon: '💹', 
      description: t('home.analysis.financial.description', 'Sector forecasts & investment timing'),
      gradient: ['#10b981', '#059669'],
      cost: 0
    },
    { 
      id: 'childbirth', 
      title: t('home.analysis.childbirth.title', 'Childbirth Planner'), 
      icon: '🤱', 
      description: t('home.analysis.childbirth.description', 'Auspicious dates for delivery'),
      gradient: ['#FF69B4', '#FF1493'],
      cost: pricing.childbirth_planner || 8
    },
    { 
      id: 'muhurat', 
      title: t('home.analysis.muhurat.title', 'Muhurat Planner'), 
      icon: '🕉️', 
      description: t('home.analysis.muhurat.description', 'Auspicious timing for all events'),
      gradient: ['#9C27B0', '#7B1FA2'],
      cost: 0
    }
  ];

  const TickerItem = ({ icon, label, value, color, showInfoIcon }) => (
    <View style={styles.tickerItem}>
      <View style={[styles.tickerIconContainer, { backgroundColor: `${color}20` }]}>
        <Icon name={icon} size={14} color={color} />
      </View>
      <View>
        <Text style={[styles.tickerLabel, { color: colors.textTertiary }]}>{label}</Text>
        <Text style={[styles.tickerValue, { color: colors.text }]}>{value}</Text>
      </View>
      {showInfoIcon && (
        <View style={styles.tickerItemInfoIcon}>
          <Icon name="information-circle-outline" size={18} color={colors.textTertiary} />
        </View>
      )}
    </View>
  );

  return (
    <View style={styles.container}>
      <LinearGradient
        colors={theme === 'dark' 
          ? [colors.gradientStart, colors.gradientMid, colors.gradientEnd, colors.primary] 
          : [colors.gradientStart, colors.gradientMid, colors.gradientEnd, colors.gradientAccent || '#fde68a']}
        style={styles.gradient}
      >
        
      <ScrollView 
        style={[styles.scrollView, { zIndex: 1 }]} 
        contentContainerStyle={styles.content} 
        showsVerticalScrollIndicator={false}
        onScroll={handleScroll}
        scrollEventThrottle={16}
      >
        {/* Header with Native Selector & Big 3 Dashboard - Integrated into ScrollView */}
        <View style={styles.header}>
          <LinearGradient
            colors={theme === 'dark' 
              ? ['rgba(255, 255, 255, 0.1)', 'rgba(255, 255, 255, 0.05)'] 
              : ['rgba(255, 255, 255, 0.98)', 'rgba(255, 247, 237, 0.95)', 'rgba(255, 237, 213, 0.92)']}
            style={[styles.headerDashboard, androidLightCardFixStyle, theme === 'light' ? { borderColor: colors.cardBorder } : {}]}
          >
            <View style={styles.headerTopRow}>
              <View style={styles.headerProfileInfo}>
                <Text style={[styles.headerGreeting, { color: colors.textSecondary }]}>
                  {t('home.greeting.hello', 'Hello')},
                </Text>
                <Text style={[styles.headerName, { color: colors.text }]} numberOfLines={1}>
                  {displayData?.name}
                </Text>
              </View>
              <NativeSelectorChip 
                birthData={displayData}
                onPress={() => navigation.navigate('SelectNative', { returnTo: 'Home' })}
                maxLength={10}
                showIcon={false}
                style={styles.headerNativeChip}
              />
            </View>

            <View style={[styles.headerBigThree, theme === 'light' && { backgroundColor: colors.surface }]}>
              <TouchableOpacity 
                style={styles.headerSignItem}
                onPress={() => {
                  const insight = getSignInsight('ascendant', chartData?.houses?.[0]?.sign);
                  setActiveInsight(insight);
                }}
              >
                <View style={[styles.headerSignIcon, { backgroundColor: theme === 'dark' ? '#3B82F620' : 'rgba(59, 130, 246, 0.12)' }]}>
                  <Text style={styles.headerSignEmoji}>
                    {loading ? '⏳' : getSignIcon(chartData?.houses?.[0]?.sign)}
                  </Text>
                </View>
                <View>
                  <Text style={[styles.headerSignLabel, { color: colors.textTertiary }]}>{t('home.signs.ascendant', 'Asc')}</Text>
                  <Text style={[styles.headerSignName, { color: colors.text }]}>
                    {loading ? '...' : getSignName(chartData?.houses?.[0]?.sign)}
                  </Text>
                </View>
              </TouchableOpacity>

              <View style={[styles.headerDivider, theme === 'light' && { backgroundColor: colors.cardBorder }]} />

              <TouchableOpacity 
                style={styles.headerSignItem}
                onPress={() => {
                  const insight = getSignInsight('moon', chartData?.planets?.Moon?.sign);
                  setActiveInsight(insight);
                }}
              >
                <View style={[styles.headerSignIcon, { backgroundColor: theme === 'dark' ? '#DC262620' : 'rgba(220, 38, 38, 0.12)' }]}>
                  <Text style={styles.headerSignEmoji}>
                    {loading ? '⏳' : getSignIcon(chartData?.planets?.Moon?.sign)}
                  </Text>
                </View>
                <View>
                  <Text style={[styles.headerSignLabel, { color: colors.textTertiary }]}>{t('home.signs.moon', 'Moon')}</Text>
                  <Text style={[styles.headerSignName, { color: colors.text }]}>
                    {loading ? '...' : getSignName(chartData?.planets?.Moon?.sign)}
                  </Text>
                </View>
              </TouchableOpacity>

              <View style={[styles.headerDivider, theme === 'light' && { backgroundColor: colors.cardBorder }]} />

              <TouchableOpacity 
                style={styles.headerSignItem}
                onPress={() => {
                  const insight = getSignInsight('sun', chartData?.planets?.Sun?.sign);
                  setActiveInsight(insight);
                }}
              >
                <View style={[styles.headerSignIcon, { backgroundColor: theme === 'dark' ? '#F59E0B20' : 'rgba(245, 158, 11, 0.2)' }]}>
                  <Text style={styles.headerSignEmoji}>
                    {loading ? '⏳' : getSignIcon(chartData?.planets?.Sun?.sign)}
                  </Text>
                </View>
                <View>
                  <Text style={[styles.headerSignLabel, { color: colors.textTertiary }]}>{t('home.signs.sun', 'Sun')}</Text>
                  <Text style={[styles.headerSignName, { color: colors.text }]}>
                    {loading ? '...' : getSignName(chartData?.planets?.Sun?.sign)}
                  </Text>
                </View>
              </TouchableOpacity>
            </View>
          </LinearGradient>
        </View>

        {/* At-a-Glance Ticker */}
        <View style={[styles.tickerContainer, theme === 'light' && { backgroundColor: colors.surface, borderColor: colors.cardBorder }]}>
          <ScrollView 
            horizontal 
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={styles.tickerContent}
          >
            {tickerData.loading ? (
              <Text style={[styles.tickerLoading, { color: colors.textTertiary }]}>
                {t('home.loading.ticker', 'Loading ticker...')}
              </Text>
            ) : (
              <>
                <TouchableOpacity
                  activeOpacity={0.8}
                  onPress={() => {
                    if (displayData && setShowDashaBrowser) setShowDashaBrowser(true);
                  }}
                >
                  <TickerItem 
                    icon="time-outline" 
                    label={t('home.ticker.activeMahadasha', 'Active Mahadasha')} 
                    value={tickerData.mahadasha || t('common.unknown', 'Unknown')}
                    color="#F59E0B"
                    showInfoIcon
                  />
                </TouchableOpacity>
                <View style={[styles.tickerSeparator, theme === 'light' && { backgroundColor: colors.cardBorder }]} />
                <TouchableOpacity
                  activeOpacity={0.8}
                  onPress={() => navigation.navigate('NakshatraCalendar', { birthData: displayData })}
                >
                  <TickerItem 
                    icon="star-outline" 
                    label={t('home.ticker.todaysNakshatra', "Today's Nakshatra")} 
                    value={tickerData.nakshatra || t('common.unknown', 'Unknown')}
                    color="#8B5CF6"
                    showInfoIcon
                  />
                </TouchableOpacity>
                <View style={[styles.tickerSeparator, theme === 'light' && { backgroundColor: colors.cardBorder }]} />
                <TouchableOpacity
                  activeOpacity={0.8}
                  onPress={() => displayData && navigation.navigate('SadeSati', { birthData: displayData })}
                >
                  <TickerItem 
                    icon="shield-checkmark-outline" 
                    label={t('home.ticker.sadeSati', 'Sade Sati')} 
                    value={tickerData.sadeSati ? t('home.ticker.active', 'Active') : t('home.ticker.noSadeSati', 'No active Sade Sati')}
                    color={tickerData.sadeSati ? "#EF4444" : "#10B981"}
                    showInfoIcon
                  />
                </TouchableOpacity>
              </>
            )}
          </ScrollView>
        </View>


        {/* Biometric Teaser Card - COMMENTED OUT */}
        {/* <BiometricTeaserCard 
          onPressReveal={() => {
            console.log('🔄 BiometricTeaserCard pressed');
            handlePhysicalScan();
          }}
          isLoading={scanLoading}
        /> */}

        <View style={styles.optionsContainer}>
          <Text style={[styles.optionsTitle, { color: colors.text }]}>{t('home.sections.choosePath', 'Choose Your Path')}</Text>
          {options.map((option, index) => (
            <OptionCard
              key={option.id}
              option={option}
              index={index}
              onOptionSelect={onOptionSelect}
            />
          ))}
        </View>

        {/* Life Analysis Options */}
        <View style={styles.analysisContainer}>
          <Text style={[styles.analysisTitle, { color: colors.text }]}>{t('home.sections.lifeAnalysis', '🧘 Life Analysis')}</Text>
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
        </View>

        {/* Timing Planners - Cosmic Ribbon (Horizontal Snap-Gallery) */}
        <View style={styles.ribbonContainer}>
          <Text style={[styles.analysisTitle, { color: colors.text, paddingHorizontal: 20 }]}>
            {t('home.sections.timingPlanners', '⏰ Timing Planners')}
          </Text>
          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            snapToInterval={width * 0.72 + 16}
            decelerationRate="fast"
            contentContainerStyle={styles.ribbonScrollContent}
          >
            {analysisOptions.slice(6).map((option, index) => (
              <CosmicRibbonCard
                key={option.id}
                option={option}
                index={index}
                onOptionSelect={onOptionSelect}
              />
            ))}
          </ScrollView>
        </View>



        {/* Magical Dashboard Cards - Moved to Bottom */}
        <View style={styles.dashboardContainer}>


          {/* Mini Insight Modal - theme aware */}
          <Modal
            visible={!!activeInsight}
            transparent={true}
            animationType="fade"
            onRequestClose={() => setActiveInsight(null)}
          >
            <TouchableOpacity 
              style={[styles.modalOverlay, { backgroundColor: theme === 'dark' ? 'rgba(0, 0, 0, 0.7)' : 'rgba(0, 0, 0, 0.45)' }]} 
              activeOpacity={1} 
              onPress={() => setActiveInsight(null)}
            >
              <View style={styles.insightModalContent}>
                <LinearGradient
                  colors={theme === 'dark' 
                    ? [colors.backgroundSecondary, colors.backgroundTertiary] 
                    : [colors.background, colors.backgroundSecondary]}
                  style={[styles.insightGradient, { borderColor: colors.cardBorder }]}
                >
                  <View style={styles.insightHeader}>
                    <Text style={styles.insightEmoji}>{activeInsight?.icon}</Text>
                    <Text style={[styles.insightTitle, { color: colors.primary }]}>{activeInsight?.title}</Text>
                  </View>
                  <Text style={[styles.insightDescription, { color: colors.text }]}>
                    {activeInsight?.description}
                  </Text>
                  <TouchableOpacity
                    style={[styles.insightCloseButton, { backgroundColor: colors.primary }]}
                    onPress={() => setActiveInsight(null)}
                  >
                    <Text style={styles.insightCloseText}>{t('languageModal.close', 'Close')}</Text>
                  </TouchableOpacity>
                </LinearGradient>
              </View>
            </TouchableOpacity>
          </Modal>

          {/* Current Dasha Timeline - Compact Style (tap to open CascadingDashaBrowser) */}
          {dashData && (
            <TouchableOpacity
              style={[styles.dashaTimelineContainer, androidLightCardFixStyle, theme === 'light' && { backgroundColor: colors.surface, borderColor: colors.cardBorder }]}
              onPress={() => setShowDashaBrowser && setShowDashaBrowser(true)}
              activeOpacity={0.85}
            >
              <Text style={[styles.dashaSectionTitle, { color: colors.text }]}>{t('home.sections.currentDasha', '⏰ Current Dasha Periods')}</Text>
              <View style={styles.timelineWrapper}>
                {[
                  { level: 'MD', data: dashData.maha_dashas?.find(d => d.current) },
                  { level: 'AD', data: dashData.antar_dashas?.find(d => d.current) },
                  { level: 'PD', data: dashData.pratyantar_dashas?.find(d => d.current) },
                ].filter(item => item.data).map((item, index) => {
                  const dasha = item.data;
                  const planetColor = getPlanetColor(dasha.planet);
                  const startDate = dasha.start ? new Date(dasha.start) : null;
                  const endDate = dasha.end ? new Date(dasha.end) : null;
                  const now = new Date();
                  
                  let progress = 0;
                  if (startDate && endDate && !isNaN(startDate.getTime()) && !isNaN(endDate.getTime())) {
                    const total = endDate.getTime() - startDate.getTime();
                    const elapsed = now.getTime() - startDate.getTime();
                    progress = (elapsed / total) * 100;
                    
                    if (isNaN(progress) || !isFinite(progress)) {
                      progress = 0;
                    }
                    
                    progress = Math.max(0, Math.min(100, progress));
                  }
                  
                  return (
                    <View key={item.level} style={styles.timelineRow}>
                      <View style={styles.timelineLeft}>
                        <View style={[styles.levelBadge, { backgroundColor: (colors.textSecondary || '#ffffff') + '20' }]}>
                          <Text style={[styles.levelText, { color: colors.textSecondary }]}>{item.level}</Text>
                        </View>
                        {index < 2 && <View style={[styles.timelineConnector, { backgroundColor: (colors.textSecondary || '#ffffff') + '30' }]} />}
                      </View>
                      
                      <View style={styles.timelineContent}>
                        <View style={styles.timelineHeader}>
                          <Text style={[styles.timelinePlanet, { color: planetColor }]}>
                            {t(`home.planet_names.${dasha.planet}`, dasha.planet)}
                          </Text>
                          <Text style={[styles.timelineDate, { color: colors.textTertiary }]}>
                            {t('common.ends', 'Ends')}: {endDate && !isNaN(endDate.getTime()) ? endDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: '2-digit' }) : '...'}
                          </Text>
                        </View>
                        
                        <View style={styles.progressContainer}>
                          <View style={[styles.progressBar, { backgroundColor: (colors.textSecondary || '#ffffff') + '10' }]}>
                            <View style={[styles.progressFill, { width: `${progress}%`, backgroundColor: planetColor }]} />
                          </View>
                          <Text style={[styles.progressPercent, { color: colors.textTertiary }]}>{Math.round(progress)}%</Text>
                        </View>
                      </View>
                    </View>
                  );
                })}
              </View>
            </TouchableOpacity>
          )}

          {/* Astrology Tools Section */}
          <View style={styles.toolsSection}>
            <Text style={[styles.toolsSectionTitle, { color: colors.text }]}>{t('home.sections.astrologyTools', '🔧 Astrology Tools')}</Text>
            <ScrollView 
              horizontal 
              showsHorizontalScrollIndicator={false}
              contentContainerStyle={styles.toolsScrollContent}
              decelerationRate="fast"
              snapToInterval={width * 0.3 + 12}
            >
              <TouchableOpacity 
                style={[styles.toolCard, androidLightCardFixStyle]}
                onPress={() => navigation.navigate('Chart', { birthData })}
                activeOpacity={0.8}
              >
                <View style={[
                  styles.toolGlassmorphism,
                  androidLightCardFixStyle,
                  {
                    backgroundColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.1)' : 'rgba(251, 146, 60, 0.15)',
                    borderColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.2)' : 'rgba(249, 115, 22, 0.3)',
                  }
                ]}>
                  <View style={styles.toolIconContainer}>
                    <Svg width="28" height="28" viewBox="0 0 48 48">
                      <Rect x="2" y="2" width="44" height="44" fill="none" stroke="#ffffff" strokeWidth="2" />
                      <Polygon points="24,2 46,24 24,46 2,24" fill="none" stroke="#ffd700" strokeWidth="1.5" />
                      <Line x1="2" y1="2" x2="46" y2="46" stroke="#ff8a65" strokeWidth="1" />
                      <Line x1="46" y1="2" x2="2" y2="46" stroke="#ff8a65" strokeWidth="1" />
                    </Svg>
                    <View style={[styles.toolIconGlow, { backgroundColor: '#ff8a65' }]} />
                  </View>
                  <Text style={[styles.toolTitle, { color: colors.text }]}>{t('home.tools.charts', 'Charts')}</Text>
                </View>
              </TouchableOpacity>
              
              <TouchableOpacity 
                style={[styles.toolCard, androidLightCardFixStyle]}
                onPress={() => setShowDashaBrowser(true)}
                activeOpacity={0.8}
              >
                <View style={[
                  styles.toolGlassmorphism,
                  androidLightCardFixStyle,
                  {
                    backgroundColor: theme === 'dark' ? 'rgba(139, 92, 246, 0.1)' : 'rgba(139, 92, 246, 0.15)',
                    borderColor: 'rgba(139, 92, 246, 0.3)',
                  }
                ]}>
                  <View style={styles.toolIconContainer}>
                    <Icon name="time-outline" size={24} color="#A78BFA" />
                    <View style={[styles.toolIconGlow, { backgroundColor: '#A78BFA' }]} />
                  </View>
                  <Text style={[styles.toolTitle, { color: colors.text }]}>{t('home.tools.dashas', 'Dashas')}</Text>
                  {dashData?.current_dasha && typeof dashData.current_dasha === 'string' && (
                    <View style={[styles.toolMiniStat, { backgroundColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.08)' }]}>
                      <Text style={[styles.toolMiniStatText, { color: theme === 'dark' ? 'rgba(255, 255, 255, 0.6)' : colors.textSecondary }]}>{dashData.current_dasha.split(' ')[0]}</Text>
                    </View>
                  )}
                </View>
              </TouchableOpacity>

              <TouchableOpacity 
                style={[styles.toolCard, androidLightCardFixStyle]}
                onPress={() => navigation.navigate('KPSystem', { birthDetails: birthData })}
                activeOpacity={0.8}
              >
                <View style={[
                  styles.toolGlassmorphism,
                  androidLightCardFixStyle,
                  {
                    backgroundColor: theme === 'dark' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(16, 185, 129, 0.15)',
                    borderColor: 'rgba(16, 185, 129, 0.3)',
                  }
                ]}>
                  <View style={styles.toolIconContainer}>
                    <Icon name="locate-outline" size={24} color="#34D399" />
                    <View style={[styles.toolIconGlow, { backgroundColor: '#34D399' }]} />
                  </View>
                  <Text style={[styles.toolTitle, { color: colors.text }]}>{t('menu.kpSystem', 'KP System')}</Text>
                  <View style={[styles.toolMiniStat, { backgroundColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.08)' }]}>
                    <Text style={[styles.toolMiniStatText, { color: theme === 'dark' ? 'rgba(255, 255, 255, 0.6)' : colors.textSecondary }]}>Precise</Text>
                  </View>
                </View>
              </TouchableOpacity>

              <TouchableOpacity 
                style={[styles.toolCard, androidLightCardFixStyle]}
                onPress={() => navigation.navigate('KotaChakra', { birthChartId: birthData?.id })}
                activeOpacity={0.8}
              >
                <View style={[
                  styles.toolGlassmorphism,
                  androidLightCardFixStyle,
                  {
                    backgroundColor: theme === 'dark' ? 'rgba(245, 158, 11, 0.1)' : 'rgba(245, 158, 11, 0.15)',
                    borderColor: 'rgba(245, 158, 11, 0.3)',
                  }
                ]}>
                  <View style={styles.toolIconContainer}>
                    <Icon name="shield-checkmark-outline" size={24} color="#FBBF24" />
                    <View style={[styles.toolIconGlow, { backgroundColor: '#FBBF24' }]} />
                  </View>
                  <Text style={[styles.toolTitle, { color: colors.text }]}>{t('menu.kotaChakra', 'Kota Chakra')}</Text>
                  <View style={[styles.toolMiniStat, { backgroundColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.08)' }]}>
                    <Text style={[styles.toolMiniStatText, { color: theme === 'dark' ? 'rgba(255, 255, 255, 0.6)' : colors.textSecondary }]}>Safety</Text>
                  </View>
                </View>
              </TouchableOpacity>

              <TouchableOpacity 
                style={[styles.toolCard, androidLightCardFixStyle]}
                onPress={() => navigation.navigate('Yogas')}
                activeOpacity={0.8}
              >
                <View style={[
                  styles.toolGlassmorphism,
                  androidLightCardFixStyle,
                  {
                    backgroundColor: theme === 'dark' ? 'rgba(236, 72, 153, 0.1)' : 'rgba(236, 72, 153, 0.15)',
                    borderColor: 'rgba(236, 72, 153, 0.3)',
                  }
                ]}>
                  <View style={styles.toolIconContainer}>
                    <Icon name="diamond-outline" size={24} color="#F472B6" />
                    <View style={[styles.toolIconGlow, { backgroundColor: '#F472B6' }]} />
                  </View>
                  <Text style={[styles.toolTitle, { color: colors.text }]}>{t('menu.yogas', 'Yogas')}</Text>
<View style={[styles.toolMiniStat, { backgroundColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.08)' }]}>
                  <Text style={[styles.toolMiniStatText, { color: theme === 'dark' ? 'rgba(255, 255, 255, 0.6)' : colors.textSecondary }]}>Fortune</Text>
                  </View>
                </View>
              </TouchableOpacity>
              
              <TouchableOpacity 
                style={[styles.toolCard, androidLightCardFixStyle]}
                onPress={() => navigation.navigate('AshtakvargaOracle')}
                activeOpacity={0.8}
              >
                <View style={[
                  styles.toolGlassmorphism,
                  androidLightCardFixStyle,
                  {
                    backgroundColor: theme === 'dark' ? 'rgba(59, 130, 246, 0.1)' : 'rgba(59, 130, 246, 0.15)',
                    borderColor: 'rgba(59, 130, 246, 0.3)',
                  }
                ]}>
                  <View style={styles.toolIconContainer}>
                    <Icon name="grid-outline" size={24} color="#60A5FA" />
                    <View style={[styles.toolIconGlow, { backgroundColor: '#60A5FA' }]} />
                  </View>
                  <Text style={[styles.toolTitle, { color: colors.text }]}>{t('home.tools.ashtakvarga', 'Ashtak-\nvarga')}</Text>
                </View>
              </TouchableOpacity>
              
              <TouchableOpacity 
                style={[styles.toolCard, androidLightCardFixStyle]}
                onPress={() => chartData && navigation.navigate('PlanetaryPositions', { chartData })}
                activeOpacity={0.8}
              >
                <View style={[
                  styles.toolGlassmorphism,
                  androidLightCardFixStyle,
                  {
                    backgroundColor: theme === 'dark' ? 'rgba(244, 63, 94, 0.1)' : 'rgba(244, 63, 94, 0.15)',
                    borderColor: 'rgba(244, 63, 94, 0.3)',
                  }
                ]}>
                  <View style={styles.toolIconContainer}>
                    <Icon name="planet-outline" size={24} color="#FB7185" />
                    <View style={[styles.toolIconGlow, { backgroundColor: '#FB7185' }]} />
                  </View>
                  <Text style={[styles.toolTitle, { color: colors.text }]}>{t('home.tools.positions', 'Positions')}</Text>
                </View>
              </TouchableOpacity>

              <TouchableOpacity 
                style={[styles.toolCard, androidLightCardFixStyle]}
                onPress={() => navigation.navigate('CosmicRing')}
                activeOpacity={0.8}
              >
                <View style={[
                  styles.toolGlassmorphism,
                  androidLightCardFixStyle,
                  {
                    backgroundColor: theme === 'dark' ? 'rgba(56, 189, 248, 0.1)' : 'rgba(56, 189, 248, 0.15)',
                    borderColor: 'rgba(56, 189, 248, 0.3)',
                  }
                ]}>
                  <View style={styles.toolIconContainer}>
                    <Icon name="ellipse-outline" size={24} color="#38BDF8" />
                    <View style={[styles.toolIconGlow, { backgroundColor: '#38BDF8' }]} />
                  </View>
                  <Text style={[styles.toolTitle, { color: colors.text }]}>{t('home.tools.cosmicRing', 'Cosmic\nRing')}</Text>
                </View>
              </TouchableOpacity>
            </ScrollView>
          </View>

          {/* Cosmic Weather - Transits & Mini Zodiac */}
          <View style={[styles.planetarySection, theme === 'light' && { backgroundColor: colors.cardBackground, borderColor: 'rgba(234, 88, 12, 0.18)' }]}>
            <View style={styles.planetaryHeader}>
              <Text style={[styles.planetarySectionTitle, { color: colors.text }]}>{t('home.sections.planetaryTransits', '🪐 Cosmic Weather')}</Text>
              <View style={styles.planetaryHeaderRight}>
                <TouchableOpacity
                  style={[styles.cosmicRingChip, theme === 'dark' ? styles.cosmicRingChipDark : styles.cosmicRingChipLight]}
                  onPress={() => navigation.navigate('CosmicRing')}
                  activeOpacity={0.8}
                >
                  <Icon name="ellipse-outline" size={16} color={colors.primary} />
                  <Text style={[styles.cosmicRingChipText, { color: colors.primary }]}>{t('home.cosmicRing.viewRing', 'Ring')}</Text>
                </TouchableOpacity>
              </View>
            </View>

            {!transitData ? (
              <Text style={[styles.loadingText, { color: colors.textTertiary }]}>{t('home.loading.transits', 'Loading transits...')}</Text>
            ) : !transitData.planets ? (
              <Text style={[styles.loadingText, { color: colors.textTertiary }]}>{t('home.loading.noTransitData', 'No transit data available')}</Text>
            ) : (
              <View>
                  {/* Mini Zodiac Map */}
                  <View style={styles.miniZodiacContainer}>
                    <View style={styles.zodiacWheelWrapper}>
                      <Svg width="160" height="160" viewBox="0 0 160 160">
                        {/* Outer Sign Ring */}
                        <Circle cx="80" cy="80" r="75" fill="none" stroke={colors.strokeStrong} strokeWidth="2" />
                        
                        {/* Sign Dividers & Symbols */}
                        {[...Array(12)].map((_, i) => {
                          const angle = (i * 30 - 90) * (Math.PI / 180);
                          const midAngle = angle + (15 * Math.PI / 180);
                          
                          // Divider lines
                          const x1 = 80 + 55 * Math.cos(angle);
                          const y1 = 80 + 55 * Math.sin(angle);
                          const x2 = 80 + 75 * Math.cos(angle);
                          const y2 = 80 + 75 * Math.sin(angle);
                          
                          if (isNaN(x1) || isNaN(y1) || isNaN(x2) || isNaN(y2)) return null;
                          
                          // Sign Symbol Position (just outside the ring)
                          const sx = 80 + 65 * Math.cos(midAngle);
                          const sy = 80 + 65 * Math.sin(midAngle);
                          
                          if (isNaN(sx) || isNaN(sy)) return null;
                          
                          return (
                            <React.Fragment key={i}>
                              <Line x1={x1} y1={y1} x2={x2} y2={y2} stroke={colors.strokeMuted} strokeWidth="1.5" />
                              <SvgText
                                x={sx}
                                y={sy}
                                fill={colors.text}
                                fontSize="14"
                                fontWeight="900"
                                textAnchor="middle"
                                alignmentBaseline="middle"
                              >
                                {getSignIcon(i)}
                              </SvgText>
                            </React.Fragment>
                          );
                        })}

                        {/* Inner Rings */}
                        <Circle cx="80" cy="80" r="55" fill="none" stroke={colors.strokeStrong} strokeWidth="2" />
                        <Circle cx="80" cy="80" r="40" fill="none" stroke={colors.strokeMuted} strokeWidth="1.5" />
                        
                        {/* Planet Dots */}
                        {Object.entries(transitData.planets || {}).map(([planet, data], i) => {
                          if (!data || data.sign === undefined || data.degree === undefined) return null;
                          const sign = parseFloat(data.sign);
                          const degree = parseFloat(data.degree);
                          if (isNaN(sign) || isNaN(degree)) return null;
                          
                          const angle = (sign * 30 + degree - 90) * (Math.PI / 180);
                          const r = 47;
                          const x = 80 + r * Math.cos(angle);
                          const y = 80 + r * Math.sin(angle);
                          
                          if (isNaN(x) || isNaN(y)) return null;
                          
                          return (
                            <Circle 
                              key={planet} 
                              cx={x} 
                              cy={y} 
                              r="5" 
                              fill={getPlanetColor(planet)} 
                              opacity={1}
                              stroke={theme === 'dark' ? '#FFFFFF' : colors.text}
                              strokeWidth="1.5"
                            />
                          );
                        })}
                      </Svg>
                      {/* Center Glow */}
                      <View style={[styles.zodiacCenterGlow, theme === 'light' && { backgroundColor: 'rgba(249, 115, 22, 0.08)' }]} />
                    </View>
                    
                    <View style={styles.zodiacSummary}>
                      <Text style={[styles.zodiacSummaryTitle, { color: colors.textSecondary }]}>Planetary Alignment</Text>
                      <Text style={[styles.zodiacSummaryText, { color: colors.text }]}>
                        {(() => {
                          const signCounts = {};
                          const planets = transitData.planets || {};
                          Object.values(planets).forEach(p => {
                            if (p && p.sign !== undefined) {
                              signCounts[p.sign] = (signCounts[p.sign] || 0) + 1;
                            }
                          });
                          const sortedSigns = Object.entries(signCounts).sort((a, b) => b[1] - a[1]);
                          const maxSign = sortedSigns.length > 0 ? sortedSigns[0] : null;
                          if (!maxSign) return '';
                          
                          const signIdx = parseInt(maxSign[0]);
                          if (isNaN(signIdx)) return '';
                          
                          const signName = getSignName(signIdx);
                          if (!signName || signName === 'Unknown' || signName === t('common.unknown', 'Unknown')) return '';
                          
                          return `${maxSign[1]} planets in ${signName}`;
                        })()}
                      </Text>
                      <View style={styles.alignmentBarContainer}>
                        <View style={[styles.alignmentBar, { width: '70%', backgroundColor: colors.primary }]} />
                      </View>
                    </View>
                  </View>

                {/* Horizontal Transit Strip */}
                <ScrollView 
                  horizontal 
                  showsHorizontalScrollIndicator={false}
                  contentContainerStyle={styles.transitScrollContent}
                >
                  {Object.entries(transitData.planets || {}).map(([planet, data]) => {
                    if (!data) return null;
                    const vibe = getPlanetVibe(planet);
                    const status = getPlanetStatus(planet, data.sign, data.is_retrograde);
                          const signIdx = parseInt(data.sign);
                          if (isNaN(signIdx)) return null;
                          const signName = getSignName(signIdx);
                          
                          return (
                            <View key={planet} style={[
                              styles.transitCard,
                              theme === 'dark'
                                ? { backgroundColor: 'rgba(255,255,255,0.03)', borderColor: getSignColor(signIdx) + '40' }
                                : { backgroundColor: '#fffbf7', borderColor: getSignColor(signIdx) + '45' }
                            ]}>
                              <View style={styles.transitCardHeader}>
                                <Text style={styles.transitPlanetIcon}>{vibe.icon}</Text>
                                <View style={styles.vibeTag}>
                                  <Text style={[styles.vibeTagText, { color: colors.textTertiary }]}>{vibe.tag}</Text>
                                </View>
                              </View>
                              
                              <View style={styles.transitMainInfo}>
                                <Text style={[styles.transitPlanetName, { color: colors.text }]}>
                                  {t(`home.planet_names.${planet}`, planet)}
                                </Text>
                                <View style={styles.statusBadges}>
                                  {status.map((s, idx) => (
                                    <View key={idx} style={[styles.statusBadge, { backgroundColor: s.color + '20' }]}>
                                      <Text style={[styles.statusBadgeText, { color: s.color }]}>{s.label}</Text>
                                    </View>
                                  ))}
                                </View>
                              </View>
                              
                              <View style={styles.transitSignRow}>
                                <Text style={styles.transitSignIcon}>{getSignIcon(signIdx)}</Text>
                                <Text style={[styles.transitSignName, { color: colors.textSecondary }]}>
                                  {signName}
                                </Text>
                              </View>
                            </View>
                          );
                  })}
                </ScrollView>
              </View>
            )}
          </View>

          {/* Panchang Timeline */}
          {panchangData && (
            <View style={[styles.panchangCard, androidLightCardFixStyle, theme === 'light' && { backgroundColor: colors.cardBackground, borderColor: 'rgba(234, 88, 12, 0.18)', borderWidth: 1 }]}>
              <Text style={[styles.panchangTitle, { color: colors.text }]}>
                {t('home.panchang.title', '🌅 Today\'s Panchang')}
              </Text>
              <View style={[styles.panchangTitleUnderline, theme === 'light' && { backgroundColor: colors.primary }]} />
              
              <View style={styles.sunTimesRow}>
                <View style={[styles.sunTimeItem, theme === 'light' && { backgroundColor: '#fffbf7', borderColor: 'rgba(234, 88, 12, 0.22)' }]}>
                  <Text style={styles.sunTimeEmoji}>🌅</Text>
                  <Text style={[styles.sunTimeLabel, { color: colors.textSecondary }]}>{t('home.panchang.sunrise', 'Sunrise')}</Text>
                  <Text style={[styles.sunTimeValue, { color: colors.text }]}>
                    {panchangData.sunrise && !isNaN(new Date(panchangData.sunrise).getTime()) ? new Date(panchangData.sunrise).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true }) : '6:30 AM'}
                  </Text>
                </View>
                <View style={[styles.sunTimeItem, theme === 'light' && { backgroundColor: '#fffbf7', borderColor: 'rgba(234, 88, 12, 0.22)' }]}>
                  <Text style={styles.sunTimeEmoji}>🌇</Text>
                  <Text style={[styles.sunTimeLabel, { color: colors.textSecondary }]}>{t('home.panchang.sunset', 'Sunset')}</Text>
                  <Text style={[styles.sunTimeValue, { color: colors.text }]}>
                    {panchangData.sunset && !isNaN(new Date(panchangData.sunset).getTime()) ? new Date(panchangData.sunset).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true }) : '6:45 PM'}
                  </Text>
                </View>
              </View>
              
              <View style={styles.sunTimesRow}>
                <View style={[styles.sunTimeItem, theme === 'light' && { backgroundColor: '#fffbf7', borderColor: 'rgba(234, 88, 12, 0.22)' }]}>
                  <Text style={styles.sunTimeEmoji}>🌙</Text>
                  <Text style={[styles.sunTimeLabel, { color: colors.textSecondary }]}>{t('home.panchang.moonrise', 'Moonrise')}</Text>
                  <Text style={[styles.sunTimeValue, { color: colors.text }]}>
                    {panchangData.daily_panchang?.sunrise_sunset?.moonrise || panchangData.sunrise_sunset?.moonrise || '7:53 AM'}
                  </Text>
                </View>
                <View style={[styles.sunTimeItem, theme === 'light' && { backgroundColor: '#fffbf7', borderColor: 'rgba(234, 88, 12, 0.22)' }]}>
                  <Text style={styles.sunTimeEmoji}>🌚</Text>
                  <Text style={[styles.sunTimeLabel, { color: colors.textSecondary }]}>{t('home.panchang.moonset', 'Moonset')}</Text>
                  <Text style={[styles.sunTimeValue, { color: colors.text }]}>
                    {panchangData.daily_panchang?.sunrise_sunset?.moonset || panchangData.sunrise_sunset?.moonset || '6:06 PM'}
                  </Text>
                </View>
              </View>
              
              {/* Day Progress */}
              <View style={styles.dayProgressBar}>
                <View style={[styles.progressTrack, theme === 'light' && { backgroundColor: 'rgba(0,0,0,0.1)' }]}>
                  {(() => {
                    const now = new Date();
                    const sunrise = panchangData.sunrise ? new Date(panchangData.sunrise) : null;
                    const sunset = panchangData.sunset ? new Date(panchangData.sunset) : null;
                    
                    if (!sunrise || !sunset || isNaN(sunrise.getTime()) || isNaN(sunset.getTime())) {
                      return <View style={[styles.progressFill, { width: '0%' }]} />;
                    }

                    const totalDayTime = sunset.getTime() - sunrise.getTime();
                    const elapsedTime = now.getTime() - sunrise.getTime();
                    let progress = (elapsedTime / totalDayTime) * 100;
                    
                    if (isNaN(progress) || !isFinite(progress)) {
                      progress = 0;
                    }
                    
                    progress = Math.max(0, Math.min(100, progress));
                    
                    return (
                      <>
                        <View style={[styles.progressFill, { width: `${progress}%` }]} />
                        <View style={[styles.currentTimeDot, { left: `${progress}%` }]}>
                          <Icon name="sunny" size={12} color="#fff" />
                        </View>
                      </>
                    );
                  })()}
                </View>
                <Text style={[styles.progressLabel, { color: colors.textTertiary }]}>
                  {t('home.panchang.dayProgress', 'Day Progress')}
                </Text>
              </View>

              {/* Panchang Elements Section */}
              {panchangData.daily_panchang && (
                <View style={styles.panchangElementsSection}>
                  <Text style={[styles.panchangElementsTitle, { color: colors.primary }]}>
                    {t('home.panchang.elements', '🕉️ Panchang Elements')}
                  </Text>
                  
                  <View style={styles.panchangElementGrid}>
                    {/* Tithi */}
                    {panchangData.daily_panchang.tithi && (
                      <View style={[styles.panchangElement, theme === 'light' && { backgroundColor: '#fffbf7', borderColor: 'rgba(234, 88, 12, 0.22)' }]}>
                        <Text style={[styles.elementLabel, { color: colors.textSecondary }]}>
                          {t('home.panchang.tithi', '🌙 Tithi')}
                        </Text>
                        <Text style={[styles.elementValue, { color: colors.text }]}>
                          {panchangData.daily_panchang.tithi.name}
                        </Text>
                      </View>
                    )}
                    
                    {/* Yoga */}
                    {panchangData.daily_panchang.yoga && (
                      <View style={[styles.panchangElement, theme === 'light' && { backgroundColor: '#fffbf7', borderColor: 'rgba(234, 88, 12, 0.22)' }]}>
                        <Text style={[styles.elementLabel, { color: colors.textSecondary }]}>
                          {t('home.panchang.yoga', '🧘 Yoga')}
                        </Text>
                        <Text style={[styles.elementValue, { color: colors.text }]}>
                          {panchangData.daily_panchang.yoga.name}
                        </Text>
                      </View>
                    )}
                    
                    {/* Karana */}
                    {panchangData.daily_panchang.karana && (
                      <View style={[styles.panchangElement, theme === 'light' && { backgroundColor: '#fffbf7', borderColor: 'rgba(234, 88, 12, 0.22)' }]}>
                        <Text style={[styles.elementLabel, { color: colors.textSecondary }]}>
                          {t('home.panchang.karana', '⚡ Karana')}
                        </Text>
                        <Text style={[styles.elementValue, { color: colors.text }]}>
                          {panchangData.daily_panchang.karana.name}
                        </Text>
                      </View>
                    )}
                  </View>
                </View>
              )}
              

              
              {/* Moon SVG & Info Row */}
              <View style={styles.moonSectionRow}>
                <View style={styles.moonSvgContainer}>
                  {/* Starlight Background */}
                  <View style={styles.starlightContainer}>
                    {[...Array(12)].map((_, i) => (
                      <View 
                        key={i} 
                        style={[
                          styles.star, 
                          { 
                            top: `${Math.random() * 100}%`, 
                            left: `${Math.random() * 100}%`,
                            opacity: Math.random() * 0.7 + 0.3,
                            width: Math.random() * 2 + 1,
                            height: Math.random() * 2 + 1,
                            backgroundColor: '#fff'
                          }
                        ]} 
                      />
                    ))}
                  </View>
                  <Svg width="100" height="100" viewBox="0 0 100 100">
                    <Circle cx="50" cy="50" r="45" fill="#1a1a1a" stroke="rgba(255,255,255,0.05)" strokeWidth="1" />
                    {(() => {
                      const illumination = parseFloat(panchangData.moon_illumination) || 98.5;
                      const phase = panchangData.moon_phase || 'Full Moon';
                      const r = 43;
                      const cx = 50;
                      const cy = 50;
                      
                      if (isNaN(illumination)) return <Circle cx="50" cy="50" r="43" fill="#f0f0f0" />;

                      const normalizedPhase = phase.toLowerCase();
                      const isWaning = normalizedPhase.includes('waning') || normalizedPhase.includes('last quarter') || normalizedPhase.includes('third quarter');
                      const isFull = normalizedPhase.includes('full');
                      const isNew = normalizedPhase.includes('new');
                      const isWaxing = !isWaning && !isFull && !isNew;

                      if (isNew || illumination <= 2) return null; 
                      if (isFull || illumination >= 98) return <Circle cx="50" cy="50" r="43" fill="#f0f0f0" />;
                      
                      const ellipseRadiusX = r * Math.abs(1 - (2 * illumination / 100));
                      if (isNaN(ellipseRadiusX)) return <Circle cx="50" cy="50" r="43" fill="#f0f0f0" />;

                      let pathData = "";
                      if (isWaxing) {
                        pathData = `M ${cx} ${cy - r} A ${r} ${r} 0 0 1 ${cx} ${cy + r}`;
                        if (illumination > 50) pathData += ` A ${ellipseRadiusX} ${r} 0 0 1 ${cx} ${cy - r} Z`;
                        else pathData += ` A ${ellipseRadiusX} ${r} 0 0 0 ${cx} ${cy - r} Z`;
                      } else {
                        pathData = `M ${cx} ${cy - r} A ${r} ${r} 0 0 0 ${cx} ${cy + r}`;
                        if (illumination > 50) pathData += ` A ${ellipseRadiusX} ${r} 0 0 0 ${cx} ${cy - r} Z`;
                        else pathData += ` A ${ellipseRadiusX} ${r} 0 0 1 ${cx} ${cy - r} Z`;
                      }
                      return <Path d={pathData} fill="#f0f0f0" stroke="none" />;
                    })()}
                  </Svg>
                </View>
                
                <View style={styles.moonInfoContainer}>
                  <Text style={[styles.moonPhaseText, { color: colors.text }]}>
                    {panchangData.moon_phase || t('home.panchang.fullMoon', 'Full Moon')}
                  </Text>
                  <Text style={[styles.moonIllumination, { color: colors.textSecondary }]}>
                    {panchangData.moon_illumination ? `${panchangData.moon_illumination.toFixed(1)}% ${t('home.panchang.illuminated', 'Illuminated')}` : '98.5% Illuminated'}
                  </Text>
                  <View style={styles.moonElementRow}>
                    <Icon name="moon-outline" size={14} color={colors.textTertiary} />
                    <Text style={[styles.moonElementText, { color: colors.textSecondary }]}>
                      {panchangData.daily_panchang?.nakshatra?.name || '...'}
                    </Text>
                  </View>
                </View>
              </View>

              {/* Visual Day Quality Timeline */}
              <View style={styles.dayQualityContainer}>
                <Text style={[styles.dayQualityTitle, { color: colors.text }]}>{t('home.panchang.dayQuality', 'Day Quality Timeline')}</Text>
                <View style={styles.qualityTimelineWrapper}>
                  <View style={[styles.qualityTimelineTrack, theme === 'light' && { backgroundColor: 'rgba(0,0,0,0.06)', borderColor: 'rgba(0,0,0,0.12)' }]}>
                    {(() => {
                      const now = new Date();
                      const startOfDay = new Date(now);
                      startOfDay.setHours(0, 0, 0, 0);
                      const totalMs = 24 * 60 * 60 * 1000;
                      
                      const getPos = (timeStr) => {
                        if (!timeStr) return null;
                        const d = new Date(timeStr);
                        if (isNaN(d.getTime())) return null;
                        return ((d.getTime() - startOfDay.getTime()) / totalMs) * 100;
                      };

                      const blocks = [];
                      
                      // Brahma Muhurta (Green)
                      if (panchangData.brahma_muhurta_start && panchangData.brahma_muhurta_end) {
                        const start = getPos(panchangData.brahma_muhurta_start);
                        const end = getPos(panchangData.brahma_muhurta_end);
                        if (start !== null && end !== null) {
                          blocks.push(<View key="brahma" style={[styles.qualityBlock, { left: `${start}%`, width: `${end - start}%`, backgroundColor: '#10B981' }]} />);
                        }
                      }

                      // Abhijit Muhurta (Green)
                      if (panchangData.abhijit_muhurta_start && panchangData.abhijit_muhurta_end) {
                        const start = getPos(panchangData.abhijit_muhurta_start);
                        const end = getPos(panchangData.abhijit_muhurta_end);
                        if (start !== null && end !== null) {
                          blocks.push(<View key="abhijit" style={[styles.qualityBlock, { left: `${start}%`, width: `${end - start}%`, backgroundColor: '#10B981' }]} />);
                        }
                      }

                      // Rahu Kaal (Red)
                      if (panchangData.rahu_kaal?.rahu_kaal_start && panchangData.rahu_kaal?.rahu_kaal_end) {
                        const start = getPos(panchangData.rahu_kaal.rahu_kaal_start);
                        const end = getPos(panchangData.rahu_kaal.rahu_kaal_end);
                        if (start !== null && end !== null) {
                          blocks.push(<View key="rahu" style={[styles.qualityBlock, { left: `${start}%`, width: `${end - start}%`, backgroundColor: '#EF4444' }]} />);
                        }
                      }

                      // Dur Muhurta (Red)
                      panchangData.inauspicious_times?.dur_muhurta?.forEach((period, i) => {
                        const start = getPos(period.start_time);
                        const end = getPos(period.end_time);
                        if (start !== null && end !== null) {
                          blocks.push(<View key={`dur-${i}`} style={[styles.qualityBlock, { left: `${start}%`, width: `${end - start}%`, backgroundColor: '#EF4444', opacity: 0.7 }]} />);
                        }
                      });

                      // Varjyam (Red)
                      panchangData.inauspicious_times?.varjyam?.forEach((period, i) => {
                        const start = getPos(period.start_time);
                        const end = getPos(period.end_time);
                        if (start !== null && end !== null) {
                          blocks.push(<View key={`varjyam-${i}`} style={[styles.qualityBlock, { left: `${start}%`, width: `${end - start}%`, backgroundColor: '#EF4444', opacity: 0.5 }]} />);
                        }
                      });

                      // Current Time Indicator
                      const currentPos = ((now.getTime() - startOfDay.getTime()) / totalMs) * 100;
                      blocks.push(
                        <View key="now" style={[styles.qualityNowIndicator, { left: `${currentPos}%` }]}>
                          <View style={styles.qualityNowDot} />
                          <View style={styles.qualityNowLine} />
                        </View>
                      );

                      return blocks;
                    })()}
                  </View>
                  <View style={styles.qualityLabels}>
                    <Text style={[styles.qualityTimeLabel, { color: colors.textTertiary }]}>00:00</Text>
                    <Text style={[styles.qualityTimeLabel, { color: colors.textTertiary }]}>06:00</Text>
                    <Text style={[styles.qualityTimeLabel, { color: colors.textTertiary }]}>12:00</Text>
                    <Text style={[styles.qualityTimeLabel, { color: colors.textTertiary }]}>18:00</Text>
                    <Text style={[styles.qualityTimeLabel, { color: colors.textTertiary }]}>23:59</Text>
                  </View>
                </View>
                <View style={styles.qualityLegend}>
                  <View style={styles.legendItem}>
                    <View style={[styles.legendDot, { backgroundColor: '#10B981' }]} />
                    <Text style={[styles.legendText, { color: colors.textSecondary }]}>{t('home.panchang.auspicious', 'Auspicious')}</Text>
                  </View>
                  <View style={styles.legendItem}>
                    <View style={[styles.legendDot, { backgroundColor: '#EF4444' }]} />
                    <Text style={[styles.legendText, { color: colors.textSecondary }]}>{t('home.panchang.inauspicious', 'Inauspicious')}</Text>
                  </View>
                </View>

                {/* Detailed Timings List */}
                <View style={styles.detailedTimingsContainer}>
                  {/* Auspicious */}
                  <View style={[styles.timingGroup, theme === 'light' && { backgroundColor: 'rgba(16, 185, 129, 0.08)', borderWidth: 1, borderColor: 'rgba(16, 185, 129, 0.2)' }]}>
                    <View style={styles.timingRow}>
                      <Text style={[styles.timingLabel, { color: colors.textSecondary }]}>{t('home.panchang.brahmaMuhurta', 'Brahma Muhurta')}</Text>
                      <Text style={[styles.timingValue, { color: '#10B981' }]}>
                        {panchangData.brahma_muhurta_start && panchangData.brahma_muhurta_end && 
                         !isNaN(new Date(panchangData.brahma_muhurta_start).getTime()) ? 
                          `${new Date(panchangData.brahma_muhurta_start).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true })} - ${new Date(panchangData.brahma_muhurta_end).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true })}` : 
                          '4:29 AM - 6:05 AM'
                        }
                      </Text>
                    </View>
                    <View style={styles.timingRow}>
                      <Text style={[styles.timingLabel, { color: colors.textSecondary }]}>{t('home.panchang.abhijitMuhurta', 'Abhijit Muhurta')}</Text>
                      <Text style={[styles.timingValue, { color: '#10B981' }]}>
                        {panchangData.abhijit_muhurta_start && panchangData.abhijit_muhurta_end &&
                         !isNaN(new Date(panchangData.abhijit_muhurta_start).getTime()) ? 
                          `${new Date(panchangData.abhijit_muhurta_start).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true })} - ${new Date(panchangData.abhijit_muhurta_end).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true })}` : 
                          '11:36 AM - 12:24 PM'
                        }
                      </Text>
                    </View>
                  </View>

                  {/* Inauspicious */}
                  <View style={[styles.timingGroup, theme === 'light' && { backgroundColor: 'rgba(239, 68, 68, 0.08)', borderWidth: 1, borderColor: 'rgba(239, 68, 68, 0.2)' }]}>
                    {panchangData.rahu_kaal && (
                      <View style={styles.timingRow}>
                        <Text style={[styles.timingLabel, { color: colors.textSecondary }]}>{t('home.panchang.rahuKaal', 'Rahu Kaal')}</Text>
                        <Text style={[styles.timingValue, { color: '#EF4444' }]}>
                          {panchangData.rahu_kaal.rahu_kaal_start && !isNaN(new Date(panchangData.rahu_kaal.rahu_kaal_start).getTime()) ? 
                            `${new Date(panchangData.rahu_kaal.rahu_kaal_start).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true })} - ${new Date(panchangData.rahu_kaal.rahu_kaal_end).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true })}` : 
                            t('common.notAvailable', 'Not available')
                          }
                        </Text>
                      </View>
                    )}
                    {panchangData.inauspicious_times?.varjyam?.map((period, index) => (
                      <View key={`varjyam-list-${index}`} style={styles.timingRow}>
                        <Text style={[styles.timingLabel, { color: colors.textSecondary }]}>{t('home.panchang.varjyam', 'Varjyam')}</Text>
                        <Text style={[styles.timingValue, { color: '#EF4444' }]}>
                          {period.start_time && !isNaN(new Date(period.start_time).getTime()) ? 
                            `${new Date(period.start_time).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true })} - ${new Date(period.end_time).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true })}` : 
                            t('common.notAvailable', 'Not available')
                          }
                        </Text>
                      </View>
                    ))}
                  </View>
                </View>
              </View>
            </View>
          )}

        </View>
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

      {/* Floating Action Button (FAB) - Outside of ScrollView and Gradient to ensure absolute positioning */}
      <Animated.View 
        style={[
          styles.fabContainer, 
          androidLightCardFixStyle,
          { 
            bottom: 90,
            width: fabWidth.interpolate({
              inputRange: [0, 1],
              outputRange: [56, 180], // Icon only vs full width
            })
          }
        ]}
      >
        <TouchableOpacity
          style={[styles.fabButton, androidLightCardFixStyle]}
          onPress={() => onOptionSelect({ action: 'question' })}
          activeOpacity={0.9}
        >
          <AnimatedLinearGradient
            colors={['#FFD700', '#F59E0B']}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 1 }}
            style={[
              styles.fabGradient, 
              {
                paddingHorizontal: fabWidth.interpolate({
                  inputRange: [0, 1],
                  outputRange: [0, 16],
                }),
                justifyContent: 'center'
              }
            ]}
          >
            <Icon name="chatbubbles" size={24} color="#854d0e" />
            <Animated.Text 
              style={[
                styles.fabText, 
                { 
                  color: '#854d0e',
                  opacity: fabWidth,
                  width: fabWidth.interpolate({
                    inputRange: [0, 1],
                    outputRange: [0, 110], // Adjusted width for "Ask AstroRoshni"
                  }),
                  transform: [{
                    translateX: fabWidth.interpolate({
                      inputRange: [0, 1],
                      outputRange: [-20, 0],
                    })
                  }]
                }
              ]} 
              numberOfLines={1}
            >
              {t('home.askFAB', 'Ask AstroRoshni')}
            </Animated.Text>
          </AnimatedLinearGradient>
        </TouchableOpacity>
      </Animated.View>

      {/* Bottom Tabs */}
      <View style={styles.bottomTabs}>
        <LinearGradient
          colors={theme === 'dark' ? ['#f97316', '#ea580c'] : ['#ffffff', '#fff5f0']}
          style={StyleSheet.absoluteFill}
          start={{ x: 0, y: 0 }}
          end={{ x: 0, y: 1 }}
        />
        {Platform.OS === 'ios' && (
          <BlurView intensity={theme === 'dark' ? 20 : 60} style={StyleSheet.absoluteFill} tint={theme === 'dark' ? 'dark' : 'light'} />
        )}
        
        <TouchableOpacity 
          style={styles.tabItem} 
          onPress={() => onOptionSelect({ action: 'question' })}
          activeOpacity={0.7}
        >
          <View style={styles.tabIconContainer}>
            <Icon 
              name="chatbubble-ellipses-outline" 
              size={22} 
              color={activeTab === 'ask' ? (theme === 'dark' ? '#ffffff' : colors.primary) : (theme === 'dark' ? 'rgba(255, 255, 255, 0.7)' : colors.textTertiary)} 
            />
          </View>
          <Text style={[styles.tabLabel, { color: activeTab === 'ask' ? (theme === 'dark' ? '#ffffff' : colors.primary) : (theme === 'dark' ? 'rgba(255, 255, 255, 0.7)' : colors.textTertiary), fontWeight: activeTab === 'ask' ? '800' : '600' }]}>
            {t('home.tabs.ask', 'Ask')}
          </Text>
        </TouchableOpacity>

        <TouchableOpacity 
          style={styles.tabItem} 
          onPress={() => onOptionSelect({ action: 'events' })}
          activeOpacity={0.7}
        >
          <View style={styles.tabIconContainer}>
            <Icon 
              name="calendar-outline" 
              size={22} 
              color={activeTab === 'events' ? (theme === 'dark' ? '#ffffff' : colors.primary) : (theme === 'dark' ? 'rgba(255, 255, 255, 0.7)' : colors.textTertiary)} 
            />
          </View>
          <Text style={[styles.tabLabel, { color: activeTab === 'events' ? (theme === 'dark' ? '#ffffff' : colors.primary) : (theme === 'dark' ? 'rgba(255, 255, 255, 0.7)' : colors.textTertiary), fontWeight: activeTab === 'events' ? '800' : '600' }]}>
            {t('home.tabs.events', 'Events')}
          </Text>
        </TouchableOpacity>

        <TouchableOpacity 
          style={styles.tabItem} 
          onPress={() => navigation.navigate('Chart', { birthData })}
          activeOpacity={0.7}
        >
          <View style={styles.tabIconContainer}>
            <Svg width="22" height="22" viewBox="0 0 48 48">
              {/* Outer square */}
              <Rect x="2" y="2" width="44" height="44" fill="none" stroke={activeTab === 'charts' ? (theme === 'dark' ? '#ffffff' : colors.primary) : (theme === 'dark' ? 'rgba(255, 255, 255, 0.7)' : colors.textTertiary)} strokeWidth="3" />
              {/* Inner diamond */}
              <Polygon points="24,2 46,24 24,46 2,24" fill="none" stroke={activeTab === 'charts' ? '#ffd700' : (theme === 'dark' ? 'rgba(255, 255, 255, 0.7)' : colors.textTertiary)} strokeWidth="2" />
              {/* Diagonal lines creating triangular houses */}
              <Line x1="2" y1="2" x2="46" y2="46" stroke={activeTab === 'charts' ? (theme === 'dark' ? '#ffffff' : colors.primary) : (theme === 'dark' ? 'rgba(255, 255, 255, 0.7)' : colors.textTertiary)} strokeWidth="1.5" />
              <Line x1="46" y1="2" x2="2" y2="46" stroke={activeTab === 'charts' ? (theme === 'dark' ? '#ffffff' : colors.primary) : (theme === 'dark' ? 'rgba(255, 255, 255, 0.7)' : colors.textTertiary)} strokeWidth="1.5" />
            </Svg>
          </View>
          <Text style={[styles.tabLabel, { color: activeTab === 'charts' ? (theme === 'dark' ? '#ffffff' : colors.primary) : (theme === 'dark' ? 'rgba(255, 255, 255, 0.7)' : colors.textTertiary), fontWeight: activeTab === 'charts' ? '800' : '600' }]}>
            {t('home.tabs.charts', 'Charts')}
          </Text>
        </TouchableOpacity>

        <TouchableOpacity 
          style={styles.tabItem} 
          onPress={() => setShowDashaBrowser(true)}
          activeOpacity={0.7}
        >
          <View style={styles.tabIconContainer}>
            <Icon 
              name="time-outline" 
              size={22} 
              color={activeTab === 'dashas' ? (theme === 'dark' ? '#ffffff' : colors.primary) : (theme === 'dark' ? 'rgba(255, 255, 255, 0.7)' : colors.textTertiary)} 
            />
          </View>
          <Text style={[styles.tabLabel, { color: activeTab === 'dashas' ? (theme === 'dark' ? '#ffffff' : colors.primary) : (theme === 'dark' ? 'rgba(255, 255, 255, 0.7)' : colors.textTertiary), fontWeight: activeTab === 'dashas' ? '800' : '600' }]}>
            {t('home.tabs.dashas', 'Dashas')}
          </Text>
        </TouchableOpacity>

        <TouchableOpacity 
          style={styles.tabItem} 
          onPress={() => navigation.navigate('Profile')}
          activeOpacity={0.7}
        >
          <View style={styles.tabIconContainer}>
            <Icon 
              name="person-outline" 
              size={22} 
              color={activeTab === 'you' ? (theme === 'dark' ? '#ffffff' : colors.primary) : (theme === 'dark' ? 'rgba(255, 255, 255, 0.7)' : colors.textTertiary)} 
            />
          </View>
          <Text style={[styles.tabLabel, { color: activeTab === 'you' ? (theme === 'dark' ? '#ffffff' : colors.primary) : (theme === 'dark' ? 'rgba(255, 255, 255, 0.7)' : colors.textTertiary), fontWeight: activeTab === 'you' ? '800' : '600' }]}>
            {t('home.tabs.you', 'You')}
          </Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

// Separate component to avoid hooks order violation
function OptionCard({ option, index, onOptionSelect }) {
  const { theme, colors, androidLightCardFixStyle } = useTheme();
  
  if (!option) return null;
  const gradientColors = option.id === 'events' 
    ? ['#FFD700', '#FF8C00'] 
    : option.id === 'ashtakvarga'
    ? ['#9C27B0', '#E91E63']
    : ['#ff6b35', '#ff8c5a'];
  
  return (
    <View 
      style={[styles.optionCard, androidLightCardFixStyle]}
    >
      <TouchableOpacity
        onPress={() => onOptionSelect(option)}
        activeOpacity={0.9}
      >
        <LinearGradient
          colors={theme === 'dark' 
            ? ['rgba(255, 255, 255, 0.15)', 'rgba(255, 255, 255, 0.05)']
            : ['rgba(251, 146, 60, 0.2)', 'rgba(249, 115, 22, 0.1)']}
          style={[styles.optionGradient, androidLightCardFixStyle]}
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
    </View>
  );
}

// Life Analysis Card - Bento Grid Layout
function LifeAnalysisCard({ option, index, onOptionSelect }) {
  const { colors, theme } = useTheme();
  
  const isLarge = option && (option.id === 'career' || option.id === 'wealth');
  const isWide = option && (option.id === 'marriage' || option.id === 'progeny');
  
  if (!option) return null;
  
  return (
    <View 
      style={[
        styles.lifeAnalysisCard,
        isLarge && styles.lifeAnalysisCardLarge,
        isWide && styles.lifeAnalysisCardWide,
      ]}
    >
      <TouchableOpacity
        onPress={() => onOptionSelect({ action: 'analysis', type: option.id })}
        activeOpacity={0.9}
      >
        <LinearGradient
          colors={option.gradient}
          style={[
            styles.lifeAnalysisGradient,
            isLarge && styles.lifeAnalysisGradientLarge,
            isWide && styles.lifeAnalysisGradientWide,
          ]}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
        >
          {/* Icon Glow Effect */}
          <View style={styles.iconGlow} />
          
          {option.cost > 0 && (
            <View style={styles.costBadge}>
              <Icon name="flash" size={8} color="#854d0e" />
              <Text style={styles.costText}>{option.cost}</Text>
            </View>
          )}

          <View style={[
            styles.lifeAnalysisContent,
            isWide && styles.lifeAnalysisContentWide
          ]}>
            <Text style={[
              styles.lifeAnalysisEmoji,
              isLarge && styles.lifeAnalysisEmojiLarge
            ]}>
              {option.icon}
            </Text>
            
            <View style={isWide ? styles.lifeAnalysisTextWide : styles.lifeAnalysisTextNormal}>
              <Text style={[
                styles.lifeAnalysisTitle,
                isLarge && styles.lifeAnalysisTitleLarge,
                isWide && styles.lifeAnalysisTitleWide
              ]}>
                {option.title}
              </Text>
              
              <Text 
                style={[
                  styles.lifeAnalysisDescription,
                  isLarge && styles.lifeAnalysisDescriptionLarge,
                  isWide && styles.lifeAnalysisDescriptionWide
                ]} 
                numberOfLines={isLarge ? 3 : 2}
              >
                {option.description}
              </Text>
            </View>
          </View>
        </LinearGradient>
      </TouchableOpacity>
    </View>
  );
}

// Premium Cosmic Ribbon Card for Timing Planners
function CosmicRibbonCard({ option, index, onOptionSelect }) {
  const { theme, colors, androidLightCardFixStyle } = useTheme();
  
  if (!option) return null;
  
  const cardWidth = width * 0.72;
  
  return (
    <View style={[styles.ribbonCardWrapper, androidLightCardFixStyle, { width: cardWidth }]}>
      <TouchableOpacity
        onPress={() => {
          if (option.id === 'muhurat') {
            onOptionSelect({ action: 'muhurat' });
          } else {
            onOptionSelect({ action: 'analysis', type: option.id });
          }
        }}
        activeOpacity={0.9}
        style={styles.ribbonCardTouch}
      >
        <View style={[
          styles.ribbonGlassmorphism,
          androidLightCardFixStyle,
          {
            backgroundColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.08)' : 'rgba(255, 255, 255, 0.7)',
            borderColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.15)' : 'rgba(249, 115, 22, 0.2)',
          }
        ]}>
          <View style={styles.ribbonContent}>
            <View style={[styles.ribbonIconContainer, { backgroundColor: (option.gradient?.[0] || colors.primary) + '15' }]}>
              <Text style={styles.ribbonEmoji}>{option.icon}</Text>
            </View>
            
            <View style={styles.ribbonTextContainer}>
              <Text style={[styles.ribbonTitle, { color: colors.text }]}>{option.title}</Text>
              <Text style={[styles.ribbonDescription, { color: colors.textSecondary }]} numberOfLines={2}>
                {option.description}
              </Text>
            </View>
            
            <View style={styles.ribbonActionContainer}>
              <Icon name="chevron-forward" size={18} color={colors.textTertiary} />
            </View>
          </View>
        </View>
      </TouchableOpacity>
    </View>
  );
}

// Full width Analysis Card for Timing Planners
function AnalysisCard({ option, index, onOptionSelect }) {
  const { theme, colors, androidLightCardFixStyle } = useTheme();
  
  if (!option) return null;
  return (
    <View
      style={[styles.analysisCard, androidLightCardFixStyle]}
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
          androidLightCardFixStyle,
          {
            backgroundColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.1)' : colors.surface,
            borderColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.2)' : colors.cardBorder,
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
    </View>
  );
}

function SignCard({ type, signIndex, colors, label, icon, loading, onPress }) {
  const { t } = useTranslation();
  const getSignIcon = (signNumber) => {
    if (signNumber === undefined || signNumber === null) return '⭐';
    const icons = {
      0: '♈', 1: '♉', 2: '♊', 3: '♋',
      4: '♌', 5: '♍', 6: '♎', 7: '♏',
      8: '♐', 9: '♑', 10: '♒', 11: '♓'
    };
    return icons[signNumber] || '⭐';
  };
  
  const getSignName = (signNumber) => {
    if (signNumber === undefined || signNumber === null) return t('common.unknown', 'Unknown');
    const signs = {
      0: 'Aries', 1: 'Taurus', 2: 'Gemini', 3: 'Cancer',
      4: 'Leo', 5: 'Virgo', 6: 'Libra', 7: 'Scorpio',
      8: 'Sagittarius', 9: 'Capricorn', 10: 'Aquarius', 11: 'Pisces'
    };
    const signName = signs[signNumber] || signNumber;
    return t(`signs.${signName}`, signName);
  };

  return (
    <TouchableOpacity 
      style={styles.signCard}
      onPress={onPress}
      activeOpacity={0.85}
    >
      <LinearGradient colors={colors} style={styles.signGradient}>
        <Text style={styles.signEmoji}>{icon}</Text>
        <Text style={styles.signLabel}>{label}</Text>
        <Text style={styles.signValue}>
          {signIndex !== undefined ? `${getSignIcon(signIndex)} ${getSignName(signIndex)}` : loading ? '...' : 'N/A'}
        </Text>
        <View style={styles.signCardGlow} />
      </LinearGradient>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  // Header Dashboard
  header: {
    marginBottom: 24,
    zIndex: 10,
    marginTop: Platform.OS === 'ios' ? 0 : 10,
  },
  headerDashboard: {
    borderRadius: 24,
    padding: 16,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.2)',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 12,
    elevation: 5,
  },
  headerTopRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  headerProfileInfo: {
    flex: 1,
  },
  headerGreeting: {
    fontSize: 12,
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 1,
    marginBottom: 2,
  },
  headerName: {
    fontSize: 20,
    fontWeight: '800',
  },
  headerNativeChip: {
    backgroundColor: 'rgba(255, 107, 53, 0.15)',
    borderColor: 'rgba(255, 107, 53, 0.3)',
    paddingVertical: 4,
    paddingHorizontal: 10,
  },
  headerBigThree: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    borderRadius: 16,
    padding: 12,
  },
  headerSignItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  headerSignIcon: {
    width: 32,
    height: 32,
    borderRadius: 16,
    justifyContent: 'center',
    alignItems: 'center',
  },
  headerSignEmoji: {
    fontSize: 16,
  },
  headerSignLabel: {
    fontSize: 9,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  headerSignName: {
    fontSize: 12,
    fontWeight: '700',
  },
  headerDivider: {
    width: 1,
    height: 24,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
  },
  
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
    paddingTop: 10,
    paddingBottom: 40,
  },
  star: {
    position: 'absolute',
  },
  starText: {
    fontSize: 12,
  },
  optionsContainer: {
    marginBottom: 30,
  },
  optionsTitle: {
    fontSize: 18,
    fontWeight: '800',
    textAlign: 'left',
    marginBottom: 16,
    textTransform: 'uppercase',
    letterSpacing: 1,
    paddingHorizontal: 4,
  },
  optionCard: {
    marginBottom: 16,
    borderRadius: 20,
    overflow: 'hidden',
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.2,
        shadowRadius: 8,
      },
      android: {
        elevation: 4,
      },
    }),
  },
  optionGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 20,
    borderWidth: 1,
    ...Platform.select({
      ios: {
        borderColor: 'rgba(255, 255, 255, 0.2)',
      },
      android: {
        borderColor: 'rgba(255, 255, 255, 0.3)',
      },
    }),
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
    borderRadius: 16,
    borderWidth: 1,
    ...Platform.select({
      ios: {
        backgroundColor: 'rgba(255, 255, 255, 0.1)',
        borderColor: 'rgba(255, 255, 255, 0.2)',
      },
      android: {
        backgroundColor: 'rgba(255, 255, 255, 0.15)',
        borderColor: 'rgba(255, 255, 255, 0.3)',
      },
    }),
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
    fontSize: 18,
    fontWeight: '800',
    textAlign: 'left',
    marginBottom: 16,
    textTransform: 'uppercase',
    letterSpacing: 1,
    paddingHorizontal: 4,
  },
  analysisCard: {
    marginBottom: 16,
    borderRadius: 20,
    overflow: 'hidden',
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.2,
        shadowRadius: 8,
      },
      android: {
        elevation: 4,
      },
    }),
  },
  analysisGlassmorphism: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 20,
    borderRadius: 20,
    ...Platform.select({
      ios: {
        backgroundColor: 'rgba(255, 255, 255, 0.1)',
        borderColor: 'rgba(255, 255, 255, 0.2)',
      },
      android: {
        backgroundColor: 'rgba(255, 255, 255, 0.15)',
        borderColor: 'rgba(255, 255, 255, 0.3)',
      },
    }),
    borderWidth: 1,
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
  lifeAnalysisGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    paddingHorizontal: 4,
  },
  lifeAnalysisCard: {
    width: '48%',
    marginBottom: 12,
    borderRadius: 24,
    overflow: 'hidden',
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.2,
        shadowRadius: 8,
      },
      android: {
        elevation: 4,
      },
    }),
  },
  lifeAnalysisCardLarge: {
    width: '48%',
    height: 220,
  },
  lifeAnalysisCardWide: {
    width: '100%',
    height: 130,
  },
  lifeAnalysisGradient: {
    padding: 16,
    alignItems: 'center',
    justifyContent: 'center',
    height: 160,
  },
  lifeAnalysisGradientLarge: {
    height: 220,
    justifyContent: 'flex-end',
    alignItems: 'flex-start',
    padding: 20,
  },
  lifeAnalysisGradientWide: {
    height: 130,
    flexDirection: 'row',
    justifyContent: 'flex-start',
    alignItems: 'center',
    padding: 20,
  },
  lifeAnalysisContent: {
    alignItems: 'center',
    width: '100%',
    paddingTop: 4,
  },
  lifeAnalysisContentWide: {
    flexDirection: 'row',
    alignItems: 'center',
    width: '100%',
    paddingTop: 0,
  },
  lifeAnalysisTextNormal: {
    alignItems: 'center',
    width: '100%',
  },
  lifeAnalysisTextWide: {
    flex: 1,
    marginLeft: 16,
    alignItems: 'flex-start',
  },
  lifeAnalysisEmoji: {
    fontSize: 32,
    marginBottom: 12,
    textAlign: 'center',
    includeFontPadding: false,
    textAlignVertical: 'center',
    lineHeight: 40,
  },
  lifeAnalysisEmojiLarge: {
    fontSize: 48,
    marginBottom: 16,
    textAlign: 'left',
    lineHeight: 56,
  },
  lifeAnalysisTitle: {
    fontSize: 14,
    fontWeight: '800',
    marginBottom: 6,
    textAlign: 'center',
    lineHeight: 18,
    color: '#ffffff',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  lifeAnalysisTitleLarge: {
    fontSize: 18,
    textAlign: 'left',
  },
  lifeAnalysisTitleWide: {
    fontSize: 16,
    textAlign: 'left',
    marginBottom: 4,
  },
  lifeAnalysisDescription: {
    fontSize: 11,
    textAlign: 'center',
    lineHeight: 14,
    paddingHorizontal: 4,
    color: 'rgba(255, 255, 255, 0.9)',
    fontWeight: '500',
  },
  lifeAnalysisDescriptionLarge: {
    textAlign: 'left',
    fontSize: 13,
    lineHeight: 18,
    paddingHorizontal: 0,
  },
  lifeAnalysisDescriptionWide: {
    textAlign: 'left',
    fontSize: 12,
    lineHeight: 16,
    paddingHorizontal: 0,
  },
  costBadge: {
    position: 'absolute',
    top: 8,
    right: 8,
    backgroundColor: 'rgba(255, 215, 0, 0.95)',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 10,
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#fff',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    elevation: 3,
  },
  costText: {
    fontSize: 9,
    fontWeight: '800',
    color: '#854d0e',
    marginLeft: 2,
  },
  iconGlow: {
    position: 'absolute',
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    zIndex: -1,
  },
  // Dashboard Cards Styles
  dashboardContainer: {
    marginBottom: 30,
  },
  dashboardTitle: {
    fontSize: 18,
    fontWeight: '800',
    textAlign: 'left',
    marginBottom: 16,
    textTransform: 'uppercase',
    letterSpacing: 1,
    paddingHorizontal: 4,
  },
  dashboardCard: {
    marginBottom: 16,
    borderRadius: 20,
    overflow: 'hidden',
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 6 },
        shadowOpacity: 0.3,
        shadowRadius: 12,
      },
      android: {
        elevation: 6,
      },
    }),
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
    fontWeight: '800',
    marginBottom: 16,
    paddingHorizontal: 4,
    textAlign: 'left',
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  dashaChip: {
    borderWidth: 1.5,
    borderRadius: 16,
    paddingHorizontal: 10,
    paddingVertical: 10,
    alignItems: 'center',
    marginRight: 8,
    width: 110,
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
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.3,
        shadowRadius: 8,
      },
      android: {
        elevation: 4,
      },
    }),
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
  signCardGlow: {
    position: 'absolute',
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: 'rgba(255, 255, 255, 0.15)',
    zIndex: -1,
    top: '10%',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.6)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  insightModalContent: {
    width: '90%',
    maxWidth: 400,
    borderRadius: 24,
    overflow: 'hidden',
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 10 },
        shadowOpacity: 0.3,
        shadowRadius: 20,
      },
      android: {
        elevation: 10,
      },
    }),
  },
  insightGradient: {
    padding: 24,
    borderRadius: 24,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
  },
  insightHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
    gap: 12,
  },
  insightEmoji: {
    fontSize: 32,
  },
  insightTitle: {
    fontSize: 18,
    fontWeight: '800',
    color: '#ff6b35',
    flex: 1,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  insightDescription: {
    fontSize: 15,
    lineHeight: 22,
    marginBottom: 24,
  },
  insightCloseButton: {
    backgroundColor: '#ff6b35',
    paddingHorizontal: 32,
    paddingVertical: 12,
    borderRadius: 25,
    alignSelf: 'center',
    ...Platform.select({
      ios: {
        shadowColor: '#ff6b35',
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.3,
        shadowRadius: 8,
      },
      android: {
        elevation: 4,
      },
    }),
  },
  insightCloseText: {
    color: 'white',
    fontSize: 14,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  
  // Astrology Tools Section
  toolsSection: {
    marginBottom: 24,
  },
  toolsSectionTitle: {
    fontSize: 18,
    fontWeight: '800',
    marginBottom: 16,
    paddingHorizontal: 4,
    textAlign: 'left',
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  toolsGrid: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 8,
  },
  toolsScrollContent: {
    paddingHorizontal: 4,
    gap: 12,
  },
  toolCard: {
    width: width * 0.26,
    borderRadius: 16,
    overflow: 'hidden',
  },
  toolGlassmorphism: {
    padding: 10,
    alignItems: 'center',
    minHeight: 80,
    maxHeight: 80,
    justifyContent: 'center',
    ...Platform.select({
      ios: {
        backgroundColor: 'rgba(255, 255, 255, 0.1)',
        borderColor: 'rgba(255, 255, 255, 0.2)',
      },
      android: {
        backgroundColor: 'rgba(255, 255, 255, 0.15)',
        borderColor: 'rgba(255, 255, 255, 0.3)',
      },
    }),
    borderWidth: 1,
  },
  toolEmoji: {
    fontSize: 24,
    marginBottom: 4,
  },
  toolTitle: {
    fontSize: 10,
    fontWeight: '700',
    textAlign: 'center',
    marginTop: 2,
    lineHeight: 12,
  },
  toolIconContainer: {
    width: 36,
    height: 36,
    justifyContent: 'center',
    alignItems: 'center',
    position: 'relative',
    marginBottom: 2,
  },
  toolIconGlow: {
    position: 'absolute',
    width: 24,
    height: 24,
    borderRadius: 12,
    opacity: 0.15,
    zIndex: -1,
  },
  toolMiniStat: {
    position: 'absolute',
    top: 4,
    right: 4,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    paddingHorizontal: 4,
    paddingVertical: 1,
    borderRadius: 6,
  },
  toolMiniStatText: {
    fontSize: 8,
    fontWeight: '800',
    color: 'rgba(255, 255, 255, 0.6)',
    textTransform: 'uppercase',
  },
  planetarySection: {
    marginBottom: 30,
    borderRadius: 24,
    padding: 20,
    borderWidth: 1,
    ...Platform.select({
      ios: {
        backgroundColor: 'rgba(255, 255, 255, 0.02)',
        borderColor: 'rgba(255, 255, 255, 0.05)',
      },
      android: {
        backgroundColor: 'rgba(0, 0, 0, 0.2)',
        borderColor: 'rgba(255, 255, 255, 0.1)',
      },
    }),
  },
  planetaryHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
    width: '100%',
    paddingRight: 4,
  },
  planetarySectionTitle: {
    fontSize: 18,
    fontWeight: '800',
    textTransform: 'uppercase',
    letterSpacing: 1,
    flexShrink: 1,
    marginRight: 8,
  },
  planetaryHeaderRight: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  cosmicRingChip: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 14,
    gap: 4,
  },
  cosmicRingChipDark: {
    backgroundColor: 'rgba(56, 189, 248, 0.15)',
  },
  cosmicRingChipLight: {
    backgroundColor: 'rgba(56, 189, 248, 0.2)',
  },
  cosmicRingChipText: {
    fontSize: 12,
    fontWeight: '700',
  },
  miniZodiacContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 24,
    padding: 16,
    borderRadius: 20,
    ...Platform.select({
      ios: {
        backgroundColor: 'rgba(255, 255, 255, 0.03)',
      },
      android: {
        backgroundColor: 'rgba(255, 255, 255, 0.05)',
      },
    }),
  },
  zodiacWheelWrapper: {
    position: 'relative',
    width: 160,
    height: 160,
    justifyContent: 'center',
    alignItems: 'center',
  },
  zodiacCenterGlow: {
    position: 'absolute',
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: 'rgba(255, 255, 255, 0.15)',
    ...Platform.select({
      ios: {
        shadowColor: '#FFFFFF',
        shadowOffset: { width: 0, height: 0 },
        shadowOpacity: 0.8,
        shadowRadius: 25,
      },
      android: {
        elevation: 10,
      },
    }),
    zIndex: -1,
  },
  zodiacSummary: {
    flex: 1,
    marginLeft: 20,
  },
  zodiacSummaryTitle: {
    fontSize: 12,
    fontWeight: '600',
    marginBottom: 4,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  zodiacSummaryText: {
    fontSize: 16,
    fontWeight: '800',
    marginBottom: 12,
  },
  alignmentBarContainer: {
    height: 4,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 2,
    overflow: 'hidden',
  },
  alignmentBar: {
    height: '100%',
    borderRadius: 2,
  },
  transitScrollContent: {
    paddingRight: 20,
    gap: 12,
  },
  transitCard: {
    width: 130,
    padding: 16,
    borderRadius: 20,
    borderWidth: 1,
  },
  transitCardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  transitPlanetIcon: {
    fontSize: 24,
  },
  transitMainInfo: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  statusBadges: {
    flexDirection: 'row',
    gap: 4,
  },
  statusBadge: {
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 6,
  },
  statusBadgeText: {
    fontSize: 8,
    fontWeight: '900',
    textTransform: 'uppercase',
  },
  transitPlanetName: {
    fontSize: 14,
    fontWeight: '800',
  },
  transitSignRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  transitSignIcon: {
    fontSize: 14,
  },
  transitSignName: {
    fontSize: 12,
    fontWeight: '600',
  },
  vibeTag: {
    backgroundColor: 'rgba(255, 255, 255, 0.08)',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
  },
  vibeTagText: {
    fontSize: 9,
    fontWeight: '700',
    textTransform: 'uppercase',
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
    borderRadius: 24,
    padding: 24,
    ...Platform.select({
      ios: {
        borderWidth: 1,
        backgroundColor: 'rgba(255, 255, 255, 0.1)',
        borderColor: 'rgba(255, 255, 255, 0.2)',
      },
      android: {
        borderWidth: StyleSheet.hairlineWidth,
        backgroundColor: 'rgba(0, 0, 0, 0.4)',
        borderColor: 'rgba(255, 255, 255, 0.15)',
      },
    }),
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 0.3,
    shadowRadius: 20,
    elevation: 5,
  },
  panchangTitle: {
    fontSize: 18,
    fontWeight: '800',
    textAlign: 'left',
    marginBottom: 16,
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  panchangTitleUnderline: {
    width: 40,
    height: 3,
    backgroundColor: '#ff6b35',
    borderRadius: 2,
    alignSelf: 'flex-start',
    marginBottom: 24,
  },
  sunTimesRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 20,
    gap: 12,
  },
  sunTimeItem: {
    flex: 1,
    alignItems: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    padding: 12,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
  },
  sunTimeEmoji: {
    fontSize: 24,
    marginBottom: 6,
  },
  sunTimeLabel: {
    fontSize: 10,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 4,
  },
  sunTimeValue: {
    fontSize: 13,
    fontWeight: '800',
  },
  dayProgressBar: {
    alignItems: 'center',
    marginVertical: 24,
    paddingHorizontal: 10,
  },
  progressTrack: {
    width: '100%',
    height: 4,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 2,
    position: 'relative',
    marginBottom: 12,
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#ff6b35',
    borderRadius: 2,
  },
  currentTimeDot: {
    position: 'absolute',
    top: -8,
    width: 20,
    height: 20,
    borderRadius: 10,
    backgroundColor: '#ff6b35',
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#ff6b35',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.8,
    shadowRadius: 6,
    elevation: 4,
  },
  progressLabel: {
    fontSize: 10,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  panchangElementsSection: {
    marginBottom: 24,
  },
  panchangElementsTitle: {
    fontSize: 14,
    fontWeight: '800',
    textAlign: 'center',
    marginBottom: 16,
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  panchangElementGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    gap: 8,
  },
  panchangElement: {
    width: '48%',
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    padding: 12,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
    marginBottom: 8,
  },
  elementLabel: {
    fontSize: 9,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 4,
  },
  elementValue: {
    fontSize: 13,
    fontWeight: '800',
  },
  muhurtaSection: {
    marginTop: 8,
    marginBottom: 16,
    backgroundColor: 'rgba(16, 185, 129, 0.08)',
    borderRadius: 20,
    padding: 20,
    borderWidth: 1,
    borderColor: 'rgba(16, 185, 129, 0.2)',
  },
  muhurtaTitle: {
    fontSize: 14,
    fontWeight: '800',
    color: '#10B981',
    textAlign: 'center',
    marginBottom: 16,
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  muhurtaRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 10,
    paddingHorizontal: 12,
    marginBottom: 8,
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    borderRadius: 12,
  },
  muhurtaLabel: {
    fontSize: 11,
    fontWeight: '600',
  },
  muhurtaTime: {
    fontSize: 12,
    fontWeight: '800',
    color: '#10B981',
  },
  inauspiciousSection: {
    marginTop: 8,
    marginBottom: 8,
    backgroundColor: 'rgba(239, 68, 68, 0.08)',
    borderRadius: 20,
    padding: 20,
    borderWidth: 1,
    borderColor: 'rgba(239, 68, 68, 0.2)',
  },
  inauspiciousTitle: {
    fontSize: 14,
    fontWeight: '800',
    color: '#EF4444',
    textAlign: 'center',
    marginBottom: 16,
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  inauspiciousTime: {
    fontSize: 12,
    fontWeight: '800',
    color: '#EF4444',
  },
  moonPhaseTextRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
    paddingHorizontal: 4,
  },
  moonSvgRow: {
    alignItems: 'center',
    marginBottom: 24,
  },
  moonPhaseText: {
    fontSize: 15,
    fontWeight: '800',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  moonIllumination: {
    fontSize: 13,
    fontWeight: '700',
  },
  // New Panchang Styles
  moonSectionRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 24,
    gap: 20,
  },
  moonSvgContainer: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: '#000',
    justifyContent: 'center',
    alignItems: 'center',
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.1)',
  },
  starlightContainer: {
    position: 'absolute',
    width: '100%',
    height: '100%',
  },
  moonInfoContainer: {
    flex: 1,
  },
  moonElementRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginTop: 8,
  },
  moonElementText: {
    fontSize: 12,
    fontWeight: '600',
  },
  dayQualityContainer: {
    marginTop: 10,
    marginBottom: 20,
  },
  dayQualityTitle: {
    fontSize: 14,
    fontWeight: '800',
    textTransform: 'uppercase',
    letterSpacing: 1,
    marginBottom: 16,
  },
  qualityTimelineWrapper: {
    marginBottom: 16,
  },
  qualityTimelineTrack: {
    height: 12,
    backgroundColor: 'rgba(255,255,255,0.05)',
    borderRadius: 6,
    position: 'relative',
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.1)',
  },
  qualityBlock: {
    position: 'absolute',
    height: '100%',
    borderRadius: 2,
  },
  qualityNowIndicator: {
    position: 'absolute',
    height: '100%',
    alignItems: 'center',
    zIndex: 10,
  },
  qualityNowDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#fff',
    borderWidth: 2,
    borderColor: '#ff6b35',
    marginTop: 2,
  },
  qualityNowLine: {
    width: 2,
    flex: 1,
    backgroundColor: 'rgba(255,255,255,0.5)',
  },
  qualityLabels: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 8,
  },
  qualityTimeLabel: {
    fontSize: 9,
    fontWeight: '600',
  },
  qualityLegend: {
    flexDirection: 'row',
    gap: 16,
    justifyContent: 'center',
  },
  legendItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  legendDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  legendText: {
    fontSize: 10,
    fontWeight: '700',
  },
  detailedTimingsContainer: {
    marginTop: 20,
    gap: 12,
  },
  timingGroup: {
    backgroundColor: 'rgba(255, 255, 255, 0.03)',
    borderRadius: 16,
    padding: 12,
    gap: 8,
  },
  timingRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  timingLabel: {
    fontSize: 11,
    fontWeight: '600',
  },
  timingValue: {
    fontSize: 11,
    fontWeight: '800',
  },
  
  // Header Styles
  header_old: {
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
  panchangWeatherTitle: {
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
  // Ticker Styles
  tickerContainer: {
    marginBottom: 24,
    backgroundColor: 'rgba(255, 255, 255, 0.03)',
    borderRadius: 16,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.08)',
    overflow: 'hidden',
  },
  tickerContent: {
    paddingVertical: 12,
    paddingHorizontal: 16,
    alignItems: 'center',
  },
  tickerItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginRight: 16,
  },
  tickerItemInfoIcon: {
    marginLeft: 6,
  },
  tickerIconContainer: {
    width: 28,
    height: 28,
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 10,
  },
  tickerLabel: {
    fontSize: 9,
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 2,
  },
  tickerValue: {
    fontSize: 12,
    fontWeight: '700',
  },
  tickerSeparator: {
    width: 1,
    height: 24,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    marginRight: 16,
  },
  tickerLoading: {
    fontSize: 12,
    fontStyle: 'italic',
  },
  // FAB Styles
  fabContainer: {
    position: 'absolute',
    right: 20,
    zIndex: 1000,
    height: 56,
    ...Platform.select({
      ios: {
        shadowColor: '#F59E0B',
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.3,
        shadowRadius: 8,
      },
      android: {
        elevation: 8,
      },
    }),
  },
  fabButton: {
    width: '100%',
    height: '100%',
    borderRadius: 28,
    overflow: 'hidden',
  },
  fabGradient: {
    width: '100%',
    height: '100%',
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    borderRadius: 28,
  },
  fabText: {
    color: '#854d0e',
    fontSize: 14,
    fontWeight: '800',
    marginLeft: 8,
  },
  // Dasha Timeline Styles
  dashaTimelineContainer: {
    marginBottom: 30,
    borderRadius: 24,
    padding: 20,
    borderWidth: 1,
    ...Platform.select({
      ios: {
        backgroundColor: 'rgba(255, 255, 255, 0.03)',
        borderColor: 'rgba(255, 255, 255, 0.08)',
      },
      android: {
        backgroundColor: 'rgba(255, 255, 255, 0.05)',
        borderColor: 'rgba(255, 255, 255, 0.12)',
      },
    }),
  },
  dashaSectionTitle: {
    fontSize: 18,
    fontWeight: '800',
    marginBottom: 20,
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  timelineWrapper: {
    gap: 16,
  },
  timelineRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  timelineLeft: {
    alignItems: 'center',
    width: 40,
    marginRight: 12,
  },
  levelBadge: {
    width: 32,
    height: 32,
    borderRadius: 16,
    justifyContent: 'center',
    alignItems: 'center',
  },
  levelText: {
    fontSize: 10,
    fontWeight: '800',
  },
  timelineConnector: {
    width: 2,
    height: 40,
    marginTop: 4,
  },
  timelineContent: {
    flex: 1,
    paddingTop: 4,
  },
  timelineHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  timelinePlanet: {
    fontSize: 16,
    fontWeight: '800',
  },
  timelineDate: {
    fontSize: 11,
    fontWeight: '600',
  },
  progressContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  progressBar: {
    flex: 1,
    height: 6,
    borderRadius: 3,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    borderRadius: 3,
  },
  progressPercent: {
    fontSize: 10,
    fontWeight: '700',
    width: 30,
  },
  // Cosmic Ribbon Styles
  ribbonContainer: {
    marginBottom: 32,
  },
  ribbonScrollContent: {
    paddingHorizontal: 20,
    paddingBottom: 16,
    gap: 16,
  },
  ribbonCardWrapper: {
    height: 100,
    borderRadius: 20,
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.1,
        shadowRadius: 8,
      },
      android: {
        elevation: 4,
      },
    }),
  },
  ribbonCardTouch: {
    flex: 1,
    borderRadius: 20,
    overflow: 'hidden',
  },
  ribbonGlassmorphism: {
    flex: 1,
    padding: 16,
    justifyContent: 'center',
    borderWidth: 1,
    borderRadius: 20,
  },
  ribbonContent: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  ribbonIconContainer: {
    width: 48,
    height: 48,
    borderRadius: 14,
    justifyContent: 'center',
    alignItems: 'center',
  },
  ribbonEmoji: {
    fontSize: 24,
  },
  ribbonTextContainer: {
    flex: 1,
  },
  ribbonTitle: {
    fontSize: 16,
    fontWeight: '800',
    marginBottom: 2,
    letterSpacing: 0.3,
  },
  ribbonDescription: {
    fontSize: 11,
    lineHeight: 15,
    fontWeight: '500',
  },
  ribbonActionContainer: {
    width: 28,
    height: 28,
    borderRadius: 14,
    justifyContent: 'center',
    alignItems: 'center',
  },
  // Bottom Tabs Styles
  bottomTabs: {
    flexDirection: 'row',
    height: 75,
    paddingBottom: 20,
    paddingTop: 8,
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    zIndex: 10000,
    overflow: 'hidden',
  },
  tabItem: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  tabIconContainer: {
    width: 42,
    height: 28,
    borderRadius: 14,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 4,
  },
  tabLabel: {
    fontSize: 11,
    marginTop: 2,
    letterSpacing: 0.3,
  },
});