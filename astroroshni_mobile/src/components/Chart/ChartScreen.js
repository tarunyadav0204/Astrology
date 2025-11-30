import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Modal,
  TouchableOpacity,
  ScrollView,
  StatusBar,
  Animated,
  Dimensions,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import Ionicons from '@expo/vector-icons/Ionicons';
import { PanGestureHandler, State, GestureHandlerRootView } from 'react-native-gesture-handler';

import { COLORS } from '../../utils/constants';
import { storage } from '../../services/storage';
import { chartAPI } from '../../services/api';
import ChartWidget from './ChartWidget';
import CascadingDashaBrowser from '../Dasha/CascadingDashaBrowser';

const { width, height } = Dimensions.get('window');

export default function ChartScreen({ visible, onClose }) {
  const [birthData, setBirthData] = useState(null);
  const [chartData, setChartData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showDashaBrowser, setShowDashaBrowser] = useState(false);
  const [activeChartIndex, setActiveChartIndex] = useState(0);
  const chartScrollRef = useRef(null);
  const bottomNavScrollRef = useRef(null);
  
  const chartTypes = [
    { id: 'lagna', name: 'Lagna (D1)', icon: '🏠', description: 'Main Birth Chart' },
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
  
  const handleSwipe = (event) => {
    if (event.nativeEvent.state === State.END) {
      const { translationX } = event.nativeEvent;
      const swipeThreshold = 50;
      
      if (translationX > swipeThreshold && activeChartIndex > 0) {
        // Swipe right - previous chart
        const newIndex = activeChartIndex - 1;
        setActiveChartIndex(newIndex);
        scrollToActiveTab(newIndex);
      } else if (translationX < -swipeThreshold && activeChartIndex < chartTypes.length - 1) {
        // Swipe left - next chart
        const newIndex = activeChartIndex + 1;
        setActiveChartIndex(newIndex);
        scrollToActiveTab(newIndex);
      }
    }
  };
  
  const scrollToActiveTab = (index) => {
    if (bottomNavScrollRef.current) {
      const tabWidth = 76; // minWidth (60) + paddingHorizontal (24) + marginHorizontal (8)
      const scrollX = Math.max(0, (index * tabWidth) - (width / 2) + (tabWidth / 2));
      setTimeout(() => {
        bottomNavScrollRef.current.scrollTo({ x: scrollX, animated: true });
      }, 100);
    }
  };

  useEffect(() => {
    if (visible) {
      loadBirthData();
      startAnimations();
    }
  }, [visible]);
  
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
      
      // Always use current birth data from storage (most up-to-date)
      const data = await storage.getBirthDetails();
      console.log('ChartScreen - Birth data from storage:', data);
      if (data && data.name) {
        setBirthData(data);
        await calculateChart(data);
      } else {
        console.log('ChartScreen - No valid birth data found');
      }
    } catch (error) {
      console.error('ChartScreen - Error loading birth data:', error);
    } finally {
      setLoading(false);
    }
  };

  const calculateChart = async (data) => {
    try {
      console.log('ChartScreen - Calculating chart for:', data);
      
      // Format data properly for API
      const formattedData = {
        ...data,
        date: typeof data.date === 'string' ? data.date.split('T')[0] : data.date,
        time: typeof data.time === 'string' ? data.time.split('T')[1]?.slice(0, 5) || data.time : data.time,
        latitude: parseFloat(data.latitude),
        longitude: parseFloat(data.longitude),
        timezone: data.timezone || 'Asia/Kolkata'
      };
      
      console.log('ChartScreen - Formatted data:', formattedData);
      const response = await chartAPI.calculateChartOnly(formattedData);
      const chartResult = response.data;
      console.log('ChartScreen - Chart calculated successfully');
      
      setChartData(chartResult);
    } catch (error) {
      console.error('ChartScreen - Error calculating chart:', error);
    }
  };

  return (
    <Modal visible={visible} animationType="slide" onRequestClose={onClose}>
      <StatusBar barStyle="light-content" backgroundColor="#1a0033" translucent={false} />
      <LinearGradient colors={['#1a0033', '#2d1b4e', '#4a2c6d', '#ff6b35']} style={styles.container}>
        
        {/* Compact Header */}
        <View style={styles.compactHeader}>
          <TouchableOpacity style={styles.closeButton} onPress={onClose}>
            <Ionicons name="close" size={20} color={COLORS.white} />
          </TouchableOpacity>
          <View style={styles.headerCenter}>
            <Text style={styles.chartName}>{chartTypes[activeChartIndex]?.name}</Text>
            <Text style={styles.nativeName}>{birthData?.name}</Text>
          </View>
          <View style={styles.chartPosition}>
            <Text style={styles.positionText}>{activeChartIndex + 1}/{chartTypes.length}</Text>
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
                  {(() => {
                    const chart = chartTypes[activeChartIndex];
                    if (chart.id === 'transit') {
                      return (
                        <ChartWidget 
                          chartData={chartData}
                          birthData={birthData}
                          defaultStyle="north"
                          showTransits={true}
                          disableSwipe={true}
                          hideHeader={true}
                          cosmicTheme={true}
                          chartType="transit"
                          onOpenDasha={() => setShowDashaBrowser(true)}
                          onNavigateToTransit={() => {
                            const transitIndex = chartTypes.findIndex(chart => chart.id === 'transit');
                            if (transitIndex !== -1) {
                              setActiveChartIndex(transitIndex);
                              scrollToActiveTab(transitIndex);
                            }
                          }}
                        />
                      );
                    } else if (chart.id === 'lagna') {
                      return (
                        <ChartWidget 
                          chartData={chartData}
                          birthData={birthData}
                          defaultStyle="north"
                          disableSwipe={true}
                          hideHeader={true}
                          cosmicTheme={true}
                          chartType="lagna"
                          onOpenDasha={() => setShowDashaBrowser(true)}
                          onNavigateToTransit={() => {
                            const transitIndex = chartTypes.findIndex(chart => chart.id === 'transit');
                            if (transitIndex !== -1) {
                              setActiveChartIndex(transitIndex);
                              scrollToActiveTab(transitIndex);
                            }
                          }}
                        />
                      );
                    } else {
                      return (
                        <ChartWidget 
                          chartData={chartData}
                          birthData={birthData}
                          defaultStyle="north"
                          disableSwipe={true}
                          hideHeader={true}
                          cosmicTheme={true}
                          chartType={chart.id}
                          onOpenDasha={() => setShowDashaBrowser(true)}
                          onNavigateToTransit={() => {
                            const transitIndex = chartTypes.findIndex(chart => chart.id === 'transit');
                            if (transitIndex !== -1) {
                              setActiveChartIndex(transitIndex);
                              scrollToActiveTab(transitIndex);
                            }
                          }}
                          division={chart.id === 'navamsa' ? 9 : 
                                   chart.id === 'dashamsa' ? 10 :
                                   chart.id === 'dwadashamsa' ? 12 :
                                   chart.id === 'shodamsa' ? 16 :
                                   chart.id === 'vimsamsa' ? 20 :
                                   chart.id === 'chaturvimsamsa' ? 24 :
                                   chart.id === 'trimsamsa' ? 30 :
                                   chart.id === 'khavedamsa' ? 40 :
                                   chart.id === 'akshavedamsa' ? 45 :
                                   chart.id === 'shashtyamsa' ? 60 : 1}
                        />
                      );
                    }
                  })()} 
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
                    style={[styles.navPill, activeChartIndex === index && styles.navPillActive]}
                    onPress={() => {
                      setActiveChartIndex(index);
                      scrollToActiveTab(index);
                    }}
                  >
                    <Text style={[styles.navIcon, activeChartIndex === index && styles.navIconActive]}>
                      {chart.icon}
                    </Text>
                    <Text style={[styles.navText, activeChartIndex === index && styles.navTextActive]}>
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
      </LinearGradient>
      
      <CascadingDashaBrowser 
        visible={showDashaBrowser} 
        onClose={() => setShowDashaBrowser(false)}
        birthData={birthData}
      />
    </Modal>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  
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
  },
  chartWrapper: {
    flex: 1,
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