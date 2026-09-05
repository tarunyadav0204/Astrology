import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Pressable,
  Modal,
  ActivityIndicator,
  Dimensions,
} from 'react-native';
import { useTranslation } from 'react-i18next';
import { useTheme } from '../../context/ThemeContext';
import { chartAPI } from '../../services/api';
import AppScrollView from '../../platform/AppScrollView';
import { DISPLAY_FONT_FAMILY } from '../../theme/tokens';
import Ionicons from '@expo/vector-icons/Ionicons';

const { height } = Dimensions.get('window');

function prettyDignity(value) {
  if (!value) return '—';
  return String(value).replace(/_/g, ' ');
}

function ChartOverviewSheet({
  visible,
  onClose,
  birthData,
  onOpenHouse,
  onOpenYogas,
}) {
  const { t } = useTranslation();
  const { theme, colors } = useTheme();
  const [overview, setOverview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!visible || !birthData) {
      setOverview(null);
      setError('');
      return undefined;
    }
    let cancelled = false;
    setLoading(true);
    setError('');
    const payload = {
      ...birthData,
      date: typeof birthData?.date === 'string' ? birthData.date.split('T')[0] : birthData?.date,
      time: typeof birthData?.time === 'string' ? birthData.time.split('T')[1]?.slice(0, 5) || birthData.time : birthData?.time,
      latitude: parseFloat(birthData?.latitude),
      longitude: parseFloat(birthData?.longitude),
    };
    chartAPI.getChartOverview(payload, 'lagna', new Date().toISOString().split('T')[0])
      .then((response) => {
        if (!cancelled) setOverview(response?.data || response);
      })
      .catch((err) => {
        if (!cancelled) {
          setOverview(null);
          setError(err?.response?.data?.detail || err.message || t('chartScreen.overview.loadError', 'Could not load chart reading'));
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [visible, birthData, t]);

  const houses = overview?.houses || [];
  const pillars = overview?.pillars || [];
  const now = overview?.now || {};
  const marks = overview?.special_marks || [];
  const sectionBg = theme === 'dark' ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.02)';

  return (
    <Modal visible={visible} transparent animationType="none" onRequestClose={onClose}>
      <View style={styles.overlay}>
        <Pressable
          style={[StyleSheet.absoluteFill, styles.backdrop]}
          onPress={onClose}
          accessibilityRole="button"
          accessibilityLabel={t('common.close', 'Close')}
        />
        <View
          style={[
            styles.sheet,
            {
              backgroundColor: colors.surfaceRaised || colors.surface,
              borderColor: colors.cardBorder,
            },
          ]}
        >
          <View style={[styles.handle, { backgroundColor: colors.borderStrong }]} />
          <View style={styles.inner}>
            <AppScrollView
              style={styles.scroll}
              contentContainerStyle={styles.scrollContent}
              showsVerticalScrollIndicator
              nestedScrollEnabled
              keyboardShouldPersistTaps="handled"
            >
              <View style={styles.header}>
                <Text style={[styles.eyebrow, { color: colors.primary }]}>
                  {t('premiumUi.common.chartOverviewEyebrow', 'CHART READING')}
                </Text>
                <Text style={[styles.title, { color: colors.text }]}>
                  {t('premiumUi.common.chartOverviewTitle', 'Read this chart')}
                </Text>
                <Text style={[styles.subtitle, { color: colors.textSecondary }]}>
                  {overview?.lagna_sign
                    ? t(`signs.${overview.lagna_sign}`, overview.lagna_sign)
                    : t('chartTypes.lagna.name', 'Lagna')}
                </Text>
              </View>

              {loading ? (
                <View style={styles.status}>
                  <ActivityIndicator color={colors.accent} />
                  <Text style={[styles.statusText, { color: colors.textSecondary }]}>
                    {t('chartScreen.overview.loading', 'Comparing the twelve houses…')}
                  </Text>
                </View>
              ) : null}
              {error ? <Text style={[styles.statusText, { color: colors.danger || '#ef4444' }]}>{error}</Text> : null}

              {overview?.summary ? (
                <View style={[styles.section, { backgroundColor: sectionBg, borderColor: colors.cardBorder }]}>
                  <Text style={[styles.sectionTitle, { color: colors.textSecondary }]}>
                    {t('chartScreen.overview.verdict', 'Verdict')}
                  </Text>
                  <Text style={[styles.body, { color: colors.text }]}>{overview.summary}</Text>
                </View>
              ) : null}

              <View style={[styles.section, { backgroundColor: sectionBg, borderColor: colors.cardBorder }]}>
                <Text style={[styles.sectionTitle, { color: colors.textSecondary }]}>
                  {t('chartScreen.overview.houses', 'Houses')}
                </Text>
                <Text style={[styles.hint, { color: colors.textSecondary }]}>
                  {t('chartScreen.overview.tapHouse', 'Tap a house for the full reading.')}
                </Text>
                <View style={styles.houseGrid}>
                  {houses.map((row) => (
                    <TouchableOpacity
                      key={row.house}
                      style={[
                        styles.houseChip,
                        { borderColor: colors.cardBorder, backgroundColor: colors.surface },
                        row.tone === 'support' && styles.houseSupport,
                        row.tone === 'pressure' && styles.housePressure,
                        row.tone === 'mixed' && styles.houseMixed,
                        row.active && { borderColor: colors.accent },
                      ]}
                      onPress={() => onOpenHouse?.(row.house)}
                      activeOpacity={0.85}
                    >
                      <Text style={[styles.houseNum, { color: colors.textSecondary }]}>H{row.house}</Text>
                      <Text style={[styles.houseSign, { color: colors.text }]} numberOfLines={1}>
                        {row.sign_name ? t(`signs.${row.sign_name}`, row.sign_name) : '—'}
                      </Text>
                      <Text style={[styles.houseLabel, { color: colors.textSecondary }]} numberOfLines={2}>
                        {row.verdict?.label || '—'}
                      </Text>
                      {row.marks?.length ? (
                        <Text style={[styles.houseMarks, { color: colors.accent }]} numberOfLines={1}>
                          {row.marks.join(' · ')}
                        </Text>
                      ) : null}
                    </TouchableOpacity>
                  ))}
                </View>
              </View>

              {pillars.length ? (
                <View style={[styles.section, { backgroundColor: sectionBg, borderColor: colors.cardBorder }]}>
                  <Text style={[styles.sectionTitle, { color: colors.textSecondary }]}>
                    {t('chartScreen.overview.pillars', 'Pillars')}
                  </Text>
                  {pillars.map((row) => (
                    <TouchableOpacity
                      key={`${row.role}-${row.planet}`}
                      style={[styles.pillar, { borderColor: colors.cardBorder, backgroundColor: colors.surface }]}
                      onPress={() => row.house && onOpenHouse?.(row.house)}
                      activeOpacity={0.85}
                    >
                      <Text style={[styles.houseNum, { color: colors.textSecondary }]}>{row.role}</Text>
                      <Text style={[styles.pillarPlanet, { color: colors.text }]}>
                        {t(`home.planet_names.${row.planet}`, row.planet)}
                      </Text>
                      <Text style={[styles.houseLabel, { color: colors.textSecondary }]}>
                        {[
                          row.sign_name ? t(`signs.${row.sign_name}`, row.sign_name) : null,
                          row.house != null ? `H${row.house}` : null,
                          prettyDignity(row.dignity),
                        ].filter(Boolean).join(' · ')}
                      </Text>
                      <Text style={[styles.houseLabel, { color: colors.textSecondary }]}>
                        {row.shadbala_rupas != null
                          ? `${row.shadbala_rupas} / ${row.required_rupas ?? '—'} rupas`
                          : ''}
                        {row.meets_minimum === false ? ' · below' : row.meets_minimum ? ' · meets' : ''}
                      </Text>
                    </TouchableOpacity>
                  ))}
                </View>
              ) : null}

              <View style={[styles.section, { backgroundColor: sectionBg, borderColor: colors.cardBorder }]}>
                <Text style={[styles.sectionTitle, { color: colors.textSecondary }]}>
                  {t('chartScreen.overview.now', 'Now')}
                </Text>
                <Text style={[styles.body, { color: colors.text }]}>
                  {[now.mahadasha, now.antardasha].filter(Boolean).join(' / ') || '—'}
                </Text>
                {now.houses?.length ? (
                  <View style={styles.nowRow}>
                    {now.houses.map((house) => (
                      <TouchableOpacity
                        key={house}
                        style={[styles.nowChip, { borderColor: colors.cardBorder, backgroundColor: colors.surface }]}
                        onPress={() => onOpenHouse?.(house)}
                      >
                        <Text style={[styles.nowChipText, { color: colors.text }]}>H{house}</Text>
                      </TouchableOpacity>
                    ))}
                  </View>
                ) : null}
              </View>

              <View style={[styles.section, { backgroundColor: sectionBg, borderColor: colors.cardBorder }]}>
                <Text style={[styles.sectionTitle, { color: colors.textSecondary }]}>
                  {t('chartScreen.overview.marks', 'Special marks')}
                </Text>
                {marks.length ? (
                  <View style={styles.markWrap}>
                    {marks.map((item) => (
                      <TouchableOpacity
                        key={item.key}
                        style={[styles.mark, { borderColor: colors.cardBorder, backgroundColor: colors.surface }]}
                        onPress={() => item.house && onOpenHouse?.(item.house)}
                      >
                        <Text style={[styles.houseNum, { color: colors.textSecondary }]}>{item.label}</Text>
                        <Text style={[styles.markValue, { color: colors.text }]}>{item.value}</Text>
                      </TouchableOpacity>
                    ))}
                  </View>
                ) : (
                  <Text style={[styles.body, { color: colors.textSecondary }]}>
                    {t('chartScreen.overview.noMarks', 'No gandanta, mūlatrikona, or special-point hits are marked.')}
                  </Text>
                )}
              </View>

              {onOpenYogas ? (
                <TouchableOpacity
                  style={[styles.section, styles.yogaCta, { backgroundColor: sectionBg, borderColor: colors.cardBorder }]}
                  onPress={onOpenYogas}
                  activeOpacity={0.85}
                >
                  <View style={styles.yogaCtaCopy}>
                    <Text style={[styles.sectionTitle, { color: colors.textSecondary, marginBottom: 4 }]}>
                      {t('chartScreen.overview.yogas', 'Yogas')}
                    </Text>
                    <Text style={[styles.body, { color: colors.text }]}>
                      {t('chartScreen.overview.openYogas', 'Open the full categorized yoga list for this kundli.')}
                    </Text>
                  </View>
                  <Ionicons name="chevron-forward" size={22} color={colors.accent} />
                </TouchableOpacity>
              ) : null}
            </AppScrollView>
          </View>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: { flex: 1, justifyContent: 'flex-end' },
  backdrop: { backgroundColor: 'rgba(0,0,0,0.5)' },
  sheet: {
    borderTopLeftRadius: 30,
    borderTopRightRadius: 30,
    borderWidth: 1,
    borderBottomWidth: 0,
    maxHeight: height * 0.75,
    zIndex: 1,
    elevation: 24,
  },
  handle: {
    width: 40,
    height: 5,
    borderRadius: 3,
    alignSelf: 'center',
    marginTop: 12,
    marginBottom: 8,
  },
  inner: { height: height * 0.7, maxHeight: height * 0.75 },
  scroll: { flex: 1, minHeight: 0 },
  scrollContent: { paddingHorizontal: 20, paddingBottom: 28 },
  header: { marginBottom: 16 },
  eyebrow: { fontSize: 11, fontWeight: '800', letterSpacing: 1.2 },
  title: { fontFamily: DISPLAY_FONT_FAMILY, fontSize: 25, fontWeight: '700', marginTop: 4 },
  subtitle: { fontSize: 14, fontWeight: '600', marginTop: 2 },
  status: { flexDirection: 'row', alignItems: 'center', gap: 10, marginBottom: 12 },
  statusText: { fontSize: 14, lineHeight: 20 },
  section: { padding: 16, borderRadius: 18, borderWidth: 1, marginBottom: 16 },
  sectionTitle: { fontSize: 12, fontWeight: '700', letterSpacing: 1, textTransform: 'uppercase', marginBottom: 8 },
  hint: { fontSize: 13, marginBottom: 10 },
  body: { fontSize: 15, lineHeight: 22 },
  houseGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  houseChip: {
    width: '31%',
    minHeight: 78,
    borderRadius: 12,
    borderWidth: 1,
    padding: 8,
  },
  houseSupport: { backgroundColor: 'rgba(34, 197, 94, 0.12)' },
  housePressure: { backgroundColor: 'rgba(239, 68, 68, 0.12)' },
  houseMixed: { backgroundColor: 'rgba(245, 158, 11, 0.14)' },
  houseNum: { fontSize: 10, fontWeight: '800', letterSpacing: 0.4, textTransform: 'uppercase' },
  houseSign: { fontSize: 13, fontWeight: '800', marginTop: 2 },
  houseLabel: { fontSize: 11, lineHeight: 14, marginTop: 2 },
  houseMarks: { fontSize: 10, fontWeight: '700', marginTop: 4 },
  pillar: { borderWidth: 1, borderRadius: 12, padding: 12, marginBottom: 8 },
  pillarPlanet: { fontSize: 16, fontWeight: '800', marginTop: 2 },
  nowRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginTop: 10 },
  nowChip: { borderWidth: 1, borderRadius: 999, paddingHorizontal: 12, paddingVertical: 6 },
  nowChipText: { fontSize: 13, fontWeight: '700' },
  markWrap: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  mark: { borderWidth: 1, borderRadius: 999, paddingHorizontal: 10, paddingVertical: 6 },
  markValue: { fontSize: 12, fontWeight: '700' },
  yogaCta: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  yogaCtaCopy: { flex: 1 },
});

export default ChartOverviewSheet;
