import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Pressable,
  ActivityIndicator,
  StatusBar,
  Animated,
  Dimensions,
  Platform,
  Image,
  Alert,
  Modal,
  PanResponder,
} from 'react-native';
import { PanGestureHandler, State, GestureHandlerRootView, ScrollView } from 'react-native-gesture-handler';
import { BlurView } from 'expo-blur';
import { Audio, Video, ResizeMode } from 'expo-av';
import { SafeAreaView, useSafeAreaInsets } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import Ionicons from '@expo/vector-icons/Ionicons';

import { captureRef } from 'react-native-view-shot';
import * as Sharing from 'expo-sharing';

import { COLORS } from '../../utils/constants';
import { storage } from '../../services/storage';
import { chartAPI } from '../../services/api';
import { chartPreloader } from '../../services/chartPreloader';
import ChartWidget from './ChartWidget';
import CascadingDashaBrowser from '../Dasha/CascadingDashaBrowser';
import NativeSelectorChip from '../Common/NativeSelectorChip';
import { useTheme } from '../../context/ThemeContext';
import { useTranslation } from 'react-i18next';
import { useAnalytics } from '../../hooks/useAnalytics';
import { getGrahaDrishtiToHouseSign } from '../../utils/grahaDrishti';
import { calculateGandantaLocal, getGandantaHouseMatches } from '../../utils/gandanta';

