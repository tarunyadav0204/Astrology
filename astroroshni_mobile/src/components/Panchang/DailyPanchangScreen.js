import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
  StatusBar,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../../context/ThemeContext';
import { panchangAPI } from '../../services/api';
import { storage } from '../../services/storage';
import DateNavigator from '../Common/DateNavigator';

const toDateKey = (d) => {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
};

const parseDateKey = (value) => {
  if (!value || typeof value !== 'string') return new Date();
  const [y, m, d] = value.split('-').map(Number);
  if (!y || !m || !d) return new Date();
  return new Date(y, m - 1, d);
};

const formatClock = (value) => {
  if (!value) return '—';
  // Accept ISO or "05:31 AM" / "05:31"
  if (typeof value === 'string' && /^\d{1,2}:\d{2}/.test(value) && !value.includes('T')) {
    return value;
  }
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return String(value);
  return d.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true });
};

const isActiveRange = (start, end) => {
  if (!start || !end) return false;
  const now = Date.now();
  const a = new Date(start).getTime();
  const b = new Date(end).getTime();
  if (Number.isNaN(a) || Number.isNaN(b)) return false;
  return now >= a && now <= b;
};

function PeriodRow({ label, start, end, tone, colors, isDark }) {
  const active = isActiveRange(start, end);
  const toneColor = tone === 'caution' ? '#EF4444' : tone === 'good' ? '#10B981' : colors.primary;
  return (
    <View
      style={[
        styles.periodRow,
        {
          backgroundColor: isDark ? 'rgba(255,255,255,0.06)' : '#fffbf7',
          borderColor: active ? toneColor + '55' : isDark ? 'rgba(255,255,255,0.08)' : 'rgba(234,88,12,0.16)',
        },
      ]}
    >
      <View style={{ flex: 1, minWidth: 0 }}>
        <Text style={[styles.periodLabel, { color: colors.text }]} numberOfLines={1}>
          {label}
          {active ? ' · now' : ''}
        </Text>
        <Text style={[styles.periodTime, { color: toneColor }]}>
          {formatClock(start)} – {formatClock(end)}
        </Text>
      </View>
    </View>
  );
}

