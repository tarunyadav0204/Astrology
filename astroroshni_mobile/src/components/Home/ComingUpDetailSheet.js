import React, { useMemo } from 'react';
import {
  Modal,
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  Pressable,
} from 'react-native';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useTranslation } from 'react-i18next';
import { useTheme } from '../../context/ThemeContext';
import { DISPLAY_FONT_FAMILY } from '../../theme/tokens';
import { sortActivatedHousesByScore } from '../../utils/houseLifeAreas';

export default function ComingUpDetailSheet({
  visible,
  data,
  localizePlanet,
  onClose,
  onAskTara,
  onOpenTimeline,
}) {
  const { colors, typography } = useTheme();
  const { t } = useTranslation();
  const peak = data?.peak;
  const isBackground = peak?.display_mode === 'background';
  const areas = useMemo(
    () => sortActivatedHousesByScore(peak?.activated_houses || [], t),
    [peak?.activated_houses, t],
  );

  const planetName = (planet) => localizePlanet?.(planet) || planet || '';
  const dashaRoles = (levels = []) => levels.map((level) => t(
    `premiumUi.homeNextPeak.role${String(level).toUpperCase()}`,
  )).join(' + ');

  const explainActivation = (reason = {}, house) => {
    if (reason.kind === 'direct_transit' && reason.transit) {
      const lines = (reason.natal_support || []).map((support) => {
        const mechanisms = support.mechanisms || [];
        const mechanism = mechanisms.includes('natal_occupation')
          ? 'Occupation'
          : mechanisms.includes('lordship') ? 'Lordship' : 'Aspect';
        return t(`premiumUi.homeNextPeak.reasonNatal${mechanism}`, {
          planet: planetName(support.planet),
          roles: dashaRoles(support.dasha_levels),
          natalHouse: support.natal_house,
          house,
        });
      });
      const transit = reason.transit;
      lines.push(t(
        transit.mechanism === 'transit_occupation'
          ? 'premiumUi.homeNextPeak.reasonTransitOccupation'
          : 'premiumUi.homeNextPeak.reasonTransitAspect',
        {
          planet: planetName(transit.planet),
          roles: dashaRoles(transit.dasha_levels),
          transitHouse: transit.house,
          house,
        },
      ));
      lines.push(t('premiumUi.homeNextPeak.reasonFullyActivated'));
      return lines;
    }
    const planet = planetName(reason.planet);
    const prefix = reason.kind === 'pd_background' ? 'Background' : 'Direct';
    const mechanism = {
      transit_occupation: 'Occupation',
      transit_aspect: 'Aspect',
      natal_occupation: 'Occupation',
      lordship: 'Lordship',
      natal_aspect: 'Aspect',
    }[reason.mechanism] || 'Linked';
    return [t(`premiumUi.homeNextPeak.reason${prefix}${mechanism}`, { planet })];
  };

  if (!peak) return null;

  return (
    <Modal visible={visible} animationType="slide" transparent onRequestClose={onClose}>
      <Pressable style={styles.backdrop} onPress={onClose}>
        <Pressable
          style={[styles.sheet, { backgroundColor: colors.surface, borderColor: colors.cardBorder }]}
          onPress={(event) => event.stopPropagation()}
        >
          <View style={styles.header}>
            <Text style={[styles.title, typography.sectionTitle, { color: colors.text }]}>
              {t('premiumUi.homeNextPeak.detailTitle')}
            </Text>
            <TouchableOpacity onPress={onClose} accessibilityRole="button" accessibilityLabel={t('premiumUi.common.close')}>
              <Ionicons name="close" size={22} color={colors.textSecondary} />
            </TouchableOpacity>
          </View>
          <ScrollView contentContainerStyle={styles.content}>
            <Text style={[styles.dates, { color: colors.text }]}>
              {peak.peak_start} – {peak.peak_end}
            </Text>
            {isBackground ? (
              <View style={[styles.backgroundNote, { backgroundColor: colors.surfaceMuted, borderColor: colors.cardBorder }]}>
                <Text style={[styles.backgroundTitle, { color: colors.text }]}>
                  {t('premiumUi.homeNextPeak.backgroundLabel')}
                </Text>
                <Text style={[styles.body, { color: colors.textSecondary }]}>
                  {t('premiumUi.homeNextPeak.backgroundBody')}
                </Text>
              </View>
            ) : null}
            {areas.length ? (
              <View style={styles.list}>
                <Text style={[styles.listLabel, { color: colors.textTertiary }]}>
                  {t(isBackground
                    ? 'premiumUi.homeNextPeak.backgroundLabel'
                    : 'premiumUi.homeNextPeak.areasActivated')}
                </Text>
                {areas.map((row, index) => (
                  <View
                    key={row.house}
                    style={[styles.row, { borderColor: colors.cardBorder }]}
                  >
                    <View style={styles.rowCopy}>
                      <Text style={[styles.rowTitle, { color: colors.text }]}>{row.label}</Text>
                      <Text style={[styles.rowMeta, { color: colors.textSecondary }]}>
                        {t('premiumUi.homeNextPeak.houseLabel', { number: row.house })}
                      </Text>
                      <View style={styles.reasonGroup}>
                        {explainActivation(row.reason, row.house).map((line, reasonIndex) => (
                          <Text
                            key={`${row.house}-reason-${reasonIndex}`}
                            style={[styles.reason, { color: colors.textSecondary }]}
                          >
                            {line}
                          </Text>
                        ))}
                      </View>
                      {index === 0 && (areas.length === 1 || Number(row.score) > Number(areas[1]?.score)) ? (
                        <Text style={[styles.strongest, { color: colors.textTertiary }]}>
                          {t('premiumUi.homeNextPeak.strongestLink')}
                        </Text>
                      ) : null}
                    </View>
                  </View>
                ))}
              </View>
            ) : null}
          </ScrollView>
          <View style={styles.actions}>
            <TouchableOpacity
              onPress={onAskTara}
              style={[styles.primary, { backgroundColor: colors.primary }]}
            >
              <Text style={[styles.primaryText, { color: colors.onPrimary }]}>
                {t('premiumUi.homeNextPeak.askTara')}
              </Text>
            </TouchableOpacity>
            <TouchableOpacity
              onPress={onOpenTimeline}
              style={[styles.secondary, { borderColor: colors.cardBorder }]}
            >
              <Text style={[styles.secondaryText, { color: colors.text }]}>
                {t('premiumUi.homeNextPeak.timeline')}
              </Text>
            </TouchableOpacity>
          </View>
        </Pressable>
      </Pressable>
    </Modal>
  );
}

