import React, { useState, useEffect, useCallback, useMemo, forwardRef, useImperativeHandle } from 'react';
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

const { width } = Dimensions.get('window');

const ChartWidget = forwardRef(({ title, chartType, chartData, birthData, defaultStyle = 'north', disableSwipe = false, hideHeader = false, cosmicTheme = false, onOpenDasha, onNavigateToTransit, division }, ref) => {
  const [chartStyle, setChartStyle] = useState(defaultStyle);
  const [showDegreeNakshatra, setShowDegreeNakshatra] = useState(true);
  const [currentChartType, setCurrentChartType] = useState(chartType || 'lagna');
  
  // Update chart type when prop changes
  useEffect(() => {
    if (chartType && chartType !== currentChartType) {
      setCurrentChartType(chartType);
    }
  }, [chartType]);
  const [currentChartData, setCurrentChartData] = useState(chartData);
  const [loading, setLoading] = useState(false);
  const [slideAnim] = useState(new Animated.Value(0));
  const [showSwipeHint, setShowSwipeHint] = useState(true);
  const [chartDataCache, setChartDataCache] = useState({ lagna: chartData });
  const [nextChartType, setNextChartType] = useState(null);
  const [prevChartType, setPrevChartType] = useState(null);
  const [transitDate, setTransitDate] = useState(new Date());
  
  const chartTypes = [
    'lagna', 'navamsa', 'transit', 'dasamsa', 'dwadasamsa', 'shodasamsa', 
    'vimshamsa', 'chaturvimshamsa', 'saptavimshamsa', 'trimshamsa', 
    'khavedamsa', 'akshavedamsa', 'shashtyamsa'
  ];
  
  const chartTitles = {
    lagna: 'Birth Chart (Lagna)',
    navamsa: 'Navamsa (D9)',
    transit: 'Transit Chart',
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
    navamsa: 9, dasamsa: 10, dwadasamsa: 12, shodasamsa: 16,
    vimshamsa: 20, chaturvimshamsa: 24, saptavimshamsa: 27,
    trimshamsa: 30, khavedamsa: 40, akshavedamsa: 45, shashtyamsa: 60
  };

  const toggleStyle = useCallback(() => {
    setChartStyle(prev => prev === 'north' ? 'south' : 'north');
  }, []);
  
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
    // For lagna chart, always use passed chartData directly
    if (currentChartType === 'lagna') {
      setCurrentChartData(chartData);
    } else if (currentChartType === 'transit') {
      loadChartData(currentChartType, true);
    } else if (division) {
      // Load divisional chart using the division prop
      loadDivisionalChart(division);
    } else {
      // Load the specific chart type data
      loadChartData(currentChartType, true);
    }
  }, [currentChartType, chartData, division]);
  
  useEffect(() => {
    // Update adjacent chart types
    const currentIndex = chartTypes.indexOf(currentChartType);
    const nextIndex = (currentIndex + 1) % chartTypes.length;
    const prevIndex = currentIndex > 0 ? currentIndex - 1 : chartTypes.length - 1;
    
    setNextChartType(chartTypes[nextIndex]);
    setPrevChartType(chartTypes[prevIndex]);
  }, [currentChartType]);
  
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
      console.error('Error loading cached charts:', error);
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
      console.error('Error saving chart cache:', error);
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
        timezone: birthData.timezone || 'Asia/Kolkata'
      };
      
      // Batch fetch all divisional charts
      const divisionalPromises = Object.entries(chartDivisions).map(async ([type, division]) => {
        try {
          const response = await chartAPI.calculateDivisionalChart(formattedData, division);
          return { type, data: response.data.divisional_chart };
        } catch (error) {
          console.error(`Error loading ${type}:`, error);
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
          console.error('Error loading transit:', error);
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
      console.error('Error loading charts:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadDivisionalChart = async (divisionNumber) => {
    if (!birthData || !divisionNumber || loading) return;
    
    try {
      setLoading(true);
      const formattedData = {
        ...birthData,
        date: typeof birthData.date === 'string' ? birthData.date.split('T')[0] : birthData.date,
        time: typeof birthData.time === 'string' ? birthData.time.split('T')[1]?.slice(0, 5) || birthData.time : birthData.time,
        latitude: parseFloat(birthData.latitude),
        longitude: parseFloat(birthData.longitude),
        timezone: birthData.timezone || 'Asia/Kolkata'
      };
      
      const response = await chartAPI.calculateDivisionalChart(formattedData, divisionNumber);
      const data = response.data.divisional_chart;
      
      if (data) {
        setChartDataCache(prev => ({ ...prev, [currentChartType]: data }));
        setCurrentChartData(data);
      }
    } catch (error) {
      console.error(`Error loading divisional chart D${divisionNumber}:`, error);
    } finally {
      setLoading(false);
    }
  };

  const loadChartData = async (type, setCurrent = true, customDate = null) => {
    // Use cached data if available (but not for transit with custom date)
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
    
    if (!birthData || loading) return;
    
    try {
      if (setCurrent) setLoading(true);
      const formattedData = {
        ...birthData,
        date: typeof birthData.date === 'string' ? birthData.date.split('T')[0] : birthData.date,
        time: typeof birthData.time === 'string' ? birthData.time.split('T')[1]?.slice(0, 5) || birthData.time : birthData.time,
        latitude: parseFloat(birthData.latitude),
        longitude: parseFloat(birthData.longitude),
        timezone: birthData.timezone || 'Asia/Kolkata'
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
      }
      
      if (data) {
        setChartDataCache(prev => ({ ...prev, [type]: data }));
        if (setCurrent) setCurrentChartData(data);
      }
    } catch (error) {
      console.error(`Error loading ${type} chart:`, error);
    } finally {
      if (setCurrent) setLoading(false);
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
    
    return chartStyle === 'north' ? (
      <NorthIndianChart 
        chartData={data}
        chartType={type}
        birthData={birthData}
        showDegreeNakshatra={showDegreeNakshatra}
        cosmicTheme={cosmicTheme}
      />
    ) : (
      <SouthIndianChart 
        chartData={data}
        chartType={type}
        birthData={birthData}
        showDegreeNakshatra={showDegreeNakshatra}
        cosmicTheme={cosmicTheme}
      />
    );
  }, [chartStyle, birthData, showDegreeNakshatra]);

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
            <Text style={styles.quickActionText}>Transits</Text>
          </TouchableOpacity>
          
          <TouchableOpacity 
            style={styles.quickActionButton}
            onPress={onOpenDasha}
          >
            <Text style={styles.quickActionIcon}>⏰</Text>
            <Text style={styles.quickActionText}>Dasha</Text>
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
    height: 400,
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
    gap: 16,
    paddingHorizontal: 20,
    marginTop: 16,
  },
  quickActionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 10,
    backgroundColor: 'rgba(0, 0, 0, 0.4)',
    borderRadius: 20,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.3)',
    gap: 8,
  },
  quickActionIcon: {
    fontSize: 16,
  },
  quickActionText: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.white,
  },
});

export default ChartWidget;