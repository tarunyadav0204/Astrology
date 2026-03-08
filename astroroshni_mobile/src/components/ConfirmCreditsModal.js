import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  Modal,
  TouchableOpacity,
  Dimensions,
  Pressable,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useTheme } from '../context/ThemeContext';

const { width } = Dimensions.get('window');

/**
 * Modal that shows credits to be charged and current balance, with Cancel/Confirm.
 * Same style as AnalysisDetailScreen's regenerate modal.
 */
export default function ConfirmCreditsModal({
  visible,
  onClose,
  onConfirm,
  title,
  description,
  cost,
  credits,
  confirmLabel = 'Continue',
}) {
  const { theme, colors } = useTheme();
  const isDark = theme === 'dark';

  const modalGradient = isDark
    ? ['rgba(26, 0, 51, 0.95)', 'rgba(77, 44, 109, 0.95)']
    : [colors.cardBackground, colors.backgroundSecondary];
  const confirmGradientColors = ['#9333ea', '#a855f7'];
  const overlayBg = 'rgba(0, 0, 0, 0.7)';
  const creditInfoBg = colors.surface;

  if (!visible) return null;

  return (
    <Modal
      visible={visible}
      transparent
      animationType="fade"
      onRequestClose={onClose}
    >
      <Pressable style={[styles.overlay, { backgroundColor: overlayBg }]} onPress={onClose}>
        <Pressable style={styles.outer} onPress={(e) => e.stopPropagation()}>
          <View style={styles.modalContainer}>
            <LinearGradient colors={modalGradient} style={styles.modalContent}>
              <View style={styles.iconRow}>
                <Ionicons name="people" size={28} color={colors.accent || '#ec4899'} />
              </View>
              <Text style={[styles.modalTitle, { color: colors.text }]}>{title}</Text>
              <Text style={[styles.modalText, { color: colors.textSecondary }]}>
                {description}
              </Text>

              <View style={[styles.modalCreditInfo, { backgroundColor: creditInfoBg }]}>
                <Text style={[styles.modalCreditText, { color: colors.text }]}>
                  💳 Credits to be charged: {cost}
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
                  <Text style={[styles.modalCancelText, { color: colors.text }]}>Cancel</Text>
                </TouchableOpacity>
                <TouchableOpacity style={styles.modalConfirmButton} onPress={onConfirm}>
                  <LinearGradient colors={confirmGradientColors} style={styles.modalConfirmGradient}>
                    <Text style={styles.modalConfirmText}>{confirmLabel}</Text>
                  </LinearGradient>
                </TouchableOpacity>
              </View>
            </LinearGradient>
          </View>
        </Pressable>
      </Pressable>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  outer: {
    width: width * 0.88,
    maxWidth: 360,
  },
  modalContainer: {
    borderRadius: 16,
    overflow: 'hidden',
  },
  modalContent: {
    padding: 24,
    alignItems: 'center',
  },
  iconRow: {
    marginBottom: 8,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: '700',
    marginBottom: 12,
    textAlign: 'center',
  },
  modalText: {
    fontSize: 15,
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
    alignItems: 'center',
  },
  modalCancelText: {
    fontSize: 16,
    fontWeight: '600',
  },
  modalConfirmButton: {
    flex: 1.2,
    borderRadius: 12,
    overflow: 'hidden',
    alignItems: 'center',
  },
  modalConfirmGradient: {
    paddingVertical: 12,
    paddingHorizontal: 20,
    width: '100%',
    alignItems: 'center',
  },
  modalConfirmText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});
