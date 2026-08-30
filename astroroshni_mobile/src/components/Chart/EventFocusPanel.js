import React, { useMemo, useState } from 'react';
import {
  ActivityIndicator,
  Modal,
  ScrollView,
  StyleSheet,
  Switch,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import Ionicons from '@expo/vector-icons/Ionicons';

import { chartAPI } from '../../services/api';

const HOUSE_SHORT = {
  1: 'Self', 2: 'Wealth', 3: 'Effort', 4: 'Home',
  5: 'Creativity', 6: 'Service', 7: 'Partnership', 8: 'Change',
  9: 'Dharma', 10: 'Career', 11: 'Gains', 12: 'Release',
};

const EVENT_GROUPS = [
  {
    label: 'Career',
    items: [
      { key: 'job_change', label: 'Job change', intro: 'Requires career plus a transition house in the same dasha. Natal wiring never vetoes the window.' },
      { key: 'promotion', label: 'Promotion / status', intro: 'Requires H10 plus H11 gain or H5 honour. This is not Job change: leaving houses are not required.' },
    ],
  },
  {
    label: 'Money',
    items: [
      { key: 'income_gain', label: 'Income / gains', intro: 'Requires both H2 and H11 dasha-opened in the same period. H5 / H9 only classify fortune or speculation.' },
    ],
  },
  {
    label: 'Health',
    items: [
      { key: 'health', label: 'Health', intro: 'Looks for health attention plus pressure, treatment or rest. This is timing only—not a diagnosis.' },
    ],
  },
  {
    label: 'Property',
    items: [
      { key: 'property_purchase', label: 'Property purchase', intro: 'Requires H4 plus a payment or financing signal (H2 savings or H8 loan).' },
      { key: 'relocation', label: 'Relocation', intro: 'Requires H4 plus a move or leaving signal (H3 or H12). Not a guaranteed move date.' },
      { key: 'property_gain', label: 'Property gain', intro: 'Requires both H4 and H11 dasha-opened so a property objective can reach fulfilment.' },
    ],
  },
  {
    label: 'Relationship',
    items: [
      { key: 'marriage', label: 'Marriage / partnership', intro: 'Requires H7 plus joining, romance or fulfilment. Relationship timing—not a wedding-date guarantee.' },
      { key: 'children', label: 'Children', intro: 'Requires H5 plus expansion or fulfilment. Not a birth prediction, fertility claim or determination of a child’s sex.' },
    ],
  },
  {
    label: 'Learning & travel',
    items: [
      { key: 'education', label: 'Education / exams', intro: 'Requires H5 plus a study path (H4 or H9). H11 classifies a result-looking window.' },
      { key: 'foreign_travel', label: 'Foreign travel / stay', intro: 'Requires H9 plus H3 papers or H12 abroad. A house move still needs Relocation (H4).' },
    ],
  },
  {
    label: 'Custom',
    items: [
      { key: 'custom', label: 'Custom', intro: 'Every selected house must be dasha-opened. Transits and exact returns only raise strength.' },
    ],
  },
];

const ALL_EVENTS = EVENT_GROUPS.flatMap((group) => group.items);
const STRENGTH_COLOR = {
  exceptional: '#7c3aed',
  strong: '#16a34a',
  developing: '#d97706',
};

const chartIdFrom = (data) => data?.chart_id || data?.birth_chart_id || data?.id || null;
const shortDate = (value) => {
  if (!value) return '—';
  const parsed = new Date(`${String(value).slice(0, 10)}T00:00:00`);
  return Number.isNaN(parsed.getTime()) ? String(value) : parsed.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });
};
const planetAbbr = (planet) => String(planet || '').slice(0, 2) || '—';

