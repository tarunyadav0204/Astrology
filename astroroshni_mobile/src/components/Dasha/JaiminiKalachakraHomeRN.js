import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Modal,
  ActivityIndicator,
} from 'react-native';
import { COLORS, API_BASE_URL } from '../../utils/constants';
import AsyncStorage from '@react-native-async-storage/async-storage';

const JaiminiKalachakraHomeRN = ({ birthData }) => {
  const [dashadata, setDashadata] = useState(null);
  const [selectedMaha, setSelectedMaha] = useState(null);
  const [antardashas, setAntardashas] = useState([]);
  const [selectedAntar, setSelectedAntar] = useState(null);
  const [showBottomSheet, setShowBottomSheet] = useState(false);
  const [showSkipReasons, setShowSkipReasons] = useState(false);
  const [selectedSkippedRashi, setSelectedSkippedRashi] = useState(null);
  const [skipReasons, setSkipReasons] = useState(null);
  const [loading, setLoading] = useState(true);
  const mahaScrollRef = useRef(null);
  const antarScrollRef = useRef(null);

  useEffect(() => {
    if (birthData) {
      loadJaiminiData();
    }
  }, [birthData]);

  useEffect(() => {
    if (dashadata?.periods) {
      const currentPeriod = dashadata.periods.find(p => p.current);
      if (currentPeriod) {
        setSelectedMaha(currentPeriod);
        loadAntardashas(currentPeriod.sign);
        
        // Auto-scroll to current mahadasha
        setTimeout(() => {
          scrollToCurrentMaha();
        }, 100);
      }
    }
  }, [dashadata]);

  const loadJaiminiData = async () => {
    try {
      setLoading(true);
      const token = await AsyncStorage.getItem('authToken');
      
      const formattedBirthData = {
        name: birthData.name,
        date: birthData.date.includes('T') ? birthData.date.split('T')[0] : birthData.date,
        time: birthData.time.includes('T') ? new Date(birthData.time).toTimeString().slice(0, 5) : birthData.time,
        latitude: parseFloat(birthData.latitude),
        longitude: parseFloat(birthData.longitude),
        timezone: birthData.timezone || 5.5,
        location: birthData.place || 'Unknown'
      };
      
      const response = await fetch(`${API_BASE_URL}/api/calculate-jaimini-kalchakra-dasha`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          birth_data: formattedBirthData
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        
        if (data.error) {
          console.log('JAIMINI HOME BACKEND ERROR:', data.error);
          console.log('JAIMINI HOME SYSTEM INFO:', data.system);
          return;
        }
        
        // Check if we have valid data structure
        if (!data.periods || data.periods.length === 0) {
          console.log('WARNING: No Jaimini periods data received in home component');
          return;
        }
        
        setDashadata(data);
      } else {
        console.log('Response not OK:', response.status, response.statusText);
      }
    } catch (error) {
      console.error('Failed to load Jaimini data:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadAntardashas = async (mahaSign) => {
    try {
      const token = await AsyncStorage.getItem('authToken');
      
      const formattedBirthData = {
        name: birthData.name,
        date: birthData.date.includes('T') ? birthData.date.split('T')[0] : birthData.date,
        time: birthData.time.includes('T') ? new Date(birthData.time).toTimeString().slice(0, 5) : birthData.time,
        latitude: parseFloat(birthData.latitude),
        longitude: parseFloat(birthData.longitude),
        timezone: birthData.timezone || 5.5,
        location: birthData.place || 'Unknown'
      };
      
      const response = await fetch(`${API_BASE_URL}/api/calculate-jaimini-kalchakra-antardasha`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          birth_data: formattedBirthData,
          maha_sign: mahaSign
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        const antarPeriods = data.antar_periods || [];
        setAntardashas(antarPeriods);
        
        // Auto-select and scroll to current antardasha
        const currentAntar = antarPeriods.find(a => a.current);
        if (currentAntar) {
          setSelectedAntar(currentAntar);
          
          // Auto-scroll to current antardasha
          setTimeout(() => {
            scrollToCurrentAntar(antarPeriods);
          }, 100);
        }
      }
    } catch (error) {
      console.error('Failed to load antardashas:', error);
    }
  };

  const scrollToCurrentMaha = () => {
    if (!mahaScrollRef.current || !dashadata?.periods) return;
    
    const currentIndex = dashadata.periods.findIndex(m => m.current);
    if (currentIndex >= 0) {
      const chipWidth = 120;
      // Show 2-3 periods before current for context, but don't scroll past beginning
      const scrollPosition = Math.max(0, (currentIndex - 2) * chipWidth);
      setTimeout(() => {
        mahaScrollRef.current.scrollTo({ x: scrollPosition, animated: true });
      }, 300);
    } else {
      // If no current period found, scroll to beginning to show from birth
      setTimeout(() => {
        mahaScrollRef.current.scrollTo({ x: 0, animated: true });
      }, 300);
    }
  };

  const scrollToCurrentAntar = (antarPeriods) => {
    if (!antarScrollRef.current || !antarPeriods) return;
    
    const currentIndex = antarPeriods.findIndex(a => a.current);
    if (currentIndex >= 0) {
      const chipWidth = 90;
      const scrollPosition = Math.max(0, (currentIndex - 1) * chipWidth);
      setTimeout(() => {
        antarScrollRef.current.scrollTo({ x: scrollPosition, animated: true });
      }, 300);
    }
  };

  const handleMahaClick = (maha) => {
    setSelectedMaha(maha);
    loadAntardashas(maha.sign);
  };

  const handleAntarClick = async (antar) => {
    setSelectedAntar(antar);
    setShowBottomSheet(true);
  };

  const handleSkippedRashiClick = async (skippedRashi) => {
    try {
      setSelectedSkippedRashi(skippedRashi);
      const token = await AsyncStorage.getItem('authToken');
      
      const formattedBirthData = {
        name: birthData.name,
        date: birthData.date.includes('T') ? birthData.date.split('T')[0] : birthData.date,
        time: birthData.time.includes('T') ? new Date(birthData.time).toTimeString().slice(0, 5) : birthData.time,
        latitude: parseFloat(birthData.latitude),
        longitude: parseFloat(birthData.longitude),
        timezone: birthData.timezone || 5.5,
        location: birthData.place || 'Unknown'
      };
      
      const response = await fetch(`${API_BASE_URL}/api/jaimini-rashi-skip-reasons`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          birth_data: formattedBirthData,
          rashi_index: skippedRashi.sign,
          threshold: 25.0
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        setSkipReasons(data);
        setShowSkipReasons(true);
      }
    } catch (error) {
      console.error('Failed to load skip reasons:', error);
    }
  };

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'short' 
    });
  };

  const formatFullDate = (dateStr) => {
    return new Date(dateStr).toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'short',
      day: 'numeric'
    });
  };

  const calculateProgress = (start, end, current = new Date()) => {
    const startTime = new Date(start).getTime();
    const endTime = new Date(end).getTime();
    const currentTime = current.getTime();
    
    if (currentTime < startTime) return 0;
    if (currentTime > endTime) return 100;
    
    return Math.round(((currentTime - startTime) / (endTime - startTime)) * 100);
  };

  const getTimeRemaining = (endDate) => {
    const end = new Date(endDate);
    const now = new Date();
    const diff = end - now;
    
    if (diff <= 0) return 'Ended';
    
    const years = Math.floor(diff / (365.25 * 24 * 60 * 60 * 1000));
    const months = Math.floor((diff % (365.25 * 24 * 60 * 60 * 1000)) / (30.44 * 24 * 60 * 60 * 1000));
    
    if (years > 0) return `${years}y ${months}m`;
    return `${months}m`;
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={COLORS.accent} />
        <Text style={styles.loadingText}>Loading Jaimini Kalchakra...</Text>
      </View>
    );
  }

  if (!dashadata || !dashadata.periods) {
    return (
      <View style={styles.errorContainer}>
        <Text style={styles.errorText}>No Jaimini data available</Text>
      </View>
    );
  }

  const currentMaha = dashadata.periods.find(p => p.current);
  const currentAntar = antardashas.find(a => a.current);

  return (
    <ScrollView style={styles.container} showsVerticalScrollIndicator={false}>
      {/* Current Summary Card */}
      <View style={styles.currentSummary}>
        <View style={styles.currentHeader}>
          <Text style={styles.currentTitle}>Current Period</Text>
          <Text style={styles.todayDate}>{new Date().toLocaleDateString()}</Text>
        </View>
        
        <View style={styles.currentPeriods}>
          <View style={styles.periodInfo}>
            <Text style={styles.periodMain}>
              {currentMaha?.sign} Mahadasha {currentAntar ? `→ ${currentAntar.sign} Antardasha` : ''}
            </Text>
            <View style={styles.periodDetails}>
              <View style={[styles.chakraBadge, { backgroundColor: currentMaha?.chakra === 1 ? '#4caf50' : '#ff9800' }]}>
                <Text style={styles.chakraBadgeText}>Chakra {currentMaha?.chakra}</Text>
              </View>
              <Text style={styles.directionArrow}>
                {currentMaha?.direction === 'Forward' ? '→' : '←'}
              </Text>
            </View>
          </View>
          
          <View style={styles.progressSection}>
            <View style={styles.progressBar}>
              <View 
                style={[
                  styles.progressFill,
                  { width: `${calculateProgress(currentMaha?.start_date, currentMaha?.end_date)}%` }
                ]}
              />
            </View>
            <Text style={styles.progressText}>
              {calculateProgress(currentMaha?.start_date, currentMaha?.end_date)}% • 
              Ends: {formatDate(currentMaha?.end_date)}
            </Text>
          </View>
        </View>
      </View>

      {/* Mahadasha Row */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Mahadasha Timeline</Text>
        <ScrollView 
          ref={mahaScrollRef}
          horizontal 
          showsHorizontalScrollIndicator={false}
          style={styles.mahaScroll}
        >
          {dashadata.periods?.map((maha, index) => (
            <TouchableOpacity
              key={`${maha.sign}-${index}`}
              style={[
                styles.mahaChip,
                selectedMaha?.sign === maha.sign && styles.selectedMahaChip,
                maha.current && styles.currentMahaChip,
                { backgroundColor: maha.chakra === 1 ? '#e8f5e8' : '#fff3e0' }
              ]}
              onPress={() => handleMahaClick(maha)}
            >
              <View style={styles.chipHeader}>
                <Text style={styles.signName}>{maha.sign}</Text>
                <View style={[styles.chakraBadgeSmall, { backgroundColor: maha.chakra === 1 ? '#4caf50' : '#ff9800' }]}>
                  <Text style={styles.chakraBadgeSmallText}>C{maha.chakra}</Text>
                </View>
              </View>
              <View style={styles.chipDetails}>
                <Text style={styles.directionArrow}>
                  {maha.direction === 'Forward' ? '→' : '←'}
                </Text>
                <Text style={styles.years}>{Math.round(maha.duration_years)}y</Text>
                <Text style={styles.cycleText}>Cycle {maha.cycle || 1}</Text>
              </View>
              <Text style={styles.chipDates}>
                {formatFullDate(maha.start_date)}
              </Text>
              <Text style={styles.chipDates}>
                {formatFullDate(maha.end_date)}
              </Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      </View>

      {/* Antardasha Row */}
      {selectedMaha && antardashas.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Antardasha for {selectedMaha.sign}</Text>
          <ScrollView 
            ref={antarScrollRef}
            horizontal 
            showsHorizontalScrollIndicator={false}
            style={styles.antarScroll}
          >
            {antardashas.map((antar, index) => (
              <TouchableOpacity
                key={`${antar.sign}-${index}`}
                style={[
                  styles.antarChip,
                  antar.current && styles.currentAntarChip
                ]}
                onPress={() => handleAntarClick(antar)}
              >
                <Text style={styles.antarName}>{antar.sign}</Text>
                <Text style={styles.antarDates}>
                  {formatFullDate(antar.start_date)}
                </Text>
                <Text style={styles.antarDates}>
                  {formatFullDate(antar.end_date)}
                </Text>
              </TouchableOpacity>
            ))}
          </ScrollView>
        </View>
      )}

      {/* Skipped Rashis Section */}
      {dashadata?.skipped_rashis && dashadata.skipped_rashis.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Skipped Rashis (Weak Signs)</Text>
          <Text style={styles.sectionSubtitle}>Tap to see why these rashis are skipped in cycles</Text>
          <View style={styles.skippedContainer}>
            {dashadata.skipped_rashis.map((skipped, index) => {
              console.log('Rendering skipped rashi:', skipped);
              return (
                <TouchableOpacity
                  key={`${skipped.sign_name}-${skipped.cycle}-${index}`}
                  style={styles.skippedChip}
                  onPress={() => handleSkippedRashiClick(skipped)}
                >
                  <Text style={styles.skippedName}>{skipped.sign_name}</Text>
                  <Text style={styles.skippedCycle}>Cycle {skipped.cycle}</Text>
                  <View style={[styles.chakraBadgeSmall, { backgroundColor: '#f44336' }]}>
                    <Text style={styles.chakraBadgeSmallText}>SKIP</Text>
                  </View>
                </TouchableOpacity>
              );
            })}
          </View>
        </View>
      )}

      {/* Antardasha Bottom Sheet */}
      <Modal
        visible={showBottomSheet}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setShowBottomSheet(false)}
      >
        <View style={styles.bottomSheetOverlay}>
          <View style={styles.bottomSheet}>
            <View style={styles.sheetHeader}>
              <Text style={styles.sheetTitle}>{selectedAntar?.sign} Antardasha</Text>
              <TouchableOpacity 
                style={styles.closeBtn}
                onPress={() => setShowBottomSheet(false)}
              >
                <Text style={styles.closeBtnText}>×</Text>
              </TouchableOpacity>
            </View>
            
            <ScrollView style={styles.sheetContent}>
              <View style={styles.detailSection}>
                <Text style={styles.detailTitle}>Duration</Text>
                <Text style={styles.detailText}>
                  {formatDate(selectedAntar?.start_date)} - {formatDate(selectedAntar?.end_date)}
                </Text>
                <Text style={styles.detailText}>
                  Duration: {Math.round(selectedAntar?.years * 12)} months
                </Text>
              </View>

              <View style={styles.detailSection}>
                <Text style={styles.detailTitle}>Progress</Text>
                <View style={styles.strengthBar}>
                  <View 
                    style={[
                      styles.strengthFill,
                      { width: `${calculateProgress(selectedAntar?.start_date, selectedAntar?.end_date)}%` }
                    ]}
                  />
                </View>
                <Text style={styles.detailText}>
                  {calculateProgress(selectedAntar?.start_date, selectedAntar?.end_date)}% complete
                </Text>
              </View>

              <View style={styles.detailSection}>
                <Text style={styles.detailTitle}>Time Remaining</Text>
                <Text style={styles.detailText}>
                  {getTimeRemaining(selectedAntar?.end_date)}
                </Text>
              </View>
            </ScrollView>
          </View>
        </View>
      </Modal>

      {/* Skip Reasons Bottom Sheet */}
      <Modal
        visible={showSkipReasons}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setShowSkipReasons(false)}
      >
        <View style={styles.bottomSheetOverlay}>
          <View style={styles.bottomSheet}>
            <View style={styles.sheetHeader}>
              <Text style={styles.sheetTitle}>Why {selectedSkippedRashi?.sign_name} is Skipped</Text>
              <TouchableOpacity 
                style={styles.closeBtn}
                onPress={() => setShowSkipReasons(false)}
              >
                <Text style={styles.closeBtnText}>×</Text>
              </TouchableOpacity>
            </View>
            
            <ScrollView style={styles.sheetContent}>
              {skipReasons && (
                <>
                  <View style={styles.detailSection}>
                    <Text style={styles.detailTitle}>Overall Strength</Text>
                    <View style={styles.strengthBar}>
                      <View 
                        style={[
                          styles.strengthFill,
                          { 
                            width: `${Math.max(5, skipReasons.total_strength)}%`,
                            backgroundColor: skipReasons.is_skipped ? '#f44336' : '#4caf50'
                          }
                        ]}
                      />
                    </View>
                    <Text style={styles.detailText}>
                      {skipReasons.total_strength}/100 (Threshold: {skipReasons.threshold})
                    </Text>
                    <Text style={[styles.detailText, { color: skipReasons.is_skipped ? '#f44336' : '#4caf50' }]}>
                      {skipReasons.is_skipped ? 'WEAK - Skipped in cycles' : 'STRONG - Not skipped'}
                    </Text>
                  </View>

                  {Object.entries(skipReasons.components).map(([component, data]) => (
                    <View key={component} style={styles.detailSection}>
                      <Text style={styles.detailTitle}>
                        {component.charAt(0).toUpperCase() + component.slice(1)} ({data.weight})
                      </Text>
                      <View style={styles.strengthBar}>
                        <View 
                          style={[
                            styles.strengthFill,
                            { 
                              width: `${Math.max(5, (data.score / 60) * 100)}%`,
                              backgroundColor: data.score > 30 ? '#4caf50' : data.score > 15 ? '#ff9800' : '#f44336'
                            }
                          ]}
                        />
                      </View>
                      <Text style={styles.detailText}>Score: {data.score}/60</Text>
                      {data.details.map((detail, index) => (
                        <Text key={index} style={styles.detailBullet}>• {detail}</Text>
                      ))}
                    </View>
                  ))}
                </>
              )}
            </ScrollView>
          </View>
        </View>
      </Modal>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  loadingText: {
    marginTop: 10,
    fontSize: 16,
    color: COLORS.textSecondary,
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  errorText: {
    fontSize: 16,
    color: COLORS.error,
    textAlign: 'center',
  },
  currentSummary: {
    backgroundColor: COLORS.surface,
    borderRadius: 12,
    padding: 16,
    margin: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  currentHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  currentTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: COLORS.textPrimary,
  },
  todayDate: {
    fontSize: 14,
    color: COLORS.textSecondary,
  },
  currentPeriods: {
    gap: 12,
  },
  periodInfo: {
    gap: 8,
  },
  periodMain: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.textPrimary,
  },
  periodDetails: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  chakraBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  chakraBadgeText: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.white,
  },
  directionArrow: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.textSecondary,
  },
  progressSection: {
    gap: 4,
  },
  progressBar: {
    height: 8,
    backgroundColor: COLORS.lightGray,
    borderRadius: 4,
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#4caf50',
    borderRadius: 4,
  },
  progressText: {
    fontSize: 12,
    color: COLORS.textSecondary,
  },
  section: {
    marginHorizontal: 16,
    marginBottom: 20,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.textPrimary,
    marginBottom: 12,
  },
  mahaScroll: {
    flexDirection: 'row',
  },
  mahaChip: {
    width: 110,
    padding: 12,
    marginRight: 8,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  selectedMahaChip: {
    borderColor: '#4caf50',
    borderWidth: 2,
  },
  currentMahaChip: {
    backgroundColor: '#e3f2fd',
    borderColor: '#2196f3',
  },
  chipHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  signName: {
    fontSize: 14,
    fontWeight: '700',
    color: COLORS.textPrimary,
  },
  chakraBadgeSmall: {
    paddingHorizontal: 4,
    paddingVertical: 2,
    borderRadius: 8,
  },

  cycleText: {
    fontSize: 10,
    color: '#2196f3',
    fontWeight: '600',
  },
  chakraBadgeSmallText: {
    fontSize: 10,
    fontWeight: '600',
    color: COLORS.white,
  },
  chipDetails: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  years: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.textSecondary,
  },
  chipDates: {
    fontSize: 10,
    color: COLORS.textSecondary,
    textAlign: 'center',
  },
  antarScroll: {
    flexDirection: 'row',
  },
  antarChip: {
    width: 80,
    padding: 8,
    marginRight: 6,
    borderRadius: 6,
    backgroundColor: '#f5f5f5',
    borderWidth: 1,
    borderColor: COLORS.border,
    alignItems: 'center',
  },
  currentAntarChip: {
    backgroundColor: '#e8f5e8',
    borderColor: '#4caf50',
  },
  antarName: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.textPrimary,
    marginBottom: 2,
  },
  antarDuration: {
    fontSize: 10,
    color: COLORS.textSecondary,
    marginBottom: 2,
  },
  antarDates: {
    fontSize: 9,
    color: COLORS.textSecondary,
  },
  bottomSheetOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'flex-end',
  },
  bottomSheet: {
    backgroundColor: COLORS.surface,
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    maxHeight: '70%',
  },
  sheetHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  sheetTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: COLORS.textPrimary,
  },
  closeBtn: {
    padding: 4,
  },
  closeBtnText: {
    fontSize: 24,
    color: COLORS.textSecondary,
  },
  sheetContent: {
    padding: 20,
  },
  detailSection: {
    marginBottom: 16,
  },
  detailTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.textPrimary,
    marginBottom: 8,
  },
  detailText: {
    fontSize: 14,
    color: COLORS.textSecondary,
    marginBottom: 4,
  },
  detailBullet: {
    fontSize: 13,
    color: COLORS.textSecondary,
    marginLeft: 8,
    marginBottom: 2,
  },
  sectionSubtitle: {
    fontSize: 12,
    color: COLORS.textSecondary,
    marginBottom: 8,
  },
  skippedContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  skippedChip: {
    backgroundColor: '#ffebee',
    borderColor: '#f44336',
    borderWidth: 1,
    borderRadius: 8,
    padding: 8,
    minWidth: 80,
    alignItems: 'center',
  },
  skippedName: {
    fontSize: 12,
    fontWeight: '600',
    color: '#d32f2f',
    marginBottom: 2,
  },
  skippedCycle: {
    fontSize: 10,
    color: '#666',
    marginBottom: 4,
  },
  strengthBar: {
    height: 8,
    backgroundColor: COLORS.lightGray,
    borderRadius: 4,
    marginBottom: 8,
  },
  strengthFill: {
    height: '100%',
    backgroundColor: '#4caf50',
    borderRadius: 4,
  },
});

export default JaiminiKalachakraHomeRN;