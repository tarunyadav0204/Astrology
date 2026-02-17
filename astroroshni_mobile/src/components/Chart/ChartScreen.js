import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  StatusBar,
  Animated,
  Dimensions,
  Platform,
  Image,
  Alert,
  Modal,
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
  const chartWidgetRef = useRef(null);
  const [isSharing, setIsSharing] = useState(false);
  const rotateAnim = useRef(new Animated.Value(0)).current;
  
  // House Drawer State
  const [selectedHouse, setSelectedHouse] = useState(null);
  const drawerAnim = useRef(new Animated.Value(height)).current;

  // Animation for smooth chart transitions
  const chartTranslateX = useRef(new Animated.Value(0)).current;
  const chartOpacity = useRef(new Animated.Value(1)).current;
  
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
  
  const onGestureEvent = Animated.event(
    [{ nativeEvent: { translationX: chartTranslateX } }],
    { useNativeDriver: true }
  );

  const handleSwipe = useCallback((event) => {
    const { translationX, state, velocityX } = event.nativeEvent;
    
    if (state === State.END) {
      const now = Date.now();
      const swipeThreshold = width * 0.2;
      const velocityThreshold = 500;
      
      if (now - lastSwipeTime.current < 300) return;
      
      let newIndex = currentChartIndex;

      if ((translationX > swipeThreshold || (velocityX > velocityThreshold && translationX > 20)) && currentChartIndex > 0) {
        newIndex = currentChartIndex - 1;
      } else if ((translationX < -swipeThreshold || (velocityX < -velocityThreshold && translationX < -20)) && currentChartIndex < chartTypes.length - 1) {
        newIndex = currentChartIndex + 1;
      }

      if (newIndex !== currentChartIndex) {
        lastSwipeTime.current = now;
        const direction = newIndex > currentChartIndex ? -1 : 1;
        Animated.parallel([
          Animated.timing(chartTranslateX, { toValue: direction * width, duration: 200, useNativeDriver: true }),
          Animated.timing(chartOpacity, { toValue: 0, duration: 200, useNativeDriver: true })
        ]).start(() => {
          setCurrentChartIndex(newIndex);
          scrollToActiveTab(newIndex);
          chartTranslateX.setValue(-direction * width);
          Animated.parallel([
            Animated.spring(chartTranslateX, { toValue: 0, friction: 8, tension: 40, useNativeDriver: true }),
            Animated.timing(chartOpacity, { toValue: 1, duration: 250, useNativeDriver: true })
          ]).start();
        });
      } else {
        Animated.spring(chartTranslateX, { toValue: 0, friction: 6, useNativeDriver: true }).start();
      }
    }
  }, [currentChartIndex, chartTypes.length]);
  
  const changeChart = useCallback((newIndex) => {
    if (newIndex === currentChartIndex) return;
    const direction = newIndex > currentChartIndex ? -1 : 1;
    Animated.parallel([
      Animated.timing(chartTranslateX, { toValue: direction * width, duration: 200, useNativeDriver: true }),
      Animated.timing(chartOpacity, { toValue: 0, duration: 200, useNativeDriver: true })
    ]).start(() => {
      setCurrentChartIndex(newIndex);
      scrollToActiveTab(newIndex);
      chartTranslateX.setValue(-direction * width);
      Animated.parallel([
        Animated.spring(chartTranslateX, { toValue: 0, friction: 8, tension: 40, useNativeDriver: true }),
        Animated.timing(chartOpacity, { toValue: 1, duration: 250, useNativeDriver: true })
      ]).start();
    });
  }, [currentChartIndex]);

  const scrollToActiveTab = useCallback((index) => {
    if (bottomNavScrollRef.current) {
      const pillWidth = 100;
      bottomNavScrollRef.current.scrollTo({ 
        x: index * pillWidth - (width / 2) + (pillWidth / 2), 
        animated: true 
      });
    }
  }, []);
  
  const getChartDataForType = useCallback((chartType) => {
    if (!birthData) return null;
    const cachedChart = chartPreloader.getChart(birthData, chartType);
    if (cachedChart) return cachedChart;
    if (chartType === 'lagna') return chartData;
    return null; 
  }, [birthData, chartData]);

  // House Lord Logic
  const getHouseLord = (rashiIndex) => {
    const lords = ['Mars', 'Venus', 'Mercury', 'Moon', 'Sun', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Saturn', 'Jupiter'];
    return lords[rashiIndex];
  };

  const getHouseSignificance = (houseNum) => {
    const significances = {
      1: { title: t('houses.1.title', '1st House: Self & Appearance'), desc: t('houses.1.desc', 'Represents your personality, physical body, and general path in life.') },
      2: { title: t('houses.2.title', '2nd House: Wealth & Speech'), desc: t('houses.2.desc', 'Governs accumulated wealth, family, speech, and early education.') },
      3: { title: t('houses.3.title', '3rd House: Courage & Siblings'), desc: t('houses.3.desc', 'Represents short travels, siblings, communication, and your own efforts.') },
      4: { title: t('houses.4.title', '4th House: Mother & Comfort'), desc: t('houses.4.desc', 'Governs home, mother, vehicles, happiness, and inner peace.') },
      5: { title: t('houses.5.title', '5th House: Creativity & Children'), desc: t('houses.5.desc', 'Represents intelligence, children, past life merits, and speculation.') },
      6: { title: t('houses.6.title', '6th House: Health & Enemies'), desc: t('houses.6.desc', 'Governs daily routine, health issues, debts, and competition.') },
      7: { title: t('houses.7.title', '7th House: Marriage & Partners'), desc: t('houses.7.desc', 'Represents long-term relationships, marriage, and business partnerships.') },
      8: { title: t('houses.8.title', '8th House: Transformation & Longevity'), desc: t('houses.8.desc', 'Governs sudden changes, longevity, occult, and hidden wealth.') },
      9: { title: t('houses.9.title', '9th House: Luck & Higher Learning'), desc: t('houses.9.desc', 'Represents fortune, father, long travels, and spiritual wisdom.') },
      10: { title: t('houses.10.title', '10th House: Career & Fame'), desc: t('houses.10.desc', 'Governs profession, social status, fame, and authority.') },
      11: { title: t('houses.11.title', '11th House: Gains & Friends'), desc: t('houses.11.desc', 'Represents fulfillment of desires, income, and social circles.') },
      12: { title: t('houses.12.title', '12th House: Loss & Spirituality'), desc: t('houses.12.desc', 'Governs isolation, expenses, foreign lands, and spiritual liberation.') },
    };
    return significances[houseNum];
  };

  const openHouseDrawer = (houseData) => {
    setSelectedHouse(houseData);
    Animated.spring(drawerAnim, {
      toValue: 0,
      friction: 8,
      tension: 40,
      useNativeDriver: true
    }).start();
  };

  const closeHouseDrawer = () => {
    Animated.timing(drawerAnim, {
      toValue: height,
      duration: 300,
      useNativeDriver: true
    }).start(() => setSelectedHouse(null));
  };
  
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
                    onGestureEvent={onGestureEvent}
                    onHandlerStateChange={handleSwipe}
                    activeOffsetX={[-10, 10]}
                    failOffsetY={[-30, 30]}
                  >
                    <Animated.View style={{ flex: 1, opacity: chartOpacity }}>
                      <Animated.View 
                        ref={captureViewRef} 
                        collapsable={false} 
                        style={[
                          styles.captureArea,
                          { transform: [{ translateX: chartTranslateX }] }
                        ]}
                      >
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
                            <View style={styles.chartWrapper}>
                              <ChartWidget 
                                ref={chartWidgetRef}
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
                                onHousePress={openHouseDrawer}
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
                            </View>
                          </View>

                          <View style={styles.captureFooter}>
                            <Text style={[styles.captureFooterText, { color: colors.textSecondary }]}>Generated by AstroRoshni</Text>
                          </View>
                        </LinearGradient>
                      </Animated.View>
                    </Animated.View>
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
                      decelerationRate="fast"
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
        
        {/* House Insights Drawer */}
        <Modal
          visible={!!selectedHouse}
          transparent
          animationType="none"
          onRequestClose={closeHouseDrawer}
        >
          <TouchableOpacity 
            style={styles.drawerOverlay} 
            activeOpacity={1} 
            onPress={closeHouseDrawer}
          >
            <Animated.View 
              style={[
                styles.drawerContent, 
                { 
                  backgroundColor: theme === 'dark' ? 'rgba(26, 0, 51, 0.98)' : 'rgba(255, 255, 255, 0.98)',
                  transform: [{ translateY: drawerAnim }]
                }
              ]}
            >
              <View style={styles.drawerHandle} />
              
              {selectedHouse && (
                <View style={{ height: height * 0.7 }}>
                  <ScrollView 
                    style={{ flex: 1 }}
                    contentContainerStyle={styles.drawerScrollContent}
                    showsVerticalScrollIndicator={false}
                  >
                    {/* House Header */}
                    <View style={styles.drawerHeader}>
                      <View style={[styles.houseNumberBadge, { backgroundColor: colors.primary }]}>
                        <Text style={styles.houseNumberText}>{selectedHouse.houseNum}</Text>
                      </View>
                      <View style={styles.houseTitleContainer}>
                        <Text style={[styles.houseTitle, { color: colors.text }]}>
                          {getHouseSignificance(selectedHouse.houseNum).title}
                        </Text>
                        <Text style={[styles.houseSign, { color: colors.primary }]}>
                          {selectedHouse.signName}
                        </Text>
                      </View>
                    </View>

                    {/* Significance Description */}
                    <View style={[styles.drawerSection, { backgroundColor: theme === 'dark' ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.02)' }]}>
                      <Text style={[styles.sectionTitle, { color: colors.textSecondary }]}>Significance</Text>
                      <Text style={[styles.sectionDesc, { color: colors.text }]}>
                        {getHouseSignificance(selectedHouse.houseNum).desc}
                      </Text>
                    </View>

                    {/* Occupant Planets */}
                    <View style={styles.drawerSection}>
                      <Text style={[styles.sectionTitle, { color: colors.textSecondary }]}>Occupant Planets</Text>
                      {selectedHouse.planets && selectedHouse.planets.length > 0 ? (
                        selectedHouse.planets.map((planet, idx) => (
                          <View key={idx} style={styles.planetRow}>
                            <View style={[styles.planetIconContainer, { backgroundColor: colors.primary + '15' }]}>
                              <Text style={[styles.planetEmoji, { color: colors.primary, fontWeight: 'bold' }]}>{planet.symbol}</Text>
                            </View>
                            <View style={styles.planetInfo}>
                              <Text style={[styles.planetName, { color: colors.text }]}>{planet.name}</Text>
                              <Text style={[styles.planetDetails, { color: colors.textSecondary }]}>
                                {planet.formattedDegree} in {planet.nakshatra}
                              </Text>
                            </View>
                          </View>
                        ))
                      ) : (
                        <Text style={[styles.emptySectionText, { color: colors.textTertiary }]}>No planets occupy this house.</Text>
                      )}
                    </View>

                    {/* House Lord */}
                    <View style={styles.drawerSection}>
                      <Text style={[styles.sectionTitle, { color: colors.textSecondary }]}>House Lord</Text>
                      <View style={styles.lordContainer}>
                        <Ionicons name="key-outline" size={20} color={colors.primary} />
                        <Text style={[styles.lordText, { color: colors.text }]}>
                          Lord of {selectedHouse.signName} is <Text style={{ fontWeight: 'bold', color: colors.primary }}>{getHouseLord(selectedHouse.rashiIndex)}</Text>
                        </Text>
                      </View>
                    </View>
                    
                    {/* Extra padding for scroll */}
                    <View style={{ height: 40 }} />
                  </ScrollView>

                  {/* Sticky Quick Actions at Bottom */}
                  <View style={[styles.drawerActions, { 
                    backgroundColor: theme === 'dark' ? 'rgba(26, 0, 51, 1)' : 'rgba(255, 255, 255, 1)',
                    borderTopWidth: 1,
                    borderTopColor: theme === 'dark' ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.05)',
                    paddingTop: 16,
                    paddingHorizontal: 24,
                    paddingBottom: Platform.OS === 'ios' ? 30 : 20
                  }]}>
                    <TouchableOpacity 
                      style={[styles.actionButton, { backgroundColor: colors.primary }]}
                      onPress={() => {
                        closeHouseDrawer();
                        if (chartWidgetRef.current) {
                          chartWidgetRef.current.handleRotate(selectedHouse.rashiIndex);
                        }
                      }}
                    >
                      <Ionicons name="refresh-outline" size={20} color="white" />
                      <Text style={styles.actionButtonText}>Make Ascendant</Text>
                    </TouchableOpacity>

                    <TouchableOpacity 
                      style={[styles.actionButton, { backgroundColor: theme === 'dark' ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.05)' }]}
                      onPress={() => {
                        const prompt = `Analyze the ${selectedHouse.houseNum} house in my ${chartTypes[currentChartIndex].name} chart. It has ${selectedHouse.signName} sign and ${selectedHouse.planets && selectedHouse.planets.length > 0 ? selectedHouse.planets.map(p => p.name).join(', ') : 'no planets'}.`;
                        closeHouseDrawer();
                        navigation.navigate('Home', { startChat: true, initialMessage: prompt });
                      }}
                    >
                      <Ionicons name="chatbubble-ellipses-outline" size={20} color={colors.text} />
                      <Text style={[styles.actionButtonText, { color: colors.text }]}>Ask AI Analysis</Text>
                    </TouchableOpacity>
                  </View>
                </View>
              )}
            </Animated.View>
          </TouchableOpacity>
        </Modal>
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
  // Drawer Styles
  drawerOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'flex-end',
  },
  drawerContent: {
    borderTopLeftRadius: 30,
    borderTopRightRadius: 30,
    maxHeight: height * 0.75,
  },
  drawerHandle: {
    width: 40,
    height: 5,
    backgroundColor: 'rgba(128,128,128,0.3)',
    borderRadius: 3,
    alignSelf: 'center',
    marginTop: 12,
    marginBottom: 8,
  },
  drawerScrollContent: {
    padding: 24,
  },
  drawerHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
  },
  houseNumberBadge: {
    width: 44,
    height: 44,
    borderRadius: 22,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 16,
  },
  houseNumberText: {
    color: 'white',
    fontSize: 20,
    fontWeight: 'bold',
  },
  houseTitleContainer: {
    flex: 1,
  },
  houseTitle: {
    fontSize: 18,
    fontWeight: '800',
  },
  houseSign: {
    fontSize: 14,
    fontWeight: '600',
    marginTop: 2,
  },
  drawerSection: {
    padding: 16,
    borderRadius: 16,
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 12,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 1,
    marginBottom: 8,
  },
  sectionDesc: {
    fontSize: 15,
    lineHeight: 22,
  },
  planetRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 12,
  },
  planetIconContainer: {
    width: 36,
    height: 36,
    borderRadius: 18,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  planetEmoji: {
    fontSize: 16,
  },
  planetName: {
    fontSize: 15,
    fontWeight: '700',
  },
  planetDetails: {
    fontSize: 13,
  },
  emptySectionText: {
    fontSize: 14,
    fontStyle: 'italic',
    marginTop: 4,
  },
  lordContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    marginTop: 4,
  },
  lordText: {
    fontSize: 15,
  },
  drawerActions: {
    flexDirection: 'row',
    gap: 12,
  },
  actionButton: {
    flex: 1,
    flexDirection: 'row',
    height: 50,
    borderRadius: 25,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
  },
  actionButtonText: {
    color: 'white',
    fontSize: 14,
    fontWeight: '700',
  },
});