const { width, height } = Dimensions.get('window');
export default function ChartScreen({ navigation, route, onHeaderStateChange }) {
  const { t } = useTranslation();
  useAnalytics('ChartScreen');
  const { theme, colors } = useTheme();
  const insets = useSafeAreaInsets();
  const embedded = !!route?.params?.embedded;
  const [birthData, setBirthData] = useState(null);
  const [chartData, setChartData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showDashaBrowser, setShowDashaBrowser] = useState(false);
  const [currentChartIndex, setCurrentChartIndex] = useState(0);
  const bottomNavScrollRef = useRef(null);
  const lastSwipeTime = useRef(0);
  const chartWidgetRef = useRef(null);
  const captureViewRef = useRef(null);
  const rotateAnim = useRef(new Animated.Value(0)).current;
  const currentChartIndexRef = useRef(0);

  useEffect(() => {
    currentChartIndexRef.current = currentChartIndex;
  }, [currentChartIndex]);
  
  // House Drawer State
  const [selectedHouse, setSelectedHouse] = useState(null);
  const [isSharing, setIsSharing] = useState(false);
  const [houseInsight, setHouseInsight] = useState(null);
  const [houseInsightLoading, setHouseInsightLoading] = useState(false);
  const [mudakkuAnalysis, setMudakkuAnalysis] = useState(null);
  const [gandantaAnalysis, setGandantaAnalysis] = useState(null);
  const [showGuidePlayer, setShowGuidePlayer] = useState(false);
  const [guidePlayerStatus, setGuidePlayerStatus] = useState('idle');
  const [chartGuideVideoUrl, setChartGuideVideoUrl] = useState(route.params?.chartGuideVideoUrl || '');
  const drawerAnim = useRef(new Animated.Value(height)).current;
  const houseInsightRequestKeyRef = useRef(null);

  // Animation for smooth chart transitions
  const chartTranslateX = useRef(new Animated.Value(0)).current;
  const chartOpacity = useRef(new Animated.Value(1)).current;
  
  const chartTypes = [
    { id: 'lagna', name: t('chartTypes.lagna.name'), icon: '🏠', description: t('chartTypes.lagna.description') },
    { id: 'navamsa', name: t('chartTypes.navamsa.name'), icon: '💎', description: t('chartTypes.navamsa.description') },
    { id: 'transit', name: t('chartTypes.transit.name'), icon: '🪐', description: t('chartTypes.transit.description') },
    { id: 'karkamsa', name: t('chartTypes.karkamsa.name'), icon: '🎯', description: t('chartTypes.karkamsa.description') },
    { id: 'swamsa', name: t('chartTypes.swamsa.name'), icon: '🕉️', description: t('chartTypes.swamsa.description') },
    { id: 'hora', name: t('chartTypes.hora.name'), icon: '💰', description: t('chartTypes.hora.description') },
    { id: 'drekkana', name: t('chartTypes.drekkana.name'), icon: '👫', description: t('chartTypes.drekkana.description') },
    { id: 'chaturthamsa', name: t('chartTypes.chaturthamsa.name'), icon: '🏡', description: t('chartTypes.chaturthamsa.description') },
    { id: 'dashamsa', name: t('chartTypes.dashamsa.name'), icon: '💼', description: t('chartTypes.dashamsa.description') },
    { id: 'dwadashamsa', name: t('chartTypes.dwadashamsa.name'), icon: '👨👩👧👦', description: t('chartTypes.dwadashamsa.description') },
    { id: 'shodamsa', name: t('chartTypes.shodamsa.name'), icon: '🚗', description: t('chartTypes.shodamsa.description') },
    { id: 'vimsamsa', name: t('chartTypes.vimsamsa.name'), icon: '🙏', description: t('chartTypes.vimsamsa.description') },
    { id: 'chaturvimsamsa', name: t('chartTypes.chaturvimsamsa.name'), icon: '📚', description: t('chartTypes.chaturvimsamsa.description') },
    { id: 'saptavimshamsa', name: t('chartTypes.saptavimshamsa.name'), icon: '⭐', description: t('chartTypes.saptavimshamsa.description') },
    { id: 'trimsamsa', name: t('chartTypes.trimsamsa.name'), icon: '⚠️', description: t('chartTypes.trimsamsa.description') },
    { id: 'khavedamsa', name: t('chartTypes.khavedamsa.name'), icon: '🍀', description: t('chartTypes.khavedamsa.description') },
    { id: 'akshavedamsa', name: t('chartTypes.akshavedamsa.name'), icon: '🎭', description: t('chartTypes.akshavedamsa.description') },
    { id: 'shashtyamsa', name: t('chartTypes.shashtyamsa.name'), icon: '⏰', description: t('chartTypes.shashtyamsa.description') },
  ];
  
  const onGestureEvent = Animated.event(
    [{ nativeEvent: { translationX: chartTranslateX } }],
    { useNativeDriver: true }
  );

  const resetChartTranslation = useCallback(() => {
    Animated.spring(chartTranslateX, { toValue: 0, friction: 8, tension: 80, useNativeDriver: true }).start();
  }, [chartTranslateX]);

  useEffect(() => {
    let cancelled = false;
    const loadGuideVideoUrl = async () => {
      try {
        const response = await chartAPI.getChartGuideVideoUrl();
        const url = String(response?.data?.url || '').trim();
        console.log('[ChartScreen] guide video url fetched:', url || '(empty)');
        if (!cancelled && url) {
          setChartGuideVideoUrl(url);
        }
      } catch (error) {
        if (__DEV__) {
          console.log('[ChartScreen] guide video URL load skipped:', error?.message || error);
        }
      }
    };
    loadGuideVideoUrl();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!showGuidePlayer) return;
    let cancelled = false;
    const enableAudio = async () => {
      try {
        await Audio.setAudioModeAsync({
          playsInSilentModeIOS: true,
          staysActiveInBackground: false,
          allowsRecordingIOS: false,
          shouldDuckAndroid: true,
          interruptionModeIOS: Audio.INTERRUPTION_MODE_IOS_DO_NOT_MIX,
          interruptionModeAndroid: Audio.INTERRUPTION_MODE_ANDROID_DO_NOT_MIX,
        });
      } catch (error) {
        if (__DEV__) {
          console.log('[ChartScreen] audio mode setup skipped:', error?.message || error);
        }
      }
    };
    enableAudio();
    return () => {
      cancelled = true;
      if (cancelled) {
        Audio.setAudioModeAsync({
          playsInSilentModeIOS: true,
          staysActiveInBackground: false,
          allowsRecordingIOS: false,
          shouldDuckAndroid: true,
        }).catch(() => {});
      }
    };
  }, [showGuidePlayer]);

  const handleSwipe = useCallback((event) => {
    const { translationX, state, velocityX } = event.nativeEvent;
    const idx = currentChartIndexRef.current;
    const numCharts = chartTypes.length;

    if (state === State.END || state === State.CANCELLED) {
      if (state === State.CANCELLED) {
        resetChartTranslation();
        return;
      }
      const now = Date.now();
      const swipeThreshold = width * 0.12;
      const velocityThreshold = 300;

      if (now - lastSwipeTime.current < 150) {
        resetChartTranslation();
        return;
      }

      let newIndex = idx;
      if ((translationX > swipeThreshold || (velocityX > velocityThreshold && translationX > 10)) && idx > 0) {
        newIndex = idx - 1;
      } else if ((translationX < -swipeThreshold || (velocityX < -velocityThreshold && translationX < -10)) && idx < numCharts - 1) {
        newIndex = idx + 1;
      }
      newIndex = Math.max(0, Math.min(newIndex, numCharts - 1));

      if (newIndex !== idx) {
        lastSwipeTime.current = now;
        chartTranslateX.setValue(0);
        setCurrentChartIndex(newIndex);
        scrollToActiveTab(newIndex);
      } else if ((translationX > swipeThreshold || (velocityX > velocityThreshold && translationX > 10)) && idx === 0) {
        // At first chart, right-swipe acts as screen back gesture.
        if (!embedded) {
          navigation.goBack();
        }
      } else {
        resetChartTranslation();
      }
    }
  }, [chartTypes.length, chartTranslateX, resetChartTranslation, scrollToActiveTab, embedded, navigation]);
  
  const changeChart = useCallback((newIndex) => {
    if (newIndex === currentChartIndex) return;
    // Simplified for performance
    setCurrentChartIndex(newIndex);
    scrollToActiveTab(newIndex);
  }, [currentChartIndex]);

  const scrollToActiveTab = useCallback((index) => {
    if (!bottomNavScrollRef.current) return;
    const pillWidth = 100;
    const maxIndex = Math.max(0, chartTypes.length - 1);
    const safeIndex = Math.max(0, Math.min(index, maxIndex));
    const x = Math.max(0, safeIndex * pillWidth - (width / 2) + (pillWidth / 2));
    try {
      bottomNavScrollRef.current.scrollTo({ x, animated: true });
    } catch (_) {}
  }, [chartTypes.length]);

  // PanGestureHandler often does not receive touch pans on Expo web/PWA.
  // Use PanResponder only on web; native keeps RNGH unchanged.
  const webSwipePanResponder = useMemo(() => {
    if (Platform.OS !== 'web') return null;
    return PanResponder.create({
      onStartShouldSetPanResponder: () => false,
      onMoveShouldSetPanResponder: (_evt, gestureState) =>
        Math.abs(gestureState.dx) > 10 && Math.abs(gestureState.dx) > Math.abs(gestureState.dy) * 1.2,
      onPanResponderTerminationRequest: () => false,
      onPanResponderGrant: () => {
        chartTranslateX.stopAnimation();
      },
      onPanResponderMove: (_evt, gestureState) => {
        chartTranslateX.setValue(gestureState.dx);
      },
      onPanResponderRelease: (_evt, gestureState) => {
        // RNGH velocity is ~px/s; PanResponder vx is px/ms.
        const velocityX = (gestureState.vx || 0) * 1000;
        handleSwipe({
          nativeEvent: {
            translationX: gestureState.dx,
            velocityX,
            state: State.END,
          },
        });
      },
      onPanResponderTerminate: () => {
        resetChartTranslation();
      },
    });
  }, [chartTranslateX, handleSwipe, resetChartTranslation]);
  
  const getChartDataForType = useCallback((chartType) => {
    if (!birthData) return null;
    const cachedChart = chartPreloader.getChart(birthData, chartType);
    if (cachedChart) return cachedChart;
    if (chartType === 'lagna') return chartData;
    return null; 
  }, [birthData, chartData]);

  // House Lord Logic
  const getHouseLord = (rashiIndex) => {
    const lords = ['Mars', 'Venus', 'Mercury', 'Moon', 'Sun', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Saturn', 'Jupiter'];
    return lords[rashiIndex];
  };

  const classifySavStrength = (points) => {
    if (typeof points !== 'number') return 'moderate';
    if (points >= 30) return 'strong';
    if (points <= 25) return 'weak';
    return 'moderate';
  };

  const classifyBavStrength = (points) => {
    if (typeof points !== 'number') return 'moderate';
    if (points >= 5) return 'strong';
    if (points <= 3) return 'weak';
    return 'moderate';
  };

  const buildAshtakavargaSummary = useCallback((oraclePayload, houseNum, rashiIndex) => {
    if (!oraclePayload || !houseNum || rashiIndex == null) return null;

    const chartAshtakavarga = oraclePayload?.chart_ashtakavarga || {};
    const individualCharts = oraclePayload?.ashtakavarga?.individual_charts || {};
    const savHouse = chartAshtakavarga?.[String(houseNum)];
    const savPoints = typeof savHouse?.bindus === 'number' ? savHouse.bindus : null;
    if (savPoints == null) return null;

    const summary = {
      sav: {
        house_points: savPoints,
        classification: classifySavStrength(savPoints),
        max_points: Object.values(chartAshtakavarga)
          .map((entry) => (typeof entry?.bindus === 'number' ? entry.bindus : null))
          .filter((value) => value != null)
          .reduce((acc, value) => (acc == null || value > acc ? value : acc), null),
        min_points: Object.values(chartAshtakavarga)
          .map((entry) => (typeof entry?.bindus === 'number' ? entry.bindus : null))
          .filter((value) => value != null)
          .reduce((acc, value) => (acc == null || value < acc ? value : acc), null),
      },
    };

    const lord = getHouseLord(rashiIndex);
    const planetChart = individualCharts?.[lord];
    if (!planetChart?.bindus) {
      return summary;
    }

    const signBindusEntries = Object.entries(planetChart.bindus)
      .map(([sign, value]) => [Number(sign), typeof value === 'number' ? value : Number(value)])
      .filter(([sign, value]) => Number.isInteger(sign) && !Number.isNaN(value));

    const housePoints = signBindusEntries.find(([sign]) => sign === rashiIndex)?.[1];
    if (housePoints == null) {
      return summary;
    }

    const signToHouseMap = Object.entries(chartAshtakavarga).reduce((acc, [houseKey, entry]) => {
      if (typeof entry?.sign === 'number') {
        acc[entry.sign] = Number(houseKey);
      }
      return acc;
    }, {});

    const pointValues = signBindusEntries.map(([, value]) => value);
    const maxBav = pointValues.length ? Math.max(...pointValues) : null;
    const minBav = pointValues.length ? Math.min(...pointValues) : null;

    summary.lord_bav = {
      planet: lord,
      house_points: housePoints,
      classification: classifyBavStrength(housePoints),
      max_points: maxBav,
      min_points: minBav,
      strongest_houses: signBindusEntries
        .filter(([, value]) => value === maxBav)
        .map(([sign]) => signToHouseMap[sign])
        .filter((value) => Number.isInteger(value)),
      weakest_houses: signBindusEntries
        .filter(([, value]) => value === minBav)
        .map(([sign]) => signToHouseMap[sign])
        .filter((value) => Number.isInteger(value)),
    };

    return summary;
  }, []);

  const getHouseSignificance = (houseNum) => {
    const significances = {
      1: { title: t('houses.1.title', '1st House: Self & Appearance'), desc: t('houses.1.desc', 'Represents your personality, physical body, and general path in life.') },
      2: { title: t('houses.2.title', '2nd House: Wealth & Speech'), desc: t('houses.2.desc', 'Governs accumulated wealth, family, speech, and early education.') },
      3: { title: t('houses.3.title', '3rd House: Courage & Siblings'), desc: t('houses.3.desc', 'Represents short travels, siblings, communication, and your own efforts.') },
      4: { title: t('houses.4.title', '4th House: Mother & Comfort'), desc: t('houses.4.desc', 'Governs home, mother, vehicles, happiness, and inner peace.') },
      5: { title: t('houses.5.title', '5th House: Creativity & Children'), desc: t('houses.5.desc', 'Represents intelligence, children, past life merits, and speculation.') },
      6: { title: t('houses.6.title', '6th House: Health & Enemies'), desc: t('houses.6.desc', 'Governs daily routine, health issues, debts, and competition.') },
      7: { title: t('houses.7.title', '7th House: Marriage & Partners'), desc: t('houses.7.desc', 'Represents long-term relationships, marriage, and business partnerships.') },
      8: { title: t('houses.8.title', '8th House: Transformation & Longevity'), desc: t('houses.8.desc', 'Governs sudden changes, longevity, occult, and hidden wealth.') },
      9: { title: t('houses.9.title', '9th House: Luck & Higher Learning'), desc: t('houses.9.desc', 'Represents fortune, father, long travels, and spiritual wisdom.') },
      10: { title: t('houses.10.title', '10th House: Career & Fame'), desc: t('houses.10.desc', 'Governs profession, social status, fame, and authority.') },
      11: { title: t('houses.11.title', '11th House: Gains & Friends'), desc: t('houses.11.desc', 'Represents fulfillment of desires, income, and social circles.') },
      12: { title: t('houses.12.title', '12th House: Loss & Spirituality'), desc: t('houses.12.desc', 'Governs isolation, expenses, foreign lands, and spiritual liberation.') },
    };
    return significances[houseNum];
  };

  const openHouseDrawer = (houseData) => {
    setSelectedHouse(houseData);
  };

  const closeHouseDrawer = () => {
    setSelectedHouse(null);
  };

  const houseDrawerAspects = useMemo(() => {
    if (!selectedHouse?.chartData || selectedHouse.rashiIndex == null) return [];
    const cd = selectedHouse.chartData;
    const h = selectedHouse.houseNum;
    const server =
      cd.graha_drishti_by_house?.[String(h)] ?? cd.houses?.[h - 1]?.graha_drishti;
    if (Array.isArray(server) && server.length > 0) {
      return server.map((row) => ({
        planetName: row.planet,
        planetHouse: row.planet_house != null ? row.planet_house : null,
        aspectKinds: row.aspect_labels || '',
      }));
    }
    return getGrahaDrishtiToHouseSign(cd, selectedHouse.rashiIndex);
  }, [selectedHouse]);

  const gandantaHouseMatches = useMemo(() => {
    if (!selectedHouse?.chartData) {
      return { planets: [], lagna: { is_gandanta: false }, moon: { is_gandanta: false } };
    }
    return getGandantaHouseMatches(selectedHouse.chartData, selectedHouse.planets || []);
  }, [selectedHouse]);

  const buildBirthPayload = useCallback((data) => ({
    ...data,
    date: typeof data?.date === 'string' ? data.date.split('T')[0] : data?.date,
    time: typeof data?.time === 'string' ? data.time.split('T')[1]?.slice(0, 5) || data.time : data?.time,
    latitude: parseFloat(data?.latitude),
    longitude: parseFloat(data?.longitude),
  }), []);

  useEffect(() => {
    if (!selectedHouse?.chartData) {
      setHouseInsight(null);
      setHouseInsightLoading(false);
      houseInsightRequestKeyRef.current = null;
      return;
    }

    let cancelled = false;
    const currentChart = chartTypes[currentChartIndex]?.id || 'lagna';
    const ashtakavargaChartType = currentChart === 'transit' ? 'transit' : currentChart === 'lagna' ? 'lagna' : null;

    const loadInsight = async () => {
      try {
        const formattedBirth = buildBirthPayload(birthData);
        const transitDate = new Date().toISOString().split('T')[0];
        const requestKey = JSON.stringify({
          birthId: birthData?.id || birthData?.name || '',
          date: formattedBirth?.date || '',
          time: formattedBirth?.time || '',
          lat: formattedBirth?.latitude || '',
          lon: formattedBirth?.longitude || '',
          chart: currentChart,
          house: selectedHouse.houseNum,
          transitDate,
        });

        if (houseInsightRequestKeyRef.current === requestKey) {
          return;
        }

        houseInsightRequestKeyRef.current = requestKey;
        setHouseInsightLoading(true);
        const requests = [
          chartAPI.getHouseInsight(
            formattedBirth,
            selectedHouse.houseNum,
            currentChart,
            transitDate,
          ),
        ];

        if (ashtakavargaChartType) {
          requests.push(
            chartAPI.calculateAshtakavarga(
              formattedBirth,
              ashtakavargaChartType,
              transitDate,
            )
          );
        }

        const [insightResponse, ashtakavargaResponse] = await Promise.all(requests);

        if (!cancelled) {
          const insightData = insightResponse?.data || null;
          if (insightData && ashtakavargaResponse?.data) {
            const oracleSummary = buildAshtakavargaSummary(
              ashtakavargaResponse.data,
              selectedHouse.houseNum,
              selectedHouse.rashiIndex,
            );
            insightData.raw = {
              ...(insightData.raw || {}),
              ashtakavarga: oracleSummary,
            };
          }
          setHouseInsight(insightData);
        }
      } catch (error) {
        console.log('[ChartScreen] house insight load failed', error?.message || String(error));
        if (!cancelled) setHouseInsight(null);
        houseInsightRequestKeyRef.current = null;
      } finally {
        if (!cancelled) setHouseInsightLoading(false);
      }
    };

    loadInsight();
    return () => {
      cancelled = true;
    };
  }, [
    selectedHouse?.houseNum,
    selectedHouse?.signName,
    selectedHouse?.rashiIndex,
    birthData?.id,
    birthData?.name,
    birthData?.date,
    birthData?.time,
    birthData?.latitude,
    birthData?.longitude,
    currentChartIndex,
    buildBirthPayload,
    buildAshtakavargaSummary,
  ]);

  useEffect(() => {
    let cancelled = false;

    const loadMudakkuAnalysis = async () => {
      if (!chartData) {
        if (!cancelled) setMudakkuAnalysis(null);
        return;
      }

      try {
        const response = await chartAPI.calculateMudakkuAnalysis(chartData);
        if (!cancelled) {
          setMudakkuAnalysis(response?.data?.mudakku_analysis || null);
        }
      } catch (error) {
        console.log('[ChartScreen] mudakku analysis load failed', error?.message || String(error));
        if (!cancelled) setMudakkuAnalysis(null);
      }
    };

    loadMudakkuAnalysis();

    return () => {
      cancelled = true;
    };
  }, [chartData]);

  useEffect(() => {
    let cancelled = false;

    const loadGandantaAnalysis = async () => {
      if (!chartData) {
        if (!cancelled) setGandantaAnalysis(null);
        return;
      }

      try {
        const response = await chartAPI.calculateGandantaAnalysis(chartData);
        if (!cancelled) {
          setGandantaAnalysis(response?.data?.gandanta_analysis || null);
        }
      } catch (error) {
        console.log('[ChartScreen] gandanta analysis load failed', error?.message || String(error));
        if (!cancelled) setGandantaAnalysis(calculateGandantaLocal(chartData));
      }
    };

    loadGandantaAnalysis();

    return () => {
      cancelled = true;
    };
  }, [chartData]);
  
  const handleShare = useCallback(async () => {
    try {
      setIsSharing(true);
      // Wait for state update and potential re-renders
      await new Promise(resolve => setTimeout(resolve, 100));
      
      const uri = await captureRef(captureViewRef, {
        format: 'png',
        quality: 0.8,
      });

      await Sharing.shareAsync(uri, {
        mimeType: 'image/png',
        dialogTitle: 'Share your Cosmic Blueprint',
        UTI: 'public.png',
      });
    } catch (error) {
      console.error('Error sharing chart:', error);
      Alert.alert('Error', 'Failed to share chart. Please try again.');
    } finally {
      setIsSharing(false);
    }
  }, []);

  useEffect(() => {
    if (!onHeaderStateChange) return;
    onHeaderStateChange({
      chartName: chartTypes[currentChartIndex]?.name || '',
      positionLabel: `${currentChartIndex + 1}/${chartTypes.length}`,
      onShare: handleShare,
      isSharing,
      birthData,
    });
  }, [
    onHeaderStateChange,
    currentChartIndex,
    chartTypes[currentChartIndex]?.name,
    chartTypes.length,
    handleShare,
    isSharing,
    birthData,
  ]);
  
  useEffect(() => {
    loadBirthData();
  }, []);
  
  useEffect(() => {
    const unsubscribe = navigation.addListener('focus', () => {
      loadBirthData();
    });
    return unsubscribe;
  }, [navigation]);

  useEffect(() => {
    if (!route.params?.reopenDashaBrowser) return;
    const selectedBirthData = route.params?.birthData || route.params?.birthDetails;
    navigation.setParams({
      reopenDashaBrowser: undefined,
      birthData: undefined,
      birthDetails: undefined,
      birthChartId: undefined,
    });
    if (selectedBirthData?.name) {
      setBirthData(selectedBirthData);
    }
    setTimeout(() => setShowDashaBrowser(true), 100);
  }, [navigation, route.params?.reopenDashaBrowser]);
  


  const loadBirthData = async () => {
    try {
      setLoading(true);
      const data = await storage.getBirthDetails();
      if (!data || !data.name) {
        setLoading(false);
        navigation.replace('BirthProfileIntro', { returnTo: embedded ? 'ChartsHub' : 'Chart' });
        return;
      }
      if (data && data.name) {
        setBirthData(data);
        const formattedData = {
          name: data.name,
          date: typeof data.date === 'string' ? data.date.split('T')[0] : data.date,
          time: typeof data.time === 'string' ? data.time.split('T')[1]?.slice(0, 5) || data.time : data.time,
          latitude: parseFloat(data.latitude),
          longitude: parseFloat(data.longitude)
        };
        const response = await chartAPI.calculateChartOnly(formattedData);
        
        // Only update if data is actually different to prevent unnecessary re-renders
        setChartData(prev => {
          if (JSON.stringify(prev) === JSON.stringify(response.data)) {
            return prev;
          }
          return response.data;
        });
      }
    } catch (error) {
      console.error('ChartScreen - Error loading birth data:', error);
    } finally {
      setLoading(false);
    }
  };

  const chartCaptureBody = (
    <View
      ref={captureViewRef}
      collapsable={false}
      style={styles.captureArea}
    >
      <LinearGradient
        colors={theme === 'dark' ? ['#1a0033', '#2d1b4e'] : ['#ffffff', '#fff5f0']}
        style={[
          styles.captureGradient,
          { paddingBottom: (insets.bottom || 16) + 80 },
        ]}
      >
        <View style={styles.chartArea}>
          <View style={styles.chartWrapper}>
            <ChartWidget
              ref={chartWidgetRef}
              chartData={getChartDataForType(chartTypes[currentChartIndex].id)}
              birthData={birthData}
              lagnaChartData={chartData}
              defaultStyle="north"
              showTransits={chartTypes[currentChartIndex].id === 'transit'}
              disableSwipe={true}
              hideHeader={true}
              cosmicTheme={true}
              chartType={chartTypes[currentChartIndex].id}
              onOpenDasha={() => setShowDashaBrowser(true)}
              onOpenChartGuide={() => {
                setGuidePlayerStatus('loading');
                setShowGuidePlayer(true);
              }}
              onNavigateToTransit={() => {
                const transitIndex = chartTypes.findIndex((chart) => chart.id === 'transit');
                if (transitIndex !== -1) changeChart(transitIndex);
              }}
              navigation={navigation}
              onHousePress={openHouseDrawer}
              division={
                chartTypes[currentChartIndex].id === 'hora' ? 2 :
                chartTypes[currentChartIndex].id === 'drekkana' ? 3 :
                chartTypes[currentChartIndex].id === 'chaturthamsa' ? 4 :
                chartTypes[currentChartIndex].id === 'navamsa' ? 9 :
                chartTypes[currentChartIndex].id === 'dashamsa' ? 10 :
                chartTypes[currentChartIndex].id === 'dwadashamsa' ? 12 :
                chartTypes[currentChartIndex].id === 'shodamsa' ? 16 :
                chartTypes[currentChartIndex].id === 'vimsamsa' ? 20 :
                chartTypes[currentChartIndex].id === 'chaturvimsamsa' ? 24 :
                chartTypes[currentChartIndex].id === 'saptavimshamsa' ? 27 :
                chartTypes[currentChartIndex].id === 'trimsamsa' ? 30 :
                chartTypes[currentChartIndex].id === 'khavedamsa' ? 40 :
                chartTypes[currentChartIndex].id === 'akshavedamsa' ? 45 :
                chartTypes[currentChartIndex].id === 'shashtyamsa' ? 60 : 1
              }
            />
          </View>
        </View>

        <View style={styles.captureFooter}>
          <Text style={[styles.captureFooterText, { color: colors.textSecondary }]}>Generated by AstroRoshni</Text>
        </View>
      </LinearGradient>
    </View>
  );

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <View style={styles.container}>
        <StatusBar barStyle={colors.statusBarStyle} backgroundColor={colors.background} translucent={false} />
        <LinearGradient 
          colors={theme === 'dark' ? [colors.gradientStart, colors.gradientMid, colors.gradientEnd] : [colors.gradientStart, colors.gradientStart]} 
          style={StyleSheet.absoluteFill} 
        />
        
        <SafeAreaView style={styles.safeArea} edges={embedded ? [] : ['top']}>
          {!embedded ? (
          <View style={styles.compactHeader}>
            <TouchableOpacity onPress={() => navigation.goBack()} style={[styles.closeButton, { backgroundColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.15)' : 'rgba(249, 115, 22, 0.25)' }]}>
              <Ionicons name="arrow-back" size={20} color={colors.text} />
            </TouchableOpacity>
            <View style={styles.headerCenter}>
              <Text style={[styles.chartName, { color: colors.text }]}>{chartTypes[currentChartIndex]?.name}</Text>
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
              onPress={handleShare} 
              style={[styles.shareButton, { backgroundColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.15)' : 'rgba(249, 115, 22, 0.25)' }]}
              disabled={isSharing}
            >
              <Ionicons name="share-outline" size={18} color={colors.text} />
            </TouchableOpacity>
            <View style={[styles.chartPosition, { backgroundColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.15)' : 'rgba(249, 115, 22, 0.25)' }]}>
              <Text style={[styles.positionText, { color: colors.text }]}>{currentChartIndex + 1}/{chartTypes.length}</Text>
            </View>
          </View>
          ) : null}

          {loading ? (
            <View style={styles.loadingContainer}>
              <View style={styles.loadingContent}>
                <View style={styles.loadingOrb}>
                  <LinearGradient colors={['#ff6b35', '#ffd700']} style={styles.loadingOrbGradient}>
                    <Text style={styles.loadingOrbIcon}>✨</Text>
                  </LinearGradient>
                </View>
                <Text style={[styles.loadingText, { color: colors.text }]}>{t('chartScreen.loadingText')}</Text>
                <Text style={[styles.loadingSubtext, { color: colors.textSecondary }]}>{t('chartScreen.loadingSubtext')}</Text>
              </View>
            </View>
          ) : chartData && birthData ? (
            <View style={{ flex: 1 }}>
              <ScrollView 
                style={{ flex: 1 }} 
                contentContainerStyle={{ flexGrow: 1 }}
                showsVerticalScrollIndicator={false}
              >
                <View 
                  style={[
                    styles.mainContent,
                    theme === 'dark' 
                      ? { backgroundColor: '#1a0033' } 
                      : { backgroundColor: '#fff5f0' }
                  ]}
                >
                  <View style={styles.chartAndNavContainer}>
                    {Platform.OS === 'web' ? (
                      <Animated.View
                        {...(webSwipePanResponder?.panHandlers || {})}
                        style={{
                          flex: 1,
                          transform: [{ translateX: chartTranslateX }],
                          // Prefer vertical browser scroll; capture mostly-horizontal pans ourselves.
                          touchAction: 'pan-y',
                          userSelect: 'none',
                        }}
                      >
                        {chartCaptureBody}
                      </Animated.View>
                    ) : (
                      <PanGestureHandler
                        onGestureEvent={onGestureEvent}
                        onHandlerStateChange={handleSwipe}
                        activeOffsetX={[-8, 8]}
                        failOffsetY={[-80, 80]}
                        shouldCancelWhenOutside={false}
                      >
                        <Animated.View
                          style={{
                            flex: 1,
                            transform: [{ translateX: chartTranslateX }],
                          }}
                        >
                          {chartCaptureBody}
                        </Animated.View>
                      </PanGestureHandler>
                    )}
                  </View>
                </View>
              </ScrollView>

              <View style={[styles.bottomNavContainer, { 
                backgroundColor: theme === 'dark' ? 'rgba(26, 0, 51, 1)' : 'rgba(255, 255, 255, 1)',
                borderTopColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.05)',
                paddingBottom: insets.bottom || 15
              }]}>
                {Platform.OS === 'ios' && (
                  <BlurView intensity={theme === 'dark' ? 40 : 60} style={StyleSheet.absoluteFill} tint={theme === 'dark' ? 'dark' : 'light'} />
                )}
                <ScrollView
                  ref={bottomNavScrollRef}
                  horizontal
                  showsHorizontalScrollIndicator={false}
                  contentContainerStyle={styles.navContent}
                  decelerationRate="fast"
                >
                  {chartTypes.map((chart, index) => (
                    <TouchableOpacity
                      key={chart.id}
                      style={[styles.navPill, currentChartIndex === index && styles.navPillActive]}
                      onPress={() => changeChart(index)}
                      activeOpacity={0.7}
                    >
                      {currentChartIndex === index && <View style={[styles.activeGlow, { backgroundColor: colors.primary + '40' }]} />}
                      <Text style={[styles.navIcon, currentChartIndex === index && styles.navIconActive]}>{chart.icon}</Text>
                      <Text style={[styles.navText, { color: theme === 'dark' ? 'rgba(255, 255, 255, 0.6)' : 'rgba(0, 0, 0, 0.6)' }, currentChartIndex === index && { color: theme === 'dark' ? '#ffffff' : colors.primary, fontWeight: '800' }]}>
                        {chart.name.split(' ')[0]}
                      </Text>
                    </TouchableOpacity>
                  ))}
                </ScrollView>
              </View>
            </View>
          ) : (
            <View style={styles.emptyContainer}>
              <Text style={styles.emptyIcon}>📊</Text>
              <Text style={[styles.emptyTitle, { color: colors.text }]}>{t('chartScreen.emptyTitle')}</Text>
              <Text style={[styles.emptyText, { color: colors.textSecondary }]}>{t('chartScreen.emptyText')}</Text>
            </View>
          )}
        </SafeAreaView>
        
        <CascadingDashaBrowser visible={showDashaBrowser} onClose={() => setShowDashaBrowser(false)} birthData={birthData} onRequireBirthData={() => navigation.replace('BirthProfileIntro', { returnTo: 'Chart' })} selectNativeReturnTo="Chart" />

        <Modal
          visible={showGuidePlayer}
          transparent
          animationType="fade"
          onRequestClose={() => setShowGuidePlayer(false)}
        >
          <View style={styles.guidePlayerOverlay}>
            <StatusBar hidden />
            <Pressable style={StyleSheet.absoluteFill} onPress={() => setShowGuidePlayer(false)} />
            <View style={styles.guidePlayerBackplate} />
            <TouchableOpacity onPress={() => setShowGuidePlayer(false)} style={styles.guidePlayerClose}>
              <Ionicons name="close" size={22} color="#fff" />
            </TouchableOpacity>
            {chartGuideVideoUrl ? (
              <View style={styles.guidePlayerVideoFrame}>
                <Video
                  source={{ uri: chartGuideVideoUrl }}
                  style={styles.guidePlayerVideo}
                  useNativeControls
                  resizeMode={ResizeMode.COVER}
                  shouldPlay
                  isLooping={false}
                  isMuted={false}
                  volume={1.0}
                  onLoadStart={() => setGuidePlayerStatus('loading')}
                  onReadyForDisplay={() => setGuidePlayerStatus('ready')}
                  onError={(error) => {
                    console.log('[ChartScreen] guide video native error:', error);
                    setGuidePlayerStatus('error');
                  }}
                />
                {guidePlayerStatus === 'loading' && (
                  <View style={styles.guidePlayerLoadingOverlay}>
                    <ActivityIndicator size="large" color="#fff" />
                  </View>
                )}
              </View>
            ) : (
              <View style={styles.guidePlayerLoadingOverlay}>
                <ActivityIndicator size="large" color="#fff" />
              </View>
            )}
          </View>
        </Modal>
        
        {/* House Insights Drawer */}
        <Modal
          visible={!!selectedHouse}
          transparent
          animationType="none"
          onRequestClose={closeHouseDrawer}
        >
          <View style={styles.drawerOverlay}>
            <Pressable
              style={[StyleSheet.absoluteFill, styles.drawerBackdrop]}
              onPress={closeHouseDrawer}
              accessibilityRole="button"
              accessibilityLabel={t('common.close', 'Close')}
            />
            <View
              style={[
                styles.drawerContent,
                {
                  backgroundColor: theme === 'dark' ? 'rgba(26, 0, 51, 0.98)' : 'rgba(255, 255, 255, 0.98)',
                },
              ]}
            >
              <View style={styles.drawerHandle} />
              
              {selectedHouse && (
                <View style={styles.drawerInner}>
                  <ScrollView
                    style={styles.drawerScroll}
                    contentContainerStyle={styles.drawerScrollContent}
                    showsVerticalScrollIndicator
                    nestedScrollEnabled
                    keyboardShouldPersistTaps="handled"
                    bounces
                  >
                    {/* House Header */}
                    <View style={styles.drawerHeader}>
                      <View style={[styles.houseNumberBadge, { backgroundColor: colors.primary }]}>
                        <Text style={styles.houseNumberText}>{selectedHouse.houseNum}</Text>
                      </View>
                      <View style={styles.houseTitleContainer}>
                        <Text style={[styles.houseTitle, { color: colors.text }]}>
                          {getHouseSignificance(selectedHouse.houseNum).title}
                        </Text>
                        <Text style={[styles.houseSign, { color: colors.primary }]}>
                          {selectedHouse.signName}
                        </Text>
                      </View>
                    </View>

                    {/* Significance Description */}
                    <View style={[styles.drawerSection, { backgroundColor: theme === 'dark' ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.02)' }]}>
                      <Text style={[styles.sectionTitle, { color: colors.textSecondary }]}>Significance</Text>
                      <Text style={[styles.sectionDesc, { color: colors.text }]}>
                        {getHouseSignificance(selectedHouse.houseNum).desc}
                      </Text>
                    </View>

                    {mudakkuAnalysis && selectedHouse.rashiIndex === mudakkuAnalysis?.mudakku_point?.sign && (
                      <View style={[styles.drawerSection, { backgroundColor: theme === 'dark' ? 'rgba(255,255,255,0.05)' : 'rgba(249, 115, 22, 0.08)' }]}>
                        <Text style={[styles.sectionTitle, { color: colors.textSecondary }]}>Mudakku / Modakku</Text>
                        <Text style={[styles.sectionDesc, { color: colors.text }]}>
                          This house contains the Mudakku point for your chart.
                        </Text>

                        <View style={styles.mudakkuDetailGrid}>
                          <View style={[styles.mudakkuDetailCard, { backgroundColor: theme === 'dark' ? 'rgba(255,255,255,0.05)' : 'rgba(15, 23, 42, 0.04)' }]}>
                            <Text style={[styles.mudakkuDetailLabel, { color: colors.textSecondary }]}>Sun Nakshatra</Text>
                            <Text style={[styles.mudakkuDetailValue, { color: colors.text }]}>
                              {mudakkuAnalysis.sun_nakshatra?.name || '-'}
                            </Text>
                          </View>

                          <View style={[styles.mudakkuDetailCard, { backgroundColor: theme === 'dark' ? 'rgba(255,255,255,0.05)' : 'rgba(15, 23, 42, 0.04)' }]}>
                            <Text style={[styles.mudakkuDetailLabel, { color: colors.textSecondary }]}>Count to Mula</Text>
                            <Text style={[styles.mudakkuDetailValue, { color: colors.text }]}>
                              {mudakkuAnalysis.count_to_mula ?? '-'}
                            </Text>
                          </View>
                        </View>

                        <Text style={[styles.mudakkuNote, { color: colors.textSecondary }]}>
                          Landing nakshatra: {mudakkuAnalysis.mudakku_nakshatra?.name || '-'} · Rashi: {mudakkuAnalysis.mudakku_rashi || '-'}
                        </Text>
                        <Text style={[styles.mudakkuNote, { color: colors.textSecondary }]}>
                          {mudakkuAnalysis.is_split_nakshatra ? 'Split nakshatra rule applied.' : 'Single sign landing.'}
                        </Text>
                      </View>
                    )}

                    {(gandantaHouseMatches.planets.length > 0 || (selectedHouse.houseNum === 1 && gandantaAnalysis?.lagna_gandanta?.is_gandanta) || (selectedHouse.houseNum === 1 && gandantaHouseMatches.lagna?.is_gandanta)) && (
                      <View style={[styles.drawerSection, { backgroundColor: theme === 'dark' ? 'rgba(255,255,255,0.05)' : 'rgba(220, 38, 38, 0.08)' }]}>
                        <Text style={[styles.sectionTitle, { color: colors.textSecondary }]}>Gandamoola (Gandanta)</Text>
                        <Text style={[styles.sectionDesc, { color: colors.text }]}>
                          {selectedHouse.houseNum === 1 && (gandantaAnalysis?.lagna_gandanta?.is_gandanta || gandantaHouseMatches.lagna?.is_gandanta)
                            ? `This is a Gandanta Lagna house (${gandantaAnalysis?.lagna_gandanta?.gandanta_info?.gandanta_name || gandantaHouseMatches.lagna?.gandanta_info?.gandanta_name || 'junction'}).`
                            : 'This house contains one or more planets in Gandanta.'}
                        </Text>

                        {gandantaHouseMatches.planets.length > 0 && (
                          <View style={styles.mudakkuDetailGrid}>
                            {gandantaHouseMatches.planets.map(({ planet, gandanta_info }, idx) => (
                              <View key={`${planet?.name || 'planet'}-${idx}`} style={[styles.mudakkuDetailCard, { backgroundColor: theme === 'dark' ? 'rgba(255,255,255,0.05)' : 'rgba(15, 23, 42, 0.04)' }]}>
                                <Text style={[styles.mudakkuDetailLabel, { color: colors.textSecondary }]}>{planet?.name || 'Planet'}</Text>
                                <Text style={[styles.mudakkuDetailValue, { color: colors.text }]}>
                                  {gandanta_info?.gandanta_name || 'Gandanta'}
                                </Text>
                                <Text style={[styles.mudakkuNote, { color: colors.textSecondary, marginTop: 4 }]}>
                                  {gandanta_info?.intensity || 'Medium'} · {gandanta_info?.distance_from_junction ?? '-'}°
                                </Text>
                              </View>
                            ))}
                        </View>
                      )}

                        {selectedHouse.houseNum === 1 && (gandantaAnalysis?.lagna_gandanta?.is_gandanta || gandantaHouseMatches.lagna?.is_gandanta) && (
                          <Text style={[styles.mudakkuNote, { color: colors.textSecondary }]}>
                            Lagna point: {gandantaAnalysis?.lagna_gandanta?.gandanta_info?.gandanta_name || gandantaHouseMatches.lagna?.gandanta_info?.gandanta_name || 'Gandanta'}
                          </Text>
                        )}

                        {(gandantaAnalysis?.moon_gandanta?.is_gandanta || gandantaHouseMatches.moon?.is_gandanta) && currentChartIndex === 0 && (
                          <Text style={[styles.mudakkuNote, { color: colors.textSecondary }]}>
                            Moon also falls in {gandantaAnalysis?.moon_gandanta?.gandanta_info?.gandanta_name || gandantaHouseMatches.moon?.gandanta_info?.gandanta_name || 'Gandanta'}.
                          </Text>
                        )}
                      </View>
                    )}

                    {houseInsight && (
                      <View style={[styles.drawerSection, { backgroundColor: theme === 'dark' ? 'rgba(255,255,255,0.05)' : 'rgba(249, 115, 22, 0.06)' }]}>
                        <View style={styles.insightHeaderRow}>
                          <Text style={[styles.sectionTitle, { color: colors.textSecondary, marginBottom: 0 }]}>Chart reading</Text>
                          <View
                            style={[
                              styles.verdictBadge,
                              houseInsight.verdict.key === 'strong' && styles.verdictBadgeStrong,
                              houseInsight.verdict.key === 'mixed' && styles.verdictBadgeMixed,
                              houseInsight.verdict.key === 'active' && styles.verdictBadgeActive,
                              houseInsight.verdict.key === 'quiet' && styles.verdictBadgeQuiet,
                              { borderColor: colors.primary + '35' },
                            ]}
                          >
                            <Text
                              style={[
                                styles.verdictBadgeText,
                                { color: theme === 'dark' ? '#fff7ed' : '#7c2d12' },
                              ]}
                            >
                              {houseInsight.verdict.label}
                            </Text>
                          </View>
                        </View>

                        <Text style={[styles.sectionDesc, { color: colors.text, marginTop: 12 }]}>
                          {houseInsight.interpretation}
                        </Text>

                        {houseInsightLoading && (
                          <Text style={[styles.insightLoadingText, { color: colors.textSecondary }]}>
                            Checking chart support, pressure, and timing...
                          </Text>
                        )}
                      </View>
                    )}

                    {houseInsight?.support_factors?.length > 0 && (
                      <View style={styles.drawerSection}>
                        <Text style={[styles.sectionTitle, { color: colors.textSecondary }]}>What supports this house</Text>
                        {houseInsight.support_factors.map((item, idx) => (
                          <View key={`${selectedHouse.houseNum}-reason-${idx}`} style={styles.reasonRow}>
                            <View style={[styles.reasonDot, { backgroundColor: '#22c55e' }]} />
                            <Text style={[styles.reasonText, { color: colors.text }]}>{item.label}</Text>
                          </View>
                        ))}
                      </View>
                    )}

                    {houseInsight?.stress_factors?.length > 0 && (
                      <View style={styles.drawerSection}>
                        <Text style={[styles.sectionTitle, { color: colors.textSecondary }]}>What adds pressure</Text>
                        {houseInsight.stress_factors.map((item, idx) => (
                          <View key={`${selectedHouse.houseNum}-stress-${idx}`} style={styles.reasonRow}>
                            <View style={[styles.reasonDot, { backgroundColor: '#ef4444' }]} />
                            <Text style={[styles.reasonText, { color: colors.text }]}>{item.label}</Text>
                          </View>
                        ))}
                      </View>
                    )}

                    {houseInsight?.activation_factors?.length > 0 && (
                      <View style={styles.drawerSection}>
                        <Text style={[styles.sectionTitle, { color: colors.textSecondary }]}>What is activating it now</Text>
                        {houseInsight.activation_factors.map((item, idx) => (
                          <View key={`${selectedHouse.houseNum}-activation-${idx}`} style={styles.reasonRow}>
                            <View style={[styles.reasonDot, { backgroundColor: colors.primary }]} />
                            <Text style={[styles.reasonText, { color: colors.text }]}>{item.label}</Text>
                          </View>
                        ))}
                      </View>
                    )}

                    {houseInsight?.raw?.ashtakavarga?.sav && (
                      <View style={styles.drawerSection}>
                        <Text style={[styles.sectionTitle, { color: colors.textSecondary }]}>Ashtakavarga</Text>
                        <View style={styles.ashtakavargaGrid}>
                          <View style={[styles.ashtakavargaCard, { backgroundColor: theme === 'dark' ? 'rgba(255,255,255,0.05)' : 'rgba(15,23,42,0.04)' }]}>
                            <Text style={[styles.ashtakavargaLabel, { color: colors.textSecondary }]}>SAV</Text>
                            <Text style={[styles.ashtakavargaValue, { color: colors.text }]}>
                              {houseInsight.raw.ashtakavarga.sav?.house_points ?? '-'}
                            </Text>
                            <Text style={[styles.ashtakavargaMeta, { color: colors.textSecondary }]}>
                              {houseInsight.raw.ashtakavarga.sav?.classification || 'moderate'}
                            </Text>
                          </View>

                          {houseInsight.raw.ashtakavarga.lord_bav && (
                            <View style={[styles.ashtakavargaCard, { backgroundColor: theme === 'dark' ? 'rgba(255,255,255,0.05)' : 'rgba(15,23,42,0.04)' }]}>
                              <Text style={[styles.ashtakavargaLabel, { color: colors.textSecondary }]}>
                                {houseInsight.raw.ashtakavarga.lord_bav.planet} BAV
                              </Text>
                              <Text style={[styles.ashtakavargaValue, { color: colors.text }]}>
                                {houseInsight.raw.ashtakavarga.lord_bav.house_points ?? '-'}
                              </Text>
                              <Text style={[styles.ashtakavargaMeta, { color: colors.textSecondary }]}>
                                {houseInsight.raw.ashtakavarga.lord_bav.classification || 'moderate'}
                              </Text>
                            </View>
                          )}
                        </View>

                        <Text style={[styles.ashtakavargaExplain, { color: colors.textSecondary }]}>
                          SAV shows the house’s total support. BAV shows how strongly the house lord contributes to this house.
                        </Text>

                        {houseInsight.raw.ashtakavarga.lord_bav?.strongest_houses?.length > 0 && (
                          <Text style={[styles.ashtakavargaDetail, { color: colors.text }]}>
                            Strongest {houseInsight.raw.ashtakavarga.lord_bav.planet} BAV houses: {houseInsight.raw.ashtakavarga.lord_bav.strongest_houses.join(', ')}
                          </Text>
                        )}

                        {houseInsight.raw.ashtakavarga.lord_bav?.weakest_houses?.length > 0 && (
                          <Text style={[styles.ashtakavargaDetail, { color: colors.text }]}>
                            Weakest {houseInsight.raw.ashtakavarga.lord_bav.planet} BAV houses: {houseInsight.raw.ashtakavarga.lord_bav.weakest_houses.join(', ')}
                          </Text>
                        )}
                      </View>
                    )}

                    {/* Occupant Planets */}
                    <View style={styles.drawerSection}>
                      <Text style={[styles.sectionTitle, { color: colors.textSecondary }]}>Occupant Planets</Text>
                      {selectedHouse.planets && selectedHouse.planets.length > 0 ? (
                        selectedHouse.planets.map((planet, idx) => {
                          const roles = houseInsight?.raw?.occupant_roles?.[planet.name] || [];
                          const showRetrograde = planet.retrograde && planet.name !== 'Rahu' && planet.name !== 'Ketu';
                          return (
                          <View key={idx} style={styles.planetRow}>
                            <View style={[styles.planetIconContainer, { backgroundColor: colors.primary + '15' }]}>
                              <Text style={[styles.planetEmoji, { color: colors.primary, fontWeight: 'bold' }]}>{planet.symbol}</Text>
                            </View>
                            <View style={styles.planetInfo}>
                              <View style={styles.planetNameRow}>
                                <Text style={[styles.planetName, { color: colors.text }]}>{planet.name}</Text>
                                {showRetrograde && (
                                  <View
                                    style={[
                                      styles.retrogradeChip,
                                      { backgroundColor: theme === 'dark' ? 'rgba(245, 158, 11, 0.18)' : 'rgba(245, 158, 11, 0.12)' },
                                    ]}
                                  >
                                    <Text style={[styles.retrogradeChipText, { color: colors.text }]}>Retrograde</Text>
                                  </View>
                                )}
                                {roles.map((role) => (
                                  <View
                                    key={`${planet.name}-${role}`}
                                    style={[
                                      styles.occupantRoleChip,
                                      {
                                        backgroundColor: role === 'Yogi lord'
                                          ? (theme === 'dark' ? 'rgba(34, 197, 94, 0.18)' : 'rgba(34, 197, 94, 0.12)')
                                          : (theme === 'dark' ? 'rgba(239, 68, 68, 0.16)' : 'rgba(239, 68, 68, 0.10)'),
                                      },
                                    ]}
                                  >
                                    <Text style={[styles.occupantRoleChipText, { color: colors.text }]}>{role}</Text>
                                  </View>
                                ))}
                              </View>
                              <Text style={[styles.planetDetails, { color: colors.textSecondary }]}>
                                {(planet.formattedDegreeFull || planet.formattedDegree)} in {planet.nakshatra}
                                {planet.pada != null ? ` · Pada ${planet.pada}` : ''}
                              </Text>
                            </View>
                          </View>
                          );
                        })
                      ) : (
                        <Text style={[styles.emptySectionText, { color: colors.textTertiary }]}>No planets occupy this house.</Text>
                      )}
                    </View>

                    <View style={styles.drawerSection}>
                      <Text style={[styles.sectionTitle, { color: colors.textSecondary }]}>
                        {t('chartScreen.grahaDrishti', 'Graha drishti')}
                      </Text>
                      {houseDrawerAspects.length > 0 ? (
                        houseDrawerAspects.map((row, idx) => (
                          <View key={`${row.planetName}-${idx}`} style={styles.aspectRow}>
                            <Ionicons name="eye-outline" size={18} color={colors.primary} style={styles.aspectIcon} />
                            <View style={styles.planetInfo}>
                              <Text style={[styles.planetName, { color: colors.text }]}>
                                {t(`planets.${row.planetName}`, row.planetName)}
                                {row.planetHouse != null
                                  ? ` · ${t('chartScreen.houseAbbr', 'H')}${row.planetHouse}`
                                  : ''}
                              </Text>
                              <Text style={[styles.planetDetails, { color: colors.textSecondary }]}>
                                {row.aspectKinds} {t('chartScreen.aspectSuffix', 'aspect')}
                              </Text>
                            </View>
                          </View>
                        ))
                      ) : (
                        <Text style={[styles.emptySectionText, { color: colors.textTertiary }]}>
                          {t('chartScreen.noGrahaDrishti', 'No graha drishti from other houses.')}
                        </Text>
                      )}
                    </View>

                    {/* House Lord */}
                    <View style={styles.drawerSection}>
                      <Text style={[styles.sectionTitle, { color: colors.textSecondary }]}>House Lord</Text>
                      <View style={styles.lordContainer}>
                        <Ionicons name="key-outline" size={20} color={colors.primary} />
                        <Text style={[styles.lordText, { color: colors.text }]}>
                          Lord of {selectedHouse.signName} is <Text style={{ fontWeight: 'bold', color: colors.primary }}>{getHouseLord(selectedHouse.rashiIndex)}</Text>
                        </Text>
                      </View>
                    </View>

                    {houseInsight?.relatedChart && currentChartIndex === 0 && (
                      <View style={[styles.drawerSection, { backgroundColor: theme === 'dark' ? 'rgba(255,255,255,0.05)' : 'rgba(37, 99, 235, 0.05)' }]}>
                        <Text style={[styles.sectionTitle, { color: colors.textSecondary }]}>Related chart</Text>
                        <Text style={[styles.sectionDesc, { color: colors.text }]}>
                          {houseInsight.relatedChart.name} is often used to validate this house theme more deeply.
                        </Text>
                      </View>
                    )}
                    
                    {/* Extra padding for scroll */}
                    <View style={{ height: 40 }} />
                  </ScrollView>

                  {/* Sticky Quick Actions at Bottom */}
                  <View style={[styles.drawerActions, { 
                    backgroundColor: theme === 'dark' ? 'rgba(26, 0, 51, 1)' : 'rgba(255, 255, 255, 1)',
                    borderTopWidth: 1,
                    borderTopColor: theme === 'dark' ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.05)',
                    paddingTop: 16,
                    paddingHorizontal: 24,
                    paddingBottom: Platform.OS === 'ios' ? 30 : 20
                  }]}>
                    <TouchableOpacity 
                      style={[styles.actionButton, { backgroundColor: colors.primary }]}
                      onPress={() => {
                        closeHouseDrawer();
                        if (chartWidgetRef.current) {
                          chartWidgetRef.current.handleRotate(selectedHouse.rashiIndex);
                        }
                      }}
                    >
                      <Ionicons name="refresh-outline" size={20} color="white" />
                      <Text style={styles.actionButtonText}>Make Ascendant</Text>
                    </TouchableOpacity>

                    <TouchableOpacity 
                      style={[styles.actionButton, { backgroundColor: theme === 'dark' ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.05)' }]}
                      onPress={() => {
                        const prompt = `Analyze the ${selectedHouse.houseNum} house in my ${chartTypes[currentChartIndex].name} chart. It has ${selectedHouse.signName} sign and ${selectedHouse.planets && selectedHouse.planets.length > 0 ? selectedHouse.planets.map(p => p.name).join(', ') : 'no planets'}.`;
                        closeHouseDrawer();
                        navigation.navigate('Home', { startChat: true, initialMessage: prompt });
                      }}
                    >
                      <Ionicons name="chatbubble-ellipses-outline" size={20} color={colors.text} />
                      <Text style={[styles.actionButtonText, { color: colors.text }]}>Ask</Text>
                    </TouchableOpacity>

                    {houseInsight?.relatedChart && currentChartIndex === 0 && (
                      <TouchableOpacity
                        style={[styles.actionButton, { backgroundColor: theme === 'dark' ? 'rgba(59,130,246,0.2)' : 'rgba(37,99,235,0.12)' }]}
                        onPress={() => {
                          const relatedIndex = chartTypes.findIndex((chart) => chart.id === houseInsight.relatedChart.id);
                          closeHouseDrawer();
                          if (relatedIndex >= 0) {
                            changeChart(relatedIndex);
                          }
                        }}
                      >
                        <Ionicons name="layers-outline" size={20} color={colors.text} />
                        <Text style={[styles.actionButtonText, { color: colors.text }]}>Open {houseInsight.relatedChart.id.toUpperCase()}</Text>
                      </TouchableOpacity>
                    )}
                  </View>
                </View>
              )}
            </View>
          </View>
        </Modal>

      </View>
    </GestureHandlerRootView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  safeArea: { flex: 1 },
  compactHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 16,
  },
  closeButton: {
    width: 32,
    height: 32,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerCenter: {
    alignItems: 'center',
    flex: 1,
  },
  chartName: {
    fontSize: 18,
    fontWeight: '700',
    textAlign: 'center',
  },
  nativeChip: {
    marginTop: 6,
    paddingHorizontal: 8,
    paddingVertical: 2,
  },
  nativeChipText: {
    fontSize: 11,
  },
  chartPosition: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    marginRight: 8,
  },
  shareButton: {
    width: 32,
    height: 32,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
  },
  positionText: {
    fontSize: 11,
    fontWeight: '600',
  },
  mainContent: {
    flex: 1,
    paddingHorizontal: 0,
  },
  chartAndNavContainer: {
    flex: 1,
  },
  captureArea: {
    flex: 1,
  },
  captureGradient: {
    flex: 1,
    padding: 0,
  },
  chartContentStack: {
    flex: 1,
  },
  captureHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
    gap: 12,
  },
  captureLogo: {
    width: 40,
    height: 40,
  },
  captureTitle: {
    fontSize: 16,
    fontWeight: '800',
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  captureName: {
    fontSize: 14,
    fontWeight: '600',
  },
  chartArea: {
    flex: 1,
    paddingTop: 20,
    paddingHorizontal: 0,
    marginHorizontal: -20,
  },
  chartWrapper: {
    flex: 1,
  },
  captureFooter: {
    alignItems: 'center',
    marginTop: 16,
    paddingBottom: 20,
  },
  captureFooterText: {
    fontSize: 12,
    fontWeight: '600',
    fontStyle: 'italic',
  },
  bottomNavContainer: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    height: 80,
    borderTopWidth: 1,
    zIndex: 10000,
    elevation: 20,
  },
  navContent: {
    paddingHorizontal: 16,
    alignItems: 'center',
  },
  navPill: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
    marginHorizontal: 6,
    height: 50,
    position: 'relative',
  },
  navPillActive: {},
  activeGlow: {
    position: 'absolute',
    width: '100%',
    height: '100%',
    borderRadius: 20,
    zIndex: -1,
  },
  navIcon: {
    fontSize: 18,
    marginBottom: 2,
  },
  navIconActive: {
    transform: [{ scale: 1.1 }],
  },
  navText: {
    fontSize: 10,
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 40,
  },
  loadingContent: {
    alignItems: 'center',
  },
  loadingOrb: {
    width: 80,
    height: 80,
    borderRadius: 40,
    marginBottom: 24,
    shadowColor: '#ff6b35',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.6,
    shadowRadius: 16,
    elevation: 10,
  },
  loadingOrbGradient: {
    width: '100%',
    height: '100%',
    borderRadius: 40,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 3,
    borderColor: 'rgba(255, 255, 255, 0.3)',
  },
  loadingOrbIcon: { fontSize: 36 },
  loadingText: {
    fontSize: 20,
    fontWeight: '700',
    textAlign: 'center',
    marginBottom: 8,
  },
  loadingSubtext: {
    fontSize: 14,
    textAlign: 'center',
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 40,
  },
  emptyIcon: { fontSize: 64, marginBottom: 16 },
  emptyTitle: {
    fontSize: 20,
    fontWeight: '700',
    marginBottom: 8,
  },
  emptyText: {
    fontSize: 14,
    textAlign: 'center',
  },
  // Drawer Styles
  drawerOverlay: {
    flex: 1,
    justifyContent: 'flex-end',
  },
  drawerBackdrop: {
    backgroundColor: 'rgba(0,0,0,0.5)',
  },
  drawerContent: {
    borderTopLeftRadius: 30,
    borderTopRightRadius: 30,
    maxHeight: height * 0.75,
    zIndex: 1,
    elevation: 24,
  },
  drawerInner: {
    height: height * 0.7,
    maxHeight: height * 0.75,
  },
  drawerScroll: {
    flex: 1,
    minHeight: 0,
  },
  drawerHandle: {
    width: 40,
    height: 5,
    backgroundColor: 'rgba(128,128,128,0.3)',
    borderRadius: 3,
    alignSelf: 'center',
    marginTop: 12,
    marginBottom: 8,
  },
  drawerScrollContent: {
    padding: 24,
  },
  drawerHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
  },
  houseNumberBadge: {
    width: 44,
    height: 44,
    borderRadius: 22,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 16,
  },
  houseNumberText: {
    color: 'white',
    fontSize: 20,
    fontWeight: 'bold',
  },
  houseTitleContainer: {
    flex: 1,
  },
  houseTitle: {
    fontSize: 18,
    fontWeight: '800',
  },
  houseSign: {
    fontSize: 14,
    fontWeight: '600',
    marginTop: 2,
  },
  drawerSection: {
    padding: 16,
    borderRadius: 16,
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 12,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 1,
    marginBottom: 8,
  },
  sectionDesc: {
    fontSize: 15,
    lineHeight: 22,
  },
  insightHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 12,
  },
  verdictBadge: {
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 999,
    borderWidth: 1,
    minHeight: 30,
    alignItems: 'center',
    justifyContent: 'center',
  },
  verdictBadgeStrong: {
    backgroundColor: 'rgba(34, 197, 94, 0.22)',
  },
  verdictBadgeMixed: {
    backgroundColor: 'rgba(245, 158, 11, 0.24)',
  },
  verdictBadgeActive: {
    backgroundColor: 'rgba(59, 130, 246, 0.22)',
  },
  verdictBadgeQuiet: {
    backgroundColor: 'rgba(100, 116, 139, 0.22)',
  },
  verdictBadgeText: {
    fontSize: 12,
    fontWeight: '800',
  },
  insightLoadingText: {
    fontSize: 12,
    marginTop: 10,
    fontStyle: 'italic',
  },
  reasonRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginTop: 10,
  },
  reasonDot: {
    width: 7,
    height: 7,
    borderRadius: 999,
    marginTop: 7,
    marginRight: 10,
  },
  reasonText: {
    flex: 1,
    fontSize: 14,
    lineHeight: 21,
  },
  ashtakavargaGrid: {
    flexDirection: 'row',
    gap: 10,
    marginTop: 4,
  },
  ashtakavargaCard: {
    flex: 1,
    borderRadius: 14,
    paddingHorizontal: 14,
    paddingVertical: 12,
  },
  ashtakavargaLabel: {
    fontSize: 12,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 0.4,
  },
  ashtakavargaValue: {
    fontSize: 24,
    fontWeight: '800',
    marginTop: 6,
  },
  ashtakavargaMeta: {
    fontSize: 12,
    marginTop: 4,
    textTransform: 'capitalize',
  },
  ashtakavargaExplain: {
    fontSize: 13,
    lineHeight: 19,
    marginTop: 12,
  },
  ashtakavargaDetail: {
    fontSize: 13,
    lineHeight: 19,
    marginTop: 8,
  },
  mudakkuDetailGrid: {
    flexDirection: 'row',
    gap: 10,
    marginTop: 12,
  },
  mudakkuDetailCard: {
    flex: 1,
    borderRadius: 14,
    paddingHorizontal: 14,
    paddingVertical: 12,
  },
  mudakkuDetailLabel: {
    fontSize: 11,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  mudakkuDetailValue: {
    fontSize: 16,
    fontWeight: '800',
    marginTop: 4,
  },
  mudakkuNote: {
    fontSize: 13,
    lineHeight: 19,
    marginTop: 8,
  },
  planetRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 12,
  },
  planetNameRow: {
    flexDirection: 'row',
    alignItems: 'center',
    flexWrap: 'wrap',
    gap: 8,
  },
  planetInfo: {
    flex: 1,
  },
  planetIconContainer: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: 'rgba(128,128,128,0.1)',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  planetEmoji: {
    fontSize: 16,
  },
  planetName: {
    fontSize: 15,
    fontWeight: '700',
  },
  retrogradeChip: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 999,
  },
  retrogradeChipText: {
    fontSize: 11,
    fontWeight: '700',
  },
  occupantRoleChip: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 999,
  },
  occupantRoleChipText: {
    fontSize: 11,
    fontWeight: '700',
  },
  planetDetails: {
    fontSize: 13,
  },
  aspectRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginTop: 12,
  },
  aspectIcon: {
    marginRight: 10,
    marginTop: 2,
  },
  emptySectionText: {
    fontSize: 14,
    fontStyle: 'italic',
    marginTop: 4,
  },
  lordContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    marginTop: 4,
  },
  lordText: {
    fontSize: 15,
  },
  drawerActions: {
    flexDirection: 'row',
    gap: 12,
    flexWrap: 'wrap',
  },
  guidePlayerOverlay: {
    flex: 1,
    backgroundColor: '#000',
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 0,
  },
  guidePlayerBackplate: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: '#000',
  },
  guidePlayerClose: {
    position: 'absolute',
    top: 18,
    right: 18,
    zIndex: 5,
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(255,255,255,0.12)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  guidePlayerVideoFrame: {
    width: '100%',
    height: '100%',
    alignSelf: 'stretch',
    borderRadius: 0,
    overflow: 'hidden',
    backgroundColor: '#000',
  },
  guidePlayerVideo: {
    width: '100%',
    height: '100%',
    backgroundColor: '#000',
  },
  guidePlayerLoadingOverlay: {
    ...StyleSheet.absoluteFillObject,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'rgba(0,0,0,0.25)',
  },
  actionButton: {
    flexGrow: 1,
    minWidth: 120,
    flexDirection: 'row',
    height: 50,
    borderRadius: 25,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
  },
  actionButtonText: {
    color: 'white',
    fontSize: 14,
    fontWeight: '700',
  },
});
