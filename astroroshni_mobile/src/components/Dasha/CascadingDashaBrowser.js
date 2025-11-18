import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  ActivityIndicator,
  TouchableOpacity,
  Modal,
  SafeAreaView,
  Platform,
} from 'react-native';
import DateTimePicker from '@react-native-community/datetimepicker';
import { Ionicons } from '@expo/vector-icons';
import { COLORS, API_BASE_URL } from '../../utils/constants';
import { chartAPI } from '../../services/api';
import AsyncStorage from '@react-native-async-storage/async-storage';

const CascadingDashaBrowser = ({ visible, onClose, birthData }) => {
  const [cascadingData, setCascadingData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [transitDate, setTransitDate] = useState(new Date());
  const [selectedDashas, setSelectedDashas] = useState({});
  const [showDatePicker, setShowDatePicker] = useState(false);
  const scrollRefs = {
    maha: React.useRef(null),
    antar: React.useRef(null),
    pratyantar: React.useRef(null),
    sookshma: React.useRef(null),
    prana: React.useRef(null)
  };

  useEffect(() => {
    if (visible && birthData) {
      fetchCascadingDashas();
    }
  }, [visible, birthData, transitDate]);

  useEffect(() => {
    if (cascadingData) {
      autoSelectCurrentDashas();
    }
  }, [cascadingData]);

  // Auto-scroll to selected dashas
  useEffect(() => {
    Object.keys(selectedDashas).forEach(dashaType => {
      const selectedValue = selectedDashas[dashaType];
      const scrollRef = scrollRefs[dashaType];
      if (selectedValue && scrollRef?.current) {
        const options = getDashaOptions(dashaType);
        const selectedIndex = options.findIndex(d => d.planet === selectedValue);
        if (selectedIndex > 0) {
          setTimeout(() => {
            scrollRef.current?.scrollTo({ x: selectedIndex * 78, animated: true });
          }, 100);
        }
      }
    });
  }, [selectedDashas, cascadingData]);

  const fetchCascadingDashas = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const targetDate = transitDate.toISOString().split('T')[0];
      const token = await AsyncStorage.getItem('authToken');
      
      const formattedBirthData = {
        name: birthData.name,
        date: birthData.date.includes('T') ? birthData.date.split('T')[0] : birthData.date,
        time: birthData.time.includes('T') ? new Date(birthData.time).toTimeString().slice(0, 5) : birthData.time,
        latitude: parseFloat(birthData.latitude),
        longitude: parseFloat(birthData.longitude),
        timezone: birthData.timezone || 'Asia/Kolkata',
        location: birthData.place || 'Unknown'
      };
      
      const response = await fetch(`${API_BASE_URL}/api/calculate-cascading-dashas`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          birth_data: formattedBirthData,
          target_date: targetDate
        })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      
      const cascadingData = await response.json();
      setCascadingData(cascadingData);
    } catch (err) {
      console.error('Cascading fetch error:', err);
      setError('Failed to load cascading dasha data');
    } finally {
      setLoading(false);
    }
  };

  const autoSelectCurrentDashas = () => {
    if (!cascadingData) return;
    
    const currentSelections = {};
    
    const currentMaha = cascadingData.maha_dashas?.find(d => d.current);
    if (currentMaha) currentSelections.maha = currentMaha.planet;
    
    const currentAntar = cascadingData.antar_dashas?.find(d => d.current);
    if (currentAntar) currentSelections.antar = currentAntar.planet;
    
    const currentPratyantar = cascadingData.pratyantar_dashas?.find(d => d.current);
    if (currentPratyantar) currentSelections.pratyantar = currentPratyantar.planet;
    
    const currentSookshma = cascadingData.sookshma_dashas?.find(d => d.current);
    if (currentSookshma) currentSelections.sookshma = currentSookshma.planet;
    
    const currentPrana = cascadingData.prana_dashas?.find(d => d.current);
    if (currentPrana) currentSelections.prana = currentPrana.planet;
    
    setSelectedDashas(currentSelections);
  };

  const adjustDate = (days) => {
    const newDate = new Date(transitDate);
    newDate.setDate(newDate.getDate() + days);
    setTransitDate(newDate);
  };

  const handleDashaSelection = async (dashaType, option) => {
    // Find the selected dasha details
    const selectedDasha = getDashaOptions(dashaType).find(d => d.planet === option);
    if (!selectedDasha) return;
    
    // Set new date to middle of selected dasha period to get its children
    const startDate = new Date(selectedDasha.start);
    const endDate = new Date(selectedDasha.end);
    const middleDate = new Date(startDate.getTime() + (endDate.getTime() - startDate.getTime()) / 2);
    
    // Update selected dashas
    setSelectedDashas(prev => {
      const newSelections = { ...prev, [dashaType]: option };
      
      // Clear child selections when parent changes
      if (dashaType === 'maha') {
        delete newSelections.antar;
        delete newSelections.pratyantar;
        delete newSelections.sookshma;
        delete newSelections.prana;
      } else if (dashaType === 'antar') {
        delete newSelections.pratyantar;
        delete newSelections.sookshma;
        delete newSelections.prana;
      } else if (dashaType === 'pratyantar') {
        delete newSelections.sookshma;
        delete newSelections.prana;
      } else if (dashaType === 'sookshma') {
        delete newSelections.prana;
      }
      
      return newSelections;
    });
    
    // Update transit date to fetch children for selected dasha
    setTransitDate(middleDate);
  };

  const getDashaOptions = (dashaType) => {
    if (!cascadingData) return [];
    
    switch (dashaType) {
      case 'maha':
        return cascadingData.maha_dashas || [];
      case 'antar':
        return cascadingData.antar_dashas || [];
      case 'pratyantar':
        return cascadingData.pratyantar_dashas || [];
      case 'sookshma':
        return cascadingData.sookshma_dashas || [];
      case 'prana':
        return cascadingData.prana_dashas || [];
      default:
        return [];
    }
  };



  const renderDateNavigation = () => (
    <View style={styles.dateNav}>
      <View style={styles.compactNavRow}>
        <View style={styles.navButtonGroup}>
          <TouchableOpacity style={styles.compactNavButton} onPress={() => adjustDate(-30)}>
            <Text style={styles.compactNavText}>-1M</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.compactNavButton} onPress={() => adjustDate(-7)}>
            <Text style={styles.compactNavText}>-1W</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.compactNavButton} onPress={() => adjustDate(-1)}>
            <Text style={styles.compactNavText}>-1D</Text>
          </TouchableOpacity>
        </View>
        
        <TouchableOpacity style={styles.compactDateButton} onPress={() => setTransitDate(new Date())}>
          <Text style={styles.compactDateText}>{transitDate.toLocaleDateString('en-US', {month: 'short', day: 'numeric'})}</Text>
        </TouchableOpacity>
        
        <TouchableOpacity style={styles.compactCalendarButton} onPress={() => setShowDatePicker(true)}>
          <Ionicons name="calendar" size={18} color={COLORS.white} />
        </TouchableOpacity>
        
        <View style={styles.navButtonGroup}>
          <TouchableOpacity style={styles.compactNavButton} onPress={() => adjustDate(1)}>
            <Text style={styles.compactNavText}>+1D</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.compactNavButton} onPress={() => adjustDate(7)}>
            <Text style={styles.compactNavText}>+1W</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.compactNavButton} onPress={() => adjustDate(30)}>
            <Text style={styles.compactNavText}>+1M</Text>
          </TouchableOpacity>
        </View>
      </View>
      
      {showDatePicker && (
        <View>
          <DateTimePicker
            value={transitDate}
            mode="date"
            display={Platform.OS === 'ios' ? 'spinner' : 'default'}
            onChange={(event, selectedDate) => {
              if (Platform.OS === 'android') {
                setShowDatePicker(false);
                if (selectedDate) {
                  setTransitDate(selectedDate);
                }
              } else {
                if (selectedDate) {
                  setTransitDate(selectedDate);
                }
              }
            }}
          />
          {Platform.OS === 'ios' && (
            <TouchableOpacity 
              style={styles.doneButton} 
              onPress={() => setShowDatePicker(false)}
            >
              <Text style={styles.doneButtonText}>Done</Text>
            </TouchableOpacity>
          )}
        </View>
      )}
    </View>
  );



  const getDashaDetails = (dashaType, planet) => {
    if (!cascadingData || !planet) return null;
    
    let dashas = [];
    switch (dashaType) {
      case 'maha': dashas = cascadingData.maha_dashas || []; break;
      case 'antar': dashas = cascadingData.antar_dashas || []; break;
      case 'pratyantar': dashas = cascadingData.pratyantar_dashas || []; break;
      case 'sookshma': dashas = cascadingData.sookshma_dashas || []; break;
      case 'prana': dashas = cascadingData.prana_dashas || []; break;
      default: return null;
    }
    
    return dashas.find(d => d.planet === planet);
  };

  const renderBreadcrumb = () => {
    if (!cascadingData) {
      return (
        <View style={styles.breadcrumb}>
          <Text style={styles.breadcrumbText}>Select dashas to see hierarchy</Text>
        </View>
      );
    }

    const breadcrumbItems = [];
    
    if (selectedDashas.maha) {
      const details = getDashaDetails('maha', selectedDashas.maha);
      breadcrumbItems.push({ planet: selectedDashas.maha, details });
    }
    
    if (selectedDashas.antar) {
      const details = getDashaDetails('antar', selectedDashas.antar);
      breadcrumbItems.push({ planet: selectedDashas.antar, details });
    }
    
    if (selectedDashas.pratyantar) {
      const details = getDashaDetails('pratyantar', selectedDashas.pratyantar);
      breadcrumbItems.push({ planet: selectedDashas.pratyantar, details });
    }
    
    if (selectedDashas.sookshma) {
      const details = getDashaDetails('sookshma', selectedDashas.sookshma);
      breadcrumbItems.push({ planet: selectedDashas.sookshma, details });
    }
    
    if (selectedDashas.prana) {
      const details = getDashaDetails('prana', selectedDashas.prana);
      breadcrumbItems.push({ planet: selectedDashas.prana, details });
    }
    
    return (
      <View style={styles.breadcrumb}>
        {breadcrumbItems.length === 0 ? (
          <Text style={styles.breadcrumbText}>Select dashas to see hierarchy</Text>
        ) : (
          <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.breadcrumbScroll}>
            {breadcrumbItems.map((item, index) => (
              <View key={`breadcrumb-${item.planet}-${index}`} style={styles.breadcrumbRow}>
                <View style={styles.breadcrumbCard}>
                  <Text style={styles.breadcrumbPlanet}>{item.planet}</Text>
                  {item.details && (
                    <>
                      <Text style={styles.breadcrumbPeriod}>{item.details.years?.toFixed(1)}y</Text>
                      <Text style={styles.breadcrumbDates}>
                        {new Date(item.details.start).toLocaleDateString('en-US', {month: 'short', year: '2-digit'})} - {new Date(item.details.end).toLocaleDateString('en-US', {month: 'short', year: '2-digit'})}
                      </Text>
                    </>
                  )}
                </View>
                {index < breadcrumbItems.length - 1 && (
                  <Text style={styles.breadcrumbArrow}>→</Text>
                )}
              </View>
            ))}
          </ScrollView>
        )}
      </View>
    );
  };

  const renderDashaSelector = (dashaType, title) => {
    const options = getDashaOptions(dashaType);
    const selectedValue = selectedDashas[dashaType];
    
    return (
      <View style={styles.selectorContainer}>
        <Text style={styles.selectorLabel}>{title}</Text>
        <ScrollView ref={scrollRefs[dashaType]} horizontal showsHorizontalScrollIndicator={false} style={styles.optionsScroll}>
          {options.length === 0 ? (
            <View style={[styles.optionCard, styles.disabledOption]}>
              <Text style={styles.disabledOptionText}>No options available</Text>
            </View>
          ) : (
            options.map((dasha, index) => {
              const isSelected = selectedValue === dasha.planet;
              const isCurrent = dasha.current;
              
              return (
                <TouchableOpacity
                  key={`${dasha.planet}-${index}`}
                  style={[
                    styles.optionCard,
                    isSelected && styles.selectedOptionCard,
                    isCurrent && styles.currentOptionCard
                  ]}
                  onPress={() => {
                    handleDashaSelection(dashaType, dasha.planet);
                  }}
                >
                  <Text style={[
                    styles.optionPlanet,
                    isSelected && styles.selectedOptionPlanet,
                    isCurrent && styles.currentOptionPlanet
                  ]}>
                    {dasha.planet}
                  </Text>
                  <Text style={[
                    styles.optionPeriod,
                    isSelected && styles.selectedOptionPeriod,
                    isCurrent && styles.currentOptionPeriod
                  ]}>
                    {dasha.years?.toFixed(1)}y
                  </Text>
                  <Text style={[
                    styles.optionDates,
                    isSelected && styles.selectedOptionDates,
                    isCurrent && styles.currentOptionDates
                  ]}>
                    {new Date(dasha.start).toLocaleDateString('en-US', {day: 'numeric', month: 'short', year: '2-digit'})} - {new Date(dasha.end).toLocaleDateString('en-US', {day: 'numeric', month: 'short', year: '2-digit'})}
                  </Text>
                </TouchableOpacity>
              );
            })
          )}
        </ScrollView>
      </View>
    );
  };

  if (loading) {
    return (
      <Modal visible={visible} animationType="slide">
        <SafeAreaView style={styles.container}>
          <View style={styles.header}>
            <TouchableOpacity onPress={onClose} style={styles.closeButton}>
              <Ionicons name="close" size={24} color={COLORS.textPrimary} />
            </TouchableOpacity>
            <Text style={styles.headerTitle}>Cascading Dasha Browser</Text>
            <View style={styles.placeholder} />
          </View>
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color={COLORS.accent} />
            <Text style={styles.loadingText}>Loading Dasha Data...</Text>
          </View>
        </SafeAreaView>
      </Modal>
    );
  }

  if (error) {
    return (
      <Modal visible={visible} animationType="slide">
        <SafeAreaView style={styles.container}>
          <View style={styles.header}>
            <TouchableOpacity onPress={onClose} style={styles.closeButton}>
              <Ionicons name="close" size={24} color={COLORS.textPrimary} />
            </TouchableOpacity>
            <Text style={styles.headerTitle}>Cascading Dasha Browser</Text>
            <View style={styles.placeholder} />
          </View>
          <View style={styles.errorContainer}>
            <Text style={styles.errorText}>{error}</Text>
            <TouchableOpacity style={styles.retryButton} onPress={fetchCascadingDashas}>
              <Text style={styles.retryText}>Retry</Text>
            </TouchableOpacity>
          </View>
        </SafeAreaView>
      </Modal>
    );
  }

  return (
    <Modal visible={visible} animationType="slide">
      <SafeAreaView style={styles.container}>
        <View style={styles.header}>
          <TouchableOpacity onPress={onClose} style={styles.closeButton}>
            <Ionicons name="close" size={24} color={COLORS.textPrimary} />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>Dashas for {birthData?.name || 'User'}</Text>
          <View style={styles.placeholder} />
        </View>
        
        <ScrollView style={styles.content}>
          {renderDateNavigation()}
          {renderBreadcrumb()}
          
          <View style={styles.selectorsContainer}>
            {renderDashaSelector('maha', 'Maha Dasha')}
            {renderDashaSelector('antar', 'Antar Dasha')}
            {renderDashaSelector('pratyantar', 'Pratyantar Dasha')}
            {renderDashaSelector('sookshma', 'Sookshma Dasha')}
            {renderDashaSelector('prana', 'Prana Dasha')}
          </View>
        </ScrollView>
      </SafeAreaView>
    </Modal>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 16,
    backgroundColor: COLORS.surface,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  closeButton: {
    padding: 8,
    borderRadius: 8,
    backgroundColor: COLORS.lightGray,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: COLORS.textPrimary,
  },
  placeholder: {
    width: 40,
  },
  content: {
    flex: 1,
    padding: 16,
  },
  dateNav: {
    marginBottom: 12,
  },
  compactNavRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: COLORS.surface,
    borderRadius: 12,
    padding: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  navButtonGroup: {
    flexDirection: 'row',
    gap: 4,
  },
  compactNavButton: {
    paddingHorizontal: 6,
    paddingVertical: 4,
    backgroundColor: COLORS.lightGray,
    borderRadius: 6,
    minWidth: 28,
  },
  compactNavText: {
    color: COLORS.accent,
    fontSize: 9,
    fontWeight: '600',
    textAlign: 'center',
  },
  compactDateButton: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    backgroundColor: COLORS.accent,
    borderRadius: 8,
    minWidth: 80,
    height: 32,
    justifyContent: 'center',
  },
  compactDateText: {
    fontSize: 12,
    fontWeight: '700',
    color: COLORS.white,
    textAlign: 'center',
  },
  compactCalendarButton: {
    padding: 8,
    backgroundColor: COLORS.accent,
    borderRadius: 8,
    height: 32,
    width: 32,
    justifyContent: 'center',
    alignItems: 'center',
  },

  breadcrumb: {
    padding: 10,
    backgroundColor: COLORS.lightGray,
    borderRadius: 8,
    marginBottom: 8,
  },
  breadcrumbText: {
    fontSize: 14,
    color: COLORS.textSecondary,
    textAlign: 'center',
  },
  breadcrumbScroll: {
    flexDirection: 'row',
  },
  breadcrumbRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  breadcrumbCard: {
    backgroundColor: COLORS.surface,
    borderRadius: 6,
    padding: 8,
    marginRight: 8,
    minWidth: 70,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  breadcrumbPlanet: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.accent,
    textAlign: 'center',
  },
  breadcrumbPeriod: {
    fontSize: 11,
    color: COLORS.textPrimary,
    textAlign: 'center',
    marginTop: 2,
  },
  breadcrumbDates: {
    fontSize: 9,
    color: COLORS.textSecondary,
    textAlign: 'center',
    marginTop: 1,
  },
  breadcrumbArrow: {
    fontSize: 16,
    color: COLORS.textSecondary,
    marginHorizontal: 4,
  },
  selectorsContainer: {
    gap: 8,
  },
  selectorContainer: {
    backgroundColor: COLORS.surface,
    borderRadius: 8,
    padding: 12,
  },
  selectorLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.textPrimary,
    marginBottom: 6,
  },
  optionsScroll: {
    flexDirection: 'row',
  },
  optionCard: {
    backgroundColor: COLORS.lightGray,
    borderRadius: 6,
    padding: 6,
    marginRight: 6,
    minWidth: 75,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  selectedOptionCard: {
    backgroundColor: COLORS.accent,
    borderColor: COLORS.accent,
  },
  disabledOption: {
    opacity: 0.5,
    backgroundColor: COLORS.lightGray,
  },
  optionPlanet: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.textPrimary,
    textAlign: 'center',
  },
  selectedOptionPlanet: {
    color: COLORS.white,
  },
  optionPeriod: {
    fontSize: 9,
    color: COLORS.textPrimary,
    textAlign: 'center',
    marginTop: 1,
  },
  selectedOptionPeriod: {
    color: COLORS.white,
  },
  optionDates: {
    fontSize: 7,
    color: COLORS.textSecondary,
    textAlign: 'center',
    marginTop: 1,
    lineHeight: 9,
  },
  selectedOptionDates: {
    color: COLORS.white,
  },
  currentOptionCard: {
    backgroundColor: '#ff6f00',
    borderColor: '#ff6f00',
  },
  currentOptionPlanet: {
    color: COLORS.white,
  },
  currentOptionPeriod: {
    color: COLORS.white,
  },
  currentOptionDates: {
    color: COLORS.white,
  },
  disabledOptionText: {
    color: COLORS.textSecondary,
    fontSize: 12,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    fontSize: 16,
    color: COLORS.textSecondary,
    marginTop: 16,
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 32,
  },
  errorText: {
    fontSize: 16,
    color: COLORS.error,
    textAlign: 'center',
    marginBottom: 16,
  },
  retryButton: {
    paddingHorizontal: 24,
    paddingVertical: 12,
    backgroundColor: COLORS.accent,
    borderRadius: 8,
  },
  retryText: {
    color: COLORS.white,
    fontSize: 16,
    fontWeight: '600',
  },
  doneButton: {
    backgroundColor: COLORS.accent,
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 8,
    alignSelf: 'center',
    marginTop: 10,
  },
  doneButtonText: {
    color: COLORS.white,
    fontSize: 16,
    fontWeight: '600',
  },
});

export default CascadingDashaBrowser;