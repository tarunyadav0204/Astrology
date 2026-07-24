import React from 'react';
import {
  Modal,
  Pressable,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { useTheme } from '../../context/ThemeContext';

export default function AnalysisCreditModal({
  visible,
  onClose,
  onConfirm,
  onGetCredits,
  title,
  description,
  cost,
  credits,
  canAfford = credits >= cost,
  confirmLabel = 'Start Analysis',
  getCreditsLabel = 'Get Credits',
  cancelLabel = 'Cancel',
  confirmGradientColors,
}) {
  const { theme, colors } = useTheme();
  const isDark = theme === 'dark';
  const modalGradient = isDark
    ? ['rgba(26, 0, 51, 0.98)', 'rgba(77, 44, 109, 0.98)']
    : [colors.cardBackground, colors.backgroundSecondary];
  const actionGradient = confirmGradientColors || [colors.primary, colors.secondary];

  return (
    <Modal
      visible={visible}
      transparent
      animationType="fade"
      onRequestClose={onClose}
    >
      <Pressable style={styles.overlay} onPress={onClose}>
        <Pressable style={styles.modalContainer} onPress={(event) => event.stopPropagation()}>
          <LinearGradient colors={modalGradient} style={styles.modalContent}>
            <Text style={[styles.modalTitle, { color: colors.text }]}>{title}</Text>
            <Text style={[styles.modalText, { color: colors.textSecondary }]}>
              {description}
            </Text>

            <View style={[styles.modalCreditInfo, { backgroundColor: colors.surface }]}>
              <Text style={[styles.modalCreditText, { color: colors.text }]}>
                💳 Credits required: {cost}
              </Text>
              <Text style={[styles.modalBalanceText, { color: colors.textSecondary }]}>
                Current balance: {credits}
              </Text>
            </View>

            <View style={styles.modalButtons}>
              <TouchableOpacity
                style={[
                  styles.modalCancelButton,
                  { backgroundColor: isDark ? 'rgba(255, 255, 255, 0.2)' : colors.surface },
                ]}
                onPress={onClose}
              >
                <Text style={[styles.modalCancelText, { color: colors.text }]}>
                  {cancelLabel}
                </Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.modalConfirmButton}
                onPress={canAfford ? onConfirm : onGetCredits}
              >
                <LinearGradient colors={actionGradient} style={styles.modalConfirmGradient}>
                  <Text style={styles.modalConfirmText}>
                    {canAfford ? confirmLabel : getCreditsLabel}
                  </Text>
                </LinearGradient>
              </TouchableOpacity>
            </View>
          </LinearGradient>
        </Pressable>
      </Pressable>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 20,
  },
  modalContainer: {
    width: '100%',
    maxWidth: 420,
    borderRadius: 16,
    overflow: 'hidden',
  },
  modalContent: {
    padding: 24,
    alignItems: 'center',
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: '700',
    marginBottom: 12,
    textAlign: 'center',
  },
  modalText: {
    fontSize: 16,
    textAlign: 'center',
    lineHeight: 22,
    marginBottom: 20,
  },
  modalCreditInfo: {
    padding: 16,
    borderRadius: 12,
    marginBottom: 24,
    width: '100%',
  },
  modalCreditText: {
    fontSize: 16,
    fontWeight: '600',
    textAlign: 'center',
    marginBottom: 4,
  },
  modalBalanceText: {
    fontSize: 14,
    textAlign: 'center',
  },
  modalButtons: {
    flexDirection: 'row',
    gap: 12,
    width: '100%',
  },
  modalCancelButton: {
    flex: 0.8,
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 12,
  },
  modalCancelText: {
    fontSize: 16,
    fontWeight: '600',
    textAlign: 'center',
  },
  modalConfirmButton: {
    flex: 1.2,
    borderRadius: 12,
    overflow: 'hidden',
  },
  modalConfirmGradient: {
    paddingVertical: 12,
    paddingHorizontal: 20,
  },
  modalConfirmText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
    textAlign: 'center',
  },
});
