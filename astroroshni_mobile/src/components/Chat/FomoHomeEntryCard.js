import React, { useMemo } from 'react';
import { StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import Icon from '@expo/vector-icons/Ionicons';
import { LinearGradient } from 'expo-linear-gradient';
import { useTranslation } from 'react-i18next';
import { useTheme } from '../../context/ThemeContext';

const subjectKey = (subject) => ({
  self: 'subjectSelf',
  spouse: 'subjectSpouse',
  mother: 'subjectMother',
  father: 'subjectFather',
}[String(subject || '').toLowerCase()] || 'subjectOther');

export default function FomoHomeEntryCard({ data, onPress }) {
  const { t } = useTranslation();
  const { theme, colors } = useTheme();
  const teasers = Array.isArray(data?.teasers) ? data.teasers : [];
  const preview = useMemo(() => teasers.slice(0, 2), [teasers]);
  if (!teasers.length) return null;

  return (
    <TouchableOpacity
      activeOpacity={0.88}
      onPress={onPress}
      accessibilityRole="button"
      accessibilityLabel={t('fomoHome.entryTitle')}
      style={[styles.shell, {
        borderColor: theme === 'dark' ? '#7C3AED' : '#FDBA74',
        backgroundColor: colors.surface,
      }]}
    >
      <LinearGradient
        colors={theme === 'dark' ? ['#31145A', '#22113B'] : ['#FFF7ED', '#F5F3FF']}
        style={styles.gradient}
      >
        <View style={styles.header}>
          <View style={styles.icon}>
            <Icon name="sparkles" size={21} color="#F97316" />
          </View>
          <View style={styles.heading}>
            <Text style={[styles.title, { color: colors.text }]}>
              {t('fomoHome.entryTitle')}
            </Text>
            <Text style={[styles.subtitle, { color: colors.textSecondary }]}>
              {t('fomoHome.entryCount', { count: teasers.length })}
            </Text>
          </View>
        </View>

        <View style={styles.previewList}>
          {preview.map((teaser) => (
            <View key={teaser.presentation_id} style={styles.previewRow}>
              <Text style={styles.subject}>
                {t(`fomoHome.${subjectKey(teaser.subject)}`)}
              </Text>
              <Text numberOfLines={2} style={[styles.area, { color: colors.text }]}>
                {teaser.area_label || teaser.title}
              </Text>
            </View>
          ))}
          {teasers.length > preview.length ? (
            <Text style={[styles.more, { color: colors.textSecondary }]}>
              {t('fomoHome.entryMore', { count: teasers.length - preview.length })}
            </Text>
          ) : null}
        </View>

        <View style={styles.cta}>
          <Text style={styles.ctaText}>{t('fomoHome.entryCta')}</Text>
          <Icon name="arrow-forward" size={18} color="#F97316" />
        </View>
      </LinearGradient>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  shell: {
    marginHorizontal: 16,
    marginTop: 14,
    marginBottom: 14,
    borderWidth: 1,
    borderRadius: 20,
    overflow: 'hidden',
  },
  gradient: { padding: 17 },
  header: { flexDirection: 'row', alignItems: 'center' },
  icon: {
    width: 42,
    height: 42,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'rgba(249,115,22,0.14)',
    marginRight: 12,
  },
  heading: { flex: 1 },
  title: { fontSize: 18, lineHeight: 23, fontWeight: '700' },
  subtitle: { fontSize: 13, lineHeight: 19, marginTop: 2 },
  previewList: { marginTop: 14, gap: 9 },
  previewRow: {
    borderLeftWidth: 3,
    borderLeftColor: '#F97316',
    paddingLeft: 10,
  },
  subject: {
    color: '#FB923C',
    fontSize: 12,
    lineHeight: 16,
    fontWeight: '700',
  },
  area: { fontSize: 14, lineHeight: 20, marginTop: 2, fontWeight: '600' },
  more: { fontSize: 12, lineHeight: 17, marginLeft: 13 },
  cta: { flexDirection: 'row', alignItems: 'center', marginTop: 15, gap: 6 },
  ctaText: { color: '#F97316', fontSize: 14, lineHeight: 19, fontWeight: '700' },
});
