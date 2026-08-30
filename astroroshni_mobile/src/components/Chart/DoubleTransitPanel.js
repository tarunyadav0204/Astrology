import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  ActivityIndicator,
  Modal,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import Ionicons from '@expo/vector-icons/Ionicons';

import { chartAPI } from '../../services/api';

const AREA_OPTIONS = [
  { key: 'all', label: 'All houses', houses: null },
  { key: 'career', label: 'Career', houses: [2, 6, 10, 11] },
  { key: 'relationship', label: 'Relationships', houses: [2, 7, 11] },
  { key: 'wealth', label: 'Wealth', houses: [2, 5, 8, 11] },
  { key: 'children', label: 'Children', houses: [2, 5, 9, 11] },
  { key: 'property', label: 'Property', houses: [4, 8, 11] },
  { key: 'health', label: 'Health', houses: [1, 6, 8, 12] },
  { key: 'education', label: 'Education', houses: [4, 5, 9] },
  { key: 'travel', label: 'Travel', houses: [3, 9, 12] },
];

const CONTACT_OPTIONS = [
  { key: 'all', label: 'Full + aspect-only' },
  { key: 'full', label: 'Full double transits' },
  { key: 'aspect_only', label: 'Aspect-only contacts' },
];

const SIGN_ABBR = {
  Aries: 'Ari', Taurus: 'Tau', Gemini: 'Gem', Cancer: 'Can',
  Leo: 'Leo', Virgo: 'Vir', Libra: 'Lib', Scorpio: 'Sco',
  Sagittarius: 'Sag', Capricorn: 'Cap', Aquarius: 'Aqu', Pisces: 'Pis',
};

const isoDay = (value) => String(value || '').slice(0, 10);

const birthYearFrom = (value) => {
  const match = String(value || '').match(/^(\d{4})-(\d{2})-(\d{2})/);
  if (!match) return null;
  const year = Number(match[1]);
  return Number.isInteger(year) && year >= 1 ? year : null;
};

const formatMoment = (value) => {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return { date: String(value || '—'), time: '' };
  return {
    date: date.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }),
    time: date.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }),
  };
};

const formatDuration = (days) => {
  const count = Number(days);
  if (!Number.isFinite(count)) return '';
  if (count >= 365) return `${(count / 365.2425).toFixed(1)} years`;
  if (count >= 60) return `${Math.round(count / 30.44)} months`;
  return `${Math.max(1, Math.round(count))} days`;
};

const ordinal = (value) => {
  const number = Number(value);
  if (number % 100 >= 11 && number % 100 <= 13) return `${number}th`;
  return `${number}${number % 10 === 1 ? 'st' : number % 10 === 2 ? 'nd' : number % 10 === 3 ? 'rd' : 'th'}`;
};

const windowDuration = (window) => {
  const start = Date.parse(window?.start_at);
  const end = Date.parse(window?.end_at);
  return Number.isFinite(start) && Number.isFinite(end) ? (end - start) / 86400000 : null;
};

const transitLine = (label, planet) => {
  if (!planet) return null;
  const sign = SIGN_ABBR[planet.sign_name] || planet.sign_name;
  const relation = planet.mode === 'occupies'
    ? `occupies H${planet.house}`
    : `${ordinal(planet.aspect_number)} aspect from H${planet.house}`;
  return `${label} · ${sign} · ${relation}`;
};

