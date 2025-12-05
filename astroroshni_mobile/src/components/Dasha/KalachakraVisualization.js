import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Dimensions,
  Modal,
} from 'react-native';
import Svg, { Circle, Path, Text as SvgText, G, Line } from 'react-native-svg';
import { COLORS, API_BASE_URL } from '../../utils/constants';
import AsyncStorage from '@react-native-async-storage/async-storage';

const { width: screenWidth } = Dimensions.get('window');
const wheelSize = Math.min(screenWidth - 40, 300);
const centerX = wheelSize / 2;
const centerY = wheelSize / 2;
const outerRadius = wheelSize / 2 - 20;
const innerRadius = outerRadius - 40;

const KalachakraVisualization = ({ visible, onClose, birthData }) => {
  const [kalachakraData, setKalachakraData] = useState(null);
  const [gatiData, setGatiData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState('wheel'); // 'wheel' or 'timeline'
  const [selectedMaha, setSelectedMaha] = useState(null);
  const [showGatiDetails, setShowGatiDetails] = useState(false);

  useEffect(() => {
    if (visible && birthData) {
      fetchKalachakraData();
      fetchGatiAnalysis();
    }
  }, [visible, birthData]);

  const fetchKalachakraData = async () => {
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
      
      const response = await fetch(`${API_BASE_URL}/api/calculate-kalchakra-dasha`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ birth_data: formattedBirthData })
      });
      
      if (response.ok) {
        const data = await response.json();
        setKalachakraData(data);
        
        // Auto-select current mahadasha
        const currentMaha = data.current_mahadasha || data.mahadashas?.find(period => {
          const startDate = new Date(period.start);
          const endDate = new Date(period.end);
          const now = new Date();
          return now >= startDate && now <= endDate;
        });
        
        if (currentMaha) {
          setSelectedMaha(currentMaha);
        }
      }
    } catch (err) {

    } finally {
      setLoading(false);
    }
  };

  const fetchGatiAnalysis = async () => {
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
      
      const response = await fetch(`${API_BASE_URL}/api/calculate-lifetime-gatis`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ birth_data: formattedBirthData })
      });
      
      if (response.ok) {
        const data = await response.json();
        setGatiData(data);
      }
    } catch (err) {

    }
  };

  const getSignPosition = (signNumber) => {
    // Aries starts at top (12 o'clock), going clockwise
    const angle = ((signNumber - 1) * 30 - 90) * (Math.PI / 180);
    return {
      x: centerX + Math.cos(angle) * (outerRadius + innerRadius) / 2,
      y: centerY + Math.sin(angle) * (outerRadius + innerRadius) / 2,
      angle: angle * (180 / Math.PI)
    };
  };

  const createArcPath = (startAngle, endAngle, radius) => {
    const start = {
      x: centerX + Math.cos(startAngle) * radius,
      y: centerY + Math.sin(startAngle) * radius
    };
    const end = {
      x: centerX + Math.cos(endAngle) * radius,
      y: centerY + Math.sin(endAngle) * radius
    };
    
    const largeArcFlag = endAngle - startAngle <= Math.PI ? "0" : "1";
    
    return `M ${start.x} ${start.y} A ${radius} ${radius} 0 ${largeArcFlag} 1 ${end.x} ${end.y}`;
  };

  const renderZodiacWheel = () => {
    if (!kalachakraData?.wheel_data) return null;

    const signs = [
      'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
      'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'
    ];

    return (
      <View style={styles.wheelContainer}>
        <Svg width={wheelSize} height={wheelSize}>
          {/* Outer circle */}
          <Circle
            cx={centerX}
            cy={centerY}
            r={outerRadius}
            fill="none"
            stroke={COLORS.border}
            strokeWidth="2"
          />
          
          {/* Inner circle */}
          <Circle
            cx={centerX}
            cy={centerY}
            r={innerRadius}
            fill="none"
            stroke={COLORS.border}
            strokeWidth="2"
          />

          {/* Sign divisions */}
          {signs.map((sign, index) => {
            const signNumber = index + 1;
            const startAngle = ((signNumber - 1) * 30 - 90) * (Math.PI / 180);
            const endAngle = (signNumber * 30 - 90) * (Math.PI / 180);
            
            // Check if this sign has active dasha
            const hasActiveDasha = kalachakraData.mahadashas?.some(maha => 
              maha.sign === signNumber && maha.gati_active
            );
            
            const isCurrentSign = selectedMaha?.sign === signNumber;
            
            return (
              <G key={sign}>
                {/* Sign sector */}
                <Path
                  d={`M ${centerX} ${centerY} L ${centerX + Math.cos(startAngle) * outerRadius} ${centerY + Math.sin(startAngle) * outerRadius} A ${outerRadius} ${outerRadius} 0 0 1 ${centerX + Math.cos(endAngle) * outerRadius} ${centerY + Math.sin(endAngle) * outerRadius} Z`}
                  fill={isCurrentSign ? '#9c27b0' : hasActiveDasha ? '#e1bee7' : '#f5f5f5'}
                  stroke={COLORS.border}
                  strokeWidth="1"
                  opacity={0.8}
                />
                
                {/* Sign name */}
                <SvgText
                  x={getSignPosition(signNumber).x}
                  y={getSignPosition(signNumber).y}
                  fontSize="10"
                  fill={isCurrentSign ? COLORS.white : COLORS.textPrimary}
                  textAnchor="middle"
                  fontWeight="600"
                >
                  {sign.slice(0, 3)}
                </SvgText>
                
                {/* Radial lines */}
                <Line
                  x1={centerX + Math.cos(startAngle) * innerRadius}
                  y1={centerY + Math.sin(startAngle) * innerRadius}
                  x2={centerX + Math.cos(startAngle) * outerRadius}
                  y2={centerY + Math.sin(startAngle) * outerRadius}
                  stroke={COLORS.border}
                  strokeWidth="1"
                />
              </G>
            );
          })}

          {/* Center point */}
          <Circle
            cx={centerX}
            cy={centerY}
            r="4"
            fill="#9c27b0"
          />
          
          {/* Deha-Jeeva indicator */}
          {kalachakraData.deha && kalachakraData.jeeva && (
            <G>
              <SvgText
                x={centerX}
                y={centerY - 15}
                fontSize="8"
                fill="#9c27b0"
                textAnchor="middle"
                fontWeight="700"
              >
                {kalachakraData.deha}→{kalachakraData.jeeva}
              </SvgText>
              <SvgText
                x={centerX}
                y={centerY + 25}
                fontSize="7"
                fill={COLORS.textSecondary}
                textAnchor="middle"
              >
                {kalachakraData.direction} • {kalachakraData.cycle_len}y
              </SvgText>
            </G>
          )}
        </Svg>
      </View>
    );
  };

  const renderHeaderPillars = () => {
    if (!kalachakraData) return null;

    return (
      <View style={styles.headerPillars}>
        <View style={styles.pillar}>
          <Text style={styles.pillarLabel}>Deha (Body)</Text>
          <Text style={styles.pillarValue}>{kalachakraData.deha}</Text>
          <Text style={styles.pillarLord}>{kalachakraData.deha_lord}</Text>
        </View>
        
        <View style={styles.pillarCenter}>
          <Text style={styles.pillarCenterText}>Nak {kalachakraData.nakshatra}.{kalachakraData.pada}</Text>
          <Text style={styles.pillarDirection}>{kalachakraData.direction}</Text>
        </View>
        
        <View style={styles.pillar}>
          <Text style={styles.pillarLabel}>Jeeva (Soul)</Text>
          <Text style={styles.pillarValue}>{kalachakraData.jeeva}</Text>
          <Text style={styles.pillarLord}>{kalachakraData.jeeva_lord}</Text>
        </View>
      </View>
    );
  };

  const renderCurrentContext = () => {
    if (!selectedMaha) return null;

    const currentAntar = kalachakraData?.current_antardasha;
    const progress = calculateProgress(selectedMaha.start, selectedMaha.end);

    return (
      <View style={styles.currentContext}>
        <View style={styles.contextRow}>
          <View style={styles.contextItem}>
            <Text style={styles.contextLabel}>Current Maha</Text>
            <Text style={styles.contextValue}>{selectedMaha.name}</Text>
            <Text style={styles.contextGati}>{selectedMaha.gati}</Text>
          </View>
          
          {currentAntar && (
            <View style={styles.contextItem}>
              <Text style={styles.contextLabel}>Current Antar</Text>
              <Text style={styles.contextValue}>{currentAntar.name}</Text>
              <Text style={styles.contextProgress}>{Math.round(calculateProgress(currentAntar.start, currentAntar.end))}%</Text>
            </View>
          )}
          
          <View style={styles.contextItem}>
            <Text style={styles.contextLabel}>Remaining</Text>
            <Text style={styles.contextValue}>{getRemainingTime(selectedMaha.end)}</Text>
            <Text style={styles.contextProgress}>{Math.round(progress)}%</Text>
          </View>
        </View>
        
        <View style={styles.progressBar}>
          <View style={[styles.progressFill, { width: `${progress}%` }]} />
        </View>
      </View>
    );
  };

  const renderViewToggle = () => (
    <View style={styles.viewToggle}>
      <TouchableOpacity
        style={[styles.toggleButton, viewMode === 'wheel' && styles.activeToggle]}
        onPress={() => setViewMode('wheel')}
      >
        <Text style={[styles.toggleText, viewMode === 'wheel' && styles.activeToggleText]}>
          🎯 Wheel
        </Text>
      </TouchableOpacity>
      
      <TouchableOpacity
        style={[styles.toggleButton, viewMode === 'timeline' && styles.activeToggle]}
        onPress={() => setViewMode('timeline')}
      >
        <Text style={[styles.toggleText, viewMode === 'timeline' && styles.activeToggleText]}>
          📊 Timeline
        </Text>
      </TouchableOpacity>
    </View>
  );

  const renderMahadashaChips = () => {
    if (!kalachakraData?.mahadashas) return null;

    return (
      <View style={styles.chipSection}>
        <Text style={styles.sectionTitle}>Mahadashas</Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.chipsContainer}>
          {kalachakraData.mahadashas.map((maha, index) => {
            const isSelected = selectedMaha?.name === maha.name;
            const isCurrent = maha.gati_active;
            
            return (
              <TouchableOpacity
                key={`${maha.name}-${index}`}
                style={[
                  styles.mahaChip,
                  isSelected && styles.selectedChip,
                  isCurrent && styles.currentChip
                ]}
                onPress={() => setSelectedMaha(maha)}
              >
                <Text style={[
                  styles.chipSign,
                  isSelected && styles.selectedChipText,
                  isCurrent && styles.currentChipText
                ]}>
                  {maha.name}
                </Text>
                <Text style={[
                  styles.chipLord,
                  isSelected && styles.selectedChipText,
                  isCurrent && styles.currentChipText
                ]}>
                  {maha.lord}
                </Text>
                <Text style={[
                  styles.chipGati,
                  isSelected && styles.selectedChipText,
                  isCurrent && styles.currentChipText
                ]}>
                  {maha.gati}
                </Text>
                <Text style={[
                  styles.chipDuration,
                  isSelected && styles.selectedChipText,
                  isCurrent && styles.currentChipText
                ]}>
                  {formatPeriodDuration(maha.years)}
                </Text>
              </TouchableOpacity>
            );
          })}
        </ScrollView>
      </View>
    );
  };

  const renderGatiAnalysis = () => {
    if (!gatiData) return null;

    return (
      <View style={styles.gatiSection}>
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Gati Analysis</Text>
          <TouchableOpacity
            style={styles.detailsButton}
            onPress={() => setShowGatiDetails(true)}
          >
            <Text style={styles.detailsButtonText}>Details</Text>
          </TouchableOpacity>
        </View>
        
        <View style={styles.gatiSummary}>
          <View style={styles.gatiStat}>
            <Text style={styles.gatiStatValue}>{gatiData.statistics?.total_transitions || 0}</Text>
            <Text style={styles.gatiStatLabel}>Total Gatis</Text>
          </View>
          
          <View style={styles.gatiStat}>
            <Text style={styles.gatiStatValue}>{gatiData.statistics?.manduka_count || 0}</Text>
            <Text style={styles.gatiStatLabel}>Manduka</Text>
          </View>
          
          <View style={styles.gatiStat}>
            <Text style={styles.gatiStatValue}>{gatiData.statistics?.simhavalokana_count || 0}</Text>
            <Text style={styles.gatiStatLabel}>Simhavalokana</Text>
          </View>
          
          <View style={styles.gatiStat}>
            <Text style={styles.gatiStatValue}>{gatiData.statistics?.markata_count || 0}</Text>
            <Text style={styles.gatiStatLabel}>Markata</Text>
          </View>
        </View>

        {gatiData.gati_transitions?.slice(0, 3).map((transition, index) => (
          <View key={index} style={styles.gatiTransition}>
            <Text style={styles.transitionText}>
              {transition.from_sign} → {transition.to_sign} ({transition.gati_type})
            </Text>
            <Text style={styles.transitionDate}>
              {new Date(transition.date).toLocaleDateString()}
            </Text>
          </View>
        ))}
      </View>
    );
  };

  const renderGatiDetailsModal = () => (
    <Modal visible={showGatiDetails} animationType="slide" transparent>
      <View style={styles.modalOverlay}>
        <View style={styles.gatiModal}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>Lifetime Gati Analysis</Text>
            <TouchableOpacity onPress={() => setShowGatiDetails(false)}>
              <Text style={styles.modalClose}>✕</Text>
            </TouchableOpacity>
          </View>
          
          <ScrollView style={styles.modalContent}>
            {gatiData?.summary && (
              <View style={styles.summarySection}>
                <Text style={styles.summaryTitle}>Summary</Text>
                <Text style={styles.summaryText}>{gatiData.summary}</Text>
              </View>
            )}
            
            {gatiData?.gati_transitions?.map((transition, index) => (
              <View key={index} style={styles.transitionCard}>
                <View style={styles.transitionHeader}>
                  <Text style={styles.transitionTitle}>
                    {transition.from_sign} → {transition.to_sign}
                  </Text>
                  <Text style={styles.transitionType}>{transition.gati_type}</Text>
                </View>
                <Text style={styles.transitionDate}>
                  {new Date(transition.date).toLocaleDateString()}
                </Text>
                {transition.meaning && (
                  <Text style={styles.transitionMeaning}>{transition.meaning}</Text>
                )}
              </View>
            ))}
          </ScrollView>
        </View>
      </View>
    </Modal>
  );

  const calculateProgress = (startDate, endDate, currentDate = new Date()) => {
    const start = new Date(startDate).getTime();
    const end = new Date(endDate).getTime();
    const current = currentDate.getTime();
    
    if (current < start) return 0;
    if (current > end) return 100;
    
    return ((current - start) / (end - start)) * 100;
  };

  const getRemainingTime = (endDate) => {
    const end = new Date(endDate);
    const now = new Date();
    const diffMs = end - now;
    
    if (diffMs <= 0) return 'Completed';
    
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    const diffYears = Math.floor(diffDays / 365);
    const remainingDays = diffDays % 365;
    const diffMonths = Math.floor(remainingDays / 30);
    
    if (diffYears > 0) {
      return `${diffYears}y ${diffMonths}m`;
    } else if (diffMonths > 0) {
      return `${diffMonths}m`;
    } else {
      return `${diffDays}d`;
    }
  };

  const formatPeriodDuration = (years) => {
    if (!years) return '';
    
    const totalDays = years * 365.25;
    const totalMonths = years * 12;
    
    if (totalDays < 90) {
      return `${Math.round(totalDays)}d`;
    } else if (totalMonths < 12) {
      return `${Math.round(totalMonths)}m`;
    } else {
      const wholeYears = Math.floor(years);
      const remainingMonths = Math.round((years - wholeYears) * 12);
      
      if (remainingMonths === 0) {
        return `${wholeYears}y`;
      } else {
        return `${wholeYears}y ${remainingMonths}m`;
      }
    }
  };

  if (loading) {
    return (
      <Modal visible={visible} animationType="slide">
        <View style={styles.container}>
          <View style={styles.header}>
            <TouchableOpacity onPress={onClose} style={styles.closeButton}>
              <Text style={styles.closeIcon}>✕</Text>
            </TouchableOpacity>
            <Text style={styles.headerTitle}>Kalachakra Visualization</Text>
            <View style={styles.placeholder} />
          </View>
          <View style={styles.loadingContainer}>
            <Text style={styles.loadingText}>Loading Kalachakra data...</Text>
          </View>
        </View>
      </Modal>
    );
  }

  return (
    <Modal visible={visible} animationType="slide">
      <View style={styles.container}>
        <View style={styles.header}>
          <TouchableOpacity onPress={onClose} style={styles.closeButton}>
            <Text style={styles.closeIcon}>✕</Text>
          </TouchableOpacity>
          <Text style={styles.headerTitle}>BPHS Kalachakra</Text>
          <View style={styles.placeholder} />
        </View>
        
        {renderHeaderPillars()}
        {renderCurrentContext()}
        {renderViewToggle()}
        
        <ScrollView style={styles.content}>
          {viewMode === 'wheel' ? (
            <>
              {renderZodiacWheel()}
              {renderMahadashaChips()}
            </>
          ) : (
            <>
              {renderMahadashaChips()}
              {renderGatiAnalysis()}
            </>
          )}
        </ScrollView>
        
        {renderGatiDetailsModal()}
      </View>
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
  closeIcon: {
    fontSize: 20,
    color: COLORS.textPrimary,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: COLORS.textPrimary,
  },
  placeholder: {
    width: 40,
  },
  headerPillars: {
    flexDirection: 'row',
    backgroundColor: '#f3e5f5',
    padding: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#e1bee7',
  },
  pillar: {
    flex: 1,
    alignItems: 'center',
  },
  pillarCenter: {
    flex: 1,
    alignItems: 'center',
    borderLeftWidth: 1,
    borderRightWidth: 1,
    borderColor: '#e1bee7',
  },
  pillarLabel: {
    fontSize: 10,
    color: COLORS.textSecondary,
    fontWeight: '600',
  },
  pillarValue: {
    fontSize: 16,
    fontWeight: '700',
    color: '#9c27b0',
    marginTop: 2,
  },
  pillarLord: {
    fontSize: 9,
    color: COLORS.textSecondary,
    marginTop: 1,
  },
  pillarCenterText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#9c27b0',
  },
  pillarDirection: {
    fontSize: 10,
    color: COLORS.textSecondary,
    marginTop: 2,
  },
  currentContext: {
    backgroundColor: COLORS.surface,
    padding: 12,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  contextRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  contextItem: {
    alignItems: 'center',
    flex: 1,
  },
  contextLabel: {
    fontSize: 9,
    color: COLORS.textSecondary,
    fontWeight: '600',
  },
  contextValue: {
    fontSize: 14,
    fontWeight: '700',
    color: COLORS.textPrimary,
    marginTop: 2,
  },
  contextGati: {
    fontSize: 8,
    color: '#9c27b0',
    marginTop: 1,
  },
  contextProgress: {
    fontSize: 8,
    color: '#673ab7',
    fontWeight: '600',
    marginTop: 1,
  },
  progressBar: {
    height: 4,
    backgroundColor: COLORS.lightGray,
    borderRadius: 2,
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#9c27b0',
    borderRadius: 2,
  },
  viewToggle: {
    flexDirection: 'row',
    backgroundColor: COLORS.surface,
    margin: 12,
    borderRadius: 8,
    padding: 4,
  },
  toggleButton: {
    flex: 1,
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 6,
    alignItems: 'center',
  },
  activeToggle: {
    backgroundColor: '#9c27b0',
  },
  toggleText: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.textSecondary,
  },
  activeToggleText: {
    color: COLORS.white,
  },
  content: {
    flex: 1,
    padding: 12,
  },
  wheelContainer: {
    alignItems: 'center',
    marginBottom: 20,
  },
  chipSection: {
    marginBottom: 20,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: COLORS.textPrimary,
    marginBottom: 8,
  },
  chipsContainer: {
    flexDirection: 'row',
  },
  mahaChip: {
    backgroundColor: '#f3e5f5',
    borderRadius: 8,
    padding: 10,
    marginRight: 8,
    minWidth: 80,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#e1bee7',
  },
  selectedChip: {
    backgroundColor: '#9c27b0',
    borderColor: '#9c27b0',
  },
  currentChip: {
    backgroundColor: '#673ab7',
    borderColor: '#673ab7',
  },
  chipSign: {
    fontSize: 12,
    fontWeight: '700',
    color: '#9c27b0',
  },
  chipLord: {
    fontSize: 9,
    color: COLORS.textSecondary,
    marginTop: 1,
  },
  chipGati: {
    fontSize: 8,
    color: '#673ab7',
    fontWeight: '600',
    marginTop: 1,
  },
  chipDuration: {
    fontSize: 9,
    color: COLORS.textPrimary,
    marginTop: 1,
  },
  selectedChipText: {
    color: COLORS.white,
  },
  currentChipText: {
    color: COLORS.white,
  },
  gatiSection: {
    backgroundColor: COLORS.surface,
    borderRadius: 8,
    padding: 12,
    marginBottom: 20,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  detailsButton: {
    backgroundColor: '#9c27b0',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
  },
  detailsButtonText: {
    color: COLORS.white,
    fontSize: 12,
    fontWeight: '600',
  },
  gatiSummary: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  gatiStat: {
    alignItems: 'center',
    flex: 1,
  },
  gatiStatValue: {
    fontSize: 18,
    fontWeight: '700',
    color: '#9c27b0',
  },
  gatiStatLabel: {
    fontSize: 9,
    color: COLORS.textSecondary,
    marginTop: 2,
  },
  gatiTransition: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 4,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  transitionText: {
    fontSize: 12,
    color: COLORS.textPrimary,
    flex: 1,
  },
  transitionDate: {
    fontSize: 10,
    color: COLORS.textSecondary,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  gatiModal: {
    backgroundColor: COLORS.surface,
    borderRadius: 16,
    maxHeight: '80%',
    width: '100%',
    maxWidth: 400,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#9c27b0',
  },
  modalClose: {
    fontSize: 18,
    color: COLORS.textSecondary,
    padding: 4,
  },
  modalContent: {
    padding: 20,
  },
  summarySection: {
    marginBottom: 20,
  },
  summaryTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.textPrimary,
    marginBottom: 8,
  },
  summaryText: {
    fontSize: 14,
    color: COLORS.textSecondary,
    lineHeight: 20,
  },
  transitionCard: {
    backgroundColor: '#f3e5f5',
    borderRadius: 8,
    padding: 12,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#e1bee7',
  },
  transitionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  transitionTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#9c27b0',
  },
  transitionType: {
    fontSize: 10,
    color: '#673ab7',
    fontWeight: '600',
  },
  transitionMeaning: {
    fontSize: 12,
    color: COLORS.textSecondary,
    marginTop: 4,
    lineHeight: 16,
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
});

export default KalachakraVisualization;