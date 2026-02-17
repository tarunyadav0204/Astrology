import React, { useState, useEffect, useCallback, useMemo, forwardRef, useImperativeHandle, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Animated,
  Dimensions,
  PanResponder,
} from 'react-native';
import Ionicons from '@expo/vector-icons/Ionicons';
import { chartAPI } from '../../services/api';
import { storage } from '../../services/storage';

import { COLORS } from '../../utils/constants';
import NorthIndianChart from './NorthIndianChart';
import SouthIndianChart from './SouthIndianChart';
import DateNavigator from '../Common/DateNavigator';
import { useTranslation } from 'react-i18next';

const { width } = Dimensions.get('window');

const ChartWidget = forwardRef(({ title, chartType, chartData, birthData, lagnaChartData, defaultStyle = 'north', disableSwipe = false, hideHeader = false, cosmicTheme = false, onOpenDasha, onNavigateToTransit, division, navigation, onHousePress }, ref) => {
  const { t } = useTranslation();
  const [chartStyle, setChartStyle] = useState(defaultStyle);
  const [showDegreeNakshatra, setShowDegreeNakshatra] = useState(true);
  const [currentChartType, setCurrentChartType] = useState(chartType || 'lagna');
  const [rotatedAscendant, setRotatedAscendant] = useState(null);
  const [showKarakas, setShowKarakas] = useState(false);
  const [karakas, setKarakas] = useState(null);
  
  // Update chart type when prop changes
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
  
  // Ref to prevent stale state updates
  const activeChartTypeRef = useRef(currentChartType);
  
  useEffect(() => {
    activeChartTypeRef.current = currentChartType;
  }, [currentChartType]);
  
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
  
  const chartDivisions = {
    hora: 2, drekkana: 3, chaturthamsa: 4, navamsa: 9, saptamsa: 7, dashamsa: 10, dwadashamsa: 12, shodamsa: 16,
    vimsamsa: 20, chaturvimsamsa: 24, saptavimshamsa: 27,
    trimsamsa: 30, khavedamsa: 40, akshavedamsa: 45, shashtyamsa: 60,
    shodamsa: 16, vimsamsa: 20, trimsamsa: 30
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
  
  const getChartData = () => {
    if (currentChartType === 'lagna') return chartData;
    if (currentChartType === 'transit') return currentChartData || chartData;
    return chartDataCache[currentChartType] || chartData;
  };

  useEffect(() => {
    if (chartData) {
      setCurrentChartData(chartData);
      if (currentChartType === 'lagna') {
        setChartDataCache(prev => ({ ...prev, lagna: chartData }));
      }
      setLoading(false);
    }
  }, [chartData, currentChartType]);
  
  useEffect(() => {
    if (!chartData) {
      if (currentChartType === 'transit') {
        loadChartData('transit', true);
      } else if (currentChartType === 'karkamsa' || currentChartType === 'swamsa') {
        loadChartData(currentChartType, true);
      } else if (division && division > 1) {
        loadDivisionalChart(division);
      } else {
        loadChartData(currentChartType, true);
      }
    }
  }, [currentChartType, division]);
  
  const loadDivisionalChart = async (divisionNumber) => {
    if (!birthData || !divisionNumber || loading) return;
    const targetChartType = Object.keys(chartDivisions).find(type => chartDivisions[type] === divisionNumber);
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
      if (data && targetChartType) {
        setChartDataCache(prev => ({ ...prev, [targetChartType]: data }));
        setCurrentChartData(data);
      }
    } catch (error) {
      console.error(`Error loading divisional chart D${divisionNumber}:`, error);
    } finally {
      setLoading(false);
    }
  };

  const loadChartData = async (type, setCurrent = true, customDate = null) => {
    if (chartDataCache[type] && !(type === 'transit' && customDate)) {
      if (setCurrent) setCurrentChartData(chartDataCache[type]);
      return;
    }
    if (type === 'lagna') {
      const data = chartData;
      setChartDataCache(prev => ({ ...prev, [type]: data }));
      if (setCurrent) setCurrentChartData(data);
      return;
    }
    if (!birthData) return;
    if (loading && setCurrent) return;
    const typeAtStart = currentChartType;
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
      if (chartDivisions[type]) {
        response = await chartAPI.calculateDivisionalChart(formattedData, chartDivisions[type]);
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
          const d1Data = lagnaChartData || chartDataCache.lagna || chartData;
          if (!d1Data || !d1Data.planets) throw new Error('D1 chart data required');
          const atmakaraka = loadedKarakas.Atmakaraka.planet;
          if (type === 'karkamsa') {
            response = await chartAPI.calculateKarkamsaChart(d1Data, atmakaraka);
            data = response.data.karkamsa?.karkamsa_chart;
          } else {
            response = await chartAPI.calculateSwamsaChart(d1Data, atmakaraka);
            data = response.data.swamsa?.swamsa_chart;
          }
        }
      }
      if (data && activeChartTypeRef.current === typeAtStart) {
        setChartDataCache(prev => ({ ...prev, [type]: data }));
        if (setCurrent) setCurrentChartData(data);
      }
    } catch (error) {
      console.error(`Error loading chart data for ${type}:`, error);
    } finally {
      if (setCurrent && activeChartTypeRef.current === typeAtStart) setLoading(false);
    }
  };

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
    if (!type || !data) return <View style={styles.loadingContainer}><Text style={styles.loadingText}>Loading...</Text></View>;
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
      />
    );
  }, [chartStyle, birthData, showDegreeNakshatra, rotatedAscendant, handleRotate, showKarakas, karakas, onHousePress]);

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
        <DateNavigator date={transitDate} onDateChange={handleTransitDateChange} cosmicTheme={cosmicTheme} />
      )}
      
      {rotatedAscendant !== null && (
        <View style={[styles.rotationBadge, cosmicTheme && styles.rotationBadgeCosmic]}>
          <Text style={[styles.rotationBadgeText, cosmicTheme && styles.rotationBadgeTextCosmic]}>🔄 Rotated View</Text>
          <TouchableOpacity onPress={handleResetRotation} style={styles.resetButton}><Text style={styles.resetButtonText}>Reset</Text></TouchableOpacity>
        </View>
      )}
      
      <View style={[styles.chartContainer, cosmicTheme && styles.cosmicChartContainer, currentChartType === 'transit' && cosmicTheme && styles.chartContainerTransit]}>
        {cosmicTheme && (
          <View style={[styles.floatingControls, currentChartType === 'transit' && styles.floatingControlsTransit]}>
            <TouchableOpacity onPress={() => setShowDegreeNakshatra(!showDegreeNakshatra)} style={[styles.floatingButton, showDegreeNakshatra && styles.floatingButtonActive]}>
              <Text style={styles.floatingButtonIcon}>👁️</Text>
            </TouchableOpacity>
            <TouchableOpacity onPress={toggleStyle} style={styles.floatingButton}>
              <Text style={[styles.floatingButtonIcon, styles.floatingButtonText]}>{chartStyle === 'north' ? 'S' : 'N'}</Text>
            </TouchableOpacity>
          </View>
        )}
        
        <Animated.View 
          {...panResponder.panHandlers}
          style={[styles.swipeArea, { transform: [{ translateX: slideAnim.interpolate({ inputRange: [-1, 0, 1], outputRange: [-20, 0, 20], extrapolate: 'clamp' }) }] }]}
        >
          {renderChart(currentChartType, getChartData())}
        </Animated.View>
      </View>
      
      {cosmicTheme && (
        <View style={styles.quickActions}>
          <TouchableOpacity style={styles.quickActionButton} onPress={() => { setCurrentChartType('transit'); if (onNavigateToTransit) onNavigateToTransit(); }}>
            <Text style={styles.quickActionIcon}>🪐</Text>
            <Text style={styles.quickActionText}>{t('chartScreen.transit', 'Transit')}</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.quickActionButton} onPress={onOpenDasha}>
            <Text style={styles.quickActionIcon}>⏰</Text>
            <Text style={styles.quickActionText}>{t('chartScreen.dasha', 'Dasha')}</Text>
          </TouchableOpacity>
          <TouchableOpacity style={[styles.quickActionButton, showKarakas && styles.quickActionButtonActive]} onPress={toggleKarakas}>
            <Text style={styles.quickActionIcon}>🎯</Text>
            <Text style={styles.quickActionText}>{t('chartScreen.karakas', 'Karakas')}</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.quickActionButton} onPress={() => navigation?.navigate('PlanetaryPositions', { chartData: getChartData(), birthData })}>
            <Text style={styles.quickActionIcon}>📋</Text>
            <Text style={styles.quickActionText}>{t('chartScreen.positions', 'Positions')}</Text>
          </TouchableOpacity>
          {currentChartType === 'lagna' && (
            <TouchableOpacity style={styles.quickActionButton} onPress={() => navigation?.navigate('Yogas')}>
              <Text style={styles.quickActionIcon}>🧘</Text>
              <Text style={styles.quickActionText}>{t('chartScreen.yogas', 'Yogas')}</Text>
            </TouchableOpacity>
          )}
          <TouchableOpacity style={styles.quickActionButton} onPress={() => {
            const chartName = chartTitles[currentChartType] || currentChartType;
            const prompt = `Analyze my ${chartName} chart in detail. What does it reveal about my life?`;
            navigation?.navigate('Home', { startChat: true, initialMessage: prompt });
          }}>
            <Text style={styles.quickActionIcon}>💬</Text>
            <Text style={styles.quickActionText}>{t('chartScreen.analyze', 'Analyze')}</Text>
          </TouchableOpacity>
        </View>
      )}
    </View>
  );
});

