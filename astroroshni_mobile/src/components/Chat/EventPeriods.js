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
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { SafeAreaView, useSafeAreaInsets } from 'react-native-safe-area-context';

import { COLORS, API_BASE_URL, getEndpoint } from '../../utils/constants';

const { width: screenWidth } = Dimensions.get('window');

export default function EventPeriods({ visible, onClose, birthData, onPeriodSelect }) {
  const [periods, setPeriods] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());
  const [viewMode, setViewMode] = useState('cards');
  const insets = useSafeAreaInsets();

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
      // Create options with current year highlighted
      const currentIndex = yearOptions.indexOf(selectedYear);
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
      Alert.alert('Year Selection', 'Use the arrows to change year');
    }
  };

  if (loading) {
    return (
      <Modal visible={visible} animationType="slide">
        <LinearGradient colors={[COLORS.gradientStart, COLORS.gradientEnd]} style={styles.container}>
          <SafeAreaView style={styles.safeArea}>
            <View style={styles.loadingContainer}>
              <Text style={styles.loadingSpinner}>🔮</Text>
              <Text style={styles.loadingText}>Analyzing your chart for significant periods...</Text>
              <Text style={styles.loadingSubtext}>This may take a moment as we calculate transit activations</Text>
            </View>
          </SafeAreaView>
        </LinearGradient>
      </Modal>
    );
  }

  if (error) {
    return (
      <Modal visible={visible} animationType="slide">
        <LinearGradient colors={[COLORS.gradientStart, COLORS.gradientEnd]} style={styles.container}>
          <SafeAreaView style={styles.safeArea}>
            <View style={styles.errorContainer}>
              <Text style={styles.errorTitle}>Unable to Load Event Periods</Text>
              <Text style={styles.errorText}>{error}</Text>
              <TouchableOpacity style={styles.backButton} onPress={onClose}>
                <Text style={styles.backButtonText}>← Back</Text>
              </TouchableOpacity>
            </View>
          </SafeAreaView>
        </LinearGradient>
      </Modal>
    );
  }

  return (
    <Modal visible={visible} animationType="slide">
      <LinearGradient colors={[COLORS.gradientStart, COLORS.gradientEnd]} style={styles.container}>
        <SafeAreaView style={styles.safeArea}>
          {/* Simple Header */}
          <View style={[styles.header, { marginTop: insets.top + 10 }]}>
            <TouchableOpacity style={styles.backBtn} onPress={onClose}>
              <Ionicons name="arrow-back" size={20} color="white" />
            </TouchableOpacity>
            
            <TouchableOpacity 
              style={styles.yearSelector}
              onPress={() => showYearPicker()}
            >
              <Text style={styles.yearText}>{selectedYear}</Text>
              <Ionicons name="chevron-down" size={16} color="#333" />
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
        </SafeAreaView>
      </LinearGradient>
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
    color: 'white',
    fontSize: 18,
    fontWeight: '600',
    textAlign: 'center',
    marginBottom: 10,
  },
  loadingSubtext: {
    color: 'rgba(255, 255, 255, 0.8)',
    fontSize: 14,
    textAlign: 'center',
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
});