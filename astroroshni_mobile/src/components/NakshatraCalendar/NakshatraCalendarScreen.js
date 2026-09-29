import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  ActivityIndicator, Alert, Modal, Platform, Pressable, ScrollView, Share, StatusBar, StyleSheet,
  Text, TextInput, TouchableOpacity, View, useWindowDimensions,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useFocusEffect } from '@react-navigation/native';
import { ScrollView as GestureScrollView } from 'react-native-gesture-handler';
import Icon from '@expo/vector-icons/Ionicons';
import { useTranslation } from 'react-i18next';
import { chartAPI } from '../../services/api';
import { useTheme } from '../../context/ThemeContext';
import PlaceSearchField from '../PlaceSearchField';

const NAKSHATRAS = [
  'Ashwini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashira', 'Ardra', 'Punarvasu', 'Pushya',
  'Ashlesha', 'Magha', 'Purva Phalguni', 'Uttara Phalguni', 'Hasta', 'Chitra', 'Swati',
  'Vishakha', 'Anuradha', 'Jyeshtha', 'Mula', 'Purva Ashadha', 'Uttara Ashadha', 'Shravana',
  'Dhanishta', 'Shatabhisha', 'Purva Bhadrapada', 'Uttara Bhadrapada', 'Revati',
];
const LORDS = ['Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury'];
const NATURES = [
  'laghu', 'ugra', 'mishra', 'dhruva', 'mridu', 'tikshna', 'chara', 'laghu', 'tikshna',
  'ugra', 'ugra', 'dhruva', 'laghu', 'mridu', 'chara', 'mishra', 'mridu', 'tikshna',
  'tikshna', 'ugra', 'dhruva', 'chara', 'chara', 'chara', 'ugra', 'dhruva', 'mridu',
];
const LOCALES = { english: 'en-IN', hindi: 'hi-IN', es: 'es-ES', french: 'fr-FR', german: 'de-DE', russian: 'ru-RU', chinese: 'zh-CN', mandarin: 'zh-CN', tamil: 'ta-IN', telugu: 'te-IN', gujarati: 'gu-IN', marathi: 'mr-IN' };
const keyFor = (name) => String(name || '').replace(/\s+/g, '_');
const parsePeriodDate = (date, time) => {
  const [y, m, d] = String(date || '').split('T')[0].split('-').map(Number);
  const match = String(time || '').match(/(\d+):(\d+)\s*(AM|PM)/i);
  if (!y || !m || !d || !match) return null;
  let hour = Number(match[1]) % 12;
  if (match[3].toUpperCase() === 'PM') hour += 12;
  return new Date(y, m - 1, d, hour, Number(match[2]));
};

