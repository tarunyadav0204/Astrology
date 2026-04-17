import React from 'react';
import { Modal, View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { useTranslation } from 'react-i18next';

/**
 * Shown after a completed chat answer to upsell podcast playback (credits on first generation).
 */
export default function PodcastPromoModal({ visible, onClose, onGenerate, podcastCost, colors }) {
  const { t } = useTranslation();
  const cost = podcastCost ?? 2;
  const text = colors?.text ?? '#111';
  const sub = colors?.textSecondary ?? '#666';
  // THEMES.dark.cardBackground is translucent glass — use opaque surfaces so the dialog reads as a solid sheet.
  const cardBg = colors?.backgroundSecondary ?? colors?.background ?? '#fff';
  const border = colors?.cardBorder ?? colors?.strokeMuted ?? '#eee';
  const primaryBtn = colors?.primary ?? '#e91e63';

  return (
    <Modal visible={visible} transparent animationType="fade" onRequestClose={onClose}>
      <View style={styles.overlay}>
        <View style={[styles.card, { backgroundColor: cardBg, borderColor: border }]}>
          <Text style={[styles.title, { color: text }]}>
            {t('chat.podcastPromo.title', 'Turn this answer into a podcast')}
          </Text>
          <Text style={[styles.body, { color: sub }]}>
            {t(
              'chat.podcastPromo.body',
              'Listen to this consultation on the go. First-time generation uses {{cost}} credits; replaying the same saved audio is free.',
              { cost }
            )}
          </Text>
          <View style={styles.row}>
            <TouchableOpacity
              style={[
                styles.btn,
                styles.btnGhost,
                {
                  backgroundColor: colors?.backgroundTertiary ?? colors?.surface ?? 'rgba(0,0,0,0.06)',
                  borderColor: border,
                },
              ]}
              onPress={onClose}
            >
              <Text style={[styles.btnGhostText, { color: sub }]}>
                {t('chat.podcastPromo.later', 'Maybe later')}
              </Text>
            </TouchableOpacity>
            <TouchableOpacity style={[styles.btnPrimary, { backgroundColor: primaryBtn }]} onPress={onGenerate}>
              <Text style={styles.btnPrimaryText}>
                {t('chat.podcastPromo.cta', 'Generate podcast')}
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
    marginBottom: 18,
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    flexWrap: 'wrap',
    gap: 10,
  },
  btn: {
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 12,
  },
  btnGhost: {
    borderWidth: 1,
  },
  btnGhostText: {
    fontWeight: '600',
    fontSize: 15,
  },
  btnPrimary: {
    paddingVertical: 12,
    paddingHorizontal: 18,
    borderRadius: 12,
  },
  btnPrimaryText: {
    color: '#fff',
    fontWeight: '700',
    fontSize: 15,
  },
});
