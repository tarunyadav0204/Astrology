import React, { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, Alert, Modal, Platform, ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import DateTimePicker from '@react-native-community/datetimepicker';
import Icon from '@expo/vector-icons/Ionicons';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { useCredits } from '../credits/CreditContext';
import { useAuthGate } from '../auth/AuthGateContext';
import { muhuratAPI, pricingAPI } from '../services/api';
import { storage } from '../services/storage';
import { useTheme } from '../context/ThemeContext';
import LocationPicker from './LocationPicker';
import { normalizeCalendarDateForApi } from '../utils/birthDateUtils';
import { useTranslation } from 'react-i18next';

const fmtDate = (value) => value.toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' });
const localDate = (value) => `${value.getFullYear()}-${String(value.getMonth() + 1).padStart(2, '0')}-${String(value.getDate()).padStart(2, '0')}`;
const profileKey = (profile) => String(profile?.id || `${profile?.name}|${profile?.date}|${profile?.time}`);
const validProfile = (profile) => profile?.name && profile?.date && profile?.time && Number.isFinite(Number(profile?.latitude)) && Number.isFinite(Number(profile?.longitude));
const apiProfile = (profile) => profile ? ({ name: profile.name, date: normalizeCalendarDateForApi(profile.date), time: profile.time, latitude: Number(profile.latitude), longitude: Number(profile.longitude), timezone: profile.timezone || undefined }) : null;

export default function MarriageMuhuratScreen({ navigation }) {
  const { t } = useTranslation();
  const { colors } = useTheme();
  const { credits, fetchBalance } = useCredits();
  const { requireAuthForPaid } = useAuthGate();
  const [profiles, setProfiles] = useState([]);
  const [bride, setBride] = useState(null);
  const [groom, setGroom] = useState(null);
  const [pickerFor, setPickerFor] = useState(null);
  const [venue, setVenue] = useState(null);
  const [venueOpen, setVenueOpen] = useState(false);
  const [startDate, setStartDate] = useState(new Date());
  const [endDate, setEndDate] = useState(new Date(Date.now() + 29 * 86400000));
  const [datePicker, setDatePicker] = useState(null);
  const [availability, setAvailability] = useState('evening');
  const [cost, setCost] = useState(0);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const load = useCallback(async () => {
    const [current, saved] = await Promise.all([storage.getBirthData(), storage.getBirthProfiles()]);
    const all = [current, ...(saved || [])].filter(validProfile).filter((item, index, list) => list.findIndex((candidate) => profileKey(candidate) === profileKey(item)) === index);
    setProfiles(all);
    if (!bride && current && validProfile(current)) setBride(current);
    if (!venue && current?.latitude != null && current?.longitude != null) setVenue({ latitude: Number(current.latitude), longitude: Number(current.longitude), name: current.place || 'My location' });
    try {
      const response = await pricingAPI.getPricing();
      setCost(Number((response?.data || response)?.pricing?.marriage_muhurat || 0));
    } catch (_) { /* price remains unavailable until retry */ }
  }, [bride, venue]);

  useEffect(() => { load(); }, [load]);
  useFocusEffect(useCallback(() => { fetchBalance(); }, [fetchBalance]));

  const hours = availability === 'day' ? ['08:00', '17:00'] : availability === 'overnight' ? ['20:00', '01:00'] : ['18:00', '23:30'];
  const choose = (profile) => { if (pickerFor === 'bride') setBride(profile); else setGroom(profile); setPickerFor(null); };
  const submit = async () => {
    if (!venue) return Alert.alert(t('muhurat.marriage.chooseVenue'), t('muhurat.marriage.chooseVenueBody'));
    if (endDate < startDate || (endDate - startDate) / 86400000 >= 60) return Alert.alert(t('muhurat.marriage.checkDates'), t('muhurat.marriage.checkDatesBody'));
    const authorised = await requireAuthForPaid({ feature: t('muhurat.marriage.title'), message: t('muhurat.marriage.signIn'), resume: { resumeRoute: 'MarriageMuhurat', resumeParams: {} } });
    if (!authorised) return;
    if (credits < cost) return Alert.alert(t('muhurat.common.insufficientCredits'), t('muhurat.common.needCredits', { cost, credits }), [{ text: t('muhurat.common.cancel') }, { text: t('muhurat.common.buyCredits'), onPress: () => navigation.navigate('Credits') }]);
    Alert.alert(t('muhurat.marriage.confirmTitle'), t('muhurat.marriage.confirmBody', { cost }), [{ text: t('muhurat.common.cancel'), style: 'cancel' }, { text: t('muhurat.marriage.continue'), onPress: calculate }]);
  };
  const calculate = async () => {
    setLoading(true); setResult(null);
    try {
      const response = await muhuratAPI.calculateMarriage({ start_date: localDate(startDate), end_date: localDate(endDate), venue_latitude: Number(venue.latitude), venue_longitude: Number(venue.longitude), allowed_start: hours[0], allowed_end: hours[1], minimum_duration_minutes: 30, bride: apiProfile(bride), groom: apiProfile(groom) });
      setResult((response?.data || response).data);
      await fetchBalance();
    } catch (error) {
      const message = error?.response?.status === 402 ? t('muhurat.marriage.balanceChanged') : (error?.response?.data?.detail || t('muhurat.marriage.calculationFailed'));
      Alert.alert(t('muhurat.marriage.title'), message);
    } finally { setLoading(false); }
  };
  const card = { backgroundColor: colors.cardBackground, borderColor: colors.cardBorder };
  return <View style={[styles.page, { backgroundColor: colors.background }]}>
    <LinearGradient colors={[colors.gradientStart, colors.gradientMid, colors.gradientEnd]} style={StyleSheet.absoluteFill} />
    <SafeAreaView style={styles.safe}><ScrollView contentContainerStyle={styles.scroll}>
      <View style={styles.header}><TouchableOpacity onPress={() => navigation.goBack()}><Icon name="arrow-back" size={24} color={colors.text} /></TouchableOpacity><Text style={[styles.title, { color: colors.text }]}>{t('muhurat.marriage.title')}</Text><View style={{ width: 24 }} /></View>
      <Text style={[styles.intro, { color: colors.textSecondary }]}>{t('muhurat.marriage.intro')}</Text>
      <View style={[styles.notice, { backgroundColor: colors.surfaceRaised, borderColor: colors.cardBorder }]}><Text style={[styles.noticeText, { color: colors.textSecondary }]}>{t('muhurat.marriage.notice')}</Text></View>
      <Section label={t('muhurat.marriage.couple')} card={card}><ProfileButton label={t('muhurat.marriage.bride')} value={bride} onPress={() => setPickerFor('bride')} colors={colors} t={t} /><ProfileButton label={t('muhurat.marriage.groom')} value={groom} onPress={() => setPickerFor('groom')} colors={colors} t={t} /><Text style={[styles.hint, { color: colors.textSecondary }]}>{t('muhurat.marriage.profileHint')}</Text></Section>
      <Section label={t('muhurat.marriage.venue')} card={card}><TouchableOpacity style={[styles.select, { backgroundColor: colors.surfaceMuted }]} onPress={() => setVenueOpen(true)}><Icon name="location" size={19} color={colors.text} /><Text style={[styles.selectText, { color: colors.text }]}>{venue?.name || t('muhurat.marriage.chooseCity')}</Text><Icon name="chevron-forward" size={18} color={colors.textSecondary} /></TouchableOpacity></Section>
      <Section label={t('muhurat.common.dateRange')} card={card}><View style={styles.row}><DateButton label={t('muhurat.common.from')} value={startDate} colors={colors} onPress={() => setDatePicker('start')} /><DateButton label={t('muhurat.marriage.through')} value={endDate} colors={colors} onPress={() => setDatePicker('end')} /></View></Section>
      <Section label={t('muhurat.marriage.hours')} card={card}><View style={styles.choices}>{[['day', t('muhurat.marriage.day')], ['evening', t('muhurat.marriage.evening')], ['overnight', t('muhurat.marriage.overnight')]].map(([id, label]) => <TouchableOpacity key={id} onPress={() => setAvailability(id)} style={[styles.choice, { borderColor: availability === id ? colors.primary : colors.cardBorder, backgroundColor: availability === id ? colors.surfaceRaised : colors.surfaceMuted }]}><Text style={[styles.choiceText, { color: colors.text }]}>{label}</Text></TouchableOpacity>)}</View><Text style={[styles.hint, { color: colors.textSecondary }]}>{t('muhurat.marriage.overnightHint')}</Text></Section>
      <TouchableOpacity disabled={loading} onPress={submit} style={styles.cta}><LinearGradient colors={[colors.primary, colors.primaryStrong]} style={styles.ctaGradient}>{loading ? <ActivityIndicator color={colors.onPrimary} /> : <Text style={[styles.ctaText, { color: colors.onPrimary }]}>{t('muhurat.marriage.find', { cost })}</Text>}</LinearGradient></TouchableOpacity>
      {result && <Results result={result} colors={colors} t={t} />}
    </ScrollView>
    <Modal visible={!!pickerFor} transparent animationType="fade" onRequestClose={() => setPickerFor(null)}><View style={styles.modal}><View style={[styles.modalCard, card]}><Text style={[styles.modalTitle, { color: colors.text }]}>{t('muhurat.marriage.chooseChart')}</Text>{profiles.map((profile) => <TouchableOpacity key={profileKey(profile)} onPress={() => choose(profile)} style={[styles.profileRow, { borderColor: colors.cardBorder }]}><Text style={[styles.profileName, { color: colors.text }]}>{profile.name}</Text><Text style={[styles.profileMeta, { color: colors.textSecondary }]}>{profile.date} · {profile.time} · {profile.place || t('muhurat.marriage.savedLocation')}</Text></TouchableOpacity>)}{!profiles.length && <Text style={{ color: colors.textSecondary }}>{t('muhurat.marriage.noCharts')}</Text>}<TouchableOpacity onPress={() => choose(null)} style={styles.close}><Text style={{ color: colors.primary }}>{t('muhurat.marriage.withoutChart')}</Text></TouchableOpacity><TouchableOpacity onPress={() => setPickerFor(null)} style={styles.close}><Text style={{ color: colors.textSecondary }}>{t('muhurat.common.cancel')}</Text></TouchableOpacity></View></View></Modal>
    {venueOpen && <LocationPicker onClose={() => setVenueOpen(false)} onLocationSelect={(place) => { setVenue(place); setVenueOpen(false); }} />}
    {datePicker && <DateTimePicker value={datePicker === 'start' ? startDate : endDate} mode="date" minimumDate={datePicker === 'end' ? startDate : new Date()} onChange={(_, selected) => { setDatePicker(null); if (!selected) return; if (datePicker === 'start') { setStartDate(selected); if (selected > endDate) setEndDate(selected); } else setEndDate(selected); }} />}
    </SafeAreaView></View>;
}

const Section = ({ label, children, card }) => <View style={[styles.card, card]}><Text style={styles.label}>{label}</Text>{children}</View>;
const ProfileButton = ({ label, value, onPress, colors, t }) => <TouchableOpacity onPress={onPress} style={[styles.select, { backgroundColor: colors.surfaceMuted }]}><Icon name="person-outline" size={19} color={colors.text} /><View style={{ flex: 1 }}><Text style={[styles.profileLabel, { color: colors.textSecondary }]}>{label}</Text><Text style={[styles.selectText, { color: colors.text }]}>{value?.name || t('muhurat.marriage.addChart')}</Text></View><Icon name="chevron-forward" size={18} color={colors.textSecondary} /></TouchableOpacity>;
const DateButton = ({ label, value, colors, onPress }) => <TouchableOpacity onPress={onPress} style={[styles.date, { backgroundColor: colors.surfaceMuted }]}><Text style={[styles.profileLabel, { color: colors.textSecondary }]}>{label}</Text><Text style={[styles.selectText, { color: colors.text }]}>{fmtDate(value)}</Text></TouchableOpacity>;
const Results = ({ result, colors, t }) => {
  const formatVenueTime = (value) => new Intl.DateTimeFormat(undefined, { hour: '2-digit', minute: '2-digit', timeZone: result.location?.timezone }).format(new Date(value));
  return <View style={[styles.results, { borderColor: colors.cardBorder, backgroundColor: colors.cardBackground }]}><Text style={[styles.resultTitle, { color: colors.text }]}>{t('muhurat.marriage.results')}</Text><Text style={[styles.hint, { color: colors.textSecondary }]}>{result.personalization} · {result.location?.timezone}</Text>{!result.recommendations?.length && <Text style={[styles.empty, { color: colors.textSecondary }]}>{t('muhurat.marriage.noResults')}</Text>}{result.recommendations?.map((day) => <View key={day.date} style={[styles.day, { borderColor: colors.cardBorder }]}><Text style={[styles.dayDate, { color: colors.text }]}>{day.date}</Text>{day.slots.map((slot) => <View key={slot.start_time} style={styles.slot}><Text style={[styles.slotTime, { color: colors.primary }]}>{formatVenueTime(slot.start_time)} – {formatVenueTime(slot.end_time)}</Text><Text style={{ color: colors.textSecondary }}>{slot.duration_minutes} min · {slot.lagna} {t('muhurat.marriage.lagna')}</Text><Text style={{ color: colors.textSecondary }}>{slot.positives?.[0]}</Text></View>)}</View>)}<Text style={[styles.hint, { color: colors.textSecondary }]}>{result.limitations?.join(' ')}</Text></View>;
};
const styles = StyleSheet.create({ page:{flex:1}, safe:{flex:1}, scroll:{padding:20,paddingBottom:42}, header:{flexDirection:'row',justifyContent:'space-between',alignItems:'center',marginBottom:16}, title:{fontSize:21,fontWeight:'700'}, intro:{lineHeight:21,marginBottom:12}, notice:{borderWidth:1,borderRadius:12,padding:12,marginBottom:12},noticeText:{fontSize:12,lineHeight:18},card:{borderWidth:1,borderRadius:16,padding:15,marginBottom:12},label:{fontSize:11,fontWeight:'700',letterSpacing:1,color:'#B45309',marginBottom:10},select:{minHeight:52,borderRadius:12,paddingHorizontal:13,flexDirection:'row',alignItems:'center',gap:10,marginBottom:8},selectText:{fontSize:15,fontWeight:'600'},profileLabel:{fontSize:11},hint:{fontSize:12,lineHeight:18},row:{flexDirection:'row',gap:10},date:{flex:1,borderRadius:12,padding:13},choices:{flexDirection:'row',gap:7},choice:{flex:1,borderWidth:1,borderRadius:10,padding:10,minHeight:58,justifyContent:'center'},choiceText:{fontSize:12,textAlign:'center',lineHeight:17},cta:{borderRadius:14,overflow:'hidden',marginVertical:8},ctaGradient:{padding:17,alignItems:'center'},ctaText:{fontSize:15,fontWeight:'700'},results:{borderWidth:1,borderRadius:16,padding:15,marginTop:10},resultTitle:{fontSize:18,fontWeight:'700',marginBottom:5},empty:{paddingVertical:18,lineHeight:20},day:{borderTopWidth:1,paddingTop:12,marginTop:12},dayDate:{fontWeight:'700',fontSize:15},slot:{paddingVertical:9,gap:3},slotTime:{fontWeight:'700',fontSize:15},modal:{flex:1,backgroundColor:'rgba(0,0,0,.5)',justifyContent:'center',padding:20},modalCard:{borderWidth:1,borderRadius:16,padding:18,maxHeight:'75%'},modalTitle:{fontSize:18,fontWeight:'700',marginBottom:10},profileRow:{paddingVertical:12,borderBottomWidth:1},profileName:{fontWeight:'700'},profileMeta:{fontSize:12,marginTop:3},close:{paddingVertical:12,alignItems:'center'} });
