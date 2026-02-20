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

const { width } = Dimensions.get('window');

const ChartWidget = forwardRef(({ title, chartType, chartData, birthData, lagnaChartData, defaultStyle = 'north', disableSwipe = false, hideHeader = false, cosmicTheme = false, onOpenDasha, onNavigateToTransit, division, navigation, onHousePress }, ref) => {
  const { t } = useTranslation();
  const { theme } = useTheme();
  const isLight = theme === 'light';
  const [chartStyle, setChartStyle] = useState(defaultStyle);
  const [showDegreeNakshatra, setShowDegreeNakshatra] = useState(false);
  const [currentChartType, setCurrentChartType] = useState(chartType || 'lagna');
  const [rotatedAscendant, setRotatedAscendant] = useState(null);
  const [showKarakas, setShowKarakas] = useState(false);
  const [karakas, setKarakas] = useState(null);
  const [showInfoModal, setShowInfoModal] = useState(false);
  
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

  const QuickActionButton = ({ icon, label, onPress, active, primary }) => {
    const iconColor = primary ? '#fff' : (isLight ? '#1e293b' : '#fff');
    const textColor = primary ? '#fff' : (isLight ? '#1e293b' : '#fff');
    return (
      <TouchableOpacity 
        style={[
          styles.quickActionButton, 
          isLight && styles.quickActionButtonLight,
          active && (isLight ? styles.quickActionButtonActiveLight : styles.quickActionButtonActive),
          primary && styles.quickActionButtonPrimary
        ]} 
        onPress={onPress}
      >
        <Ionicons name={icon} size={18} color={iconColor} />
        <Text style={[
          styles.quickActionText, 
          { color: textColor },
          active && styles.quickActionTextActive,
          primary && styles.quickActionTextPrimary
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
          <Text style={[styles.rotationBadgeText, cosmicTheme && styles.rotationBadgeTextCosmic]}>🔄 Rotated View</Text>
          <TouchableOpacity onPress={handleResetRotation} style={styles.resetButton}><Text style={styles.resetButtonText}>Reset</Text></TouchableOpacity>
        </View>
      )}
      
      <View style={[styles.chartContainer, cosmicTheme && styles.cosmicChartContainer, currentChartType === 'transit' && cosmicTheme && styles.chartContainerTransit]}>
        {cosmicTheme && (
          <>
            <View style={[styles.floatingControls, currentChartType === 'transit' && styles.floatingControlsTransit]}>
              <TouchableOpacity
                onPress={() => setShowDegreeNakshatra(!showDegreeNakshatra)}
                style={[styles.floatingButton, showDegreeNakshatra && styles.floatingButtonActive]}
              >
                <Ionicons name={showDegreeNakshatra ? "eye" : "eye-off"} size={18} color="#fff" />
              </TouchableOpacity>
              <TouchableOpacity onPress={toggleStyle} style={styles.floatingButton}>
                <Text style={styles.floatingButtonText}>{chartStyle === 'north' ? 'S' : 'N'}</Text>
              </TouchableOpacity>
              <TouchableOpacity 
                onPress={() => navigation?.navigate('AshtakvargaOracle')} 
                style={styles.floatingButton}
              >
                <Ionicons name="grid-outline" size={18} color="#fff" />
              </TouchableOpacity>
              <TouchableOpacity 
                onPress={() => navigation?.navigate('KPSystem', { birthDetails: birthData })} 
                style={styles.floatingButton}
              >
                <Ionicons name="compass-outline" size={18} color="#fff" />
              </TouchableOpacity>
              <TouchableOpacity 
                onPress={() => navigation?.navigate('KotaChakra', { birthChartId: birthData?.id })} 
                style={styles.floatingButton}
              >
                <Ionicons name="shield-outline" size={18} color="#fff" />
              </TouchableOpacity>
            </View>
            <View style={styles.infoButtonContainer}>
              <TouchableOpacity onPress={() => setShowInfoModal(true)} style={styles.infoButton}>
                <Ionicons name="information-circle-outline" size={20} color="#fff" />
              </TouchableOpacity>
            </View>
          </>
        )}
        
        <Animated.View 
          {...(disableSwipe ? {} : panResponder.panHandlers)}
          style={[styles.swipeArea, { transform: [{ translateX: slideAnim.interpolate({ inputRange: [-1, 0, 1], outputRange: [-20, 0, 20], extrapolate: 'clamp' }) }] }]}
        >
          {renderChart(currentChartType, getChartData())}
        </Animated.View>
      </View>
      
      {cosmicTheme && (
        <View style={styles.quickActionsGrid}>
          <View style={styles.quickActionsRow}>
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
          </View>
          <View style={styles.quickActionsRow}>
            <QuickActionButton 
              icon="list-outline" 
              label={t('chartScreen.positions', 'Positions')} 
              onPress={() => navigation?.navigate('PlanetaryPositions', { chartData: getChartData(), birthData })}
            />
            {currentChartType === 'lagna' ? (
              <QuickActionButton 
                icon="body-outline" 
                label={t('chartScreen.yogas', 'Yogas')} 
                onPress={() => navigation?.navigate('Yogas')}
              />
            ) : (
              <View style={{ flex: 1 }} />
            )}
            <QuickActionButton 
              icon="sparkles-outline" 
              label={t('chartScreen.analyze', 'Analyze')} 
              primary
              onPress={() => {
                const chartName = chartTitles[currentChartType] || currentChartType;
                const prompt = `Analyze my ${chartName} chart in detail. What does it reveal about my life?`;
                navigation?.navigate('Home', { startChat: true, initialMessage: prompt });
              }}
            />
          </View>
        </View>
      )}
      
      {showInfoModal && (
        <Modal
          visible={showInfoModal}
          transparent
          animationType="fade"
          onRequestClose={() => setShowInfoModal(false)}
        >
          <View style={styles.infoOverlay}>
            <View style={styles.infoContent}>
              <Text style={styles.infoTitle}>
                {t('chartScreen.infoTitle', 'About this chart')}
              </Text>
              <ScrollView style={styles.infoScroll} showsVerticalScrollIndicator={false}>
                <Text style={styles.infoText}>
                  {getChartInfoIntro()}
                </Text>
                <Text style={styles.infoText}>
                  {getChartInfoUsage()}
                </Text>
                <Text style={styles.infoSubTitle}>
                  {t('chartScreen.legendTitle', 'Legend')}
                </Text>
                <Text style={styles.infoText}>
                  • {t('chartScreen.legendHouses', 'The house with ASC written is your 1st house. From there, go counter‑clockwise around the chart for houses 1–12.')}{'\n'}
                  • {t('chartScreen.legendSigns', 'The small number inside each diamond is the zodiac sign number (1–12), not the house number.')}{'\n'}
                  • {t('chartScreen.legendPlanets', 'Planet symbols show where each planet sits in the chart.')}{'\n'}
                  • {t('chartScreen.legendRetro', '(R) after a planet means it is retrograde.')}{'\n'}
                  • {t('chartScreen.legendExaltDebil', '↑ and ↓ indicate exalted or debilitated planets.')}{'\n'}
                  • {t('chartScreen.legendNakshatra', 'Turn on the eye icon to see exact degrees and nakshatra names under each planet.')}
                </Text>
              </ScrollView>
              <TouchableOpacity onPress={() => setShowInfoModal(false)} style={styles.infoCloseButton}>
                <Text style={styles.infoCloseButtonText}>
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
  header: { alignItems: 'center', marginBottom: 20 },
  title: { fontSize: 20, fontWeight: '700', color: COLORS.textPrimary, marginBottom: 12 },
  chartIndicators: { flexDirection: 'row', gap: 6 },
  indicator: { width: 6, height: 6, borderRadius: 3, backgroundColor: COLORS.border, marginHorizontal: 3 },
  indicatorActive: { backgroundColor: COLORS.accent, width: 24, height: 6, borderRadius: 3 },
  chartContainer: { width: '100%', aspectRatio: 1, position: 'relative', alignItems: 'center', justifyContent: 'center', padding: 0, paddingTop: 60 },
  cosmicChartContainer: { width: '100%', aspectRatio: 1, padding: 0, paddingTop: 60, marginBottom: 20 },
  swipeArea: { flex: 1, width: '100%', alignItems: 'center', justifyContent: 'center' },
  loadingContainer: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  loadingText: { fontSize: 16, color: COLORS.textSecondary },
  floatingControls: { position: 'absolute', top: 10, left: 30, flexDirection: 'row', gap: 8, zIndex: 10 },
  floatingControlsTransit: { top: 10 },
  chartContainerTransit: { marginTop: 20 },
  floatingButton: { width: 36, height: 36, borderRadius: 18, backgroundColor: 'rgba(0, 0, 0, 0.6)', alignItems: 'center', justifyContent: 'center', borderWidth: 1, borderColor: 'rgba(255, 255, 255, 0.3)' },
  floatingButtonActive: { backgroundColor: 'rgba(255, 107, 53, 0.8)', borderColor: 'rgba(255, 107, 53, 1)' },
  floatingButtonText: { fontSize: 14, fontWeight: '700', color: '#fff' },
  infoButtonContainer: { position: 'absolute', top: 10, right: 30, zIndex: 10 },
  infoButton: { width: 36, height: 36, borderRadius: 18, backgroundColor: 'rgba(0, 0, 0, 0.6)', alignItems: 'center', justifyContent: 'center', borderWidth: 1, borderColor: 'rgba(255, 255, 255, 0.3)' },
  quickActionsGrid: { marginTop: 24, paddingHorizontal: 36, gap: 12 },
  quickActionsRow: { flexDirection: 'row', gap: 12 },
  quickActionButton: { 
    flex: 1,
    flexDirection: 'row', 
    alignItems: 'center', 
    paddingHorizontal: 12, 
    paddingVertical: 12, 
    backgroundColor: 'rgba(255, 255, 255, 0.1)', 
    borderRadius: 16, 
    borderWidth: 1, 
    borderColor: 'rgba(255, 255, 255, 0.2)', 
    gap: 8,
    justifyContent: 'center'
  },
  quickActionButtonLight: {
    backgroundColor: 'rgba(30, 41, 59, 0.08)',
    borderColor: 'rgba(30, 41, 59, 0.2)',
  },
  quickActionButtonActive: { 
    backgroundColor: 'rgba(255, 255, 255, 0.25)', 
    borderColor: 'rgba(255, 255, 255, 0.4)',
  },
  quickActionButtonActiveLight: {
    backgroundColor: 'rgba(30, 41, 59, 0.15)',
    borderColor: 'rgba(30, 41, 59, 0.35)',
  },
  quickActionButtonPrimary: {
    backgroundColor: '#ff6b35',
    borderColor: '#ff8a65',
  },
  quickActionText: { fontSize: 12, fontWeight: '600' },
  quickActionTextActive: { fontWeight: '800' },
  quickActionTextPrimary: { color: '#fff', fontWeight: '800' },
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
    backgroundColor: '#020617', 
    borderRadius: 24, 
    paddingHorizontal: 22, 
    paddingVertical: 20, 
    borderWidth: 1, 
    borderColor: 'rgba(248, 250, 252, 0.1)',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 16 },
    shadowOpacity: 0.45,
    shadowRadius: 26,
    elevation: 16,
  },
  infoTitle: { 
    fontSize: 19, 
    fontWeight: '800', 
    color: '#f9fafb', 
    marginBottom: 6, 
    textAlign: 'center', 
    letterSpacing: 0.4,
    textTransform: 'uppercase',
  },
  infoSubTitle: { fontSize: 14, fontWeight: '700', color: '#cbd5f5', marginTop: 12, marginBottom: 4 },
  infoScroll: { maxHeight: 360, marginBottom: 16 },
  infoText: { fontSize: 13, color: '#e5e7eb', lineHeight: 20, marginBottom: 8 },
  infoCloseButton: { alignSelf: 'center', paddingHorizontal: 24, paddingVertical: 10, borderRadius: 999, backgroundColor: '#f97316' },
  infoCloseButtonText: { fontSize: 14, fontWeight: '700', color: '#fff', letterSpacing: 0.3, textTransform: 'uppercase' },
});

export default ChartWidget;
