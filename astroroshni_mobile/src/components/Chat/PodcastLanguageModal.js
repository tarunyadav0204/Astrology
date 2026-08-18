import React from 'react';
import { Modal, View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { useTranslation } from 'react-i18next';

const OPTIONS = [
  { code: 'en', labelKey: 'chat.podcastLanguage.english', fallback: 'English' },
  { code: 'hi', labelKey: 'chat.podcastLanguage.hindi', fallback: 'हिन्दी' },
];

/**
 * English / Hindi picker before podcast generate or replay.
 */
export default function PodcastLanguageModal({
  visible,
  selectedLang = 'en',
  included = false,
  onSelect,
  onClose,
  colors,
}) {
  const { t } = useTranslation();
  const text = colors?.text ?? '#111';
  const sub = colors?.textSecondary ?? '#666';
  const cardBg = colors?.backgroundSecondary ?? colors?.background ?? '#fff';
  const border = colors?.cardBorder ?? colors?.strokeMuted ?? '#eee';
  const primary = colors?.primary ?? '#e91e63';
  const selected = String(selectedLang || 'en').toLowerCase().startsWith('hi') ? 'hi' : 'en';

  return (
    <Modal visible={visible} transparent animationType="fade" onRequestClose={onClose}>
      <View style={styles.overlay}>
        <View style={[styles.card, { backgroundColor: cardBg, borderColor: border }]}>
          <Text style={[styles.title, { color: text }]}>
            {t('chat.podcastLanguage.title', 'Choose podcast language')}
          </Text>
          <Text style={[styles.body, { color: sub }]}>
            {included
              ? t(
                  'chat.podcastLanguage.premiumBody',
                  'This Premium answer includes a free podcast. Choose English or Hindi.',
                )
              : t(
                  'chat.podcastLanguage.body',
                  "We'll generate the audio in the language you pick. English and Hindi only.",
                )}
          </Text>
          <View style={styles.options}>
            {OPTIONS.map((opt) => {
              const isSelected = selected === opt.code;
              return (
                <TouchableOpacity
                  key={opt.code}
                  style={[
                    styles.option,
                    {
                      borderColor: isSelected ? primary : border,
                      backgroundColor: isSelected
                        ? `${primary}14`
                        : (colors?.backgroundTertiary ?? colors?.surface ?? 'rgba(0,0,0,0.04)'),
                    },
                  ]}
                  onPress={() => onSelect?.(opt.code)}
                  accessibilityRole="button"
                  accessibilityState={{ selected: isSelected }}
                >
                  <Text style={[styles.optionLabel, { color: isSelected ? primary : text }]}>
                    {t(opt.labelKey, opt.fallback)}
                  </Text>
                </TouchableOpacity>
              );
            })}
          </View>
          <TouchableOpacity
            style={[
              styles.cancel,
              {
                backgroundColor: colors?.backgroundTertiary ?? colors?.surface ?? 'rgba(0,0,0,0.06)',
                borderColor: border,
              },
            ]}
            onPress={onClose}
          >
            <Text style={[styles.cancelText, { color: sub }]}>
              {t('chat.podcastLanguage.cancel', 'Cancel')}
            </Text>
          </TouchableOpacity>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.45)',
    justifyContent: 'center',
    padding: 20,
  },
  card: {
    borderRadius: 16,
    padding: 22,
    borderWidth: 1,
  },
  title: {
    fontSize: 18,
    fontWeight: '700',
    marginBottom: 10,
  },
  body: {
    fontSize: 14,
    lineHeight: 21,
    marginBottom: 16,
  },
  options: {
    gap: 10,
  },
  option: {
    paddingVertical: 14,
    paddingHorizontal: 16,
    borderRadius: 12,
    borderWidth: 1.5,
  },
  optionLabel: {
    fontSize: 17,
    fontWeight: '700',
    textAlign: 'center',
  },
  cancel: {
    marginTop: 14,
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 12,
    borderWidth: 1,
    alignItems: 'center',
  },
  cancelText: {
    fontWeight: '600',
    fontSize: 15,
  },
});
