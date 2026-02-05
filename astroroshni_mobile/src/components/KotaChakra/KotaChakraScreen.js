import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTheme } from '../../context/ThemeContext';
import DateNavigator from '../Common/DateNavigator';
import FortressWheel from './FortressWheel';
import FortressTable from './FortressTable';
import PeriodsModal from './PeriodsModal';
import PlanetDetailsModal from './PlanetDetailsModal';
import KotaChakraInfoModal from './KotaChakraInfoModal';
import { API_BASE_URL, getEndpoint } from '../../utils/constants';
import AsyncStorage from '@react-native-async-storage/async-storage';

const KotaChakraScreen = ({ route, navigation }) => {
  const { birthChartId } = route.params;
  const { colors } = useTheme();
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [kotaData, setKotaData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showPeriodsModal, setShowPeriodsModal] = useState(false);
  const [periodsType, setPeriodsType] = useState('good');
  const [periodsData, setPeriodsData] = useState({ good_periods: [], vulnerable_periods: [] });
  const [showPlanetModal, setShowPlanetModal] = useState(false);
  const [planetDetails, setPlanetDetails] = useState(null);
  const [showInfoModal, setShowInfoModal] = useState(false);

  useEffect(() => {
    fetchKotaChakra();
  }, [selectedDate]);

  const fetchKotaChakra = async () => {
    try {
      setLoading(true);
      
      if (!birthChartId) {
        Alert.alert('Error', 'Birth chart ID is required');
        return;
      }
      
      const token = await AsyncStorage.getItem('authToken');
      if (!token) {
        Alert.alert('Error', 'Authentication required');
        navigation.navigate('Login');
        return;
      }
      
      const url = `${API_BASE_URL}${getEndpoint('/kota-chakra/calculate')}`;
      console.log('🏰 Fetching Kota Chakra from:', url);
      console.log('🏰 Birth Chart ID:', birthChartId);
      console.log('🏰 Date:', selectedDate.toISOString().split('T')[0]);
      
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          birth_chart_id: birthChartId,
          date: selectedDate.toISOString().split('T')[0]
        })
      });

      console.log('🏰 Response status:', response.status);
      console.log('🏰 Response ok:', response.ok);

      if (!response.ok) {
        const errorText = await response.text();
        console.log('🏰 Error response:', errorText);
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      console.log('🏰 Response data:', data);
      
      if (data.success) {
        setKotaData(data.kota_chakra);
      } else {
        Alert.alert('Error', data.error || 'Failed to calculate Kota Chakra');
      }
    } catch (error) {
      console.error('Kota Chakra fetch error:', error);
      Alert.alert('Error', error.message || 'Network error occurred');
    } finally {
      setLoading(false);
    }
  };

  const fetchPlanetDetails = async (planetName) => {
    try {
      const token = await AsyncStorage.getItem('authToken');
      if (!token) {
        Alert.alert('Error', 'Authentication required');
        return;
      }
      
      const response = await fetch(`${API_BASE_URL}${getEndpoint('/kota-chakra/planet-details')}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          birth_chart_id: birthChartId,
          planet: planetName,
          date: selectedDate.toISOString().split('T')[0]
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      
      console.log('Planet details response:', data);
      
      if (data.success) {
        console.log('Planet details data:', data.planet_details);
        setPlanetDetails(data.planet_details);
        setShowPlanetModal(true);
      } else {
        console.log('Planet details error:', data.error);
        Alert.alert('Error', data.error || 'Failed to fetch planet details');
      }
    } catch (error) {
      console.error('Planet details fetch error:', error);
      Alert.alert('Error', error.message || 'Network error occurred');
    }
  };

  const fetchPeriods = async (type) => {
    try {
      if (!birthChartId) {
        Alert.alert('Error', 'Birth chart ID is required');
        return;
      }
      
      const token = await AsyncStorage.getItem('authToken');
      if (!token) {
        Alert.alert('Error', 'Authentication required');
        return;
      }
      
      const response = await fetch(`${API_BASE_URL}${getEndpoint('/kota-chakra/periods')}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          birth_chart_id: birthChartId,
          date: selectedDate.toISOString().split('T')[0]
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      
      console.log('📊 Periods API Response:', JSON.stringify(data, null, 2));
      console.log('📊 Good Periods:', data.good_periods);
      console.log('📊 Vulnerable Periods:', data.vulnerable_periods);
      
      if (data.success) {
        setPeriodsData(data);
        setPeriodsType(type);
        setShowPeriodsModal(true);
      } else {
        Alert.alert('Error', data.error || 'Failed to fetch periods');
      }
    } catch (error) {
      console.error('Periods fetch error:', error);
      Alert.alert('Error', error.message || 'Network error occurred');
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'High Vulnerability': return colors.error;
      case 'Moderate Caution': return colors.warning;
      case 'Protected': return colors.success;
      default: return colors.textSecondary;
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'High Vulnerability': return '🚨';
      case 'Moderate Caution': return '⚠️';
      case 'Protected': return '🛡️';
      default: return '🔮';
    }
  };

  if (loading) {
    return (
      <LinearGradient colors={[colors.gradientStart, colors.gradientEnd]} style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={colors.primary} />
          <Text style={[styles.loadingText, { color: colors.text }]}>
            Calculating Fortress...
          </Text>
        </View>
      </LinearGradient>
    );
  }

  return (
    <LinearGradient colors={[colors.gradientStart, colors.gradientEnd]} style={styles.container}>
      <SafeAreaView style={styles.safeArea}>
        <ScrollView style={styles.scrollView} showsVerticalScrollIndicator={false}>
        {/* Header with Back Button */}
        <View style={styles.header}>
          <TouchableOpacity 
            style={styles.backButton}
            onPress={() => navigation.goBack()}
          >
            <Text style={[styles.backButtonText, { color: colors.text }]}>←</Text>
          </TouchableOpacity>
          <View style={styles.titleContainer}>
            <Text style={[styles.title, { color: colors.text }]}>🏰 Kota Chakra</Text>
            <TouchableOpacity 
              style={styles.infoButton}
              onPress={() => setShowInfoModal(true)}
            >
              <Text style={[styles.infoButtonText, { color: colors.primary }]}>ⓘ</Text>
            </TouchableOpacity>
          </View>
          <Text style={[styles.subtitle, { color: colors.textSecondary }]}>
            Fortress Protection Analysis
          </Text>
        </View>

        {/* Date Navigation */}
        <DateNavigator
          date={selectedDate}
          onDateChange={setSelectedDate}
          cosmicTheme={true}
        />

        {/* Status Card */}
        {kotaData && (
          <View style={[styles.statusCard, { backgroundColor: colors.cardBackground, borderColor: colors.cardBorder }]}>
            <View style={styles.statusHeader}>
              <Text style={[styles.janmaNakshatra, { color: colors.text }]}>
                🌙 Janma: {kotaData.janma_nakshatra}
              </Text>
              <View style={styles.statusBadge}>
                <Text style={styles.statusIcon}>
                  {getStatusIcon(kotaData.protection_score?.status)}
                </Text>
                <Text style={[styles.statusText, { color: getStatusColor(kotaData.protection_score?.status) }]}>
                  {kotaData.protection_score?.status || 'Unknown'}
                </Text>
              </View>
            </View>
            
            <View style={styles.protectionMeter}>
              <Text style={[styles.meterLabel, { color: colors.textSecondary }]}>
                Protection Score
              </Text>
              <View style={styles.meterBar}>
                <View 
                  style={[
                    styles.meterFill, 
                    { 
                      width: `${Math.max(0, 100 - (kotaData.protection_score?.vulnerability_score || 0) * 10)}%`,
                      backgroundColor: getStatusColor(kotaData.protection_score?.status)
                    }
                  ]} 
                />
              </View>
              <Text style={[styles.meterValue, { color: colors.text }]}>
                {Math.max(0, 10 - (kotaData.protection_score?.vulnerability_score || 0))}/10
              </Text>
            </View>

            <View style={styles.guardianInfo}>
              <Text style={[styles.guardianText, { color: colors.textSecondary }]}>
                🛡️ Kota Swami: {kotaData.kota_swami} 
                {kotaData.protection_score?.kota_swami_strong ? ' (Strong)' : ' (Weak)'}
              </Text>
              <Text style={[styles.guardianText, { color: colors.textSecondary }]}>
                👮 Kota Paala: {kotaData.kota_paala}
                {kotaData.protection_score?.kota_paala_guarding ? ' (Guarding)' : ' (Away)'}
              </Text>
            </View>
          </View>
        )}

        {/* Fortress Wheel */}
        {kotaData && (
          <FortressWheel 
            kotaData={kotaData}
            colors={colors}
            onPlanetPress={fetchPlanetDetails}
          />
        )}

        {/* Fortress Table */}
        {kotaData && (
          <FortressTable 
            kotaData={kotaData}
            colors={colors}
          />
        )}

        {/* Action Buttons */}
        <View style={styles.actionButtons}>
          <TouchableOpacity
            style={[styles.actionButton, styles.goodButton, { backgroundColor: colors.success }]}
            onPress={() => fetchPeriods('good')}
          >
            <Text style={styles.actionButtonText}>🟢 Good Periods</Text>
          </TouchableOpacity>
          
          <TouchableOpacity
            style={[styles.actionButton, styles.vulnerableButton, { backgroundColor: colors.error }]}
            onPress={() => fetchPeriods('vulnerable')}
          >
            <Text style={styles.actionButtonText}>🔴 Vulnerable</Text>
          </TouchableOpacity>
        </View>

        {/* Interpretation */}
        {kotaData?.interpretation && (
          <View style={[styles.interpretationCard, { backgroundColor: colors.cardBackground, borderColor: colors.cardBorder }]}>
            <Text style={[styles.interpretationTitle, { color: colors.text }]}>
              📜 Current Analysis
            </Text>
            <Text style={[styles.interpretationText, { color: colors.textSecondary }]}>
              {kotaData.interpretation}
            </Text>
          </View>
        )}
      </ScrollView>
      </SafeAreaView>

      <PeriodsModal
        visible={showPeriodsModal}
        onClose={() => setShowPeriodsModal(false)}
        type={periodsType}
        data={periodsData}
        colors={colors}
      />

      <PlanetDetailsModal
        visible={showPlanetModal}
        onClose={() => setShowPlanetModal(false)}
        planetDetails={planetDetails}
        colors={colors}
      />

      <KotaChakraInfoModal
        visible={showInfoModal}
        onClose={() => setShowInfoModal(false)}
        colors={colors}
      />
    </LinearGradient>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  safeArea: {
    flex: 1,
  },
  scrollView: {
    flex: 1,
    paddingHorizontal: 16,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    fontWeight: '600',
  },
  header: {
    alignItems: 'center',
    paddingVertical: 20,
    position: 'relative',
  },
  backButton: {
    position: 'absolute',
    left: 0,
    top: 20,
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 8,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
  },
  backButtonText: {
    fontSize: 16,
    fontWeight: '600',
  },
  titleContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  infoButton: {
    padding: 4,
  },
  infoButtonText: {
    fontSize: 18,
    fontWeight: '600',
  },
  title: {
    fontSize: 24,
    fontWeight: '700',
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 14,
    fontWeight: '500',
  },
  statusCard: {
    borderRadius: 16,
    padding: 20,
    marginVertical: 16,
    borderWidth: 1,
  },
  statusHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  janmaNakshatra: {
    fontSize: 16,
    fontWeight: '600',
  },
  statusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  statusIcon: {
    fontSize: 16,
  },
  statusText: {
    fontSize: 14,
    fontWeight: '700',
  },
  protectionMeter: {
    marginBottom: 16,
  },
  meterLabel: {
    fontSize: 12,
    marginBottom: 8,
  },
  meterBar: {
    height: 8,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    borderRadius: 4,
    overflow: 'hidden',
  },
  meterFill: {
    height: '100%',
    borderRadius: 4,
  },
  meterValue: {
    fontSize: 12,
    textAlign: 'right',
    marginTop: 4,
  },
  guardianInfo: {
    gap: 4,
  },
  guardianText: {
    fontSize: 12,
  },
  actionButtons: {
    flexDirection: 'row',
    gap: 12,
    marginVertical: 16,
  },
  actionButton: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 12,
    alignItems: 'center',
  },
  actionButtonText: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: '600',
  },
  interpretationCard: {
    borderRadius: 16,
    padding: 16,
    marginBottom: 20,
    borderWidth: 1,
  },
  interpretationTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 8,
  },
  interpretationText: {
    fontSize: 14,
    lineHeight: 20,
  },
});

export default KotaChakraScreen;