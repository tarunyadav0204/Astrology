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
import { SafeAreaView } from 'react-native-safe-area-context';
import Icon from '@expo/vector-icons/Ionicons';
import { chartAPI } from '../../services/api';
import { useTheme } from '../../context/ThemeContext';
import { useTranslation } from 'react-i18next';

const MONTH_NAMES = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
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

export default function SadeSatiScreen({ navigation, route }) {
  const { t } = useTranslation();
  const { theme, colors } = useTheme();
  const birthData = route.params?.birthData || null;
  const [periods, setPeriods] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!birthData) {
      setLoading(false);
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const formatted = {
          name: birthData.name,
          date: typeof birthData.date === 'string' ? birthData.date.split('T')[0] : birthData.date,
          time: typeof birthData.time === 'string' ? birthData.time.split('T')[1]?.slice(0, 5) || birthData.time : birthData.time,
          latitude: parseFloat(birthData.latitude) || 0,
          longitude: parseFloat(birthData.longitude) || 0,
          place: birthData.place || '',
        };
        const res = await chartAPI.getSadeSatiPeriods(formatted);
        if (!cancelled) setPeriods(res?.data?.periods || []);
      } catch (e) {
        if (!cancelled) {
          Alert.alert(t('common.error', 'Error'), t('home.sadeSati.loadError', 'Could not load Sade Sati periods.'));
          setPeriods([]);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [birthData, t]);

  const isLight = theme === 'light';
  const headerBg = isLight ? colors.cardBackground : 'rgba(15,23,42,0.98)';
  const screenBg = isLight ? colors.background : '#0f172a';
  const rowBg = isLight ? '#f8fafc' : 'rgba(255,255,255,0.05)';
  const rowBorder = isLight ? colors.cardBorder : 'rgba(148,163,184,0.2)';

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: screenBg }]} edges={['top']}>
      <View style={[styles.header, { backgroundColor: headerBg, borderBottomColor: rowBorder }]}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}>
          <Icon name="arrow-back" size={24} color={colors.text} />
        </TouchableOpacity>
        <Text style={[styles.title, { color: colors.text }]} numberOfLines={1}>
          {t('home.sadeSati.title', 'Sade Sati Periods')}
        </Text>
        <View style={styles.backBtn} />
      </View>
      {loading ? (
        <View style={styles.loadingWrap}>
          <ActivityIndicator size="large" color={colors.primary} />
          <Text style={[styles.loadingText, { color: colors.textSecondary }]}>{t('home.loading.ticker', 'Loading...')}</Text>
        </View>
      ) : (
        <ScrollView
          style={styles.scroll}
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={true}
        >
          {!birthData && (
            <Text style={[styles.empty, { color: colors.textSecondary }]}>{t('home.sadeSati.noBirthData', 'Birth details required.')}</Text>
          )}
          {birthData && periods.length === 0 && (
            <Text style={[styles.empty, { color: colors.textSecondary }]}>{t('home.sadeSati.noPeriods', 'No periods found.')}</Text>
          )}
          {birthData && periods.map((p, i) => (
            <View
              key={`${p.start_date}-${i}`}
              style={[
                styles.row,
                { backgroundColor: rowBg, borderColor: rowBorder },
                p.is_current && styles.rowCurrent,
              ]}
            >
              <Text style={[styles.rowDates, { color: colors.text }]}>
                {formatDateOrdinal(p.start_date)} — {formatDateOrdinal(p.end_date)}
              </Text>
              {p.is_current && (
                <View style={styles.badge}>
                  <Text style={styles.badgeText}>{t('home.ticker.active', 'Active')}</Text>
                </View>
              )}
            </View>
          ))}
        </ScrollView>
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 12,
    paddingVertical: 14,
    borderBottomWidth: 1,
  },
  backBtn: {
    width: 44,
    height: 44,
    alignItems: 'center',
    justifyContent: 'center',
  },
  title: {
    fontSize: 17,
    fontWeight: '700',
    flex: 1,
    textAlign: 'center',
  },
  loadingWrap: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
  },
  loadingText: {
    marginTop: 12,
    fontSize: 14,
  },
  scroll: {
    flex: 1,
  },
  scrollContent: {
    paddingHorizontal: 20,
    paddingVertical: 16,
    paddingBottom: 32,
  },
  empty: {
    padding: 24,
    textAlign: 'center',
    fontSize: 14,
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 14,
    paddingHorizontal: 14,
    marginBottom: 10,
    borderRadius: 12,
    borderWidth: 1,
  },
  rowCurrent: {
    borderColor: 'rgba(239, 68, 68, 0.6)',
    backgroundColor: 'rgba(239, 68, 68, 0.12)',
  },
  rowDates: {
    fontSize: 14,
    fontWeight: '600',
    flex: 1,
  },
  badge: {
    backgroundColor: '#EF4444',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  badgeText: {
    color: '#fff',
    fontSize: 11,
    fontWeight: '700',
  },
});
