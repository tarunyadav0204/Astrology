import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Platform } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import Icon from '@expo/vector-icons/Ionicons';
import { useTranslation } from 'react-i18next';

export default function HomeStudyLabCtaCard({ onPress, colors, isClassic, theme }) {
  const { t } = useTranslation();
  const isDark = theme === 'dark';

  const cardBg = isClassic
    ? [colors.cardBackground, colors.backgroundSecondary]
    : isDark
      ? ['rgba(255,255,255,0.12)', 'rgba(255,255,255,0.05)']
      : ['#ffffff', '#faf8f5'];

  const accent = isClassic ? colors.text : isDark ? '#ffffff' : '#1c1917';
  const accentMuted = isClassic ? colors.textSecondary : isDark ? 'rgba(255,255,255,0.75)' : '#57534e';

  return (
    <TouchableOpacity
      style={styles.wrap}
      onPress={onPress}
      activeOpacity={0.92}
      accessibilityRole="button"
      accessibilityLabel={t('home.studyLabCta.a11y', 'Open chart study chat')}
    >
      <LinearGradient
        colors={cardBg}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={[
          styles.card,
          {
            borderColor: colors.cardBorder,
            ...Platform.select({
              ios: {
                shadowColor: isClassic ? '#000' : '#000',
                shadowOffset: { width: 0, height: 4 },
                shadowOpacity: isClassic ? 0.06 : 0.12,
                shadowRadius: 12,
              },
              android: { elevation: isClassic ? 2 : 4 },
            }),
          },
        ]}
      >
        <View style={[styles.accentBar, { backgroundColor: accent }]} />

        <View style={styles.body}>
          <View style={styles.topRow}>
            <View style={[styles.iconCircle, { backgroundColor: isClassic ? colors.surface : 'rgba(0,0,0,0.06)' }]}>
              <Icon name="school" size={22} color={accent} />
            </View>
            <View style={styles.titleBlock}>
              <Text style={[styles.eyebrow, { color: accentMuted }]}>
                {t('home.studyLabCta.eyebrow', 'PRIMARY')}
              </Text>
              <Text style={[styles.title, { color: accent }]}>
                {t('home.studyLabCta.title', 'Chart Study Lab')}
              </Text>
            </View>
            <View style={[styles.chevronCircle, { borderColor: colors.cardBorder }]}>
              <Icon name="arrow-forward" size={18} color={accent} />
            </View>
          </View>

          <Text style={[styles.description, { color: accentMuted }]}>
            {t(
              'home.studyLabCta.description',
              'Use your birth chart as a worked example. Ask how houses, dashas, and classical techniques are read—for study, not fortune telling.',
            )}
          </Text>

          <View
            style={[
              styles.ctaPill,
              { backgroundColor: isClassic ? colors.text : isDark ? '#ffffff' : '#1c1917' },
            ]}
          >
            <Text
              style={[
                styles.ctaPillText,
                { color: isClassic || !isDark ? '#ffffff' : '#1c1917' },
              ]}
            >
              {t('home.studyLabCta.button', 'Open Study Chat')}
            </Text>
            <Icon
              name="chatbubbles-outline"
              size={16}
              color={isClassic || !isDark ? '#ffffff' : '#1c1917'}
              style={styles.ctaIcon}
            />
          </View>
        </View>
      </LinearGradient>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  wrap: {
    alignSelf: 'stretch',
    marginTop: 0,
    marginBottom: 12,
  },
  card: {
    borderRadius: 20,
    borderWidth: 1,
    overflow: 'hidden',
    flexDirection: 'row',
  },
  accentBar: {
    width: 4,
    alignSelf: 'stretch',
  },
  body: {
    flex: 1,
    paddingVertical: 18,
    paddingHorizontal: 16,
    paddingLeft: 14,
  },
  topRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  iconCircle: {
    width: 44,
    height: 44,
    borderRadius: 22,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  titleBlock: {
    flex: 1,
    minWidth: 0,
  },
  eyebrow: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 1.2,
    marginBottom: 2,
  },
  title: {
    fontSize: 18,
    fontWeight: '700',
    letterSpacing: -0.3,
  },
  chevronCircle: {
    width: 36,
    height: 36,
    borderRadius: 18,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
    marginLeft: 8,
  },
  description: {
    fontSize: 13,
    lineHeight: 19,
    marginBottom: 16,
  },
  ctaPill: {
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'flex-start',
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 12,
  },
  ctaPillText: {
    fontSize: 14,
    fontWeight: '600',
  },
  ctaIcon: {
    marginLeft: 8,
  },
});