const styles = StyleSheet.create({
  backdrop: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.45)',
    justifyContent: 'flex-end',
  },
  sheet: {
    maxHeight: '82%',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    borderWidth: 1,
    paddingBottom: 24,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingTop: 18,
    paddingBottom: 8,
  },
  title: {
    flex: 1,
    paddingRight: 12,
  },
  content: {
    paddingHorizontal: 20,
    paddingBottom: 12,
    gap: 12,
  },
  dates: {
    fontFamily: DISPLAY_FONT_FAMILY,
    fontSize: 18,
    fontWeight: '600',
  },
  body: {
    fontFamily: DISPLAY_FONT_FAMILY,
    fontSize: 14,
    lineHeight: 21,
  },
  backgroundNote: {
    borderWidth: 1,
    borderRadius: 12,
    padding: 12,
    gap: 6,
  },
  backgroundTitle: {
    fontFamily: DISPLAY_FONT_FAMILY,
    fontSize: 14,
    fontWeight: '600',
  },
  list: {
    gap: 10,
    marginTop: 4,
  },
  listLabel: {
    fontFamily: DISPLAY_FONT_FAMILY,
    fontSize: 11,
    letterSpacing: 0.8,
    textTransform: 'uppercase',
  },
  row: {
    borderWidth: 1,
    borderRadius: 12,
    padding: 12,
  },
  rowCopy: {
    gap: 4,
  },
  rowTitle: {
    fontFamily: DISPLAY_FONT_FAMILY,
    fontSize: 16,
    fontWeight: '600',
  },
  rowMeta: {
    fontFamily: DISPLAY_FONT_FAMILY,
    fontSize: 13,
  },
  reason: {
    fontFamily: DISPLAY_FONT_FAMILY,
    fontSize: 13,
    lineHeight: 19,
  },
  reasonGroup: {
    marginTop: 4,
    gap: 5,
  },
  strongest: {
    marginTop: 4,
    fontFamily: DISPLAY_FONT_FAMILY,
    fontSize: 12,
    lineHeight: 17,
  },
  actions: {
    paddingHorizontal: 20,
    gap: 10,
  },
  primary: {
    minHeight: 46,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  primaryText: {
    fontFamily: DISPLAY_FONT_FAMILY,
    fontSize: 15,
    fontWeight: '600',
  },
  secondary: {
    minHeight: 44,
    borderRadius: 12,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  secondaryText: {
    fontFamily: DISPLAY_FONT_FAMILY,
    fontSize: 14,
    fontWeight: '500',
  },
});