const styles = StyleSheet.create({
  container: { backgroundColor: COLORS.surface, borderRadius: 16, paddingVertical: 10, shadowColor: '#000', shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.1, shadowRadius: 8, elevation: 5 },
  cosmicContainer: { backgroundColor: 'transparent', borderRadius: 0, paddingVertical: 0, shadowColor: 'transparent', shadowOffset: { width: 0, height: 0 }, shadowOpacity: 0, shadowRadius: 0, elevation: 0 },
  header: { alignItems: 'center', marginBottom: 20 },
  title: { fontSize: 20, fontWeight: '700', color: COLORS.textPrimary, marginBottom: 12 },
  chartIndicators: { flexDirection: 'row', gap: 6 },
  indicator: { width: 6, height: 6, borderRadius: 3, backgroundColor: COLORS.border, marginHorizontal: 3 },
  indicatorActive: { backgroundColor: COLORS.accent, width: 24, height: 6, borderRadius: 3 },
  chartContainer: { width: '100%', height: 400, position: 'relative', alignItems: 'center', justifyContent: 'center', padding: 10 },
  cosmicChartContainer: { flex: 1, minHeight: 400, padding: 10 },
  swipeArea: { flex: 1, width: '100%', alignItems: 'center', justifyContent: 'center' },
  loadingContainer: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  loadingText: { fontSize: 16, color: COLORS.textSecondary },
  floatingControls: { position: 'absolute', top: -30, right: 10, flexDirection: 'row', gap: 8, zIndex: 10 },
  floatingControlsTransit: { top: -30 },
  chartContainerTransit: { marginTop: 20 },
  floatingButton: { width: 36, height: 36, borderRadius: 18, backgroundColor: 'rgba(0, 0, 0, 0.6)', alignItems: 'center', justifyContent: 'center', borderWidth: 1, borderColor: 'rgba(255, 255, 255, 0.3)' },
  floatingButtonActive: { backgroundColor: 'rgba(255, 107, 53, 0.8)', borderColor: 'rgba(255, 107, 53, 1)' },
  floatingButtonIcon: { fontSize: 16 },
  floatingButtonText: { fontSize: 14, fontWeight: '700', color: COLORS.white },
  quickActions: { flexDirection: 'row', justifyContent: 'center', gap: 8, paddingHorizontal: 20, marginTop: 16, flexWrap: 'wrap' },
  quickActionButton: { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 12, paddingVertical: 10, backgroundColor: 'rgba(0, 0, 0, 0.4)', borderRadius: 20, borderWidth: 1, borderColor: 'rgba(255, 255, 255, 0.3)', gap: 6, marginBottom: 8 },
  quickActionButtonActive: { backgroundColor: 'rgba(255, 107, 53, 0.6)', borderColor: 'rgba(255, 107, 53, 0.8)' },
  quickActionIcon: { fontSize: 14 },
  quickActionText: { fontSize: 12, fontWeight: '600', color: COLORS.white },
  rotationBadge: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', backgroundColor: COLORS.accent, paddingHorizontal: 16, paddingVertical: 8, borderRadius: 20, marginVertical: 12, alignSelf: 'center', gap: 12 },
  rotationBadgeCosmic: { backgroundColor: 'rgba(255, 107, 53, 0.8)', borderWidth: 1, borderColor: 'rgba(255, 255, 255, 0.3)' },
  rotationBadgeText: { fontSize: 14, fontWeight: '600', color: COLORS.white },
  rotationBadgeTextCosmic: { color: COLORS.white },
  resetButton: { backgroundColor: 'rgba(255, 255, 255, 0.2)', paddingHorizontal: 12, paddingVertical: 4, borderRadius: 12 },
  resetButtonText: { fontSize: 12, fontWeight: '700', color: COLORS.white },
});

export default ChartWidget;
