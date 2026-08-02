import React, { useState, useEffect } from 'react';
import { useFocusEffect } from '@react-navigation/native';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Alert, ActivityIndicator, Platform, Modal, Share } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { SafeAreaView } from 'react-native-safe-area-context';
import Icon from '@expo/vector-icons/Ionicons';
import DateTimePicker from '@react-native-community/datetimepicker';
import { storage } from '../services/storage';
import { API_BASE_URL, getEndpoint, COLORS } from '../utils/constants';
import LocationPicker from './LocationPicker';
import { useCredits } from '../credits/CreditContext';
import { useAuthGate } from '../auth/AuthGateContext';
import { pricingAPI } from '../services/api';
import WebDatePickerModal from './Common/WebDatePickerModal';
import { useTheme } from '../context/ThemeContext';
import { trackAstrologyEvent } from '../utils/analytics';
import { useTranslation } from 'react-i18next';

const isWeb = Platform.OS === 'web';


export default function ChildbirthPlannerScreen({ navigation }) {
  const { t } = useTranslation();
  const { credits, fetchBalance } = useCredits();
  const { requireAuthForPaid } = useAuthGate();
  const { theme, colors } = useTheme();
  const isDark = theme === 'dark';
  const ui = {
    text: colors.text,
    muted: colors.textSecondary,
    cardBg: isDark ? 'rgba(255,255,255,0.1)' : colors.cardBackground,
    cardBorder: isDark ? 'rgba(255,255,255,0.2)' : colors.cardBorder,
    insetBg: isDark ? 'rgba(0,0,0,0.3)' : colors.backgroundSecondary,
    softBg: isDark ? 'rgba(255,255,255,0.08)' : colors.backgroundSecondary,
  };
  const [loading, setLoading] = useState(false);
  const [motherProfile, setMotherProfile] = useState(null);
  
  // Date state
  const [startDate, setStartDate] = useState(new Date());
  const [endDate, setEndDate] = useState(new Date(new Date().setDate(new Date().getDate() + 30)));
  const [showStartPicker, setShowStartPicker] = useState(false);
  const [showEndPicker, setShowEndPicker] = useState(false);
  
  // Location state
  const [deliveryLocation, setDeliveryLocation] = useState(null);
  const [showLocationPicker, setShowLocationPicker] = useState(false);
  
  // Results
  const [results, setResults] = useState(null);
  
  // Credits
  const [creditInfo, setCreditInfo] = useState({ cost: 0, current_credits: 0, can_afford: false });

  useEffect(() => {
    loadProfile();
    loadCreditInfo();
  }, []);

  useFocusEffect(
    React.useCallback(() => {
      fetchBalance();
      loadCreditInfo();
    }, [])
  );

  useEffect(() => {
    setCreditInfo(prev => ({
      ...prev,
      current_credits: credits,
      can_afford: credits >= prev.cost
    }));
  }, [credits]);

  useEffect(() => {
    const unsubscribe = navigation.addListener('focus', () => {
      // Reload profile when returning from SelectNative
      loadProfile();
    });
    return unsubscribe;
  }, [navigation]);

  const loadProfile = async () => {
    try {
      const data = await storage.getBirthData();
      if (!data?.name) {
        navigation.replace('BirthProfileIntro', { returnTo: 'ChildbirthPlanner' });
        return;
      }
      setMotherProfile(data);
      if (data.latitude && data.longitude) {
        setDeliveryLocation({
          latitude: parseFloat(data.latitude),
          longitude: parseFloat(data.longitude),
          name: data.place || t('muhurat.childbirth.mothersLocation', "Mother's location")
        });
      }
    } catch(e) { 
      console.error(e); 
    }
  };

  const loadCreditInfo = async () => {
    try {
      const response = await pricingAPI.getPricing();
      const data = response?.data || response;
      const cost = data?.pricing?.childbirth != null ? Number(data.pricing.childbirth) : 0;
      setCreditInfo({
        cost,
        current_credits: credits,
        can_afford: credits >= cost
      });
    } catch(e) {
      console.error('Failed to load credit info:', e);
    }
  };

  const calculateDates = async () => {
    if (!motherProfile) {
      Alert.alert(
        t('muhurat.childbirth.missingInfo', 'Missing Information'),
        t('muhurat.childbirth.selectMotherFirst', "Please select mother's chart first.")
      );
      return;
    }
    
    if (!deliveryLocation) {
      Alert.alert(
        t('muhurat.childbirth.missingInfo', 'Missing Information'),
        t('muhurat.childbirth.selectDeliveryFirst', 'Please select delivery location.')
      );
      return;
    }

    const authOk = await requireAuthForPaid({
      feature: 'childbirth planner',
      message: t('muhurat.childbirth.signIn', 'Sign in to run the childbirth muhurat planner.'),
      resume: { resumeRoute: 'ChildbirthPlanner', resumeParams: {} },
    });
    if (!authOk) return;

    const daysDiff = Math.ceil((endDate - startDate) / (1000 * 60 * 60 * 24));
    if (daysDiff > 30) {
      Alert.alert(
        t('muhurat.childbirth.dateRangeLimit', 'Date Range Limit'),
        t('muhurat.childbirth.dateRangeLimitBody', 'Date range cannot exceed 30 days. Please adjust your selection.')
      );
      return;
    }

    if (!creditInfo.can_afford) {
      Alert.alert(
        t('muhurat.common.insufficientCredits', 'Insufficient Credits'),
        t('muhurat.common.needCredits', {
          cost: creditInfo.cost,
          credits: creditInfo.current_credits,
          defaultValue: 'You need {{cost}} credits but have {{credits}}. Please purchase more credits.',
        }),
        [
          { text: t('muhurat.common.cancel', 'Cancel'), style: 'cancel' },
          { text: t('muhurat.common.buyCredits', 'Buy Credits'), onPress: () => navigation.navigate('Credits') },
        ]
      );
      return;
    }

    // Confirmation dialog before deducting credits
    Alert.alert(
      t('muhurat.common.confirmCalculation', 'Confirm Calculation'),
      t('muhurat.common.confirmDeduct', {
        cost: creditInfo.cost,
        defaultValue: 'This will deduct {{cost}} credits from your account. Do you want to proceed?',
      }),
      [
        { text: t('muhurat.common.cancel', 'Cancel'), style: 'cancel' },
        { text: t('muhurat.common.proceed', 'Proceed'), onPress: () => performCalculation() },
      ]
    );
  };

  const performCalculation = async () => {
    try {
      const token = await storage.getAuthToken();
      
      const payload = {
        start_date: (() => {
          const d = startDate;
          return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
        })(),
        end_date: (() => {
          const d = endDate;
          return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
        })(),
        delivery_latitude: parseFloat(deliveryLocation.latitude),
        delivery_longitude: parseFloat(deliveryLocation.longitude),
        
        mother_dob: motherProfile.date,
        mother_time: motherProfile.time,
        mother_lat: parseFloat(motherProfile.latitude),
        mother_lon: parseFloat(motherProfile.longitude)
      };

      const response = await fetch(`${API_BASE_URL}${getEndpoint('/muhurat/childbirth-planner')}`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}` 
        },
        body: JSON.stringify(payload)
      });

      const json = await response.json();
      if (response.status === 402) {
        Alert.alert(
          t('muhurat.common.insufficientCredits', 'Insufficient Credits'),
          json.detail?.message || t('muhurat.childbirth.notEnoughCredits', 'Not enough credits'),
          [
            { text: t('muhurat.common.cancel', 'Cancel'), style: 'cancel' },
            { text: t('muhurat.common.buyCredits', 'Buy Credits'), onPress: () => navigation.navigate('Credits') },
          ]
        );
      } else if (json.status === 'success') {
        setResults(json.data);
        await fetchBalance();
        setCreditInfo(prev => ({
          ...prev,
          current_credits: json.remaining_credits || credits - prev.cost,
          can_afford: (json.remaining_credits || credits - prev.cost) >= prev.cost
        }));
      } else {
        Alert.alert(
          t('muhurat.common.error', 'Error'),
          t('muhurat.childbirth.calculationFailed', 'Calculation failed. Please check inputs.')
        );
      }
    } catch (e) {
      Alert.alert(
        t('muhurat.common.error', 'Error'),
        t('muhurat.common.networkError', 'Network Error')
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      {isDark ? (
        <LinearGradient colors={['#1a0033', '#2d1b4e', '#4a2c6d', '#ff6b35']} style={StyleSheet.absoluteFill} />
      ) : null}
        <SafeAreaView style={styles.safeArea}>
          <ScrollView contentContainerStyle={styles.scroll}>
            
            {/* Header */}
            <View style={styles.header}>
              <TouchableOpacity onPress={() => navigation.goBack()}>
                <Icon name="arrow-back" size={24} color={ui.text} />
              </TouchableOpacity>
              <Text style={[styles.headerTitle, { color: ui.text }]}>{t('muhurat.childbirth.title', 'Childbirth Planner')}</Text>
              <View style={styles.placeholder} />
            </View>

            {/* Credit Info Card */}
            <View style={[styles.creditCard, { backgroundColor: ui.softBg, borderColor: ui.cardBorder, borderWidth: 1 }]}>
              <View style={styles.creditRow}>
                <Text style={[styles.creditLabel, { color: ui.text }]}>
                  💎 {t('muhurat.common.costCredits', { cost: creditInfo.cost, defaultValue: 'Cost: {{cost}} credits' })}
                </Text>
                <Text style={[styles.creditBalance, { color: credits >= creditInfo.cost ? '#00C853' : '#FF5722' }]}>
                  {t('muhurat.common.balance', { credits, defaultValue: 'Balance: {{credits}}' })}
                </Text>
              </View>
              {!creditInfo.can_afford && (
                <TouchableOpacity 
                  style={styles.buyCreditsBtn} 
                  onPress={() => navigation.navigate('Credits')}
                >
                  <Text style={styles.buyCreditsText}>{t('muhurat.common.buyCredits', 'Buy Credits')}</Text>
                </TouchableOpacity>
              )}
            </View>

            {/* Mother Selection Card */}
            <View style={[styles.card, { backgroundColor: ui.cardBg, borderColor: ui.cardBorder, borderWidth: 1 }]}>
              <Text style={[styles.cardTitle, { color: ui.text }]}>👩 {t('muhurat.childbirth.mothersChart', "MOTHER'S CHART")}</Text>
              <TouchableOpacity style={[styles.locationBtn, { backgroundColor: ui.insetBg }]} onPress={() => navigation.navigate('SelectNative', { returnTo: 'ChildbirthPlanner' })}>
                <Icon name="person" size={20} color={ui.text} />
                <Text style={[styles.locationText, { color: ui.text }]}>
                  {motherProfile?.name || t('muhurat.childbirth.selectMother', "Select mother's chart")}
                </Text>
                <Icon name="chevron-forward" size={20} color={ui.muted} />
              </TouchableOpacity>
              <Text style={[styles.hint, { color: ui.muted }]}>{t('muhurat.childbirth.motherRequired', 'Required for nakshatra calculations')}</Text>
            </View>

            {/* Date Selection Card */}
            <View style={[styles.card, { backgroundColor: ui.cardBg, borderColor: ui.cardBorder, borderWidth: 1 }]}>
              <Text style={[styles.cardTitle, { color: ui.text }]}>📅 {t('muhurat.childbirth.selectDateRange', 'SELECT DATE RANGE')}</Text>
              <View style={styles.dateRow}>
                <TouchableOpacity style={[styles.dateBtn, { backgroundColor: ui.insetBg }]} onPress={() => setShowStartPicker(true)}>
                  <Text style={[styles.dateLabel, { color: ui.muted }]}>{t('muhurat.common.from', 'From')}</Text>
                  <Text style={[styles.dateValue, { color: ui.text }]}>{startDate.toLocaleDateString()}</Text>
                </TouchableOpacity>
                <Icon name="arrow-forward" size={20} color={ui.muted} />
                <TouchableOpacity style={[styles.dateBtn, { backgroundColor: ui.insetBg }]} onPress={() => setShowEndPicker(true)}>
                  <Text style={[styles.dateLabel, { color: ui.muted }]}>{t('muhurat.common.to', 'To')}</Text>
                  <Text style={[styles.dateValue, { color: ui.text }]}>{endDate.toLocaleDateString()}</Text>
                </TouchableOpacity>
              </View>
            </View>

            {/* Location Card */}
            <View style={[styles.card, { backgroundColor: ui.cardBg, borderColor: ui.cardBorder, borderWidth: 1 }]}>
              <Text style={[styles.cardTitle, { color: ui.text }]}>🏥 {t('muhurat.childbirth.deliveryLocation', 'DELIVERY LOCATION')}</Text>
              <TouchableOpacity style={[styles.locationBtn, { backgroundColor: ui.insetBg }]} onPress={() => setShowLocationPicker(true)}>
                <Icon name="location" size={20} color={ui.text} />
                <Text style={[styles.locationText, { color: ui.text }]}>
                  {deliveryLocation?.name || t('muhurat.childbirth.selectDeliveryLocation', 'Select delivery location')}
                </Text>
                <Icon name="chevron-forward" size={20} color={ui.muted} />
              </TouchableOpacity>
              <Text style={[styles.hint, { color: ui.muted }]}>
                {motherProfile?.place
                  ? `${t('muhurat.childbirth.defaultMotherLocation', "Default: mother's location").split(':')[0]}: ${motherProfile.place}`
                  : t('muhurat.childbirth.defaultMotherLocation', "Default: mother's location")}
              </Text>
            </View>

            {/* Calculate Button */}
            <TouchableOpacity 
              style={[styles.calcButton, !creditInfo.can_afford && styles.disabledButton]} 
              onPress={calculateDates} 
              disabled={loading || !creditInfo.can_afford}
            >
              {isDark ? (
                <LinearGradient 
                  colors={creditInfo.can_afford ? ['#ff6b35', '#ff8c5a'] : ['#666', '#888']} 
                  style={styles.calcGradient}
                >
                  {loading ? (
                    <ActivityIndicator color={COLORS.white} />
                  ) : (
                    <Text style={styles.calcButtonText}>
                      {creditInfo.can_afford
                        ? t('muhurat.common.findAuspiciousDates', 'Find Auspicious Dates')
                        : t('muhurat.common.insufficientCredits', 'Insufficient Credits')}
                    </Text>
                  )}
                </LinearGradient>
              ) : (
                <View
                  style={[
                    styles.calcGradient,
                    { backgroundColor: creditInfo.can_afford ? colors.primary : colors.backgroundTertiary },
                  ]}
                >
                  {loading ? (
                    <ActivityIndicator color="#fff" />
                  ) : (
                    <Text style={styles.calcButtonText}>
                      {creditInfo.can_afford
                        ? t('muhurat.common.findAuspiciousDates', 'Find Auspicious Dates')
                        : t('muhurat.common.insufficientCredits', 'Insufficient Credits')}
                    </Text>
                  )}
                </View>
              )}
            </TouchableOpacity>

            {/* Results */}
            {results && (
              <View style={styles.resultsContainer}>
                <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 4, gap: 10 }}>
                  <Text style={[styles.resultHeader, { color: ui.text, flex: 1, marginBottom: 0 }]}>✨ {t('muhurat.common.recommendedSlots', 'Recommended Slots')}</Text>
                  <TouchableOpacity
                    onPress={async () => {
                      const days = results.recommendations || [];
                      const shareTitle = t('muhurat.childbirth.shareTitle', 'AstroRoshni — Childbirth Muhurat');
                      const lines = [
                        shareTitle,
                        '',
                        ...days.slice(0, 8).map((day) => `• ${day.date}${day.nakshatra ? ` · ${day.nakshatra}` : ''}`),
                      ];
                      if (!days.length) lines.push(t('muhurat.childbirth.noAuspicious', 'No auspicious dates found in this period'));
                      try {
                        trackAstrologyEvent.shareTapped({
                          content_type: 'muhurat',
                          muhurat_type: 'childbirth',
                          source: 'childbirth_planner',
                        });
                        await Share.share({ message: lines.join('\n'), title: shareTitle });
                        trackAstrologyEvent.muhuratShared('childbirth', {
                          recommendation_count: days.length,
                        });
                      } catch (error) {
                        if (String(error?.message || '').toLowerCase().includes('dismiss')) return;
                        Alert.alert(
                          t('muhurat.common.shareFailed', 'Share failed'),
                          error?.message || t('muhurat.common.shareFailedBody', 'Could not share muhurat results.')
                        );
                      }
                    }}
                    style={{
                      flexDirection: 'row',
                      alignItems: 'center',
                      gap: 6,
                      paddingHorizontal: 10,
                      paddingVertical: 8,
                      borderRadius: 8,
                      borderWidth: 1,
                      borderColor: ui.cardBorder,
                      backgroundColor: ui.insetBg,
                    }}
                  >
                    <Icon name="share-outline" size={18} color={ui.text} />
                    <Text style={{ color: ui.text, fontSize: 13, fontWeight: '600' }}>{t('muhurat.common.share', 'Share')}</Text>
                  </TouchableOpacity>
                </View>
                {results.recommendations.length === 0 ? (
                  <View style={[styles.noDataCard, { backgroundColor: ui.softBg }]}>
                    <Text style={[styles.noDataText, { color: ui.text }]}>{t('muhurat.childbirth.noAuspicious', 'No auspicious dates found in this period')}</Text>
                <Text style={[styles.noDataHint, { color: ui.muted }]}>{t('muhurat.childbirth.emptyHint', 'Try widening the date range and checking different chart conditions:')}</Text>
                    <Text style={[styles.noDataTip, { color: ui.muted }]}>• {t('muhurat.childbirth.tipExtend', 'Extending the date range to 60-90 days')}</Text>
                    <Text style={[styles.noDataTip, { color: ui.muted }]}>• {t('muhurat.childbirth.tipEclipse', 'Avoiding eclipse periods and inauspicious months')}</Text>
                    <Text style={[styles.noDataTip, { color: ui.muted }]}>• {t('muhurat.childbirth.tipLunar', 'Checking different lunar months')}</Text>
                  </View>
                ) : (
                  results.recommendations.map((day, idx) => (
                    <View key={idx} style={[styles.resultItem, { backgroundColor: ui.softBg, borderColor: ui.cardBorder, borderWidth: isDark ? 0 : 1 }]}>
                      <View style={styles.dateHeader}>
                        <Text style={[styles.dateTitle, { color: ui.text }]}>{new Date(day.date).toDateString()}</Text>
                        <View style={styles.tag}>
                          <Text style={styles.tagText}>{day.nakshatra}</Text>
                        </View>
                      </View>
                      {day.panchak?.is_panchak && (
                        <View style={[styles.panchakAlert, !isDark && { backgroundColor: 'rgba(234, 88, 12, 0.08)', borderColor: 'rgba(234, 88, 12, 0.35)' }]}>
                          <Text style={[styles.panchakTitle, !isDark && { color: '#C2410C' }]}>⚠ {t('muhurat.common.panchakActive', 'Panchak is active')}</Text>
                          <Text style={[styles.panchakReason, { color: ui.muted }]}>{day.panchak.reason}</Text>
                          {(day.panchak.intervals || []).map((interval, intervalIndex) => (
                            <Text key={`${interval.start}-${interval.end}-${intervalIndex}`} style={[styles.panchakInterval, !isDark && { color: '#9A3412' }]}>
                              {t('muhurat.common.panchakActiveFrom', {
                                start: interval.start,
                                end: interval.end,
                                defaultValue: 'Active from {{start}} to {{end}}',
                              })}
                            </Text>
                          ))}
                          <Text style={[styles.panchakNote, { color: ui.muted }]}>{t('muhurat.common.panchakConfirm', 'Confirm a Panchak window with a qualified priest before use.')}</Text>
                        </View>
                      )}
                      
                      <View style={styles.slotGrid}>
                        {day.slots.map((slot, sIdx) => (
                          <View key={sIdx} style={[styles.slot, day.panchak?.is_panchak && styles.panchakSlot]}>
                            <Text style={[styles.slotTime, { color: ui.text }]}>{slot.time}</Text>
                            <Text style={[styles.slotLagna, { color: isDark ? '#FFD700' : '#A16207' }]}>{slot.lagna}</Text>
                          </View>
                        ))}
                      </View>
                    </View>
                  ))
                )}
              </View>
            )}

          </ScrollView>

          {/* Date Pickers */}
          {isWeb ? (
            <>
              <WebDatePickerModal
                visible={showStartPicker}
                value={startDate}
                title={t('muhurat.common.fromDate', 'From date')}
                minimumDate={new Date()}
                onClose={() => setShowStartPicker(false)}
                onChange={(next) => {
                  setStartDate(next);
                  if (next > endDate) setEndDate(next);
                }}
              />
              <WebDatePickerModal
                visible={showEndPicker}
                value={endDate}
                title={t('muhurat.common.toDate', 'To date')}
                minimumDate={startDate}
                onClose={() => setShowEndPicker(false)}
                onChange={(d) => {
                  const daysDiff = Math.ceil((d - startDate) / (1000 * 60 * 60 * 24));
                  if (daysDiff > 30) {
                    Alert.alert(
                      t('muhurat.childbirth.dateRangeLimit', 'Date Range Limit'),
                      t('muhurat.childbirth.dateRangeLimitBody', 'Date range cannot exceed 30 days. Please adjust your selection.')
                    );
                    return;
                  }
                  setEndDate(d);
                }}
              />
            </>
          ) : Platform.OS === 'ios' ? (
            <>
              <Modal visible={showStartPicker} transparent animationType="slide">
                <View style={styles.modalOverlay}>
                  <View style={styles.pickerContainer}>
                    <View style={styles.pickerGradient}>
                      <View style={styles.pickerHeader}>
                        <TouchableOpacity onPress={() => setShowStartPicker(false)}>
                          <Text style={styles.pickerButton}>{t('muhurat.common.cancel', 'Cancel')}</Text>
                        </TouchableOpacity>
                        <TouchableOpacity onPress={() => setShowStartPicker(false)}>
                          <Text style={[styles.pickerButton, styles.pickerButtonDone]}>{t('birthForm.picker.done', 'Done')}</Text>
                        </TouchableOpacity>
                      </View>
                      <DateTimePicker
                        value={startDate}
                        mode="date"
                        display="spinner"
                        minimumDate={new Date()}
                        onChange={(event, selectedDate) => {
                          if (selectedDate) setStartDate(selectedDate);
                        }}
                        style={styles.iosPicker}
                      />
                    </View>
                  </View>
                </View>
              </Modal>
              
              <Modal visible={showEndPicker} transparent animationType="slide">
                <View style={styles.modalOverlay}>
                  <View style={styles.pickerContainer}>
                    <View style={styles.pickerGradient}>
                      <View style={styles.pickerHeader}>
                        <TouchableOpacity onPress={() => setShowEndPicker(false)}>
                          <Text style={styles.pickerButton}>{t('muhurat.common.cancel', 'Cancel')}</Text>
                        </TouchableOpacity>
                        <TouchableOpacity onPress={() => {
                          const daysDiff = Math.ceil((endDate - startDate) / (1000 * 60 * 60 * 24));
                          if (daysDiff > 30) {
                            Alert.alert(
                              t('muhurat.childbirth.dateRangeLimit', 'Date Range Limit'),
                              t('muhurat.childbirth.dateRangeLimitBody', 'Date range cannot exceed 30 days. Please adjust your selection.')
                            );
                            return;
                          }
                          setShowEndPicker(false);
                        }}>
                          <Text style={[styles.pickerButton, styles.pickerButtonDone]}>{t('birthForm.picker.done', 'Done')}</Text>
                        </TouchableOpacity>
                      </View>
                      <DateTimePicker
                        value={endDate}
                        mode="date"
                        display="spinner"
                        minimumDate={startDate}
                        onChange={(event, selectedDate) => {
                          if (selectedDate) setEndDate(selectedDate);
                        }}
                        style={styles.iosPicker}
                      />
                    </View>
                  </View>
                </View>
              </Modal>
            </>
          ) : (
            <>
              {showStartPicker && (
                <DateTimePicker
                  value={startDate}
                  mode="date"
                  display="default"
                  minimumDate={new Date()}
                  onChange={(e, d) => { 
                    setShowStartPicker(false); 
                    if(d) setStartDate(d); 
                  }}
                />
              )}
              {showEndPicker && (
                <DateTimePicker
                  value={endDate}
                  mode="date"
                  display="default"
                  minimumDate={startDate}
                  onChange={(e, d) => { 
                    setShowEndPicker(false); 
                    if(d) {
                      const daysDiff = Math.ceil((d - startDate) / (1000 * 60 * 60 * 24));
                      if (daysDiff > 30) {
                        Alert.alert(
                          t('muhurat.childbirth.dateRangeLimit', 'Date Range Limit'),
                          t('muhurat.childbirth.dateRangeLimitBody', 'Date range cannot exceed 30 days. Please adjust your selection.')
                        );
                        return;
                      }
                      setEndDate(d);
                    }
                  }}
                />
              )}
            </>
          )}



          {/* Location Picker Modal */}
          {showLocationPicker && (
            <LocationPicker
              onLocationSelect={(location) => {
                setDeliveryLocation(location);
                setShowLocationPicker(false);
              }}
              onClose={() => setShowLocationPicker(false)}
            />
          )}

        </SafeAreaView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  gradient: { flex: 1 },
  safeArea: { flex: 1 },
  scroll: { padding: 20 },
  header: { 
    flexDirection: 'row', 
    justifyContent: 'space-between', 
    alignItems: 'center', 
    marginBottom: 20 
  },
  headerTitle: { 
    color: COLORS.white, 
    fontSize: 20, 
    fontWeight: '600' 
  },
  placeholder: { width: 24 },
  
  creditCard: {
    backgroundColor: 'rgba(255,255,255,0.08)',
    borderRadius: 12,
    padding: 15,
    marginBottom: 20,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.15)'
  },
  creditRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8
  },
  creditLabel: {
    color: 'rgba(255,255,255,0.9)',
    fontSize: 14,
    fontWeight: '600'
  },
  creditBalance: {
    fontSize: 14,
    fontWeight: '600'
  },
  buyCreditsBtn: {
    backgroundColor: '#FF5722',
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 6,
    alignSelf: 'flex-start'
  },
  buyCreditsText: {
    color: COLORS.white,
    fontSize: 12,
    fontWeight: '600'
  },
  
  card: { 
    backgroundColor: 'rgba(255,255,255,0.1)', 
    borderRadius: 16, 
    padding: 20, 
    marginBottom: 20,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.2)'
  },
  cardTitle: { 
    color: 'rgba(255,255,255,0.8)', 
    fontSize: 14, 
    fontWeight: '600', 
    marginBottom: 15 
  },
  dateRow: { 
    flexDirection: 'row', 
    justifyContent: 'space-between', 
    alignItems: 'center' 
  },
  dateBtn: { 
    backgroundColor: 'rgba(0,0,0,0.3)', 
    padding: 12, 
    borderRadius: 8, 
    width: '42%' 
  },
  dateLabel: { 
    color: 'rgba(255,255,255,0.6)', 
    fontSize: 12 
  },
  dateValue: { 
    color: COLORS.white, 
    fontSize: 16, 
    fontWeight: '600', 
    marginTop: 2 
  },
  
  locationBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(0,0,0,0.3)',
    padding: 12,
    borderRadius: 8,
    gap: 10
  },
  locationText: {
    flex: 1,
    color: COLORS.white,
    fontSize: 16
  },
  hint: { 
    color: 'rgba(255,255,255,0.6)', 
    fontSize: 12, 
    marginTop: 10 
  },
  
  calcButton: { 
    borderRadius: 12, 
    overflow: 'hidden',
    marginBottom: 20 
  },
  calcGradient: {
    padding: 16, 
    alignItems: 'center'
  },
  calcButtonText: { 
    color: COLORS.white, 
    fontWeight: '600', 
    fontSize: 16 
  },
  disabledButton: {
    opacity: 0.6
  },
  
  resultsContainer: { marginTop: 10 },
  resultHeader: { 
    color: COLORS.white, 
    fontSize: 18, 
    fontWeight: '600', 
    marginBottom: 15 
  },
  resultItem: { 
    backgroundColor: 'rgba(255,255,255,0.05)', 
    borderRadius: 12, 
    padding: 15, 
    marginBottom: 15, 
    borderLeftWidth: 4, 
    borderLeftColor: '#00C853' 
  },
  dateHeader: { 
    flexDirection: 'row', 
    justifyContent: 'space-between', 
    alignItems: 'center', 
    marginBottom: 10 
  },
  dateTitle: { 
    color: COLORS.white, 
    fontSize: 16, 
    fontWeight: '600' 
  },
  tag: { 
    backgroundColor: 'rgba(255,255,255,0.1)', 
    paddingHorizontal: 8, 
    paddingVertical: 2, 
    borderRadius: 4 
  },
  tagText: { 
    color: 'rgba(255,255,255,0.8)', 
    fontSize: 12 
  },
  
  slotGrid: { 
    flexDirection: 'row', 
    flexWrap: 'wrap', 
    gap: 8 
  },
  slot: { 
    backgroundColor: 'rgba(0, 200, 83, 0.15)', 
    paddingVertical: 6, 
    paddingHorizontal: 12, 
    borderRadius: 6, 
    alignItems: 'center', 
    minWidth: 70 
  },
  slotTime: { 
    color: COLORS.white, 
    fontWeight: '600', 
    fontSize: 14 
  },
  slotLagna: { 
    color: '#FFD700', 
    fontSize: 10 
  },
  panchakAlert: { backgroundColor: 'rgba(255, 87, 34, 0.14)', borderWidth: 1, borderColor: 'rgba(255, 152, 0, 0.55)', borderRadius: 10, padding: 10, marginBottom: 12 },
  panchakTitle: { color: '#FFB74D', fontSize: 14, fontWeight: '600', marginBottom: 4 },
  panchakReason: { color: 'rgba(255,255,255,0.78)', fontSize: 12, lineHeight: 17 },
  panchakInterval: { color: '#FFD180', fontSize: 12, fontWeight: '600', marginTop: 4 },
  panchakNote: { color: 'rgba(255,255,255,0.7)', fontSize: 11, lineHeight: 15, marginTop: 6 },
  panchakSlot: { backgroundColor: 'rgba(255, 87, 34, 0.18)', borderWidth: 1, borderColor: 'rgba(255, 152, 0, 0.35)' },
  noDataCard: {
    backgroundColor: 'rgba(255,255,255,0.05)',
    borderRadius: 12,
    padding: 20,
    alignItems: 'center'
  },
  noDataText: { 
    color: 'rgba(255,255,255,0.8)', 
    textAlign: 'center',
    fontSize: 16,
    marginBottom: 8
  },
  noDataHint: {
    color: 'rgba(255,255,255,0.6)',
    textAlign: 'center',
    fontSize: 14,
    marginBottom: 10
  },
  noDataTip: {
    color: 'rgba(255,255,255,0.5)',
    fontSize: 13,
    marginBottom: 5,
    paddingLeft: 10
  },
  modalOverlay: { 
    flex: 1, 
    backgroundColor: 'rgba(0, 0, 0, 0.5)', 
    justifyContent: 'flex-end' 
  },
  pickerContainer: { 
    backgroundColor: '#fff',
    borderTopLeftRadius: 20, 
    borderTopRightRadius: 20, 
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: -2 },
    shadowOpacity: 0.25,
    shadowRadius: 10,
    elevation: 10
  },
  pickerGradient: { 
    paddingBottom: 30,
    backgroundColor: '#fff'
  },
  pickerHeader: { 
    flexDirection: 'row', 
    justifyContent: 'space-between', 
    alignItems: 'center',
    paddingHorizontal: 20, 
    paddingVertical: 16, 
    borderBottomWidth: 0.5, 
    borderBottomColor: 'rgba(0, 0, 0, 0.1)',
    backgroundColor: '#f8f9fa'
  },
  pickerButton: { 
    fontSize: 17, 
    color: '#007AFF', 
    fontWeight: '400' 
  },
  pickerButtonDone: { 
    color: '#007AFF', 
    fontWeight: '600' 
  },
  iosPicker: {
    backgroundColor: '#fff',
    marginHorizontal: 20
  }
});
