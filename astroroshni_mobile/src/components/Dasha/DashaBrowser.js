import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Modal,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Ionicons from '@expo/vector-icons/Ionicons';
import { COLORS } from '../../utils/constants';
import { chartAPI } from '../../services/api';

const DashaBrowser = ({ visible, onClose, birthData }) => {
  const [transitDate, setTransitDate] = useState(new Date());
  const [cascadingData, setCascadingData] = useState(null);
  const [selectedDashas, setSelectedDashas] = useState({});
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (visible && birthData) {
      loadDashaData(new Date());
    }
  }, [visible, birthData]);

  const loadDashaData = async (date) => {
    setLoading(true);
    try {
      // Format birth data properly for API
      const formattedData = {
        ...birthData,
        date: typeof birthData.date === 'string' ? birthData.date.split('T')[0] : birthData.date,
        time: typeof birthData.time === 'string' ? birthData.time.split('T')[1]?.slice(0, 5) || birthData.time : birthData.time,
        latitude: parseFloat(birthData.latitude),
        longitude: parseFloat(birthData.longitude),
        timezone: birthData.timezone || 'Asia/Kolkata'
      };




      const response = await chartAPI.calculateDasha(formattedData);

      if (response.data.error) {
        setError(`Dasha calculation failed: ${response.data.error}`);
        return;
      }
      
      setCascadingData(response.data);
    } catch (error) {


    } finally {
      setLoading(false);
    }
  };

  const handleDateChange = (days) => {
    const newDate = new Date(transitDate);
    newDate.setDate(newDate.getDate() + days);
    setTransitDate(newDate);
    loadDashaData(newDate);
  };

  const resetToToday = () => {
    const today = new Date();
    setTransitDate(today);
    loadDashaData(today);
    setSelectedDashas({});
  };

  const formatDate = (date) => {
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric', 
      year: 'numeric' 
    });
  };

  const getCurrentDasha = (level) => {
    if (!cascadingData) return null;
    
    // Use current_dashas from backend response for accurate current periods
    if (level === 'maha' && cascadingData.current_dashas?.mahadasha) {
      return cascadingData.current_dashas.mahadasha;
    }
    
    if (level === 'antar' && cascadingData.current_dashas?.antardasha) {
      return cascadingData.current_dashas.antardasha;
    }
    
    if (level === 'pratyantar' && cascadingData.current_dashas?.pratyantardasha) {
      return cascadingData.current_dashas.pratyantardasha;
    }
    
    if (level === 'sookshma' && cascadingData.current_dashas?.sookshma) {
      return cascadingData.current_dashas.sookshma;
    }
    
    if (level === 'prana' && cascadingData.current_dashas?.prana) {
      return cascadingData.current_dashas.prana;
    }
    
    return null;
  };

  const getProgressPercentage = (dasha) => {
    if (!dasha) return 0;
    
    // For current dashas from backend, we don't have start/end dates
    // Return a default progress indication
    return 65; // Show some progress to indicate active period
  };

  const renderBreadcrumb = () => {
    const levels = ['maha', 'antar', 'pratyantar', 'sookshma', 'prana'];
    const breadcrumb = levels.map(level => getCurrentDasha(level)?.planet).filter(Boolean);
    
    return (
      <View style={styles.breadcrumb}>
        <Text style={styles.breadcrumbText}>
          {breadcrumb.join(' → ') || 'Loading...'}
        </Text>
      </View>
    );
  };

  const renderMainCard = () => {
    const currentMaha = getCurrentDasha('maha');
    const currentAntar = getCurrentDasha('antar');
    
    if (!currentMaha) return null;

    // Use mahadasha for main display, show antardasha as subtitle
    const progress = getProgressPercentage(currentMaha);
    
    return (
      <View style={styles.mainCard}>
        <Text style={styles.cardTitle}>🪐 {currentMaha.planet.toUpperCase()} MAHA</Text>
        {currentAntar && (
          <Text style={styles.cardSubtitle}>
            {currentAntar.planet} Antar
          </Text>
        )}
        
        <View style={styles.progressContainer}>
          <View style={styles.progressBar}>
            <View style={[styles.progressFill, { width: `${progress}%` }]} />
          </View>
          <Text style={styles.progressText}>
            Current Mahadasha Period
          </Text>
        </View>

        <Text style={styles.cardEffects}>
          💫 Focus: {getPlanetEffects(currentMaha.planet)}
        </Text>
      </View>
    );
  };

  const getPlanetEffects = (planet) => {
    const effects = {
      'Sun': 'Authority, Leadership, Government',
      'Moon': 'Emotions, Travel, Public',
      'Mars': 'Energy, Courage, Property',
      'Mercury': 'Communication, Business, Learning',
      'Jupiter': 'Wisdom, Teaching, Spirituality',
      'Venus': 'Relationships, Arts, Luxury',
      'Saturn': 'Discipline, Hard work, Delays',
      'Rahu': 'Innovation, Foreign, Technology',
      'Ketu': 'Spirituality, Research, Detachment'
    };
    return effects[planet] || 'General influences';
  };

  const renderLevelDots = () => {
    const levels = [
      { key: 'maha', label: 'M' },
      { key: 'antar', label: 'A' },
      { key: 'pratyantar', label: 'P' },
      { key: 'sookshma', label: 'S' },
      { key: 'prana', label: 'K' }
    ];

    return (
      <View style={styles.levelDots}>
        {levels.map((level, index) => (
          <TouchableOpacity key={level.key} style={styles.levelDot}>
            <Text style={styles.levelDotText}>{level.label}</Text>
          </TouchableOpacity>
        ))}
      </View>
    );
  };

  const handleClose = () => {
    if (onClose) {
      onClose();
    }
  };

  return (
    <Modal visible={visible} animationType="slide" onRequestClose={handleClose}>
      <SafeAreaView style={styles.container}>
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity onPress={handleClose} style={styles.closeButton}>
            <Ionicons name="close" size={24} color={COLORS.textPrimary} />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>🎯 Dasha Browser</Text>
          <View style={styles.placeholder} />
        </View>

        {/* Date Navigator */}
        <View style={styles.dateNavigator}>
          <TouchableOpacity onPress={() => handleDateChange(-1)} style={styles.navButton}>
            <Ionicons name="chevron-back" size={20} color={COLORS.accent} />
          </TouchableOpacity>
          
          <View style={styles.dateDisplay}>
            <Text style={styles.dateText}>{formatDate(transitDate)}</Text>
            <TouchableOpacity onPress={resetToToday} style={styles.todayButton}>
              <Text style={styles.todayText}>Today</Text>
            </TouchableOpacity>
          </View>
          
          <TouchableOpacity onPress={() => handleDateChange(1)} style={styles.navButton}>
            <Ionicons name="chevron-forward" size={20} color={COLORS.accent} />
          </TouchableOpacity>
        </View>

        {/* Breadcrumb */}
        {renderBreadcrumb()}

        {/* Main Content */}
        <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
          {loading ? (
            <View style={styles.loadingContainer}>
              <Text style={styles.loadingText}>Loading dasha data...</Text>
            </View>
          ) : cascadingData && cascadingData.maha_dashas?.length === 0 ? (
            <View style={styles.loadingContainer}>
              <Text style={styles.errorText}>⚠️ No dasha data available</Text>
              <Text style={styles.errorSubText}>The backend calculation returned empty results. Please check birth data.</Text>
            </View>
          ) : (
            <>
              {renderMainCard()}
              
              {/* Level Navigation */}
              <View style={styles.levelSection}>
                <Text style={styles.sectionTitle}>Dasha Levels</Text>
                {renderLevelDots()}
              </View>

              {/* Action Buttons */}
              <View style={styles.actionButtons}>
                <TouchableOpacity style={styles.actionButton}>
                  <Ionicons name="calendar" size={20} color={COLORS.accent} />
                  <Text style={styles.actionButtonText}>Calendar</Text>
                </TouchableOpacity>
                
                <TouchableOpacity style={styles.actionButton}>
                  <Ionicons name="analytics" size={20} color={COLORS.accent} />
                  <Text style={styles.actionButtonText}>Effects</Text>
                </TouchableOpacity>
                
                <TouchableOpacity style={styles.actionButton}>
                  <Ionicons name="search" size={20} color={COLORS.accent} />
                  <Text style={styles.actionButtonText}>Find</Text>
                </TouchableOpacity>
              </View>
            </>
          )}
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
    padding: 12,
    borderRadius: 8,
    backgroundColor: COLORS.lightGray,
    minWidth: 40,
    minHeight: 40,
    justifyContent: 'center',
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: COLORS.textPrimary,
  },
  placeholder: {
    width: 40,
  },
  dateNavigator: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 16,
    backgroundColor: COLORS.surface,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  navButton: {
    padding: 12,
    borderRadius: 8,
    backgroundColor: COLORS.lightGray,
  },
  dateDisplay: {
    alignItems: 'center',
  },
  dateText: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.textPrimary,
    marginBottom: 4,
  },
  todayButton: {
    paddingHorizontal: 12,
    paddingVertical: 4,
    backgroundColor: COLORS.accent,
    borderRadius: 12,
  },
  todayText: {
    color: COLORS.white,
    fontSize: 12,
    fontWeight: '600',
  },
  breadcrumb: {
    padding: 16,
    backgroundColor: COLORS.lightGray,
  },
  breadcrumbText: {
    fontSize: 14,
    color: COLORS.textSecondary,
    textAlign: 'center',
  },
  content: {
    flex: 1,
    padding: 16,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    fontSize: 16,
    color: COLORS.textSecondary,
  },
  errorText: {
    fontSize: 18,
    color: COLORS.error,
    textAlign: 'center',
    marginBottom: 8,
  },
  errorSubText: {
    fontSize: 14,
    color: COLORS.textSecondary,
    textAlign: 'center',
    lineHeight: 20,
  },
  mainCard: {
    backgroundColor: COLORS.surface,
    borderRadius: 16,
    padding: 20,
    marginBottom: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 4,
  },
  cardTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: COLORS.accent,
    textAlign: 'center',
    marginBottom: 8,
  },
  cardSubtitle: {
    fontSize: 14,
    fontWeight: '500',
    color: COLORS.textSecondary,
    textAlign: 'center',
    marginBottom: 12,
  },
  cardDates: {
    fontSize: 14,
    color: COLORS.textSecondary,
    textAlign: 'center',
    marginBottom: 16,
  },
  progressContainer: {
    marginBottom: 16,
  },
  progressBar: {
    height: 8,
    backgroundColor: COLORS.lightGray,
    borderRadius: 4,
    overflow: 'hidden',
    marginBottom: 8,
  },
  progressFill: {
    height: '100%',
    backgroundColor: COLORS.accent,
  },
  progressText: {
    fontSize: 12,
    color: COLORS.textSecondary,
    textAlign: 'center',
  },
  cardEffects: {
    fontSize: 14,
    color: COLORS.textPrimary,
    textAlign: 'center',
    lineHeight: 20,
  },
  levelSection: {
    marginBottom: 20,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.textPrimary,
    marginBottom: 12,
    textAlign: 'center',
  },
  levelDots: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 12,
  },
  levelDot: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: COLORS.accent,
    justifyContent: 'center',
    alignItems: 'center',
  },
  levelDotText: {
    color: COLORS.white,
    fontSize: 14,
    fontWeight: '600',
  },
  actionButtons: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginTop: 20,
  },
  actionButton: {
    alignItems: 'center',
    padding: 16,
    borderRadius: 12,
    backgroundColor: COLORS.surface,
    minWidth: 80,
  },
  actionButtonText: {
    fontSize: 12,
    color: COLORS.accent,
    marginTop: 4,
    fontWeight: '600',
  },
});

export default DashaBrowser;