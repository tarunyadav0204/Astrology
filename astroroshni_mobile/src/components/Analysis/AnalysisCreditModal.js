import React from 'react';
import {
  Modal,
  Pressable,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { useTheme } from '../../context/ThemeContext';
import { useTranslation } from 'react-i18next';

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
  confirmLabel,
  getCreditsLabel,
  cancelLabel,
}) {
  const { colors } = useTheme();
  const { t } = useTranslation();

  return (
    <Modal
      visible={visible}
      transparent
      animationType="fade"
      onRequestClose={onClose}
    >
      <Pressable style={[styles.overlay, { backgroundColor: colors.overlay }]} onPress={onClose}>
        <Pressable style={styles.modalContainer} onPress={(event) => event.stopPropagation()}>
          <View style={[styles.modalContent, { backgroundColor: colors.surfaceRaised, borderColor: colors.cardBorder }]}>
            <Text style={[styles.eyebrow, { color: colors.primary }]}>{t('lifeAnalysisFlow.personalisedReading')}</Text>
            <Text style={[styles.modalTitle, { color: colors.text }]}>{title}</Text>
            <Text style={[styles.modalText, { color: colors.textSecondary }]}>
              {description}
            </Text>

            <View style={[styles.modalCreditInfo, { backgroundColor: colors.surfaceMuted, borderColor: colors.cardBorder }]}>
              <Text style={[styles.modalCreditText, { color: colors.text }]}>
                {t('lifeAnalysisFlow.creditsRequiredValue', { cost })}
              </Text>
              <Text style={[styles.modalBalanceText, { color: colors.textSecondary }]}>
                {t('lifeAnalysisFlow.currentBalance', { credits })}
              </Text>
            </View>

            <View style={styles.modalButtons}>
              <TouchableOpacity
                style={[
                  styles.modalCancelButton,
                  { backgroundColor: colors.surface, borderColor: colors.cardBorder },
                ]}
                onPress={onClose}
              >
                <Text style={[styles.modalCancelText, { color: colors.text }]}>
                  {cancelLabel || t('common.cancel')}
                </Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.modalConfirmButton}
                onPress={canAfford ? onConfirm : onGetCredits}
              >
                <View style={[styles.modalConfirmGradient, { backgroundColor: colors.primary }]}>
                  <Text style={[styles.modalConfirmText, { color: colors.onPrimary }]}>
                    {canAfford
                      ? (confirmLabel || t('lifeAnalysisFlow.startAnalysis'))
                      : (getCreditsLabel || t('lifeAnalysisFlow.getCredits'))}
                  </Text>
                </View>
              </TouchableOpacity>
            </View>
          </View>
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
    borderRadius: 26,
    overflow: 'hidden',
  },
  modalContent: {
    padding: 26,
    alignItems: 'stretch',
    borderWidth: 1,
  },
  eyebrow: {
    fontSize: 11,
    fontWeight: '800',
    letterSpacing: 1.8,
    marginBottom: 10,
  },
  modalTitle: {
    fontSize: 30,
    fontFamily: 'serif',
    fontWeight: '500',
    marginBottom: 12,
    textAlign: 'left',
  },
  modalText: {
    fontSize: 16,
    textAlign: 'left',
    lineHeight: 22,
    marginBottom: 20,
  },
  modalCreditInfo: {
    padding: 16,
    borderRadius: 12,
    marginBottom: 24,
    width: '100%',
    borderWidth: 1,
  },
  modalCreditText: {
    fontSize: 16,
    fontWeight: '600',
    textAlign: 'left',
    marginBottom: 4,
  },
  modalBalanceText: {
    fontSize: 14,
    textAlign: 'left',
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
    borderWidth: 1,
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
