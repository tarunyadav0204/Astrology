import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  ActivityIndicator, Platform, ScrollView, StatusBar, StyleSheet, Text, TextInput,
  TouchableOpacity, View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useFocusEffect } from '@react-navigation/native';
import Icon from '@expo/vector-icons/Ionicons';
import { useTranslation } from 'react-i18next';
import { chartAPI } from '../../services/api';
import { useTheme } from '../../context/ThemeContext';

const NAKSHATRAS = [
  'Ashwini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashira', 'Ardra', 'Punarvasu', 'Pushya',
  'Ashlesha', 'Magha', 'Purva Phalguni', 'Uttara Phalguni', 'Hasta', 'Chitra', 'Swati',
  'Vishakha', 'Anuradha', 'Jyeshtha', 'Mula', 'Purva Ashadha', 'Uttara Ashadha', 'Shravana',
  'Dhanishta', 'Shatabhisha', 'Purva Bhadrapada', 'Uttara Bhadrapada', 'Revati',
];
const LORDS = ['Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury'];

const keyFor = (name) => String(name || '').replace(/\s+/g, '_');

const SECTIONS = [
  ['description', 'description'],
  ['characteristics', 'characteristics'],
  ['positive_traits', 'strengths'],
  ['negative_traits', 'cautions'],
  ['careers', 'careers'],
  ['compatibility', 'compatibility'],
];