export default function EventFocusPanel({
  birthData,
  asOf,
  colors,
  ui,
  card,
  navigation,
  onInspectDate,
}) {
  const defaultYear = Number(String(asOf || '').slice(0, 4)) || new Date().getFullYear();
  const [eventKey, setEventKey] = useState('job_change');
  const [eventYear, setEventYear] = useState(defaultYear);
  const [includeDeveloping, setIncludeDeveloping] = useState(false);
  const [customHouses, setCustomHouses] = useState([]);
  const [pickerOpen, setPickerOpen] = useState(false);
  const [expandedWindow, setExpandedWindow] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [licenseRequired, setLicenseRequired] = useState(false);
  const [result, setResult] = useState(null);

  const eventMeta = useMemo(
    () => ALL_EVENTS.find((item) => item.key === eventKey) || ALL_EVENTS[0],
    [eventKey]
  );
  const customDisabled = eventKey === 'custom' && customHouses.length === 0;

  const selectEvent = (key) => {
    setEventKey(key);
    setResult(null);
    setError('');
    setLicenseRequired(false);
    setExpandedWindow(null);
    if (key === 'custom') setIncludeDeveloping(true);
    setPickerOpen(false);
  };

  const toggleHouse = (house) => {
    setCustomHouses((current) => (
      current.includes(house)
        ? current.filter((value) => value !== house)
        : [...current, house].sort((left, right) => left - right)
    ));
    setResult(null);
    setError('');
  };

  const runSearch = async () => {
    if (!birthData || loading || customDisabled) return;
    setLoading(true);
    setError('');
    setLicenseRequired(false);
    setExpandedWindow(null);
    try {
      const response = await chartAPI.getEventWindows({
        birthChartId: chartIdFrom(birthData),
        birthData,
        eventKey,
        year: eventYear,
        includeDeveloping,
        focusHouses: eventKey === 'custom' ? customHouses : null,
      });
      setResult(response.data);
    } catch (requestError) {
      setResult(null);
      const detail = requestError?.response?.data?.detail;
      if (detail?.code === 'ASTROLOGER_LICENSE_REQUIRED') {
        setLicenseRequired(true);
        setError(detail.message || 'An active Astrologer License is required for this professional tool.');
      } else {
        setError(typeof detail === 'string' ? detail : requestError?.message || 'Could not calculate event windows.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={[card, styles.wrap]}>
      <Text style={[styles.eyebrow, { color: colors.primary }]}>LIFE-EVENT SEARCH</Text>
      <Text style={[styles.title, { color: colors.text }]}>Find windows</Text>
      <Text style={[styles.intro, { color: colors.textSecondary }]}>
        Search one calendar year with the same dasha-and-confirmation rules used on the desk. A house counts only when an MD, AD or PD lord opens it.
      </Text>

      <Text style={[styles.fieldLabel, { color: colors.textSecondary }]}>LIFE EVENT</Text>
      <TouchableOpacity
        onPress={() => setPickerOpen(true)}
        style={[styles.selector, { borderColor: ui.border, backgroundColor: ui.surfaceMuted }]}
        accessibilityRole="button"
        accessibilityLabel="Choose life event"
      >
        <Text style={[styles.selectorValue, { color: colors.text }]}>{eventMeta.label}</Text>
        <Ionicons name="chevron-down" size={18} color={colors.textSecondary} />
      </TouchableOpacity>
      <Text style={[styles.intro, { color: colors.textSecondary }]}>{eventMeta.intro}</Text>

      {eventKey === 'custom' ? (
        <View style={styles.houseGrid}>
          {Array.from({ length: 12 }, (_, index) => index + 1).map((house) => {
            const selected = customHouses.includes(house);
            return (
              <TouchableOpacity
                key={house}
                onPress={() => toggleHouse(house)}
                style={[
                  styles.houseChip,
                  {
                    borderColor: selected ? colors.selectionBorder : ui.border,
                    backgroundColor: selected ? colors.selectionSurface : ui.surfaceMuted,
                  },
                ]}
                accessibilityRole="button"
                accessibilityState={{ selected }}
              >
                <Text style={[styles.houseChipTitle, { color: selected ? colors.selectionText : colors.text }]}>H{house}</Text>
                <Text style={[styles.houseChipMeta, { color: selected ? colors.selectionText : colors.textSecondary }]}>{HOUSE_SHORT[house]}</Text>
              </TouchableOpacity>
            );
          })}
        </View>
      ) : null}

      <View style={styles.yearRow}>
        <TouchableOpacity onPress={() => setEventYear((year) => Math.max(1900, year - 1))} style={[styles.yearButton, { backgroundColor: ui.surfaceMuted }]}>
          <Ionicons name="remove" size={18} color={colors.text} />
        </TouchableOpacity>
        <View style={styles.yearCopy}>
          <Text style={[styles.fieldLabel, { color: colors.textSecondary }]}>YEAR</Text>
          <Text style={[styles.yearValue, { color: colors.text }]}>{eventYear}</Text>
        </View>
        <TouchableOpacity onPress={() => setEventYear((year) => Math.min(2200, year + 1))} style={[styles.yearButton, { backgroundColor: ui.surfaceMuted }]}>
          <Ionicons name="add" size={18} color={colors.text} />
        </TouchableOpacity>
      </View>

      <View style={styles.developingRow}>
        <Switch
          value={includeDeveloping}
          onValueChange={setIncludeDeveloping}
          trackColor={{ false: ui.border, true: `${colors.primary}66` }}
          thumbColor={includeDeveloping ? colors.primary : colors.textSecondary}
        />
        <Text style={[styles.developingLabel, { color: colors.text }]}>Include developing windows</Text>
      </View>

      <TouchableOpacity
        onPress={runSearch}
        disabled={loading || customDisabled}
        style={[styles.runButton, { backgroundColor: colors.primary, opacity: loading || customDisabled ? 0.55 : 1 }]}
      >
        {loading
          ? <ActivityIndicator color="#fff" />
          : <Text style={styles.runButtonText}>{customDisabled ? 'Select at least one house' : 'Find windows'}</Text>}
      </TouchableOpacity>

      {error ? (
        <View style={styles.state}>
          <Ionicons name={licenseRequired ? 'school-outline' : 'alert-circle-outline'} size={28} color={licenseRequired ? colors.primary : colors.error} />
          <Text style={[styles.stateTitle, { color: colors.text }]}>{licenseRequired ? 'Astrologer License required' : 'Search could not finish'}</Text>
          <Text style={[styles.stateText, { color: colors.textSecondary }]}>{error}</Text>
          <TouchableOpacity
            onPress={licenseRequired
              ? () => navigation.navigate('Credits', {
                focusSubscriptionFamily: 'astrologer',
                returnTo: 'ActivationExplorer',
                returnParams: { birthData },
              })
              : runSearch}
            style={[styles.runButton, { backgroundColor: colors.primary, marginTop: 4 }]}
          >
            <Text style={styles.runButtonText}>{licenseRequired ? 'View ₹100 monthly plan' : 'Try again'}</Text>
          </TouchableOpacity>
        </View>
      ) : null}

      {loading ? (
        <View style={styles.state}>
          <ActivityIndicator size="large" color={colors.primary} />
          <Text style={[styles.stateTitle, { color: colors.text }]}>Evaluating {eventYear}</Text>
          <Text style={[styles.stateText, { color: colors.textSecondary }]}>Connecting dasha permission, house groups and independent timing confirmation.</Text>
        </View>
      ) : null}

      {!loading && result ? (
        <View style={styles.results}>
          <Text style={[styles.sectionTitle, { color: colors.text }]}>
            {result.qualified_windows} qualified {result.qualified_windows === 1 ? 'window' : 'windows'}
          </Text>
          <Text style={[styles.stateText, { color: colors.textSecondary, textAlign: 'left' }]}>
            {result.evaluated_windows} timing slices evaluated · {result.definition_version}
          </Text>
          {(result.windows || []).length ? result.windows.map((window) => {
            const open = expandedWindow === window.window_id;
            const tone = STRENGTH_COLOR[window.strength] || colors.primary;
            return (
              <View key={window.window_id} style={[styles.windowCard, { borderColor: ui.border, borderLeftColor: tone }]}>
                <View style={styles.windowHeading}>
                  <View style={{ flex: 1 }}>
                    <Text style={[styles.strength, { color: tone }]}>{String(window.strength || '').replaceAll('_', ' ')}</Text>
                    <Text style={[styles.windowDates, { color: colors.text }]}>{shortDate(window.start_date)} – {shortDate(window.end_date)}</Text>
                    <Text style={[styles.meta, { color: colors.textSecondary }]}>
                      {planetAbbr(window.dasha?.mahadasha)} → {planetAbbr(window.dasha?.antardasha)} → {planetAbbr(window.dasha?.pratyantardasha)}
                    </Text>
                  </View>
                  <Text style={[styles.score, { color: colors.text }]}>{window.score}/{window.maximum_score}</Text>
                </View>
                <Text style={[styles.windowTitle, { color: colors.text }]}>{window.classification_label}</Text>
                <Text style={[styles.meta, { color: colors.textSecondary }]}>{window.summary}</Text>
                <View style={styles.houseRow}>
                  {(window.activated_houses || []).map((house) => (
                    <Text key={house} style={[styles.houseTag, { color: colors.text, backgroundColor: ui.surfaceMuted }]}>H{house} {HOUSE_SHORT[house]}</Text>
                  ))}
                </View>
                <TouchableOpacity
                  onPress={() => onInspectDate?.(window.inspection_date || window.peak_date || window.start_date)}
                  style={styles.linkRow}
                >
                  <Text style={[styles.link, { color: colors.primary }]}>
                    Set as-of · {shortDate(window.inspection_date || window.peak_date || window.start_date)}
                  </Text>
                </TouchableOpacity>
                <TouchableOpacity onPress={() => setExpandedWindow(open ? null : window.window_id)} style={styles.linkRow}>
                  <Text style={[styles.link, { color: colors.primary }]}>{open ? 'Hide calculation' : 'Show full calculation'}</Text>
                  <Ionicons name={open ? 'chevron-up' : 'chevron-down'} size={16} color={colors.primary} />
                </TouchableOpacity>
                {open ? (
                  <View style={[styles.trace, { borderColor: ui.border }]}>
                    <Text style={[styles.meta, { color: colors.textSecondary }]}>{window.qualification_summary}</Text>
                    {(window.calculation_trace || []).map((step) => (
                      <View key={step.key} style={styles.traceStep}>
                        <View style={styles.windowHeading}>
                          <Text style={[styles.reasonTitle, { color: colors.text, flex: 1 }]}>{step.label}</Text>
                          <Text style={{ color: step.passed ? '#16a34a' : colors.textSecondary, fontSize: 11, fontWeight: '700' }}>
                            {step.passed ? 'Passed' : (step.required ? 'Required · not met' : 'Not present')}
                          </Text>
                        </View>
                        <Text style={[styles.meta, { color: colors.textSecondary }]}>+{step.score}/{step.maximum_score} · {step.description}</Text>
                      </View>
                    ))}
                  </View>
                ) : null}
              </View>
            );
          }) : (
            <Text style={[styles.stateText, { color: colors.textSecondary, textAlign: 'left' }]}>
              No qualified {String(result.event_label || eventMeta.label).toLowerCase()} window in {result.year}. The engine did not weaken the rules.
            </Text>
          )}
        </View>
      ) : null}

      <Modal visible={pickerOpen} transparent animationType="slide" onRequestClose={() => setPickerOpen(false)}>
        <View style={styles.modalBackdrop}>
          <View style={[styles.sheet, { backgroundColor: colors.surfaceRaised }]}>
            <View style={styles.sheetHeader}>
              <Text style={[styles.title, { color: colors.text }]}>Life event</Text>
              <TouchableOpacity onPress={() => setPickerOpen(false)} accessibilityLabel="Close">
                <Ionicons name="close" size={24} color={colors.text} />
              </TouchableOpacity>
            </View>
            <ScrollView>
              {EVENT_GROUPS.map((group) => (
                <View key={group.label} style={styles.group}>
                  <Text style={[styles.fieldLabel, { color: colors.textSecondary }]}>{group.label.toUpperCase()}</Text>
                  {group.items.map((item) => {
                    const active = item.key === eventKey;
                    return (
                      <TouchableOpacity
                        key={item.key}
                        onPress={() => selectEvent(item.key)}
                        style={[styles.option, { borderColor: active ? colors.selectionBorder : ui.border, backgroundColor: active ? colors.selectionSurface : ui.surfaceMuted }]}
                      >
                        <Text style={[styles.reasonTitle, { color: active ? colors.selectionText : colors.text }]}>{item.label}</Text>
                        <Text style={[styles.meta, { color: active ? colors.selectionText : colors.textSecondary }]}>{item.intro}</Text>
                      </TouchableOpacity>
                    );
                  })}
                </View>
              ))}
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
  fieldLabel: { fontSize: 10, lineHeight: 14, fontWeight: '700', letterSpacing: 1.1, marginTop: 8 },
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
  houseGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginTop: 4 },
  houseChip: { width: '31%', borderWidth: 1, borderRadius: 14, paddingVertical: 8, paddingHorizontal: 8 },
  houseChipTitle: { fontSize: 13, fontWeight: '800' },
  houseChipMeta: { fontSize: 11, marginTop: 2 },
  yearRow: { flexDirection: 'row', alignItems: 'center', gap: 12, marginTop: 6 },
  yearButton: { width: 40, height: 40, borderRadius: 20, alignItems: 'center', justifyContent: 'center' },
  yearCopy: { flex: 1, alignItems: 'center' },
  yearValue: { fontSize: 20, fontWeight: '700' },
  developingRow: { flexDirection: 'row', alignItems: 'center', gap: 10, minHeight: 44 },
  developingLabel: { fontSize: 14, fontWeight: '600', flex: 1 },
  runButton: { borderRadius: 22, minHeight: 46, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 18 },
  runButtonText: { color: '#fff', fontSize: 14, fontWeight: '700' },
  state: { alignItems: 'center', paddingVertical: 18, gap: 8 },
  stateTitle: { fontSize: 16, fontWeight: '700', textAlign: 'center' },
  stateText: { fontSize: 13, lineHeight: 19, textAlign: 'center' },
  results: { gap: 12, marginTop: 8 },
  sectionTitle: { fontSize: 18, fontWeight: '700' },
  windowCard: { borderWidth: 1, borderLeftWidth: 4, borderRadius: 16, padding: 14, gap: 6 },
  windowHeading: { flexDirection: 'row', alignItems: 'flex-start', gap: 10 },
  strength: { fontSize: 11, fontWeight: '800', textTransform: 'capitalize' },
  windowDates: { fontSize: 16, fontWeight: '700', marginTop: 2 },
  score: { fontSize: 16, fontWeight: '800' },
  windowTitle: { fontSize: 15, fontWeight: '700' },
  meta: { fontSize: 13, lineHeight: 18 },
  houseRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 6, marginTop: 4 },
  houseTag: { fontSize: 11, fontWeight: '700', overflow: 'hidden', borderRadius: 999, paddingHorizontal: 8, paddingVertical: 4 },
  linkRow: { flexDirection: 'row', alignItems: 'center', gap: 4, minHeight: 36 },
  link: { fontSize: 13, fontWeight: '700' },
  trace: { borderTopWidth: StyleSheet.hairlineWidth, paddingTop: 10, gap: 10 },
  traceStep: { gap: 3 },
  reasonTitle: { fontSize: 14, fontWeight: '700' },
  modalBackdrop: { flex: 1, backgroundColor: 'rgba(20,10,28,0.45)', justifyContent: 'flex-end' },
  sheet: { maxHeight: '82%', borderTopLeftRadius: 22, borderTopRightRadius: 22, padding: 18 },
  sheetHeader: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 },
  group: { gap: 8, marginBottom: 16 },
  option: { borderWidth: 1, borderRadius: 14, padding: 12, gap: 4 },
});
