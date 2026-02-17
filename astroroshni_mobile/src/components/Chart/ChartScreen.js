import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  FlatList,
  StatusBar,
  Animated,
  Dimensions,
  Platform,
  Image,
  Alert,
} from 'react-native';
import { PanGestureHandler, State, GestureHandlerRootView, ScrollView } from 'react-native-gesture-handler';
import { BlurView } from 'expo-blur';
import { captureRef } from 'react-native-view-shot';
import * as Sharing from 'expo-sharing';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import Ionicons from '@expo/vector-icons/Ionicons';

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
  const bottomNavScrollRef = useRef(null);
  const lastSwipeTime = useRef(0);
  const captureViewRef = useRef(null);
  const [isSharing, setIsSharing] = useState(false);
  const rotateAnim = useRef(new Animated.Value(0)).current;
  
  const handleShare = async () => {
    if (isSharing) return;
    try {
      setIsSharing(true);
      const uri = await captureRef(captureViewRef, {
        format: 'png',
        quality: 1.0,
        result: 'tmpfile',
      });
      if (await Sharing.isAvailableAsync()) {
        await Sharing.shareAsync(uri, {
          mimeType: 'image/png',
          dialogTitle: `Cosmic Blueprint - ${birthData?.name}`,
          UTI: 'public.png',
        });
      } else {
        Alert.alert('Sharing not available', 'Sharing is not supported on this device.');
      }
    } catch (error) {
      console.error('Error sharing chart:', error);
      Alert.alert('Error', 'Failed to generate shareable image.');
    } finally {
      setIsSharing(false);
    }
  };
  
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
  
  const handleSwipe = useCallback((event) => {
    if (event.nativeEvent.state === State.END) {
      const now = Date.now();
      const { translationX } = event.nativeEvent;
      const swipeThreshold = 50;
      if (now - lastSwipeTime.current < 100) return;
      lastSwipeTime.current = now;
      let newIndex = currentChartIndex;
      if (translationX > swipeThreshold && currentChartIndex > 0) {
        newIndex = currentChartIndex - 1;
      } else if (translationX < -swipeThreshold && currentChartIndex < chartTypes.length - 1) {
        newIndex = currentChartIndex + 1;
      }
      if (newIndex !== currentChartIndex) {
        changeChart(newIndex);
      }
    }
  }, [currentChartIndex, chartTypes.length]);
  
  const changeChart = useCallback((newIndex) => {
    setCurrentChartIndex(newIndex);
    if (bottomNavScrollRef.current) {
      const pillWidth = 100;
      bottomNavScrollRef.current.scrollTo({ x: newIndex * pillWidth - (width / 2) + (pillWidth / 2), animated: true });
    }
  }, []);
  
  const getChartDataForType = useCallback((chartType) => {
    if (!birthData) return null;
    const cachedChart = chartPreloader.getChart(birthData, chartType);
    if (cachedChart) return cachedChart;
    if (chartType === 'lagna') return chartData;
    return null; 
  }, [birthData, chartData]);
  
  useEffect(() => {
    loadBirthData();
    startAnimations();
  }, []);
  
  useEffect(() => {
    const unsubscribe = navigation.addListener('focus', () => {
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
      const data = await storage.getBirthDetails();
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
        setChartData(response.data);
      }
    } catch (error) {
      console.error('ChartScreen - Error loading birth data:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <View style={styles.container}>
        <StatusBar barStyle={colors.statusBarStyle} backgroundColor={colors.background} translucent={false} />
        <LinearGradient colors={theme === 'dark' ? [colors.gradientStart, colors.gradientMid, colors.gradientEnd, colors.primary] : [colors.gradientStart, colors.gradientStart, colors.gradientStart, colors.gradientStart]} style={styles.container}>
          <SafeAreaView style={styles.safeArea} edges={['top']}>
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
              <TouchableOpacity 
                onPress={handleShare} 
                disabled={isSharing}
                style={[styles.shareButton, { backgroundColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.15)' : 'rgba(249, 115, 22, 0.25)' }]}
              >
                <Ionicons name={isSharing ? "hourglass-outline" : "share-social-outline"} size={20} color={colors.text} />
              </TouchableOpacity>
            </View>

            {loading ? (
              <View style={styles.loadingContainer}>
                <View style={styles.loadingContent}>
                  <Animated.View style={[styles.loadingOrb, { transform: [{ rotate: spin }] }]}>
                    <LinearGradient colors={['#ff6b35', '#ffd700']} style={styles.loadingOrbGradient}>
                      <Text style={styles.loadingOrbIcon}>✨</Text>
                    </LinearGradient>
                  </Animated.View>
                  <Text style={[styles.loadingText, { color: colors.text }]}>{t('chartScreen.loadingText')}</Text>
                  <Text style={[styles.loadingSubtext, { color: colors.textSecondary }]}>{t('chartScreen.loadingSubtext')}</Text>
                </View>
              </View>
            ) : chartData && birthData ? (
              <View style={styles.mainContent}>
                <View style={styles.chartAndNavContainer}>
                  <PanGestureHandler 
                    onHandlerStateChange={handleSwipe}
                    activeOffsetX={[-20, 20]}
                    failOffsetY={[-20, 20]}
                  >
                    <View style={{ flex: 1 }}>
                      <View ref={captureViewRef} collapsable={false} style={styles.captureArea}>
                        <LinearGradient
                          colors={theme === 'dark' ? ['#1a0033', '#2d1b4e'] : ['#ffffff', '#fff5f0']}
                          style={styles.captureGradient}
                        >
                          <View style={styles.captureHeader}>
                            <Image source={require('../../../assets/logo.png')} style={styles.captureLogo} resizeMode="contain" />
                            <View>
                              <Text style={[styles.captureTitle, { color: colors.text }]}>Cosmic Blueprint</Text>
                              <Text style={[styles.captureName, { color: colors.primary }]}>{birthData?.name}</Text>
                            </View>
                          </View>

                          <View style={styles.chartArea}>
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
                                  if (transitIndex !== -1) changeChart(transitIndex);
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
                          </View>

                          <View style={styles.captureFooter}>
                            <Text style={[styles.captureFooterText, { color: colors.textSecondary }]}>Generated by AstroRoshni</Text>
                          </View>
                        </LinearGradient>
                      </View>
                    </View>
                  </PanGestureHandler>

                  <View style={[styles.bottomNavContainer, { 
                    backgroundColor: theme === 'dark' ? 'rgba(26, 0, 51, 0.95)' : 'rgba(255, 255, 255, 0.95)',
                    borderTopColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.05)',
                  }]}>
                    {Platform.OS === 'ios' && (
                      <BlurView intensity={theme === 'dark' ? 40 : 60} style={StyleSheet.absoluteFill} tint={theme === 'dark' ? 'dark' : 'light'} />
                    )}
                    <ScrollView
                      ref={bottomNavScrollRef}
                      horizontal
                      showsHorizontalScrollIndicator={false}
                      contentContainerStyle={styles.navContent}
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
        <CascadingDashaBrowser visible={showDashaBrowser} onClose={() => setShowDashaBrowser(false)} birthData={birthData} />
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
  },
  chartAndNavContainer: {
    flex: 1,
  },
  captureArea: {
    flex: 1,
  },
  captureGradient: {
    flex: 1,
    padding: 16,
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
    paddingHorizontal: 16,
  },
  chartWrapper: {
    flex: 1,
  },
  captureFooter: {
    alignItems: 'center',
    marginTop: 16,
    paddingBottom: 90, // Space for bottom nav
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
    paddingBottom: 15,
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
});
