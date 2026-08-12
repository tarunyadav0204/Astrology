import React, { useState, useEffect, useRef, useCallback, useMemo, forwardRef, useImperativeHandle } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Animated,
  Dimensions,
  PanResponder,
  Platform,
  Modal,
  ScrollView,
} from 'react-native';
import Ionicons from '@expo/vector-icons/Ionicons';
import { BlurView } from 'expo-blur';
import { chartAPI } from '../../services/api';
import { storage } from '../../services/storage';

import { COLORS } from '../../utils/constants';
import NorthIndianChart from './NorthIndianChart';
import SouthIndianChart from './SouthIndianChart';
import DateNavigator from '../Common/DateNavigator';
import { useTranslation } from 'react-i18next';
import { useTheme } from '../../context/ThemeContext';
import { DISPLAY_FONT_FAMILY } from '../../theme/tokens';
import AppScrollView from '../../platform/AppScrollView';

const isWeb = Platform.OS === 'web';

const ChartWidget = forwardRef(({ title, chartType, chartData, birthData, lagnaChartData, defaultStyle = 'north', disableSwipe = false, hideHeader = false, cosmicTheme = false, onOpenDasha, onNavigateToTransit, onOpenChartGuide, division, navigation, onHousePress }, ref) => {
  const { t } = useTranslation();
  const { theme, colors } = useTheme();
  const [chartStyle, setChartStyle] = useState(defaultStyle);
  const [showDegreeNakshatra, setShowDegreeNakshatra] = useState(false);
  const [currentChartType, setCurrentChartType] = useState(chartType || 'lagna');
  const [rotatedAscendant, setRotatedAscendant] = useState(null);
  const [showKarakas, setShowKarakas] = useState(false);
  const [karakas, setKarakas] = useState(null);
  const [showInfoModal, setShowInfoModal] = useState(false);
  // PWA/web: measure parent width before locking SVG pixels (window width can be
  // wider than the chart column and clipped the diamond + toolbar).
  const [webChartSize, setWebChartSize] = useState(null);

  const onWebChartLayout = useCallback((event) => {
    if (!isWeb) return;
    const nextWidth = Math.floor(event?.nativeEvent?.layout?.width || 0);
    if (nextWidth < 80) return;
    setWebChartSize((prev) => (prev === nextWidth ? prev : nextWidth));
  }, []);

  useEffect(() => {
    if (!isWeb) return undefined;
    const syncSize = ({ window: nextWindow } = {}) => {
      const nextWidth = Math.floor((nextWindow || Dimensions.get('window')).width);
      if (nextWidth < 80) return;
      // Cap to window; prefer onLayout measurement when already smaller.
      setWebChartSize((prev) => {
        if (prev && prev > 0 && prev <= nextWidth) return prev;
        return nextWidth;
      });
    };
    syncSize();
    const subscription = Dimensions.addEventListener('change', syncSize);
    return () => subscription?.remove?.();
  }, []);

  useEffect(() => {
    if (chartType && chartType !== currentChartType) {
      setCurrentChartType(chartType);
    }
  }, [chartType, currentChartType]);

  const [currentChartData, setCurrentChartData] = useState(chartData);
  const [loading, setLoading] = useState(false);
  const [slideAnim] = useState(new Animated.Value(0));
  const [showSwipeHint, setShowSwipeHint] = useState(true);
  const [chartDataCache, setChartDataCache] = useState({ lagna: chartData });
  const [transitDate, setTransitDate] = useState(new Date());

  const activeChartTypeRef = useRef(currentChartType);
  const chartDataCacheRef = useRef(chartDataCache);

  useEffect(() => {
    activeChartTypeRef.current = currentChartType;
  }, [currentChartType]);

  useEffect(() => {
    chartDataCacheRef.current = chartDataCache;
  }, [chartDataCache]);

  const chartTypes = [
    'lagna', 'navamsa', 'transit', 'karkamsa', 'swamsa', 'saptamsa', 'dasamsa', 'dwadasamsa', 'shodasamsa',
    'vimshamsa', 'chaturvimshamsa', 'saptavimshamsa', 'trimshamsa',
    'khavedamsa', 'akshavedamsa', 'shashtyamsa'
  ];

  const chartTitles = {
    lagna: 'Birth Chart (Lagna)',
    navamsa: 'Navamsa (D9)',
    transit: 'Transit Chart',
    karkamsa: 'Karkamsa Chart',
    swamsa: 'Swamsa Chart',
    saptamsa: 'Saptamsa (D7)',
    dasamsa: 'Dasamsa (D10)',
    dwadasamsa: 'Dwadasamsa (D12)',
    shodasamsa: 'Shodasamsa (D16)',
    vimshamsa: 'Vimshamsa (D20)',
    chaturvimshamsa: 'Chaturvimshamsa (D24)',
    saptavimshamsa: 'Saptavimshamsa (D27)',
    trimshamsa: 'Trimshamsa (D30)',
    khavedamsa: 'Khavedamsa (D40)',
    akshavedamsa: 'Akshavedamsa (D45)',
    shashtyamsa: 'Shashtyamsa (D60)'
  };

  // Keys must match ChartScreen chart type ids (and swipe list aliases).
  const chartDivisions = {
    hora: 2,
    drekkana: 3,
    chaturthamsa: 4,
    navamsa: 9,
    saptamsa: 7,
    dashamsa: 10,
    dasamsa: 10,
    dwadashamsa: 12,
    dwadasamsa: 12,
    shodamsa: 16,
    shodasamsa: 16,
    vimsamsa: 20,
    vimshamsa: 20,
    chaturvimsamsa: 24,
    chaturvimshamsa: 24,
    saptavimshamsa: 27,
    trimsamsa: 30,
    trimshamsa: 30,
    khavedamsa: 40,
    akshavedamsa: 45,
    shashtyamsa: 60,
  };

  const toggleStyle = useCallback(() => {
    setChartStyle(prev => prev === 'north' ? 'south' : 'north');
  }, []);

  const handleRotate = useCallback((rashiIndex) => {
    setRotatedAscendant(rashiIndex);
  }, []);

  const handleResetRotation = useCallback(() => {
    setRotatedAscendant(null);
  }, []);

  const loadKarakas = useCallback(async () => {
    if (!birthData) return null;
    try {
      let d1ChartData;
      if (currentChartType === 'lagna') {
        d1ChartData = chartData;
      } else {
        d1ChartData = chartDataCache.lagna;
        if (!d1ChartData) {
          const formattedData = {
            ...birthData,
            date: typeof birthData.date === 'string' ? birthData.date.split('T')[0] : birthData.date,
            time: typeof birthData.time === 'string' ? birthData.time.split('T')[1]?.slice(0, 5) || birthData.time : birthData.time,
            latitude: parseFloat(birthData.latitude),
            longitude: parseFloat(birthData.longitude),
          };
          const response = await chartAPI.calculateChartOnly(formattedData);
          d1ChartData = response.data;
          setChartDataCache(prev => ({ ...prev, lagna: d1ChartData }));
        }
      }
      if (!d1ChartData) return null;
      const response = await chartAPI.calculateCharaKarakas(d1ChartData, birthData);
      const loadedKarakas = response.data.chara_karakas;
      setKarakas(loadedKarakas);
      return loadedKarakas;
    } catch (error) {
      console.error('Failed to load Karakas:', error);
      return null;
    }
  }, [chartData, birthData, chartDataCache.lagna, currentChartType]);

  const toggleKarakas = useCallback(async () => {
    if (!karakas && !showKarakas) {
      await loadKarakas();
    }
    setShowKarakas(prev => !prev);
  }, [karakas, showKarakas, loadKarakas]);

  const getChartInfoIntro = () => {
    switch (currentChartType) {
      case 'lagna':
        return 'This is your Lagna (D1) birth chart. It shows how the 12 houses and zodiac signs were arranged at your birth, and where each planet was placed.';
      case 'navamsa':
        return 'This is your Navamsa (D9) chart. It refines your birth chart and is especially important for marriage, dharma, and the strength of planets.';
      case 'transit':
        return 'This is your Transit chart. It shows where the planets are today in the sky and how they interact with the houses and signs in your chart.';
      case 'dasamsa':
        return 'This is your Dasamsa (D10) chart, often used for career, profession, and public role analysis.';
      case 'saptamsa':
        return 'This is your Saptamsa (D7) chart, often used for children, progeny, and related life themes.';
      case 'dwadasamsa':
        return 'This is your Dwadasamsa (D12) chart, sometimes used for ancestry, parents, and inherited patterns.';
      default:
        return `This is your ${chartTitles[currentChartType] || 'divisional'} chart. It is a Vedic astrology divisional chart used to zoom in on specific areas of life.`;
    }
  };

  const getChartInfoUsage = () => {
    switch (currentChartType) {
      case 'lagna':
        return 'Use this chart to understand your overall life pattern: personality, health, family, career foundations, relationships and major life themes across all 12 houses.';
      case 'navamsa':
        return 'Use this chart to study deeper patterns in relationships, marriage, spiritual path and the true strength and maturity of planets over time.';
      case 'transit':
        return 'Use this chart to see how current planetary movements activate different houses and themes in your life right now (e.g. timing of events, focus areas).';
      case 'dasamsa':
        return 'Use this chart to explore your career direction, professional growth, leadership potential and how your work life may evolve.';
      case 'saptamsa':
        return 'Use this chart to explore themes related to children, fertility, joy from progeny and how that area may unfold in your life.';
      case 'dwadasamsa':
        return 'Use this chart to explore connections with parents, ancestors, family lineage and inherited tendencies.';
      default:
        return 'Use this chart to focus on a specific life theme connected to this divisional chart, alongside your main Lagna (D1) chart for full context.';
    }
  };

  const getChartData = () => {
    if (currentChartType === 'lagna') return chartData || lagnaChartData || currentChartData;
    if (currentChartType === 'transit') return currentChartData || chartDataCache.transit;
    return chartDataCache[currentChartType] || currentChartData || null;
  };

  // Seed lagna into local cache when parent provides it.
  useEffect(() => {
    const lagna = chartType === 'lagna' ? chartData : lagnaChartData;
    if (lagna?.planets) {
      setChartDataCache((prev) => (prev.lagna === lagna ? prev : { ...prev, lagna }));
      if (currentChartType === 'lagna') {
        setCurrentChartData(lagna);
        setLoading(false);
      }
    }
  }, [chartData, lagnaChartData, chartType, currentChartType]);

  const loadDivisionalChart = useCallback(async (divisionNumber, typeKey) => {
    if (!birthData || !divisionNumber || divisionNumber <= 1) return;
    const cacheKey = typeKey || currentChartType;
    if (chartDataCacheRef.current[cacheKey]) {
      if (activeChartTypeRef.current === cacheKey) {
        setCurrentChartData(chartDataCacheRef.current[cacheKey]);
        setLoading(false);
      }
      return;
    }
    try {
      setLoading(true);
      const formattedData = {
        ...birthData,
        date: typeof birthData.date === 'string' ? birthData.date.split('T')[0] : birthData.date,
        time: typeof birthData.time === 'string' ? birthData.time.split('T')[1]?.slice(0, 5) || birthData.time : birthData.time,
        latitude: parseFloat(birthData.latitude),
        longitude: parseFloat(birthData.longitude),
      };
      const response = await chartAPI.calculateDivisionalChart(formattedData, divisionNumber);
      const data = response.data.divisional_chart;
      if (data) {
        setChartDataCache((prev) => ({ ...prev, [cacheKey]: data }));
        if (activeChartTypeRef.current === cacheKey) {
          setCurrentChartData(data);
        }
      }
    } catch (error) {
      console.error(`Error loading divisional chart D${divisionNumber}:`, error);
    } finally {
      if (activeChartTypeRef.current === cacheKey) setLoading(false);
    }
  }, [birthData, currentChartType]);

  const loadChartData = useCallback(async (type, setCurrent = true, customDate = null) => {
    const typeAtStart = type;
    if (type === 'lagna') {
      const data = chartData || lagnaChartData;
      if (data) {
        setChartDataCache((prev) => ({ ...prev, lagna: data }));
        if (setCurrent) {
          setCurrentChartData(data);
          setLoading(false);
        }
      }
      return;
    }
    if (!birthData) return;
    const cachedHit =
      chartDataCacheRef.current[type] && !(type === 'transit' && customDate)
        ? chartDataCacheRef.current[type]
        : null;
    if (cachedHit) {
      if (setCurrent && activeChartTypeRef.current === typeAtStart) {
        setCurrentChartData(cachedHit);
        setLoading(false);
      }
      return;
    }
    try {
      if (setCurrent) setLoading(true);

      const formattedData = {
        ...birthData,
        date: typeof birthData.date === 'string' ? birthData.date.split('T')[0] : birthData.date,
        time: typeof birthData.time === 'string' ? birthData.time.split('T')[1]?.slice(0, 5) || birthData.time : birthData.time,
        latitude: parseFloat(birthData.latitude),
        longitude: parseFloat(birthData.longitude),
      };
      let response;
      let data;
      const divisionNumber = chartDivisions[type] || (division > 1 ? division : null);
      if (divisionNumber) {
        response = await chartAPI.calculateDivisionalChart(formattedData, divisionNumber);
        data = response.data.divisional_chart;
      } else if (type === 'transit') {
        const targetDate = customDate || transitDate;
        const dateStr = targetDate.toISOString().split('T')[0];
        response = await chartAPI.calculateTransits(formattedData, dateStr);
        data = response.data;
      } else if (type === 'karkamsa' || type === 'swamsa') {
        let loadedKarakas = karakas;
        if (!loadedKarakas?.Atmakaraka?.planet) loadedKarakas = await loadKarakas();
        if (loadedKarakas?.Atmakaraka?.planet) {
          let resolvedD1 = lagnaChartData || chartData || chartDataCacheRef.current.lagna;
          if (!resolvedD1?.planets) {
            const d1Res = await chartAPI.calculateChartOnly(formattedData, {
              suppressGlobalError: true,
            });
            resolvedD1 = d1Res?.data;
            if (resolvedD1) {
              setChartDataCache((prev) => ({ ...prev, lagna: resolvedD1 }));
            }
          }
          if (!resolvedD1?.planets) throw new Error('D1 chart data required');
          const atmakaraka = loadedKarakas.Atmakaraka.planet;
          if (type === 'karkamsa') {
            response = await chartAPI.calculateKarkamsaChart(resolvedD1, atmakaraka);
            data = response.data.karkamsa?.karkamsa_chart;
          } else {
            response = await chartAPI.calculateSwamsaChart(resolvedD1, atmakaraka);
            data = response.data.swamsa?.swamsa_chart;
          }
        }
      }
      if (data && activeChartTypeRef.current === typeAtStart) {
        setChartDataCache((prev) => ({ ...prev, [type]: data }));
        if (setCurrent) setCurrentChartData(data);
      }
    } catch (error) {
      console.error(`Error loading chart data for ${type}:`, error);
    } finally {
      if (setCurrent && activeChartTypeRef.current === typeAtStart) setLoading(false);
    }
  }, [
    birthData,
    chartData,
    lagnaChartData,
    division,
    transitDate,
    karakas,
    loadKarakas,
  ]);

  // Always resolve the active chart when type/division/birth changes.
  // (Previously only loaded when parent chartData was null, and skipped while `loading`
  // was true — which left Hora/D10/etc stuck on "Loading..." for guests.)
  useEffect(() => {
    const type = currentChartType;
    if (!type) return;

    if (type === 'lagna') {
      const data = chartData || lagnaChartData;
      if (data) {
        setCurrentChartData(data);
        setChartDataCache((prev) => ({ ...prev, lagna: data }));
        setLoading(false);
      }
      return;
    }

    const cached = chartDataCacheRef.current[type];
    if (cached && type !== 'transit') {
      setCurrentChartData(cached);
      setLoading(false);
      return;
    }

    if (type === 'transit') {
      loadChartData('transit', true);
      return;
    }
    if (type === 'karkamsa' || type === 'swamsa') {
      loadChartData(type, true);
      return;
    }
    if (division && division > 1) {
      loadDivisionalChart(division, type);
      return;
    }
    if (chartDivisions[type]) {
      loadChartData(type, true);
    }
  }, [currentChartType, division, birthData?.id, birthData?.date, birthData?.time, loadChartData, loadDivisionalChart, chartData, lagnaChartData]);

  const panResponder = PanResponder.create({
    onStartShouldSetPanResponder: () => false,
    onMoveShouldSetPanResponder: () => false,
    onPanResponderGrant: () => setShowSwipeHint(false),
    onPanResponderMove: (evt, gestureState) => {
      const normalizedTranslation = Math.max(-1, Math.min(1, gestureState.dx / 100));
      slideAnim.setValue(normalizedTranslation);
    },
    onPanResponderRelease: (evt, gestureState) => {
      const threshold = 50;
      const shouldSwipe = Math.abs(gestureState.dx) > threshold;
      if (shouldSwipe) {
        const currentIndex = chartTypes.indexOf(currentChartType);
        let newIndex;
        if (gestureState.dx > 0) {
          newIndex = currentIndex > 0 ? currentIndex - 1 : chartTypes.length - 1;
        } else {
          newIndex = currentIndex < chartTypes.length - 1 ? currentIndex + 1 : 0;
        }
        setCurrentChartType(chartTypes[newIndex]);
        Animated.timing(slideAnim, { toValue: 0, duration: 200, useNativeDriver: true }).start();
      } else {
        Animated.spring(slideAnim, { toValue: 0, useNativeDriver: true }).start();
      }
    },
  });

  const navigateToTransit = useCallback(() => {
    setShowSwipeHint(false);
    setCurrentChartType('transit');
    Animated.timing(slideAnim, { toValue: -1, duration: 350, useNativeDriver: true }).start(() => slideAnim.setValue(0));
  }, [slideAnim]);

  useEffect(() => {
    if (currentChartType === 'transit') loadChartData('transit', true, transitDate);
  }, [transitDate]);

  const handleTransitDateChange = (newDate) => setTransitDate(newDate);

  useImperativeHandle(ref, () => ({ navigateToTransit, handleRotate }), [navigateToTransit, handleRotate]);

  useEffect(() => {
    const timer = setTimeout(() => setShowSwipeHint(false), 3000);
    return () => clearTimeout(timer);
  }, []);

  const renderChart = useCallback((type, data) => {
    if (!type || !data) return <View style={styles.loadingContainer}><Text style={styles.loadingText}>{t('premiumUi.common.loading')}</Text></View>;
    const sizeProp = isWeb && webChartSize ? { size: webChartSize } : {};
    return chartStyle === 'north' ? (
      <NorthIndianChart
        chartData={data}
        chartType={type}
        birthData={birthData}
        showDegreeNakshatra={showDegreeNakshatra}
        cosmicTheme={cosmicTheme}
        rotatedAscendant={rotatedAscendant}
        onRotate={handleRotate}
        showKarakas={showKarakas}
        karakas={karakas}
        onHousePress={onHousePress}
        hideInstructions={cosmicTheme}
        {...sizeProp}
      />
    ) : (
      <SouthIndianChart
        chartData={data}
        chartType={type}
        birthData={birthData}
        showDegreeNakshatra={showDegreeNakshatra}
        cosmicTheme={cosmicTheme}
        rotatedAscendant={rotatedAscendant}
        onRotate={handleRotate}
        showKarakas={showKarakas}
        karakas={karakas}
        {...sizeProp}
      />
    );
  }, [chartStyle, birthData, showDegreeNakshatra, rotatedAscendant, handleRotate, showKarakas, karakas, onHousePress, webChartSize]);

  const QuickActionButton = ({ icon, label, onPress, active, primary }) => {
    const iconColor = primary ? colors.onPrimary : (active ? colors.onAccent : colors.text);
    const textColor = colors.text;
    return (
      <TouchableOpacity
        style={[
          styles.quickActionButton,
        ]}
        onPress={onPress}
        activeOpacity={0.8}
      >
        <View style={[styles.quickActionIcon, { backgroundColor: primary ? colors.primary : active ? colors.accentSoft : colors.surfaceMuted }]}>
          <Ionicons name={icon} size={18} color={iconColor} />
        </View>
        <Text style={[
          styles.quickActionText,
          { color: textColor },
        ]}>
          {label}
        </Text>
      </TouchableOpacity>
    );
  };

  return (
    <View style={[styles.container, cosmicTheme && styles.cosmicContainer]}>
      {!hideHeader && (
        <View style={styles.header}>
          <Text style={styles.title}>{chartTitles[currentChartType] || title}</Text>
          <View style={styles.chartIndicators}>
            {chartTypes.map((type) => (
              <View key={type} style={[styles.indicator, currentChartType === type && styles.indicatorActive]} />
            ))}
          </View>
        </View>
      )}

      {currentChartType === 'transit' && (
        <DateNavigator
          date={transitDate}
          onDateChange={handleTransitDateChange}
          cosmicTheme={cosmicTheme}
        />
      )}

      {rotatedAscendant !== null && (
        <View style={[styles.rotationBadge, cosmicTheme && styles.rotationBadgeCosmic]}>
          <Text style={[styles.rotationBadgeText, cosmicTheme && styles.rotationBadgeTextCosmic]}>🔄 {t('premiumUi.chart.rotatedView')}</Text>
          <TouchableOpacity onPress={handleResetRotation} style={styles.resetButton}><Text style={styles.resetButtonText}>{t('premiumUi.common.reset')}</Text></TouchableOpacity>
        </View>
      )}

      <View
        style={cosmicTheme
          ? [styles.chartStage, { backgroundColor: colors.chartSurface, borderColor: colors.chartLine }]
          : null}
      >
      {cosmicTheme ? (
        <View style={[styles.webToolbar, { backgroundColor: colors.chartRaised, borderBottomColor: colors.chartLine }]}>
          <Text style={[styles.viewToolbarLabel, { color: colors.chartTextMuted }]}>{t('premiumUi.common.view')}</Text>
          <View style={styles.webToolbarLeft}>
            <TouchableOpacity
              onPress={() => setShowDegreeNakshatra(!showDegreeNakshatra)}
              style={[
                styles.viewControl,
                {
                  backgroundColor: 'transparent',
                },
              ]}
            >
              <Ionicons name={showDegreeNakshatra ? "eye" : "eye-off"} size={15} color={showDegreeNakshatra ? colors.primary : colors.chartTextMuted} />
              <Text style={[styles.viewControlText, { color: showDegreeNakshatra ? colors.primary : colors.chartTextMuted }]}>{t('premiumUi.common.degrees')}</Text>
            </TouchableOpacity>
            <TouchableOpacity
              onPress={toggleStyle}
              style={[styles.viewControl, { backgroundColor: 'transparent' }]}
            >
              <Ionicons name="grid-outline" size={15} color={colors.chartTextMuted} />
              <Text style={[styles.viewControlText, { color: colors.chartTextMuted }]}>{chartStyle === 'north' ? 'South' : 'North'}</Text>
            </TouchableOpacity>
          </View>
          <TouchableOpacity
            onPress={() => setShowInfoModal(true)}
            style={styles.viewInfoButton}
            accessibilityRole="button"
            accessibilityLabel={t('premiumUi.common.aboutChart')}
          >
            <Ionicons name="information-circle-outline" size={18} color={colors.chartTextMuted} />
          </TouchableOpacity>
        </View>
      ) : null}

      <View
        onLayout={onWebChartLayout}
        style={[
          styles.chartContainer,
          cosmicTheme && styles.cosmicChartContainer,
          currentChartType === 'transit' && cosmicTheme && styles.chartContainerTransit,
          isWeb
            ? {
                width: '100%',
                aspectRatio: 1,
                maxWidth: '100%',
                alignSelf: 'stretch',
                overflow: 'visible',
              }
            : null,
        ]}
      >
        <Animated.View
          {...(disableSwipe ? {} : panResponder.panHandlers)}
          style={[
            styles.swipeArea,
            isWeb && styles.swipeAreaWeb,
            isWeb
              ? { width: '100%', aspectRatio: 1, overflow: 'visible' }
              : null,
            { transform: [{ translateX: slideAnim.interpolate({ inputRange: [-1, 0, 1], outputRange: [-20, 0, 20], extrapolate: 'clamp' }) }] },
          ]}
        >
          {renderChart(currentChartType, getChartData())}
        </Animated.View>
      </View>
      </View>

      {cosmicTheme && (
        <View style={styles.advancedToolsSection}>
          <Text style={[styles.advancedToolsLabel, { color: colors.textSecondary }]}>{t('premiumUi.common.professionalTools')}</Text>
          <AppScrollView
            horizontal
            nestedScrollEnabled
            directionalLockEnabled
            showsHorizontalScrollIndicator={false}
            style={styles.horizontalRail}
            contentContainerStyle={styles.advancedToolsRow}
          >
            {[
              ['grid-outline', 'Ashtakvarga', () => navigation?.navigate('AshtakvargaOracle')],
              ['compass-outline', 'KP system', () => navigation?.navigate('KPSystem', { birthDetails: birthData })],
              ['shield-outline', 'Kota Chakra', () => navigation?.navigate('KotaChakra', { birthChartId: birthData?.id })],
              ...(onOpenChartGuide ? [['play-circle-outline', 'Chart guide', onOpenChartGuide]] : []),
            ].map(([icon, label, action]) => (
              <TouchableOpacity
                key={label}
                onPress={action}
                style={styles.advancedTool}
                activeOpacity={0.8}
              >
                <Ionicons name={icon} size={16} color={colors.primary} />
                <Text style={[styles.advancedToolText, { color: colors.text }]}>{label}</Text>
              </TouchableOpacity>
            ))}
          </AppScrollView>
        </View>
      )}

      {cosmicTheme && (
        <View style={styles.quickActionsGrid}>
          <Text style={[styles.advancedToolsLabel, { color: colors.textSecondary }]}>{t('premiumUi.common.readChart')}</Text>
          <AppScrollView
            horizontal
            nestedScrollEnabled
            directionalLockEnabled
            showsHorizontalScrollIndicator={false}
            style={styles.horizontalRail}
            contentContainerStyle={styles.quickActionsRow}
          >
            {currentChartType !== 'transit' && (
              <QuickActionButton
                icon="planet-outline"
                label={t('chartScreen.transit', 'Transit')}
                onPress={() => { setCurrentChartType('transit'); if (onNavigateToTransit) onNavigateToTransit(); }}
                active={false}
              />
            )}
            <QuickActionButton
              icon="time-outline"
              label={t('chartScreen.dasha', 'Dasha')}
              onPress={onOpenDasha}
            />
            <QuickActionButton
              icon="star-outline"
              label={t('chartScreen.karakas', 'Karakas')}
              onPress={toggleKarakas}
              active={showKarakas}
            />
            <QuickActionButton
              icon="list-outline"
              label={t('chartScreen.positions', 'Positions')}
              onPress={() => {
                const cd = getChartData();
                if (cd?.planets && birthData) {
                  navigation?.navigate('PlanetaryPositions', { chartData: cd, birthData });
                }
              }}
            />
            {currentChartType === 'lagna' && (
              <QuickActionButton
                icon="body-outline"
                label={t('chartScreen.yogas', 'Yogas')}
                onPress={() => navigation?.navigate('Yogas')}
              />
            )}
            <QuickActionButton
              icon="sparkles-outline"
              label={t('chartScreen.askTara', 'Ask Tara')}
              primary
              onPress={() => {
                const chartName = chartTitles[currentChartType] || currentChartType;
                const prompt = `Analyze my ${chartName} chart in detail. What does it reveal about my life?`;
                navigation?.navigate('Home', { startChat: true, initialMessage: prompt });
              }}
            />
          </AppScrollView>
        </View>
      )}

      {showInfoModal && (
        <Modal
          visible={showInfoModal}
          transparent
          animationType="fade"
          onRequestClose={() => setShowInfoModal(false)}
        >
          <View style={[styles.infoOverlay, { backgroundColor: colors.overlay }]}>
            <View style={[styles.infoContent, { backgroundColor: colors.surface, borderColor: colors.cardBorder }]}>
              <Text style={[styles.infoTitle, { color: colors.text }]}>
                {t('chartScreen.infoTitle', 'About this chart')}
              </Text>
              <ScrollView style={styles.infoScroll} showsVerticalScrollIndicator={false}>
                {onOpenChartGuide ? (
                  <TouchableOpacity
                    activeOpacity={0.85}
                    onPress={() => {
                      setShowInfoModal(false);
                      onOpenChartGuide();
                    }}
                    style={[styles.infoGuideCard, { backgroundColor: colors.surfaceMuted, borderColor: colors.cardBorder }]}
                    accessibilityRole="button"
                    accessibilityLabel={t('chartScreen.watchGuideTitle', 'How to read this chart')}
                  >
                    <View style={[styles.infoGuideIcon, { backgroundColor: colors.primary }]}>
                      <Ionicons name="play" size={14} color={colors.onPrimary} />
                    </View>
                    <View style={styles.infoGuideTextWrap}>
                      <Text style={[styles.infoGuideLabel, { color: colors.primary }]}>
                        {t('chartScreen.watchGuide', 'Watch guide')}
                      </Text>
                      <Text style={[styles.infoGuideTitle, { color: colors.text }]}>
                        {t('chartScreen.watchGuideTitle', 'How to read this chart')}
                      </Text>
                    </View>
                    <Text style={[styles.infoGuideMeta, { color: colors.primary }]}>
                      {t('chartScreen.watchGuideDuration', '4 min')}
                    </Text>
                  </TouchableOpacity>
                ) : null}
                <Text style={[styles.infoText, { color: colors.textSecondary }]}>
                  {getChartInfoIntro()}
                </Text>
                <Text style={[styles.infoText, { color: colors.textSecondary }]}>
                  {getChartInfoUsage()}
                </Text>
                <Text style={[styles.infoSubTitle, { color: colors.text }]}>
                  {t('chartScreen.legendTitle', 'Legend')}
                </Text>
                <Text style={[styles.infoText, { color: colors.textSecondary }]}>
                  • {t('chartScreen.legendHouses', 'The house with ASC written is your 1st house. From there, go counter‑clockwise around the chart for houses 1–12.')}{'\n'}
                  • {t('chartScreen.legendSigns', 'The small number inside each diamond is the zodiac sign number (1–12), not the house number.')}{'\n'}
                  • {t('chartScreen.legendPlanets', 'Planet symbols show where each planet sits in the chart.')}{'\n'}
                  • {t('chartScreen.legendRetro', '(R) after a planet means it is retrograde.')}{'\n'}
                  • {t('chartScreen.legendExaltDebil', '↑ and ↓ indicate exalted or debilitated planets.')}{'\n'}
                  • {t('chartScreen.legendNakshatra', 'Turn on the eye icon to see exact degrees and nakshatra names under each planet.')}
                </Text>
              </ScrollView>
              <TouchableOpacity onPress={() => setShowInfoModal(false)} style={[styles.infoCloseButton, { backgroundColor: colors.primary }]}>
                <Text style={[styles.infoCloseButtonText, { color: colors.onPrimary }]}>
                  {t('common.close', 'Close')}
                </Text>
              </TouchableOpacity>
            </View>
          </View>
        </Modal>
      )}

    </View>
  );
});

