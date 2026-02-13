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

const ChartWidget = forwardRef(({ title, chartType, chartData, birthData, lagnaChartData, defaultStyle = 'north', disableSwipe = false, hideHeader = false, cosmicTheme = false, onOpenDasha, onNavigateToTransit, division, navigation }, ref) => {
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
  
  console.log('[ChartWidget] Available chart types:', chartTypes);
  
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
    hora: 2, drekkana: 3, chaturthamsa: 4, navamsa: 9, saptamsa: 7, dasamsa: 10, dwadasamsa: 12, shodasamsa: 16,
    vimshamsa: 20, chaturvimshamsa: 24, saptavimshamsa: 27,
    trimshamsa: 30, khavedamsa: 40, akshavedamsa: 45, shashtyamsa: 60,
    // Aliases for consistency with ChartScreen
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
      // Get D1 chart data - use getChartData for 'lagna' type
      let d1ChartData;
      if (currentChartType === 'lagna') {
        d1ChartData = chartData;
      } else {
        // Try to get from cache first
        d1ChartData = chartDataCache.lagna;
        // If not in cache, calculate it
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
          // Cache it
          setChartDataCache(prev => ({ ...prev, lagna: d1ChartData }));
        }
      }
      
      if (!d1ChartData) {
        return null;
      }
      
      const response = await chartAPI.calculateCharaKarakas(d1ChartData, birthData);
      const loadedKarakas = response.data.chara_karakas;
      setKarakas(loadedKarakas);
      return loadedKarakas; // Return the karakas so caller can use them immediately
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
  
  const memoizedChartTypes = useMemo(() => chartTypes, []);
  const memoizedChartTitles = useMemo(() => chartTitles, []);

  const getChartData = () => {
    if (currentChartType === 'lagna') {
      return chartData;
    }
    if (currentChartType === 'transit') {
      return currentChartData || chartData;
    }
    // For divisional charts, use the cached data or return base chart
    return chartDataCache[currentChartType] || chartData;
  };

  useEffect(() => {
    // Always use chartData from props when available
    if (chartData) {
      setCurrentChartData(chartData);
      // Cache lagna chart when it's loaded
      if (currentChartType === 'lagna') {
        setChartDataCache(prev => ({ ...prev, lagna: chartData }));
        // console.log('Cached D1 chart data');
      }
      setLoading(false);
    }
  }, [chartData, currentChartType]);
  
  useEffect(() => {
    // Only load data if not provided by parent
    if (!chartData) {
      if (currentChartType === 'transit') {
        loadChartData('transit', true);
      } else if (currentChartType === 'karkamsa' || currentChartType === 'swamsa') {
        // Karkamsa and Swamsa are special Jaimini charts, not divisional charts
        loadChartData(currentChartType, true);
      } else if (division && division > 1) {
        loadDivisionalChart(division);
      } else {
        loadChartData(currentChartType, true);
      }
    }
  }, [currentChartType, division]);
  

  
  const loadCachedCharts = async () => {
    if (!birthData) return;
    
    // For lagna chart, always use passed chartData
    if (currentChartType === 'lagna') {
      setCurrentChartData(chartData);
      return;
    }
    
    try {
      // Create cache key based on birth data
      const cacheKey = `charts_${birthData.name}_${birthData.date}_${birthData.time}`;
      const cachedCharts = await storage.getItem(cacheKey);
      
      if (cachedCharts) {
        const parsedCache = JSON.parse(cachedCharts);
        setChartDataCache({ lagna: chartData, ...parsedCache });
      } else {
        // No cache, load all charts
        loadAllCharts();
      }
    } catch (error) {

      loadAllCharts();
    }
  };
  
  const saveCacheToStorage = async (cache) => {
    if (!birthData) return;
    
    try {
      const cacheKey = `charts_${birthData.name}_${birthData.date}_${birthData.time}`;
      const { lagna, ...cacheToSave } = cache; // Don't save lagna as it's always available
      await storage.setItem(cacheKey, JSON.stringify(cacheToSave));
    } catch (error) {

    }
  };

  const loadAllCharts = async () => {
    if (!birthData) return;
    
    try {
      setLoading(true);
      const formattedData = {
        ...birthData,
        date: typeof birthData.date === 'string' ? birthData.date.split('T')[0] : birthData.date,
        time: typeof birthData.time === 'string' ? birthData.time.split('T')[1]?.slice(0, 5) || birthData.time : birthData.time,
        latitude: parseFloat(birthData.latitude),
        longitude: parseFloat(birthData.longitude),
      };
      
      // Batch fetch all divisional charts
      const divisionalPromises = Object.entries(chartDivisions).map(async ([type, division]) => {
        try {
          const response = await chartAPI.calculateDivisionalChart(formattedData, division);
          return { type, data: response.data.divisional_chart };
        } catch (error) {

          return { type, data: null };
        }
      });
      
      // Fetch transit chart
      const transitPromise = (async () => {
        try {
          const today = new Date().toISOString().split('T')[0];
          const response = await chartAPI.calculateTransits(formattedData, today);
          return { type: 'transit', data: response.data };
        } catch (error) {

          return { type: 'transit', data: null };
        }
      })();
      
      // Wait for all charts to load
      const results = await Promise.all([...divisionalPromises, transitPromise]);
      
      // Update cache with all results
      const newCache = { lagna: chartData };
      results.forEach(({ type, data }) => {
        if (data) newCache[type] = data;
      });
      
      setChartDataCache(newCache);
      setCurrentChartData(newCache[currentChartType] || chartData);
      
      // Save to persistent storage
      await saveCacheToStorage(newCache);
      
    } catch (error) {

    } finally {
      setLoading(false);
    }
  };

  const loadDivisionalChart = async (divisionNumber) => {
    if (!birthData || !divisionNumber || loading) {
      return;
    }
    
    // Find the chart type that corresponds to this division
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
      
      // Cache under the correct chart type and set as current data
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
    
    if (!birthData) {
      return;
    }
    
    // Don't block if already loading - just skip setting loading state
    if (loading && setCurrent) {
      return;
    }
    
    const typeAtStart = currentChartType;
    
    try {
      if (setCurrent) {
        setLoading(true);
      }
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
        if (!loadedKarakas?.Atmakaraka?.planet) {
          loadedKarakas = await loadKarakas();
        }
        if (loadedKarakas?.Atmakaraka?.planet) {
          // Use lagnaChartData from parent (ChartScreen always has this)
          const d1Data = lagnaChartData || chartDataCache.lagna || chartData;
          
          if (!d1Data || !d1Data.planets) {
            console.error(`CRITICAL: No D1 chart data available for ${type}`);
            throw new Error('D1 chart data required for Jaimini charts');
          }
          
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
      
      // Only update if user hasn't switched charts while loading
      if (data && activeChartTypeRef.current === typeAtStart) {
        setChartDataCache(prev => ({ ...prev, [type]: data }));
        if (setCurrent) setCurrentChartData(data);
      }
    } catch (error) {
      console.error(`Error loading chart data for ${type}:`, error);
    } finally {
      if (setCurrent && activeChartTypeRef.current === typeAtStart) {
        setLoading(false);
      }
    }
  };

  const panResponder = PanResponder.create({
    onStartShouldSetPanResponder: () => false,
    onMoveShouldSetPanResponder: () => false,
    onPanResponderGrant: () => {
      setShowSwipeHint(false);
    },
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
        
        Animated.timing(slideAnim, {
          toValue: 0,
          duration: 200,
          useNativeDriver: true,
        }).start();
      } else {
        Animated.spring(slideAnim, {
          toValue: 0,
          useNativeDriver: true,
        }).start();
      }
    },
  });
  
  const navigateChart = (direction) => {
    setShowSwipeHint(false);
    const currentIndex = chartTypes.indexOf(currentChartType);
    let newIndex;
    
    if (direction === 'prev') {
      newIndex = currentIndex > 0 ? currentIndex - 1 : chartTypes.length - 1;
    } else {
      newIndex = currentIndex < chartTypes.length - 1 ? currentIndex + 1 : 0;
    }
    
    setCurrentChartType(chartTypes[newIndex]);
    
    // Smooth programmatic transition
    Animated.timing(slideAnim, {
      toValue: direction === 'prev' ? 1 : -1,
      duration: 350,
      useNativeDriver: true,
    }).start(() => {
      slideAnim.setValue(0);
    });
  };
  
  const navigateToTransit = useCallback(() => {
    setShowSwipeHint(false);
    setCurrentChartType('transit');
    
    // Smooth programmatic transition
    Animated.timing(slideAnim, {
      toValue: -1,
      duration: 350,
      useNativeDriver: true,
    }).start(() => {
      slideAnim.setValue(0);
    });
  }, [slideAnim]);
  
  // Reload transit chart when date changes
  useEffect(() => {
    if (currentChartType === 'transit') {
      loadChartData('transit', true, transitDate);
    }
  }, [transitDate]);
  
  const handleTransitDateChange = (newDate) => {
    setTransitDate(newDate);
  };
  
  // Expose methods to parent via ref
  useImperativeHandle(ref, () => ({
    navigateToTransit
  }), [navigateToTransit]);
  
  // Hide swipe hint after 3 seconds
  useEffect(() => {
    const timer = setTimeout(() => setShowSwipeHint(false), 3000);
    return () => clearTimeout(timer);
  }, []);
  
  const renderChart = useCallback((type, data) => {
    if (!type || !data) {
      return (
        <View style={styles.loadingContainer}>
          <Text style={styles.loadingText}>Loading...</Text>
        </View>
      );
    }
    
    // console.log('Rendering chart with showKarakas:', showKarakas, 'karakas:', karakas ? 'loaded' : 'null');
    
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
  }, [chartStyle, birthData, showDegreeNakshatra, rotatedAscendant, handleRotate, showKarakas, karakas]);

  return (
    <View style={[styles.container, cosmicTheme && styles.cosmicContainer]}>
      {!hideHeader && (
        <View style={styles.header}>
          <Text style={styles.title}>{chartTitles[currentChartType] || title}</Text>
          <View style={styles.chartIndicators}>
            {chartTypes.map((type, index) => (
              <View
                key={type}
                style={[
                  styles.indicator,
                  currentChartType === type && styles.indicatorActive
                ]}
              />
            ))}
          </View>
        </View>
      )}
      
      {!cosmicTheme && (
        <View style={styles.controls}>
          <TouchableOpacity
            onPress={() => setShowDegreeNakshatra(!showDegreeNakshatra)}
            style={[
              styles.controlButton,
              showDegreeNakshatra && styles.controlButtonActive
            ]}
          >
            <Text style={{
              fontSize: 16,
              color: showDegreeNakshatra ? COLORS.white : COLORS.textSecondary
            }}>
              {showDegreeNakshatra ? '👁️' : '👁️'}
            </Text>
            <Text style={[
              styles.controlButtonText,
              showDegreeNakshatra && styles.controlButtonTextActive
            ]}>
              Details
            </Text>
          </TouchableOpacity>
          
          <TouchableOpacity
            onPress={toggleStyle}
            style={styles.styleToggle}
          >
            <Text style={styles.styleToggleIcon}>🔄</Text>
            <Text style={styles.styleToggleText}>
              {chartStyle === 'north' ? 'South' : 'North'}
            </Text>
          </TouchableOpacity>
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
          <Text style={[styles.rotationBadgeText, cosmicTheme && styles.rotationBadgeTextCosmic]}>
            🔄 Rotated View
          </Text>
          <TouchableOpacity onPress={handleResetRotation} style={styles.resetButton}>
            <Text style={styles.resetButtonText}>Reset</Text>
          </TouchableOpacity>
        </View>
      )}
      
      <View style={[styles.chartContainer, cosmicTheme && styles.cosmicChartContainer, currentChartType === 'transit' && cosmicTheme && styles.chartContainerTransit]}>
        {cosmicTheme && (
          <View style={[styles.floatingControls, currentChartType === 'transit' && styles.floatingControlsTransit]}>
            <TouchableOpacity
              onPress={() => setShowDegreeNakshatra(!showDegreeNakshatra)}
              style={[styles.floatingButton, showDegreeNakshatra && styles.floatingButtonActive]}
            >
              <Text style={styles.floatingButtonIcon}>👁️</Text>
            </TouchableOpacity>
            
            <TouchableOpacity
              onPress={toggleStyle}
              style={styles.floatingButton}
            >
              <Text style={[styles.floatingButtonIcon, styles.floatingButtonText]}>
                {chartStyle === 'north' ? 'S' : 'N'}
              </Text>
            </TouchableOpacity>
          </View>
        )}
        
        <Animated.View 
          {...panResponder.panHandlers}
          style={[
            styles.swipeArea,
            {
              transform: [{
                translateX: slideAnim.interpolate({
                  inputRange: [-1, 0, 1],
                  outputRange: [-20, 0, 20],
                  extrapolate: 'clamp',
                })
              }]
            }
          ]}
        >
          {renderChart(currentChartType, getChartData())}
        </Animated.View>
      </View>
      
      {cosmicTheme && (
        <View style={styles.quickActions}>
          <TouchableOpacity 
            style={styles.quickActionButton}
            onPress={() => {
              setCurrentChartType('transit');
              if (onNavigateToTransit) onNavigateToTransit();
            }}
          >
            <Text style={styles.quickActionIcon}>🪐</Text>
            <Text style={styles.quickActionText}>{t('chartScreen.transit', 'Transit')}</Text>
          </TouchableOpacity>
          
          <TouchableOpacity 
            style={styles.quickActionButton}
            onPress={onOpenDasha}
          >
            <Text style={styles.quickActionIcon}>⏰</Text>
            <Text style={styles.quickActionText}>{t('chartScreen.dasha', 'Dasha')}</Text>
          </TouchableOpacity>
          
          <TouchableOpacity 
            style={[styles.quickActionButton, showKarakas && styles.quickActionButtonActive]}
            onPress={toggleKarakas}
          >
            <Text style={styles.quickActionIcon}>🎯</Text>
            <Text style={styles.quickActionText}>{t('chartScreen.karakas', 'Karakas')}</Text>
          </TouchableOpacity>
          
          <TouchableOpacity 
            style={styles.quickActionButton}
            onPress={() => navigation?.navigate('PlanetaryPositions', { chartData: getChartData(), birthData })}
          >
            <Text style={styles.quickActionIcon}>📋</Text>
            <Text style={styles.quickActionText}>{t('chartScreen.positions', 'Positions')}</Text>
          </TouchableOpacity>
        </View>
      )}
        
        {showSwipeHint && (
          <Animated.View style={[
            styles.swipeHint,
            {
              opacity: slideAnim.interpolate({
                inputRange: [-0.5, 0, 0.5],
                outputRange: [0.5, 1, 0.5],
                extrapolate: 'clamp',
              }),
              transform: [{
                translateY: slideAnim.interpolate({
                  inputRange: [-1, 0, 1],
                  outputRange: [5, 0, 5],
                  extrapolate: 'clamp',
                })
              }]
            }
          ]}>
            <View style={styles.swipeIndicator}>
              <Animated.View style={[
                styles.swipeDot,
                {
                  transform: [{
                    translateX: slideAnim.interpolate({
                      inputRange: [-1, 0, 1],
                      outputRange: [2, 0, -2],
                      extrapolate: 'clamp',
                    })
                  }]
                }
              ]} />
              <View style={styles.swipeDot} />
              <Animated.View style={[
                styles.swipeDot,
                {
                  transform: [{
                    translateX: slideAnim.interpolate({
                      inputRange: [-1, 0, 1],
                      outputRange: [-2, 0, 2],
                      extrapolate: 'clamp',
                    })
                  }]
                }
              ]} />
            </View>
            <Text style={styles.swipeHintText}>Swipe left or right</Text>
          </Animated.View>
        )}
    </View>
  );
});

