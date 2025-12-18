import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  StatusBar,
  Animated,
  Dimensions,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import Ionicons from '@expo/vector-icons/Ionicons';
import { PanGestureHandler, State, GestureHandlerRootView } from 'react-native-gesture-handler';

import { COLORS } from '../../utils/constants';
import { storage } from '../../services/storage';
import { chartAPI } from '../../services/api';
import { chartPreloader } from '../../services/chartPreloader';
import ChartWidget from './ChartWidget';
import CascadingDashaBrowser from '../Dasha/CascadingDashaBrowser';

const { width, height } = Dimensions.get('window');

export default function ChartScreen({ navigation, route }) {
  const [birthData, setBirthData] = useState(null);
  const [chartData, setChartData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showDashaBrowser, setShowDashaBrowser] = useState(false);
  const [currentChartIndex, setCurrentChartIndex] = useState(0);
  const chartScrollRef = useRef(null);
  const bottomNavScrollRef = useRef(null);
  const swipeTimeoutRef = useRef(null);
  const lastSwipeTime = useRef(0);
  
  const chartTypes = [
    { id: 'lagna', name: 'Lagna (D1)', icon: '🏠', description: 'Main Birth Chart' },
    { id: 'hora', name: 'Hora (D2)', icon: '💰', description: 'Wealth & Family' },
    { id: 'drekkana', name: 'Drekkana (D3)', icon: '👫', description: 'Siblings & Happiness' },
    { id: 'chaturthamsa', name: 'Chaturthamsa (D4)', icon: '🏡', description: 'Destiny & Assets' },
    { id: 'navamsa', name: 'Navamsa (D9)', icon: '💎', description: 'Marriage & Spirituality' },
    { id: 'dashamsa', name: 'Dashamsa (D10)', icon: '💼', description: 'Career & Profession' },
    { id: 'dwadashamsa', name: 'Dwadashamsa (D12)', icon: '👨👩👧👦', description: 'Parents & Ancestry' },
    { id: 'shodamsa', name: 'Shodamsa (D16)', icon: '🚗', description: 'Vehicles & Comforts' },
    { id: 'vimsamsa', name: 'Vimsamsa (D20)', icon: '🙏', description: 'Spiritual Practices' },
    { id: 'chaturvimsamsa', name: 'Chaturvimsamsa (D24)', icon: '📚', description: 'Learning & Education' },
    { id: 'trimsamsa', name: 'Trimsamsa (D30)', icon: '⚠️', description: 'Misfortunes & Troubles' },
    { id: 'khavedamsa', name: 'Khavedamsa (D40)', icon: '🍀', description: 'Auspicious & Inauspicious' },
    { id: 'akshavedamsa', name: 'Akshavedamsa (D45)', icon: '🎭', description: 'Character & Conduct' },
    { id: 'shashtyamsa', name: 'Shashtyamsa (D60)', icon: '⏰', description: 'Past Life Karma' },
    { id: 'transit', name: 'Transit', icon: '🪐', description: 'Live Planetary Positions' },
  ];
  const chartWidgetRef = useRef(null);
  
  const fadeAnim = useRef(new Animated.Value(1)).current;
  const slideAnim = useRef(new Animated.Value(0)).current;
  const scaleAnim = useRef(new Animated.Value(1)).current;
  const rotateAnim = useRef(new Animated.Value(0)).current;
  
  const handleSwipe = useCallback((event) => {
    if (event.nativeEvent.state === State.END) {
      const now = Date.now();
      const { translationX } = event.nativeEvent;
      const swipeThreshold = 50;
      
      // Prevent swipes faster than 100ms
      if (now - lastSwipeTime.current < 100) {
        return;
      }
      lastSwipeTime.current = now;
      
      let newIndex = currentChartIndex;
      
      if (translationX > swipeThreshold && currentChartIndex > 0) {
        newIndex = currentChartIndex - 1;
      } else if (translationX < -swipeThreshold && currentChartIndex < chartTypes.length - 1) {
        newIndex = currentChartIndex + 1;
      }
      
      if (newIndex !== currentChartIndex) {
        setCurrentChartIndex(newIndex);
        scrollToActiveTab(newIndex);
      }
    }
  }, [currentChartIndex]);
  
  const changeChart = useCallback((newIndex) => {
    if (newIndex === currentChartIndex) return;
    setCurrentChartIndex(newIndex);
    scrollToActiveTab(newIndex);
  }, [currentChartIndex]);
  
  const getChartDataForType = useCallback((chartType) => {
    if (!birthData) return null;
    
    // Get from preloader cache
    const cachedChart = chartPreloader.getChart(birthData, chartType);
    if (cachedChart) {
      console.log(`Using cached data for ${chartType}`);
      return cachedChart;
    }
    
    // If it's the main chart (lagna), return the state data
    if (chartType === 'lagna') return chartData;

    // CRITICAL FIX: Return null for other charts if not cached.
    // This forces ChartWidget to fetch the data itself instead of showing Lagna.
    console.log(`No cached data for ${chartType}, returning null`);
    return null; 
  }, [birthData, chartData]);
  
  const scrollToActiveTab = useCallback((index) => {
    if (bottomNavScrollRef.current) {
      const tabWidth = 76;
      const scrollX = Math.max(0, (index * tabWidth) - (width / 2) + (tabWidth / 2));
      bottomNavScrollRef.current.scrollTo({ x: scrollX, animated: true });
    }
  }, []);

  useEffect(() => {
    loadBirthData();
    startAnimations();
  }, []);
  
  // Add focus effect to reload data when screen comes into focus
  useEffect(() => {
    const unsubscribe = navigation.addListener('focus', () => {
      console.log('📊 ChartScreen focused - reloading birth data');
      loadBirthData();
    });
    
    return unsubscribe;
  }, [navigation]);
  
  const startAnimations = () => {
    Animated.loop(
      Animated.timing(rotateAnim, {
        toValue: 1,
        duration: 20000,
        useNativeDriver: true,
      })
    ).start();
  };
  
  const spin = rotateAnim.interpolate({
    inputRange: [0, 1],
    outputRange: ['0deg', '360deg'],
  });

  const loadBirthData = async () => {
    try {
      setLoading(true);
      
      // Get fresh data from storage
      const data = await storage.getBirthDetails();
      console.log('📊 ChartScreen loading data for:', data?.name, 'ID:', data?.id);
      
      if (data && data.name) {
        setBirthData(data);
        
        // Calculate fresh chart directly without any caching
        const formattedData = {
          name: data.name,
          date: typeof data.date === 'string' ? data.date.split('T')[0] : data.date,
          time: typeof data.time === 'string' ? data.time.split('T')[1]?.slice(0, 5) || data.time : data.time,
          latitude: parseFloat(data.latitude),
          longitude: parseFloat(data.longitude),
          timezone: data.timezone || 'Asia/Kolkata'
        };
        
        console.log('🚀 Calculating chart for ID:', data.id, 'Name:', data.name);
        const response = await chartAPI.calculateChartOnly(formattedData);
        setChartData(response.data);
        console.log('✅ Chart calculated - Ascendant:', response.data.ascendant);
      } else {
        console.log('⚠️ No birth data found in storage');
      }
    } catch (error) {
      console.error('ChartScreen - Error loading birth data:', error);
    } finally {
      setLoading(false);
    }
  };

  const preloadAllCharts = async (data) => {
    try {
      // Format data properly for API
      const formattedData = {
        ...data,
        date: typeof data.date === 'string' ? data.date.split('T')[0] : data.date,
        time: typeof data.time === 'string' ? data.time.split('T')[1]?.slice(0, 5) || data.time : data.time,
        latitude: parseFloat(data.latitude),
        longitude: parseFloat(data.longitude),
        timezone: data.timezone || 'Asia/Kolkata'
      };
      
      // Pre-load all charts at once
      const allCharts = await chartPreloader.preloadAllCharts(formattedData);
      setChartData(allCharts.lagna); // Set initial chart data
      
    } catch (error) {
      console.error('ChartScreen - Error preloading charts:', error);
      // Fallback to individual calculation
      try {
        const response = await chartAPI.calculateChartOnly(formattedData);
        setChartData(response.data);
      } catch (fallbackError) {
        console.error('ChartScreen - Fallback calculation failed:', fallbackError);
      }
    }
  };

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#1a0033" translucent={false} />
      <LinearGradient colors={['#1a0033', '#2d1b4e', '#4a2c6d', '#ff6b35']} style={styles.container}>
        <SafeAreaView style={styles.safeArea}>
        {/* Compact Header */}
        <View style={styles.compactHeader}>
          <TouchableOpacity onPress={() => navigation.goBack()} style={styles.closeButton}>
            <Ionicons name="close" size={20} color={COLORS.white} />
          </TouchableOpacity>
          <View style={styles.headerCenter}>
            <Text style={styles.chartName}>{chartTypes[currentChartIndex]?.name}</Text>
            <Text style={styles.nativeName}>{birthData?.name}</Text>
          </View>
          <View style={styles.chartPosition}>
            <Text style={styles.positionText}>{currentChartIndex + 1}/{chartTypes.length}</Text>
          </View>
        </View>

        {loading ? (
          <View style={styles.loadingContainer}>
            <View style={styles.loadingContent}>
              <Animated.View style={[styles.loadingOrb, { transform: [{ rotate: spin }] }]}>
                <LinearGradient
                  colors={['#ff6b35', '#ffd700']}
                  style={styles.loadingOrbGradient}
                >
                  <Text style={styles.loadingOrbIcon}>✨</Text>
                </LinearGradient>
              </Animated.View>
              <Text style={styles.loadingText}>Calculating Cosmic Alignments...</Text>
              <Text style={styles.loadingSubtext}>Reading planetary positions</Text>
            </View>
          </View>
        ) : chartData && birthData ? (
          <View style={styles.mainContent}>
            {/* Chart Display */}
            <GestureHandlerRootView style={styles.chartArea}>
              <PanGestureHandler onHandlerStateChange={handleSwipe}>
                <Animated.View style={styles.chartWrapper}>

                  <ChartWidget 
                    key={currentChartIndex}
                    chartData={getChartDataForType(chartTypes[currentChartIndex].id)}
                    birthData={birthData}
                    defaultStyle="north"
                    showTransits={chartTypes[currentChartIndex].id === 'transit'}
                    disableSwipe={true}
                    hideHeader={true}
                    cosmicTheme={true}
                    chartType={chartTypes[currentChartIndex].id}
                    onOpenDasha={() => setShowDashaBrowser(true)}
                    onNavigateToTransit={() => {
                      const transitIndex = chartTypes.findIndex(chart => chart.id === 'transit');
                      if (transitIndex !== -1) {
                        setCurrentChartIndex(transitIndex);
                        scrollToActiveTab(transitIndex);
                      }
                    }}
                    division={chartTypes[currentChartIndex].id === 'hora' ? 2 :
                             chartTypes[currentChartIndex].id === 'drekkana' ? 3 :
                             chartTypes[currentChartIndex].id === 'chaturthamsa' ? 4 :
                             chartTypes[currentChartIndex].id === 'navamsa' ? 9 : 
                             chartTypes[currentChartIndex].id === 'dashamsa' ? 10 :
                             chartTypes[currentChartIndex].id === 'dwadashamsa' ? 12 :
                             chartTypes[currentChartIndex].id === 'shodamsa' ? 16 :
                             chartTypes[currentChartIndex].id === 'vimsamsa' ? 20 :
                             chartTypes[currentChartIndex].id === 'chaturvimsamsa' ? 24 :
                             chartTypes[currentChartIndex].id === 'trimsamsa' ? 30 :
                             chartTypes[currentChartIndex].id === 'khavedamsa' ? 40 :
                             chartTypes[currentChartIndex].id === 'akshavedamsa' ? 45 :
                             chartTypes[currentChartIndex].id === 'shashtyamsa' ? 60 : 1}
                  /> 
                </Animated.View>
              </PanGestureHandler>
            </GestureHandlerRootView>
            
            {/* Floating Bottom Navigation */}
            <View style={styles.bottomNav}>
              <ScrollView 
                ref={bottomNavScrollRef}
                horizontal 
                showsHorizontalScrollIndicator={false}
                contentContainerStyle={styles.navContent}
              >
                {chartTypes.map((chart, index) => (
                  <TouchableOpacity
                    key={chart.id}
                    style={[
                      styles.navPill, 
                      currentChartIndex === index && styles.navPillActive
                    ]}
                    onPress={() => changeChart(index)}
                    disabled={false}
                  >
                    <Text style={[styles.navIcon, currentChartIndex === index && styles.navIconActive]}>
                      {chart.icon}
                    </Text>
                    <Text style={[styles.navText, currentChartIndex === index && styles.navTextActive]}>
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
            <Text style={styles.emptyTitle}>No Chart Data</Text>
            <Text style={styles.emptyText}>Please add birth details to view charts</Text>
          </View>
        )}
        </SafeAreaView>
      </LinearGradient>
      
      <CascadingDashaBrowser 
        visible={showDashaBrowser} 
        onClose={() => setShowDashaBrowser(false)}
        birthData={birthData}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  safeArea: { flex: 1 },
  
  // Compact Header
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
    backgroundColor: 'rgba(255, 255, 255, 0.15)',
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
    color: COLORS.white,
    textAlign: 'center',
  },
  nativeName: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.7)',
    marginTop: 2,
  },
  chartPosition: {
    backgroundColor: 'rgba(255, 255, 255, 0.15)',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  positionText: {
    fontSize: 11,
    fontWeight: '600',
    color: COLORS.white,
  },
  
  // Loading Styles
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
    color: COLORS.white,
    textAlign: 'center',
    marginBottom: 8,
  },
  loadingSubtext: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.7)',
    textAlign: 'center',
  },
  
  // Main Content
  mainContent: {
    flex: 1,
  },
  chartArea: {
    flex: 1,
    paddingHorizontal: 16,
    paddingBottom: 100,
  },
  chartWrapper: {
    flex: 1,
  },
  transitionOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.3)',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 1000,
  },
  transitionSpinner: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(255, 107, 53, 0.9)',
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#ff6b35',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.6,
    shadowRadius: 8,
    elevation: 6,
  },
  transitionIcon: {
    fontSize: 20,
    color: '#fff',
  },
  
  // Bottom Navigation
  bottomNav: {
    position: 'absolute',
    bottom: 20,
    left: 0,
    right: 0,
    paddingHorizontal: 20,
  },
  navContent: {
    alignItems: 'center',
    paddingHorizontal: 10,
  },
  navPill: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
    backgroundColor: 'rgba(0, 0, 0, 0.4)',
    alignItems: 'center',
    justifyContent: 'center',
    marginHorizontal: 4,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.2)',
    minWidth: 60,
    opacity: 1,
  },
  navPillActive: {
    backgroundColor: 'rgba(255, 107, 53, 0.8)',
    borderColor: 'rgba(255, 107, 53, 1)',
    shadowColor: '#ff6b35',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.6,
    shadowRadius: 8,
    elevation: 6,
  },

  navIcon: {
    fontSize: 16,
    marginBottom: 2,
  },
  navIconActive: {
    fontSize: 16,
    marginBottom: 2,
  },
  navText: {
    fontSize: 10,
    color: 'rgba(255, 255, 255, 0.7)',
    fontWeight: '500',
    textAlign: 'center',
  },
  navTextActive: {
    color: COLORS.white,
    fontWeight: '700',
  },
  
  // Empty State
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
    color: COLORS.white,
    marginBottom: 8,
  },
  emptyText: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.7)',
    textAlign: 'center',
  },
});