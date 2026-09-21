import React, { useMemo, useState } from 'react';
import { StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useTranslation } from 'react-i18next';

import { useTheme } from '../context/ThemeContext';
import MonthlyAccordion from './MonthlyAccordion';
import LegacyMonthlyAccordion from './LegacyMonthlyAccordion';
import yearlySample from '../data/eventTimelineYearlySample.json';
import monthlySample from '../data/eventTimelineMonthlySample.json';

const MONTH_NAMES = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December',
];

export default function EventTimelineSamplePreview({ mode = 'yearly', engineVersion = null }) {
  const [expanded, setExpanded] = useState(false);
  const { t } = useTranslation();
  const { colors } = useTheme();
  const sample = mode === 'monthly' ? monthlySample : yearlySample;
  const months = useMemo(() => sample.monthly_predictions || [], [sample]);
  const isYearly = mode !== 'monthly';
  const SampleMonthlyAccordion = engineVersion === 'legacy_v1'
    ? LegacyMonthlyAccordion
    : MonthlyAccordion;

  return (
    <View style={[styles.container, { backgroundColor: colors.surface, borderColor: colors.cardBorder }]}>
      <View style={styles.headingRow}>
        <View style={[styles.sampleBadge, { backgroundColor: colors.primary }]}>
          <Text style={[styles.sampleBadgeText, { color: colors.onPrimary }]}>SAMPLE</Text>
        </View>
        <View style={styles.headingCopy}>
          <Text style={[styles.title, { color: colors.text }]}>
            {t('eventTimelineSample.title', 'See a complete sample')}
          </Text>
          <Text style={[styles.description, { color: colors.textSecondary }]}>
            {t(
              'eventTimelineSample.description',
              'This was generated from a fictional birth chart. Your report will use your selected chart.'
            )}
          </Text>
        </View>
      </View>

      <Text style={[styles.languageNote, { color: colors.textTertiary }]}>
        {t(
          'eventTimelineSample.languageNote',
          'The sample report is shown in English. Your report follows your selected language.'
        )}
      </Text>

      <TouchableOpacity
        style={[styles.toggle, { borderColor: colors.primary }]}
        onPress={() => setExpanded((value) => !value)}
        activeOpacity={0.75}
        accessibilityRole="button"
        accessibilityState={{ expanded }}
      >
        <Text style={[styles.toggleText, { color: colors.primary }]}>
          {expanded
            ? t('eventTimelineSample.hide', 'Hide sample')
            : isYearly
              ? t('eventTimelineSample.showYearly', 'View the complete 12-month sample')
              : t('eventTimelineSample.showMonthly', 'View the complete monthly sample')}
        </Text>
        <Ionicons name={expanded ? 'chevron-up' : 'chevron-down'} size={18} color={colors.primary} />
      </TouchableOpacity>

      {expanded ? (
        <View style={styles.report}>
          {months.map((month) => (
            <View key={`sample-${mode}-${month.month_id}`} style={styles.sampleMonth}>
              <SampleMonthlyAccordion
                data={{
                  ...month,
                  month: MONTH_NAMES[Number(month.month_id) - 1] || `Month ${month.month_id}`,
                }}
                defaultExpanded={!isYearly}
                hideDiveDeep
              />
              <View pointerEvents="none" accessible={false} style={styles.watermarkLayer}>
                <Text style={[styles.watermark, { color: colors.primary }]}>SAMPLE</Text>
              </View>
            </View>
          ))}
        </View>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    borderWidth: 1,
    borderRadius: 16,
    padding: 14,
    marginBottom: 18,
    overflow: 'hidden',
  },
  headingRow: { flexDirection: 'row', alignItems: 'flex-start', gap: 10 },
  sampleBadge: { paddingHorizontal: 9, paddingVertical: 5, borderRadius: 7 },
  sampleBadgeText: { fontSize: 11, fontWeight: '900', letterSpacing: 1.1 },
  headingCopy: { flex: 1 },
  title: { fontSize: 16, fontWeight: '800', marginBottom: 4 },
  description: { fontSize: 13, lineHeight: 19 },
  languageNote: { fontSize: 12, lineHeight: 17, marginTop: 10 },
  toggle: {
    marginTop: 13,
    borderWidth: 1,
    borderRadius: 12,
    paddingVertical: 11,
    paddingHorizontal: 13,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 8,
  },
  toggleText: { flex: 1, fontSize: 14, fontWeight: '700' },
  report: { marginTop: 14, marginHorizontal: -14 },
  sampleMonth: { position: 'relative' },
  watermarkLayer: {
    ...StyleSheet.absoluteFillObject,
    alignItems: 'center',
    justifyContent: 'center',
    opacity: 0.075,
    transform: [{ rotate: '-20deg' }],
  },
  watermark: { fontSize: 54, fontWeight: '900', letterSpacing: 5 },
});
