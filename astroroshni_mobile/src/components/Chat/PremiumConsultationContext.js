import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useTheme } from '../../context/ThemeContext';
import { DISPLAY_FONT_FAMILY } from '../../theme/tokens';
import { useTranslation } from 'react-i18next';

function ChartPoint({ label, value, colors, calculating }) {
  return (
    <View style={styles.chartPoint}>
      <Text style={[styles.chartPointLabel, { color: colors.textInverseMuted }]}>{label}</Text>
      <Text style={[styles.chartPointValue, { color: colors.textInverse }]} numberOfLines={1}>{value || calculating}</Text>
    </View>
  );
}

export default function PremiumConsultationContext({
  name,
  sun,
  moon,
  ascendant,
  activePeriod,
  onChangeChart,
  onOpenDasha,
  onOpenHistory,
}) {
  const { colors, typography } = useTheme();
  const { t } = useTranslation();

  return (
    <View style={[styles.shell, { backgroundColor: colors.cosmicSurface, borderColor: colors.cosmicLine }]}>
      <View style={styles.orbitOne} pointerEvents="none" />
      <View style={styles.orbitTwo} pointerEvents="none" />

      <View style={styles.topRow}>
        <View style={[styles.taraSeal, { borderColor: colors.cosmicLine, backgroundColor: colors.cosmicGlow }]}>
          <Text style={[styles.taraGlyph, { color: colors.accent }]}>त</Text>
        </View>
        <View style={styles.topCopy}>
          <Text style={[styles.eyebrow, typography.eyebrow, { color: colors.accent }]}>{t('premiumUi.chat.privateConsultation')}</Text>
          <Text style={[styles.title, { color: colors.textInverse }]}>{t('premiumUi.home.askTara')}</Text>
        </View>
        <TouchableOpacity onPress={onOpenHistory} style={[styles.historyButton, { borderColor: colors.cosmicLine }]} accessibilityLabel={t('premiumUi.chat.conversationHistory')}>
          <Ionicons name="time-outline" size={18} color={colors.textInverse} />
        </TouchableOpacity>
      </View>

      <Text style={[styles.body, { color: colors.textInverseMuted }]}>{t('premiumUi.chat.consultationBody')}</Text>

      <View style={[styles.readingFor, { borderColor: colors.cosmicLine }]}>
        <View style={styles.readingForCopy}>
          <Text style={[styles.readingLabel, { color: colors.textInverseMuted }]}>{t('premiumUi.chat.readingFor')}</Text>
          <Text style={[styles.readingName, { color: colors.textInverse }]} numberOfLines={1}>{name || t('premiumUi.chat.yourChart')}</Text>
        </View>
        <TouchableOpacity onPress={onChangeChart} style={[styles.changeButton, { backgroundColor: colors.accent }]}>
          <Text style={[styles.changeButtonText, { color: colors.onAccent }]}>{t('premiumUi.common.change')}</Text>
          <Ionicons name="swap-horizontal-outline" size={14} color={colors.onAccent} />
        </TouchableOpacity>
      </View>

      <View style={[styles.chartStrip, { borderColor: colors.cosmicLine }]}>
        <ChartPoint label={t('premiumUi.chat.asc')} value={ascendant} colors={colors} calculating={t('premiumUi.home.calculating')} />
        <View style={[styles.divider, { backgroundColor: colors.cosmicLine }]} />
        <ChartPoint label={t('premiumUi.home.moon')} value={moon} colors={colors} calculating={t('premiumUi.home.calculating')} />
        <View style={[styles.divider, { backgroundColor: colors.cosmicLine }]} />
        <ChartPoint label={t('premiumUi.home.sun')} value={sun} colors={colors} calculating={t('premiumUi.home.calculating')} />
      </View>

      <TouchableOpacity onPress={onOpenDasha} style={styles.synthesisRow} activeOpacity={0.75}>
        <View style={[styles.liveDot, { backgroundColor: colors.accent }]} />
        <Text style={[styles.synthesisText, { color: colors.textInverseMuted }]} numberOfLines={1}>
          {activePeriod ? t('premiumUi.chat.activePeriod', { period: activePeriod }) : t('premiumUi.chat.timingPreparing')}
        </Text>
        <Text style={[styles.synthesisMethods, { color: colors.accent }]}>{t('premiumUi.chat.methods')}</Text>
        <Ionicons name="chevron-forward" size={13} color={colors.textInverseMuted} />
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  shell: { borderWidth: 1, borderRadius: 28, padding: 20, marginBottom: 18, overflow: 'hidden' },
  orbitOne: { position: 'absolute', width: 190, height: 190, borderRadius: 95, borderWidth: 1, borderColor: 'rgba(215,184,120,0.12)', right: -88, top: -92 },
  orbitTwo: { position: 'absolute', width: 126, height: 126, borderRadius: 63, borderWidth: 1, borderColor: 'rgba(215,184,120,0.10)', right: -45, top: -53 },
  topRow: { flexDirection: 'row', alignItems: 'center' },
  taraSeal: { width: 50, height: 50, borderRadius: 25, borderWidth: 1, alignItems: 'center', justifyContent: 'center', marginRight: 12 },
  taraGlyph: { fontFamily: DISPLAY_FONT_FAMILY, fontSize: 27 },
  topCopy: { flex: 1 },
  eyebrow: { fontSize: 9, marginBottom: 3 },
  title: { fontFamily: DISPLAY_FONT_FAMILY, fontSize: 29, lineHeight: 33 },
  historyButton: { width: 38, height: 38, borderRadius: 19, borderWidth: 1, alignItems: 'center', justifyContent: 'center' },
  body: { fontSize: 13, lineHeight: 20, marginTop: 16, marginBottom: 18, maxWidth: 340 },
  readingFor: { flexDirection: 'row', alignItems: 'center', borderTopWidth: 1, borderBottomWidth: 1, paddingVertical: 13 },
  readingForCopy: { flex: 1 },
  readingLabel: { fontSize: 9, fontWeight: '800', letterSpacing: 1.2, textTransform: 'uppercase', marginBottom: 3 },
  readingName: { fontFamily: DISPLAY_FONT_FAMILY, fontSize: 19 },
  changeButton: { flexDirection: 'row', alignItems: 'center', gap: 5, paddingHorizontal: 12, paddingVertical: 8, borderRadius: 999 },
  changeButtonText: { fontSize: 11, fontWeight: '900' },
  chartStrip: { flexDirection: 'row', alignItems: 'center', borderBottomWidth: 1, paddingVertical: 13 },
  chartPoint: { flex: 1, alignItems: 'center', minWidth: 0 },
  chartPointLabel: { fontSize: 8, fontWeight: '900', letterSpacing: 1, marginBottom: 4 },
  chartPointValue: { fontFamily: DISPLAY_FONT_FAMILY, fontSize: 14, paddingHorizontal: 4 },
  divider: { width: 1, height: 26 },
  synthesisRow: { flexDirection: 'row', alignItems: 'center', paddingTop: 13, gap: 7 },
  liveDot: { width: 6, height: 6, borderRadius: 3 },
  synthesisText: { flex: 1, fontSize: 10, fontWeight: '700' },
  synthesisMethods: { fontSize: 7, fontWeight: '900', letterSpacing: 0.6 },
});
