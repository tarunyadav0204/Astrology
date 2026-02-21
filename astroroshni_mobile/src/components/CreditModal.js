import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  Modal,
  TouchableOpacity,
  Dimensions,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useTheme } from '../context/ThemeContext';

const { width } = Dimensions.get('window');

export default function CreditModal({ visible, onConfirm, onCancel, cost, title, description }) {
  const { theme, colors } = useTheme();
  const isDark = theme === 'dark';

  const modalGradient = isDark
    ? [colors.gradientStart || '#1E1E2E', colors.gradientMid || '#2A2A40']
    : [colors.cardBackground, colors.backgroundSecondary];
  const confirmGradientColors = isDark ? [colors.accent, colors.primary] : [colors.primary, colors.secondary];
  const overlayBg = isDark ? 'rgba(0, 0, 0, 0.7)' : 'rgba(0, 0, 0, 0.5)';
  const costContainerBg = isDark ? 'rgba(255, 215, 0, 0.1)' : 'rgba(249, 115, 22, 0.12)';

  return (
    <Modal
      visible={visible}
      transparent={true}
      animationType="fade"
      onRequestClose={onCancel}
    >
      <View style={[styles.overlay, { backgroundColor: overlayBg }]}>
        <View style={styles.modalContainer}>
          <LinearGradient
            colors={modalGradient}
            style={styles.modalContent}
          >
            {/* Header */}
            <View style={styles.header}>
              <Ionicons name="sparkles" size={32} color={colors.accent} />
              <Text style={[styles.title, { color: colors.text }]}>{title}</Text>
            </View>

            {/* Description */}
            <Text style={[styles.description, { color: colors.textSecondary }]}>{description}</Text>

            {/* Credit Cost */}
            <View style={[styles.costContainer, { backgroundColor: costContainerBg }]}>
              <Ionicons name="diamond" size={20} color={colors.accent} />
              <Text style={[styles.costText, { color: colors.accent }]}>{cost} Credits Required</Text>
            </View>

            {/* Buttons */}
            <View style={styles.buttonContainer}>
              <TouchableOpacity
                style={[styles.cancelButton, { borderColor: colors.cardBorder }]}
                onPress={onCancel}
              >
                <Text style={[styles.cancelText, { color: colors.textSecondary }]}>Cancel</Text>
              </TouchableOpacity>

              <TouchableOpacity style={styles.confirmButton} onPress={onConfirm}>
                <LinearGradient
                  colors={confirmGradientColors}
                  style={styles.confirmGradient}
                >
                  <Text style={styles.confirmText}>Start Analysis</Text>
                </LinearGradient>
              </TouchableOpacity>
            </View>
          </LinearGradient>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalContainer: {
    width: width * 0.85,
    borderRadius: 16,
    overflow: 'hidden',
  },
  modalContent: {
    padding: 24,
    alignItems: 'center',
  },
  header: {
    alignItems: 'center',
    marginBottom: 16,
  },
  title: {
    fontSize: 20,
    fontWeight: 'bold',
    marginTop: 8,
    textAlign: 'center',
  },
  description: {
    fontSize: 14,
    textAlign: 'center',
    lineHeight: 20,
    marginBottom: 20,
  },
  costContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    marginBottom: 24,
  },
  costText: {
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 8,
  },
  buttonContainer: {
    flexDirection: 'row',
    gap: 12,
    width: '100%',
  },
  cancelButton: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 8,
    borderWidth: 1,
    alignItems: 'center',
  },
  cancelText: {
    fontSize: 16,
    fontWeight: '600',
  },
  confirmButton: {
    flex: 1,
    borderRadius: 8,
    overflow: 'hidden',
  },
  confirmGradient: {
    paddingVertical: 12,
    alignItems: 'center',
  },
  confirmText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
});