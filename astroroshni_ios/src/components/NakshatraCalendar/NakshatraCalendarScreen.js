import React, { useState, useCallback, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Alert,
  ActivityIndicator,
  Modal,
  Dimensions,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Icon from '@expo/vector-icons/Ionicons';
import { chartAPI } from '../../services/api';
import { useTheme } from '../../context/ThemeContext';
import { useTranslation } from 'react-i18next';

const MONTH_NAMES = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
const MONTH_LABELS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
const ordinalSuffix = (n) => {
  if (n >= 11 && n <= 13) return 'th';
  switch (n % 10) { case 1: return 'st'; case 2: return 'nd'; case 3: return 'rd'; default: return 'th'; }
};
const formatDateOrdinal = (isoDate) => {
  if (!isoDate || typeof isoDate !== 'string') return isoDate || '';
  const [y, m, d] = isoDate.split('T')[0].split('-').map(Number);
  if (!y || !m || !d) return isoDate;
  return `${d}${ordinalSuffix(d)} ${MONTH_NAMES[m - 1] || m} ${y}`;
};

const { height: WINDOW_HEIGHT } = Dimensions.get('window');

export default function NakshatraCalendarScreen({ navigation, route }) {
  const { t } = useTranslation();
  const { theme, colors } = useTheme();
  const birthData = route.params?.birthData || null;
  const [yearData, setYearData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedMonth, setSelectedMonth] = useState(() => new Date().getMonth() + 1);
  const [selectedYear, setSelectedYear] = useState(() => new Date().getFullYear());
  const [yearPickerVisible, setYearPickerVisible] = useState(false);

  const displayData = birthData;
  const loadYear = useCallback(async (year) => {
    setLoading(true);
    const lat = displayData ? parseFloat(displayData.latitude) : 28.6139;
    const lon = displayData ? parseFloat(displayData.longitude) : 77.2090;
    try {
      const res = await chartAPI.getNakshatraYearCalendar(year, lat, lon);
      setYearData(res?.data || null);
      setSelectedYear(year);
    } catch (e) {
      Alert.alert(t('common.error', 'Error'), t('home.nakshatra.loadError', 'Could not load nakshatra calendar.'));
      setYearData(null);
    } finally {
      setLoading(false);
    }
  }, [displayData, t]);

  useEffect(() => {
    if (!birthData?.name) {
      navigation.replace('BirthProfileIntro', { returnTo: 'NakshatraCalendar' });
      return;
    }
  }, [birthData, navigation]);

  useEffect(() => {
    if (!displayData) {
      setLoading(false);
      return;
    }
    loadYear(selectedYear);
  }, [displayData?.latitude, displayData?.longitude]);

  const isLight = theme === 'light';
  const headerBg = isLight ? colors.cardBackground : 'rgba(15,23,42,0.98)';
  const screenBg = isLight ? colors.background : '#0f172a';
  const stripBorder = isLight ? colors.cardBorder : 'rgba(148,163,184,0.2)';
  const rowBg = isLight ? '#f8fafc' : 'rgba(255,255,255,0.05)';
  const rowBorder = isLight ? colors.cardBorder : 'rgba(148,163,184,0.2)';
  const yearPickerBg = isLight ? colors.cardBackground : 'rgba(15,23,42,0.98)';
  const yearPickerBorder = isLight ? colors.cardBorder : 'rgba(148,163,184,0.3)';

  const monthList = yearData?.months?.[String(selectedMonth)] || [];
  const currentYear = new Date().getFullYear();
  const yearOptions = [];
  for (let y = currentYear - 1; y <= currentYear + 10; y++) yearOptions.push(y);

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: screenBg }]} edges={['top']}>
      <View style={[styles.header, { backgroundColor: headerBg, borderBottomColor: stripBorder }]}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}>
          <Icon name="arrow-back" size={24} color={colors.text} />
        </TouchableOpacity>
        <View style={styles.titleRow}>
          <Text style={[styles.title, { color: colors.text }]} numberOfLines={1}>
            {t('home.nakshatra.title', 'Nakshatra calendar')}{' '}
          </Text>
          <TouchableOpacity
            onPress={() => setYearPickerVisible(true)}
            style={styles.yearChip}
            hitSlop={{ top: 12, bottom: 12, left: 8, right: 8 }}
          >
            <Text style={[styles.title, { color: colors.primary }]}>{selectedYear}</Text>
            <Icon name="chevron-down" size={20} color={colors.primary} style={{ marginLeft: 4 }} />
          </TouchableOpacity>
        </View>
        <View style={styles.backBtn} />
      </View>

      {!displayData ? (
        <View style={styles.centered}>
          <Text style={[styles.empty, { color: colors.textSecondary }]}>{t('home.nakshatra.noBirthData', 'Birth details required.')}</Text>
        </View>
      ) : loading ? (
        <View style={styles.centered}>
          <ActivityIndicator size="large" color={colors.primary} />
          <Text style={[styles.loadingText, { color: colors.textSecondary }]}>{t('home.loading.ticker', 'Loading...')}</Text>
        </View>
      ) : (
        <>
          <View style={[styles.monthStripWrap, { borderBottomColor: stripBorder }]}>
            <ScrollView
              horizontal
              showsHorizontalScrollIndicator={false}
              contentContainerStyle={styles.monthStrip}
            >
              {MONTH_LABELS.map((label, i) => {
                const monthNum = i + 1;
                const isSelected = selectedMonth === monthNum;
                return (
                  <TouchableOpacity
                    key={monthNum}
                    onPress={() => setSelectedMonth(monthNum)}
                    style={[
                      styles.monthChip,
                      !isSelected && (isLight ? { borderColor: '#cbd5e1', backgroundColor: '#f1f5f9' } : { borderColor: 'rgba(148,163,184,0.3)', backgroundColor: 'rgba(255,255,255,0.08)' }),
                      isSelected && styles.monthChipSelected,
                      isSelected && isLight && { backgroundColor: colors.primary, borderColor: colors.primary },
                    ]}
                  >
                    <Text style={[styles.monthChipText, { color: isSelected ? '#fff' : (isLight ? '#334155' : '#e2e8f0') }]}>
                      {label}
                    </Text>
                  </TouchableOpacity>
                );
              })}
            </ScrollView>
          </View>
          <ScrollView
            style={styles.listScroll}
            contentContainerStyle={styles.listContent}
            showsVerticalScrollIndicator={true}
          >
            {monthList.length === 0 && (
              <Text style={[styles.empty, { color: colors.textSecondary }]}>{t('home.nakshatra.noData', 'No nakshatra data for this month.')}</Text>
            )}
            {monthList.map((p, i) => (
              <View
                key={`${p.nakshatra}-${p.start_date}-${i}`}
                style={[styles.periodRow, { backgroundColor: rowBg, borderColor: rowBorder }]}
              >
                <Text style={[styles.periodName, { color: colors.text }]}>{p.nakshatra}</Text>
                <Text style={[styles.periodMeta, { color: colors.textSecondary }]}>
                  {t('home.nakshatra.begins', 'Begins')} {formatDateOrdinal(p.start_date)}{p.start_time ? ` ${t('home.nakshatra.at', 'at')} ${p.start_time}` : ''}
                </Text>
                <Text style={[styles.periodMeta, { color: colors.textTertiary }]}>
                  {t('home.nakshatra.ends', 'Ends')} {formatDateOrdinal(p.end_date)}{p.end_time ? ` ${t('home.nakshatra.at', 'at')} ${p.end_time}` : ''}
                </Text>
              </View>
            ))}
          </ScrollView>
        </>
      )}

      <Modal visible={yearPickerVisible} transparent animationType="fade" onRequestClose={() => setYearPickerVisible(false)}>
        <TouchableOpacity style={styles.yearPickerOverlay} activeOpacity={1} onPress={() => setYearPickerVisible(false)}>
          <View style={styles.yearPickerCenter}>
            <TouchableOpacity activeOpacity={1} onPress={(e) => e.stopPropagation()} style={[styles.yearPickerBox, { backgroundColor: yearPickerBg, borderColor: yearPickerBorder }]}>
              <Text style={[styles.yearPickerTitle, { color: colors.text }]}>{t('home.nakshatra.selectYear', 'Select year')}</Text>
              <ScrollView style={styles.yearPickerList} showsVerticalScrollIndicator={true}>
                {yearOptions.map((y) => (
                  <TouchableOpacity
                    key={y}
                    onPress={() => {
                      setYearPickerVisible(false);
                      loadYear(y);
                    }}
                    style={[styles.yearPickerRow, selectedYear === y && (isLight ? { backgroundColor: colors.primary + '22', borderColor: colors.primary } : { backgroundColor: 'rgba(139,92,246,0.25)', borderColor: '#8B5CF6' })]}
                  >
                    <Text style={[styles.yearPickerRowText, { color: selectedYear === y ? colors.primary : colors.text }]}>{y}</Text>
                  </TouchableOpacity>
                ))}
              </ScrollView>
            </TouchableOpacity>
          </View>
        </TouchableOpacity>
      </Modal>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 14,
    borderBottomWidth: 1,
  },
  backBtn: { width: 44, height: 44, alignItems: 'center', justifyContent: 'center' },
  titleRow: { flex: 1, flexDirection: 'row', alignItems: 'center', flexWrap: 'wrap' },
  title: { fontSize: 17, fontWeight: '700' },
  yearChip: { flexDirection: 'row', alignItems: 'center', paddingVertical: 4, paddingRight: 4 },
  monthStripWrap: {
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
  },
  monthStrip: { flexDirection: 'row', alignItems: 'center' },
  monthChip: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 20,
    borderWidth: 1,
    marginRight: 8,
    minWidth: 36,
    alignItems: 'center',
    justifyContent: 'center',
  },
  monthChipSelected: { backgroundColor: '#8B5CF6', borderColor: '#8B5CF6' },
  monthChipText: { fontSize: 12, fontWeight: '600' },
  listScroll: { flex: 1 },
  listContent: { paddingHorizontal: 20, paddingVertical: 16, paddingBottom: 32 },
  centered: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: 24 },
  empty: { textAlign: 'center', fontSize: 14 },
  loadingText: { marginTop: 12, fontSize: 14 },
  periodRow: {
    paddingVertical: 14,
    paddingHorizontal: 14,
    marginBottom: 10,
    borderRadius: 12,
    borderWidth: 1,
  },
  periodName: { fontSize: 16, fontWeight: '600', marginBottom: 6 },
  periodMeta: { fontSize: 13, marginBottom: 2 },
  yearPickerOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  yearPickerCenter: { width: '100%', alignItems: 'center', padding: 20 },
  yearPickerBox: {
    width: '100%',
    maxWidth: 280,
    borderRadius: 16,
    borderWidth: 1,
    padding: 20,
  },
  yearPickerTitle: { fontSize: 17, fontWeight: '700', marginBottom: 12 },
  yearPickerList: { maxHeight: Math.min(WINDOW_HEIGHT * 0.5, 320) },
  yearPickerRow: {
    paddingVertical: 14,
    paddingHorizontal: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: 'transparent',
    marginBottom: 6,
  },
  yearPickerRowText: { fontSize: 16, fontWeight: '600' },
});
