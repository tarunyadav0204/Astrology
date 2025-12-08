import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  Modal,
  Dimensions,
  Platform,
  StatusBar,
  Animated,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import Icon from '@expo/vector-icons/Ionicons';
import { SafeAreaView } from 'react-native-safe-area-context';
import { COLORS, API_BASE_URL, getEndpoint } from '../../utils/constants';

const { width } = Dimensions.get('window');

export default function EventPeriods({ visible, onClose, birthData, onPeriodSelect }) {
  const [periods, setPeriods] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());
  const [viewMode, setViewMode] = useState('cards');
  const [showYearModal, setShowYearModal] = useState(false);
  const yearScrollRef = useRef(null);
  
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(50)).current;
  const rotateAnim = useRef(new Animated.Value(0)).current;
  const pulseAnim = useRef(new Animated.Value(1)).current;
  const starAnims = useRef([...Array(15)].map(() => new Animated.Value(0))).current;

  useEffect(() => {
    if (visible) {
      loadEventPeriods();
      startAnimations();
    }
  }, [visible, selectedYear]);

  // Separate effect for debugging state changes
  useEffect(() => {
  }, [loading, error, periods.length, selectedYear]);

  const startAnimations = () => {
    fadeAnim.setValue(0);
    slideAnim.setValue(50);
    
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 800,
        useNativeDriver: true,
      }),
      Animated.spring(slideAnim, {
        toValue: 0,
        tension: 50,
        friction: 8,
        useNativeDriver: true,
      }),
    ]).start();

    Animated.loop(
      Animated.timing(rotateAnim, {
        toValue: 1,
        duration: 20000,
        useNativeDriver: true,
      })
    ).start();

    Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, {
          toValue: 1.1,
          duration: 1500,
          useNativeDriver: true,
        }),
        Animated.timing(pulseAnim, {
          toValue: 1,
          duration: 1500,
          useNativeDriver: true,
        }),
      ])
    ).start();

    starAnims.forEach((anim, index) => {
      Animated.loop(
        Animated.sequence([
          Animated.delay(index * 150),
          Animated.timing(anim, {
            toValue: 1,
            duration: 2000,
            useNativeDriver: true,
          }),
          Animated.timing(anim, {
            toValue: 0,
            duration: 2000,
            useNativeDriver: true,
          }),
        ])
      ).start();
    });
  };

  const loadEventPeriods = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Add timeout to prevent hanging
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10000);
      
      const response = await fetch(`${API_BASE_URL}${getEndpoint('/chat/event-periods')}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...birthData, selectedYear }),
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
      
      
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Failed to load event periods: ${response.status} - ${errorText}`);
      }

      const data = await response.json();
      
      const filteredPeriods = (data.periods || [])
        .filter(period => {
          try {
            return new Date(period.start_date).getFullYear() === selectedYear;
          } catch {
            return false;
          }
        })
        .sort((a, b) => {
          try {
            return new Date(a.start_date) - new Date(b.start_date);
          } catch {
            return 0;
          }
        });
      
      setPeriods(filteredPeriods);
    } catch (err) {
      console.error('EventPeriods: Error occurred', err);
      setError(err.message);
      setPeriods([]);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric'
    });
  };

  const getPlanetIcon = (planet) => {
    const icons = {
      'Jupiter': '♃', 'Saturn': '♄', 'Mars': '♂', 'Venus': '♀',
      'Mercury': '☿', 'Sun': '☉', 'Moon': '☽', 'Rahu': '☊', 'Ketu': '☋'
    };
    return icons[planet] || '⭐';
  };

  const getSignificanceGradient = (significance) => {
    switch (significance) {
      case 'maximum': return ['#ff4757', '#ff6b35'];
      case 'high': return ['#ff6b35', '#ff8c5a'];
      default: return ['#3742fa', '#5f6cff'];
    }
  };

  const getLifeAreaDescription = (period) => {
    const houseAreas = {
      1: "Personal growth", 2: "Money & family", 3: "Communication",
      4: "Home & mother", 5: "Children & creativity", 6: "Work & health",
      7: "Marriage & partnerships", 8: "Major life changes", 9: "Higher learning",
      10: "Career & reputation", 11: "Income & friendships", 12: "Spirituality"
    };
    const transitHouse = period.period_data?.transit_house;
    return houseAreas[transitHouse] || "Important developments";
  };

  const yearOptions = Array.from({ length: 121 }, (_, i) => 1950 + i);

  const spin = rotateAnim.interpolate({
    inputRange: [0, 1],
    outputRange: ['0deg', '360deg'],
  });

  // Always render the modal structure, show loading inside
  const renderContent = () => {
    if (loading) {
      return (
        <View style={styles.loadingContainer}>
          <Animated.View style={[styles.cosmicOrb, { transform: [{ rotate: spin }] }]}>
            <LinearGradient
              colors={['#ff6b35', '#ffd700', '#ff6b35']}
              style={styles.orbGradient}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 1 }}
            >
              <Text style={styles.orbIcon}>🎯</Text>
            </LinearGradient>
          </Animated.View>
          <Text style={styles.loadingText}>Finding Event Periods</Text>
          <Text style={styles.loadingSubtext}>Analyzing planetary transits for {selectedYear}...</Text>
        </View>
      );
    }

    if (error) {
      return (
        <Animated.View style={[styles.emptyState, { opacity: fadeAnim }]}>
          <Text style={styles.emptyIcon}>⚠️</Text>
          <Text style={styles.emptyText}>Error loading periods: {error}</Text>
          <TouchableOpacity 
            style={styles.retryButton} 
            onPress={loadEventPeriods}
          >
            <Text style={styles.retryText}>Retry</Text>
          </TouchableOpacity>
        </Animated.View>
      );
    }

    if (periods.length === 0) {
      return (
        <Animated.View style={[styles.emptyState, { opacity: fadeAnim }]}>
          <Text style={styles.emptyIcon}>🎯</Text>
          <Text style={styles.emptyText}>No significant periods found for {selectedYear}</Text>
        </Animated.View>
      );
    }

    return (
      <ScrollView 
        style={styles.periodsContainer}
        contentContainerStyle={styles.periodsContent}
        showsVerticalScrollIndicator={false}
      >
        {periods.map((period, index) => (
          <PeriodCard key={period.id || `${index}-${period.start_date}`} period={period} index={index} />
        ))}
      </ScrollView>
    );
  };

  const PeriodCard = ({ period, index }) => {
    const cardAnim = useRef(new Animated.Value(0)).current;

    useEffect(() => {
      Animated.spring(cardAnim, {
        toValue: 1,
        delay: index * 100,
        tension: 50,
        friction: 7,
        useNativeDriver: true,
      }).start();
    }, []);

    const isHighSignificance = period.significance === 'maximum' || period.significance === 'high';

    return (
      <Animated.View
        style={[
          styles.periodCardWrapper,
          {
            opacity: cardAnim,
            transform: [
              {
                translateY: cardAnim.interpolate({
                  inputRange: [0, 1],
                  outputRange: [50, 0],
                }),
              },
              {
                scale: cardAnim.interpolate({
                  inputRange: [0, 1],
                  outputRange: [0.9, 1],
                }),
              },
            ],
          },
        ]}
      >
        <TouchableOpacity
          style={styles.periodCard}
          onPress={() => onPeriodSelect && onPeriodSelect(period)}
          activeOpacity={0.9}
        >
          <LinearGradient
            colors={['rgba(255, 255, 255, 0.15)', 'rgba(255, 255, 255, 0.05)']}
            style={styles.periodGradient}
          >
            <View style={styles.cardHeader}>
              <View style={styles.planetIconContainer}>
                <LinearGradient
                  colors={getSignificanceGradient(period.significance)}
                  style={styles.planetIconGradient}
                >
                  <Text style={styles.planetIcon}>{getPlanetIcon(period.transit_planet)}</Text>
                </LinearGradient>
              </View>
              <View style={styles.cardHeaderInfo}>
                <Text style={styles.periodDates}>
                  {formatDate(period.start_date)} - {formatDate(period.end_date)}
                </Text>
                <Text style={styles.lifeArea}>{getLifeAreaDescription(period)}</Text>
              </View>
              {isHighSignificance && (
                <Animated.View style={[styles.highBadge, { transform: [{ scale: pulseAnim }] }]}>
                  <LinearGradient
                    colors={getSignificanceGradient(period.significance)}
                    style={styles.highBadgeGradient}
                  >
                    <Text style={styles.highBadgeText}>
                      {period.significance === 'maximum' ? '🔥' : '📈'}
                    </Text>
                  </LinearGradient>
                </Animated.View>
              )}
            </View>

            <View style={styles.cardContent}>
              <Text style={styles.planetActivation}>
                {getPlanetIcon(period.transit_planet)} {period.transit_planet} → {getPlanetIcon(period.natal_planet)} {period.natal_planet}
              </Text>
              {period.period_data?.transit_house && (
                <View style={styles.houseInfo}>
                  <Icon name="home-outline" size={14} color="rgba(255, 255, 255, 0.7)" />
                  <Text style={styles.houseText}>House {period.period_data.transit_house}</Text>
                </View>
              )}
            </View>
          </LinearGradient>
        </TouchableOpacity>
      </Animated.View>
    );
  };

  return (
    <Modal visible={visible} animationType="slide">
      <LinearGradient colors={['#1a0033', '#2d1b4e', '#4a2c6d', '#ff6b35']} style={styles.container}>
        <StatusBar barStyle="light-content" backgroundColor="transparent" translucent />
        
        {/* Twinkling Stars */}
        {starAnims.map((anim, index) => {
          const top = Math.random() * 100;
          const left = Math.random() * 100;
          return (
            <Animated.View
              key={index}
              style={[
                styles.star,
                {
                  top: `${top}%`,
                  left: `${left}%`,
                  opacity: anim,
                },
              ]}
            >
              <Text style={styles.starText}>✨</Text>
            </Animated.View>
          );
        })}

        <SafeAreaView style={styles.safeArea} edges={['top', 'left', 'right']}>
            
            {/* Header */}
            <Animated.View style={[styles.header, { opacity: fadeAnim }]}>
              <TouchableOpacity style={styles.backButton} onPress={onClose}>
                <Icon name="arrow-back" size={24} color={COLORS.white} />
              </TouchableOpacity>
              
              <View style={styles.headerCenter}>
                <Text style={styles.headerTitle}>Event Periods</Text>
                <Text style={styles.headerSubtitle}>High-probability life events</Text>
              </View>
              
              <TouchableOpacity 
                style={styles.viewToggle}
                onPress={() => setViewMode(viewMode === 'timeline' ? 'cards' : 'timeline')}
              >
                <Icon 
                  name={viewMode === 'timeline' ? 'grid-outline' : 'list-outline'} 
                  size={24} 
                  color={COLORS.white} 
                />
              </TouchableOpacity>
            </Animated.View>

            {/* Year Selector */}
            <Animated.View style={[styles.yearSelector, { opacity: fadeAnim, transform: [{ translateY: slideAnim }] }]}>
              <TouchableOpacity style={styles.yearButton} onPress={() => setShowYearModal(true)}>
                <LinearGradient
                  colors={['rgba(255, 255, 255, 0.2)', 'rgba(255, 255, 255, 0.1)']}
                  style={styles.yearButtonGradient}
                >
                  <Icon name="calendar-outline" size={20} color={COLORS.white} />
                  <Text style={styles.yearText}>{selectedYear}</Text>
                  <Icon name="chevron-down" size={20} color={COLORS.white} />
                </LinearGradient>
              </TouchableOpacity>
            </Animated.View>

            {/* Content */}
            {renderContent()}

        </SafeAreaView>
      </LinearGradient>

      {/* Year Modal */}
      <Modal visible={showYearModal} transparent animationType="fade">
        <View style={styles.yearModalOverlay}>
          <Animated.View style={[styles.yearModalContent, { opacity: fadeAnim }]}>
            <LinearGradient
              colors={['rgba(255, 255, 255, 0.95)', 'rgba(255, 255, 255, 0.9)']}
              style={styles.yearModalGradient}
            >
              <Text style={styles.yearModalTitle}>Select Year</Text>
              <ScrollView 
                ref={yearScrollRef}
                style={styles.yearList} 
                showsVerticalScrollIndicator={false}
                onLayout={() => {
                  // Auto-scroll to current year when modal opens
                  const currentIndex = yearOptions.findIndex(year => year === selectedYear);
                  if (currentIndex !== -1 && yearScrollRef.current) {
                    setTimeout(() => {
                      yearScrollRef.current.scrollTo({
                        y: currentIndex * 56, // 56 is approximate height of yearOption
                        animated: true
                      });
                    }, 100);
                  }
                }}
              >
                {yearOptions.map(year => (
                  <TouchableOpacity
                    key={year}
                    style={[
                      styles.yearOption,
                      year === selectedYear && styles.yearOptionSelected
                    ]}
                    onPress={() => {
                      setShowYearModal(false);
                      if (year !== selectedYear) {
                        setSelectedYear(year);
                      }
                    }}
                  >
                    <Text style={[
                      styles.yearOptionText,
                      year === selectedYear && styles.yearOptionTextSelected
                    ]}>
                      {year} {year === selectedYear ? '✓' : ''}
                    </Text>
                  </TouchableOpacity>
                ))}
              </ScrollView>
              <TouchableOpacity
                style={styles.yearModalClose}
                onPress={() => setShowYearModal(false)}
              >
                <LinearGradient
                  colors={['#ff6b35', '#ff8c5a']}
                  style={styles.yearModalCloseGradient}
                >
                  <Text style={styles.yearModalCloseText}>Close</Text>
                </LinearGradient>
              </TouchableOpacity>
            </LinearGradient>
          </Animated.View>
        </View>
      </Modal>
    </Modal>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  safeArea: { flex: 1 },
  star: { position: 'absolute' },
  starText: { fontSize: 10 },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  cosmicOrb: {
    width: 100,
    height: 100,
    borderRadius: 50,
    marginBottom: 24,
    shadowColor: '#ff6b35',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.6,
    shadowRadius: 20,
    elevation: 10,
  },
  orbGradient: {
    width: '100%',
    height: '100%',
    borderRadius: 50,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 3,
    borderColor: 'rgba(255, 255, 255, 0.3)',
  },
  orbIcon: { fontSize: 48 },
  loadingText: {
    fontSize: 20,
    fontWeight: '700',
    color: COLORS.white,
    marginBottom: 8,
  },
  loadingSubtext: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.7)',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 16,
    paddingTop: 16,
  },
  backButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(255, 255, 255, 0.15)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  headerCenter: {
    flex: 1,
    alignItems: 'center',
    marginHorizontal: 16,
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: COLORS.white,
  },
  headerSubtitle: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.7)',
    marginTop: 2,
  },
  viewToggle: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(255, 255, 255, 0.15)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  yearSelector: {
    paddingHorizontal: 20,
    marginBottom: 16,
  },
  yearButton: {
    borderRadius: 16,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 5,
  },
  yearButtonGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 12,
    gap: 8,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.2)',
    borderRadius: 16,
  },
  yearText: {
    fontSize: 18,
    fontWeight: '700',
    color: COLORS.white,
  },
  periodsContainer: {
    flex: 1,
  },
  periodsContent: {
    padding: 20,
    paddingBottom: 40,
  },
  periodCardWrapper: {
    marginBottom: 16,
  },
  periodCard: {
    borderRadius: 20,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.3,
    shadowRadius: 12,
    elevation: 8,
  },
  periodGradient: {
    padding: 20,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.2)',
    borderRadius: 20,
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  planetIconContainer: {
    marginRight: 12,
  },
  planetIconGradient: {
    width: 48,
    height: 48,
    borderRadius: 24,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 2,
    borderColor: 'rgba(255, 255, 255, 0.3)',
  },
  planetIcon: { fontSize: 24 },
  cardHeaderInfo: {
    flex: 1,
  },
  periodDates: {
    fontSize: 14,
    fontWeight: '700',
    color: COLORS.white,
    marginBottom: 4,
  },
  lifeArea: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.8)',
  },
  highBadge: {
    width: 36,
    height: 36,
    borderRadius: 18,
    overflow: 'hidden',
  },
  highBadgeGradient: {
    width: '100%',
    height: '100%',
    justifyContent: 'center',
    alignItems: 'center',
  },
  highBadgeText: { fontSize: 18 },
  cardContent: {
    gap: 8,
  },
  planetActivation: {
    fontSize: 15,
    fontWeight: '600',
    color: COLORS.white,
  },
  houseInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  houseText: {
    fontSize: 13,
    color: 'rgba(255, 255, 255, 0.7)',
  },
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 40,
  },
  emptyIcon: {
    fontSize: 64,
    marginBottom: 16,
  },
  emptyText: {
    fontSize: 16,
    color: 'rgba(255, 255, 255, 0.8)',
    textAlign: 'center',
  },
  retryButton: {
    marginTop: 16,
    paddingHorizontal: 24,
    paddingVertical: 12,
    backgroundColor: 'rgba(255, 107, 53, 0.2)',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: 'rgba(255, 107, 53, 0.5)',
  },
  retryText: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.white,
    textAlign: 'center',
  },
  yearModalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  yearModalContent: {
    width: '85%',
    maxHeight: '70%',
    borderRadius: 20,
    overflow: 'hidden',
  },
  yearModalGradient: {
    padding: 20,
  },
  yearModalTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: COLORS.accent,
    textAlign: 'center',
    marginBottom: 16,
  },
  yearList: {
    maxHeight: 300,
  },
  yearOption: {
    padding: 14,
    borderRadius: 12,
    marginBottom: 6,
    backgroundColor: 'rgba(255, 107, 53, 0.05)',
  },
  yearOptionSelected: {
    backgroundColor: 'rgba(255, 107, 53, 0.15)',
  },
  yearOptionText: {
    fontSize: 16,
    color: '#333',
    textAlign: 'center',
  },
  yearOptionTextSelected: {
    color: COLORS.accent,
    fontWeight: '700',
  },
  yearModalClose: {
    marginTop: 16,
    borderRadius: 12,
    overflow: 'hidden',
  },
  yearModalCloseGradient: {
    padding: 14,
  },
  yearModalCloseText: {
    fontSize: 16,
    fontWeight: '700',
    color: COLORS.white,
    textAlign: 'center',
  },
});