const styles = StyleSheet.create({
  container: { backgroundColor: COLORS.surface, borderRadius: 16, paddingVertical: 10, shadowColor: '#000', shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.1, shadowRadius: 8, elevation: 5 },
  cosmicContainer: { backgroundColor: 'transparent', borderRadius: 0, paddingVertical: 0, shadowColor: 'transparent', shadowOffset: { width: 0, height: 0 }, shadowOpacity: 0, shadowRadius: 0, elevation: 0 },
  chartStage: {
    marginHorizontal: 10,
    borderRadius: 24,
    borderWidth: 1,
    overflow: 'hidden',
  },
  header: { alignItems: 'center', marginBottom: 20 },
  title: { fontSize: 20, fontWeight: '700', color: COLORS.textPrimary, marginBottom: 12 },
  chartIndicators: { flexDirection: 'row', gap: 6 },
  indicator: { width: 6, height: 6, borderRadius: 3, backgroundColor: COLORS.border, marginHorizontal: 3 },
  indicatorActive: { backgroundColor: COLORS.accent, width: 24, height: 6, borderRadius: 3 },
  chartContainer: Platform.select({
    web: {
      width: '100%',
      aspectRatio: 1,
      position: 'relative',
      alignItems: 'center',
      justifyContent: 'center',
      padding: 0,
      marginTop: 0,
      overflow: 'visible',
    },
    default: {
      width: '100%',
      aspectRatio: 1,
      position: 'relative',
      alignItems: 'center',
      justifyContent: 'center',
      padding: 0,
      paddingTop: 0,
    },
  }),
  cosmicChartContainer: Platform.select({
    web: {
      width: '100%',
      aspectRatio: 1,
      padding: 0,
      marginTop: 0,
      marginBottom: 0,
      overflow: 'visible',
    },
    default: {
      width: '100%',
      aspectRatio: 1,
      padding: 0,
      paddingTop: 0,
      marginBottom: 0,
    },
  }),
  swipeArea: { flex: 1, width: '100%', alignItems: 'center', justifyContent: 'center' },
  swipeAreaWeb: { flex: 0, width: '100%', alignSelf: 'center', overflow: 'visible' },
  loadingContainer: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  loadingText: { fontSize: 16, color: COLORS.textSecondary },
  chartContainerTransit: { marginTop: 12 },
  webToolbar: {
    flexDirection: 'row',
    alignItems: 'center',
    width: '100%',
    minHeight: 46,
    paddingHorizontal: 15,
    paddingVertical: 6,
    borderBottomWidth: 1,
    zIndex: 2,
  },
  viewToolbarLabel: {
    fontSize: 8,
    fontWeight: '800',
    letterSpacing: 1.4,
    marginRight: 12,
  },
  webToolbarLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 7,
    flex: 1,
  },
  viewControl: {
    minHeight: 30,
    paddingHorizontal: 4,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  viewControlText: {
    fontSize: 10,
    fontWeight: '600',
  },
  viewInfoButton: {
    width: 30,
    height: 30,
    alignItems: 'center',
    justifyContent: 'center',
  },
  quickActionsGrid: { marginTop: 22 },
  quickActionsRow: { paddingHorizontal: 16, paddingRight: 28, gap: 18 },
  quickActionButton: {
    width: 58,
    minHeight: 62,
    alignItems: 'center',
    justifyContent: 'flex-start',
  },
  quickActionIcon: {
    width: 38,
    height: 38,
    borderRadius: 19,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 7,
  },
  quickActionText: { fontSize: 10, lineHeight: 13, fontWeight: '700', textAlign: 'center' },
  advancedToolsSection: {
    marginTop: 20,
  },
  horizontalRail: Platform.select({
    web: { width: '100%', overflow: 'auto', touchAction: 'pan-x' },
    default: { width: '100%' },
  }),
  advancedToolsLabel: {
    paddingHorizontal: 16,
    marginBottom: 8,
    fontSize: 9,
    fontWeight: '800',
    letterSpacing: 1.4,
  },
  advancedToolsRow: {
    paddingHorizontal: 16,
    paddingRight: 28,
    gap: 8,
  },
  advancedTool: {
    minHeight: 32,
    paddingHorizontal: 2,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  advancedToolText: {
    fontSize: 11,
    fontWeight: '700',
  },
  rotationBadge: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', backgroundColor: COLORS.accent, paddingHorizontal: 16, paddingVertical: 8, borderRadius: 20, marginVertical: 12, alignSelf: 'center', gap: 12 },
  rotationBadgeCosmic: { backgroundColor: 'rgba(255, 107, 53, 0.8)', borderWidth: 1, borderColor: 'rgba(255, 255, 255, 0.3)' },
  rotationBadgeText: { fontSize: 14, fontWeight: '600', color: COLORS.white },
  rotationBadgeTextCosmic: { color: COLORS.white },
  resetButton: { backgroundColor: 'rgba(255, 255, 255, 0.2)', paddingHorizontal: 12, paddingVertical: 4, borderRadius: 12 },
  resetButtonText: { fontSize: 12, fontWeight: '700', color: COLORS.white },
  infoOverlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.7)', justifyContent: 'center', alignItems: 'center', padding: 24 },
  infoContent: {
    width: '100%',
    maxWidth: 420,
    maxHeight: 480,
    borderRadius: 28,
    paddingHorizontal: 22,
    paddingVertical: 20,
    borderWidth: 1,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 16 },
    shadowOpacity: 0.45,
    shadowRadius: 26,
    elevation: 16,
  },
  infoTitle: {
    fontFamily: DISPLAY_FONT_FAMILY,
    fontSize: 24,
    fontWeight: '600',
    marginBottom: 8,
    textAlign: 'center',
  },
  infoSubTitle: { fontSize: 12, fontWeight: '800', marginTop: 12, marginBottom: 5, letterSpacing: 1.1 },
  infoScroll: { maxHeight: 360, marginBottom: 16 },
  infoText: { fontSize: 13, lineHeight: 20, marginBottom: 8 },
  infoGuideCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    marginBottom: 14,
    paddingVertical: 10,
    paddingHorizontal: 12,
    borderRadius: 14,
    borderWidth: 1,
  },
  infoGuideIcon: {
    width: 28,
    height: 28,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
  },
  infoGuideTextWrap: { flex: 1, minWidth: 0 },
  infoGuideLabel: {
    fontSize: 10,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 0.6,
    marginBottom: 1,
  },
  infoGuideTitle: { fontSize: 13, fontWeight: '700' },
  infoGuideMeta: {
    fontSize: 11,
    fontWeight: '700',
    flexShrink: 0,
  },
  infoCloseButton: { alignSelf: 'stretch', alignItems: 'center', paddingHorizontal: 24, paddingVertical: 12, borderRadius: 999 },
  infoCloseButtonText: { fontSize: 14, fontWeight: '800', letterSpacing: 0.2 },
});

export default ChartWidget;
