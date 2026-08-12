import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  Modal,
  TouchableOpacity,
  Pressable,
} from 'react-native';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useTheme } from '../context/ThemeContext';
import { useTranslation } from 'react-i18next';
import { typographyTokens } from '../theme/tokens';

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
  confirmLabel,
  iconName = 'card-outline',
}) {
  const { colors, getCardElevation } = useTheme();
  const { t } = useTranslation();
  const actionLabel = confirmLabel || t('creditConfirmation.continue');

  if (!visible) return null;

  return (
    <Modal
      visible={visible}
      transparent
      animationType="fade"
      onRequestClose={onClose}
    >
      <Pressable style={[styles.overlay, { backgroundColor: colors.overlay }]} onPress={onClose}>
        <Pressable style={styles.outer} onPress={(e) => e.stopPropagation()}>
          <View style={[styles.modalContainer, {
            backgroundColor: colors.surfaceRaised,
            borderColor: colors.cardBorder,
            elevation: getCardElevation(4),
          }]}>
            <View style={[styles.modalAccentLine, { backgroundColor: colors.accent }]} />
            <View style={styles.modalContent}>
              <TouchableOpacity
                style={[styles.closeButton, { backgroundColor: colors.surfaceMuted, borderColor: colors.cardBorder }]}
                onPress={onClose}
                accessibilityRole="button"
                accessibilityLabel={t('creditConfirmation.cancel')}
              >
                <Ionicons name="close" size={18} color={colors.textSecondary} />
              </TouchableOpacity>
              <View style={[styles.iconRow, { backgroundColor: colors.accentSoft }]}>
                <Ionicons name={iconName} size={25} color={colors.onAccent || colors.text} />
              </View>
              <Text style={[styles.eyebrow, { color: colors.accent }]}>{t('creditConfirmation.eyebrow')}</Text>
              <Text style={[styles.modalTitle, { color: colors.text }]}>{title}</Text>
              <Text style={[styles.modalText, { color: colors.textSecondary }]}>
                {description}
              </Text>

              <View style={[styles.modalCreditInfo, { backgroundColor: colors.selectionSurface, borderColor: colors.selectionBorder }]}>
                <View style={styles.creditPrimaryRow}>
                  <View style={[styles.creditGlyph, { backgroundColor: colors.selectionControl }]}>
                    <Ionicons name="card-outline" size={18} color={colors.selectionText} />
                  </View>
                  <View style={styles.creditCopy}>
                    <Text style={[styles.creditLabel, { color: colors.selectionTextMuted }]}>{t('creditConfirmation.chargeLabel')}</Text>
                    <Text style={[styles.modalCreditText, { color: colors.selectionText }]}>{t('creditConfirmation.creditCount', { count: cost })}</Text>
                  </View>
                </View>
                <View style={[styles.balanceDivider, { backgroundColor: colors.selectionBorder }]} />
                <Text style={[styles.modalBalanceText, { color: colors.selectionTextMuted }]}>
                  {t('creditConfirmation.balance', { count: credits })}
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
                  <Text style={[styles.modalCancelText, { color: colors.text }]}>{t('creditConfirmation.cancel')}</Text>
                </TouchableOpacity>
                <TouchableOpacity style={[styles.modalConfirmButton, { backgroundColor: colors.primaryStrong }]} onPress={onConfirm}>
                  <View style={styles.modalConfirmGradient}>
                    <Text style={[styles.modalConfirmText, { color: colors.onPrimary }]}>{actionLabel}</Text>
                    <Ionicons name="arrow-forward" size={17} color={colors.onPrimary} />
                  </View>
                </TouchableOpacity>
              </View>
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
    justifyContent: 'center',
    alignItems: 'center',
  },
  outer: {
    width: '88%',
    maxWidth: 410,
  },
  modalContainer: {
    borderRadius: 28,
    overflow: 'hidden',
    borderWidth: 1,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 18 },
    shadowOpacity: 0.28,
    shadowRadius: 30,
  },
  modalAccentLine: { height: 4, width: '100%' },
  modalContent: {
    paddingHorizontal: 24,
    paddingTop: 28,
    paddingBottom: 22,
    alignItems: 'center',
  },
  iconRow: {
    width: 52,
    height: 52,
    borderRadius: 26,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 14,
  },
  closeButton: {
    position: 'absolute',
    right: 16,
    top: 16,
    width: 34,
    height: 34,
    borderRadius: 17,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  eyebrow: {
    ...typographyTokens.eyebrow,
    fontSize: 9,
    marginBottom: 8,
  },
  modalTitle: {
    ...typographyTokens.display,
    fontSize: 28,
    lineHeight: 32,
    marginBottom: 10,
    textAlign: 'center',
  },
  modalText: {
    fontSize: 15,
    textAlign: 'center',
    lineHeight: 22,
    marginBottom: 22,
    maxWidth: 320,
  },
  modalCreditInfo: {
    padding: 15,
    borderRadius: 18,
    borderWidth: 1,
    marginBottom: 20,
    width: '100%',
  },
  creditPrimaryRow: { flexDirection: 'row', alignItems: 'center' },
  creditGlyph: { width: 38, height: 38, borderRadius: 19, alignItems: 'center', justifyContent: 'center', marginRight: 11 },
  creditCopy: { flex: 1 },
  creditLabel: { fontSize: 9, fontWeight: '800', letterSpacing: 1.2, textTransform: 'uppercase', marginBottom: 2 },
  modalCreditText: {
    fontSize: 17,
    fontWeight: '700',
  },
  balanceDivider: { height: StyleSheet.hairlineWidth, marginVertical: 12 },
  modalBalanceText: {
    fontSize: 12,
    textAlign: 'right',
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
    borderWidth: 1,
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
    justifyContent: 'center',
    flexDirection: 'row',
    gap: 8,
  },
  modalConfirmText: {
    fontSize: 16,
    fontWeight: '600',
  },
});
