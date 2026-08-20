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
  onClose,
  onAskTara,
  onOpenTimeline,
}) {
  const { colors, typography } = useTheme();
  const { t } = useTranslation();
  const peak = data?.peak;
  const areas = useMemo(
    () => sortActivatedHousesByScore(peak?.activated_houses || [], t),
    [peak?.activated_houses, t],
  );

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
            {peak.mechanism_summary ? (
              <Text style={[styles.body, { color: colors.textSecondary }]}>{peak.mechanism_summary}</Text>
            ) : null}
            {areas.length ? (
              <View style={styles.list}>
                <Text style={[styles.listLabel, { color: colors.textTertiary }]}>
                  {t('premiumUi.homeNextPeak.areasActivated')}
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
                        {' · '}
                        {t('premiumUi.homeNextPeak.scoreLabel', { score: row.score || 0 })}
                      </Text>
                      {index === 0 ? (
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
