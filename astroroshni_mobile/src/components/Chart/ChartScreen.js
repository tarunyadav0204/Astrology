import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  FlatList,
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
import NativeSelectorChip from '../Common/NativeSelectorChip';
import { useTheme } from '../../context/ThemeContext';
import { useTranslation } from 'react-i18next';
import { useAnalytics } from '../../hooks/useAnalytics';

const { width, height } = Dimensions.get('window');

export default function ChartScreen({ navigation, route }) {
  const { t } = useTranslation();
  useAnalytics('ChartScreen');
  const { theme, colors } = useTheme();
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
    { id: 'trimsamsa', name: t('chartTypes.trimsamsa.name'), icon: '⚠️', description: t('chartTypes.trimsamsa.description') },
    { id: 'khavedamsa', name: t('chartTypes.khavedamsa.name'), icon: '🍀', description: t('chartTypes.khavedamsa.description') },
    { id: 'akshavedamsa', name: t('chartTypes.akshavedamsa.name'), icon: '🎭', description: t('chartTypes.akshavedamsa.description') },
    { id: 'shashtyamsa', name: t('chartTypes.shashtyamsa.name'), icon: '⏰', description: t('chartTypes.shashtyamsa.description') },
  ];
  
  console.log('[ChartScreen] Chart types loaded:', chartTypes.map(c => c.id));
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
      return cachedChart;
    }
    
    // If it's the main chart (lagna), return the state data
    if (chartType === 'lagna') {
      return chartData;
    }

    // Return null for other charts if not cached - forces ChartWidget to fetch
    return null; 
  }, [birthData, chartData]);
  
  const scrollToActiveTab = useCallback((index) => {
    if (bottomNavScrollRef.current) {
      try {
        bottomNavScrollRef.current.scrollToIndex({ index, animated: true, viewPosition: 0.5 });
      } catch (e) {
        // Fallback if scrollToIndex fails
      }
    }
  }, []);

  useEffect(() => {
    loadBirthData();
    startAnimations();
  }, []);
  
  // Add focus effect to reload data when screen comes into focus
  useEffect(() => {
    const unsubscribe = navigation.addListener('focus', () => {
      // console.log('📊 ChartScreen focused - reloading birth data');
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
      // console.log('📊 ChartScreen loading data for:', data?.name, 'ID:', data?.id);
      
      if (data && data.name) {
        setBirthData(data);
        
        // Calculate fresh chart directly without any caching
        const formattedData = {
          name: data.name,
          date: typeof data.date === 'string' ? data.date.split('T')[0] : data.date,
          time: typeof data.time === 'string' ? data.time.split('T')[1]?.slice(0, 5) || data.time : data.time,
          latitude: parseFloat(data.latitude),
          longitude: parseFloat(data.longitude)
        };
        
        // console.log('🚀 Calculating chart for ID:', data.id, 'Name:', data.name);
        const response = await chartAPI.calculateChartOnly(formattedData);
        setChartData(response.data);
        // console.log('✅ Chart calculated - Ascendant:', response.data.ascendant);
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
        longitude: parseFloat(data.longitude)
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
      <StatusBar barStyle={colors.statusBarStyle} backgroundColor={colors.background} translucent={false} />
      <LinearGradient colors={theme === 'dark' ? [colors.gradientStart, colors.gradientMid, colors.gradientEnd, colors.primary] : [colors.gradientStart, colors.gradientStart, colors.gradientStart, colors.gradientStart]} style={styles.container}>
        <SafeAreaView style={styles.safeArea}>
        {/* Compact Header */}
        <View style={styles.compactHeader}>
          <TouchableOpacity onPress={() => navigation.goBack()} style={[styles.closeButton, { backgroundColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.15)' : 'rgba(249, 115, 22, 0.25)' }]}>
            <Ionicons name="close" size={20} color={colors.text} />
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
          <View style={[styles.chartPosition, { backgroundColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.15)' : 'rgba(249, 115, 22, 0.25)' }]}>
            <Text style={[styles.positionText, { color: colors.text }]}>{currentChartIndex + 1}/{chartTypes.length}</Text>
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
              <Text style={[styles.loadingText, { color: colors.text }]}>{t('chartScreen.loadingText')}</Text>
              <Text style={[styles.loadingSubtext, { color: colors.textSecondary }]}>{t('chartScreen.loadingSubtext')}</Text>
            </View>
          </View>
        ) : chartData && birthData ? (
          <View style={styles.mainContent}>
            {/* Chart Display */}
            <GestureHandlerRootView style={styles.chartArea}>
              <PanGestureHandler onHandlerStateChange={handleSwipe}>
                <Animated.View style={styles.chartWrapper}>

                  <ChartWidget 
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
                    onNavigateToTransit={() => {
                      const transitIndex = chartTypes.findIndex(chart => chart.id === 'transit');
                      if (transitIndex !== -1) {
                        setCurrentChartIndex(transitIndex);
                        scrollToActiveTab(transitIndex);
                      }
                    }}
                    navigation={navigation}
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
            <FlatList
              ref={bottomNavScrollRef}
              horizontal
              showsHorizontalScrollIndicator={false}
              data={chartTypes}
              keyExtractor={(item) => item.id}
              renderItem={({ item: chart, index }) => (
                <TouchableOpacity
                  key={chart.id}
                  style={[
                    styles.navPill,
                    { backgroundColor: theme === 'dark' ? 'rgba(0, 0, 0, 0.4)' : 'rgba(249, 115, 22, 0.15)', borderColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.2)' : 'rgba(249, 115, 22, 0.3)' },
                    currentChartIndex === index && (theme === 'dark' ? styles.navPillActive : styles.navPillActiveLight)
                  ]}
                  onPress={() => changeChart(index)}
                  activeOpacity={0.7}
                >
                  <Text style={[styles.navIcon, currentChartIndex === index && styles.navIconActive]}>
                    {chart.icon}
                  </Text>
                  <Text style={[styles.navText, { color: theme === 'dark' ? 'rgba(255, 255, 255, 0.7)' : 'rgba(0, 0, 0, 0.7)' }, currentChartIndex === index && styles.navTextActive]}>
                    {chart.name.split(' ')[0]}
                  </Text>
                </TouchableOpacity>
              )}
              contentContainerStyle={styles.navContent}
              style={styles.bottomNav}
            />
          </View>
        ) : (
          <View style={styles.emptyContainer}>
            <Text style={styles.emptyIcon}>📊</Text>
            <Text style={[styles.emptyTitle, { color: colors.text }]}>{t('chartScreen.emptyTitle')}</Text>
            <Text style={[styles.emptyText, { color: colors.textSecondary }]}>{t('chartScreen.emptyText')}</Text>
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
    marginTop: 4,
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
  },
  positionText: {
    fontSize: 11,
    fontWeight: '600',
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
    textAlign: 'center',
    marginBottom: 8,
  },
  loadingSubtext: {
    fontSize: 14,
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
  },
  navContent: {
    paddingHorizontal: 4,
  },
  navPill: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
    marginHorizontal: 4,
    borderWidth: 1,
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
  navPillActiveLight: {
    backgroundColor: '#f97316',
    borderColor: '#f97316',
    shadowColor: '#f97316',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.3,
    shadowRadius: 4,
    elevation: 4,
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
    fontWeight: '500',
    textAlign: 'center',
  },
  navTextActive: {
    color: '#fff',
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
    marginBottom: 8,
  },
  emptyText: {
    fontSize: 14,
    textAlign: 'center',
  },
});