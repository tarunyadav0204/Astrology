import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  Alert,
  Modal,
  Dimensions,
  ActionSheetIOS,
  Platform,
  StatusBar,
  PanResponder,
} from 'react-native';
import { LinearGradient } from 'react-native-linear-gradient';
import Icon from 'react-native-vector-icons/Ionicons';
import { SafeAreaView, useSafeAreaInsets } from 'react-native-safe-area-context';

import { COLORS, API_BASE_URL, getEndpoint } from '../../utils/constants';

const { width: screenWidth } = Dimensions.get('window');

export default function EventPeriods({ visible, onClose, birthData, onPeriodSelect }) {
  const [periods, setPeriods] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());
  const [viewMode, setViewMode] = useState('cards');
  const [showYearModal, setShowYearModal] = useState(false);
  const insets = useSafeAreaInsets();

  const panResponder = PanResponder.create({
    onStartShouldSetPanResponder: () => true,
    onMoveShouldSetPanResponder: (evt, gestureState) => {
      return Math.abs(gestureState.dx) > 10;
    },
    onPanResponderGrant: () => {},
    onPanResponderMove: () => {},
    onPanResponderRelease: (evt, gestureState) => {
      if (gestureState.dx > 50) {
        onClose();
      }
    },
  });

  useEffect(() => {
    if (visible) {
      loadEventPeriods();
    }
  }, [visible, selectedYear]);

  const loadEventPeriods = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch(`${API_BASE_URL}${getEndpoint('/chat/event-periods')}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...birthData, selectedYear })
      });
      
      if (!response.ok) {
        throw new Error(`Failed to load event periods: ${response.status}`);
      }

      const data = await response.json();
      
      const filteredPeriods = (data.periods || []).filter(period => {
        const periodYear = new Date(period.start_date).getFullYear();
        return periodYear === selectedYear;
      }).sort((a, b) => new Date(a.start_date) - new Date(b.start_date));
      
      setPeriods(filteredPeriods);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  const getSignificanceColor = (significance) => {
    switch (significance) {
      case 'maximum': return '#ff4757';
      case 'high': return '#ff6b35';
      default: return '#3742fa';
    }
  };

  const getSignificanceLabel = (significance) => {
    switch (significance) {
      case 'maximum': return '🔥 Maximum';
      case 'high': return '📈 High';
      default: return '📊 Moderate';
    }
  };

  const getLifeAreaDescription = (period) => {
    const transitHouse = period.period_data?.transit_house;
    const natalHouse = period.period_data?.natal_house;
    
    const houseAreas = {
      1: "Personal growth & health",
      2: "Money & family matters", 
      3: "Communication & siblings",
      4: "Home & mother",
      5: "Children & creativity",
      6: "Work & health issues",
      7: "Marriage & partnerships",
      8: "Major life changes",
      9: "Higher learning & father",
      10: "Career & reputation",
      11: "Income & friendships",
      12: "Spirituality & expenses"
    };
    
    const areas = [];
    if (transitHouse && houseAreas[transitHouse]) areas.push(houseAreas[transitHouse]);
    if (natalHouse && houseAreas[natalHouse] && natalHouse !== transitHouse) areas.push(houseAreas[natalHouse]);
    
    return areas.length > 0 ? areas.join(" & ") : "Important life developments";
  };

  const getSimpleDescription = (transitPlanet) => {
    const descriptions = {
      'Jupiter': 'Opportunities for growth and expansion',
      'Saturn': 'Important decisions and responsibilities',
      'Mars': 'Action-oriented period with energy boost',
      'Venus': 'Focus on relationships and finances',
      'Mercury': 'Communication and learning opportunities',
      'Sun': 'Recognition and leadership opportunities',
      'Moon': 'Emotional developments and family matters',
      'Rahu': 'Significant life changes and new directions',
      'Ketu': 'Significant life changes and new directions'
    };
    return descriptions[transitPlanet] || 'Important planetary influence';
  };

  const yearOptions = Array.from({ length: 121 }, (_, i) => 1950 + i);

  const showYearPicker = () => {
    if (Platform.OS === 'ios') {
      const yearLabels = yearOptions.map(year => 
        year === selectedYear ? `${year} ✓` : year.toString()
      );
      
      ActionSheetIOS.showActionSheetWithOptions(
        {
          options: ['Cancel', ...yearLabels],
          cancelButtonIndex: 0,
          title: `Select Year (Current: ${selectedYear})`
        },
        (buttonIndex) => {
          if (buttonIndex > 0) {
            setSelectedYear(yearOptions[buttonIndex - 1]);
          }
        }
      );
    } else {
      setShowYearModal(true);
    }
  };

  const changeYear = (direction) => {
    const currentIndex = yearOptions.indexOf(selectedYear);
    if (direction === 'prev' && currentIndex > 0) {
      setSelectedYear(yearOptions[currentIndex - 1]);
    } else if (direction === 'next' && currentIndex < yearOptions.length - 1) {
      setSelectedYear(yearOptions[currentIndex + 1]);
    }
  };

  if (loading) {
    return (
      <Modal visible={visible} animationType="slide">
        <View style={[styles.container, { backgroundColor: COLORS.gradientStart }]}>
          <SafeAreaView style={styles.safeArea}>
            <View style={styles.loadingContainer}>
              <Text style={styles.loadingSpinner}>🎯</Text>
              <Text style={styles.loadingText}>🔍 Finding All Life Events</Text>
              <Text style={styles.loadingSubtext}>✨ Calculating probability of occurrence for each event</Text>
              <Text style={styles.loadingDetails}>📊 Analyzing planetary transits & activations...</Text>
            </View>
          </SafeAreaView>
        </View>
      </Modal>
    );
  }

  if (error) {
    return (
      <Modal visible={visible} animationType="slide">
        <View style={[styles.container, { backgroundColor: COLORS.gradientStart }]}>
          <SafeAreaView style={styles.safeArea}>
            <View style={styles.errorContainer}>
              <Text style={styles.errorTitle}>Unable to Load Event Periods</Text>
              <Text style={styles.errorText}>{error}</Text>
              <TouchableOpacity style={styles.backButton} onPress={onClose}>
                <Text style={styles.backButtonText}>← Back</Text>
              </TouchableOpacity>
            </View>
          </SafeAreaView>
        </View>
      </Modal>
    );
  }

  return (
    <Modal visible={visible} animationType="slide">
      <StatusBar barStyle="light-content" backgroundColor="#ff6f00" translucent={false} />
      <View style={[styles.container, { backgroundColor: COLORS.gradientStart }]}>
        <SafeAreaView style={styles.safeArea}>
          {/* Page Title */}
          <View style={styles.pageTitle}>
            <Text style={styles.pageTitleText}>🎯 Event Periods</Text>
            <Text style={styles.pageSubtitle}>High-probability periods for significant life events</Text>
            <Text style={styles.tapHint}>💬 Tap any period for detailed analysis</Text>
          </View>

          {/* Simple Header */}
          <View style={styles.header}>
            <TouchableOpacity style={styles.backBtn} onPress={onClose}>
              <Text style={styles.backIcon}>←</Text>
            </TouchableOpacity>
            
            <TouchableOpacity 
              style={styles.yearSelector}
              onPress={showYearPicker}
            >
              <Text style={styles.yearText}>{selectedYear}</Text>
              <Text style={styles.chevronDown}>▼</Text>
            </TouchableOpacity>
            
            <TouchableOpacity 
              style={styles.toggleBtn} 
              onPress={() => setViewMode(viewMode === 'timeline' ? 'cards' : 'timeline')}
            >
              <Text style={styles.toggleBtnText}>
                {viewMode === 'timeline' ? '📋' : '📊'}
              </Text>
            </TouchableOpacity>
          </View>

          {/* Content */}
          <View {...panResponder.panHandlers} style={styles.gestureContainer}>
          {periods.length === 0 ? (
            <View style={styles.noPeriodsContainer}>
              <Text style={styles.noPeriodsText}>No high-significance periods found for {selectedYear}.</Text>
            </View>
          ) : viewMode === 'timeline' ? (
            <ScrollView style={styles.timelineContainer} showsVerticalScrollIndicator={false}>
              {(() => {
                // Group periods by month
                const periodsByMonth = {};
                periods.forEach(period => {
                  const monthKey = new Date(period.start_date).toLocaleDateString('en-US', { 
                    year: 'numeric', 
                    month: 'long' 
                  });
                  if (!periodsByMonth[monthKey]) {
                    periodsByMonth[monthKey] = [];
                  }
                  periodsByMonth[monthKey].push(period);
                });
                
                return Object.entries(periodsByMonth)
                  .sort(([a], [b]) => new Date(a + ' 1') - new Date(b + ' 1'))
                  .map(([month, monthPeriods]) => (
                    <View key={month} style={styles.monthSection}>
                      <Text style={styles.monthHeader}>{month}</Text>
                      {monthPeriods.map((period) => (
                        <TouchableOpacity
                          key={period.id}
                          style={[
                            styles.timelinePeriod,
                            { borderLeftColor: getSignificanceColor(period.significance) }
                          ]}
                          onPress={() => onPeriodSelect && onPeriodSelect(period)}
                        >
                          <View style={styles.timelinePeriodHeader}>
                            <Text style={styles.timelineDates}>
                              {formatDate(period.start_date)} - {formatDate(period.end_date)}
                            </Text>
                            <View 
                              style={[
                                styles.timelineSignificanceBadge,
                                { backgroundColor: getSignificanceColor(period.significance) }
                              ]}
                            >
                              <Text style={styles.timelineSignificanceText}>
                                {period.significance === 'maximum' ? '🔥' : period.significance === 'high' ? '📈' : '📊'}
                              </Text>
                            </View>
                          </View>
                          <Text style={styles.timelinePlanetActivation}>
                            {period.transit_planet} → {period.natal_planet}
                          </Text>
                          <Text style={styles.timelineLifeArea}>
                            {getLifeAreaDescription(period)}
                          </Text>
                        </TouchableOpacity>
                      ))}
                    </View>
                  ));
              })()
              }
            </ScrollView>
          ) : (
            <ScrollView style={styles.periodsContainer} showsVerticalScrollIndicator={false}>
              {periods.map((period) => (
                <TouchableOpacity
                  key={period.id}
                  style={styles.periodCard}
                  onPress={() => onPeriodSelect && onPeriodSelect(period)}
                >
                  <View style={styles.cardHeader}>
                    <Text style={styles.periodDates}>
                      {formatDate(period.start_date)} - {formatDate(period.end_date)}
                    </Text>
                    <View 
                      style={[
                        styles.significanceBadge,
                        { backgroundColor: getSignificanceColor(period.significance) }
                      ]}
                    >
                      <Text style={styles.significanceBadgeText}>
                        {getSignificanceLabel(period.significance)}
                      </Text>
                    </View>
                  </View>
                  
                  <View style={styles.cardContent}>
                    <Text style={styles.lifeAreaText}>
                      {getLifeAreaDescription(period)}
                    </Text>
                    <Text style={styles.simpleDescription}>
                      {getSimpleDescription(period.transit_planet)}
                    </Text>
                    
                    <View style={styles.technicalDetails}>
                      <Text style={styles.planetActivation}>
                        {period.transit_planet} → {period.natal_planet}
                      </Text>
                      <View style={styles.houseDetails}>
                        {period.period_data?.transit_house && (
                          <Text style={styles.houseTag}>Transit: H{period.period_data.transit_house}</Text>
                        )}
                        {period.period_data?.natal_house && (
                          <Text style={styles.houseTag}>Natal: H{period.period_data.natal_house}</Text>
                        )}
                      </View>
                    </View>
                  </View>
                </TouchableOpacity>
              ))}
            </ScrollView>
          )}
          </View>
        </SafeAreaView>
      </View>
      
      {/* Year Selection Modal for Android */}
      <Modal visible={showYearModal} transparent animationType="fade">
        <View style={styles.yearModalOverlay}>
          <View style={styles.yearModalContent}>
            <Text style={styles.yearModalTitle}>Select Year</Text>
            <ScrollView style={styles.yearList} showsVerticalScrollIndicator={false}>
              {yearOptions.map(year => (
                <TouchableOpacity
                  key={year}
                  style={[
                    styles.yearOption,
                    year === selectedYear && styles.yearOptionSelected
                  ]}
                  onPress={() => {
                    setSelectedYear(year);
                    setShowYearModal(false);
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
              <Text style={styles.yearModalCloseText}>Cancel</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </Modal>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  safeArea: {
    flex: 1,
  },
  pageTitle: {
    alignItems: 'center',
    paddingVertical: 15,
    paddingHorizontal: 20,
  },
  pageTitleText: {
    fontSize: 24,
    fontWeight: '700',
    color: '#1a1a1a',
    textAlign: 'center',
    marginBottom: 5,
    textShadowColor: 'rgba(255, 255, 255, 0.8)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 2,
  },
  pageSubtitle: {
    fontSize: 14,
    color: '#2d2d2d',
    textAlign: 'center',
    lineHeight: 18,
    textShadowColor: 'rgba(255, 255, 255, 0.6)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 1,
  },
  tapHint: {
    fontSize: 12,
    color: COLORS.accent,
    textAlign: 'center',
    marginTop: 5,
    fontWeight: '600',
    textShadowColor: 'rgba(255, 255, 255, 0.8)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 1,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 15,
    paddingVertical: 8,
    backgroundColor: 'rgba(0, 0, 0, 0.1)',
    marginHorizontal: 10,
    borderRadius: 8,
    height: 50,
  },
  backBtn: {
    backgroundColor: COLORS.accent,
    padding: 8,
    borderRadius: 6,
    minWidth: 40,
    alignItems: 'center',
    justifyContent: 'center',
  },
  backIcon: {
    fontSize: 18,
    color: 'white',
    fontWeight: 'bold',
    lineHeight: 18,
    textAlignVertical: 'center',
  },
  chevronDown: {
    fontSize: 12,
    color: '#333',
  },
  yearSelector: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.9)',
    borderRadius: 6,
    paddingHorizontal: 12,
    height: 35,
    marginHorizontal: 10,
    minWidth: 80,
  },
  yearText: {
    fontSize: 16,
    fontWeight: '700',
    color: '#333',
    marginRight: 5,
  },
  toggleBtn: {
    backgroundColor: COLORS.secondary,
    padding: 8,
    borderRadius: 6,
    minWidth: 40,
    alignItems: 'center',
  },
  toggleBtnText: {
    fontSize: 16,
    color: 'white',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 40,
  },
  loadingSpinner: {
    fontSize: 48,
    marginBottom: 20,
  },
  loadingText: {
    color: '#1a1a1a',
    fontSize: 20,
    fontWeight: '700',
    textAlign: 'center',
    marginBottom: 15,
    textShadowColor: 'rgba(255, 255, 255, 0.8)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 2,
  },
  loadingSubtext: {
    color: '#2d2d2d',
    fontSize: 16,
    textAlign: 'center',
    fontWeight: '600',
    marginBottom: 10,
    textShadowColor: 'rgba(255, 255, 255, 0.6)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 1,
  },
  loadingDetails: {
    color: '#444',
    fontSize: 14,
    textAlign: 'center',
    fontStyle: 'italic',
    textShadowColor: 'rgba(255, 255, 255, 0.5)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 1,
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 40,
  },
  errorTitle: {
    color: 'white',
    fontSize: 20,
    fontWeight: '700',
    textAlign: 'center',
    marginBottom: 10,
  },
  errorText: {
    color: 'rgba(255, 255, 255, 0.8)',
    fontSize: 16,
    textAlign: 'center',
    marginBottom: 20,
  },
  backButton: {
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 8,
  },
  backButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
  noPeriodsContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 40,
  },
  noPeriodsText: {
    color: 'white',
    fontSize: 16,
    textAlign: 'center',
  },
  periodsContainer: {
    flex: 1,
    paddingHorizontal: 15,
    paddingTop: 10,
  },
  periodCard: {
    backgroundColor: 'rgba(255, 255, 255, 0.95)',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
    paddingBottom: 8,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255, 107, 53, 0.2)',
  },
  periodDates: {
    fontSize: 16,
    fontWeight: '700',
    color: COLORS.accent,
    flex: 1,
  },
  significanceBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  significanceBadgeText: {
    color: 'white',
    fontSize: 10,
    fontWeight: '700',
  },
  cardContent: {
    gap: 8,
  },
  lifeAreaText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
  },
  simpleDescription: {
    fontSize: 12,
    color: '#666',
    fontStyle: 'italic',
    lineHeight: 16,
  },
  technicalDetails: {
    backgroundColor: 'rgba(255, 107, 53, 0.08)',
    padding: 8,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: 'rgba(255, 107, 53, 0.15)',
    marginTop: 4,
  },
  planetActivation: {
    fontSize: 13,
    fontWeight: '600',
    color: COLORS.accent,
    marginBottom: 4,
  },
  houseDetails: {
    flexDirection: 'row',
    gap: 8,
  },
  houseTag: {
    fontSize: 9,
    backgroundColor: 'rgba(255, 107, 53, 0.12)',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 8,
    color: COLORS.accent,
    fontWeight: '600',
  },
  // Timeline styles
  timelineContainer: {
    flex: 1,
    paddingHorizontal: 15,
    paddingTop: 10,
  },
  monthSection: {
    marginBottom: 20,
  },
  monthHeader: {
    fontSize: 18,
    fontWeight: '700',
    color: 'white',
    marginBottom: 10,
    paddingHorizontal: 10,
    textShadowColor: 'rgba(0, 0, 0, 0.5)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 2,
  },
  timelinePeriod: {
    backgroundColor: 'rgba(255, 255, 255, 0.9)',
    borderRadius: 8,
    padding: 12,
    marginBottom: 8,
    marginLeft: 10,
    borderLeftWidth: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  timelinePeriodHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6,
  },
  timelineDates: {
    fontSize: 12,
    fontWeight: '600',
    color: '#333',
    flex: 1,
  },
  timelineSignificanceBadge: {
    width: 24,
    height: 24,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
  },
  timelineSignificanceText: {
    fontSize: 12,
  },
  timelinePlanetActivation: {
    fontSize: 13,
    fontWeight: '700',
    color: COLORS.accent,
    marginBottom: 4,
  },
  timelineLifeArea: {
    fontSize: 12,
    color: '#666',
    lineHeight: 16,
  },
  // Year Modal Styles
  yearModalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  yearModalContent: {
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 20,
    width: '80%',
    maxHeight: '70%',
  },
  yearModalTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: COLORS.accent,
    textAlign: 'center',
    marginBottom: 15,
  },
  yearList: {
    maxHeight: 300,
  },
  yearOption: {
    padding: 12,
    borderRadius: 8,
    marginBottom: 4,
  },
  yearOptionSelected: {
    backgroundColor: COLORS.accent,
  },
  yearOptionText: {
    fontSize: 16,
    color: '#333',
    textAlign: 'center',
  },
  yearOptionTextSelected: {
    color: 'white',
    fontWeight: '600',
  },
  yearModalClose: {
    backgroundColor: COLORS.lightGray,
    padding: 12,
    borderRadius: 8,
    marginTop: 15,
  },
  yearModalCloseText: {
    fontSize: 16,
    color: COLORS.accent,
    textAlign: 'center',
    fontWeight: '600',
  },
  gestureContainer: {
    flex: 1,
  },
});