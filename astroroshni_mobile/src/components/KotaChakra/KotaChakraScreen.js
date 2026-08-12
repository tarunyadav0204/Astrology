import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  StatusBar,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { SafeAreaView } from 'react-native-safe-area-context';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useTheme } from '../../context/ThemeContext';
import DateNavigator from '../Common/DateNavigator';
import FortressWheel from './FortressWheel';
import FortressTable from './FortressTable';
import PeriodsModal from './PeriodsModal';
import PlanetDetailsModal from './PlanetDetailsModal';
import KotaChakraInfoModal from './KotaChakraInfoModal';
import { API_BASE_URL, getEndpoint } from '../../utils/constants';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { typographyTokens } from '../../theme/tokens';
import AppAlertModal from '../Common/AppAlertModal';

const KotaChakraScreen = ({ route, navigation }) => {
  const { birthChartId } = route.params || {};
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
  const [appAlert, setAppAlert] = useState(null);

  const showError = (message) => setAppAlert({ title: 'Unable to continue', message, variant: 'error' });

  useEffect(() => {
    if (!birthChartId) {
      navigation.replace('BirthProfileIntro', { returnTo: 'KotaChakra' });
      return;
    }
  }, [birthChartId, navigation]);

  useEffect(() => {
    if (birthChartId) fetchKotaChakra();
  }, [selectedDate, birthChartId]);

  const fetchKotaChakra = async () => {
    try {
      setLoading(true);

      if (!birthChartId) {
        showError('A saved birth chart is required.');
        return;
      }

      const token = await AsyncStorage.getItem('authToken');
      if (!token) {
        setAppAlert({
          title: 'Sign in required',
          message: 'Kota Chakra needs a saved account chart. You can keep exploring free tools on Home.',
          variant: 'info',
          primaryText: 'Sign in',
          secondaryText: 'Stay',
          onPrimary: () => {
            const { replaceWithLogin } = require('../../navigation/replaceWithLogin');
            replaceWithLogin(navigation);
          },
        });
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
        showError(data.error || 'Failed to calculate Kota Chakra.');
      }
    } catch (error) {
      console.error('Kota Chakra fetch error:', error);
      showError(error.message || 'A network error occurred.');
    } finally {
      setLoading(false);
    }
  };

  const fetchPlanetDetails = async (planetName) => {
    try {
      const token = await AsyncStorage.getItem('authToken');
      if (!token) {
        showError('Please sign in to view planet details.');
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
        showError(data.error || 'Failed to fetch planet details.');
      }
    } catch (error) {
      console.error('Planet details fetch error:', error);
      showError(error.message || 'A network error occurred.');
    }
  };

  const fetchPeriods = async (type) => {
    try {
      if (!birthChartId) {
        showError('A saved birth chart is required.');
        return;
      }

      const token = await AsyncStorage.getItem('authToken');
      if (!token) {
        showError('Please sign in to view Kota Chakra periods.');
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
        showError(data.error || 'Failed to fetch periods.');
      }
    } catch (error) {
      console.error('Periods fetch error:', error);
      showError(error.message || 'A network error occurred.');
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
      <LinearGradient colors={[colors.background, colors.backgroundSecondary]} style={styles.container}>
        <StatusBar barStyle="light-content" backgroundColor={colors.headerSurface} translucent={false} />
        <View style={styles.loadingContainer}>
          <View style={[styles.loadingMark, { backgroundColor: colors.cosmicSurface, borderColor: colors.cosmicLine }]}>
            <Ionicons name="shield-half-outline" size={32} color={colors.accent} />
          </View>
          <ActivityIndicator size="small" color={colors.primary} />
          <Text style={[styles.loadingText, { color: colors.text }]}>
            Mapping the fortress…
          </Text>
        </View>
      </LinearGradient>
    );
  }

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      <StatusBar barStyle="light-content" backgroundColor={colors.headerSurface} translucent={false} />
      <LinearGradient colors={[colors.background, colors.backgroundSecondary, colors.background]} style={styles.container}>
        <SafeAreaView edges={['top']} style={{ backgroundColor: colors.headerSurface }}>
          <View style={[styles.header, { backgroundColor: colors.headerSurface, borderBottomColor: colors.cosmicLine }]}>
            <TouchableOpacity
              style={[styles.headerButton, { backgroundColor: colors.cosmicRaised, borderColor: colors.cosmicLine }]}
              onPress={() => navigation.goBack()}
              accessibilityLabel="Go back"
            >
              <Ionicons name="arrow-back" size={22} color={colors.textInverse} />
            </TouchableOpacity>
            <View style={styles.titleContainer}>
              <Text style={[styles.headerEyebrow, { color: colors.accent }]}>FORTRESS TIMING</Text>
              <Text style={[styles.title, { color: colors.textInverse }]}>Kota Chakra</Text>
            </View>
            <TouchableOpacity
              style={[styles.headerButton, { backgroundColor: colors.cosmicRaised, borderColor: colors.cosmicLine }]}
              onPress={() => setShowInfoModal(true)}
              accessibilityLabel="About Kota Chakra"
            >
              <Ionicons name="information-outline" size={22} color={colors.textInverse} />
            </TouchableOpacity>
          </View>
        </SafeAreaView>

        <SafeAreaView edges={['bottom']} style={styles.safeArea}>
          <ScrollView style={styles.scrollView} contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
            <View style={[styles.heroCard, { backgroundColor: colors.cosmicSurface, borderColor: colors.cosmicLine }]}>
              <View style={[styles.heroOrbit, styles.heroOrbitLarge, { borderColor: colors.cosmicLine }]} />
              <View style={[styles.heroOrbit, styles.heroOrbitSmall, { borderColor: colors.cosmicLine }]} />
              <Text style={[styles.heroEyebrow, { color: colors.accent }]}>YOUR CELESTIAL FORTRESS</Text>
              <Text style={[styles.heroTitle, { color: colors.textInverse }]}>Protection around your natal Moon.</Text>
              <Text style={[styles.heroCopy, { color: colors.textInverseMuted }]}>See where transiting planets guard, pressure or cross the four defensive zones.</Text>
            </View>

            <DateNavigator date={selectedDate} onDateChange={setSelectedDate} />

            {kotaData && (
              <View style={[styles.statusCard, { backgroundColor: colors.surfaceRaised, borderColor: colors.cardBorder }]}>
                <View style={styles.statusHeader}>
                  <View>
                    <Text style={[styles.cardEyebrow, { color: colors.primary }]}>FORTRESS STATUS</Text>
                    <Text style={[styles.janmaNakshatra, { color: colors.text }]}>{kotaData.janma_nakshatra}</Text>
                    <Text style={[styles.janmaLabel, { color: colors.textSecondary }]}>Janma nakshatra</Text>
                  </View>
                  <View style={[styles.statusBadge, { backgroundColor: colors.surfaceMuted, borderColor: colors.cardBorder }]}>
                    <Text style={styles.statusIcon}>{getStatusIcon(kotaData.protection_score?.status)}</Text>
                    <Text style={[styles.statusText, { color: getStatusColor(kotaData.protection_score?.status) }]}>
                      {kotaData.protection_score?.status || 'Unknown'}
                    </Text>
                  </View>
                </View>

                <View style={styles.protectionMeter}>
                  <View style={styles.meterHeading}>
                    <Text style={[styles.meterLabel, { color: colors.textSecondary }]}>Protection score</Text>
                    <Text style={[styles.meterValue, { color: colors.text }]}>{Math.max(0, 10 - (kotaData.protection_score?.vulnerability_score || 0))}/10</Text>
                  </View>
                  <View style={[styles.meterBar, { backgroundColor: colors.surfaceMuted }]}>
                    <View style={[styles.meterFill, {
                      width: `${Math.max(0, 100 - (kotaData.protection_score?.vulnerability_score || 0) * 10)}%`,
                      backgroundColor: getStatusColor(kotaData.protection_score?.status),
                    }]} />
                  </View>
                </View>

                <View style={styles.guardianInfo}>
                  <View style={[styles.guardianCard, { backgroundColor: colors.selectionSurface, borderColor: colors.selectionBorder }]}>
                    <Ionicons name="shield-outline" size={18} color={colors.selectionText} />
                    <Text style={[styles.guardianLabel, { color: colors.selectionTextMuted }]}>Kota Swami</Text>
                    <Text style={[styles.guardianName, { color: colors.selectionText }]}>{kotaData.kota_swami}</Text>
                    <Text style={[styles.guardianState, { color: colors.selectionTextMuted }]}>{kotaData.protection_score?.kota_swami_strong ? 'Strong' : 'Weak'}</Text>
                  </View>
                  <View style={[styles.guardianCard, { backgroundColor: colors.surfaceMuted, borderColor: colors.cardBorder }]}>
                    <Ionicons name="eye-outline" size={18} color={colors.primary} />
                    <Text style={[styles.guardianLabel, { color: colors.textSecondary }]}>Kota Paala</Text>
                    <Text style={[styles.guardianName, { color: colors.text }]}>{kotaData.kota_paala}</Text>
                    <Text style={[styles.guardianState, { color: colors.textSecondary }]}>{kotaData.protection_score?.kota_paala_guarding ? 'Guarding' : 'Away'}</Text>
                  </View>
                </View>
              </View>
            )}

            {kotaData && <FortressWheel kotaData={kotaData} colors={colors} onPlanetPress={fetchPlanetDetails} />}

            {kotaData && <FortressTable kotaData={kotaData} colors={colors} />}

            <View style={styles.actionButtons}>
              <TouchableOpacity style={[styles.actionButton, { backgroundColor: colors.surfaceRaised, borderColor: colors.success }]} onPress={() => fetchPeriods('good')}>
                <Ionicons name="shield-checkmark-outline" size={19} color={colors.success} />
                <Text style={[styles.actionButtonText, { color: colors.text }]}>Protected periods</Text>
              </TouchableOpacity>
              <TouchableOpacity style={[styles.actionButton, { backgroundColor: colors.surfaceRaised, borderColor: colors.error }]} onPress={() => fetchPeriods('vulnerable')}>
                <Ionicons name="warning-outline" size={19} color={colors.error} />
                <Text style={[styles.actionButtonText, { color: colors.text }]}>Vulnerable periods</Text>
              </TouchableOpacity>
            </View>

            {kotaData?.interpretation && (
              <View style={[styles.interpretationCard, { backgroundColor: colors.cosmicSurface, borderColor: colors.cosmicLine }]}>
                <Text style={[styles.interpretationEyebrow, { color: colors.accent }]}>CURRENT READING</Text>
                <Text style={[styles.interpretationTitle, { color: colors.textInverse }]}>How to read this moment</Text>
                <Text style={[styles.interpretationText, { color: colors.textInverseMuted }]}>{kotaData.interpretation}</Text>
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

      <AppAlertModal
        visible={Boolean(appAlert)}
        title={appAlert?.title || ''}
        message={appAlert?.message || ''}
        variant={appAlert?.variant || 'error'}
        primaryText={appAlert?.primaryText || 'OK'}
        secondaryText={appAlert?.secondaryText}
        onPrimaryPress={() => {
          const action = appAlert?.onPrimary;
          setAppAlert(null);
          action?.();
        }}
        onSecondaryPress={() => setAppAlert(null)}
        onRequestClose={() => setAppAlert(null)}
      />
      </LinearGradient>
    </View>
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
  },
  scrollContent: {
    paddingHorizontal: 14,
    paddingTop: 14,
    paddingBottom: 28,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 12,
    fontSize: 16,
    fontWeight: '600',
  },
  loadingMark: {
    width: 68,
    height: 68,
    borderRadius: 34,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 11,
    minHeight: 74,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  headerButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  titleContainer: {
    flex: 1,
    alignItems: 'center',
    paddingHorizontal: 8,
  },
  title: {
    ...typographyTokens.display,
    fontSize: 25,
    lineHeight: 28,
  },
  headerEyebrow: {
    ...typographyTokens.eyebrow,
    fontSize: 9,
    letterSpacing: 1.5,
    marginBottom: 2,
  },
  heroCard: {
    minHeight: 166,
    borderWidth: 1,
    borderRadius: 24,
    paddingHorizontal: 20,
    paddingVertical: 20,
    overflow: 'hidden',
  },
  heroEyebrow: {
    ...typographyTokens.eyebrow,
    marginBottom: 9,
  },
  heroTitle: {
    ...typographyTokens.display,
    fontSize: 29,
    lineHeight: 34,
    maxWidth: '80%',
    marginBottom: 8,
  },
  heroCopy: {
    fontSize: 14,
    lineHeight: 20,
    fontWeight: '500',
    maxWidth: '86%',
  },
  heroOrbit: {
    position: 'absolute',
    borderWidth: 1,
    borderRadius: 999,
  },
  heroOrbitLarge: {
    width: 150,
    height: 150,
    right: -52,
    top: -42,
  },
  heroOrbitSmall: {
    width: 92,
    height: 92,
    right: -12,
    top: -16,
  },
  statusCard: {
    borderRadius: 22,
    padding: 16,
    marginBottom: 14,
    borderWidth: 1,
  },
  statusHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 18,
  },
  cardEyebrow: {
    ...typographyTokens.eyebrow,
    marginBottom: 5,
  },
  janmaNakshatra: {
    ...typographyTokens.display,
    fontSize: 23,
    lineHeight: 27,
  },
  janmaLabel: {
    fontSize: 12,
    fontWeight: '500',
    marginTop: 2,
  },
  statusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    paddingHorizontal: 10,
    paddingVertical: 7,
    borderRadius: 999,
    borderWidth: 1,
  },
  statusIcon: {
    fontSize: 16,
  },
  statusText: {
    fontSize: 14,
    fontWeight: '700',
  },
  protectionMeter: {
    marginBottom: 18,
  },
  meterHeading: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  meterLabel: {
    fontSize: 12,
    fontWeight: '600',
  },
  meterBar: {
    height: 8,
    borderRadius: 4,
    overflow: 'hidden',
  },
  meterFill: {
    height: '100%',
    borderRadius: 4,
  },
  meterValue: {
    fontSize: 12,
    fontWeight: '700',
  },
  guardianInfo: {
    flexDirection: 'row',
    gap: 10,
  },
  guardianCard: {
    flex: 1,
    minWidth: 0,
    borderWidth: 1,
    borderRadius: 16,
    padding: 12,
  },
  guardianLabel: {
    fontSize: 10,
    textTransform: 'uppercase',
    letterSpacing: 0.8,
    fontWeight: '700',
    marginTop: 8,
  },
  guardianName: {
    fontSize: 16,
    fontWeight: '700',
    marginTop: 3,
  },
  guardianState: {
    fontSize: 12,
    marginTop: 2,
  },
  actionButtons: {
    flexDirection: 'row',
    gap: 12,
    marginVertical: 14,
  },
  actionButton: {
    flex: 1,
    minHeight: 68,
    paddingHorizontal: 10,
    paddingVertical: 11,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    gap: 6,
  },
  actionButtonText: {
    fontSize: 12,
    fontWeight: '700',
    textAlign: 'center',
  },
  interpretationCard: {
    borderRadius: 22,
    padding: 18,
    borderWidth: 1,
  },
  interpretationEyebrow: {
    ...typographyTokens.eyebrow,
    marginBottom: 7,
  },
  interpretationTitle: {
    ...typographyTokens.sectionTitle,
    marginBottom: 9,
  },
  interpretationText: {
    fontSize: 14,
    lineHeight: 21,
    fontWeight: '500',
  },
});

export default KotaChakraScreen;
