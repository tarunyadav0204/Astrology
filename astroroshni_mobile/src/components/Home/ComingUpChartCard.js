import React, { useMemo } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ActivityIndicator } from 'react-native';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useTranslation } from 'react-i18next';
import { useTheme } from '../../context/ThemeContext';
import { DISPLAY_FONT_FAMILY } from '../../theme/tokens';
import { houseLifeAreaLabel, sortActivatedHousesByScore } from '../../utils/houseLifeAreas';

const LANGUAGE_LOCALES = {
  english: 'en-IN', hindi: 'hi-IN', es: 'es-ES', french: 'fr-FR', german: 'de-DE',
  russian: 'ru-RU', chinese: 'zh-CN', mandarin: 'zh-CN', tamil: 'ta-IN', telugu: 'te-IN',
  gujarati: 'gu-IN', marathi: 'mr-IN',
};

function formatDateBand(start, end, locale) {
  const fmt = new Intl.DateTimeFormat(locale || 'en-IN', { month: 'short', day: 'numeric' });
  const startLabel = fmt.format(new Date(`${start}T12:00:00`));
  const endLabel = fmt.format(new Date(`${end}T12:00:00`));
  return `${startLabel} – ${endLabel}`;
}

function nearnessLabel(daysUntil, t) {
  if (daysUntil == null || daysUntil < 0) return null;
  if (daysUntil === 0) return t('premiumUi.homeNextPeak.dateBandToday');
  if (daysUntil === 1) return t('premiumUi.homeNextPeak.dateBandSoonDay', { count: 1 });
  if (daysUntil <= 13) return t('premiumUi.homeNextPeak.dateBandSoonDays', { count: daysUntil });
  const weeks = Math.max(1, Math.round(daysUntil / 7));
  return t('premiumUi.homeNextPeak.dateBandNearWeeks', { count: weeks });
}

function shortNativeName(name) {
  const raw = String(name || '').trim();
  if (!raw) return '';
  if (raw.length <= 7) return raw;
  return `${raw.slice(0, 7)}...`;
}

export default function ComingUpChartCard({
  data,
  loading,
  nativeName,
  localizePlanet,
  onPressDetail,
  onAskTara,
  onOpenTimeline,
}) {
  const { colors, typography } = useTheme();
  const { t, i18n } = useTranslation();
  const locale = LANGUAGE_LOCALES[i18n.resolvedLanguage || i18n.language] || 'en-IN';

  const peak = data?.peak;
  const pdHandoff = data?.pd_handoff;
  const isBackground = peak?.display_mode === 'background';
  const areas = useMemo(
    () => sortActivatedHousesByScore(peak?.activated_houses || [], t),
    [peak?.activated_houses, t],
  );

  if (loading) {
    return (
      <View style={[styles.shell, { backgroundColor: colors.surface, borderColor: colors.cardBorder }]}>
        <ActivityIndicator color={colors.primary} />
        <Text style={[styles.loadingText, { color: colors.textSecondary }]}>
          {t('premiumUi.homeNextPeak.loading')}
        </Text>
      </View>
    );
  }

  if (!peak || (data?.status !== 'ready' && data?.status !== 'theme_only')) {
    return null;
  }

  const dateTitle = formatDateBand(peak.peak_start, peak.peak_end, locale);
  const nearLabel = nearnessLabel(peak.days_until_start, t);
  const pd = localizePlanet?.(peak.pratyantardasha) || peak.pratyantardasha;
  const ad = localizePlanet?.(peak.antardasha) || peak.antardasha;

  return (
    <View style={[styles.shell, { backgroundColor: colors.surface, borderColor: colors.cardBorder }]}>
      <TouchableOpacity activeOpacity={0.86} onPress={onPressDetail}>
        <Text style={[styles.eyebrow, typography.eyebrow, { color: colors.primary }]}>
          {t('premiumUi.homeNextPeak.eyebrow', { name: shortNativeName(nativeName) || t('premiumUi.home.explorer') })}
        </Text>
        {isBackground ? (
          <View style={[styles.modePill, { backgroundColor: colors.surfaceMuted, borderColor: colors.cardBorder }]}>
            <Ionicons name="layers-outline" size={13} color={colors.textSecondary} />
            <Text style={[styles.modePillText, { color: colors.textSecondary }]}>
              {t('premiumUi.homeNextPeak.backgroundLabel')}
            </Text>
          </View>
        ) : null}
        <Text style={[styles.title, { color: colors.text }]}>
          {dateTitle}
          {nearLabel ? (
            <Text style={[styles.near, { color: colors.textSecondary }]}>{` · ${nearLabel}`}</Text>
          ) : null}
        </Text>
        {pd && ad ? (
          <Text style={[styles.dashaLine, { color: colors.textSecondary }]}>
            {t('premiumUi.homeNextPeak.dashaLine', { pd, ad })}
          </Text>
        ) : null}
        {pdHandoff?.show ? (
          <Text style={[styles.handoff, { color: colors.textTertiary }]}>
            {t('premiumUi.homeNextPeak.pdHandoff', {
              days: pdHandoff.days_until_pd_change,
              nextPd: localizePlanet?.(pdHandoff.next_pd_planet) || pdHandoff.next_pd_planet || pd,
            })}
          </Text>
        ) : null}
        <Text style={[styles.mechanism, { color: colors.textSecondary }]} numberOfLines={3}>
          {isBackground
            ? t('premiumUi.homeNextPeak.backgroundBody')
            : (peak.mechanism_summary || t('premiumUi.homeNextPeak.themeOnlyBody'))}
        </Text>
        {areas.length ? (
          <View style={styles.areaBlock}>
            <Text style={[styles.areaLabel, { color: colors.textTertiary }]}>
              {t(isBackground
                ? 'premiumUi.homeNextPeak.backgroundLabel'
                : 'premiumUi.homeNextPeak.areasActivated')}
            </Text>
            {areas.map((row) => (
              <View key={row.house} style={styles.areaRow}>
                <View style={[styles.bullet, { backgroundColor: colors.primary }]} />
                <Text style={[styles.areaText, { color: colors.text }]}>{row.label}</Text>
              </View>
            ))}
          </View>
        ) : null}
      </TouchableOpacity>
      <View style={styles.actions}>
        <TouchableOpacity
          onPress={onAskTara}
          activeOpacity={0.86}
          style={[styles.primaryAction, { backgroundColor: colors.primary }]}
        >
          <Ionicons name="sparkles-outline" size={16} color={colors.onPrimary} />
          <Text style={[styles.primaryActionText, { color: colors.onPrimary }]}>
            {t('premiumUi.homeNextPeak.askTara')}
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          onPress={onOpenTimeline}
          activeOpacity={0.82}
          style={[styles.secondaryAction, { borderColor: colors.cardBorder }]}
        >
          <Text style={[styles.secondaryActionText, { color: colors.text }]}>
            {t('premiumUi.homeNextPeak.timeline')}
          </Text>
          <Ionicons name="arrow-forward" size={15} color={colors.textSecondary} />
        </TouchableOpacity>
      </View>
    </View>
  );
}

