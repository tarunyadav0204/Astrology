import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  Modal,
  ScrollView,
  TouchableOpacity,
  useWindowDimensions,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useTranslation } from 'react-i18next';
import { useTheme } from '../context/ThemeContext';

export default function CreditModal({ visible, onConfirm, onCancel, cost, title, description, confirmLabel }) {
  const { t } = useTranslation();
  const { theme, colors } = useTheme();
  const { width, height } = useWindowDimensions();
  const isDark = theme === 'dark';

  const modalGradient = isDark
    ? [colors.gradientStart || '#1E1E2E', colors.gradientMid || '#2A2A40']
    : [colors.cardBackground, colors.backgroundSecondary];
  const confirmGradientColors = isDark ? [colors.accent, colors.primary] : [colors.primary, colors.secondary];
  const overlayBg = isDark ? 'rgba(0, 0, 0, 0.7)' : 'rgba(0, 0, 0, 0.5)';

  return (
    <Modal
      visible={visible}
      transparent={true}
      animationType="fade"
      onRequestClose={onCancel}
    >
      <View style={[styles.overlay, { backgroundColor: overlayBg }]}>
        <View
          style={[
            styles.modalContainer,
            {
              width: Math.min(Math.max(1, width - 32), 420),
              maxHeight: Math.max(1, height - 40),
            },
          ]}
        >
          <LinearGradient
            colors={modalGradient}
            style={styles.modalGradient}
          >
            <ScrollView
              style={styles.modalScroll}
              contentContainerStyle={styles.modalContent}
              showsVerticalScrollIndicator={false}
              bounces={false}
              keyboardShouldPersistTaps="handled"
            >
              {/* Header */}
              <View style={styles.header}>
                <Ionicons name="sparkles" size={32} color={colors.accent} />
                <Text style={[styles.title, { color: colors.text }]}>{title}</Text>
              </View>

              {/* Description */}
              <Text style={[styles.description, { color: colors.textSecondary }]}>{description}</Text>

              {/* Credit Cost */}
              <View
                style={[
                  styles.costContainer,
                  {
                    backgroundColor: colors.selectionSurface,
                    borderColor: colors.selectionBorder,
                  },
                ]}
              >
                <Ionicons name="diamond" size={20} color={colors.selectionText} />
                <Text style={[styles.costText, { color: colors.selectionText }]}>
                  {t('lifeAnalysisFlow.creditsRequiredValue', { cost })}
                </Text>
              </View>

              {/* Buttons */}
              <View style={styles.buttonContainer}>
                <TouchableOpacity
                  style={[styles.cancelButton, { borderColor: colors.cardBorder }]}
                  onPress={onCancel}
                >
                  <Text style={[styles.cancelText, { color: colors.textSecondary }]}>{t('creditConfirmation.cancel')}</Text>
                </TouchableOpacity>

                <TouchableOpacity style={styles.confirmButton} onPress={onConfirm}>
                  <LinearGradient
                    colors={confirmGradientColors}
                    style={styles.confirmGradient}
                  >
                    <Text style={styles.confirmText}>{confirmLabel || t('lifeAnalysisFlow.startAnalysis')}</Text>
                  </LinearGradient>
                </TouchableOpacity>
              </View>
            </ScrollView>
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
    paddingHorizontal: 16,
    paddingVertical: 20,
  },
  modalContainer: {
    borderRadius: 16,
    overflow: 'hidden',
    flexShrink: 1,
  },
  modalGradient: {
    flexShrink: 1,
  },
  modalScroll: {
    flexShrink: 1,
  },
  modalContent: {
    padding: 24,
    alignItems: 'center',
    flexGrow: 1,
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
    borderWidth: 1,
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    marginBottom: 24,
  },
  costText: {
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 8,
    flexShrink: 1,
  },
  buttonContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
    width: '100%',
  },
  cancelButton: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 8,
    borderWidth: 1,
    alignItems: 'center',
    minWidth: 110,
  },
  cancelText: {
    fontSize: 16,
    fontWeight: '600',
  },
  confirmButton: {
    flex: 1,
    borderRadius: 8,
    overflow: 'hidden',
    minWidth: 130,
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
