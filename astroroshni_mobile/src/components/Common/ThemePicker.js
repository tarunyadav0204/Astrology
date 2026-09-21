import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, useWindowDimensions } from 'react-native';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useTheme } from '../../context/ThemeContext';
import { THEME_PALETTES } from '../../theme/tokens';
import AppScrollView from '../../platform/AppScrollView';
import { useTranslation } from 'react-i18next';

export default function ThemePicker({ compact = false }) {
  const { themeId, setTheme, themes, colors, typography } = useTheme();
  const { t } = useTranslation();
  const { width } = useWindowDimensions();
  const [expanded, setExpanded] = useState(false);
  const PickerContainer = expanded ? View : AppScrollView;

  return (
    <View style={styles.wrap}>
      {!compact ? (
        <View style={styles.headingRow}>
          <View>
            <Text style={[styles.eyebrow, typography.eyebrow, { color: colors.textTertiary }]}>{t('premiumUi.theme.appearance')}</Text>
            <Text style={[styles.heading, typography.sectionTitle, { color: colors.text }]}>{t('premiumUi.theme.chooseAtmosphere')}</Text>
          </View>
        </View>
      ) : null}
      {!compact && <TouchableOpacity
        onPress={() => setExpanded(value => !value)}
        accessibilityRole="button"
        accessibilityState={{ expanded }}
        style={styles.galleryToggle}
      >
        <Text style={{ color: colors.primary, fontSize: 14, fontWeight: '700' }}>{expanded ? t('common.showLess', 'Show less') : t('themeDiscovery.viewAll', 'View all themes')}</Text>
        <Ionicons name={expanded ? 'chevron-up' : 'grid-outline'} size={18} color={colors.primary} />
      </TouchableOpacity>}
      <PickerContainer
        {...(expanded ? {} : { horizontal: true,
        nestedScrollEnabled: true,
        directionalLockEnabled: true,
        showsHorizontalScrollIndicator: false,
        contentContainerStyle: styles.list })}
        style={expanded ? styles.gallery : styles.scroller}
      >

        {themes.map((item) => {
          const palette = THEME_PALETTES[item.id];
          const selected = themeId === item.id;
          return (
            <TouchableOpacity
              key={item.id}
              onPress={() => setTheme(item.id)}
              activeOpacity={0.82}
              accessibilityRole="radio"
              accessibilityState={{ selected }}
              accessibilityLabel={t('premiumUi.theme.themeLabel', { name: item.label })}
              style={[
                styles.option,
                expanded && styles.galleryOption,
                expanded && { width: width < 380 ? '100%' : '48%' },
                {
                  backgroundColor: colors.surface,
                  borderColor: selected ? colors.primary : colors.cardBorder,
                },
              ]}
            >
              {expanded && <View accessible={false} style={[styles.screenPreview, { backgroundColor: palette.background }]}>
                <View style={[styles.previewHeader, { backgroundColor: palette.headerSurface }]} />
                <View style={[styles.previewCard, { backgroundColor: palette.surface, borderColor: palette.cardBorder }]}>
                  <View style={[styles.previewLine, { backgroundColor: palette.text }]} />
                  <View style={[styles.previewShortLine, { backgroundColor: palette.primary }]} />
                </View>
              </View>}
              <View style={styles.preview}>
                {item.preview.map((swatch, index) => (
                  <View
                    key={swatch}
                    style={[
                      styles.swatch,
                      { backgroundColor: swatch, zIndex: 3 - index },
                      index > 0 && styles.swatchOverlap,
                    ]}
                  />
                ))}
              </View>
              <View style={styles.optionCopy}>
                <Text style={[styles.label, { color: colors.text }]} numberOfLines={expanded ? undefined : 1}>{item.label}</Text>
                {!compact ? (
                  <Text style={[styles.description, { color: colors.textSecondary }]} numberOfLines={expanded ? undefined : 2}>
                    {item.description}
                  </Text>
                ) : null}
              </View>
              <View
                style={[
                  styles.check,
                  { backgroundColor: selected ? colors.primary : 'transparent', borderColor: selected ? colors.primary : colors.cardBorder },
                ]}
              >
                {selected ? <Ionicons name="checkmark" size={13} color={colors.onPrimary} /> : null}
              </View>
            </TouchableOpacity>
          );
        })}
      </PickerContainer>
    </View>
  );
}

const styles = StyleSheet.create({
  galleryToggle: { minHeight: 44, flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 8 },
  gallery: { flexDirection: 'row', flexWrap: 'wrap', gap: 10 },
  galleryOption: { width: '100%', minWidth: 0 },
  screenPreview: { height: 78, borderRadius: 10, overflow: 'hidden', marginBottom: 12, marginRight: 24 },
  previewHeader: { height: 18 },
  previewCard: { margin: 8, padding: 8, borderWidth: 1, borderRadius: 6 },
  previewLine: { width: '65%', height: 4, borderRadius: 2, marginBottom: 6 },
  previewShortLine: { width: '32%', height: 5, borderRadius: 3 },
  wrap: { width: '100%' },
  headingRow: { marginBottom: 14 },
  eyebrow: { marginBottom: 6 },
  heading: { fontSize: 24, lineHeight: 29 },
  scroller: { width: '100%' },
  list: { gap: 10, paddingRight: 18 },
  option: {
    width: 174,
    minHeight: 104,
    borderWidth: 1,
    borderRadius: 18,
    padding: 14,
  },
  preview: { flexDirection: 'row', alignItems: 'center', marginBottom: 12 },
  swatch: { width: 28, height: 28, borderRadius: 14, borderWidth: 2, borderColor: 'rgba(255,255,255,0.75)' },
  swatchOverlap: { marginLeft: -8 },
  optionCopy: { paddingRight: 24 },
  label: { fontSize: 14, fontWeight: '800', marginBottom: 3 },
  description: { fontSize: 13, lineHeight: 18, fontWeight: '500' },
  check: {
    position: 'absolute', right: 12, top: 12,
    width: 22, height: 22, borderRadius: 11, borderWidth: 1,
    alignItems: 'center', justifyContent: 'center',
  },
});
