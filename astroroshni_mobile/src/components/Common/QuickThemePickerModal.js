import React from 'react';
import { Modal, Pressable, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useTranslation } from 'react-i18next';
import { useTheme } from '../../context/ThemeContext';
import ThemePicker from './ThemePicker';

export default function QuickThemePickerModal({ visible, onClose, onViewAll, discovery = false }) {
  const { t } = useTranslation();
  const { colors, themeDefinition } = useTheme();

  return (
    <Modal visible={visible} transparent animationType="slide" onRequestClose={onClose} statusBarTranslucent>
      <View style={[styles.overlay, { backgroundColor: colors.overlay }]}>
        <Pressable style={StyleSheet.absoluteFill} onPress={onClose} accessibilityRole="button" />
        <View style={[styles.sheet, { backgroundColor: colors.surface, borderColor: colors.cardBorder }]}>
          <View style={[styles.handle, { backgroundColor: colors.cardBorder }]} />
          <View style={styles.header}>
            <View style={[styles.icon, { backgroundColor: colors.selectionSurface, borderColor: colors.selectionBorder }]}>
              <Ionicons name="color-palette-outline" size={23} color={colors.primary} />
            </View>
            <View style={styles.headerCopy}>
              <Text style={[styles.eyebrow, { color: colors.primary }]}>
                {discovery ? t('themeDiscovery.discoveryEyebrow') : t('themeDiscovery.eyebrow')}
              </Text>
              <Text style={[styles.title, { color: colors.text }]}>
                {discovery ? t('themeDiscovery.discoveryTitle') : t('themeDiscovery.title')}
              </Text>
            </View>
            <TouchableOpacity
              style={[styles.close, { backgroundColor: colors.surfaceMuted, borderColor: colors.cardBorder }]}
              onPress={onClose}
              accessibilityRole="button"
              accessibilityLabel={t('common.close', 'Close')}
            >
              <Ionicons name="close" size={21} color={colors.text} />
            </TouchableOpacity>
          </View>

          <Text style={[styles.body, { color: colors.textSecondary }]}>
            {discovery ? t('themeDiscovery.discoveryBody') : t('themeDiscovery.body')}
          </Text>

          <View style={[styles.current, { backgroundColor: colors.cosmicSurface, borderColor: colors.cosmicLine }]}>
            <View style={[styles.currentDot, { backgroundColor: colors.accent }]} />
            <Text style={[styles.currentLabel, { color: colors.textInverseMuted }]}>
              {t('themeDiscovery.currentTheme')}
            </Text>
            <Text style={[styles.currentName, { color: colors.textInverse }]} numberOfLines={1}>
              {themeDefinition?.label || ''}
            </Text>
          </View>

          <ThemePicker compact />

          <View style={styles.footer}>
            <Text style={[styles.instantHint, { color: colors.textTertiary }]}>
              {t('themeDiscovery.instantHint')}
            </Text>
            <TouchableOpacity
              style={[styles.viewAll, { borderColor: colors.cardBorder }]}
              onPress={onViewAll}
              accessibilityRole="button"
            >
              <Text style={[styles.viewAllText, { color: colors.primary }]}>{t('themeDiscovery.viewAll')}</Text>
              <Ionicons name="arrow-forward" size={17} color={colors.primary} />
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: { flex: 1, justifyContent: 'flex-end' },
  sheet: {
    borderTopLeftRadius: 30,
    borderTopRightRadius: 30,
    borderWidth: 1,
    paddingHorizontal: 20,
    paddingTop: 10,
    paddingBottom: 28,
  },
  handle: { width: 42, height: 4, borderRadius: 2, alignSelf: 'center', marginBottom: 18 },
  header: { flexDirection: 'row', alignItems: 'center' },
  icon: { width: 46, height: 46, borderRadius: 16, borderWidth: 1, alignItems: 'center', justifyContent: 'center', marginRight: 12 },
  headerCopy: { flex: 1, minWidth: 0 },
  eyebrow: { fontSize: 9, fontWeight: '800', letterSpacing: 1.7, textTransform: 'uppercase', marginBottom: 3 },
  title: { fontFamily: 'serif', fontSize: 25, lineHeight: 29, fontWeight: '600' },
  close: { width: 40, height: 40, borderRadius: 20, borderWidth: 1, alignItems: 'center', justifyContent: 'center', marginLeft: 10 },
  body: { fontSize: 14, lineHeight: 20, marginTop: 14, marginBottom: 15 },
  current: { minHeight: 46, borderRadius: 16, borderWidth: 1, flexDirection: 'row', alignItems: 'center', paddingHorizontal: 14, marginBottom: 15 },
  currentDot: { width: 8, height: 8, borderRadius: 4, marginRight: 9 },
  currentLabel: { fontSize: 10, fontWeight: '700', letterSpacing: 0.5, textTransform: 'uppercase', marginRight: 8 },
  currentName: { flex: 1, fontSize: 13, fontWeight: '800', textAlign: 'right' },
  footer: { marginTop: 16 },
  instantHint: { fontSize: 11, lineHeight: 16, textAlign: 'center', marginBottom: 11 },
  viewAll: { minHeight: 50, borderRadius: 999, borderWidth: 1, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8 },
  viewAllText: { fontSize: 14, fontWeight: '800' },
});
