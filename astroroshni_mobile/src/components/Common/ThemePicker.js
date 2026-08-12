import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useTheme } from '../../context/ThemeContext';
import AppScrollView from '../../platform/AppScrollView';
import { useTranslation } from 'react-i18next';

export default function ThemePicker({ compact = false }) {
  const { themeId, setTheme, themes, colors, typography } = useTheme();
  const { t } = useTranslation();

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
      <AppScrollView
        horizontal
        nestedScrollEnabled
        directionalLockEnabled
        alwaysBounceHorizontal
        showsHorizontalScrollIndicator={false}
        style={styles.scroller}
        contentContainerStyle={styles.list}
      >
        {themes.map((item) => {
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
                {
                  backgroundColor: colors.surface,
                  borderColor: selected ? colors.primary : colors.cardBorder,
                },
              ]}
            >
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
                <Text style={[styles.label, { color: colors.text }]} numberOfLines={1}>{item.label}</Text>
                {!compact ? (
                  <Text style={[styles.description, { color: colors.textSecondary }]} numberOfLines={2}>
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
      </AppScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
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
  description: { fontSize: 11, lineHeight: 15, fontWeight: '500' },
  check: {
    position: 'absolute', right: 12, top: 12,
    width: 22, height: 22, borderRadius: 11, borderWidth: 1,
    alignItems: 'center', justifyContent: 'center',
  },
});