export default function DoubleTransitPanel({
  birthData,
  chartData,
  colors,
  ui,
  card,
  onInspectDate,
}) {
  const currentYear = new Date().getFullYear();
  const birthYear = birthYearFrom(birthData?.date);
  const chartFingerprint = [
    birthData?.date,
    chartData?.ascendant,
    ...['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']
      .map((planet) => chartData?.planets?.[planet]?.longitude),
  ].join('|');
  const [startYear, setStartYear] = useState(birthYear || currentYear);
  const [endYear, setEndYear] = useState(Math.min(currentYear + 15, (birthYear || currentYear) + 119));
  const [phase, setPhase] = useState('current');
  const [strength, setStrength] = useState('all');
  const [area, setArea] = useState('all');
  const [areaOpen, setAreaOpen] = useState(false);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const requestIdRef = useRef(0);

  const clampRange = (from, to) => {
    const nextFrom = Math.min(2399, Math.max(1800, Number(from) || currentYear));
    const nextTo = Math.min(Math.min(2399, nextFrom + 119), Math.max(nextFrom, Number(to) || nextFrom));
    return { from: nextFrom, to: nextTo };
  };

  const calculate = useCallback(async (signal, requestedRange) => {
    const requestId = ++requestIdRef.current;
    setError('');
    if (!birthYear) {
      setResult(null);
      setError('The saved chart has no valid birth date. No transit result was produced.');
      return;
    }
    if (typeof chartData?.ascendant !== 'number' || !Number.isFinite(chartData.ascendant)) {
      setResult(null);
      setError('The chart has no verified ascendant longitude. No transit result was produced.');
      return;
    }
    const { from, to } = clampRange(requestedRange?.from ?? startYear, requestedRange?.to ?? endYear);
    setStartYear(from);
    setEndYear(to);
    setResult(null);
    setLoading(true);
    try {
      const response = await chartAPI.getDoubleTransits({
        chartData,
        startDate: from === birthYear ? isoDay(birthData.date) : `${from}-01-01`,
        endDate: `${to}-12-31`,
        includeAspectOnly: true,
      });
      if (!signal?.cancelled && requestId === requestIdRef.current) setResult(response.data);
    } catch (requestError) {
      if (!signal?.cancelled && requestId === requestIdRef.current) {
        setResult(null);
        const detail = requestError?.response?.data?.detail;
        setError(typeof detail === 'string' ? detail : requestError?.message || 'The exact ephemeris calculation failed. No fallback result was produced.');
      }
    } finally {
      if (!signal?.cancelled && requestId === requestIdRef.current) setLoading(false);
    }
  }, [birthData?.date, birthYear, chartData, endYear, startYear]);

  useEffect(() => {
    const signal = { cancelled: false };
    const initialStart = birthYear || currentYear;
    const initialEnd = Math.min(currentYear + 15, initialStart + 119);
    setStartYear(initialStart);
    setEndYear(initialEnd);
    if (chartData) calculate(signal, { from: initialStart, to: initialEnd });
    return () => { signal.cancelled = true; };
  }, [chartFingerprint]);

  const windows = useMemo(() => {
    const now = new Date().toISOString();
    const houseSet = AREA_OPTIONS.find((item) => item.key === area)?.houses;
    return (result?.windows || []).filter((window) => {
      const start = window.start_at;
      const end = window.end_at;
      if (phase === 'current' && !(start <= now && end > now)) return false;
      if (phase === 'future' && start <= now) return false;
      if (phase === 'past' && end > now) return false;
      if (strength !== 'all' && window.status !== strength) return false;
      if (houseSet && !houseSet.includes(window.house)) return false;
      return true;
    }).sort((a, b) => (
      phase === 'past'
        ? String(b.start_at).localeCompare(String(a.start_at))
        : String(a.start_at).localeCompare(String(b.start_at))
    ));
  }, [area, phase, result, strength]);

  const counts = useMemo(() => {
    const now = new Date().toISOString();
    return (result?.windows || []).reduce((acc, window) => {
      const start = window.start_at;
      const end = window.end_at;
      if (start <= now && end > now) acc.current += 1;
      else if (start > now) acc.future += 1;
      else acc.past += 1;
      return acc;
    }, { current: 0, future: 0, past: 0 });
  }, [result]);

  const areaMeta = AREA_OPTIONS.find((item) => item.key === area) || AREA_OPTIONS[0];
  const contactMeta = CONTACT_OPTIONS.find((item) => item.key === strength) || CONTACT_OPTIONS[0];

  return (
    <View style={[card, styles.wrap]}>
      <Text style={[styles.eyebrow, { color: colors.primary }]}>JUPITER × SATURN</Text>
      <Text style={[styles.title, { color: colors.text }]}>Double Transit</Text>
      <Text style={[styles.intro, { color: colors.textSecondary }]}>
        Exact periods when both planets activate the same natal house. Full means at least one occupies it; aspect-only is graha dṛṣṭi without occupation.
      </Text>
      <Text style={[styles.method, { color: colors.textSecondary }]}>Lahiri · whole sign · Swiss Ephemeris · 1-second ingress</Text>

      <View style={styles.yearRow}>
        <TouchableOpacity
          onPress={() => setStartYear((year) => Math.max(1800, year - 1))}
          style={[styles.yearButton, { backgroundColor: ui.surfaceMuted }]}
        >
          <Ionicons name="remove" size={18} color={colors.text} />
        </TouchableOpacity>
        <View style={styles.yearCopy}>
          <Text style={[styles.fieldLabel, { color: colors.textSecondary }]}>FROM YEAR</Text>
          <Text style={[styles.yearValue, { color: colors.text }]}>{startYear}</Text>
        </View>
        <TouchableOpacity
          onPress={() => {
            const next = Math.min(2399, startYear + 1);
            setStartYear(next);
            setEndYear((previous) => Math.min(Math.max(previous, next), Math.min(2399, next + 119)));
          }}
          style={[styles.yearButton, { backgroundColor: ui.surfaceMuted }]}
        >
          <Ionicons name="add" size={18} color={colors.text} />
        </TouchableOpacity>
      </View>

      <View style={styles.yearRow}>
        <TouchableOpacity
          onPress={() => setEndYear((year) => Math.max(startYear, year - 1))}
          style={[styles.yearButton, { backgroundColor: ui.surfaceMuted }]}
        >
          <Ionicons name="remove" size={18} color={colors.text} />
        </TouchableOpacity>
        <View style={styles.yearCopy}>
          <Text style={[styles.fieldLabel, { color: colors.textSecondary }]}>THROUGH YEAR</Text>
          <Text style={[styles.yearValue, { color: colors.text }]}>{endYear}</Text>
        </View>
        <TouchableOpacity
          onPress={() => setEndYear((year) => Math.min(Math.min(2399, startYear + 119), year + 1))}
          style={[styles.yearButton, { backgroundColor: ui.surfaceMuted }]}
        >
          <Ionicons name="add" size={18} color={colors.text} />
        </TouchableOpacity>
      </View>

      <TouchableOpacity
        onPress={() => calculate()}
        disabled={loading}
        style={[styles.runButton, { backgroundColor: colors.primary, opacity: loading ? 0.55 : 1 }]}
      >
        {loading
          ? <ActivityIndicator color="#fff" />
          : <Text style={styles.runButtonText}>Calculate exact windows</Text>}
      </TouchableOpacity>

      {error ? (
        <View style={styles.state}>
          <Ionicons name="alert-circle-outline" size={28} color={colors.error} />
          <Text style={[styles.stateTitle, { color: colors.text }]}>Double transit unavailable</Text>
          <Text style={[styles.stateText, { color: colors.textSecondary }]}>{error}</Text>
          <TouchableOpacity onPress={() => calculate()} style={[styles.runButton, { backgroundColor: colors.primary, marginTop: 4 }]}>
            <Text style={styles.runButtonText}>Retry exact calculation</Text>
          </TouchableOpacity>
        </View>
      ) : null}

      {loading ? (
        <View style={styles.state}>
          <ActivityIndicator size="large" color={colors.primary} />
          <Text style={[styles.stateTitle, { color: colors.text }]}>Computing exact intervals</Text>
          <Text style={[styles.stateText, { color: colors.textSecondary }]}>Solving Jupiter and Saturn sign ingresses for {startYear}–{endYear}.</Text>
        </View>
      ) : null}

      {!loading && result ? (
        <View style={styles.results}>
          <View style={[styles.phaseRow, { backgroundColor: ui.surfaceMuted, borderColor: ui.border }]}>
            {[
              ['current', 'Current', counts.current],
              ['future', 'Future', counts.future],
              ['past', 'Past', counts.past],
            ].map(([id, label, count]) => (
              <TouchableOpacity
                key={id}
                onPress={() => setPhase(id)}
                style={[styles.phaseTab, phase === id && { backgroundColor: colors.selectionSurface }]}
              >
                <Text style={[styles.phaseText, { color: phase === id ? colors.selectionText : colors.textSecondary }]}>
                  {label} {count}
                </Text>
              </TouchableOpacity>
            ))}
          </View>

          <View style={styles.filterRow}>
            {CONTACT_OPTIONS.map((item) => {
              const active = item.key === strength;
              return (
                <TouchableOpacity
                  key={item.key}
                  onPress={() => setStrength(item.key)}
                  style={[
                    styles.filterChip,
                    {
                      borderColor: active ? colors.selectionBorder : ui.border,
                      backgroundColor: active ? colors.selectionSurface : ui.surfaceMuted,
                    },
                  ]}
                >
                  <Text style={[styles.filterChipText, { color: active ? colors.selectionText : colors.textSecondary }]}>
                    {item.key === 'all' ? 'All contacts' : item.key === 'full' ? 'Full' : 'Aspect-only'}
                  </Text>
                </TouchableOpacity>
              );
            })}
          </View>

          <Text style={[styles.fieldLabel, { color: colors.textSecondary }]}>LIFE AREA</Text>
          <TouchableOpacity
            onPress={() => setAreaOpen(true)}
            style={[styles.selector, { borderColor: ui.border, backgroundColor: ui.surfaceMuted }]}
          >
            <Text style={[styles.selectorValue, { color: colors.text }]}>{areaMeta.label}</Text>
            <Ionicons name="chevron-down" size={18} color={colors.textSecondary} />
          </TouchableOpacity>
          <Text style={[styles.meta, { color: colors.textSecondary }]}>{windows.length} shown · {contactMeta.label}</Text>

          <Text style={[styles.definition, { color: colors.textSecondary }]}>
            Start is inclusive; until is exclusive. Times use this device’s timezone. This is a transit condition, not a guaranteed event.
          </Text>

          {windows.length ? windows.map((window) => {
            const natal = window.natal || {};
            const occupants = natal.occupants?.length ? natal.occupants.join(', ') : 'none';
            const starts = formatMoment(window.start_at);
            const until = formatMoment(window.end_at);
            const full = window.status === 'full';
            return (
              <View
                key={window.id}
                style={[
                  styles.windowCard,
                  { borderColor: ui.border, borderLeftColor: full ? colors.primary : colors.cosmicGlow },
                ]}
              >
                <View style={styles.windowHeading}>
                  <View style={{ flex: 1 }}>
                    <Text style={[styles.strength, { color: full ? colors.primary : colors.cosmicGlow }]}>
                      {full ? 'Full double transit' : 'Aspect-only contact'}
                    </Text>
                    <Text style={[styles.windowDates, { color: colors.text }]}>{starts.date} – {until.date}</Text>
                    <Text style={[styles.meta, { color: colors.textSecondary }]}>
                      {starts.time} → {until.time} · {formatDuration(windowDuration(window))}
                    </Text>
                  </View>
                  <View style={[styles.houseBadge, { backgroundColor: ui.surfaceMuted }]}>
                    <Text style={[styles.houseBadgeText, { color: colors.text }]}>H{window.house}</Text>
                  </View>
                </View>
                <Text style={[styles.windowTitle, { color: colors.text }]}>{window.house_title}</Text>
                <Text style={[styles.meta, { color: colors.textSecondary }]}>{window.themes}</Text>
                <Text style={[styles.meta, { color: colors.text }]}>{transitLine('Jupiter', window.jupiter)}</Text>
                <Text style={[styles.meta, { color: colors.text }]}>{transitLine('Saturn', window.saturn)}</Text>
                <Text style={[styles.summary, { color: colors.textSecondary }]}>{window.activation_summary}</Text>
                <Text style={[styles.meta, { color: colors.textSecondary }]}>
                  Natal H{window.house} · {natal.sign_name} · lord {natal.lord} · occupants {occupants}
                </Text>
                <Text style={[styles.rule, { color: colors.textSecondary }]}>{window.manifestation_rule}</Text>
                <TouchableOpacity
                  onPress={() => onInspectDate?.(isoDay(window.start_at))}
                  style={styles.linkRow}
                >
                  <Text style={[styles.link, { color: colors.primary }]}>Set as-of · {starts.date}</Text>
                </TouchableOpacity>
              </View>
            );
          }) : (
            <Text style={[styles.stateText, { color: colors.textSecondary, textAlign: 'left' }]}>
              The exact calculation found no window for these filters and dates.
            </Text>
          )}
        </View>
      ) : null}

      <Modal visible={areaOpen} transparent animationType="slide" onRequestClose={() => setAreaOpen(false)}>
        <View style={styles.modalBackdrop}>
          <View style={[styles.sheet, { backgroundColor: colors.surfaceRaised }]}>
            <View style={styles.sheetHeader}>
              <Text style={[styles.title, { color: colors.text }]}>Life area</Text>
              <TouchableOpacity onPress={() => setAreaOpen(false)} accessibilityLabel="Close">
                <Ionicons name="close" size={24} color={colors.text} />
              </TouchableOpacity>
            </View>
            <ScrollView>
              {AREA_OPTIONS.map((item) => {
                const active = item.key === area;
                return (
                  <TouchableOpacity
                    key={item.key}
                    onPress={() => {
                      setArea(item.key);
                      setAreaOpen(false);
                    }}
                    style={[
                      styles.option,
                      {
                        borderColor: active ? colors.selectionBorder : ui.border,
                        backgroundColor: active ? colors.selectionSurface : ui.surfaceMuted,
                      },
                    ]}
                  >
                    <Text style={[styles.windowTitle, { color: active ? colors.selectionText : colors.text }]}>{item.label}</Text>
                    <Text style={[styles.meta, { color: active ? colors.selectionText : colors.textSecondary }]}>
                      {item.houses ? item.houses.map((house) => `H${house}`).join(' · ') : 'Every natal house'}
                    </Text>
                  </TouchableOpacity>
                );
              })}
            </ScrollView>
          </View>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { gap: 10 },
  eyebrow: { fontSize: 10, lineHeight: 14, fontWeight: '700', letterSpacing: 1.1 },
  title: { fontSize: 21, lineHeight: 27, fontWeight: '700', letterSpacing: -0.35 },
  intro: { fontSize: 14, lineHeight: 21 },
  method: { fontSize: 12, lineHeight: 18 },
  fieldLabel: { fontSize: 10, lineHeight: 14, fontWeight: '700', letterSpacing: 1.1, marginTop: 8 },
  yearRow: { flexDirection: 'row', alignItems: 'center', gap: 12, marginTop: 6 },
  yearButton: { width: 40, height: 40, borderRadius: 20, alignItems: 'center', justifyContent: 'center' },
  yearCopy: { flex: 1, alignItems: 'center' },
  yearValue: { fontSize: 20, fontWeight: '700' },
  runButton: { borderRadius: 22, minHeight: 46, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 18 },
  runButtonText: { color: '#fff', fontSize: 14, fontWeight: '700' },
  state: { alignItems: 'center', paddingVertical: 18, gap: 8 },
  stateTitle: { fontSize: 16, fontWeight: '700', textAlign: 'center' },
  stateText: { fontSize: 13, lineHeight: 19, textAlign: 'center' },
  results: { gap: 12, marginTop: 8 },
  phaseRow: { flexDirection: 'row', gap: 6, padding: 5, borderWidth: 1, borderRadius: 17 },
  phaseTab: { flex: 1, minHeight: 40, borderRadius: 13, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 4 },
  phaseText: { fontSize: 11, lineHeight: 15, fontWeight: '700', textAlign: 'center' },
  filterRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  filterChip: { borderWidth: 1, borderRadius: 999, paddingHorizontal: 12, paddingVertical: 8 },
  filterChipText: { fontSize: 12, fontWeight: '700' },
  selector: {
    minHeight: 48,
    borderWidth: 1,
    borderRadius: 16,
    paddingHorizontal: 14,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  selectorValue: { fontSize: 16, fontWeight: '700' },
  definition: { fontSize: 12, lineHeight: 18 },
  meta: { fontSize: 13, lineHeight: 18 },
  windowCard: { borderWidth: 1, borderLeftWidth: 4, borderRadius: 16, padding: 14, gap: 6 },
  windowHeading: { flexDirection: 'row', alignItems: 'flex-start', gap: 10 },
  strength: { fontSize: 11, fontWeight: '800' },
  windowDates: { fontSize: 16, fontWeight: '700', marginTop: 2 },
  houseBadge: { minWidth: 42, minHeight: 32, borderRadius: 10, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 8 },
  houseBadgeText: { fontSize: 13, fontWeight: '800' },
  windowTitle: { fontSize: 15, fontWeight: '700' },
  summary: { fontSize: 13, lineHeight: 19, marginTop: 2 },
  rule: { fontSize: 12, lineHeight: 18, marginTop: 2 },
  linkRow: { minHeight: 36, justifyContent: 'center' },
  link: { fontSize: 13, fontWeight: '700' },
  modalBackdrop: { flex: 1, backgroundColor: 'rgba(20,10,28,0.45)', justifyContent: 'flex-end' },
  sheet: { maxHeight: '82%', borderTopLeftRadius: 22, borderTopRightRadius: 22, padding: 18 },
  sheetHeader: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 },
  option: { borderWidth: 1, borderRadius: 14, padding: 12, gap: 4, marginBottom: 8 },
});
