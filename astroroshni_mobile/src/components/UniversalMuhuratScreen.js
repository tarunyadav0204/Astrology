import React, { useState, useEffect } from 'react';
import { useFocusEffect } from '@react-navigation/native';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Alert, ActivityIndicator, Platform, Modal, Share } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { SafeAreaView } from 'react-native-safe-area-context';
import Icon from '@expo/vector-icons/Ionicons';
import DateTimePicker from '@react-native-community/datetimepicker';
import { storage } from '../services/storage';
import { API_BASE_URL, getEndpoint } from '../utils/constants';
import LocationPicker from './LocationPicker';
import { useCredits } from '../credits/CreditContext';
import { useAuthGate } from '../auth/AuthGateContext';
import { pricingAPI } from '../services/api';
import WebDatePickerModal from './Common/WebDatePickerModal';
import { useTheme } from '../context/ThemeContext';
import { trackAstrologyEvent } from '../utils/analytics';
import { useTranslation } from 'react-i18next';

const isWeb = Platform.OS === 'web';

export default function UniversalMuhuratScreen({ route, navigation }) {
  const { t } = useTranslation();
  const { config: rawConfig } = route.params;
  const config = {
    ...rawConfig,
    title: t(`muhurat.types.${rawConfig?.id}.title`, rawConfig?.title || 'Muhurat'),
    subtitle: t(`muhurat.types.${rawConfig?.id}.subtitle`, rawConfig?.subtitle || ''),
  };
  const { credits, fetchBalance } = useCredits();
  const { requireAuthForPaid } = useAuthGate();
  const { theme, colors } = useTheme();
  const isDark = theme === 'dark';
  const accent = isDark ? (config?.gradient?.[0] || colors.primary) : colors.primary;
  const ui = {
    text: colors.text,
    muted: colors.textSecondary,
    cardBg: isDark ? 'rgba(255,255,255,0.1)' : colors.cardBackground,
    cardBorder: isDark ? 'rgba(255,255,255,0.2)' : colors.cardBorder,
    insetBg: isDark ? 'rgba(0,0,0,0.3)' : colors.backgroundSecondary,
    softBg: isDark ? 'rgba(255,255,255,0.08)' : colors.backgroundSecondary,
    resultBg: isDark ? 'rgba(255,255,255,0.05)' : colors.cardBackground,
  };
  
  const [loading, setLoading] = useState(false);
  const [userProfile, setUserProfile] = useState(null);
  const [results, setResults] = useState(null);
  const [creditInfo, setCreditInfo] = useState({ cost: 0, current_credits: 0, can_afford: false });
  
  const [startDate, setStartDate] = useState(new Date());
  const [endDate, setEndDate] = useState(new Date(new Date().setDate(new Date().getDate() + 30)));
  const [showStartPicker, setShowStartPicker] = useState(false);
  const [showEndPicker, setShowEndPicker] = useState(false);
  
  const [location, setLocation] = useState(null);
  const [showLocationPicker, setShowLocationPicker] = useState(false);

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

  const loadProfile = async () => {
    try {
      const data = await storage.getBirthData();
      if (!data?.name) {
        navigation.replace('BirthProfileIntro', { returnTo: 'UniversalMuhurat' });
        return;
      }
      setUserProfile(data);
      if (data.latitude) {
        setLocation({
          latitude: parseFloat(data.latitude),
          longitude: parseFloat(data.longitude),
          name: data.place || t('muhurat.common.myLocation', 'My Location')
        });
      }
    } catch(e) { console.error(e); }
  };

  const loadCreditInfo = async () => {
    try {
      const response = await pricingAPI.getPricing();
      const data = response?.data || response;
      const pricing = data?.pricing || {};
      const configToKey = {
        'childbirth-planner': 'childbirth',
        'childbirth': 'childbirth',
        'vehicle-purchase': 'vehicle',
        'griha-pravesh': 'griha_pravesh',
        'gold-purchase': 'gold',
        'business-opening': 'business'
      };
      const featureName = config.endpoint ? config.endpoint.split('/').pop() : config.id;
      const pricingKey = configToKey[featureName] || configToKey[config.id];
      const cost = pricingKey != null && pricing[pricingKey] != null ? Number(pricing[pricingKey]) : 0;
      setCreditInfo(prev => ({
        ...prev,
        cost,
        current_credits: credits,
        can_afford: credits >= cost
      }));
    } catch(e) {
      console.error('Failed to load credit info:', e);
    }
  };

  const calculate = async () => {
    if (!userProfile || !location) {
      Alert.alert(
        t('muhurat.common.missingData', 'Missing Data'),
        t('muhurat.common.verifyProfileLocation', 'Please verify your profile and location.'),
      );
      return;
    }

    const authOk = await requireAuthForPaid({
      feature: 'muhurat search',
      message: t(
        'muhurat.common.signInSearch',
        'Sign in to run a muhurat search. Credits are charged only after you confirm.',
      ),
      resume: { resumeRoute: 'UniversalMuhurat', resumeParams: route?.params || {} },
    });
    if (!authOk) return;

    if (credits < creditInfo.cost) {
      Alert.alert(
        t('muhurat.common.insufficientCredits', 'Insufficient Credits'),
        t('muhurat.common.needCredits', {
          cost: creditInfo.cost,
          credits,
          defaultValue: 'You need {{cost}} credits but have {{credits}}. Please purchase more credits.',
        }),
        [
          { text: t('muhurat.common.cancel', 'Cancel'), style: 'cancel' },
          { text: t('muhurat.common.buyCredits', 'Buy Credits'), onPress: () => navigation.navigate('Credits') },
        ],
      );
      return;
    }

    Alert.alert(
      t('muhurat.common.confirmCalculation', 'Confirm Calculation'),
      t('muhurat.common.confirmDeduct', {
        cost: creditInfo.cost,
        defaultValue: 'This will deduct {{cost}} credits from your account. Do you want to proceed?',
      }),
      [
        { text: t('muhurat.common.cancel', 'Cancel'), style: 'cancel' },
        { text: t('muhurat.common.proceed', 'Proceed'), onPress: () => performCalculation() },
      ],
    );
  };

  const performCalculation = async () => {
    setLoading(true);
    try {
      const token = await storage.getAuthToken();
      
      const toLocalDateKey = (d) => {
        const y = d.getFullYear();
        const m = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        return `${y}-${m}-${day}`;
      };

      const payload = {
        start_date: toLocalDateKey(startDate),
        end_date: toLocalDateKey(endDate),
        latitude: parseFloat(location.latitude),
        longitude: parseFloat(location.longitude),
        
        user_dob: userProfile.date,
        user_time: userProfile.time,
        user_lat: parseFloat(userProfile.latitude),
        user_lon: parseFloat(userProfile.longitude)
      };

      const response = await fetch(`${API_BASE_URL}${getEndpoint(config.endpoint)}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify(payload)
      });

      const json = await response.json();
      
      if (response.status === 402) {
        Alert.alert(
          t('muhurat.common.insufficientCredits', 'Insufficient Credits'),
          json.detail?.message || t('muhurat.common.pleaseBuyMore', 'Please buy more credits.'),
          [
            { text: t('muhurat.common.cancel', 'Cancel') },
            { text: t('muhurat.common.buy', 'Buy'), onPress: () => navigation.navigate('Credits') },
          ],
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
          t('muhurat.common.calculationFailed', 'Calculation failed.'),
        );
      }
    } catch (e) {
      Alert.alert(
        t('muhurat.common.error', 'Error'),
        t('muhurat.common.networkError', 'Network Error'),
      );
    } finally {
      setLoading(false);
    }
  };

  const visibleRecommendations = results?.recommendations?.length
    ? results.recommendations
    : (results?.best_available_recommendations || []);

  const shareMuhuratResults = async () => {
    if (!results) return;
    const muhuratType = config?.id || config?.key || config?.title || 'muhurat';
    const lines = [
      t('muhurat.common.shareTitle', {
        title: config?.title || muhuratType,
        defaultValue: 'AstroRoshni Muhurat — {{title}}',
      }),
      '',
      ...visibleRecommendations.slice(0, 8).map((day) => {
        const slots = (day.slots || [])
          .slice(0, 3)
          .map((slot) => `${slot.time}${slot.lagna ? ` · ${slot.lagna}` : ''}`)
          .join('; ');
        return `• ${day.date}${slots ? ` — ${slots}` : ''}`;
      }),
    ];
    if (!visibleRecommendations.length) {
      lines.push(t('muhurat.common.noDatesInRange', 'No suitable dates found in the selected range.'));
    }
    try {
      trackAstrologyEvent.shareTapped({
        content_type: 'muhurat',
        muhurat_type: muhuratType,
        source: 'universal_muhurat',
      });
      await Share.share({
        message: lines.join('\n'),
        title: config?.title || t('home.tabs.muhurat', 'Muhurat'),
      });
      trackAstrologyEvent.muhuratShared(muhuratType, {
        recommendation_count: visibleRecommendations.length,
      });
    } catch (error) {
      if (String(error?.message || '').toLowerCase().includes('dismiss')) return;
      Alert.alert(
        t('muhurat.common.shareFailed', 'Share failed'),
        error?.message || t('muhurat.common.shareFailedBody', 'Could not share muhurat results.'),
      );
    }
  };

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      {isDark ? (
        <LinearGradient colors={['#120E24', '#261C45']} style={StyleSheet.absoluteFill} />
      ) : null}
      <SafeAreaView style={styles.safeArea}>
          <ScrollView contentContainerStyle={styles.scroll}>
            
            <View style={styles.header}>
              <TouchableOpacity onPress={() => navigation.goBack()}>
                <Icon name="arrow-back" size={24} color={ui.text} />
              </TouchableOpacity>
              <Text style={[styles.headerTitle, { color: ui.text }]}>{config.title}</Text>
              <View style={{width: 24}}/>
            </View>

            <View style={[styles.creditCard, { backgroundColor: ui.softBg, borderColor: ui.cardBorder }]}>
              <View style={styles.creditRow}>
                <Text style={[styles.creditLabel, { color: ui.text }]}>
                  💎 {t('muhurat.common.costCredits', { cost: creditInfo.cost, defaultValue: 'Cost: {{cost}} credits' })}
                </Text>
                <Text style={[styles.creditBalance, { color: credits >= creditInfo.cost ? '#00C853' : '#FF5722' }]}>
                  {t('muhurat.common.balance', { credits, defaultValue: 'Balance: {{credits}}' })}
                </Text>
              </View>
              {credits < creditInfo.cost && (
                <TouchableOpacity 
                  style={styles.buyCreditsBtn} 
                  onPress={() => navigation.navigate('Credits')}
                >
                  <Text style={styles.buyCreditsText}>{t('muhurat.common.buyCredits', 'Buy Credits')}</Text>
                </TouchableOpacity>
              )}
            </View>

            <View style={[styles.card, { backgroundColor: ui.cardBg, borderColor: ui.cardBorder }]}>
              <Text style={[styles.cardTitle, { color: accent }]}>📅 {t('muhurat.common.dateRange', 'DATE RANGE')}</Text>
              <View style={styles.row}>
                <TouchableOpacity onPress={() => setShowStartPicker(true)} style={[styles.picker, { backgroundColor: ui.insetBg }]}>
                  <Text style={[styles.pickerLabel, { color: ui.muted }]}>{t('muhurat.common.from', 'From')}</Text>
                  <Text style={[styles.pickerValue, { color: ui.text }]}>{startDate.toLocaleDateString()}</Text>
                </TouchableOpacity>
                <Icon name="arrow-forward" size={20} color={ui.muted} />
                <TouchableOpacity onPress={() => setShowEndPicker(true)} style={[styles.picker, { backgroundColor: ui.insetBg }]}>
                  <Text style={[styles.pickerLabel, { color: ui.muted }]}>{t('muhurat.common.to', 'To')}</Text>
                  <Text style={[styles.pickerValue, { color: ui.text }]}>{endDate.toLocaleDateString()}</Text>
                </TouchableOpacity>
              </View>
            </View>

            <View style={[styles.card, { backgroundColor: ui.cardBg, borderColor: ui.cardBorder }]}>
              <Text style={[styles.cardTitle, { color: accent }]}>📍 {t('muhurat.common.location', 'LOCATION')}</Text>
              <TouchableOpacity style={[styles.locBtn, { backgroundColor: ui.insetBg }]} onPress={() => setShowLocationPicker(true)}>
                <Icon name="location" size={20} color={ui.text} />
                <Text style={[styles.locText, { color: ui.text }]}>
                  {location?.name || t('muhurat.common.selectCity', 'Select City')}
                </Text>
                <Text style={[styles.changeText, { color: ui.muted }]}>{t('muhurat.common.change', 'Change')}</Text>
              </TouchableOpacity>
            </View>

            <TouchableOpacity 
              style={[styles.btn, credits < creditInfo.cost && styles.disabledButton]} 
              onPress={calculate} 
              disabled={loading || credits < creditInfo.cost}
            >
              {isDark ? (
                <LinearGradient 
                  colors={credits >= creditInfo.cost ? config.gradient : ['#666', '#888']} 
                  style={styles.btnGrad}
                >
                  {loading ? (
                    <ActivityIndicator color="#fff"/>
                  ) : (
                    <Text style={styles.btnText}>
                      {credits >= creditInfo.cost
                        ? t('muhurat.common.findAuspiciousTime', 'Find Auspicious Time')
                        : t('muhurat.common.insufficientCredits', 'Insufficient Credits')}
                    </Text>
                  )}
                </LinearGradient>
              ) : (
                <View
                  style={[
                    styles.btnGrad,
                    { backgroundColor: credits >= creditInfo.cost ? colors.primary : colors.backgroundTertiary },
                  ]}
                >
                  {loading ? (
                    <ActivityIndicator color="#fff"/>
                  ) : (
                    <Text style={styles.btnText}>
                      {credits >= creditInfo.cost
                        ? t('muhurat.common.findAuspiciousTime', 'Find Auspicious Time')
                        : t('muhurat.common.insufficientCredits', 'Insufficient Credits')}
                    </Text>
                  )}
                </View>
              )}
            </TouchableOpacity>

            {results && (
              <View style={styles.results}>
                <View style={styles.resultsHeaderRow}>
                  <Text style={[styles.resHeader, { color: ui.text, flex: 1 }]}>
                    {t('muhurat.common.recommendedSlots', 'Recommended Slots')}
                  </Text>
                  <TouchableOpacity
                    onPress={shareMuhuratResults}
                    style={[styles.shareBtn, { backgroundColor: ui.insetBg, borderColor: ui.cardBorder }]}
                    accessibilityRole="button"
                    accessibilityLabel={t('muhurat.common.share', 'Share')}
                  >
                    <Icon name="share-outline" size={18} color={ui.text} />
                    <Text style={[styles.shareBtnText, { color: ui.text }]}>{t('muhurat.common.share', 'Share')}</Text>
                  </TouchableOpacity>
                </View>
                <Text style={[styles.auditHint, { color: ui.muted }]}>
                  {t('muhurat.common.auditHint', 'Every date in your selected range is shown below. Tap a rejected date to see why.')}
                </Text>
                <View style={styles.dateAuditGrid}>
                  {[...(results.recommendations || []).map((item) => ({ ...item, accepted: true })), ...(results.best_available_recommendations || []).map((item) => ({ ...item, accepted: false, fallback: true })), ...(results.rejected_dates || []).map((item) => ({ ...item, accepted: false }))]
                    .sort((a, b) => String(a.date).localeCompare(String(b.date)))
                    .map((item) => (
                      <TouchableOpacity
                        key={item.date}
                        style={[styles.dateChip, item.accepted ? styles.dateChipAccepted : (item.fallback ? styles.dateChipFallback : styles.dateChipRejected)]}
                        onPress={() => item.accepted
                          ? Alert.alert(t('muhurat.common.suitableDate', 'Suitable date'), `${item.date}\n${(item.slots || []).map((slot) => `${slot.time} · ${slot.lagna} · ${slot.score}/100`).join('\n')}`)
                          : item.fallback
                            ? Alert.alert(t('muhurat.common.bestAvailableCautions', 'Best available with cautions'), `${item.date}\n${(item.date_warnings || []).join('\n')}`)
                            : Alert.alert(t('muhurat.common.whyRejected', 'Why this date was rejected'), `${item.date}\n${(item.reasons || []).join('\n')}`)}
                      >
                        <Text style={[styles.dateChipDate, { color: ui.text }]}>{item.date.slice(5)}</Text>
                        <Text style={[styles.dateChipState, { color: ui.muted }]}>
                          {item.accepted
                            ? t('muhurat.common.suitable', 'Suitable')
                            : (item.fallback
                              ? t('muhurat.common.caution', 'Caution')
                              : t('muhurat.common.rejected', 'Rejected'))}
                        </Text>
                      </TouchableOpacity>
                    ))}
                </View>
                {results.recommendations.length === 0 && visibleRecommendations.length === 0 ? (
                  <View style={[styles.noDataContainer, { backgroundColor: ui.resultBg }]}>
                    <Text style={[styles.noData, { color: ui.text }]}>
                      {t('muhurat.common.noMuhuratFound', 'No suitable muhurat found')}
                    </Text>
                    <Text style={[styles.noDataSub, { color: ui.muted }]}>
                      {t('muhurat.common.noMuhuratSub', 'Traditional timing rules did not leave a recommended date in this range.')}
                    </Text>
                    {(results.rejected_dates || []).slice(0, 4).map((item) => (
                      <Text key={item.date} style={[styles.noDataTip, { color: ui.muted }]}>• {item.date}: {(item.reasons || []).join(' ')}</Text>
                    ))}
                    <Text style={[styles.noDataTip, { color: ui.muted }]}>
                      {t('muhurat.common.extendRangeTip', 'Try extending the date range or choosing a different location.')}
                    </Text>
                  </View>
                ) : (
                  <>
                  {!results.recommendations.length && (
                    <View style={styles.fallbackNotice}>
                      <Text style={[styles.fallbackTitle, { color: isDark ? '#FFD080' : '#A16207' }]}>
                        {t('muhurat.common.bestAvailableTitle', 'Best available dates with cautions')}
                      </Text>
                      <Text style={[styles.fallbackText, { color: ui.muted }]}>
                        {results.best_available_notice || t('muhurat.common.bestAvailableDefault', 'These dates are shown only when you must proceed. They are not strict recommendations.')}
                      </Text>
                    </View>
                  )}
                  {visibleRecommendations.map((day, idx) => (
                    <View key={idx} style={[styles.resultItem, { backgroundColor: ui.resultBg, borderColor: ui.cardBorder, borderWidth: isDark ? 0 : 1 }]}>
                      <Text style={[styles.resultDate, { color: ui.text }]}>{new Date(day.date).toDateString()}</Text>
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
                          <Text style={[styles.panchakNote, { color: ui.muted }]}>
                            {t('muhurat.common.panchakConfirm', 'Confirm a Panchak window with a qualified priest before use.')}
                          </Text>
                        </View>
                      )}
                      <View style={styles.slotGrid}>
                        {day.slots.map((slot, sIdx) => (
                          <View key={sIdx} style={[styles.slot, day.panchak?.is_panchak && styles.panchakSlot, !isDark && { backgroundColor: 'rgba(16, 185, 129, 0.1)' }]}>
                            <Text style={[styles.slotTime, { color: ui.text }]}>{slot.time}</Text>
                            <Text style={[styles.slotLagna, { color: isDark ? '#FFD700' : '#A16207' }]}>{slot.lagna}</Text>
                            <Text style={[styles.slotScore, { color: ui.muted }]}>{slot.quality} · {slot.score}/100</Text>
                            <Text style={[styles.slotRationale, { color: ui.muted }]}>{slot.rationale}</Text>
                            {slot.panchak && (
                              <Text style={styles.slotCaution}>
                                ⚠ {t('muhurat.common.panchakSlotConfirm', 'Panchak active — confirm this slot with a priest before use.')}
                              </Text>
                            )}
                            {(slot.positives?.length > 0 || slot.cautions?.length > 0) && (
                              <View style={styles.slotFactors}>
                                {slot.positives?.map((reason) => <Text key={`p-${reason}`} style={[styles.slotPositive, !isDark && { color: '#15803D' }]}>✓ {reason}</Text>)}
                                {slot.cautions?.map((reason) => <Text key={`c-${reason}`} style={[styles.slotCaution, !isDark && { color: '#A16207' }]}>! {reason}</Text>)}
                              </View>
                            )}
                          </View>
                        ))}
                      </View>
                    </View>
                  ))}
                  </>
                )}
              </View>
            )}

          </ScrollView>

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
                onChange={setEndDate}
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
                        onChange={(event, selectedDate) => {
                          if (selectedDate) setStartDate(selectedDate);
                        }}
                        minimumDate={new Date()}
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
                        <TouchableOpacity onPress={() => setShowEndPicker(false)}>
                          <Text style={[styles.pickerButton, styles.pickerButtonDone]}>{t('birthForm.picker.done', 'Done')}</Text>
                        </TouchableOpacity>
                      </View>
                      <DateTimePicker
                        value={endDate}
                        mode="date"
                        display="spinner"
                        onChange={(event, selectedDate) => {
                          if (selectedDate) setEndDate(selectedDate);
                        }}
                        minimumDate={startDate}
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
                  onChange={(event, selectedDate) => {
                    setShowStartPicker(false);
                    if (selectedDate) setStartDate(selectedDate);
                  }}
                  minimumDate={new Date()}
                />
              )}
              
              {showEndPicker && (
                <DateTimePicker
                  value={endDate}
                  mode="date"
                  display="default"
                  onChange={(event, selectedDate) => {
                    setShowEndPicker(false);
                    if (selectedDate) setEndDate(selectedDate);
                  }}
                  minimumDate={startDate}
                />
              )}
            </>
          )}

          {showLocationPicker && (
            <LocationPicker
              onLocationSelect={(location) => {
                setLocation(location);
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
  bg: { flex: 1 },
  safeArea: { flex: 1 },
  scroll: { padding: 20 },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 },
  headerTitle: { color: '#fff', fontSize: 20, fontWeight: '600' },
  creditCard: { backgroundColor: 'rgba(255,255,255,0.08)', borderRadius: 12, padding: 15, marginBottom: 20, borderWidth: 1, borderColor: 'rgba(255,255,255,0.15)' },
  creditRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  creditLabel: { color: 'rgba(255,255,255,0.9)', fontSize: 14, fontWeight: '600' },
  creditBalance: { fontSize: 14, fontWeight: '600' },
  buyCreditsBtn: { backgroundColor: '#FF5722', paddingVertical: 8, paddingHorizontal: 16, borderRadius: 6, alignSelf: 'flex-start', marginTop: 8 },
  buyCreditsText: { color: '#fff', fontSize: 12, fontWeight: '600' },
  card: { backgroundColor: 'rgba(255,255,255,0.1)', borderRadius: 16, padding: 20, marginBottom: 20, borderWidth: 1, borderColor: 'rgba(255,255,255,0.2)' },
  cardTitle: { fontSize: 14, fontWeight: '600', marginBottom: 15, color: 'rgba(255,255,255,0.8)' },
  row: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  picker: { backgroundColor: 'rgba(0,0,0,0.3)', padding: 12, borderRadius: 8, width: '42%' },
  pickerLabel: { color: 'rgba(255,255,255,0.6)', fontSize: 12 },
  pickerValue: { color: '#fff', fontSize: 16, fontWeight: '600', marginTop: 2 },
  locBtn: { flexDirection: 'row', alignItems: 'center', backgroundColor: 'rgba(0,0,0,0.3)', padding: 12, borderRadius: 8, gap: 10 },
  locText: { flex: 1, color: '#fff', fontSize: 16 },
  changeText: { color: 'rgba(255,255,255,0.6)', fontSize: 12 },
  btn: { borderRadius: 12, overflow: 'hidden', marginBottom: 20 },
  btnGrad: { padding: 16, alignItems: 'center' },
  btnText: { color: '#fff', fontWeight: '600', fontSize: 16 },
  disabledButton: { opacity: 0.6 },
  results: { marginTop: 20 },
  resultsHeaderRow: { flexDirection: 'row', alignItems: 'center', gap: 10, marginBottom: 4 },
  shareBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 10,
    paddingVertical: 8,
    borderRadius: 8,
    borderWidth: 1,
  },
  shareBtnText: { fontSize: 13, fontWeight: '600' },
  resHeader: { color: '#fff', fontSize: 18, fontWeight: '600', marginBottom: 15 },
  auditHint: { color: 'rgba(255,255,255,0.6)', fontSize: 12, marginBottom: 10 },
  dateAuditGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 7, marginBottom: 15 },
  dateChip: { borderRadius: 8, paddingVertical: 7, paddingHorizontal: 9, minWidth: 66, borderWidth: 1 },
  dateChipAccepted: { backgroundColor: 'rgba(0, 200, 83, 0.18)', borderColor: 'rgba(129, 255, 169, 0.75)' },
  dateChipRejected: { backgroundColor: 'rgba(198, 40, 40, 0.18)', borderColor: 'rgba(255, 128, 128, 0.75)' },
  dateChipFallback: { backgroundColor: 'rgba(188, 116, 24, 0.18)', borderColor: 'rgba(245, 180, 70, 0.8)' },
  dateChipDate: { color: '#fff', fontSize: 12, fontWeight: '600', textAlign: 'center' },
  dateChipState: { color: 'rgba(255,255,255,0.7)', fontSize: 9, textAlign: 'center', marginTop: 2 },
  noDataContainer: { backgroundColor: 'rgba(255,255,255,0.05)', borderRadius: 12, padding: 20, alignItems: 'center' },
  noData: { color: 'rgba(255,255,255,0.8)', fontSize: 16, marginBottom: 8, textAlign: 'center' },
  noDataSub: { color: 'rgba(255,255,255,0.6)', fontSize: 14, marginBottom: 10, textAlign: 'center' },
  noDataTip: { color: 'rgba(255,255,255,0.5)', fontSize: 13, marginBottom: 5 },
  fallbackNotice: { marginTop: 12, padding: 14, borderRadius: 12, backgroundColor: 'rgba(188, 116, 24, 0.14)', borderWidth: 1, borderColor: 'rgba(245, 180, 70, 0.55)' },
  fallbackTitle: { color: '#FFD080', fontSize: 16, fontWeight: '600', marginBottom: 5 },
  fallbackText: { color: 'rgba(255,255,255,0.72)', fontSize: 13, lineHeight: 19 },
  resultItem: { backgroundColor: 'rgba(255,255,255,0.05)', borderRadius: 12, padding: 15, marginBottom: 15 },
  resultDate: { color: '#fff', fontSize: 16, fontWeight: '600', marginBottom: 10 },
  slotGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  slot: { backgroundColor: 'rgba(0, 200, 83, 0.15)', paddingVertical: 8, paddingHorizontal: 12, borderRadius: 6, alignItems: 'center', width: '100%' },
  slotTime: { color: '#fff', fontWeight: '600', fontSize: 14 },
  slotLagna: { color: '#FFD700', fontSize: 10 },
  slotScore: { color: 'rgba(255,255,255,0.65)', fontSize: 9, marginTop: 2 },
  slotRationale: { color: 'rgba(255,255,255,0.75)', fontSize: 9, marginTop: 4, textAlign: 'center' },
  slotFactors: { marginTop: 5, width: '100%' },
  slotPositive: { color: '#B9F6CA', fontSize: 9, marginTop: 2 },
  slotCaution: { color: '#FFE082', fontSize: 9, marginTop: 2 },
  panchakAlert: { backgroundColor: 'rgba(255, 87, 34, 0.14)', borderWidth: 1, borderColor: 'rgba(255, 152, 0, 0.55)', borderRadius: 10, padding: 10, marginBottom: 12 },
  panchakTitle: { color: '#FFB74D', fontSize: 14, fontWeight: '600', marginBottom: 4 },
  panchakReason: { color: 'rgba(255,255,255,0.78)', fontSize: 12, lineHeight: 17 },
  panchakInterval: { color: '#FFD180', fontSize: 12, fontWeight: '600', marginTop: 4 },
  panchakNote: { color: 'rgba(255,255,255,0.7)', fontSize: 11, lineHeight: 15, marginTop: 6 },
  panchakSlot: { backgroundColor: 'rgba(255, 87, 34, 0.18)', borderWidth: 1, borderColor: 'rgba(255, 152, 0, 0.35)' },
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