export function buildComingUpAskMessage(peak, t, localizePlanet) {
  if (!peak) return '';
  const areas = sortActivatedHousesByScore(peak.activated_houses || [], t)
    .map((row) => row.label)
    .filter(Boolean);
  const areaText = areas.length
    ? areas.join(', ')
    : houseLifeAreaLabel(peak.activated_houses?.[0]?.house, t);
  const key = peak.display_mode === 'background'
    ? 'premiumUi.homeNextPeak.backgroundAskPrefill'
    : 'premiumUi.homeNextPeak.askPrefill';
  return t(key, {
    start: peak.peak_start,
    end: peak.peak_end,
    areas: areaText,
    pd: localizePlanet?.(peak.pratyantardasha) || peak.pratyantardasha,
    ad: localizePlanet?.(peak.antardasha) || peak.antardasha,
  });
}

const styles = StyleSheet.create({
  shell: {
    borderWidth: 1,
    borderRadius: 18,
    padding: 16,
    gap: 12,
  },
  loadingText: {
    fontFamily: DISPLAY_FONT_FAMILY,
    fontSize: 14,
    marginTop: 8,
  },
  eyebrow: {
    marginBottom: 6,
  },
  modePill: {
    alignSelf: 'flex-start',
    minHeight: 28,
    borderRadius: 14,
    borderWidth: 1,
    paddingHorizontal: 10,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 8,
  },
  modePillText: {
    fontFamily: DISPLAY_FONT_FAMILY,
    fontSize: 12,
    fontWeight: '600',
  },
  title: {
    fontFamily: DISPLAY_FONT_FAMILY,
    fontSize: 22,
    lineHeight: 28,
    fontWeight: '600',
  },
  near: {
    fontSize: 16,
    fontWeight: '400',
  },
  dashaLine: {
    marginTop: 6,
    fontFamily: DISPLAY_FONT_FAMILY,
    fontSize: 14,
  },
  handoff: {
    marginTop: 4,
    fontFamily: DISPLAY_FONT_FAMILY,
    fontSize: 12,
    lineHeight: 17,
  },
  mechanism: {
    marginTop: 10,
    fontFamily: DISPLAY_FONT_FAMILY,
    fontSize: 14,
    lineHeight: 20,
  },
  areaBlock: {
    marginTop: 14,
    gap: 8,
  },
  areaLabel: {
    fontFamily: DISPLAY_FONT_FAMILY,
    fontSize: 11,
    letterSpacing: 0.8,
    textTransform: 'uppercase',
  },
  areaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  bullet: {
    width: 6,
    height: 6,
    borderRadius: 3,
  },
  areaText: {
    flex: 1,
    fontFamily: DISPLAY_FONT_FAMILY,
    fontSize: 15,
    lineHeight: 21,
  },
  actions: {
    flexDirection: 'row',
    gap: 10,
    marginTop: 4,
  },
  primaryAction: {
    flex: 1,
    minHeight: 44,
    borderRadius: 12,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
  },
  primaryActionText: {
    fontFamily: DISPLAY_FONT_FAMILY,
    fontSize: 14,
    fontWeight: '600',
  },
  secondaryAction: {
    flex: 1,
    minHeight: 44,
    borderRadius: 12,
    borderWidth: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    paddingHorizontal: 10,
  },
  secondaryActionText: {
    fontFamily: DISPLAY_FONT_FAMILY,
    fontSize: 14,
    fontWeight: '500',
  },
});