export default function NakshatraLibraryScreen({ navigation, route }) {
  const { t } = useTranslation();
  const { colors } = useTheme();
  const selected = route.params?.nakshatra || null;
  const [info, setInfo] = useState(null);
  const [navigationLinks, setNavigationLinks] = useState(null);
  const [loading, setLoading] = useState(Boolean(selected));
  const [error, setError] = useState(false);
  const [search, setSearch] = useState('');
  const surface = colors.cardBackground || colors.surface;
  const muted = colors.surfaceMuted || colors.background;
  const border = colors.cardBorder;

  const localName = useCallback((name) => t(`home.nakshatra_names.${keyFor(name)}`, name), [t]);
  const localPlanet = useCallback((name) => t(`home.planet_names.${name}`, name), [t]);

  const load = useCallback(async (name) => {
    if (!name) return;
    setLoading(true);
    setError(false);
    try {
      const response = await chartAPI.getNakshatraInfo(name);
      setInfo(response?.data?.nakshatra || null);
      setNavigationLinks(response?.data?.navigation || null);
      if (!response?.data?.nakshatra) setError(true);
    } catch (_) {
      setInfo(null);
      setNavigationLinks(null);
      setError(true);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(selected); }, [load, selected]);

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

  const filtered = useMemo(() => NAKSHATRAS.filter((name) => {
    const query = search.trim().toLowerCase();
    return !query || name.toLowerCase().includes(query) || localName(name).toLowerCase().includes(query);
  }), [localName, search]);

  const open = (name) => navigation.push('NakshatraLibrary', { nakshatra: name });

  const facts = info ? [
    [t('nakshatraLibrary.lord'), localPlanet(info.lord)],
    [t('nakshatraLibrary.deity'), info.deity],
    [t('nakshatraLibrary.nature'), info.nature],
    [t('nakshatraLibrary.guna'), info.guna],
  ] : [];

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: colors.background }]} edges={['top']}>
      <StatusBar barStyle={colors.statusBarStyle || 'dark-content'} backgroundColor={colors.background} translucent={false} />
      <View style={[styles.header, { backgroundColor: surface, borderBottomColor: border }]}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.icon} accessibilityRole="button">
          <Icon name="arrow-back" size={23} color={colors.text} />
        </TouchableOpacity>
        <Text style={[styles.headerTitle, { color: colors.text }]} numberOfLines={1}>
          {selected ? localName(selected) : t('nakshatraLibrary.title')}
        </Text>
      </View>

      {selected ? (
        loading ? (
          <View style={styles.center}>
            <ActivityIndicator size="large" color={colors.primary} />
          </View>
        ) : error || !info ? (
          <View style={styles.center}>
            <Text style={[styles.body, { color: colors.textSecondary, textAlign: 'center' }]}>{t('nakshatraLibrary.loadError')}</Text>
            <TouchableOpacity onPress={() => load(selected)} style={[styles.retry, { borderColor: border }]}>
              <Text style={{ color: colors.primary, fontWeight: '800' }}>{t('common.retry', 'Retry')}</Text>
            </TouchableOpacity>
          </View>
        ) : (
          <ScrollView contentContainerStyle={styles.detail}>
            <View style={styles.facts}>
              {facts.map(([label, value]) => (
                <View key={label} style={[styles.fact, { backgroundColor: muted, borderColor: border }]}>
                  <Text style={[styles.factLabel, { color: colors.textSecondary }]}>{label}</Text>
                  <Text style={[styles.factValue, { color: colors.text }]}>{value || '—'}</Text>
                </View>
              ))}
            </View>
            {SECTIONS.map(([field, labelKey]) => info[field] ? (
              <View key={field} style={[styles.section, { backgroundColor: surface, borderColor: border }]}>
                <Text style={[styles.sectionTitle, { color: colors.primary }]}>{t(`nakshatraLibrary.${labelKey}`)}</Text>
                <Text style={[styles.body, { color: colors.text }]}>{info[field]}</Text>
              </View>
            ) : null)}
            {navigationLinks ? (
              <View style={styles.pager}>
                <TouchableOpacity onPress={() => open(navigationLinks.previous)} style={[styles.pageButton, { borderColor: border }]}>
                  <Text style={[styles.pageLabel, { color: colors.textSecondary }]}>{t('nakshatraLibrary.previous')}</Text>
                  <Text style={[styles.pageName, { color: colors.text }]}>{localName(navigationLinks.previous)}</Text>
                </TouchableOpacity>
                <TouchableOpacity onPress={() => open(navigationLinks.next)} style={[styles.pageButton, { borderColor: border }]}>
                  <Text style={[styles.pageLabel, { color: colors.textSecondary, textAlign: 'right' }]}>{t('nakshatraLibrary.next')}</Text>
                  <Text style={[styles.pageName, { color: colors.text, textAlign: 'right' }]}>{localName(navigationLinks.next)}</Text>
                </TouchableOpacity>
              </View>
            ) : null}
          </ScrollView>
        )
      ) : (
        <ScrollView contentContainerStyle={styles.list} keyboardShouldPersistTaps="handled">
          <Text style={[styles.hint, { color: colors.textSecondary }]}>{t('nakshatraLibrary.listHint')}</Text>
          <View style={[styles.search, { backgroundColor: muted, borderColor: border }]}>
            <Icon name="search" size={18} color={colors.textSecondary} />
            <TextInput
              value={search}
              onChangeText={setSearch}
              placeholder={t('nakshatraLibrary.search')}
              placeholderTextColor={colors.textSecondary}
              style={[styles.searchInput, { color: colors.text }]}
            />
          </View>
          {filtered.map((name) => {
            const index = NAKSHATRAS.indexOf(name);
            return (
              <TouchableOpacity
                key={name}
                onPress={() => open(name)}
                style={[styles.row, { backgroundColor: surface, borderColor: border }]}
                accessibilityRole="button"
                accessibilityLabel={t('nakshatraLibrary.open', { name: localName(name) })}
              >
                <Text style={[styles.index, { color: colors.primary }]}>{index + 1}</Text>
                <View style={styles.flex}>
                  <Text style={[styles.rowTitle, { color: colors.text }]}>{localName(name)}</Text>
                  <Text style={[styles.rowMeta, { color: colors.textSecondary }]}>{localPlanet(LORDS[index % 9])}</Text>
                </View>
                <Icon name="chevron-forward" size={18} color={colors.textSecondary} />
              </TouchableOpacity>
            );
          })}
        </ScrollView>
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  header: { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 8, paddingVertical: 8, borderBottomWidth: StyleSheet.hairlineWidth },
  icon: { width: 40, height: 40, alignItems: 'center', justifyContent: 'center' },
  headerTitle: { flex: 1, fontSize: 20, fontWeight: '800' },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: 24 },
  list: { padding: 16, paddingBottom: 32 },
  hint: { fontSize: 14, lineHeight: 20, marginBottom: 12 },
  search: { flexDirection: 'row', alignItems: 'center', borderWidth: 1, borderRadius: 14, paddingHorizontal: 12, marginBottom: 12 },
  searchInput: { flex: 1, minHeight: 44, marginLeft: 8, fontSize: 15 },
  row: { flexDirection: 'row', alignItems: 'center', borderWidth: 1, borderRadius: 16, paddingVertical: 12, paddingHorizontal: 14, marginBottom: 8 },
  index: { width: 28, fontSize: 13, fontWeight: '800' },
  flex: { flex: 1 },
  rowTitle: { fontSize: 16, fontWeight: '800' },
  rowMeta: { fontSize: 13, marginTop: 2 },
  detail: { padding: 16, paddingBottom: 36 },
  facts: { flexDirection: 'row', flexWrap: 'wrap', marginHorizontal: -4 },
  fact: { width: '48%', margin: '1%', borderWidth: 1, borderRadius: 14, padding: 12 },
  factLabel: { fontSize: 11, fontWeight: '800', letterSpacing: 0.4, textTransform: 'uppercase' },
  factValue: { fontSize: 15, fontWeight: '700', marginTop: 4 },
  section: { borderWidth: 1, borderRadius: 16, padding: 14, marginTop: 12 },
  sectionTitle: { fontSize: 12, fontWeight: '800', letterSpacing: 0.4, textTransform: 'uppercase', marginBottom: 6 },
  body: { fontSize: 15, lineHeight: 22 },
  retry: { marginTop: 14, borderWidth: 1, borderRadius: 12, paddingHorizontal: 16, paddingVertical: 10 },
  pager: { flexDirection: 'row', marginTop: 16 },
  pageButton: { flex: 1, borderWidth: 1, borderRadius: 14, padding: 12, marginHorizontal: 4 },
  pageLabel: { fontSize: 11, fontWeight: '800', textTransform: 'uppercase' },
  pageName: { fontSize: 15, fontWeight: '800', marginTop: 4 },
});