export default function DailyPanchangScreen({ navigation, route }) {
  const { theme, colors } = useTheme();
  const isDark = theme === 'dark';
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const [payload, setPayload] = useState(null);
  const [selectedDate, setSelectedDate] = useState(() =>
    parseDateKey(route?.params?.date)
  );

  const coords = useMemo(() => {
    const p = route?.params || {};
    return {
      latitude: Number(p.latitude) || 28.6139,
      longitude: Number(p.longitude) || 77.2090,
      placeLabel: p.placeLabel || 'New Delhi',
    };
  }, [route?.params]);

  const dateKey = useMemo(() => toDateKey(selectedDate), [selectedDate]);

  const load = useCallback(async () => {
    setError(null);
    try {
      let lat = coords.latitude;
      let lon = coords.longitude;
      let placeLabel = coords.placeLabel;
      try {
        const birth = await storage.getBirthData();
        if (birth?.latitude != null && birth?.longitude != null) {
          lat = Number(birth.latitude);
          lon = Number(birth.longitude);
          placeLabel = birth.place || birth.name || placeLabel;
        }
      } catch (_) {
        /* keep defaults */
      }

      const date = dateKey;
      const [daily, chog, hora, special, ina] = await Promise.all([
        panchangAPI.calculateDailyPanchang(date, lat, lon),
        panchangAPI.calculateChoghadiya(date, lat, lon),
        panchangAPI.calculateHora(date, lat, lon),
        panchangAPI.calculateSpecialMuhurtas(date, lat, lon),
        panchangAPI.calculateInauspiciousTimes(date, lat, lon),
      ]);

      setPayload({
        placeLabel,
        date,
        daily: daily?.data || daily,
        choghadiya: chog?.data || chog,
        hora: hora?.data || hora,
        special: special?.data || special,
        inauspicious: ina?.data || ina,
      });
    } catch (e) {
      setError(e?.message || 'Failed to load panchang');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [coords, dateKey]);

  useEffect(() => {
    setLoading(true);
    load();
  }, [load]);

  const handleDateChange = useCallback((nextDate) => {
    setSelectedDate(nextDate);
  }, []);

  const basic = payload?.daily?.basic_panchang;
  const sun = payload?.daily?.sunrise_sunset;
  const specialTimes = payload?.daily?.special_times || {};
  const dayContext = payload?.daily?.day_context;
  const dayChog = payload?.choghadiya?.day_choghadiya || [];
  const nightChog = payload?.choghadiya?.night_choghadiya || [];
  const dayHora = payload?.hora?.day_horas || [];
  const amrit = payload?.inauspicious?.amrit_kalam || specialTimes.amrit_kalam || [];
  const specialMuhurtas = (() => {
    const s = payload?.special;
    if (!s) return [];
    if (Array.isArray(s.muhurtas) && s.muhurtas.length) return s.muhurtas;
    const out = [];
    if (s.brahma_muhurta) {
      out.push({
        name: 'Brahma Muhurta',
        start_time: s.brahma_muhurta.start_time,
        end_time: s.brahma_muhurta.end_time,
      });
    }
    if (s.abhijit_muhurta) {
      out.push({
        name: 'Abhijit Muhurta',
        start_time: s.abhijit_muhurta.start_time,
        end_time: s.abhijit_muhurta.end_time,
      });
    }
    return out;
  })();

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      <StatusBar barStyle={colors.statusBarStyle} backgroundColor={colors.background} />
      <SafeAreaView style={styles.safe} edges={['top']}>
        <View style={[styles.header, { borderBottomColor: isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.06)' }]}>
          <TouchableOpacity
            onPress={() => navigation.goBack()}
            style={[styles.backBtn, { backgroundColor: isDark ? 'rgba(255,255,255,0.12)' : 'rgba(24, 24, 27, 0.08)' }]}
          >
            <Ionicons name="arrow-back" size={20} color={colors.text} />
          </TouchableOpacity>
          <View style={styles.headerCenter}>
            <Text style={[styles.title, { color: colors.text }]}>Daily Panchang</Text>
            <Text style={[styles.subtitle, { color: colors.textSecondary }]} numberOfLines={1}>
              {payload?.placeLabel || coords.placeLabel}
            </Text>
          </View>
          <View style={styles.headerSpacer} />
        </View>

        <View style={styles.dateNavWrap}>
          <DateNavigator
            date={selectedDate}
            onDateChange={handleDateChange}
            cosmicTheme={isDark}
            resetDate={new Date()}
          />
        </View>

        {loading ? (
          <View style={styles.centered}>
            <ActivityIndicator color={colors.primary} />
          </View>
        ) : error ? (
          <View style={styles.centered}>
            <Text style={{ color: colors.text, marginBottom: 12 }}>{error}</Text>
            <TouchableOpacity onPress={load}>
              <Text style={{ color: colors.primary, fontWeight: '700' }}>Retry</Text>
            </TouchableOpacity>
          </View>
        ) : (
          <ScrollView
            contentContainerStyle={styles.scroll}
            refreshControl={
              <RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); load(); }} tintColor={colors.primary} />
            }
          >
            <View style={[styles.card, { backgroundColor: isDark ? 'rgba(255,255,255,0.05)' : '#fff', borderColor: isDark ? 'rgba(255,255,255,0.08)' : 'rgba(234,88,12,0.16)' }]}>
              <Text style={[styles.sectionTitle, { color: colors.text }]}>Sun</Text>
              <Text style={[styles.meta, { color: colors.textSecondary }]}>
                Sunrise {sun?.sunrise || '—'} · Sunset {sun?.sunset || '—'}
              </Text>
              {dayContext ? (
                <Text style={[styles.meta, { color: colors.textSecondary, marginTop: 6 }]}>
                  {dayContext.ritu} · {dayContext.ayana}
                  {dayContext.chandra_balam?.status ? ` · Chandra ${dayContext.chandra_balam.status}` : ''}
                </Text>
              ) : null}
            </View>

            <View style={[styles.card, { backgroundColor: isDark ? 'rgba(255,255,255,0.05)' : '#fff', borderColor: isDark ? 'rgba(255,255,255,0.08)' : 'rgba(234,88,12,0.16)' }]}>
              <Text style={[styles.sectionTitle, { color: colors.text }]}>Elements</Text>
              {[
                ['Tithi', basic?.tithi?.name],
                ['Nakshatra', basic?.nakshatra?.name],
                ['Yoga', basic?.yoga?.name],
                ['Karana', basic?.karana?.name],
                ['Vara', basic?.vara?.name],
              ].map(([k, v]) => (
                <View key={k} style={styles.elementRow}>
                  <Text style={[styles.elementKey, { color: colors.textSecondary }]}>{k}</Text>
                  <Text style={[styles.elementVal, { color: colors.text }]}>{v || '—'}</Text>
                </View>
              ))}
            </View>

            <Text style={[styles.blockTitle, { color: colors.text }]}>Auspicious</Text>
            {(Array.isArray(amrit) ? amrit : amrit?.start ? [amrit] : []).map((p, i) => (
              <PeriodRow
                key={`amrit-${i}`}
                label="Amrit Kalam"
                start={p.start_time || p.start}
                end={p.end_time || p.end}
                tone="good"
                colors={colors}
                isDark={isDark}
              />
            ))}
            {specialTimes.abhijit ? (
              <PeriodRow
                label="Abhijit"
                start={`${payload.date} ${specialTimes.abhijit.start}`}
                end={`${payload.date} ${specialTimes.abhijit.end}`}
                tone="good"
                colors={colors}
                isDark={isDark}
              />
            ) : null}
            {(specialMuhurtas || []).map((m, i) => (
              <PeriodRow
                key={`muh-${i}`}
                label={m.name}
                start={m.start_time}
                end={m.end_time}
                tone="good"
                colors={colors}
                isDark={isDark}
              />
            ))}

            <Text style={[styles.blockTitle, { color: colors.text }]}>Inauspicious</Text>
            {payload?.inauspicious?.rahu_kaal ? (
              <PeriodRow
                label="Rahu Kaal"
                start={payload.inauspicious.rahu_kaal.start_time}
                end={payload.inauspicious.rahu_kaal.end_time}
                tone="caution"
                colors={colors}
                isDark={isDark}
              />
            ) : null}
            {(payload?.inauspicious?.dur_muhurta || []).map((p, i) => (
              <PeriodRow
                key={`dur-${i}`}
                label={`Dur Muhurta ${i + 1}`}
                start={p.start_time}
                end={p.end_time}
                tone="caution"
                colors={colors}
                isDark={isDark}
              />
            ))}
            {(payload?.inauspicious?.varjyam || []).map((p, i) => (
              <PeriodRow
                key={`var-${i}`}
                label="Varjyam"
                start={p.start_time}
                end={p.end_time}
                tone="caution"
                colors={colors}
                isDark={isDark}
              />
            ))}

            <Text style={[styles.blockTitle, { color: colors.text }]}>Day Choghadiya</Text>
            {dayChog.map((p, i) => (
              <PeriodRow
                key={`dc-${i}`}
                label={`${p.name} (${p.quality})`}
                start={p.start_time}
                end={p.end_time}
                tone={['Good', 'Gain', 'Best', 'Movable'].includes(p.quality) ? 'good' : 'caution'}
                colors={colors}
                isDark={isDark}
              />
            ))}

            <Text style={[styles.blockTitle, { color: colors.text }]}>Night Choghadiya</Text>
            {nightChog.slice(0, 4).map((p, i) => (
              <PeriodRow
                key={`nc-${i}`}
                label={`${p.name} (${p.quality})`}
                start={p.start_time}
                end={p.end_time}
                tone={['Good', 'Gain', 'Best', 'Movable'].includes(p.quality) ? 'good' : 'caution'}
                colors={colors}
                isDark={isDark}
              />
            ))}

            <Text style={[styles.blockTitle, { color: colors.text }]}>Day Hora</Text>
            {dayHora.map((p, i) => (
              <PeriodRow
                key={`h-${i}`}
                label={p.planet}
                start={p.start_time}
                end={p.end_time}
                tone="neutral"
                colors={colors}
                isDark={isDark}
              />
            ))}

            <TouchableOpacity
              style={[styles.secondaryBtn, { borderColor: colors.primary }]}
              onPress={() => navigation.navigate('MuhuratHub')}
            >
              <Text style={{ color: colors.primary, fontWeight: '700' }}>Open event muhurat planners</Text>
            </TouchableOpacity>
          </ScrollView>
        )}
      </SafeAreaView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  safe: { flex: 1 },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderBottomWidth: StyleSheet.hairlineWidth,
    gap: 8,
  },
  backBtn: {
    width: 36,
    height: 36,
    borderRadius: 18,
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerCenter: { flex: 1, minWidth: 0, alignItems: 'center' },
  headerSpacer: { width: 36 },
  dateNavWrap: { paddingHorizontal: 12, paddingTop: 8 },
  title: { fontSize: 16, fontWeight: '800' },
  subtitle: { fontSize: 11, marginTop: 2 },
  centered: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: 24 },
  scroll: { padding: 16, paddingBottom: 40 },
  card: {
    borderWidth: 1,
    borderRadius: 16,
    padding: 14,
    marginBottom: 12,
  },
  sectionTitle: { fontSize: 15, fontWeight: '800', marginBottom: 6 },
  meta: { fontSize: 13 },
  elementRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 6,
  },
  elementKey: { fontSize: 13 },
  elementVal: { fontSize: 13, fontWeight: '700' },
  blockTitle: {
    fontSize: 14,
    fontWeight: '800',
    marginTop: 8,
    marginBottom: 8,
  },
  periodRow: {
    borderWidth: 1,
    borderRadius: 12,
    paddingHorizontal: 12,
    paddingVertical: 10,
    marginBottom: 8,
  },
  periodLabel: { fontSize: 13, fontWeight: '700' },
  periodTime: { fontSize: 12, fontWeight: '700', marginTop: 2 },
  secondaryBtn: {
    marginTop: 16,
    borderWidth: 1,
    borderRadius: 12,
    paddingVertical: 12,
    alignItems: 'center',
  },
});