export default function NakshatraCalendarScreen({ navigation, route }) {
  const { t, i18n } = useTranslation();
  const { colors } = useTheme();
  const { width, height } = useWindowDimensions();
  const tablet = width >= 768;
  const birth = route.params?.birthData || {};
  const today = new Date();
  const [mode, setMode] = useState(route.params?.mode === 'nakshatra' ? 'nakshatra' : 'date');
  const [year, setYear] = useState(route.params?.year || today.getFullYear());
  const [month, setMonth] = useState(today.getMonth() + 1);
  const [nakshatra, setNakshatra] = useState(route.params?.nakshatra || 'Revati');
  const initialSelectionPending = useRef(!route.params?.nakshatra);
  const [location, setLocation] = useState({
    name: birth.place || route.params?.locationName || 'New Delhi, India',
    latitude: Number.isFinite(Number(birth.latitude)) ? Number(birth.latitude) : 28.6139,
    longitude: Number.isFinite(Number(birth.longitude)) ? Number(birth.longitude) : 77.2090,
  });
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [yearModal, setYearModal] = useState(false);
  const [nakshatraModal, setNakshatraModal] = useState(false);
  const [locationModal, setLocationModal] = useState(false);
  const [detail, setDetail] = useState(null);
  const surface = colors.cardBackground || colors.surface;
  const raised = colors.surfaceRaised || surface;
  const muted = colors.surfaceMuted || colors.background;
  const border = colors.cardBorder;

  const localName = useCallback((name) => t(`home.nakshatra_names.${keyFor(name)}`, name), [t]);
  const localPlanet = useCallback((name) => t(`home.planet_names.${name}`, name), [t]);
  const formatDate = useCallback((iso, weekday = false) => {
    const [y, m, d] = String(iso || '').split('T')[0].split('-').map(Number);
    if (!y || !m || !d) return iso || '';
    try {
      return new Intl.DateTimeFormat(LOCALES[i18n.language] || 'en-IN', {
        day: 'numeric', month: 'short', year: 'numeric', ...(weekday ? { weekday: 'short' } : {}), timeZone: 'UTC',
      }).format(new Date(Date.UTC(y, m - 1, d, 12)));
    } catch (_) { return `${d}/${m}/${y}`; }
  }, [i18n.language]);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const response = await chartAPI.getNakshatraYearCalendar(year, location.latitude, location.longitude);
      setData(response?.data || null);
    } catch (_) {
      Alert.alert(t('common.error', 'Error'), t('nakshatraCalendar.loadError'));
      setData(null);
    } finally { setLoading(false); }
  }, [location.latitude, location.longitude, t, year]);
  useEffect(() => { load(); }, [load]);

  useFocusEffect(
    useCallback(() => {
      const style = colors.statusBarStyle || 'dark-content';
      StatusBar.setBarStyle(style, true);
      if (Platform.OS === 'android') {
        StatusBar.setTranslucent(false);
        StatusBar.setBackgroundColor(colors.background, true);
      }
      return () => {
        StatusBar.setBarStyle('light-content', true);
        if (Platform.OS === 'android') StatusBar.setBackgroundColor(colors.headerSurface, true);
      };
    }, [colors.background, colors.headerSurface, colors.statusBarStyle])
  );

  const periods = useMemo(() => Object.values(data?.months || {}).flat().sort((a, b) => (
    (parsePeriodDate(a.start_date, a.start_time)?.getTime() || 0) - (parsePeriodDate(b.start_date, b.start_time)?.getTime() || 0)
  )), [data]);
  const monthPeriods = data?.months?.[String(month)] || [];
  const selectedPeriods = useMemo(() => periods.filter((row) => row.nakshatra === nakshatra), [nakshatra, periods]);
  const current = useMemo(() => periods.find((row) => {
    const start = parsePeriodDate(row.start_date, row.start_time);
    const end = parsePeriodDate(row.end_date, row.end_time);
    return start && end && start <= today && today < end;
  }), [periods]);
  useEffect(() => {
    if (initialSelectionPending.current && current?.nakshatra) {
      initialSelectionPending.current = false;
      setNakshatra(current.nakshatra);
    }
  }, [current]);
  const nextIndex = selectedPeriods.findIndex((row) => (parsePeriodDate(row.end_date, row.end_time) || 0) >= today);
  const filtered = NAKSHATRAS.filter((name) => {
    const query = search.trim().toLowerCase();
    return !query || name.toLowerCase().includes(query) || localName(name).toLowerCase().includes(query);
  });
  const selectedIndex = Math.max(0, NAKSHATRAS.indexOf(nakshatra));
  const years = Array.from({ length: 12 }, (_, index) => today.getFullYear() - 1 + index);

  const chooseNakshatra = (name) => {
    initialSelectionPending.current = false;
    setNakshatra(name);
    setSearch('');
    setNakshatraModal(false);
  };
  const share = async (row) => {
    const message = `${localName(row.nakshatra)}\n${t('nakshatraCalendar.begins')}: ${formatDate(row.start_date)} · ${row.start_time}\n${t('nakshatraCalendar.ends')}: ${formatDate(row.end_date)} · ${row.end_time}\n${location.name}`;
    try { await Share.share({ message }); } catch (_) { /* dismissed */ }
  };

  const occurrence = (row, index) => {
    const active = current?.nakshatra === row.nakshatra && current?.start_date === row.start_date && current?.start_time === row.start_time;
    const next = mode === 'nakshatra' && index === nextIndex && !active;
    return (
      <TouchableOpacity key={`${row.nakshatra}-${row.start_date}-${row.start_time}`} onPress={() => setDetail(row)} activeOpacity={0.78}
        style={[styles.card, { backgroundColor: raised, borderColor: active || next ? colors.primary : border }]}>
        <View style={styles.cardHead}>
          <View style={styles.titleLine}>
            <Text style={[styles.cardTitle, { color: colors.text }]}>{mode === 'date' ? localName(row.nakshatra) : formatDate(row.start_date, true)}</Text>
            {active || next ? <View style={[styles.badge, { backgroundColor: colors.primary }]}><Text style={styles.badgeText}>{active ? t('nakshatraCalendar.activeNow') : t('nakshatraCalendar.next')}</Text></View> : null}
          </View>
          <Icon name="chevron-forward" size={18} color={colors.textSecondary} />
        </View>
        <View style={styles.times}>
          <View style={styles.timeBlock}><Text style={[styles.label, { color: colors.textSecondary }]}>{t('nakshatraCalendar.begins')}</Text><Text style={[styles.time, { color: colors.text }]}>{row.start_time}</Text><Text style={[styles.date, { color: colors.textSecondary }]}>{formatDate(row.start_date)}</Text></View>
          <Icon name="arrow-forward" size={20} color={colors.primary} />
          <View style={styles.timeBlock}><Text style={[styles.label, { color: colors.textSecondary }]}>{t('nakshatraCalendar.ends')}</Text><Text style={[styles.time, { color: colors.text }]}>{row.end_time}</Text><Text style={[styles.date, { color: colors.textSecondary }]}>{formatDate(row.end_date)}</Text></View>
        </View>
      </TouchableOpacity>
    );
  };

  const selector = (modal = false) => (
    <View style={[styles.selector, modal && { borderWidth: 0, padding: 0 }, { backgroundColor: surface, borderColor: border }]}>
      <View style={[styles.search, { backgroundColor: muted, borderColor: border }]}><Icon name="search" size={18} color={colors.textSecondary} /><TextInput value={search} onChangeText={setSearch} placeholder={t('nakshatraCalendar.search')} placeholderTextColor={colors.textSecondary} style={[styles.searchInput, { color: colors.text }]} /></View>
      <ScrollView style={modal || tablet ? styles.selectorScroll : null} contentContainerStyle={styles.grid} keyboardShouldPersistTaps="handled">
        {filtered.map((name) => <TouchableOpacity key={name} onPress={() => chooseNakshatra(name)} style={[styles.nakChip, { backgroundColor: name === nakshatra ? colors.primary : muted, borderColor: name === nakshatra ? colors.primary : border }]}><Text numberOfLines={1} style={[styles.nakChipText, { color: name === nakshatra ? '#fff' : colors.text }]}>{localName(name)}</Text></TouchableOpacity>)}
      </ScrollView>
    </View>
  );

  const dateView = (
    <View style={styles.flex}>
      <View style={styles.monthStrip}>
        <GestureScrollView
          horizontal
          nestedScrollEnabled
          directionalLockEnabled
          showsHorizontalScrollIndicator={false}
          style={styles.monthScroll}
          contentContainerStyle={styles.months}
        >
          {Array.from({ length: 12 }, (_, i) => i + 1).map((number) => {
            const label = new Intl.DateTimeFormat(LOCALES[i18n.language] || 'en-IN', { month: 'short', timeZone: 'UTC' }).format(new Date(Date.UTC(2026, number - 1, 1)));
            return (
              <TouchableOpacity
                key={number}
                onPress={() => setMonth(number)}
                style={[styles.month, { backgroundColor: number === month ? colors.primary : muted, borderColor: number === month ? colors.primary : border }]}
              >
                <Text style={{ color: number === month ? '#fff' : colors.text, fontWeight: '800', fontSize: 12 }}>{label}</Text>
              </TouchableOpacity>
            );
          })}
        </GestureScrollView>
      </View>
      <ScrollView style={styles.flex} contentContainerStyle={styles.list}>
        <View style={styles.sectionHead}><View style={styles.flex}><Text style={[styles.eyebrow, { color: colors.primary }]}>{t('nakshatraCalendar.chronological')}</Text><Text style={[styles.sectionTitle, { color: colors.text }]}>{t('nakshatraCalendar.monthTransitions')}</Text></View><TouchableOpacity onPress={() => { setYear(today.getFullYear()); setMonth(today.getMonth() + 1); }} style={[styles.today, { borderColor: border }]}><Text style={{ color: colors.primary, fontWeight: '800' }}>{t('nakshatraCalendar.today')}</Text></TouchableOpacity></View>
        {monthPeriods.length ? monthPeriods.map(occurrence) : <Text style={[styles.empty, { color: colors.textSecondary }]}>{t('nakshatraCalendar.noData')}</Text>}
      </ScrollView>
    </View>
  );

  const selectedList = (
    <ScrollView style={styles.flex} contentContainerStyle={styles.list}>
      <View style={[styles.hero, { backgroundColor: muted, borderColor: border }]}><TouchableOpacity style={styles.flex} onPress={() => navigation.navigate('NakshatraLibrary', { nakshatra })} accessibilityRole="button" accessibilityLabel={t('nakshatraLibrary.open', { name: localName(nakshatra) })}><Text style={[styles.eyebrow, { color: colors.primary }]}>{t('nakshatraCalendar.selected')}</Text><View style={styles.titleLine}><Text style={[styles.heroTitle, { color: colors.text, flexShrink: 1 }]}>{localName(nakshatra)}</Text><Icon name="book-outline" size={16} color={colors.primary} /></View><Text style={[styles.heroMeta, { color: colors.textSecondary }]}>{localPlanet(LORDS[selectedIndex % 9])} · {t(`nakshatraCalendar.natures.${NATURES[selectedIndex]}`)}</Text><Text style={[styles.readMore, { color: colors.primary }]}>{t('nakshatraLibrary.open', { name: localName(nakshatra) })} →</Text></TouchableOpacity>{!tablet ? <TouchableOpacity onPress={() => setNakshatraModal(true)} style={[styles.change, { backgroundColor: raised, borderColor: border }]}><Text style={{ color: colors.primary, fontWeight: '800' }}>{t('nakshatraCalendar.change')}</Text></TouchableOpacity> : null}</View>
      <Text style={[styles.count, { color: colors.textSecondary }]}>{t('nakshatraCalendar.count', { count: selectedPeriods.length, year })}</Text>
      {selectedPeriods.map(occurrence)}
    </ScrollView>
  );

  const duration = detail ? ((parsePeriodDate(detail.end_date, detail.end_time) - parsePeriodDate(detail.start_date, detail.start_time)) / 3600000).toFixed(1) : null;
  return (
    <SafeAreaView style={[styles.container, { backgroundColor: colors.background }]} edges={['top']}>
      <StatusBar barStyle={colors.statusBarStyle || 'dark-content'} backgroundColor={colors.background} translucent={false} />
      <View style={[styles.header, { backgroundColor: surface, borderBottomColor: border }]}><TouchableOpacity onPress={() => navigation.goBack()} style={styles.icon}><Icon name="arrow-back" size={23} color={colors.text} /></TouchableOpacity><View style={styles.flex}><Text style={[styles.headerTitle, { color: colors.text }]}>{t('nakshatraCalendar.title')}</Text><TouchableOpacity onPress={() => setLocationModal(true)} style={styles.location}><Icon name="location-outline" size={14} color={colors.primary} /><Text numberOfLines={1} style={[styles.locationText, { color: colors.textSecondary }]}>{location.name}</Text><Icon name="chevron-down" size={13} color={colors.textSecondary} /></TouchableOpacity></View><TouchableOpacity onPress={() => setYearModal(true)} style={[styles.year, { backgroundColor: muted, borderColor: border }]}><Text style={{ color: colors.text, fontWeight: '900' }}>{year}</Text><Icon name="chevron-down" size={14} color={colors.primary} /></TouchableOpacity></View>
      <View style={[styles.tabs, { backgroundColor: muted, borderColor: border }]}>{[['date', t('nakshatraCalendar.byDate')], ['nakshatra', t('nakshatraCalendar.byNakshatra')]].map(([value, label]) => <TouchableOpacity key={value} onPress={() => setMode(value)} style={[styles.tab, mode === value && { backgroundColor: surface, borderColor: colors.primary }]}><Text style={{ color: mode === value ? colors.primary : colors.textSecondary, fontWeight: '900' }}>{label}</Text></TouchableOpacity>)}</View>
      <View style={[styles.timezone, { borderBottomColor: border }]}><Icon name="time-outline" size={15} color={colors.textSecondary} /><Text style={[styles.timezoneText, { color: colors.textSecondary }]}>{t('nakshatraCalendar.locationTime', { location: location.name })}</Text></View>
      {loading ? <View style={styles.center}><ActivityIndicator size="large" color={colors.primary} /><Text style={[styles.loading, { color: colors.textSecondary }]}>{t('nakshatraCalendar.loading')}</Text></View> : mode === 'date' ? dateView : <View style={[styles.flex, tablet && styles.split]}>{tablet ? <View style={styles.selectorColumn}>{selector()}</View> : null}{selectedList}</View>}

      <Modal visible={yearModal} transparent animationType="fade" onRequestClose={() => setYearModal(false)}><Pressable style={styles.overlay} onPress={() => setYearModal(false)}><Pressable style={[styles.dialog, { backgroundColor: surface, borderColor: border }]} onPress={(e) => e.stopPropagation()}><Text style={[styles.modalTitle, { color: colors.text }]}>{t('nakshatraCalendar.selectYear')}</Text><ScrollView style={{ maxHeight: height * 0.55 }}>{years.map((value) => <TouchableOpacity key={value} onPress={() => { setYear(value); setYearModal(false); }} style={[styles.row, value === year && { backgroundColor: muted }]}><Text style={{ color: value === year ? colors.primary : colors.text, fontWeight: '800' }}>{value}</Text>{value === year ? <Icon name="checkmark-circle" size={20} color={colors.primary} /> : null}</TouchableOpacity>)}</ScrollView></Pressable></Pressable></Modal>
      <Modal visible={nakshatraModal} transparent animationType="slide" onRequestClose={() => setNakshatraModal(false)}><View style={[styles.overlay, styles.bottom]}><View style={[styles.sheet, styles.pickerSheet, { backgroundColor: surface, borderColor: border, height: Math.round(height * 0.75) }]}><View style={styles.sheetHead}><View><Text style={[styles.eyebrow, { color: colors.primary }]}>{t('nakshatraCalendar.all27')}</Text><Text style={[styles.modalTitle, { color: colors.text }]}>{t('nakshatraCalendar.choose')}</Text></View><TouchableOpacity onPress={() => setNakshatraModal(false)} style={styles.icon}><Icon name="close" size={24} color={colors.text} /></TouchableOpacity></View>{selector(true)}</View></View></Modal>
      <Modal visible={locationModal} transparent animationType="slide" onRequestClose={() => setLocationModal(false)}><View style={[styles.overlay, styles.bottom]}><View style={[styles.sheet, { backgroundColor: surface, borderColor: border }]}><View style={styles.sheetHead}><Text style={[styles.modalTitle, { color: colors.text }]}>{t('nakshatraCalendar.changeLocation')}</Text><TouchableOpacity onPress={() => setLocationModal(false)} style={styles.icon}><Icon name="close" size={24} color={colors.text} /></TouchableOpacity></View><Text style={[styles.help, { color: colors.textSecondary }]}>{t('nakshatraCalendar.locationHelp')}</Text><PlaceSearchField selectedName={location.name} selectedLatitude={location.latitude} selectedLongitude={location.longitude} onSelect={(place) => { setLocation({ name: place.name, latitude: Number(place.latitude), longitude: Number(place.longitude) }); setLocationModal(false); }} /></View></View></Modal>
      <Modal visible={Boolean(detail)} transparent animationType="slide" onRequestClose={() => setDetail(null)}><View style={[styles.overlay, styles.bottom]}><View style={[styles.sheet, { backgroundColor: surface, borderColor: border }]}><View style={styles.sheetHead}><View><Text style={[styles.eyebrow, { color: colors.primary }]}>{t('nakshatraCalendar.details')}</Text><Text style={[styles.detailTitle, { color: colors.text }]}>{localName(detail?.nakshatra)}</Text></View><TouchableOpacity onPress={() => setDetail(null)} style={styles.icon}><Icon name="close" size={24} color={colors.text} /></TouchableOpacity></View>{detail ? <><View style={[styles.detailTimes, { backgroundColor: muted }]}><View style={styles.timeBlock}><Text style={[styles.label, { color: colors.textSecondary }]}>{t('nakshatraCalendar.begins')}</Text><Text style={[styles.time, { color: colors.text }]}>{detail.start_time}</Text><Text style={[styles.date, { color: colors.textSecondary }]}>{formatDate(detail.start_date, true)}</Text></View><Icon name="arrow-forward" size={20} color={colors.primary} /><View style={styles.timeBlock}><Text style={[styles.label, { color: colors.textSecondary }]}>{t('nakshatraCalendar.ends')}</Text><Text style={[styles.time, { color: colors.text }]}>{detail.end_time}</Text><Text style={[styles.date, { color: colors.textSecondary }]}>{formatDate(detail.end_date, true)}</Text></View></View><View style={styles.facts}><Text style={{ color: colors.textSecondary }}>{t('nakshatraCalendar.duration')}</Text><Text style={{ color: colors.text, fontWeight: '800' }}>{t('nakshatraCalendar.hours', { count: duration })}</Text></View><TouchableOpacity
        onPress={() => { const name = detail.nakshatra; setDetail(null); navigation.navigate('NakshatraLibrary', { nakshatra: name }); }}
        accessibilityRole="button"
        style={[styles.readButton, { borderColor: border }]}
      ><Icon name="book-outline" size={19} color={colors.primary} /><Text style={[styles.readButtonText, { color: colors.primary }]}>{t('nakshatraLibrary.open', { name: localName(detail.nakshatra) })}</Text><Icon name="chevron-forward" size={18} color={colors.primary} /></TouchableOpacity><TouchableOpacity onPress={() => share(detail)} style={[styles.share, { backgroundColor: colors.primary }]}><Icon name="share-social-outline" size={19} color="#fff" /><Text style={styles.shareText}>{t('nakshatraCalendar.share')}</Text></TouchableOpacity></> : null}</View></View></Modal>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 }, flex: { flex: 1 }, header: { minHeight: 70, flexDirection: 'row', alignItems: 'center', padding: 12, borderBottomWidth: 1 }, icon: { width: 42, height: 42, alignItems: 'center', justifyContent: 'center' }, headerTitle: { fontSize: 20, fontWeight: '900' }, location: { flexDirection: 'row', alignItems: 'center', marginTop: 3, maxWidth: 320 }, locationText: { fontSize: 12, marginHorizontal: 3, flexShrink: 1 }, year: { height: 40, borderWidth: 1, borderRadius: 20, paddingHorizontal: 12, flexDirection: 'row', alignItems: 'center', gap: 4 },
  tabs: { margin: 14, marginBottom: 8, padding: 4, borderWidth: 1, borderRadius: 16, flexDirection: 'row' }, tab: { flex: 1, minHeight: 42, borderRadius: 12, borderWidth: 1, borderColor: 'transparent', alignItems: 'center', justifyContent: 'center' }, timezone: { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 20, paddingBottom: 10, borderBottomWidth: 1 }, timezoneText: { fontSize: 12, marginLeft: 6, flex: 1 }, center: { flex: 1, alignItems: 'center', justifyContent: 'center' }, loading: { marginTop: 12 },
  monthStrip: { width: '100%', height: 64 }, monthScroll: { flex: 1 }, months: { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 14 }, month: { height: 40, paddingHorizontal: 14, borderWidth: 1, borderRadius: 20, marginRight: 8, alignItems: 'center', justifyContent: 'center' }, list: { padding: 16, paddingBottom: 40, width: '100%', maxWidth: 900, alignSelf: 'center' }, sectionHead: { flexDirection: 'row', alignItems: 'center', marginBottom: 14 }, eyebrow: { fontSize: 10, fontWeight: '900', letterSpacing: 1.1, marginBottom: 4 }, sectionTitle: { fontSize: 19, fontWeight: '900' }, today: { borderWidth: 1, borderRadius: 18, paddingHorizontal: 12, paddingVertical: 8 }, empty: { textAlign: 'center', padding: 40 },
  card: { borderWidth: 1, borderRadius: 18, padding: 16, marginBottom: 12 }, cardHead: { flexDirection: 'row', alignItems: 'center' }, titleLine: { flex: 1, flexDirection: 'row', alignItems: 'center', flexWrap: 'wrap' }, cardTitle: { fontSize: 17, fontWeight: '900', marginRight: 8 }, badge: { borderRadius: 10, paddingHorizontal: 8, paddingVertical: 3 }, badgeText: { color: '#fff', fontSize: 10, fontWeight: '900' }, times: { flexDirection: 'row', alignItems: 'center', marginTop: 14, gap: 12 }, timeBlock: { flex: 1 }, label: { fontSize: 10, fontWeight: '900', textTransform: 'uppercase' }, time: { fontSize: 16, fontWeight: '900', marginTop: 3 }, date: { fontSize: 12, marginTop: 2 },
  split: { flexDirection: 'row', maxWidth: 1180, alignSelf: 'center', width: '100%' }, selectorColumn: { width: 330, padding: 16, paddingRight: 0 }, selector: { flex: 1, borderWidth: 1, borderRadius: 20, padding: 13 }, selectorScroll: { flex: 1, minHeight: 0 }, search: { minHeight: 48, borderWidth: 1, borderRadius: 14, paddingHorizontal: 12, flexDirection: 'row', alignItems: 'center' }, searchInput: { flex: 1, paddingHorizontal: 9, color: '#111' }, grid: { flexDirection: 'row', flexWrap: 'wrap', paddingTop: 12, paddingBottom: 12 }, nakChip: { width: '48%', marginRight: '2%', marginBottom: 8, minHeight: 42, borderWidth: 1, borderRadius: 12, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 6 }, nakChipText: { fontSize: 12, fontWeight: '800' },
  readMore: { fontSize: 13, fontWeight: '800', marginTop: 10 },
  readButton: { minHeight: 48, borderWidth: 1, borderRadius: 14, padding: 12, marginBottom: 12, flexDirection: 'row', alignItems: 'center', gap: 8 },
  readButtonText: { flex: 1, fontWeight: '800' },
  hero: { borderWidth: 1, borderRadius: 20, padding: 17, flexDirection: 'row', alignItems: 'center', marginBottom: 12 }, heroTitle: { fontSize: 25, fontWeight: '900' }, heroMeta: { fontSize: 13, marginTop: 4, textTransform: 'capitalize' }, change: { borderWidth: 1, borderRadius: 18, paddingHorizontal: 12, paddingVertical: 9 }, count: { fontSize: 12, fontWeight: '700', marginBottom: 12 },
  overlay: { flex: 1, padding: 18, alignItems: 'center', justifyContent: 'center', backgroundColor: 'rgba(0,0,0,.55)' }, bottom: { justifyContent: 'flex-end' }, dialog: { width: '100%', maxWidth: 360, borderWidth: 1, borderRadius: 24, padding: 20 }, modalTitle: { fontSize: 20, fontWeight: '900' }, row: { minHeight: 50, borderRadius: 12, paddingHorizontal: 14, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }, sheet: { width: '100%', maxWidth: 720, borderWidth: 1, borderTopLeftRadius: 28, borderTopRightRadius: 28, padding: 20, paddingBottom: 30 }, pickerSheet: { overflow: 'hidden' }, sheetHead: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }, help: { fontSize: 13, lineHeight: 19, marginBottom: 16 }, detailTitle: { fontSize: 27, fontWeight: '900' }, detailTimes: { borderRadius: 18, padding: 18, flexDirection: 'row', alignItems: 'center', gap: 12 }, facts: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 18 }, share: { minHeight: 50, borderRadius: 16, flexDirection: 'row', alignItems: 'center', justifyContent: 'center' }, shareText: { color: '#fff', fontWeight: '900', marginLeft: 8 },
});
