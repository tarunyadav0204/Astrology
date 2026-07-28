import React from 'react';
import {
  Modal,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useTranslation } from 'react-i18next';
import { useTheme } from '../../context/ThemeContext';

const TONE_COLORS = {
  light: {
    supportive: '#15803D',
    mixed: '#B45309',
    challenging: '#DC2626',
    neutral: '#6D28D9',
  },
  dark: {
    supportive: '#4ADE80',
    mixed: '#FBBF24',
    challenging: '#FF7A7A',
    neutral: '#C4B5FD',
  },
};

const SUBJECT_LABEL_KEYS = {
  self: 'fomoHome.subjectSelf',
  spouse: 'fomoHome.subjectSpouse',
  mother: 'fomoHome.subjectMother',
  father: 'fomoHome.subjectFather',
};

export default function FomoHomeSheet({
  visible,
  data,
  onDismiss,
  onAsk,
}) {
  const { t } = useTranslation();
  const { colors, theme } = useTheme();
  const insets = useSafeAreaInsets();
  const teasers = Array.isArray(data?.teasers) ? data.teasers : [];

  const surface = theme === 'dark' ? '#211238' : '#FFFDFC';
  const tileSurface = theme === 'dark' ? '#2D1948' : '#FFF7ED';
  const border = theme === 'dark' ? 'rgba(255,255,255,0.13)' : '#FED7AA';
  const tonePalette = theme === 'dark' ? TONE_COLORS.dark : TONE_COLORS.light;

  return (
    <Modal
      visible={visible}
      transparent
      animationType="slide"
      onRequestClose={onDismiss}
      statusBarTranslucent
    >
      <View style={styles.overlay}>
        <TouchableOpacity
          style={StyleSheet.absoluteFill}
          activeOpacity={1}
          onPress={onDismiss}
          accessibilityRole="button"
          accessibilityLabel={t('fomoHome.notNow')}
        />
        <View
          style={[
            styles.sheet,
            {
              backgroundColor: surface,
              borderColor: border,
              paddingBottom: Math.max(insets.bottom, 16),
            },
          ]}
        >
          <View style={styles.handle} />
          <View style={styles.header}>
            <View style={styles.headerIcon}>
              <Ionicons name="sparkles" size={20} color="#F97316" />
            </View>
            <View style={styles.headerCopy}>
              <Text style={[styles.eyebrow, { color: '#F97316' }]}>
                {t('fomoHome.eyebrow')}
              </Text>
              <Text style={[styles.heading, { color: colors.text }]}>
                {t('fomoHome.heading')}
              </Text>
              <Text style={[styles.subheading, { color: colors.textSecondary }]}>
                {t('fomoHome.subheading')}
              </Text>
              {data?.chart_name ? (
                <Text style={[styles.chartLabel, { color: colors.textSecondary }]}>
                  {t('fomoHome.chartLabel', { name: data.chart_name })}
                </Text>
              ) : null}
            </View>
            <TouchableOpacity
              style={[styles.closeButton, { backgroundColor: tileSurface }]}
              onPress={onDismiss}
              accessibilityRole="button"
              accessibilityLabel={t('fomoHome.notNow')}
            >
              <Ionicons name="close" size={21} color={colors.text} />
            </TouchableOpacity>
          </View>

          <ScrollView
            style={styles.list}
            contentContainerStyle={styles.listContent}
            showsVerticalScrollIndicator={false}
            keyboardShouldPersistTaps="handled"
          >
            {teasers.map((teaser) => {
              const toneColor =
                tonePalette[teaser.tone] || tonePalette.neutral;
              const suggestedQuestion = String(teaser.suggested_question || '').trim();
              const subjectLabelKey =
                SUBJECT_LABEL_KEYS[String(teaser.subject || '').toLowerCase()];
              return (
                <View
                  key={teaser.presentation_id}
                  style={[
                    styles.tile,
                    {
                      backgroundColor: tileSurface,
                      borderColor: border,
                    },
                  ]}
                >
                  <View style={[styles.toneBar, { backgroundColor: toneColor }]} />
                  <View style={styles.tileCopy}>
                    <View
                      style={[
                        styles.subjectBadge,
                        { backgroundColor: `${toneColor}18` },
                      ]}
                    >
                      <Ionicons
                        name={teaser.subject === 'self' ? 'person' : 'people'}
                        size={14}
                        color={toneColor}
                      />
                      <Text style={[styles.subjectBadgeText, { color: toneColor }]}>
                        {subjectLabelKey
                          ? t(subjectLabelKey)
                          : t('fomoHome.subjectOther')}
                      </Text>
                    </View>
                    <Text style={[styles.tileTitle, { color: colors.text }]}>
                      {teaser.title}
                    </Text>
                    <Text style={[styles.tileTeaser, { color: colors.textSecondary }]}>
                      {teaser.teaser}
                    </Text>
                    <TouchableOpacity
                      activeOpacity={0.82}
                      disabled={!suggestedQuestion}
                      onPress={() => onAsk?.(teaser, suggestedQuestion)}
                      accessibilityRole="button"
                      accessibilityLabel={t('fomoHome.askTara')}
                      style={[
                        styles.askTaraButton,
                        { borderColor: toneColor },
                        !suggestedQuestion && styles.askTaraButtonDisabled,
                      ]}
                    >
                      <Ionicons
                        name="chatbubble-ellipses"
                        size={17}
                        color={toneColor}
                      />
                      <Text style={[styles.revealText, { color: toneColor }]}>
                        {t('fomoHome.askTara')}
                      </Text>
                      <Ionicons
                        name="chevron-forward"
                        size={16}
                        color={toneColor}
                      />
                    </TouchableOpacity>
                  </View>
                </View>
              );
            })}
          </ScrollView>

          <View style={[styles.footer, { borderTopColor: border }]}>
            <TouchableOpacity onPress={onDismiss} style={styles.footerAction}>
              <Text style={[styles.footerPrimary, { color: colors.textSecondary }]}>
                {t('fomoHome.notNow')}
              </Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    justifyContent: 'flex-end',
    backgroundColor: 'rgba(10, 4, 18, 0.72)',
  },
  sheet: {
    width: '100%',
    maxWidth: 680,
    maxHeight: '88%',
    alignSelf: 'center',
    borderTopLeftRadius: 28,
    borderTopRightRadius: 28,
    borderWidth: 1,
    paddingHorizontal: 18,
    shadowColor: '#000000',
    shadowOffset: { width: 0, height: -8 },
    shadowOpacity: 0.28,
    shadowRadius: 24,
    elevation: 24,
  },
  handle: {
    width: 42,
    height: 5,
    borderRadius: 999,
    backgroundColor: 'rgba(148,163,184,0.55)',
    alignSelf: 'center',
    marginTop: 10,
    marginBottom: 14,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 12,
    paddingBottom: 14,
  },
  headerIcon: {
    width: 40,
    height: 40,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'rgba(249,115,22,0.14)',
  },
  headerCopy: { flex: 1 },
  eyebrow: {
    fontSize: 12,
    lineHeight: 16,
    fontWeight: '700',
    letterSpacing: 0.8,
    textTransform: 'uppercase',
  },
  heading: {
    fontSize: 23,
    lineHeight: 29,
    fontWeight: '700',
    marginTop: 2,
  },
  subheading: {
    fontSize: 14,
    lineHeight: 20,
    marginTop: 5,
  },
  chartLabel: {
    fontSize: 12,
    lineHeight: 17,
    fontWeight: '600',
    marginTop: 6,
  },
  closeButton: {
    width: 38,
    height: 38,
    borderRadius: 19,
    alignItems: 'center',
    justifyContent: 'center',
  },
  list: { flexGrow: 0 },
  listContent: { paddingBottom: 12, gap: 10 },
  tile: {
    position: 'relative',
    flexDirection: 'row',
    overflow: 'hidden',
    borderWidth: 1,
    borderRadius: 18,
    minHeight: 120,
  },
  toneBar: { width: 5 },
  tileCopy: { flex: 1, padding: 15 },
  subjectBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'flex-start',
    gap: 5,
    minHeight: 27,
    borderRadius: 999,
    paddingHorizontal: 9,
    marginBottom: 9,
  },
  subjectBadgeText: {
    fontSize: 12,
    lineHeight: 16,
    fontWeight: '700',
  },
  tileTitle: {
    fontSize: 17,
    lineHeight: 23,
    fontWeight: '700',
  },
  tileTeaser: {
    fontSize: 14,
    lineHeight: 20,
    marginTop: 7,
  },
  askTaraButton: {
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'flex-start',
    gap: 6,
    minHeight: 38,
    borderWidth: 1,
    borderRadius: 12,
    paddingHorizontal: 11,
    marginTop: 12,
  },
  askTaraButtonDisabled: { opacity: 0.45 },
  revealText: {
    fontSize: 13,
    lineHeight: 18,
    fontWeight: '700',
  },
  footer: {
    borderTopWidth: StyleSheet.hairlineWidth,
    flexDirection: 'row',
    justifyContent: 'center',
    paddingTop: 12,
  },
  footerAction: {
    alignItems: 'center',
    minWidth: 120,
    paddingVertical: 8,
    paddingHorizontal: 12,
  },
  footerPrimary: { fontSize: 14, fontWeight: '600' },
});
