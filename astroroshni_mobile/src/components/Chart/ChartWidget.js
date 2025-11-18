import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Animated,
  Dimensions,
} from 'react-native';
import { GestureHandlerRootView, PanGestureHandler } from 'react-native-gesture-handler';
import { Ionicons } from '@expo/vector-icons';
import { chartAPI } from '../../services/api';

import { COLORS } from '../../utils/constants';
import NorthIndianChart from './NorthIndianChart';
import SouthIndianChart from './SouthIndianChart';

const { width } = Dimensions.get('window');

const ChartWidget = ({ title, chartType, chartData, birthData, defaultStyle = 'north' }) => {
  const [chartStyle, setChartStyle] = useState(defaultStyle);
  const [showDegreeNakshatra, setShowDegreeNakshatra] = useState(true);
  const [currentChartType, setCurrentChartType] = useState(chartType || 'lagna');
  const [currentChartData, setCurrentChartData] = useState(chartData);
  const [loading, setLoading] = useState(false);
  const [slideAnim] = useState(new Animated.Value(0));
  const [showSwipeHint, setShowSwipeHint] = useState(true);
  const [chartDataCache, setChartDataCache] = useState({ lagna: chartData });
  const [nextChartType, setNextChartType] = useState(null);
  const [prevChartType, setPrevChartType] = useState(null);
  
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

  useEffect(() => {
    loadChartData(currentChartType);
    // Preload adjacent charts
    const currentIndex = chartTypes.indexOf(currentChartType);
    const nextIndex = (currentIndex + 1) % chartTypes.length;
    const prevIndex = currentIndex > 0 ? currentIndex - 1 : chartTypes.length - 1;
    
    setNextChartType(chartTypes[nextIndex]);
    setPrevChartType(chartTypes[prevIndex]);
    
    // Preload next and previous charts
    if (!chartDataCache[chartTypes[nextIndex]]) {
      loadChartData(chartTypes[nextIndex], false);
    }
    if (!chartDataCache[chartTypes[prevIndex]]) {
      loadChartData(chartTypes[prevIndex], false);
    }
  }, [currentChartType]);

  const loadChartData = async (type, setCurrent = true) => {
    if (type === 'lagna') {
      const data = chartData;
      setChartDataCache(prev => ({ ...prev, [type]: data }));
      if (setCurrent) setCurrentChartData(data);
      return;
    }
    
    if (!birthData) return;
    
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
        // Divisional chart
        response = await chartAPI.calculateDivisionalChart(formattedData, chartDivisions[type]);
        data = response.data.divisional_chart;
      } else if (type === 'transit') {
        const today = new Date().toISOString().split('T')[0];
        response = await chartAPI.calculateTransits(formattedData, today);
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

  const onSwipeGesture = (event) => {
    const { translationX, state, velocityX } = event.nativeEvent;
    
    // Update animation during gesture
    if (state === 2) { // ACTIVE state
      const normalizedTranslation = Math.max(-1, Math.min(1, translationX / (width * 0.3)));
      slideAnim.setValue(normalizedTranslation);
    }
    
    // Handle gesture end
    if (state === 5) { // END state
      const threshold = Math.abs(velocityX) > 500 ? 50 : 100;
      const shouldSwipe = Math.abs(translationX) > threshold;
      
      if (shouldSwipe) {
        setShowSwipeHint(false);
        const currentIndex = chartTypes.indexOf(currentChartType);
        let newIndex;
        
        if (translationX > 0) {
          newIndex = currentIndex > 0 ? currentIndex - 1 : chartTypes.length - 1;
        } else {
          newIndex = currentIndex < chartTypes.length - 1 ? currentIndex + 1 : 0;
        }
        
        setCurrentChartType(chartTypes[newIndex]);
        
        // Complete the swipe animation
        Animated.spring(slideAnim, {
          toValue: translationX > 0 ? 1 : -1,
          useNativeDriver: true,
          tension: 100,
          friction: 8,
        }).start(() => {
          slideAnim.setValue(0);
        });
      } else {
        // Snap back
        Animated.spring(slideAnim, {
          toValue: 0,
          useNativeDriver: true,
          tension: 150,
          friction: 10,
        }).start();
      }
    }
  };
  
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
      />
    ) : (
      <SouthIndianChart 
        chartData={data}
        chartType={type}
        birthData={birthData}
        showDegreeNakshatra={showDegreeNakshatra}
      />
    );
  }, [chartStyle, birthData, showDegreeNakshatra]);

  return (
    <View style={styles.container}>
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
      
      <View style={styles.controls}>
        <TouchableOpacity
          onPress={() => setShowDegreeNakshatra(!showDegreeNakshatra)}
          style={[
            styles.controlButton,
            showDegreeNakshatra && styles.controlButtonActive
          ]}
        >
          <Ionicons 
            name={showDegreeNakshatra ? 'eye-off' : 'eye'} 
            size={16} 
            color={showDegreeNakshatra ? COLORS.white : COLORS.textSecondary} 
          />
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
          <Text style={styles.styleToggleText}>
            {chartStyle === 'north' ? 'South' : 'North'}
          </Text>
        </TouchableOpacity>
      </View>
      
      <GestureHandlerRootView style={styles.chartContainer}>
        <PanGestureHandler 
          onGestureEvent={onSwipeGesture}
          onHandlerStateChange={onSwipeGesture}
          activeOffsetX={[-10, 10]}
          failOffsetY={[-20, 20]}
        >
          <Animated.View style={[
            styles.carouselContainer,
            {
              transform: [{
                translateX: slideAnim.interpolate({
                  inputRange: [-1, 0, 1],
                  outputRange: [width, 0, -width],
                  extrapolate: 'clamp',
                })
              }]
            }
          ]}>
            {/* Previous Chart */}
            <View style={[styles.chartSlide, { left: -width }]}>
              <View style={styles.chartCard}>
                {renderChart(prevChartType, chartDataCache[prevChartType])}
              </View>
            </View>
            
            {/* Current Chart */}
            <View style={[styles.chartSlide, { left: 0 }]}>
              <View style={styles.chartCard}>
                {renderChart(currentChartType, currentChartData)}
              </View>
            </View>
            
            {/* Next Chart */}
            <View style={[styles.chartSlide, { left: width }]}>
              <View style={styles.chartCard}>
                {renderChart(nextChartType, chartDataCache[nextChartType])}
              </View>
            </View>
          </Animated.View>
        </PanGestureHandler>
        
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
      </GestureHandlerRootView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: COLORS.surface,
    borderRadius: 16,
    padding: 20,
    marginBottom: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 5,
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
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: COLORS.accent,
    borderWidth: 1,
    borderColor: COLORS.accent,
  },
  styleToggleText: {
    color: COLORS.white,
    fontSize: 13,
    fontWeight: '600',
  },
  chartContainer: {
    width: '100%',
    aspectRatio: 1,
    position: 'relative',
    overflow: 'hidden',
  },
  carouselContainer: {
    flex: 1,
    flexDirection: 'row',
    width: width * 3,
  },
  chartSlide: {
    width: width,
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
});

export default ChartWidget;