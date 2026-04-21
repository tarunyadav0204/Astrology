import React from 'react';
import { Modal, View, Text, TouchableOpacity, StyleSheet } from 'react-native';

export default function ChatRatingPromptModal({ visible, onRateNow, onLater, colors }) {
  const text = colors?.text ?? '#111';
  const sub = colors?.textSecondary ?? '#666';
  const cardBg = colors?.backgroundSecondary ?? colors?.background ?? '#fff';
  const border = colors?.cardBorder ?? colors?.strokeMuted ?? '#eee';
  const primaryBtn = colors?.primary ?? '#e91e63';

  return (
    <Modal visible={visible} transparent animationType="fade" onRequestClose={onLater}>
      <View style={styles.overlay}>
        <View style={[styles.card, { backgroundColor: cardBg, borderColor: border }]}>
          <Text style={[styles.title, { color: text }]}>Enjoying AstroRoshni?</Text>
          <Text style={[styles.body, { color: sub }]}>
            If this answer helped you, please rate us on the Play Store. Your feedback helps us improve.
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
              onPress={onLater}
            >
              <Text style={[styles.btnGhostText, { color: sub }]}>Maybe later</Text>
            </TouchableOpacity>
            <TouchableOpacity style={[styles.btn, styles.btnPrimary, { backgroundColor: primaryBtn }]} onPress={onRateNow}>
              <Text style={styles.btnPrimaryText}>Rate now</Text>
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
    justifyContent: 'space-between',
    gap: 10,
  },
  btn: {
    flex: 1,
    paddingVertical: 11,
    paddingHorizontal: 14,
    borderRadius: 12,
    alignItems: 'center',
  },
  btnGhost: {
    borderWidth: 1,
  },
  btnGhostText: {
    fontWeight: '600',
    fontSize: 14,
  },
  btnPrimary: {
    borderWidth: 0,
  },
  btnPrimaryText: {
    color: '#fff',
    fontWeight: '700',
    fontSize: 14,
  },
});