const styles = StyleSheet.create({
  container: {
    backgroundColor: COLORS.surface,
    borderRadius: 16,
    paddingVertical: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 5,
  },
  cosmicContainer: {
    backgroundColor: 'transparent',
    borderRadius: 0,
    paddingVertical: 0,
    shadowColor: 'transparent',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0,
    shadowRadius: 0,
    elevation: 0,
  },
  header: {
    alignItems: 'center',
    marginBottom: 20,
  },
  title: {
    fontSize: 20,
    fontWeight: '700',
    color: COLORS.textPrimary,
    marginBottom: 12,
  },
  chartIndicators: {
    flexDirection: 'row',
    gap: 6,
  },
  indicator: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: COLORS.border,
    marginHorizontal: 3,
  },
  indicatorActive: {
    backgroundColor: COLORS.accent,
    width: 24,
    height: 6,
    borderRadius: 3,
  },
  controls: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 12,
    marginBottom: 15,
  },
  controlButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: COLORS.lightGray,
    borderWidth: 1,
    borderColor: COLORS.border,
    gap: 6,
  },
  controlButtonActive: {
    backgroundColor: COLORS.accent,
    borderColor: COLORS.accent,
  },
  controlButtonText: {
    fontSize: 13,
    color: COLORS.textSecondary,
    fontWeight: '600',
  },
  controlButtonTextActive: {
    color: COLORS.white,
  },
  styleToggle: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: COLORS.accent,
    borderWidth: 1,
    borderColor: COLORS.accent,
    gap: 6,
  },
  styleToggleIcon: {
    fontSize: 14,
  },
  styleToggleText: {
    color: COLORS.white,
    fontSize: 13,
    fontWeight: '600',
  },
  chartContainer: {
    width: '100%',
    height: 400,
    position: 'relative',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 10,
  },
  cosmicChartContainer: {
    flex: 1,
    minHeight: 400,
    padding: 10,
  },
  swipeArea: {
    flex: 1,
    width: '100%',
    alignItems: 'center',
    justifyContent: 'center',
  },
  carouselContainer: {
    flex: 1,
    flexDirection: 'row',
    width: width * 3,
  },
  chartSlide: {
    width: width - 40,
    position: 'absolute',
    top: 0,
    bottom: 0,
  },
  chartCard: {
    flex: 1,
    backgroundColor: 'transparent',
  },
  swipeHint: {
    position: 'absolute',
    bottom: 30,
    left: 0,
    right: 0,
    alignItems: 'center',
  },
  swipeIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(0, 0, 0, 0.6)',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    marginBottom: 8,
  },
  swipeDot: {
    width: 4,
    height: 4,
    borderRadius: 2,
    backgroundColor: COLORS.white,
    marginHorizontal: 2,
  },
  swipeHintText: {
    color: COLORS.textSecondary,
    fontSize: 11,
    fontWeight: '500',
    backgroundColor: 'rgba(255, 255, 255, 0.9)',
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 12,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    fontSize: 16,
    color: COLORS.textSecondary,
  },
  floatingControls: {
    position: 'absolute',
    top: -30,
    right: 10,
    flexDirection: 'row',
    gap: 8,
    zIndex: 10,
  },
  floatingControlsTransit: {
    top: -30,
  },
  chartContainerTransit: {
    marginTop: 20,
  },
  floatingButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: 'rgba(0, 0, 0, 0.6)',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.3)',
  },
  floatingButtonActive: {
    backgroundColor: 'rgba(255, 107, 53, 0.8)',
    borderColor: 'rgba(255, 107, 53, 1)',
  },
  floatingButtonIcon: {
    fontSize: 16,
  },
  floatingButtonText: {
    fontSize: 14,
    fontWeight: '700',
    color: COLORS.white,
  },
  quickActions: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 8,
    paddingHorizontal: 20,
    marginTop: 16,
    flexWrap: 'wrap',
  },
  quickActionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 10,
    backgroundColor: 'rgba(0, 0, 0, 0.4)',
    borderRadius: 20,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.3)',
    gap: 6,
    marginBottom: 8,
  },
  quickActionButtonActive: {
    backgroundColor: 'rgba(255, 107, 53, 0.6)',
    borderColor: 'rgba(255, 107, 53, 0.8)',
  },
  quickActionIcon: {
    fontSize: 14,
  },
  quickActionText: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.white,
  },
  rotationBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: COLORS.accent,
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    marginVertical: 12,
    alignSelf: 'center',
    gap: 12,
  },
  rotationBadgeCosmic: {
    backgroundColor: 'rgba(255, 107, 53, 0.8)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.3)',
  },
  rotationBadgeText: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.white,
  },
  rotationBadgeTextCosmic: {
    color: COLORS.white,
  },
  resetButton: {
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 12,
  },
  resetButtonText: {
    fontSize: 12,
    fontWeight: '700',
    color: COLORS.white,
  },
});

export default ChartWidget;